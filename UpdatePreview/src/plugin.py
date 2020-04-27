# -*- coding: utf-8 -*-
# UpdatePreview plugin
# Copyright (c) 2boom 2013-15
# v.0.7-r0
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
from Components.MenuList import MenuList
from Components.Sources.StaticText import StaticText
from Components.ScrollLabel import ScrollLabel
from Components.Sources.List import List
from Components.Language import language
from Components.Console import Console as iConsole
from Components.config import ConfigLocations, ConfigSubsection, config, configfile
from Components.FileList import MultiFileSelectList
from Plugins.Plugin import PluginDescriptor
from Screens.Console2 import Console2
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from enigma import eTimer
from urllib2 import urlopen
import os
import gettext

lang = language.getLanguage()
os.environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("UpdatePreview", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/UpdatePreview/locale"))
def _(txt):
	t = gettext.dgettext("UpdatePreview", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t
	
config.plugins.upw = ConfigSubsection()
config.plugins.upw.userfiles = ConfigLocations(default=[])

SKIN_INFO = """
<screen name="get_opkg_data" position="center,140" size="625,35" title="Please wait">
  <widget source="status" render="Label" position="10,5" size="605,22" zPosition="2" font="Regular; 20" halign="center" transparent="2" />
</screen>"""
class get_opkg_data(Screen):
	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self.session = session
		self.skin = SKIN_INFO
		self.setTitle(_("Please wait"))
		self["status"] = StaticText()
		self.iConsole = iConsole()
		self["status"].text = _("Updating list of available packages")
		self.iConsole.ePopen("opkg update", self.preview_list)
		
	def preview_list(self, result, retval, extra_args):
		if retval is 0:
			self["status"].text = _("Updating list installed and upgradable packages")
			self.iConsole.ePopen("opkg list-upgradable", self.preview)
		else:
			self["status"].text = _("Error receive list-upgradable, try later")
			self.iConsole.ePopen("sleep 5", self.cancel2)
			
	def cancel2(self, result, retval, extra_args):
		self.close()

	def cancel(self):
		self.close()
		
	def preview(self, result, retval, extra_args):
		if retval is 0:
			self.session.openWithCallback(self.cancel, updateprv2, result)
		else:
			self["status"].text = _("Error receive list-upgradable, try later")
			self.iConsole.ePopen("sleep 5", self.cancel)

SKIN_VIEW = """
<screen name="updateprv2" position="center,140" size="1100,520" title="Update Preview">
  	<widget name="text" position="10,10" size="1080,470" font="Console;22" noWrap="1" />
  	<ePixmap position="10,518" zPosition="1" size="165,2" pixmap="~/images/red.png" alphatest="blend" />
  	<widget source="red_key" render="Label" position="10,488" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
  	<ePixmap position="175,518" zPosition="1" size="165,2" pixmap="~/images/green.png" alphatest="blend" />
  	<widget source="green_key" render="Label" position="176,488" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
  	<ePixmap position="340,518" zPosition="1" size="165,2" pixmap="~/images/yellow.png" alphatest="blend" />
  	<widget source="yellow_key" render="Label" position="340,488" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
  	<ePixmap position="508,518" zPosition="1" size="165,2" pixmap="~/images/blue.png" alphatest="blend" />
  	<widget source="blue_key" render="Label" position="508,488" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
	<ePixmap pixmap="~/images/menu.png" position="1020,488" size="70,30" alphatest="blend" zPosition="3" />
</screen>"""
class updateprv2(Screen):
	def __init__(self, session, result):
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/UpdatePreview")
		self.session = session
		self.skin = SKIN_VIEW
		self.result = result
		self.iConsole = iConsole()
		self.setTitle(_("Please wait"))
		self.count = 0
		self["red_key"] = StaticText(_("Close"))
		self["green_key"] = StaticText(_("Update"))
		self["yellow_key"] = StaticText(_("Restart"))
		self["blue_key"] = StaticText(_("Latest Commits"))
		self["text"] = ScrollLabel("")
		self["actions"] = ActionMap(["OkCancelActions", "DirectionActions", "ColorActions", "MenuActions"],
		{ 
		"cancel": self.close,
		"red": self.close,
		"green": self.update,
		"yellow": self.sysreboot,
		"blue": self.showCommits,
		"menu": self.selectfiles,
		"up": self["text"].pageUp,
		"left": self["text"].pageUp,
		"down": self["text"].pageDown,
		"right": self["text"].pageDown,
		},
		-1)
		self.onShow.append(self.preview)

	def preview(self):
		list = ""
		title_msg = _("No updates available")
		self.count = 0
		if len(self.result) > 0:
			for line in self.result.splitlines(True):
				if not line.startswith('Not '):
					list += line
					self.count += 1
			if not self.count is 0:
				title_msg = _("Update preview: %s aviable") % self.count
				try:
					status = urlopen("http://openpli.org/status").read().split('!', 1)
					title_msg += _(". Image is stable.")
				except:
					pass
		self.setTitle(title_msg)
		self["text"].setText(list)

	def cancel(self):
		self.close()
	
	def sysreboot(self):
		self.session.open(TryQuitMainloop, 2)
	
	def selectfiles(self):
		self.session.open(FilesSelection)
		
	def showCommits(self):
		self.session.open(commitinfo)
		
	def update(self):
		if self.count is not 0:
			if len(config.plugins.upw.userfiles.value) is 0:
				self.session.open(Console2,title = _("Updating..."), cmdlist = ["opkg upgrade"])
			else:
				for i in range(len(config.plugins.upw.userfiles.value)):
					config.plugins.upw.userfiles.value[i] = config.plugins.upw.userfiles.value[i].lstrip('/')
				self.session.open(Console2,title = _("Updating..."), cmdlist = ["tar czvf /tmp/noupdate.tar.gz %s && opkg upgrade ; tar -C/ -xzpvf /tmp/noupdate.tar.gz" % ' '.join(config.plugins.upw.userfiles.value)])

class commitinfo(Screen):
	skin = """
  <screen name="commitinfo" position="center,140" size="1100,520" title="Latest Commits">
    <widget name="AboutLatestCommits" position="10,10" size="1080,470" font="Console;22" noWrap="1"/>
  </screen>"""
	def __init__(self, session):
		Screen.__init__(self, session)
		self.setTitle(_("Please wait"))
		self["AboutLatestCommits"] = ScrollLabel("")
		self["actions"] = ActionMap(["SetupActions", "DirectionActions"],
			{
				"cancel": self.close,
				"ok": self.close,
				"up": self["AboutLatestCommits"].pageUp,
				"down": self["AboutLatestCommits"].pageDown
			})

		self.Timer = eTimer()
		self.Timer.callback.append(self.readCommitLogs)
		self.Timer.start(50, True)
	
	def readCommitLogs(self):
		url = 'https://api.github.com/repos/openpli/enigma2/commits'
		commitlog = ""
		from datetime import datetime
		from json import loads
		from urllib2 import urlopen
		try:
			commitlog += 80 * '-' + '\n'
			commitlog += url.split('/')[-2] + '\n'
			commitlog += 80 * '-' + '\n'
			for c in loads(urlopen(url, timeout=5).read()):
				creator = c['commit']['author']['name']
				title = c['commit']['message']
				date = datetime.strptime(c['commit']['committer']['date'], '%Y-%m-%dT%H:%M:%SZ').strftime('%x %X')
				commitlog += date + ' ' + creator + '\n' + title + 2 * '\n'
			commitlog = commitlog.encode('utf-8')
			self.cachedProjects[self.projects[self.project][1]] = commitlog
		except:
			commitlog += _("Currently the commit log cannot be retrieved - please try later again")
		self.setTitle(_("Latest Commits"))
		self["AboutLatestCommits"].setText(commitlog)
		
class FilesSelection(Screen):
	skin = """
	<screen name="FilesSelection" position="265,160" size="750,360" title="Select files">
    		<widget name="checkList" position="15,10" size="720,300" transparent="1" scrollbarMode="showOnDemand" />
    		<ePixmap position="10,355" zPosition="1" size="165,2" pixmap="~/images/red.png" alphatest="blend" />
    		<widget source="key_red" render="Label" position="10,325" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" transparent="1" />
    		<ePixmap position="175,355" zPosition="1" size="180,2" pixmap="~/images/green.png" alphatest="blend" />
    		<widget source="key_green" render="Label" position="175,325" zPosition="2" size="180,30" font="Regular;20" halign="center" valign="center" transparent="1" />
    		<ePixmap position="355,355" zPosition="1" size="180,2" pixmap="~/images/yellow.png" alphatest="blend" />
    		<widget source="key_yellow" render="Label" position="355,325" zPosition="2" size="180,30" font="Regular;20" halign="center" valign="center" transparent="1" />
 	 </screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/UpdatePreview")
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText()
		self.selectedFiles = config.plugins.upw.userfiles.value
		defaultDir = '/'
		self.filelist = MultiFileSelectList(self.selectedFiles, defaultDir, showDirectories = True, matchingPattern = "^.*" )
		self["checkList"] = self.filelist
		self["actions"] = ActionMap(["DirectionActions", "OkCancelActions", "ShortcutActions"],
		{
			"cancel": self.exit,
			"red": self.exit,
			"yellow": self.changeSelectionState,
			"green": self.saveSelection,
			"ok": self.okClicked,
			"left": self.left,
			"right": self.right,
			"down": self.down,
			"up": self.up
		}, -1)
		if not self.selectionChanged in self["checkList"].onSelectionChanged:
			self["checkList"].onSelectionChanged.append(self.selectionChanged)
		self.onLayoutFinish.append(self.layoutFinished)

	def layoutFinished(self):
		idx = 0
		self["checkList"].moveToIndex(idx)
		self.setWindowTitle()
		self.selectionChanged()

	def setWindowTitle(self):
		self.setTitle(_("Select files"))

	def selectionChanged(self):
		current = self["checkList"].getCurrent()[0]
		if len(current) > 2:
			if current[2] is True:
				self["key_yellow"].setText(_("Deselect"))
			else:
				self["key_yellow"].setText(_("Select"))
		
	def up(self):
		self["checkList"].up()

	def down(self):
		self["checkList"].down()

	def left(self):
		self["checkList"].pageUp()

	def right(self):
		self["checkList"].pageDown()

	def changeSelectionState(self):
		self["checkList"].changeSelectionState()
		self.selectedFiles = self["checkList"].getSelectedList()

	def saveSelection(self):
		self.selectedFiles = self["checkList"].getSelectedList()
		config.plugins.upw.userfiles.value = self.selectedFiles
		config.plugins.upw.userfiles.save()
		config.plugins.upw.save()
		config.save()
		self.close(None)

	def exit(self):
		self.close(None)

	def okClicked(self):
		if self.filelist.canDescent():
			self.filelist.descent()


def main(session, **kwargs):
	session.open(get_opkg_data)
	
def menu(menuid, **kwargs):
	if menuid == "setup":
		return [(_("Software update preview"), main, _("update preview from feed"), None)]
	return []

def Plugins(**kwargs):
	list = [PluginDescriptor(name=_("Software update preview"), description=_("update preview from feed"), where = [PluginDescriptor.WHERE_MENU], fnc=menu)]
	return list
