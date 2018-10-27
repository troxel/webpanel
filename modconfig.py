from pprint import pprint
import os

import sys
sys.path.insert(0,'./packages')
from templaterex import TemplateRex

# Makes configuration changes to OS.

class DHCP:

   # Assumes dhcpcd5 network management...
   # Reference https://www.daemon-systems.org/man/dhcpcd.conf.5.html

   # ------------------------
   def __init__(self, ro_flag=True):
      self.version = 1.0;

      self.ro_flag = ro_flag

   # ------------------------
   def set_static_ip(self):

      trex_dhcpcd = TemplateRex(fname='/etc/dhcpcd-template.conf',cmnt_prefix='##-',cmnt_postfix='-##',dev_mode=True)
      if params['ip_method'] == 'static':
         trex_dhcpcd.render_sec('static_conf',params)

      dhcpcd_file = trex_dhcpcd.render(params)
      return(self.write_file(dhcpcd_file))

   # ------------------------
   def set_dhcp(self):

      trex_dhcpcd = TemplateRex(fname='/etc/dhcpcd-template.conf',cmnt_prefix='##-',cmnt_postfix='-##',dev_mode=True)

      dhcpcd_file_content = trex_dhcpcd.render()
      self.write_sysfile('/etc/dhcpcd.conf',dhcpcd_file_content)

   # ------------------------
   def reboot(self,delay=2):

      os.command( 'showdown -t {} -r -f'.format(delay) )


   # -----------------------
   # Utitility functions
   # -----------------------

   # -----------------------
   # Write file to a ro filesystem
   def write_sysfile(self,fspec,contents):

      # Write to a filesystem that is configured as ro

      rtn = os.system('mount -o rw,remount /')
      if rtn != 0:
         raise FileSysError("Cannot remount rw root partition")

      with open(fspec, 'w+') as fid:
         fid.write(contents)

      os.sync()

      # Leave in a ro state...
      if self.ro_flag:
         rtn = os.system('mount -o ro,remount /')
         if rtn != 0:
            raise FileSysError("Cannot remount ro root partition")
