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
   def netconf(self,err_msg=""):

      data_hsh = {}

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

      for nic in nic_info:
         trex.render_sec('nic_blk',nic_info[nic])

      data_hsh['version'] = self.version

      trex.render_sec('content',data_hsh)

      page = trex.render(data_hsh)

      return page

   # ------------------------
   @cherrypy.expose
   def netconf_rtn(self, **params):

      host_info = sysinfo.get_host_info()
      pprint.pprint(host_info)

      if params['ip_method'] == 'static':

         err_msg = ''
         for ip_addr in ('addr','gateway','netmask'):
            try:
               ip_ckh = ipaddress.ip_address(params[ip_addr])
            except:
               err_msg += "ip " + ip_addr

         if err_msg:
            return self.netconf(err_msg=err_msg)

      pprint.pprint(params)
      return("hello <pre>",pprint.pformat(params))



   # --------------------------------------------
   # utility functions
   # --------------------------------------------
   #def _get_nic_info(self):
   #
   #   nics = psutil.net_if_addrs()
   #   nics.pop('lo')
   #
   #   nic_info = {}
   #   for nic, nic_addrs in nics.items():
   #      nic_info[nic] = {}
   #      nic_info[nic]['ip_addr']    = nic_addrs[0].address
   #      nic_info[nic]['ip_netmask'] = nic_addrs[0].netmask
   #      nic_info[nic]['mac_addr']   = nic_addrs[2].address
   #      nic_info[nic]['nic_name']   = nic
   #
   #   return(nic_info)

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

   cherrypy.quickstart(PyServ(), '/', '/opt/webpanel/conf/pyserv.conf')
   p.terminate()
