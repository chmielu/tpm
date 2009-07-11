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
	def get(self, message = None):
		categories = db.Query(models.Category).fetch(1000)
		self.forum_render("index.html", categories=sorted(categories), message=message)

	@administrator
	def post(self):
		try:
			if not self.request.get("slug"):
				slug = self.request.get("title")
			else:
				slug = self.request.get("slug")
			if not slug:
				raise Exception("An error has occured: You must specify category slug!")
			if models.Category.gql("WHERE slug = :1 LIMIT 1", slug).count():
				raise Exception("An error has occured: This category slug already exists!")
			cat = models.Category(
				title = db.Category(self.request.get("title")),
				slug = db.Category(slugify(slug)),
				desc = self.request.get("desc")
			)
		except Exception, message:
			self.get(message);return
		cat.put()
		self.redirect('/forum')

class TopicsPage(TpmRequestHandler):
	def get(self, category, message = None):
		cat = models.Category.gql("WHERE slug = :1 LIMIT 1", db.Category(category))
		if not cat.count():
			error(self, 404);return

		topics = models.Post.gql("WHERE category = :1 ORDER BY date ASC", cat[0])

		array = {}
		for topic in topics:
			if not array.has_key(topic.topic_id):
				array[topic.topic_id] = {
					"oldest": topic,
					"newest": "",
					"sticked": topic.sticky,
					"replies": 0
				}
			else:
				array[topic.topic_id]["replies"] += 1
			array[topic.topic_id].update({
				"newest": topic,
				"profile": db.Query(models.Profile).filter("user =", topic.user).get(),
			})

		undecorated = array.values()
		decorated = [(dict_["sticked"], dict_["newest"].date, dict_) for dict_ in undecorated]
		decorated.sort()
		decorated.reverse()
		topics = [dict_ for (_, key, dict_) in decorated]

		slug = category
		category = models.Category.gql("WHERE slug = :1 LIMIT 1", db.Category(category))[0].title

		self.forum_render("topics.html", slug=slug, category=category, topics=topics, message=message)

	@login_required
	def post(self, category):
		try:
			if not self.request.get("title"):
				raise Exception("An error has occured: You must enter a topic title and the content!")
			cat = models.Category.gql("WHERE slug = :1 LIMIT 1", db.Category(category)).get()
			if not cat:
				raise Exception("An error has occured: Wrong category id!")
			if not self.request.get("slug"):
				slug = slugify(title)
			else:
				slug = self.request.get("slug")
			if not slug:
				raise Exception("An error has occured: You must specify slug!")
			if models.Post.gql("WHERE topic_id = :1 AND category = :2 LIMIT 1", slug, cat).count():
				raise Exception("An error has occured: This topic slug already exist in this category!")

			post = models.Post(
				content = self.request.get("content"),
				content_html = re.sub("<br />$", "", to_html(self.request.get("content"))),
				title = self.request.get("title"),
				sticky = bool(self.request.get("sticky")),
				closed = bool(self.request.get("closed")),
				category = cat,
				topic_id = slugify(slug)
			)
		except Exception, message:
			self.get(category, message);return

		cat.topics += 1
		cat.posts += 1
		cat.put()

		post.put()

		self.redirect("/forum/%s" % category)

class PostsPage(TpmRequestHandler):
	def get(self, category, topic, message = None):
		cat = models.Category.gql("WHERE slug = :1 LIMIT 1", db.Category(category))
		if not cat.count():
			error(self, 404);return
		posts = models.Post.gql("WHERE topic_id = :1 AND category = :2 ORDER BY date ASC", db.Category(topic), cat[0])
		if not posts.count():
			error(self, 404, uri="/forum/%s" % category);return

		array = []
		for post in posts:
			array.append({
				"post": post,
				"profile": db.Query(models.Profile).filter("user =", post.user).get(),
			})
		del posts

		slug = {
			"category": category,
			"topic": topic
		}

		self.forum_render("posts.html", topic=array[0]["post"].title, category=cat[0].title,
			closed=array[0]["post"].closed, slug=slug, posts=array, message=message)

	@login_required
	def post(self, category, topic):
		try:
			cat = models.Category.gql("WHERE slug = :1 LIMIT 1", db.Category(category)).get()

			if not cat:
				raise Exception("An error has occured: Wrong category id!")

			oldest_post = models.Post.gql("WHERE topic_id = :1 ORDER BY date ASC LIMIT 1", topic).get()

			if oldest_post.closed:
				raise Exception("An error has occured: This topic is closed!")

			if self.request.get("title"):
				title = self.request.get("title")
			else:
				title = "Re: %s" % oldest_post.title

			post = models.Post(
				content = self.request.get("content"),
				content_html = re.sub("<br />$", "", to_html(self.request.get("content"))),
				title = title,
				category = cat,
				topic_id = topic,
			)
		except Exception, message:
			self.get(category, topic, message);return

		cat.posts += 1
		cat.put()

		post.put()

		self.redirect("/forum/%s/%s" % (category, topic))

application = webapp.WSGIApplication([
	('/forum/(.+)/(.+)', PostsPage),
	('/forum/(.+)', TopicsPage),
	('/forum', MainPage),
], debug=True)

if __name__ == "__main__":
	run_wsgi_app(application)
