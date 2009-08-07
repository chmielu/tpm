import sys
sys.path.append("../")
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import images
from utils import TpmRequestHandler, error
import models

class UserPage(TpmRequestHandler):
	def get(self):
		self.misc_render("user.html")

class AvatarPage(TpmRequestHandler):
	def get(self):
		self.misc_render("user_avatar.html")

	def post(self):
		profile = db.Query(models.Profile).filter("user =", users.get_current_user()).get()
		if self.request.get("delete"):
			profile.avatar = None
		else:
			profile.avatar = images.resize(self.request.get("avatar"), 60, 60)
		profile.put()
		self.redirect("/user/avatar")

class ProfilePage(TpmRequestHandler):
	def get(self):
		self.misc_render("user_profile.html")

	def post(self):
		profile = db.Query(models.Profile).filter("user =", users.get_current_user()).get()
		screenname = self.request.get("screenname")

		if profile:
			if screenname != profile.screenname:
				if db.Query(models.Profile).filter("screenname =", screenname).get():
					self.misc_render("user_profile.html", message="This screen name is taken."); return
			profile.screenname = screenname
		else:
			if db.Query(models.Profile).filter("screenname =", screenname).get():
				self.misc_render("user_profile.html", message="This screen name is taken."); return
			try:
				profile = models.Profile(
					user = users.get_current_user(),
					screenname = screenname,
				)
			except Exception, message:
				self.misc_render("user_profile.html", message="An error has occured: %s" % message); return
		
		profile.put()
		self.redirect("/user/profile")

class SignaturePage(TpmRequestHandler):
	def get(self):
		self.misc_render("user_signature.html")

	def post(self):
		self.redirect("/user/signature")

application = webapp.WSGIApplication([
	('/user', UserPage),
	('/user/avatar', AvatarPage),
	('/user/profile', ProfilePage),
	('/user/signature', SignaturePage),
], debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()
