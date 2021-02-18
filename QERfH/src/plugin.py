#!/usr/bin/python
# -*- coding: utf-8 -*-
#QuickEmuRestart for Hotkey
#Copyright (c) 2boom 2017
# v.0.1-r4
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

from Components.Language import language
from Components.Sources.StaticText import StaticText
from Components.config import config
from Screens.Screen import Screen
from Components.Console import Console
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import fileExists, resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS
from enigma import ePoint, getDesktop, iServiceInformation
from os import environ
import gettext
import os
import sys

if fileExists(resolveFilename(SCOPE_PLUGINS, "Extensions/AlternativeSoftCamManager/Softcam.pyo")):
	from Plugins.Extensions.AlternativeSoftCamManager.Softcam import getcamcmd

lang = language.getLanguage()
environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("qerfh", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/QERfH/locale/"))

def _(txt):
	t = gettext.dgettext("qerfh", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

SKIN_DWN = """
<screen name="get_epg_data" position="center,140" size="625,35" title="Please wait">
  <widget source="status" render="Label" position="10,5" size="605,22" zPosition="2" font="Regular; 20" halign="center" transparent="2" />
</screen>"""

class QERfH(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.Console = Console()
		self.skin = SKIN_DWN
		self.setTitle(_("Please wait"))
		self["status"] = StaticText()
		self.service = None
		if fileExists(resolveFilename(SCOPE_PLUGINS, "Extensions/AlternativeSoftCamManager/Softcam.pyo")):
			self.service = self.session.nav.getCurrentlyPlayingServiceReference()
			emunam = config.plugins.AltSoftcam.actcam.value
			if emunam != "none":
				self.Console.ePopen("killall -15 %s" % emunam)
				if self.service:
					self.session.nav.stopService()
				self.Console.ePopen("%s && sleep 4" % getcamcmd(emunam), self.finish)
		if fileExists("/etc/init.d/softcam") and fileExists("/etc/init.d/cardserver"):
			if self.isCamNone('softcam') and self.isCamNone('cardserver'):
				self.notFoundActiveCam()
		if fileExists("/etc/init.d/softcam") or fileExists("/etc/init.d/cardserver"):
			if fileExists("/etc/init.d/softcam") and not self.isCamNone('softcam'):
				self.Console.ePopen("/etc/init.d/softcam restart && sleep 4", self.finish)
			if fileExists("/etc/init.d/cardserver") and not self.isCamNone('cardserver'):
				self.Console.ePopen("/etc/init.d/cardserver restart && sleep 4", self.finish)
			self["status"].text = _("Restarting %s") % self.emuname()
			
	def notFoundActiveCam(self):
		self.close()
			
	def finish(self, result, retval, extra_args):
		if self.service is not None:
			self.session.nav.playService(self.service)
		self.close()
		
	def isCamNone(self, camlink):
		if fileExists("/etc/init.d/%s" % camlink):
			if '# Placeholder for no cam' in open("/etc/init.d/%s" % camlink).read():
				return True
		return False

	def emuname(self):
		serlist = camdlist = None
		nameemu = nameser = []
		ecminfo = ''
		#Alternative SoftCam Manager 
		if os.path.isfile(resolveFilename(SCOPE_PLUGINS, "Extensions/AlternativeSoftCamManager/plugin.pyo")): 
			if config.plugins.AltSoftcam.actcam.value != "none": 
				return config.plugins.AltSoftcam.actcam.value 
			else: 
				return None
		#Pli
		elif fileExists("/etc/init.d/softcam") or fileExists("/etc/init.d/cardserver"):
			if fileExists("/etc/init.d/softcam") and not self.isCamNone('softcam'):
				for line in open("/etc/init.d/softcam"):
					if "echo" in line:
						nameemu.append(line)
				if len(nameemu) > 1:
					camdlist = "%s" % nameemu[1].split('"')[1]
			if fileExists("/etc/init.d/cardserver") and not self.isCamNone('cardserver'):
				for line in open("/etc/init.d/cardserver"):
					if "echo" in line:
						nameser.append(line)
				if len(nameser) > 1:
					serlist = "%s" % nameser[1].split('"')[1]
			if serlist is not None and camdlist is not None:
				return ("%s %s" % (serlist, camdlist))
			elif camdlist is not None:
				return "%s" % camdlist
			elif serlist is not None:
				return "%s" % serlist
			return ""
		else:
			emu = ""
			ecminfo = "%s %s" % (cardserver.split('\n')[0], emu.split('\n')[0])
		return ecminfo

def main(session, **kwargs):
	session.open(QERfH)

def Plugins(**kwargs):
	list = [PluginDescriptor(name=_("2boom's QuickEmuRestart for Hotkey"), description=_("quick restart softcam & cardserver for hotkey extentions"), where = [PluginDescriptor.WHERE_PLUGINMENU], icon="qerfh.png", fnc=main)]
	return list
