import os, sys
sys.path.append("../")
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from utils import TpmRequestHandler, error
import models

class ChatPage(TpmRequestHandler):
	def get(self):
		nickname=str(users.get_current_user()).split("@")[0]
		self.misc_render("chat.html", nickname=nickname)

class CodePage(TpmRequestHandler):
	def get(self):
		self.misc_render("code.html")

class ErrorPage(TpmRequestHandler):
	def get(self, anything):
		error(self, 404)

class FeedPage(TpmRequestHandler):
	def get(self):
		entries = db.Query(models.Entry).order("-published").fetch(limit=10)
		if entries:
			latest = entries[0]
		else:
			latest = None
		hostname = os.environ["SERVER_NAME"]
		if not os.environ["SERVER_PORT"] == 80:
			hostname = "%s:%s" % (hostname, os.environ["SERVER_PORT"])
		self.response.headers['Content-Type'] = 'application/atom+xml'
		self.misc_render("atom.xml", entries=entries, latest=latest, hostname=hostname)

class HelpPage(TpmRequestHandler):
	def get(self):
		self.misc_render("help_index.html")

class MarkupPage(TpmRequestHandler):
	def get(self):
		self.misc_render("help_markup.html")

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

application = webapp.WSGIApplication([	('/chat', ChatPage),
										('/code', CodePage),
										('/feed', FeedPage),
										('/help', HelpPage),
										('/help/markup', MarkupPage),
										('/login', LoginHandler),
										('/logout', LogoutHandler),
										('/(.*)', ErrorPage),
									], debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()