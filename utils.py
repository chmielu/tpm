from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
import os, sys, re, functools, datetime, models
sys.path.append("../lib")
import postmarkup

# TODO put it into database
ADMINS = [ "banana@thepuma.eu", "robert@chmielowiec.net" ]
MEMBERS = "thepuma.eu"

class TpmRequestHandler(webapp.RequestHandler):
	def __init__(self,**kw):
		webapp.RequestHandler.__init__(self, **kw)
		self.user = users.get_current_user()
		self.is_admin = str(self.user) in ADMINS
		self.profile = None
		if self.user:
			self.profile = db.Query(models.Profile).filter("user =", self.user).get()

	def render(self, tmpl, tmplprefix="blog/", *args, **kw):
		template_values = dict(**kw)
		template_values.update({'user': self.user})
		if self.profile:
			template_values.update({'profile': self.profile})
		elif self.user and not "message" in template_values:
			 template_values.update({'message': "We strongly recommend you to create your profile <a href=\"/user/create\">here</a>."})
		template_values.update({'users': users})
		template_values.update({'admin': self.is_admin})
		path = os.path.join(os.path.dirname(__file__), '%stemplates/%s' % (tmplprefix, tmpl))
		self.response.out.write(template.render(path, template_values))

	def forum_render(self, tmpl, *args, **kw):
		self.render(tmpl, "forum/", *args, **kw)

	def misc_render(self, tmpl, *args, **kw):
		self.render(tmpl, "misc/", *args, **kw)

def error(self, errorcode, error_message=None, uri=None, referer=None):
	errorcodes = (400,401,403,404,500)
	if not errorcode in errorcodes:
		return False
	if 'HTTP_REFERER' in os.environ:
		referer = os.environ['HTTP_REFERER']
	self.misc_render("%s.html" % errorcode, error_message=error_message, uri=uri, referer=referer)

def administrator(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        user = users.get_current_user()
        if not user:
            if self.request.method == "GET":
                self.redirect(users.create_login_url(self.request.uri))
                return
        if not str(user) in ADMINS:
            error(self, 403)
        else:
            return method(self, *args, **kwargs)
    return wrapper

def login_required(method):
	@functools.wraps(method)
	def decorator(self, *args, **kwargs):
		user = users.get_current_user()
		if not user:
			self.redirect(users.create_login_url(self.request.uri))
			return
		else:
			return method(self, *args, **kwargs)
	return decorator

def slugify(string):
    '''
    >>> slugify("Hello world !")
    'hello_world'
    '''
    string = re.sub('\s+', '_', string)
    string = re.sub('[^\w.-]', '', string)
    return string.strip('_.- ').lower()

def to_html(body):
	postmarkup.LinkTag.annotate_link = lambda self, domain: u""
	body_html = postmarkup.render_bbcode(body)
	return body_html
