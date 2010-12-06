#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#	  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

import os

from dropbox import auth, client, rest
from config import config
import logging
from models import User, Temp

from oauth import oauth

from gaesessions import get_current_session

try:
	import json
except Exception, e:
	from django.utils import simplejson as json

def get_session(decoratedFunction):
	def wrapper(self):
		session = get_current_session()
		logging.info(session)
		if not hasattr(self, 'd'):
			self.d = {'session' : session }
		else:
			self.d['session'] = session
		decoratedFunction(self)
	return wrapper
	
def check_login(decoratedFunction):
	@get_session
	def wrapper(self):
		if 'user' in self.d['session']:#hasattr(self.d['session'],'user'):
			decoratedFunction(self)
		else:
			self.redirect('/')
	return wrapper
	
class MainHandler(webapp.RequestHandler):
	@get_session
	def get(self):
		self.d = {}
		path = os.path.join(os.path.dirname(__file__), 'templates/home.html')
		self.response.out.write(template.render(path,{'data':self.d}))

	@get_session
	def post(self):
		user = Temp()
		acc = auth.Authenticator(config['auth'])
		token = acc.obtain_request_token()
		logging.info(token.__dict__)
		user.oauth_key = token.key
		user.oauth_secret = token.secret
		user.put()
		self.redirect(acc.build_authorize_url(token,'https://dropboxplayer.appspot.com/oauth_callback'))

class OauthCallback(webapp.RequestHandler):
	@get_session
	def post(self):
		self.get()

	@get_session
	def get(self):
		if self.request.get('oauth_token', None) is not None:
			user = Temp.all().filter('oauth_key =',self.request.get('oauth_token')).get()
			if user is not None:
				acc = auth.Authenticator(config['auth'])
				token = oauth.OAuthToken(user.oauth_key,user.oauth_secret)
				access_token = acc.obtain_access_token(token,'')
				logging.info(access_token.__dict__)
				user.access_key = access_token.key
				user.access_secret = access_token.secret
				user.put()

				self.d['session'].regenerate_id()
				self.d['session']['user'] = user
				self.redirect('/home')

class ChooseFolder(webapp.RequestHandler):
	@check_login
	def get(self):
		path = ''
		if self.request.get('path',None):
			path = self.request.get( 'path' )
		access_token = oauth.OAuthToken(self.d['session']['user'].access_key,self.d['session']['user'].access_secret)
		acc = auth.Authenticator(config['auth'])
		client_acc = client.DropboxClient(config['auth']['server'],config['auth']['content_server'],config['auth']['port'],acc,access_token)
		self.d['files'] = client_acc.metadata("dropbox",path).body
		files = json.loads(self.d['files'])['contents']
		f_list = []
		for f in files:
			if f['is_dir']:
				f_list.append((f['path'],f['path'].split('/')[-1]))
		f_list.sort( key = lambda x : x[1] )
		logging.info(f_list)
		self.d['file_list'] = f_list
		path = os.path.join(os.path.dirname(__file__), 'templates/folder.html')
		self.response.out.write(template.render(path,{'data':self.d}))

class Player(webapp.RequestHandler):
	@check_login
	def get(self):
		path = self.request.get('path', None)
		if path is not None:
			access_token = oauth.OAuthToken(self.d['session']['user'].access_key,self.d['session']['user'].access_secret)
			acc = auth.Authenticator(config['auth'])
			client_acc = client.DropboxClient(config['auth']['server'],config['auth']['content_server'],config['auth']['port'],acc,access_token)
			f_list = []
			self.d['files'] = json.loads(client_acc.metadata("dropbox",path).body)['contents']
			for f in self.d['files']:
				if not f['is_dir'] and (f['path'].split('/')[-1].split('.')[-1].lower() == 'mp3' or f['path'].split('/')[-1].split('.')[-1].lower() == 'm4a' ): 
					f_name = f['path'].split('/')[-1]
					f_type = f_name.split('.')[-1]
					f_list.append((f['path'],f_name,f_type))
			f_list.sort(key = lambda x: x[1])
			self.d['file_list'] = f_list
			path = os.path.join(os.path.dirname(__file__), 'templates/player.html')
			self.response.out.write(template.render(path,{'data':self.d}))
			
class GetFile(webapp.RequestHandler):
	@check_login
	def get(self):
		path = self.request.get('path',None)
		if path is not None:
			access_token = oauth.OAuthToken(self.d['session']['user'].access_key,self.d['session']['user'].access_secret)
			acc = auth.Authenticator(config['auth'])
			client_acc = client.DropboxClient(config['auth']['server'],config['auth']['content_server'],config['auth']['port'],acc,access_token)
			read_file = client_acc.get_file("dropbox",path)
			if path.split('/')[-1].split('.')[-1].lower() == 'mp3':
				self.response.headers['Content-Type'] = 'audio/mpeg'
			else:
				self.response.headers['Content-Type'] = 'audio/mp4'
			self.response.out.write(read_file.read())

class Logout(webapp.RequestHandler):
	@get_session
	def get(self):
		try:
			session = get_current_session()
			session.terminate()
		except:
			pass
		self.redirect('/')
		
def main():
	application = webapp.WSGIApplication([
											('/', MainHandler),
											('/oauth_callback',OauthCallback),
											('/player.*',Player),
											('/file.*',GetFile),
											('/home',ChooseFolder),
											('/logout',Logout)
										],
										 debug=True)
	util.run_wsgi_app(application)


if __name__ == '__main__':
	main()
