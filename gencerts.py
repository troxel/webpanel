#!/usr/bin/python3

import os
from templaterex import TemplateRex
import time
import ssl
import subprocess
import sys

from commonutils import Utils

class GenCerts(Utils):

   #-----------------------------------------------
   def __init__(self,dir_root='./cert'):

      self.dir_root = dir_root
      self.error_msg = ""
      Utils.__init__(self)

   #-----------------------------------------------
   def gen_server_cert(self,subj_hsh,ip_lst=[],dns_lst=[]):

      # subj_hsh should contain: 'countryName','organizationName','commonName'

      fspec_template = os.path.join(self.dir_root,'openssl-template.ini')
      trex = TemplateRex(fname=fspec_template,template_dirs=['.'],cmnt_prefix='##-',cmnt_postfix='-##',dev_mode=True)

      for inx,ip in enumerate(ip_lst):
         if not ip: continue
         trex.render_sec('alt_name_ip',{'inx':inx,'ip':ip})

      for inx,dns in enumerate(dns_lst):
         if not dns: continue
         trex.render_sec('alt_name_dns',{'inx':inx,'dns':dns})

      subj_hsh['dir_root'] = self.dir_root

      ini_out = trex.render(subj_hsh)

      fspec_ini = os.path.join(self.dir_root,'openssl_cert.ini')
      self.write_sysfile(fspec_ini,ini_out)

      # House cleaning... gets a db error if doen't do this
      # we don't care about crl - remove the contents of newcerts
      fspec_newcert = os.path.join(self.dir_root,'newcerts/*')
      self.rm_dir(fspec_newcert)

      # An index file needs to be present
      fspec_index = os.path.join(self.dir_root,'index.txt')
      self.write_sysfile(fspec_index,'')

      fspec_serial = os.path.join(self.dir_root,'serial')
      self.write_sysfile(fspec_serial, str( int(time.time() )) )

      # Generate private key and csr
      fspec_key = os.path.join(self.dir_root,'webpanel.key')
      fspec_csr = os.path.join(self.dir_root,'webpanel.csr')
      ##cmd = "openssl req -verbose -config openssl_cert.ini -newkey rsa:2048 -nodes -keyout webpanel.key  -out webpanel.csr -batch"

      # Wrap the following system call in file system rw/ro
      self.rw()

      cmd = "openssl req -verbose -config {} -newkey rsa:2048 -nodes -keyout {} -out {} -batch".format(fspec_ini,fspec_key,fspec_csr)

      rtn = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      out,err = rtn.communicate()
      #print(">>>>>",out)
      #print(">>>>>",err)
      #rtn = os.system(cmd)
      #if rtn:
      #   raise SystemError('openssl cmd error')

      chmod_cmd = "chmod 600 {}".format(fspec_key)
      rtn = os.system(chmod_cmd)

      # Finally sign CSR and generate server cert
      fspec_crt = os.path.join(self.dir_root,'webpanel.crt')
      options = "ca -config {} -batch -in {} -out {}".format(fspec_ini,fspec_csr,fspec_crt)
      cmd_lst = ['openssl',"ca","-config",fspec_ini,"-batch","-in",fspec_csr,"-out",fspec_crt]

      try:
        rtn = subprocess.check_output(cmd_lst, stderr=subprocess.STDOUT)
      except subprocess.CalledProcessError as e:
          self.error_msg = e.output.decode(sys.getfilesystemencoding())
          self.ro()
          return(False)

      self.ro()

      return(True)

   #-----------------------------------------------
   def gen_CA_cert(subj_hsh):
      # later... not sure if need a web CA cert generatioin.
      pass;

   # -----------------------------------------
   # utility function to decode struct to more useful hash
   def parse_cert(self,fname):

      # Set up return hash
      cert_hsh = {}
      cert_hsh['subject'] = {}
      cert_hsh['subjectAltName'] = {}
      cert_hsh['subjectAltName']['ip_lst'] = []
      cert_hsh['subjectAltName']['dns_lst'] = []

      # Using undocumented stealth function in the ssl lib
      # in retrospect might have been easier to do our own parse
      try:
         fspec = os.path.join(self.dir_root,fname)

         cert_struct = ssl._ssl._test_decode_cert(fspec)

      except:
         return cert_hsh

      ##pprint.pprint(cert_struct)

      # subjectAltName not in CA cert and v1 certs
      if 'subjectAltName' in cert_struct:
         for san in cert_struct['subjectAltName']:
            if san[0] == 'IP Address':
               cert_hsh['subjectAltName']['ip_lst'].append(san[1])
            elif san[0] == 'DNS':
               cert_hsh['subjectAltName']['dns_lst'].append(san[1])

      for subj in cert_struct['subject']:
         cert_hsh['subject'][subj[0][0]] = subj[0][1]

      cert_hsh['issuer_commonName'] = cert_struct['issuer'][4][0][1]
      cert_hsh['valid_to']   = cert_struct['notAfter']
      cert_hsh['valid_from'] = cert_struct['notBefore']

      return cert_hsh
