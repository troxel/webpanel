
Steps to ro root partition... 

Raspberry PI

Some files are dynamically created in /etc 
and /var that need links to so that the os 
can write to them

ln -s /var/lib/dhcpcd5/dhcpcd-eth0.lease /tmp

ln -s /run/resolvconf/interfaces/eth0.dhcp /etc/resolv.conf

