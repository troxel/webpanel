import pprint
import os
import re

import sys

from commonutils import Utils
from templaterex import TemplateRex

# Makes configuration changes to OS.

class DHCP(Utils):

   # Assumes dhcpcd5 network management...
   # Reference https://www.daemon-systems.org/man/dhcpcd.conf.5.html
  
   # ------------------------
   def __init__(self):
      self.version = 1.0
     
      # Use a hash since there are a lot parameters including search path  
      self.template_args = {}
      self.template_args['template_dirs'] = ['./templates_sys','/etc']
      self.template_args['cmnt_prefix']   = '##-'
      self.template_args['cmnt_postfix']  = '-##'
      self.template_args['dev_mode'] = True
 
      Utils.__init__(self)

   # ------------------------
   def set_static(self,params):

      self.template_args['fname'] = 'dhcpcd-template.conf'
      trex_dhcpcd = TemplateRex(**self.template_args)

      if params['ip_method'] == 'static':
         trex_dhcpcd.render_sec('static_conf',params)

      dhcpcd_file_content = trex_dhcpcd.render(params)
      return(self.write_sysfile('/etc/dhcpcd.conf',dhcpcd_file_content))

   # ------------------------
   def set_dhcp(self):

      self.template_args['fname'] = 'dhcpcd-template.conf'
      trex_dhcpcd = TemplateRex(**self.template_args)

      dhcpcd_file_content = trex_dhcpcd.render()
      self.write_sysfile('/etc/dhcpcd.conf',dhcpcd_file_content)

   # ------------------------
   def set_hostname(self, hostname, ip):

      self.write_sysfile('/etc/hostname',hostname)

      # Write to host file
      self.template_args['fname'] = 'hosts-template'
      trex_hosts = TemplateRex(**self.template_args)
      trex_hosts.render_sec('hostname',{'ip':ip,'hostname':hostname})
      host_content = trex_hosts.render()
      self.write_sysfile('/etc/hosts',host_content)

   # ------------------------
   def set_ntp_server(self, ntp_server=""):

      self.template_args['fname'] = 't-ntp.conf.dhcp'
      trex_ntp = TemplateRex(**self.template_args)

      if ntp_server:
         trex_ntp.render_sec('server_blk',{'ntp_server':ntp_server})

      ntp_content = trex_ntp.render()
      self.write_sysfile('/etc/ntp.conf',ntp_content)
      os.system( 'systemctl restart ntp' )

   # ------------------------
   def reboot(self,delay='now'):

      os.system( '/sbin/shutdown -r {}'.format(delay) )
