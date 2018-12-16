import pprint
import os
import os.path
import subprocess
import cherrypy

class Utils:

   # Common utils to mostly handle ro/rw issues and other common needs

   def __init__(self):
      version = 1.0;

   # -----------------------
   # Write file to a ro filesystem
   def write_sysfile(self,fspec,contents):

      # If filesystem is currently ro then umount ro and remount rw
      # Otherwise leave alone

      self.rw()

      with open(fspec, 'w+') as fid:
         fid.write(contents)

      self.ro()

   # ------------------------
   def rw(self):
      rtn = os.system('mount -o rw,remount /')
      if rtn != 0:
         raise SystemError("Cannot remount rw root partition")

   # ------------------------
   def ro(self):

      os.sync() # Forces write from buffer to disk...

      # If the filesystem was originally in ro mode leave in ro mode
      # Otherwise leave alone - a development feature...
      is_ro = self.is_filesys_ro()
      if is_ro:
         rtn = os.system('mount -o ro,remount /')
         if rtn != 0:
            raise SystemError("Cannot remount ro root partition")

   # ------------------------
   def is_filesys_ro(self):

      rtn = os.system('egrep "\sro[\s,]" /proc/mounts | egrep "\s+/\s+"')
      if rtn == 0:
         return(True)
      else:
         return(False)

   # ------------------------
   def rm_dir(self,dspec):

      cnt = dspec.count("/")
      if cnt < 2:
         print("Refusing to remove low level directory {}".format(dspec), file=sys.stderr)
         return(False)

      self.rw()
      rtn = os.system('rm {}'.format(dspec))
      self.ro()

      if rtn == 0:
         return(True)
      else:
         return(False)

   # ------------------------
   def url_gen(self,path,from_page=''):
      # Cannot do relative url redirects when working with proxy
      # as cherrpy isn't aware of the protocol   
      
      host = cherrypy.request.headers.get('Host')
      proto = cherrypy.request.headers.get('X-Scheme') 
      if proto is None: proto = 'http' 
      
      if from_page:
         from_page = "?from_page={}".format(from_page)
      
      url = "{}://{}{}{}".format(proto,host,path,from_page)
      return(url)
      
         