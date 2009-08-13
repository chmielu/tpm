import os, sys, datetime
sys.path.append("../")
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app
from utils import TpmRequestHandler, error
import models

class MainPage(TpmRequestHandler):
	def get(self):
		entries = db.Query(models.Entry).order('-published').fetch(limit=5)
		for entry in entries:
			if entry.updated > entry.published+datetime.timedelta(seconds=30):
				entry.it_was_updated = True
		self.render("index.html", entries=entries)

class EntryPage(TpmRequestHandler):
	def get(self, entry_slug):
		entry = db.Query(models.Entry).filter("slug =", entry_slug).get()
		if not entry:
			error(self, 404, "Couldn't find entry you requested. Sorry."); return
		if entry.updated > entry.published+datetime.timedelta(seconds=30):
			entry.it_was_updated = True
		self.render("entry.html", entry=entry)

application = webapp.WSGIApplication([	('/', MainPage),
										('/entry/(.*)', EntryPage),
									], debug=True)

if __name__ == "__main__":
	run_wsgi_app(application)
