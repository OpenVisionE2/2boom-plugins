# -*- coding: utf-8 -*-
# 2boom's IPK Tools
# Copyright (c) 2boom 2011-15
# v.2.0-r6
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

from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Screens.Console import Console
from Components.Sources.StaticText import StaticText
from Components.config import config
from Components.ConfigList import ConfigListScreen
from Components.Pixmap import Pixmap
from Components.ActionMap import ActionMap
from Components.Sources.List import List
from Components.Console import Console as iConsole
from Components.Label import Label
from Components.MenuList import MenuList
from Plugins.Plugin import PluginDescriptor
from Components.Language import language
from Tools.LoadPixmap import LoadPixmap
from Tools.Directories import fileExists, pathExists, resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE, SCOPE_LIBDIR
from Components.config import config, getConfigListEntry, ConfigText, ConfigSelection, ConfigSubsection, ConfigYesNo, configfile
from Components.ConfigList import ConfigListScreen
from os import environ
import os
import gettext
import time
import enigma


def status_path():
	status = ''
	if fileExists(resolveFilename(SCOPE_LIBDIR, "opkg/status")):
		status = resolveFilename(SCOPE_LIBDIR, "opkg/status")
	elif fileExists(resolveFilename(SCOPE_LIBDIR, "ipkg/status")):
		status = resolveFilename(SCOPE_LIBDIR, "ipkg/status")
	elif fileExists("/var/lib/opkg/status"):
		status = "/var/lib/opkg/status"
	elif fileExists("/var/opkg/status"):
		status = "/var/opkg/status"
	return status


lang = language.getLanguage()
environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("ipktools", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/ipktools/locale/"))


def _(txt):
	t = gettext.dgettext("ipktools", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t


config.plugins.ipktools = ConfigSubsection()
config.plugins.ipktools.showsetupipk = ConfigYesNo(default=True)
config.plugins.ipktools.filtername = ConfigYesNo(default=False)
config.plugins.ipktools.userdir = ConfigText(default="/", visible_width=70, fixed_size=False)
config.plugins.ipktools.multifilemode = ConfigSelection(default="Multi", choices=[
		("Multi", _("Multi files")),
		("Single", _("Single file")),
])


class IPKTools2(Screen):
	skin = """
	<screen name="IPKTools2" position="center,160" size="750,370" title="2boom's IPK tools">
		<ePixmap position="20,358" zPosition="1" size="170,2" pixmap="~/images/red.png" transparent="1" alphaTest="on" />
		<ePixmap position="190,358" zPosition="1" size="200,2" pixmap="~/images/green.png" transparent="1" alphaTest="on" />
		<widget source="key_red" render="Label" position="20,328" zPosition="2" size="170,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
		<widget source="key_green" render="Label" position="190,328" zPosition="2" size="200,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
		<widget source="menu" render="Listbox" position="15,10" size="710,300">
			<convert type="TemplatedMultiContent">
				{"template": [
					MultiContentEntryText(pos = (120, 2), size = (580, 25), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel
					MultiContentEntryText(pos = (130, 29), size = (580, 18), font=1, flags = RT_HALIGN_LEFT, text = 2), # index 3 is the Description
					MultiContentEntryPixmapAlphaTest(pos = (5, 5), size = (100, 40), png = 3), # index 4 is the pixmap
					],
					"fonts": [gFont("Regular", 23),gFont("Regular", 16)],
					"itemHeight": 50
				}
			</convert>
		</widget>
	</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/ipktools")
		self.setTitle(_("2boom's IPK tools"))
		self.iConsole = iConsole()
		self.indexpos = None
		self["shortcuts"] = ActionMap(["ShortcutActions", "WizardActions"],
		{
			"ok": self.OK,
			"cancel": self.exit,
			"back": self.exit,
			"red": self.exit,
			"green": self.clear,
		})
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Clear /tmp"))
		self.list = []
		self["menu"] = List(self.list)
		self.mList()

	def mList(self):
		self.list = []
		onepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/ipktools/images/tar.png"))
		treepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/ipktools/images/ipk.png"))
		sixpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/ipktools/images/ipk3.png"))
		fivepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/ipktools/images/ipk4.png"))
		self.list.append((_("ipk packets, bh.tgz, tar.gz, nab.tgz installer"), 1, _("install & forced install ipk, bh.tgz, tar.gz, nab.tgz from /tmp"), onepng))
		self.list.append((_("install extensions"), 2, _("install extensions from feed"), sixpng))
		self.list.append((_("download extensions"), 3, _("dowmload extensions from feed"), fivepng))
		self.list.append((_("ipk packets remover"), 4, _("remove & advanced remove ipk packets"), treepng))
		if self.indexpos != None:
			self["menu"].setIndex(self.indexpos)
		self["menu"].setList(self.list)

	def exit(self):
		self.close()

	def clear(self):
		self.iConsole.ePopen("rm /tmp/*.tar.gz /tmp/*.bh.tgz /tmp/*.ipk /tmp/*.nab.tgz", self.info_message)

	def info_message(self, result, retval, extra_args):
		self.mbox = self.session.open(MessageBox, _("Removing files..."), MessageBox.TYPE_INFO, timeout=4)

	def OK(self):
		item = self["menu"].getCurrent()[1]
		self.indexpos = self["menu"].getIndex()
		if item is 1:
			self.session.open(InstallAll4)
		elif item is 2:
			self.session.open(downfeed)
		elif item is 3:
			self.session.open(DownloadFeed)
		elif item is 4:
			self.session.open(RemoveIPK)
###############################################


class downfeed(Screen):
	skin = """
	<screen name="downfeed" position="center,110" size="850,520" title="Insatall extensions from feed">
		<widget source="menu" render="Listbox" position="15,10" size="820,455" scrollbarMode="showOnDemand">
			<convert type="TemplatedMultiContent">
				{"template": [
					MultiContentEntryText(pos = (70, 2), size = (630, 25), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel
					MultiContentEntryText(pos = (80, 29), size = (630, 18), font=1, flags = RT_HALIGN_LEFT, text = 1), # index 3 is the Description
					MultiContentEntryPixmapAlphaTest(pos = (5, 5), size = (50, 40), png = 2), # index 4 is the pixmap
					],
					"fonts": [gFont("Regular", 23),gFont("Regular", 16)],
					"itemHeight": 50
				}
			</convert>
		</widget>
		<ePixmap position="20,512" zPosition="1" size="170,2" pixmap="~/images/red.png" transparent="1" alphaTest="on" />
		<ePixmap position="190,512" zPosition="1" size="170,2" pixmap="~/images/green.png" transparent="1" alphaTest="on" />
		<widget source="key_red" render="Label" position="20,482" zPosition="2" size="170,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
		<widget source="key_green" render="Label" position="190,482" zPosition="2" size="170,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
	</screen>"""

	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/ipktools")
		self.setTitle(_("Insatall extensions from feed"))
		self.session = session
		self.path = status_path()
		self.list = []
		self["menu"] = List(self.list)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"ok": self.setup,
				"green": self.setup,
				"red": self.cancel,
			}, -1)
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText("")
		self.feedlist()

	def feedlist(self):
		self.list = []
		statuspath = ''
		pkg_name = pkg_desc = ' '
		png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/epanel/images/ipkmini.png"))
		list = os.listdir(self.path[:-7])
		if fileExists(self.path + '.backup'):
			list = os.listdir(self.path[:-7] + '/lists')
			statuspath = self.path[:-6] + 'lists/'
		else:
			statuspath = self.path[:-6]
		for file in list:
			if os.path.isfile(statuspath + file):
				if not 'box' in file:
					for line in open(statuspath + file):
						if 'Package:' in line and '-dev' not in line:
							pkg_name = line.split(':')[1]
						elif 'Description:' in line:
							pkg_desc = line.split(':')[1]
							self.list.append((pkg_name, pkg_desc.replace('"', ''), png))
		self.list.sort()
		self["menu"].setList(self.list)
		self["key_green"].setText(_("Install"))

	def cancel(self):
		self.close()

	def setup(self):
		self.session.open(Console, title=_("Insatall extensions from feed"), cmdlist=["opkg install -force-reinstall %s" % self["menu"].getCurrent()[0]], closeOnSuccess=False)
##############################################################################


class DownloadFeed(Screen):
	skin = """
	<screen name="DownloadFeed" position="center,110" size="850,520" title="Download extensions from feed">
		<widget source="menu" render="Listbox" position="15,10" size="820,455" scrollbarMode="showOnDemand">
			<convert type="TemplatedMultiContent">
				{"template": [
					MultiContentEntryText(pos = (70, 2), size = (630, 25), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel
					MultiContentEntryText(pos = (80, 29), size = (630, 18), font=1, flags = RT_HALIGN_LEFT, text = 1), # index 3 is the Description
					MultiContentEntryPixmapAlphaTest(pos = (5, 5), size = (50, 40), png = 2), # index 4 is the pixmap
					],
					"fonts": [gFont("Regular", 23),gFont("Regular", 16)],
					"itemHeight": 50
				}
			</convert>
		</widget>
		<ePixmap name="red" position="20,512" zPosition="1" size="170,2" pixmap="~/images/red.png" transparent="1" alphaTest="on" />
		<ePixmap name="green" position="190,512" zPosition="1" size="220,2" pixmap="~/images/green.png" transparent="1" alphaTest="on" />
		<ePixmap name="yellow" position="410,512" zPosition="1" size="220,2" pixmap="~/images/yellow.png" transparent="1" alphaTest="on" />
		<widget name="key_red" position="20,482" zPosition="2" size="170,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
		<widget name="key_green" position="190,482" zPosition="2" size="220,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
		<widget name="key_yellow" position="410,482" zPosition="2" size="220,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Download extensions from feed"))
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/ipktools")
		self.session = session
		self.path = status_path()
		self.iConsole = iConsole()
		if fileExists(self.path[:-6] + 'status'):
			self.iConsole.ePopen("mv %s %s.tmp" % (self.path[:-6] + 'status', self.path[:-6] + 'status'))
		self.list = []
		self["menu"] = List(self.list)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"ok": self.download,
				"green": self.download,
				"yellow": self.download_wdeps,
				"red": self.cancel,
			}, -1)
		self["key_red"] = Label(_("Close"))
		self["key_green"] = Label("")
		self["key_yellow"] = Label("")
		self.feedlist()

	def feedlist(self):
		self.list = []
		pkg_name = pkg_desc = ' '
		statuspath = ''
		png = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/epanel/images/ipkmini.png"))
		list = os.listdir(self.path[:-7])
		if fileExists(self.path + '.backup'):
			list = os.listdir(self.path[:-7] + '/lists')
			statuspath = self.path[:-6] + 'lists/'
		else:
			statuspath = self.path[:-6]
		for file in list:
			if os.path.isfile(statuspath + file):
				if not 'box' in file:
					for line in open(statuspath + file):
						if 'Package:' in line and '-dev' not in line:
							pkg_name = line.split(':')[1]
						elif 'Description:' in line:
							pkg_desc = line.split(':')[1]
							self.list.append((pkg_name, pkg_desc.replace('"', ''), png))
		self.list.sort()
		self["menu"].setList(self.list)
		self["key_green"].setText(_("Download -nodeps"))
		self["key_yellow"].setText(_("Download -deps"))

	def download(self):
		self.session.open(Console, title=_("Download extensions from feed"), cmdlist=["cd /tmp && opkg download %s" % self["menu"].getCurrent()[0]], closeOnSuccess=False)

	def download_wdeps(self):
		self.session.open(Console, title=_("Download extensions from feed"), cmdlist=["cd /tmp && opkg install -download-only %s" % self["menu"].getCurrent()[0]], closeOnSuccess=False)

	def cancel(self):
		if fileExists(self.path[:-6] + 'status.tmp'):
			self.iConsole.ePopen("mv %s.tmp %s" % (self.path[:-6] + 'status', self.path[:-6] + 'status'))
		self.close()
####################################################################


class InstallAll4(Screen):
	skin = """
	<screen name="InstallAll4" position="center,160" size="750,405" title="Press -Info- to update plugin list">
  		<widget source="menu" render="Listbox" position="15,10" size="720,300" scrollbarMode="showOnDemand">
   			 <convert type="TemplatedMultiContent">
       				{"template": [
         				MultiContentEntryText(pos = (70, 2), size = (650, 25), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel
          				MultiContentEntryText(pos = (80, 29), size = (630, 18), font=1, flags = RT_HALIGN_LEFT, text = 1), # index 3 is the Description
          				MultiContentEntryPixmapAlphaTest(pos = (5, 5), size = (50, 40), png = 2), # index 4 is the pixmap
          				],
      					"fonts": [gFont("Regular", 23),gFont("Regular", 16)],
       					"itemHeight": 50
      				}
    			</convert>
  		</widget>
  		<ePixmap position="20,393" zPosition="1" size="165,2" pixmap="~/images/red.png" transparent="1" alphaTest="on" />
  		<ePixmap position="185,393" zPosition="1" size="165,2" pixmap="~/images/green.png" transparent="1" alphaTest="on" />
  		<ePixmap position="350,393" zPosition="1" size="200,2" pixmap="~/images/yellow.png" transparent="1" alphaTest="on" />
  		<ePixmap position="550,393" zPosition="1" size="190,2" pixmap="~/images/blue.png" transparent="1" alphaTest="on" />
  		<widget source="key_red" render="Label" position="20,363" zPosition="2" size="165,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
  		<widget source="key_green" render="Label" position="185,363" zPosition="2" size="165,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
 	 	<widget source="key_yellow" render="Label" position="350,363" zPosition="2" size="200,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
  		<widget source="key_blue" render="Label" position="550,363" zPosition="2" size="190,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
	</screen>"""

	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/ipktools")
		if config.plugins.ipktools.multifilemode.value is 'Multi':
			self.setTitle(_('MultiSelect Mode'))
		else:
			self.setTitle(_('SingleSelect Mode'))

		self.session = session
		self.workdir = []
		self.list = []
		self.commamd_line_ipk = []
		self.commamd_line_tar = []
		self.force_install = False
		self.status = False
		self.ipkminipng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/ipktools/images/ipkmini.png"))
		self.tarminipng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/ipktools/images/tarmini.png"))
		self["menu"] = List(self.list)
		self.nList()
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"ok": self.press_ok,
				"green": self.all_install,
				"red": self.cancel,
				"yellow": self.install_force,
				"blue": self.restart_enigma,
			}, -1)
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Install"))
		self["key_yellow"] = StaticText(_("Forced Install"))
		self["key_blue"] = StaticText(_("Restart"))

	def mount_point(self):
		searchPaths = []
		if fileExists("/proc/mounts"):
			for line in open("/proc/mounts"):
				if "/dev/sd" in line:
					#searchPaths.append(line.split()[1].replace('\\040', ' ') + "/")
					searchPaths.append(line.split()[1].replace('\\040', ' ') + config.plugins.ipktools.userdir.value)
		searchPaths.append('/tmp/')
		return searchPaths

	def press_ok(self):
		if config.plugins.ipktools.multifilemode.value is 'Multi':
			self.mark_list()
		else:
			self.all_install()

	def install_force(self):
		self.force_install = True
		self.all_install()

	def mark_list(self):
		line_old = self["menu"].getCurrent()
		if line_old != None:
			if not line_old[-2]:
				if ".ipk" in line_old[0]:
					pngfile = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/ipktools/images/ipkact.png"))
					self.commamd_line_ipk.append(line_old[-1])
				else:
					pngfile = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/ipktools/images/taract.png"))
					self.commamd_line_tar.append('tar -C/ -xzpvf %s' % line_old[-1])
				self.status = True
			else:
				if ".ipk" in line_old[0]:
					pngfile = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/ipktools/images/ipkmini.png"))
					self.commamd_line_ipk.remove(line_old[-1])
				else:
					pngfile = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/ipktools/images/tarmini.png"))
					self.commamd_line_tar.remove('tar -C/ -xzpvf %s' % line_old[-1])
				self.status = False
			line_new = (line_old[0], line_old[1], pngfile, self.status, line_old[-1])
			self["menu"].modifyEntry(self["menu"].getIndex(), line_new)
			if self["menu"].getIndex() + 1 >= self["menu"].count():
				self["menu"].setIndex(0)
			else:
				self["menu"].selectNext()

	def all_install(self):
		line_old = self["menu"].getCurrent()
		if line_old != None:
			if config.plugins.ipktools.multifilemode.value is not 'Multi':
				self.commamd_line_tar = []
				self.commamd_line_ipk = []
				if '.ipk' in self["menu"].getCurrent()[-1]:
					self.commamd_line_ipk.append(self["menu"].getCurrent()[-1])
				else:
					self.commamd_line_tar.append('tar -C/ -xzpvf %s' % self["menu"].getCurrent()[-1])
			force_string = ''
			if self.force_install:
				force_string = "-force-overwrite -force-downgrade"
			if len(self.commamd_line_ipk) >= 1 and len(self.commamd_line_tar) >= 1:
				self.session.open(Console, title=_("Install packets"), cmdlist=["opkg install %s %s && %s" % (force_string, ' '.join(self.commamd_line_ipk), ' && '.join(self.commamd_line_tar))])
			elif len(self.commamd_line_ipk) >= 1:
				self.session.open(Console, title=_("Install packets"), cmdlist=["opkg install %s %s" % (force_string, ' '.join(self.commamd_line_ipk))])
			elif len(self.commamd_line_tar) >= 1:
				self.session.open(Console, title=_("Install tar.gz, bh.tgz, nab.tgz"), cmdlist=["%s" % ' && '.join(self.commamd_line_tar)])
			self.force_install = False

	def nList(self):
		self.workdir = self.mount_point()
		for i in range(len(self.workdir)):
			if pathExists(self.workdir[i]):
				ipklist = os.listdir(self.workdir[i])
				for line in ipklist:
					if line.endswith('tar.gz') or line.endswith('bh.tgz') or line.endswith('nab.tgz'):
						try:
							self.list.append((line.strip("\n"), "%s, %s Kb,  %s" % (self.workdir[i], (os.path.getsize(self.workdir[i] + line.strip("\n")) / 1024), time.ctime(os.path.getctime(self.workdir[i] + line.strip("\n")))), self.tarminipng, self.status, self.workdir[i] + line.strip("\n")))
						except:
							pass
					elif line.endswith('.ipk'):
						try:
							self.list.append((line.strip("\n"), "%s, %s Kb,  %s" % (self.workdir[i], (os.path.getsize(self.workdir[i] + line.strip("\n")) / 1024), time.ctime(os.path.getctime(self.workdir[i] + line.strip("\n")))), self.ipkminipng, self.status, self.workdir[i] + line.strip("\n")))
						except:
							pass
		self.list.sort()
		self["menu"].setList(self.list)

	def restart_enigma(self):
		self.session.open(TryQuitMainloop, 3)

	def cancel(self):
		self.close()
########################################################################################################


class RemoveIPK(Screen):
	skin = """
	<screen name="RemoveIPK" position="center,100" size="750,570" title="Ipk remove">
		<widget source="menu" position="15,10" render="Listbox" size="720,500">
			<convert type="TemplatedMultiContent">
				{"template": [
					MultiContentEntryText(pos = (70, 2), size = (630, 25), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel
					MultiContentEntryText(pos = (80, 29), size = (630, 18), font=1, flags = RT_HALIGN_LEFT, text = 1), # index 3 is the Description
					MultiContentEntryPixmapAlphaTest(pos = (5, 5), size = (50, 40), png = 2), # index 4 is the pixmap
					],
					"fonts": [gFont("Regular", 23),gFont("Regular", 16)],
					"itemHeight": 50
				}
			</convert>
		</widget>
		<ePixmap position="20,558" zPosition="1" size="170,2" pixmap="~/images/red.png" transparent="1" alphaTest="on" />
		<ePixmap position="190,558" zPosition="1" size="170,2" pixmap="~/images/green.png" transparent="1" alphaTest="on" />
		<ePixmap position="360,558" zPosition="1" size="200,2" pixmap="~/images/yellow.png" transparent="1" alphaTest="on" />
		<widget source="key_red" render="Label" position="20,528" zPosition="2" size="170,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
		<widget source="key_green" render="Label" position="190,528" zPosition="2" size="170,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
		<widget source="key_yellow" render="Label" position="360,528" zPosition="2" size="200,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
	</screen>"""

	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/ipktools")
		self.setTitle(_("Ipk remove"))
		self.session = session
		self.path = status_path()
		self.iConsole = iConsole()
		self.status = False
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("UnInstall"))
		self["key_yellow"] = StaticText(_("Adv. UnInstall"))
		self.list = []
		self["menu"] = List(self.list)
		self.nList()
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"ok": self.remove_ipk,
				"green": self.remove_ipk,
				"red": self.cancel,
				"yellow": self.adv_remove,
			}, -1)

	def nList(self):
		self.list = []
		ipkminipng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/ipktools/images/ipkmini.png"))
		for line in open(status_path()):
			if "Package:" in line:
				name1 = line.replace("\n", "").split()[-1]
			elif "Version:" in line:
				name2 = line.split()[-1] + "\n"
			elif "Status:" in line and not "not-installed" in line:
				self.list.append((name1, name2, ipkminipng))
		self.list.sort()
		self["menu"].setList(self.list)

	def cancel(self):
		self.close()

	def remove_ipk(self):
		local_status = ipk_dir = ''
		pkg_name = self["menu"].getCurrent()[0]
		if self.status:
			local_status = '-force-remove'
			self.staus = False
		if 'plugin' in pkg_name or 'skin' in pkg_name:
			if fileExists('%s%s.list' % (self.path[:-6] + 'info/', pkg_name)):
				for line in open('%s%s.list' % (self.path[:-6] + 'info/', pkg_name)):
					if 'plugin.py' in line or 'plugin.pyo' in line:
						ipk_dir = line[:-11]
					elif 'skin.xml' in line:
						ipk_dir = line[:-10]
		self.session.open(Console, title=_("%s" % ipk_dir), cmdlist=["opkg remove %s %s" % (local_status, pkg_name)], closeOnSuccess=False)
		if pathExists(ipk_dir):
			self.iConsole.ePopen("rm -rf %s" % ipk_dir, self.finish)
		else:
			self.nList()

	def finish(self, result, retval, extra_args):
		self.nList()

	def adv_remove(self):
		self.staus = True
		self.remove_ipk()


class opkgUpdate():
	def __init__(self):
		self.dialog = None

	def gotSession(self, session):
		self.session = session
		self.iConsole = iConsole()
		self.timer = enigma.eTimer()
		self.timer.callback.append(self.update)
		self.timer.start(60000, True)

	def update(self):
		self.timer.stop()
		now = time.localtime(time.time())
		if (now.tm_hour == 1 or now.tm_hour == 5 or now.tm_hour == 9 or now.tm_hour == 13 or now.tm_hour == 17 or now.tm_hour == 21) and now.tm_min == 1:
			self.iConsole.ePopen("opkg update")

		self.timer.start(60000, True)


def setupipk(session, **kwargs):
	session.open(InstallAll4)


def main(session, **kwargs):
	session.open(IPKTools2)


######################################################################################
pTools = opkgUpdate()
######################################################################################


def sessionstart(reason, session=None, **kwargs):
	if reason == 0:
		pTools.gotSession(session)
######################################################################################


def Plugins(**kwargs):
	list = [PluginDescriptor(name=_("2boom's IPK tools"), description=_("install & forced install ipk, bh.tgz, tar.gz, nab.tgz from /tmp"), where=[PluginDescriptor.WHERE_PLUGINMENU], icon="ipktools.png", fnc=main)]
	if config.plugins.ipktools.showsetupipk.value:
		list.append(PluginDescriptor(name=_("IPK Tools Installer"), description=_("install & forced install ipk, bh.tgz, tar.gz, nab.tgz from /tmp"), where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=setupipk))
	list.append(PluginDescriptor(name=_("2boom's IPK tools"), description=_("install & forced install ipk, bh.tgz, tar.gz, nab.tgz from /tmp"), where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=sessionstart))
	return list
