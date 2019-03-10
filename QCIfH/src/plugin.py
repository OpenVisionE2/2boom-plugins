#QuickChannelInfo for Hotkey
#Copyright (c) 2boom 2015
# v.0.1-r0
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
from Components.ScrollLabel import ScrollLabel
from Components.Pixmap import Pixmap
from Components.Language import language
from Components.Sources.StaticText import StaticText
from Components.Sources.CurrentService import CurrentService
from Components.config import getConfigListEntry, ConfigText, ConfigYesNo, ConfigSubsection, ConfigSelection, config, configfile
from Components.ConfigList import ConfigListScreen
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS
from enigma import ePoint, eTimer, getDesktop, iServiceInformation, iPlayableService, iPlayableServicePtr
from os import environ
import gettext
import os, sys

lang = language.getLanguage()
environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("qcifh", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/QCIfH/locale/"))

def _(txt):
	t = gettext.dgettext("qcifh", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t
	
if os.path.isfile('%s%sbitratecalc.so' % (resolveFilename(SCOPE_PLUGINS), "Extensions/QCIfH/")):
	from bitratecalc import eBitrateCalculator
	binary_file = True
else:
	binary_file = False

config.plugins.qcifh = ConfigSubsection()	
config.plugins.qcifh.skin = ConfigYesNo(default=False)

SKIN_HD = """
<screen name="QCIfH" position="50,165" size="1180,335" title="2boom's QuickChannelInfo for Hotkey" zPosition="1">
  <widget source="session.FrontendStatus" render="Label" position="420,5" zPosition="2" size="360,35" font="Regular; 33" foregroundColor="#00aaaaaa" halign="center" valign="center" transparent="1">
    <convert type="FrontendInfo">SNRdB</convert>
  </widget>
  <eLabel name="snr" text="SNR:" position="5,85" size="100,35" font="Regular;33" halign="right" foregroundColor="#00aaaaaa" transparent="1" />
  <widget source="session.FrontendStatus" render="Progress" position="135,50" size="910,100" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/QCIfH/images/bar.png" zPosition="2" borderWidth="4" borderColor="un656565">
    <convert type="FrontendInfo">SNR</convert>
  </widget>
  <widget source="session.FrontendStatus" render="Label" position="1080,85" size="100,35" font="Regular;33" foregroundColor="#00aaaaaa" transparent="1">
    <convert type="FrontendInfo">SNR</convert>
  </widget>
  <eLabel name="agc" text="AGC:" position="5,190" size="100,35" font="Regular;33" halign="right" foregroundColor="#00aaaaaa" transparent="1" />
  <widget source="session.FrontendStatus" render="Progress" position="135,160" size="910,100" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/QCIfH/images/bar.png" zPosition="2" borderWidth="4" borderColor="un656565">
    <convert type="FrontendInfo">AGC</convert>
  </widget>
  <widget source="session.FrontendStatus" render="Label" position="1080,190" size="100,35" font="Regular;33" foregroundColor="#00aaaaaa" transparent="1">
    <convert type="FrontendInfo">AGC</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="133,270" size="575,30" font="Regular; 27" foregroundColor="#00aaaaaa" transparent="1" halign="left" zPosition="5" valign="center">
    <convert type="ServiceName">Name</convert>
  </widget>
  <widget source="session.CurrentService" render="Label" position="131,304" zPosition="3" size="350,25" valign="top" halign="left" font="Regular; 22" transparent="1" foregroundColor="#00aaaaaa">
    <convert type="ServiceName">Provider</convert>
  </widget>
</screen>"""

class QCIfH(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		if config.plugins.qcifh.skin.value:
			if os.path.isfile('%sExtensions/QCIfH/skin_user.xml' % resolveFilename(SCOPE_PLUGINS)):
				with open('%sExtensions/QCIfH/skin_user.xml' % resolveFilename(SCOPE_PLUGINS),'r') as user_skin:
					self.skin = user_skin.read()
				user_skin.close()
			else:
				self.skin = SKIN_HD
		else:
			self.skin = SKIN_HD
		self["vbit"] = StaticText()
		self["abit"] = StaticText()
		self["resx"] = StaticText()
		self["resy"] = StaticText()
		self["fps"] = StaticText()
		self["codec"] = StaticText()
		self["sids"] = StaticText()
		self["actions"] = ActionMap(["WizardActions",  "MenuActions"],
		{
			"back": self.close,
			"ok": self.close,
			"right": self.close,
			"left": self.close,
			"down": self.close,
			"up": self.close,
			"menu": self.conf,
		}, -2)
		ref = session.nav.getCurrentlyPlayingServiceReference()
		vpid = apid = dvbnamespace = tsid = onid = -1
		service = session.nav.getCurrentService()
		if service:
			serviceInfo = service.info()
			info = service and service.info()
			vpid = info.getInfo(iServiceInformation.sVideoPID)
			apid = info.getInfo(iServiceInformation.sAudioPID)
			tsid = info.getInfo(iServiceInformation.sTSID)
			onid = info.getInfo(iServiceInformation.sONID)
			dvbnamespace = info.getInfo(iServiceInformation.sNamespace)
			self.resolutionx = self.resolutionx(serviceInfo)
			self.resolutiony = self.resolutiony(serviceInfo)
			self.fps = self.fps(serviceInfo)
			audio = service.audioTracks()
			if audio:
				if audio.getCurrentTrack() > -1:
					self.audiocodec = str(audio.getTrackInfo(audio.getCurrentTrack()).getDescription()).replace(",","")
			self.videocodec = ("MPEG2", "MPEG4", "MPEG1", "MPEG4-II", "VC1", "VC1-SM", "")[info.getInfo(iServiceInformation.sVideoType)]
		if apid and binary_file:
			self.audioBitrate = eBitrateCalculator(apid, dvbnamespace, tsid, onid, 1000, 64*1024)
			self.audioBitrate.callback.append(self.getAudioBitrateData)
		if vpid and binary_file:
			self.videoBitrate = eBitrateCalculator(vpid, dvbnamespace, tsid, onid, 1000, 1024*1024)
			self.videoBitrate.callback.append(self.getVideoBitrateData)
		self.onShow.append(self.staticinfo)
		
	def staticinfo(self):
		self.setTitle(_("2boom's QuickChannelInfo for Hotkey"))
		self["resx"].text = self.resolutionx
		self["resy"].text = self.resolutiony
		self["fps"].text = self.fps
		self["codec"].text = '%s/%s' % (self.videocodec, self.audiocodec)
		self["sids"].text = self.pidsline()
		
	def pidsline(self):
		vpid = apid = tsid = onid = sid = -1
		service = self.session.nav.getCurrentService()
		if service is not None:
			info = service and service.info()
			sid = info.getInfo(iServiceInformation.sSID)
			vpid = info.getInfo(iServiceInformation.sVideoPID)
			apid = info.getInfo(iServiceInformation.sAudioPID)
			tsid = info.getInfo(iServiceInformation.sTSID)
			onid = info.getInfo(iServiceInformation.sONID)
			prcpid = info.getInfo(iServiceInformation.sPCRPID)
		return 'Sid: %0.4X  Vpid: %0.4X  Apid: %0.4X  Tsid: %0.4X  Prcpid: %0.4X  Onid: %0.4X' % (sid, vpid, apid, tsid, prcpid, onid)	

	def resolutionx(self, serviceInfo):
		xres = serviceInfo.getInfo(iServiceInformation.sVideoWidth)
		if xres == -1:
			return ''
		return str(xres)
	
	def resolutiony(self, serviceInfo):
		yres = serviceInfo.getInfo(iServiceInformation.sVideoHeight)
		if yres == -1:
			return ''
		mode = ('i', 'p', ' ')[serviceInfo.getInfo(iServiceInformation.sProgressive)]
		return str(yres) + mode
		
	def fps(self, serviceInfo):
		xres = serviceInfo.getInfo(iServiceInformation.sVideoWidth)
		if xres == -1:
			return ''
		fps  = str((serviceInfo.getInfo(iServiceInformation.sFrameRate) + 500) / 1000)
		return fps

	def getVideoBitrateData(self,value, status): 
		if status:
			self["vbit"].text = '%d Kb/s' % value
		else:
			self.videoBitrate = None		

	def getAudioBitrateData(self,value, status): 
		if status:
			self["abit"].text = '%s Kb/s' % value
		else:
			self.audioBitrate = None

	def conf(self):
		self.session.open(qcifh_setup)
	
SKIN_CONFIG_HD = """
<screen name="qcifh_setup" position="265,160" size="750,75" title="2boom's QuickChannelInfo setup">
  <widget position="15,10" size="720,25" name="config" scrollbarMode="showOnDemand" />
  <ePixmap position="10,70" zPosition="1" size="165,2" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/QCIfH/images/red.png" alphatest="blend" />
  <widget source="key_red" render="Label" position="10,40" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" transparent="1" />
  <ePixmap position="175,70" zPosition="1" size="165,2" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/QCIfH/images/green.png" alphatest="blend" />
  <widget source="key_green" render="Label" position="175,40" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" transparent="1" />
</screen>"""

class qcifh_setup(Screen, ConfigListScreen):
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skin = SKIN_CONFIG_HD
		self.setTitle(_("2boom's QuickChannelInfo setup"))
		self.list = []
		self.list.append(getConfigListEntry(_("User skin"), config.plugins.qcifh.skin))
		ConfigListScreen.__init__(self, self.list, session=session)
		self["text"] = ScrollLabel("")
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
		self.mbox = self.session.open(MessageBox,(_("configuration is saved")), MessageBox.TYPE_INFO, timeout = 4 )
		
def main(session, **kwargs):
	session.open(QCIfH)

def Plugins(**kwargs):
	list = [PluginDescriptor(name=_("2boom's QuickChannelInfo for Hotkey"), description=_("quickchannelinfo for hotkey extentions"), where = [PluginDescriptor.WHERE_PLUGINMENU], icon="qcifh.png", fnc=main)]
	return list