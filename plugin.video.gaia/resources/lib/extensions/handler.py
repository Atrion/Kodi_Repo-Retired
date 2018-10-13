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

from resources.lib.extensions import tools
from resources.lib.extensions import network
from resources.lib.extensions import debrid
from resources.lib.extensions import interface
from resources.lib.modules import client
from resources.lib.modules import cache
from resources.lib.modules import debrid as debridold

# NB: Only initialize the services once, otherwise it takes about 150ms each time Handler._initialize is called, because the objects have to be created and the settings be read from file.
# NB: Do not declare these variables as class variables in Handler, because if no object of Handler exists, it will delete the class variables.
# NB: This is important for sources -> __init__.py -> addItem.
HandlerServicesDirect = None
HandlerServicesTorrent = None
HandlerServicesUsenet = None
HandlerServicesHoster = None

HandlerDefaultDirect = None
HandlerDefaultTorrent = None
HandlerDefaultUsenet = None
HandlerDefaultHoster = None

Handles = None
HandlesCache = None
HandlesHoster = None

class Handler(object):

	ModeNone = None
	ModeSelection = 'selection'
	ModeDefault = 'default'

	ReturnUnavailable = 'unavailable'
	ReturnExternal = 'external'
	ReturnCancel = 'cancel'

	TypeDirect = 'direct'
	TypeTorrent = 'torrent'
	TypeUsenet = 'usenet'
	TypeHoster = 'hoster'

	def __init__(self, type = None):
		self.mServices = []
		self.mType = None
		self.mDefault = None
		self._initialize(type)

	@classmethod
	def handles(self):
		global Handles
		if Handles == None:
			Handles = [
				{
					'id' : HandlePremiumize.Id,
					'name' : HandlePremiumize.Name,
					'abbreviation' : HandlePremiumize.Abbreviation,
				},
				{
					'id' : HandleOffCloud.Id,
					'name' : HandleOffCloud.Name,
					'abbreviation' : HandleOffCloud.Abbreviation,
				},
				{
					'id' : HandleRealDebrid.Id,
					'name' : HandleRealDebrid.Name,
					'abbreviation' : HandleRealDebrid.Abbreviation,
				},
				{
					'id' : HandleAllDebrid.Id,
					'name' : HandleAllDebrid.Name,
					'abbreviation' : HandleAllDebrid.Abbreviation,
				},
				{
					'id' : HandleRapidPremium.Id,
					'name' : HandleRapidPremium.Name,
					'abbreviation' : HandleRapidPremium.Abbreviation,
				},
			]
		return Handles

	@classmethod
	def handlesSingleCache(self):
		global HandlesCache
		if HandlesCache == None:
			HandlesCache = 0
			services = [debrid.Premiumize(), debrid.OffCloud(), debrid.RealDebrid()]
			for service in services:
				if service.accountValid():
					HandlesCache += 1
		return HandlesCache <= 1

	@classmethod
	def handlesSingleHoster(self):
		global HandlesHoster
		if HandlesHoster == None:
			HandlesHoster = 0
			services = [debrid.Premiumize(), debrid.OffCloud(), debrid.RealDebrid(), debrid.AllDebrid(), debrid.RapidPremium()]
			for service in services:
				if service.accountValid():
					HandlesHoster += 1
		return HandlesHoster <= 1

	def _initialize(self, type):
		if type == None:
			return

		try:
			direct = 'direct' in type and type['direct']
			type = type['source'].lower()
		except:
			type = type.lower()
			direct = type == self.TypeDirect

		if not type == self.TypeTorrent and not type == self.TypeUsenet:
			if direct: type = self.TypeDirect
			else: type = self.TypeHoster
		if type == self.mType:
			return

		self.mType = type
		self.mServices = []
		self.mDefault = None

		global HandlerServicesDirect
		global HandlerServicesTorrent
		global HandlerServicesUsenet
		global HandlerServicesHoster

		global HandlerDefaultDirect
		global HandlerDefaultTorrent
		global HandlerDefaultUsenet
		global HandlerDefaultHoster

		if type == self.TypeDirect:
			if HandlerServicesDirect == None:
				HandlerServicesDirect = []
				if tools.Settings.getBoolean('streaming.direct.enabled'):
					handle = HandleDirect()
					HandlerServicesDirect.append(handle)
					HandlerDefaultDirect = handle
					self.mServices = HandlerServicesDirect
					self.mDefault = HandlerDefaultDirect
			else:
				self.mServices = HandlerServicesDirect
				self.mDefault = HandlerDefaultDirect
		elif type == self.TypeTorrent:
			if HandlerServicesTorrent == None:
				HandlerServicesTorrent = []
				if tools.Settings.getBoolean('streaming.torrent.enabled'):
					premiumize = debrid.Premiumize()
					offcloud = debrid.OffCloud()
					realdebrid = debrid.RealDebrid()
					default = tools.Settings.getInteger('streaming.torrent.default')
					if premiumize.accountValid() and premiumize.streamingTorrent():
						handle = HandlePremiumize()
						HandlerServicesTorrent.append(handle)
						if default == 1: HandlerDefaultTorrent = handle
					if offcloud.accountValid() and offcloud.streamingTorrent():
						handle = HandleOffCloud()
						HandlerServicesTorrent.append(handle)
						if default == 2: HandlerDefaultTorrent = handle
					if realdebrid.accountValid() and realdebrid.streamingTorrent():
						handle = HandleRealDebrid()
						HandlerServicesTorrent.append(handle)
						if default == 3: HandlerDefaultTorrent = handle
					if tools.Settings.getBoolean('streaming.torrent.elementum.enabled') and tools.Settings.getBoolean('streaming.torrent.elementum.connected'):
						handle = HandleElementum()
						HandlerServicesTorrent.append(handle)
						if default == 4: HandlerDefaultTorrent = handle
					if tools.Settings.getBoolean('streaming.torrent.quasar.enabled') and tools.Settings.getBoolean('streaming.torrent.quasar.connected'):
						handle = HandleQuasar()
						HandlerServicesTorrent.append(handle)
						if default == 5: HandlerDefaultTorrent = handle
					self.mServices = HandlerServicesTorrent
					self.mDefault = HandlerDefaultTorrent
			else:
				self.mServices = HandlerServicesTorrent
				self.mDefault = HandlerDefaultTorrent
		elif type == self.TypeUsenet:
			if HandlerServicesUsenet == None:
				HandlerServicesUsenet = []
				if tools.Settings.getBoolean('streaming.usenet.enabled'):
					premiumize = debrid.Premiumize()
					offcloud = debrid.OffCloud()
					default = tools.Settings.getInteger('streaming.usenet.default')
					if premiumize.accountValid() and premiumize.streamingUsenet():
						handle = HandlePremiumize()
						HandlerServicesUsenet.append(handle)
						if default == 1: HandlerDefaultUsenet = handle
					if offcloud.accountValid() and offcloud.streamingUsenet():
						handle = HandleOffCloud()
						HandlerServicesUsenet.append(handle)
						if default == 2: HandlerDefaultUsenet = handle
					self.mServices = HandlerServicesUsenet
					self.mDefault = HandlerDefaultUsenet
			else:
				self.mServices = HandlerServicesUsenet
				self.mDefault = HandlerDefaultUsenet
		elif type == self.TypeHoster:
			if HandlerServicesHoster == None:
				HandlerServicesHoster = []
				if tools.Settings.getBoolean('streaming.hoster.enabled'):
					premiumize = debrid.Premiumize()
					offcloud = debrid.OffCloud()
					realdebrid = debrid.RealDebrid()
					alldebrid = debrid.AllDebrid()
					rapidpremium = debrid.RapidPremium()
					default = tools.Settings.getInteger('streaming.hoster.default')
					if premiumize.accountValid() and premiumize.streamingHoster():
						handle = HandlePremiumize()
						HandlerServicesHoster.append(handle)
						if default == 1: HandlerDefaultHoster = handle
					if offcloud.accountValid() and offcloud.streamingHoster():
						handle = HandleOffCloud()
						HandlerServicesHoster.append(handle)
						if default == 2: HandlerDefaultHoster = handle
					if realdebrid.accountValid() and realdebrid.streamingHoster():
						handle = HandleRealDebrid()
						HandlerServicesHoster.append(handle)
						if default == 3: HandlerDefaultHoster = handle
					if alldebrid.accountValid() and alldebrid.streamingHoster():
						handle = HandleAllDebrid()
						HandlerServicesHoster.append(handle)
						if default == 4: HandlerDefaultHoster = handle
					if rapidpremium.accountValid() and rapidpremium.streamingHoster():
						handle = HandleRapidPremium()
						HandlerServicesHoster.append(handle)
						if default == 5: HandlerDefaultHoster = handle
					if tools.Settings.getBoolean('streaming.hoster.resolveurl.enabled'):
						handle = HandleResolveUrl()
						HandlerServicesHoster.append(handle)
						if default == 6: HandlerDefaultHoster = handle
					if tools.Settings.getBoolean('streaming.hoster.urlresolver.enabled'):
						handle = HandleUrlResolver()
						HandlerServicesHoster.append(handle)
						if default == 7: HandlerDefaultHoster = handle
					self.mServices = HandlerServicesHoster
					self.mDefault = HandlerDefaultHoster
			else:
				self.mServices = HandlerServicesHoster
				self.mDefault = HandlerDefaultHoster

	def serviceHas(self):
		return self.serviceCount() > 0

	def serviceCount(self):
		return len(self.mServices)

	def service(self, name = None):
		if self.serviceHas():
			if name == None:
				return self.mServices[0]
			else:
				name = name.lower()
				for service in self.mServices:
					if service.id() == name:
						return service
		return None

	def supported(self, item = None):
		if item == None:
			return len(self.mServices) > 0
		else:
			self._initialize(item)
			for service in self.mServices:
				if service.supported(item):
					return True
			return False

	def supportedCount(self, item = None):
		if item == None:
			return len(self.mServices)
		else:
			count = 0
			self._initialize(item)
			for service in self.mServices:
				try:
					if service.supported(item):
						count += 1
				except: pass
			return count

	def serviceBest(self, item, cached = True):
		try:
			self._initialize(item)
			services = [i.id() for i in self.mServices if i.supported(item)]

			if not 'cache' in item or not any([i for i in item['cache'].iteritems()]): cached = False
			if cached: cache = item['cache']

			selections = [HandleDirect().id(), HandlePremiumize().id(), HandleOffCloud().id(), HandleRealDebrid().id(), HandleAllDebrid().id(), HandleRapidPremium().id(), HandleElementum().id(), HandleQuasar().id(), HandleResolveUrl().id(), HandleUrlResolver().id()]
			for selection in selections:
				# Try to find a cached link first.
				if selection in services and ((not cached) or (cached and selection in cache and cache[selection])):
					return selection

			# If no service was found that has the link cached, search again for the the best sevice but do not check if it is cached this time.
			if cached: return self.serviceBest(item = item, cached = False)

			return None
		except:
			tools.Logger.error()

	def serviceDetermine(self, mode, item, popups = False):
		try:
			self._initialize(item)

			service = None
			services = [i for i in self.mServices if i.supported(item)]

			if len(services) == 1:
				service = services[0].name()
			else:
				if popups:
					if mode == self.ModeNone or mode == self.ModeDefault:
						if self.mDefault == self.ModeNone or self.mDefault == self.ModeSelection:
							service = self.options(item = item, popups = popups)
						else:
							try: service = self.mDefault.name()
							except: service = self.options(item = item, popups = popups)
					else:
						service = self.options(item = item, popups = popups)
				elif mode == self.ModeDefault: # Autoplay
					try:
						service = self.mDefault.name()
					except:
						service = self.serviceBest(item = item)

			if service == None:
				service = self.options(item = item, popups = popups)
			if service == None:
				return self.ReturnUnavailable
			elif service == self.ReturnCancel:
				return service
			else:
				if self.service(name = service).supported(item):
					return service
				else:
					return self.serviceBest(item = item)
		except:
			tools.Logger.error()

	@classmethod
	def serviceExternal(self, service):
		if not isinstance(service, basestring):
			try:
				service = service.name()
			except:
				tools.Logger.error()
				return False
		return service == HandleElementum().name().lower() or service == HandleQuasar().name().lower()

	def options(self, item, popups = False):
		if popups:
			self._initialize(item)

			if self.mType == self.TypeTorrent: title = 33473
			elif self.mType == self.TypeUsenet: title = 33482
			else: title = 33488

			services = [i for i in self.mServices if i.supported(item)]
			servicesCount = len(services)

			if servicesCount == 1:
				return services[0].name()
			elif servicesCount > 1:
				items = [interface.Format.fontBold(i.name()) for i in services]
				index = interface.Dialog.options(title = title, items = items)
				if index < 0:
					return self.ReturnCancel
				else:
					return services[index].name()
		return self.ReturnUnavailable

	def handle(self, link, item, name = None, download = False, popups = False, close = True):
		self._initialize(item)

		if popups and name == None:
			name = self.options(item = item, popups = popups)
			if name == self.ReturnUnavailable or name == self.ReturnCancel:
				return name

		service = self.service(name = name)

		if popups and service == None:
			if self.mType == self.TypeTorrent:
				title = 33473
				message = 33483
			elif self.mType == self.TypeUsenet:
				title = 33482
				message = 33484
			elif self.mType == self.TypeHoster:
				title = 33488
				message = 33485
			if interface.Dialog.option(title = title, message = message, labelConfirm = 33011, labelDeny = 33486):
				tools.Settings.launch(category = tools.Settings.CategoryStreaming)
			return self.ReturnUnavailable

		result = service.handle(link = link, item = item, download = download, popups = popups, close = close)
		result['handle'] = service.id()
		if not result['success']:
			if not result['error'] in [self.ReturnUnavailable, self.ReturnExternal, self.ReturnCancel]:
				if not 'notification' in result or not result['notification']:
					interface.Dialog.notification(title = 33448, message = 35295, icon = interface.Dialog.IconError)
				result['error'] = self.ReturnUnavailable
		return result

class Handle(object):

	def __init__(self, name, id = None, abbreviation = None):
		self.mId = name.lower() if id == None else id
		self.mName = name
		self.mAbbreviation = abbreviation

	def id(self):
		return self.mId

	def name(self):
		return self.mName

	def abbreviation(self):
		return self.mAbbreviation

	def supported(self, item):
		try:
			services = self.services()
			if services == None:
				return False
			else:
				try: source = item['source'].strip().lower()
				except: source = item
				for service in services:
					service = service.lower()
					if source in service or service in source:
						return True
				return source == self.id()
		except:
			tools.Logger.error()
			return False

	def handle(self, link, item, download = False, popups = False, close = True):
		pass

	def services(self):
		pass

class HandleDirect(Handle):

	def __init__(self):
		Handle.__init__(self, interface.Translation.string(33489))

	def handle(self, link, item, download = False, popups = False, close = True):
		if item['provider'].lower() == 'realdebrid':
			return HandleRealDebrid().handle(link = link, item = item, download = download, popups = popups, close = close)
		else:
			return debrid.Debrid.addResult(link = link)

	def supported(self, item):
		if isinstance(item, dict) and 'direct' in item and item['direct'] == True:
			return True
		else:
			return False

	def services(self):
		return None

class HandleResolveUrl(Handle):

	def __init__(self):
		Handle.__init__(self, interface.Translation.string(35310))
		self.mServices = None

	def handle(self, link, item, download = False, popups = False, close = True):
		try:
			if item and 'direct' in item and item['direct'] == True:
				return link
			else:
				try: import resolveurl # Do not import at the start of the script, otherwise ResolveUrl will be loaded everytime handler.py is imported, drastically slowing down menus.
				except: pass
				media = resolveurl.HostedMediaFile(url = link, include_disabled = True, include_universal = False)
				if media.valid_url() == True:
					return debrid.Debrid.addResult(link = media.resolve(allow_popups = popups))
				else:
					return debrid.Debrid.addResult(link = None)
		except:
			return debrid.Debrid.addResult(link = None)

	def supported(self, item):
		if isinstance(item, dict) and 'direct' in item and item['direct'] == True:
			return True
		else:
			return Handle.supported(self, item)

	def services(self):
		if self.mServices == None:
			try: import resolveurl # Do not import at the start of the script, otherwise ResolveUrl will be loaded everytime handler.py is imported, drastically slowing down menus.
			except: pass
			try:
				result = resolveurl.relevant_resolvers(order_matters = True)
				result = [i.domains for i in result if not '*' in i.domains]
				result = [i.lower() for i in reduce(lambda x, y: x+y, result)]
				result = [x for y,x in enumerate(result) if x not in result[:y]]
				self.mServices = result
			except:
				return []
		return self.mServices

class HandleUrlResolver(Handle):

	def __init__(self):
		Handle.__init__(self, interface.Translation.string(33747))
		self.mServices = None

	def handle(self, link, item, download = False, popups = False, close = True):
		try:
			if item and 'direct' in item and item['direct'] == True:
				return link
			else:
				try: import urlresolver # Do not import at the start of the script, otherwise UrlResolver will be loaded everytime handler.py is imported, drastically slowing down menus.
				except: pass
				media = urlresolver.HostedMediaFile(url = link, include_disabled = True, include_universal = False)
				if media.valid_url() == True:
					return debrid.Debrid.addResult(link = media.resolve(allow_popups = popups))
				else:
					return debrid.Debrid.addResult(link = None)
		except:
			return debrid.Debrid.addResult(link = None)

	def supported(self, item):
		if isinstance(item, dict) and 'direct' in item and item['direct'] == True:
			return True
		else:
			return Handle.supported(self, item)

	def services(self):
		if self.mServices == None:
			try: import urlresolver # Do not import at the start of the script, otherwise UrlResolver will be loaded everytime handler.py is imported, drastically slowing down menus.
			except: pass
			try:
				result = urlresolver.relevant_resolvers(order_matters = True)
				result = [i.domains for i in result if not '*' in i.domains]
				result = [i.lower() for i in reduce(lambda x, y: x+y, result)]
				result = [x for y,x in enumerate(result) if x not in result[:y]]
				self.mServices = result
			except:
				return []
		return self.mServices

class HandlePremiumize(Handle):

	# Accessed from metadata.
	Id = 'premiumize'
	Name = 'Premiumize'
	Abbreviation = 'P'

	def __init__(self):
		Handle.__init__(self, id = self.Id, name = self.Name, abbreviation = self.Abbreviation)
		self.mService = debrid.Premiumize()
		self.mServices = None

	def handle(self, link, item, download = False, popups = False, close = True):
		try: title = item['metadata'].title(extended = True, prefix = True, pack = True)
		except: title = item['title']
		try: pack = item['metadata'].pack()
		except: pack = False
		try:
			season = item['information']['season']
			episode = item['information']['episode']
		except:
			season = None
			episode = None
		return debridold.resolver(link, debrid = self.id(), title = title, season = season, episode = episode, pack = pack, close = close, source = item['source'])

	def services(self):
		try:
			if self.mServices == None and self.mService.accountValid():
				self.mServices = self.mService.servicesList(onlyEnabled = True)
		except: pass
		return self.mServices

	def supported(self, item):
		if isinstance(item, dict) and 'source' in item:
			if item['source'] == 'torrent':
				return True
			if item['source'] == 'usenet':
				return True
		return Handle.supported(self, item)

class HandleOffCloud(Handle):

	# Accessed from metadata.
	Id = 'offcloud'
	Name = 'OffCloud'
	Abbreviation = 'O'

	def __init__(self):
		Handle.__init__(self, id = self.Id, name = self.Name, abbreviation = self.Abbreviation)
		self.mService = debrid.OffCloud()
		self.mServices = None

	def handle(self, link, item, download = False, popups = False, close = True):
		try: title = item['metadata'].title(extended = True, prefix = True, pack = True)
		except: title = item['title']
		try: pack = item['metadata'].pack()
		except: pack = False
		try:
			season = item['information']['season']
			episode = item['information']['episode']
		except:
			season = None
			episode = None
		return debridold.resolver(link, debrid = self.id(), title = title, season = season, episode = episode, pack = pack, close = close, source = item['source'])

	def services(self):
		try:
			if self.mServices == None and self.mService.accountValid():
				self.mServices = self.mService.servicesList(onlyEnabled = True)
		except: pass
		return self.mServices

	def supported(self, item):
		if isinstance(item, dict) and 'source' in item:
			if item['source'] == 'torrent':
				return True
			if item['source'] == 'usenet':
				return True
		return Handle.supported(self, item)

class HandleRealDebrid(Handle):

	# Accessed from metadata.
	Id = 'realdebrid'
	Name = 'RealDebrid'
	Abbreviation = 'R'

	def __init__(self):
		Handle.__init__(self, id = self.Id, name = self.Name, abbreviation = self.Abbreviation)
		self.mService = debrid.RealDebrid()
		self.mServices = None

	def handle(self, link, item, download = False, popups = False, close = True):
		try: title = item['metadata'].title(extended = True, prefix = True, pack = True)
		except: title = item['title']
		try: pack = item['metadata'].pack()
		except: pack = False
		try:
			season = item['information']['season']
			episode = item['information']['episode']
		except:
			season = None
			episode = None
		return debridold.resolver(link, debrid = self.id(), title = title, season = season, episode = episode, pack = pack, close = close, source = item['source'])

	def services(self):
		try:
			if self.mServices == None and self.mService.accountValid():
				self.mServices = self.mService.servicesList(onlyEnabled = True)
		except: pass
		return self.mServices

	def supported(self, item):
		if isinstance(item, dict) and 'source' in item:
			if item['source'] == 'torrent':
				return True
		return Handle.supported(self, item)

class HandleAllDebrid(Handle):

	# Accessed from metadata.
	Id = 'alldebrid'
	Name = 'AllDebrid'
	Abbreviation = 'A'

	def __init__(self):
		Handle.__init__(self, id = self.Id, name = self.Name, abbreviation = self.Abbreviation)
		self.mService = debrid.AllDebrid()
		self.mServices = None

	def handle(self, link, item, download = False, popups = False, close = True):
		try: title = item['metadata'].title(extended = True, prefix = True, pack = True)
		except: title = item['title']
		try: pack = item['metadata'].pack()
		except: pack = False
		try:
			season = item['information']['season']
			episode = item['information']['episode']
		except:
			season = None
			episode = None
		return debridold.resolver(link, debrid = self.id(), title = title, season = season, episode = episode, pack = pack, close = close, source = item['source'])

	def services(self):
		try:
			if self.mServices == None and self.mService.accountValid():
				self.mServices = self.mService.servicesList(onlyEnabled = True)
		except: pass
		return self.mServices

class HandleRapidPremium(Handle):

	# Accessed from metadata.
	Id = 'rapidpremium'
	Name = 'RapidPremium'
	Abbreviation = 'M'

	def __init__(self):
		Handle.__init__(self, id = self.Id, name = self.Name, abbreviation = self.Abbreviation)
		self.mService = debrid.RapidPremium()
		self.mServices = None

	def handle(self, link, item, download = False, popups = False, close = True):
		try: title = item['metadata'].title(extended = True, prefix = True, pack = True)
		except: title = item['title']
		try: pack = item['metadata'].pack()
		except: pack = False
		try:
			season = item['information']['season']
			episode = item['information']['episode']
		except:
			season = None
			episode = None
		return debridold.resolver(link, debrid = self.id(), title = title, season = season, episode = episode, pack = pack, close = close, source = item['source'])

	def services(self):
		try:
			if self.mServices == None and self.mService.accountValid():
				self.mServices = self.mService.servicesList(onlyEnabled = True)
		except: pass
		return self.mServices

class HandleElementum(Handle):

	def __init__(self):
		Handle.__init__(self, 'Elementum')
		self.mServices = None

	def handle(self, link, item, download = False, popups = False, close = True):
		try:
			parameters = {}

			# Link
			parameters['uri'] = network.Networker.quote(link)

			# Type
			type = None
			if 'type' in item and not 'type' == None:
				if item['type'] == tools.Media.TypeShow:
					type = 'episode'
				else:
					type = 'movie'
			elif 'tvshowtitle' in item:
				type = 'episode'
			else:
				type = 'movie'
			parameters['type'] = type

			# Information
			information = item['information'] if 'information' in item else None

			# Show
			if type == 'episode':
				if 'season' in information:
					parameters['season'] = information['season']
				if 'episode' in information:
					parameters['episode'] = information['episode']

			# TMDB
			try:
				tmdbApi = tools.Settings.getString('accounts.informants.tmdb.api') if tools.Settings.getBoolean('accounts.informants.tmdb.enabled') else ''
				if tmdbApi == '': tmdbApi = tools.System.obfuscate(tools.Settings.getString('internal.tmdb.api', raw = True))
				if not tmdbApi == '':
					if 'tvdb' in information and not information['tvdb'] == None: # Shows - IMDB ID for episodes does not work on tmdb
						result = cache.get(client.request, 240, 'http://api.themoviedb.org/3/find/%s?api_key=%s&external_source=tvdb_id' % (information['tvdb'], tmdbApi))
						result = result['tv_episode_results']
						parameters['tmdb'] = str(result['id'])
						parameters['show'] = str(result['show_id'])
					elif 'imdb' in information and not information['imdb'] == None:
						result = cache.get(client.request, 240, 'http://api.themoviedb.org/3/find/%s?api_key=%s&external_source=imdb_id' % (information['imdb'], tmdbApi))
						if isinstance(result, basestring): result = tools.Converter.jsonFrom(result)
						result = result['movie_results']
						if isinstance(result, list): result = result[0]
						parameters['tmdb'] = str(result['id'])
			except:
				tools.Logger.error()

			# This will add the torrent to Elementum, but after Elementum's buffer phase, playback is not started and nothing happens.
			# This is because of the source-selection dialog that causes Kodi's addon handle to be -1 (aka no handle). This will cause the Kodi player to not launch.
			# Use the RPC instead.
			# action = 'torrents/add' if download else 'play'
			#parameters = network.Networker.linkParameters(parameters)
			#tools.System.execute('RunPlugin(plugin://plugin.video.elementum/%s?%s)' % (action, parameters))

			interface.Dialog.notification(title = 35316, message = 35319, icon = interface.Dialog.IconSuccess, time = 10000)
			interface.Core.close()
			interface.Loader.show()

			if download: network.Networker(tools.Elementum.linkAdd(parameters)).request()
			else: network.Networker(tools.Elementum.linkPlay(parameters)).request()

			tools.Time.sleep(1)
			while True:
				if interface.Dialog.dialogProgressVisible(): break
				tools.Time.sleep(0.5)

			interface.Loader.hide()

			while True:
				if not interface.Dialog.dialogProgressVisible(): break
				tools.Time.sleep(0.5)

			# Elementum does not start playback after initial buffering.
			# If requesting the link again after buffering is done, Elementum does start playback.
			if not download:
				if not interface.Player().isPlaying(): interface.Loader.show()
				tools.Time.sleep(3)
				if not interface.Player().isPlaying(): network.Networker(tools.Elementum.linkPlay({'resume' : parameters['uri']})).request()
				interface.Loader.hide()

			return debrid.Debrid.addResult(error = Handler.ReturnExternal) # Return because Elementum will handle the playback.
		except:
			tools.Logger.error()

	def services(self):
		if self.mServices == None:
			self.mServices = []
			if tools.Settings.getBoolean('streaming.torrent.elementum.enabled'):
				self.mServices.append('torrent')
		return self.mServices

class HandleQuasar(Handle):

	def __init__(self):
		Handle.__init__(self, 'Quasar')
		self.mServices = None

	def handle(self, link, item, download = False, popups = False, close = True):
		try:
			parameters = {}

			# Link
			parameters['uri'] = network.Networker.quote(link)

			# Type
			type = None
			if 'type' in item and not 'type' == None:
				if item['type'] == tools.Media.TypeShow:
					type = 'episode'
				else:
					type = 'movie'
			elif 'tvshowtitle' in item:
				type = 'episode'
			else:
				type = 'movie'
			parameters['type'] = type

			# Information
			information = item['information'] if 'information' in item else None

			# Show
			if type == 'episode':
				if 'season' in information:
					parameters['season'] = information['season']
				if 'episode' in information:
					parameters['episode'] = information['episode']

			# TMDB
			try:
				tmdbApi = tools.Settings.getString('accounts.informants.tmdb.api') if tools.Settings.getBoolean('accounts.informants.tmdb.enabled') else ''
				if tmdbApi == '': tmdbApi = tools.System.obfuscate(tools.Settings.getString('internal.tmdb.api', raw = True))
				if not tmdbApi == '':
					if 'tvdb' in information and not information['tvdb'] == None: # Shows - IMDB ID for episodes does not work on tmdb
						result = cache.get(client.request, 240, 'http://api.themoviedb.org/3/find/%s?api_key=%s&external_source=tvdb_id' % (information['tvdb'], tmdbApi))
						result = result['tv_episode_results']
						parameters['tmdb'] = str(result['id'])
						parameters['show'] = str(result['show_id'])
					elif 'imdb' in information and not information['imdb'] == None:
						result = cache.get(client.request, 240, 'http://api.themoviedb.org/3/find/%s?api_key=%s&external_source=imdb_id' % (information['imdb'], tmdbApi))
						if isinstance(result, basestring): result = tools.Converter.jsonFrom(result)
						result = result['movie_results']
						if isinstance(result, list): result = result[0]
						parameters['tmdb'] = str(result['id'])
			except:
				tools.Logger.error()

			# This will add the torrent to Quasar, but after Quasar's buffer phase, playback is not started and nothing happens.
			# This is because of the source-selection dialog that causes Kodi's addon handle to be -1 (aka no handle). This will cause the Kodi player to not launch.
			# Use the RPC instead.
			# action = 'torrents/add' if download else 'play'
			#parameters = network.Networker.linkParameters(parameters)
			#tools.System.execute('RunPlugin(plugin://plugin.video.quasar/%s?%s)' % (action, parameters))

			interface.Dialog.notification(title = 33570, message = 35320, icon = interface.Dialog.IconSuccess, time = 10000)
			interface.Core.close()
			interface.Loader.show()

			if download: network.Networker(tools.Quasar.linkAdd(parameters)).request()
			else: network.Networker(tools.Quasar.linkPlay(parameters)).request()

			tools.Time.sleep(1)
			while True:
				if interface.Dialog.dialogProgressVisible(): break
				tools.Time.sleep(0.5)

			interface.Loader.hide()

			while True:
				if not interface.Dialog.dialogProgressVisible(): break
				tools.Time.sleep(0.5)

			# Quasar does not start playback after initial buffering.
			# If requesting the link again after buffering is done, Quasar does start playback.
			if not download:
				if not interface.Player().isPlaying(): interface.Loader.show()
				tools.Time.sleep(3)
				if not interface.Player().isPlaying(): network.Networker(tools.Quasar.linkPlay({'resume' : parameters['uri']})).request()
				interface.Loader.hide()

			return debrid.Debrid.addResult(error = Handler.ReturnExternal) # Return because Quasar will handle the playback.
		except:
			tools.Logger.error()

	def services(self):
		if self.mServices == None:
			self.mServices = []
			if tools.Settings.getBoolean('streaming.torrent.quasar.enabled'):
				self.mServices.append('torrent')
		return self.mServices
