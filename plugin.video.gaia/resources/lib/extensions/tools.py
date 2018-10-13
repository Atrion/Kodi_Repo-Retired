# -*- coding: utf-8 -*-

'''
	Gaia Add-on
	Copyright (C) 2016 Gaia

	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import xbmc
import xbmcgui
import xbmcaddon
import xbmcvfs
import xbmcgui
import numbers
import json
import time
import datetime
import calendar
import subprocess
import webbrowser
import sys
import os
import stat
import uuid
import hashlib
import shutil
import imp
import pkgutil
import re
import urlparse
import urllib
import platform
import zipfile
import threading

from resources.lib.externals import pytz
from resources.lib.externals.unidecode import unidecode

class Time(object):

	# Use time.clock() instead of time.time() for processing time.
	# NB: Do not use time.clock(). Gives the wrong answer in timestamp() AND runs very fast in Linux. Hence, in the stream finding dialog, for every real second, Linux progresses 5-6 seconds.
	# http://stackoverflow.com/questions/85451/python-time-clock-vs-time-time-accuracy
	# https://www.tutorialspoint.com/python/time_clock.htm

	ZoneUtc = 'utc'
	ZoneLocal = 'local'

	def __init__(self, start = False):
		self.mStart = None
		if start: self.start()

	def start(self):
		self.mStart = time.time()
		return self.mStart

	def restart(self):
		return self.start()

	def elapsed(self, milliseconds = False):
		if self.mStart == None:
			self.mStart = time.time()
		if milliseconds: return int((time.time() - self.mStart) * 1000)
		else: return int(time.time() - self.mStart)

	def expired(self, expiration):
		return self.elapsed() >= expiration

	@classmethod
	def sleep(self, seconds):
		time.sleep(seconds)

	# UTC timestamp
	@classmethod
	def timestamp(self, fixedTime = None):
		if fixedTime == None:
			# Do not use time.clock(), gives incorrect result for search.py
			return int(time.time())
		else:
			return int(time.mktime(fixedTime.timetuple()))

	# datetime object from string
	@classmethod
	def datetime(self, string, format = '%Y-%m-%d %H:%M:%S'):
		try:
			return datetime.datetime.strptime(string, format)
		except:
			# Older Kodi Python versions do not have the strptime function.
			# http://forum.kodi.tv/showthread.php?tid=112916
			return datetime.datetime.fromtimestamp(time.mktime(time.strptime(string, format)))

	@classmethod
	def localZone(self):
		if time.daylight:
			offsetHour = time.altzone / 3600
		else:
			offsetHour = time.timezone / 3600
		return 'Etc/GMT%+d' % offsetHour

	@classmethod
	def convert(self, stringTime, stringDay = None, abbreviate = False, formatInput = '%H:%M', formatOutput = None, zoneFrom = ZoneUtc, zoneTo = ZoneLocal):
		result = ''
		try:
			# If only time is given, the date will be set to 1900-01-01 and there are conversion problems if this goes down to 1899.
			if formatInput == '%H:%M':
				# Use current datetime (now) in order to accomodate for daylight saving time.
				stringTime = '%s %s' % (datetime.datetime.now().strftime('%Y-%m-%d'), stringTime)
				formatNew = '%Y-%m-%d %H:%M'
			else:
				formatNew = formatInput

			if zoneFrom == self.ZoneUtc: zoneFrom = pytz.timezone('UTC')
			elif zoneFrom == self.ZoneLocal: zoneFrom = pytz.timezone(self.localZone())
			else: zoneFrom = pytz.timezone(zoneFrom)

			if zoneTo == self.ZoneUtc: zoneTo = pytz.timezone('UTC')
			elif zoneTo == self.ZoneLocal: zoneTo = pytz.timezone(self.localZone())
			else: zoneTo = pytz.timezone(zoneTo)

			timeobject = self.datetime(string = stringTime, format = formatNew)

			if stringDay:
				stringDay = stringDay.lower()
				if stringDay.startswith('mon'): weekday = 0
				elif stringDay.startswith('tue'): weekday = 1
				elif stringDay.startswith('wed'): weekday = 2
				elif stringDay.startswith('thu'): weekday = 3
				elif stringDay.startswith('fri'): weekday = 4
				elif stringDay.startswith('sat'): weekday = 5
				else: weekday = 6
				weekdayCurrent = datetime.datetime.now().weekday()
				timeobject += datetime.timedelta(days = weekday) - datetime.timedelta(days = weekdayCurrent)

			timeobject = zoneFrom.localize(timeobject)
			timeobject = timeobject.astimezone(zoneTo)

			if not formatOutput: formatOutput = formatInput

			stringTime = timeobject.strftime(formatOutput)
			if stringDay:
				if abbreviate:
					stringDay = calendar.day_abbr[timeobject.weekday()]
				else:
					stringDay = calendar.day_name[timeobject.weekday()]
				return (stringTime, stringDay)
			else:
				return stringTime
		except:
			Logger.error()
			return stringTime

class Math(object):

	@classmethod
	def scale(self, value, fromMinimum = 0, fromMaximum = 1, toMinimum = 0, toMaximum = 1):
		return toMinimum + (value - fromMinimum) * ((toMaximum - toMinimum) / (fromMaximum - fromMinimum))

class Language(object):

	# Cases
	CaseCapital = 0
	CaseUpper = 1
	CaseLower = 2

	Automatic = 'automatic'
	Alternative = 'alternative'

	UniversalName = 'Universal'
	UniversalCode = 'un'

	EnglishName = 'English'
	EnglishCode = 'en'

	Names = [UniversalName, 'Abkhaz', 'Afar', 'Afrikaans', 'Akan', 'Albanian', 'Amharic', 'Arabic', 'Aragonese', 'Armenian', 'Assamese', 'Avaric', 'Avestan', 'Aymara', 'Azerbaijani', 'Bambara', 'Bashkir', 'Basque', 'Belarusian', 'Bengali', 'Bihari', 'Bislama', 'Bokmal', 'Bosnian', 'Breton', 'Bulgarian', 'Burmese', 'Catalan', 'Chamorro', 'Chechen', 'Chichewa', 'Chinese', 'Chuvash', 'Cornish', 'Corsican', 'Cree', 'Croatian', 'Czech', 'Danish', 'Divehi', 'Dutch', 'Dzongkha', EnglishName, 'Esperanto', 'Estonian', 'Ewe', 'Faroese', 'Fijian', 'Finnish', 'French', 'Fula', 'Gaelic', 'Galician', 'Ganda', 'Georgian', 'German', 'Greek', 'Guarani', 'Gujarati', 'Haitian', 'Hausa', 'Hebrew', 'Herero', 'Hindi', 'Hiri Motu', 'Hungarian', 'Icelandic', 'Ido', 'Igbo', 'Indonesian', 'Interlingua', 'Interlingue', 'Inuktitut', 'Inupiaq', 'Irish', 'Italian', 'Japanese', 'Javanese', 'Kalaallisut', 'Kannada', 'Kanuri', 'Kashmiri', 'Kazakh', 'Khmer', 'Kikuyu', 'Kinyarwanda', 'Kirundi', 'Komi', 'Kongo', 'Korean', 'Kurdish', 'Kwanyama', 'Kyrgyz', 'Lao', 'Latin', 'Latvian', 'Limburgish', 'Lingala', 'Lithuanian', 'Luba-Katanga', 'Luxembourgish', 'Macedonian', 'Malagasy', 'Malay', 'Malayalam', 'Maltese', 'Manx', 'Maori', 'Marathi', 'Marshallese', 'Mongolian', 'Nauruan', 'Navajo', 'Ndonga', 'Nepali', 'Northern Ndebele', 'Northern Sami', 'Norwegian', 'Nuosu', 'Nynorsk', 'Occitan', 'Ojibwe', 'Oriya', 'Oromo', 'Ossetian', 'Pali', 'Pashto', 'Persian', 'Polish', 'Portuguese', 'Punjabi', 'Quechua', 'Romanian', 'Romansh', 'Russian', 'Samoan', 'Sango', 'Sanskrit', 'Sardinian', 'Serbian', 'Shona', 'Sindhi', 'Sinhalese', 'Slavonic', 'Slovak', 'Slovene', 'Somali', 'Southern Ndebele', 'Southern Sotho', 'Spanish', 'Sundanese', 'Swahili', 'Swati', 'Swedish', 'Tagalog', 'Tahitian', 'Tajik', 'Tamil', 'Tatar', 'Telugu', 'Thai', 'Tibetan', 'Tigrinya', 'Tonga', 'Tsonga', 'Tswana', 'Turkish', 'Turkmen', 'Twi', 'Ukrainian', 'Urdu', 'Uyghur', 'Uzbek', 'Venda', 'Vietnamese', 'Volapuk', 'Walloon', 'Welsh', 'Western Frisian', 'Wolof', 'Xhosa', 'Yiddish', 'Yoruba', 'Zhuang', 'Zulu']
	Codes = [UniversalCode, 'ab', 'aa', 'af', 'ak', 'sq', 'am', 'ar', 'an', 'hy', 'as', 'av', 'ae', 'ay', 'az', 'bm', 'ba', 'eu', 'be', 'bn', 'bh', 'bi', 'nb', 'bs', 'br', 'bg', 'my', 'ca', 'ch', 'ce', 'ny', 'zh', 'cv', 'kw', 'co', 'cr', 'hr', 'cs', 'da', 'dv', 'nl', 'dz', EnglishCode, 'eo', 'et', 'ee', 'fo', 'fj', 'fi', 'fr', 'ff', 'gd', 'gl', 'lg', 'ka', 'de', 'el', 'gn', 'gu', 'ht', 'ha', 'he', 'hz', 'hi', 'ho', 'hu', 'is', 'io', 'ig', 'id', 'ia', 'ie', 'iu', 'ik', 'ga', 'it', 'ja', 'jv', 'kl', 'kn', 'kr', 'ks', 'kk', 'km', 'ki', 'rw', 'rn', 'kv', 'kg', 'ko', 'ku', 'kj', 'ky', 'lo', 'la', 'lv', 'li', 'ln', 'lt', 'lu', 'lb', 'mk', 'mg', 'ms', 'ml', 'mt', 'gv', 'mi', 'mr', 'mh', 'mn', 'na', 'nv', 'ng', 'ne', 'nd', 'se', 'no', 'ii', 'nn', 'oc', 'oj', 'or', 'om', 'os', 'pi', 'ps', 'fa', 'pl', 'pt', 'pa', 'qu', 'ro', 'rm', 'ru', 'sm', 'sg', 'sa', 'sc', 'sr', 'sn', 'sd', 'si', 'cu', 'sk', 'sl', 'so', 'nr', 'st', 'es', 'su', 'sw', 'ss', 'sv', 'tl', 'ty', 'tg', 'ta', 'tt', 'te', 'th', 'bo', 'ti', 'to', 'ts', 'tn', 'tr', 'tk', 'tw', 'uk', 'ur', 'ug', 'uz', 've', 'vi', 'vo', 'wa', 'cy', 'fy', 'wo', 'xh', 'yi', 'yo', 'za', 'zu']

	@classmethod
	def customization(self):
		return Settings.getBoolean('general.language.customization')

	@classmethod
	def settings(self, single = False):
		languages = []

		language = Settings.getString('general.language.primary')
		if not language == 'None':
			language = self.language(language)
			if language:
				if single: return language
				if not language in languages: languages.append(language)

		language = Settings.getString('general.language.secondary')
		if not language == 'None':
			language = self.language(language)
			if language:
				if single: return language
				if not language in languages: languages.append(language)

		language = Settings.getString('general.language.tertiary')
		if not language == 'None':
			language = self.language(language)
			if language:
				if single: return language
				if not language in languages: languages.append(language)

		if len(languages) == 0: languages.append(self.language(self.EnglishCode))

		if single: return languages[0]
		else: return languages

	@classmethod
	def isUniversal(self, nameOrCode):
		if nameOrCode == None: return False
		elif type(nameOrCode) is tuple: nameOrCode = nameOrCode[0]
		nameOrCode = nameOrCode.lower()
		return nameOrCode == self.UniversalCode.lower() or nameOrCode == self.UniversalName.lower()

	@classmethod
	def isEnglish(self, nameOrCode):
		if nameOrCode == None: return False
		elif type(nameOrCode) is tuple: nameOrCode = nameOrCode[0]
		nameOrCode = nameOrCode.lower()
		return nameOrCode == self.EnglishCode.lower() or nameOrCode == self.EnglishName.lower()

	@classmethod
	def languages(self):
		result = []
		for i in range(len(self.Codes)):
			result.append((self.Codes[i], self.Names[i]))
		return result

	@classmethod
	def names(self, case = CaseCapital):
		if case == self.CaseUpper:
			return [i.upper() for i in self.Names]
		elif case == self.CaseLower:
			return [i.lower() for i in self.Names]
		else:
			return self.Names

	@classmethod
	def codes(self, case = CaseLower):
		if case == self.CaseCapital:
			return [i.capitalize() for i in self.Codes]
		elif case == self.CaseUpper:
			return [i.upper() for i in self.Codes]
		else:
			return self.Codes

	@classmethod
	def language(self, nameOrCode):
		if nameOrCode == None: return None
		elif type(nameOrCode) is tuple: nameOrCode = nameOrCode[0]
		nameOrCode = nameOrCode.lower().strip()

		if self.Automatic in nameOrCode:
			return self.settings(single = True)
		elif self.Alternative in nameOrCode:
			languages = self.settings()
			for language in languages:
				if not language[0] == self.EnglishCode:
					return language
			return languages[0]

		# NB & TODO: Very bad, but easy implementation to compares ISO 639-1 and ISO 639-2 codes. This does not work properley for languages, and a proper map for ISO 639-2 must be added.
		if isinstance(nameOrCode, basestring) and len(nameOrCode) == 3:
			if nameOrCode == 'ger':
					return self.language('de')
			else:
				code = None
				for i in range(len(self.Codes)):
					code = self.Codes[i]
					if nameOrCode.startswith(code) or (code[0] == nameOrCode[0] and code[1] == nameOrCode[2]):
						return (self.Codes[i], self.Names[i])

		for i in range(len(self.Codes)):
			if self.Codes[i] == nameOrCode:
				return (self.Codes[i], self.Names[i])

		for i in range(len(self.Codes)):
			if self.Names[i].lower() == nameOrCode:
				return (self.Codes[i], self.Names[i])

		return None

	@classmethod
	def name(self, nameOrCode):
		if nameOrCode == None: return None
		elif type(nameOrCode) is tuple: nameOrCode = nameOrCode[0]
		nameOrCode = nameOrCode.lower().strip()

		if self.Automatic in nameOrCode:
			return self.settings(single = True)[1]
		elif self.Alternative in nameOrCode:
			languages = self.settings()
			for language in languages:
				if not language[0] == self.EnglishCode:
					return language[1]
			return languages[0][1]

		# NB & TODO: Very bad, but easy implementation to compares ISO 639-1 and ISO 639-2 codes. This does not work properley for languages, and a proper map for ISO 639-2 must be added.
		if isinstance(nameOrCode, basestring) and len(nameOrCode) == 3:
			if nameOrCode == 'ger':
					return self.name('de')
			else:
				code = None
				for i in range(len(self.Codes)):
					code = self.Codes[i]
					if nameOrCode.startswith(code) or (code[0] == nameOrCode[0] and code[1] == nameOrCode[2]):
						return self.Names[i]

		for i in range(len(self.Codes)):
			if self.Codes[i] == nameOrCode:
				return self.Names[i]

		for i in range(len(self.Codes)):
			if self.Names[i].lower() == nameOrCode:
				return self.Names[i]

		return None

	@classmethod
	def code(self, nameOrCode):
		if nameOrCode == None: return None
		elif type(nameOrCode) is tuple: nameOrCode = nameOrCode[0]
		nameOrCode = nameOrCode.lower().strip()

		if self.Automatic in nameOrCode:
			return self.settings(single = True)[0]
		elif self.Alternative in nameOrCode:
			languages = self.settings()
			for language in languages:
				if not language[0] == self.EnglishCode:
					return language[0]
			return languages[0][0]

		# NB & TODO: Very bad, but easy implementation to compares ISO 639-1 and ISO 639-2 codes. This does not work properley for languages, and a proper map for ISO 639-2 must be added.
		if isinstance(nameOrCode, basestring) and len(nameOrCode) == 3:
			if nameOrCode == 'ger':
					return self.code('de')
			else:
				code = None
				for i in range(len(self.Codes)):
					code = self.Codes[i]
					if nameOrCode.startswith(code) or (code[0] == nameOrCode[0] and code[1] == nameOrCode[2]):
						return self.Codes[i]

		for i in range(len(self.Names)):
			if self.Names[i].lower() == nameOrCode:
				return self.Codes[i]

		for i in range(len(self.Codes)):
			if self.Codes[i] == nameOrCode:
				return self.Codes[i]

		return None

class Hash(object):

	@classmethod
	def random(self):
		return str(uuid.uuid4().hex).upper()

	@classmethod
	def sha1(self, data):
		return hashlib.sha1(data).hexdigest().upper()

	@classmethod
	def sha256(self, data):
		return hashlib.sha256(data).hexdigest().upper()

	@classmethod
	def sha512(self, data):
		return hashlib.sha512(data).hexdigest().upper()

	@classmethod
	def md5(self, data):
		return hashlib.md5(data).hexdigest().upper()

	@classmethod
	def fileSha1(self, path):
		return hashlib.sha1(File.readNow(path)).hexdigest().upper()

	@classmethod
	def valid(self, hash, length = 40):
		return hash and len(hash) == length and bool(re.match('^[a-fA-F0-9]+', hash))

class Video(object):

	Extensions = ['mp4', 'mpg', 'mpeg', 'mp2', 'm4v', 'm2v', 'mkv', 'avi', 'flv', 'asf', '3gp', '3g2', 'wmv', 'mov', 'qt', 'webm', 'vob']

	@classmethod
	def extensions(self):
		return self.Extensions

	@classmethod
	def extensionValid(self, extension = None, path = None):
		if extension == None: extension = os.path.splitext(path)[1][1:]
		extension = extension.replace('.', '').replace(' ', '').lower()
		return extension in self.Extensions

class Audio(object):

	# Values must correspond to settings.
	StartupNone = 0
	Startup1 = 1
	Startup2 = 2
	Startup3 = 3
	Startup4 = 4
	Startup5 = 5

	@classmethod
	def startup(self, type = None):
		if type == None:
			type = Settings.getInteger('general.launch.sound')
		if type == 0 or type == None:
			return False
		else:
			path = os.path.join(System.pathResources(), 'resources', 'media', 'audio', 'startup', 'startup%d' % type, 'Gaia')
			return self.play(path = path, notPlaying = True)

	@classmethod
	def play(self, path, notPlaying = True):
		player = xbmc.Player()
		if not notPlaying or not player.isPlaying():
			player.play(path)
			return True
		else:
			return False

# Kodi's thumbnail cache
class Thumbnail(object):

	Directory = 'special://thumbnails'

	@classmethod
	def hash(self, path):
		try:
			path = path.lower()
			bs = bytearray(path.encode())
			crc = 0xffffffff
			for b in bs:
				crc = crc ^ (b << 24)
				for i in range(8):
					if crc & 0x80000000:
						crc = (crc << 1) ^ 0x04C11DB7
					else:
						crc = crc << 1
				crc = crc & 0xFFFFFFFF
			return '%08x' % crc
		except:
			return None

	@classmethod
	def delete(self, path):
		name = self.hash(path)
		if name == None:
			return None
		name += '.jpg'
		file = None
		directories, files = File.listDirectory(self.Directory)
		for f in files:
			if f == name:
				file = os.path.join(self.Directory, f)
				break
		for d in directories:
			dir = os.path.join(self.Directory, d)
			directories2, files2 = File.listDirectory(dir)
			for f in files2:
				if f == name:
					file = os.path.join(dir, f)
					break
			if not file == None:
				break
		if not file == None:
			File.delete(file, force = True)

class Selection(object):

	# Must be integers
	TypeExclude = -1
	TypeUndefined = 0
	TypeInclude = 1

class Kids(object):

	Restriction7 = 0
	Restriction13 = 1
	Restriction16 = 2
	Restriction18 = 3

	@classmethod
	def enabled(self):
		return Settings.getBoolean('general.kids.enabled')

	@classmethod
	def restriction(self):
		return Settings.getInteger('general.kids.restriction')

	@classmethod
	def password(self, hash = True):
		password = Settings.getString('general.kids.password')
		if hash and not(password == None or password == ''): password = Hash.md5(password).lower()
		return password

	@classmethod
	def passwordEmpty(self):
		password = self.password()
		return password == None or password == ''

	@classmethod
	def verify(self, password):
		return not self.enabled() or self.passwordEmpty() or password.lower() == self.password().lower()

	@classmethod
	def locked(self):
		return Settings.getBoolean('general.kids.locked')

	@classmethod
	def lockable(self):
		return not self.passwordEmpty() and not self.locked()

	@classmethod
	def unlockable(self):
		return not self.passwordEmpty() and self.locked()

	@classmethod
	def lock(self):
		if self.locked():
			return True
		else:
			from resources.lib.extensions import interface # Circular import.
			Settings.set('general.kids.locked', True)
			System.restart() # Kodi still keeps the old menus in cache (when going BACK). Clear them by restarting the addon.
			interface.Dialog.confirm(title = 33438, message = 33445)
			return True

	@classmethod
	def unlock(self, internal = False):
		if self.locked():
			from resources.lib.extensions import interface # Circular import.
			password = self.password()
			if password and not password == '':
				match = interface.Dialog.inputPassword(title = 33440, verify = password)
				if not match:
					interface.Dialog.confirm(title = 33440, message = 33441)
					return False
			Settings.set('general.kids.locked', False)
			System.restart() # Kodi still keeps the old menus in cache (when going BACK). Clear them by restarting the addon.
			if not internal:
				interface.Dialog.confirm(title = 33438, message = 33444)
			return True
		else:
			return True

	@classmethod
	def allowed(self, certificate):
		if certificate == None or certificate == '':
			return False

		certificate = certificate.lower().replace(' ', '').replace('-', '').replace('_', '').strip()
		restriction = self.restriction()

		if (certificate  == 'g' or certificate  == 'tvy'):
			return True
		elif (certificate == 'pg' or certificate == 'tvy7') and restriction >= 1:
			return True
		elif (certificate == 'pg13' or certificate == 'tvpg') and restriction >= 2:
			return True
		elif (certificate == 'r' or certificate == 'tv14') and restriction >= 3:
			return True
		return False

class Converter(object):

	Base64 = 'base64'

	@classmethod
	def roman(self, number):
		number = number.lower().replace(' ', '')
		numerals = {'i' : 1, 'v' : 5, 'x' : 10, 'l' : 50, 'c' : 100, 'd' : 500, 'm' : 1000}
		result = 0
		for i, c in enumerate(number):
			if not c in numerals:
				return None
			elif (i + 1) == len(number) or numerals[c] > numerals[number[i + 1]]:
				result += numerals[c]
			else:
				result -= numerals[c]
		return result

	@classmethod
	def boolean(self, value, string = False):
		if string:
			return 'true' if value else 'false'
		else:
			if value == True or value == False:
				return value
			elif isinstance(value, numbers.Number):
				return value > 0
			elif isinstance(value, basestring):
				value = value.lower()
				return value == 'true' or value == 'yes' or value == 't' or value == 'y' or value == '1'
			else:
				return False

	@classmethod
	def dictionary(self, jsonData):
		try:
			if jsonData == None:
				return None

			jsonData = json.loads(jsonData)

			# In case the quotes in the string were escaped, causing the first json.loads to return a unicode string.
			try: jsonData = json.loads(jsonData)
			except: pass

			return jsonData
		except:
			return None

	@classmethod
	def unicode(self, string, umlaut = False):
		try:
			if string == None:
				return string
			if umlaut:
				try: string = string.replace(unichr(196), 'AE').replace(unichr(203), 'EE').replace(unichr(207), 'IE').replace(unichr(214), 'OE').replace(unichr(220), 'UE').replace(unichr(228), 'ae').replace(unichr(235), 'ee').replace(unichr(239), 'ie').replace(unichr(246), 'oe').replace(unichr(252), 'ue')
				except: pass
			return unidecode(string.decode('utf-8'))
		except:
			try: return string.encode('ascii', 'ignore')
			except: return string

	@classmethod
	def base64From(self, data, iterations = 1):
		data = str(data)
		for i in range(iterations):
			data = data.decode(self.Base64)
		return data

	@classmethod
	def base64To(self, data, iterations = 1):
		data = str(data)
		for i in range(iterations):
			data = data.encode(self.Base64).replace('\n', '')
		return data

	@classmethod
	def jsonFrom(self, data):
		try: return json.loads(data)
		except: return None

	@classmethod
	def jsonTo(self, data):
		try: return json.dumps(data)
		except: return None

	@classmethod
	def serialize(self, data):
		try:
			import pickle
			return pickle.dumps(data)
		except:
			return None

	@classmethod
	def unserialize(self, data):
		try:
			import pickle
			return pickle.loads(data)
		except:
			return None

	# Convert HTML entities to ASCII.
	@classmethod
	def htmlFrom(self, data):
		try:
			try: from HTMLParser import HTMLParser
			except: from html.parser import HTMLParser
			return str(HTMLParser().unescape(data))
		except:
			return data

class Cache(object):

	# Example: cacheNamed(functionPointer, 30, val1, val2)
	# If timeout <= 0 or None, will force new retrieval.
	@classmethod
	def cache(self, function, timeout, *arguments):
		from resources.lib.modules import cache
		return cache.get(function, timeout, *arguments)

	# Example: cacheNamed(functionPointer, 30, par1 = val1, par2 = val2)
	# If timeout <= 0 or None, will force new retrieval.
	# NB: DO NOT USE THIS FUNCTION. It seems that this function often does not work. Sometimes it does. Rather cache() and pass the function manually like in debrid.Premiumize.
	'''@classmethod
	def cacheNamed(self, function, timeout, **arguments):
		def cacheNamed(**arguments):
			return function(**arguments)
		return self.cache(cacheNamed, timeout, dict(**arguments)) # arguments must be converted to dict, since cache.get only takes unnamed parameters.
	'''

class Logger(object):

	TypeNotice = xbmc.LOGNOTICE
	TypeError = xbmc.LOGERROR
	TypeSevere = xbmc.LOGSEVERE
	TypeFatal = xbmc.LOGFATAL
	TypeDefault = TypeNotice

	@classmethod
	def log(self, message, message2 = None, message3 = None, message4 = None, message5 = None, name = True, parameters = None, level = TypeDefault):
		divider = ' '
		message = str(message)
		if message2: message += divider + str(message2)
		if message3: message += divider + str(message3)
		if message4: message += divider + str(message4)
		if message5: message += divider + str(message5)
		if name:
			nameValue = System.name().upper()
			if not name == True:
				nameValue += ' ' + name
			nameValue += ' ' + System.version()
			if parameters:
				nameValue += ' ['
				if isinstance(parameters, basestring):
					nameValue += parameters
				else:
					nameValue += ', '.join([str(parameter) for parameter in parameters])
				nameValue += ']'
			nameValue += ': '
			message = nameValue + message
		xbmc.log(message, level)

	@classmethod
	def error(self, message = None, exception = True):
		if exception:
			type, value, traceback = sys.exc_info()
			filename = traceback.tb_frame.f_code.co_filename
			linenumber = traceback.tb_lineno
			name = traceback.tb_frame.f_code.co_name
			errortype = type.__name__
			errormessage = value.message
			if message:
				message += ' -> '
			else:
				message = ''
			message += str(errortype) + ' -> ' + str(errormessage)
			parameters = [filename, linenumber, name]
		else:
			parameters = None
		self.log(message, name = 'ERROR', parameters = parameters, level = self.TypeError)

	@classmethod
	def errorCustom(self, message):
		self.log(message, name = 'ERROR', level = self.TypeError)

class File(object):

	PrefixSpecial = 'special://'
	PrefixSamba = 'smb://'

	DirectoryHome = PrefixSpecial + 'home'
	DirectoryTemporary = PrefixSpecial + 'temp'

	@classmethod
	def translate(self, path):
		if path.startswith(self.PrefixSpecial):
			path = xbmc.translatePath(path)
		return path

	@classmethod
	def name(self, path):
		name = os.path.basename(os.path.splitext(path)[0])
		if name == '': name = None
		return name

	@classmethod
	def makeDirectory(self, path):
		return xbmcvfs.mkdirs(path)

	@classmethod
	def translatePath(self, path):
		return xbmc.translatePath(path)

	@classmethod
	def legalPath(self, path):
		return xbmc.makeLegalFilename(path)

	@classmethod
	def joinPath(self, path, *paths):
		return os.path.join(path, *paths)

	@classmethod
	def exists(self, path): # Directory must end with slash
		# Do not use xbmcvfs.exists, since it returns true for http links.
		if path.startswith('http:') or path.startswith('https:') or path.startswith('ftp:') or path.startswith('ftps:'):
			return os.path.exists(path)
		else:
			return xbmcvfs.exists(path)

	@classmethod
	def existsDirectory(self, path):
		if not path.endswith('/') and not path.endswith('\\'):
			path += '/'
		return xbmcvfs.exists(path)

	# If samba file or directory.
	@classmethod
	def samba(self, path):
		return path.startswith(self.PrefixSamba)

	# If network (samba or any other non-local supported Kodi path) file or directory.
	# Path must point to a valid file or directory.
	@classmethod
	def network(self, path):
		return self.samba(path) or (self.exists(path) and not os.path.exists(path))

	@classmethod
	def delete(self, path, force = True):
		try:
			# For samba paths
			try:
				if self.exists(path):
					xbmcvfs.delete(path)
			except:
				pass

			# All with force
			try:
				if self.exists(path):
					if force: os.chmod(path, stat.S_IWRITE) # Remove read only.
					return os.remove(path) # xbmcvfs often has problems deleting files
			except:
				pass

			return not self.exists(path)
		except:
			return False

	@classmethod
	def deleteDirectory(self, path, force = True):
		try:
			# For samba paths
			try:
				if self.existsDirectory(path):
					xbmcvfs.rmdir(path)
					if not self.existsDirectory(path):
						return True
			except:
				pass

			try:
				if self.existsDirectory(path):
					shutil.rmtree(path)
					if not self.existsDirectory(path):
						return True
			except:
				pass

			# All with force
			try:
				if self.existsDirectory(path):
					if force: os.chmod(path, stat.S_IWRITE) # Remove read only.
					os.rmdir(path)
					if not self.existsDirectory(path):
						return True
			except:
				pass

			# Try individual delete
			try:
				if self.existsDirectory(path):
					directories, files = self.listDirectory(path)
					for i in files:
						self.delete(os.path.join(path, i), force = force)
					for i in directories:
						self.deleteDirectory(os.path.join(path, i), force = force)
					try: xbmcvfs.rmdir(path)
					except: pass
					try: shutil.rmtree(path)
					except: pass
					try: os.rmdir(path)
					except: pass
			except:
				pass

			return not self.existsDirectory(path)
		except:
			Logger.error()
			return False

	@classmethod
	def size(self, path):
		return xbmcvfs.File(path).size()

	@classmethod
	def create(self, path):
		return self.writeNow(path, '')

	@classmethod
	def readNow(self, path):
		file = xbmcvfs.File(path)
		result = file.read()
		file.close()
		return result

	@classmethod
	def writeNow(self, path, value):
		file = xbmcvfs.File(path, 'w')
		result = file.write(str(value))
		file.close()
		return result

	# replaceNow(path, 'from', 'to')
	# replaceNow(path, [['from1', 'to1'], ['from2', 'to2']])
	@classmethod
	def replaceNow(self, path, valueFrom, valueTo = None):
		data = self.readNow(path)
		if not isinstance(valueFrom, list):
			valueFrom = [[valueFrom, valueTo]]
		for replacement in valueFrom:
			data = data.replace(replacement[0], replacement[1])
		self.writeNow(path, data)

	# Returns: directories, files
	@classmethod
	def listDirectory(self, path, absolute = False):
		directories, files = xbmcvfs.listdir(path)
		if absolute:
			for i in range(len(files)):
				files[i] = File.joinPath(path, files[i])
			for i in range(len(directories)):
				directories[i] = File.joinPath(path, directories[i])
		return directories, files

	@classmethod
	def copy(self, pathFrom, pathTo, bytes = None, overwrite = False):
		if overwrite and xbmcvfs.exists(pathTo):
			try: xbmcvfs.delete(pathTo)
			except: pass
		if bytes == None:
			return xbmcvfs.copy(pathFrom, pathTo)
		else:
			try:
				fileFrom = xbmcvfs.File(pathFrom)
				fileTo = xbmcvfs.File(pathTo, 'w')
				chunk = min(bytes, 1048576) # 1 MB
				while bytes > 0:
					size = min(bytes, chunk)
					fileTo.write(fileFrom.read(size))
					bytes -= size
				fileFrom.close()
				fileTo.close()
				return True
			except:
				return False

	@classmethod
	def copyDirectory(self, pathFrom, pathTo, overwrite = True):
		if not pathFrom.endswith('/') and not pathFrom.endswith('\\'):
			pathFrom += '/'
		if not pathTo.endswith('/') and not pathTo.endswith('\\'):
			pathTo += '/'

		# NB: Always check if directory exists before copying it on Windows.
		# If the source directory does not exist, Windows will simply copy the entire C: drive.
		if self.existsDirectory(pathFrom):
			try:
				if overwrite: File.deleteDirectory(pathTo)
				shutil.copytree(pathFrom, pathTo)
				return True
			except:
				return False
		else:
			return False

	@classmethod
	def renameDirectory(self, pathFrom, pathTo):
		if not pathFrom.endswith('/') and not pathFrom.endswith('\\'):
			pathFrom += '/'
		if not pathTo.endswith('/') and not pathTo.endswith('\\'):
			pathTo += '/'
		os.rename(pathFrom, pathTo)

	# Not for samba paths
	@classmethod
	def move(self, pathFrom, pathTo, replace = True):
		if pathFrom == pathTo:
			return False
		if replace:
			try: os.remove(pathTo)
			except: pass
		try:
			shutil.move(pathFrom, pathTo)
			return True
		except:
			return False

class System(object):

	Observe = 'gaiaobserve'
	Launch = 'gaialaunch'

	StartupScript = 'special://masterprofile/autoexec.py'

	PluginPrefix = 'plugin://'

	GaiaAddon = 'plugin.video.gaia'
	GaiaArtwork = 'script.gaia.artwork'
	GaiaBinaries = 'script.gaia.binaries'
	GaiaResources = 'script.gaia.resources'
	GaiaIcons = 'script.gaia.icons'
	GaiaSkins = 'script.gaia.skins'

	@classmethod
	def handle(self):
		return int(sys.argv[1])

	@classmethod
	def sleep(self, milliseconds):
		time.sleep(int(milliseconds / 1000.0))

	@classmethod
	def osLinux(self):
		return sys.platform == 'linux' or sys.platform == 'linux2'

	# If the developers option is enabled.
	@classmethod
	def developers(self):
		return Settings.getString('general.access.code') == Converter.base64From('b3BlbnNlc2FtZQ==')

	@classmethod
	def developersCode(self):
		return Converter.base64From('b3BlbnNlc2FtZQ==')

	@classmethod
	def obfuscate(self, data, iterations = 3, inverse = True):
		if inverse:
			for i in range(iterations):
				data = Converter.base64From(data)[::-1]
		else:
			for i in range(iterations):
				data = Converter.base64To(data[::-1])
		return data

	# Simulated restart of the addon.
	@classmethod
	def restart(self, sleep = True):
		System.execute('Container.Update(path,replace)')
		System.execute('ActivateWindow(Home)')
		System.execute('RunAddon(%s)' % self.GaiaAddon)
		if sleep: time.sleep(2)

	@classmethod
	def exit(self):
		System.execute('Container.Update(path,replace)')
		System.execute('ActivateWindow(Home)')

	@classmethod
	def aborted(self):
		return xbmc.abortRequested

	@classmethod
	def visible(self, item):
		return xbmc.getCondVisibility(item)

	@classmethod
	def versionKodi(self, full = False):
		version = self.infoLabel('System.BuildVersion')
		if not full:
			try: version = float(re.search('^\d+\.?\d+', version).group(0))
			except: pass
		return version

	@classmethod
	def home(self):
		System.execute('ActivateWindow(Home)')

	@classmethod
	def windowPropertyGet(self, property, id = 10000):
		return xbmcgui.Window(id).getProperty(property)

	@classmethod
	def windowPropertySet(self, property, value, id = 10000):
		return xbmcgui.Window(id).setProperty(property, str(value))

	@classmethod
	def path(self, id = GaiaAddon):
		try: addon = xbmcaddon.Addon(id)
		except: addon = None
		if addon == None:
			return ''
		else:
			return File.translatePath(addon.getAddonInfo('path').decode('utf-8'))

	@classmethod
	def pathArtwork(self):
		return self.path(self.GaiaArtwork)

	@classmethod
	def pathBinaries(self):
		return self.path(self.GaiaBinaries)

	@classmethod
	def pathIcons(self):
		return self.path(self.GaiaIcons)

	@classmethod
	def pathResources(self):
		return self.path(self.GaiaResources)

	@classmethod
	def pathSkins(self):
		return self.path(self.GaiaSkins)

	# OS user home directory
	@classmethod
	def pathHome(self):
		try: return os.path.expanduser('~')
		except: return None

	@classmethod
	def addon(self, value):
		return xbmcaddon.Addon(self.GaiaAddon).getAddonInfo(value)

	@classmethod
	def plugin(self, id = GaiaAddon):
		return self.PluginPrefix + str(id)

	@classmethod
	def pluginCommand(self, action = None, parameters = None, id = GaiaAddon, duplicates = False, run = True):
		if parameters == None:
			parameters = {}
		if not action == None:
			parameters['action'] = action
		parameters = urllib.urlencode(parameters, doseq = duplicates)
		command = '%s?%s' % (self.plugin(id = id), parameters)
		if run: command = 'RunPlugin(%s)' % command
		return command

	@classmethod
	def id(self, id = GaiaAddon):
		return xbmcaddon.Addon(id).getAddonInfo('id')

	@classmethod
	def name(self, id = GaiaAddon):
		return xbmcaddon.Addon(id).getAddonInfo('name')

	@classmethod
	def author(self, id = GaiaAddon):
		return xbmcaddon.Addon(id).getAddonInfo('author')

	@classmethod
	def version(self, id = GaiaAddon):
		return xbmcaddon.Addon(id).getAddonInfo('version')

	@classmethod
	def profile(self, id = GaiaAddon):
		return File.translatePath(xbmcaddon.Addon(id).getAddonInfo('profile').decode('utf-8'))

	@classmethod
	def description(self, id = GaiaAddon):
		return xbmcaddon.Addon(id).getAddonInfo('description')

	@classmethod
	def disclaimer(self, id = GaiaAddon):
		return xbmcaddon.Addon(id).getAddonInfo('disclaimer')

	@classmethod
	def infoLabel(self, value):
		return xbmc.getInfoLabel(value)

	# Checks if an addon is installed
	@classmethod
	def installed(self, id = GaiaAddon):
		try:
			addon = xbmcaddon.Addon(id)
			id = addon.getAddonInfo('id')
			return not id == None and not id == ''
		except:
			return False

	@classmethod
	def execute(self, command):
		return xbmc.executebuiltin(command)

	@classmethod
	def executeScript(self, script, parameters = []):
		command = 'RunScript(' + script
		for parameter in parameters:
			command += ',' + str(parameter)
		command += ')'
		return self.execute(command)

	@classmethod
	def stopScript(self, script):
		return self.execute('StopScript(%s)' % script)

	# action can be passed manually, or as a value in the parameters dictionary.
	@classmethod
	def executePlugin(self, action = None, parameters = {}):
		if action: parameters['action'] = action
		if not parameters == None and not parameters == '' and not parameters == {}:
			if not isinstance(parameters, basestring):
				parameters = urllib.urlencode(parameters)
			if not parameters.startswith('?'):
				parameters = '?' + parameters
		else:
			parameters = ''
		return self.execute('RunPlugin(%s%s/%s)' % (self.PluginPrefix, self.GaiaAddon, parameters))

	@classmethod
	def executeJson(self, query):
		return xbmc.executeJSONRPC(query)

	# sleep for n seconds. Sometimes causes the new window not to show (only in the background). Sleeping seems to solve the problem.
	@classmethod
	def window(self, action = None, parameters = {}, command = None, sleep = None):
		if command == None:
			if action: parameters['action'] = action
			if not parameters == None and not parameters == '' and not parameters == {}:
				if not isinstance(parameters, basestring):
					parameters = urllib.urlencode(parameters)
				if not parameters.startswith('?'):
					parameters = '?' + parameters
			else:
				parameters = ''
			command = '%s%s/%s' % (self.PluginPrefix, self.GaiaAddon, parameters)
		result = System.execute('ActivateWindow(10025,%s,return)' % command)
		if sleep: time.sleep(sleep)
		return result

	@classmethod
	def temporary(self, directory = None, file = None, gaia = True, make = True, clear = False):
		path = File.translatePath('special://temp/')
		if gaia: path = os.path.join(path, System.name().lower())
		if directory: path = os.path.join(path, directory)
		if clear: File.deleteDirectory(path, force = True)
		if make: File.makeDirectory(path)
		if file: path = os.path.join(path, file)
		return path

	@classmethod
	def temporaryRandom(self, directory = None, extension = 'dat', gaia = True, make = True, clear = False):
		if extension and not extension == '' and not extension.startswith('.'):
			extension = '.' + extension
		file = Hash.random() + extension
		path = self.temporary(directory = directory, file = file, gaia = gaia, make = make, clear = clear)
		while File.exists(path):
			file = Hash.random() + extension
			path = self.temporary(directory = directory, file = file, gaia = gaia, make = make, clear = clear)
		return path

	@classmethod
	def temporaryClear(self):
		return File.deleteDirectory(self.temporary(make = False))

	@classmethod
	def openLink(self, link, popup = True, popupForce = False, front = True):
		from resources.lib.extensions import interface # Circular import.
		interface.Loader.show() # Needs some time to load. Show busy.
		try:
			success = False
			if sys.platform == 'darwin': # OS X
				try:
					subprocess.Popen(['open', link])
					success = True
				except: pass
			if not success:
				webbrowser.open(link, autoraise = front, new = 2) # new = 2 opens new tab.
		except:
			popupForce = True
		if popupForce:
			from resources.lib.extensions import clipboard
			clipboard.Clipboard.copyLink(link, popup)
		interface.Loader.hide()

	@classmethod
	def _observe(self):
		xbmc.Monitor().waitForAbort()
		os._exit(1)

	@classmethod
	def observe(self):
		# Observes when Kodi closes and exits.
		# Reduces the chances the Kodi freezes on exit (might still take a few seconds).
		value = xbmcgui.Window(10000).getProperty(self.Observe)
		first = not value or value == ''
		if first:
			xbmcgui.Window(10000).setProperty(self.Observe, str(Time.timestamp()))
			thread = threading.Thread(target = self._observe)
			thread.start()

	@classmethod
	def launchAddon(self):
		return System.execute('RunAddon(%s)' % self.id())

	@classmethod
	def launchInitialize(self):
		xbmcgui.Window(10000).setProperty(self.Launch, str(Time.timestamp()))

	@classmethod
	def launchUninitialize(self):
		xbmcgui.Window(10000).setProperty(self.Launch, '')

	@classmethod
	def launch(self):
		thread = threading.Thread(target = self._launch)
		thread.start()

	@classmethod
	def _launch(self):
		value = xbmcgui.Window(10000).getProperty(self.Launch)
		first = not value or value == '' # First launch
		try: idle = (Time.timestamp() - int(value)) > 10800 # If the last launch was more than 3 hours ago.
		except: idle = True
		if first or idle:
			from resources.lib.extensions import interface
			from resources.lib.extensions import debrid
			from resources.lib.extensions import settings
			from resources.lib.extensions import provider
			from resources.lib.extensions import library
			from resources.lib.extensions import vpn
			from resources.lib.modules import control

			version = Settings.getString('internal.version')
			try: versionOld = int(version.replace('.', ''))
			except: versionOld = 0
			if not versionOld: versionOld = 0
			try: versionNew = int(self.version().replace('.', ''))
			except: versionNew = 0
			if not versionNew: versionNew = 0
			Settings.set('internal.version', self.version())

			# Backup - Import
			Backup.automaticImport()

			# Splash
			#interface.Splash.popup()

			# Lightpack
			Lightpack().launch(execution = Lightpack.ExecutionGaia)

			# Clear Temporary
			System.temporaryClear()

			# Sound
			Audio.startup()

			# Initial Launch
			self.launchInitial()

			# Providers
			provider.Provider.launch()

			# Local Library Update
			library.Library.service(gaia = True)

			# Legal Disclaimer
			if not interface.Legal.launchInitial(exit = False):
				self.launchUninitialize()
				System.exit()
				return False

			# Initial Launch
			wizard = settings.Wizard().launchInitial()

			'''
			if versionOld < 300 and versionNew >= 300:
				interface.Dialog.page('[COLOR FFA0C12C][B]WELCOME TO GAIA 3. [/B][/COLOR][CR][CR]The new version has many new features and bug fixes. Due to the many changes, we suggest to reset your Gaia settings. Alternatively, your old settings will still work, but the interface layout will look weird. If you decide to use your old settings, change the [I]Stream Layout[/I] options under the [I]Interface[/I] settings to [I]Full[/I].[CR][CR]The main improvement in the new version is better scraper support. Firstly, the Incursion and Placenta scrapers should now work properly and use the settings from their respective addons. Secondly, we have finally added the Orion project.[CR][CR]We initially wanted to create Orion ourselves, but due to the heavy workload from Gaia we decided to get some help. Orion is maintained by another group of developers, and bug reports and suggestions should therefore be submitted to the Orion team and not us. Orion is an API with its own Kodi addon that can be integrated in any other addon, similar to [I]Universal Scrapers[/I]. Orion is a link indexer and caching service for torrent, usenet, and hoster links. It operates similar to [I]Alluc[/I], just with a wider variety of links and way more search features. Links from users are cached on the Orion servers, and instead of having to go through the length scraping process, you can retrieve the cached links from previous users very quickly. This is especially useful for people with slow internet, cheap devices, or those who are impatient. Note that Orion is not a debrid service and does not host any files, it simply indexes links and their corresponding metadata. Free and premium accounts are available. For more info, head over to:[CR][CR][COLOR FFA0C12C][B]https://orionoid.com[/B][/COLOR][CR][CR]Also, for those of you who disabled the [I]Settings Cache[/I] option, we highly suggest turning it back on. This setting drastically improves the performance of almost everything in Gaia. We made some changes to it, and hope it works better now. You should only disable this option if your settings constantly reset after launching Gaia.')
			'''

			# Announcements
			if not wizard:
				def announcementsShow():
					Time.sleep(3) # Wait a bit so that everything has been loaded.
					Announcements.show()
				thread = threading.Thread(target = announcementsShow)
				thread.start()

			# VPN
			vpn.Vpn().launch(vpn.Vpn.ExecutionGaia)

			# Elementum
			Elementum.connect()

			# Quasar
			Quasar.connect()

			# Scrapers
			LamScrapers.check()
			UniScrapers.check()
			NanScrapers.check()
			IncScrapers.check()
			PlaScrapers.check()

			# Intialize Premiumize
			debrid.Premiumize().initialize()

			# Clear debrid files
			debrid.Premiumize().deleteLaunch()
			debrid.OffCloud().deleteLaunch()
			debrid.RealDebrid().deleteLaunch()

			# Copy the select theme background as fanart to the root folder.
			# Ensures that the selected theme also shows outside the addon.
			# Requires first a Gaia restart (to replace the old fanart) and then a Kodi restart (to load the new fanart, since the old one was still in memory).
			fanartTo = os.path.join(System.path(), 'fanart.jpg')
			Thumbnail.delete(fanartTo) # Delete from cache
			File.delete(fanartTo) # Delete old fanart
			fanartFrom = control.addonFanart()
			if not fanartFrom == None:
				fanartTo = os.path.join(System.path(), 'fanart.jpg')
				File.copy(fanartFrom, fanartTo, overwrite = True)

			# Backup - Export
			Backup.automaticImport() # Check again, in case the initialization corrupted the settings.
			Backup.automaticExport()

			# Statistics
			# Last, in case video pops up.
			Statistics.share(wait = False)

		self.launchInitialize()

	@classmethod
	def launchInitial(self):
		if not Settings.getBoolean('internal.launch.initialzed'):
			# Check Hardware
			# Leave for now, since it is adjusted by the configurations wizard. If this is enabled again, make sure to not show it on every launch, only the first.
			'''if Hardware.slow():
				from resources.lib.extensions import interface
				if interface.Dialog.option(title = 33467, message = 33700, labelConfirm = 33011, labelDeny = 33701):
					Settings.launch()'''
			Settings.set('internal.launch.initialzed', False)

	@classmethod
	def launchAutomatic(self):
		if Settings.getBoolean('general.launch.automatic'):
			self.execute('RunAddon(plugin.video.gaia)')

	@classmethod
	def _automaticIdentifier(self, identifier):
		identifier = identifier.upper()
		return ('#[%s]' % identifier, '#[/%s]' % identifier)

	# Checks if a command is in the Kodi startup script.
	@classmethod
	def automaticContains(self, identifier):
		if xbmcvfs.exists(self.StartupScript):
			identifiers = self._automaticIdentifier(identifier)
			file = xbmcvfs.File(self.StartupScript, 'r')
			data = file.read()
			file.close()
			if identifiers[0] in data and identifiers[1] in data:
				return True
		return False

	# Inserts a command into the Kodi startup script.
	@classmethod
	def automaticInsert(self, identifier, command):
		identifiers = self._automaticIdentifier(identifier)
		data = ''
		contains = False

		if xbmcvfs.exists(self.StartupScript):
			file = xbmcvfs.File(self.StartupScript, 'r')
			data = file.read()
			file.close()
			if identifiers[0] in data and identifiers[1] in data:
				contains = True

		if contains:
			return False
		else:
			id = self.id()
			module = identifier.lower() + 'xbmc'
			command = command.replace(self.PluginPrefix, '').replace(id, '')
			while command.startswith('/') or command.startswith('?'):
				command = command[1:]
			command = self.PluginPrefix + id + '/?' + command
			content = '%s\n%s\nimport xbmc as %s\nif %s.getCondVisibility("System.HasAddon(%s)") == 1: %s.executebuiltin("RunPlugin(%s)")\n%s' % (data, identifiers[0], module, module, id, module, command, identifiers[1])
			file = xbmcvfs.File(self.StartupScript, 'w')
			file.write(content)
			file.close()
			return True

	# Removes a command from the Kodi startup script.
	@classmethod
	def automaticRemove(self, identifier):
		identifiers = self._automaticIdentifier(identifier)
		data = ''
		contains = False
		indexStart = 0
		indexEnd = 0
		if xbmcvfs.exists(self.StartupScript):
			file = xbmcvfs.File(self.StartupScript, 'r')
			data = file.read()
			file.close()
			if data and not data == '':
				data += '\n'
				indexStart = data.find(identifiers[0])
				if indexStart >= 0:
					indexEnd = data.find(identifiers[1]) + len(identifiers[1])
					contains = True

		if contains:
			data = data[:indexStart] + data[indexEnd:]
			file = xbmcvfs.File(self.StartupScript, 'w')
			file.write(data)
			file.close()
			return True
		else:
			return False

	#	[
	#		['title' : 'Category 1', 'items' : [{'title' : 'Name 1', 'value' : 'Value 1', 'link' : True}, {'title' : 'Name 2', 'value' : 'Value 2'}]]
	#		['title' : 'Category 2', 'items' : [{'title' : 'Name 3', 'value' : 'Value 3', 'link' : False}, {'title' : 'Name 4', 'value' : 'Value 4'}]]
	#	]
	@classmethod
	def information(self):
		from resources.lib.extensions import convert

		items = []

		# System
		system = self.informationSystem()
		subitems = []
		subitems.append({'title' : 'Name', 'value' : system['name']})
		subitems.append({'title' : 'Version', 'value' : system['version']})
		if not system['codename'] == None: subitems.append({'title' : 'Codename', 'value' : system['codename']})
		subitems.append({'title' : 'Family', 'value' : system['family']})
		subitems.append({'title' : 'Architecture', 'value' : system['architecture']})
		subitems.append({'title' : 'Processors', 'value' : str(Hardware.processors())})
		subitems.append({'title' : 'Memory', 'value' : convert.ConverterSize(value =  Hardware.memory()).stringOptimal()})
		items.append({'title' : 'System', 'items' : subitems})

		# Python
		system = self.informationPython()
		subitems = []
		subitems.append({'title' : 'Version', 'value' : system['version']})
		subitems.append({'title' : 'Implementation', 'value' : system['implementation']})
		subitems.append({'title' : 'Architecture', 'value' : system['architecture']})
		items.append({'title' : 'Python', 'items' : subitems})

		# Kodi
		system = self.informationKodi()
		subitems = []
		subitems.append({'title' : 'Name', 'value' : system['name']})
		subitems.append({'title' : 'Version', 'value' : system['version']})
		items.append({'title' : 'Kodi', 'items' : subitems})

		# Addon
		system = self.informationAddon()
		subitems = []
		subitems.append({'title' : 'Name', 'value' : system['name']})
		subitems.append({'title' : 'Author', 'value' : system['author']})
		subitems.append({'title' : 'Version', 'value' : system['version']})
		items.append({'title' : 'Addon', 'items' : subitems})

		from resources.lib.extensions import interface
		return interface.Dialog.information(title = 33467, items = items)

	@classmethod
	def informationSystem(self):
		system = platform.system().capitalize()
		version = platform.release().capitalize()

		distribution = platform.dist()

		try:
			name = distribution[0].replace('"', '') # "elementary"
			if name == 'elementary os': name = 'elementary'
		except:
			name = ''

		distributionHas = not distribution == None and not distribution[0] == None and not distribution[0] == ''
		distributionName = name.capitalize() if distributionHas else None
		distributionVersion = distribution[1].capitalize() if distributionHas and not distribution[1] == None and not distribution[1] == '' else None
		distributionCodename = distribution[2].capitalize() if distributionHas and not distribution[2] == None and not distribution[2] == '' else None

		# Manually check for Android
		if system == 'Linux' and distributionName == None:
			id = None
			if 'ANDROID_ARGUMENT' in os.environ:
				id = True
			if id == None or id == '':
				try: id = subprocess.Popen('getprop ril.serialnumber'.split(), stdout = subprocess.PIPE).communicate()[0]
				except: pass
			if id == None or id == '':
				try: id = subprocess.Popen('getprop ro.serialno'.split(), stdout = subprocess.PIPE).communicate()[0]
				except: pass
			if id == None or id == '':
				try: id = subprocess.Popen('getprop sys.serialnumber'.split(), stdout = subprocess.PIPE).communicate()[0]
				except: pass
			if id == None or id == '':
				try: id = subprocess.Popen('getprop gsm.sn1'.split(), stdout = subprocess.PIPE).communicate()[0]
				except: pass
			if not id == None and not id == '':
				distributionName = 'Android'
				distributionHas = True

		# Structure used by Statistics.
		return {
			'family' : system,
			'name' : distributionName if distributionHas else system,
			'codename' : distributionCodename if distributionHas else None,
			'version' : distributionVersion if distributionHas else version,
			'architecture' : '64 bit' if '64' in platform.processor() else '32 bit',
		}

	@classmethod
	def informationPython(self):
		# Structure used by Statistics.
		return {
			'implementation' : platform.python_implementation(),
			'version' : platform.python_version(),
			'architecture' : '64 bit' if '64' in platform.architecture() else '32 bit',
		}

	@classmethod
	def informationKodi(self):
		spmc = 'spmc' in xbmc.translatePath('special://xbmc').lower() or 'spmc' in xbmc.translatePath('special://logpath').lower()
		version = xbmc.getInfoLabel('System.BuildVersion')
		index = version.find(' ')
		if index >= 0: version = version[:index].strip()
		# Structure used by Statistics.
		return {
			'name' : 'SPMC' if spmc else 'Kodi',
			'version' : version,
		}

	@classmethod
	def informationAddon(self):
		return {
			'name' : self.name(),
			'author' : self.author(),
			'version' : self.version(),
		}

	@classmethod
	def manager(self):
		self.execute('ActivateWindow(systeminfo)')

	@classmethod
	def clean(self, confirm = True):
		from resources.lib.extensions import interface
		if confirm:
			choice = interface.Dialog.option(title = 33468, message = 33469)
		else:
			choice = True
		if choice:
			path = File.translate(File.PrefixSpecial + 'masterprofile/addon_data/' + System.id())
			File.deleteDirectory(path = path, force = True)
			self.temporaryClear()
			if File.existsDirectory(path):
				interface.Dialog.confirm(title = 33468, message = 33916)

SettingsCache = None

class Settings(object):

	Database = 'settings'

	SettingsId = 10140

	ParameterDefault = 'default'
	ParameterValue = 'value'
	ParameterVisible = 'visible'

	CategoryGeneral = 0
	CategoryInterface = 1
	CategoryScraping = 2
	CategoryProviders = 3
	CategoryAccounts = 4
	CategoryStreaming = 5
	CategoryManual = 6
	CategoryAutomation = 7
	CategoryDownloads = 8
	CategorySubtitles = 9
	CategoryLibrary = 10
	CategoryLightpack = 11

	CacheEnabled = False
	CacheMainData = None
	CacheMainValues = None
	CacheUserData = None
	CacheUserValues = None

	@classmethod
	def _database(self):
		from resources.lib.extensions import database
		return database.Database.instance(self.Database, default = File.joinPath(System.path(), 'resources'))

	@classmethod
	def pathAddon(self):
		return File.joinPath(System.path(), 'resources', 'settings.xml')

	@classmethod
	def pathProfile(self):
		return File.joinPath(System.profile(), 'settings.xml')

	@classmethod
	def cache(self):
		# Ensures that the data always stays in memory.
		# Otherwise the "static variables" are deleted if there is no more reference to the Settings class.
		global SettingsCache
		if SettingsCache == None:
			SettingsCache = Settings()
			SettingsCache.CacheEnabled = Converter.boolean(xbmcaddon.Addon(System.GaiaAddon).getSetting('general.settings.cache'))
			SettingsCache.CacheMainValues = {}
			SettingsCache.CacheUserValues = {}
		return SettingsCache

	@classmethod
	def cacheClear(self):
		global SettingsCache
		SettingsCache = None
		self.CacheEnabled = False
		self.CacheMainData = None
		self.CacheMainValues = None
		self.CacheUserData = None
		self.CacheUserValues = None

	@classmethod
	def cacheEnabled(self):
		return self.cache().CacheEnabled

	@classmethod
	def cacheGet(self, id, raw, database = False):
		instance = self.cache()
		if raw:
			if instance.CacheMainData == None:
				instance.CacheMainData = File.readNow(self.pathAddon())
			data = instance.CacheMainData
			values = instance.CacheMainValues
			parameter = self.ParameterDefault
		else:
			if instance.CacheUserData == None:
				instance.CacheUserData = File.readNow(self.pathProfile())
			data = instance.CacheUserData
			values = instance.CacheUserValues
			parameter = self.ParameterValue

		if id in values: # Already looked-up previously.
			return values[id]
		elif database:
			result = self._getDatabase(id = id)
			values[id] = result
			return result
		else:
			result = self.raw(id = id, parameter = parameter, data = data)
			if result == None: # Not in the userdata settings yet. Fallback to normal Kodi lookup.
				result = xbmcaddon.Addon(System.GaiaAddon).getSetting(id)
			values[id] = result
			return result

	@classmethod
	def cacheSet(self, id, value):
		self.cache().CacheUserValues[id] = value

	@classmethod
	def launch(self, category = None, section = None):
		from resources.lib.extensions import interface
		interface.Loader.hide()
		System.execute('Addon.OpenSettings(%s)' % System.id())
		if not category == None:
			System.execute('SetFocus(%i)' % (int(category) + 100))
		if not section == None:
			System.execute('SetFocus(%i)' % (int(section) + 200))

	@classmethod
	def visible(self):
		from resources.lib.extensions import interface
		return interface.Dialog.dialogVisible(self.SettingsId)

	@classmethod
	def data(self):
		data = None
		path = File.joinPath(System.path(), 'resources', 'settings.xml')
		with open(path, 'r') as file:
			data = file.read()
		return data

	@classmethod
	def set(self, id, value, cached = False):
		if isinstance(value, (dict, list, tuple)):
			from resources.lib.extensions import database
			database = self._database()
			database._insert('INSERT OR IGNORE INTO %s (id) VALUES(?);' % self.Database, parameters = (id,))
			database._update('UPDATE %s SET data = ? WHERE id = ?;' % self.Database, parameters = (Converter.jsonTo(value), id))
			if cached or self.cacheEnabled(): self.cacheSet(id = id, value = value)
		else:
			if value is True or value is False: # Use is an not ==, becasue checks type as well. Otherwise int/float might also be true.
				value = Converter.boolean(value, string = True)
			else:
				value = str(value)
			xbmcaddon.Addon(System.GaiaAddon).setSetting(id = id, value = value)
			if cached or self.cacheEnabled(): self.cacheSet(id = id, value = value)

	@classmethod
	def setMultiple(self, id, values, label = None, attribute = 'items'):
		if label == None: label = len(values)
		self.set(id, label)
		self.set(id + '.' + attribute, values)

	# wait : number of seconds to sleep after command, since it takes a while to send.
	@classmethod
	def external(self, values, wait = 0.1):
		System.executePlugin(action = 'settingsExternal', parameters = values)
		Time.sleep(wait)

	# values is a dictionary.
	@classmethod
	def externalSave(self, values):
		if 'action' in values: del values['action']
		for id, value in values.iteritems():
			self.set(id = id, value = value, external = False)

	# Retrieve the values directly from the original settings instead of the saved user XML.
	# This is for internal values/settings that have a default value. If these values change, they are not propagate to the user XML, since the value was already set from a previous version.
	@classmethod
	def raw(self, id, parameter = ParameterDefault, data = None):
		try:
			if data == None: data = self.data()
			indexStart = data.find(id)
			if indexStart < 0: return None
			indexStart = data.find('"', indexStart)
			if indexStart < 0: return None
			indexEnd = data.find('/>', indexStart)
			if indexEnd < 0: return None
			data = data[indexStart : indexEnd]
			indexStart = data.find(parameter)
			if indexStart < 0: return None
			indexStart = data.find('"', indexStart) + 1
			indexEnd = data.find('"', indexStart)
			return data[indexStart : indexEnd]
		except:
			return None

	@classmethod
	def _getDatabase(self, id):
		try:
			from resources.lib.extensions import database
			return Converter.jsonFrom(self._database()._selectValue('SELECT data FROM %s WHERE id = "%s";' % (self.Database, id)))
		except: return None

	# Kodi reads the settings file on every request, which is slow.
	# If the cached option is used, the settings XML is read manually once, and all requests are done from there, which is faster.
	@classmethod
	def get(self, id, raw = False, cached = True, database = False):
		if cached and self.cacheEnabled():
			return self.cacheGet(id = id, raw = raw, database = database)
		elif raw:
			return self.raw(id)
		elif database:
			return self._getDatabase(id)
		else:
			return xbmcaddon.Addon(System.GaiaAddon).getSetting(id)

	@classmethod
	def getString(self, id, raw = False, cached = True):
		return self.get(id = id, raw = raw, cached = cached)

	@classmethod
	def getBoolean(self, id, raw = False, cached = True):
		return Converter.boolean(self.get(id = id, raw = raw, cached = cached))

	@classmethod
	def getBool(self, id, raw = False, cached = True):
		return self.getBoolean(id = id, raw = raw, cached = cached)

	@classmethod
	def getNumber(self, id, raw = False, cached = True):
		return self.getDecimal(id = id, raw = raw, cached = cached)

	@classmethod
	def getDecimal(self, id, raw = False, cached = True):
		value = self.get(id = id, raw = raw, cached = cached)
		try: return float(value)
		except: return 0

	@classmethod
	def getFloat(self, id, raw = False, cached = True):
		return self.getDecimal(id = id, raw = raw, cached = cached)

	@classmethod
	def getInteger(self, id, raw = False, cached = True):
		value = self.get(id = id, raw = raw, cached = cached)
		try: return int(value)
		except: return 0

	@classmethod
	def getInt(self, id, raw = False, cached = True):
		return self.getInteger(id = id, raw = raw, cached = cached)

	@classmethod
	def getList(self, id, raw = False, cached = True):
		result = self.get(id = id, raw = raw, cached = cached, database = True)
		return [] if result == None or result == '' else result

	@classmethod
	def getObject(self, id, raw = False, cached = True):
		result = self.get(id = id, raw = raw, cached = cached, database = True)
		return None if result == None or result == '' else result

	@classmethod
	def customGetReleases(self, type, raw = False):
		result = self.getList(id = 'playback.%s.additional.releases.items' % type, raw = raw)
		if result == '': return None
		else: return result

	@classmethod
	def customSetReleases(self, type):
		from resources.lib.extensions import metadata
		from resources.lib.extensions import interface
		releases = sorted([key[:key.find('|')] for key, value in metadata.Metadata.DictionaryReleases.iteritems()])
		current = self.customGetReleases(type)
		preselect = []
		if current == None:
			preselect = [i for i in range(len(releases))]
		else:
			preselect = [releases.index(current[i]) for i in range(len(current))]
		items = interface.Dialog.options(title = 35164, items = releases, multiple = True, preselect = preselect)
		if not items == None:
			for i in range(len(items)):
				items[i] = releases[items[i]]
			if len(items) == 0: label = interface.Translation.string(33112)
			elif len(items) == len(releases): label = interface.Translation.string(33029)
			else: label = '%d %s' % (len(items), interface.Translation.string(35164))
			self.setMultiple(id = 'playback.%s.additional.releases' % type, values = items, label = label)
		self.launch(self.CategoryAutomation if type == 'automatic' else self.CategoryManual)

	@classmethod
	def customGetUploaders(self, type, raw = False):
		result = self.getList(id = 'playback.%s.additional.uploaders.items' % type, raw = raw)
		if result == '': return None
		else: return result

	@classmethod
	def customSetUploaders(self, type):
		from resources.lib.extensions import metadata
		from resources.lib.extensions import interface
		uploaders = sorted([key for key, value in metadata.Metadata.DictionaryUploaders.iteritems()])
		current = self.customGetUploaders(type)
		preselect = []
		if current == None:
			preselect = [i for i in range(len(uploaders))]
		else:
			preselect = [uploaders.index(current[i]) for i in range(len(current))]
		items = interface.Dialog.options(title = 35165, items = uploaders, multiple = True, preselect = preselect)
		if not items == None:
			for i in range(len(items)):
				items[i] = uploaders[items[i]]
			if len(items) == 0: label = interface.Translation.string(33112)
			elif len(items) == len(uploaders): label = interface.Translation.string(33029)
			else: label = '%d %s' % (len(items), interface.Translation.string(35165))
			self.setMultiple(id = 'playback.%s.additional.uploaders' % type, values = items, label = label)
		self.launch(self.CategoryAutomation if type == 'automatic' else self.CategoryManual)

###################################################################
# MEDIA
###################################################################

class Media(object):

	TypeNone = None
	TypeMovie = 'movie'
	TypeDocumentary = 'documentary'
	TypeShort = 'short'
	TypeShow = 'show'
	TypeSeason = 'season'
	TypeEpisode = 'episode'

	NameSeasonLong = xbmcaddon.Addon(System.GaiaAddon).getLocalizedString(32055).encode('utf-8')
	NameSeasonShort = NameSeasonLong[0].upper()
	NameEpisodeLong = xbmcaddon.Addon(System.GaiaAddon).getLocalizedString(33028).encode('utf-8')
	NameEpisodeShort = NameEpisodeLong[0].upper()

	OrderTitle = 0
	OrderTitleYear = 1
	OrderYearTitle = 2
	OrderSeason = 3
	OrderEpisode = 4
	OrderSeasonEpisode = 5
	OrderEpisodeTitle = 6
	OrderSeasonEpisodeTitle = 7

	Default = 0

	DefaultMovie = 4
	DefaultDocumentary = 4
	DefaultShort = 4
	DefaultShow = 0
	DefaultSeason = 0
	DefaultEpisode = 6

	DefaultAeonNoxMovie = 0
	DefaultAeonNoxDocumentary = 0
	DefaultAeonNoxShort = 0
	DefaultAeonNoxShow = 0
	DefaultAeonNoxSeason = 0
	DefaultAeonNoxEpisode = 0

	FormatsTitle = [
		(OrderTitle,		'%s'),
		(OrderTitleYear,	'%s %d'),
		(OrderTitleYear,	'%s. %d'),
		(OrderTitleYear,	'%s - %d'),
		(OrderTitleYear,	'%s (%d)'),
		(OrderTitleYear,	'%s [%d]'),
		(OrderYearTitle,	'%d %s'),
		(OrderYearTitle,	'%d. %s'),
		(OrderYearTitle,	'%d - %s'),
		(OrderYearTitle,	'(%d) %s'),
		(OrderYearTitle,	'[%d] %s'),
	]

	FormatsSeason = [
		(OrderSeason,	NameSeasonLong + ' %01d'),
		(OrderSeason,	NameSeasonLong + ' %02d'),
		(OrderSeason,	NameSeasonShort + ' %01d'),
		(OrderSeason,	NameSeasonShort + ' %02d'),
		(OrderSeason,	'%01d ' + NameSeasonLong),
		(OrderSeason,	'%02d ' + NameSeasonLong),
		(OrderSeason,	'%01d. ' + NameSeasonLong),
		(OrderSeason,	'%02d. ' + NameSeasonLong),
		(OrderSeason,	'%01d'),
		(OrderSeason,	'%02d'),
	]

	FormatsEpisode = [
		(OrderTitle,				'%s'),
		(OrderEpisodeTitle,			'%01d %s'),
		(OrderEpisodeTitle,			'%02d %s'),
		(OrderEpisodeTitle,			'%01d. %s'),
		(OrderEpisodeTitle,			'%02d. %s'),
		(OrderSeasonEpisodeTitle,	'%01dx%01d %s'),
		(OrderSeasonEpisodeTitle,	'%01dx%02d %s'),
		(OrderSeasonEpisodeTitle,	'%02dx%02d %s'),
		(OrderEpisodeTitle,			NameEpisodeShort + '%01d %s'),
		(OrderEpisodeTitle,			NameEpisodeShort + '%02d %s'),
		(OrderEpisodeTitle,			NameEpisodeShort + '%01d. %s'),
		(OrderEpisodeTitle,			NameEpisodeShort + '%02d. %s'),
		(OrderSeasonEpisodeTitle,	NameSeasonShort + '%01d' + NameEpisodeShort + '%01d %s'),
		(OrderSeasonEpisodeTitle,	NameSeasonShort + '%01d' + NameEpisodeShort + '%02d %s'),
		(OrderSeasonEpisodeTitle,	NameSeasonShort + '%02d' + NameEpisodeShort + '%02d %s'),
		(OrderEpisode,				'%01d'),
		(OrderEpisode,				'%02d'),
		(OrderSeasonEpisode,		'%01dx%01d'),
		(OrderSeasonEpisode,		'%01dx%02d'),
		(OrderSeasonEpisode,		'%02dx%02d'),
		(OrderEpisode,				NameEpisodeShort + '%01d'),
		(OrderEpisode,				NameEpisodeShort + '%02d'),
		(OrderSeasonEpisode,		NameSeasonShort + '%01d' + NameEpisodeShort + '%01d'),
		(OrderSeasonEpisode,		NameSeasonShort + '%01d' + NameEpisodeShort + '%02d'),
		(OrderSeasonEpisode,		NameSeasonShort + '%02d' + NameEpisodeShort + '%02d'),
	]

	Formats = None

	@classmethod
	def _format(self, format, title = None, year = None, season = None, episode = None):
		order = format[0]
		format = format[1]
		if order == self.OrderTitle:
			return format % (title)
		elif order == self.OrderTitleYear:
			return format % (title, year)
		elif order == self.OrderYearTitle:
			return format % (year, title)
		elif order == self.OrderSeason:
			return format % (season)
		elif order == self.OrderEpisode:
			return format % (episode)
		elif order == self.OrderSeasonEpisode:
			return format % (season, episode)
		elif order == self.OrderEpisodeTitle:
			return format % (episode, title)
		elif order == self.OrderSeasonEpisodeTitle:
			return format % (season, episode, title)
		else:
			return title

	@classmethod
	def _extract(self, metadata, encode = False):
		title = metadata['tvshowtitle'] if 'tvshowtitle' in metadata else metadata['title']
		if encode: title = Converter.unicode(string = title, umlaut = True)
		year = int(metadata['year']) if 'year' in metadata else None
		season = int(metadata['season']) if 'season' in metadata else None
		episode = int(metadata['episode']) if 'episode' in metadata else None
		pack = bool(metadata['pack']) if 'pack' in metadata else False
		return (title, year, season, episode, pack)

	@classmethod
	def _data(self, title, year, season, episode, encode = False):
		if not title == None and encode: title = Converter.unicode(string = title, umlaut = True)
		if not year == None: year = int(year)
		if not season == None: season = int(season)
		if not episode == None: episode = int(episode)
		return (title, year, season, episode)

	@classmethod
	def _initialize(self):
		if self.Formats == None:
			from resources.lib.extensions import interface
			aeonNox = interface.Skin.isGaiaAeonNox()
			self.Formats = {}

			setting = Settings.getInteger('interface.title.movies')
			if setting == self.Default:
				setting = self.DefaultAeonNoxMovie if aeonNox else self.DefaultMovie
			else:
				setting -= 1
			self.Formats[self.TypeMovie] = self.FormatsTitle[setting]

			setting = Settings.getInteger('interface.title.documentaries')
			if setting == self.Default:
				setting = self.DefaultAeonNoxDocumentary if aeonNox else self.DefaultDocumentary
			else:
				setting -= 1
			self.Formats[self.TypeDocumentary] = self.FormatsTitle[setting]

			setting = Settings.getInteger('interface.title.shorts')
			if setting == self.Default:
				setting = self.DefaultAeonNoxShort if aeonNox else self.DefaultShort
			else:
				setting -= 1
			self.Formats[self.TypeShort] = self.FormatsTitle[setting]

			setting = Settings.getInteger('interface.title.shows')
			if setting == self.Default:
				setting = self.DefaultAeonNoxShow if aeonNox else self.DefaultShow
			else:
				setting -= 1
			self.Formats[self.TypeShow] = self.FormatsTitle[setting]

			setting = Settings.getInteger('interface.title.seasons')
			if setting == self.Default:
				setting = self.DefaultAeonNoxSeason if aeonNox else self.DefaultSeason
			else:
				setting -= 1
			self.Formats[self.TypeSeason] = self.FormatsSeason[setting]

			setting = Settings.getInteger('interface.title.episodes')
			if setting == self.Default:
				setting = self.DefaultAeonNoxEpisode if aeonNox else self.DefaultEpisode
			else:
				setting -= 1
			self.Formats[self.TypeEpisode] = self.FormatsEpisode[setting]

	@classmethod
	def title(self, type = TypeNone, metadata = None, title = None, year = None, season = None, episode = None, encode = False, pack = False):
		if not metadata == None:
			title, year, season, episode, packs = self._extract(metadata = metadata, encode = encode)
		title, year, season, episode = self._data(title = title, year = year, season = season, episode = episode, encode = encode)

		if type == self.TypeNone:
			pack = (pack and packs)
			if not season == None and not episode == None and not pack:
				type = self.TypeEpisode
			if not season == None:
				type = self.TypeSeason
			else:
				type = self.TypeMovie

		self._initialize()
		format = self.Formats[type]

		return self._format(format = format, title = title, year = year, season = season, episode = episode)

	# Raw title to search on the web/scrapers.
	@classmethod
	def titleUniversal(self, metadata = None, title = None, year = None, season = None, episode = None, encode = False):
		if not metadata == None:
			title, year, season, episode, packs = self._extract(metadata = metadata, encode = encode)
		title, year, season, episode = self._data(title = title, year = year, season = season, episode = episode, encode = encode)

		if not season == None and not episode == None:
			return '%s S%02dE%02d' % (title, season, episode)
		elif not year == None:
			return  '%s (%s)' % (title, year)
		else:
			return title

	@classmethod
	def typeMovie(self, type):
		return type == self.TypeMovie or type == self.TypeDocumentary or type == self.TypeShort

	@classmethod
	def typeTelevision(self, type):
		return type == self.TypeShow or type == self.TypeSeason or type == self.TypeEpisode

###################################################################
# LIGHTPACK
###################################################################

from resources.lib.externals.lightpack import lightpack

class Lightpack(object):

	ExecutionKodi = 'kodi'
	ExecutionGaia = 'gaia'

	StatusUnknown = None
	StatusOn = 'on'
	StatusOff = 'off'

	# Number of LEDs in Lightpack
	MapSize = 10

	PathWindows = ['C:\\Program Files (x86)\\Prismatik\\Prismatik.exe', 'C:\\Program Files\\Prismatik\\Prismatik.exe']
	PathLinux = ['/usr/bin/prismatik', '/usr/local/bin/prismatik']

	def __init__(self):
		self.mError = False

		self.mEnabled = Settings.getBoolean('lightpack.enabled')

		self.mPrismatikMode = Settings.getInteger('lightpack.prismatik.mode')
		self.mPrismatikLocation = Settings.getString('lightpack.prismatik.location')

		self.mLaunchAutomatic = Settings.getInteger('lightpack.launch.automatic')
		self.mLaunchAnimation = Settings.getBoolean('lightpack.launch.animation')

		self.mProfileFixed = Settings.getBoolean('lightpack.profile.fixed')
		self.mProfileName = Settings.getString('lightpack.profile.name')

		self.mCount = Settings.getInteger('lightpack.count')
		self.mMap = self._map()

		self.mHost = Settings.getString('lightpack.connection.host')
		self.mPort = Settings.getInteger('lightpack.connection.port')
		self.mAuthorization = Settings.getBoolean('lightpack.connection.authorization')
		self.mApiKey = Settings.getString('lightpack.connection.api')

		self.mLightpack = None
		self._initialize()

	def __del__(self):
		try: self._unlock()
		except: pass
		try: self._disconnect()
		except: pass

	def _map(self):
		result = []
		set = 10
		for i in range(self.mCount):
			start = self.MapSize * i
			for j in range(1, self.MapSize + 1):
				result.append(start + j)
		return result

	def _initialize(self):
		if not self.mEnabled:
			return

		api = self.mApiKey if self.mAuthorization else ''
		self.mLightpack = lightpack.lightpack(self.mHost, self.mPort, api, self.mMap)

	def _error(self):
		return self.mError

	def _errorSuccess(self):
		return not self.mError

	def _errorSet(self):
		self.mError = True

	def _errorClear(self):
		self.mError = False

	def _connect(self):
		return self.mLightpack.connect() >= 0

	def _disconnect(self):
		self.mLightpack.disconnect()

	def _lock(self):
		self.mLightpack.lock()

	def _unlock(self):
		self.mLightpack.unlock()

	# Color is RGB array or hex. If index is None, uses all LEDs.
	def _colorSet(self, color, index = None, lock = False):
		if lock: self.mLightpack.lock()

		if isinstance(color, basestring):
			color = color.replace('#', '')
			if len(color) == 6:
				color = 'FF' + color
			color = [int(color[i : i + 2], 16) for i in range(2, 8, 2)]

		if index == None:
			self.mLightpack.setColorToAll(color[0], color[1], color[2])
		else:
			self.mLightpack.setColor(index, color[0], color[1], color[2])

		if lock: self.mLightpack.unlock()

	def _profileSet(self, profile):
		try:
			self._errorClear()
			self._lock()
			self.mLightpack.setProfile(profile)
			self._unlock()
		except:
			self._errorSet()
		return self._errorSuccess()

	def _message(self):
		from resources.lib.extensions import interface
		interface.Dialog.confirm(title = 33406, message = 33410)

	def _launchEnabled(self, execution):
		if self.mEnabled:
			if execution == self.ExecutionKodi and (self.mLaunchAutomatic == 1 or self.mLaunchAutomatic == 3):
				return True
			if execution == self.ExecutionGaia and (self.mLaunchAutomatic == 2 or self.mLaunchAutomatic == 3):
				return True
		return False

	def _launch(self):
		try:
			if not self._connect():
				raise Exception()
		except:
			try:
				if self.mLaunchAutomatic > 0:
					automatic = self.mPrismatikMode == 0 or self.mPrismatikPath == None or self.mPrismatikPath == ''

					if 'win' in sys.platform or 'nt' in sys.platform:
						command = 'start "Prismatik" /B /MIN "%s"'
						if automatic:
							executed = False
							for path in self.PathWindows:
								if os.path.exists(path):
									os.system(command % path)
									executed = True
									break
							if not executed:
								os.system('prismatik') # Global path
						else:
							os.system(command % self.mPrismatikPath)
					elif 'darwin' in sys.platform or 'max' in sys.platform:
						os.system('open "' + self.mPrismatikPath + '"')
					else:
						command = '"%s" &'
						if automatic:
							executed = False
							for path in self.PathLinux:
								if os.path.exists(path):
									os.system(command % path)
									executed = True
									break
							if not executed:
								os.system('prismatik') # Global path
						else:
							os.system(command % self.mPrismatikPath)

					time.sleep(3)
					self._connect()
					self.switchOn()
			except:
				self._errorSet()

		try:
			if self.status() == self.StatusUnknown:
				self.mLightpack = None
			else:
				try:
					if self.mProfileFixed and self.mProfileName and not self.mProfileName == '':
						self._profileSet(self.mProfileName)
				except:
					self._errorSet()
		except:
			self.mLightpack = None

		self.animate(force = False)

	def launchAutomatic(self):
		self.launch(self.ExecutionKodi)

	def launch(self, execution):
		if self._launchEnabled(execution = execution):
			thread = threading.Thread(target = self._launch)
			thread.start()

	@classmethod
	def settings(self):
		Settings.launch(category = Settings.CategoryLightpack)

	def enabled(self):
		return self.mEnabled

	def status(self):
		if not self.mEnabled:
			return self.StatusUnknown

		try:
			self._errorClear()
			self._lock()
			status = self.mLightpack.getStatus()
			self._unlock()
			return status.strip()
		except:
			self._errorSet()
		return self.StatusUnknown

	def statusUnknown(self):
		return self.status() == self.StatusUnknown

	def statusOn(self):
		return self.status() == self.StatusOn

	def statusOff(self):
		return self.status() == self.StatusOff

	def switchOn(self, message = False):
		if not self.mEnabled:
			return False

		try:
			self._errorClear()
			self._lock()
			self.mLightpack.turnOn()
			self._unlock()
		except:
			self._errorSet()
		success = self._errorSuccess()
		if not success and message: self._message()
		return success

	def switchOff(self, message = False):
		if not self.mEnabled:
			return False

		try:
			self._errorClear()
			self._lock()
			self.mLightpack.turnOff()
			self._unlock()
		except:
			self._errorSet()
		success = self._errorSuccess()
		if not success and message: self._message()
		return success

	def _animateSpin(self, color):
		for i in range(len(self.mMap)):
			self._colorSet(color = color, index = i)
			time.sleep(0.1)

	def animate(self, force = True, message = False, delay = False):
		if not self.mEnabled:
			return False

		if force or self.mLaunchAnimation:
			try:
				self.switchOn()
				self._errorClear()
				if delay: # The Lightpack sometimes gets stuck on the red light on startup animation. Maybe this delay will solve that?
					time.sleep(1)
				self._lock()

				for i in range(2):
					self._animateSpin('FFFF0000')
					self._animateSpin('FFFF00FF')
					self._animateSpin('FF0000FF')
					self._animateSpin('FF00FFFF')
					self._animateSpin('FF00FF00')
					self._animateSpin('FFFFFF00')

				self._unlock()
			except:
				self._errorSet()
		else:
			return False
		success = self._errorSuccess()
		if not success and message: self._message()
		return success

###################################################################
# PLATFORM
###################################################################

PlatformInstance = None

class Platform:

	FamilyWindows = 'windows'
	FamilyUnix = 'unix'

	SystemWindows = 'windows'
	SystemMacintosh = 'macintosh'
	SystemLinux = 'linux'
	SystemAndroid = 'android'

	Architecture64bit = '64bit'
	Architecture32bit = '32bit'
	ArchitectureArm = 'arm'

	def __init__(self):
		self.mFamilyType = None
		self.mFamilyName = None
		self.mSystemType = None
		self.mSystemName = None
		self.mDistributionType = None
		self.mDistributionName = None
		self.mVersionShort = None
		self.mVersionFull = None
		self.mArchitecture = None
		self.mAgent = None
		self._detect()

	@classmethod
	def instance(self):
		global PlatformInstance
		if PlatformInstance == None:
			PlatformInstance = Platform()
		return PlatformInstance

	@classmethod
	def familyType(self):
		return self.instance().mFamilyType

	@classmethod
	def familyName(self):
		return self.instance().mFamilyName

	@classmethod
	def systemType(self):
		return self.instance().mSystemType

	@classmethod
	def systemName(self):
		return self.instance().mSystemName

	@classmethod
	def distributionType(self):
		return self.instance().mDistributionType

	@classmethod
	def distributionName(self):
		return self.instance().mDistributionName

	@classmethod
	def versionShort(self):
		return self.instance().mVersionShort

	@classmethod
	def versionFull(self):
		return self.instance().mVersionFull

	@classmethod
	def architecture(self):
		return self.instance().mArchitecture

	@classmethod
	def agent(self):
		return self.instance().mAgent

	@classmethod
	def _detectWindows(self):
		try: return self.SystemWindows in platform.system().lower()
		except: return False

	@classmethod
	def _detectMacintosh(self):
		try:
			version = platform.mac_ver()
			return not version[0] == None and not version[0] == ''
		except: return False

	@classmethod
	def _detectLinux(self):
		try: return platform.system().lower() == 'linux' and not self._detectAndroid()
		except: return False

	@classmethod
	def _detectAndroid(self):
		try:
			system = platform.system().lower()
			distribution = platform.linux_distribution()
			if self.SystemAndroid in system or self.SystemAndroid in system or (len(distribution) > 0 and isinstance(distribution[0], basestring) and self.SystemAndroid in distribution[0].lower()):
				return True
			if system == self.SystemLinux:
				id = ''
				if 'ANDROID_ARGUMENT' in os.environ:
					id = True
				if id == None or id == '':
					try: id = subprocess.Popen('getprop ril.serialnumber'.split(), stdout = subprocess.PIPE).communicate()[0].trim()
					except: pass
				if id == None or id == '':
					try: id = subprocess.Popen('getprop ro.serialno'.split(), stdout = subprocess.PIPE).communicate()[0].trim()
					except: pass
				if id == None or id == '':
					try: id = subprocess.Popen('getprop sys.serialnumber'.split(), stdout = subprocess.PIPE).communicate()[0].trim()
					except: pass
				if id == None or id == '':
					try: id = subprocess.Popen('getprop gsm.sn1'.split(), stdout = subprocess.PIPE).communicate()[0].trim()
					except: pass
				if not id == None and not id == '':
					try: return not 'not found' in id
					except: return True
		except: pass
		return False

	def _detect(self):
		try:
			if self._detectWindows():
				self.mFamilyType = self.FamilyWindows
				self.mFamilyName = self.mFamilyType.capitalize()

				self.mSystemType = self.SystemWindows
				self.mSystemName = self.mSystemType.capitalize()

				version = platform.win32_ver()
				self.mVersionShort = version[0]
				self.mVersionFull = version[1]
			elif self._detectAndroid():
				self.mFamilyType = self.FamilyUnix
				self.mFamilyName = self.mFamilyType.capitalize()

				self.mSystemType = self.SystemAndroid
				self.mSystemName =  self.mSystemType.capitalize()

				distribution = platform.linux_distribution()
				self.mVersionShort = distribution[1]
				self.mVersionFull = distribution[2]
			elif self._detectMacintosh():
				self.mFamilyType = self.FamilyUnix
				self.mFamilyName = self.mFamilyType.capitalize()

				self.mSystemType = self.SystemMacintosh
				self.mSystemName =  self.mSystemType.capitalize()

				mac = platform.mac_ver()
				self.mVersionShort = mac[0]
				self.mVersionFull = self.mVersionShort
			elif self._detectLinux():
				self.mFamilyType = self.FamilyUnix
				self.mFamilyName = self.mFamilyType.capitalize()

				self.mSystemType = self.SystemLinux
				self.mSystemName =  self.mSystemType.capitalize()

				distribution = platform.linux_distribution()
				self.mDistributionType = distribution[0].lower().replace('"', '').replace(' ', '')
				self.mDistributionName = distribution[0].replace('"', '')

				self.mVersionShort = distribution[1]
				self.mVersionFull = distribution[2]

			machine = platform.machine().lower()
			if '64' in machine: self.mArchitecture = self.Architecture64bit
			elif '86' in machine or '32' in machine or 'i386' in machine or 'i686' in machine: self.mArchitecture = self.Architecture32bit
			elif 'arm' in machine or 'risc' in machine or 'acorn' in machine: self.mArchitecture = self.ArchitectureArm

			try:
				system = ''
				if self.mSystemType == self.SystemWindows:
					system += 'Windows NT'
					if self.mVersionFull: system += ' ' + self.mVersionFull
					if self.mArchitecture == self.Architecture64bit: system += '; Win64; x64'
					elif self.mArchitecture == self.ArchitectureArm: system += '; ARM'
				elif self.mSystemType == self.SystemMacintosh:
					system += 'Macintosh; Intel Mac OS X ' + self.mVersionShort.replace('.', '_')
				elif self.mSystemType == self.SystemLinux:
					system += 'X11;'
					if self.mDistributionName: system += ' ' + self.mDistributionName + ';'
					system += ' Linux;'
					if self.mArchitecture == self.Architecture32bit: system += ' x86'
					elif self.mArchitecture == self.Architecture64bit: system += ' x86_64'
					elif self.mArchitecture == self.ArchitectureArm: system += ' arm'
				elif self.mSystemType == self.SystemAndroid:
					system += 'Linux; Android ' + self.mVersionShort
				if not system == '': system = '(' + system + ') '
				system = System.name() + '/' + System.version() + ' ' + system + 'Kodi/' + str(System.versionKodi())

				# Do in 2 steps, previous statement can fail
				self.mAgent = system
			except:
				Logger.error()

		except:
			Logger.error()

###################################################################
# HARDWARE
###################################################################

class Hardware(object):

	PerformanceSlow = 'slow'
	PerformanceMedium = 'medium'
	PerformanceFast = 'fast'

	ConfigurationSlow = {'processors' : 2, 'memory' : 2147483648}
	ConfigurationMedium = {'processors' : 4, 'memory' : 4294967296}

	@classmethod
	def identifier(self):
		id = None

		# Windows
		if os.name == 'nt':
			if id == None or ' ' in id:
				try:
					import _winreg
					registry = _winreg.HKEY_LOCAL_MACHINE
					address = 'SOFTWARE\\Microsoft\\Cryptography'
					keyargs = _winreg.KEY_READ | _winreg.KEY_WOW64_64KEY
					key = _winreg.OpenKey(registry, address, 0, keyargs)
					value = _winreg.QueryValueEx(key, 'MachineGuid')
					_winreg.CloseKey(key)
					id = value[0]
				except: pass

			if id == None or ' ' in id:
				try:
					id = subprocess.Popen('wmic csproduct get uuid'.split(), stdout = subprocess.PIPE).communicate()[0]
				except: pass

			if id == None or ' ' in id:
				try:
					id = subprocess.Popen('dmidecode.exe -s system-uuid'.split(), stdout = subprocess.PIPE).communicate()[0]
				except: pass

		# Android
		if id == None or ' ' in id:
			try:
				id = subprocess.Popen('getprop ril.serialnumber'.split(), stdout = subprocess.PIPE).communicate()[0]
			except: pass
		if id == None or ' ' in id:
			try:
				id = subprocess.Popen('getprop ro.serialno'.split(), stdout = subprocess.PIPE).communicate()[0]
			except: pass
		if id == None or ' ' in id:
			try:
				id = subprocess.Popen('getprop sys.serialnumber'.split(), stdout = subprocess.PIPE).communicate()[0]
			except: pass
		if id == None or ' ' in id:
			try:
				id = subprocess.Popen('getprop gsm.sn1'.split(), stdout = subprocess.PIPE).communicate()[0]
			except: pass

		# Linux
		if id == None or ' ' in id:
			try:
				id = subprocess.Popen('hal-get-property --udi /org/freedesktop/Hal/devices/computer --key system.hardware.uuid'.split(), stdout = subprocess.PIPE).communicate()[0]
			except: pass

		# Linux
		if id == None or ' ' in id:
			try:
				id = subprocess.Popen('/sys/class/dmi/id/board_serial', stdout = subprocess.PIPE).communicate()[0]
			except: pass

		# Linux
		if id == None or ' ' in id:
			try:
				id = subprocess.Popen('/sys/class/dmi/id/product_uuid', stdout = subprocess.PIPE).communicate()[0]
			except: pass

		# Linux
		if id == None or ' ' in id:
			try:
				id = subprocess.Popen('cat /var/lib/dbus/machine-id', stdout = subprocess.PIPE).communicate()[0]
			except: pass

		# If still not found, get the MAC address
		if id == None or ' ' in id:
			try:
				import psutil
				nics = psutil.net_if_addrs()
				nics.pop('lo')
				for i in nics:
					for j in nics[i]:
						if j.family == 17:
							id = j.address
							break
			except: pass

		# If still not found, get the MAC address
		if id == None or ' ' in id:
			try:
				import netifaces
				interface = [i for i in netifaces.interfaces() if not i.startswith('lo')][0]
				id = netifaces.ifaddresses(interface)[netifaces.AF_LINK]
			except: pass

		# If still not found, get the MAC address
		if id == None or ' ' in id:
			try:
				import uuid
				# Might return a random ID on failure
				# In such a case, save it to the settings and return it, ensuring that the same ID is used.
				id = Settings.getString('general.statistics.identifier')
				if id == None or id == '':
					id = uuid.getnode()
					Settings.set('general.statistics.identifier', id)
			except: pass

		if id == None: id = ''
		else: id = str(id)

		try: id += str(System.informationSystem()['name'])
		except: pass

		try: id += str(self.processors())
		except: pass

		try: id += str(self.memory())
		except: pass

		return Hash.sha256(id)

	@classmethod
	def performance(self):
		processors = self.processors()
		memory = self.memory()

		if processors == None and memory == None:
			return self.PerformanceMedium

		if not processors == None and not self.ConfigurationSlow['processors'] == None and processors <= self.ConfigurationSlow['processors']:
			return self.PerformanceSlow
		if not memory == None and not self.ConfigurationSlow['memory'] == None and memory <= self.ConfigurationSlow['memory']:
			return self.PerformanceSlow

		if not processors == None and not self.ConfigurationMedium['processors'] == None and processors <= self.ConfigurationMedium['processors']:
			return self.PerformanceMedium
		if not memory == None and not self.ConfigurationMedium['memory'] == None and memory <= self.ConfigurationMedium['memory']:
			return self.PerformanceMedium

		return self.PerformanceFast

	@classmethod
	def slow(self):
		processors = self.processors()
		if not processors == None and not self.ConfigurationSlow['processors'] == None and processors <= self.ConfigurationSlow['processors']:
			return True
		memory = self.memory()
		if not memory == None and not self.ConfigurationSlow['memory'] == None and memory <= self.ConfigurationSlow['memory']:
			return True
		return False

	@classmethod
	def processors(self):
		# http://stackoverflow.com/questions/1006289/how-to-find-out-the-number-of-cpus-using-python

		# Python 2.6+
		try:
			import multiprocessing
			return multiprocessing.cpu_count()
		except: pass

		# PSUtil
		try:
			import psutil
			return psutil.cpu_count() # psutil.NUM_CPUS on old versions
		except: pass

		# POSIX
		try:
			result = int(os.sysconf('SC_NPROCESSORS_ONLN'))
			if result > 0: return result
		except: pass

		# Windows
		try:
			result = int(os.environ['NUMBER_OF_PROCESSORS'])
			if result > 0: return result
		except: pass

		# jython
		try:
			from java.lang import Runtime
			runtime = Runtime.getRuntime()
			result = runtime.availableProcessors()
			if result > 0: return result
		except: pass

		# cpuset
		# cpuset may restrict the number of *available* processors
		try:
			result = re.search(r'(?m)^Cpus_allowed:\s*(.*)$', open('/proc/self/status').read())
			if result:
				result = bin(int(result.group(1).replace(',', ''), 16)).count('1')
				if result > 0: return result
		except: pass

		# BSD
		try:
			sysctl = subprocess.Popen(['sysctl', '-n', 'hw.ncpu'], stdout=subprocess.PIPE)
			scStdout = sysctl.communicate()[0]
			result = int(scStdout)
			if result > 0: return result
		except: pass

		# Linux
		try:
			result = open('/proc/cpuinfo').read().count('processor\t:')
			if result > 0: return result
		except: pass

		# Solaris
		try:
			pseudoDevices = os.listdir('/devices/pseudo/')
			result = 0
			for pd in pseudoDevices:
				if re.match(r'^cpuid@[0-9]+$', pd):
					result += 1
			if result > 0: return result
		except: pass

		# Other UNIXes (heuristic)
		try:
			try:
				dmesg = open('/var/run/dmesg.boot').read()
			except IOError:
				dmesgProcess = subprocess.Popen(['dmesg'], stdout=subprocess.PIPE)
				dmesg = dmesgProcess.communicate()[0]
			result = 0
			while '\ncpu' + str(result) + ':' in dmesg:
				result += 1
			if result > 0: return result
		except: pass

		return None

	@classmethod
	def memory(self):
		try:
			from psutil import virtual_memory
			memory = virtual_memory().total
			if memory > 0: return memory
		except: pass

		try:
			memory = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
			if memory > 0: return memory
		except: pass

		try:
			memory = dict((i.split()[0].rstrip(':'),int(i.split()[1])) for i in open('/proc/meminfo').readlines())
			memory = memory['MemTotal'] * 1024
			if memory > 0: return memory
		except: pass

		try:
			from ctypes import Structure, c_int32, c_uint64, sizeof, byref, windll
			class MemoryStatusEx(Structure):
				_fields_ = [
					('length', c_int32),
					('memoryLoad', c_int32),
					('totalPhys', c_uint64),
					('availPhys', c_uint64),
					('totalPageFile', c_uint64),
					('availPageFile', c_uint64),
					('totalVirtual', c_uint64),
					('availVirtual', c_uint64),
					('availExtendedVirtual', c_uint64)]
				def __init__(self):
					self.length = sizeof(self)
			memory = MemoryStatusEx()
			windll.kernel32.GlobalMemoryStatusEx(byref(memory))
			memory = memory.totalPhys
			if memory > 0: return memory
		except: pass

		return None

###################################################################
# EXTENSIONS
###################################################################

class Extensions(object):

	# Types
	TypeRequired = 'required'
	TypeRecommended = 'recommended'
	TypeOptional = 'optional'

	# IDs
	IdGaiaAddon = 'plugin.video.gaia'
	IdGaiaRepository1 = 'repository.gaia.1'
	IdGaiaRepository2 = 'repository.gaia.2'
	IdGaiaRepository3 = 'repository.gaia.3'
	IdGaiaArtwork = 'script.gaia.artwork'
	IdGaiaBinaries = 'script.gaia.binaries'
	IdGaiaResources = 'script.gaia.resources'
	IdGaiaIcons = 'script.gaia.icons'
	IdGaiaSkins = 'script.gaia.skins'
	IdGaiaAeonNox = 'skin.gaia.aeon.nox' if System.versionKodi() < 18 else 'skin.gaia.aeon.nox.18'
	IdResolveUrl = 'script.module.resolveurl'
	IdUrlResolver = 'script.module.urlresolver'
	IdLamScrapers = 'script.module.lambdascrapers'
	IdUniScrapers = 'script.module.universalscrapers'
	IdNanScrapers = 'script.module.nanscrapers'
	IdIncursion = 'plugin.video.incursion'
	IdIncScrapers = 'script.module.incursion'
	IdPlacenta = 'plugin.video.placenta'
	IdPlaScrapers = 'script.module.placenta'
	IdMetaHandler = 'script.module.metahandler'
	IdTrakt = 'script.trakt'
	IdElementum = 'plugin.video.elementum'
	IdElementumRepository = 'repository.elementum'
	IdQuasar = 'plugin.video.quasar'
	IdQuasarRepository = 'repository.quasar'
	IdYouTube = 'plugin.video.youtube'

	@classmethod
	def settings(self, id):
		try:
			System.execute('Addon.OpenSettings(%s)' % id)
			return True
		except:
			return False

	@classmethod
	def launch(self, id):
		try:
			System.execute('RunAddon(%s)' % id)
			return True
		except:
			return False

	@classmethod
	def installed(self, id):
		try:
			idReal = xbmcaddon.Addon(id).getAddonInfo('id')
			return id == idReal
		except:
			return False

	@classmethod
	def enable(self, id, refresh = False):
		try: System.execute('InstallAddon(%s)' % id)
		except: pass
		try: System.executeJson('{"jsonrpc" : "2.0", "method" : "Addons.SetAddonEnabled", "params" : {"addonid" : "%s", "enabled" : true}, "id" : 1}' % id)
		except: pass
		if refresh:
			try: System.execute('Container.Refresh')
			except: pass

	@classmethod
	def disable(self, id, refresh = False):
		try: System.executeJson('{"jsonrpc" : "2.0", "method" : "Addons.SetAddonEnabled", "params" : {"addonid" : "%s", "enabled" : false}, "id" : 1}' % id)
		except: pass
		if refresh:
			try: System.execute('Container.Refresh')
			except: pass

	@classmethod
	def list(self):
		from resources.lib.extensions import orionoid
		from resources.lib.extensions import interface

		result = [
			{
				'id' : self.IdGaiaRepository1,
				'name' : 'Gaia Repository 1',
				'type' : self.TypeRequired,
				'description' : 33917,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : self.IdGaiaRepository2,
				'name' : 'Gaia Repository 2',
				'type' : self.TypeRecommended,
				'description' : 33918,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : self.IdGaiaRepository3,
				'name' : 'Gaia Repository 3',
				'type' : self.TypeRecommended,
				'description' : 33918,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : self.IdGaiaResources,
				'name' : 'Gaia Resources',
				'type' : self.TypeRequired,
				'description' : 33726,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : self.IdGaiaArtwork,
				'name' : 'Gaia Artwork',
				'type' : self.TypeRecommended,
				'description' : 33727,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : self.IdGaiaBinaries,
				'name' : 'Gaia Binaries',
				'type' : self.TypeOptional,
				'description' : 33728,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : self.IdGaiaIcons,
				'name' : 'Gaia Icons',
				'type' : self.TypeOptional,
				'description' : 33729,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : self.IdGaiaSkins,
				'name' : 'Gaia Skins',
				'type' : self.TypeOptional,
				'description' : 33730,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : self.IdGaiaAeonNox,
				'name' : 'Gaia Aeon Nox',
				'type' : self.TypeOptional,
				'description' : 33731,
				'icon' : 'extensionsgaia.png',
			},
			{
				'id' : self.IdResolveUrl,
				'name' : 'ResolveUrl',
				'type' : self.TypeRequired,
				'description' : 33732,
				'icon' : 'extensionsresolveurl.png',
			},
			{
				'id' : self.IdUrlResolver,
				'name' : 'UrlResolver',
				'type' : self.TypeRequired,
				'description' : 33732,
				'icon' : 'extensionsurlresolver.png',
			},
			{
				'id' : orionoid.Orionoid.Id,
				'name' : orionoid.Orionoid.Name + ' Scrapers',
				'type' : self.TypeRequired,
				'description' : 35401,
				'icon' : 'extensionsorion.png',
			},
			{
				'id' : self.IdLamScrapers,
				'name' : 'Lambda Scrapers',
				'type' : self.TypeRecommended,
				'description' : 33963,
				'icon' : 'extensionslamscrapers.png',
			},
			{
				'id' : self.IdUniScrapers,
				'name' : 'Universal Scrapers',
				'type' : self.TypeRecommended,
				'description' : 33963,
				'icon' : 'extensionsuniscrapers.png',
			},
			{
				'id' : self.IdNanScrapers,
				'name' : 'NoobsAndNerds Scrapers',
				'type' : self.TypeOptional,
				'description' : 33963,
				'icon' : 'extensionsnanscrapers.png',
			},
			{
				'id' : self.IdIncursion,
				'name' : 'Incursion Scrapers',
				'type' : self.TypeOptional,
				'description' : 33963,
				'icon' : 'extensionsincscrapers.png',
			},
			{
				'id' : self.IdPlacenta,
				'name' : 'Placenta Scrapers',
				'type' : self.TypeOptional,
				'description' : 33963,
				'icon' : 'extensionsplascrapers.png',
			},
			{
				'id' : self.IdMetaHandler,
				'name' : 'MetaHandler',
				'type' : self.TypeOptional,
				'description' : 33733,
				'icon' : 'extensionsmetahandler.png',
			},
			{
				'id' : self.IdTrakt,
				'name' : 'Trakt',
				'type' : self.TypeRecommended,
				'description' : 33734,
				'icon' : 'extensionstrakt.png',
			},
			{
				'id' : self.IdElementum,
				'dependencies' : [self.IdElementumRepository],
				'name' : 'Elementum',
				'type' : self.TypeOptional,
				'description' : 33735,
				'icon' : 'extensionselementum.png',
			},
			{
				'id' : self.IdQuasar,
				'dependencies' : [self.IdQuasarRepository],
				'name' : 'Quasar',
				'type' : self.TypeOptional,
				'description' : 33735,
				'icon' : 'extensionsquasar.png',
			},
			{
				'id' : self.IdYouTube,
				'dependencies' : [self.IdResolveUrl],
				'name' : 'YouTube',
				'type' : self.TypeOptional,
				'description' : 35297,
				'icon' : 'extensionsyoutube.png',
			},
		]

		for i in range(len(result)):
			result[i]['installed'] = self.installed(result[i]['id'])
			if 'dependencies' in result[i]:
				for dependency in result[i]['dependencies']:
					if not self.installed(dependency):
						result[i]['installed'] = False
						break
			result[i]['description'] = interface.Translation.string(result[i]['description'])

		return result

	@classmethod
	def dialog(self, id):
		extensions = self.list()
		for extension in extensions:
			if extension['id'] == id:
				from resources.lib.extensions import interface

				type = ''
				if extension['type'] == self.TypeRequired:
					type = 33723
				elif extension['type'] == self.TypeRecommended:
					type = 33724
				elif extension['type'] == self.TypeOptional:
					type = 33725
				if not type == '':
					type = ' (%s)' % interface.Translation.string(type)

				message = ''
				message += interface.Format.fontBold(extension['name'] + type)
				message += interface.Format.newline() + extension['description']

				action = 33737 if extension['installed'] else 33736

				choice = interface.Dialog.option(title = 33391, message = message, labelConfirm = action, labelDeny = 33486)
				if choice:
					if extension['installed']:
						if extension['type'] == self.TypeRequired:
							interface.Dialog.confirm(title = 33391, message = 33738)
						else:
							self.disable(extension['id'], refresh = True)
					else:
						if 'dependencies' in extension:
							for dependency in extension['dependencies']:
								self.enable(dependency, refresh = True)
						self.enable(extension['id'], refresh = True)

					LamScrapers.check()
					UniScrapers.check()
					NanScrapers.check()
					IncScrapers.check()
					PlaScrapers.check()

				return True
		return False

###################################################################
# ELEMENTUM
###################################################################

class Elementum(object):

	Id = Extensions.IdElementum
	Name = 'Elementum'

	@classmethod
	def settings(self):
		Extensions.settings(id = self.Id)

	@classmethod
	def launch(self):
		Extensions.launch(id = self.Id)

	@classmethod
	def install(self, confirm = False):
		Extensions.enable(id = Extensions.IdElementum, refresh = False)
		self.connect(confirm = confirm)
		return True

	@classmethod
	def interface(self):
		System.openLink(self.linkWeb())

	@classmethod
	def link(self, type, parameters = None):
		host = Settings.getString('streaming.torrent.elementum.host')
		port = Settings.getString('streaming.torrent.elementum.port')
		if parameters == None or parameters == [] or parameters == {}: parameters = ''
		else: parameters = '?' + ('&'.join(['%s=%s' % (key, value) for key, value in parameters.iteritems()]))
		return 'http://%s:%s/%s%s' % (host, port, type, parameters)

	@classmethod
	def linkWeb(self, parameters = None):
		return self.link(type = 'web', parameters = parameters)

	@classmethod
	def linkPlay(self, parameters = None):
		return self.link(type = 'playuri', parameters = parameters)

	@classmethod
	def linkAdd(self, parameters = None):
		return self.link(type = 'torrents/add', parameters = parameters)

	@classmethod
	def connected(self):
		return Settings.getBoolean('streaming.torrent.elementum.connected')

	@classmethod
	def connect(self, confirm = False):
		try:
			if not System.installed(self.Id):
				if confirm:
					from resources.lib.extensions import interface
					message = interface.Translation.string(35318) + ' ' + interface.Translation.string(35317)
					if interface.Dialog.option(title = self.Name, message = message):
						self.install(confirm = False)
					else:
						raise Exception()
				else:
					raise Exception()
			Settings.set('streaming.torrent.elementum.connected', True)
			Settings.set('streaming.torrent.elementum.connection', 'Connected')
		except:
			self.disconnect()

	@classmethod
	def disconnect(self):
		Settings.set('streaming.torrent.elementum.connected', False)
		Settings.set('streaming.torrent.elementum.connection', 'Disconnected')

###################################################################
# QUASAR
###################################################################

class Quasar(object):

	Id = Extensions.IdQuasar
	Name = 'Quasar'

	@classmethod
	def settings(self):
		Extensions.settings(id = self.Id)

	@classmethod
	def launch(self):
		Extensions.launch(id = self.Id)

	@classmethod
	def install(self, confirm = False):
		Extensions.enable(id = Extensions.IdQuasar, refresh = False)
		self.connect(confirm = confirm)
		return True

	@classmethod
	def interface(self):
		System.openLink(self.linkWeb())

	@classmethod
	def link(self, type, parameters = None):
		host = Settings.getString('streaming.torrent.quasar.host')
		port = Settings.getString('streaming.torrent.quasar.port')
		if parameters == None or parameters == [] or parameters == {}: parameters = ''
		else: parameters = '?' + ('&'.join(['%s=%s' % (key, value) for key, value in parameters.iteritems()]))
		return 'http://%s:%s/%s%s' % (host, port, type, parameters)

	@classmethod
	def linkWeb(self, parameters = None):
		return self.link(type = 'web', parameters = parameters)

	@classmethod
	def linkPlay(self, parameters = None):
		return self.link(type = 'playuri', parameters = parameters)

	@classmethod
	def linkAdd(self, parameters = None):
		return self.link(type = 'torrents/add', parameters = parameters)

	@classmethod
	def connected(self):
		return Settings.getBoolean('streaming.torrent.quasar.connected')

	@classmethod
	def connect(self, confirm = False):
		try:
			if not System.installed(self.Id):
				if confirm:
					from resources.lib.extensions import interface
					message = interface.Translation.string(33476) + ' ' + interface.Translation.string(33475)
					if interface.Dialog.option(title = self.Name, message = message):
						self.install(confirm = False)
					else:
						raise Exception()
				else:
					raise Exception()
			Settings.set('streaming.torrent.quasar.connected', True)
			Settings.set('streaming.torrent.quasar.connection', 'Connected')
		except:
			self.disconnect()

	@classmethod
	def disconnect(self):
		Settings.set('streaming.torrent.quasar.connected', False)
		Settings.set('streaming.torrent.quasar.connection', 'Disconnected')

###################################################################
# TRAKT
###################################################################

class Trakt(object):

	Id = Extensions.IdTrakt
	Website = 'https://trakt.tv'

	@classmethod
	def settings(self):
		Extensions.settings(id = self.Id)

	@classmethod
	def launch(self):
		Extensions.launch(id = self.Id)

	@classmethod
	def installed(self):
		return Extensions.installed(id = self.Id)

	@classmethod
	def enable(self, refresh = False):
		return Extensions.enable(id = self.Id, refresh = refresh)

	@classmethod
	def disable(self, refresh = False):
		return Extensions.disable(id = self.Id, refresh = refresh)

	@classmethod
	def website(self, open = False):
		if open: System.openLink(self.Website)
		return self.Website

###################################################################
# RESOLVEURL
###################################################################

class ResolveUrl(object):

	Id = Extensions.IdResolveUrl

	@classmethod
	def settings(self):
		Extensions.settings(id = self.Id)

	@classmethod
	def installed(self):
		return Extensions.installed(id = self.Id)

	@classmethod
	def enable(self, refresh = False):
		return Extensions.enable(id = self.Id, refresh = refresh)

	@classmethod
	def disable(self, refresh = False):
		return Extensions.disable(id = self.Id, refresh = refresh)


###################################################################
# URLRESOLVER
###################################################################

class UrlResolver(object):

	Id = Extensions.IdUrlResolver

	@classmethod
	def settings(self):
		Extensions.settings(id = self.Id)

	@classmethod
	def installed(self):
		return Extensions.installed(id = self.Id)

	@classmethod
	def enable(self, refresh = False):
		return Extensions.enable(id = self.Id, refresh = refresh)

	@classmethod
	def disable(self, refresh = False):
		return Extensions.disable(id = self.Id, refresh = refresh)

###################################################################
# LAMSCRAPERS
###################################################################

class LamScrapers(object):

	Id = Extensions.IdLamScrapers

	@classmethod
	def settings(self):
		Extensions.settings(id = self.Id)

	@classmethod
	def check(self):
		Settings.set('providers.external.universal.open.lamscrapersx.installed', self.installed())

	@classmethod
	def installed(self):
		return Extensions.installed(id = self.Id)

	@classmethod
	def enable(self, refresh = False):
		result = Extensions.enable(id = self.Id, refresh = refresh)
		self.check()
		return result

	@classmethod
	def disable(self, refresh = False):
		result = Extensions.disable(id = self.Id, refresh = refresh)
		self.check()
		return result

###################################################################
# UNISCRAPERS
###################################################################

class UniScrapers(object):

	Id = Extensions.IdUniScrapers

	@classmethod
	def settings(self):
		Extensions.settings(id = self.Id)

	@classmethod
	def check(self):
		Settings.set('providers.external.universal.open.uniscrapersx.installed', self.installed())

	@classmethod
	def installed(self):
		return Extensions.installed(id = self.Id)

	@classmethod
	def enable(self, refresh = False):
		result = Extensions.enable(id = self.Id, refresh = refresh)
		self.check()
		return result

	@classmethod
	def disable(self, refresh = False):
		result = Extensions.disable(id = self.Id, refresh = refresh)
		self.check()
		return result

###################################################################
# NANSCRAPERS
###################################################################

class NanScrapers(object):

	Id = Extensions.IdNanScrapers

	@classmethod
	def settings(self):
		Extensions.settings(id = self.Id)

	@classmethod
	def check(self):
		Settings.set('providers.external.universal.open.nanscrapersx.installed', self.installed())

	@classmethod
	def installed(self):
		return Extensions.installed(id = self.Id)

	@classmethod
	def enable(self, refresh = False):
		result = Extensions.enable(id = self.Id, refresh = refresh)
		self.check()
		return result

	@classmethod
	def disable(self, refresh = False):
		result = Extensions.disable(id = self.Id, refresh = refresh)
		self.check()
		return result

###################################################################
# INCSCRAPERS
###################################################################

class IncScrapers(object):

	Id = Extensions.IdIncScrapers
	IdMain = Extensions.IdIncursion

	@classmethod
	def settings(self):
		if Extensions.installed(id = self.IdMain):
			Extensions.settings(id = self.IdMain)
		else:
			from resources.lib.extensions import interface
			name = 'Incursion'
			interface.Dialog.confirm(title = 33391, message = (interface.Translation.string(35336) % (name, name)))

	@classmethod
	def check(self):
		Settings.set('providers.external.universal.open.incscrapersx.installed', self.installed())

	@classmethod
	def installed(self, full = False):
		if full: return Extensions.installed(id = self.IdMain)
		else: return Extensions.installed(id = self.Id)

	@classmethod
	def enable(self, refresh = False):
		result = Extensions.enable(id = self.Id, refresh = refresh)
		self.check()
		return result

	@classmethod
	def disable(self, refresh = False):
		result = Extensions.disable(id = self.Id, refresh = refresh)
		self.check()
		return result

###################################################################
# PLASCRAPERS
###################################################################

class PlaScrapers(object):

	Id = Extensions.IdPlaScrapers
	IdMain = Extensions.IdPlacenta

	@classmethod
	def settings(self):
		if Extensions.installed(id = self.IdMain):
			Extensions.settings(id = self.IdMain)
		else:
			from resources.lib.extensions import interface
			name = 'Placenta'
			interface.Dialog.confirm(title = 33391, message = (interface.Translation.string(35336) % (name, name)))

	@classmethod
	def check(self):
		Settings.set('providers.external.universal.open.plascrapersx.installed', self.installed())

	@classmethod
	def installed(self, full = False):
		if full: return Extensions.installed(id = self.IdMain)
		else: return Extensions.installed(id = self.Id)

	@classmethod
	def enable(self, refresh = False):
		result = Extensions.enable(id = self.Id, refresh = refresh)
		self.check()
		return result

	@classmethod
	def disable(self, refresh = False):
		result = Extensions.disable(id = self.Id, refresh = refresh)
		self.check()
		return result

###################################################################
# YOUTUBE
###################################################################

class YouTube(object):

	Id = Extensions.IdYouTube
	Website = 'https://youtube.com'

	@classmethod
	def settings(self):
		Extensions.settings(id = self.Id)

	@classmethod
	def launch(self):
		Extensions.launch(id = self.Id)

	@classmethod
	def installed(self):
		return Extensions.installed(id = self.Id)

	@classmethod
	def enable(self, refresh = False):
		return Extensions.enable(id = self.Id, refresh = refresh)

	@classmethod
	def disable(self, refresh = False):
		return Extensions.disable(id = self.Id, refresh = refresh)

	@classmethod
	def website(self, open = False):
		if open: System.openLink(self.Website)
		return self.Website

###################################################################
# METAHANDLER
###################################################################

class MetaHandler(object):

	Id = Extensions.IdMetaHandler

	@classmethod
	def settings(self):
		Extensions.settings(id = self.Id)

	@classmethod
	def installed(self):
		return Extensions.installed(id = self.Id)

	@classmethod
	def enable(self, refresh = False):
		return Extensions.enable(id = self.Id, refresh = refresh)

	@classmethod
	def disable(self, refresh = False):
		return Extensions.disable(id = self.Id, refresh = refresh)

###################################################################
# BACKUP
###################################################################

class Backup(object):

	Extension = 'zip'
	Directory = 'Backups'

	TypeEverything = 'everything'
	TypeSettings = 'settings'
	TypeDatabases = 'databases'

	ResultFailure = 'failure'
	ResultPartial = 'partial'
	ResultSuccess = 'success'

	@classmethod
	def _path(self, clear = False):
		return System.temporary(directory = 'backup', gaia = True, make = True, clear = clear)

	@classmethod
	def _name(self):
		from resources.lib.extensions import interface
		from resources.lib.extensions import convert
		date = convert.ConverterTime(Time.timestamp(), convert.ConverterTime.FormatTimestamp).string(convert.ConverterTime.FormatDateTime)
		date = date.replace(':', '.') # Windows does not support colons in file names.
		return System.name() + ' ' + interface.Translation.string(33773) + ' '+ date + '%s.' + self.Extension

	@classmethod
	def _import(self, path):
		try:
			directory = self._path(clear = True)
			directoryData = System.profile()

			file = zipfile.ZipFile(path, 'r')
			file.extractall(directory)
			file.close()

			directories, files = File.listDirectory(directory)
			counter = 0
			for file in files:
				fileFrom = File.joinPath(directory, file)
				fileTo = File.joinPath(directoryData, file)
				if File.move(fileFrom, fileTo, replace = True):
					counter += 1

			File.deleteDirectory(path = directory, force = True)

			Settings.cacheClear() # Clear the data from the old file.

			if counter == 0: return self.ResultFailure
			elif counter == len(files): return self.ResultSuccess
			else: return self.ResultPartial
		except:
			return self.ResultFailure

	@classmethod
	def _export(self, type, path, automatic = False):
		try:
			File.makeDirectory(path)
			name = self._name()
			path = File.joinPath(path, name)
			if automatic:
				path = path % ''
			else:
				counter = 0
				suffix = ''
				while File.exists(path % suffix):
					counter += 1
					suffix = ' [%d]' % counter
				path = path % suffix

			file = zipfile.ZipFile(path, 'w')

			content = []
			directory = self._path(clear = True)
			directoryData = System.profile()
			directories, files = File.listDirectory(directoryData)

			from resources.lib.extensions import database
			settingsDatabase = (Settings.Database + database.Database.Extension).lower()

			if type == self.TypeEverything or type == self.TypeSettings:
				settings = ['settings.xml', settingsDatabase]
				for i in range(len(files)):
					if files[i].lower() in settings:
						content.append(files[i])

			if type == self.TypeEverything or type == self.TypeDatabases:
				extension = '.db'
				for i in range(len(files)):
					if files[i].lower().endswith(extension) and not files[i].lower() == settingsDatabase:
						content.append(files[i])

			tos = [File.joinPath(directory, i) for i in content]
			froms = [File.joinPath(directoryData, i) for i in content]

			for i in range(len(content)):
				try:
					File.copy(froms[i], tos[i], overwrite = True)
					file.write(tos[i], content[i])
				except: pass

			file.close()
			File.deleteDirectory(path = directory, force = True)
			return self.ResultSuccess
		except:
			Logger.error()
			return self.ResultFailure

	@classmethod
	def automaticPath(self):
		return File.joinPath(System.profile(), self.Directory)

	@classmethod
	def automaticClean(self):
		limit = Settings.getInteger('general.settings.backup.limit', cached = False)
		path = self.automaticPath()
		directories, files = File.listDirectory(path)
		count = len(files)
		if count >= limit:
			files.sort(reverse = False)
			i = 0
			while count >= limit:
				File.delete(File.joinPath(path, files[i]), force = True)
				i += 1
				count -= 1

	@classmethod
	def automaticImport(self, force = False):
		try:
			# The problem here is that if the settings are corrupt, the user's preferences, set previously, cannot be determined.
			# Hence, always load the last backup if settings are corrupt. Then check if automatic/selection was enabled.
			# If automatic, don't do anything further.
			# If selection, ask the user which backup to load.

			from resources.lib.extensions import interface
			if force or (Settings.getString('general.settings.backup.time', cached = False) == '' and File.existsDirectory(self.automaticPath())):
				directories, files = File.listDirectory(self.automaticPath())
				Settings.set('general.settings.backup.time', Time.timestamp(), cached = True)

				if len(files) > 0:
					files.sort(reverse = True)
					self._import(path = File.joinPath(self.automaticPath(), files[0]))
					Settings.set('general.settings.backup.time', Time.timestamp(), cached = True)

					if not Settings.getBoolean('general.settings.backup.enabled', cached = False):
						return False

					restore = Settings.getInteger('general.settings.backup.restore', cached = False)
					choice = -1
					if not force and restore == 0:
						choice = 0
					elif force or (restore == 1 and interface.Dialog.option(title = 33773, message = 35210)):
						items = [interface.Format.fontBold(re.search('\\d*-\\d*-\\d*\\s*\\d*\\.\\d*\\.\\d*', file).group(0).replace('.', ':')) for file in files]
						choice = interface.Dialog.options(title = 33773, items = items)

					if choice >= 0:
						result = self._import(path = File.joinPath(self.automaticPath(), files[choice]))
						Settings.set('general.settings.backup.time', Time.timestamp(), cached = True)
						interface.Dialog.notification(title = 33773, message = 35211, icon = interface.Dialog.IconSuccess)
						return result == self.ResultSuccess

					return False

			# Not returned from the inner if.
			if force: interface.Dialog.notification(title = 33773, message = 35247, icon = interface.Dialog.IconError)
			return False
		except:
			Logger.error()
		return False

	@classmethod
	def automaticExport(self, force = False):
		try:
			if Settings.getBoolean('general.settings.backup.enabled', cached = False) or force:
				self.automaticClean()
				Settings.set('general.settings.backup.time', Time.timestamp(), cached = True)
				return self._export(type = self.TypeSettings, path = self.automaticPath(), automatic = True) == self.ResultSuccess
		except:
			Logger.error()
		return False

	@classmethod
	def automatic(self):
		from resources.lib.extensions import interface

		interface.Dialog.confirm(title = 33773, message = 35209)

		items = [
			interface.Format.bold(interface.Translation.string(33774) + ':') + ' ' + interface.Translation.string(35214),
			interface.Format.bold(interface.Translation.string(35212) + ':') + ' ' + interface.Translation.string(35215),
			interface.Format.bold(interface.Translation.string(33011) + ':') + ' ' + interface.Translation.string(35216),
		]

		choice = interface.Dialog.options(title = 33773, items = items)
		if choice == 0:
			if interface.Dialog.option(title = 33773, message = 35217):
				self.automaticImport(force = True)
		elif choice == 1:
			if self.automaticExport(force = True):
				interface.Dialog.notification(title = 33773, message = 35218, icon = interface.Dialog.IconSuccess)
			else:
				interface.Dialog.notification(title = 33773, message = 35219, icon = interface.Dialog.IconError)
		elif choice == 2:
			Settings.launch(Settings.CategoryGeneral)

	@classmethod
	def manualImport(self):
		from resources.lib.extensions import interface

		choice = interface.Dialog.option(title = 33773, message = 33782)
		if not choice: return

		path = interface.Dialog.browse(title = 33773, type = interface.Dialog.BrowseFile, mask = self.Extension)
		result = self._import(path = path)

		if result == self.ResultSuccess:
			interface.Dialog.notification(title = 33773, message = 33785, icon = interface.Dialog.IconSuccess)
		elif result == self.ResultPartial:
			interface.Dialog.confirm(title = 33773, message = interface.Translation.string(33783) % System.id())
		else:
			interface.Dialog.confirm(title = 33773, message = 33778)

	@classmethod
	def manualExport(self):
		from resources.lib.extensions import interface

		choice = interface.Dialog.option(title = 33773, message = 35213)
		if not choice: return

		types = [
			self.TypeEverything,
			self.TypeSettings,
			self.TypeDatabases,
		]
		items = [
			interface.Format.bold(interface.Translation.string(33776) + ':') + ' ' + interface.Translation.string(33779),
			interface.Format.bold(interface.Translation.string(33011) + ':') + ' ' + interface.Translation.string(33780),
			interface.Format.bold(interface.Translation.string(33775) + ':') + ' ' + interface.Translation.string(33781),
		]

		choice = interface.Dialog.options(title = 33773, items = items)
		if choice >= 0:
			path = interface.Dialog.browse(title = 33773, type = interface.Dialog.BrowseDirectoryWrite)
			result = self._export(type = types[choice], path = path)

			if result == self.ResultSuccess:
				interface.Dialog.notification(title = 33773, message = 33784, icon = interface.Dialog.IconSuccess)
			else:
				interface.Dialog.confirm(title = 33773, message = 33777)

	@classmethod
	def directImport(self, path):
		from resources.lib.extensions import interface
		self._import(path)
		interface.Dialog.notification(title = 33773, message = 35326, icon = interface.Dialog.IconSuccess)

	@classmethod
	def reaper(self, confirm = True):
		from resources.lib.extensions import interface
		interface.Dialog.confirm(title = 35321, message = 35323)
		interface.Dialog.confirm(title = 35321, message = 35324)
		if not confirm or interface.Dialog.option(title = 35321, message = 35325):
			Backup.directImport(File.joinPath(System.path(id = System.GaiaResources), 'resources', 'settings', 'reaper.zip'))
			return True
		else:
			return False

###################################################################
# DONATIONS
###################################################################

class Donations(object):

	# Currency
	CurrencyNone = None
	CurrencyAragon = 'aragon'
	CurrencyAugur = 'augur'
	CurrencyBitcoin = 'bitcoin'
	CurrencyBitcoinCash = 'bitcoincash'
	CurrencyDash = 'dash'
	CurrencyDecred = 'decred'
	CurrencyDogecoin = 'dogecoin'
	CurrencyEos = 'eos'
	CurrencyEthereum = 'ethereum'
	CurrencyEthereumClassic = 'ethereumclassic'
	CurrencyGolem = 'golem'
	CurrencyLitecoin = 'litecoin'
	CurrencyGnosis = 'gnosis'
	CurrencyOmiseGo = 'omisego'
	CurrencyRipple = 'ripple'
	CurrencyZcash = 'zcash'

	# Popup
	PopupThreshold = 30

	@classmethod
	def donor(self):
		return System.developers() or Settings.getString('general.access.code') == Converter.base64From('ZG9ub3I=')

	@classmethod
	def coinbase(self, openLink = True):
		link = Settings.getString('link.coinbase')
		if openLink: System.openLink(link)
		return link

	@classmethod
	def exodus(self, openLink = True):
		link = Settings.getString('link.exodus')
		if openLink: System.openLink(link)
		return link

	@classmethod
	def other(self, openLink = True):
		link = Settings.getString('link.donation')
		if openLink: System.openLink(link)
		from resources.lib.extensions import interface
		return interface.Splash.popupDonations()
		return link

	@classmethod
	def show(self, currency = None):
		if currency == None:
			System.window(action = 'donationsNavigator')
		else:
			from resources.lib.extensions import interface
			from resources.lib.extensions import api
			data = api.Api.donations(currency)
			return interface.Splash.popupDonations(donation = data)

	@classmethod
	def popup(self):
		from resources.lib.extensions import orionoid
		orion = orionoid.Orionoid()
		if not self.donor() and not(orion.accountEnabled() and orion.accountValid() and orion.accountPremium()):
			from resources.lib.extensions import interface
			counter = Settings.getInteger('internal.donation')
			counter += 1
			if counter >= self.PopupThreshold:
				Settings.set('internal.donation', 0)
				if not interface.Dialog.option(title = 33505, message = 35014, labelConfirm = 35015, labelDeny = 33505):
					self.show()
					return True
			else:
				Settings.set('internal.donation', counter)
		return False

	@classmethod
	def currencies(self):
		return [
			{
				'identifier' : self.CurrencyBitcoin,
				'name' : 'Bitcoin',
				'color' : 'F7931A',
				'icon' : 'donationsbitcoin.png',
			},
			{
				'identifier' : self.CurrencyBitcoinCash,
				'name' : 'Bitcoin Cash',
				'color' : 'E97900',
				'icon' : 'donationsbitcoincash.png',
			},
			{
				'identifier' : self.CurrencyEthereum,
				'name' : 'Ethereum',
				'color' : '62688F',
				'icon' : 'donationsethereum.png',
			},
			{
				'identifier' : self.CurrencyEthereumClassic,
				'name' : 'Ethereum Classic',
				'color' : '628A6E',
				'icon' : 'donationsethereumclassic.png',
			},
			{
				'identifier' : self.CurrencyDash,
				'name' : 'Dash',
				'color' : '2588DC',
				'icon' : 'donationsdash.png',
			},
			{
				'identifier' : self.CurrencyLitecoin,
				'name' : 'Litecoin',
				'color' : 'A7A7A7',
				'icon' : 'donationslitecoin.png',
			},
			{
				'identifier' : self.CurrencyRipple,
				'name' : 'Ripple',
				'color' : '00A3DB',
				'icon' : 'donationsripple.png',
			},
			{
				'identifier' : self.CurrencyOmiseGo,
				'name' : 'OmiseGo',
				'color' : '3874F5',
				'icon' : 'donationsomisego.png',
			},
			{
				'identifier' : self.CurrencyZcash,
				'name' : 'Zcash',
				'color' : 'F5BA0D',
				'icon' : 'donationszcash.png',
			},
			{
				'identifier' : self.CurrencyDecred,
				'name' : 'Decred',
				'color' : '2ED8A3',
				'icon' : 'donationsdecred.png',
			},
		]

###################################################################
# STATISTICS
###################################################################

class Statistics(object):

	@classmethod
	def enabled(self):
		# Do not share if developer is enabled and sharing is switched off.
		return not(System.developers() and not self.sharing())

	@classmethod
	def sharing(self):
		return Settings.getBoolean('general.statistics.sharing')

	@classmethod
	def share(self, wait = False):
		thread = threading.Thread(target = self._share)
		thread.start()
		if wait: thread.join()

	@classmethod
	def _share(self):
		try:
			if not self.enabled(): return

			from resources.lib.extensions import api
			from resources.lib.extensions import debrid
			from resources.lib.extensions import network
			from resources.lib.extensions import orionoid

			orion = orionoid.Orionoid()
			data = {
				'version' : System.version(),
				'orion' : orion.accountEnabled() and orion.accountValid(),

				'system' : System.informationSystem(),
				'python' : System.informationPython(),
				'kodi' : System.informationKodi(),

				'hardware' :
				{
					'processors' : Hardware.processors(),
					'memory' : Hardware.memory(),
				},

				'premium' :
				{
					'premiumize' : debrid.Premiumize().accountValid(),
					'offcloud' : debrid.OffCloud().accountValid(),
					'realdebrid' : debrid.RealDebrid().accountValid(),
					'easynews' : debrid.EasyNews().accountValid(),
					'alldebrid' : debrid.AllDebrid().accountValid(),
					'rapidpremium' : debrid.RapidPremium().accountValid(),
				},
			}

			if self.sharing():
				information = network.Networker.information(obfuscate = True)
				information = information['global']

				# Strip important data to make it anonymous.
				information['connection']['address'] = None
				information['connection']['name'] = None
				information['location']['coordinates']['latitude'] = None
				information['location']['coordinates']['longitude'] = None

				data.update(information)

			api.Api.deviceUpdate(data = data)
		except:
			Logger.error()

###################################################################
# ANNOUNCEMENT
###################################################################

class Announcements(object):

	@classmethod
	def show(self, force = False):
		try: last = int(Settings.getString('internal.announcements'))
		except: last = None
		from resources.lib.extensions import api
		from resources.lib.extensions import interface
		if force: result = api.Api.announcements(last = force)
		else: result = api.Api.announcements(last = last)
		try:
			time = result['time']
			mode = result['mode']
			text = result['format']
			if not force: Settings.set('internal.announcements', str(time))
			if mode == 'dialog':
				interface.Dialog.confirm(title = 33962, message = text)
			elif mode == 'splash':
				interface.Splash.popupMessage(message = text)
			elif mode == 'page':
				interface.Dialog.page(title = 33962, message = text)
		except:
			pass
