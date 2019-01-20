#!/usr/bin/python3

import os
from templaterex import TemplateRex
import time
import subprocess
import re

# Config parameters
ifname = 'eth0'

import socket
hostname = socket.gethostname()
fqdn     = socket.getfqdn(hostname)
ip_addr   = socket.gethostbyname(hostname)

# Get ethernet interface ip addr
ip_addr_iface = ''
rtn = subprocess.check_output(['ifconfig',ifname],stderr=subprocess.STDOUT)
pattern = "inet addr:(\S+)".encode()
match = re.search(pattern,rtn)
if match:
   ip_addr_iface = match.group(1).decode()

print("hostname = {}\nip_addr = {}".format(hostname,ip_addr))
print("ip_addr_iface = {}\n".format(ip_addr_iface))

trex = TemplateRex(fname='openssl-template.ini',cmnt_prefix='##-',cmnt_postfix='-##',dev_mode=True)

hsh = {}
hsh['dir_root'] = '.'
hsh['countryName'] = "US"
hsh['organizationName'] = "IoT Embedded"
hsh['commonName'] = "webpanel"

hsh['ip_lst'] = [ ip_addr,ip_addr_iface, "127.0.0.1" ]
hsh['dns_lst'] = [ hostname, fqdn ]

for inx,ip in enumerate(hsh['ip_lst']):
   if ip:
      trex.render_sec('alt_name_ip',{'inx':inx,'ip':ip})

for inx,dns in enumerate(hsh['dns_lst']):
   trex.render_sec('alt_name_dns',{'inx':inx,'dns':dns})

out = trex.render(hsh)

fid = open('openssl_cert.ini','w+')
fid.write(out)
fid.close()

# Generating key first and then csr did not work
# Do in one pass...
#cmd = "openssl genrsa -out ./webpanel.key 2048"
#rtn = os.system(cmd)
#if rtn:
#   raise
#print("keygen rtn = ",rtn)

# House cleaning... get a db error if newcerts doesn't exist/not empty
# we don't care about crl
os.system('mkdir ./newcerts')
os.system('rm ./newcerts/*')

fid = open('index.txt','w+')
fid.close()

fid = open('serial','w+')
fid.write(str(int(time.time())))
fid.close()

cmd = "openssl req -verbose -config openssl_cert.ini -newkey rsa:2048 -nodes -keyout webpanel.key  -out webpanel.csr -batch"
rtn = os.system(cmd)
if rtn:
   raise

print("csr rtn = ",rtn)

cmd = "chmod 600 ./webpanel.key"
rtn = os.system(cmd)

# Finally sign CSR and make server cert
cmd = "openssl ca -config openssl_cert.ini -batch -in webpanel.csr -out webpanel.crt"
rtn = os.system(cmd)
print("cert! rtn = ",rtn)

os.system('rm ./*.old')
