#--------------------------------------
# Auth CallBacks
#--------------------------------------
import cherrypy
from html import escape
from templaterex import TemplateRex
import os
import pprint

from passlib.apache import HtpasswdFile

class AuthSession(object):

   def __init__(self,session_key='auth_session',url_login='/auth/login/',htpasswd='/opt/webpanel/htpasswd'):

      self.version = 1.0;
      self.url_login = url_login;
      self.SESSION_KEY = session_key
      self.htpasswd = htpasswd

   #--------------------------------------
   @cherrypy.expose
   def login(self, username="", password="", from_page="/"):

      username = escape(username)
      password = escape(password)
      from_page = escape(from_page)

      if username and password:
         msg = self.check_credentials(username, password)
         if msg == True:
            cherrypy.session[self.SESSION_KEY] = cherrypy.request.login = username

            # Need to do a redirect to set session
            # Had to add the host as just using /url/path would somehow add a "/" so we got "//"
            url_redirect = "https://{}{}".format(cherrypy.request.headers.get('Host'),from_page)
            raise cherrypy.HTTPRedirect(url_redirect)

      url_login = self.url_login
      trex = TemplateRex(fname='t_loginform.html')
      return( trex.render(locals()) )

   #--------------------------------------
   @cherrypy.expose
   def logout(self, from_page="/"):
       sess = cherrypy.session
       username = sess.get(self.SESSION_KEY, None)
       sess[self.SESSION_KEY] = None
       if username:
           cherrypy.request.login = None

       if len(from_page) > 1:
          from_page = "https://{}{}".format(cherrypy.request.headers.get('Host'),from_page)

       raise cherrypy.HTTPRedirect(from_page or "/")

   # --------------------------------------------
   # utility functions
   # --------------------------------------------

   # Include this at top of function to protect...
   def authorize(self):

      username = cherrypy.session.get(self.SESSION_KEY)
      if username:
         cherrypy.request.login = username
      else:
         path_rel = cherrypy.request.path_info
         ##raise cherrypy.InternalRedirect(self.url_login,query_string="from_page={}".format(path_rel))
         raise cherrypy.HTTPRedirect("{}?from_page={}".format(self.url_login,path_rel) )

      return(username)

   # --------------------------------------------
   # check credentials...
   def check_credentials(self, username, password):
       """ Need to make this file based. """

       if os.path.isfile(self.htpasswd):
          ht = HtpasswdFile(self.htpasswd)
          if ht.check_password(username,password):
             return(True)
          else:
             return( u"Incorrect username or password." )

       return( u"Htpasswd file was not found " )
