#!/usr/bin/env python
# coding: utf-8
#
#       forum.py
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

import re, sys, os
from urllib import unquote
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app

sys.path.append("../")

import models
from utils import *

class MainPage(TpmRequestHandler):
	def get(self):
		categories = models.Category().gql("ORDER BY title").fetch(1000)

		self.forum_render("index.html", categories=categories)

	@administrator
	@login_required
	def post(self):
		if not self.request.get("title"):
			error(self, 400, "you must enter a category title!");return
		if not self.request.get("slug"):
			slug = title
		else:
			slug = self.request.get("slug")
		if not slug:
			error(self, 400, "you must specify slug!");return
		if models.Category().gql("WHERE slug = :1 LIMIT 1", slug).fetch(1):
			error(self, 400, "this category slug already exist!");return
		cat = models.Category(
			title = db.Category(self.request.get("title")),
			slug = db.Category(slugify(slug)),
			desc = self.request.get("desc")
		).put()

		self.redirect('/forum')

class TopicsPage(TpmRequestHandler):
	def get(self, category):
		cat = models.Category().gql("WHERE slug = :1 LIMIT 1", db.Category(category))
		if not cat.count():
			error(self, 404);return

		topics = models.Post().gql("WHERE category = :1 ORDER BY date ASC", cat[0])

		array = {}
		for topic in topics:
			if not array.has_key(topic.topic_id):
				array[topic.topic_id] = {"oldest": topic, "newest": "", "sticked": topic.sticky, "replies": 0}
			else:
				array[topic.topic_id]["replies"] += 1
			array[topic.topic_id]["newest"] = topic

		undecorated = array.values()
		decorated = [(dict_["sticked"], dict_["newest"].date, dict_) for dict_ in undecorated]
		decorated.sort()
		decorated.reverse()
		topics = [dict_ for (_, key, dict_) in decorated]

		slug = category
		category = models.Category().gql("WHERE slug = :1 LIMIT 1", db.Category(category))[0].title

		self.forum_render("topics.html", slug=slug, category=category, topics=topics)

	@login_required
	def post(self, category):
		if not self.request.get("content") or not self.request.get("title"):
			error(self, 400, "you must enter a topic title and the content!");return
		cat = models.Category().gql("WHERE slug = :1 LIMIT 1", db.Category(category))
		if not cat.count():
			error(self, 400, "wrong category id!");return
		if not self.request.get("slug"):
			slug = slugify(title)
		else:
			slug = self.request.get("slug")
		if not slug:
			error(self, 400, "you must specify slug (it must be other then \"admin\")!");return
		if models.Post.gql("WHERE topic_id = :1 LIMIT 1", slug).fetch(1):
			error(self, 400, "this topic slug already exist!");return

		cat = cat[0]
		cat.topics += 1
		cat.posts += 1
		cat.put()

		post = models.Post(
			content = self.request.get("content"),
			content_html = re.sub("<br />$", "", to_html(self.request.get("content"))),
			title = self.request.get("title"),
			sticky = bool(self.request.get("sticky")),
			closed = bool(self.request.get("closed")),
			category = cat,
			topic_id = slugify(slug)
		).put()

		self.redirect("/forum/%s" % category)

class PostsPage(TpmRequestHandler):
	def get(self, category, topic):
		cat = models.Category().gql("WHERE slug = :1 LIMIT 1", db.Category(category))
		if not cat.count():
			error(self, 404);return
		posts = models.Post().gql("WHERE topic_id = :1 AND category = :2 ORDER BY date ASC", db.Category(topic), cat[0])
		if not posts.count():
			error(self, 404, uri="/forum/%s" % category);return

		slug = {
			"category": category,
			"topic": topic
		}

		self.forum_render("posts.html", topic=posts[0].title, category=cat[0].title, closed=posts[0].closed, slug=slug, posts=posts)

	@login_required
	def post(self, category, topic):
		if not self.request.get("content"):
			error(self, 400, "you must enter a topic title and the content!");return

		cat = models.Category().gql("WHERE slug = :1 LIMIT 1", db.Category(category))

		if not cat.count():
			error(self, 400, "wrong category id!");return

		oldest_post = models.Post().gql("WHERE topic_id = :1 ORDER BY date ASC LIMIT 1", topic)[0]

		if oldest_post.closed:
			error(self, 400, "this topic is closed!");return

		if self.request.get("title"):
			title = self.request.get("title")
		else:
			title = "Re: %s" % oldest_post.title

		cat = cat[0]
		cat.posts += 1
		cat.put()

		post = models.Post(
			content = self.request.get("content"),
			content_html = re.sub("<br />$", "", to_html(self.request.get("content"))),
			title = title,
			category = cat,
			topic_id = topic,
		).put()

		self.redirect("/forum/%s/%s" % (category, topic))

application = webapp.WSGIApplication(
	[
		('/forum/(.+)/(.+)', PostsPage),
		('/forum/(.+)', TopicsPage),
		('/forum', MainPage),
	],

	debug=True)

if __name__ == "__main__":
	run_wsgi_app(application)
