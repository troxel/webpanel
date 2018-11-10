#!/usr/bin/python3

# Import Libraries
import os, os.path
import cherrypy
import random
import csv
import json
import sys
import time
import pprint
import stat
import collections
import re
import datetime
import subprocess
import ssl

import psutil

import ipaddress

import traceback

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-q", help="Run in embedded mode",action="store_true")
args = parser.parse_args()

import sysinfo
import modconfig
import gencerts

# Local sub-modules
sys.path.insert(0,'./packages')
from templaterex import TemplateRex

import solo
solo.chk_and_stopall(__file__)

class PyServ(object):

   def __init__(self):

      self.version = 1.0;

      if os.path.isfile('./DEV_MODE'):
         self.dev_mode = True

      self.dir = {}
      self.dir['cert'] = './cert'

      # Create deque for tail
      self.tail_max = 20
      self.tail = collections.deque(maxlen=self.tail_max)

      # cert stuff...
      self.certobj = gencerts.GenCerts(dir_root='./cert')

      # Test stuff... erase later.
      self.cnt = 1
      self.inc=0

   # ------------------------
   @cherrypy.expose
   def index(self):

      data_hsh = {}
      root_path = os.getcwd()

      nic_info = sysinfo.get_iface_info()

      host_info = sysinfo.get_host_info()

      data_hsh.update(host_info)

      trex = TemplateRex(fname='t_index.html')

      for nic in nic_info:
         trex.render_sec('nic_blk',nic_info[nic])

      return( self.render_layout(trex,data_hsh) )

   # ------------------------
   @cherrypy.expose
   def netconf(self,err_struct=""):

      data_hsh = {}

      #if err_struct:
      #   data_hsh['err_msg'] = err_struct['err_msg'];
      #   data_hsh['err_id_lst_json'] = json.dumps(err_struct['err_ids'])

      nic_info  = sysinfo.get_iface_info()
      host_info = sysinfo.get_host_info()
      dns_info  = sysinfo.get_dns_info()

      for inx,srv in enumerate(dns_info['nameserver']):
         key = 'dns_server_{}'.format(inx)
         data_hsh[key] = srv

      ##pprint.pprint(data_hsh)

      data_hsh.update(nic_info)
      data_hsh.update(host_info)

      # Still holding on the possibility of more than one nic
      nic_name = list(nic_info.keys())[0]

      if sysinfo.is_dhcp(nic_name):
         data_hsh['dhcp_checked'] = 'checked'
      else:
         data_hsh['static_checked'] = 'checked'

      trex = TemplateRex(fname='t_netconf.html')

      # Pulling back support for multiple NIC for now.
      if len(nic_info) > 1:
         return("Error only one NIC supported")

      for nic in nic_info:
         trex.render_sec('nic_blk',nic_info[nic])

      return( self.render_layout(trex,data_hsh) )

   # ------------------------
   @cherrypy.expose
   def netconf_rtn(self, **params):

      # Object to handle the actual system config.
      # Assumes dhcpcd5 is controlling the network configuration

      # This takes the extra step to handle multiple interfaces. Adds
      # complexity but there cases when there are multiple interfaces.

      if self.dev_mode:
         modconf = modconfig.DHCP(ro_flag=False)
      else:
         modconf = modconfig.DHCP(ro_flag=True)

      if params['ip_method'] == 'static':

         # --------- Validate input   ---------
         err_hsh = self.netconf_validate(params)

         if err_hsh:
            trex_err = TemplateRex(fname='t_netconf_err.html')
            for key in err_hsh:
               print("key ->",key," ",params[key])
               trex_err.render_sec("err_blk",{'key':key, 'val':params[key], 'msg':err_hsh[key]})

            trex_err.render_sec('content')

            return(trex_err.render())
         # -------------

         modconf.set_static(params)

         modconf.set_hostname(params['hostname'], params['ip_address'])

      else:

         modconf.set_dhcp()

      trex_redirect = TemplateRex(fname='t_redirect.html')
      data_hsh = {}
      data_hsh['refresh'] = "2; url=netconf"
      data_hsh['msg'] = "Reconfiguring... please wait"

      return( self.render_layout(trex_redirect,data_hsh) )

   # ------------------------
   def netconf_validate(self,params):

      err_hsh = {}

      for key in ('ip_address','gateway','dns_server_0','dns_server_1'):

         try:
            ip_ckh = ipaddress.ip_address(params[key])
         except:
            if key == 'dns_server_1' and params[key] == '': continue
            err_hsh[key] = "Not valid IP address"   # assumes id == name in input html

      cidr = int(params['cidr'])
      if ( cidr < 1 or cidr > 31):
         err_hsh['cidr'] = "Must integer between 1 and 31"

      if re.search('\.',params['hostname']):
         err_hsh['hostname'] = 'Invalid Hostname'

      return(err_hsh)

   # ------------------------
   @cherrypy.expose
   def sslcert(self):

      data_hsh = sysinfo.get_host_info()

      trex = TemplateRex(fname='t_sslcert.html')

      cert_hsh = self.certobj.parse_cert('webpanel.crt')
      ca_hsh = self.certobj.parse_cert('webpanelCA.crt')

      # First server cert
      # subj alt name really important for x509 v3
      for inx,ip in enumerate(cert_hsh['subjectAltName']['ip_lst']):
         trex.render_sec('subj_alt_name_ip',{'inx':inx, 'val':ip})

      for inx,dns in enumerate(cert_hsh['subjectAltName']['dns_lst']):
         trex.render_sec('subj_alt_name_dns',{'inx':inx, 'val':dns})

      trex.render_sec('subject',cert_hsh['subject'])
      trex.render_sec('cert_server',cert_hsh)

      # Then CA cert
      trex.render_sec('subject',ca_hsh['subject'])
      trex.render_sec('cert_CA',ca_hsh)

      return( self.render_layout(trex,data_hsh) )

   #--------------------------------------
   @cherrypy.expose
   def sslcert_newcert(self,**params):
      trex = TemplateRex(fname='t_sslcert-newcert.html')

      cert_hsh = self.certobj.parse_cert('webpanel.crt')

      nic_info  = sysinfo.get_iface_info()
      host_info = sysinfo.get_host_info()
      dns_info  = sysinfo.get_dns_info()

      trex.render_sec('subject',cert_hsh['subject'])

      # Use actual ip address an not what is in current cert. If nic is not eth0 trouble...
      try:
         trex.render_sec('subj_alt_name_ip',{'inx':0,'val':nic_info['eth0']['ip_address']})
      except:
         trex.render_sec('subj_alt_name_ip',{'inx':0,'val':''})

      trex.render_sec('subj_alt_name_ip',{'inx':1,'val':'127.0.0.1'})
      trex.render_sec('subj_alt_name_ip',{'inx':2,'val':''})
      trex.render_sec('subj_alt_name_ip',{'inx':3,'val':''})

      try:
         trex.render_sec('subj_alt_name_dns',{'inx':0,'val':host_info['hostname']})
      except:
         trex.render_sec('subj_alt_name_dns',{'inx':0,'val':''})

      try:
         trex.render_sec('subj_alt_name_dns',{'inx':1,'val':"{}.{}".format(host_info['hostname'],dns_info['domain'])})
      except:
         trex.render_sec('subj_alt_name_dns',{'inx':1,'val':''})

      trex.render_sec('subj_alt_name_dns',{'inx':2,'val':''})
      trex.render_sec('subj_alt_name_dns',{'inx':3,'val':''})

      return( self.render_layout(trex,{}) )

   #--------------------------------------
   @cherrypy.expose
   def sslcert_newcert_rtn(self,**params):
      #pprint.pprint(params)

      rtn = self.certobj.gen_server_cert( params,ip_lst=params['ip_lst'],dns_lst=params['dns_lst'] )

      trex_redirect = TemplateRex(fname='t_redirect.html')
      data_hsh = {}
      data_hsh['refresh'] = "2; url=sslcert/"
      data_hsh['msg'] = "Generating New Key and Server Certificate... Please wait"

      return( self.render_layout(trex_redirect,data_hsh) )

   # --------------------------------------------
   # utility functions
   # --------------------------------------------

   # Common featured called at the end of each callback abstracted out
   def render_layout(self,trex,data_hsh={}):

      data_hsh['version'] = self.version

      # local ip means nginx is handling the request - set baseref
      if cherrypy.request.headers['Remote-Addr'] == '127.0.0.1':
         data_hsh['base_ref'] = '/webpanel/'
      else:
         data_hsh['base_ref'] = '/'

      trex.render_sec('content',data_hsh)

      return(trex.render(data_hsh))

# ---------------------------------
port = 9091
if __name__ == '__main__':

   #dir_session = './sessions'
   #if not os.path.exists(dir_session):
   #       print "making dir",dir_session
   #       os.mkdir(dir_session)
   #import inspect
   #print(inspect.getfile(TemplateRex))

   if not args.q:
      print("\nStarting {} Server\n".format(__file__))
      print("Use Chrome and go to port {}/\n".format(port))

   cherrypy.config.update({'server.socket_port': port})
   cherrypy.config.update({'server.socket_host': "0.0.0.0" })

   # Run in embedded mode
   if args.q:
      cherrypy.config.update({'environment': 'production'})
      cherrypy.config.update({'log.access_file':'/dev/null'})
      cherrypy.config.update({'request.error_response': show_blank_page_on_error})

   cherrypy.quickstart(PyServ(), '/', '/opt/webpanel/conf/pyserv.conf')
   p.terminate()

   # --------------------------------------------------
   def show_blank_page_on_error(msg):
      cherrypy.response.status = 500
      cherrypy.response.body = "Hello " + msg
