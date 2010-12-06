from google.appengine.ext import db

class User(db.Expando):
	name = db.StringProperty()
	oauth_key = db.StringProperty()
	oauth_secret = db.StringProperty()
	access_key = db.StringProperty()
	access_secret = db.StringProperty()
	
class Temp(db.Expando):
	oauth_key = db.StringProperty()
	oauth_secret = db.StringProperty()
	access_key = db.StringProperty()
	access_secret = db.StringProperty()