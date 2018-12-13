# webpanel

Provide generic web interface to facilitate setting network and related parameters for embedded linux and creating and installing a self-signed certificate.

# Screen Shots

![Home Page](docs/img/index.jpg "Home Page")

---

![Home Page](docs/img/netconf.jpg "Net Configure")

---

![Home Page](docs/img/sslcert.jpg "SSL Cert Info")


# SSL Configuration

A self-signed CA is generated in the ./cert directory. This CA is
downloadable on the sslcert page. Install this cert in the trusted
certificate store of the client system.

There is a command line tool

create_CA_cert.py

That will recreate a new CA cert. After install run create_CA_cert.py

A new server cert should be created from the sslcert page which
will create and install a new server with the parameters entered for the
common name.  With in place and the CA installed in the trusted store you
should have warning-free ssl access.  The new cert is a v3 x509 cert.

# Authentication

User Names and Passwords are stored in an Apache style htpasswd file.
Presently there is not web forms to CRUD user/passwords. A TBD. The
htpasswd file can be managed via the htpasswd file on the command line.
Default credentials is user/pass = root/root

Authentication uses a session cookie and obviously only makes sense in
a ssl environment.

Any callback that you want to add and want to protect it with a login
just add at beginning of the callback:

self.auth.authorize()


# Misc config file notes:

## filesystem read only 'ro' and read write 'rw' mode.

All file writes and files system actions are handled by commonutils.py.

If the status of the root file system at start up is 'ro' then all changes
to the file system will change the status to 'rw' mode and then back to 'ro'
mode when done.

If the status of the root files system at start is 'rw' then all changes
will leave the file system in 'rw'. This is useful for development.

## NGINX

An example nginx config file is given in the setup directory. nginx
provides for ssl (as cherrypy ssl implimentation is broken) and allows
you to integrate other apps.

## unit-files

Example unit-files are in the setup directory. Note that unit files
are configured to restart if app quits. This means that to run on the
command line you have stop the service and then run from from the command
line. That is:

>systemctl stop webpanel
>cd /opt/webpanel
>./webpanel.py

Also the unit file runs the webpanel in quiet mode.


## DEV_MODE

If a file DEV_MODE exists in webpanel directory then template renders
will include the source of the templates in the output.

# Dependencies

Python3

Python Modules

pip3 install distro
pip3 install netifaces
pip3 install netaddr
pip3 install cryptography
pip3 install TemplateRex
pip3 install platform


Linux modules

apt-get install dhcpcd5
apt-get install apache2-utils  # <--- htpasswd utility

apt-get remove conmann
