import os, sys, datetime
sys.path.append("../")
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app
from utils import *
import models

class MainPage(TpmRequestHandler):
	def get(self):
		entries = db.Query(models.Entry).order('-published').fetch(limit=5)
		for entry in entries:
			if entry.updated > entry.published+datetime.timedelta(seconds=30):
				entry.it_was_updated = True
			entry.published = entry.published.replace(tzinfo=TZINFOS['utc']) 
			entry.published = entry.published.astimezone(CET_tzinfo())
		self.render("index.html", entries=entries)

class LoginHandler(TpmRequestHandler):
    def get(self):
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        else:
            self.redirect('/')

class LogoutHandler(TpmRequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.redirect(users.create_logout_url('/'))
        else:
            self.redirect('/')

class FeedPage(TpmRequestHandler):
	def get(self):
		entries = db.Query(models.Entry).order("-published").fetch(limit=10)
		if entries:
			latest = entries[0]
		else:
			latest = None
		self.response.headers['Content-Type'] = 'application/atom+xml'
		self.render("templates/atom.xml", entries=entries, latest=latest)

class ChatPage(TpmRequestHandler):
	def get(self):
		nickname=str(users.get_current_user()).split("@")[0]
		self.render("chat.html", nickname=nickname)

class EntryPage(TpmRequestHandler):
	def get(self, entry_slug):
		entry = db.Query(models.Entry).filter("slug =", entry_slug).get()
		if not entry:
			error(self, 404, "Couldn't find entry you requested. Sorry."); return
		if entry.updated > entry.published+datetime.timedelta(seconds=30):
			entry.it_was_updated = True
		entry.published = entry.published.replace(tzinfo=TZINFOS['utc']) 
		entry.published = entry.published.astimezone(CET_tzinfo())
		self.render("entry.html", entry=entry)

class ErrorPage(TpmRequestHandler):
	def get(self, anything):
		error(self, 404)

application = webapp.WSGIApplication([	('/', MainPage),
										('/login', LoginHandler),
										('/logout', LogoutHandler),
										('/chat', ChatPage),
										('/entry/(.*)', EntryPage),
										('/feed', FeedPage),
										('/(.*)', ErrorPage),
									], debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()