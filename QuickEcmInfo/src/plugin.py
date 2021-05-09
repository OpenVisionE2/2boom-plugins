#!/usr/bin/python
# -*- coding: utf-8 -*-
#QuickEcmInfo
#Copyright (c) 2boom 2012-14
# v.3.0-r0 26.05.2014
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

from Components.ActionMap import ActionMap
from Components.config import config, getConfigListEntry, ConfigText, ConfigInteger, ConfigClock, ConfigSelection, ConfigSubsection, ConfigYesNo, configfile, NoSave
from Components.ConfigList import ConfigListScreen
from GlobalActions import globalActionMap
from Components.ActionMap import readKeymap, removeKeymap
from enigma import ePoint, eTimer, getDesktop
from Components.Pixmap import Pixmap
from os import environ
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Tools.Directories import fileExists, resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS
from Screens.Standby import TryQuitMainloop
import gettext
from Screens.MessageBox import MessageBox
from Components.Language import language
from Components.Sources.StaticText import StaticText
import os
from os import environ

lang = language.getLanguage()
environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("qei", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/QuickEcmInfo/locale/"))


def _(txt):
	t = gettext.dgettext("qei", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t


##############################################################################
config.plugins.QuickEcm = ConfigSubsection()
config.plugins.QuickEcm.enabled = ConfigYesNo(default=True)
config.plugins.QuickEcm.keyname = ConfigSelection(default="KEY_HELP", choices=[
		("KEY_TEXT", "TEXT"),
		("KEY_SUBTITLE", "SUBTITLE"),
		("KEY_HELP", "HELP"),
		("KEY_TITLE", "PORTAL (8120/Amico)"),
		("KEY_TEEN", "<P (Fortis)"),
		])
config.plugins.QuickEcm.enabled.value = False
##############################################################################
SKIN_HD = """
<screen name="QuickEcmInfo" position="265,140" size="770,406" title="2boom's QuickEcmInfo SE" zPosition="1">
<eLabel position="20,33" size="730,2" backgroundColor="#00aaaaaa" zPosition="4" />
  <eLabel position="20,69" size="730,2" backgroundColor="#00aaaaaa" zPosition="4" />
  <eLabel position="20,299" size="730,2" backgroundColor="#00aaaaaa" zPosition="4" />
  <eLabel position="20,333" size="730,2" backgroundColor="#00aaaaaa" zPosition="4" />
  <eLabel position="50,368" size="670,2" backgroundColor="#00aaaaaa" zPosition="4" />
<widget source="session.CurrentService" render="Label" position="10,4" size="750,25" font="Regular; 22" zPosition="2" transparent="1" valign="top" noWrap="1" halign="center">
    <convert type="QuickEcmInfo2">boxdata</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="10,80" size="750,215" font="Regular; 23" zPosition="2" foregroundColor="#00ffffff" transparent="1" valign="top" noWrap="1" halign="center">
    <convert type="QuickEcmInfo2">ecmfile</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="20,40" size="480,25" font="Regular; 22" zPosition="2" foregroundColor="#00f0bf4f" transparent="1" valign="top" halign="left">
    <convert type="QuickEcmInfo2">emuname</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="500,40" size="250,25" font="Regular; 22" zPosition="2" foregroundColor="#00aaaaaa" transparent="1" valign="top" halign="right">
    <convert type="QuickEcmInfo2">txtcaid</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="5,304" size="755,25" font="Regular; 22" zPosition="2" foregroundColor="#00aaaaaa" transparent="1" valign="top" halign="center">
    <convert type="QuickEcmInfo2">caidbar</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="5,339" size="755,25" font="Regular; 22" zPosition="2" foregroundColor="#00aaaaaa" transparent="1" valign="top" halign="center">
    <convert type="QuickEcmInfo2">pids</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="5,375" size="755,25" font="Regular; 22" zPosition="2" foregroundColor="#00aaaaaa" transparent="1" valign="top" halign="center">
    <convert type="QuickEcmInfo2">bitrate</convert>
  </widget>
</screen>"""

##############################################################################


class QuickEcmInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin = SKIN_HD
		self.setTitle(_("2boom's QuickEcmInfo SE"))
##############################################################################


class QuickEcm():
	def __init__(self):
		self.dialog = None

	def gotSession(self, session):
		self.session = session
		keymap = '%sExtensions/QuickEcmInfo/keymap.xml' % resolveFilename(SCOPE_PLUGINS)
		global globalActionMap
		readKeymap(keymap)
		self.dialog = session.instantiateDialog(QuickEcmInfo)
		if 'displayHelp' in globalActionMap.actions:
			del globalActionMap.actions['displayHelp']
		elif 'showSherlock' in globalActionMap.actions:
			del globalActionMap.actions['showSherlock']
		globalActionMap.actions['showEcmInfo'] = self.ShowHide
##############################################################################

	def ShowHide(self):
		if config.plugins.QuickEcm.enabled.value:
			config.plugins.QuickEcm.enabled.value = False
			pEcm.dialog.hide()
		else:
			config.plugins.QuickEcm.enabled.value = True
			pEcm.dialog.show()


##############################################################################
pEcm = QuickEcm()
##############################################################################
skin_hdsetup = """
<screen name="qei_setup" position="center,160" size="750,370" title="2boom's QuickEcmInfo setup">
  	<widget position="15,10" size="720,200" name="config" scrollbarMode="showOnDemand" />
   	<ePixmap position="10,358" zPosition="1" size="165,2" pixmap="~/images/red.png" alphatest="blend" />
  	<widget source="key_red" render="Label" position="10,328" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
  	<ePixmap position="175,358" zPosition="1" size="165,2" pixmap="~/images/green.png" alphatest="blend" />
  	<widget source="key_green" render="Label" position="175,328" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
  	<ePixmap position="340,358" zPosition="1" size="200,2" pixmap="~/images/yellow.png" alphatest="blend" />
  	<widget source="yellow_key" render="Label" position="340,328" zPosition="2" size="200,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
</screen>"""
skin_sdsetup = """
<screen name="qei_setup" position="center,160" size="635,370" title="2boom's QuickEcmInfo setup">
  	<widget position="10,10" size="615,200" name="config" scrollbarMode="showOnDemand" />
  	 <ePixmap position="10,358" zPosition="1" size="165,2" pixmap="~/images/red.png" alphatest="blend" />
 	 <widget source="key_red" render="Label" position="10,328" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
  	<ePixmap position="175,358" zPosition="1" size="165,2" pixmap="~/images/green.png" alphatest="blend" />
  	<widget source="key_green" render="Label" position="175,328" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
  	<ePixmap position="340,358" zPosition="1" size="200,2" pixmap="~/images/yellow.png" alphatest="blend" />
  	<widget source="yellow_key" render="Label" position="340,328" zPosition="2" size="200,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
</screen>"""


class qei_setup(ConfigListScreen, Screen):
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/QuickEcmInfo")
		if getDesktop(0).size().width() == 1280:
			self.skin = skin_hdsetup
		else:
			self.skin = skin_sdsetup
		self.setTitle(_("2boom's QuickEcmInfo setup"))
		self.list = []
		self.list.append(getConfigListEntry(_("Select key to show QuickEcmInfo"), config.plugins.QuickEcm.keyname))
		ConfigListScreen.__init__(self, self.list)
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["yellow_key"] = StaticText(_("Restart enigma"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions", "EPGSelectActions"],
		{
			"red": self.cancel,
			"cancel": self.cancel,
			"green": self.save,
			"yellow": self.restart,
			"ok": self.save
		}, -2)

	def cancel(self):
		for i in self["config"].list:
			i[1].cancel()
		self.close(False)

	def restart(self):
		self.session.open(TryQuitMainloop, 3)

	def save(self):
		config.plugins.QuickEcm.keyname.save()
		configfile.save()
		with open(resolveFilename(SCOPE_PLUGINS, "Extensions/QuickEcmInfo/keymap.xml"), "w") as keyfile:
			keyfile.write('<keymap>\n\t<map context="GlobalActions">\n\t\t<key id="%s" mapto="showEcmInfo" flags="m" />\n\t</map>\n</keymap>' % config.plugins.QuickEcm.keyname.value)
			keyfile.close()
		self.mbox = self.session.open(MessageBox, (_("configuration is saved")), MessageBox.TYPE_INFO, timeout=4)
##############################################################################


def sessionstart(reason, session=None, **kwargs):
	if reason == 0:
		pEcm.gotSession(session)
##############################################################################


def main(session, **kwargs):
	session.open(qei_setup)
##############################################################################


def Plugins(**kwargs):
	result = [
		PluginDescriptor(
			where=[PluginDescriptor.WHERE_SESSIONSTART],
			fnc=sessionstart
		),
		PluginDescriptor(
			name=_("2boom's QuickEcmInfo"),
			description=_("2boom's QuickEcmInfo setup"),
			where=PluginDescriptor.WHERE_PLUGINMENU,
			icon='qei.png',
			fnc=main
		),
	]
	return result
