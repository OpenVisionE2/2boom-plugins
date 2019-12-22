# QuickEcmInfo2 Converter
# Copyright (c) 2boom 2012-14
# v.1.3-r0 29.06.2014
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

from Poll import Poll
from Components.Converter.Converter import Converter
from enigma import eTimer, iPlayableService, iServiceInformation, eServiceReference, iServiceKeys, getDesktop
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigText, ConfigPassword, ConfigClock, ConfigSelection, ConfigSubsection, ConfigYesNo, configfile
from Components.Element import cached
from Tools.Directories import fileExists
import os, time
if os.path.isfile('/usr/lib/bitratecalc.so'):
	from bitratecalc import eBitrateCalculator
	binaryfound = True
else:
	binaryfound = False

class QuickEcmInfo2(Poll, Converter, object):
	caidbar = 0
	txtcaid = 1
	boxdata = 2
	ecmfile = 3
	emuname = 4
	pids = 5
	bitrate = 6

	def __init__(self, type):
		Converter.__init__(self, type)
		Poll.__init__(self)
		if type == "caidbar":
			self.type = self.caidbar
		elif type == "txtcaid":
			self.type = self.txtcaid
		elif type == "boxdata":
			self.type = self.boxdata
		elif type == "ecmfile":
			self.type = self.ecmfile
		elif type == "emuname":
			self.type = self.emuname
		elif type == "pids":
			self.type = self.pids
		elif type == "bitrate":
			self.type = self.bitrate
		self.basecolor = self.convert_color('#00ffffff')
		self.maincolor = self.convert_color('#00aaaaaa')
		self.emmcolor = self.convert_color('#0003a902')
		self.ecmcolor = self.convert_color('#00f0bf4f')
		self.videoBitrate = self.audioBitrate = None
		self.video = self.audio = 0
		self.poll_interval = 1000
		self.poll_enabled = True
		self.clearData()
		self.initTimer = eTimer()
		self.initTimer.callback.append(self.initBitrateCalc)

	def getCaidInEcmFile(self):
		caidvalue = return_line = ''
		zero_line = '0000'
		if os.path.isfile('/tmp/ecm.info'):
			try:
				filedata = open('/tmp/ecm.info')
			except:
				filedata = False
			if filedata:
				for line in filedata.readlines():
					if "caid:" in line:
						caidvalue = line.strip("\n").split()[-1][2:]
						if len(caidvalue) < 4:
							caidvalue = zero_line[len(caidvalue):] + caidvalue
					elif "CaID" in line or "CAID" in line:
						caidvalue = line.split(',')[0].split()[-1][2:]
				return_line = caidvalue.upper()
				filedata.close()
		return return_line

	def getCatEcmFile(self):
		ecmfiledata = ''
		if os.path.isfile('/tmp/ecm.info') and config.plugins.QuickEcm.enabled.value:
			try:
				filedata = open('/tmp/ecm.info')
			except:
				filedata = False
			if filedata:
				for line in filedata.readlines():
					if "caid:" in line or "provider:" in line or "provid:" in line or "pid:" in line or "hops:" in line  or "system:" in line or "address:" in line or "using:" in line or "ecm time:" in line:
						line = line.replace(' ',"").replace(":",": ")
					if "caid:" in line or "pid:" in line or "reader:" in line or "from:" in line or "hops:" in line  or "system:" in line or "Service:" in line or "CAID:" in line or "Provider:" in line:
						line = line.strip('\n') + "  "
					if "Signature" in line:
						line = ""
					if "=" in line:
						line = line.lstrip('=').replace('======', "").replace('\n', "").rstrip() + ', '
					if "ecmtime:" in line:
						line = line.replace("ecmtime:", "ecm time:")
					if "response time:" in line:
						line = line.replace("response time:", "ecm time:").replace("decoded by", "by")
					if not line.startswith('\n'):
						if 'pkey:' in line:
							line = '\n' + line + '\n'
					ecmfiledata += line
				filedata.close()
				return ecmfiledata
			else:
				return ''
		else:
			return ''

	def status(self):
		status = ''
		if os.path.isfile("/usr/lib/opkg/status"):
			status = "/usr/lib/opkg/status"
		elif os.path.isfile("/usr/lib/ipkg/status"):
			status = "/usr/lib/ipkg/status"
		elif os.path.isfile("/var/lib/opkg/status"):
			status = "/var/lib/opkg/status"
		elif os.path.isfile("/var/opkg/status"):
			status = "/var/opkg/status"
		return status

	def boxinfo(self):
		box = software = enigma = driver = ''
		package = 0
		if config.plugins.QuickEcm.enabled.value:
			if os.path.isfile(self.status()):
				for line in open(self.status()):
					if "-dvb-modules" in line and "Package:" in line:
						package = 1
					if "Version:" in line and package == 1:
						package = 0
						driver = self.maincolor + '(%s)' % line.split()[1] + self.basecolor
						break
			if os.path.isfile("/proc/version"):
				enigma = open("/proc/version").read().split()[2]
			if os.path.isfile("/etc/model"):
				box = open("/etc/model").read().strip().upper()
			if os.path.isfile("/etc/issue"):
				for line in open("/etc/issue"):
					software += line.capitalize().replace('\n', '').replace('\l', '').replace('\\', '').strip()[:-1]
				software = self.maincolor + ' (%s)' % software.strip() + self.basecolor
			return '%s%s  Kernel: %s %s' % (box, software, enigma, driver)
		else:
			return ''

	def convert_color(self, color_in):
		hex_color = {'0':'0', '1':'1', '2':'2', '3':'3', '4':'4', '5':'5', '6':'6', '7':'7', '8':'8', '9':'9',\
			'a':':', 'b':';', 'c':'<', 'd':'=', 'e':'>', 'f':'?', 'A':':', 'B':';', 'C':'<', 'D':'=', 'E':'>', 'F':'?'}
		color_out = '\c'
		for i in range(1, len(color_in)):
			color_out += hex_color.get(color_in[i])
		return color_out

	def getServiceInfoString(self, info, what):
		value = info.getInfo(what)
		if value == -3:
			line_caids = info.getInfoObject(what)
			if line_caids and len(line_caids) > 0:
				return_value = ''
				for caid in line_caids:
					return_value += '%.4X ' % caid
				return return_value[:-1]
			else:
				return ''
		return '%d' % value

	def getEmuName(self):
		if config.plugins.QuickEcm.enabled.value:
			nameemu = nameser = []
			camdlist = serlist = None
			#Alternative SoftCam Manager 
			if os.path.isfile("/usr/lib/enigma2/python/Plugins/Extensions/AlternativeSoftCamManager/plugin.py"): 
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
			else:
				return 'N/A'
		else:
			return 'N/A'

	def resolutioninfo(self, info):
		if config.plugins.QuickEcm.enabled.value:
			xres = info.getInfo(iServiceInformation.sVideoWidth)
			if xres == -1:
				return ''
			yres = info.getInfo(iServiceInformation.sVideoHeight)
			mode = ('i', 'p', ' ')[info.getInfo(iServiceInformation.sProgressive)]
			fps  = str((info.getInfo(iServiceInformation.sFrameRate) + 500) / 1000)
			if '0' is fps:
				fps = ''
			else:
				fps = '(%s)' % fps
			return str(xres) + 'x' + str(yres) + mode + fps
		else:
			return ''

	def clearData(self):
		self.videoBitrate = None
		self.audioBitrate = None
		self.video = self.audio = 0

	def initBitrateCalc(self):
		service = self.source.service
		vpid = apid = dvbnamespace = tsid = onid = -1
		if config.plugins.QuickEcm.enabled.value:
			if binaryfound:
				if service:
					serviceInfo = service.info()
					vpid = serviceInfo.getInfo(iServiceInformation.sVideoPID)
					apid = serviceInfo.getInfo(iServiceInformation.sAudioPID)
					tsid = serviceInfo.getInfo(iServiceInformation.sTSID)
					onid = serviceInfo.getInfo(iServiceInformation.sONID)
					dvbnamespace = serviceInfo.getInfo(iServiceInformation.sNamespace)
				if vpid:
					self.videoBitrate = eBitrateCalculator(vpid, dvbnamespace, tsid, onid, 1000, 1024*1024) 
					self.videoBitrate.callback.append(self.getVideoBitrateData)
				if apid:
					self.audioBitrate = eBitrateCalculator(apid, dvbnamespace, tsid, onid, 1000, 64*1024)
					self.audioBitrate.callback.append(self.getAudioBitrateData)
		else:
			self.clearData()

	def getVideoBitrateData(self, value, status):
		if status:
			self.video = value
		else:
			self.videoBitrate = None
		Converter.changed(self, (self.CHANGED_POLL,))

	def getAudioBitrateData(self, value, status):
		if status:
			self.audio = value
		else:
			self.audioBitrate = None
		Converter.changed(self, (self.CHANGED_POLL,))
		
	@cached
	def getText(self):
		array_caid = []
		bar_caids = ecm_caid = ''
		service = self.source.service
		info = service and service.info()
		if not info:
			return ''
		if self.type is self.caidbar:
			caid_default = ['01XX', '05XX', '06XX', '09XX', '0BXX', '0DXX', '17XX', '18XX', '26XX', '27XX', '4AXX', '56XX']
			caidinfo = self.getServiceInfoString(info, iServiceInformation.sCAIDs)
			if caidinfo:
				ecm_caid = self.getCaidInEcmFile()
				for caid in caidinfo.split():
					array_caid.append(caid.strip())
				caidinfo = ' '.join(str(x) for x in set(array_caid))
				bar_caids = self.maincolor + ''
				array_caid = caidinfo.split()
				for i in range(len(caid_default)):
					for j in range(len(caidinfo.split())):
						if caid_default[i][:2] == array_caid[j][:2]:
							if caid_default[i][:2] == ecm_caid[:2]:
								caid_default[i] = self.ecmcolor + ecm_caid + self.maincolor
							else:
								caid_default[i] = self.emmcolor + array_caid[j] + self.maincolor
					bar_caids += caid_default[i] + '  '
			else:
				for i in range(len(caid_default)):
					bar_caids += self.maincolor + caid_default[i] + '  '
			return bar_caids.strip()
		elif self.type is self.txtcaid:
			TxtCaids = {"26" : "BiSS", "01" : "Seca Mediaguard", "06" : "Irdeto", "17" : "BetaCrypt", "05" : "Viaccess", "18" : "Nagravision",\
				"09" : "NDS-Videoguard", "0B" : "Conax", "0D" : "Cryptoworks", "4A" : "DRE-Crypt", "27" : "ExSet", "0E" : "PowerVu", "22" : "Codicrypt",\
				"07" : "DigiCipher", "56" : "Verimatrix", "7B" : "DRE-Crypt", "A1" : "Rosscrypt"} 
			iscrypt = self.getServiceInfoString(info, iServiceInformation.sCAIDs)
			if not iscrypt:
				return _('Free-to-air')
			elif iscrypt and not os.path.isfile('/tmp/ecm.info'):
				return _('No parse cannot emu')
			elif iscrypt and os.path.isfile('/tmp/ecm.info'):
				try:
					if not os.stat('/tmp/ecm.info').st_size:
						return _('No parse cannot emu')
				except:
					return _('No parse cannot emu')
				else:
					return TxtCaids.get(self.getCaidInEcmFile()[:2], ' ')
		elif self.type is self.boxdata:
			return self.boxinfo()
		elif self.type is self.ecmfile:
			iscrypt = self.getServiceInfoString(info, iServiceInformation.sCAIDs)
			if not iscrypt:
				return ''
			elif iscrypt and not os.path.isfile('/tmp/ecm.info'):
				return ''
			elif iscrypt and os.path.isfile('/tmp/ecm.info'):
				try:
					if not os.stat('/tmp/ecm.info').st_size:
						return ''
				except:
					return ''
				else:
					return self.getCatEcmFile()
		elif self.type is self.emuname:
			return self.getEmuName()
		elif self.type is self.pids:
			bar_pids = ''
			vpid = apid = prcpid = tsid = onid = sid = -1
			sid = info.getInfo(iServiceInformation.sSID)
			vpid = info.getInfo(iServiceInformation.sVideoPID)
			apid = info.getInfo(iServiceInformation.sAudioPID)
			tsid = info.getInfo(iServiceInformation.sTSID)
			prcpid = info.getInfo(iServiceInformation.sPCRPID)
			onid = info.getInfo(iServiceInformation.sONID)
			bar_pids = '%sSID: %s%0.4X%s  VPID: %s%0.4X%s  APID: %s%0.4X%s  PRCPID: %s%0.4X%s  TSID: %s%0.4X%s  ONID: %s%0.4X%s' %\
				(self.maincolor, self.basecolor, sid, self.maincolor, self.basecolor, vpid, self.maincolor,\
				self.basecolor, apid, self.maincolor, self.basecolor, prcpid, self.maincolor,\
				self.basecolor, tsid, self.maincolor, self.basecolor, onid, self.maincolor)
			return bar_pids.replace('-0001', 'N/A')
		elif self.type is self.bitrate:
			if config.plugins.QuickEcm.enabled.value:
				self.initTimer.start(1000, True)
			else:
				self.clearData()
			bar_bitrate = videocodec = audiocodec = ''
			audio = service.audioTracks()
			if audio:
				if audio.getCurrentTrack() > -1:
					if self.audio is not 0:
						audiocodec = '  AUDIO %s: %s%s%s Kbit/s' % (str(audio.getTrackInfo(audio.getCurrentTrack()).getDescription()).replace(",","").upper(), self.basecolor, self.audio, self.maincolor)
					else:
						audiocodec = ''
			if self.video is not 0:
				videocodec = '  VIDEO %s: %s%s%s Kbit/s' % (("MPEG2", "MPEG4", "MPEG1", "MPEG4-II", "VC1", "VC1-SM", "")[info.getInfo(iServiceInformation.sVideoType)], self.basecolor, self.video, self.maincolor)
			else:
				videocodec = ''
			bar_bitrate = self.resolutioninfo(info) + videocodec + audiocodec
			return bar_bitrate

	text = property(getText)

	def changed(self, what):
		if what[0] is self.CHANGED_SPECIFIC:
			if what[1] is iPlayableService.evStart or what[1] is iPlayableService.evUpdatedInfo:
				self.initTimer.start(1000, True)
			elif what[1] is iPlayableService.evEnd:
				self.clearData()
			Converter.changed(self, what)
		elif what[0] is self.CHANGED_POLL:
			self.downstream_elements.changed(what)
