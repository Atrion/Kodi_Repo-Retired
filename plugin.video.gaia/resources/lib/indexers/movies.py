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

import os,sys,re,json,urllib,urlparse,datetime,random

from resources.lib.modules import trakt
from resources.lib.modules import cleangenre
from resources.lib.modules import cleantitle
from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import cache
from resources.lib.modules import metacache
from resources.lib.modules import playcount
from resources.lib.modules import workers
from resources.lib.modules import views

from resources.lib.extensions import tools
from resources.lib.extensions import interface
from resources.lib.extensions import shortcuts
from resources.lib.externals.beautifulsoup import BeautifulSoup

params = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))

action = params.get('action')

class movies:

	def __init__(self, type = tools.Media.TypeMovie, kids = tools.Selection.TypeUndefined):
		self.count = 60

		self.type = type
		if type == tools.Media.TypeDocumentary:
			self.category = 'documentary'
			self.categoryTheatre = 'documentary'
			self.votes = 10000
			self.awards = 'oscar_winners'
		elif type == tools.Media.TypeShort:
			self.category = 'short,tvshort' # Do nit include the "video" category from IMDB here.
			self.categoryTheatre = 'short,tvshort'
			self.votes = 10000
			self.awards = 'oscar_winners'
		else:
			self.category = 'feature,movie,tv_movie'
			self.categoryTheatre = 'feature'
			self.votes = 100000
			self.awards = 'oscar_best_picture_winners'

		self.kids = kids
		self.certificates = None
		self.restriction = 0

		if self.kidsOnly():
			self.certificates = []
			self.restriction = tools.Settings.getInteger('general.kids.restriction')
			if self.restriction >= 0:
				self.certificates.append('G')
			if self.restriction >= 1:
				self.certificates.append('PG')
			if self.restriction >= 2:
				self.certificates.append('PG-13')
			if self.restriction >= 3:
				self.certificates.append('R')
			self.certificates = ','.join(self.certificates).replace('-', '_').lower()
			self.certificates = '&certificates=us:' + self.certificates
		else:
			self.certificates = ''

		self.list = []

		self.imdb_link = 'http://www.imdb.com'
		self.trakt_link = 'http://api-v2launch.trakt.tv'
		self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours = 5))
		self.systime = (self.datetime).strftime('%Y%m%d%H%M%S%f')

		self.trakt_user = control.setting('accounts.informants.trakt.user').strip() if control.setting('accounts.informants.trakt.enabled') else ''
		self.imdb_user = control.setting('accounts.informants.imdb.user').replace('ur', '') if control.setting('accounts.informants.imdb.enabled') else ''
		self.tm_user = control.setting('accounts.informants.tmdb.api') if control.setting('accounts.informants.tmdb.enabled') and not control.setting('accounts.informants.tmdb.api') == '' else tools.System.obfuscate(tools.Settings.getString('internal.tmdb.api', raw = True))
		self.fanart_tv_user = control.setting('accounts.artwork.fanart.api') if control.setting('accounts.artwork.fanart.enabled') else ''
		self.user = str(self.fanart_tv_user) + str(self.tm_user)

		self.lang = control.apiLanguage()['trakt']

		self.search_link = 'http://api-v2launch.trakt.tv/search?type=movie&limit=20&page=1&query='
		self.trakt_info_link = 'http://api-v2launch.trakt.tv/movies/%s'
		self.trakt_lang_link = 'http://api-v2launch.trakt.tv/movies/%s/translations/%s'
		self.fanart_tv_art_link = 'http://webservice.fanart.tv/v3/movies/%s'
		self.fanart_tv_level_link = 'http://webservice.fanart.tv/v3/level'
		self.tm_art_link = 'http://api.themoviedb.org/3/movie/%s/images?api_key=' + self.tm_user
		self.tm_img_link = 'https://image.tmdb.org/t/p/w%s%s'

		self.persons_link = 'http://www.imdb.com/search/name?count=100&name='
		self.personlist_link = 'http://www.imdb.com/search/name?count=100&gender=male,female'
		self.views_link = 'http://www.imdb.com/search/title?title_type=%s&languages=en&num_votes=1000,&production_status=released&sort=num_votes,desc&count=%d&start=1%s' % (self.category, self.count, self.certificates)
		self.featured_link = 'http://www.imdb.com/search/title?title_type=%s&languages=en&num_votes=1000,&production_status=released&release_date=date[365],date[60]&sort=moviemeter,asc&count=%d&start=1%s' % (self.category, self.count, self.certificates)
		self.person_link = 'http://www.imdb.com/search/title?title_type=%s&production_status=released&role=%s&sort=year,desc&count=%d&start=1%s' % (self.category, '%s', self.count, self.certificates)
		self.genre_link = 'http://www.imdb.com/search/title?title_type=%s&languages=en&num_votes=100,&release_date=,date[0]&genres=%s&sort=moviemeter,asc&count=%d&start=1%s' % (self.category, '%s', self.count, self.certificates)
		self.language_link = 'http://www.imdb.com/search/title?title_type=%s&num_votes=100,&production_status=released&languages=%s&sort=moviemeter,asc&count=%d&start=1%s' % (self.category, '%s', self.count, self.certificates)
		self.certification_link = 'http://www.imdb.com/search/title?title_type=%s&languages=en&num_votes=100,&production_status=released&certificates=us:%s&sort=moviemeter,asc&count=%d&start=1' % (self.category, '%s', self.count) # Does not use certificates, since it has it's own.
		self.year_link = 'http://www.imdb.com/search/title?title_type=%s&languages=en&num_votes=100,&production_status=released&year=%s,%s&sort=moviemeter,asc&count=%d&start=1%s' % (self.category, '%s', '%s', self.count, self.certificates)
		self.boxoffice_link = 'http://www.imdb.com/search/title?title_type=%s&languages=en&production_status=released&sort=boxoffice_gross_us,desc&count=%d&start=1%s' % (self.category, self.count, self.certificates)
		self.oscars_link = 'http://www.imdb.com/search/title?title_type=%s&languages=en&production_status=released&groups=%s&sort=year,desc&count=%d&start=1%s' % (self.category, self.awards, self.count, self.certificates)
		self.theaters_link = 'http://www.imdb.com/search/title?title_type=%s&languages=en&num_votes=1000,&release_date=date[365],date[0]&sort=release_date_us,desc&count=%d&start=1%s' % (self.categoryTheatre, self.count, self.certificates)
		self.rating_link = 'http://www.imdb.com/search/title?title_type=%s&num_votes=%d,&release_date=,date[0]&sort=user_rating,desc&count=%d&start=1%s' % (self.categoryTheatre, self.votes, self.count, self.certificates)

		self.drugsgeneral_link = 'https://www.imdb.com/list/ls052149893/'
		self.drugsalcohol_link = 'https://www.imdb.com/list/ls000527140/'
		self.drugsmarijuana_link = 'http://www.imdb.com/list/ls036810850/'
		self.drugspsychedelics_link = 'http://www.imdb.com/list/ls054725090/'

		if self.type == tools.Media.TypeDocumentary or self.type == tools.Media.TypeShort:
			# Documentaries and Shorts do not have a TOP list. Simply use a list sorted by ratings.
			self.popular_link = 'http://www.imdb.com/search/title?title_type=%s&languages=en&production_status=released&sort=user_rating,desc&count=%d&start=1%s' % (self.category, self.count, self.certificates)
			self.new_link = 'http://www.imdb.com/search/title?title_type=%s&languages=en&num_votes=100,&production_status=released&release_date=date[365],date[1]&sort=moviemeter,asc&count=%d&start=1%s' % (self.category, self.count, self.certificates)
			self.home_link = 'http://www.imdb.com/search/title?online_availability=US/today/Amazon/paid,US/today/Amazon/subs,US/today/Amazon/subs,UK/today/Amazon/paid,UK/today/Amazon/subs,UK/today/Amazon/subs&title_type=%s&languages=en&num_votes=300,&production_status=released&release_date=date[730],date[30]&sort=moviemeter,asc&count=%d&start=1%s' % (self.category, self.count, self.certificates)
			self.trending_link = self.featured_link
		else:
			self.popular_link = 'http://www.imdb.com/search/title?title_type=%s&languages=en&num_votes=1000,&production_status=released&groups=top_1000&sort=moviemeter,asc&count=%d&start=1%s' % (self.category, self.count, self.certificates)
			self.new_link = 'http://www.imdb.com/search/title?title_type=%s&languages=en&num_votes=300,&production_status=released&release_date=date[90],date[1]&sort=moviemeter,asc&count=%d&start=1%s' % (self.category, self.count, self.certificates)
			self.home_link = 'http://www.imdb.com/search/title?online_availability=US/today/Amazon/paid,US/today/Amazon/subs,US/today/Amazon/subs,UK/today/Amazon/paid,UK/today/Amazon/subs,UK/today/Amazon/subs&title_type=%s&languages=en&num_votes=1000,&production_status=released&release_date=date[365],date[30]&sort=moviemeter,asc&count=%d&start=1%s' % (self.category, self.count, self.certificates)
			self.trending_link = 'http://api-v2launch.trakt.tv/movies/trending?limit=%d&page=1' % self.count

		self.traktlists_link = 'http://api-v2launch.trakt.tv/users/me/lists'
		self.traktlikedlists_link = 'http://api-v2launch.trakt.tv/users/likes/lists?limit=1000000'
		self.traktlist_link = 'http://api-v2launch.trakt.tv/users/%s/lists/%s/items'
		self.traktcollection_link = 'http://api-v2launch.trakt.tv/users/me/collection/movies'
		self.traktwatchlist_link = 'http://api-v2launch.trakt.tv/users/me/watchlist/movies'
		self.traktrecommendations_link = 'http://api-v2launch.trakt.tv/recommendations/movies?limit=%d' % self.count
		self.trakthistory_link = 'http://api-v2launch.trakt.tv/users/me/history/movies?limit=%d&page=1' % self.count
		self.traktunfinished_link = 'https://api.trakt.tv/sync/playback/movies'
		self.imdblists_link = 'http://www.imdb.com/user/ur%s/lists?tab=all&sort=modified:desc&filter=titles' % self.imdb_user
		self.imdblist_link = 'http://www.imdb.com/list/%s/?view=detail&sort=title:asc&title_type=feature,movie,short,tv_movie,tv_special,video,documentary,game&start=1'
		self.imdblist2_link = 'http://www.imdb.com/list/%s/?view=detail&sort=created:desc&title_type=feature,movie,short,tv_movie,tv_special,video,documentary,game&start=1'
		self.imdbwatchlist_link = 'http://www.imdb.com/user/ur%s/watchlist?sort=alpha,asc' % self.imdb_user
		self.imdbwatchlist2_link = 'http://www.imdb.com/user/ur%s/watchlist?sort=date_added,desc' % self.imdb_user

	def parameterize(self, action):
		if not self.type == None: action += '&type=%s' % self.type
		if not self.kids == None: action += '&kids=%d' % self.kids
		return action

	def kidsOnly(self):
		return self.kids == tools.Selection.TypeInclude

	def sort(self):
		try:
			if self.type == tools.Media.TypeDocumentary: type = 'documentaries'
			elif self.type == tools.Media.TypeShort: type = 'shorts'
			else: type = 'movies'
			attribute = tools.Settings.getInteger('interface.sort.%s.type' % type)
			reverse = tools.Settings.getInteger('interface.sort.%s.order' % type) == 1
			if attribute > 0:
				if attribute == 1:
					if tools.Settings.getBoolean('interface.sort.articles'):
						self.list = sorted(self.list, key = lambda k: re.sub('(^the |^a |^an )', '', k['title'].lower()), reverse = reverse)
					else:
						self.list = sorted(self.list, key = lambda k: k['title'].lower(), reverse = reverse)
				elif attribute == 2:
					self.list = sorted(self.list, key = lambda k: float(k['rating']), reverse = reverse)
				elif attribute == 3:
					self.list = sorted(self.list, key = lambda k: int(k['votes'].replace(',', '')), reverse = reverse)
				elif attribute == 4:
					for i in range(len(self.list)):
						if not 'premiered' in self.list[i]: self.list[i]['premiered'] = ''
					self.list = sorted(self.list, key = lambda k: k['premiered'], reverse = reverse)
				elif attribute == 5:
					for i in range(len(self.list)):
						if not 'added' in self.list[i]: self.list[i]['added'] = ''
					self.list = sorted(self.list, key = lambda k: k['added'], reverse = reverse)
				elif attribute == 6:
					for i in range(len(self.list)):
						if not 'watched' in self.list[i]: self.list[i]['watched'] = ''
					self.list = sorted(self.list, key = lambda k: k['watched'], reverse = reverse)
			elif reverse:
				self.list = reversed(self.list)
		except:
			tools.Logger.error()

	def get(self, url, idx = True, notifications = True):
		try:
			try: url = getattr(self, url + '_link')
			except: pass

			try: u = urlparse.urlparse(url).netloc.lower()
			except: pass

			self.list = []
			if u in self.trakt_link and '/users/' in url:
				try:
					if url == self.trakthistory_link: raise Exception()
					if not '/users/me/' in url: raise Exception()
					if trakt.getActivity() > cache.timeout(self.trakt_list, url, self.trakt_user): raise Exception()
					self.list = cache.get(self.trakt_list, 0, url, self.trakt_user)
				except:
					self.list = cache.get(self.trakt_list, 0, url, self.trakt_user)

				#if '/users/me/' in url and not '/watchlist/' in url:
				#	self.list = sorted(self.list, key=lambda k: re.sub('(^the |^a |^an )', '', k['title'].lower()))
				self.sort()
				if idx == True: self.worker()

			elif u in self.trakt_link and self.search_link in url:
				self.list = cache.get(self.trakt_list, 1, url, self.trakt_user)
				if idx == True: self.worker(level = 0)

			elif self.traktunfinished_link in url:
				self.list = cache.get(self.trakt_list, 0.3, url, self.trakt_user)
				if idx == True: self.worker(level = 0)

			elif u in self.trakt_link:
				self.list = cache.get(self.trakt_list, 24, url, self.trakt_user)
				if idx == True: self.worker()

			elif u in self.imdb_link and ('/user/' in url or '/list/' in url):
				self.list = cache.get(self.imdb_list, 0.3, url)
				self.sort()
				if idx == True: self.worker()

			elif u in self.imdb_link:
				self.list = cache.get(self.imdb_list, 24, url)
				if idx == True: self.worker()
				self._displayFilter()

			if self.list == None: self.list = []

			if self.search_link in url:
				if not self.persons_link in url and not self.personlist_link in url:
					if self.type == tools.Media.TypeDocumentary:
						self.list = [i for i in self.list if 'genre' in i and 'documentary' in i['genre'].lower()]
					elif self.type == tools.Media.TypeShort:
						self.list = [i for i in self.list if 'genre' in i and 'short' in i['genre'].lower()]

				if len(self.list) == 0:
					interface.Loader.hide()
					if notifications: interface.Dialog.notification(title = 32010, message = 33049, icon = interface.Dialog.IconInformation)

			if self.kidsOnly() and not self.persons_link in url and not self.personlist_link in url:
				self.list = [i for i in self.list if 'mpaa' in i and tools.Kids.allowed(i['mpaa'])]

			if idx == True: self.movieDirectory(self.list)

			return self.list
		except:
			try: invalid = self.list == None or len(self.list) == 0
			except: invalid = True
			if invalid:
				interface.Loader.hide()
				if notifications: interface.Dialog.notification(title = 32001, message = 33049, icon = interface.Dialog.IconInformation)


	def _displayFilter(self):
		def _validPoster(poster):
			return not poster == None and not poster == '' and not poster == '0'
		def _validPosters(item):
			if 'poster' in item and _validPoster(item['poster']): return True
			elif 'poster2' in item and _validPoster(item['poster2']): return True
			elif 'poster3' in item and _validPoster(item['poster3']): return True
			else: return False
		newList = [item for item in self.list if _validPosters(item)]
		if len(newList) >= 10: self.list = newList


	def random(self):
		from resources.lib.extensions import core

		yearCurrent = datetime.datetime.now().year
		yearRandom = random.randint(1950, yearCurrent)
		selection = [
			self.views_link,
			self.featured_link,
			self.boxoffice_link,
			self.oscars_link,
			self.theaters_link,
			self.rating_link,
			self.popular_link,
			self.new_link,
			self.trending_link,
			self.drugspsychedelics_link,
			self.year_link % (yearRandom, min(yearRandom + 5, yearCurrent)),
		]
		select = None
		while select == None:
			try:
				result = cache.get(self.imdb_list, 24, random.choice(selection))
				select = random.choice(result)
			except:
				select = None

		message = ''
		if 'title' in select: message += interface.Format.bold(interface.Translation.string(33039) + ': ') + str(select['title']) + interface.Format.newline()
		if 'year' in select: message += interface.Format.bold(interface.Translation.string(32012) + ': ') + str(select['year']) + interface.Format.newline()
		if 'rating' in select and not select['rating'] == '0': message += interface.Format.bold(interface.Translation.string(35187) + ': ') + str(select['rating']) + interface.Format.newline()
		if 'director' in select and not select['director'] == '0': message += interface.Format.bold(interface.Translation.string(35377) + ': ') + str(select['director']) + interface.Format.newline()
		if 'genre' in select and not select['genre'] == '0': message += interface.Format.bold(interface.Translation.string(35376) + ': ') + str(select['genre'])

		if interface.Dialog.option(title = 35375, message = message, labelConfirm = 35379, labelDeny = 35378):
			self.random()
		else:
			core.Core(type = self.type, kids = self.kids).play(
				title = select['title'] if 'title' in select else None,
				year = select['year'] if 'year' in select else None,
				imdb = select['imdb'] if 'imdb' in select else None,
				tvdb = select['tvdb'] if 'tvdb' in select else None,
				season = select['season'] if 'season' in select else None,
				episode = select['episode'] if 'episode' in select else None,
				tvshowtitle = select['tvshowtitle'] if 'tvshowtitle' in select else None,
				premiered = select['premiered'] if 'premiered' in select else None,
				meta = select
			)

	def arrivals(self):
		if self.type == tools.Media.TypeDocumentary:
			setting = tools.Settings.getInteger('interface.arrivals.documentaries')
		elif self.type == tools.Media.TypeShort:
			setting = tools.Settings.getInteger('interface.arrivals.shorts')
		else:
			setting = tools.Settings.getInteger('interface.arrivals.movies')

		if setting == 0:
			self.get(self.new_link)
		elif setting == 1:
			self.get(self.home_link)
		elif setting == 2:
			self.get(self.popular_link)
		elif setting == 3:
			self.get(self.theaters_link)
		elif setting == 4:
			self.get(self.trending_link)
		else:
			self.get(self.home_link)


	def search(self, terms = None):
		try:
			# NB: Sleeping here for a while seems to fix the problem of search results not showing.
			# Sleeping for 200ms seems not to be enough. 500ms also is sometimes to little.  800ms works most of the time, but still the results sometimes do not show.
			#control.idle()
			control.sleep(1000)

			from resources.lib.extensions import search

			if terms:
				if (terms == None or terms == ''): return
				if self.type == tools.Media.TypeDocumentary:
					search.Searches().updateDocumentaries(terms)
				elif self.type == tools.Media.TypeShort:
					search.Searches().updateShorts(terms)
				else:
					search.Searches().updateMovies(terms)
			else:
				t = control.lang(32010).encode('utf-8')
				k = control.keyboard('', t) ; k.doModal()
				terms = k.getText() if k.isConfirmed() else None
				if (terms == None or terms == ''): return
				if self.type == tools.Media.TypeDocumentary:
					search.Searches().insertDocumentaries(terms, self.kids)
				elif self.type == tools.Media.TypeShort:
					search.Searches().insertShorts(terms, self.kids)
				else:
					search.Searches().insertMovies(terms, self.kids)

			url = self.search_link + urllib.quote_plus(terms)
			url = '%s?action=moviePage&url=%s' % (sys.argv[0], urllib.quote_plus(url))
			url = self.parameterize(url)
			control.execute('Container.Update(%s)' % url)
		except:
			return
	# [/GAIACODE]

	# [GAIACODE]
	def person(self, terms = None):
		try:
			# NB: Sleeping here for a while seems to fix the problem of search results not showing.
			# Sleeping for 200ms seems not to be enough. 500ms also is sometimes to little.  800ms works most of the time, but still the results sometimes do not show.
			#control.idle()
			control.sleep(1000)

			from resources.lib.extensions import search

			if terms:
				if (terms == None or terms == ''): return
				search.Searches().updatePeople(terms)
			else:
				t = control.lang(32010).encode('utf-8')
				k = control.keyboard('', t) ; k.doModal()
				terms = k.getText() if k.isConfirmed() else None
				if (terms == None or terms == ''): return
				search.Searches().insertPeople(terms, self.kids)

			url = self.persons_link + urllib.quote_plus(terms)
			url = '%s?action=moviePersons&url=%s' % (sys.argv[0], urllib.quote_plus(url))
			url = self.parameterize(url)
			control.execute('Container.Update(%s)' % url)
		except:
			return

	def collections(self):
		collections = []

		if not self.kidsOnly() or self.restriction >= 0:
			collections.extend([
				('Disney', 'http://www.imdb.com/search/title?keywords=disney&num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie'),
				('Toy Story', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=toy%20story&title_type=feature,movie,tv_movie'),
				('Land Before Time', 'http://www.imdb.com/search/title?production_status=released&title_type=feature,movie,tv_movie,video&title=land%20before%20time'),
			])
		if not self.kidsOnly() or self.restriction >= 1:
			collections.extend([
				('Harry Potter', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=harry%20potter&title_type=feature,movie,tv_movie'),
				('Star Wars', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=star%20wars&title_type=feature,movie,tv_movie'),
				('Back To The Future', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=back%20to%20the%20future&title_type=feature,movie,tv_movie'),
				('Rocky', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=rocky&title_type=feature,movie,tv_movie&genres=sport'),
				('Karate Kid', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=karate%20kid&title_type=feature,movie,tv_movie'),
				('Narnia', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=narnia&title_type=feature,movie,tv_movie'),
				('Shrek', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=shrek&title_type=feature,movie,tv_movie'),
				('Kung Fu Panda', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=kung%20fu%20panda&title_type=feature,movie,tv_movie'),
				('Alvin and the Chipmunks', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie&title=chipmunks'),
			])
		if not self.kidsOnly() or self.restriction >= 2:
			collections.extend([
				('Marvel Comics', 'http://www.imdb.com/search/title?keywords=marvel-comics&num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie'),
				('X-Men', 'http://www.imdb.com/search/title?keywords=marvel-comics&num_votes=1000,&production_status=released&title=x-men&title_type=feature,movie,tv_movie'),
				('Spider-Man', 'http://www.imdb.com/search/title?keywords=marvel-comics&num_votes=1000,&production_status=released&title=spider-man&title_type=feature,movie,tv_movie'),
				('Fantastic Four', 'http://www.imdb.com/search/title?keywords=marvel-comics&num_votes=1000,&production_status=released&title=fantastic%20four&title_type=feature,movie,tv_movie'),
				('Hulk', 'http://www.imdb.com/search/title?keywords=marvel-comics&num_votes=1000,&production_status=released&title=hulk&title_type=feature,movie,tv_movie'),
				('Iron Man', 'http://www.imdb.com/search/title?keywords=marvel-comics&num_votes=1000,&production_status=released&title=iron%20man&title_type=feature,movie,tv_movie'),
				('Captain America', 'http://www.imdb.com/search/title?keywords=marvel-comics&num_votes=1000,&production_status=released&title=captain%20america&title_type=feature,movie,tv_movie'),
				('Thor', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie&title=thor'),

				('DC Comics', 'http://www.imdb.com/search/title?keywords=dc-comics&num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie'),
				('Batman', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=batman&title_type=feature,movie,tv_movie'),
				('Superman', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=superman&title_type=feature,movie,tv_movie'),

				('Dark Horse Comics', 'http://www.imdb.com/search/title?keywords=dark-horse-comics&num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie'),
				('Hellboy', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie&title=hellboy'),
				('Sin City', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie&title=sin%20city'),
				('300', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie&title=300'),

				('Middle Earth', 'http://www.imdb.com/search/title?keywords=hobbit&num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie&user_rating=4.0,'),
				('Star Trek', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=star%20trek&title_type=feature,movie,tv_movie'),
				('Matrix', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=matrix&title_type=feature,movie,tv_movie'),
				('Fast And Furious', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=fast%20furious&title_type=feature,movie,tv_movie'),
				('007', 'http://www.imdb.com/search/title?keywords=007&num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie'),
				('James Bond', 'http://www.imdb.com/search/title?keywords=007&num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie'),
				('Jurassic Park', 'http://www.imdb.com/search/title?keywords=jurassic-park&num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie'),
				('Hunger Games', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=hunger%20games&title_type=feature,movie,tv_movie'),
				('Terminator', 'http://www.imdb.com/search/title?genres=action&keywords=the-terminator&num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie'),
				('Rambo', 'http://www.imdb.com/search/title?genres=action&keywords=rambo&num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie'),
				('Mission Impossible', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=mission%20impossible&title_type=feature,movie,tv_movie'),
				('Indiana Jones', 'http://www.imdb.com/search/title?num_votes=1000,&plot=indiana%20jones&production_status=released&role=nm0000148&title_type=feature,movie,tv_movie'),
				('Jason Bourne', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=bourne&title_type=feature,movie,tv_movie'),
				('Twilight', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&role=nm0829576&title=twilight&title_type=feature,movie,tv_movie'),
				('Pirates Of The Caribbean', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=pirates%20caribbean&title_type=feature,movie,tv_movie'),
				('Rush Hour', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=rush%20hour&title_type=feature,movie,tv_movie'),
				('Transformers', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=transformers&title_type=feature,movie,tv_movie'),
				('Ace Ventura', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=ace%20ventura&title_type=feature,movie,tv_movie'),
				('Dan Brown', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&role=nm1467010&title_type=feature,movie,tv_movie'),
				('Ocean\'s', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=oceans&title_type=feature,movie,tv_movie&genres=crime'),
				('Mummy', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=the%20mummy&title_type=feature,movie,tv_movie&genres=fantasy,adventure'),
				('Austin Powers', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=austin%20powers&title_type=feature,movie,tv_movie'),
				('Transporter', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=transporter&title_type=feature,movie,tv_movie'),
				('Taxi', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=taxi&title_type=feature,movie,tv_movie&genres=action,comedy'),
				('Men In Black', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=men%20in%20black&title_type=feature,movie,tv_movie'),
				('Space Odyssey', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&role=nm0002009&title_type=feature,movie,tv_movie'),
				('Godzilla', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=godzilla&title_type=feature,movie,tv_movie'),
				('King Kong', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=king%20kong&title_type=feature,movie,tv_movie'),
				('Planet Of The Apes', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie&title=planet%20apes'),
				('Tron', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie&title=tron'),
				('Naked Gun', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie&title=naked%20gun'),
				('Final Fantasy', 'http://www.imdb.com/search/title?production_status=released&title_type=feature,movie,tv_movie&title=final%20fantasy'),
			])
		if not self.kidsOnly() or self.restriction >= 3:
			collections.extend([
				('Predator', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=predator&title_type=feature,movie,tv_movie&genres=action'),
				('Saw', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=saw&title_type=feature,movie,tv_movie&genres=horror'),
				('The Godfather', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=the%20godfather&title_type=feature,movie,tv_movie&genres=crime,drama'),
				('Underworld', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=underworld&title_type=feature&genres=action'),
				('Alien', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=alien&title_type=feature,movie,tv_movie&genres=sci_fi'),
				('Mad Max', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=mad%20max&title_type=feature,movie,tv_movie'),
				('Blade', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=blade&title_type=feature,movie,tv_movie&genres=horror,action'),
				('Hannibal Lecter', 'http://www.imdb.com/search/title?num_votes=1000,&plot=hannibal%20lecter&production_status=released&title_type=feature,movie,tv_movie&genres=crime'),
				('Harold And Kumar', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=kumar&title_type=feature,movie,tv_movie'),
				('Resident Evil', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=resident%20evil&title_type=feature,movie,tv_movie'),
				('Kill Bill', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=kill%20bill&title_type=feature,movie,tv_movie'),
				('Scream', 'http://www.imdb.com/search/title?num_votes=10000,&production_status=released&title=scream&title_type=feature,movie,tv_movie&genres=horror,mystery'),
				('Die Hard', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=die%20hard&title_type=feature,movie,tv_movie&genres=action'),
				('Lethal Weapon', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=lethal%20weapon&title_type=feature,movie,tv_movie'),
				('Three Colors', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=three%20colors&title_type=feature,movie,tv_movie'),
				('Butterfly Effect', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=butterfly%20effect&title_type=feature,movie,tv_movie'),
				('Beverly Hills Cop', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=beverly%20hill%20cop&title_type=feature,movie,tv_movie'),
				('American Pie', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=american&role=nm0004755&title_type=feature,movie,tv_movie'),
				('Scary Movie', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title=scary%20movie&title_type=feature,movie,tv_movie'),
				('Final Destination', 'http://www.imdb.com/search/title?num_votes=50000,&production_status=released&title=final%20destination&title_type=feature,movie,tv_movie'),
				('Man With No Name', 'http://www.imdb.com/search/title?genres=western&num_votes=1000,&production_status=released&release_date=1964,1966&role=nm0001466&title_type=feature,movie,tv_movie'),
				('Mexico', 'http://www.imdb.com/search/title?keywords=mariachi&production_status=released&release_date=1992,2003&role=nm0001675&title_type=feature,movie,tv_movie&genre=actions,thriller'),
				('Millennium', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&role=nm2297183&title_type=feature,movie,tv_movie'),
				('Halloween', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie&title=halloween'),
				('Friday The 13th', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie&title=friday%20the%2013th'),
				('Nightmare On Elm Street', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie&title=nightmare%20elm'),
				('Chronicles Of Riddick', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie&title=riddick'),
				('Paranormal Activity', 'http://www.imdb.com/search/title?num_votes=1000,&production_status=released&title_type=feature,movie,tv_movie&title=paranormal%20activity'),
			])

		collections = sorted(collections, key=lambda x: x[0])

		for i in collections: self.list.append({'name': i[0], 'url': i[1], 'context' : i[1], 'image': 'collections.png', 'action': self.parameterize('movies')})
		self.addDirectory(self.list)
		return self.list

	def genres(self):
		genres = []

		if not self.kidsOnly() or self.restriction >= 0:
			genres.extend([
				('Adventure', 'adventure'),
				('Animation', 'animation'),
				('Biography', 'biography'),
				('Comedy', 'comedy'),
				('Drama', 'drama'),
				('Family', 'family'),
				('Fantasy', 'fantasy'),
				('History', 'history'),
				('Music ', 'music'),
				('Musical', 'musical'),
				('Sport', 'sport'),
			])
		if not self.kidsOnly() or self.restriction >= 1:
			genres.extend([
				('Mystery', 'mystery'),
				('Romance', 'romance'),
				('Science Fiction', 'sci_fi'),
			])
		if not self.kidsOnly() or self.restriction >= 2:
			genres.extend([
				('Action', 'action'),
				('Crime', 'crime'),
				('Thriller', 'thriller'),
				('Western', 'western'),
			])
		if not self.kidsOnly() or self.restriction >= 3:
			genres.extend([
				('Horror', 'horror'),
				('War', 'war'),
				('Film Noir', 'film_noir'),
			])

		genres = sorted(genres, key=lambda x: x[0])

		for i in genres: self.list.append({'name': cleangenre.lang(i[0], self.lang), 'url': self.genre_link % i[1], 'image': 'genres.png', 'action': self.parameterize('movies')})
		self.addDirectory(self.list)
		return self.list


	def languages(self):
		languages = [
		('Afrikaans', 'af'),
		('Arabic', 'ar'),
		('Arabic', 'ar'),
		('Bulgarian', 'bg'),
		('Chinese', 'zh'),
		('Croatian', 'hr'),
		('Dutch', 'nl'),
		('English', 'en'),
		('Finnish', 'fi'),
		('French', 'fr'),
		('German', 'de'),
		('Greek', 'el'),
		('Hebrew', 'he'),
		('Hindi ', 'hi'),
		('Hungarian', 'hu'),
		('Icelandic', 'is'),
		('Italian', 'it'),
		('Japanese', 'ja'),
		('Korean', 'ko'),
		('Norwegian', 'no'),
		('Persian', 'fa'),
		('Polish', 'pl'),
		('Portuguese', 'pt'),
		('Punjabi', 'pa'),
		('Romanian', 'ro'),
		('Russian', 'ru'),
		('Spanish', 'es'),
		('Swedish', 'sv'),
		('Turkish', 'tr'),
		('Ukrainian', 'uk')
		]

		for i in languages: self.list.append({'name': str(i[0]), 'url': self.language_link % i[1], 'image': 'languages.png', 'action': self.parameterize('movies')})
		self.addDirectory(self.list)
		return self.list


	def certifications(self):
		certificates = []

		if not self.kidsOnly() or self.restriction >= 0:
			certificates.append(('General Audience (G)', 'G'))
		if not self.kidsOnly() or self.restriction >= 1:
			certificates.append(('Parental Guidance (PG)', 'PG'))
		if not self.kidsOnly() or self.restriction >= 2:
			certificates.append(('Parental Caution (PG-13)', 'PG-13'))
		if not self.kidsOnly() or self.restriction >= 3:
			certificates.append(('Parental Restriction (R)', 'R'))
		if not self.kidsOnly():
			certificates.append(('Mature Audience (NC-17)', 'NC-17'))

		for i in certificates: self.list.append({'name': str(i[0]), 'url': self.certification_link % str(i[1]).replace('-', '_').lower(), 'image': 'certificates.png', 'action': self.parameterize('movies')})
		self.addDirectory(self.list)
		return self.list

	def age(self):
		certificates = []

		if not self.kidsOnly() or self.restriction >= 0:
			certificates.append(('Minor (3+)', 'G'))
		if not self.kidsOnly() or self.restriction >= 1:
			certificates.append(('Young (7+)', 'PG'))
		if not self.kidsOnly() or self.restriction >= 2:
			certificates.append(('Teens (13+)', 'PG-13'))
		if not self.kidsOnly() or self.restriction >= 3:
			certificates.append(('Youth (16+)', 'R'))
		if not self.kidsOnly():
			certificates.append(('Mature (18+)', 'NC-17'))

		for i in certificates: self.list.append({'name': str(i[0]), 'url': self.certification_link % str(i[1]).replace('-', '_').lower(), 'image': 'age.png', 'action': self.parameterize('movies')})
		self.addDirectory(self.list)
		return self.list


	def years(self):
		year = (self.datetime.strftime('%Y'))

		for i in range(int(year)-0, int(year)-100, -1): self.list.append({'name': str(i), 'url': self.year_link % (str(i), str(i)), 'image': 'calendar.png', 'action': self.parameterize('movies')})
		self.addDirectory(self.list)
		return self.list


	def persons(self, url):
		if url == None:
			self.list = cache.get(self.imdb_person_list, 24, self.personlist_link)
		else:
			self.list = cache.get(self.imdb_person_list, 1, url)

		if len(self.list) == 0:
			interface.Loader.hide()
			interface.Dialog.notification(title = 32010, message = 33049, icon = interface.Dialog.IconInformation)

		for i in range(0, len(self.list)): self.list[i].update({'action': self.parameterize('movies')})
		self.addDirectory(self.list)
		return self.list


	def userlists(self, mode = None):
		if not mode == None:
			mode = mode.lower().strip()
		userlists = []

		if mode == None or mode == 'trakt':
			try:
				if trakt.getTraktCredentialsInfo() == False: raise Exception()
				activity = trakt.getActivity()
			except: pass

			try:
				if trakt.getTraktCredentialsInfo() == False: raise Exception()
				self.list = []
				lists = []

				try:
					if activity > cache.timeout(self.trakt_user_list, self.traktlists_link, self.trakt_user): raise Exception()
					lists += cache.get(self.trakt_user_list, 3, self.traktlists_link, self.trakt_user)
				except:
					lists += cache.get(self.trakt_user_list, 0, self.traktlists_link, self.trakt_user)

				for i in range(len(lists)): lists[i].update({'image': 'traktlists.png'})
				userlists += lists
			except:
				pass

		if mode == None or mode == 'imdb':
			try:
				if self.imdb_user == '': raise Exception()
				self.list = []
				lists = cache.get(self.imdb_user_list, 0, self.imdblists_link)
				for i in range(len(lists)): lists[i].update({'image': 'imdblists.png'})
				userlists += lists
			except: pass

		if mode == None or mode == 'trakt':
			try:
				if trakt.getTraktCredentialsInfo() == False: raise Exception()
				self.list = []
				lists = []

				try:
					if activity > cache.timeout(self.trakt_user_list, self.traktlikedlists_link, self.trakt_user): raise Exception()
					lists += cache.get(self.trakt_user_list, 3, self.traktlikedlists_link, self.trakt_user)
				except:
					lists += cache.get(self.trakt_user_list, 0, self.traktlikedlists_link, self.trakt_user)

				for i in range(len(lists)): lists[i].update({'image': 'traktlists.png'})
				userlists += lists
			except: pass

		self.list = []

		# Filter the user's own lists that were
		for i in range(len(userlists)):
			contains = False
			adapted = userlists[i]['url'].replace('/me/', '/%s/' % self.trakt_user)
			for j in range(len(self.list)):
				if adapted == self.list[j]['url'].replace('/me/', '/%s/' % self.trakt_user):
					contains = True
					break
			if not contains:
				self.list.append(userlists[i])

		for i in range(0, len(self.list)): self.list[i].update({'action': self.parameterize('movies')})

		# Watchlist
		if (mode == None or mode == 'trakt') and trakt.getTraktCredentialsInfo():
			self.list.insert(0, {'name' : interface.Translation.string(32033), 'url' : self.traktwatchlist_link, 'context' : self.traktwatchlist_link, 'image': 'traktwatch.png', 'action': self.parameterize('movies')})

		self.addDirectory(self.list, queue=True)
		return self.list


	def trakt_list(self, url, user):
		try:
			q = dict(urlparse.parse_qsl(urlparse.urlsplit(url).query))
			q.update({'extended': 'full'})
			q = (urllib.urlencode(q)).replace('%2C', ',')
			u = url.replace('?' + urlparse.urlparse(url).query, '') + '?' + q

			result = trakt.getTraktAsJson(u)

			items = []
			for i in result:
				try:
					movie = i['movie']
					try: movie['progress'] = max(0, min(1, i['progress'] / 100.0))
					except: pass
					items.append(movie)
				except: pass
			if len(items) == 0:
				items = result
		except:
			return

		try:
			q = dict(urlparse.parse_qsl(urlparse.urlsplit(url).query))
			if not int(q['limit']) == len(items): raise Exception()
			q.update({'page': str(int(q['page']) + 1)})
			q = (urllib.urlencode(q)).replace('%2C', ',')
			next = url.replace('?' + urlparse.urlparse(url).query, '') + '?' + q
			next = next.encode('utf-8')
		except:
			next = ''

		for item in items:
			try:
				title = item['title'].encode('utf-8')
				title = client.replaceHTMLCodes(title)
				title = title.encode('utf-8')

				year = item['year']
				year = re.sub('[^0-9]', '', str(year))
				year = year.encode('utf-8')

				try:
					if int(year) > int((self.datetime).strftime('%Y')): continue
				except: pass

				try: progress = item['progress']
				except: progress = None

				try:
					imdb = item['ids']['imdb']
					#if imdb == None or imdb == '': raise Exception()
					imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))
					imdb = imdb.encode('utf-8')
				except:
					imdb = '0'

				tmdb = str(item.get('ids', {}).get('tmdb', 0))

				try: premiered = item['released']
				except: premiered = '0'
				try: premiered = re.compile('(\d{4}-\d{2}-\d{2})').findall(premiered)[0]
				except: premiered = '0'
				premiered = premiered.encode('utf-8')

				try: genre = item['genres']
				except: genre = '0'
				genre = [i.title() for i in genre]
				if genre == []: genre = '0'
				genre = ' / '.join(genre)
				genre = genre.encode('utf-8')

				try: duration = str(item['runtime'])
				except: duration = '0'
				if duration == None: duration = '0'
				duration = duration.encode('utf-8')

				try: rating = str(item['rating'])
				except: rating = '0'
				if rating == None or rating == '0.0': rating = '0'
				rating = rating.encode('utf-8')

				try: votes = str(item['votes'])
				except: votes = '0'
				try: votes = str(format(int(votes),',d'))
				except: pass
				if votes == None: votes = '0'
				votes = votes.encode('utf-8')

				try: mpaa = item['certification']
				except: mpaa = '0'
				if mpaa == None: mpaa = '0'
				mpaa = mpaa.encode('utf-8')

				try: plot = item['overview'].encode('utf-8')
				except: plot = '0'
				if plot == None: plot = '0'
				plot = client.replaceHTMLCodes(plot)
				plot = plot.encode('utf-8')

				self.list.append({'title': title, 'originaltitle': title, 'year': year, 'premiered': premiered, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'plot': plot, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'poster': '0', 'next': next, 'progress' : progress})
			except:
				pass

		return self.list


	def trakt_user_list(self, url, user):
		try:
			result = trakt.getTrakt(url)
			items = json.loads(result)
		except:
			pass

		for item in items:
			try:
				try: name = item['list']['name']
				except: name = item['name']
				name = client.replaceHTMLCodes(name)
				name = name.encode('utf-8')

				try: url = (trakt.slug(item['list']['user']['username']), item['list']['ids']['slug'])
				except: url = ('me', item['ids']['slug'])
				url = self.traktlist_link % url
				url = url.encode('utf-8')

				self.list.append({'name': name, 'url': url, 'context': url})
			except:
				pass

		self.list = sorted(self.list, key=lambda k: re.sub('(^the |^a |^an )', '', k['name'].lower()))
		return self.list


	def imdb_list(self, url):
		try:
			for i in re.findall('date\[(\d+)\]', url):
				url = url.replace('date[%s]' % i, (self.datetime - datetime.timedelta(days = int(i))).strftime('%Y-%m-%d'))

			def imdb_watchlist_id(url):
				return client.parseDOM(client.request(url).decode('iso-8859-1').encode('utf-8'), 'meta', ret='content', attrs = {'property': 'pageId'})[0]

			if url == self.imdbwatchlist_link:
				# [GAIACODE]

				#url = cache.get(imdb_watchlist_id, 8640, url)
				url = cache.get(imdb_watchlist_id, 0, url) # Seems like IMDB takes a lot longer to load lists.

				# [/GAIACODE]
				url = self.imdblist_link % url

			elif url == self.imdbwatchlist2_link:
				# [GAIACODE]

				#url = cache.get(imdb_watchlist_id, 8640, url)
				url = cache.get(imdb_watchlist_id, 0, url) # Seems like IMDB takes a lot longer to load lists.

				# [/GAIACODE]
				url = self.imdblist2_link % url

			result = client.request(url)

			result = result.replace('\n','')
			result = result.decode('iso-8859-1').encode('utf-8')

			items = client.parseDOM(result, 'div', attrs = {'class': '.+? lister-item'}) + client.parseDOM(result, 'div', attrs = {'class': 'lister-item .+?'})
			items += client.parseDOM(result, 'div', attrs = {'class': 'list_item.+?'})
		except:
			return

		try:
			# Gaia
			# HTML syntax error, " directly followed by attribute name. Insert space in between. parseDOM can otherwise not handle it.
			result = result.replace('"class="lister-page-next', '" class="lister-page-next')

			next = client.parseDOM(result, 'a', ret='href', attrs = {'class': 'lister-page-next.+?'})

			if len(next) == 0:
				next = client.parseDOM(result, 'div', attrs = {'class': 'pagination'})[0]
				next = zip(client.parseDOM(next, 'a', ret='href'), client.parseDOM(next, 'a'))
				next = [i[0] for i in next if 'Next' in i[1]]

			next = url.replace(urlparse.urlparse(url).query, urlparse.urlparse(next[0]).query)
			next = client.replaceHTMLCodes(next)
			next = next.encode('utf-8')
		except:
			next = ''

		for item in items:
			try:
				title = client.parseDOM(item, 'a')[1]
				title = client.replaceHTMLCodes(title)
				title = title.encode('utf-8')

				year = client.parseDOM(item, 'span', attrs = {'class': 'lister-item-year.+?'})
				year += client.parseDOM(item, 'span', attrs = {'class': 'year_type'})
				year = re.findall('(\d{4})', year[0])[0]
				year = year.encode('utf-8')

				if int(year) > int((self.datetime).strftime('%Y')): raise Exception()

				imdb = client.parseDOM(item, 'a', ret='href')[0]
				imdb = re.findall('(tt\d*)', imdb)[0]
				imdb = imdb.encode('utf-8')

				# [GAIACODE]
				# parseDOM cannot handle elements without a closing tag.

				#try: poster = client.parseDOM(item, 'img', ret='loadlate')[0]
				#except: poster = '0'

				try:
					html = BeautifulSoup(item)
					poster = html.find_all('img')[0]['loadlate']
				except:
					poster = '0'
				# [/GAIACODE]

				if '/nopicture/' in poster: poster = '0'
				poster = re.sub('(?:_SX|_SY|_UX|_UY|_CR|_AL)(?:\d+|_).+?\.', '_SX500.', poster)
				poster = client.replaceHTMLCodes(poster)
				poster = poster.encode('utf-8')

				try: genre = client.parseDOM(item, 'span', attrs = {'class': 'genre'})[0]
				except: genre = '0'
				genre = ' / '.join([i.strip() for i in genre.split(',')])
				if genre == '': genre = '0'
				genre = client.replaceHTMLCodes(genre)
				genre = genre.encode('utf-8')

				try: duration = re.findall('(\d+?) min(?:s|)', item)[-1]
				except: duration = '0'
				duration = duration.encode('utf-8')

				rating = '0'
				try: rating = client.parseDOM(item, 'span', attrs = {'class': 'rating-rating'})[0]
				except:
					try: rating = client.parseDOM(rating, 'span', attrs = {'class': 'value'})[0]
					except:
						try: rating = client.parseDOM(item, 'div', ret='data-value', attrs = {'class': '.*?imdb-rating'})[0]
						except: pass
				if rating == '' or rating == '-': rating = '0'
				rating = client.replaceHTMLCodes(rating)
				rating = rating.encode('utf-8')

				votes = '0'
				try: votes = client.parseDOM(item, 'span', attrs = {'name': 'nv'})[0]
				except:
					try: votes = client.parseDOM(item, 'div', ret='title', attrs = {'class': '.*?rating-list'})[0]
					except:
						try: votes = re.findall('\((.+?) vote(?:s|)\)', votes)[0]
						except: pass
				if votes == '': votes = '0'
				votes = client.replaceHTMLCodes(votes)
				votes = votes.encode('utf-8')

				try: mpaa = client.parseDOM(item, 'span', attrs = {'class': 'certificate'})[0]
				except: mpaa = '0'
				if mpaa == '' or mpaa == 'NOT_RATED': mpaa = '0'
				mpaa = mpaa.replace('_', '-')
				mpaa = client.replaceHTMLCodes(mpaa)
				mpaa = mpaa.encode('utf-8')

				try: director = re.findall('Director(?:s|):(.+?)(?:\||</div>)', item)[0]
				except: director = '0'
				director = client.parseDOM(director, 'a')
				director = ' / '.join(director)
				if director == '': director = '0'
				director = client.replaceHTMLCodes(director)
				director = director.encode('utf-8')

				try: cast = re.findall('Stars(?:s|):(.+?)(?:\||</div>)', item)[0]
				except: cast = '0'
				cast = client.replaceHTMLCodes(cast)
				cast = cast.encode('utf-8')
				cast = client.parseDOM(cast, 'a')
				if cast == []: cast = '0'

				plot = '0'
				try: plot = client.parseDOM(item, 'p', attrs = {'class': 'text-muted'})[0]
				except:
					try: plot = client.parseDOM(item, 'div', attrs = {'class': 'item_description'})[0]
					except: pass
				plot = plot.rsplit('<span>', 1)[0].strip()
				plot = re.sub('<.+?>|</.+?>', '', plot)
				if plot == '': plot = '0'
				plot = client.replaceHTMLCodes(plot)
				plot = plot.encode('utf-8')

				self.list.append({'title': title, 'originaltitle': title, 'year': year, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director, 'cast': cast, 'plot': plot, 'imdb': imdb, 'tmdb': '0', 'tvdb': '0', 'poster': poster, 'next': next})
			except:
				pass

		return self.list


	def imdb_person_list(self, url):
		try:
			result = client.request(url)
			result = result.decode('iso-8859-1').encode('utf-8')
			items = client.parseDOM(result, 'div', attrs = {'class': '.+? lister-item'}) + client.parseDOM(result, 'div', attrs = {'class': 'lister-item .+?'})
		except:
			tools.Logger.error()

		for item in items:
			try:
				name = client.parseDOM(item, 'a')[1]
				name = client.replaceHTMLCodes(name)
				name = name.encode('utf-8')

				url = client.parseDOM(item, 'a', ret='href')[1]
				url = re.findall('(nm\d*)', url, re.I)[0]
				url = self.person_link % url
				url = client.replaceHTMLCodes(url)
				url = url.encode('utf-8')

				image = client.parseDOM(item, 'img', ret='src')[0]
				image = re.sub('(?:_SX|_SY|_UX|_UY|_CR|_AL)(?:\d+|_).+?\.', '_SX500.', image)
				image = client.replaceHTMLCodes(image)
				image = image.encode('utf-8')

				self.list.append({'name': name, 'url': url, 'image': image})
			except:
				tools.Logger.error()

		return self.list


	def imdb_user_list(self, url):
		try:
			result = client.request(url)
			result = result.decode('iso-8859-1').encode('utf-8')
			items = client.parseDOM(result, 'div', attrs = {'class': 'list_name'})
		except:
			pass

		for item in items:
			try:
				name = client.parseDOM(item, 'a')[0]
				name = client.replaceHTMLCodes(name)
				name = name.encode('utf-8')

				url = client.parseDOM(item, 'a', ret='href')[0]
				url = url.split('/list/', 1)[-1].replace('/', '')
				url = self.imdblist_link % url
				url = client.replaceHTMLCodes(url)
				url = url.encode('utf-8')

				self.list.append({'name': name, 'url': url, 'context': url})
			except:
				pass

		self.list = sorted(self.list, key=lambda k: re.sub('(^the |^a |^an )', '', k['name'].lower()))
		return self.list


	def worker(self, level=1):
		if self.list == None or self.list == []: return
		self.meta = []
		total = len(self.list)

		# [GAIACODE]
		self.fanart_tv_headers = {'api-key': tools.System.obfuscate(tools.Settings.getString('internal.fanart.api', raw = True))}
		# [/GAIACODE]
		if not self.fanart_tv_user == '':
			self.fanart_tv_headers.update({'client-key': self.fanart_tv_user})

		for i in range(0, total): self.list[i].update({'metacache': False})

		self.list = metacache.fetch(self.list, self.lang, self.user)

		for r in range(0, total, 40):
			threads = []
			for i in range(r, r+40):
				if i <= total: threads.append(workers.Thread(self.super_info, i))
			[i.start() for i in threads]
			[i.join() for i in threads]
			if self.meta: metacache.insert(self.meta)

		self.list = [i for i in self.list if not i['imdb'] == '0']

		self.list = metacache.local(self.list, self.tm_img_link, 'poster3', 'fanart2')

		if self.fanart_tv_user == '':
			for i in self.list: i.update({'clearlogo': '0', 'clearart': '0'})


	def metadataRetrieve(self, imdb):
		self.list = [{'imdb' : imdb}]
		self.worker()
		return self.list[0]


	def super_info(self, i):
		try:
			if self.list[i]['metacache'] == True: raise Exception()

			imdb = self.list[i]['imdb']

			item = trakt.getMovieSummary(imdb)

			title = item.get('title')
			title = client.replaceHTMLCodes(title)

			originaltitle = title

			year = item.get('year', 0)
			year = re.sub('[^0-9]', '', str(year))

			imdb = item.get('ids', {}).get('imdb', '0')
			imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))

			tmdb = str(item.get('ids', {}).get('tmdb', 0))

			premiered = item.get('released', '0')
			try: premiered = re.compile('(\d{4}-\d{2}-\d{2})').findall(premiered)[0]
			except: premiered = '0'

			genre = item.get('genres', [])
			genre = [x.title() for x in genre]
			genre = ' / '.join(genre).strip()
			if not genre: genre = '0'

			duration = str(item.get('Runtime', 0))

			rating = item.get('rating', '0')
			if not rating or rating == '0.0': rating = '0'

			votes = item.get('votes', '0')
			try: votes = str(format(int(votes), ',d'))
			except: pass

			mpaa = item.get('certification', '0')
			if not mpaa: mpaa = '0'

			tagline = item.get('tagline', '0')

			plot = item.get('overview', '0')

			people = trakt.getPeople(imdb, 'movies')

			director = writer = ''
			if 'crew' in people and 'directing' in people['crew']:
				director = ', '.join([director['person']['name'] for director in people['crew']['directing'] if director['job'].lower() == 'director'])
			if 'crew' in people and 'writing' in people['crew']:
				writer = ', '.join([writer['person']['name'] for writer in people['crew']['writing'] if writer['job'].lower() in ['writer', 'screenplay', 'author']])

			cast = []
			for person in people.get('cast', []):
				cast.append({'name': person['person']['name'], 'role': person['character']})
			cast = [(person['name'], person['role']) for person in cast]

			try:
				if self.lang == 'en' or self.lang not in item.get('available_translations', [self.lang]): raise Exception()
				trans_item = trakt.getMovieTranslation(imdb, self.lang, full=True)

				title = trans_item.get('title') or title
				tagline = trans_item.get('tagline') or tagline
				plot = trans_item.get('overview') or plot
			except:
				pass

			try:
				artmeta = True
				art = client.request(self.fanart_tv_art_link % imdb, headers=self.fanart_tv_headers, timeout='10', error=True)
				try: art = json.loads(art)
				except: artmeta = False
			except:
				pass

			try:
				poster2 = art['movieposter']
				poster2 = [x for x in poster2 if x.get('lang') == self.lang][::-1] + [x for x in poster2 if x.get('lang') == 'en'][::-1] + [x for x in poster2 if x.get('lang') in ['00', '']][::-1]
				poster2 = poster2[0]['url'].encode('utf-8')
			except:
				poster2 = '0'

			try:
				if 'moviebackground' in art: fanart = art['moviebackground']
				else: fanart = art['moviethumb']
				fanart = [x for x in fanart if x.get('lang') == self.lang][::-1] + [x for x in fanart if x.get('lang') == 'en'][::-1] + [x for x in fanart if x.get('lang') in ['00', '']][::-1]
				fanart = fanart[0]['url'].encode('utf-8')
			except:
				fanart = '0'

			try:
				banner = art['moviebanner']
				banner = [x for x in banner if x.get('lang') == self.lang][::-1] + [x for x in banner if x.get('lang') == 'en'][::-1] + [x for x in banner if x.get('lang') in ['00', '']][::-1]
				banner = banner[0]['url'].encode('utf-8')
			except:
				banner = '0'

			try:
				if 'hdmovielogo' in art: clearlogo = art['hdmovielogo']
				else: clearlogo = art['clearlogo']
				clearlogo = [x for x in clearlogo if x.get('lang') == self.lang][::-1] + [x for x in clearlogo if x.get('lang') == 'en'][::-1] + [x for x in clearlogo if x.get('lang') in ['00', '']][::-1]
				clearlogo = clearlogo[0]['url'].encode('utf-8')
			except:
				clearlogo = '0'

			try:
				if 'hdmovieclearart' in art: clearart = art['hdmovieclearart']
				else: clearart = art['clearart']
				clearart = [x for x in clearart if x.get('lang') == self.lang][::-1] + [x for x in clearart if x.get('lang') == 'en'][::-1] + [x for x in clearart if x.get('lang') in ['00', '']][::-1]
				clearart = clearart[0]['url'].encode('utf-8')
			except:
				clearart = '0'

			try:
				if self.tm_user == '': raise Exception()

				art2 = client.request(self.tm_art_link % imdb, timeout='10', error=True)
				art2 = json.loads(art2)
			except:
				pass

			try:
				poster3 = art2['posters']
				poster3 = [x for x in poster3 if x.get('iso_639_1') == 'en'] + [x for x in poster3 if not x.get('iso_639_1') == 'en']
				poster3 = [(x['width'], x['file_path']) for x in poster3]
				poster3 = [(x[0], x[1]) if x[0] < 300 else ('300', x[1]) for x in poster3]
				poster3 = self.tm_img_link % poster3[0]
				poster3 = poster3.encode('utf-8')
			except:
				poster3 = '0'

			try:
				fanart2 = art2['backdrops']
				fanart2 = [x for x in fanart2 if x.get('iso_639_1') == 'en'] + [x for x in fanart2 if not x.get('iso_639_1') == 'en']
				fanart2 = [x for x in fanart2 if x.get('width') == 1920] + [x for x in fanart2 if x.get('width') < 1920]
				fanart2 = [(x['width'], x['file_path']) for x in fanart2]
				fanart2 = [(x[0], x[1]) if x[0] < 1280 else ('1280', x[1]) for x in fanart2]
				fanart2 = self.tm_img_link % fanart2[0]
				fanart2 = fanart2.encode('utf-8')
			except:
				fanart2 = '0'

			item = {'title': title, 'originaltitle': originaltitle, 'year': year, 'imdb': imdb, 'tmdb': tmdb, 'poster': '0', 'poster2': poster2, 'poster3': poster3, 'banner': banner, 'fanart': fanart, 'fanart2': fanart2, 'clearlogo': clearlogo, 'clearart': clearart, 'premiered': premiered, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': writer, 'cast': cast, 'plot': plot, 'tagline': tagline}
			item = dict((k,v) for k, v in item.iteritems() if not v == '0')
			self.list[i].update(item)

			if artmeta == False: raise Exception()

			meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'lang': self.lang, 'user': self.user, 'item': item}
			self.meta.append(meta)

		except:
			pass


	def movieDirectory(self, items, next = True):
		if isinstance(items, dict) and 'value' in items:
			items = items['value']
		if isinstance(items, basestring):
			try: items = tools.Converter.jsonFrom(items)
			except: pass

		if items == None or len(items) == 0:
			interface.Loader.hide()
			interface.Dialog.notification(title = 32001, message = 33049, icon = interface.Dialog.IconInformation)
			sys.exit()

		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])

		addonPoster, addonBanner = control.addonPoster(), control.addonBanner()
		addonFanart, settingFanart = control.addonFanart(), tools.Settings.getBoolean('interface.fanart')
		traktCredentials = trakt.getTraktCredentialsInfo()

		try:
			isOld = False
			control.item().getArt('type')
		except:
			isOld = True

		isPlayable = 'true' if not 'plugin' in control.infoLabel('Container.PluginName') else 'false'
		indicators = playcount.getMovieIndicators(refresh = True) if action == 'movies' else playcount.getMovieIndicators()

		downloadsEnabled = tools.Settings.getBoolean('downloads.manual.enabled')
		libraryEnabled = tools.Settings.getBoolean('library.enabled')

		presetMenu = interface.Translation.string(35058) if tools.Settings.getBoolean('providers.customization.presets.enabled') else None
		playbackMenu = interface.Translation.string(32063) if tools.Settings.getBoolean('playback.automatic.enabled') else interface.Translation.string(32064)

		traktHas = trakt.getTraktIndicatorsInfo() == True
		watchedMenu = interface.Translation.string(32068) if traktHas else interface.Translation.string(32066)
		unwatchedMenu = interface.Translation.string(32069) if traktHas else interface.Translation.string(32067)

		informationMenu = interface.Translation.string(19033, system = True)
		shortcutsMenu = interface.Translation.string(35119)
		downloadManagerMenu = interface.Translation.string(33585)
		queueMenu = interface.Translation.string(32065)
		traktManagerMenu = interface.Translation.string(32070)
		nextMenu = interface.Translation.string(32053)
		libraryMenu = interface.Translation.string(35180)

		media = tools.Media()

		for i in items:
			try:
				label = None
				try: label = media.title(self.type, title = i['title'], year = i['year'])
				except: pass
				if label == None:
					label = i['title']

				try: label += ' (' + str(int(i['progress'] * 100)) + '%)'
				except: pass

				imdb, tmdb, title, year = i['imdb'], i['tmdb'], i['originaltitle'], i['year']
				sysname = urllib.quote_plus('%s (%s)' % (title, year))
				systitle = urllib.quote_plus(title)

				meta = dict((k,v) for k, v in i.iteritems() if not v == '0')
				meta.update({'code': imdb, 'imdbnumber': imdb, 'imdb_id': imdb})
				meta.update({'tmdb_id': tmdb})
				meta.update({'mediatype': 'movie'})
				meta.update({'trailer': '%s?action=trailer&name=%s' % (sysaddon, urllib.quote_plus(label))})
				#meta.update({'trailer': 'plugin://script.extendedinfo/?info=playtrailer&&id=%s' % imdb})

				# Gaia
				# Remove default time, since this might mislead users. Rather show no time.
				#if not 'duration' in i: meta.update({'duration': '120'})
				#elif i['duration'] == '0': meta.update({'duration': '120'})

				# Gaia
				# Some descriptions have a link at the end that. Remove it.
				try:
					plot = meta['plot']
					index = plot.rfind('See full summary')
					if index >= 0: plot = plot[:index]
					plot = plot.strip()
					if re.match('[a-zA-Z\d]$', plot): plot += ' ...'
					meta['plot'] = plot
				except: pass

				try: meta.update({'duration': str(int(meta['duration']) * 60)})
				except: pass
				try: meta.update({'genre': cleangenre.lang(meta['genre'], self.lang)})
				except: pass
				try: meta.update({'year': int(meta['year'])})
				except: pass

				sysmeta = urllib.quote_plus(json.dumps(meta))

				url = self.parameterize('%s?action=play&title=%s&year=%s&imdb=%s&meta=%s&t=%s' % (sysaddon, systitle, year, imdb, sysmeta, self.systime))
				sysurl = urllib.quote_plus(url)

				path = self.parameterize('%s?action=play&title=%s&year=%s&imdb=%s' % (sysaddon, systitle, year, imdb))

				cm = []

				cm.append((shortcutsMenu, 'RunPlugin(%s?action=shortcutsShow&link=%s&name=%s&create=1)' % (sysaddon, sysurl, label)))
				cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon))

				if libraryEnabled:
					link = self.parameterize('%s?action=libraryAdd&name=%s&title=%s&year=%s&imdb=%s&tmdb=%s&metadata=%s' % (sysaddon, sysname, systitle, year, imdb, tmdb, sysmeta))
					cm.append((libraryMenu, 'RunPlugin(%s)' % link))

				try:
					overlay = int(playcount.getMovieOverlay(indicators, imdb))
					if overlay == 7:
						if not traktHas:
							link = self.parameterize('%s?action=moviePlaycount&imdb=%s&query=6' % (sysaddon, imdb))
							cm.append((unwatchedMenu, 'RunPlugin(%s)' % link))
						meta.update({'playcount': 1, 'overlay': 7})
					else:
						if not traktHas:
							link = self.parameterize('%s?action=moviePlaycount&imdb=%s&query=7' % (sysaddon, imdb))
							cm.append((watchedMenu, 'RunPlugin(%s)' % link))
						meta.update({'playcount': 0, 'overlay': 6})
				except:
					pass

				if traktCredentials == True:
					link = self.parameterize('%s?action=traktManager&imdb=%s' % (sysaddon, imdb))
					cm.append((traktManagerMenu, 'RunPlugin(%s)' % link))

				if not self.kidsOnly() and downloadsEnabled:
					cm.append((downloadManagerMenu, 'Container.Update(%s?action=downloadsManager)' % (sysaddon)))

				cm.append((playbackMenu, 'RunPlugin(%s?action=alterSources&url=%s&meta=%s)' % (sysaddon, sysurl, sysmeta)))

				if presetMenu:
					cm.append((presetMenu, 'RunPlugin(%s?action=presetSources&url=%s&meta=%s)' % (sysaddon, sysurl, sysmeta)))

				if isOld: cm.append((informationMenu, 'Action(Info)'))

				item = control.item(label = label)

				art = {}

				poster = '0'
				if poster == '0' and 'poster3' in i: poster = i['poster3']
				if poster == '0' and 'poster2' in i: poster = i['poster2']
				if poster == '0' and 'poster' in i: poster = i['poster']

				icon = '0'
				if icon == '0' and 'icon3' in i: icon = i['icon3']
				if icon == '0' and 'icon2' in i: icon = i['icon2']
				if icon == '0' and 'icon' in i: icon = i['icon']

				thumb = '0'
				if thumb == '0' and 'thumb3' in i: thumb = i['thumb3']
				if thumb == '0' and 'thumb2' in i: thumb = i['thumb2']
				if thumb == '0' and 'thumb' in i: thumb = i['thumb']

				banner = '0'
				if banner == '0' and 'banner3' in i: banner = i['banner3']
				if banner == '0' and 'banner2' in i: banner = i['banner2']
				if banner == '0' and 'banner' in i: banner = i['banner']

				fanart = '0'
				if settingFanart:
					if fanart == '0' and 'fanart3' in i: fanart = i['fanart3']
					if fanart == '0' and 'fanart2' in i: fanart = i['fanart2']
					if fanart == '0' and 'fanart' in i: fanart = i['fanart']

				clearlogo = '0'
				if clearlogo == '0' and 'clearlogo' in i: clearlogo = i['clearlogo']

				clearart = '0'
				if clearart == '0' and 'clearart' in i: clearart = i['clearart']

				if poster == '0': poster = addonPoster
				if icon == '0': icon = poster
				if thumb == '0': thumb = poster
				if banner == '0': banner = addonBanner
				if fanart == '0': fanart = addonFanart

				if not poster == '0' and not poster == None: art.update({'poster' : poster})
				if not icon == '0' and not icon == None: art.update({'icon' : icon})
				if not thumb == '0' and not thumb == None: art.update({'thumb' : thumb})
				if not banner == '0' and not banner == None: art.update({'banner' : banner})
				if not clearlogo == '0' and not clearlogo == None: art.update({'clearlogo' : clearlogo})
				if not clearart == '0' and not clearart == None: art.update({'clearart' : clearart})
				if not fanart == '0' and not fanart == None: item.setProperty('Fanart_Image', fanart)

				item.setArt(art)
				item.addContextMenuItems(cm)
				item.setProperty('IsPlayable', isPlayable)
				item.setInfo(type='Video', infoLabels = meta)

				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=False)
			except:
				pass

		if next:
			try:
				url = items[0]['next']
				if url == '': raise Exception()

				url = '%s?action=moviePage&url=%s' % (sysaddon, urllib.quote_plus(url))
				url = self.parameterize(url)

				item = control.item(label=nextMenu)

				item.setProperty('nextpage', 'true') # Used by skin.gaia.aeon.nox

				iconIcon, iconThumb, iconPoster, iconBanner = interface.Icon.pathAll(icon = 'next.png', default = 'DefaultFolder.png')
				item.setArt({'icon': iconIcon, 'thumb': iconThumb, 'poster': iconPoster, 'banner': iconBanner})

				if not addonFanart == None: item.setProperty('Fanart_Image', addonFanart)

				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
			except:
				pass

		control.content(syshandle, 'movies')
		control.directory(syshandle, cacheToDisc=True)
		if self.type == tools.Media.TypeDocumentary:
			content = 'documentaries'
		elif self.type == tools.Media.TypeShort:
			content = 'shorts'
		else:
			content = 'movies'
		views.setView(content, {'skin.estuary': 55, 'skin.confluence': 500})

	def addDirectory(self, items, queue = False):
		if items == None or len(items) == 0:
			interface.Loader.hide()
			interface.Dialog.notification(title = 32001, message = 33049, icon = interface.Dialog.IconInformation)
			sys.exit()

		sysaddon = sys.argv[0]

		syshandle = int(sys.argv[1])

		addonFanart = control.addonFanart()
		addonThumb = control.addonThumb()

		libraryEnabled = tools.Settings.getBoolean('library.enabled')

		queueMenu = interface.Translation.string(32065)
		libraryMenu = interface.Translation.string(35180)

		for i in items:
			try:
				name = i['name']
				url = '%s?action=%s' % (sysaddon, i['action'])
				try: url += '&url=%s' % urllib.quote_plus(i['url'])
				except: pass

				cm = []

				if queue == True:
					cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon))

				if libraryEnabled:
					try:
						link = i['context'] if 'context' in i else i['url']
						link = self.parameterize('%s?action=libraryAdd&link=%s' % (sysaddon, urllib.quote_plus(link)))
						cm.append((libraryMenu, 'RunPlugin(%s)' % link))
					except: pass

				item = control.item(label=name)

				if i['image'].startswith('http'):
					iconIcon = iconThumb = iconPoster = iconBanner = i['image']
				else:
					iconIcon, iconThumb, iconPoster, iconBanner = interface.Icon.pathAll(icon = i['image'], default = addonThumb)
				item.setArt({'icon': iconIcon, 'thumb': iconThumb, 'poster': iconPoster, 'banner': iconBanner})

				if not addonFanart == None: item.setProperty('Fanart_Image', addonFanart)

				item.addContextMenuItems(cm)

				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
			except Exception as error:
				tools.Logger.error()
				pass

		control.content(syshandle, 'addons')
		control.directory(syshandle, cacheToDisc=True)
