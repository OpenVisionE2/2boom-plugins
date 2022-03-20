#!/usr/bin/python
# -*- coding: utf-8 -*-
#QuickEcmInfo for Hotkey
#Copyright (c) 2boom 2014-16
# v.0.2-r7
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
from Components.Language import language
from Components.Sources.StaticText import StaticText
from Components.Sources.CurrentService import CurrentService
from Components.config import config
from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import resolveFilename, SCOPE_LANGUAGE, SCOPE_PLUGINS, SCOPE_LIBDIR
from enigma import eTimer, iServiceInformation
from os import environ
import gettext
import os
import sys

lang = language.getLanguage()
environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("qeifh", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/QEIfH/locale/"))


def _(txt):
	t = gettext.dgettext("qeifh", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t


if os.path.isfile(resolveFilename(SCOPE_LIBDIR, 'bitratecalc.so')):
	from bitratecalc import eBitrateCalculator
	binary_file = True
else:
	binary_file = False

SKIN_HD = """
<screen name="QEIfH" position="265,140" size="750,425" title="2boom's QuickEcmInfo for Hotkey" zPosition="1">
  <eLabel position="20,58" size="710,2" backgroundColor="grey" zPosition="4" />
  <eLabel position="20,91" size="710,2" backgroundColor="grey" zPosition="4" />
  <eLabel position="20,319" size="710,2" backgroundColor="grey" zPosition="4" />
  <eLabel position="20,353" size="710,2" backgroundColor="grey" zPosition="4" />
  <eLabel position="50,388" size="650,2" backgroundColor="grey" zPosition="4" />
  <widget source="boxinfo" render="Label" position="10,5" size="730,25" font="Regular; 23" zPosition="2" foregroundColor="foreground" transparent="1" valign="top" noWrap="1" halign="center" />
  <widget source="hardinfo" render="Label" position="10,30" size="730,25" font="Regular; 23" zPosition="2" foregroundColor="grey" transparent="1" valign="top" noWrap="1" halign="center" />
  <widget name="ecmfile" render="Label" position="11,98" size="730,215" font="Regular; 23" zPosition="2" foregroundColor="foreground" transparent="1" valign="top" noWrap="1" halign="center" />
  <widget source="emuname" render="Label" position="20,62" size="470,25" font="Regular; 22" zPosition="2" foregroundColor="unfec000" transparent="1" valign="top" halign="left" />
  <widget source="txtcaid" render="Label" position="430,62" size="300,25" font="Regular; 22" zPosition="2" foregroundColor="grey" transparent="1" valign="top" halign="right" />
  <widget source="caids" render="Label" position="6,325" size="740,25" font="Regular; 22" zPosition="2" foregroundColor="grey" transparent="1" valign="top" halign="center" />
  <widget source="pids" render="Label" position="5,359" size="740,25" font="Regular; 22" zPosition="2" foregroundColor="foreground" transparent="1" valign="top" halign="center" />
  <widget source="res" render="Label" position="14,395" size="180,25" font="Regular; 22" zPosition="2" foregroundColor="grey" transparent="1" valign="top" halign="right" />
<widget source="abit" render="Label" position="485,395" size="230,25" font="Regular; 22" zPosition="2" foregroundColor="grey" transparent="1" valign="top" halign="left" />
<widget source="vbit" render="Label" position="180,395" size="320,25" font="Regular; 22" zPosition="2" foregroundColor="grey" transparent="1" valign="top" halign="center" />
</screen>"""


class QEIfH(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.session = session
		self.skin = SKIN_HD
		self.setTitle(_("2boom's QuickEcmInfo for Hotkey"))
		self.videoBitrate = self.audioBitrate = None
		self.resolution = self.audiocodec = self.videocodec = ''
		self.active_caid = 'FFFF'
		self.maincolor = self.convert_color('#00aaaaaa')
		self.emmcolor = self.convert_color('#0003a902')
		self.ecmcolor = self.convert_color('#00f0bf4f')
		self["ecmfile"] = ScrollLabel("")
		self["boxinfo"] = StaticText()
		self["hardinfo"] = StaticText()
		self["emuname"] = StaticText()
		self["txtcaid"] = StaticText()
		self["caids"] = StaticText()
		self["pids"] = StaticText()
		#self["bitrate"] = StaticText()
		self["res"] = StaticText()
		self["vbit"] = StaticText()
		self["abit"] = StaticText()
		self.TxtCaids = {
			"26": "BiSS", "01": "Seca Mediaguard", "06": "Irdeto", "17": "BetaCrypt", "05": "Viacces", "18": "Nagravision", "09": "NDS-Videoguard",
			"0B": "Conax", "0D": "Cryptoworks", "4A": "DRE-Crypt", "27": "ExSet", "0E": "PowerVu", "22": "Codicrypt", "07": "DigiCipher",
			"56": "Verimatrix", "7B": "DRE-Crypt", "A1": "Rosscrypt"}
		self["ecmfile"].setText(self.ecm_view())
		self["actions"] = ActionMap(["WizardActions"],
		{
			"back": self.close,
			"ok": self.close,
			"right": self.close,
			"left": self.close,
			"down": self.close,
			"up": self.close,
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
			self.resolution = self.resolutioninfo(serviceInfo)
			audio = service.audioTracks()
			if audio:
				if audio.getCurrentTrack() > -1:
					self.audiocodec = str(audio.getTrackInfo(audio.getCurrentTrack()).getDescription()).replace(",", "")
			self.videocodec = ("MPEG2", "MPEG4", "MPEG1", "MPEG4-II", "VC1", "VC1-SM", "")[info.getInfo(iServiceInformation.sVideoType)]
		if apid and binary_file:
			self.audioBitrate = eBitrateCalculator(apid, dvbnamespace, tsid, onid, 1000, 64 * 1024)
			self.audioBitrate.callback.append(self.getAudioBitrateData)
		if vpid and binary_file:
			self.videoBitrate = eBitrateCalculator(vpid, dvbnamespace, tsid, onid, 1000, 1024 * 1024)
			self.videoBitrate.callback.append(self.getVideoBitrateData)
		self.Timer = eTimer()
		self.Timer.callback.append(self.ecmfileinfo)
		self.Timer.start(1000 * 2, False)
		self.onShow.append(self.staticinfo)

	def getVideoBitrateData(self, value, status):
		if status:
			self["vbit"].text = 'VIDEO %s: %d Kb/s' % (self.videocodec, value)
			self["res"].text = self.resolution
		else:
			self.videoBitrate = None

	def getAudioBitrateData(self, value, status):
		if status:
			self["abit"].text = 'AUDIO %s: %s Kb/s' % (self.audiocodec, value)
		else:
			self.audioBitrate = None

	def ecmfileinfo(self):
		self["ecmfile"].setText(self.ecm_view())

	def staticinfo(self):
		self["boxinfo"].text = self.boxinfo()
		self["emuname"].text = self.emuname()
		self["hardinfo"].text = self.hardinfo()
		self["pids"].text = self.pidsline()
		self["caids"].text = self.caidline()

	def convert_color(self, color_in):
		hex_color = {'0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6', '7': '7', '8': '8', '9': '9',
			'a': ':', 'b': ';', 'c': '<', 'd': '=', 'e': '>', 'f': '?', 'A': ':', 'B': ';', 'C': '<', 'D': '=', 'E': '>', 'F': '?'}
		color_out = '\c'
		for i in range(1, len(color_in)):
			color_out += hex_color.get(color_in[i])
		return color_out

	def caidline(self):
		array_caid = []
		bar_caids = ecm_caid = ''
		service = self.session.nav.getCurrentService()
		if service:
			info = service and service.info()
			caid_default = ['01XX', '05XX', '06XX', '09XX', '0BXX', '0DXX', '17XX', '18XX', '26XX', '27XX', '4AXX', '56XX']
			caidinfo = self.getServiceInfoString(info, iServiceInformation.sCAIDs)
			if caidinfo:
				ecm_caid = self.active_caid
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
		return 'SID: %0.4X  VPID: %0.4X  APID: %0.4X  TSID: %0.4X ONID: %0.4X' % (sid, vpid, apid, tsid, onid)

	def resolutioninfo(self, serviceInfo):
		xres = serviceInfo.getInfo(iServiceInformation.sVideoWidth)
		if xres == -1:
			return ''
		yres = serviceInfo.getInfo(iServiceInformation.sVideoHeight)
		mode = ('i', 'p', ' ')[serviceInfo.getInfo(iServiceInformation.sProgressive)]
		fps = str((serviceInfo.getInfo(iServiceInformation.sFrameRate) + 500) / 1000)
		return str(xres) + 'x' + str(yres) + mode + '(%s)' % fps

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

	def ecm_view(self):
		service = self.session.nav.getCurrentService()
		if service is not None:
			info = service and service.info()
			list = caidvalue = ''
			port_flag = 0
			zero_line = '0000'
			self["txtcaid"].text = ''
			iscrypt = info.getInfo(iServiceInformation.sIsCrypted)
			if not iscrypt or iscrypt == -1:
				self["txtcaid"].text = _('Free-to-air')
			elif iscrypt and not os.path.isfile('/tmp/ecm.info'):
				self["txtcaid"].text = _('No parse cannot emu')
			elif iscrypt and os.path.isfile('/tmp/ecm.info'):
				try:
					if not os.stat('/tmp/ecm.info').st_size:
						self["txtcaid"].text = _('No parse cannot emu')
				except:
					self["txtcaid"].text = _('No parse cannot emu')
			if os.path.isfile("/tmp/ecm.info"):
				try:
					ecmfiles = open('/tmp/ecm.info').readlines()
				except:
					pass
				if ecmfiles:
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
						if "caid:" in line:
							caidvalue = line.strip("\n").split()[-1][2:]
							if len(caidvalue) < 4:
								caidvalue = zero_line[len(caidvalue):] + caidvalue
						elif "CaID" in line or "CAID" in line:
							caidvalue = line.split(',')[0].split()[-1][2:]
					self["txtcaid"].text = self.TxtCaids.get(caidvalue[:2].upper(), ' ')
					self.active_caid = caidvalue.upper()
					return list
		return ''

	def emuname(self):
		serlist = camdlist = None
		nameemu = nameser = []
		ecminfo = ''
		# Alternative SoftCam Manager
		if os.path.isfile(resolveFilename(SCOPE_PLUGINS, "Extensions/AlternativeSoftCamManager/plugin.pyo")):
			if config.plugins.AltSoftcam.actcam.value != "none":
				return config.plugins.AltSoftcam.actcam.value
			else:
				return None
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
			emu = ""
			ecminfo = "%s %s" % (cardserver.split('\n')[0], emu.split('\n')[0])
		return ecminfo

	def status(self):
		status = ''
		if os.path.isfile(resolveFilename(SCOPE_LIBDIR, "opkg/status")):
			status = resolveFilename(SCOPE_LIBDIR, "opkg/status")
		elif os.path.isfile(resolveFilename(SCOPE_LIBDIR, "ipkg/status")):
			status = resolveFilename(SCOPE_LIBDIR, "ipkg/status")
		elif os.path.isfile("/var/lib/opkg/status"):
			status = "/var/lib/opkg/status"
		elif os.path.isfile("/var/opkg/status"):
			status = "/var/opkg/status"
		return status

	def boxinfo(self):
		box = software = enigma = driver = tmp_line = ''
		package = 0
		try:
			if os.path.isfile(self.status()):
				for line in open(self.status()):
					if "-dvb-modules" in line and "Package:" in line:
						package = 1
					elif "kernel-module-player2" in line and "Package:" in line:
						package = 1
					if "Version:" in line and package == 1:
						package = 0
						if line.count('.') == 3:
							tmp_line = line.split()[-1].split('+')[-1].split('-')[0]
						else:
							tmp_line = line.split()[-1].split('-')[-1].split('.')[0]
						driver = '%s.%s.%s' % (tmp_line[6:], tmp_line[4:-2], tmp_line[:4])
						break
			if os.path.isfile("/proc/version"):
				enigma = open("/proc/version").read().split()[2]
			if os.path.isfile("/etc/model"):
				box = open("/etc/model").read().strip().upper()
			if os.path.isfile("/etc/issue"):
				if os.path.isfile("/etc/issue"):
					for line in open("/etc/issue"):
						if not line.startswith('Welcom') and '\l' in line:
							software += line.capitalize().replace('\n', '').replace('\l', '').replace('\\', '').strip()[:-1]
				else:
					software = _("undefined")
				software = ' (%s)' % software.strip()
			return _('%s%s  Kernel: %s (%s)') % (box, software, enigma, driver)
		except:
			pass
		return ''

	def hardinfo(self):
		if os.path.isfile("/proc/cpuinfo"):
			cpu_count = 0
			processor = cpu_speed = cpu_family = cpu_variant = temp = ''
			core = _("core")
			cores = _("cores")
			for line in open('/proc/cpuinfo'):
				if "system type" in line:
					processor = line.split(':')[-1].split()[0].strip().strip('\n')
				elif "cpu MHz" in line:
					cpu_speed = line.split(':')[-1].strip().strip('\n')
				elif "cpu type" in line:
					processor = line.split(':')[-1].strip().strip('\n')
				elif "model name" in line:
					processor = line.split(':')[-1].strip().strip('\n').replace('Processor ', '')
				elif "cpu family" in line:
					cpu_family = line.split(':')[-1].strip().strip('\n')
				elif "cpu variant" in line:
					cpu_variant = line.split(':')[-1].strip().strip('\n')
				elif line.startswith('processor'):
					cpu_count += 1
			if not cpu_speed:
				try:
					cpu_speed = int(open("/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq").read()) / 1000
				except:
					cpu_speed = '-'
			if os.path.isfile("/proc/stb/sensors/temp0/value") and os.path.isfile("/proc/stb/sensors/temp0/unit"):
				temp = "%s%s%s" % (open("/proc/stb/sensors/temp0/value").read().strip('\n'), unichr(176).encode("latin-1"), open("/proc/stb/sensors/temp0/unit").read().strip('\n'))
			elif os.path.isfile("/proc/stb/fp/temp_sensor_avs"):
				temp = "%s%sC" % (open("/proc/stb/fp/temp_sensor_avs").read().strip('\n'), unichr(176).encode("latin-1"))
			if cpu_variant == '':
				return _("%s, %s Mhz (%d %s) %s") % (processor, cpu_speed, cpu_count, cpu_count > 1 and cores or core, temp)
			else:
				return "%s(%s), %s %s" % (processor, cpu_family, cpu_variant, temp)
		else:
			return _("undefined")


def main(session, **kwargs):
	session.open(QEIfH)


def Plugins(**kwargs):
	list = [PluginDescriptor(name=_("2boom's QuickEcmInfo for Hotkey"), description=_("quickecminfo for hotkey extentions"), where=[PluginDescriptor.WHERE_PLUGINMENU], icon="qeifh.png", fnc=main)]
	return list
