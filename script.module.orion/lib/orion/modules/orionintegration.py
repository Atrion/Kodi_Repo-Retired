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
# ORIONINTEGRATION
##############################################################################
# Class for integrating Orion into other addons.
##############################################################################

from orion.modules.oriontools import *
from orion.modules.orionsettings import *
from orion.modules.orioninterface import *

class OrionIntegration:

	ExtensionBackup = '.orion'
	PathLength = 50

	AddonGaia = 'Gaia'
	AddonIncursion = 'Incursion'
	AddonPlacenta = 'Placenta'
	AddonCovenant = 'Covenant'
	AddonMagicality = 'Magicality'
	AddonYoda = 'Yoda'
	AddonBodie = 'Bodie'
	AddonNeptuneRising = 'Neptune Rising'
	AddonDeathStreams = 'Death Streams'
	AddonLambdaScrapers = 'Lambda Scrapers'
	AddonUniversalScrapers = 'Universal Scrapers'
	AddonNanScrapers = 'NaN Scrapers'
	Addons = [AddonGaia, AddonIncursion, AddonPlacenta, AddonCovenant, AddonMagicality, AddonYoda, AddonBodie, AddonNeptuneRising, AddonDeathStreams, AddonLambdaScrapers, AddonUniversalScrapers, AddonNanScrapers]

	LanguageXml = 'xml'
	LanguagePython = 'python'

	CommentXmlStart = '<!-- [ORION/] -->'
	CommentXmlEnd = '<!-- [/ORION] -->'
	CommentPythonStart = '# [ORION/]'
	CommentPythonEnd = '# [/ORION]'

	##############################################################################
	# GENERAL
	##############################################################################

	@classmethod
	def id(self, addon, check = False):
		if addon == None: return addon
		addon = addon.lower().replace(' ', '')
		if check:
			addons = [i.lower().replace(' ', '') for i in self.Addons]
			if not addon in addons: return None
		return addon

	@classmethod
	def _comment(self, data, language = LanguagePython, indentation = ''):
		commentStart = ''
		commentEnd = ''
		if language == self.LanguageXml:
			commentStart = self.CommentXmlStart
			commentEnd = self.CommentXmlEnd
		elif language == self.LanguagePython:
			commentStart = self.CommentPythonStart
			commentEnd = self.CommentPythonEnd
		data = data.replace('\n', '\n' + indentation)
		return '\n\n' + indentation + commentStart + '\n' + indentation + data + '\n' + indentation + commentEnd + '\n'

	@classmethod
	def _expression(self, language = LanguagePython, full = True):
		commentStart = ''
		commentEnd = ''
		if language == self.LanguageXml:
			commentStart = self.CommentXmlStart
			commentEnd = self.CommentXmlEnd
		elif language == self.LanguagePython:
			commentStart = self.CommentPythonStart
			commentEnd = self.CommentPythonEnd
		if full: return '\n[\t ]*' + ((commentStart + '.*' + commentEnd).replace('\n', '').replace('[', '\[').replace(']', '\]').replace('/', '\/')) + '[\t ]*\n'
		else: return commentStart.replace('\n', '').replace('[', '\[').replace(']', '\]').replace('/', '\/')

	def _path(self, file):
		return OrionTools.pathJoin(OrionTools.addonPath(), 'lib', 'orion', 'integration', self.id, file)

	def _content(self, file):
		return OrionTools.fileRead(self._path(file)).strip()

	##############################################################################
	# BACKUP
	##############################################################################

	def _backupContains(self, path):
		return OrionTools.fileContains(path, self._expression(self.LanguageXml, False)) or OrionTools.fileContains(path, self._expression(self.LanguagePython, False))

	def _backupCreate(self):
		for i in self.files:
			if not self._backupContains(i):
				OrionTools.fileCopy(i, i + self.ExtensionBackup, overwrite = True)

	def _backupRestore(self):
		for i in self.files:
			j = i + self.ExtensionBackup
			if OrionTools.fileExists(j):
				OrionTools.fileMove(j, i, overwrite = True)

	##############################################################################
	# INIRIALIZE
	##############################################################################

	@classmethod
	def initialize(self, addon):
		integration = OrionIntegration()
		try:
			if addon == self.AddonGaia: integration._gaiaInitialize()
			elif addon == self.AddonIncursion: integration._incursionInitialize()
			elif addon == self.AddonPlacenta: integration._placentaInitialize()
			elif addon == self.AddonCovenant: integration._covenantInitialize()
			elif addon == self.AddonMagicality: integration._magicalityInitialize()
			elif addon == self.AddonYoda: integration._yodaInitialize()
			elif addon == self.AddonDeathStreams: integration._deathStreamsInitialize()
			elif addon == self.AddonLambdaScrapers: integration._lambdaScrapersInitialize()
			elif addon == self.AddonUniversalScrapers: integration._universalScrapersInitialize()
			elif addon == self.AddonNanScrapers: integration._nanScrapersInitialize()
		except: pass
		return integration

	##############################################################################
	# CHECK
	##############################################################################

	@classmethod
	def check(self):
		for addon in self.Addons:
			try:
				integration = self.initialize(addon)
				setting = OrionSettings.getIntegration(integration.id)
				if (not setting == '' or addon == self.AddonGaia) and not setting == integration.version:
					integration._integrate(addon)
					OrionSettings.setIntegration(integration.id, integration.version)
			except: pass

	##############################################################################
	# CLEAN
	##############################################################################

	def _clean(self, language = None):
		if language == None:
			self._clean(language = self.LanguageXml)
			self._clean(language = self.LanguagePython)
		else:
			expression = self._expression(language, True)
			for i in self.files:
				OrionTools.fileClean(i, expression)
			if not self.deletes == None:
				for i in self.deletes:
					if OrionTools.fileExists(i):
						OrionTools.fileDelete(i)
					elif OrionTools.directoryExists(i):
						OrionTools.directoryDelete(i)

	@classmethod
	def clean(self, addon):
		integration = self.initialize(addon)
		if OrionTools.addonEnabled(integration.idPlugin):
			if OrionInterface.dialogOption(title = 32174, message = OrionTools.translate(33021) % addon):
				integration._clean()
				integration._backupRestore()
				OrionSettings.externalRemove(integration.id)
				OrionInterface.dialogNotification(title = 32177, message = 33019, icon = OrionInterface.IconSuccess)
				return True
		else:
			OrionInterface.dialogNotification(title = 32175, message = 33027, icon = OrionInterface.IconError)
		return False

	##############################################################################
	# INTEGRATE
	##############################################################################

	@classmethod
	def integrate(self, addon):
		integration = self.initialize(addon)
		if OrionTools.addonEnabled(integration.idPlugin):
			if OrionInterface.dialogOption(title = 32174, message = OrionTools.translate(33020) % (addon, addon)):
				if integration._integrate(addon):
					if OrionInterface.dialogOption(title = 32174, message = OrionTools.translate(33022) % (addon, addon)):
						OrionSettings.setIntegration(integration.id, integration.version)
					else:
						OrionSettings.setIntegration(integration.id, '')
					OrionInterface.dialogConfirm(title = 32174, message = (OrionTools.translate(33025) % addon) + OrionInterface.fontNewline() + OrionInterface.font(33026, bold = True, color = OrionInterface.ColorPrimary))
		else:
			OrionInterface.dialogNotification(title = 32175, message = 33027, icon = OrionInterface.IconError)
		return False

	def _integrate(self, addon):
		self._backupCreate()
		self._clean()
		result = False
		if addon == self.AddonGaia: result = True
		elif addon == self.AddonIncursion: result = self._incursionIntegrate()
		elif addon == self.AddonPlacenta: result = self._placentaIntegrate()
		elif addon == self.AddonCovenant: result = self._covenantIntegrate()
		elif addon == self.AddonMagicality: result = self._magicalityIntegrate()
		elif addon == self.AddonYoda: result = self._yodaIntegrate()
		elif addon == self.AddonDeathStreams: result = self._deathStreamsIntegrate()
		elif addon == self.AddonLambdaScrapers: result = self._lambdaScrapersIntegrate()
		elif addon == self.AddonUniversalScrapers: result = self._universalScrapersIntegrate()
		elif addon == self.AddonNanScrapers: result = self._nanScrapersIntegrate()
		if result: OrionSettings.externalInsert(addon)
		return result

	def _integrateSuccess(self):
		OrionInterface.dialogNotification(title = 32176, message = 33018, icon = OrionInterface.IconSuccess)
		return True

	def _integrateFailure(self, message = None, path = None):
		self._clean()
		self._backupRestore()
		original = path
		if path == None: path = ''
		else: path = OrionInterface.fontNewline().join([path[i - self.PathLength : i] for i in range(self.PathLength, len(path) + self.PathLength, self.PathLength)])
		OrionInterface.dialogNotification(title = 32175, message = 33017, icon = OrionInterface.IconError)
		OrionInterface.dialogConfirm(title = 32174, message = OrionInterface.fontBold(32175) + OrionInterface.fontNewline() + message + OrionInterface.fontNewline() + path)
		OrionTools.log('INTEGRATION FAILURE: ' + message + ' (' + original + ')')
		return False

	##############################################################################
	# LAUNCH
	##############################################################################

	@classmethod
	def launch(self, addon):
		integration = self.initialize(addon)
		if OrionTools.addonEnabled(integration.idPlugin):
			OrionTools.addonLaunch(integration.idPlugin)
			return True
		else:
			OrionInterface.dialogNotification(title = 32175, message = 33027, icon = OrionInterface.IconError)
			return False

	##############################################################################
	# EXECUTE
	##############################################################################

	@classmethod
	def execute(self, addon, integration = True):
		items = []
		if integration:
			items.append(OrionInterface.fontBold(32178) + ': ' + OrionTools.translate(32179))
			items.append(OrionInterface.fontBold(32006) + ': ' + OrionTools.translate(32180))
		items.append(OrionInterface.fontBold(32181) + ': ' + OrionTools.translate(32182))
		choice = OrionInterface.dialogOptions(title = 32174, items = items)
		if integration:
			if choice == 0: return self.integrate(addon)
			elif choice == 1: return self.clean(addon)
			elif choice == 2: return self.launch(addon)
		else:
			if choice == 0: return self.launch(addon)

	@classmethod
	def executeGaia(self):
		OrionInterface.dialogConfirm(title = 32174, message = 33024)
		return self.execute(self.AddonGaia, integration = False)

	@classmethod
	def executeIncursion(self):
		return self.execute(self.AddonIncursion)

	@classmethod
	def executePlacenta(self):
		return self.execute(self.AddonPlacenta)

	@classmethod
	def executeCovenant(self):
		return self.execute(self.AddonCovenant)

	@classmethod
	def executeMagicality(self):
		return self.execute(self.AddonMagicality)

	@classmethod
	def executeYoda(self):
		return self.execute(self.AddonYoda)

	@classmethod
	def executeBodie(self):
		if OrionInterface.dialogOption(title = 32174, message = OrionTools.translate(33023) % (self.AddonBodie, self.AddonLambdaScrapers, self.AddonLambdaScrapers)):
			return self.executeLambdaScrapers()
		else:
			return False

	@classmethod
	def executeNeptuneRising(self):
		if OrionInterface.dialogOption(title = 32174, message = OrionTools.translate(33023) % (self.AddonNeptuneRising, self.AddonUniversalScrapers, self.AddonUniversalScrapers)):
			return self.executeUniversalScrapers()
		else:
			return False

	@classmethod
	def executeLambdaScrapers(self):
		return self.execute(self.AddonLambdaScrapers)

	@classmethod
	def executeDeathStreams(self):
		return self.execute(self.AddonDeathStreams)

	@classmethod
	def executeUniversalScrapers(self):
		return self.execute(self.AddonUniversalScrapers)

	@classmethod
	def executeNanScrapers(self):
		return self.execute(self.AddonNanScrapers)

	##############################################################################
	# GAIA
	##############################################################################

	def _gaiaInitialize(self):
		self.name = self.AddonGaia
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.gaia'
		self.version = OrionTools.addonVersion(self.idPlugin)
		self.files = []
		self.deletes = []

	##############################################################################
	# INCURSION
	##############################################################################

	def _incursionInitialize(self):
		self.name = self.AddonIncursion
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.incursion'
		self.idModule = 'script.module.incursion'
		self.version = OrionTools.addonVersion(self.idPlugin) + '-' + OrionTools.addonVersion(self.idModule)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)
		self.pathModule = OrionTools.addonPath(self.idModule)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathModule, 'addon.xml')
		self.pathSources = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _incursionIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), self.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]32345[\'"]\s*>', data):
			return self._integrateFailure('Incursion settings integration failure', self.pathSettings)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), self.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]script\.module\.beautifulsoup4[\'"]\s*\/>', data):
			return self._integrateFailure('Incursion addon metadata integration failure', self.pathAddon)

		# __init__.py
		data = self._comment(self._content('sources.py'), self.LanguagePython, '                    ')
		if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
			return self._integrateFailure('Incursion sources integration failure', self.pathSources)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('Incursion directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Incursion provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('Incursion module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# PLACENTA
	##############################################################################

	def _placentaInitialize(self):
		self.name = self.AddonPlacenta
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.placenta'
		self.idModule = 'script.module.placenta'
		self.version = OrionTools.addonVersion(self.idPlugin) + '-' + OrionTools.addonVersion(self.idModule)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)
		self.pathModule = OrionTools.addonPath(self.idModule)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathModule, 'addon.xml')
		self.pathSources = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _placentaIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), self.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]32345[\'"]\s*>', data):
			return self._integrateFailure('Placenta settings integration failure', self.pathSettings)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), self.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]script\.module\.beautifulsoup4[\'"]\s*\/>', data):
			return self._integrateFailure('Placenta addon metadata integration failure', self.pathAddon)

		# __init__.py
		data = self._comment(self._content('sources.py'), self.LanguagePython, '                    ')
		if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
			return self._integrateFailure('Placenta sources integration failure', self.pathSources)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('Placenta directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Placenta provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('Placenta module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# COVENANT
	##############################################################################

	def _covenantInitialize(self):
		self.name = self.AddonCovenant
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.covenant'
		self.idModule = 'script.module.covenant'
		self.version = OrionTools.addonVersion(self.idPlugin) + '-' + OrionTools.addonVersion(self.idModule)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)
		self.pathModule = OrionTools.addonPath(self.idModule)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathModule, 'addon.xml')
		self.pathSources = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _covenantIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), self.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]32345[\'"]\s*>', data):
			return self._integrateFailure('Covenant settings integration failure', self.pathSettings)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), self.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]xbmc\.python[\'"].*\/>', data):
			return self._integrateFailure('Covenant addon metadata integration failure', self.pathAddon)

		# __init__.py
		data = self._comment(self._content('sources.py'), self.LanguagePython, '                    ')
		if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
			return self._integrateFailure('Covenant sources integration failure', self.pathSources)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('Covenant directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Covenant provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('Covenant module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# MAGICALITY
	##############################################################################

	def _magicalityInitialize(self):
		self.name = self.AddonMagicality
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.magicality'
		self.idModule = 'script.module.magicality'
		self.version = OrionTools.addonVersion(self.idPlugin) + '-' + OrionTools.addonVersion(self.idModule)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)
		self.pathModule = OrionTools.addonPath(self.idModule)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathModule, 'addon.xml')
		self.pathSources = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _magicalityIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), self.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]32345[\'"]\s*>', data):
			return self._integrateFailure('Magicality settings integration failure', self.pathSettings)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), self.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]xbmc\.python[\'"].*\/>', data):
			return self._integrateFailure('Magicality addon metadata integration failure', self.pathAddon)

		# __init__.py
		data = self._comment(self._content('sources.py'), self.LanguagePython, '                    ')
		if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
			return self._integrateFailure('Magicality sources integration failure', self.pathSources)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('Magicality directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Magicality provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('Magicality module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# YODA
	##############################################################################

	def _yodaInitialize(self):
		self.name = self.AddonYoda
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.Yoda'
		self.idModule = 'script.module.Yoda'
		self.version = OrionTools.addonVersion(self.idPlugin) + '-' + OrionTools.addonVersion(self.idModule)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)
		self.pathModule = OrionTools.addonPath(self.idModule)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathModule, 'addon.xml')
		self.pathSources = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathModule, 'lib', 'resources', 'lib', 'sources', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _yodaIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), self.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]32345[\'"]\s*>', data):
			return self._integrateFailure('Yoda settings integration failure', self.pathSettings)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), self.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]xbmc\.python[\'"].*\/>', data):
			return self._integrateFailure('Yoda addon metadata integration failure', self.pathAddon)

		# __init__.py
		data = self._comment(self._content('sources.py'), self.LanguagePython, '                    ')
		if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
			return self._integrateFailure('Yoda sources integration failure', self.pathSources)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('Yoda directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Yoda provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('Yoda module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# DEATH STREAMS
	##############################################################################

	def _deathStreamsInitialize(self):
		self.name = self.AddonDeathStreams
		self.id = self.id(self.name)
		self.idPlugin = 'plugin.video.blamo'
		self.version = OrionTools.addonVersion(self.idPlugin)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)

		self.pathAddon = OrionTools.pathJoin(self.pathPlugin, 'addon.xml')
		self.pathOrionoid = OrionTools.pathJoin(self.pathPlugin, 'scrapers', 'orionoid.py')

		self.files = []
		self.files.append(self.pathAddon)

		self.deletes = []
		self.deletes.append(self.pathOrionoid)

	def _deathStreamsIntegrate(self):
		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), self.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]script\.module\.dateutil[\'"]\s*\/>', data):
			return self._integrateFailure('Death Streams addon metadata integration failure', self.pathAddon)

		# orionoid.py
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Death Streams provider integration failure', self.pathOrionoid)

		return self._integrateSuccess()

	##############################################################################
	# LAMBDA SCRAPERS
	##############################################################################

	def _lambdaScrapersInitialize(self):
		self.name = self.AddonLambdaScrapers
		self.id = self.id(self.name)
		self.idPlugin = 'script.module.lambdascrapers'
		self.version = OrionTools.addonVersion(self.idPlugin)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)

		self.pathAddon = OrionTools.pathJoin(self.pathPlugin, 'addon.xml')
		self.pathSources = OrionTools.pathJoin(self.pathPlugin, 'lib', 'lambdascrapers', 'sources_ALL', '__init__.py')
		self.pathOrion = OrionTools.pathJoin(self.pathPlugin, 'lib', 'lambdascrapers', 'sources_ALL', 'orion')
		self.pathOrionoid = OrionTools.pathJoin(self.pathOrion, 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathOrion, '__init__.py')

		self.files = []
		self.files.append(self.pathAddon)
		self.files.append(self.pathSources)
		self.files.append(self.pathInit)

		self.deletes = []
		self.deletes.append(self.pathOrion)

	def _lambdaScrapersIntegrate(self):
		# __init__.py
		data = self._comment(self._content('sources.py'), self.LanguagePython, '                    ')
		if not OrionTools.fileInsert(self.pathSources, '\.load_module\(module_name\)', data):
			return self._integrateFailure('Lambda Scrapers sources integration failure', self.pathSources)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), self.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]xbmc\.python[\'"].*\/>', data):
			return self._integrateFailure('Lambda Scrapers addon metadata integration failure', self.pathAddon)

		# orionoid.py
		if not OrionTools.directoryExists(self.pathOrion) and not OrionTools.directoryCreate(self.pathOrion):
			return self._integrateFailure('Lambda Scrapers directory creation error', self.pathOrion)
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Lambda Scrapers provider integration failure', self.pathOrionoid)
		if not OrionTools.fileCopy(self._path('module.py'), self.pathInit, overwrite = True):
			return self._integrateFailure('Lambda Scrapers module integration failure', self.pathInit)

		return self._integrateSuccess()

	##############################################################################
	# UNIVERSAL SCRAPERS
	##############################################################################

	def _universalScrapersInitialize(self):
		self.name = self.AddonUniversalScrapers
		self.id = self.id(self.name)
		self.idPlugin = 'script.module.universalscrapers'
		self.version = OrionTools.addonVersion(self.idPlugin)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathPlugin, 'addon.xml')
		self.pathOrionoid = OrionTools.pathJoin(self.pathPlugin, 'lib', 'universalscrapers', 'scraperplugins', 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathPlugin, 'lib', 'universalscrapers', '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathInit)

		self.deletes = []
		self.deletes.append(self.pathOrionoid)

	def _universalScrapersIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), self.LanguageXml, '\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]Scrapers\s*1[\'"]\s*>', data):
			return self._integrateFailure('Universal Scrapers settings integration failure', self.pathSettings)

		# __init__.py
		data = self._comment(self._content('module.py'), self.LanguagePython, '    ')
		if not OrionTools.fileInsert(self.pathInit, 'relevant_scrapers\(\s*include_disabled\s*=\s*True\s*\),\s*key\s*=\s*lambda\s*x\s*:\s*x\.name\.lower\(\)\s*\)', data):
			return self._integrateFailure('Universal Scrapers module integration failure', self.pathInit)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), self.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]repository\.universalscrapers[\'"]\s*\/>', data):
			return self._integrateFailure('Universal Scrapers addon metadata integration failure', self.pathAddon)

		# orionoid.py
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('Universal Scrapers provider integration failure', self.pathOrionoid)

		return self._integrateSuccess()

	##############################################################################
	# NAN SCRAPERS
	##############################################################################

	def _nanScrapersInitialize(self):
		self.name = self.AddonNanScrapers
		self.id = self.id(self.name)
		self.idPlugin = 'script.module.nanscrapers'
		self.version = OrionTools.addonVersion(self.idPlugin)

		self.pathPlugin = OrionTools.addonPath(self.idPlugin)

		self.pathSettings = OrionTools.pathJoin(self.pathPlugin, 'resources', 'settings.xml')
		self.pathAddon = OrionTools.pathJoin(self.pathPlugin, 'addon.xml')
		self.pathOrionoid = OrionTools.pathJoin(self.pathPlugin, 'lib', 'nanscrapers', 'scraperplugins', 'orionoid.py')
		self.pathInit = OrionTools.pathJoin(self.pathPlugin, 'lib', 'nanscrapers', '__init__.py')

		self.files = []
		self.files.append(self.pathSettings)
		self.files.append(self.pathAddon)
		self.files.append(self.pathInit)

		self.deletes = []
		self.deletes.append(self.pathOrionoid)

	def _nanScrapersIntegrate(self):
		# settings.xml
		data = self._comment(self._content('settings.xml'), self.LanguageXml, '\t')
		if not OrionTools.fileInsert(self.pathSettings, '<\s*category\s+label\s*=\s*[\'"]Scrapers\s*1[\'"]\s*>', data):
			return self._integrateFailure('NaN Scrapers settings integration failure', self.pathSettings)

		# __init__.py
		data = self._comment(self._content('module.py'), self.LanguagePython, '    ')
		if not OrionTools.fileInsert(self.pathInit, 'relevant_scrapers\(\s*include_disabled\s*=\s*True\s*\),\s*key\s*=\s*lambda\s*x\s*:\s*x\.name\.lower\(\)\s*\)', data):
			return self._integrateFailure('NaN Scrapers module integration failure', self.pathInit)

		# addon.xml
		data = self._comment(self._content('addon.xml') % (OrionTools.addonId(), OrionTools.addonVersion()), self.LanguageXml, '\t\t')
		if not OrionTools.fileInsert(self.pathAddon, '<import\s+addon\s*=\s*[\'"]script\.module\.six[\'"]\s*\/>', data):
			return self._integrateFailure('NaN Scrapers addon metadata integration failure', self.pathAddon)

		# orionoid.py
		if not OrionTools.fileCopy(self._path('orionoid.py'), self.pathOrionoid, overwrite = True):
			return self._integrateFailure('NaN Scrapers provider integration failure', self.pathOrionoid)

		return self._integrateSuccess()
