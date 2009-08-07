from google.appengine.ext import db

class Entry(db.Model):
	author = db.UserProperty()
	title = db.StringProperty(required=True)
	slug = db.StringProperty(required=True)
	body = db.TextProperty(required=True)
	body_html = db.TextProperty()
	updated = db.DateTimeProperty(auto_now=True)
	published = db.DateTimeProperty(auto_now_add=True)

class Category(db.Model):
	title = db.CategoryProperty(required=True)
	desc = db.StringProperty()
	slug = db.CategoryProperty(required=True)
	topics = db.IntegerProperty(default=0)
	posts = db.IntegerProperty(default=0)

class Post(db.Model):
	user = db.UserProperty(auto_current_user_add=True)
	title = db.StringProperty(required=True)
	content = db.TextProperty(required=True)
	content_html = db.TextProperty()
	date = db.DateTimeProperty(auto_now_add=True)
	category = db.ReferenceProperty(Category)
	topic_id = db.CategoryProperty()
	sticky = db.BooleanProperty(default=False)
	closed = db.BooleanProperty(default=False)

class Profile(db.Model):
	user = db.UserProperty(required=True)
	screenname = db.StringProperty()
	realname = db.StringProperty()
	is_member = db.BooleanProperty(default=False)
	is_admin = db.BooleanProperty(default=False)
	avatar = db.BlobProperty()
	signature = db.TextProperty()
	signature_html = db.TextProperty()