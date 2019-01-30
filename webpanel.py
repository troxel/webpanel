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

from html import escape

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-q", help="Run in embedded mode",action="store_true")
args = parser.parse_args()

import sysinfo
import modconfig
import gencerts

from templaterex import TemplateRex

# Custom search path
TemplateRex.template_dirs = ['./templates_cust','./templates']

from webauth  import AuthSession
from firmware import FirmwareUpdate
from commonutils import Utils

import solo
solo.chk_and_stopall(__file__)

# #########################################
# Begin Main CherryPy Server Class
# #########################################
class WebPanel(Utils):

   def __init__(self):

      self.version = 1.0;

      if os.path.isfile('./DEV_MODE'):
         self.dev_mode = True
      else:
         self.dev_mode = False

      TemplateRex.dev_mode = self.dev_mode

      self.dir = {}
      self.dir['cert'] = './cert'

      # Create deque for tail
      self.tail_max = 20
      self.tail = collections.deque(maxlen=self.tail_max)

      # cert stuff...
      self.certobj = gencerts.GenCerts(dir_root='./cert')

      self.auth = AuthSession(url_login="/webpanel/auth/login")
      self.firmware = FirmwareUpdate()

      # merge common utils
      Utils.__init__(self)

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

      data_hsh['username'] = self.auth.authorize()

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

      ntp_info = sysinfo.get_ntp_info()
      if 'ntp_status' in ntp_info: data_hsh['ntp_status'] = ntp_info['ntp_status']
      if 'ntp_server' in ntp_info: data_hsh['ntp_server'] = ntp_info['ntp_server']

      return( self.render_layout(trex,data_hsh) )

   # ------------------------
   @cherrypy.expose
   def netconf_rtn(self, **params):

      username = self.auth.authorize()

      # A complete specification of the url for redirects is required
      url_redirect = self.url_gen('/webpanel')

      # Object to handle the actual system config.
      # Assumes dhcpcd5 is controlling the network configuration

      # This takes the extra step to handle multiple interfaces. Adds
      # complexity but there cases when there are multiple interfaces.

      modconf = modconfig.DHCP()

      if not 'ip_method' in params:
         raise cherrypy.HTTPRedirect(url_redirect)

      if params['ip_method'] == 'static':

         # --------- Validate input   ---------

         err_hsh = self.netconf_validate(params)

         if err_hsh:
            trex_err = TemplateRex(fname='t_netconf_err.html')
            for key in err_hsh:
               trex_err.render_sec("err_blk",{'key':key, 'val':params[key], 'msg':err_hsh[key]})

            trex_err.render_sec('content')

            return(trex_err.render())
         # -------------

         modconf.set_static(params)

         modconf.set_hostname(params['hostname'], params['ip_address'])

         modconf.set_ntp_server(params['ntp_server'])

         modconf.set_dns(dns_servers = [ params['dns_server_0'], params['dns_server_1'] ])

      else:

         modconf.set_dhcp()

      ###rtn = subprocess.check_output(['systemctl','restart','dhcpcd.service'],stderr=subprocess.STDOUT)
      rtn = os.system("(sleep 2; reboot)&")

      raise cherrypy.HTTPRedirect(url_redirect)

   # ------------------------
   def netconf_validate(self,params):

      err_hsh = {}

      for key in ('ip_address','gateway'):

         try:
            ip_ckh = ipaddress.ip_address(params[key])
         except:
            err_hsh[key] = "Not valid IP address"   # assumes id == name in input html

      for key in ('ntp_server',):
         if not sysinfo.is_valid_hostname(params[key]):
            err_hsh[key] = "Not valid IP/Host address"

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

      self.auth.authorize()

      # dev_mode give location of templates being used in html output
      trex = TemplateRex(fname='t_sslcert-newcert.html',dev_mode=True)

      cert_hsh = self.certobj.parse_cert('webpanel.crt')

      nic_info  = sysinfo.get_iface_info()
      host_info = sysinfo.get_host_info()
      dns_info  = sysinfo.get_dns_info()

      trex.render_sec('subject',cert_hsh['subject'])

      # Use actual ip address and not what is in current cert. If nic is not eth0 trouble...
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
      # Todo: add some validation

      self.auth.authorize()

      rtn = self.certobj.gen_server_cert( params,ip_lst=params['ip_lst'],dns_lst=params['dns_lst'] )
      if rtn == True:
         rtn = os.system("(sleep 2; systemctl restart nginx)&")
         raise cherrypy.InternalRedirect('/webpanel/sslcert/')
      else:
         raise cherrypy.HTTPError(500,self.certobj.error_msg)


   # --------------------------------------------
   # Common featured called at the end of each callback abstracted out
   def render_layout(self,trex,data_hsh={}):

      data_hsh['version'] = self.version
      data_hsh['user']    = cherrypy.request.login

      if cherrypy.request.login:
         trex.render_sec('logged_in',{'user':cherrypy.request.login})

      trex.render_sec('content',data_hsh)

      return(trex.render(data_hsh))

   # --------------------------------------------
   def redirect(self,url):

      # local ip means nginx is handling the request - set baseref
      #if cherrypy.request.headers['Remote-Addr'] == '127.0.0.1':
      #   url = '/webpanel/' + url

      raise cherrypy.HTTPRedirect(url)

# ----------------------------
class PyServ(object):

   def __init__(self):

      self.version = 1.0;

      if os.path.isfile('./DEV_MODE'):
         self.dev_mode = True

   webpanel = WebPanel()

   @cherrypy.expose
   def index(self):
      print(">>>>>")
      raise cherrypy.HTTPRedirect("/webpanel/")


# #################################
port = 9091
if __name__ == '__main__':

   dir_session = '/tmp/sessions'
   if not os.path.exists(dir_session):
          os.mkdir(dir_session)

   cherrypy.config.update({'tools.sessions.storage_type':"file"})
   cherrypy.config.update({'tools.sessions.storage_path':dir_session})
   cherrypy.config.update({'tools.sessions.on': True})
   cherrypy.config.update({'tools.sessions.timeout': 99999})

   cherrypy.config.update({'tools.response_headers.on': True})

   if not args.q:
      print("\nStarting {} Server\n".format(__file__))
      print("Use Chrome and go to port {}/\n".format(port))

   cherrypy.config.update({'server.socket_port': port})
   cherrypy.config.update({'server.socket_host': "0.0.0.0" })

   # Run in embedded mode
   if args.q:
      cherrypy.config.update({'environment': 'production'})
      cherrypy.config.update({'log.access_file':'/dev/null'})
      cherrypy.config.update({'engine.autoreload.on' : False})
      #cherrypy.config.update({'request.error_response': show_blank_page_on_error})

   cherrypy.quickstart(PyServ(), '/', '/opt/webpanel/conf/pyserv.conf')


   # --------------------------------------------------
   def show_blank_page_on_error(msg):
      cherrypy.response.status = 500
      cherrypy.response.body = "Hello " + msg
