#!/usr/bin/python3

# Import Libraries
import os, os.path
import cherrypy
import random
import csv
import json
import sys
import time
from pprint import pprint
import stat
import collections
import re
import datetime
import subprocess

import traceback


import solo
solo.chk_and_stopall(__file__)

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("-q", help="Run in embedded mode",action="store_true")
args = parser.parse_args()

# Common file specifications
import fspec

sys.path.append('./packages')
from templaterex import TemplateRex

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

      trex = TemplateRex(fname='t_mon_index.html')

      # Last Measurement
      rtn_json = self._read_json(fspec.t_last)
      if rtn_json:

         # json is returned as a list of hash
         for dev_hsh in rtn_json['json']:
            trex.render_sec('t_row',dev_hsh)

         diff_time = time.time() - rtn_json['stat'].st_mtime

         if diff_time > 10:
            trex.render_sec('stale_warn',{'diff_time':str(diff_time)})

      else:
         trex.render_sec('no_last',{})

      # Display power down events.
      if os.path.isfile(fspec.pwr_down_log):
         cmd_lst = ['tail',fspec.pwr_down_log]
         rtn = subprocess.run(cmd_lst, stdout=subprocess.PIPE)
         log_tail = rtn.stdout.decode('utf-8')

         log_lst = log_tail.splitlines()
         log_lst.reverse()

         for log_line in log_lst:
            trex.render_sec('log_row',{'log_line':log_line})
      else:
            uptime_str = self._uptime()
            trex.render_sec('no_events',{'uptime_str':uptime_str})


      data_hsh['version'] = self.version

      trex.render_sec('content',data_hsh)

      page = trex.render()

      return page

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
port = 8080

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

   cherrypy.quickstart(PyServ(), '/', '/home/pi/t_mon/conf/pyserv.conf')
   p.terminate()
