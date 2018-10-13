# -*- coding: utf-8 -*-

"""
	Gaia Addon

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

import urllib
import urlparse
import pkgutil
import imp
import sys
import shutil

from resources.lib.extensions import tools
from resources.lib.extensions import debrid
from resources.lib.extensions import convert
from resources.lib.extensions import network

IncursionSettings = tools.File.readNow(tools.File.joinPath(tools.System.profile(tools.Extensions.IdIncursion), 'settings.xml'))

class source:
	def __init__(self):
		self.priority = 1
		self.language = ['un']
		self.domains = []
		self.base_link = ''
		self.id = ''
		self.name = ''
		self.enabled = False
		self.object = None
		self.path = ''

	def instanceId(self):
		name = self.name.lower()
		name = name.replace(' ', '').replace('-', '').replace('_', '')
		return 'inc-' + name

	def instanceName(self):
		name = self.name.capitalize()
		name = name.replace(' ', '').replace('-', '').replace('_', '')
		return 'INC-' + name

	def instanceEnabled(self):
		# Get the latests setting.
		if not self.id == '':
			global IncursionSettings
			try:
				result = tools.Settings.raw('provider.' + self.id, parameter = tools.Settings.ParameterValue, data = IncursionSettings)
				return not result == 'false' and not result == None
			except: return True
		return self.enabled

	def instanceParameters(self):
		return {
			'id' : self.id,
			'name' : self.name,
			'enabled' : self.enabled,
			'path' : self.path,
		}

	def instanceParameterize(self, parameters = {}):
		try:
			for key, value in parameters.iteritems():
				try: setattr(self, key, value)
				except: pass
		except: pass

	def instanceObject(self):
		try:
			if self.object == None:
				self._instancesInclude()
				self.object = imp.load_source(self.id, self.path).source()
		except:
			tools.Logger.error()
		return self.object

	@classmethod
	def _instancesPath(self):
		return tools.File.joinPath(tools.System.profile(), 'Scrapers', 'Incursion')

	@classmethod
	def _instancesInclude(self):
		sys.path.append(tools.File.joinPath(self._instancesPath(), 'lib'))

	@classmethod
	def _instancesRename(self, path):
		replacements = [['from resources.', 'from incursion.'], ['xbmcaddon.Addon()', 'xbmcaddon.Addon("' + tools.Extensions.IdIncursion + '")']]
		directories, files = tools.File.listDirectory(path, absolute = True)
		for file in files:
			tools.File.replaceNow(file, replacements)
		for directory in directories:
			self._instancesRename(directory)

	@classmethod
	def _instancesPrepare(self):
		# Incursion's imports (from resources.lib...) clash with Gaia's imports.
		# Copy Incursion's code and change all import statements
		pathSource = tools.System.path(tools.Extensions.IdIncScrapers)
		pathDestination = self._instancesPath()
		file = 'addon.xml'
		fileSource = tools.File.joinPath(pathSource, file)
		fileDesitnation = tools.File.joinPath(pathDestination, file)
		if not tools.File.exists(fileDesitnation) or not tools.Hash.fileSha1(fileSource) == tools.Hash.fileSha1(fileDesitnation):
			tools.File.copyDirectory(pathSource, pathDestination)
			pathResources = tools.File.joinPath(pathDestination, 'lib', 'resources')
			pathIncursion = tools.File.joinPath(pathDestination, 'lib', 'incursion')
			tools.File.renameDirectory(pathResources, pathIncursion)
			self._instancesRename(pathIncursion)
		self._instancesInclude()
		return tools.File.joinPath(pathDestination, 'lib', 'incursion', 'lib', 'sources')

	@classmethod
	def instances(self):
		global IncursionSettings
		result = []
		sources = self._instancesPrepare()

		# Sometimes there is a __init__.py file missing in the directories.
		# This file is required for a valid Python module and will cause walk_packages to fail if absence.
		directories, files = tools.File.listDirectory(sources, absolute = True)
		for directory in directories:
			path = tools.File.joinPath(directory, '__init__.py')
			if not tools.File.exists(path): tools.File.create(path)

		try:
			path1 = [sources]
			for package1, name1, pkg1 in pkgutil.walk_packages(path1):
				path2 = [tools.File.joinPath(sources, name1)]
				for package2, name2, pkg2 in pkgutil.walk_packages(path2):
					if not pkg2:
						try:
							id = name2
							if id == 'orion' or id == 'orionoid': continue
							name = id.replace(' ', '').replace('-', '').replace('_', '').replace('.', '').capitalize()
							path = tools.File.joinPath(path2[0], id + '.py')
							scraper = imp.load_source(id, path).source()
							scraperNew = source()
							scraperNew.id = id
							scraperNew.name = name
							scraperNew.path = path
							if not hasattr(scraper, '_base_link'): # _base_link: Do not use base_link that is defined as a property (eg: KinoX), since this can make additional HTTP requests, slowing down the process.
								if not scraperNew.base_link or scraperNew.base_link == '':
									try: scraperNew.base_link = scraper.base_link
									except: pass
							scraperNew.enabled = tools.Settings.raw('provider.' + id, parameter = tools.Settings.ParameterValue, data = IncursionSettings)
							scraperNew.enabled = not scraperNew.enabled == 'false' and not scraperNew.enabled == None
							scraperNew.object = scraper
							result.append(scraperNew)
						except:
							pass
		except:
			tools.Logger.error()
		return result

	def movie(self, imdb, title, localtitle, aliases, year):
		try:
			return self.instanceObject().movie(imdb = imdb, title = title, localtitle = localtitle, aliases = aliases, year = year)
		except:
			return None

	def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
		try:
			return self.instanceObject().tvshow(imdb = imdb, tvdb = tvdb, tvshowtitle = tvshowtitle, localtvshowtitle = localtvshowtitle, aliases = aliases, year = year)
		except:
			return None

	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			return self.instanceObject().episode(url = url, imdb = imdb, tvdb = tvdb, title = title, premiered = premiered, season = season, episode = episode)
		except:
			return None

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			result = self.instanceObject().sources(url, hostDict, hostprDict) # Don't use named parameters due to CMovies.
			if result:
				for item in result:
					try:
						item['external'] = True

						if not 'language' in item: item['language'] = self.language[0]
						item['url'] = item['url'].replace('http:http:', 'http:').replace('https:https:', 'https:').replace('http:https:', 'https:').replace('https:http:', 'http:') # Some of the links start with a double http.

						# External providers (eg: "Get Out"), sometimes has weird characters in the URL.
						# Ignore the links that have non-printable ASCII or UTF8 characters.
						try: item['url'].decode('utf-8')
						except: continue

						source = item['source'].lower().replace(' ', '')
						if source == 'direct' or source == 'directlink':
							source = urlparse.urlsplit(item['url'])[1].split(':')[0]
							if network.Networker.ipIs(source):
								source = 'Anonymous'
							else:
								split = source.split('.')
								for i in split:
									i = i.lower()
									if i in ['www', 'ftp']: continue
									source = i
									break
							item['source'] = source
						sources.append(item)
					except:
						tools.Logger.error()
			return sources
		except:
			tools.Logger.error()
			return sources

	def resolve(self, url):
		return self.instanceObject().resolve(url)
