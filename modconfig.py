from pprint import pprint
import os
import re

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
   def set_static(self,params):

      trex_dhcpcd = TemplateRex(fname='/etc/dhcpcd-template.conf',cmnt_prefix='##-',cmnt_postfix='-##',dev_mode=True)
      if params['ip_method'] == 'static':
         trex_dhcpcd.render_sec('static_conf',params)

      dhcpcd_file_content = trex_dhcpcd.render(params)
      return(self.write_sysfile('/etc/dhcpcd.conf',dhcpcd_file_content))

   # ------------------------
   def set_dhcp(self):

      trex_dhcpcd = TemplateRex(fname='/etc/dhcpcd-template.conf',cmnt_prefix='##-',cmnt_postfix='-##',dev_mode=True)

      dhcpcd_file_content = trex_dhcpcd.render()
      self.write_sysfile('/etc/dhcpcd.conf',dhcpcd_file_content)

   # ------------------------
   def set_hostname(self, hostname, ip):

      self.write_sysfile('/etc/hostname',hostname)

      # Write to host file
      trex_hosts = TemplateRex(fname='/etc/hosts-template',cmnt_prefix='##-',cmnt_postfix='-##',dev_mode=True)
      trex_hosts.render_sec('hostname',{'ip':ip,'hostname':hostname})
      host_content = trex_hosts.render()
      self.write_sysfile('/etc/hosts',host_content)

   # ------------------------
   def set_ntp_server(self, ntp_server=""):

      trex_ntp = TemplateRex(fname='t-ntp.conf.dhcp',cmnt_prefix='##-',cmnt_postfix='-##',dev_mode=True)

      if ntp_server:
         trex_ntp.render_sec('server_blk',{'ntp_server':ntp_server})

      ntp_content = trex_ntp.render()
      self.write_sysfile('/etc/ntp.conf',ntp_content)
      os.system( 'systemctl restart ntp' )

   # ------------------------
   def reboot(self,delay='now'):

      os.system( '/sbin/shutdown -r {}'.format(delay) )

   # -----------------------
   # Utitility functions
   # -----------------------

   # -----------------------
   # Write file to a ro filesystem
   def write_sysfile(self,fspec,contents):

      # Write to a filesystem that is configured as ro

      rtn = os.system('mount -o rw,remount /')
      if rtn != 0:
         raise SystemError("Cannot remount rw root partition")

      with open(fspec, 'w+') as fid:
         fid.write(contents)

      os.sync()

      # Leave in a ro state...
      if self.ro_flag:
         rtn = os.system('mount -o ro,remount /')
         if rtn != 0:
            raise SystemError("Cannot remount ro root partition ",rtn)
