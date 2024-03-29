# -*- coding: utf-8 -*-
 # Yahoo! weather for Hotkey
# Copyright (c) 2boom 2015-16
# v.0.3-r2
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

# http://where.yahooapis.com/v1/places.q('Kyiv')?appid=dj0yJmk9QmFoVGxPMzBiV282JmQ9WVdrOU5XbE5hVWxrTnpRbWNHbzlNQS0tJnM9Y29uc3VtZXJzZWNyZXQmeD0xMw--

import os
import time
import gettext
import socket
from enigma import eTimer
from twisted.web.client import downloadPage
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Tools.Directories import fileExists, resolveFilename, SCOPE_PLUGINS, SCOPE_LANGUAGE
from Components.config import getConfigListEntry, ConfigText, ConfigYesNo, ConfigSubsection, ConfigSelection, config, configfile
from Components.ConfigList import ConfigListScreen
from Components.Sources.StaticText import StaticText
from Components.ScrollLabel import ScrollLabel
from Components.Language import language
from Components.Pixmap import Pixmap
from Screens.MessageBox import MessageBox
from Screens.Standby import TryQuitMainloop
from Screens.Screen import Screen
import urllib

lang = language.getLanguage()
os.environ["LANGUAGE"] = lang[:2]
gettext.bindtextdomain("enigma2", resolveFilename(SCOPE_LANGUAGE))
gettext.textdomain("enigma2")
gettext.bindtextdomain("YWeather", "%s%s" % (resolveFilename(SCOPE_PLUGINS), "Extensions/YWfH/locale/"))


def _(txt):
	t = gettext.dgettext("YWeather", txt)
	if t == txt:
		t = gettext.gettext(txt)
	return t


def iconsdirs():
	iconset = []
	dirs = os.listdir("%sExtensions/YWfH/istyle/" % resolveFilename(SCOPE_PLUGINS))
	for istyledir in dirs:
		if os.path.isdir("%sExtensions/YWfH/istyle/%s" % (resolveFilename(SCOPE_PLUGINS), istyledir)):
			iconset.append(istyledir)
	return iconset


config.plugins.yweather = ConfigSubsection()
config.plugins.yweather.weather_city = ConfigText(default="924938", visible_width=70, fixed_size=False)
config.plugins.yweather.weather_city_locale = ConfigText(default="Kyiv", visible_width=170, fixed_size=False)
config.plugins.yweather.weather_city_locale_search = ConfigText(default="", visible_width=170, fixed_size=False)
config.plugins.yweather.enabled = ConfigYesNo(default=True)
config.plugins.yweather.skin = ConfigYesNo(default=False)
config.plugins.yweather.timeout = ConfigSelection(default='0', choices=[
		('0', _("Off")),
		('5', _("5 sec")),
		('8', _("8 sec")),
		('10', _("10 sec")),
		('12', _("12 sec")),
		('16', _("16 sec")),
		])
config.plugins.yweather.istyle = ConfigSelection(choices=iconsdirs())

help_txt = _("1. Visit http://woeid.rosselliot.co.nz\\n2. Enter your city or zip code and give go...\\n3. Copy ID (digit only)\\n4. Save and restart the enigma")


class WeatherInfo(Screen):
	def __init__(self, session):
		Screen.__init__(self, session)
		self.skin = SKIN_STYLE1_HD

		if config.plugins.yweather.skin.value:
			if fileExists('%sExtensions/YWfH/skin_user.xml' % resolveFilename(SCOPE_PLUGINS)):
				with open('%sExtensions/YWfH/skin_user.xml' % resolveFilename(SCOPE_PLUGINS), 'r') as user_skin:
					self.skin = user_skin.read()
				user_skin.close()
		self.setTitle(_("2boom's Yahoo! Weather"))
		self.Timer = eTimer()
		self.time_update = 20
		self.text = {'0': (_('Tornado')), '1': (_('Tropical storm')), '2': (_('Hurricane')), '3': (_('Severe thunderstorms')), '4': (_('Thunderstorms')),
			'5': (_('Mixed rain and snow')), '6': (_('Mixed rain and sleet')), '7': (_('Mixed snow and sleet')), '8': (_('Freezing drizzle')), '9': (_('Drizzle')),
			'10': (_('Freezing rain')), '11': (_('Showers')), '12': (_('Rain')), '13': (_('Snow flurries')), '14': (_('Light snow showers')), '15': (_('Blowing snow')),
			'16': (_('Snow')), '17': (_('Hail')), '18': (_('Sleet')), '19': (_('Dust')), '20': (_('Foggy')), '21': (_('Haze')), '22': (_('Smoky')), '23': (_('Blustery')),
			'24': (_('Windy')), '25': (_('Cold')), '26': (_('Cloudy')), '27': (_('Mostly cloudy (night)')), '28': (_('Mostly cloudy (day)')), '29': (_('Partly cloudy (night)')),
			'30': (_('Partly cloudy (day)')), '31': (_('Clear (night)')), '32': (_('Sunny')), '33': (_('Fair (night)')), '34': (_('Fair (day)')), '35': (_('Mixed rain and hail')),
			'36': (_('Hot')), '37': (_('Isolated thunderstorms')), '38': (_('Scattered thunderstorms')), '39': (_('Scattered thunderstorms')), '40': (_('Scattered showers')),
			'41': (_('Heavy snow')), '42': (_('Scattered snow showers')), '43': (_('Heavy snow')), '44': (_('Partly cloudy')), '45': (_('Thundershowers')), '46': (_('Snow showers')),
			'47': (_('Isolated thundershowers')), '3200': (_('Not available'))}
		self.weekday = {'Mon': (_('Monday')), 'Tue': (_('Tuesday')), 'Wed': (_('Wednesday')), 'Thu': (_('Thursday')), 'Fri': (_('Friday')), 'Sat': (_('Saturday')), 'Sun': (_('Sunday'))}
		self.month = {'Jan': (_('Jan.')), 'Feb': (_('Feb.')), 'Mar': (_('Mar.')), 'Apr': (_('Apr.')), 'May': (_('May')), 'June': (_('June')), 'July': (_('July')),
			'Aug': (_('Aug.')), 'Sept': (_('Sept.')), 'Oct': (_('Oct.')), 'Nov': (_('Nov.')), 'Dec': (_('Dec.'))}
		self.location = {'city': '', 'country': ''}
		self.geo = {'lat': '', 'long': ''}
		self.units = {'temperature': '', 'distance': '', 'pressure': '', 'speed': ''}
		self.wind = {'chill': '', 'direction': '', 'speed': ''}
		self.atmosphere = {'humidity': '', 'visibility': '', 'pressure': '', 'rising': ''}
		self.astronomy = {'sunrise': '', 'sunset': ''}
		self.condition = {'text': '', 'code': '', 'temp': '', 'date': ''}
		self.forecast = []
		self.forecastdata = {}
		self["temp_now"] = StaticText()
		self["temp_now_nounits"] = StaticText()
		self["temp_now_min"] = StaticText()
		self["temp_now_max"] = StaticText()
		self["feels_like"] = StaticText()
		self["wind"] = StaticText()
		self["text_now"] = StaticText()
		self["pressure"] = StaticText()
		self["humidity"] = StaticText()
		self["city_locale"] = StaticText()
		self["picon_now"] = Pixmap()
		self["tomorrow"] = StaticText(_('Tomorrow'))
		self["pressure_hpa"] = StaticText()
		self["wind_kmh"] = StaticText()
		self["sunrise"] = StaticText()
		self["sunset"] = StaticText()
		self["date"] = StaticText()
		self["visibility"] = StaticText()
		self["tomorrow"] = StaticText(_('Tomorrow'))
		self["lat"] = StaticText()
		self["long"] = StaticText()
		for daynumber in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
			day = 'day' + daynumber
			self["temp_" + day] = StaticText()
			self["forecast_" + day] = StaticText()
			self["forecastdate_" + day] = StaticText()
			self["picon_" + day] = Pixmap()
			self["text_" + day] = StaticText()
		self.notdata = False
		self["actions"] = ActionMap(["WizardActions", "MenuActions"],
		{
			"back": self.close,
			"ok": self.close,
			"right": self.close,
			"left": self.close,
			"down": self.close,
			"up": self.close,
			"menu": self.conf,
		}, -2)
		self.onShow.append(self.get_weather_data)

	def conf(self):
		self.session.open(yweather_setup)

	def isServerOnline(self):
		try:
			socket.gethostbyaddr('weather.yahooapis.com')
		except:
			return False
		return True

	def get_weather_data(self):
		if not os.path.exists("/tmp/yweather.xml") or int((time.time() - os.stat("/tmp/yweather.xml").st_mtime) / 60) >= self.time_update or self.notdata:
			self.get_xmlfile()
		else:
			self.parse_weather_data()

	def parse_weather_data(self):
		self.forecast = []
		for line in open("/tmp/yweather.xml"):
			if '<yweather:location' in line:
				self.location['city'] = self.get_data(line, 'city')
				self.location['country'] = self.get_data(line, 'country')
			elif '<yweather:units' in line:
				for data in ('temperature', 'distance', 'pressure', 'speed'):
					self.units[data] = self.get_data(line, data)
			elif '<yweather:wind' in line:
				for data in ('chill', 'direction', 'speed'):
					self.wind[data] = self.get_data(line, data)
			elif '<yweather:atmosphere' in line:
				for data in ('humidity', 'visibility', 'pressure', 'rising'):
					self.atmosphere[data] = self.get_data(line, data)
			elif '<yweather:astronomy' in line:
				self.astronomy['sunrise'] = self.get_data(line, 'sunrise')
				self.astronomy['sunset'] = self.get_data(line, 'sunset')
			elif '<yweather:condition' in line:
				for data in ('text', 'code', 'temp', 'date'):
					self.condition[data] = self.get_data(line, data)
			elif '<geo:lat' in line:
				self.geo['lat'] = self.get_data_xml(line)
			elif '<geo:long' in line:
				self.geo['long'] = self.get_data_xml(line)
			elif '<yweather:forecast' in line:
				self.forecast.append(line)
		for data in ('day', 'date', 'low', 'high', 'text', 'code'):
			for daynumber in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
				self.forecastdata[data + daynumber] = ''
		if len(self.forecast) == 10:
			for data in ('day', 'date', 'low', 'high', 'text', 'code'):
				for daynumber in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
					self.forecastdata[data + daynumber] = self.get_data(self.forecast[int(daynumber)], data)
		else:
			self.notdata = True
		if len(config.plugins.yweather.weather_city_locale.value) > 0:
			self["city_locale"].text = config.plugins.yweather.weather_city_locale.value
		for daynumber in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
			day = 'day' + daynumber
			if self.forecastdata[day] != '':
				self["forecast_" + day].text = '%s' % self.weekday[self.forecastdata[day]]
			else:
				self["forecast_" + day].text = _('N/A')
				self.notdata = True

			if self.forecastdata['date' + daynumber] != '':
				tmp_date = self.forecastdata['date' + daynumber]
				self["forecastdate_" + day].text = '%s %s' % (tmp_date.split()[0], self.month[tmp_date.split()[1]])
			else:
				self["forecastdate_" + day].text = _('N/A')
				self.notdata = True

			if self.forecastdata['low0'] != '' and self.forecastdata['high0'] != '':
				self["temp_now_min"].text = _('min: %s') % self.tempsing(self.forecastdata['low0'])
				self["temp_now_max"].text = _('max: %s') % self.tempsing(self.forecastdata['high0'])
			else:
				self["temp_now_min"].text = _('N/A')
				self["temp_now_max"].text = _('N/A')
				self.notdata = True
			if self.forecastdata['low' + daynumber] != '' and self.forecastdata['high' + daynumber] != '':
				self["temp_" + day].text = '%s / %s' % (self.tempsing_nu(self.forecastdata['low' + daynumber]), self.tempsing_nu(self.forecastdata['high' + daynumber]))
			else:
				self["temp_" + day].text = _('N/A')
				self.notdata = True
		defpicon = "%sExtensions/YWfH/istyle/%s/3200.png" % (resolveFilename(SCOPE_PLUGINS), config.plugins.yweather.istyle.value)
		for daynumber in ('0', '1', '2', '3', '4', '5', '6', '7', '8', '9'):
			day = 'day' + daynumber
			self["picon_" + day].instance.setScale(1)
			if self.forecastdata['code' + daynumber] != '':
				self["text_" + day].text = self.text[self.forecastdata['code' + daynumber]]
				self["picon_" + day].instance.setPixmapFromFile("%sExtensions/YWfH/istyle/%s/%s.png" % (resolveFilename(SCOPE_PLUGINS), config.plugins.yweather.istyle.value, self.forecastdata['code' + daynumber]))
			else:
				self["text_" + day].text = _('N/A')
				self["picon_" + day].instance.setPixmapFromFile(defpicon)
				self.notdata = True
			self["picon_" + day].instance.show()
		if self.condition['temp'] != '':
			self["temp_now"].text = self.tempsing(self.condition['temp'])
			self["temp_now_nounits"].text = self.tempsing_nu(self.condition['temp'])
		else:
			self["temp_now"].text = _('N/A')
			self["temp_now_nounits"].text = _('N/A')
			self.notdata = True

		if self.condition['date'] != '':
			self["date"].text = self.tempsing(self.condition['date']).replace('+', '')
		else:
			self["date"].text = _('N/A')
			self.notdata = True

		if self.wind['chill'] != '':
			self["feels_like"].text = _('Feels: %s') % self.tempsing(self.wind['chill'])
		else:
			self["feels_like"].text = _('N/A')
			self.notdata = True
		if self.condition['code'] != '' and self.wind['speed'] != '':
			direct = int(self.condition['code'])
			tmp_wind = (float(self.wind['speed']) * 1000) / 3600
			if direct >= 0 and direct <= 20:
				self["wind"].text = _('N, %3.02f m/s') % tmp_wind
			elif direct >= 21 and direct <= 35:
				self["wind"].text = _('NNE, %3.02f m/s') % tmp_wind
			elif direct >= 36 and direct <= 55:
				self["wind"].text = _('NE, %3.02f m/s') % tmp_wind
			elif direct >= 56 and direct <= 70:
				self["wind"].text = _('ENE, %3.02f m/s') % tmp_wind
			elif direct >= 71 and direct <= 110:
				self["wind"].text = _('E, %3.02f m/s') % tmp_wind
			elif direct >= 111 and direct <= 125:
				self["wind"].text = _('ESE, %3.02f m/s') % tmp_wind
			elif direct >= 126 and direct <= 145:
				self["wind"].text = _('SE, %3.02f m/s') % tmp_wind
			elif direct >= 146 and direct <= 160:
				self["wind"].text = _('SSE, %3.02f m/s') % tmp_wind
			elif direct >= 161 and direct <= 200:
				self["wind"].text = _('S, %3.02f m/s') % tmp_wind
			elif direct >= 201 and direct <= 215:
				self["wind"].text = _('SSW, %3.02f m/s') % tmp_wind
			elif direct >= 216 and direct <= 235:
				self["wind"].text = _('SW, %3.02f m/s') % tmp_wind
			elif direct >= 236 and direct <= 250:
				self["wind"].text = _('WSW, %3.02f m/s') % tmp_wind
			elif direct >= 251 and direct <= 290:
				self["wind"].text = _('W, %3.02f m/s') % tmp_wind
			elif direct >= 291 and direct <= 305:
				self["wind"].text = _('WNW, %3.02f m/s') % tmp_wind
			elif direct >= 306 and direct <= 325:
				self["wind"].text = _('NW, %3.02f m/s') % tmp_wind
			elif direct >= 326 and direct <= 340:
				self["wind"].text = _('NNW, %3.02f m/s') % tmp_wind
			elif direct >= 341 and direct <= 360:
				self["wind"].text = _('N, %3.02f m/s') % tmp_wind
			else:
				self["wind"].text = _('N/A')
				self.notdata = True
		if self.condition['code'] != '' and self.wind['speed'] != '':
			direct = int(self.condition['code'])
			if direct >= 0 and direct <= 20:
				self["wind_kmh"].text = _('N, %s km/h') % self.wind['speed']
			elif direct >= 21 and direct <= 35:
				self["wind_kmh"].text = _('NNE, %s km/h') % self.wind['speed']
			elif direct >= 36 and direct <= 55:
				self["wind_kmh"].text = _('NE, %s km/h') % self.wind['speed']
			elif direct >= 56 and direct <= 70:
				self["wind_kmh"].text = _('ENE, %s km/h') % self.wind['speed']
			elif direct >= 71 and direct <= 110:
				self["wind_kmh"].text = _('E, %s km/h') % self.wind['speed']
			elif direct >= 111 and direct <= 125:
				self["wind_kmh"].text = _('ESE, %s km/h') % self.wind['speed']
			elif direct >= 126 and direct <= 145:
				self["wind_kmh"].text = _('SE, %s km/h') % self.wind['speed']
			elif direct >= 146 and direct <= 160:
				self["wind_kmh"].text = _('SSE, %s km/h') % self.wind['speed']
			elif direct >= 161 and direct <= 200:
				self["wind_kmh"].text = _('S, %s km/h') % self.wind['speed']
			elif direct >= 201 and direct <= 215:
				self["wind_kmh"].text = _('SSW, %s km/h') % self.wind['speed']
			elif direct >= 216 and direct <= 235:
				self["wind_kmh"].text = _('SW, %s km/h') % self.wind['speed']
			elif direct >= 236 and direct <= 250:
				self["wind_kmh"].text = _('WSW, %s km/h') % self.wind['speed']
			elif direct >= 251 and direct <= 290:
				self["wind_kmh"].text = _('W, %s km/h') % self.wind['speed']
			elif direct >= 291 and direct <= 305:
				self["wind_kmh"].text = _('WNW, %s km/h') % self.wind['speed']
			elif direct >= 306 and direct <= 325:
				self["wind_kmh"].text = _('NW, %s km/h') % self.wind['speed']
			elif direct >= 326 and direct <= 340:
				self["wind_kmh"].text = _('NNW, %s km/h') % self.wind['speed']
			elif direct >= 341 and direct <= 360:
				self["wind_kmh"].text = _('N, %s km/h') % self.wind['speed']
			else:
				self["wind_kmh"].text = _('N/A')
				self.notdata = True
		else:
			self.notdata = True
		if self.condition['code'] != '':
			self["text_now"].text = self.text[self.condition['code']]
		else:
			self["text_now"].text = _('N/A')
			self.notdata = True
		if self.atmosphere['pressure'] != '':
			tmp_pressure = round(float(self.atmosphere['pressure']) * 0.75)
			self["pressure"].text = _("%d mmHg") % tmp_pressure
		else:
			self["pressure"].text = _('N/A')
			self.notdata = True
		if self.atmosphere['pressure'] != '':
			self["pressure_hpa"].text = _("%s hPa(mbar)") % self.atmosphere['pressure']
		else:
			self["pressure_hpa"].text = _('N/A')
			self.notdata = True
		if self.atmosphere['humidity'] != '':
			self["humidity"].text = _('%s%% humidity') % self.atmosphere['humidity']
		else:
			self["humidity"].text = _('N/A')
			self.notdata = True
		if self.atmosphere['visibility'] != '':
			self["visibility"].text = _('%s km') % self.atmosphere['visibility']
		else:
			self["visibility"].text = _('N/A')
			self.notdata = True

		if self.geo['lat'] != '':
			if self.geo['lat'].startswith('-'):
				self["lat"].text = '%s S' % self.geo['lat']
			else:
				self["lat"].text = '%s N' % self.geo['lat']
		else:
			self["lat"].text = _('N/A')
			self.notdata = True

		if self.geo['long'] != '':
			if self.geo['long'].startswith('-'):
				self["long"].text = '%s W' % self.geo['long']
			else:
				self["long"].text = '%s E' % self.geo['long']
		else:
			self["long"].text = _('N/A')
			self.notdata = True

		if self.astronomy['sunrise'] != '':
			self["sunrise"].text = _('%s') % self.time_convert(self.astronomy['sunrise'])
		else:
			self["sunrise"].text = _('N/A')
			self.notdata = True

		if self.astronomy['sunset'] != '':
			self["sunset"].text = _('%s') % self.time_convert(self.astronomy['sunset'])
		else:
			self["sunset"].text = _('N/A')
			self.notdata = True

		self["picon_now"].instance.setScale(1)
		if self.condition['code'] != '':
			self["picon_now"].instance.setPixmapFromFile("%sExtensions/YWfH/istyle/%s/%s.png" % (resolveFilename(SCOPE_PLUGINS), config.plugins.yweather.istyle.value, self.condition['code']))
		else:
			self["picon_now"].instance.setPixmapFromFile(defpicon)
		self["picon_now"].instance.show()
		if config.plugins.yweather.timeout.value != '0':
			self.Timer.callback.append(self.endshow)
			self.Timer.startLongTimer(int(config.plugins.yweather.timeout.value))

	def endshow(self):
		if config.plugins.yweather.timeout.value != '0':
			self.Timer.stop()
			self.close(False)

	def get_xmlfile(self):
		if self.isServerOnline():
			xmlfile = "http://weather.yahooapis.com/forecastrss?w=%s&d=10&u=c" % config.plugins.yweather.weather_city.value
			downloadPage(xmlfile, "/tmp/yweather.xml").addCallback(self.downloadFinished).addErrback(self.downloadFailed)
		else:
			self["text_now"].text = _('weatherserver not respond')
			self.notdata = True

	def time_convert(self, time):
		print("[YWeather] Time convert")
		tmp_time = ''
		if time.endswith('pm'):
			tmp_time = '%s:%s' % (int(time.split()[0].split(':')[0]) + 12, time.split()[0].split(':')[-1])
		else:
			tmp_time = time.replace('am', '').strip()
		if len(tmp_time) == 4:
			return '0%s' % tmp_time
		else:
			return tmp_time

	def downloadFinished(self, result):
		print("[YWeather] Download finished")
		self.notdata = False
		self.parse_weather_data()

	def downloadFailed(self, result):
		self.notdata = True
		print("[YWeather] Download failed!")

	def get_data(self, line, what):
		return line.split(what)[-1].split('"')[1]

	def get_data_xml(self, line):
		return line.split('</')[0].split('>')[1]

	def tempsing(self, what):
		if what[0] != '-' and what[0] != '0':
			return '+' + what + '%s' % unichr(176).encode("latin-1") + self.units['temperature']
		else:
			return what + '%s' % unichr(176).encode("latin-1") + self.units['temperature']

	def tempsing_nu(self, what):
		if what[0] != '-' and what[0] != '0':
			return '+' + what + '%s' % unichr(176).encode("latin-1")
		else:
			return what + '%s' % unichr(176).encode("latin-1")


##############################################################################
SKIN_STYLE1_HD = """
<screen name="WeatherInfo" position="365,90" size="550,590" title="2boom's Yahoo Weather" zPosition="1" flags="wfBorder">
    <widget source="city_locale" render="Label" position="150,2" size="250,30" zPosition="3" font="Regular; 27" horizontalAlignment="center" transparent="1" verticalAlignment="center" />
    <eLabel position="20,181" size="512,2" backgroundColor="#00aaaaaa" zPosition="5" />
    <eLabel position="20,385" size="512,2" backgroundColor="#00aaaaaa" zPosition="5" />
    <eLabel position="145,35" size="260,2" backgroundColor="#00aaaaaa" zPosition="5" />
    <widget name="picon_now" position="206,40" size="112,112" zPosition="2" alphaTest="blend" />
    <widget source="temp_now_min" render="Label" position="0,102" size="170,20" zPosition="3" font="Regular; 17" horizontalAlignment="right" transparent="1" foregroundColor="#00aaaaaa" />
    <widget source="temp_now_max" render="Label" position="0,123" size="170,20" zPosition="3" font="Regular; 17" horizontalAlignment="right" transparent="1" foregroundColor="#00aaaaaa" />
    <widget source="temp_now" render="Label" position="0,66" size="170,35" zPosition="2" font="Regular; 35" horizontalAlignment="right" transparent="1" foregroundColor="#00f0bf4f" />
    <widget source="feels_like" render="Label" position="0,46" size="170,20" zPosition="2" font="Regular; 17" horizontalAlignment="right" transparent="2" />
    <widget source="text_now" render="Label" position="146,152" size="250,22" zPosition="3" font="Regular; 19" horizontalAlignment="center" transparent="1" />
    <widget source="pressure" render="Label" position="379,80" size="140,20" zPosition="3" font="Regular; 17" horizontalAlignment="left" transparent="1" foregroundColor="#00aaaaaa" />
    <widget source="humidity" render="Label" position="379,102" size="140,20" zPosition="3" font="Regular; 17" horizontalAlignment="left" transparent="1" foregroundColor="#00aaaaaa" />
    <widget source="wind" render="Label" position="379,46" size="140,20" zPosition="3" font="Regular; 17" horizontalAlignment="left" transparent="1" foregroundColor="#00aaaaaa" />
    <widget name="picon_day1" position="20,231" size="96,96" zPosition="2" alphaTest="blend" />
    <widget source="forecast_day1" render="Label" position="4,187" size="125,22" zPosition="2" font="Regular; 19" horizontalAlignment="center" transparent="1" />
    <widget source="temp_day1" render="Label" position="7,325" size="120,21" zPosition="2" font="Regular; 19" horizontalAlignment="center" transparent="1" foregroundColor="#00f0bf4f" />
    <widget source="text_day1" render="Label" position="7,345" size="120,36" zPosition="2" font="Regular; 16" horizontalAlignment="center" transparent="1" foregroundColor="#00aaaaaa" />
    <eLabel position="135,198" size="2,170" backgroundColor="#00aaaaaa" zPosition="5" />
    <widget name="picon_day2" position="160,230" size="96,96" zPosition="2" alphaTest="blend" />
    <widget source="forecast_day2" render="Label" position="143,187" size="125,22" zPosition="2" font="Regular; 19" horizontalAlignment="center" transparent="1" />
    <widget source="temp_day2" render="Label" position="147,325" size="120,21" zPosition="2" font="Regular; 19" horizontalAlignment="center" transparent="1" foregroundColor="#00f0bf4f" />
    <widget source="text_day2" render="Label" position="147,345" size="120,36" zPosition="2" font="Regular; 16" horizontalAlignment="center" transparent="1" foregroundColor="#00aaaaaa" />
    <eLabel position="275,198" size="2,170" backgroundColor="#00aaaaaa" zPosition="5" />
    <widget name="picon_day3" position="295,230" size="96,96" zPosition="2" alphaTest="blend" />
    <widget source="forecast_day3" render="Label" position="284,187" size="125,22" zPosition="2" font="Regular; 19" horizontalAlignment="center" transparent="1" verticalAlignment="center" />
    <widget source="temp_day3" render="Label" position="286,325" size="120,21" zPosition="2" font="Regular; 19" horizontalAlignment="center" transparent="1" foregroundColor="#00f0bf4f" />
    <widget source="text_day3" render="Label" position="286,345" size="120,36" zPosition="2" font="Regular; 16" horizontalAlignment="center" transparent="1" foregroundColor="#00aaaaaa" />
    <eLabel position="415,198" size="2,170" backgroundColor="#00aaaaaa" zPosition="5" />
    <widget name="picon_day4" position="435,230" size="96,96" zPosition="2" alphaTest="blend" />
    <widget source="forecast_day4" render="Label" position="424,187" size="125,22" zPosition="2" font="Regular; 19" horizontalAlignment="center" transparent="1" />
    <widget source="temp_day4" render="Label" position="426,325" size="120,21" zPosition="2" font="Regular; 19" horizontalAlignment="center" transparent="1" foregroundColor="#00f0bf4f" />
    <widget source="text_day4" render="Label" position="426,345" size="120,36" zPosition="2" font="Regular; 16" horizontalAlignment="center" transparent="1" foregroundColor="#00aaaaaa" />
    <widget source="forecastdate_day1" render="Label" position="7,210" size="120,19" zPosition="2" font="Regular; 17" horizontalAlignment="center" transparent="1" foregroundColor="#00f0bf4f" />
    <widget source="forecastdate_day2" render="Label" position="147,210" size="120,19" zPosition="2" font="Regular; 17" horizontalAlignment="center" transparent="1" foregroundColor="#00f0bf4f" />
    <widget source="forecastdate_day3" render="Label" position="286,210" size="120,19" zPosition="2" font="Regular; 17" horizontalAlignment="center" transparent="1" foregroundColor="#00f0bf4f" />
    <widget source="forecastdate_day4" render="Label" position="426,210" size="120,19" zPosition="2" font="Regular; 17" horizontalAlignment="center" transparent="1" foregroundColor="#00f0bf4f" />
    <eLabel position="415,407" size="2,170" backgroundColor="#00aaaaaa" zPosition="5" />
    <widget source="forecast_day8" render="Label" position="424,391" size="125,22" zPosition="2" font="Regular; 19" horizontalAlignment="center" transparent="1" />
    <widget source="forecastdate_day8" render="Label" position="426,414" size="120,19" zPosition="2" font="Regular; 17" horizontalAlignment="center" transparent="1" foregroundColor="#00f0bf4f" />
    <widget name="picon_day8" position="435,434" size="96,96" zPosition="2" alphaTest="blend" />
    <widget source="temp_day8" render="Label" position="426,529" size="120,21" zPosition="2" font="Regular; 19" horizontalAlignment="center" transparent="1" foregroundColor="#00f0bf4f" />
    <widget source="text_day8" render="Label" position="426,549" size="120,36" zPosition="2" font="Regular; 16" horizontalAlignment="center" transparent="1" foregroundColor="#00aaaaaa" />
    <eLabel position="275,407" size="2,170" backgroundColor="#00aaaaaa" zPosition="5" />
    <widget source="forecast_day7" render="Label" position="284,391" size="125,22" zPosition="2" font="Regular; 19" horizontalAlignment="center" transparent="1" />
    <widget source="forecastdate_day7" render="Label" position="286,414" size="120,19" zPosition="2" font="Regular; 17" horizontalAlignment="center" transparent="1" foregroundColor="#00f0bf4f" />
    <widget name="picon_day7" position="295,434" size="96,96" zPosition="2" alphaTest="blend" />
    <widget source="temp_day7" render="Label" position="286,529" size="120,21" zPosition="2" font="Regular; 19" horizontalAlignment="center" transparent="1" foregroundColor="#00f0bf4f" />
    <widget source="text_day7" render="Label" position="286,549" size="120,36" zPosition="2" font="Regular; 16" horizontalAlignment="center" transparent="1" foregroundColor="#00aaaaaa" />
    <eLabel position="135,407" size="2,170" backgroundColor="#00aaaaaa" zPosition="5" />
    <widget source="forecast_day6" render="Label" position="144,391" size="125,22" zPosition="2" font="Regular; 19" horizontalAlignment="center" transparent="1" />
    <widget source="forecastdate_day6" render="Label" position="146,414" size="120,19" zPosition="2" font="Regular; 17" horizontalAlignment="center" transparent="1" foregroundColor="#00f0bf4f" />
    <widget name="picon_day6" position="155,434" size="96,96" zPosition="2" alphaTest="blend" />
    <widget source="temp_day6" render="Label" position="146,529" size="120,21" zPosition="2" font="Regular; 19" horizontalAlignment="center" transparent="1" foregroundColor="#00f0bf4f" />
    <widget source="text_day6" render="Label" position="146,549" size="120,36" zPosition="2" font="Regular; 16" horizontalAlignment="center" transparent="1" foregroundColor="#00aaaaaa" />
    <widget source="forecast_day5" render="Label" position="4,391" size="125,22" zPosition="2" font="Regular; 19" horizontalAlignment="center" transparent="1" />
    <widget source="forecastdate_day5" render="Label" position="6,414" size="120,19" zPosition="2" font="Regular; 17" horizontalAlignment="center" transparent="1" foregroundColor="#00f0bf4f" />
    <widget name="picon_day5" position="15,434" size="96,96" zPosition="2" alphaTest="blend" />
    <widget source="temp_day5" render="Label" position="6,529" size="120,21" zPosition="2" font="Regular; 19" horizontalAlignment="center" transparent="1" foregroundColor="#00f0bf4f" />
    <widget source="text_day5" render="Label" position="6,549" size="120,36" zPosition="2" font="Regular; 16" horizontalAlignment="center" transparent="1" foregroundColor="#00aaaaaa" />
    <widget source="visibility" render="Label" position="379,123" size="140,20" zPosition="3" font="Regular; 17" horizontalAlignment="left" transparent="1" foregroundColor="#00aaaaaa" />
</screen>
"""
SKIN_CONFIG_HD = """
<screen name="yweather_setup" position="center,140" size="750,505" title="2boom's Yahoo Weather">
  <widget position="15,10" size="720,150" name="config" scrollbarMode="showOnDemand" />
  <eLabel position="30,165" size="690,2" backgroundColor="#00aaaaaa" zPosition="5" />
  <ePixmap position="10,498" zPosition="1" size="165,2" pixmap="~/images/red.png" alphaTest="blend" />
  <widget source="key_red" render="Label" position="10,468" zPosition="2" size="165,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" transparent="1" />
  <ePixmap position="175,498" zPosition="1" size="165,2" pixmap="~/images/green.png" alphaTest="blend" />
  <widget source="key_green" render="Label" position="175,468" zPosition="2" size="165,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" transparent="1" />
  <ePixmap position="340,498" zPosition="1" size="195,2" pixmap="~/images/yellow.png" alphaTest="blend" />
  <widget source="key_yellow" render="Label" position="340,468" zPosition="2" size="195,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" transparent="1" />
  <ePixmap position="535,498" zPosition="1" size="195,2" pixmap="~/images/blue.png" alphaTest="blend" />
  <widget source="key_blue" render="Label" position="535,468" zPosition="2" size="195,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" transparent="1" />
  <widget name="text" position="50,175" size="650,150" font="Regular;22" horizontalAlignment="left" noWrap="1" />
  <widget name="icon1" position="100,336" size="96,96" zPosition="2" alphaTest="blend" />
  <widget name="icon2" position="245,336" size="96,96" zPosition="2" alphaTest="blend" />
  <widget name="icon3" position="390,336" size="96,96" zPosition="2" alphaTest="blend" />
  <widget name="icon4" position="535,336" size="96,96" zPosition="2" alphaTest="blend" />
</screen>"""

SKIN_SEARCH_HD = """
<screen name="search_setup" position="center,140" size="750,505" title="2boom's Yahoo Weather">
  <widget position="15,10" size="720,50" name="config" scrollbarMode="showOnDemand" />
  <eLabel position="30,65" size="690,2" backgroundColor="#00aaaaaa" zPosition="5" />
  <ePixmap position="10,498" zPosition="1" size="165,2" pixmap="~/images/red.png" alphaTest="blend" />
  <widget source="key_red" render="Label" position="10,468" zPosition="2" size="165,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" transparent="1" />
  <ePixmap position="175,498" zPosition="1" size="165,2" pixmap="~/images/green.png" alphaTest="blend" />
  <widget source="key_green" render="Label" position="175,468" zPosition="2" size="165,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" transparent="1" />
  <ePixmap position="340,498" zPosition="1" size="195,2" pixmap="~/images/yellow.png" alphaTest="blend" />
  <widget source="key_yellow" render="Label" position="340,468" zPosition="2" size="195,30" font="Regular;20" horizontalAlignment="center" verticalAlignment="center" transparent="1" />
  <widget name="text" position="50,75" size="650,150" font="Regular;22" horizontalAlignment="left" noWrap="1" />
</screen>"""


class yweather_setup(Screen, ConfigListScreen):
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skin_path = resolveFilename(SCOPE_PLUGINS, "Extensions/YWfH")
		self.skin = SKIN_CONFIG_HD
		config.plugins.yweather.istyle = ConfigSelection(choices=iconsdirs())
		self.setTitle(_("2boom's Yahoo! Weather"))
		self.list = []
		self.list.append(getConfigListEntry(_("City code (woeid)"), config.plugins.yweather.weather_city))
		self.list.append(getConfigListEntry(_("City name (alias)"), config.plugins.yweather.weather_city_locale))
		self.list.append(getConfigListEntry(_("Weather info timeout"), config.plugins.yweather.timeout))
		self.list.append(getConfigListEntry(_("Weather icons style"), config.plugins.yweather.istyle))
		self.list.append(getConfigListEntry(_("User skin"), config.plugins.yweather.skin))
		ConfigListScreen.__init__(self, self.list, session=session)
		self["text"] = ScrollLabel("")
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Restart"))
		self["key_blue"] = StaticText(_("Get WOEID"))
		self["text"].setText(help_txt)
		for item in ('1', '2', '3', '4'):
			self["icon" + item] = Pixmap()
		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.cancel,
			"cancel": self.cancel,
			"green": self.save,
			"yellow": self.restart,
			"blue": self.get_woeid,
			"ok": self.save
		}, -2)
		self.onLayoutFinish.append(self.showicon)

	def get_woeid(self):
		self.session.open(search_setup)

	def showicon(self):
		count = 1
		for number in ('8', '18', '22', '32'):
			if fileExists("%sExtensions/YWfH/istyle/%s/%s.png" % (resolveFilename(SCOPE_PLUGINS), config.plugins.yweather.istyle.value, number)):
				self["icon%s" % str(count)].instance.setScale(1)
				self["icon%s" % str(count)].instance.setPixmapFromFile("%sExtensions/YWfH/istyle/%s/%s.png" % (resolveFilename(SCOPE_PLUGINS), config.plugins.yweather.istyle.value, number))
				self["icon%s" % str(count)].instance.show()
			count += 1

	def keyLeft(self):
		ConfigListScreen.keyLeft(self)
		self.showicon()

	def keyRight(self):
		ConfigListScreen.keyRight(self)
		self.showicon()

	def restart(self):
		self.session.open(TryQuitMainloop, 3)

	def cancel(self):
		for i in self["config"].list:
			i[1].cancel()
		self.close(False)

	def save(self):
		for i in self["config"].list:
			i[1].save()
		configfile.save()
		self.mbox = self.session.open(MessageBox, (_("configuration is saved")), MessageBox.TYPE_INFO, timeout=4)


class search_setup(Screen, ConfigListScreen):
	def __init__(self, session):
		self.session = session
		Screen.__init__(self, session)
		self.skin = SKIN_SEARCH_HD
		config.plugins.yweather.weather_city_locale_search.value = ''
		self.setTitle(_("2boom's Yahoo! Weather"))
		self.list = []
		self.code_woeid = ''
		self.place_name = ''
		self.list.append(getConfigListEntry(_("The name of the location"), config.plugins.yweather.weather_city_locale_search))
		ConfigListScreen.__init__(self, self.list, session=session)
		self["text"] = ScrollLabel("")
		self["key_red"] = StaticText(_("Close"))
		self["key_green"] = StaticText(_("Save"))
		self["key_yellow"] = StaticText(_("Get"))

		self["setupActions"] = ActionMap(["SetupActions", "ColorActions"],
		{
			"red": self.cancel,
			"cancel": self.cancel,
			"green": self.save,
			"yellow": self.get_woeid,
			"ok": self.save
		}, -2)
		self.onLayoutFinish.append(self.show_woeid)

	def show_woeid(self):
		self["text"].setText(_('no woeid code yet'))

	def parse_woeid_data(self):
		if os.path.exists("/tmp/woeid.xml"):
			woeid_line = open('/tmp/woeid.xml').read()
			os.remove("/tmp/woeid.xml")
			self.code_woeid = self.get_data_inline(woeid_line, 'woeid')
			self.place_name = self.get_data_inline(woeid_line, 'name')
			if 'yahoo:uri' in woeid_line:
				self["text"].setText(self.get_data_inline(woeid_line, 'woeid') + '\n' + self.get_data_inline(woeid_line, 'name') + '\n' + self.get_lastdata_inline(woeid_line, 'admin1') + '\n' + self.get_lastdata_inline(woeid_line, 'country'))
			else:
				self["text"].setText(_('error location name'))
		else:
			self["text"].setText(_('/tmp/woeid.xml not found'))

	def get_data_inline(self, line, what):
		return line.split('</' + what + '>')[0].split('<' + what + '>')[-1]

	def get_lastdata_inline(self, line, what):
		return line.split('</' + what + '>')[0].split('>')[-1]

	def cancel(self):
		for i in self["config"].list:
			i[1].cancel()
		config.plugins.yweather.weather_city_locale_search.value = ''
		if os.path.exists("/tmp/woeid.xml"):
			os.remove("/tmp/woeid.xml")
		self.close(False)

	def save(self):
		config.plugins.yweather.weather_city.value = self.code_woeid
		config.plugins.yweather.weather_city_locale.value = self.place_name
		config.plugins.yweather.weather_city_locale_search.value = ''
		config.plugins.yweather.weather_city_locale_search.save()
		config.plugins.yweather.weather_city_locale.save()
		config.plugins.yweather.weather_city.save()
		configfile.save()
		if os.path.exists("/tmp/woeid.xml"):
			os.remove("/tmp/woeid.xml")
		if os.path.exists("/tmp/yweather.xml"):
			os.remove("/tmp/yweather.xml")
		self.mbox = self.session.open(MessageBox, (_("configuration is saved")), MessageBox.TYPE_INFO, timeout=4)

	def get_woeid(self):
		if self.isServerOnline():
			urllib.urlretrieve("http://where.yahooapis.com/v1/places.q('%s')?appid=dj0yJmk9QmFoVGxPMzBiV282JmQ9WVdrOU5XbE5hVWxrTnpRbWNHbzlNQS0tJnM9Y29uc3VtZXJzZWNyZXQmeD0xMw--" % config.plugins.yweather.weather_city_locale_search.value, "/tmp/woeid.xml")
			self.parse_woeid_data()
		else:
			self["text"].setText('/tmp/woeid.xml not found')

	def isServerOnline(self):
		try:
			socket.gethostbyaddr('where.yahooapis.com')
		except:
			return False
		return True


def main(session, **kwargs):
	session.open(WeatherInfo)


def Plugins(**kwargs):
	list = [PluginDescriptor(name=_("2boom's Yahoo! Weather for Hotkey"), description=_("press menukey for config"), where=[PluginDescriptor.WHERE_PLUGINMENU], icon="yw.png", fnc=main)]
	return list
