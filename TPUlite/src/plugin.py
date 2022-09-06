# -*- coding: utf-8 -*-
# Triolan lite proxy updater
# Copyright (c) 2boom 2014
# v.0.2-r0
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

import os
import sys
import os.path
import re
import gettext
from enigma import eTimer, eEnv
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from Components.config import getConfigListEntry, ConfigText, ConfigClock, ConfigYesNo, ConfigLocations, ConfigSubsection, ConfigSelection, config, configfile
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.ScrollLabel import ScrollLabel
from Components.ActionMap import ActionMap
from Components.Language import language
from Components.Sources.List import List
from Components.Label import Label
from Components.Console import Console as iConsole
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from GlobalActions import globalActionMap

lang = language.getLanguage()
os.environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("TPUlite", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/TPUlite/locale/"))


def _(txt):
	t = gettext.dgettext("TPUlite", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t


config.plugins.tpulite = ConfigSubsection()
config.plugins.tpulite.menuext = ConfigYesNo(default=True)
config.plugins.tpulite.ip = ConfigText(default='000.000.000.000', visible_width=150, fixed_size=False)
config.plugins.tpulite.bname = ConfigText(default='Triolan', visible_width=250, fixed_size=False)
config.plugins.tpulite.rpassw = ConfigText(default='', visible_width=150, fixed_size=False)
config.plugins.tpulite.servicetype = ConfigSelection(default='1', choices=[
		('1', _("TV")),
		('2', _("LiveStreamer")),
		('4097', _("GStreamer")),
		])


def remove_line(filename, what):
	if os.path.isfile(filename):
		file_read = open(filename).readlines()
		file_write = open(filename, 'w')
		for line in file_read:
			if what not in line:
				file_write.write(line)
		file_write.close()


def add_line(filename, what):
	if os.path.isfile(filename):
		with open(filename, 'a') as file_out:
			file_out.write(what)
			file_out.close()


class rpulite(Screen, ConfigListScreen):
	skin = """
	<screen name="rpulite" position="265,160" size="750,360" title="2boom's Triolan lite proxy updater">
  		<widget position="15,10" size="720,125" name="config" scrollbarMode="showOnDemand" />
  		<ePixmap position="635,260" zPosition="2" size="100,60" pixmap="~/images/TRIOLAN.png" alphaTest="blend" />
  		<eLabel position="30,140" size="690,2" backgroundColor="grey" zPosition="5" />
  		<ePixmap position="10,355" zPosition="1" size="165,2" pixmap="~/images/red.png" alphaTest="blend" />
  		<widget source="key_red" render="Label" position="10,325" zPosition="2" size="165,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" transparent="1" />
  		<ePixmap position="175,355" zPosition="1" size="165,2" pixmap="~/images/green.png" alphaTest="blend" />
  		<widget source="key_green" render="Label" position="175,325" zPosition="2" size="165,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" transparent="1" />
  		<ePixmap position="340,355" zPosition="1" size="230,2" pixmap="~/images/yellow.png" alphaTest="blend" />
  		<widget source="key_yellow" render="Label" position="340,325" zPosition="2" size="230,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" transparent="1" />
  		<ePixmap position="570,355" zPosition="1" size="165,2" pixmap="~/images/blue.png" alphaTest="blend" />
  		<widget source="key_blue" render="Label" position="570,325" zPosition="2" size="165,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" transparent="1" />
  		<widget name="text" position="15,255" size="610,48" font="Regular;22" horizontalAlignment="left" />
	</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/TPUlite")
		self.iConsole = iConsole()
		self.keyext = config.plugins.tpulite.menuext.value
		self.newproxy = ''
		self.update_system()
		self.list = []
		self.list.append(getConfigListEntry(_("Input new proxy ip"), config.plugins.tpulite.ip))
		self.list.append(getConfigListEntry(_("Select service type in default bouquet"), config.plugins.tpulite.servicetype))
		self.list.append(getConfigListEntry(_("Input Name of default bouquet"), config.plugins.tpulite.bname))
		self.list.append(getConfigListEntry(_("Input password (if needed)"), config.plugins.tpulite.rpassw))
		self.list.append(getConfigListEntry(_("Proxy updater in ExtensionMenu"), config.plugins.tpulite.menuext))
		ConfigListScreen.__init__(self, self.list)
		self["text"] = ScrollLabel("")
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("IP & Ch.List Update"))
		self["key_blue"] = StaticText(_("Update IP"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.cancel,
			"cancel": self.cancel,
			"green": self.save,
			"yellow": self.update_all,
			"blue": self.update_ip,
			"ok": self.ok_key,
		}, -2)
		self.onShow.append(self.listuserbouquet)

	def listuserbouquet(self):
		self.setTitle(_("2boom's Triolan lite proxy updater"))

	def ok_key(self):
		status = 'Unknow'
		if os.path.isfile('/usr/bin/curl'):
			self.iConsole.ePopen("curl -I -m1 '%s:8888'" % config.plugins.tpulite.ip.value, self.Ondisplay, status)
		else:
			self["text"].setText('Current userbouquet proxy: %s  Status: %s' % (config.plugins.tpulite.ip.value, status))

	def Ondisplay(self, result, retval, extra_args):
		status = extra_args
		for line in result.splitlines(True):
			if 'HTTP/' in result and '200' in result:
				status = 'OK'
				break
		self["text"].setText('Current proxy: %s  Status: %s' % (config.plugins.tpulite.ip.value, status))

	def save(self):
		for i in self["config"].list:
			i[1].save()
		configfile.save()
		self.mbox = self.session.open(MessageBox, (_("configuration is saved")), MessageBox.TYPE_INFO, timeout=6)

	def update_system(self):
		if os.path.isfile('/etc/hosts'):
			for line in open('/etc/hosts'):
				if 'triolan' in line:
					config.plugins.tpulite.ip.value = line.split('\t')[0]

	def cancel(self):
		for i in self["config"].list:
			i[1].cancel()
		self.session.openWithCallback(self.close, reloadsl)

	def update_ip(self):
		config.plugins.tpulite.servicetype.save()
		config.plugins.tpulite.bname.save()
		for i in self["config"].list:
			i[1].save()
		configfile.save()
		self["text"].setText('')
		self.session.open(get_ip)

	def update_all(self):
		#self.session.open(get_ip)
		self.session.open(get_chlist)
		self.session.open(get_ip)
		self["text"].setText('')
		self["text"].setText(_('userbouquet.triolan_tmp.tv added or updated'))


class reloadsl(Screen):
	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self.session = session
		self.skin = SKIN_DWN
		self.newproxy = ''
		self.setTitle(_("Please wait"))
		self["status"] = StaticText()
		self.iConsole = iConsole()
		self["status"].text = _("Reload servicelist")
		self.iConsole.ePopen('wget -q -O - http://root:%s@127.0.0.1/web/servicelistreload?mode=0 && sleep 2' % config.plugins.tpulite.rpassw.value, self.cancel)

	def cancel(self, result, retval, extra_args):
		self.close()


SKIN_DWN = """
<screen name="get_epg_data" position="center,140" size="625,35" title="Please wait">
  <widget source="status" render="Label" position="10,5" size="605,22" zPosition="2" font="Regular; 20" horizontalAlignment="center" transparent="2" />
</screen>"""


class get_chlist(Screen):
	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self.session = session
		self.skin = SKIN_DWN
		self.newproxy = ''
		self.setTitle(_("Please wait"))
		self["status"] = StaticText()
		self.iConsole = iConsole()
		self["status"].text = _("Donwloading ip & channel list")
		if os.path.isfile('/tmp/triolan.m3u'):
			os.remove('/tmp/triolan.m3u')
		self.iConsole.ePopen("wget -q 'http://triolan.tv/getPlaylist.ashx' -O /tmp/triolan.m3u", self.user_upg2)

	def user_upg2(self, result, retval, extra_args):
		self.newproxy = config.plugins.tpulite.ip.value
		if retval == 0:
			tmp_proxy = '%3a//triolan%3a8888/'
			self.oldproxy = desk_tmp = channel_ref = ''
			if config.plugins.tpulite.servicetype.value == '2':
				stream_tmp = 'http%3a//127.0.0.1%3a88/httpstream%3a//'
			else:
				stream_tmp = ''
			if os.path.isfile('/tmp/triolan.m3u'):
				if os.path.isfile('/etc/enigma2/userbouquet.triolan_tmp.tv'):
					os.remove('/etc/enigma2/userbouquet.triolan_tmp.tv')
				with open('/etc/enigma2/userbouquet.triolan_tmp.tv', 'w') as outfile:
					outfile.write('#NAME %s\r\n' % config.plugins.tpulite.bname.value)
					for line in open('/tmp/triolan.m3u'):
						if 'udp://@' in line:
							channel_ref = ':0:1:0:0:0:0:0:0:0'
							if config.plugins.tpulite.servicetype.value == '4097':
								outfile.write('#SERVICE %s%s:http%s%s:%s\r\n' % (config.plugins.tpulite.servicetype.value, channel_ref, tmp_proxy, line.replace('udp://@', 'udp/')[:-2].replace(':', '%3a'), desk_tmp))
							else:
								outfile.write('#SERVICE 1%s:%shttp%s%s:%s\r\n' % (channel_ref, stream_tmp, tmp_proxy, line.replace('udp://@', 'udp/')[:-2].replace(':', '%3a'), desk_tmp))
							outfile.write('#DESCRIPTION %s\r\n' % desk_tmp)
						elif '#EXTINF:0' in line:
							desk_tmp = line.split(',')[-1][:-2]
				outfile.close()
				if os.path.isfile('/etc/enigma2/userbouquet.triolan_tmp.tv') and os.path.isfile('/etc/enigma2/bouquets.tv'):
					remove_line('/etc/enigma2/bouquets.tv', 'triolan_tmp')
					remove_line('/etc/enigma2/bouquets.tv', 'LastScanned')
					with open('/etc/enigma2/bouquets.tv', 'a') as outfile:
						outfile.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.triolan_tmp.tv" ORDER BY bouquet\r\n')
						outfile.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.LastScanned.tv" ORDER BY bouquet\r\n')
					outfile.close()
		self.close()


class get_ip(Screen):
	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self.session = session
		self.skin = SKIN_DWN
		self.newproxy = ''
		self.setTitle(_("Please wait"))
		self["status"] = StaticText()
		self.iConsole = iConsole()
		self["status"].text = _("Donwloading ip & channel list")
		self.iConsole.ePopen("wget -q 'http://www.satorbita.com/iptv/free/1triolan.php?list.m3u' -O /tmp/triolan.m3u", self.get_ip2)

	def get_ip2(self, result, retval, extra_args):
		self.newproxy = ''
		if retval == 0:
			if os.path.isfile('/tmp/triolan.m3u'):
				for line in open('/tmp/triolan.m3u'):
					if 'http://' in line:
						self.newproxy = line.split(':')[1].replace('//', '')
						break
			config.plugins.tpulite.ip.value = self.newproxy
			remove_line('/etc/hosts', 'triolan')
			add_line('/etc/hosts', '%s\ttriolan\t\ttriolan\n' % self.newproxy)
		else:
			self["status"].text = _("error...")
		config.plugins.tpulite.ip.save()
		config.save()
		self.close()


def main(session, **kwargs):
	session.open(rpulite)


def Plugins(**kwargs):
	list = [PluginDescriptor(name=_("2boom's Triolan lite proxy updater"), description=_("update Triolan iptv proxy"), where=[PluginDescriptor.WHERE_PLUGINMENU], icon="rpu.png", fnc=main)]
	if config.plugins.tpulite.menuext.value:
		list.append(PluginDescriptor(name=_("Triolan proxy lite updater"), description=_("update Triolan iptv proxy"), where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main))
	return list
