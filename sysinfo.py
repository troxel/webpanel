from pprint import pprint

import netifaces as net
import os
import datetime
import re
import platform

class netinfo(object):

   def __init__(self):

      self.version = 1.0;
      self.if_lst = net.interfaces()
      self.if_lst.pop(0) # remove lo

   # ------------------------
   def get_iface_info(self):

      if_hsh = {}

      # ugli... but that is why we need write this class
      gw_hsh=net.gateways()
      gw_default_lst = gw_hsh['default'][net.AF_INET]

      for if_name in self.if_lst:
         ifstruct = net.ifaddresses(if_name)

         if_hsh[if_name] = ifstruct[net.AF_INET][0]  # loads addr,broadcast,netmask
         if_hsh[if_name]['if_name'] = if_name
         if_hsh[if_name]['mac'] = ifstruct[net.AF_LINK][0]['addr']

         # set default gateway
         if gw_default_lst[1] == if_name:
            if_hsh[if_name]['gateway'] = gw_default_lst[0]

      return if_hsh

   # ------------------------
   def get_host_info(self):

      host_hsh = {}

      uname = os.uname()
      host_hsh['hostname'] = uname.nodename
      host_hsh['release']  = uname.release
      host_hsh['machine']   = uname.machine

      # Not cross platform....
      try:
         with open('/proc/uptime', 'r') as fid:
            uptime_seconds = float(fid.readline().split()[0])
            uptime_str = str(datetime.timedelta(seconds = uptime_seconds))
            host_hsh['uptime'] = re.sub('\.\d+$','',uptime_str)
      except:
         pass

      try:
         host_hsh.update(distro.info())
      except:
         print("Not supported")


      return host_hsh
