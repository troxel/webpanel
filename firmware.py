#--------------------------------------
# Firmware Update CallBacks
#--------------------------------------
import cherrypy
from html import escape
from templaterex import TemplateRex
import os
import pprint
import urllib.parse

from webauth  import AuthSession

class FirmwareUpdate(object):

   def __init__(self):

      self.version = 1.0;
      self.upload_dir = '/tmp';
      self.auth = AuthSession(url_login="/webpanel/auth/login")
   
   #--------------------------------------
   @cherrypy.expose
   def upload(self):
      
      self.auth.authorize()
  
      trex = TemplateRex(fname='t_firmware_upload.html')
      return( self.render_layout(trex, locals()) )

   #--------------------------------------
   @cherrypy.expose
   def upload_rtn(self,upload_file):
      
      self.auth.authorize()
            
      # I hate spaces in filenames      
      upload_files.filename(" ", "_")
           
      # Should check for illegal file characters
           
      upload_fspec = os.path.join(self.upload_dir, upload_file.filename)
      with open(upload_fspec, 'wb') as out:
         while True:
         
            # Should be checking the size and being sure it doesn't fill up the upload_dir         
            data = upload_file.file.read(8192)
            if not data:
               break
            out.write(data)
            
      # Do something
      
      # Probably reboot at this point. 
      
      raise cherrypy.HTTPRedirect("/")

   #--------------------------------------
   # Need to make this a util function... 
   def render_layout(self,trex,data_hsh={}):

      data_hsh['version'] = self.version
      data_hsh['user']    = cherrypy.request.login

      if cherrypy.request.login:
         trex.render_sec('logged_in',{'user':cherrypy.request.login})

      trex.render_sec('content',data_hsh)

      return(trex.render(data_hsh))