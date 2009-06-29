import sys
sys.path.append("../")
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from utils import TpmRequestHandler

class HelpPage(TpmRequestHandler):
	def get(self):
		self.misc_render("help_index.html")

class MarkupPage(TpmRequestHandler):
	def get(self):
		self.misc_render("help_markup.html")


application = webapp.WSGIApplication([	('/help', HelpPage),
										('/help/markup', MarkupPage),
									], debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()