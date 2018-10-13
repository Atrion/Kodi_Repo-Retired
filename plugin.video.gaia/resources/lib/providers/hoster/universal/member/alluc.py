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

import re,urllib,urlparse,json,math
from resources.lib.modules import client
from resources.lib.extensions import metadata
from resources.lib.extensions import tools
from resources.lib.extensions import settings
from resources.lib.extensions import interface

class source:
	def __init__(self):
		self.priority = 0
		self.language = ['un']
		self.domains = ['alluc.ee']
		self.base_link = 'https://www.alluc.ee'
		self.search_link = '/api/search/%s/?apikey=%s&getmeta=0&query=%s&count=%d&from=%d'
		self.types = ['download', 'stream']

		language = tools.Settings.getString('accounts.providers.alluc.language')
		if language.lower() == 'any':
			self.streamLanguage = None
		else:
			if not tools.Language.customization():
				language = tools.Language.Automatic
			self.streamLanguage = tools.Language.code(language)

		self.streamQuality = tools.Settings.getInteger('accounts.providers.alluc.quality')
		if self.streamQuality == 1: self.streamQuality = '720'
		elif self.streamQuality == 2: self.streamQuality = '1080'
		elif self.streamQuality == 3: self.streamQuality = '2K'
		elif self.streamQuality == 4: self.streamQuality = '4K'
		elif self.streamQuality == 5: self.streamQuality = '6K'
		elif self.streamQuality == 6: self.streamQuality = '8K'
		else: self.streamQuality = None

		self.streamLimit = tools.Settings.getInteger('accounts.providers.alluc.limit')
		self.streamIncrease = 100 # The maximum number of links to retrieved for one API call. Alluc currently caps it at 100.

		self.enabled = tools.Settings.getBoolean('accounts.providers.alluc.enabled')

	def movie(self, imdb, title, localtitle, year):
		try:
			url = {'imdb': imdb, 'title': title, 'year': year}
			url = urllib.urlencode(url)
			return url
		except:
			return

	def tvshow(self, imdb, tvdb, tvshowtitle, localtitle, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
			url = urllib.urlencode(url)
			return url
		except:
			return

	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if url == None: return
			url = urlparse.parse_qs(url)
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
			url = urllib.urlencode(url)
			return url
		except:
			return

	def retrieve(self, type, api, query, searchCount, searchFrom):
		try:
			url = urlparse.urljoin(self.base_link, self.search_link)
			url = url % (type, api, query, searchCount, searchFrom)
			results = client.request(url)
			return json.loads(results)
		except:
			return None

	def limit(self, result):
		return 'limit' in result['message'].lower() and result['fetchedtoday'] > 0

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			if url == None:
				raise Exception()

			if not self.enabled:
				raise Exception()

			data = urlparse.parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			if 'exact' in data and data['exact']:
				query = title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				year = None
				season = None
				episode = None
			else:
				title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
				year = int(data['year']) if 'year' in data and not data['year'] == None else None
				season = int(data['season']) if 'season' in data and not data['season'] == None else None
				episode = int(data['episode']) if 'episode' in data and not data['episode'] == None else None
				query = '%s S%02dE%02d' % (title, season, episode) if 'tvshowtitle' in data else '%s %d' % (title, year)

			query = re.sub('(\\\|/| -|:|;|\*|\?|"|\'|<|>|\|)', ' ', query)
			if not self.streamQuality == None and not self.streamQuality == '' and not self.streamQuality == 'sd':
				query += ' %s' % self.streamQuality
			if not self.streamLanguage == None and not self.streamLanguage == '' and not self.streamLanguage == 'un':
				query += ' lang:%s' % self.streamLanguage
			query = urllib.quote_plus(query)

			hostDict = hostprDict + hostDict

			iterations = self.streamLimit / float(self.streamIncrease)
			if iterations < 1:
				last = self.streamLimit
				iterations = 1
			else:
				difference = iterations - math.floor(iterations)
				last = self.streamIncrease if difference == 0 else int(difference * self.streamIncrease)
				iterations = int(math.ceil(iterations))

			timerEnd = tools.Settings.getInteger('scraping.providers.timeout') - 8
			timer = tools.Time(start = True)

			last = settings.Alluc.apiLast()
			api = settings.Alluc.apiNext()
			first = last

			for type in self.types:
				for offset in range(iterations):
					# Stop searching 8 seconds before the provider timeout, otherwise might continue searching, not complete in time, and therefore not returning any links.
					if timer.elapsed() > timerEnd:
						break

					if len(sources) >= self.streamLimit:
						break

					searchCount = last if offset == iterations - 1 else self.streamIncrease
					searchFrom = (offset * self.streamIncrease) + 1

					results = self.retrieve(type, api, query, searchCount, searchFrom)

					try:
						while self.limit(results):
							last = settings.Alluc.apiLast()
							if first == last: break
							api = settings.Alluc.apiNext()
							results = self.retrieve(type, api, query, searchCount, searchFrom)

						if self.limit(results):
							interface.Dialog.notification(title = 35261, message = interface.Translation.string(33952) + ' (' + str(results['fetchedtoday']) + ' ' + interface.Translation.string(35222) + ')', icon = interface.Dialog.IconWarning)
							tools.Time.sleep(2)
							return sources
					except: pass

					results = results['result']
					added = False
					for result in results:
						# Information
						jsonName = result['title']
						jsonSize = result['sizeinternal']
						jsonExtension = result['extension']
						jsonLanguage = result['lang']
						jsonHoster = result['hostername'].lower()
						jsonLink = result['hosterurls'][0]['url']

						# Ignore Hosters
						if not jsonHoster in hostDict:
							continue

						# Ignore Non-Videos
						# Alluc often has other files, such as SRT, also listed as streams.
						if not jsonExtension == None and not jsonExtension == '' and not tools.Video.extensionValid(jsonExtension):
							continue

						# Metadata
						meta = metadata.Metadata(name = jsonName, title = title, year = year, season = season, episode = episode, link = jsonLink, size = jsonSize)

						# Ignore
						if meta.ignore(False):
							continue

						# Add
						sources.append({'url' : jsonLink, 'debridonly' : False, 'direct' : False, 'memberonly' : True, 'source' : jsonHoster, 'language' : jsonLanguage, 'quality':  meta.videoQuality(), 'metadata' : meta, 'file' : jsonName})
						added = True

					if not added:
						break

			return sources
		except:
			return sources

	def resolve(self, url):
		return url
