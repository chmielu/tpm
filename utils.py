from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api import users
import os, sys, re, functools, datetime
sys.path.append("../lib")
import postmarkup

ADMINS = [ "banana@thepuma.eu", "robert@chmielowiec.net" ]

class TpmRequestHandler(webapp.RequestHandler):
	def __init__(self,**kw):
		webapp.RequestHandler.__init__(self, **kw)

	def render(self, tmpl, *args, **kw):
		template_values = dict(**kw)
		template_values.update({'user': users.get_current_user()})
		template_values.update({'users': users})
		template_values.update({'admin': str(users.get_current_user()) in ADMINS})
		path = os.path.join(os.path.dirname(__file__), 'blog/templates/%s' % tmpl)
		self.response.out.write(template.render(path, template_values))

	def forum_render(self, tmpl, *args, **kw):
		template_values = dict(**kw)
		template_values.update({'user': users.get_current_user()})
		template_values.update({'users': users})
		template_values.update({'admin': str(users.get_current_user()) in ADMINS})
		path = os.path.join(os.path.dirname(__file__), 'forum/templates/%s' % tmpl)
		self.response.out.write(template.render(path, template_values))

def error(self, errorcode, message = None, uri = None):
	errorcodes = (400,401,403,404,500)
	if not errorcode in errorcodes:
		return False
	referrer = self.request.headers.get("Referer")
	self.render("%s.html" % errorcode, message=message, uri=uri, referrer=referrer)

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

class UtcTzinfo(datetime.tzinfo):
  def utcoffset(self, dt): return datetime.timedelta(0)
  def dst(self, dt): return datetime.timedelta(0)
  def tzname(self, dt): return 'UTC'
  def olsen_name(self): return 'UTC'

TZINFOS = {
  'utc': UtcTzinfo(),
}

class CET_tzinfo(datetime.tzinfo):
	"""Implementation of the Central European timezone."""
	def utcoffset(self, dt):
		return datetime.timedelta(hours=+1) + self.dst(dt)

	def _FirstSunday(self, dt):
		"""First Sunday on or after dt."""
		return dt + datetime.timedelta(days=(6-dt.weekday()))

	def dst(self, dt):
		# 2 am on the last Sunday in March
		dst_start = self._FirstSunday(datetime.datetime(dt.year, 3, 25, 2))
		# 1 am on the last Sunday in October
		dst_end = self._FirstSunday(datetime.datetime(dt.year, 10, 25, 1))

		if dst_start <= dt.replace(tzinfo=None) < dst_end:
			return datetime.timedelta(hours=1)
		else:
			return datetime.timedelta(hours=0)

	def tzname(self, dt):
		if self.dst(dt) == datetime.timedelta(hours=0):
			return "CET+01CET"
		else:
			return "CEST+02CET"

	def olsen_name(self): return 'Europe/Warsaw'
