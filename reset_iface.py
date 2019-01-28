#!/usr/bin/python3

import pprint
import os
import modconfig

# Single purpose script to reset inteface

wpath = '/opt/webpanel'

os.chdir(wpath)

modconf = modconfig.DHCP()
modconf.set_dhcp()
os.system( '/sbin/reboot' )
