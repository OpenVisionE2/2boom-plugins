# Easy Cccam config plugin
# Copyright (c) 2boom 2015
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
from keymapparser import readKeymap, removeKeymap
from os import environ
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Components.Console import Console
from Components.Language import language
from Components.config import config, getConfigListEntry, ConfigText, ConfigInteger, ConfigSubsection, configfile, NoSave
from Components.ConfigList import ConfigListScreen
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from Components.Sources.StaticText import StaticText
import os
import gettext
from os import environ

lang = language.getLanguage()
environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("ecccam", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/ECCcam/locale/"))

def _(txt):
	t = gettext.dgettext("ecccam", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t
	
config.plugins.ecccam = ConfigSubsection()
config.plugins.ecccam.server = ConfigText(default="server.name.com", visible_width = 70, fixed_size = False)
config.plugins.ecccam.name = ConfigText(default="username", visible_width = 70, fixed_size = False)
config.plugins.ecccam.passw = ConfigText(default="userpassword", visible_width = 70, fixed_size = False)
config.plugins.ecccam.port = ConfigInteger(default = 0, limits = (1, 99999))
##############################################################################
class ecccam_setup(ConfigListScreen, Screen):
	skin = """
	<screen name="ecccam_setup" position="center,160" size="750,147" title="2boom's Easy CCcam">
  		<widget position="15,5" size="720,100" name="config" scrollbarMode="showOnDemand" />
   		<ePixmap position="10,140" zPosition="1" size="165,2" pixmap="~/images/red.png" alphatest="blend" />
  		<widget source="key_red" render="Label" position="10,110" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
  		<ePixmap position="175,140" zPosition="1" size="165,2" pixmap="~/images/green.png" alphatest="blend" />
  		<widget source="key_green" render="Label" position="175,110" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
	</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/ECCcam")
		self.setTitle(_("2boom's Easy CCcam"))
		self.config_path = self.get_config_path()
		if os.path.isfile('%sCCcam.cfg' % self.config_path):
			for line in open('%sCCcam.cfg' % self.config_path):
				if line.startswith("C:"):
					if len(line.split()) >= 5:
						config.plugins.ecccam.server.value = line.split()[1]
						config.plugins.ecccam.port.value = int(line.split()[2])
						config.plugins.ecccam.name.value = line.split()[3]
						config.plugins.ecccam.passw.value = line.split()[4].strip('\r').strip('\n')
		self.list = []
		self.list.append(getConfigListEntry(_("Server"), config.plugins.ecccam.server))
		self.list.append(getConfigListEntry(_("Port"), config.plugins.ecccam.port))
		self.list.append(getConfigListEntry(_("UserName"), config.plugins.ecccam.name))
		self.list.append(getConfigListEntry(_("Password"), config.plugins.ecccam.passw))
		ConfigListScreen.__init__(self, self.list, session=session)
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions", "EPGSelectActions"],
		{
			"red": self.cancel,
			"cancel": self.cancel,
			"green": self.save,
			"ok": self.save
		}, -2)

	def get_config_path(self):
		path = '/etc/'
		if os.path.isfile("/etc/issue"):
			for line in open("/etc/issue"):
				if "openATV" in line:
					return '/usr/keys/'
		return path

	def cancel(self):
		for i in self["config"].list:
			i[1].cancel()
		self.close(False)

	def save(self):
		if os.path.isfile('%sCCcam.cfg' % self.config_path):
			os.rename('%sCCcam.cfg' % self.config_path, '%sCCcam.cfg.bak' % self.config_path)
		with open("%sCCcam.cfg" % self.config_path, "w") as config_file:
			if os.path.isfile('%sCCcam.cfg.bak' % self.config_path):
				for line in open('%sCCcam.cfg.bak' % self.config_path):
					if line.startswith("C:") or line.startswith("#C:"):
						config_file.write('C: %s %s %s %s\r\n' % (config.plugins.ecccam.server.value, config.plugins.ecccam.port.value, config.plugins.ecccam.name.value, config.plugins.ecccam.passw.value))
					else:
						config_file.write(line)
			else:
				config_file.write('C: %s %s %s %s\r\n' % (config.plugins.ecccam.server.value, config.plugins.ecccam.port.value, config.plugins.ecccam.name.value, config.plugins.ecccam.passw.value))
			config_file.close()
		self.mbox = self.session.open(MessageBox,(_("configuration is saved")), MessageBox.TYPE_INFO, timeout = 4 )

def main(session, **kwargs):
	session.open(ecccam_setup)

def Plugins(**kwargs):
	result = [
			PluginDescriptor(
			name=_("2boom's Easy CCcam"),
			description = _("Easy Edit CCcam.cfg"),
			where = PluginDescriptor.WHERE_PLUGINMENU,
			icon = 'ecccam.png',
			fnc = main
		),
	]
	return result
