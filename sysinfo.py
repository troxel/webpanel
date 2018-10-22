from pprint import pprint

import netifaces as net
import os
import os.path
import datetime
import re
import platform
import distro

def __init__():
   version = 1.0;

# ------------------------
def get_iface_info():

   if_hsh = {}

   # ugli... but that is why we need write this class
   gw_hsh=net.gateways()
   gw_default_lst = gw_hsh['default'][net.AF_INET]

   if_lst = net.interfaces()
   if_lst.pop(0) # remove lo

   for if_name in if_lst:
      ifstruct = net.ifaddresses(if_name)
      
      try: 
         tmp_hsh = ifstruct[net.AF_INET][0]  # loads addr,broadcast,netmask
      except:
         continue 
      
      if_hsh[if_name] = {}
      if_hsh[if_name]['ip_address'] = tmp_hsh['addr']
      if_hsh[if_name]['broadcast']  = tmp_hsh['broadcast']
      if_hsh[if_name]['netmask']    = tmp_hsh['netmask']
      if_hsh[if_name]['cidr']       = sum([bin(int(x)).count('1') for x in tmp_hsh['netmask'].split('.')])

      if_hsh[if_name]['if_name'] = if_name
      if_hsh[if_name]['mac'] = ifstruct[net.AF_LINK][0]['addr']

      # set default gateway
      if gw_default_lst[1] == if_name:
         if_hsh[if_name]['gateway'] = gw_default_lst[0]

   return if_hsh

# ------------------------
def get_host_info():

   host_hsh = {}

   uname = os.uname()
   host_hsh['hostname'] = uname.nodename
   host_hsh['release']  = uname.release
   host_hsh['machine']  = uname.machine

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
   except Exception as err:
      print("Not supported ",err, file=sys.stderr)

   return host_hsh

# ------------------------
def get_dns_info():

   dns_srv = []
   try:
      fid = open('/etc/resolv.conf', 'r')
      for line in fid:
         columns = line.split()
         if columns[0] == 'nameserver':
            dns_srv.extend(columns[1:])
   except Exception as err:
         print("resolve.comf not found ",err, file=sys.stderr)

   return dns_srv

# ------------------------
def is_dhcp():

   # Surpisingly there is no unified way to determine if the current
   # ip is souced from dhcp or static. Add a series of checks

   # Typical of dhcpcd5 raspberrian debian 9
   if os.path.isfile('/var/lib/dhcpcd5/dhcpcd-eth0.lease'):
      return True

   if os.path.isfile('/run/dhclient-eth0.pid'):
      return True

   return False
