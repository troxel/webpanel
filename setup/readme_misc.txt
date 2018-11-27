1. Webpanel service

Copy webpanel.service to the systemd directory

>cp -a webpanel.service /etc/systemd/system/

Then
 
>/opt/webpanel/setup# systemctl enable webpanel

Note you will have to stop the service if you want to start webpanel from the command line
as the unit-file when developing

>systemctl stop webpanel 

Then run from the command line to get logging to the screen and restart on edit. 



2. Copy original ntp.conf

Selecting static network overwrite the static ntp.conf, keep the original around for debuging later 
if needed. 

>cp -a /etc/ntp.conf /etc/ntp.conf.orig
