from gaesessions import SessionMiddleware

# suggestion: generate your own random key using os.urandom(64)
import os
COOKIE_KEY = '$\xf4\x85\x9e\x04\x91\x1a\x07*\xa7e\x13af\xde\xc9g+lH\x94\xf2^Q=\xe96\x7f\xe3\x1b\x08\xed\xb7\x12\x8eb\xebZ\x1d\x113\rB\xc4\xad\xaeR\xdf\xa6I\x07\xb0\xe5\xb2\xa3D\xef3{j\xbf\x85\xdc\xc2'

def webapp_add_wsgi_middleware(app):
  from google.appengine.ext.appstats import recording
  app = SessionMiddleware(app, cookie_key=COOKIE_KEY)
  app = recording.appstats_wsgi_middleware(app)
  return app
