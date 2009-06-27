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
	title = db.CategoryProperty()
	desc = db.StringProperty()
	slug = db.CategoryProperty()
	topics = db.IntegerProperty(default=0)
	posts = db.IntegerProperty(default=0)

class Post(db.Model):
	user = db.UserProperty(auto_current_user_add = True)
	title = db.StringProperty()
	content = db.TextProperty()
	content_html = db.TextProperty()
	date = db.DateTimeProperty(auto_now_add=True)
	category = db.ReferenceProperty(Category)
	topic_id = db.CategoryProperty()