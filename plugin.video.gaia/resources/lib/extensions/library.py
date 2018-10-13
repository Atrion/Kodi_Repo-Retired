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
import sys
import urllib
import urlparse
import threading
import datetime
import time

from resources.lib.extensions import tools
from resources.lib.extensions import interface
from resources.lib.extensions import database

class Library(object):

	DatabaseName = 'library'

	UpdateFlag = 'gaialibrary'
	UpdateInterval = 21600 # Number of seconds between library updates by the service.
	UpdateCheck = 120 # Number of seconds between checking if the system was aborted.

	InfoMovie = 'movie'
	InfoShow = 'tv'

	LinkTvdb = 'http://thetvdb.com/?tab=series&id=%s'
	LinkTmdb = 'https://www.themoviedb.org/%s/%s'
	LinkImdb = 'http://www.imdb.com/title/%s/'

	##############################################################################
	# CONSTRUCTORS
	##############################################################################

	def __init__(self, type = tools.Media.TypeNone, kids = tools.Selection.TypeUndefined):
		self.mType = type
		self.mTypeMovie = tools.Media.typeMovie(self.mType)
		self.mTypeTelevision = tools.Media.typeTelevision(self.mType)
		self.mInfo = self.InfoShow if self.mTypeTelevision else self.InfoMovie
		self.mKids = kids

		self.mDuplicates = tools.Settings.getBoolean('library.general.duplicates')
		self.mPrecheck = tools.Settings.getBoolean('library.general.precheck')
		self.mUnaired = tools.Settings.getBoolean('library.general.unaired')
		self.mUpdate = tools.Settings.getBoolean('library.updates.automatic')

		self.mLocation = self._location()
		self.mDialog = False

	##############################################################################
	# INTERNAL
	##############################################################################

	def _parameterize(self, link):
		if not self.mType == None: link += '&type=%s' % self.mType
		if not self.mKids == None: link += '&kids=%d' % self.mKids
		return link

	def _location(self, type = None):
		if type == None: type = self.mType
		if type == None: return None
		path = None
		if tools.Settings.getInteger('library.locations.selection') == 0:
			if type == tools.Media.TypeMovie: label = 32001
			elif type == tools.Media.TypeDocumentary: label = 33470
			elif type == tools.Media.TypeShort: label = 33471
			elif type == tools.Media.TypeShow or type == tools.Media.TypeSeason or type == tools.Media.TypeEpisode: label = 32002
			path = tools.File.joinPath(tools.Settings.getString('library.locations.combined'), interface.Translation.string(label))
		else:
			if type == tools.Media.TypeMovie: setting = 'movies'
			elif type == tools.Media.TypeDocumentary: setting = 'documentaries'
			elif type == tools.Media.TypeShort: setting = 'shorts'
			elif type == tools.Media.TypeShow or type == tools.Media.TypeSeason or type == tools.Media.TypeEpisode: setting = 'shows'
			path = tools.Settings.getString('library.locations.%s' % setting)
		path = path.strip()
		if not path.endswith('\\') and not path.endswith('/'): path += '/'
		tools.File.makeDirectory(path)
		return path

	@classmethod
	def _createDirectory(self, path):
		try:
			if path.startswith('ftp://') or path.startswith('ftps://'):
				from ftplib import FTP
				arguments = re.compile('ftp://(.+?):(.+?)@(.+?):?(\d+)?/(.+/?)').findall(path)
				ftp = FTP(arguments[0][2], arguments[0][0], arguments[0][1])
				try: ftp.cwd(arguments[0][4])
				except: ftp.mkd(arguments[0][4])
				ftp.quit()
			else:
				path = tools.File.legalPath(path)
				if not tools.File.existsDirectory(path):
					return tools.File.makeDirectory(path)
			return True
		except:
			tools.Logger.error()
			return False

	@classmethod
	def _writeFile(self, path, content):
		try:
			path = tools.File.legalPath(path)
			return tools.File.writeNow(path, content)
		except:
			return False

	def _infoLink(self, ids):
		if 'tvdb' in ids and not str(ids['tvdb']) == '' and not str(ids['tvdb']) == '0':
			return self.LinkTvdb % (str(ids['tvdb']))
		elif 'tmdb' in ids and not str(ids['tmdb']) == '' and not str(ids['tmdb']) == '0':
			return self.LinkTmdb % (self.mInfo, str(ids['tmdb']))
		elif 'imdb' in ids and not str(ids['imdb']) == '' and not str(ids['imdb']) == '0':
			return self.LinkImdb % (str(ids['imdb']))
		else:
			return ''

	@classmethod
	def _checkSources(self, title, year, imdb, tvdb = None, season = None, episode = None, tvshowtitle = None, premiered = None):
		try:
			from resources.lib.extensions import core
			streams = core.Core().getSources(title, year, imdb, tvdb, season, episode, tvshowtitle, premiered)
			return streams and len(streams) > 1
		except:
			return False

	@classmethod
	def _legalPath(self, path):
		try:
			path = path.strip()
			path = re.sub(r'(?!%s)[^\w\-_\.]', '.', path)
			path = re.sub('\.+', '.', path)
			path = re.sub(re.compile('(CON|PRN|AUX|NUL|COM\d|LPT\d)\.', re.I), '\\1_', path)
		except:
			pass
		return path

	@classmethod
	def _path(self, path, title, year = None, season = None):
		show = re.sub(r'[^\w\-_\. ]', '_', title)
		show = '%s (%s)' % (show, str(year)) if year else show
		path = tools.File.joinPath(path, show)
		if season: path = tools.File.joinPath(path, interface.Translation.string(32055) + ' ' + str(season))
		return path

	@classmethod
	def _ready(self):
		return not tools.System.visible('Window.IsVisible(infodialog)') and not tools.System.visible('Player.HasVideo')

	@classmethod
	def _libraryBusy(self):
		return tools.System.visible('Library.IsScanningVideo')

	def _libraryUpdate(self):
		# Updating specific paths creates problems, since the user might have a special:// path in Gaia settings and a C:/ path in the Kodi library.
		# Kodi does not see these two paths as the same, and will therefore not update the library.
		# Scan the entire library instead.
		#tools.System.execute('UpdateLibrary(video,%s)' % self.mLocation)
		tools.System.execute('UpdateLibrary(video)')

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def settings(self):
		tools.Settings.launch(category = tools.Settings.CategoryLibrary)

	def local(self):
		type = 'tvshows' if tools.Media.typeTelevision(self.mType) else 'movies'
		tools.System.execute('ActivateWindow(10025,library://video/%s/,return)' % type)

	def location(self):
		return self.mLocation

	##############################################################################
	# MOVIES
	##############################################################################

	def _movieAddSingle(self, title, year, imdb, tmdb, metadata, multiple = False):
		count = 0

		if self._ready() and not multiple:
			interface.Dialog.notification(title = 33244, message = 35177, icon = interface.Dialog.IconInformation, time = 100000000)
			self.mDialog = True

		try:
			if self.mDuplicates:
				id = [imdb, tmdb] if not tmdb == '0' else [imdb]
				library = tools.System.executeJson('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties" : ["imdbnumber", "originaltitle", "year"]}, "id": 1}' % (year, str(int(year)+1), str(int(year)-1)))
				library = unicode(library, 'utf-8', errors='ignore')
				library = tools.Converter.jsonFrom(library)['result']['movies']
				library = [i for i in library if str(i['imdbnumber']) in id or (i['originaltitle'].encode('utf-8') == title and str(i['year']) == year)]
		except:
			library = []

		if len(library) == 0:
			if not self.mPrecheck or self._checkSources(title, year, imdb, None, None, None, None, None):
				self._movieFiles(title, year, imdb, tmdb, metadata)
				count += 1

		return count

	def _movieAddMultiple(self, link):
		interface.Loader.hide()
		count = -1

		if interface.Dialog.option(title = 33244, message = 35179):
			count = 0
			if self._ready():
				interface.Dialog.notification(title = 33244, message = 35177, icon = interface.Dialog.IconInformation, time = 100000000)
				self.mDialog = True

			from resources.lib.indexers import movies
			items = movies.movies().get(link, idx = True, notifications = False)
			if items == None: items = []

			for i in items:
				try:
					if tools.System.aborted(): return sys.exit()
					count += self._movieAddSingle(i['title'], i['year'], i['imdb'], i['tmdb'], i, multiple = True)
				except:
					pass

		return count

	def _movieFiles(self, title, year, imdb, tmdb, metadata = None):
		try:
			name = re.sub('([^\s\w]|_)+', '', title)

			# Do not save the metadata to file. The link becomes too long and Kodi cuts it off.
			#metadata = urllib.quote_plus(tools.Converter.jsonTo(metadata))
			#link = '%s?action=play&title=%s&year=%s&imdb=%s&tmdb=%s&meta=%s' % (sys.argv[0], urllib.quote_plus(title), year, imdb, tmdb, metadata)
			link = '%s?action=play&title=%s&year=%s&imdb=%s&tmdb=%s' % (sys.argv[0], urllib.quote_plus(title), year, imdb, tmdb)

			link = self._parameterize(link)

			path = self._path(self.mLocation, name, year)
			self._createDirectory(path)

			pathSrtm = tools.File.joinPath(path, self._legalPath(name) + '.strm')
			self._writeFile(pathSrtm, link)

			pathNfo = tools.File.joinPath(path, 'movie.nfo')
			self._writeFile(pathNfo, self._infoLink({'imdb': imdb, 'tmdb': tmdb}))
		except:
			tools.Logger.error()

	##############################################################################
	# SHOW
	##############################################################################

	def _televisionAddSingle(self, title, year, imdb, tvdb, metadata, multiple = False):
		count = 0

		if self._ready() and not multiple:
			interface.Dialog.notification(title = 33244, message = 35177, icon = interface.Dialog.IconInformation, time = 100000000)
			self.mDialog = True

		from resources.lib.indexers import episodes
		items = episodes.episodes().get(title, year, imdb, tvdb, idx = False)

		try: items = [{'title': i['title'], 'year': i['year'], 'imdb': i['imdb'], 'tvdb': i['tvdb'], 'season': i['season'], 'episode': i['episode'], 'tvshowtitle': i['tvshowtitle'], 'premiered': i['premiered'], 'seasoncount': i['seasoncount'] if 'seasoncount' in i else None} for i in items]
		except: items = []

		try:
			if self.mDuplicates and len(items) > 0:
				id = [items[0]['imdb'], items[0]['tvdb']]

				library = tools.System.executeJson('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"properties" : ["imdbnumber", "title", "year"]}, "id": 1}')
				library = unicode(library, 'utf-8', errors='ignore')
				library = tools.Converter.jsonFrom(library)['result']['tvshows']
				library = [i['title'].encode('utf-8') for i in library if str(i['imdbnumber']) in id or (i['title'].encode('utf-8') == items[0]['tvshowtitle'] and str(i['year']) == items[0]['year'])][0]

				library = tools.System.executeJson('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"filter":{"and": [{"field": "tvshow", "operator": "is", "value": "%s"}]}, "properties": ["season", "episode"]}, "id": 1}' % library)
				library = unicode(library, 'utf-8', errors='ignore')
				library = tools.Converter.jsonFrom(library)['result']['episodes']
				library = ['S%02dE%02d' % (int(i['season']), int(i['episode'])) for i in library]

				items = [i for i in items if not 'S%02dE%02d' % (int(i['season']), int(i['episode'])) in library]
		except:
			pass

		dateCurrent = int((datetime.datetime.utcnow() - datetime.timedelta(hours = 6)).strftime('%Y%m%d'))

		for i in items:
			try:
				if tools.System.aborted(): return sys.exit()

				if self.mPrecheck:
					if i['episode'] == '1':
						self.mBlock = True
						streams = self._checkSources(i['title'], i['year'], i['imdb'], i['tvdb'], i['season'], i['episode'], i['tvshowtitle'], i['premiered'])
						if streams: self.mBlock = False
					if self.mBlock: raise Exception()

				try: premiered = i['premiered']
				except: premiered = None
				if not premiered or premiered == '' or premiered =='0': premiered = None

				if (premiered and int(re.sub('[^0-9]', '', str(premiered))) > dateCurrent) or (not premiered and not self.mUnaired):
					continue

				self._televisionFiles(item = i, metadata = metadata)
				count += 1
			except:
				tools.Logger.error()

		return count

	def _televisionAddMultiple(self, link):
		interface.Loader.hide()
		count = -1

		if interface.Dialog.option(title = 33244, message = 35179):
			count = 0
			if self._ready():
				interface.Dialog.notification(title = 33244, message = 35177, icon = interface.Dialog.IconInformation, time = 100000000)
				self.mDialog = True

			items = None
			try:
				from resources.lib.indexers import tvshows
				items = tvshows.tvshows().get(link, idx = False, notifications = False)
			except:
				pass
			if not items or len(items) == 0:
				from resources.lib.indexers import episodes
				items = episodes.episodes().calendar(link)
			if items == None: items = []

			for i in items:
				try:
					if tools.System.aborted(): return sys.exit()
					count += self._televisionAddSingle(i['tvshowtitle'] if 'tvshowtitle' in i else i['title'], i['year'], i['imdb'], i['tvdb'], i, multiple = True)
				except:
					pass

		return count

	def _televisionFiles(self, item, metadata = None):
		try:
			title, year, imdb, tvdb, season, episode, showtitle, premiered, seasoncount = item['title'], item['year'], item['imdb'], item['tvdb'], item['season'], item['episode'], item['tvshowtitle'], item['premiered'], item['seasoncount']
			try: seasoncount = int(seasoncount)
			except: seasoncount = None

			name = re.sub('([^\s\w]|_)+', '', showtitle)
			title = urllib.quote_plus(title)
			showtitle = urllib.quote_plus(showtitle)
			premiered = urllib.quote_plus(premiered)

			# Do not save the metadata to file. The link becomes too long and Kodi cuts it off.
			#metadata = urllib.quote_plus(tools.Converter.jsonTo(metadata))
			#link = '%s?action=play&title=%s&year=%s&imdb=%s&tvdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s&meta=%s' % (sys.argv[0], title, year, imdb, tvdb, season, episode, showtitle, premiered, metadata)
			if seasoncount: link = '%s?action=play&title=%s&year=%s&imdb=%s&tvdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s&seasoncount=%i' % (sys.argv[0], title, year, imdb, tvdb, season, episode, showtitle, premiered, seasoncount)
			else: link = '%s?action=play&title=%s&year=%s&imdb=%s&tvdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s' % (sys.argv[0], title, year, imdb, tvdb, season, episode, showtitle, premiered)

			path = self._path(self.mLocation, name, year)

			pathNfo = tools.File.joinPath(path, 'tvshow.nfo')
			self._createDirectory(path)
			self._writeFile(pathNfo, self._infoLink(item))

			path = self._path(self.mLocation, name, year, season)
			pathSrtm = tools.File.joinPath(path, self._legalPath('%s S%02dE%02d' % (showtitle, int(season), int(episode))) + '.strm')
			self._createDirectory(path)
			self._writeFile(pathSrtm, link)
		except:
			tools.Logger.error()

	##############################################################################
	# SERVICE
	##############################################################################

	@classmethod
	def service(self, background = True, continues = True, gaia = False):
		setting = tools.Settings.getInteger('library.updates.shows')
		if tools.Settings.getBoolean('library.enabled') and setting > 0:
			if (not gaia and (setting == 1 or setting == 3)) or (gaia and (setting == 2 or setting == 3)):
				if background:
					tools.System.executePlugin(action = 'libraryService')
				else:
					library = Library(type = tools.Media.TypeShow)
					if continues:
						flag = tools.System.windowPropertyGet(self.UpdateFlag)
						if not flag == '1':
							tools.System.windowPropertySet(self.UpdateFlag, '1')
							interval = self.UpdateInterval / self.UpdateCheck
							while True:
								library.update(wait = True)
								for i in range(interval):
									time.sleep(self.UpdateCheck)
									if tools.System.aborted(): sys.exit()
					else:
						library.update()

	##############################################################################
	# UPDATE
	##############################################################################

	@classmethod
	def update(self, notifications = None, wait = True): # Must wait, otherwise the script finishes before the thread.
		library = Library(type = tools.Media.TypeShow)
		thread = threading.Thread(target = library._update, args = (notifications, ))
		thread.start()
		if wait: thread.join()

	def _update(self, notifications = None):
		try:
			self._createDirectory(self._location(tools.Media.TypeMovie))
			self._createDirectory(self._location(tools.Media.TypeShow))
			self._createDirectory(self._location(tools.Media.TypeDocumentary))
			self._createDirectory(self._location(tools.Media.TypeShort))
		except:
			pass

		if notifications == None:
			notifications = tools.Settings.getInteger('library.updates.shows.notifications')
			notificationDuration = 10000000000 if notifications == 2 else 3000
			notifications = notifications > 0
		interface.Loader.hide()

		try:
			items = []
			season, episode = [], []
			show = [tools.File.joinPath(self.mLocation, i) for i in tools.File.listDirectory(self.mLocation)[0]]
			for s in show:
				try: season += [tools.File.joinPath(s, i) for i in tools.File.listDirectory(s)[0]]
				except: pass
			for s in season:
				try: episode.append([tools.File.joinPath(s, i) for i in tools.File.listDirectory(s)[1] if i.endswith('.strm')][-1])
				except: pass

			for file in episode:
				try:
					data = tools.File.readNow(file).encode('utf-8')
					if not data.startswith(sys.argv[0]): raise Exception()

					params = dict(urlparse.parse_qsl(data.replace('?','')))

					try: tvshowtitle = params['tvshowtitle']
					except: tvshowtitle = None
					try: tvshowtitle = params['show']
					except: pass
					if tvshowtitle == None or tvshowtitle == '': raise Exception()

					year, imdb, tvdb = params['year'], params['imdb'], params['tvdb']

					imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))

					try: tmdb = params['tmdb']
					except: tmdb = '0'

					items.append({'tvshowtitle': tvshowtitle, 'year': year, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb})
				except:
					pass

			items = [i for x, i in enumerate(items) if i not in items[x + 1:]]
			if len(items) == 0: raise Exception()
		except:
			return

		try:
			library = tools.System.executeJson('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"properties" : ["imdbnumber", "title", "year"]}, "id": 1}')
			library = unicode(library, 'utf-8', errors = 'ignore')
			library = tools.Converter.jsonFrom(library)['result']['tvshows']
		except:
			return

		if notifications and self._ready():
			interface.Dialog.notification(title = 33244, message = 35181, icon = interface.Dialog.IconInformation, time = notificationDuration)
			self.mDialog = True

		try:
			base = database.Database(name = self.DatabaseName)
			base._create('CREATE TABLE IF NOT EXISTS shows (id TEXT, items TEXT, UNIQUE(id));')
		except:
			return

		try: from resources.lib.indexers import episodes
		except: return

		count = 0

		for item in items:
			if tools.System.aborted(): return sys.exit()
			it = None

			try:
				fetch = base._selectSingle('SELECT * FROM shows WHERE id = "%s";' % item['tvdb'])
				it = tools.Converter.jsonFrom(tools.Converter.base64From(fetch[1].encode('utf-8')))
			except:
				pass

			try:
				if not it == None: raise Exception()
				it = episodes.episodes().get(item['tvshowtitle'], item['year'], item['imdb'], item['tvdb'], idx = False)

				status = it[0]['status'].lower()
				it = [{'title': i['title'], 'year': i['year'], 'imdb': i['imdb'], 'tvdb': i['tvdb'], 'season': i['season'], 'episode': i['episode'], 'tvshowtitle': i['tvshowtitle'], 'premiered': i['premiered'], 'seasoncount': i['seasoncount'] if 'seasoncount' in i else None} for i in it]

				if status == 'continuing': raise Exception()

				json = tools.Converter.base64To(tools.Converter.jsonTo(it))
				base._insert('INSERT INTO shows VALUES ("%s", "%s");' % (item['tvdb'], json))
			except:
				pass

			try:
				id = [item['imdb'], item['tvdb']]
				if not item['tmdb'] == '0': id += [item['tmdb']]

				episode = [x['title'].encode('utf-8') for x in library if str(x['imdbnumber']) in id or (x['title'].encode('utf-8') == item['tvshowtitle'] and str(x['year']) == item['year'])][0]
				episode = tools.System.executeJson('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params": {"filter":{"and": [{"field": "tvshow", "operator": "is", "value": "%s"}]}, "properties": ["season", "episode"]}, "id": 1}' % episode)
				episode = unicode(episode, 'utf-8', errors = 'ignore')
				episode = tools.Converter.jsonFrom(episode).get('result', {}).get('episodes', {})
				episode = [{'season': int(i['season']), 'episode': int(i['episode'])} for i in episode]
				episode = sorted(episode, key=lambda x: (x['season'], x['episode']))[-1]

				num = [x for x, y in enumerate(it) if str(y['season']) == str(episode['season']) and str(y['episode']) == str(episode['episode'])][-1]
				it = [y for x, y in enumerate(it) if x > num]
				if len(it) == 0: continue
			except:
				continue

			dateCurrent = int((datetime.datetime.utcnow() - datetime.timedelta(hours = 6)).strftime('%Y%m%d'))

			for i in it:
				try:
					if tools.System.aborted(): return sys.exit()

					try: premiered = i['premiered']
					except: premiered = None
					if not premiered or premiered == '' or premiered =='0': premiered = None

					#if (premiered and int(re.sub('[^0-9]', '', str(premiered))) > dateCurrent) or (not premiered and not self.mUnaired):
					#	continue

					self._televisionFiles(i)
					count += 1
				except:
					tools.Logger.error()

		if notifications and self.mDialog:
			interface.Dialog.notification(title = 33244, message = 35182, icon = interface.Dialog.IconSuccess)
		if self.mUpdate and not self._libraryBusy() and count > 0:
			self._libraryUpdate()

	##############################################################################
	# ADD
	##############################################################################

	def add(self, link = None, title = None, year = None, imdb = None, tmdb = None, tvdb = None, metadata = None):
		count = -1

		try: metadata = tools.Converter.jsonFrom(metadata)
		except: pass

		if self.mTypeMovie:
			if link == None: count = self._movieAddSingle(title = title, year = year, imdb = imdb, tmdb = tmdb, metadata = metadata)
			else: count = self._movieAddMultiple(link = link)
		elif self.mTypeTelevision:
			if link == None: count = self._televisionAddSingle(title = title, year = year, imdb = imdb, tvdb = tvdb, metadata = metadata)
			else: count = self._televisionAddMultiple(link = link)

		if count >= 0:
			if self.mDialog:
				if count > 0: interface.Dialog.notification(title = 33244, message = 35178, icon = interface.Dialog.IconSuccess)
				else: interface.Dialog.notification(title = 33244, message = 35196, icon = interface.Dialog.IconError)
			if self.mUpdate and not self._libraryBusy() and count > 0:
				self._libraryUpdate()
