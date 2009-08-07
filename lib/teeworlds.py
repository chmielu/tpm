#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time, operator
from socket import AF_INET, SOCK_DGRAM, socket

"""
Python port of Daniel Wirtz's PHP Teeworlds server query tool (blog.code-emitter.com/?page_id=214)
Author: Krzysztof Socha (ksocha.com)

Usage: look at teeworlds_usage()
"""

class TeeworldsServer(object):
	def __init__(self, ip, port):
		self.ip = ip
		self.port = int(port)
		self.is_passworded = False
		self.players = dict()
	
	def query(self, timeout=3):
		fp = socket(AF_INET, SOCK_DGRAM)
		fp.connect((self.ip, self.port))
		packet = chr(255)*10 + "gief"
		reqtime = time.time()
		try:
			fp.send(packet)
			data = fp.recv(10000)
		except:
			return False
		restime = time.time()
		fp.close()
		info = data[10:14]
		if not info == "info":
			return False
		data = data[14:]
		self.version, self.name, self.map, self.gametype, self.flags, self.clientid, self.numplayers, self.maxplayers, rawplayers = data.split(chr(0), 8)
		self.name = unicode(self.name, 'latin-1')
		self.ping = round(1000*(restime-reqtime))
		if int(self.flags) == 1:
			self.is_passworded = True
		rawplayers = rawplayers.split(chr(0))
		for i in range(int(self.numplayers)):
			"""get rid of fake clients"""
			if rawplayers[0] == "":
				self.numplayers = i
				if not 1 in rawplayers:
					break
				continue
			self.players[unicode(rawplayers.pop(0), 'latin-1')] = int(rawplayers.pop(1))
		return True

def teeworlds_usage():
	"""few sample servers"""
	#t = TeeworldsServer("srv.thepuma.eu", 8304)
	#t = TeeworldsServer("87.118.106.50", 8303)
	#t = TeeworldsServer("78.111.75.193", 8316)
	t = TeeworldsServer("194.146.225.83", 27966)
	if not t.query():
		exit("Server is down, or you are trying to connect to non-Teeworlds server.")
	server_name = "Server name: %s" % t.name.strip()
	if t.is_passworded:
		server_name += " \033[0;1m(pwd)\033[0;0m"
	print server_name
	print "Address: %s:%s" % (t.ip, t.port)
	print "Ping: %d" % t.ping
	print "Gametype: %s" % t.gametype
	print "Map: %s" % t.map
	players = "Players: %s/%s" % (t.numplayers, t.maxplayers)
	if int(t.maxplayers) <= int(t.numplayers):
		players += " \033[0;1m(full)\033[0;0m"
	print players
	t.players = sorted(t.players.items(), key=operator.itemgetter(1), reverse=True)
	if t.players:
		print "Score  Player"
		for k, v in t.players:
			print "%5d  %s" % (v, k)

teeworlds_usage()