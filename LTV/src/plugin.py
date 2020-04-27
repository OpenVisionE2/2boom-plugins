#!/usr/bin/python
# -*- coding: utf-8 -*-
# LIST TV updater
# Copyright (c) 2boom 2015
# v.0.4-r1
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import os, sys, os.path
from Plugins.Plugin import PluginDescriptor
from Components.Sources.StaticText import StaticText
from Components.Label import Label
from Components.Console import Console as iConsole
from Screens.Screen import Screen
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

BNAME = 'Lanet TV'
BFNAME = 'userbouquet.lanettv.tv'
PLGDIR = 'LTV'
M3UNAME = 'lanettv.m3u'
HLS = 'hls'
PASSW = ''

if PASSW is not '':
	PASSW = ':%s' % PASSW

def remove_line(filename, what):
	if os.path.isfile(filename):
		file_read = open(filename).readlines()
		file_write = open(filename, 'w')
		for line in file_read:
			if what not in line:
				file_write.write(line)
		file_write.close()

SKIN_DWN = """
<screen name="get_chlist" position="center,140" size="625,35" title="Please wait">
  <widget source="status" render="Label" position="10,5" size="605,22" zPosition="2" font="Regular; 20" halign="center" transparent="2" />
</screen>"""

class get_chlist(Screen):
	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self.session = session
		self.skin = SKIN_DWN
		self.setTitle(_("Please wait"))
		self["status"] = StaticText()
		self.iConsole = iConsole()
		self["status"].text = _("Donwloading channel list")
		self.address = self.link_file()
		if self.address is 'None':
			self["status"].text = _("No link file found")
			self.iConsole.ePopen('sleep 3', self.cancel)
		else:
			self.iConsole.ePopen("wget -q '%s' -O /tmp/%s" % (self.address, M3UNAME), self.user_upg2)

	def user_upg2(self, result, retval, extra_args):
		name_key = {}
		if retval is 0:
			if os.path.isfile('%sExtensions/%s/reference.txt' % (resolveFilename(SCOPE_PLUGINS), PLGDIR)):
				for line in open('%sExtensions/%s/reference.txt' % (resolveFilename(SCOPE_PLUGINS), PLGDIR)):
					if len(line.split()) > 0:
						name_key[line.split(';')[0].strip().split()[-1].strip('\r\n')] = line.split()[0]

			self["status"].text = _("Building bouquet")
			desk_tmp = default_ref = ''
			in_bouquets = 0
			if os.path.isfile('/tmp/%s' % M3UNAME):
				if os.path.isfile('/etc/enigma2/%s' % BFNAME):
					os.remove('/etc/enigma2/%s' % BFNAME)
				with open('/etc/enigma2/%s' % BFNAME, 'w') as outfile:
					outfile.write('#NAME %s\r\n' % BNAME)
					for line in open('/tmp/%s' % M3UNAME):
						default_ref = '1:0:1:0:0:0:0:0:0:0:'
						if line.startswith('#EXTINF:0,=== '):
							break
						if 'http://' in line:
							try:
								if name_key.get(line.split('/')[-1][:4]) is None:
									default_ref = '1:0:1:0:0:0:0:0:0:0:'
								else:
									default_ref = name_key.get(line.split('/')[-1][:4])
							except:
								pass
							outfile.write('#SERVICE %shttp%%3a//127.0.0.1%%3a88/%s%%3a//%s:%s\r\n' % (default_ref, HLS, line.strip('\n').replace(':', '%3a'), desk_tmp))
						elif '#EXTINF' in line:
							desk_tmp = '%s' % line.split(',')[-1].strip('\n').strip()
					outfile.close()
				if os.path.isfile('/etc/enigma2/bouquets.tv'):
					for line in open('/etc/enigma2/bouquets.tv'):
						if BFNAME in line:
							in_bouquets = 1
					if in_bouquets is 0:
						if os.path.isfile('/etc/enigma2/%s' % BFNAME) and os.path.isfile('/etc/enigma2/bouquets.tv'):
							remove_line('/etc/enigma2/bouquets.tv', BFNAME)
							remove_line('/etc/enigma2/bouquets.tv', 'LastScanned')
							with open('/etc/enigma2/bouquets.tv', 'a') as outfile:
								outfile.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet\r\n' % BFNAME)
								outfile.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.LastScanned.tv" ORDER BY bouquet\r\n')
								outfile.close()
			self["status"].text = _("Reload servicelist")
			self.iConsole.ePopen('wget -q -O - http://root%s@127.0.0.1/web/servicelistreload?mode=0 && sleep 2' % PASSW, self.cancel)
		else:
			self["status"].text = _("Error loading m3u")
			self.iConsole.ePopen('sleep 2', self.cancel)

	def cancel(self, result, retval, extra_args):
		self.close()

	def link_file(self):
		if os.path.isfile('%sExtensions/%s/link.txt' % (resolveFilename(SCOPE_PLUGINS), PLGDIR)):
			for line in open('%sExtensions/%s/link.txt' % (resolveFilename(SCOPE_PLUGINS), PLGDIR)):
				if line.startswith('http://'):
					return line.strip('\r').strip('\r').strip()
		return 'None'
	
def main(session, **kwargs):
	session.open(get_chlist)

def Plugins(**kwargs):
	list = PluginDescriptor(name=_("%s updater" % BNAME), description=_("update %s bouquet" % BNAME), where = [PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main)
	return list

