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
	def get(self, category):
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

		self.forum_render("topics.html", slug=slug, category=category, topics=topics)

	@login_required
	def post(self, category):
		if not self.request.get("title"):
			self.forum_render("topics.html", message="You must enter a topic title and the content!"); return
		cat = models.Category.gql("WHERE slug = :1 LIMIT 1", db.Category(category))
		if not cat.count():
			self.forum_render("topics.html", message="Wrong category id!"); return
		if not self.request.get("slug"):
			slug = slugify(title)
		else:
			slug = self.request.get("slug")
		if not slug:
			self.forum_render("topics.html", message="You must specify slug (it must be other then \"admin\")!"); return
		if models.Post.gql("WHERE topic_id = :1 AND category = :2 LIMIT 1", slug, cat[0]).count():
			self.forum_render("topics.html", message="This topic slug already exist in this category!"); return

		cat = cat[0]
		cat.topics += 1
		cat.posts += 1
		cat.put()

		try:
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
			self.forum_render("topics.html", message=message); return
		post.put()

		self.redirect("/forum/%s" % category)

class PostsPage(TpmRequestHandler):
	def get(self, category, topic):
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
			closed=array[0]["post"].closed, slug=slug, posts=array)

	@login_required
	def post(self, category, topic):

		cat = models.Category.gql("WHERE slug = :1 LIMIT 1", db.Category(category))

		if not cat.count():
			self.forum_render("posts.html", message="Wrong category id!"); return

		oldest_post = models.Post.gql("WHERE topic_id = :1 ORDER BY date ASC LIMIT 1", topic)[0]

		if oldest_post.closed:
			error(self, 403, "This topic is closed!"); return

		if self.request.get("title"):
			title = self.request.get("title")
		else:
			title = "Re: %s" % oldest_post.title

		cat = cat[0]
		cat.posts += 1
		cat.put()

		try:
			post = models.Post(
				content = self.request.get("content"),
				content_html = re.sub("<br />$", "", to_html(self.request.get("content"))),
				title = title,
				category = cat,
				topic_id = topic,
			)
		except Exception, message:
			self.forum_render("posts.html", message=message)
		post.put()

		self.redirect("/forum/%s/%s" % (category, topic))

application = webapp.WSGIApplication([
	('/forum/(.+)/(.+)', PostsPage),
	('/forum/(.+)', TopicsPage),
	('/forum', MainPage),
], debug=True)

if __name__ == "__main__":
	run_wsgi_app(application)
