#!/usr/bin/python
# -*- coding: utf-8 -*-
# ReMountNetShare plugin
# Copyright (c) 2boom 2013-14
# v.0.6-r2
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
from Tools.Directories import fileExists, pathExists, resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from Tools import Notifications
from Components.Console import Console
from Components.ActionMap import ActionMap
from Components.config import getConfigListEntry, ConfigBoolean, ConfigSubsection, ConfigYesNo, config, configfile
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.ScrollLabel import ScrollLabel
from Components.Language import language
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
import os
import enigma
import gettext

config.plugins.remount = ConfigSubsection()
config.plugins.remount.status = ConfigBoolean(default=True)
config.plugins.remount.menuext = ConfigYesNo(default=False)
config.plugins.remount.menuextum = ConfigYesNo(default=False)
config.plugins.remount.inwakeup = ConfigYesNo(default=False)
config.plugins.remount.inrestartui = ConfigYesNo(default=False)
config.plugins.remount.indeepstanby = ConfigYesNo(default=False)

lang = language.getLanguage()
os.environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("RemountNetshare", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/ReMountNetShare/locale"))
def _(txt):
	t = gettext.dgettext("RemountNetshare", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

def main_func():
	mount_type = mount_status = mount_ip = mount_sharename = mount_sharedir = mount_user = mount_password = mount_options = all_options = ""
	command_remount = "umount -a -f -t nfs,cifs"
	command_mount = []
	if fileExists("/etc/enigma2/automounts.xml"):
		for line in open("/etc/enigma2/automounts.xml"):
			if "cifs" in line:
				mount_type = "cifs"
			elif "nfs" in line:
				mount_type = "nfs"
			elif "/active" in line:
				mount_status = get_xml_data(line)
			elif "/ip" in line:
				mount_ip = get_xml_data(line)
			elif "/sharename" in line:
				mount_sharename = get_xml_data(line)
			elif "/options" in line:
				mount_options = get_xml_data(line)
			elif "/sharedir" in line:
				mount_sharedir =  get_xml_data(line)
			elif "</username" in line:
				if "<username></username>" not in line:
					mount_user = "%s" % get_xml_data(line)
				else:
					mount_user = ""
			elif "</password" in line:
				if "<password></password>" not in line:
					mount_password = "%s" % get_xml_data(line)
				else:
					mount_password = ""
			elif "</mount>" in line:
				if mount_status == "True":
					if mount_type == "cifs":
						all_options = mount_options + ',noatime,noserverino,iocharset=utf8,username='+ mount_user + ',password='+ mount_password
						command_mount.append("mount -t cifs -o %s '//%s/%s' '/media/net/%s'" % (all_options, mount_ip, mount_sharedir, mount_sharename))
					elif mount_type == "nfs":
						command_mount.append("mount -t nfs -o %s '%s' '/media/net/%s'" % (mount_options, mount_ip + ':/' + mount_sharedir, mount_sharename))
	for count_mounts in command_mount:
		command_remount += " && %s" % count_mounts
	return command_remount
	


def get_xml_data(what):
	return what.split("<")[1].split(">")[1]

def IsImageName():
	if fileExists("/etc/issue"):
		for line in open("/etc/issue"):
			if "BlackHole" in line or "vuplus" in line:
				return True
	return False
	
def IsImageATV():
	if fileExists("/etc/issue"):
		for line in open("/etc/issue"):
			if "openATV" in line:
				return True
	return False

class ReMountNetShare():
	def __init__(self):
		self.dialog = None
		self.Console = Console()

	def gotSession(self, session):
		self.session = session
		config.misc.standbyCounter.addNotifier(self.onEnterStandby, initial_call=False)
		if IsImageName():
			config.misc.DeepStandbyOn.addNotifier(self.onEnterDeepStandby, initial_call=False)
			
			#config.misc.DeepStandby.addNotifier(self.onEnterDeepStandby, initial_call = False)
		else:
			config.misc.DeepStandby.addNotifier(self.onEnterDeepStandby, initial_call=False)
			if not IsImageATV():
				if config.plugins.remount.inrestartui.value:
					if not config.misc.RestartUI.value:
						config.misc.RestartUI.addNotifier(self.onRestartUI, initial_call=False)

	def onRestartUI(self, configElement):
		if config.misc.RestartUI.value:
			self.Console.ePopen(main_func())

	def onEnterDeepStandby(self, configElement):
		command_unmount = "umount -a -f -t nfs,cifs"
		if config.plugins.remount.indeepstanby:
			self.Console.ePopen(command_unmount)

	def onEnterStandby(self, configElement):
		from Screens.Standby import inStandby
		inStandby.onClose.append(self.StandbyEnd)
		if config.plugins.remount.status.value:
			config.plugins.remount.status.value = False

	def StandbyEnd(self):
		if not config.plugins.remount.status.value:
			config.plugins.remount.status.value = True
			if config.plugins.remount.inwakeup:
				self.Console.ePopen(main_func())

class remount_setup(ConfigListScreen, Screen):
	skin = """
	<screen name="remount_setup" position="center,160" size="750,370" title="2boom's RemountNetShare">
  	<eLabel position="30,145" size="690,2" backgroundColor="#00aaaaaa" zPosition="5" />
  	<widget position="15,10" size="720,125" name="config" scrollbarMode="showOnDemand" />
  	<ePixmap position="10,358" zPosition="1" size="165,2" pixmap="~/images/red.png" alphatest="blend" />
  	<widget source="key_red" render="Label" position="10,328" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" transparent="1" />
  	<ePixmap position="175,358" zPosition="1" size="165,2" pixmap="~/images/green.png" alphatest="blend" />
  	<widget source="key_green" render="Label" position="175,328" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" transparent="1" />
  	<ePixmap position="340,358" zPosition="1" size="195,2" pixmap="~/images/yellow.png" alphatest="blend" />
  	<widget source="key_yellow" render="Label" position="340,328" zPosition="2" size="195,30" font="Regular;20" halign="center" valign="center" transparent="1" />
  	<widget name="text" position="20,160" size="710,160" font="Regular; 20" halign="left" noWrap="1" />
	</screen>"""
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/ReMountNetShare")
		self.Console = Console()
		self.setTitle(_("2boom's RemountNetShare"))
		self.list = []
		self.list.append(getConfigListEntry(_("UnMount in deepstandby"), config.plugins.remount.indeepstanby))
		self.list.append(getConfigListEntry(_("ReMount on wakeup"), config.plugins.remount.inwakeup))
		if not IsImageATV():
			self.list.append(getConfigListEntry(_("ReMount on restart enigma2"), config.plugins.remount.inrestartui))
		self.list.append(getConfigListEntry(_("Show Remount NetShare in ExtensionMenu"), config.plugins.remount.menuext))
		self.list.append(getConfigListEntry(_("Show Unmount NetShare in ExtensionMenu"), config.plugins.remount.menuextum))
		ConfigListScreen.__init__(self, self.list)
		self["text"] = ScrollLabel("")
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Remount now"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.cancel,
			"cancel": self.cancel,
			"green": self.save,
			"yellow": self.remount,
			"ok": self.save
		}, -2)
		self.onShow.append(self.list_mount_point)

	def list_mount_point(self):
		mount_list = ""
		line = main_func()[28:].replace("'", '').split('&&')
		if fileExists("/etc/enigma2/automounts.xml"):
			for i in range(len(line)):
				if  '/media/net/' in line[i]:
					mount_list += _('active: %s %s %s\n') % (line[i].split()[2], line[i].split()[-2], line[i].split()[-1])
			self["text"].setText(mount_list)
		else:
			self["text"].setText('')

	def cancel(self):
		for i in self["config"].list:
			i[1].cancel()
		self.close(False)

	def remount(self):
		self.Console.ePopen(main_func())
		self.mbox = self.session.open(MessageBox, (_("remounting ...")), MessageBox.TYPE_INFO, timeout=4)

	def save(self):
		for i in self["config"].list:
			i[1].save()
		configfile.save()
		self.mbox = self.session.open(MessageBox, (_("configuration is saved")), MessageBox.TYPE_INFO, timeout=4)
		if not IsImageName():
			from Components.PluginComponent import plugins
			plugins.reloadPlugins()

def main(session, **kwargs):
	session.open(remount_setup)

def func(session, **kwargs):
	Console().ePopen(main_func())
	session.open(MessageBox, (_("remounting ...")), MessageBox.TYPE_INFO, timeout=4)
	
def func2(session, **kwargs):
	Console().ePopen("umount -a -f -t nfs,cifs")
	session.open(MessageBox, (_("unmounting ...")), MessageBox.TYPE_INFO, timeout=4)

pRemount = ReMountNetShare()

def sessionstart(reason,session=None, **kwargs):
	if reason == 0:
		pRemount.gotSession(session)

def Plugins(**kwargs):
	list = [PluginDescriptor(name=_("2boom's RemountNetShare"), description=_("manual or auto remount network share"), where=[PluginDescriptor.WHERE_PLUGINMENU], icon="remnet.png", fnc=main)]
	if config.plugins.remount.menuext.value:
		list.append(PluginDescriptor(name=_("Remount NetShare"), description=_("manual or auto remount network share"), where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=func))
	if config.plugins.remount.menuextum.value:
		list.append(PluginDescriptor(name=_("Unmount NetShare"), description=_("manual or auto remount network share"), where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=func2))
	list.append(PluginDescriptor(where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart))
	return list

     
