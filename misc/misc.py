import re, sys, os
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

class ClanwarsPage(TpmRequestHandler):
	def get(self):
		category = "clanwars"
		cat = db.Query(models.Category).filter("slug =", db.Category(category)).get()
		if not cat:
			error(self, 500, "Administrator have to set up  category with 'clanwars' slug.");return
		clanwars = db.Query(models.Post).filter("category =", cat).order("date").fetch(limit=20)
		array = {}
		for topic in clanwars:
			if not array.has_key(topic.topic_id):
				splitted = topic.title.split(" - ")
				if len(splitted) >= 2:
					cmp = splitted[1].split(':')
					if len(cmp) != 2:
						cmp = splitted[1].split('-')

					# if still not 2 someone is an idiot?
					if len(cmp) != 2:
						cmp = ["0","0"]

					cwinfo = {
						"opponent": splitted[0].split()[2],
						"score": {
							"class": (int(cmp[0]) > int(cmp[1])) and "win" or (cmp[0] == cmp[1]) and "draw" or "lost",
							"int": re.sub(r"(\b|:)(0?0?0?)",
								r'\1<span class="leadingzeros">\2</span>',
								"%04d:%04d" % (int(cmp[0]), int(cmp[1]))),
						},
						"map": (len(splitted) > 2) and splitted[2] or None,
						"gametype": (len(splitted) > 3) and splitted[3] or None,
						"teams": (len(splitted) > 4) and splitted[4] or None,
						"cup": (len(splitted) > 5) and splitted[5] or None,
					}

					array[topic.topic_id] = {
						"oldest": topic,
						"cwinfo": cwinfo,
						"replies": 0
					}
			else:
				array[topic.topic_id]["replies"] += 1

		undecorated = array.values()
		decorated = [(dict_["oldest"].date, dict_) for dict_ in undecorated]
		decorated.sort()
		decorated.reverse()
		array = [dict_ for (key, dict_) in decorated]
		clanwars = array
		self.misc_render("clanwars.html", slug=category, clanwars=clanwars)

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
            self.redirect(users.create_logout_url(os.environ["HTTP_REFERER"]))
        else:
            self.redirect('/')

application = webapp.WSGIApplication(
[	('/chat', ChatPage),
	('/clanwars', ClanwarsPage),
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
