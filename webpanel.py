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

import psutil

import ipaddress

import traceback

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-q", help="Run in embedded mode",action="store_true")
args = parser.parse_args()

import sysinfo
import modconfig

# Local sub-modules
sys.path.insert(0,'./packages')
from templaterex import TemplateRex

import solo
solo.chk_and_stopall(__file__)

class PyServ(object):

   def __init__(self):

      self.version = 1.0;

      # Create deque for tail
      self.tail_max = 20
      self.tail = collections.deque(maxlen=self.tail_max)

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
      pprint.pprint(host_info)
      data_hsh.update(host_info)

      trex = TemplateRex(fname='t_index.html')

      for nic in nic_info:
         trex.render_sec('nic_blk',nic_info[nic])

      data_hsh['version'] = self.version

      trex.render_sec('content',data_hsh)

      page = trex.render(data_hsh)

      return page

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

      for inx,srv in enumerate(dns_info):
         key = 'dns_server_{}'.format(inx)
         data_hsh[key] = srv

      pprint.pprint(data_hsh)

      data_hsh.update(nic_info)
      data_hsh.update(host_info)

      if sysinfo.is_dhcp():
         data_hsh['dhcp_checked'] = 'checked'
      else:
         data_hsh['static_checked'] = 'checked'

      trex = TemplateRex(fname='t_netconf.html')

      # Pulling back support for multiple NIC for now.
      if len(nic_info) > 1:
         return("Error only one NIC supported")

      for nic in nic_info:
         trex.render_sec('nic_blk',nic_info[nic])

      data_hsh['version'] = self.version

      trex.render_sec('content',data_hsh)

      page = trex.render(data_hsh)

      return page

   # ------------------------
   @cherrypy.expose
   def netconf_rtn(self, **params):

      # This takes the extra step to handle multiple interfaces. Adds
      # complexity but there cases when there are multiple interfaces.

      # Object to handle the actual system config.
      # Assumes dhcpcd5 is controlling the network configuration

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
      page = trex_redirect.render({'msg':"Rebooting... please wait",'refresh':"10; url=/"})

      modconf.reboot()

      return(page)

      #print("doing a redirect")
      #raise cherrypy.HTTPRedirect("/")

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
   def certificate(self,err_struct=""):

      data_hsh = sysinfo.get_host_info()

      trex = TemplateRex(fname='t_certificate.html')

      trex.render_sec('gen_cert_btn')
      trex.render_sec('content',data_hsh)

      return(trex.render())


   # --------------------------------------------
   # utility functions
   # --------------------------------------------
   def _uptime(self):
      with open('/proc/uptime', 'r') as fid:
         uptime_seconds = float(fid.readline().split()[0])
         uptime_str = str(datetime.timedelta(seconds = uptime_seconds))
         uptime_str = re.sub('\.\d+$','',uptime_str)
      return(uptime_str)

   def _read_json(self,fspec,try_max=20):
      try_inx = 1
      if os.path.isfile(fspec):
         while try_inx < try_max:
            try:
               fd = open(fspec,'r')
               rtn = {}
               rtn['json'] = json.loads(fd.read())
               rtn['stat'] = os.stat(fspec)
               fd.close()
               return(rtn)
            except:
               try_inx = try_inx + 1
               print("Unexpected error:", sys.exc_info()[0])
               print(traceback.format_exc())
      print(">>> {}".format(try_inx))
      return(False)

####### End of Class PyServ #############

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
