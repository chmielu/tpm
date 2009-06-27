#!/usr/bin/env python
# coding: utf-8
#
#       models.py
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


from google.appengine.ext import db

class Category(db.Model):
	title = db.CategoryProperty()
	desc = db.StringProperty()
	slug = db.CategoryProperty()
	topics = db.IntegerProperty(default=0)
	posts = db.IntegerProperty(default=0)

class Post(db.Model):
	user = db.UserProperty(auto_current_user_add = True)
	title = db.StringProperty()
	content = db.TextProperty()
	content_html = db.TextProperty()
	date = db.DateTimeProperty(auto_now_add=True)
	category = db.ReferenceProperty(Category)
	topic_id = db.CategoryProperty()
