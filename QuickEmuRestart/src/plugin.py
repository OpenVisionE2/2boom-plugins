#!/usr/bin/python
# -*- coding: utf-8 -*-
# QuickEmuRestart plugin
# Copyright (c) 2boom 2012-14
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
from Screens.MessageBox import MessageBox
from Tools.Directories import fileExists
from GlobalActions import globalActionMap
from Components.ActionMap import loadKeymap, removeKeymap
from os import environ
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Console import Console
from Components.Language import language
from Components.config import config, getConfigListEntry, ConfigText, ConfigInteger, ConfigClock, ConfigSelection, ConfigSubsection, ConfigYesNo, configfile, NoSave
from Components.ConfigList import ConfigListScreen
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from Components.Sources.StaticText import StaticText
import os
import gettext
from os import environ

if fileExists(resolveFilename(SCOPE_PLUGINS, "Extensions/AlternativeSoftCamManager/Softcam.pyo")):
	from Plugins.Extensions.AlternativeSoftCamManager.Softcam import getcamcmd

lang = language.getLanguage()
environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("qemurestart", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/QuickEmuRestart/locale/"))


def _(txt):
	t = gettext.dgettext("qemurestart", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t


config.plugins.qer = ConfigSubsection()
config.plugins.qer.keyname = ConfigSelection(default="KEY_TEXT", choices=[
		("KEY_TEXT", "TEXT"),
		("KEY_SUBTITLE", "SUBTITLE"),
		("KEY_HELP", "HELP"),
		("KEY_PORTAL", "PORTAL (8120/Amico)"),
		("KEY_TEEN", "<P (Fortis)"),
		])
config.plugins.qer.time = ConfigInteger(default=6, limits=(1, 99))
##############################################################################


class QuickEmu():
	def __init__(self):
		self.dialog = None

	def gotSession(self, session):
		self.session = session
		self.Console = Console()
		keymap = '%sExtensions/QuickEmuRestart/keymap.xml' % resolveFilename(SCOPE_PLUGINS)
		global globalActionMap
		loadKeymap(keymap)
		globalActionMap.actions['showEmuRestart'] = self.restartCam

	def restartCam(self):
		camname = emunam = estart = estop = ""
# Alternative SoftCam Manager
		if fileExists(resolveFilename(SCOPE_PLUGINS, "Extensions/AlternativeSoftCamManager/Softcam.pyo")):
			service = self.session.nav.getCurrentlyPlayingServiceReference()
			emunam = config.plugins.AltSoftcam.actcam.value
			if emunam != "none":
				self.Console.ePopen("killall -15 %s" % emunam)
				if service:
					self.session.nav.stopService()
				self.Console.ePopen(getcamcmd(emunam))
				if service:
					self.session.nav.playService(service)
# PLI
		elif fileExists("/etc/init.d/softcam") or fileExists("/etc/init.d/cardserver"):
			if fileExists("/etc/init.d/cardserver"):
				self.Console.ePopen("/etc/init.d/cardserver restart")
			if fileExists("/etc/init.d/softcam"):
				self.Console.ePopen("/etc/init.d/softcam restart")
# TS-Panel
		elif fileExists("/etc/startcam.sh"):
			for line in open("/etc/startcam.sh"):
				if "script" in line:
					currentemu = line.split()[0]
			if fileExists("%s " % currentemu):
				self.Console.ePopen("%s cam_down & && %s cam_up &" % (currentemu, currentemu))
		try:
			if config.plugins.qer.time.value != 0:
				self.mbox = self.session.open(MessageBox, (_("%s  restarted...") % self.showcamname()), MessageBox.TYPE_INFO, timeout=config.plugins.qer.time.value)
		except:
			pass
#########################################################################################################

	def showcamname(self):
		nameemu = nameser = []
		camdlist = serlist = None
		#Alternative SoftCam Manager
		if os.path.isfile(resolveFilename(SCOPE_PLUGINS, "Extensions/AlternativeSoftCamManager/plugin.pyo")):
			if config.plugins.AltSoftcam.actcam.value != "none":
				return config.plugins.AltSoftcam.actcam.value
			else:
				return None
		#GlassSysUtil
		elif os.path.isfile("/tmp/ucm_cam.info"):
			return open("/tmp/ucm_cam.info").read()
		#Pli
		elif os.path.isfile("/etc/init.d/softcam") or os.path.isfile("/etc/init.d/cardserver"):
			if os.path.isfile("/etc/init.d/softcam"):
				for line in open("/etc/init.d/softcam"):
					if "echo" in line:
						nameemu.append(line)
				if len(nameemu) > 1:
					camdlist = "%s" % nameemu[1].split('"')[1]
			if os.path.isfile("/etc/init.d/cardserver"):
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
		#TS-Panel
		elif os.path.isfile("/etc/startcam.sh"):
			for line in open("/etc/startcam.sh"):
				if "script" in line:
					return "%s" % line.split("/")[-1].split()[0][:-3]
		else:
			return ''
#####################################################


class qer_setup(ConfigListScreen, Screen):
	skin = """
	<screen name="qer_setup" position="center,160" size="750,370" title="2boom's QuickEmuRestart">
  		<widget position="15,10" size="720,200" name="config" scrollbarMode="showOnDemand" />
   		<ePixmap position="10,358" zPosition="1" size="165,2" pixmap="~/images/red.png" alphatest="blend" />
  		<widget source="key_red" render="Label" position="10,328" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
  		<ePixmap position="175,358" zPosition="1" size="165,2" pixmap="~/images/green.png" alphatest="blend" />
  		<widget source="key_green" render="Label" position="175,328" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
	</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/QuickEmuRestart")
		self.setTitle(_("2boom's QuickEmuRestart"))
		self.list = []
		self.list.append(getConfigListEntry(_("Select key to Softcam restart"), config.plugins.qer.keyname))
		self.list.append(getConfigListEntry(_("Set time in sec message window is shown"), config.plugins.qer.time))
		ConfigListScreen.__init__(self, self.list)
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions", "EPGSelectActions"],
		{
			"red": self.cancel,
			"cancel": self.cancel,
			"green": self.save,
			"ok": self.save
		}, -2)

	def cancel(self):
		for i in self["config"].list:
			i[1].cancel()
		self.close(False)

	def TrueImage(self):
		if fileExists("/etc/issue"):
			for line in open("/etc/issue"):
				if "openpli" in line:
					return True
		return False

	def save(self):
		config.plugins.qer.keyname.save()
		config.plugins.qer.time.save()
		configfile.save()
		with open(resolveFilename(SCOPE_PLUGINS, "Extensions/QuickEmuRestart/keymap.xml"), "w") as keyfile:
			keyfile.write('<keymap>\n\t<map context="GlobalActions">\n\t\t<key id="%s" mapto="showEmuRestart" flags="m" />\n\t</map>\n</keymap>' % config.plugins.qer.keyname.value)
			keyfile.close()
		self.mbox = self.session.open(MessageBox, (_("configuration is saved")), MessageBox.TYPE_INFO, timeout=4)
		if self.TrueImage():
			from Components.PluginComponent import plugins
			plugins.reloadPlugins()
#####################################################


def main(session, **kwargs):
	session.open(qer_setup)


##############################################################################
pEmu = QuickEmu()
##############################################################################


def sessionstart(reason, session=None, **kwargs):
	if reason == 0:
		pEmu.gotSession(session)
##############################################################################


def Plugins(**kwargs):
	result = [
		PluginDescriptor(
			where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART],
			fnc=sessionstart
		),
		PluginDescriptor(
			name=_("2boom's QuickEmuRestart"),
			description=_("Restart Softcam with a single button"),
			where=PluginDescriptor.WHERE_PLUGINMENU,
			icon='qer.png',
			fnc=main
		),
	]
	return result
