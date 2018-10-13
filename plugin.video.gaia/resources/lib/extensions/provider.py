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

import re
import os
import sys
import imp
import json
import copy
import pkgutil
import urlparse
import time
import threading

from resources.lib.extensions import database

class Provider(object):

	DatabaseName = 'providers'
	DatabaseProviders = 'providers'
	DatabaseFailure = 'failure'

	# If enabled is false, retrieves all providers, even if they are disbaled in the settings.
	# If local is false, excludes local providers.
	# If object is true, it will create an instance of the class.

	Providers = None

	# Categories - must have the same value as the directory name
	CategoryUnknown = None
	CategoryGeneral = 'general'
	CategoryTorrent = 'torrent'
	CategoryUsenet = 'usenet'
	CategoryHoster = 'hoster'
	CategoryExternal = 'external'
	Categories = [CategoryGeneral, CategoryTorrent, CategoryUsenet, CategoryHoster, CategoryExternal]

	# Types - must have the same value as the directory name
	TypeUnknown = None
	TypeUniversal = 'universal'
	TypeLocal = 'local'
	TypePremium = 'premium'
	TypeFrench = 'french'
	TypeRussian = 'russian'
	Types = [TypeUniversal, TypeLocal, TypePremium, TypeFrench, TypeRussian]

	# Modes - must have the same value as the directory name
	ModeUnknown = None
	ModeOpen = 'open'
	ModeMember = 'member'

	# Groups
	GroupUnknown = None
	GroupMovies = 'movies'
	GroupTvshows = 'tvshows'
	GroupAll = 'all'

	PerformanceSlow = 'slow'
	PerformanceMedium = 'medium'
	PerformanceFast = 'fast'

	@classmethod
	def __name(self, data, setting):
		name = ''
		if data:
			dummy = True
			index = 0
			setting = setting.lower()
			while dummy:
				index = data.find(setting, index)
				if index < 0: break
				dummy = 'visible="false"' in data[index : data.find('/>', index)]
				index += 1
			if dummy: index = -1

			if index >= 0:
				index = data.find('label="', index)
				if index >= 0:
					name = data[index + 7 : data.find('" ', index)]
					if name.isdigit():
						from resources.lib.extensions import interface
						name = interface.Translation.string(int(name))
		return name

	@classmethod
	def __domain(self, link):
		domain = urlparse.urlparse(link).netloc
		isIp = re.match('(?:\d{1,3}\.){3}\d{1,3}', domain)
		if not isIp:
			index = domain.rfind('.')
			if index >= 0:
				index = domain.rfind('.', 0, index)
				if index >= 0:
					return domain[index + 1:]
		return domain

	@classmethod
	def _databaseInitialize(self):
		base = database.Database(name = self.DatabaseName)
		base._create('CREATE TABLE IF NOT EXISTS %s (version TEXT, data TEXT, UNIQUE(version));' % self.DatabaseProviders)
		return base

	@classmethod
	def _databaseRetrieve(self, description = None, enabled = False, forceAll = False, forcePreset = None, quick = False):
		try:
			from resources.lib.extensions import tools
			base = self._databaseInitialize()
			result = base._selectSingle('SELECT version, data FROM %s;' % (self.DatabaseProviders))
			version = result[0]
			if version == tools.System.version():
				if quick:
					data = tools.Converter.jsonFrom(result[1])
					#return len(data) > 0
					return data
				else:
					from resources.lib.extensions import handler
					handleDirect = handler.Handler(type = handler.Handler.TypeDirect)
					handleTorrent = handler.Handler(type = handler.Handler.TypeTorrent)
					handleUsenet = handler.Handler(type = handler.Handler.TypeUsenet)
					handleHoster = handler.Handler(type = handler.Handler.TypeHoster)

					failures = self.failureList()

					try:
						force = not forcePreset == None
						if force: forcePreset = tools.Settings.getObject('providers.customization.presets.values%d' % int(forcePreset))
					except:
						force = False

					data = tools.Converter.jsonFrom(result[1])
					providers = []

					for i in range(len(data)):
						provider = data[i]
						allow = False
						id = provider['id']
						setting = provider['setting']
						settingCategory = provider['settingcategory']

						if not force and tools.Settings.getBoolean(settingCategory): allow = True
						elif forceAll: allow = True
						try:
							if force and settingCategory in forcePreset['categories']: allow = True
						except: pass

						if allow:
							enabled1 = tools.Settings.getBoolean(settingCategory)
							enabled2 = tools.Settings.getBoolean(provider['setting'])
							enabled3 = not id in failures
							enabledAll = True if force else (enabled1 and enabled2 and enabled3)

							if enabled and not enabledAll: continue # Saves time to exclude disabled providers.

							type = provider['type']
							file = provider['file']
							if not description == None: # Saves time when only a single provider is needed.
								if not(id == description or provider['name'].lower() == description or setting == description or file == description):
									continue

							try:
								if force and not setting in forcePreset['providers']: continue
							except: pass

							try:
								if type == handler.Handler.TypeDirect:
									if not handleDirect.supported(): continue
								elif type == handler.Handler.TypeTorrent:
									if not handleTorrent.supported(): continue
								elif type == handler.Handler.TypeUsenet:
									if not handleUsenet.supported(): continue
								elif type == handler.Handler.TypeHoster:
									if not handleHoster.supported(): continue
							except: pass

							classPointer = imp.load_source(file.replace('.py', ''), provider['path']) # Don't use id, since the ids from external addons aare changed.
							provider['class'] = classPointer
							provider['object'] = classPointer.source()

							try:
								instanceFunction = getattr(provider['object'], 'instanceParameterize')
								if instanceFunction and callable(instanceFunction): instanceFunction(provider['parameters'])
							except:
								pass

							try:
								instanceFunction = getattr(provider['object'], 'instanceEnabled')
								if instanceFunction and callable(instanceFunction): enabledAll = enabledAll and instanceFunction()
								if enabled and not enabledAll: continue # Saves time to exclude disabled providers.
							except:
								pass

							provider['selected'] = True if force else (enabled1 and enabled2)
							provider['enabled'] = enabledAll

							# Replace custom links which were retrieved from the settings.
							provider['object'].base_link = provider['link']

							providers.append(provider)

							if not description == None:
								break

					return providers
		except:
			pass
		return None

	@classmethod
	def _databaseUpdate(self, data):
		try:
			from resources.lib.extensions import tools
			self.databaseClear()
			base = self._databaseInitialize()
			data = '"%s"' % tools.Converter.jsonTo(data).replace('"', '""').replace("'", "''")
			base._insert('INSERT INTO %s (version, data) VALUES ("%s", %s);' % (self.DatabaseProviders, tools.System.version(), data))
		except:
			tools.Logger.error()

	@classmethod
	def databaseClear(self):
		database.Database(name = self.DatabaseName)._drop(self.DatabaseProviders)

	@classmethod
	def launch(self):
		thread = threading.Thread(target = self.initialize, args = (None, False, True, None, True))
		thread.start()

	@classmethod
	def initialize(self, description = None, enabled = False, forceAll = False, forcePreset = None, progress = False, special = False):
		try:
			from resources.lib.extensions import tools
			from resources.lib.extensions import interface

			progressDialog = None
			self.Providers = []
			data = self._databaseRetrieve(description = description, enabled = enabled, forceAll = forceAll, forcePreset = forcePreset, quick = progress)

			if not data:
				if progress: progressDialog = interface.Dialog.progress(title = 35147, message = 35148, background = True)

				root = os.path.join(tools.System.path(), 'resources')
				settingsData = tools.Settings.data()
				customLinks = tools.Settings.getObject('providers.customization.locations.value')

				providers = []
				data = []
				files = []

				if progress: total = 185 # +- the total number of providers

				if special:
					total = 1
					path1 = [os.path.join(root, 'lib', 'providers', 'general', 'special', 'member')]
					for package1, name1, pkg1 in pkgutil.walk_packages(path1):
						if not pkg1:
							files.append([path1[0], name1])
							if progress: progressDialog.update(int(40 * (len(files) / total)))
				else:
					path1 = [os.path.join(root, 'lib', 'providers')]
					for package1, name1, pkg1 in pkgutil.walk_packages(path1):
						path2 = [os.path.join(path1[0], name1)]
						for package2, name2, pkg2 in pkgutil.walk_packages(path2):
							path3 = [os.path.join(path2[0], name2)]
							for package3, name3, pkg3 in pkgutil.walk_packages(path3):
								path4 = [os.path.join(path3[0], name3)]
								for package4, name4, pkg4 in pkgutil.walk_packages(path4):
									if not pkg4:
										files.append([path4[0], name1, name2, name3, name4])
										if progress: progressDialog.update(int(40 * (len(files) / total)))

				if progress:
					total = len(files)
					providersExtras = 0

				for f in files:
					try:
						directory = f[0]
						settingCategory = 'providers.%s.%s.%s.enabled' % (f[1], f[2], f[3])

						typed = f[2]
						id = f[4]
						setting = '.'.join(['providers', f[1], typed, f[3], id])

						# Ignore developer providers
						try:
							if not tools.System.developers() and tools.System.developersCode() in tools.Settings.raw(setting, parameter = tools.Settings.ParameterVisible):
								continue
						except:
							pass

						name = self.__name(settingsData, setting)
						file = id + '.py'

						path = os.path.join(directory, file)
						classPointer = imp.load_source(id, path)
						object = classPointer.source()

						instances = []
						try:
							instanceFunction = getattr(object, 'instances')
							if callable(instanceFunction): instances = instanceFunction()
						except:
							instances.append(object)

						instancesMulti = len(instances) > 1
						if progress and instancesMulti: providersExtras += len(instances) - 1

						for instance in instances:

							if instancesMulti:
								try:
									instanceFunction = getattr(instance, 'instanceId')
									if callable(instanceFunction): id = instanceFunction()
								except:
									pass
								try:
									instanceFunction = getattr(instance, 'instanceName')
									if callable(instanceFunction): name = instanceFunction()
								except:
									pass

							try: pack = instance.pack
							except: pack = False

							try:
								functionMovie = getattr(instance, 'movie', None)
								groupMovies = True if callable(functionMovie) else False
							except:
								groupMovies = False

							try:
								functionTvshow = getattr(instance, 'tvshow', None)
								functionEpisode = getattr(instance, 'episode', None)
								groupTvshows = True if callable(functionTvshow) or callable(functionEpisode) else False
							except:
								groupTvshows = False

							parameters = None
							try:
								functionParameters = getattr(instance, 'instanceParameters')
								if callable(functionParameters): parameters = functionParameters()
							except:
								pass

							if groupMovies and groupTvshows: group = self.GroupAll
							elif groupMovies: group = self.GroupMovies
							elif groupTvshows: group = self.GroupTvshows
							else: group = self.GroupUnknown

							link = None
							domain = None
							links = []
							domains = []
							language = None
							languages = []
							genres = []

							if hasattr(instance, 'domains') and isinstance(instance.domains, (list, tuple)) and len(instance.domains) > 0:
								domains = instance.domains
								for i in range(len(domains)):
									if domains[i].startswith('http'):
										domains[i] = self.__domain(domains[i])

							if hasattr(instance, 'language') and isinstance(instance.language, (list, tuple)) and len(instance.language) > 0:
								languages = instance.language
								language = languages[0]

							if hasattr(instance, 'genre_filter') and isinstance(instance.genre_filter, (list, tuple)) and len(instance.genre_filter) > 0:
								genres = instance.genre_filter

							# _base_link: Do not use base_link that is defined as a property (eg: KinoX), since this can make additional HTTP requests, slowing down the process.
							if not hasattr(instance, '_base_link') and hasattr(instance, 'base_link'):
								if customLinks and id in customLinks:
									instance.base_link = customLinks[id]
								link = instance.base_link
							if link == None and len(domains) > 0:
								link = domains[0]

							if not link == None:
								if not link.startswith('http'):
									link = 'http://' + link
								links.append(link)
								domain = self.__domain(link)
								domains.append(domain)

							for d in domains:
								if not d.startswith('http'):
									d = 'http://' + d
								links.append(d)
							if domain == None and len(domains) > 0:
								domain = domains[0]

							# Remove duplicates
							links = list(set(links))
							domains = list(set(domains))

							source = {}

							source['parameters'] = parameters

							source['category'] = f[1]
							source['type'] = typed
							source['mode'] = f[3]
							source['group'] = group

							source['link'] = link
							source['links'] = links
							source['domain'] = domain
							source['domains'] = domains

							source['language'] = language
							source['languages'] = languages
							source['genres'] = genres

							source['id'] = id
							source['name'] = name
							source['pack'] = pack
							source['setting'] = setting
							source['settingcategory'] = settingCategory
							source['selected'] = True
							source['enabled'] = True

							source['file'] = file
							source['directory'] = directory
							source['path'] = path

							providers.append(source)

						if progress:
							total = len(files)
							progressDialog.update(int(40 + (50 * ((len(providers) - providersExtras) / float(total)))))

					except Exception as error:
						tools.Logger.log('A provider could not be loaded (%s): %s.' % (str(f[4]), str(error)))
						tools.Logger.error()

				self._databaseUpdate(providers)
				if progress: progressDialog.update(100)
				data = self._databaseRetrieve(description = description, enabled = enabled, forceAll = forceAll, forcePreset = forcePreset)

			self.Providers = data
		except Exception as error:
			tools.Logger.log('The providers could not be loaded (%s).' % str(error))
			tools.Logger.error()

		if progressDialog:
			try: progressDialog.close()
			except: pass

		return self.Providers

	# description can be id, name, file, or setting.
	# exact to match alternative names, eg szukajka vs szukajkatv
	@classmethod
	def _providerEqual(self, source, description, exact = True):
		if exact:
			if source['id'] == description or source['name'] == description or source['setting'] == description or source['file'] == description:
				return True
		else:
			if source['id'] in description or description in source['id'] or source['name'] in description or description in source['name'] or source['setting'] in description or description in source['setting'] or source['file'] in description or description in source['file']:
				return True
		return False

	# description can be id, name, file, or setting.
	@classmethod
	def provider(self, description, enabled = True, local = True, genres = None, exact = True):
		from resources.lib.extensions import tools
		description = description.lower().replace(' ', '') # Important for "local library".
		sources = self.providers(description = description if exact else None, enabled = enabled, local = local, genres = genres)
		for source in sources:
			if self._providerEqual(source, description, exact = exact):
				return source
		return None

	@classmethod
	def providers(self, description = None, enabled = True, local = True, genres = None, excludes = None):
		# Extremley important. Only detect providers the first time.
		# If the providers are searched every time, this creates a major overhead and slow-down during the prechecks: sources.sourcesResolve() through the networker.
		if self.Providers == None:
			self.initialize(description = description, enabled = enabled)
		from resources.lib.extensions import tools
		sources = []
		for i in range(len(self.Providers)):

			source = self.Providers[i]
			if enabled and not source['enabled']:
				continue

			if not local and source['type'] == self.TypeLocal:
				continue

			sourceGenres = source['genres']
			if genres and len(genres) > 0 and sourceGenres and len(sourceGenres) > 0 and not any(genre in sourceGenres for genre in genres):
				continue

			if not excludes == None:
				exclude = False
				for ex in excludes:
					if self._providerEqual(source, ex):
						exclude = True
						break
				if exclude:
					continue

			sources.append(source)

		# Clear providers in case only a single one was searched.
		if not description == None:
			self.Providers = None

		return sources

	@classmethod
	def providersMovies(self, enabled = True, local = True, genres = None, excludes = None):
		sources = self.providers(enabled = enabled, local = local, genres = genres, excludes = excludes)
		return [i for i in sources if i['group'] == self.GroupMovies or i['group'] == self.GroupAll]

	@classmethod
	def providersTvshows(self, enabled = True, local = True, genres = None, excludes = None):
		sources = self.providers(enabled = enabled, local = local, genres = genres, excludes = excludes)
		return [i for i in sources if i['group'] == self.GroupTvshows or i['group'] == self.GroupAll]

	@classmethod
	def providersAll(self, enabled = True, local = True, genres = None, excludes = None):
		sources = self.providers(enabled = enabled, local = local, genres = genres, excludes = excludes)
		return [i for i in sources if i['group'] == self.GroupAll]

	@classmethod
	def providersTorrent(self, enabled = True, genres = None, excludes = None):
		sources = self.providers(enabled = enabled, genres = genres, excludes = excludes)
		return [i for i in sources if i['category'] == self.CategoryTorrent]

	@classmethod
	def providersUsenet(self, enabled = True, genres = None, excludes = None):
		sources = self.providers(enabled = enabled, genres = genres, excludes = excludes)
		return [i for i in sources if i['category'] == self.CategoryUsenet]

	@classmethod
	def providersHoster(self, enabled = True, genres = None, excludes = None):
		sources = self.providers(enabled = enabled, genres = genres, excludes = excludes)
		return [i for i in sources if i['type'] == self.CategoryHoster]

	@classmethod
	def names(self, enabled = True, local = True, genres = None, excludes = None):
		sources = self.providers(enabled = enabled, local = local, genres = genres, excludes = excludes)
		return [i['name'] for i in sources]

	@classmethod
	def _failureInitialize(self):
		data = database.Database(name = self.DatabaseName)
		data._create('CREATE TABLE IF NOT EXISTS %s (id TEXT, count INTEGER, time INTEGER, UNIQUE(id));' % self.DatabaseFailure)
		return data

	@classmethod
	def failureClear(self):
		database.Database(name = self.DatabaseName)._drop(self.DatabaseFailure)

	@classmethod
	def failureEnabled(self):
		from resources.lib.extensions import tools
		return tools.Settings.getBoolean('scraping.failure.enabled')

	@classmethod
	def failureList(self):
		result = []
		if self.failureEnabled():
			from resources.lib.extensions import tools

			thresholdCount = tools.Settings.getInteger('scraping.failure.count')
			thresholdTime = tools.Settings.getInteger('scraping.failure.time')
			if thresholdTime > 0:
				thresholdTime = thresholdTime * 86400 # Convert to seconds.
				thresholdTime = tools.Time.timestamp() - thresholdTime

			data = self._failureInitialize()
			result = data._selectValues('SELECT id FROM %s WHERE NOT (count < %d OR time < %d);' % (self.DatabaseFailure, thresholdCount, thresholdTime))
		return result

	@classmethod
	def failureUpdate(self, finished, unfinished):
		if self.failureEnabled():
			from resources.lib.extensions import tools
			from resources.lib.extensions import orionoid

			data = self._failureInitialize()
			current = data._selectValues('SELECT id FROM %s;' % self.DatabaseFailure)
			timestamp = tools.Time.timestamp()

			for id in finished:
				if not orionoid.Orionoid.Scraper in id:
					if id in current:
						data._update('UPDATE %s SET count = 0, time = %d WHERE id = "%s";' % (self.DatabaseFailure, timestamp, id), commit = False)
					else:
						data._insert('INSERT INTO %s (id, count, time) VALUES ("%s", 0, %d);' % (self.DatabaseFailure, id, timestamp), commit = False)

			for id in unfinished:
				if not orionoid.Orionoid.Scraper in id:
					if id in current:
						data._update('UPDATE %s SET count = count + 1, time = %d WHERE id = "%s";' % (self.DatabaseFailure, timestamp, id), commit = False)
					else:
						data._insert('INSERT INTO %s (id, count, time) VALUES ("%s", 1, %d);' % (self.DatabaseFailure, id, timestamp), commit = False)

			data._commit()

	# mode: manual or automatic
	@classmethod
	def sortDialog(self, mode, slot):
		from resources.lib.extensions import tools
		from resources.lib.extensions import interface

		interface.Loader.show()
		providers = self.providers(enabled = True, local = False)
		items = [interface.Format.fontBold(33112)]
		items += [i['name'] for i in providers]
		interface.Loader.hide()

		index = interface.Dialog.options(title = 33196, items = items)
		if index < 0: return False
		elif index == 0: provider = ''
		else: provider = items[index]

		id = 'playback.%s.sort.provider%d' % (mode, int(slot))
		tools.Settings.set(id = id, value = provider)

		slot = tools.Settings.CategoryManual if mode == 'manual' else tools.Settings.CategoryAutomation
		tools.Settings.launch(slot)

		return True

	@classmethod
	def presetDialog(self, slot):
		from resources.lib.extensions import tools
		from resources.lib.extensions import interface

		slot = int(slot)
		slotValues = 'providers.customization.presets.values%d' % slot
		slotPreset = 'providers.customization.presets.preset%d' % slot

		current = tools.Settings.getObject(slotValues)
		if current == None: option = True
		else: option = interface.Dialog.option(title = 33682, message = 33684, labelConfirm = 33686, labelDeny = 33685)

		if option:
			name = tools.Settings.getString(slotPreset)
			if not name == None and not name == '':
				index = name.find(' (')
				if index >= 0:
					name = name[:index]
			interface.Loader.hide()
			name = interface.Dialog.input(title = 33687, type = interface.Dialog.InputAlphabetic, default = name)
			if name == None or name == '':
				tools.Settings.set(slotValues, '')
				tools.Settings.set(slotPreset, '')
				interface.Dialog.notification(title = 33692, message = 33689, icon = interface.Dialog.IconSuccess)
				tools.Settings.launch(category = tools.Settings.CategoryProviders)
				interface.Loader.hide()
				return False
			interface.Loader.show()

		interface.Loader.show()
		providers = self.providers(enabled = False, local = True)
		categories = list(set([i['settingcategory'] for i in providers]))

		if option:
			items = []
			for i in providers:
				if i['selected']:
					items.append(i['setting'])

			name = '%s (%d)' % (name, len(items))
			tools.Settings.set(slotPreset, name)

			categoriesSelected = [i for i in categories if tools.Settings.getBoolean(i)]
			items = {'categories' : categoriesSelected, 'providers' : items}
			tools.Settings.set(slotValues, items)

			interface.Dialog.notification(title = 33692, message = 33688, icon = interface.Dialog.IconSuccess)
		else:
			for i in categories: tools.Settings.set(i, False)
			for i in providers: tools.Settings.set(i['setting'], False)

			currentCategories = current['categories']
			currentProviders = current['providers']
			for i in currentCategories: tools.Settings.set(i, True)
			for i in currentProviders: tools.Settings.set(i, True)

			interface.Dialog.notification(title = 33692, message = 33690, icon = interface.Dialog.IconSuccess)

		tools.Settings.launch(category = tools.Settings.CategoryProviders)
		interface.Loader.hide()

		return True

	@classmethod
	def language(self):
		from resources.lib.extensions import tools
		if tools.Language.customization():
			language = tools.Settings.getString('scraping.foreign.language')
		else:
			language = tools.Language.Alternative
		return tools.Language.code(language)

	@classmethod
	def languageSelect(self):
		from resources.lib.extensions import tools
		from resources.lib.extensions import interface
		id = 'scraping.foreign.language'
		items = tools.Settings.raw(id, 'values').split('|')
		choice = interface.Dialog.select(title = 33787, items = items)
		if choice >= 0: tools.Settings.set(id, items[choice])

	@classmethod
	def _optimizationPerformance(self, performance):
		from resources.lib.extensions import interface
		if performance == self.PerformanceSlow: return interface.Translation.string(33997)
		elif performance == self.PerformanceFast: return interface.Translation.string(33998)
		else: return interface.Translation.string(33999)

	@classmethod
	def optimizationDevice(self):
		from resources.lib.extensions import tools
		from resources.lib.extensions import interface
		from resources.lib.extensions import convert
		try:
			hardware = tools.Hardware.performance()
			hardwareProcessors = tools.Hardware.processors()
			hardwareMemory = tools.Hardware.memory()
			hardwareMemory = convert.ConverterSize(value = hardwareMemory).stringOptimal()

			labels = []
			label = self._optimizationPerformance(hardware)
			if hardwareProcessors: labels.append(str(hardwareProcessors) + ' ' + interface.Translation.string(35003))
			if hardwareMemory: labels.append(str(hardwareMemory) + ' ' + interface.Translation.string(35004))
			if len(labels) > 0: label += ' (%s)' % (', '.join(labels))

			if hardware == tools.Hardware.PerformanceFast: timeout = 10
			elif hardware == tools.Hardware.PerformanceMedium: timeout = 15
			else: timeout = 20

			return (timeout, label)
		except:
			tools.Logger.error()
			return (10, interface.Translation.string(33387))

	@classmethod
	def optimizationConnection(self, iterations = 3):
		from resources.lib.extensions import tools
		from resources.lib.extensions import interface
		from resources.lib.extensions import speedtest
		try:
			minimum = 0
			maximum = 9999999999
			latency = maximum
			download = minimum
			latencyLabel = None
			downloadLabel = None

			for i in range(iterations):
				speedtester = speedtest.SpeedTesterGlobal()
				speedtester.performance()
				if speedtester.latency() < latency:
					latency = speedtester.latency()
				if speedtester.download() > download:
					download = speedtester.download()

			if latency == maximum: latency = None
			if download == minimum: download = None
			speedtester = speedtest.SpeedTesterGlobal()
			speedtester.latencySet(latency)
			speedtester.downloadSet(download)
			performance = speedtester.performance(test = False)

			labels = []
			label = self._optimizationPerformance(performance)
			download = speedtester.formatDownload(unknown = None)
			latency = speedtester.formatLatency(unknown = None)
			if download: labels.append(download)
			if latency: labels.append(latency)
			if len(labels) > 0: label += ' (%s)' % (', '.join(labels))

			if performance == speedtest.SpeedTester.PerformanceFast: timeout = 10
			elif performance == speedtest.SpeedTester.PerformanceMedium: timeout = 15
			else: timeout = 20

			return (timeout, label)
		except:
			tools.Logger.error()
			return (10, interface.Translation.string(33387))

	@classmethod
	def optimizationProviders(self):
		from resources.lib.extensions import tools
		from resources.lib.extensions import interface
		try:
			providersMovies = len(self.providersMovies(enabled = True, local = False))
			providersTvshows = len(self.providersTvshows(enabled = True, local = False))
			providers = max(providersMovies, providersTvshows)

			label = '%s (' + str(providers) + ' ' + interface.Translation.string(32301) + ')'
			if providers <= 10:
				timeout = 20
				label = label % interface.Translation.string(35000)
			elif providers <= 20:
				timeout = 25
				label = label % interface.Translation.string(35001)
			elif providers <= 30:
				timeout = 30
				label = label % interface.Translation.string(35001)
			elif providers <= 40:
				timeout = 35
				label = label % interface.Translation.string(35002)
			else:
				timeout = 60
				label = label % interface.Translation.string(35002)

			return (timeout, label)
		except:
			tools.Logger.error()
			return (10, interface.Translation.string(33387))

	@classmethod
	def optimizationForeign(self):
		from resources.lib.extensions import tools
		from resources.lib.extensions import interface
		try:
			timeout = 0

			if self.language() == tools.Language.EnglishCode:
				timeout = 0
				label = interface.Translation.string(33342)
			else:
				timeout = 15
				label = interface.Translation.string(33341)

			return (timeout, label)
		except:
			tools.Logger.error()
			return (10, interface.Translation.string(33387))

	# Cannot be static, since it uses a member variable
	def optimization(self, title = 33996, introduction = True, settings = False):
		try:
			from resources.lib.extensions import tools
			from resources.lib.extensions import interface

			if introduction:
				choice = interface.Dialog.option(title = title, message = 35005)
				if not choice:
					if settings: tools.Settings.launch(tools.Settings.CategoryScraping)
					return False

			dialog = interface.Dialog.progress(title = title, message = 35006)
			dots = ''

			self.resultTimeout = 0
			self.resultLabels = []
			resultNames = [35012, 33404, 32345, 35013]
			def results(function):
				result = function()
				self.resultTimeout += result[0]
				self.resultLabels.append(result[1])

			index = 0
			thread = None
			label = None
			functions = [self.optimizationDevice, self.optimizationConnection, self.optimizationProviders, self.optimizationForeign]
			labels = [35007, 35008, 35009, 35010]
			message = interface.Translation.string(35006)

			while True:
				# NB: Do not check for abort here. This will cause the speedtest to close automatically in the configuration wizard.
				if dialog.iscanceled():
					if settings: tools.Settings.launch(tools.Settings.CategoryScraping)
					return False

				if thread == None or not thread.is_alive():
					if index >= len(functions): break
					thread = threading.Thread(target = results, args = (functions[index],))
					thread.start()
					label = interface.Translation.string(labels[index])
					index += 1

				progress = int(((index - 1) / float(len(functions))) * 100)
				dialog.update(progress, message, '     %s %s' % (label, dots))

				dots += '.'
				if len(dots) > 3: dots = ''
				time.sleep(0.5)

			message = interface.Translation.string(35011) % self.resultTimeout
			for i in range(len(self.resultLabels)):
				message += '%s     %s: %s' % (interface.Format.newline(), interface.Translation.string(resultNames[i]), self.resultLabels[i])
			message += interface.Format.newline() + interface.Translation.string(33968)

			dialog.close()
			choice = interface.Dialog.option(title = title, message = message, labelDeny = 33926, labelConfirm = 33925)
			if choice:
				self.resultTimeout = int(interface.Dialog.input(title = title, type = interface.Dialog.InputNumeric, default = str(self.resultTimeout)))
				if self.resultTimeout < 5: self.resultTimeout = 5
				elif self.resultTimeout > 300: self.resultTimeout = 300

			tools.Settings.set('scraping.providers.timeout', self.resultTimeout)
			if settings: tools.Settings.launch(tools.Settings.CategoryScraping)
			return True
		except:
			tools.Logger.error()

	def customization(self, settings = False):
		try:
			from resources.lib.extensions import tools
			from resources.lib.extensions import interface
			from resources.lib.extensions import verification

			def extract(providers, category):
				try:
					subproviders = [i for i in providers if i['category'] == category]
					for i in range(len(subproviders)):
						subproviders[i]['reset'] = interface.Format.bold('[%s %s] ' % (subproviders[i]['category'].capitalize(), subproviders[i]['type'].capitalize())) + subproviders[i]['name']
						subproviders[i]['label'] = interface.Format.bold('[%s %s] ' % (subproviders[i]['category'].capitalize(), subproviders[i]['type'].capitalize())) + interface.Format.color(subproviders[i]['name'], (subproviders[i]['color'] if 'color' in subproviders[i] else None))
					return sorted(subproviders, key=lambda k: k['label'])
				except:
					tools.Logger.error()

			colors = {
				verification.Verification.StatusOperational : interface.Format.ColorExcellent,
				verification.Verification.StatusLimited : interface.Format.ColorMedium,
				verification.Verification.StatusFailure : interface.Format.ColorBad,
				verification.Verification.StatusDisabled : interface.Format.ColorMain,
			}
			message = interface.Translation.string(35234) % (colors[verification.Verification.StatusOperational], colors[verification.Verification.StatusLimited], colors[verification.Verification.StatusFailure], colors[verification.Verification.StatusDisabled])
			verifications = None
			if interface.Dialog.option(title = 33017, message = message):
				verifications = verification.Verification().verifyProviders(dialog = False)

			interface.Loader.show()

			self.initialize(enabled = False, forceAll = True)
			providers = self.providers(enabled = False, local = False)

			if verifications:
				for i in range(len(providers)):
					for j in verifications:
						if providers[i]['id'] == j['id']:
							providers[i]['color'] = colors[j['status']]
							break

			items = []
			remaining = []

			items += extract(providers, 'general')
			items += extract(providers, 'torrent')
			items += extract(providers, 'usenet')
			items += extract(providers, 'hoster')
			items += extract(providers, 'external')

			labels = [i['label'] for i in items]
			interface.Loader.hide()

			while True:
				index = interface.Dialog.select(title = 35167, items = labels)
				if index < 0: break
				labels[index] = items[index]['reset'] # Reset color if location is customized
				choice = items[index]
				link = interface.Dialog.input(title = 35167, type = interface.Dialog.InputAlphabetic, default = choice['link'])

				interface.Loader.show()

				id = 'providers.customization.locations.value'
				value = tools.Settings.getObject(id)
				if value == None: value = {}
				if link == '' or link == choice['object'].base_link:
					try: del value[choice['id']]
					except: pass
				else:
					value[choice['id']] = link
				if not value: value = ''
				tools.Settings.set(id, value)
				self.databaseClear() # Ensures that the new links are reloaded.

				interface.Loader.hide()

			if settings: tools.Settings.launch(tools.Settings.CategoryProviders)
			return True
		except:
			tools.Logger.error()
			interface.Loader.hide()
