#!/usr/bin/python3

import os
from templaterex import TemplateRex
import time

trex = TemplateRex(fname='openssl-template.ini',cmnt_prefix='##-',cmnt_postfix='-##',dev_mode=True)

hsh = {}
hsh['countryName'] = "US"
hsh['organizationName'] = "IoT Embedded"
hsh['commonName'] = "webpanel"

hsh['ip_lst'] = [ "130.46.82.68", "127.0.0.1" ]
hsh['dns_lst'] = [ "RaspberryPI-2", "RaspberryPI-2.nswccd.navy.mil" ]

for inx,ip in enumerate(hsh['ip_lst']):
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

# House cleaning... gets a db error if doen't do this
# we don't care about crl
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
