#!/usr/bin/python
# -*- coding: utf-8 -*-
# Add/Remove bouquet files
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

import os, sys, os.path
import re
import gettext
from enigma import eTimer, eEnv
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import pathExists, fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from Tools.LoadPixmap import LoadPixmap
from Components.config import getConfigListEntry, ConfigText, ConfigClock, ConfigYesNo, ConfigLocations, ConfigSubsection, ConfigSelection, config, configfile
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.ScrollLabel import ScrollLabel
from Components.ActionMap import ActionMap
from Components.Language import language
from Components.Sources.List import List
from Components.MenuList import MenuList
from Components.Label import Label
from Components.Console import Console as iConsole
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from GlobalActions import globalActionMap

lang = language.getLanguage()
os.environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("ARbouquet", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/ARbouquet/locale/"))

def _(txt):
	t = gettext.dgettext("ARbouquet", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

config.plugins.arbouquet = ConfigSubsection()
config.plugins.arbouquet.menuext = ConfigYesNo(default = True)
config.plugins.arbouquet.passw = ConfigText(default='', visible_width = 150, fixed_size = False)
config.plugins.arbouquet.bouquettype = ConfigSelection(default = '.tv', choices = [
		('.tv', _("TV")),
		('.radio', _("Radio")),
		])
	
def remove_line(filename, what):
	if os.path.isfile(filename):
		file_read = open(filename).readlines()
		file_write = open(filename, 'w')
		for line in file_read:
			if what not in line:
				file_write.write(line)
		file_write.close()

class ARbouquet(Screen):
	skin = """
	<screen name="ARbouquet" position="265,140" size="750,445" title="2boom's add/remove bouquet">
  		<ePixmap position="10,440" zPosition="1" size="165,2" pixmap="~/images/red.png" alphatest="blend" />
  		<ePixmap position="175,440" zPosition="1" size="165,2" pixmap="~/images/green.png" alphatest="blend" />
  		<ePixmap position="340,440" zPosition="3" size="165,2" pixmap="~/images/yellow.png" alphatest="blend" />
  		<widget source="key_red" render="Label" position="10,410" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" transparent="1" />
  		<widget source="key_green" render="Label" position="175,410" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" transparent="1" />
  		<widget source="key_yellow" render="Label" position="340,410" zPosition="3" size="165,30" font="Regular;20" halign="center" valign="center" transparent="1" />
    		<widget source="menu" render="Listbox" position="15,5" size="720,400" scrollbarMode="showOnDemand">
    			<convert type="TemplatedMultiContent">
     				{"template": [
					MultiContentEntryText(pos = (70, 2), size = (675, 25), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel
					MultiContentEntryText(pos = (80, 29), size = (665, 18), font=1, flags = RT_HALIGN_LEFT, text = 1), # index 3 is the Description
					MultiContentEntryPixmapAlphaTest(pos = (5, 5), size = (50, 40), png = 2), # index 4 is the pixmap
					],
					"fonts": [gFont("Regular", 23),gFont("Regular", 16)],
					"itemHeight": 50
				}
   			</convert>
  		</widget>
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/ARbouquet")
		self.iConsole = iConsole()
		self.session = session
		self.list = []
		self.indexpos = None
		self.item_name = ''
		self["menu"] = List(self.list)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"cancel": self.reload_bq,
				"red": self.reload_bq,
				"green": self.make_bq,
				"yellow": self.remove_bq,
			},-1)
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Add"))
		self["key_yellow"] = StaticText(_("Remove"))
		self.bq_list()
		self.onLayoutFinish.append(self.make_title)
		
	def bq_list(self):
		self.list = []
		file_name = boquet_name = ''
		png_name = LoadPixmap(cached=True, path = resolveFilename(SCOPE_PLUGINS, "Extensions/ARbouquet/images/folder.png"))
		if os.path.isfile('/etc/enigma2/bouquets%s' % config.plugins.arbouquet.bouquettype.value):
			for line in open('/etc/enigma2/bouquets%s' % config.plugins.arbouquet.bouquettype.value):
				if line.startswith('#SERVICE'):
					file_name = line.split('"')[1].strip('\r\n')
					if '/etc/enigma2/%s' % file_name is not '/etc/enigma2/bouquets%s' % config.plugins.arbouquet.bouquettype.value:
						if os.path.isfile('/etc/enigma2/%s' % file_name):
							for name in open('/etc/enigma2/%s' % file_name):
								if name.startswith('#NAME'):
									boquet_name = name.replace('#NAME', '').strip('\r\n').strip()
									break
					self.list.append((boquet_name, file_name, png_name))
		self["menu"].setList(self.list)
		if self.indexpos is not None:
			self["menu"].setIndex(self.indexpos)
		
	def make_title(self):
		self.setTitle(_("2boom's add/remove bouquet"))
		
	def reload_bq(self):
		self.session.openWithCallback(self.close, reloadsl)

	def make_bq(self):
		self.session.openWithCallback(self.bq_list, AddScreen)
		
	def remove_bq(self):
		self.item_name = self["menu"].getCurrent()[1]
		if self.item_name:
			remove_line('/etc/enigma2/bouquets%s' % config.plugins.arbouquet.bouquettype.value, self.item_name)
			if fileExists('/etc/enigma2/%s' % self.item_name):
				os.rename('/etc/enigma2/%s' % self.item_name, '/etc/enigma2/%s.del' % self.item_name)
			self.mbox = self.session.open(MessageBox,(_("%s removed" % self.item_name)), MessageBox.TYPE_INFO, timeout = 4 )
		self.bq_list()

SKIN_DWN = """
<screen name="reloadsl" position="center,140" size="625,35" title="Please wait">
	<widget source="status" render="Label" position="10,5" size="605,22" zPosition="2" font="Regular; 20" halign="center" transparent="2" />
</screen>"""

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
		self.iConsole.ePopen('wget -q -O - http://root:%s@127.0.0.1/web/servicelistreload?mode=0 && sleep 2' % config.plugins.arbouquet.passw.value, self.cancel)
		
	def cancel(self, result, retval, extra_args):
		self.close()

class AddScreen(Screen):
	skin = """
	<screen name="AddScreen" position="center,140" size="750,445" title="Add bouquetfile">
  		<widget name="list" position="20,5" size="710,400" scrollbarMode="showOnDemand" />
 		 <ePixmap position="20,440" zPosition="1" size="165,2" pixmap="~/images/red.png" alphatest="blend" />
  		<widget source="key_red" render="Label" position="20,410" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/ARbouquet")
		self.session = session
		self.file_name = ''
		self.setTitle(_("Add bouquetfile"))
		self.add_menu()
		self["key_red"] = StaticText(_("Close"))
		self["actions"] = ActionMap(["OkCancelActions","ColorActions"], {"ok": self.run, "red": self.close, "cancel": self.close}, -1)

	def add_menu(self):
		list = []
		if pathExists('/etc/enigma2'):
			list = os.listdir('/etc/enigma2')
			list = [x for x in list if x.endswith(config.plugins.arbouquet.bouquettype.value + '.del')]
		self["list"] = MenuList(list)

	def run(self):
		self.file_name = self["list"].getCurrent().rstrip('.del')
		if self.file_name is not None:
			if fileExists('/etc/enigma2/%s.del' % self.file_name):
				os.rename('/etc/enigma2/%s.del' % self.file_name, '/etc/enigma2/%s' % self.file_name)
			remove_line('/etc/enigma2/bouquets%s' % config.plugins.arbouquet.bouquettype.value, 'LastScanned')
			with open('/etc/enigma2/bouquets%s' % config.plugins.arbouquet.bouquettype.value, 'a') as out_file:
				if config.plugins.arbouquet.bouquettype.value == '.tv':
					out_file.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet\r\n' % self.file_name)
					out_file.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.LastScanned.tv" ORDER BY bouquet\r\n')
				else:
					out_file.write('#SERVICE 1:7:2:0:0:0:0:0:0:0:FROM BOUQUET "%s" ORDER BY bouquet\r\n' % self.file_name)
				out_file.close()
			self.mbox = self.session.open(MessageBox,(_("%s added" % self.file_name)), MessageBox.TYPE_INFO, timeout = 4 )
		if not fileExists('/etc/enigma2/userbouquet.LastScanned.tv'):
			with open('/etc/enigma2/userbouquet.LastScanned.tv', 'a') as last:
				last.write('#NAME Last Scanned\r\n')
				last.close()
		self.cancel()

	def cancel(self):
		self.close()

class ARconfig(Screen, ConfigListScreen):
	skin = """
	<screen name="ARconfig" position="265,160" size="750,360" title="2boom's add/remove bouquet config">
  		<widget position="15,10" size="720,100" name="config" scrollbarMode="showOnDemand" />
  		<ePixmap position="10,355" zPosition="1" size="165,2" pixmap="~/images/red.png" alphatest="blend" />
  		<widget source="key_red" render="Label" position="10,325" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" transparent="1" />
  		<ePixmap position="175,355" zPosition="1" size="180,2" pixmap="~/images/green.png" alphatest="blend" />
 	 	<widget source="key_green" render="Label" position="175,325" zPosition="2" size="180,30" font="Regular;20" halign="center" valign="center" transparent="1" />
  	</screen>"""
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/ARbouquet")
		self.list = []
		self.list.append(getConfigListEntry(_("Select bouquet type"), config.plugins.arbouquet.bouquettype))
		self.list.append(getConfigListEntry(_("Input password (if needed)"), config.plugins.arbouquet.passw))
		self.list.append(getConfigListEntry(_("Add/remove bouquet in ExtensionMenu"), config.plugins.arbouquet.menuext))
		ConfigListScreen.__init__(self, self.list)
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["setupActions"] = ActionMap(["SetupActions", "OkCancelActions", "ColorActions"],
		{
			"red": self.cancel,
			"cancel": self.cancel,
			"green": self.save,
		}, -2)
		self.onShow.append(self.listuserbouquet)

	def listuserbouquet(self):
		self.setTitle(_("2boom's add/remove bouquet config"))
		
	def save(self):
		for i in self["config"].list:
			i[1].save()
		configfile.save()
		self.mbox = self.session.open(MessageBox,(_("configuration is saved")), MessageBox.TYPE_INFO, timeout = 4 )

	def cancel(self):
		for i in self["config"].list:
			i[1].cancel()
		self.close(False)

def main(session, **kwargs):
	session.open(ARconfig)

def extmain(session, **kwargs):
	session.open(ARbouquet)

def Plugins(**kwargs):
	result = [
		PluginDescriptor(
			name=_("2boom's ARbouquet"),
			description=_("add/remove bouquet"),
			where = [PluginDescriptor.WHERE_PLUGINMENU],
			icon="arb.png",
			fnc=main
		),
		PluginDescriptor(
			name=_("add/remove bouquet"),
			description=_("add/remove bouquet"),
			where = [PluginDescriptor.WHERE_EXTENSIONSMENU],
			fnc=extmain
		),
	]
	return result
