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
# ORIONAPI
##############################################################################
# API connection and queries to the Orion server
##############################################################################

import copy
from orion.modules.oriontools import *
from orion.modules.orionsettings import *
from orion.modules.orioninterface import *
from orion.modules.orionnetworker import *

class OrionApi:

	##############################################################################
	# CONSTANTS
	##############################################################################

	# Used by OrionSettings.
	# Determines which API results to not show a notification for.
	Nonessential = ['exception', 'success', 'streammissing']

	IgnoreExcludes = ['alluc', 'alluc.ee', 'prontv', 'pron.tv', 'llucy', 'llucy.net']

	ParameterMode = 'mode'
	ParameterAction = 'action'
	ParameterKeyApp = 'keyapp'
	ParameterKeyUser = 'keyuser'
	ParameterKey = 'key'
	ParameterId = 'id'
	ParameterEmail = 'email'
	ParameterPassword = 'password'
	ParameterLink = 'link'
	ParameterResult = 'result'
	ParameterQuery = 'query'
	ParameterStatus = 'status'
	ParameterType = 'type'
	ParameterItem = 'item'
	ParameterStream = 'stream'
	ParameterType = 'type'
	ParameterDescription = 'description'
	ParameterMessage = 'message'
	ParameterData = 'data'
	ParameterCount = 'count'
	ParameterFiltered = 'filtered'
	ParameterTotal = 'total'
	ParameterTime = 'time'
	ParameterDirection = 'direction'
	ParameterAll = 'all'

	StatusUnknown = 'unknown'
	StatusBusy = 'busy'
	StatusSuccess = 'success'
	StatusError = 'error'

	ModeStream = 'stream'
	ModeApp = 'app'
	ModeUser = 'user'
	ModeNotification = 'notification'
	ModeServer = 'server'
	ModeFlare = 'flare'

	ActionUpdate = 'update'
	ActionRetrieve = 'retrieve'
	ActionAnonymous = 'anonymous'
	ActionLogin = 'login'
	ActionVote = 'vote'
	ActionTest = 'test'

	TypeMovie = 'movie'
	TypeShow = 'show'

	StreamTorrent = 'torrent'
	StreamUsenet = 'usenet'
	StreamHoster = 'hoster'

	AudioStandard = 'standard'
	AudioDubbed = 'dubbed'

	SubtitleSoft = 'soft'
	SubtitleHard = 'hard'

	VoteUp = 'up'
	VoteDown = 'down'

	##############################################################################
	# CONSTRUCTOR
	##############################################################################

	def __init__(self):
		self.mStatus = None
		self.mType = None
		self.mDescription = None
		self.mMessage = None
		self.mData = None

	##############################################################################
	# DESTRUCTOR
	##############################################################################

	def __del__(self):
		pass

	##############################################################################
	# INTERNAL
	##############################################################################

	@classmethod
	def _keyInternal(self):
		return OrionSettings.getString('internal.api.orion', raw = True, obfuscate = True)

	def _logMessage(self):
		result = []
		if not self.mStatus == None: result.append(self.mStatus)
		if not self.mType == None: result.append(self.mType)
		if not self.mDescription == None: result.append(self.mDescription)
		if not self.mMessage == None: result.append(self.mMessage)
		return ' | '.join(result)

	##############################################################################
	# REQUEST
	##############################################################################

	def _request(self, mode = None, action = None, parameters = {}, raw = False):
		self.mStatus = None
		self.mType = None
		self.mDescription = None
		self.mMessage = None
		self.mData = None

		data = None
		networker = None

		try:
			if not mode == None: parameters[self.ParameterMode] = mode
			if not action == None: parameters[self.ParameterAction] = action

			from orion.modules.orionapp import OrionApp
			keyApp = OrionApp.instance().key()
			if keyApp == None and mode == self.ModeApp and action == self.ActionRetrieve: keyApp = self._keyInternal()
			if not keyApp == None and not keyApp == '': parameters[self.ParameterKeyApp] = keyApp

			from orion.modules.orionuser import OrionUser
			keyUser = OrionUser.instance().key()
			if not keyUser == None and not keyUser == '': parameters[self.ParameterKeyUser] = keyUser

			if not OrionSettings.silent():
				query = copy.deepcopy(parameters)
				if query:
					truncate = [self.ParameterId, self.ParameterKey, self.ParameterKeyApp, self.ParameterKeyUser, self.ParameterData]
					for key, value in query.iteritems():
						if key in truncate: query[key] = '-- truncated --'
				OrionTools.log('ORION API REQUEST: ' + OrionTools.jsonTo(query))

			networker = OrionNetworker(
				link = OrionSettings.getString('internal.api.link', raw = True),
				parameters = parameters,
				timeout = max(30, OrionSettings.getInteger('general.scraping.timeout')),
				agent = OrionNetworker.AgentOrion,
				debug = not OrionSettings.silent()
			)
			data = networker.request()
			if raw: return {'status' : networker.status(), 'headers' : networker.headers(), 'body' : data, 'response' : networker.response()}
			json = OrionTools.jsonFrom(data)

			result = json[self.ParameterResult]
			if self.ParameterStatus in result: self.mStatus = result[self.ParameterStatus]
			if self.ParameterType in result: self.mType = result[self.ParameterType]
			if self.ParameterDescription in result: self.mDescription = result[self.ParameterDescription]
			if self.ParameterMessage in result: self.mMessage = result[self.ParameterMessage]

			if self.ParameterData in json: self.mData = json[self.ParameterData]

			if self.mStatus == self.StatusError:
				if not OrionSettings.silent():
					OrionTools.log('ORION API ERROR: ' + self._logMessage())
				if OrionSettings.silentAllow(self.mType):
					OrionInterface.dialogNotification(title = 32048, message = self.mDescription, icon = OrionInterface.IconError)
			elif self.mStatus == self.StatusSuccess:
				if not OrionSettings.silent():
					OrionTools.log('ORION API SUCCESS: ' + self._logMessage())
				try:
					if OrionSettings.silentAllow(self.mStatus):
						count = self.mData[self.ParameterCount]
						message = OrionTools.translate(32062) + ': ' + str(count[self.ParameterTotal]) + ' | ' + OrionTools.translate(32063) + ': ' + str(count[self.ParameterFiltered])
						OrionTools.log('ORION STREAMS FOUND: ' + message)
						OrionInterface.dialogNotification(title = 32060, message = message, icon = OrionInterface.IconSuccess)
				except: pass
		except:
			try:
				self.mStatus = self.StatusError
				if not networker == None and networker.error() and not OrionSettings.silent():
					OrionInterface.dialogNotification(title = 32064, message = 33007, icon = OrionInterface.IconError)
				else:
					if not OrionSettings.silent():
						OrionTools.error('ORION API EXCEPTION')
						OrionTools.log('ORION API DATA: ' + str(data))
					if OrionSettings.silentAllow('exception'):
						OrionInterface.dialogNotification(title = 32061, message = 33006, icon = OrionInterface.IconError)
			except:
				OrionTools.error('ORION UNKNOWN API EXCEPTION')

		return self.statusSuccess()

	##############################################################################
	# STATUS
	##############################################################################

	def status(self):
		return self.mStatus

	def statusHas(self):
		return not self.mStatus == None

	def statusSuccess(self):
		return self.mStatus == self.StatusSuccess

	def statusError(self):
		return self.mStatus == self.StatusError

	##############################################################################
	# TYPE
	##############################################################################

	def type(self):
		return self.mType

	def typeHas(self):
		return not self.mType == None

	##############################################################################
	# DESCRIPTION
	##############################################################################

	def description(self):
		return self.mDescription

	def descriptionHas(self):
		return not self.mDescription == None

	##############################################################################
	# MESSAGE
	##############################################################################

	def message(self):
		return self.mMessage

	def messageHas(self):
		return not self.mMessage == None

	##############################################################################
	# DATA
	##############################################################################

	def data(self):
		return self.mData

	def dataHas(self):
		return not self.mData == None

	##############################################################################
	# RANGE
	##############################################################################

	@classmethod
	def range(self, value):
		if OrionTools.isArray(value):
			result = ''
			if len(value) == 0: return result
			if len(value) > 1 and not value[0] == None: result += str(value[0])
			result += '_'
			if len(value) > 1 and not value[1] == None: result += str(value[1])
			else: result += str(value[0])
			return result
		else:
			return str(value)

	##############################################################################
	# APP
	##############################################################################

	def appRetrieve(self, id = None, key = None):
		single = False
		if not id == None:
			single = OrionTools.isString(id)
			result = self._request(mode = self.ModeApp, action = self.ActionRetrieve, parameters = {self.ParameterId : id})
		elif not key == None:
			single = OrionTools.isString(key)
			result = self._request(mode = self.ModeApp, action = self.ActionRetrieve, parameters = {self.ParameterKey : key})
		else:
			result = self._request(mode = self.ModeApp, action = self.ActionRetrieve, parameters = {self.ParameterAll : True})
		try:
			if single: self.mData = self.mData[0]
			elif OrionTools.isDictionary(self.mData): self.mData = [self.mData]
		except: pass
		return result

	##############################################################################
	# USER
	##############################################################################

	def userRetrieve(self):
		return self._request(mode = self.ModeUser, action = self.ActionRetrieve)

	def userLogin(self, email, password):
		return self._request(mode = self.ModeUser, action = self.ActionLogin, parameters = {self.ParameterEmail : email, self.ParameterPassword : password})

	def userAnonymous(self):
		x = [OrionTools.randomInteger(1,9) for i in range(3)]
		return self._request(mode = self.ModeUser, action = self.ActionAnonymous, parameters = {self.ParameterKey : str(str(x[0])+str(x[1])+str(x[2])+str(x[0]+x[1]*x[2]))[::-1]})

	##############################################################################
	# STREAM
	##############################################################################

	def streamUpdate(self, item):
		return self._request(mode = self.ModeStream, action = self.ActionUpdate, parameters = {self.ParameterData : item})

	def streamVote(self, item, stream, vote = VoteUp):
		return self._request(mode = self.ModeStream, action = self.ActionVote, parameters = {self.ParameterItem : item, self.ParameterStream : stream, self.ParameterDirection : vote})

	def streamRetrieve(self, filters):
		return self._request(mode = self.ModeStream, action = self.ActionRetrieve, parameters = {self.ParameterData : filters})

	##############################################################################
	# NOTIFICATION
	##############################################################################

	def notificationRetrieve(self, time = None):
		parameters = {}
		if not time == None: parameters[self.ParameterTime] = time
		return self._request(mode = self.ModeNotification, action = self.ActionRetrieve, parameters = parameters)

	##############################################################################
	# SERVER
	##############################################################################

	def serverRetrieve(self, time = None):
		parameters = {}
		if not time == None: parameters[self.ParameterTime] = time
		return self._request(mode = self.ModeServer, action = self.ActionRetrieve, parameters = parameters)

	def serverTest(self):
		return self._request(mode = self.ModeServer, action = self.ActionTest)

	##############################################################################
	# FLARE
	##############################################################################

	def flare(self, link):
		return self._request(mode = self.ModeFlare, parameters = {self.ParameterLink : link}, raw = True)
