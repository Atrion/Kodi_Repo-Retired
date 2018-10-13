# -*- coding: utf-8 -*-

"""
	Orion
    https://orionoid.com

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
"""

##############################################################################
# ORIONSETTINGS
##############################################################################
# Class for handling the Kodi addon settings.
##############################################################################

import re
import zipfile
import threading
import xbmcaddon
from orion.modules.oriontools import *
from orion.modules.orioninterface import *
from orion.modules.orionstream import *
from orion.modules.oriondatabase import *

OrionSettingsSilent = False
OrionSettingsBackup = False

class OrionSettings:

	##############################################################################
	# CONSTANTS
	##############################################################################

	DatabaseSettings = 'settings'
	DatabaseTemp = 'temp'

	ExtensionManual = 'zip'
	ExtensionAutomatic = 'bck'

	ParameterDefault = 'default'
	ParameterValue = 'value'
	ParameterVisible = 'visible'

	CategoryGeneral = 0
	CategoryAccount = 1
	CategoryFilters = 2

	NotificationsDisabled = 0
	NotificationsEssential = 1
	NotificationsAll = 2

	ScrapingExclusive = 0
	ScrapingSequential = 1
	ScrapingParallel = 2

	ExternalStart = '<!-- ORION FILTERS - %s START -->'
	ExternalEnd = '<!-- ORION FILTERS - %s END -->'

	##############################################################################
	# INTERNAL
	##############################################################################

	@classmethod
	def _filtersAttribute(self, attribute, type = None):
		from orion.modules.orionintegration import OrionIntegration
		if not type == None:
			type = OrionIntegration.id(type)
			if not type == 'universal':
				attribute = attribute.replace('filters.', 'filters.' + type + '.')
		return attribute

	##############################################################################
	# LAUNCH
	##############################################################################

	@classmethod
	def launch(self, category = None, section = None):
		OrionTools.execute('Addon.OpenSettings(%s)' % OrionTools.addonId())
		if not category == None: OrionTools.execute('SetFocus(%i)' % (int(category) + 100))
		if not section == None: OrionTools.execute('SetFocus(%i)' % (int(section) + 200))

	##############################################################################
	# PATH
	##############################################################################

	@classmethod
	def pathAddon(self):
		return OrionTools.pathJoin(OrionTools.addonPath(), 'resources', 'settings.xml')

	@classmethod
	def pathProfile(self):
		return OrionTools.pathJoin(OrionTools.addonProfile(), 'settings.xml')

	##############################################################################
	# SILENT
	##############################################################################

	@classmethod
	def silent(self):
		from orion.modules.orionuser import OrionUser
		global OrionSettingsSilent
		return OrionSettingsSilent or not OrionUser.instance().enabled()

	@classmethod
	def silentSet(self, silent = True):
		global OrionSettingsSilent
		OrionSettingsSilent = silent

	@classmethod
	def silentAllow(self, type = None):
		if self.silent():
			return False
		notifications = self.getGeneralNotificationsApi()
		if notifications == self.NotificationsDisabled:
			return False
		elif notifications == self.NotificationsAll:
			return True
		from orion.modules.orionapi import OrionApi
		return type == None or not type in OrionApi.Nonessential

	##############################################################################
	# DATA
	##############################################################################

	@classmethod
	def data(self):
		data = None
		path = OrionTools.pathJoin(self.pathAddon())
		with open(path, 'r') as file: data = file.read()
		return data

	@classmethod
	def _database(self):
		return OrionDatabase.instance(self.DatabaseSettings, default = OrionTools.pathJoin(OrionTools.addonPath(), 'resources'))

	##############################################################################
	# SET
	##############################################################################

	@classmethod
	def set(self, id, value, commit = True):
		if value is True or value is False:
			value = OrionTools.toBoolean(value, string = True)
		elif OrionTools.isStructure(value):
			database = self._database()
			database.insert('INSERT OR IGNORE INTO %s (id) VALUES(?);' % self.DatabaseSettings, parameters = (id,), commit = commit)
			database.update('UPDATE %s SET data = ? WHERE id = ?;' % self.DatabaseSettings, parameters = (OrionTools.jsonTo(value), id), commit = commit)
			value = ''
		else:
			value = str(value)
		OrionTools.addon().setSetting(id = id, value = value)
		if commit: self._backupAutomatic(force = True)

	##############################################################################
	# GET
	##############################################################################

	@classmethod
	def _getDatabase(self, id):
		try: return OrionTools.jsonFrom(self._database().selectValue('SELECT data FROM %s WHERE id = "%s";' % (self.DatabaseSettings, id)))
		except: return None

	@classmethod
	def get(self, id, raw = False, obfuscate = False):
		if raw:
			return self.getRaw(id = id, obfuscate = obfuscate)
		else:
			self._backupAutomatic()
			data = OrionTools.addon().getSetting(id)
			if obfuscate: data = OrionTools.obfuscate(data)
			return data

	@classmethod
	def getRaw(self, id, parameter = ParameterDefault, data = None, obfuscate = False):
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
			data = data[indexStart : indexEnd]
			if obfuscate: data = OrionTools.obfuscate(data)
			return data
		except:
			return None

	@classmethod
	def getString(self, id, raw = False, obfuscate = False):
		return self.get(id = id, raw = raw, obfuscate = obfuscate)

	@classmethod
	def getBoolean(self, id, raw = False, obfuscate = False):
		return OrionTools.toBoolean(self.get(id = id, raw = raw, obfuscate = obfuscate))

	@classmethod
	def getBool(self, id, raw = False, obfuscate = False):
		return self.getBoolean(id = id, raw = raw, obfuscate = obfuscate)

	@classmethod
	def getNumber(self, id, raw = False, obfuscate = False):
		return self.getDecimal(id = id, raw = raw, obfuscate = obfuscate)

	@classmethod
	def getDecimal(self, id, raw = False, obfuscate = False):
		value = self.get(id = id, raw = raw, obfuscate = obfuscate)
		try: return float(value)
		except: return 0

	@classmethod
	def getFloat(self, id, raw = False, obfuscate = False):
		return self.getDecimal(id = id, raw = raw, obfuscate = obfuscate)

	@classmethod
	def getInteger(self, id, raw = False, obfuscate = False):
		value = self.get(id = id, raw = raw, obfuscate = obfuscate)
		try: return int(value)
		except: return 0

	@classmethod
	def getInt(self, id, raw = False, obfuscate = False):
		return self.getInteger(id = id, raw = raw, obfuscate = obfuscate)

	@classmethod
	def getList(self, id):
		result = self._getDatabase(id)
		return [] if result == None or result == '' else result

	@classmethod
	def getObject(self, id):
		result = self._getDatabase(id)
		return None if result == None or result == '' else result

	##############################################################################
	# GET CUSTOM
	##############################################################################

	@classmethod
	def getIntegration(self, addon):
		try: return self.getString('filters.' + addon + '.integration')
		except: return ''

	@classmethod
	def getGeneralNotificationsApi(self):
		return self.getInteger('general.notifications.api')

	@classmethod
	def getGeneralNotificationsNews(self):
		return self.getBoolean('general.notifications.news')

	@classmethod
	def getGeneralScrapingTimeout(self):
		return self.getInteger('general.scraping.timeout')

	@classmethod
	def getGeneralScrapingMode(self):
		return self.getInteger('general.scraping.mode')

	@classmethod
	def getGeneralScrapingCount(self):
		return self.getInteger('general.scraping.count')

	@classmethod
	def getGeneralScrapingQuality(self, index = False):
		quality = max(0, self.getInteger('general.scraping.quality') - 1)
		if not index: quality = OrionStream.QualityOrder[quality]
		return quality

	@classmethod
	def getFiltersBoolean(self, attribute, type = None):
		return self.getBoolean(self._filtersAttribute(attribute, type))

	@classmethod
	def getFiltersInteger(self, attribute, type = None):
		return self.getInteger(self._filtersAttribute(attribute, type))

	@classmethod
	def getFiltersString(self, attribute, type = None):
		return self.getString(self._filtersAttribute(attribute, type))

	@classmethod
	def getFiltersObject(self, attribute, type = None, include = False, exclude = False):
		values = self.getObject(self._filtersAttribute(attribute, type))
		try:
			if include: values = [key for key, value in values.iteritems() if value['enabled']]
		except: pass
		try:
			if exclude: values = [key for key, value in values.iteritems() if not value['enabled']]
		except: pass
		return values if values else [] if (include or exclude) else {}

	@classmethod
	def getFiltersEnabled(self, type = None):
		return self.getFiltersBoolean('filters.enabled', type = type)

	@classmethod
	def getFiltersStreamSource(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.stream.source', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersStreamHoster(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.stream.hoster', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersMetaRelease(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.meta.release', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersMetaUploader(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.meta.uploader', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersMetaEdition(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.meta.edition', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersVideoCodec(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.video.codec', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersAudioType(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.audio.type', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersAudioCodec(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.audio.codec', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersAudioLanguages(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.audio.languages', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersSubtitleType(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.subtitle.type', type = type, include = include, exclude = exclude)

	@classmethod
	def getFiltersSubtitleLanguages(self, type = None, include = False, exclude = False):
		return self.getFiltersObject('filters.subtitle.languages', type = type, include = include, exclude = exclude)

	##############################################################################
	# SET CUSTOM
	##############################################################################

	@classmethod
	def setIntegration(self, addon, value, commit = True):
		return self.set('filters.' + addon + '.integration', value, commit = commit)

	@classmethod
	def setFilters(self, values, wait = False):
		# Do not use threads directly to update settings. Updating the settings in a threads can cause the settings file to become corrupt.
		if wait:
			self.setFiltersUpdate(values)
		else:
			thread = threading.Thread(target = self._setFiltersThread, args = (values,))
			thread.start()

	@classmethod
	def _setFiltersThread(self, values):
		# Do not pass the values as plugin parameters, since this immediately fills up the log, since Kodi prints the entire command.
		database = self._database()
		database.create('CREATE TABLE IF NOT EXISTS %s (data TEXT);' % self.DatabaseTemp)
		database.insert('INSERT INTO %s (data) VALUES(?);' % self.DatabaseTemp, parameters = (OrionTools.jsonTo([value.data() for value in values]),))
		OrionTools.executePlugin(execute = True, action = 'settingsFiltersUpdate')

	@classmethod
	def setFiltersUpdate(self, values = None):
		from orion.modules.orionintegration import OrionIntegration
		try:
			if values == None:
				database = self._database()
				values = database.selectValue('SELECT data FROM  %s;' % self.DatabaseTemp)
				database.drop(self.DatabaseTemp)
			values = OrionTools.jsonFrom(values)
			values = [OrionStream(value) for value in values]
		except: pass
		addons = [None] + OrionIntegration.Addons
		for addon in addons:
			if not addon == None: addon = OrionIntegration.id(addon)
			self.setFiltersStreamSource(values, type = addon, commit = False)
			self.setFiltersStreamHoster(values, type = addon, commit = False)
			self.setFiltersMetaRelease(values, type = addon, commit = False)
			self.setFiltersMetaUploader(values, type = addon, commit = False)
			self.setFiltersMetaEdition(values, type = addon, commit = False)
			self.setFiltersVideoCodec(values, type = addon, commit = False)
			self.setFiltersAudioType(values, type = addon, commit = False)
			self.setFiltersAudioCodec(values, type = addon, commit = False)
		self._database()._commit()
		self._backupAutomatic(force = True)

	@classmethod
	def _setFilters(self, values, setting, functionStreams, functionGet, type = None, commit = True):
		if not values: return
		items = {}
		try:
			from orion.modules.orionstream import OrionStream
			for value in values:
				attribute = getattr(value, functionStreams)()
				if not attribute == None:
					items[attribute.lower()] = {'name' : attribute.upper(), 'enabled' : True}
			settings = getattr(self, functionGet)(type = type)
			if settings:
				for key, value in items.iteritems():
					if not key in settings:
						settings[key] = value
				items = settings
		except:
			items = values
		if items: count = len([1 for key, value in items.iteritems() if value['enabled']])
		else: count = 0
		self.set(self._filtersAttribute(setting, type), items, commit = commit)
		self.set(self._filtersAttribute(setting + '.label', type), str(count) + ' ' + OrionTools.translate(32096), commit = commit)

	@classmethod
	def _setFiltersLanguages(self, values, setting, functionStreams, functionGet, type = None, commit = True):
		if not values: return
		if values: count = len([1 for key, value in values.iteritems() if value['enabled']])
		else: count = 0
		self.set(self._filtersAttribute(setting, type), values, commit = commit)
		self.set(self._filtersAttribute(setting + '.label', type), str(count) + ' ' + OrionTools.translate(32096), commit = commit)

	@classmethod
	def setFiltersLimitCount(self, value, type = None, commit = True):
		self.set(self._filtersAttribute('filters.limit.count', type), value, commit = commit)

	@classmethod
	def setFiltersLimitRetry(self, value, type = None, commit = True):
		self.set(self._filtersAttribute('filters.limit.retry', type), value, commit = commit)

	@classmethod
	def setFiltersStreamSource(self, values, type = None, commit = True):
		if not values: return
		items = {}
		try:
			from orion.modules.orionstream import OrionStream
			for value in values:
				attribute = value.streamSource()
				if not attribute == None and not attribute == '':
					items[attribute.lower()] = {'name' : attribute.upper(), 'type' : value.streamType(), 'enabled' : True}
			settings = self.getFiltersStreamSource(type = type)
			if settings:
				for key, value in items.iteritems():
					if not key in settings:
						settings[key] = value
				items = settings
		except:
			items = values
		if items: count = len([1 for key, value in items.iteritems() if value['enabled']])
		else: count = 0
		self.set(self._filtersAttribute('filters.stream.source', type), items, commit = commit)
		self.set(self._filtersAttribute('filters.stream.source.label', type), str(count) + ' ' + OrionTools.translate(32096), commit = commit)

	@classmethod
	def setFiltersStreamHoster(self, values, type = None, commit = True):
		if not values: return
		items = {}
		try:
			from orion.modules.orionstream import OrionStream
			for value in values:
				attribute = value.streamHoster()
				if not attribute == None and not attribute == '':
					items[attribute.lower()] = {'name' : attribute.upper(), 'enabled' : True}
			settings = self.getFiltersStreamHoster(type = type)
			if settings:
				for key, value in items.iteritems():
					if not key in settings:
						settings[key] = value
				items = settings
		except:
			items = values
		if items: count = len([1 for key, value in items.iteritems() if value['enabled']])
		else: count = 0
		self.set(self._filtersAttribute('filters.stream.hoster', type), items, commit = commit)
		self.set(self._filtersAttribute('filters.stream.hoster.label', type), str(count) + ' ' + OrionTools.translate(32096), commit = commit)

	@classmethod
	def setFiltersMetaRelease(self, values, type = None, commit = True):
		self._setFilters(values, 'filters.meta.release', 'metaRelease', 'getFiltersMetaRelease', type, commit = commit)

	@classmethod
	def setFiltersMetaUploader(self, values, type = None, commit = True):
		self._setFilters(values, 'filters.meta.uploader', 'metaUploader', 'getFiltersMetaUploader', type, commit = commit)

	@classmethod
	def setFiltersMetaEdition(self, values, type = None, commit = True):
		self._setFilters(values, 'filters.meta.edition', 'metaEdition', 'getFiltersMetaEdition', type, commit = commit)

	@classmethod
	def setFiltersVideoCodec(self, values, type = None, commit = True):
		self._setFilters(values, 'filters.video.codec', 'videoCodec', 'getFiltersVideoCodec', type, commit = commit)

	@classmethod
	def setFiltersAudioType(self, values, type = None, commit = True):
		self._setFilters(values, 'filters.audio.type', 'audioType', 'getFiltersAudioType', type, commit = commit)

	@classmethod
	def setFiltersAudioCodec(self, values, type = None, commit = True):
		self._setFilters(values, 'filters.audio.codec', 'audioCodec', 'getFiltersAudioCodec', type, commit = commit)

	@classmethod
	def setFiltersAudioLanguages(self, values, type = None, commit = True):
		self._setFiltersLanguages(values, 'filters.audio.languages', 'audioLanguages', 'getFiltersAudioLanguages', type, commit = commit)

	@classmethod
	def setFiltersSubtitleType(self, values, type = None, commit = True):
		self._setFilters(values, 'filters.subtitle.type', 'subtitleType', 'getFiltersSubtitleType', type, commit = commit)

	@classmethod
	def setFiltersSubtitleLanguages(self, values, type = None, commit = True):
		self._setFiltersLanguages(values, 'filters.subtitle.languages', 'subtitleLanguages', 'getFiltersSubtitleLanguages', type, commit = commit)

	##############################################################################
	# BACKUP
	##############################################################################

	@classmethod
	def _backupPath(self, clear = False):
		path = OrionTools.pathResolve('special://temp/')
		path = OrionTools.pathJoin(path, OrionTools.addonName().lower(), 'backup')
		OrionTools.directoryDelete(path)
		OrionTools.directoryCreate(path)
		return path

	@classmethod
	def _backupName(self, extension = ExtensionManual):
		# Windows does not support colons in file names.
		return OrionTools.addonName() + ' ' + OrionTools.translate(32170) + ' ' + OrionTools.timeFormat(format = '%Y-%m-%d %H.%M.%S') + '%s.' + extension

	@classmethod
	def _backupAutomaticValid(self):
		return OrionTools.toBoolean(OrionTools.addon().getSetting(id = 'internal.backup'))

	@classmethod
	def _backupAutomatic(self, force = False):
		if not self._backupAutomaticValid() or OrionTools.toBoolean(OrionTools.addon().getSetting(id = 'general.backup.automatic')):
			if not self._backupAutomaticImport(force = force):
				self._backupAutomaticExport(force = force)

	@classmethod
	def _backupAutomaticExport(self, force = False):
		global OrionSettingsBackup
		OrionTools.addon().setSetting(id = 'internal.backup', value = OrionTools.toBoolean(True, string = True))
		if force or not OrionSettingsBackup:
			OrionSettingsBackup = True
			directory = OrionTools.addonProfile()
			fileFrom = OrionTools.pathJoin(directory, 'settings.xml')
			if 'internal.backup' in OrionTools.fileRead(fileFrom):
				fileTo = OrionTools.pathJoin(directory, 'settings.' + self.ExtensionAutomatic)
				OrionTools.fileCopy(fileFrom, fileTo, overwrite = True)
				return True
		return False

	@classmethod
	def _backupAutomaticImport(self, force = False):
		if self._backupAutomaticValid():
			return force # Must return force
		else:
			directory = OrionTools.addonProfile()
			fileTo = OrionTools.pathJoin(directory, 'settings.xml')
			fileFrom = OrionTools.pathJoin(directory, 'settings.' + self.ExtensionAutomatic)
			OrionTools.fileCopy(fileFrom, fileTo, overwrite = True)
			return True

	@classmethod
	def backupImport(self, path = None, extension = ExtensionManual):
		try:
			from orion.modules.orionuser import OrionUser

			if path == None: path = OrionInterface.dialogBrowse(title = 32170, type = OrionInterface.BrowseFile, mask = extension)

			directory = self._backupPath(clear = True)
			directoryData = OrionTools.addonProfile()

			file = zipfile.ZipFile(path, 'r')
			file.extractall(directory)
			file.close()

			directories, files = OrionTools.directoryList(directory)
			counter = 0
			for file in files:
				fileFrom = OrionTools.pathJoin(directory, file)
				fileTo = OrionTools.pathJoin(directoryData, file)
				if OrionTools.fileMove(fileFrom, fileTo, overwrite = True):
					counter += 1

			OrionTools.directoryDelete(path = directory, force = True)

			# Get updated user status
			OrionInterface.loaderShow()
			OrionUser.instance().update()
			OrionInterface.loaderHide()

			if counter > 0:
				OrionInterface.dialogNotification(title = 32170, message = 33014, icon = OrionInterface.IconSuccess)
				return True
			else:
				OrionInterface.dialogNotification(title = 32170, message = 33016, icon = OrionInterface.IconError)
				return False
		except:
			OrionInterface.dialogNotification(title = 32170, message = 33016, icon = OrionInterface.IconError)
			OrionTools.error()
			return False

	@classmethod
	def backupExport(self, path = None, extension = ExtensionManual):
		try:
			if path == None: path = OrionInterface.dialogBrowse(title = 32170, type = OrionInterface.BrowseDirectoryWrite)

			OrionTools.directoryCreate(path)
			name = self._backupName(extension = extension)
			path = OrionTools.pathJoin(path, name)
			counter = 0
			suffix = ''
			while OrionTools.fileExists(path % suffix):
				counter += 1
				suffix = ' [%d]' % counter
			path = path % suffix

			file = zipfile.ZipFile(path, 'w')

			directory = self._backupPath(clear = True)
			directoryData = OrionTools.addonProfile()
			directories, files = OrionTools.directoryList(directoryData)

			content = []
			settings = ['settings.xml', (self.DatabaseSettings + OrionDatabase.Extension).lower()]
			for i in range(len(files)):
				if files[i].lower() in settings:
					content.append(files[i])

			tos = [OrionTools.pathJoin(directory, i) for i in content]
			froms = [OrionTools.pathJoin(directoryData, i) for i in content]

			for i in range(len(content)):
				try:
					OrionTools.fileCopy(froms[i], tos[i], overwrite = True)
					file.write(tos[i], content[i])
				except: pass

			file.close()
			OrionTools.directoryDelete(path = directory, force = True)
			if OrionTools.fileExists(path):
				OrionInterface.dialogNotification(title = 32170, message = 33013, icon = OrionInterface.IconSuccess)
				return True
			else:
				OrionInterface.dialogNotification(title = 32170, message = 33015, icon = OrionInterface.IconError)
				return False
		except:
			OrionInterface.dialogNotification(title = 32170, message = 33015, icon = OrionInterface.IconError)
			OrionTools.error()
			return False

	##############################################################################
	# EXTERNAL
	##############################################################################

	@classmethod
	def _externalId(self, addon):
		from orion.modules.orionintegration import OrionIntegration
		return OrionIntegration.id(addon)

	@classmethod
	def _externalComment(self, addon):
		return self._externalId(addon).upper()

	@classmethod
	def _externalStart(self, addon):
		return self.ExternalStart % self._externalComment(addon)

	@classmethod
	def _externalEnd(self, addon):
		return self.ExternalEnd % self._externalComment(addon)

	@classmethod
	def _externalClean(self, data):
		while re.search('(\r?\n){3,}', data): data = re.sub('(\r?\n){3,}', '\n\n', data)
		return data

	@classmethod
	def externalCategory(self, addon):
		if addon == None: return self.launch(OrionSettings.CategoryFilters)
		addonId = self._externalId(addon)
		if addon == 'universal': return self.launch(OrionSettings.CategoryFilters)
		data = OrionTools.fileRead(self.pathAddon())
		data = data[:data.find('filters.' + addon)]
		self.launch(data.count('<category') - 1)

	@classmethod
	def externalInsert(self, addon):
		self.externalRemove(addon)
		data = OrionTools.fileRead(self.pathAddon())

		commentStart = self._externalStart('universal')
		commentEnd = self._externalEnd('universal')

		addonId = self._externalId(addon)
		addonComment = self._externalComment(addon)

		subset = data[data.find(commentStart) + len(commentStart) : data.find(commentEnd)].strip('\n').strip('\r')

		index = subset.find('filters.addon')
		subset = subset[:index] + subset[index:].replace('default="false"', 'default="true"', 1)

		index = subset.find('filters.enabled')
		subset = subset[:index] + subset[index:].replace('default="true"', 'default="false"', 1)

		subset = subset.replace('&type=universal', '&type=' + addonId)
		subset = subset.replace('id="filters.', 'id="filters.' + addonId + '.')

		addonStart = '\n\n' + self.ExternalStart % addonComment + '\n<category label = "' + addon.title() + '">'
		addonEnd = '</category>\n' + self.ExternalEnd % addonComment + '\n'
		subset = addonStart + subset + addonEnd

		end = '</category>'
		end = data.rfind(end) + len(end)
		data = data[:end] + subset + data[end:]
		OrionTools.fileWrite(self.pathAddon(), self._externalClean(data))

		database = OrionDatabase(path = OrionTools.pathJoin(OrionTools.addonPath(), 'resources', self.DatabaseSettings + OrionDatabase.Extension))
		settings = database.select('SELECT id, data FROM  %s;' % self.DatabaseSettings)
		for setting in settings:
			if setting[0].startswith('filters.'):
				OrionSettings.set(self._filtersAttribute(setting[0], addonId), OrionTools.jsonFrom(setting[1]))

	@classmethod
	def externalRemove(self, addon):
		data = OrionTools.fileRead(self.pathAddon())
		commentStart = self._externalStart(addon)
		commentEnd = self._externalEnd(addon)
		indexStart = data.find(commentStart)
		indexEnd = data.find(commentEnd)
		if indexStart > 0 and indexEnd > indexStart:
			data = data[:indexStart] + data[indexEnd + len(commentEnd):]
		OrionTools.fileWrite(self.pathAddon(), self._externalClean(data))

	@classmethod
	def externalClean(self):
		from orion.modules.orionintegration import OrionIntegration
		data = OrionTools.fileRead(self.pathAddon())
		for addon in OrionIntegration.Addons:
			commentStart = self._externalStart(addon)
			commentEnd = self._externalEnd(addon)
			indexStart = data.find(commentStart)
			indexEnd = data.find(commentEnd)
			if indexStart > 0 and indexEnd > indexStart:
				data = data[:indexStart] + data[indexEnd + len(commentEnd):]
		OrionTools.fileWrite(self.pathAddon(), self._externalClean(data))
