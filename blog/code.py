import sys
sys.path.append("../")
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from utils import TpmRequestHandler

class CodePage(TpmRequestHandler):
	def get(self):
		self.render("code.html")

application = webapp.WSGIApplication([	('/code', CodePage),
									], debug=True)

def main():
	run_wsgi_app(application)

if __name__ == "__main__":
	main()