#!/usr/bin/python
# -*- coding: utf-8 -*-
# Auto EPG downloader
# Copyright (c) 2boom 2015-17
# v.03-r12a
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

from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigText, ConfigInteger, ConfigSelection, ConfigSubsection, ConfigYesNo, configfile, NoSave
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Sources.List import List
from Components.Language import language
from Components.Sources.StaticText import StaticText
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from os import environ
import os
import gettext
from enigma import eEPGCache
from types import *
from enigma import *
import sys, traceback
import time
import new
import _enigma
import enigma
import socket
import gzip
import urllib
import stat

lang = language.getLanguage()
environ['LANGUAGE'] = lang[:2]
gettext.bindtextdomain('enigma2', resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain('enigma2')
gettext.bindtextdomain('epgdd', '%s%s' % (resolveFilename(SCOPE_PLUGINS), 'Extensions/epgdd/locale/'))

def _(txt):
	t = gettext.dgettext('epgdd', txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t
	
def mountp():
	pathmp = []
	if os.path.isfile('/proc/mounts'):
		for line in open('/proc/mounts'):
			if '/dev/sd' in line or '/dev/disk/by-uuid/' in line or '/dev/mmc' in line or '/dev/mtdblock' in line:
				pathmp.append(line.split()[1].replace('\\040', ' ') + '/')
	pathmp.append('/usr/share/enigma2/')
	pathmp.append('/tmp/')
	return pathmp
	
def logging(line):
	log_file = open('/tmp/epgdd.log', 'a')
	log_file.write(line)
	log_file.close()

config.plugins.epgdd = ConfigSubsection()
config.plugins.epgdd.direct = ConfigSelection(choices = mountp())
config.plugins.epgdd.epgname = ConfigText(default='epg.dat', visible_width = 50, fixed_size = False)
config.plugins.epgdd.url = ConfigText(default='http://epg.giclub.tv/epg/epg.datru.gz', visible_width = 80, fixed_size = False)
config.plugins.epgdd.leghtfile = ConfigInteger(default = 0)
config.plugins.epgdd.menuext = ConfigYesNo(default = False)
config.plugins.epgdd.flush = ConfigYesNo(default = False)
config.plugins.epgdd.epgupdate = ConfigYesNo(default = False)
config.plugins.epgdd.checkepgfile = ConfigYesNo(default = False)
config.plugins.epgdd.nocheck = ConfigYesNo(default = True)
config.plugins.epgdd.first = ConfigYesNo(default = True)
config.plugins.epgdd.checkp = ConfigSelection(default = '60', choices = [
		('30', _("30 min")),
		('60', _("60 min")),
		('120', _("120 min")),
		('180', _("180 min")),
		('240', _("240 min")),
		])
config.plugins.epgdd.lastupdate = ConfigText(default=_('last epg.dat updated - not yet'))

class epgdd(ConfigListScreen, Screen):
	skin = """
<screen name="epgdd" position="center,160" size="850,280" title="">
  <widget position="15,5" size="820,200" name="config" scrollbarMode="showOnDemand" />
  <ePixmap position="10,275" zPosition="1" size="165,2" pixmap="~/images/red.png" alphatest="blend" />
  <widget source="key_red" render="Label" position="10,245" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
  <ePixmap position="175,275" zPosition="1" size="165,2" pixmap="~/images/green.png" alphatest="blend" />
  <widget source="key_green" render="Label" position="175,245" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
  <ePixmap position="340,275" zPosition="1" size="200,2" pixmap="~/images/yellow.png" alphatest="blend" />
  <widget source="key_yellow" render="Label" position="340,245" zPosition="2" size="200,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
  <ePixmap position="540,275" zPosition="1" size="250,2" pixmap="~/images/blue.png" alphatest="blend" />
  <widget source="key_blue" render="Label" position="540,245" zPosition="2" size="250,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
  <widget source="lastupdate" render="Label" position="20,212" zPosition="2" size="810,24" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="grey" transparent="1" />
  <eLabel position="30,208" size="790,2" backgroundColor="grey" />
</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/epgdd")
		config.plugins.epgdd.direct = ConfigSelection(choices = mountp())
		self.setTitle(_('EPG from %s') % config.plugins.epgdd.url.value.split('/')[2])
		self.list = []
		self.list.append(getConfigListEntry(_('Set autoupdate epg.dat'), config.plugins.epgdd.epgupdate))
		self.list.append(getConfigListEntry(_('Select path to save epg.dat'), config.plugins.epgdd.direct))
		self.list.append(getConfigListEntry(_('Set EPG filename'), config.plugins.epgdd.epgname))
		self.list.append(getConfigListEntry(_('Download url'), config.plugins.epgdd.url))
		self.list.append(getConfigListEntry(_('Periodicity checks'), config.plugins.epgdd.checkp))
		self.list.append(getConfigListEntry(_('EPGFlush if support'), config.plugins.epgdd.flush))
		self.list.append(getConfigListEntry(_('Check epg.dat exists'), config.plugins.epgdd.checkepgfile))
		self.list.append(getConfigListEntry(_('Show Auto EPG Downloader in ExtensionMenu'), config.plugins.epgdd.menuext))
		ConfigListScreen.__init__(self, self.list, session=session)
		self['key_red'] = StaticText(_('Close'))
		self['key_green'] = StaticText(_('Save'))
		self['key_yellow'] = StaticText(_('Download EPG'))
		self['key_blue'] = StaticText(_('Source'))
		self['lastupdate'] = StaticText()
		self['lastupdate'].text = config.plugins.epgdd.lastupdate.value
		self.timer = enigma.eTimer() 
		self.timer.callback.append(self.updatestatus)
		self.timer.start(3000, True)
		self['setupActions'] = ActionMap(['SetupActions', 'ColorActions'],
		{
			'red': self.cancel,
			'cancel': self.cancel,
			'green': self.save,
			'yellow': self.loadepgdat,
			'blue': self.choicesource,
			'ok': self.save
		}, -2)
		
	def choicesource(self):
		self.session.open(get_source)
		
	def updatestatus(self):
		self.timer.stop()
		self['lastupdate'].text = config.plugins.epgdd.lastupdate.value
		self.timer.start(3000, True)

	def save(self):
		now = time.localtime(time.time())
		config.plugins.epgdd.url.value = config.plugins.epgdd.url.value.replace(' ', '')
		for i in self['config'].list:
			i[1].save()
		if self.image_is_OA():
			config.misc.epgcachefilename.value = config.plugins.epgdd.epgname.value
			config.misc.epgcachepath.value = config.plugins.epgdd.direct.value
			config.misc.epgcachepath.save()
			config.misc.epgcachefilename.save()
			config.plugins.epgdd.epgupdate.save()
			if self.image_is_atv6():
				config.misc.epgcache_filename.value = '%s%s' % (config.plugins.epanel.direct.value, config.plugins.epanel.epgname.value)
				config.misc.epgcache_filename.save()
			logging('%02d:%02d:%d %02d:%02d:%02d - set %s\r\n%02d:%02d:%d %02d:%02d:%02d - set %s\r\n' % \
				(now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, config.misc.epgcachepath.value, now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, config.misc.epgcachefilename.value))
		else:
			config.misc.epgcache_filename.value = '%s%s' % (config.plugins.epgdd.direct.value, config.plugins.epgdd.epgname.value)
			config.misc.epgcache_filename.save()
			logging('%02d:%02d:%d %02d:%02d:%02d - set %s\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, config.misc.epgcache_filename.value))
		logging('%02d:%02d:%d %02d:%02d:%02d - set %s\r\n%02d:%02d:%d %02d:%02d:%02d - set %s min check period\r\n' % \
			(now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, config.plugins.epgdd.url.value, now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, config.plugins.epgdd.checkp.value))
		configfile.save()
		if self.image_is_pli():
			from Components.PluginComponent import plugins
			plugins.reloadPlugins()
		self.mbox = self.session.open(MessageBox, (_('configuration is saved')), MessageBox.TYPE_INFO, timeout = 4 )

	def cancel(self):
		self.close()

	def loadepgdat(self):
		self.session.open(get_epgdat)

	def image_is_OA(self):
		if os.path.isfile('/etc/issue'):
			for line in open('/etc/issue'):
				if 'openatv' in line or 'openhdf' in line or 'openvix' in line.lower():
					return True
		return False
	
	def image_is_atv6(self):
		if os.path.isfile('/etc/issue'):
			for line in open('/etc/issue'):
				if 'openatv 6' in line.lower():
					return True
		return False

	def image_is_pli(self):
		if os.path.isfile('/etc/issue'):
			for line in open('/etc/issue'):
				if 'openpli' in line.lower():
					return True
		return False

class Check_EPG():
	def __init__(self):
		self.dialog = None

	def gotSession(self, session):
		self.session = session
		if config.plugins.epgdd.epgupdate.value:
			self.timer = enigma.eTimer() 
			self.timermin = enigma.eTimer() 
			self.timermin.callback.append(self.check_change_min)
			self.timer.callback.append(self.check_change)
			self.timermin.startLongTimer(30)
			self.timer.startLongTimer(60)

	def check_change(self):
		self.timer.stop()
		now = time.localtime(time.time())
		try:
			lenght_epgfile = int(urllib.urlopen(config.plugins.epgdd.url.value).info()['content-length'])
			logging('%02d:%02d:%d %02d:%02d:%02d - size epg.tar.gz: %d bytes\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, lenght_epgfile))
			if config.plugins.epgdd.leghtfile.value != lenght_epgfile:
				self.loadepgdat()
		except Exception as e:
			logging('%02d:%02d:%d %02d:%02d:%02d - %s\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec,  str(e)))
		self.timer.startLongTimer(int(config.plugins.epgdd.checkp.value) * 60)

	def check_change_min(self):
		self.timermin.stop()
		now = time.localtime(time.time())
		if config.plugins.epgdd.first.value and config.plugins.epgdd.nocheck.value:
			config.plugins.epgdd.first.value = False
			if os.path.isfile('%s%s' % (config.plugins.epgdd.direct.value, config.plugins.epgdd.epgname.value)):
				epgcache = new.instancemethod(_enigma.eEPGCache_load, None, eEPGCache)
				epgcache = eEPGCache.getInstance().load()
				logging('%02d:%02d:%d %02d:%02d:%02d - reload epg.dat\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec))
				
		if config.plugins.epgdd.checkepgfile.value and config.plugins.epgdd.nocheck.value:
			if not os.path.isfile('%s%s' % (config.plugins.epgdd.direct.value, config.plugins.epgdd.epgname.value)):
				logging('%02d:%02d:%d %02d:%02d:%02d - restore epg.dat\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec))
				self.loadepgdat()
		self.timermin.startLongTimer(60)

	def loadepgdat(self):
		config.plugins.epgdd.nocheck.value = False
		now = time.localtime(time.time())
		try:
			if self.isServerOnline():
				config.plugins.epgdd.leghtfile.value = int(urllib.urlopen(config.plugins.epgdd.url.value).info()['content-length'])
				config.plugins.epgdd.leghtfile.save()
				configfile.save()
				if os.path.isfile('%s%s' % (config.plugins.epgdd.direct.value, config.plugins.epgdd.epgname.value)):
					os.chmod('%s%s' % (config.plugins.epgdd.direct.value, config.plugins.epgdd.epgname.value), stat.S_IWRITE)
				urllib.urlretrieve (config.plugins.epgdd.url.value, '/tmp/epg.dat.gz')
				if os.path.isfile('/tmp/epg.dat.gz'):
					inFile = gzip.GzipFile('/tmp/epg.dat.gz', 'rb')
					s = inFile.read()
					inFile.close()
					outFile = open('%s%s' % (config.plugins.epgdd.direct.value, config.plugins.epgdd.epgname.value), 'wb')
					outFile.write(s)
					outFile.close()
					if os.path.isfile('/tmp/epg.dat.gz'):
						os.chmod('/tmp/epg.dat.gz', stat.S_IWRITE)
						os.remove('/tmp/epg.dat.gz')
					self.epgcash_do()
					logging('%02d:%02d:%d %02d:%02d:%02d - Auto Donwload & Unzip epg.dat.gz successful\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec))
					config.plugins.epgdd.lastupdate.value = _('last epg.dat updated - %02d:%02d:%d %02d:%02d:%02d' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec))
					config.plugins.epgdd.lastupdate.save()
					configfile.save()
			else:
				logging('%02d:%02d:%d %02d:%02d:%02d - %s not respond\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, config.plugins.epgdd.url.value.split('/')[2]))
		except Exception as e:
			logging('%02d:%02d:%d %02d:%02d:%02d - %s\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, str(e)))
		config.plugins.epgdd.nocheck.value = True

	def epgcash_do(self):
		now = time.localtime(time.time())
		if config.plugins.epgdd.flush.value:
			try:
				epgcache = eEPGCache.getInstance()
				epgcache.flushEPG()
			except Exception as e:
				logging('%02d:%02d:%d %02d:%02d:%02d - %s - image not suuport flushEPG\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, str(e)))
			try:	
				epgcache = new.instancemethod(_enigma.eEPGCache_load, None, eEPGCache)
				epgcache = eEPGCache.getInstance().load()
			except Exception as e:
				logging('%02d:%02d:%d %02d:%02d:%02d - %s\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, str(e)))
		else:
			logging('%02d:%02d:%d %02d:%02d:%02d - EPGFlush turn off\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec))

	def isServerOnline(self):
		now = time.localtime(time.time())
		try:
			socket.gethostbyaddr(config.plugins.epgdd.url.value.split('/')[2])
		except Exception as e:
			logging('%02d:%02d:%d %02d:%02d:%02d - %s\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, str(e)))
			return False
		return True

class get_source(Screen):
	skin = """
	<screen name="ChoiceSource" position="center,160" size="850,255" title="Choice epg.dat source">
		<widget source="key_red" render="Label" position="20,220" zPosition="2" size="170,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
		<widget source="key_green" render="Label" position="190,220" zPosition="2" size="170,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />	
		<ePixmap position="20,250" zPosition="1" size="170,2" pixmap="~/images/red.png" alphatest="blend" />
		<ePixmap position="190,250" zPosition="1" size="170,2" pixmap="~/images/green.png" alphatest="blend" />
		<widget source="menu" render="Listbox" position="15,10" size="820,250" itemHeight="25" scrollbarMode="showOnDemand">
			<convert type="TemplatedMultiContent">
				{"template": [
					MultiContentEntryText(pos = (10, 2), size = (580, 25), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel
					],
					"fonts": [gFont("Regular", 20),gFont("Regular", 20)],
					"itemHeight": 25
				}
			</convert>
		</widget>
	</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/epgdd")
		self.setTitle(_("Choice epg.dat source"))
		self["shortcuts"] = ActionMap(['SetupActions', 'ColorActions', 'MenuActions'],
		{
			"cancel": self.cancel,
			"back": self.cancel,
			"red": self.cancel,
			"green": self.choice,
			'ok': self.choice
		})
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Choice"))
		self.list = []
		self["menu"] = List(self.list)
		self.CfgMenu()
		
	def CfgMenu(self):
		self.list = []
		if os.path.isfile(resolveFilename(SCOPE_PLUGINS, "Extensions/epgdd/epghosts.txt")):
			for line in open(resolveFilename(SCOPE_PLUGINS, "Extensions/epgdd/epghosts.txt")):
				if line.startswith('http://'):
					self.list.append((line.strip().rstrip('\r').rstrip('\n'), line.strip().rstrip('\r').rstrip('\n')))
		self["menu"].setList(self.list)
		self["actions"] = ActionMap(["OkCancelActions"], {"cancel": self.close}, -1)
	
	def choice(self):
		now = time.localtime(time.time())
		if self["menu"].getCurrent()[0] is not None:
			config.plugins.epgdd.url.value = self["menu"].getCurrent()[0]
			logging('%02d:%02d:%d %02d:%02d:%02d - set source %s\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, config.plugins.epgdd.url.value))
			config.plugins.epgdd.url.save()
			configfile.save()
		self.close()
		
	def cancel(self):
		self.close()

SKIN_EPG = """
<screen name="get_epgdat" position="center,140" size="625,35" title="Please wait">
  <widget source="status" render="Label" position="10,5" size="605,22" zPosition="2" font="Regular; 20" halign="center" transparent="2" />
</screen>"""

class get_epgdat(Screen):
	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self.session = session
		self.skin = SKIN_EPG
		self.setTitle(_('Please wait'))
		self['status'] = StaticText()
		config.plugins.epgdd.nocheck.value = False
		now = time.localtime(time.time())
		if self.isServerOnline():
			try:
				config.plugins.epgdd.leghtfile.value = int(urllib.urlopen(config.plugins.epgdd.url.value).info()['content-length'])
				config.plugins.epgdd.leghtfile.save()
				configfile.save()
				urllib.urlretrieve (config.plugins.epgdd.url.value, '/tmp/epg.dat.gz')
				if os.path.isfile('/tmp/epg.dat.gz'):
					inFile = gzip.GzipFile('/tmp/epg.dat.gz', 'rb')
					s = inFile.read()
					inFile.close()
					outFile = open('%s%s' % (config.plugins.epgdd.direct.value, config.plugins.epgdd.epgname.value), 'wb')
					outFile.write(s)
					outFile.close()
					if os.path.isfile('/tmp/epg.dat.gz'):
						os.remove('/tmp/epg.dat.gz')
					if os.path.isfile('%s%s' % (config.plugins.epgdd.direct.value, config.plugins.epgdd.epgname.value)):
						os.chmod('%s%s' % (config.plugins.epgdd.direct.value, config.plugins.epgdd.epgname.value), 0755)
					self.epgcash_do()
					self['status'].text = _('Download epg.dat successful')
					logging('%02d:%02d:%d %02d:%02d:%02d - Manual Donwload & Unzip epg.dat.gz successful\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec))
					config.plugins.epgdd.lastupdate.value = _('last epg.dat updated - %02d:%02d:%d %02d:%02d:%02d' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec))
					config.plugins.epgdd.lastupdate.save()
					configfile.save()
			except Exception as e:
				self['status'].text = _('Manual Donwloading epg.dat.gz error')
				logging('%02d:%02d:%d %02d:%02d:%02d - %s\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, str(e)))
		else:
			self['status'].text = _('%s not respond' % config.plugins.epgdd.url.value.split('/')[2])
			logging('%02d:%02d:%d %02d:%02d:%02d - %s not respond\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, config.plugins.epgdd.url.value.split('/')[2]))
		config.plugins.epgdd.nocheck.value = True
		self.timer = enigma.eTimer() 
		self.timer.callback.append(self.endshow)
		self.timer.startLongTimer(3)

	def epgcash_do(self):
		now = time.localtime(time.time())
		if config.plugins.epgdd.flush.value:
			try:
				epgcache = eEPGCache.getInstance()
				epgcache.flushEPG()
			except Exception as e:
				logging('%02d:%02d:%d %02d:%02d:%02d - %s - image not suuport flushEPG\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, str(e)))
			try:	
				epgcache = new.instancemethod(_enigma.eEPGCache_load, None, eEPGCache)
				epgcache = eEPGCache.getInstance().load()
			except Exception as e:
				logging('%02d:%02d:%d %02d:%02d:%02d - %s\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, str(e)))
		else:
			logging('%02d:%02d:%d %02d:%02d:%02d - EPGFlush turn off\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec))

	def endshow(self):
		self.timer.stop()
		self.close()
		
	def isServerOnline(self):
		now = time.localtime(time.time())
		try:
			socket.gethostbyaddr(config.plugins.epgdd.url.value.split('/')[2])
		except Exception as e:
			logging('%02d:%02d:%d %02d:%02d:%02d - %s\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, str(e)))
			return False
		return True

def main(session, **kwargs):
	session.open(epgdd)

pEpg = Check_EPG()

def sessionstart(reason,session=None, **kwargs):
	if reason == 0:
		pEpg.gotSession(session)

def Plugins(**kwargs):
	result = [
		PluginDescriptor(
			where = [PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART],
			fnc = sessionstart
		),
		PluginDescriptor(
			name=_("2boom's Auto EPG Downloader"),
			description = _('EPG from %s') % config.plugins.epgdd.url.value.split('/')[2],
			where = PluginDescriptor.WHERE_PLUGINMENU,
			icon = 'epgdd.png',
			fnc = main
		),
	]
	if config.plugins.epgdd.menuext.value:
		result.append(PluginDescriptor(
			name=_("2boom's Auto EPG Downloader"),
			description = _('EPG from %s') % config.plugins.epgdd.url.value.split('/')[2],
			where = PluginDescriptor.WHERE_EXTENSIONSMENU,
			fnc = main
			))
	return result
