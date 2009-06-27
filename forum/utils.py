#!/usr/bin/env python
# coding: utf-8
#
#       utils.py
#
#       Copyright 2009 Robert Chmielowiec <robert@chmielowiec.net>
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#


import functools, re, postmarkup

from google.appengine.api import users
from google.appengine.ext.webapp import template

ADMINS = ["banana@thepuma.eu", "robert@chmielowiec.net"]

def error(self, errorcode, message = None, uri = None):
	errorcodes = (400, 401, 403, 404, 500)
	if not errorcode in errorcodes:
		return False
	self.response.clear()
	self.response.out.write(template.render("templates/%d.html" % errorcode, {"login": create_login_box(self.request.uri), "message":message, "uri":uri}))

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

def admin_required(method):
	@functools.wraps(method)
	def decorator(self, *args, **kwargs):
		user = users.get_current_user()
		if str(user) not in ADMINS:
			error(self, 403)
		else:
			return method(self, *args, **kwargs)
	return decorator

def create_login_box(url):
	login = {}
	user = users.get_current_user()
	if user:
		login["url"] = users.create_logout_url(url)
		login["user"] = user
	else:
		login["url"] = users.create_login_url(url)
	return login

def slugify(string):
	string = re.sub('\s+', '_', string)
	string = re.sub('[^\w-]', '', string)
	return string.strip('_- ').lower()

def to_html(body):
	postmarkup.LinkTag.annotate_link = lambda self, domain: u""
	body_html = postmarkup.render_bbcode(body)
	return body_html

