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
# ORIONITEM
##############################################################################
# Class for handling items that contain movie/show info and a list of streams.
##############################################################################

import re
import threading
from orion.modules.oriontools import *
from orion.modules.orionstream import *
from orion.modules.orionapi import *
from orion.modules.orionapp import *
from orion.modules.orionsettings import *

class OrionItem:

	##############################################################################
	# CONSTANTS
	##############################################################################

	TypeMovie = 'movie'
	TypeShow = 'show'

	IdOrion = 'orion'
	IdImdb = 'imdb'
	IdTmdb = 'tmdb'
	IdTvdb = 'tvdb'
	IdDefault = IdOrion

	SelectDefault = None
	SelectMovie = 'movie'
	SelectShow = 'show'
	SelectSeason = 'season'
	SelectEpisode = 'episode'

	AccessDirect = 'direct'
	AccessIndirect = 'indirect'
	AccessPremiumize = 'premiumize'
	AccessOffcloud = 'offcloud'
	AccessRealdebrid = 'realdebrid'

	FilterNone = None
	FilterSettings = -1

	SortShuffle = 'shuffle'
	SortPopularity = 'popularity'
	SortTimeAdded = 'timeadded'
	SortTimeUpdated = 'timeupdated'
	SortVideoQuality = 'videoquality'
	SortAudioChannels = 'audiochannels'
	SortFileSize = 'filesize'
	SortStreamSeeds = 'streamseeds'
	SortStreamAge = 'streamage'
	SortIds = [None, SortShuffle, SortPopularity, SortTimeAdded, SortTimeUpdated, SortVideoQuality, SortAudioChannels, SortFileSize, SortStreamSeeds, SortStreamAge]

	OrderAscending = 'ascending'
	OrderDescending = 'descendig'
	OrderIds = [OrderAscending, OrderDescending]

	VoteUp = OrionApi.VoteUp
	VoteDown = OrionApi.VoteDown

	ChoiceInclude = 'include'
	ChoiceExclude = 'exclude'
	ChoiceRequire = 'require'
	ChoiceIds = [ChoiceInclude, ChoiceExclude, ChoiceRequire]

	QualityOrder = [None] + OrionStream.QualityOrder
	ChannelsOrder = [None] + OrionStream.ChannelsOrder

	Editions = ['extended']

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self, data = {}):
		self.mData = None
		self.mStreams = None
		self.dataSet(data = data)

	##############################################################################
	# INTERNAL
	##############################################################################

	def _select(self, select):
		return self.type() if select == self.SelectDefault else select

	def _valid(self, value):
		return not value == None and not value == ''

	##############################################################################
	# ACCESS
	##############################################################################

	def _accessEqual(self, access1, access2):
		for key1, value1 in access1.iteritems():
			for key2, value2 in access2.iteritems():
				if key1 == key2 and not value1 == value2:
					return False
		return True

	def _accessSave(self):
		access = {}
		for stream in self.mData['streams']:
			access[OrionTools.hash(stream['stream']['link'])] = stream['access']
		OrionSettings.set('internal.api.access', access)

	def _accessLoad(self):
		access = OrionSettings.getObject('internal.api.access')
		if access:
			streams = []
			for stream in self.mData['streams']:
				if not 'orion' in stream or not stream['orion']:
					streams.append(stream)
				elif 'orion' in stream and stream['orion']:
					id = OrionTools.hash(stream['stream']['link'])
					if not self._accessEqual(access[id], stream['access']):
						# Only send neccessary information
						new = {'orion' : True, 'access' : stream['access']}
						try:
							if len(stream['file']['hash']) > 0:
								new['file'] = {'hash' : stream['file']['hash']}
						except:
							try: new['stream'] = {'link' : stream['stream']['link']}
							except: pass
						try: new['movie'] = {'id' : stream['movie']['id']}
						except: pass
						try: new['show'] = {'id' : stream['show']['id']}
						except: pass
						try: new['episode'] = {'number' : stream['episode']['number']}
						except: pass
						streams.append(new)
			self.mData['streams'] = streams
			OrionSettings.set('internal.api.access', '')

	##############################################################################
	# UPDATE
	##############################################################################

	def update(self):
		try:
			if self.mStreams == None or self.mStreams == []: return False
			if not self.mData['type']: return False

			if self.mData['type'] == self.TypeMovie:
				if not self._valid(self.mData['movie']['id']['imdb']): return False
			elif self.mData['type'] == self.TypeShow:
				if not self._valid(self.mData['show']['id']['imdb']): return False
				if not self._valid(self.mData['episode']['number']['season']): return False
				if not self._valid(self.mData['episode']['number']['episode']): return False
			else:
				return False

			# Invalid links
			streams = []
			for stream in self.mData['streams']:
				link = stream['stream']['link']
				if link == None or link == '': continue
				magnet = link.startswith('magnet:')

				# Not a standard torrent magnet of HTTP/FTP link
				if not magnet and not link.startswith('http://') and not link.startswith('https://') and not link.startswith('ftp://') and not link.startswith('ftps://'):
					continue

				if not magnet:
					# Not normal link (eg: http://localhost or http://downloads)
					if not '.' in link.split('://')[1].split('/')[0]: continue

					# Streams with cookie/session/headers
					if '|' in link: continue

					# Very long links which are most likely invalid or contain other cookie/session/headers data
					if len(link) > 1024: continue

				if len(link) > 100000: continue

				streams.append(stream)
			self.mData['streams'] = streams
			self._accessLoad()
			if len(self.mData['streams']) == 0: return False
			return OrionApi().streamUpdate(self.mData)
		except:
			OrionTools.error()
			return False

	##############################################################################
	# RETRIEVE
	##############################################################################

	@classmethod
	def retrieve(self,

				type,

				query = None,

				idOrion = None,
				idImdb = None,
				idTmdb = None,
				idTvdb = None,

				numberSeason = None,
				numberEpisode = None,

				limitCount = FilterSettings,
				limitRetry = FilterSettings,
				limitOffset = FilterSettings,
				limitPage = FilterSettings,

				timeAdded = FilterSettings,
				timeAddedAge = FilterSettings,
				timeUpdated = FilterSettings,
				timeUpdatedAge = FilterSettings,

				sortValue = FilterSettings,
				sortOrder = FilterSettings,

				popularityPercent = FilterSettings,
				popularityCount = FilterSettings,

				streamType = FilterSettings,
				streamSource = FilterSettings,
				streamHoster = FilterSettings,
				streamSeeds = FilterSettings,
				streamAge = FilterSettings,

				access = FilterSettings,

				fileSize = FilterSettings,
				fileUnknown = FilterSettings,
				filePack = FilterSettings,

				metaRelease = FilterSettings,
				metaUploader = FilterSettings,
				metaEdition = FilterSettings,

				videoQuality = FilterSettings,
				videoCodec = FilterSettings,
				video3D = FilterSettings,

				audioType = FilterSettings,
				audioChannels = FilterSettings,
				audioCodec = FilterSettings,
				audioLanguages = FilterSettings,

				subtitleType = FilterSettings,
				subtitleLanguages = FilterSettings,

				item = None
			):

		try:
			from orion.modules.orionintegration import OrionIntegration
			addon = OrionIntegration.id(OrionApp.instance().name(), check = True)
			if not OrionSettings.getFiltersEnabled(addon): addon = None

			def pick(addon, function):
				include = getattr(OrionSettings, function)(addon, True, False)
				if include == None: include = []
				exclude = getattr(OrionSettings, function)(addon, False, True)
				if exclude == None: exclude = []
				if len(exclude) > len(include): return include
				else: return [('-' + value) for value in exclude]

			# Important to use "is" (equivalent to ===)
			if limitCount is self.FilterSettings: limitCount = OrionSettings.getFiltersInteger('filters.limit.count', addon)
			if limitRetry is self.FilterSettings: limitRetry = OrionSettings.getFiltersInteger('filters.limit.retry', addon)
			if limitOffset is self.FilterSettings: limitOffset = self.FilterNone
			if limitPage is self.FilterSettings: limitPage = self.FilterNone
			if sortValue is self.FilterSettings: sortValue = self.SortIds[OrionSettings.getFiltersInteger('filters.sort.value', addon)]
			if sortOrder is self.FilterSettings: sortOrder = self.OrderIds[OrionSettings.getFiltersInteger('filters.sort.order', addon)]
			if popularityPercent is self.FilterSettings: popularityPercent = OrionSettings.getFiltersInteger('filters.limit.popularity', addon)
			if popularityCount is self.FilterSettings: popularityCount = self.FilterNone
			if timeAdded is self.FilterSettings: timeAdded = self.FilterNone
			if timeAddedAge is self.FilterSettings: timeAddedAge = self.FilterNone
			if timeUpdated is self.FilterSettings: timeUpdated = self.FilterNone
			if timeUpdatedAge is self.FilterSettings: timeUpdatedAge = OrionSettings.getFiltersInteger('filters.limit.age', addon)
			if streamType is self.FilterSettings: streamType = OrionSettings.getFiltersInteger('filters.stream.type', addon)
			if streamSource is self.FilterSettings: streamSource = pick(addon, 'getFiltersStreamSource')
			if streamHoster is self.FilterSettings: streamHoster = pick(addon, 'getFiltersStreamHoster')
			if streamSeeds is self.FilterSettings: streamSeeds = OrionSettings.getFiltersInteger('filters.stream.seeds', addon)
			if streamAge is self.FilterSettings: streamAge = OrionSettings.getFiltersInteger('filters.stream.age', addon)
			if access is self.FilterSettings:
				access = []
				accessSettings = OrionSettings.getFiltersInteger('filters.stream.access', addon)
				if accessSettings == 1 or accessSettings == 3 or accessSettings == 5: access.append(self.AccessDirect)
				if accessSettings == 4 or accessSettings == 5: access.append(self.AccessIndirect)
				if (accessSettings == 1 or accessSettings == 2 or accessSettings == 4 or accessSettings == 5) and OrionSettings.getFiltersBoolean('filters.stream.access.premiumize', addon): access.append(self.AccessPremiumize)
				if (accessSettings == 1 or accessSettings == 2 or accessSettings == 4 or accessSettings == 5) and OrionSettings.getFiltersBoolean('filters.stream.access.offcloud', addon): access.append(self.AccessOffcloud)
				if (accessSettings == 1 or accessSettings == 2 or accessSettings == 4 or accessSettings == 5) and OrionSettings.getFiltersBoolean('filters.stream.access.realdebrid', addon): access.append(self.AccessRealdebrid)
			if filePack is self.FilterSettings: filePack = self.ChoiceIds[OrionSettings.getFiltersInteger('filters.stream.pack', addon)]
			if fileSize is self.FilterSettings: fileSize = [OrionSettings.getFiltersInteger('filters.stream.size.minimum', addon), OrionSettings.getFiltersInteger('filters.stream.size.maximum', addon)] if OrionSettings.getFiltersBoolean('filters.stream.size', addon) else self.FilterNone
			if fileUnknown is self.FilterSettings: fileUnknown = OrionSettings.getFiltersBoolean('filters.stream.unknown', addon)
			if metaRelease is self.FilterSettings: metaRelease = pick(addon, 'getFiltersMetaRelease')
			if metaUploader is self.FilterSettings: metaUploader = pick(addon, 'getFiltersMetaUploader')
			if metaEdition is self.FilterSettings: metaEdition = pick(addon, 'getFiltersMetaEdition')
			if videoQuality is self.FilterSettings:
				minimum = OrionSettings.getFiltersInteger('filters.video.quality.minimum', addon)
				maximum = OrionSettings.getFiltersInteger('filters.video.quality.maximum', addon)
				videoQuality = [self.QualityOrder[min(minimum, maximum)], self.QualityOrder[max(minimum, maximum)]] if OrionSettings.getFiltersBoolean('filters.video.quality', addon) else self.FilterNone
			if videoCodec is self.FilterSettings: videoCodec = pick(addon, 'getFiltersVideoCodec')
			if video3D is self.FilterSettings: video3D = self.ChoiceIds[OrionSettings.getFiltersInteger('filters.video.3d', addon)]
			if audioType is self.FilterSettings: audioType = pick(addon, 'getFiltersAudioType')
			if audioCodec is self.FilterSettings: audioCodec = pick(addon, 'getFiltersAudioCodec')
			if audioChannels is self.FilterSettings:
				minimum = OrionSettings.getFiltersInteger('filters.audio.channels.minimum', addon)
				maximum = OrionSettings.getFiltersInteger('filters.audio.channels.maximum', addon)				
				audioChannels = [self.ChannelsOrder[min(minimum, maximum)], self.ChannelsOrder[max(minimum, maximum)]] if OrionSettings.getFiltersBoolean('filters.audio.channels', addon) else self.FilterNone
			if audioLanguages is self.FilterSettings: audioLanguages = pick(addon, 'getFiltersAudioLanguages')

			if not limitCount is self.FilterNone:
				if limitCount <= 0: limitCount == self.FilterNone
				if limitCount > 5000: limitCount == 5000
			if not limitRetry is self.FilterNone:
				if limitRetry <= 0: limitRetry == self.FilterNone
				if limitRetry > 5000: limitRetry == 5000
			if sortValue is self.FilterNone:
				sortOrder = self.FilterNone
			elif sortValue <= 0:
				sortValue = self.FilterNone
				sortOrder = self.FilterNone
			if not popularityPercent is self.FilterNone:
				if popularityPercent <= 0: popularityPercent == self.FilterNone
				elif popularityPercent > 1: popularityPercent /= 100.0 # Important for the percentage retrieved from settings
			if not timeAdded is self.FilterNone and timeAdded <= 0:
				timeAdded = self.FilterNone
			if not timeAddedAge is self.FilterNone and timeAddedAge <= 0:
				timeAddedAge = self.FilterNone
			if not timeUpdated is self.FilterNone and timeUpdated <= 0:
				timeUpdated = self.FilterNone
			if not timeUpdatedAge is self.FilterNone and timeUpdatedAge <= 0:
				timeUpdatedAge = self.FilterNone
			if not streamSource is self.FilterNone:
				if OrionTools.isString(streamSource) and not streamSource == '': streamSource = [streamSource]
				if OrionTools.isList(streamSource):
					if len(streamSource) == 0: streamSource = self.FilterNone
				else: streamSource = self.FilterNone
			if not streamHoster is self.FilterNone:
				if OrionTools.isString(streamHoster) and not streamHoster == '': streamHoster = [streamHoster]
				if OrionTools.isList(streamHoster):
					if len(streamHoster) == 0: streamHoster = self.FilterNone
				else: streamHoster = self.FilterNone
			if not streamSeeds is self.FilterNone and (streamSeeds <= 0 or not(streamType == 1 or streamType == 2 or streamType == 4)):
				streamSeeds = self.FilterNone
			if not streamAge is self.FilterNone and (streamAge <= 0 or not(streamType == 1 or streamType == 3 or streamType == 5)):
				streamAge = self.FilterNone
			if not streamType is self.FilterNone: # Must be after subsettings.
				types = []
				if streamType == OrionStream.TypeTorrent or streamType == 1 or streamType == 2 or streamType == 4: types.append(OrionStream.TypeTorrent)
				if streamType == OrionStream.TypeUsenet or streamType == 1 or streamType == 3 or streamType == 5: types.append(OrionStream.TypeUsenet)
				if streamType == OrionStream.TypeHoster or streamType == 2 or streamType == 3 or streamType == 6: types.append(OrionStream.TypeHoster)
				if len(types) == 0: streamType = self.FilterNone
				else: streamType = types
			if not filePack is self.FilterNone:
				if filePack is self.ChoiceInclude: filePack = self.FilterNone
				elif filePack is self.ChoiceRequire: filePack = True
				elif filePack is self.ChoiceExclude: filePack = False
				else: filePack = self.FilterNone
			if not fileSize is self.FilterNone:
				# If given in MB.
				try:
					if OrionTools.isNumber(fileSize):
						if fileSize < 1048576: fileSize *= 1048576
					else:
						for i in range(len(fileSize)):
							if fileSize[i] < 1048576: fileSize[i] *= 1048576
				except: pass
				fileSize = OrionApi.range(fileSize)
			if not fileUnknown is self.FilterNone:
				fileUnknown = bool(fileUnknown)
			if not metaRelease is self.FilterNone:
				if OrionTools.isString(metaRelease) and not metaRelease == '': metaRelease = [metaRelease]
				if OrionTools.isList(metaRelease):
					if len(metaRelease) == 0: metaRelease = self.FilterNone
				else: metaRelease = self.FilterNone
			if not metaUploader is self.FilterNone:
				if OrionTools.isString(metaUploader) and not metaUploader == '': metaUploader = [metaUploader]
				if OrionTools.isList(metaUploader):
					if len(metaUploader) == 0: metaUploader = self.FilterNone
				else: metaUploader = self.FilterNone
			if not metaEdition is self.FilterNone:
				if OrionTools.isString(metaEdition):
					metaEdition = metaEdition.lower()
					if metaEdition in self.Editions: metaEdition = [metaEdition]
					else: metaEdition = self.FilterNone
				if OrionTools.isList(metaEdition):
					if len(metaEdition) == 0: metaEdition = self.FilterNone
				else: metaEdition = self.FilterNone
			if not videoQuality is self.FilterNone:
				videoQuality = OrionApi.range(videoQuality)
			if not videoCodec is self.FilterNone:
				if OrionTools.isString(videoCodec) and not videoCodec == '': videoCodec = [videoCodec]
				if OrionTools.isList(videoCodec):
					if len(videoCodec) == 0: videoCodec = self.FilterNone
				else: videoCodec = self.FilterNone
			if not video3D is self.FilterNone:
				if video3D is self.ChoiceInclude: video3D = self.FilterNone
				elif video3D is self.ChoiceRequire: video3D = True
				elif video3D is self.ChoiceExclude: video3D = False
				else: video3D = self.FilterNone
			if not audioType is self.FilterNone:
				if OrionTools.isString(audioType) and not audioType == '': audioType = [audioType]
				if OrionTools.isList(audioType):
					if len(audioType) == 0: audioType = self.FilterNone
				else: audioType = self.FilterNone
			if not audioCodec is self.FilterNone:
				if OrionTools.isString(audioCodec) and not audioCodec == '': audioCodec = [audioCodec]
				if OrionTools.isList(audioCodec):
					if len(audioCodec) == 0: audioCodec = self.FilterNone
				else: audioCodec = self.FilterNone
			if not audioChannels is self.FilterNone:
				audioChannels = OrionApi.range(audioChannels)
			if not audioLanguages is self.FilterNone:
				if OrionTools.isString(audioLanguages) and not audioLanguages == '': audioLanguages = [audioLanguages]
				if OrionTools.isList(audioLanguages):
					if len(audioLanguages) == 0: audioLanguages = self.FilterNone
				else: audioLanguages = self.FilterNone
			if not subtitleType is self.FilterNone:
				if OrionTools.isString(subtitleType) and not subtitleType == '': subtitleType = [subtitleType]
				if OrionTools.isList(subtitleType):
					if len(subtitleType) == 0: subtitleType = self.FilterNone
				else: subtitleType = self.FilterNone
			if not subtitleLanguages is self.FilterNone:
				if OrionTools.isString(subtitleLanguages) and not subtitleLanguages == '': subtitleLanguages = [subtitleLanguages]
				if OrionTools.isList(subtitleLanguages):
					if len(subtitleLanguages) == 0: subtitleLanguages = self.FilterNone
				else: subtitleLanguages = self.FilterNone

			filters = {}

			if not type == None: filters['type'] = type
			if not query == None: filters['query'] = query

			if not idOrion == None or not idImdb == None or not idTmdb == None or not idTvdb == None:
				filters['id'] = {}
				if not idOrion == None: filters['id']['orion'] = idOrion
				if not idImdb == None: filters['id']['imdb'] = idImdb
				if not idTmdb == None: filters['id']['tmdb'] = idTmdb
				if not idTvdb == None: filters['id']['tvdb'] = idTvdb

			if not numberSeason == None or not numberEpisode == None:
				filters['number'] = {}
				if not numberSeason == None: filters['number']['season'] = numberSeason
				if not numberEpisode == None: filters['number']['episode'] = numberEpisode

			if not limitCount == None or not limitRetry == None or not limitOffset == None or not limitPage == None:
				filters['limit'] = {}
				if not limitCount == None: filters['limit']['count'] = limitCount
				if not limitRetry == None: filters['limit']['retry'] = limitRetry
				if not limitOffset == None: filters['limit']['offset'] = limitOffset
				if not limitPage == None: filters['limit']['page'] = limitPage

			if not timeAdded == None or not timeUpdated == None:
				filters['time'] = {}
				if not timeAdded == None: filters['time']['added'] = timeAdded
				if not timeUpdated == None: filters['time']['updated'] = timeUpdated

			if not timeAddedAge == None or not timeUpdatedAge == None:
				filters['age'] = {}
				if not timeAddedAge == None: filters['age']['added'] = timeAddedAge
				if not timeUpdatedAge == None: filters['age']['updated'] = timeUpdatedAge

			if not sortValue == None or not sortOrder == None:
				filters['sort'] = {}
				if not sortValue == None: filters['sort']['value'] = sortValue
				if not sortOrder == None: filters['sort']['order'] = sortOrder

			if not popularityPercent == None or not popularityCount == None:
				filters['popularity'] = {}
				if not popularityPercent == None: filters['popularity']['percent'] = popularityPercent
				if not popularityCount == None: filters['popularity']['count'] = popularityCount

			if not streamType == None or not streamSource == None or not streamHoster == None or not streamSeeds == None or not streamAge == None:
				filters['stream'] = {}
				if not streamType == None: filters['stream']['type'] = streamType
				if not streamSource == None: filters['stream']['source'] = streamSource
				if not streamHoster == None: filters['stream']['hoster'] = streamHoster
				if not streamSeeds == None: filters['stream']['seeds'] = streamSeeds
				if not streamAge == None: filters['stream']['age'] = streamAge

			if not access == None:
				if OrionTools.isString(access): access = [access]
				filters['access'] = access

			if not fileSize == None or not fileUnknown == None or not filePack == None:
				filters['file'] = {}
				if not fileSize == None: filters['file']['size'] = fileSize
				if not fileUnknown == None: filters['file']['unknown'] = fileUnknown
				if not filePack == None: filters['file']['pack'] = filePack

			if not metaRelease == None or not metaUploader == None or not metaEdition == None:
				filters['meta'] = {}
				if not metaRelease == None: filters['meta']['release'] = metaRelease
				if not metaUploader == None: filters['meta']['uploader'] = metaUploader
				if not metaEdition == None: filters['meta']['edition'] = metaEdition

			if not videoQuality == None or not videoCodec == None or not video3D == None:
				filters['video'] = {}
				if not videoQuality == None: filters['video']['quality'] = videoQuality
				if not videoCodec == None: filters['video']['codec'] = videoCodec
				if not video3D == None: filters['video']['3d'] = video3D

			if not audioType == None or not audioChannels == None or not audioCodec == None or not audioLanguages == None:
				filters['audio'] = {}
				if not audioType == None: filters['audio']['type'] = audioType
				if not audioChannels == None: filters['audio']['channels'] = audioChannels
				if not audioCodec == None: filters['audio']['codec'] = audioCodec
				if not audioLanguages == None: filters['audio']['languages'] = audioLanguages

			if not subtitleType == None or not subtitleLanguages == None:
				filters['subtitle'] = {}
				if not subtitleType == None: filters['subtitle']['type'] = subtitleType
				if not subtitleLanguages == None: filters['subtitle']['languages'] = subtitleLanguages

			api = OrionApi()
			api.streamRetrieve(filters)
			if api.statusSuccess():
				item = OrionItem(data = api.data())
				item._accessSave()
				return item
			else: return None
		except:
			OrionTools.error()
			return None

	##############################################################################
	# DATA
	##############################################################################

	def data(self):
		return self.mData

	def dataSet(self, data):
		try:
			self.mData = data
			self.mStreams = []
			streams = self.mData['streams']
			for stream in streams:
				self.mStreams.append(OrionStream(data = stream))
			if len(self.mStreams) > 0:
				OrionSettings.setFilters(self.mStreams)
			return True
		except:
			OrionTools.error()
			return False

	##############################################################################
	# TYPE
	##############################################################################

	def type(self, default = None):
		try: return self.mData['type']
		except: return default

	##############################################################################
	# ID
	##############################################################################

	def idOrion(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['id']['orion']
		except: return default

	def idOrionMovie(self, default = None):
		return self.idOrion(select = self.SelectMovie, default = default)

	def idOrionShow(self, default = None):
		return self.idOrion(select = self.SelectShow, default = default)

	def idOrionEpisode(self, default = None):
		return self.idOrion(select = self.SelectEpisode, default = default)

	def idImdb(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['id']['imdb']
		except: return default

	def idTmdb(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['id']['tmdb']
		except: return default

	def idTvdb(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['id']['tvdb']
		except: return default

	##############################################################################
	# POPULARITY
	##############################################################################

	def popularityCount(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['popularity']['count']
		except: return default

	def popularityCountMovie(self, default = None):
		return self.popularityCount(select = self.SelectMovie, default = default)

	def popularityCountShow(self, default = None):
		return self.popularityCount(select = self.SelectShow, default = default)

	def popularityCountEpisode(self, default = None):
		return self.popularityCount(select = self.SelectEpisode, default = default)

	def popularityPercent(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['popularity']['percent']
		except: return default

	def popularityPercentMovie(self, default = None):
		return self.popularityPercent(select = self.SelectMovie, default = default)

	def popularityPercentShow(self, default = None):
		return self.popularityPercent(select = self.SelectShow, default = default)

	def popularityPercentEpisode(self, default = None):
		return self.popularityPercent(select = self.SelectEpisode, default = default)

	@classmethod
	def _popularityVote(self, idItem, idStream, vote = VoteUp):
		return OrionApi().streamVote(item = idItem, stream = idStream, vote = vote)

	@classmethod
	def popularityVote(self, idItem, idStream, vote = VoteUp, wait = False):
		thread = threading.Thread(target = self._popularityVote, args = (idItem, idStream, vote))
		thread.start()
		if wait: thread.join()

	##############################################################################
	# TIME
	##############################################################################

	def timeAdded(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['time']['added']
		except: return default

	def timeAddedMovie(self, default = None):
		return self.timeAdded(select = self.SelectMovie, default = default)

	def timeAddedShow(self, default = None):
		return self.timeAdded(select = self.SelectShow, default = default)

	def timeAddedEpisode(self, default = None):
		return self.timeAdded(select = self.SelectEpisode, default = default)

	def timeUpdated(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['time']['updated']
		except: return default

	def timeUpdatedMovie(self, default = None):
		return self.timeUpdated(select = self.SelectMovie, default = default)

	def timeUpdatedShow(self, default = None):
		return self.timeUpdated(select = self.SelectShow, default = default)

	def timeUpdatedEpisode(self, default = None):
		return self.timeUpdated(select = self.SelectEpisode, default = default)

	##############################################################################
	# META
	##############################################################################

	def metaTitle(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['title']
		except: return default

	def metaTitleMovie(self, default = None):
		return self.metaTitle(select = self.SelectMovie, default = default)

	def metaTitleShow(self, default = None):
		return self.metaTitle(select = self.SelectShow, default = default)

	def metaTitleEpisode(self, default = None):
		return self.metaTitle(select = self.SelectEpisode, default = default)

	def metaYear(self, select = SelectDefault, default = None):
		try: return self.mData[self._select(select)]['year']
		except: return default

	def metaYearMovie(self, default = None):
		return self.metaYear(select = self.SelectMovie, default = default)

	def metaYearShow(self, default = None):
		return self.metaYear(select = self.SelectShow, default = default)

	def metaYearEpisode(self, default = None):
		return self.metaYear(select = self.SelectEpisode, default = default)

	##############################################################################
	# NUMBER
	##############################################################################

	def number(self, select = SelectDefault, default = None):
		try: return self.mData[self.SelectEpisode]['number'][self.SelectEpisode if select == self.SelectEpisode else self.SelectSeason]
		except: return default

	def numberSeason(self, default = None):
		return self.number(select = self.SelectSeason, default = default)

	def numberEpisode(self, default = None):
		return self.number(select = self.SelectEpisode, default = default)

	##############################################################################
	# COUNT
	##############################################################################

	def count(self, default = None):
		return self.countFiltered(default = default)

	def countTotal(self, default = None):
		try: return self.mData['count']['total']
		except: return default

	def countFiltered(self, default = None):
		try: return self.mData['count']['filtered']
		except: return default

	##############################################################################
	# REQUESTS
	##############################################################################

	def requestsTotalCount(self, default = None):
		try: return self.mData['requests']['total']['count']
		except: return default

	def requestsTotalLinks(self, default = None):
		try: return self.mData['requests']['total']['links']
		except: return default

	def requestsDailyLimit(self, default = None):
		try: return self.mData['requests']['daily']['limit']
		except: return default

	def requestsDailyUsed(self, default = None):
		try: return self.mData['requests']['daily']['used']
		except: return default

	def requestsDailyRemaining(self, default = None):
		try: return self.mData['requests']['daily']['remaining']
		except: return default

	##############################################################################
	# STREAMS
	##############################################################################

	def streams(self):
		return self.mStreams
