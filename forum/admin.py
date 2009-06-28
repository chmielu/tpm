#!/usr/bin/env python
# coding: utf-8
#
#       admin.py
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


import sys, os
from urllib import unquote
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app

sys.path.append("../")

import models
from utils import *

class DeleteCategoryPage(TpmRequestHandler):
	@administrator
	def get(self, category):
		cat = models.Category().gql("WHERE slug = :1 LIMIT 1", db.Category(category))
		if not cat.count():
			error(self, 404);return

		title = cat[0].title
		slug = category
		self.forum_render("delete_category.html", title=title, slug=slug)

	@administrator
	def post(self, category):
		if self.request.get("delete_confirmation") == "no":
			self.redirect("/forum")
			return
		elif self.request.get("delete_confirmation") == "yes":
			cat = models.Category().gql("WHERE slug = :1 LIMIT 1", db.Category(category))
			if not cat.count():
				error(self, 400, "wrong category id!");return

			posts = models.Post().gql("WHERE category = :1", cat[0])

			for post in posts:
				post.delete()
			cat[0].delete()

			self.redirect("/forum")

class DeleteTopicPage(TpmRequestHandler):
	@administrator
	def get(self, category, topic):
		cat = models.Category().gql("WHERE slug = :1 LIMIT 1", db.Category(category))
		if not cat.count():
			error(self, 404);return
		posts = models.Post().gql("WHERE topic_id = :1 AND category = :2 ORDER BY date ASC", db.Category(topic), cat[0])
		if not posts.count():
			error(self, 404, uri="/forum/%s" % category);return

		title = posts[0].title
		slug = {
			"category": category,
			"topic": topic
		}
		self.forum_render("delete_topics.html", title=title, slug=slug)

	@administrator
	def post(self, category, topic):
		if self.request.get("delete_confirmation") == "no":
			self.redirect("/forum/%s" % category);return
		elif self.request.get("delete_confirmation") == "yes":
			cat = models.Category().gql("WHERE slug = :1 LIMIT 1", db.Category(category))
			if not cat.count():
				error(self, 400, "wrong category id!");return

			posts = models.Post().gql("WHERE topic_id = :1 AND category = :2 ORDER BY date ASC", db.Category(topic), cat[0])

			cat = cat[0]
			cat.topics -= 1

			for post in posts:
				cat.posts -= 1
				post.delete()
			cat.put()

			self.redirect("/forum/%s" % category)

class DeletePostPage(TpmRequestHandler):
	@administrator
	def get(self, slug):
		try:
			key = db.Key(slug)
		except db.BadKeyError:
			error(self, 400, "bad key id!");return
		post = models.Post.get(key)
		if not post:
			error(self, 400, "wrong post id!");return
		title = post.title

		self.forum_render("delete_posts.html", title=title, slug=slug)

	@administrator
	def post(self, slug):
		if self.request.get("delete_confirmation") == "no":
			self.redirect("/forum");return
		elif self.request.get("delete_confirmation") == "yes":
			try:
				key = db.Key(slug)
			except db.BadKeyError:
				error(self, 400, "bad key id!");return

			post = models.Post.get(key)

			if not post:
				error(self, 400, "wrong post id!");return

			post.category.posts -=1
			post.category.put()

			post.delete()
			self.redirect('/forum')

class EditCategoryPage(TpmRequestHandler):
	@administrator
	def get(self, category):
		cat = models.Category().gql("WHERE slug = :1 LIMIT 1", db.Category(category))
		if not cat.count():
			error(self, 404);return

		title = cat[0].title
		slug = category
		desc = cat[0].desc
		self.forum_render("edit_category.html", title=title, slug=slug, desc=desc)

	@administrator
	def post(self, category):
		cat = models.Category().gql("WHERE slug = :1 LIMIT 1", db.Category(category))
		if not cat.count():
			error(self, 404);return
		if not self.request.get("title"):
			error(self, 400, "you must enter a category title!");return
		if not self.request.get("slug"):
			slug = title
		else:
			slug = self.request.get("slug")
		if not slug:
			error(self, 400, "you must specify slug!");return
		if category != slug:
			if models.Category().gql("WHERE slug = :1 LIMIT 1", db.Category(slug)).count():
				error(self, 400, "this category slug already exist!");return

		cat = cat[0]
		cat.title = db.Category(self.request.get("title"))
		cat.slug = db.Category(slugify(slug))
		cat.desc = self.request.get("desc")
		cat.put()

		self.redirect("/forum")

class EditTopicPage(TpmRequestHandler):
	@administrator
	def get(self, category, topic):
		cat = models.Category().gql("WHERE slug = :1 LIMIT 1", db.Category(category))
		if not cat.count():
			error(self, 404);return
		posts = models.Post().gql("WHERE topic_id = :1 AND category = :2 ORDER BY date ASC", db.Category(topic), cat[0])
		if not posts.count():
			error(self, 404, uri="/forum/%s" % category);return

		title = posts[0].title
		content = posts[0].content
		slug = {
			"category": category,
			"topic": topic
		}
		self.forum_render("edit_topics.html", title=title, content=content, slug=slug)

	@administrator
	def post(self, category, topic):
		cat = models.Category().gql("WHERE slug = :1 LIMIT 1", db.Category(category))
		if not cat.count(): error(self, 400, "wrong category id!");return

		posts = models.Post().gql("WHERE topic_id = :1 AND category = :2 ORDER BY date ASC", db.Category(topic), cat[0])
		if not posts.count(): error(self, 400, "wrong topic id!");return

		if not self.request.get("content") or not self.request.get("title"):
			error(self, 400, "you must enter a topic title and the content!");return
		if not self.request.get("slug"):
			slug = title
		else:
			slug = self.request.get("slug")
		if not slug:
			error(self, 400, "you must specify slug!");return
		if topic != slug:
			if models.Post().gql("WHERE topic_id = :1 AND category = :2 LIMIT 1", db.Category(slug), cat[0]).count():
				error(self, 400, "this category slug already exist!");return

		posts = posts.fetch(1000)
		posts[0].title = self.request.get("title")
		posts[0].content = self.request.get("content")
		posts[0].content_html = re.sub("<br />$", "", to_html(self.request.get("content")))

		for post in posts:
			post.topic_id = slug
			post.put()

		self.redirect("/forum/%s" % category)

class EditPostPage(TpmRequestHandler):
	@administrator
	def get(self, slug):
		try:
			key = db.Key(slug)
		except db.BadKeyError:
			error(self, 404, "bad key id!");return

		post = models.Post.get(key)

		if not post:
			error(self, 400, "wrong post id!");return

		title = post.title
		content = post.content
		slug = slug

		self.forum_render("edit_posts.html", title=title, content=content, slug=slug)

	@administrator
	def post(self, slug):
		try:
			key = db.Key(slug)
		except db.BadKeyError:
			error(self, 400, "bad key id!");return

		post = models.Post.get(key)
		if not post: error(self, 400, "wrong post id!");return

		if not self.request.get("content") or not self.request.get("title"):
			error(self, 400, "you must enter a topic title and the content!");return

		post.title = self.request.get("title")
		post.content = self.request.get("content")
		post.content_html = re.sub("<br />$", "", to_html(self.request.get("content")))
		post.put()

		self.redirect('/forum')

application = webapp.WSGIApplication(
	[
		('/forum/admin/delete/topic/(.+)/(.+)', DeleteTopicPage),
		('/forum/admin/delete/post/(.+)', DeletePostPage),
		('/forum/admin/delete/category/(.+)', DeleteCategoryPage),

		('/forum/admin/edit/topic/(.+)/(.+)', EditTopicPage),
		('/forum/admin/edit/post/(.+)', EditPostPage),
		('/forum/admin/edit/category/(.+)', EditCategoryPage),
	],

	debug=True)

if __name__ == "__main__":
	run_wsgi_app(application)
