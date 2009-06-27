import os, sys, datetime, re
sys.path.append("../")
from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app
from utils import *
import models

class MainPage(TpmRequestHandler):
	@administrator
	def get(self):
		self.render("admin_welcome.html")

class NewEntryPage(TpmRequestHandler):
	@administrator
	def get(self):
		self.render("admin_new.html")

	@administrator
	def post(self):
		slug = slugify(self.request.get("title"))
		if self.request.get("slug"):
			slug = self.request.get("slug")
		entry = models.Entry(
			key_name=slug,
			author=users.get_current_user(),
			title=self.request.get("title"),
			slug=slug,
			body=self.request.get("body"),
			body_html=re.sub("<br />$", "", to_html(self.request.get("body")))
		)
		entry.put()
		self.redirect("/entry/" + entry.slug)

class EditEntryPage(TpmRequestHandler):
	@administrator
	def get(self, slug):
		entry = models.Entry.get_by_key_name(slug)
		if not entry:
			error(self, 404); return
		self.render("admin_edit.html", entry=entry)

	@administrator
	def post(self, slug):
		entry = models.Entry.get_by_key_name(slug)
		if not entry:
			error(self, 400, "Don't use this form to add new entries. Thank you."); return
		else:
			if self.request.get("slug") and not self.request.get("slug") == slug:
				slug = self.request.get("slug")
			entry.key_name=slug
			entry.title=self.request.get("title")
			entry.slug=slug
			entry.body = self.request.get("body")
			entry.body_html = re.sub("<br />$", "", to_html(self.request.get("body")))
			entry.updated = datetime.datetime.now()
		entry.put()
		self.redirect("/entry/" + entry.slug)

class DeleteEntryPage(TpmRequestHandler):
	@administrator
	def get(self, slug):
		entry = models.Entry.get_by_key_name(slug)
		if not entry:
			error(self, 404); return
		self.render("admin_delete.html", entry=entry)

	@administrator
	def post(self, slug):
		entry = models.Entry.get_by_key_name(slug)
		if not entry:
			error(self, 404); return
		delete = self.request.get("delete_confirmation")
		if delete and delete == 'yes':
			entry.delete()
		self.redirect('/admin/list')

class ListEntryPage(TpmRequestHandler):
	@administrator
	def get(self):
		entries = db.Query(models.Entry).order('-published').fetch(limit=10)
		for entry in entries:
			entry.published = entry.published.replace(tzinfo=TZINFOS['utc']) 
			entry.published = entry.published.astimezone(CET_tzinfo())
		self.render("admin_list.html", entries=entries)

application = webapp.WSGIApplication([	('/admin', MainPage),
										('/admin/entry/new', NewEntryPage),
										('/admin/entry/edit/(.*)', EditEntryPage),
										('/admin/entry/delete/(.*)', DeleteEntryPage),
										('/admin/entry/list', ListEntryPage),
										('/admin/entry', ListEntryPage),
									], debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()