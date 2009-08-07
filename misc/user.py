import sys, urllib
sys.path.append("../")
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import images
from utils import TpmRequestHandler, error
import models

class UserPage(TpmRequestHandler):
	def get(self, username):
		# TODO need to rewrite this method
		username = urllib.unquote(username)
		if username == str(self.user):
			if not self.profile:
				self.redirect("/user/create")
			form_profile = self.profile
		elif self.is_admin:
			form_profile = db.Query(models.Profile).filter("user =", users.User(username)).get()
			if not form_profile:
				self.redirect("/admin/user/new")
		else:
			self.misc_render("user_overview.html", username=username); return
		self.misc_render("user.html", form_profile=form_profile, username=username)

class AvatarPage(TpmRequestHandler):
	def get(self, username):
		# TODO need to rewrite this method
		username = urllib.unquote(username)
		if username == str(self.user):
			if not self.profile:
				self.redirect("/user/create")
			form_profile = self.profile
		elif self.is_admin:
			form_profile = db.Query(models.Profile).filter("user =", users.User(username)).get()
			if not form_profile:
				self.redirect("/admin/user/new")
		else:
			error(self, 403); return
		self.misc_render("user_avatar.html", form_profile=form_profile, username=username)

	def post(self, username):
		username = urllib.unquote(username)
		if username != str(self.user) and not self.is_admin:
			error(self, 403); return
		profile = db.Query(models.Profile).filter("user =", users.User(username)).get()
		if not profile:
			self.redirect("/user/create")
		if self.request.get("delete"):
			profile.avatar = None
		else:
			profile.avatar = images.resize(self.request.get("avatar"), 60, 60)
		profile.put()
		self.redirect("/user/%s/avatar" % username)

class CreatePage(TpmRequestHandler):
	def get(self):
		if self.profile:
			error(self, 403); return
		self.misc_render("user_create.html", username=self.user)
	
	def post(self):
		if self.profile:
			error(self, 403); return
		if self.request.get("no_thanks"):
			self.redirect("/")
		if not self.request.get("rules_accepted"):
			self.misc_render("user_create.html", message="You need to accept rules."); return
		if db.Query(models.Profile).filter("user =", self.user).get():
			self.misc_render("user_create.html", message="This screen name is taken."); return
		profile = models.Profile(
			user = self.user,
		)
		profile.put()
		
		# FIXME add some informations here
		self.misc_render("user_profile.html", message="Profile succesfully created. You can edit your basic informations here.")

class ProfilePage(TpmRequestHandler):
	def get(self, username):
		# TODO need to rewrite this method
		username = urllib.unquote(username)
		if username == str(self.user):
			if not self.profile:
				self.redirect("/user/create")
			form_profile = self.profile
		elif self.is_admin:
			form_profile = db.Query(models.Profile).filter("user =", users.User(username)).get()
			if not form_profile:
				self.redirect("/admin/user/new")
		else:
			error(self, 403); return
		self.misc_render("user_profile.html", form_profile=form_profile, username=username)

	def post(self, username):
		username = urllib.unquote(username)
		if username != str(self.user) and not self.is_admin:
			error(self, 403); return
		profile = db.Query(models.Profile).filter("user =", users.User(username)).get()
		screenname = self.request.get("screenname")

		if not profile:
			self.redirect("/user/create")
		
		if screenname != profile.screenname:
			if db.Query(models.Profile).filter("screenname =", screenname).get():
				self.misc_render("user_profile.html", message="This screen name is taken."); return
		profile.screenname = screenname
		profile.put()
		self.redirect("/user/%s/profile" % username)

class SignaturePage(TpmRequestHandler):
	def get(self, username):
		self.misc_render("user_signature.html")

	def post(self, username):
		self.redirect("/user/signature")

application = webapp.WSGIApplication([
	('/user/create', CreatePage),
	('/user/(.*)/avatar', AvatarPage),
	('/user/(.*)/profile', ProfilePage),
	('/user/(.*)/signature', SignaturePage),
	('/user/(.*)', UserPage),
], debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()
