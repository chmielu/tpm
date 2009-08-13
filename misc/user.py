import sys, re, urllib
sys.path.append("../")
from google.appengine.api import images
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from utils import TpmRequestHandler, error, to_html
import models

class UserPage(TpmRequestHandler):
	def get(self, username):
		# TODO need to rewrite this method
		username = urllib.unquote(username)
		if username == str(self.user):
			if not self.profile:
				self.redirect("/user/create"); return
			form_profile = self.profile
		elif self.is_admin:
			form_profile = db.Query(models.Profile).filter("user =", users.User(username)).get()
			if not form_profile:
				self.redirect("/admin/user/new"); return
		else:
			self.redirect("/user/%s/overview" % username); return
		self.misc_render("user.html", form_profile=form_profile, username=username)

class AvatarPage(TpmRequestHandler):
	def get(self, username):
		# TODO need to rewrite this method
		username = urllib.unquote(username)
		if username == str(self.user):
			if not self.profile:
				self.redirect("/user/create"); return
			form_profile = self.profile
		elif self.is_admin:
			form_profile = db.Query(models.Profile).filter("user =", users.User(username)).get()
			if not form_profile:
				self.redirect("/admin/user/new"); return
		else:
			error(self, 403); return
		self.misc_render("user_avatar.html", form_profile=form_profile, username=username)

	def post(self, username):
		username = urllib.unquote(username)
		if username != str(self.user) and not self.is_admin:
			error(self, 403); return
		profile = db.Query(models.Profile).filter("user =", users.User(username)).get()
		if not profile:
			self.redirect("/user/create"); return
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
			self.redirect("/"); return
		if not self.request.get("i_agree"):
			self.misc_render("user_create.html", message="You need to accept rules."); return
		profile = models.Profile(
			user = self.user,
		)
		profile.put()
		self.misc_render("user_profile.html", message="Profile succesfully created. You can edit your basic informations here.", username=self.user)

class OverviewPage(TpmRequestHandler):
	def get(self, username):
		username = urllib.unquote(username)
		profile = db.Query(models.Profile).filter("user =", users.User(username)).get()
		if not profile:
			error(self, 404); return
		self.misc_render("user_overview.html", username=username, profiler=profile)

class ProfilePage(TpmRequestHandler):
	def get(self, username):
		# TODO need to rewrite this method
		username = urllib.unquote(username)
		if username == str(self.user):
			if not self.profile:
				self.redirect("/user/create"); return
			form_profile = self.profile
		elif self.is_admin:
			form_profile = db.Query(models.Profile).filter("user =", users.User(username)).get()
			if not form_profile:
				self.redirect("/admin/user/new"); return
		else:
			error(self, 403); return
		self.misc_render("user_profile.html", form_profile=form_profile, username=username)

	def post(self, username):
		username = urllib.unquote(username)
		if username != str(self.user) and not self.is_admin:
			error(self, 403); return

		if not self.is_admin and (self.request.get("is_member") or self.request.get("is_admin")):
			error(self, 403); return

		profile = db.Query(models.Profile).filter("user =", users.User(username)).get()

		if not profile:
			self.redirect("/user/create"); return

		screenname = self.request.get("screenname")
		if screenname:
			if screenname != profile.screenname:
				if db.Query(models.Profile).filter("screenname =", screenname).get():
					self.misc_render("user_profile.html", message="This screen name is taken.", form_profile=profile, username=username); return
			profile.screenname = screenname
		if self.request.get("realname"):
			profile.realname = self.request.get("realname")
		if self.request.get("is_member"):
			profile.is_member = True
		else:
			profile.is_member = False
		if self.request.get("is_admin"):
			profile.is_admin = True
		else:
			profile.is_admin = False

		profile.put()
		self.redirect("/user/%s/profile" % username)

class SignaturePage(TpmRequestHandler):
	def get(self, username):
		# TODO need to rewrite this method
		username = urllib.unquote(username)
		if username == str(self.user):
			if not self.profile:
				self.redirect("/user/create"); return
			form_profile = self.profile
		elif self.is_admin:
			form_profile = db.Query(models.Profile).filter("user =", users.User(username)).get()
			if not form_profile:
				self.redirect("/admin/user/new"); return
		else:
			error(self, 403); return
		self.misc_render("user_signature.html", form_profile=form_profile, username=username)

	def post(self, username):
		username = urllib.unquote(username)
		if username != str(self.user) and not self.is_admin:
			error(self, 403); return
		profile = db.Query(models.Profile).filter("user =", users.User(username)).get()
		if not profile:
			self.redirect("/user/create"); return
		if self.request.get("delete"):
			profile.signature = profile.signature_html = None
		else:
			profile.signature = self.request.get("signature")
			profile.signature_html = re.sub("<br />$", "", to_html(self.request.get("signature")))
		profile.put()
		self.redirect("/user/%s/signature" % username)

application = webapp.WSGIApplication([
	('/user/create', CreatePage),
	('/user/(.*)/avatar', AvatarPage),
	('/user/(.*)/overview', OverviewPage),
	('/user/(.*)/profile', ProfilePage),
	('/user/(.*)/signature', SignaturePage),
	('/user/(.*)', UserPage),
], debug=True)

if __name__ == "__main__":
	run_wsgi_app(application)
