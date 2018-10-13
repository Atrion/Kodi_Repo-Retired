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

import nanscrapers

from resources.lib.extensions import tools
from resources.lib.extensions import debrid
from resources.lib.extensions import convert
from resources.lib.extensions import network

class source:
	def __init__(self):
		self.priority = 1
		self.language = ['un']
		self.domains = []
		self.base_link = ''
		self.name = ''
		self.enabled = False

	def instanceId(self):
		name = self.name.lower()
		name = name.replace(' ', '').replace('-', '').replace('_', '')
		return 'nan-' + name

	def instanceName(self):
		name = self.name.capitalize()
		name = name.replace(' ', '').replace('-', '').replace('_', '')
		return 'NAN-' + name

	def instanceEnabled(self):
		# Get the latests setting.
		if not self.name == '':
			try: return nanscrapers.relevant_scrapers(names_list = self.name.lower(), include_disabled = False, exclude = None)[0]()._is_enabled()
			except: return False
		return self.enabled

	def instanceParameters(self):
		return {
			'name' : self.name,
			'enabled' : self.enabled,
		}

	def instanceParameterize(self, parameters = {}):
		try:
			for key, value in parameters.iteritems():
				try: setattr(self, key, value)
				except: pass
		except: pass

	@classmethod
	def instances(self):
		result = []
		try:
			get_scrapers = nanscrapers.relevant_scrapers(names_list = None, include_disabled = True, exclude = None)
			for scraper in get_scrapers:
				scraper = scraper()
				id = scraper.name.lower()
				if id == 'orion' or id == 'orionoid': continue
				scraperNew = source()
				scraperNew.name = scraper.name
				if not hasattr(scraper, '_base_link'): # _base_link: Do not use base_link that is defined as a property (eg: KinoX), since this can make additional HTTP requests, slowing down the process.
					if not scraperNew.base_link or scraperNew.base_link == '':
						try: scraperNew.base_link = scraper.base_link
						except: pass
				scraperNew.enabled = scraper._is_enabled()
				result.append(scraperNew)
		except:
			tools.Logger.error()
		return result

	def movie(self, imdb, title, localtitle, aliases, year):
		try:
			url = {'imdb': imdb, 'title': title, 'year': year}
			url = urllib.urlencode(url)
			return url
		except:
			return None

	def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
		try:
			url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
			url = urllib.urlencode(url)
			return url
		except:
			return None

	def episode(self, url, imdb, tvdb, title, premiered, season, episode):
		try:
			if url == None: return None
			url = urlparse.parse_qs(url)
			url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
			url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
			url = urllib.urlencode(url)
			return url
		except:
			return None

	def sources(self, url, hostDict, hostprDict):
		sources = []
		try:
			debridHas = False
			if not debridHas:
				premiumize = debrid.Premiumize()
				debridHas = premiumize.accountEnabled() and premiumize.accountValid()
				if not debridHas:
					offcloud = debrid.OffCloud()
					debridHas = offcloud.accountEnabled() and offcloud.accountValid()
					if not debridHas:
						realdebrid = debrid.RealDebrid()
						debridHas = realdebrid.accountEnabled() and realdebrid.accountValid()
						if not debridHas:
							alldebrid = debrid.AllDebrid()
							debridHas = alldebrid.accountEnabled() and alldebrid.accountValid()
							if not debrid:
								rapidpremium = debrid.RapidPremium()
								debridHas = rapidpremium.accountEnabled() and rapidpremium.accountValid()

			data = urlparse.parse_qs(url)
			data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])

			movie = False if 'tvshowtitle' in data else True
			title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
			year = str(data['year']) if 'year' in data and not data['year'] == None else ''
			season = str(data['season']) if 'season' in data and not data['season'] == None else ''
			episode = str(data['episode']) if 'episode' in data and not data['episode'] == None else ''
			imdb = data['imdb'] if 'imdb' in data else ''
			tvdb = data['tvdb'] if 'tvdb' in data else ''

			scraper = nanscrapers.relevant_scrapers(names_list = self.name.lower(), include_disabled = True, exclude = None)[0]()
			if self.base_link and not self.base_link == '': scraper.base_link = self.base_link
			if movie:
				result = scraper.scrape_movie(title = title, year = year, imdb = imdb, debrid = debridHas)
			else:
				showYear = year
				try:
					if 'premiered' in data and not data['premiered'] == None and not data['premiered'] == '':
						for format in ['%Y-%m-%d', '%Y-%d-%m', '%d-%m-%Y', '%m-%d-%Y']:
							try:
								showYear = str(int(convert.ConverterTime(value = data['premiered'], format = format).string(format = '%Y')))
								if len(showYear) == 4: break
							except:
								pass
				except:
					pass
				result = scraper.scrape_episode(title = title, year = year, show_year = showYear, season = season, episode = episode, imdb = imdb, tvdb = tvdb, debrid = debridHas)

			if result:
				for item in result:
					item['external'] = True
					item['language']= self.language[0]
					item['debridonly'] = False
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

			return sources
		except:
			tools.Logger.error()
			return sources

	def resolve(self, url):
		return url
