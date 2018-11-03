#!/usr/bin/python3

import os
from templaterex import TemplateRex

trex = TemplateRex(fname='openssl-template.ini',cmnt_prefix='##-',cmnt_postfix='-##',dev_mode=True)

hsh = {}
hsh['countryName'] = "US"
hsh['stateName'] = "ID"
hsh['organizationName'] = "IoT Embedded"
hsh['commonName'] = "WebpanelCA"


#hsh['dns1'] = "130.46.82.68"
#hsh['dns2'] = "RaspberryPI-2"

# To keep alt names happy.. not really used in CA
trex.render_sec('alt_name_ip',{'inx':0,'ip':'127.0.0.1'})
trex.render_sec('alt_name_dns',{'inx':0,'dns':'localhost'})


out = trex.render(hsh)
fid = open('opensslCA.ini','w+')
fid.write(out)
fid.close()

# Create private key
cmd = "openssl genrsa -out ./webpanelCA.key 2048"
rtn = os.system(cmd)
print("keygen rtn = ",rtn)

cmd = "chmod 600 ./webpanelCA.key"
rtn = os.system(cmd)

# Create CA cert
cmd = "openssl req -new -batch -x509 -config opensslCA.ini -nodes -days 12000 -key webpanelCA.key -out webpanelCA.crt"
rtn = os.system(cmd)
print("CA cert rtn = ",rtn)
