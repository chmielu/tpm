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
            self.redirect(users.create_login_url(os.environ["HTTP_REFERER"]))
        else:
            self.redirect('/')

class LogoutHandler(TpmRequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.redirect(users.create_logout_url('/'))
        else:
            self.redirect('/')

class WarsPage(TpmRequestHandler):
	def get(self):
		category = "clanwars"
		# cat = models.Category().gql("WHERE slug = :1 LIMIT 1", db.Category("clanwars"))
		cat = db.Query(models.Category).filter("slug =", db.Category(category)).get()
		if not cat:
			error(self, 404);return
		# clanwars = models.Post().gql("WHERE category = :1 ORDER BY date ASC", cat[0])
		clanwars = db.Query(models.Post).filter("category =", cat).order("-date").fetch(limit=20)
		array = {}
		for topic in clanwars:
			if not array.has_key(topic.topic_id):
				array[topic.topic_id] = {"oldest": topic, "newest": "", "replies": 0}
			else:
				array[topic.topic_id]["replies"] += 1
			array[topic.topic_id]["newest"] = topic
		undecorated = array.values()
		decorated = [(dict_["newest"].date, dict_) for dict_ in undecorated]
		decorated.sort()
		decorated.reverse()
		array = [dict_ for (key, dict_) in decorated]
		clanwars = array
		self.misc_render("clanwars.html", slug=category, clanwars=clanwars)

application = webapp.WSGIApplication([	('/chat', ChatPage),
										('/clanwars', WarsPage),
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