# -*- coding: utf-8 -*-
# by 2boom 2011-2015 4bob@ua.fm
from Components.config import config, getConfigListEntry, ConfigText, ConfigPassword, ConfigSelection, ConfigSubsection, ConfigYesNo, config, configfile
from Components.ConfigList import ConfigListScreen
from Components.ScrollLabel import ScrollLabel
from Components.Sources.StaticText import StaticText
from Components.ActionMap import ActionMap, NumberActionMap
from Screens.PluginBrowser import PluginBrowser
from Screens.MessageBox import MessageBox
from Components.MenuList import MenuList
from Components.Sources.List import List
from Tools.LoadPixmap import LoadPixmap
from Plugins.Plugin import PluginDescriptor
from Components.Console import Console as iConsole
from Screens.Screen import Screen
from Components.Label import Label
from enigma import eTimer
from Components.Language import language
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from os import environ
import time
import os
import gettext
from . import tools

lang = language.getLanguage()
environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("epanel", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/epanel/locale"))


def _(txt):
	t = gettext.dgettext("epanel", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t


def logging(line):
	log_file = open('/tmp/epanel.log', 'a')
	log_file.write(line)
	log_file.close()


####################################################################
config.plugins.epanel.activeserver = ConfigText(default="NotSelected")
config.plugins.epanel.activeconf = ConfigText(default="NotSelected")
config.plugins.epanel.activeemu = ConfigText(default="NotSelected")
config.plugins.epanel.addbiss = ConfigSelection(default="0", choices=[
		("0", _("No")),
		("1", _("Yes")),
		])
config.plugins.epanel.path = ConfigSelection(default="/usr/keys/", choices=[
		("/usr/keys/", "/usr/keys/"),
		("/etc/keys/", "/etc/keys/"),
		("/etc/tuxbox/config/", "/etc/tuxbox/config/"),
		("/etc/tuxbox/config/oscam/", "/etc/tuxbox/config/oscam/"),
		("/etc/tuxbox/config/ncam/", "/etc/tuxbox/config/ncam/"),
		])
config.plugins.epanel.keyname = ConfigSelection(default="SoftCam.Key", choices=[
		("SoftCam.Key", "SoftCam.Key"),
		("oscam.keys", "oscam.keys"),
		("oscam.biss", "oscam.biss"),
		("ncam.keys", "ncam.keys"),
		("ncam.biss", "ncam.biss"),
		])
config.plugins.epanel.softcamserver = ConfigText(default="http://softcam.esy.es/softcam/SoftCam.Key", visible_width=200, fixed_size=False)
config.plugins.usw = ConfigSubsection()
config.plugins.usw.activeconf = ConfigText(default="")
config.plugins.usw.configpath = ConfigText(default="")
config.plugins.usw.emu = ConfigText(default="")
config.plugins.usw.configfile = ConfigText(default="")
config.plugins.usw.configext = ConfigText(default="")

config.plugins.uswoscam = ConfigSubsection()
config.plugins.uswoscam.active = ConfigYesNo(default=False)
config.plugins.uswoscam.activeconf = ConfigText(default="NotSelected")
config.plugins.uswoscam.configpath = ConfigText(default="/etc/tuxbox/config/oscam", visible_width=200, fixed_size=False)
config.plugins.uswoscam.configfile = ConfigText(default="oscam.conf", visible_width=200, fixed_size=False)
config.plugins.uswoscam.configext = ConfigText(default="os", visible_width=100, fixed_size=False)

config.plugins.uswncam = ConfigSubsection()
config.plugins.uswncam.active = ConfigYesNo(default=False)
config.plugins.uswncam.activeconf = ConfigText(default="NotSelected")
config.plugins.uswncam.configpath = ConfigText(default="/etc/tuxbox/config/ncam", visible_width=200, fixed_size=False)
config.plugins.uswncam.configfile = ConfigText(default="ncam.conf", visible_width=200, fixed_size=False)
config.plugins.uswncam.configext = ConfigText(default="os", visible_width=100, fixed_size=False)
######################################################################################


def ecm_view():
	list = ''
	port_flag = 0
	if fileExists("/tmp/ecm.info"):
		try:
			ecmfiles = open('/tmp/ecm.info', 'r')
			for line in ecmfiles:
				if 'port:' in line:
					port_flag = 1
				if 'caid:' in line or 'provider:' in line or 'provid:' in line or 'pid:' in line or 'hops:' in line or 'system:' in line or 'address:' in line or 'using:' in line or 'ecm time:' in line:
					line = line.replace(' ', '').replace(':', ': ')
				if 'from:' in line or 'protocol:' in line or 'caid:' in line or 'pid:' in line or 'reader:' in line or 'hops:' in line or 'system:' in line or 'Service:' in line or 'CAID:' in line or 'Provider:' in line:
					line = line.strip('\n') + '  '
				if 'Signature' in line:
					line = ""
				if '=' in line:
					line = line.lstrip('=').replace('======', "").replace('\n', "").rstrip() + ', '
				if 'ecmtime:' in line:
					line = line.replace('ecmtime:', 'ecm time:')
				if 'response time:' in line:
					line = line.replace('response time:', 'ecm time:').replace('decoded by', 'by')
				if not line.startswith('\n'):
					if 'protocol:' in line and port_flag == 0:
						line = '\n' + line
					if 'pkey:' in line:
						line = '\n' + line + '\n'
					list += line
			ecmfiles.close()
			return list
		except:
			return ''
	return ''
######################################################################################


class emuSel5(Screen):
	skin = """
	<screen name="emuSel5" position="265,125" size="750,490" title="Select SoftCam or CardServer">
  		<widget source="menu" render="Listbox" position="15,10" size="720,250" scrollbarMode="showOnDemand">
   			<convert type="TemplatedMultiContent">
				{"template": [
					MultiContentEntryText(pos = (70, 2), size = (630, 25), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel
					MultiContentEntryText(pos = (80, 29), size = (580, 18), font=1, flags = RT_HALIGN_LEFT, text = 1), # index 3 is the Description
					MultiContentEntryPixmapAlphaTest(pos = (5, 5), size = (50, 40), png = 2), # index 4 is the pixmap
					],
					"fonts": [gFont("Regular", 23),gFont("Regular", 16)],
					"itemHeight": 50
				}
			</convert>
  		</widget>
  		<ePixmap position="20,488" zPosition="1" size="170,2" pixmap="~/images/red.png" transparent="1" alphaTest="on" />
  		<ePixmap position="190,488" zPosition="1" size="170,2" pixmap="~/images/green.png" transparent="1" alphaTest="on" />
  		<ePixmap position="360,488" zPosition="1" size="170,2" pixmap="~/images/yellow.png" transparent="1" alphaTest="on" />
  		<ePixmap position="530,488" zPosition="1" size="200,2" pixmap="~/images/blue.png" transparent="1" alphaTest="on" />
  		<widget name="key_red" position="20,458" zPosition="2" size="170,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
  		<widget name="key_green" position="190,458" zPosition="2" size="170,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
  		<widget name="key_yellow" position="360,458" zPosition="2" size="170,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
  		<widget name="key_blue" position="530,458" zPosition="2" size="200,30" verticalAlignment="center" horizontalAlignment="center" font="Regular;22" transparent="1" />
  		<widget name="text" position="25,310" size="700,205" font="Regular;22" horizontalAlignment="center" noWrap="1" />
		<widget source="inmemory" render="Label"  position="50,270" size="650,24" font="Regular;22"  horizontalAlignment="center" noWrap="1" />
		<eLabel position="25,268" size="700,2" backgroundColor="#00aaaaaa" zPosition="3" />
		<eLabel position="25,298" size="700,2" backgroundColor="#00aaaaaa" zPosition="3" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/epanel")
		self.setTitle(_("Select SoftCam or CardServer: - %s") % config.plugins.epanel.activeemu.value)
		self.session = session
		self.iConsole = iConsole()
		self.current_emu = ''
		self.emutype = ''
		self.list = []
		self.indexpos = None
		self["menu"] = List(self.list)
		self["actions"] = ActionMap(["OkCancelActions", "ColorActions"],
			{
				"cancel": self.cancel,
				"ok": self.ok,
				"green": self.ok,
				"red": self.emuStopOperation,
				"yellow": self.emuRestartOperation,
				"blue": self.switcher,
			}, -1)
		self.list = []
		self["key_red"] = Label(_("Stop"))
		self["key_green"] = Label(_("Start"))
		self["key_yellow"] = Label(_("ReStart"))
		self["key_blue"] = Label(_("Switcher"))
		self["text"] = ScrollLabel("")
		self["inmemory"] = StaticText()
		self.update_rc()
		self.listecm()
		self.Timer = eTimer()
		self.Timer.callback.append(self.listecm)
		self.Timer.start(1000 * 4, False)
		self.selemulist()

	def update_rc(self):
		if not fileExists('/etc/init.d/softcam'):
			self.iConsole.ePopen("echo -e '# Placeholder for no cam' >> /etc/init.d/softcam.None && ln -s /etc/init.d/softcam.None /etc/init.d/softcam")
		if not fileExists('/etc/rc3.d/S50softcam'):
			self.iConsole.ePopen('echo /etc/init.d/softcam restart > /etc/rc3.d/S50softcam | chmod 777 /etc/rc3.d/S50softcam')

	def selemulist(self):
		self.list = []
		typeemu = ' '
		camdlist = os.listdir("/etc/init.d/")
		for line in camdlist:
			if '.None' not in line and '.none' not in line:
				if line.split(".")[0] == 'softcam':
					typeemu = 'softcam'
					if self.emuversion(line) == self.emuversion('softcam'):
						softpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/epanel/images/%s" % 'emuact.png'))
					else:
						softpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/epanel/images/%s" % 'emumini.png'))
				elif line.split(".")[0] == 'cardserver':
					typeemu = 'cardserver'
					if self.emuversion(line) == self.emuversion('cardserver'):
						softpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/epanel/images/%s" % 'cardact.png'))
					else:
						softpng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/epanel/images/%s" % 'cardmini.png'))
				try:
					if 'softcam.' in line or 'cardserver.' in line:
						self.list.append((line, self.emuversion(line), softpng, typeemu))
				except:
					pass
		self.list.sort()
		self["menu"].setList(self.list)
		self.setTitle(_("Select SoftCam or CardServer: - %s") % config.plugins.epanel.activeemu.value)
		if self.indexpos is not None:
			self["menu"].setIndex(self.indexpos)
		self.name_in_memory()

	def emuversion(self, what):
		emuname = ' '
		nameemu = []
		if fileExists('/etc/init.d/%s' % what.split("\n")[0]):
			try:
				for line in open('/etc/init.d/%s' % what.split("\n")[0]):
					if 'echo' in line:
						nameemu.append(line)
				emuname = '%s' % nameemu[1].split('"')[1]
			except:
				emuname = ' '
		return emuname

	def cut_name(self, what):
		count = 0
		what = what.replace('_', ' ').replace('-', ' ')
		count = len(what.split())
		if count <= 1:
			return what
		else:
			return what.split()[0]

	def name_in_memory(self):
		self.iConsole.ePopen("ps", self.stdout_find)

	def stdout_find(self, result, retval, extra_args):
		#if retval is 0:
		status = ''
		name_emu = self.cut_name(self.emuversion('softcam'))
		name_card = self.cut_name(self.emuversion('cardserver'))
		if name_card != ' ':
			for line in result.splitlines(True):
				if name_card.split()[0].upper() in result.upper():
					status += '%s ' % name_card
					break
		if name_emu != ' ':
			for line in result.splitlines(True):
				if name_emu.split()[0].upper() in result.upper():
					status += '%s' % name_emu
					break
		try:
			if status != '':
				self["inmemory"].text = _('%s loaded in memory') % status
			else:
				self["inmemory"].text = _('not loaded modules')
		except Exception as e:
			now = time.localtime(time.time())
			logging('%02d:%02d:%d %02d:%02d:%02d - %s\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, str(e)))

	def listecm(self):
		self["text"].setText(ecm_view())
##################################################################################

	def ok(self):
		try:
			self.setTitle(_("Please wait"))
			self.emutype = self["menu"].getCurrent()[3]
			self.current_item = self["menu"].getCurrent()[0]
			if self["menu"].getCurrent()[1] != self.emuversion(self.emutype):
				self.indexpos = self["menu"].getIndex()
				self.session.openWithCallback(self.selemulist, start_cam, self.emutype, self.current_item)
		except Exception as e:
			now = time.localtime(time.time())
			logging('%02d:%02d:%d %02d:%02d:%02d - %s\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, str(e)))
##################################################################################

	def emuStopOperation(self):
		try:
			self.setTitle(_("Please wait"))
			self.emutype = self["menu"].getCurrent()[3]
			self.current_item = self["menu"].getCurrent()[0]
			if self.emuversion(self.emutype) != ' ':
				self.indexpos = self["menu"].getIndex()
				self.session.openWithCallback(self.selemulist, stop_cam, self.emutype)
		except Exception as e:
			now = time.localtime(time.time())
			logging('%02d:%02d:%d %02d:%02d:%02d - %s\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, str(e)))
##################################################################################

	def emuRestartOperation(self):
		try:
			self.setTitle(_("Please wait"))
			self.emutype = self["menu"].getCurrent()[3]
			if self.emuversion(self.emutype) != ' ':
				self.indexpos = self["menu"].getIndex()
				self.session.openWithCallback(self.selemulist, restart_cam, self.emutype)
		except Exception as e:
			now = time.localtime(time.time())
			logging('%02d:%02d:%d %02d:%02d:%02d - %s\r\n' % (now.tm_mday, now.tm_mon, now.tm_year, now.tm_hour, now.tm_min, now.tm_sec, str(e)))

	def cancel(self):
		self.close()

	def switcher(self):
		status = True
		if fileExists('/etc/init.d/softcam'):
			for line in open('/etc/init.d/softcam'):
				if 'oscam' in line.lower():
					config.plugins.usw.activeconf.value = config.plugins.uswoscam.activeconf.value
					config.plugins.usw.configpath.value = config.plugins.uswoscam.configpath.value
					config.plugins.usw.emu.value = "Oscam"
					config.plugins.usw.configfile.value = config.plugins.uswoscam.configfile.value
					config.plugins.usw.configext.value = config.plugins.uswoscam.configext.value
				elif 'ncam' in line.lower():
					config.plugins.usw.activeconf.value = config.plugins.uswncam.activeconf.value
					config.plugins.usw.configpath.value = config.plugins.uswncam.configpath.value
					config.plugins.usw.emu.value = "Ncam"
					config.plugins.usw.configfile.value = config.plugins.uswncam.configfile.value
					config.plugins.usw.configext.value = config.plugins.uswncam.configext.value
				elif 'placeholder' in line.lower():
					status = False
			if status:
				self.session.open(uniswitcher)
			else:
				self.session.open(UniConfigScreen)
		else:
			self.session.open(UniConfigScreen)


#####################################################################################################
SKIN_DWN = """
<screen name="get_epg_data" position="center,140" size="625,35" title="Please wait">
  <widget source="status" render="Label" position="10,5" size="605,22" zPosition="2" font="Regular; 20" horizontalAlignment="center" transparent="2" />
</screen>"""


class start_cam(Screen):
	def __init__(self, session, emutype, current_item):
		Screen.__init__(self, session)
		self.session = session
		self.skin = SKIN_DWN
		self.emutype = emutype
		self.current_item = current_item
		self.setTitle(_("Please wait"))
		self["status"] = StaticText()
		self.iConsole = iConsole()
		self["status"].text = _("Stoping...")
		self.iConsole.ePopen("/etc/init.d/%s stop" % self.emutype, self.emuRemoveStartScript)

	def emuRemoveStartScript(self, result, retval, extra_args):
		self["status"].text = _("Removing startscript...")
		self.iConsole.ePopen("rm -f /etc/init.d/%s" % self.emutype, self.emuRemoveEcmInfo)

	def emuRemoveEcmInfo(self, result, retval, extra_args):
		self["status"].text = _("Removing ecm.info...")
		self.iConsole.ePopen("rm -f /tmp/ecm.info", self.emuAddStartScript)

	def emuAddStartScript(self, result, retval, extra_args):
		self["status"].text = _("Adding startscript...")
		self.iConsole.ePopen("ln -s /etc/init.d/%s /etc/init.d/%s" % (self.current_item, self.emutype), self.emuChmodStartScript)

	def emuChmodStartScript(self, result, retval, extra_args):
		self.iConsole.ePopen("chmod 777 /etc/init.d/%s" % self.emutype, self.emuScriptStart)

	def emuScriptStart(self, result, retval, extra_args):
		self["status"].text = _("Starting...")
		self.iConsole.ePopen("/etc/init.d/%s start" % self.emutype, self.sleep_time)

	def sleep_time(self, result, retval, extra_args):
		self.iConsole.ePopen("sleep 6", self.emuStartEndOperation)

	def emuStartEndOperation(self, result, retval, extra_args):
		config.plugins.epanel.activeemu.value = self.emuversion(self.emutype)
		config.plugins.epanel.activeemu.save()
		self["status"].setText(' ')
		self.close()

	def emuversion(self, what):
		emuname = ' '
		nameemu = []
		if fileExists('/etc/init.d/%s' % what.split("\n")[0]):
			try:
				for line in open('/etc/init.d/%s' % what.split("\n")[0]):
					if 'echo' in line:
						nameemu.append(line)
				emuname = '%s' % nameemu[1].split('"')[1]
			except:
				emuname = ' '
		return emuname


class restart_cam(Screen):
	def __init__(self, session, emutype):
		Screen.__init__(self, session)
		self.session = session
		self.skin = SKIN_DWN
		self.emutype = emutype
		self.setTitle(_("Please wait"))
		self["status"] = StaticText()
		self.iConsole = iConsole()
		self["status"].text = _("Restarting...")
		self.iConsole.ePopen("/etc/init.d/%s restart" % self.emutype, self.sleep_time)

	def sleep_time(self, result, retval, extra_args):
		self.iConsole.ePopen("sleep 6", self.emuRestartOperationEnd)

	def emuRestartOperationEnd(self, result, retval, extra_args):
		self["status"].setText(' ')
		self.close()
####################################################################################################


class stop_cam(Screen):
	def __init__(self, session, emutype):
		Screen.__init__(self, session)
		self.session = session
		self.skin = SKIN_DWN
		self.emutype = emutype
		self.setTitle(_("Please wait"))
		self["status"] = StaticText()
		self.iConsole = iConsole()
		self["status"].text = _("Stoping...")
		self.iConsole.ePopen("/etc/init.d/%s stop" % self.emutype, self.emuRemoveScriptStop)

	def emuRemoveScriptStop(self, result, retval, extra_args):
		self["status"].text = _("Removing startscript...")
		self.iConsole.ePopen("rm -f /etc/init.d/%s" % self.emutype, self.emuRemoveEcmInfoStop)

	def emuRemoveEcmInfoStop(self, result, retval, extra_args):
		self["status"].text = _("Removing ecm.info...")
		self.iConsole.ePopen("rm -f /tmp/ecm.info", self.emuCreateNone)

	def emuCreateNone(self, result, retval, extra_args):
		self["status"].text = _("Creating None script...")
		if fileExists("/etc/init.d/%s.None" % self.emutype):
			self.iConsole.ePopen("ln -s /etc/init.d/%s.None /etc/init.d/%s" % (self.emutype, self.emutype), self.emuChmodStopScript)
		elif fileExists("/etc/init.d/%s.none" % self.emutype):
			self.iConsole.ePopen("ln -s /etc/init.d/%s.none /etc/init.d/%s" % (self.emutype, self.emutype), self.emuChmodStopScript)
		else:
			self.iConsole.ePopen("echo -e '# Placeholder for no cam' >> /etc/init.d/%s.None && ln -s /etc/init.d/%s.None /etc/init.d/%s" %
				(self.emutype, self.emutype, self.emutype), self.emuChmodStopScript)

	def emuChmodStopScript(self, result, retval, extra_args):
		self.iConsole.ePopen("chmod 777 /etc/init.d/%s" % self.emutype, self.sleep_time)

	def sleep_time(self, result, retval, extra_args):
		self.iConsole.ePopen("sleep 4", self.emuStopEndOperation)

	def emuStopEndOperation(self, result, retval, extra_args):
		self["status"].setText(' ')
		self.close()
####################################################################################################


class SoftcamPanel2(Screen):
	skin = """
	<screen name="SoftcamPanel2" position="center,160" size="750,370" title="SoftCam/CardServer Panel">
		<ePixmap position="20,358" zPosition="1" size="170,2" pixmap="~/images/red.png" alphaTest="blend" />
		<widget source="key_red" render="Label" position="20,328" zPosition="2" size="170,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
		<widget source="menu" render="Listbox" position="15,10" size="720,300" scrollbarMode="showOnDemand">
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
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/epanel")
		self.indexpos = None
		self.setTitle(_("SoftCam/CardServer Panel"))
		#self["shortcuts"] = ActionMap(["ShortcutActions", "WizardActions"],
		self["shortcuts"] = NumberActionMap(["ShortcutActions", "WizardActions", "NumberActions"],
		{
			"ok": self.keyOK,
			"cancel": self.exit,
			"back": self.exit,
			"red": self.exit,
			"1": self.go,
			"2": self.go,
			"3": self.go,
		})
		self["key_red"] = StaticText(_("Close"))
		self.list = []
		self["menu"] = List(self.list)
		self.mList()

	def mList(self):
		self.list = []
		onepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/epanel/images/softcam.png"))
		twopng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/epanel/images/unisw.png"))
		treepng = LoadPixmap(cached=True, path=resolveFilename(SCOPE_PLUGINS, "Extensions/epanel/images/soft.png"))
		self.list.append((_("Simple Softcam/Cardserver"), 1, _("Start, Stop, Restart Sofcam/Cardserver"), onepng))
		self.list.append((_("Universal Switcher"), 2, _("switch config files oscam and ncam with remote conrol"), twopng))
		self.list.append((_("SoftCam.Key Updater"), 3, _("update Softcam.key from internet"), treepng))
		if self.indexpos != None:
			self["menu"].setIndex(self.indexpos)
		self["menu"].setList(self.list)

	def exit(self):
		self.close()

	def go(self, num=None):
		if num is not None:
			num -= 1
			if not num < self["menu"].count():
				return
			self["menu"].setIndex(num)
		item = self["menu"].getCurrent()[1]
		self.select_item(item)

	def keyOK(self, item=None):
		if item == None:
			self.indexpos = self["menu"].getIndex()
			item = self["menu"].getCurrent()[1]
			self.select_item(item)

	def select_item(self, item):
		if item:
			if item == 1:
				self.session.open(emuSel5)
			elif item == 2:
				self.session.open(UniConfigScreen)
			elif item == 3:
				self.session.open(SoftcamUpd2)
			else:
				self.close(None)

###############################################################################################


class SoftcamUpd2(ConfigListScreen, Screen):
	skin = """
	<screen name="SoftcamUpd2" position="center,160" size="750,370" title="SoftCam.Key Updater">
		<widget position="15,10" size="720,300" name="config" scrollbarMode="showOnDemand" />
		<ePixmap position="10,358" zPosition="1" size="165,2" pixmap="~/images/red.png" alphaTest="blend" />
		<widget source="key_red" render="Label" position="10,328" zPosition="2" size="165,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
		<ePixmap position="175,358" zPosition="1" size="165,2" pixmap="~/images/green.png" alphaTest="blend" />
		<widget source="key_green" render="Label" position="175,328" zPosition="2" size="165,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
		<ePixmap position="340,358" zPosition="1" size="165,2" pixmap="~/images/yellow.png" alphaTest="blend" />
		<widget source="key_yellow" render="Label" position="340,328" zPosition="2" size="165,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
	</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/epanel")
		self.setTitle(_("SoftCam.Key Updater"))
		self.iConsole = iConsole()
		self.list = []
		self.list.append(getConfigListEntry(_("SoftCam.Key server"), config.plugins.epanel.softcamserver))
		self.list.append(getConfigListEntry(_("Path to save keyfile"), config.plugins.epanel.path))
		self.list.append(getConfigListEntry(_("Name of keyfile"), config.plugins.epanel.keyname))
		ConfigListScreen.__init__(self, self.list)
		#ConfigListScreen.__init__(self, self.list, session=session)
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Download"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions", "EPGSelectActions"],
		{
			"red": self.cancel,
			"cancel": self.cancel,
			"green": self.save,
			"yellow": self.CreateOldKeyFile,
			"ok": self.save
		}, -2)

	def cancel(self):
		for i in self["config"].list:
			i[1].cancel()
		self.close(False)

	def save(self):
		for i in self["config"].list:
			i[1].save()
		configfile.save()
		self.mbox = self.session.open(MessageBox, (_("configuration is saved")), MessageBox.TYPE_INFO, timeout=4)

	def CreateOldKeyFile(self):
		self.mbox = self.session.open(MessageBox, (_("%s downloading" % config.plugins.epanel.keyname.value)), MessageBox.TYPE_INFO)
		self.iConsole.ePopen('mv %s%s %s%s' %
			(config.plugins.epanel.path.value, config.plugins.epanel.keyname.value, config.plugins.epanel.path.value, config.plugins.epanel.keyname.value.split('.')[0] + 'old'), self.DownloadKeyFile)

	def DownloadKeyFile(self, result, retval, extra_args):
		self.iConsole.ePopen("wget -q %s -O %s%s" %
			(config.plugins.epanel.softcamserver.value, config.plugins.epanel.path.value, config.plugins.epanel.keyname.value), self.CheckNewKeyFile)

	def CheckNewKeyFile(self, result, retval, extra_args):
		if retval == 0:
			if fileExists('%s%s' % (config.plugins.epanel.path.value, config.plugins.epanel.keyname.value)):
				self.iConsole.ePopen('rm -f %s%s' % (config.plugins.epanel.path.value, config.plugins.epanel.keyname.value.split('.')[0] + 'old'), self.ChmodKeyFile)
			else:
				self.iConsole.ePopen('mv %s%s %s%s' %
					(config.plugins.epanel.path.value, config.plugins.epanel.keyname.value.split('.')[0] + 'old', config.plugins.epanel.path.value, config.plugins.epanel.keyname.value), self.ChmodKeyFile)

	def ChmodKeyFile(self, result, retval, extra_args):
		self.iConsole.ePopen("chmod 644 %s%s" % (config.plugins.epanel.path.value, config.plugins.epanel.keyname.value))
		if self.mbox:
			self.mbox.close()
###############################################################################


class uniswitcher(Screen):
	skin = """
	<screen name="uniswitcher" position="center,140" size="750,460" title="...">
  		<ePixmap position="20,455" zPosition="1" size="170,2" pixmap="~/images/red.png" alphaTest="blend" />
  		<widget source="key_red" render="Label" position="20,425" zPosition="2" size="170,30" font="Regular; 19" horizontalAlignment="center" verticalAlignment="center" backgroundColor="background" foregroundColor="white" transparent="1" />
  		<ePixmap position="190,455" zPosition="1" size="250,2" pixmap="~/images/green.png" alphaTest="blend" />
  		<widget source="key_green" render="Label" position="190,425" zPosition="2" size="250,30" font="Regular; 19" horizontalAlignment="center" verticalAlignment="center" backgroundColor="background" foregroundColor="white" transparent="1" />
  		<widget source="list" render="Listbox" position="15,10" size="720,250" scrollbarMode="showOnDemand">
  			 <convert type="TemplatedMultiContent">
   				{"template": [
    					MultiContentEntryText(pos = (70, 2), size = (580, 25), font=0, flags = RT_HALIGN_LEFT, text = 0), # index 2 is the Menu Titel
    					MultiContentEntryText(pos = (80, 29), size = (580, 18), font=1, flags = RT_HALIGN_LEFT, text = 1), # index 3 is the Description
    					MultiContentEntryPixmapAlphaTest(pos = (5, 5), size = (51, 40), png = 2), # index 4 is the pixmap
   					],
   					"fonts": [gFont("Regular", 23),gFont("Regular", 16)],
   					"itemHeight": 50
  				}
    			</convert>
      		</widget>
   		<widget name="text" position="20,280" size="710,205" font="Regular;22" horizontalAlignment="center" noWrap="1" />
  		<eLabel position="20,268" size="710,2" backgroundColor="grey" zPosition="3" />
	</screen>"""

	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/epanel")
		self.iConsole = iConsole()
		self.skin = uniswitcher.skin
		self.setTitle(_("%s Switcher: - %s") % (config.plugins.usw.emu.value, config.plugins.usw.activeconf.value))
		self.session = session
		self.indexpos = None
		self.list = []
		self.servinactpng = LoadPixmap(path=resolveFilename(SCOPE_PLUGINS, "Extensions/epanel/images/serv.png"))
		self.servactpng = LoadPixmap(path=resolveFilename(SCOPE_PLUGINS, "Extensions/epanel/images/servact.png"))
		self["list"] = List(self.list)
		self["actions"] = ActionMap(["OkCancelActions", "ShortcutActions"],
		{
			"ok": self.run,
			"red": self.close,
			"green": self.restartsoft,
			"cancel": self.close
		}, -1)
		self["readServ"] = StaticText()
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Restart Softcam"))
		self["text"] = ScrollLabel("")
		self.listecm()
		self.Timer = eTimer()
		self.Timer.callback.append(self.listecm)
		self.Timer.start(1000 * 4, False)
		self.mList()

	def listecm(self):
		self["text"].setText(ecm_view())

	def mList(self):
		if config.plugins.usw.emu.value == "Oscam":
			config.plugins.usw.activeconf.value = config.plugins.uswoscam.activeconf.value
		elif config.plugins.usw.emu.value == "Ncam":
			config.plugins.usw.activeconf.value = config.plugins.uswncam.activeconf.value
		self.list = []
		if os.path.exists(config.plugins.usw.configpath.value):
			list = os.listdir('%s' % config.plugins.usw.configpath.value)
			for line in list:
				if '.%s' % config.plugins.usw.configext.value in line:
					if line[:-3] == config.plugins.usw.activeconf.value:
						self.list.append((line[:-3], self.Adress(line), self.servactpng))
					else:
						self.list.append((line[:-3], self.Adress(line), self.servinactpng))
			self.list.sort()
			self["list"].setList(self.list)
			if self.indexpos != None:
				self["list"].setIndex(self.indexpos)

	def run(self):
		if self["list"].getCurrent() is not None:
			config.plugins.usw.activeconf.value = self["list"].getCurrent()[0]
			if config.plugins.usw.emu.value == "Oscam":
				config.plugins.uswoscam.activeconf.value = config.plugins.usw.activeconf.value
				config.plugins.uswoscam.activeconf.save()
			elif config.plugins.usw.emu.value == "Ncam":
				config.plugins.uswncam.activeconf.value = config.plugins.usw.activeconf.value
				config.plugins.uswncam.activeconf.save()
			self.setTitle(_("%s Switcher: - %s") % (config.plugins.usw.emu.value, config.plugins.usw.activeconf.value))
			if fileExists("%s/%s" % (config.plugins.usw.configpath.value, config.plugins.usw.configfile.value)):
				file_cfg = open('%s/%s' % (config.plugins.usw.configpath.value, config.plugins.usw.configfile.value), 'r').read()
				file_prv = open('%s/previous.%s' % (config.plugins.usw.configpath.value, config.plugins.usw.configext.value), 'w')
				file_prv.write(file_cfg)
				file_prv.close()
				os.chmod('%s/previous.%s' % (config.plugins.usw.configpath.value, config.plugins.usw.configext.value), 664)
			file_cfg = open('%s/%s.%s' % (config.plugins.usw.configpath.value, self["list"].getCurrent()[0], config.plugins.usw.configext.value), 'r').read()
			file_prv = open('%s/%s' % (config.plugins.usw.configpath.value, config.plugins.usw.configfile.value), 'w')
			file_prv.write(file_cfg)
			file_prv.close()
			os.chmod('%s/%s' % (config.plugins.usw.configpath.value, config.plugins.usw.configfile.value), 664)
			self.session.open(MessageBox, _("%s %s" % (self["list"].getCurrent()[0], config.plugins.usw.configfile.value)), type=MessageBox.TYPE_INFO, timeout=6)
			self.indexpos = self["list"].getIndex()
			self.mList()

	def restartsoft(self):
		clearlist = ""
		if fileExists("/etc/init.d/softcam"):
			self["text"].setText(clearlist)
			self.iConsole.ePopen("/etc/init.d/softcam restart")
		if fileExists("/etc/init.d/cardserver"):
			self["text"].setText(clearlist)
			self.iConsole.ePopen("/etc/init.d/cardserver restart")
		self.session.open(MessageBox, _("Softcam Restarted"), type=MessageBox.TYPE_INFO, timeout=7)

	def Adress(self, nameserv):
		cardline = ""
		iscard = 0
		if config.plugins.usw.emu.value == "Oscam":
			if fileExists("%s/%s" % (config.plugins.usw.configpath.value, nameserv)):
				for line in open("%s/%s" % (config.plugins.usw.configpath.value, nameserv)):
					if "device" in line and "#" not in line:
						cardline += "card: %s " % line.split()[2]
					# card name change
					elif "internal" in line and "#" not in line:
						cardline += "card: %s " % line.split()[2].strip("]")
				return cardline
		elif config.plugins.usw.emu.value == "Ncam":
			if fileExists("%s/%s" % (config.plugins.usw.configpath.value, nameserv)):
				for line in open("%s/%s" % (config.plugins.usw.configpath.value, nameserv)):
					if "device" in line and "#" not in line:
						cardline += "card: %s " % line.split()[2]
					# card name change
					elif "internal" in line and "#" not in line:
						cardline += "card: %s " % line.split()[2].strip("]")
				return cardline
		return ""

####################################################################################


class UniConfigScreen(ConfigListScreen, Screen):
	skin = """
	<screen name="UniConfigScreen" position="center,140" size="750,460" title="E-Panel Universal Switcher">
  		<widget position="15,10" size="720,400" name="config" scrollbarMode="showOnDemand" />
  		<ePixmap position="10,455" zPosition="1" size="165,2" pixmap="~/images/red.png" alphaTest="blend" />
  		<widget source="key_red" render="Label" position="10,425" zPosition="2" size="165,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
  		<ePixmap position="175,455" zPosition="1" size="165,2" pixmap="~/images/green.png" alphaTest="blend" />
  		<widget source="key_green" render="Label" position="175,425" zPosition="2" size="165,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" backgroundColor="background" foregroundColor="foreground" transparent="1" />
	</screen>"""

	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/epanel")
		self.setTitle(_("E-Panel Universal Switcher"))
		self.list = []
		self.list.append(getConfigListEntry(_("Oscam config switcher"), config.plugins.uswoscam.active))
		self.list.append(getConfigListEntry(_("Oscam configpath"), config.plugins.uswoscam.configpath))
		self.list.append(getConfigListEntry(_("Oscam config filename"), config.plugins.uswoscam.configfile))
		self.list.append(getConfigListEntry(_("Oscam configfile extention"), config.plugins.uswoscam.configext))
		self.list.append(getConfigListEntry(_("Ncam config switcher"), config.plugins.uswncam.active))
		self.list.append(getConfigListEntry(_("Ncam configpath"), config.plugins.uswncam.configpath))
		self.list.append(getConfigListEntry(_("Ncam config filename"), config.plugins.uswncam.configfile))
		self.list.append(getConfigListEntry(_("Ncam configfile extention"), config.plugins.uswncam.configext))
		ConfigListScreen.__init__(self, self.list)
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
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

	def save(self):
		for i in self["config"].list:
			i[1].save()
		configfile.save()
		from Components.PluginComponent import plugins
		plugins.reloadPlugins()
		self.mbox = self.session.open(MessageBox, (_("configuration is saved")), MessageBox.TYPE_INFO, timeout=4)
####################################################################################
