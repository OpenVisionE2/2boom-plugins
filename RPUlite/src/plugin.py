# -*- coding: utf-8 -*-
# Rostelecom lite proxy updater
# Copyright (c) 2boom 2014
# v.1.1-r0
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

import os, sys, os.path
import re
import gettext
from enigma import eTimer, eEnv
from Plugins.Plugin import PluginDescriptor
from Tools.Directories import resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from Components.config import getConfigListEntry, ConfigText, ConfigClock, ConfigYesNo, ConfigLocations, ConfigSubsection, ConfigSelection, config, configfile
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.ScrollLabel import ScrollLabel
from Components.ActionMap import ActionMap
from Components.Language import language
from Components.Sources.List import List
from Components.Label import Label
from Components.Console import Console as iConsole
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from GlobalActions import globalActionMap
from StringIO import StringIO
import ref_base
import pycurl

lang = language.getLanguage()
os.environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("RPUlite", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/RPUlite/locale/"))

def _(txt):
	t = gettext.dgettext("RPUlite", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t

config.plugins.rpulite = ConfigSubsection()
config.plugins.rpulite.menuext = ConfigYesNo(default = True)
config.plugins.rpulite.ip = ConfigText(default='000.000.000.000', visible_width = 150, fixed_size = False)
config.plugins.rpulite.bname = ConfigText(default='Rostelecom', visible_width = 250, fixed_size = False)
config.plugins.rpulite.rpassw = ConfigText(default='', visible_width = 150, fixed_size = False)
config.plugins.rpulite.servicetype = ConfigSelection(default = '1', choices = [
		('1', _("TV")),
		('2', _("LiveStreamer")),
		('4097', _("GStreamer")),
		])
config.plugins.rpulite.source = ConfigSelection(default = '0', choices = [
		('0', _("source 1")),
		('1', _("source 2")),
		])
config.plugins.rpulite.ref = ConfigYesNo(default = True)
config.plugins.rpulite.startup = ConfigYesNo(default = False)
config.plugins.rpulite.timeup = ConfigSelection(default = '0', choices = [
		('0', _("off")),
		('1', _("1 hour")),
		('2', _("2 hours")),
		('3', _("3 hours")),
		])

def remove_line(filename, what):
	if os.path.isfile(filename):
		file_read = open(filename).readlines()
		file_write = open(filename, 'w')
		for line in file_read:
			if what not in line:
				file_write.write(line)
		file_write.close()

def add_line(filename, what):
	if os.path.isfile(filename):
		with open(filename, 'a') as file_out:
			file_out.write(what)
			file_out.close()

def cronpath():
	path = "/etc/cron/crontabs/root"
	if os.path.isfile("/etc/cron/crontabs"):
		return "/etc/cron/crontabs/root"
	elif os.path.isfile("/etc/bhcron"):
		return "/etc/bhcron/root"
	elif os.path.isfile("/etc/crontabs"):
		return "/etc/crontabs/root"
	elif os.path.isfile("/var/spool/cron/crontabs"):
		return "/var/spool/cron/crontabs/root"
	return path

class rpulite(Screen, ConfigListScreen):
	skin = """
<screen name="rpulite" position="265,160" size="750,360" title="2boom's Rostelecom lite proxy updater">
  <widget position="15,10" size="720,225" name="config" scrollbarMode="showOnDemand" />
  <ePixmap position="635,260" zPosition="2" size="100,60" pixmap="~/images/ROSTELECOM.png" alphatest="blend" />
  <eLabel position="30,240" size="690,2" backgroundColor="grey" zPosition="5" />
  <ePixmap position="10,355" zPosition="1" size="165,2" pixmap="~/images/red.png" alphatest="blend" />
  <widget source="key_red" render="Label" position="10,325" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" transparent="1" />
  <ePixmap position="175,355" zPosition="1" size="165,2" pixmap="~/images/green.png" alphatest="blend" />
  <widget source="key_green" render="Label" position="175,325" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" transparent="1" />
  <ePixmap position="340,355" zPosition="1" size="230,2" pixmap="~/images/yellow.png" alphatest="blend" />
  <widget source="key_yellow" render="Label" position="340,325" zPosition="2" size="230,30" font="Regular;20" halign="center" valign="center" transparent="1" />
  <ePixmap position="570,355" zPosition="1" size="165,2" pixmap="~/images/blue.png" alphatest="blend" />
  <widget source="key_blue" render="Label" position="570,325" zPosition="2" size="165,30" font="Regular;20" halign="center" valign="center" transparent="1" />
  <widget name="text" position="20,255" size="720,48" font="Regular;22" halign="left" />
</screen>"""
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/RPUlite")
		self.iConsole = iConsole()
		self.keyext = config.plugins.rpulite.menuext.value
		self.newproxy = ''
		self.path = cronpath()
		self.update_system()
		self.list = []
		self.list.append(getConfigListEntry(_("Select source"),config.plugins.rpulite.source))
		self.list.append(getConfigListEntry(_("Input new proxy ip"), config.plugins.rpulite.ip))
		self.list.append(getConfigListEntry(_("Select service type in default bouquet"), config.plugins.rpulite.servicetype))
		self.list.append(getConfigListEntry(_("Input Name of default bouquet"), config.plugins.rpulite.bname))
		self.list.append(getConfigListEntry(_("Input password (if needed)"), config.plugins.rpulite.rpassw))
		self.list.append(getConfigListEntry(_("Reference in default bouquet"), config.plugins.rpulite.ref))
		self.list.append(getConfigListEntry(_("Set time to update ip (cron needed)"), config.plugins.rpulite.timeup))
		if os.path.isdir('/etc/rcS.d') or os.path.isdir('/etc/rc.d/rcS.d'): #/etc/rc.d/rcS.d/
			self.list.append(getConfigListEntry(_("Update ip on startup"), config.plugins.rpulite.startup))
		self.list.append(getConfigListEntry(_("Proxy updater in ExtensionMenu"), config.plugins.rpulite.menuext))
		ConfigListScreen.__init__(self, self.list)
		#ConfigListScreen.__init__(self, self.list, session=session)
		self["text"] = ScrollLabel("")
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("IP & Ch.List Update"))
		self["key_blue"] = StaticText(_("IP Update"))
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.cancel,
			"cancel": self.cancel,
			"green": self.save,
			"yellow": self.update_all,
			"blue": self.update_ip,
			"ok": self.ok_key,
		}, -2)
		self.onShow.append(self.listuserbouquet)

	def listuserbouquet(self):
		self.setTitle(_("2boom's Rostelecom lite proxy updater"))

	def ok_key(self):
		try:
			buffer = StringIO()
			c = pycurl.Curl()
			c.setopt(c.URL, '%s:1234/status' % config.plugins.rpulite.ip.value)
			c.setopt(c.TIMEOUT, 1)
			c.setopt(c.WRITEDATA, buffer)
			c.perform()
			c.close()
			body = buffer.getvalue()
			if 'udpxy' in body:
				self["text"].setText(_('Current proxy: %s  Status: OK user(s): %s') % (config.plugins.rpulite.ip.value, body.count('233.7.70.')))
			else:
				self["text"].setText(_('Current proxy: %s  Not working') % config.plugins.rpulite.ip.value)
		except:
			self["text"].setText(_('Current proxy: %s  Not working') % config.plugins.rpulite.ip.value)

	def save(self):
		for i in self["config"].list:
			i[1].save()
		configfile.save()
		if config.plugins.rpulite.startup.value or not config.plugins.rpulite.timeup.value is '0':
			if not os.path.isfile(resolveFilename(SCOPE_PLUGINS, 'Extensions/RPUlite/get_ip_rtc.sh')):
				self.create_script()
		
		if config.plugins.rpulite.startup.value: #/etc/rc.d/rcS.d/
			if not os.path.isfile('/etc/rcS.d/get_ip_rtc'):
				if os.path.isfile(resolveFilename(SCOPE_PLUGINS, 'Extensions/RPUlite/get_ip_rtc.sh')) and os.path.isdir('/etc/rcS.d'):
					os.link(resolveFilename(SCOPE_PLUGINS, 'Extensions/RPUlite/get_ip_rtc.sh'), '/etc/rcS.d/get_ip_rtc')
			if not os.path.isfile('/etc/rc.d/rcS.d/S98get_ip_rtc'):
				if os.path.isfile(resolveFilename(SCOPE_PLUGINS, 'Extensions/RPUlite/get_ip_rtc.sh')) and os.path.isdir('/etc/rc.d/rcS.d/'):
					os.link(resolveFilename(SCOPE_PLUGINS, 'Extensions/RPUlite/get_ip_rtc.sh'), '/etc/rc.d/rcS.d/S98get_ip_rtc')
		else:
			if os.path.isfile('/etc/rcS.d/get_ip_rtc'):
				os.unlink('/etc/rcS.d/get_ip_rtc')
			elif os.path.isfile('/etc/rc.d/rcS.d/S98get_ip_rtc'):
				os.unlink('/etc/rc.d/rcS.d/S98get_ip_rtc')
		if not config.plugins.rpulite.timeup.value is '0':
			if os.path.isfile(self.path):
				remove_line(self.path, 'get_ip_rtc')
				add_line(self.path, '15 */%s * * * %s\n' % (config.plugins.rpulite.timeup.value, resolveFilename(SCOPE_PLUGINS, 'Extensions/RPUlite/get_ip_rtc.sh')))
				self.cron_update()
		else:
			if os.path.isfile(self.path):
				remove_line(self.path, 'get_ip_rtc')
				self.cron_update()
		self.mbox = self.session.open(MessageBox,(_("configuration is saved")), MessageBox.TYPE_INFO, timeout = 6 )

	def cron_update(self):
		if os.path.isfile(self.path):
			with open('%scron.update' % self.path[:-4], 'w') as cron_update:
				cron_update.write('root')
				cron_update.close()
			
	def update_system(self):
		if os.path.isfile('/etc/hosts'):
			for line in open('/etc/hosts'):
				if 'rostelecom' in line:
					config.plugins.rpulite.ip.value = line.split('\t')[0]

	def create_script(self):
		with open(resolveFilename(SCOPE_PLUGINS, 'Extensions/RPUlite/get_ip_rtc.sh'), 'w') as out_script:
			out_script.write("#!/bin/sh\n")
			out_script.write("# (c) 2boom 2014\n")
			out_script.write("SERVER_1='http://iptv.lamp.ufa-it.ru/generate_m3u.php?num_list=001&shift=2&type=m3u'\n")
			out_script.write("SERVER_2='http://plstonline.org/iptv/IPTV_29_V.m3u?'\n")
			out_script.write("M3U_FILE='/tmp/rostelecom.m3u'\n")
			out_script.write("HOST_FILE='/etc/hosts'\n")
			out_script.write("rm -f $M3U_FILE\n")
			out_script.write("wget -q $SERVER_1 -O $M3U_FILE\n")
			out_script.write("if [ -f $M3U_FILE ]; then\n")
			out_script.write("\techo \"The '$SERVER_1' loaded...\"\n")
			out_script.write("else\n")
			out_script.write("\twget -q $SERVER_2 -O $M3U_FILE\n")
			out_script.write("\tif [ -f $M3U_FILE ]; then\n")
			out_script.write("\t\techo \"The '$SERVER_2' loaded...\"\n")
			out_script.write("\telse\n")
			out_script.write("\t\techo \"The '$SERVER_2' not respond...\"\n")
			out_script.write("\tfi\n")
			out_script.write("\techo \"The '$SERVER_1' not respond...\"\n")
			out_script.write("fi\n")
			out_script.write("if [ -f $M3U_FILE ]; then\n")
			out_script.write("\tsed -i /EXTM3U/d $M3U_FILE\n")
			out_script.write("\tsed -i /EXTINF/d $M3U_FILE\n")
			out_script.write("\tsed -i '/^http:/q' $M3U_FILE\n")
			out_script.write("\tsed -i 's/^[http://]*//' $M3U_FILE\n")
			out_script.write("\tsed -i '1,$ s/:.*//g' $M3U_FILE\n")
			out_script.write("\tsed -i /rostelecom/d $HOST_FILE\n")
			out_script.write("\twhile read LINE; do\n")
			out_script.write("\t\techo -e \"$LINE\trostelecom\t\trostelecom\" >>$HOST_FILE\n")
			out_script.write("\tdone < $M3U_FILE\n")
			out_script.write("else\n")
			out_script.write("\tsed -i /rostelecom/d $HOST_FILE\n")
			out_script.write("\techo \"The '$M3U_FILE' does not loaded\"\n")
			out_script.write("fi\n")
			out_script.close()
		if os.path.isfile(resolveFilename(SCOPE_PLUGINS, 'Extensions/RPUlite/get_ip_rtc.sh')):
			os.chmod(resolveFilename(SCOPE_PLUGINS, 'Extensions/RPUlite/get_ip_rtc.sh'), 0755)

	def cancel(self):
		for i in self["config"].list:
			i[1].cancel()
		self.session.openWithCallback(self.close, reloadsl)

	def update_ip(self):
		config.plugins.rpulite.servicetype.save()
		config.plugins.rpulite.bname.save()
		config.plugins.rpulite.source.save()
		for i in self["config"].list:
			i[1].save()
		configfile.save()

		self["text"].setText('')
		self.session.open(get_ip)

	def update_all(self):
		self.session.open(get_ip)
		self["text"].setText('')
		self.newproxy = config.plugins.rpulite.ip.value
		desk_tmp = channel_ref = ''
		#stream_tmp = 'http%3a//127.0.0.1%3a88/httpstream%3a//'
		if config.plugins.rpulite.servicetype.value is '2':
			stream_tmp = 'http%3a//127.0.0.1%3a88/httpstream%3a//'
		else:
			stream_tmp = ''
		if os.path.isfile('/tmp/rostelecom.m3u'):
			if os.path.isfile('/etc/enigma2/userbouquet.rostelecom_tmp.tv'):
				os.remove('/etc/enigma2/userbouquet.rostelecom_tmp.tv')
			with open('/etc/enigma2/userbouquet.rostelecom_tmp.tv', 'w') as outfile:
				outfile.write('#NAME %s\r\n' % config.plugins.rpulite.bname.value)
				for line in open('/tmp/rostelecom.m3u'):
					if len(line) > 2:
						if line[-2] != '\r':
							line = line.replace('\n', '\r\n')
					if 'udp/233.7.70.' in line:
						channel_ref = ref_base.ref.get(line.split('udp/')[-1].split(':')[0].strip('\r\n'))
						if not channel_ref or not config.plugins.rpulite.ref.value:
							channel_ref = ':0:1:0:0:0:0:0:0:0'
						line = line.replace(self.newproxy,  'rostelecom').replace(',ru', '')
						if config.plugins.rpulite.servicetype.value is '4097':
							outfile.write('#SERVICE %s%s:%s:%s\r\n' % (config.plugins.rpulite.servicetype.value, channel_ref, line.replace(':', '%3a', 3)[:-2], desk_tmp))
						else:
							outfile.write('#SERVICE 1%s:%s%s:%s\r\n' % (channel_ref, stream_tmp, line.replace(':', '%3a', 3)[:-2], desk_tmp))
						outfile.write('#DESCRIPTION %s\r\n' % desk_tmp)
					elif '#EXTINF:' in line:
						desk_tmp = line.split(',')[-1].replace('\r\n', '')
			outfile.close()
		if os.path.isfile('/etc/enigma2/userbouquet.rostelecom_tmp.tv') and os.path.isfile('/etc/enigma2/bouquets.tv'):
			remove_line('/etc/enigma2/bouquets.tv', 'rostelecom_tmp')
			remove_line('/etc/enigma2/bouquets.tv', 'LastScanned')
			with open('/etc/enigma2/bouquets.tv', 'a') as outfile:
				outfile.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.rostelecom_tmp.tv" ORDER BY bouquet\r\n')
				outfile.write('#SERVICE 1:7:1:0:0:0:0:0:0:0:FROM BOUQUET "userbouquet.LastScanned.tv" ORDER BY bouquet\r\n')
			outfile.close()
		self.iConsole.ePopen('wget -q -O - http://root:%s@127.0.0.1/web/servicelistreload?mode=0' % config.plugins.rpulite.rpassw.value)
		self["text"].setText(_('userbouquet.rostelecom_tmp.tv added or updated'))

class reloadsl(Screen):
	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self.session = session
		self.skin = SKIN_DWN
		self.newproxy = ''
		self.setTitle(_("Please wait"))
		self["status"] = StaticText()
		self.iConsole = iConsole()
		self["status"].text = _("Reload servicelist")
		self.iConsole.ePopen('wget -q -O - http://root:%s@127.0.0.1/web/servicelistreload?mode=0 && sleep 2' % config.plugins.rpulite.rpassw.value, self.cancel)
		
	def cancel(self, result, retval, extra_args):
		self.close()

SKIN_DWN = """
<screen name="get_epg_data" position="center,140" size="625,35" title="Please wait">
  <widget source="status" render="Label" position="10,5" size="605,22" zPosition="2" font="Regular; 20" halign="center" transparent="2" />
</screen>"""

class get_ip(Screen):
	def __init__(self, session, args=None):
		Screen.__init__(self, session)
		self.session = session
		self.skin = SKIN_DWN
		self.newproxy = ''
		self.setTitle(_("Please wait"))
		self["status"] = StaticText()
		self.iConsole = iConsole()
		self["status"].text = _("Donwloading ip & channel list")
		if config.plugins.rpulite.source.value == '0':
			self.iConsole.ePopen("wget -q 'http://plstonline.org/iptv/IPTV_29_V.m3u?' -O /tmp/rostelecom.m3u && sleep 4", self.get_ip2)
		else:
			self.iConsole.ePopen("wget -q 'http://iptv.lamp.ufa-it.ru/generate_m3u.php?num_list=001&shift=2&type=m3u' -O /tmp/rostelecom.m3u && sleep 4", self.get_ip2)
		
	def get_ip2(self, result, retval, extra_args):
		self.newproxy = ''
		if retval is 0:
			if os.path.isfile('/tmp/rostelecom.m3u'):
				for line in open('/tmp/rostelecom.m3u'):
					if 'udp/233.7.70.' in line:
						self.newproxy = line.split(':')[1].replace('//', '')
						break
			config.plugins.rpulite.ip.value = self.newproxy
			remove_line('/etc/hosts', 'rostelecom')
			add_line('/etc/hosts', '%s\trostelecom\t\trostelecom\n' % self.newproxy)
		else:
			self["status"].text = _("error...")
		config.plugins.rpulite.ip.save()
		config.save()
		self.close()

def main(session, **kwargs):
	session.open(rpulite)

def Plugins(**kwargs):
	list = [PluginDescriptor(name=_("2boom's Rostelecom lite proxy updater"), description=_("update Rostelecom iptv proxy"), where = [PluginDescriptor.WHERE_PLUGINMENU], icon="rpu.png", fnc=main)]
	if config.plugins.rpulite.menuext.value:
		list.append(PluginDescriptor(name=_("Rostelecom proxy lite updater"), description=_("update Rostelecom iptv proxy"), where = [PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main))
	return list

