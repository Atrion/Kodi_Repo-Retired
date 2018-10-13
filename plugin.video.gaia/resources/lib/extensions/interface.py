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

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import re
import os
import json
import urllib
import time
import datetime
import threading
from resources.lib.extensions import tools
from resources.lib.extensions import network
from resources.lib.modules import workers

class Translation(object):

	@classmethod
	def string(self, id, utf8 = True, system = False):
		if isinstance(id, (int, long)):
			# Needs ID when called from RunScript(vpn.py)
			if system: result = xbmc.getLocalizedString(id)
			else: result = xbmcaddon.Addon(tools.System.GaiaAddon).getLocalizedString(id)
		else:
			try: result = str(id)
			except: result = id
		if utf8:
			result = tools.Converter.unicode(string = result, umlaut = True).encode('utf-8')
		return result

class Skin(object):

	TypeAeonNox = 'aeon.nox'
	TypeGaiaAeonNox = 'skin.gaia.aeon.nox'

	@classmethod
	def _directory(self):
		return xbmc.getSkinDir()

	@classmethod
	def id(self):
		return self._directory()

	# Any Aeon Nox version
	@classmethod
	def isAeonNox(self):
		return self.TypeAeonNox in self.id()

	@classmethod
	def isGaiaAeonNox(self):
		return self.TypeGaiaAeonNox in self.id()

	@classmethod
	def select(self):
		id = tools.Extensions.IdGaiaSkins
		items = ['Default', 'Gaia 1 (Color)']
		getMore = Format.fontBold(Translation.string(33740))
		if tools.Extensions.installed(id):
			items.extend(['Gaia 2 (Color)', 'Gaia 3 (Color)', 'Bubbles 1 (Blue)', 'Bubbles 2 (Color)', 'Minimalism (Grey)', 'Universe (Color)', 'Glass (Transparent)', 'Cinema 1 (Blue)', 'Cinema 2 (Blue)', 'Cinema 3 (Orange)', 'Cinema 4 (Red)', 'Home 1 (Color)', 'Home 2 (Blue)', 'Home 3 (Red)', 'Home 4 (White)', 'Home 5 (Black)', 'Home 6 (Blue)'])
		else:
			items.extend([getMore])
		choice = Dialog.options(title = 33337, items = items)
		if choice >= 0:
			if items[choice] == getMore:
				choice = Dialog.option(title = 33337, message = 33742, labelConfirm = 33736, labelDeny = 33743)
				if choice:
					tools.Extensions.enable(id = id)
			else:
				tools.Settings.set('interface.theme.skin', items[choice])

class Icon(object):

	TypeIcon = 'icon'
	TypeThumb = 'thumb'
	TypePoster = 'poster'
	TypeBanner = 'banner'
	TypeDefault = TypeIcon

	QualitySmall = 'small'
	QualityLarge = 'large'
	QualityDefault = QualityLarge

	SpecialNone = None
	SpecialDonations = 'donations'
	SpecialNotifications = 'notifications'

	ThemeInitialized = False
	ThemePath = None
	ThemeIcon = None
	ThemeThumb = None
	ThemePoster = None
	ThemeBanner = None

	@classmethod
	def _initialize(self, special = SpecialNone):
		if special == False or not special == self.ThemeInitialized:
			self.ThemeInitialized = special
			if special: theme = special
			else: theme = tools.Settings.getString('interface.theme.icon').lower()

			if not theme in ['default', '-', '']:

				theme = theme.replace(' ', '').lower()
				if 'glass' in theme:
					theme = theme.replace('(', '').replace(')', '')
				else:
					index = theme.find('(')
					if index >= 0: theme = theme[:index]

				addon = tools.System.pathResources() if theme in ['white', self.SpecialDonations, self.SpecialNotifications] else tools.System.pathIcons()
				self.ThemePath = os.path.join(addon, 'resources', 'media', 'icons', theme)

				quality = tools.Settings.getInteger('interface.theme.icon.quality')
				if quality == 0:
					if Skin.isAeonNox():
						self.ThemeIcon = self.QualitySmall
						self.ThemeThumb = self.QualitySmall
						self.ThemePoster = self.QualityLarge
						self.ThemeBanner = self.QualityLarge
					else:
						self.ThemeIcon = self.QualityLarge
						self.ThemeThumb = self.QualityLarge
						self.ThemePoster = self.QualityLarge
						self.ThemeBanner = self.QualityLarge
				elif quality == 1:
					self.ThemeIcon = self.QualitySmall
					self.ThemeThumb = self.QualitySmall
					self.ThemePoster = self.QualitySmall
					self.ThemeBanner = self.QualitySmall
				elif quality == 2:
					self.ThemeIcon = self.QualityLarge
					self.ThemeThumb = self.QualityLarge
					self.ThemePoster = self.QualityLarge
					self.ThemeBanner = self.QualityLarge
				else:
					self.ThemeIcon = self.QualityLarge
					self.ThemeThumb = self.QualityLarge
					self.ThemePoster = self.QualityLarge
					self.ThemeBanner = self.QualityLarge

	@classmethod
	def path(self, icon, type = TypeDefault, default = None, special = SpecialNone, quality = None):
		if icon == None: return None
		self._initialize(special = special)
		if self.ThemePath == None:
			return default
		else:
			if quality == None:
				if type == self.TypeIcon: type = self.ThemeIcon
				elif type == self.TypeThumb: type = self.ThemeThumb
				elif type == self.TypePoster: type = self.ThemePoster
				elif type == self.TypeBanner: type = self.ThemeBanner
				else: type = self.ThemeIcon
			else:
				type = quality
			if not icon.endswith('.png'): icon += '.png'
			return os.path.join(self.ThemePath, type, icon)

	@classmethod
	def pathAll(self, icon, default = None, special = SpecialNone):
		return (
			self.pathIcon(icon = icon, default = default, special = special),
			self.pathThumb(icon = icon, default = default, special = special),
			self.pathPoster(icon = icon, default = default, special = special),
			self.pathBanner(icon = icon, default = default, special = special)
		)

	@classmethod
	def pathIcon(self, icon, default = None, special = SpecialNone):
		return self.path(icon = icon, type = self.TypeIcon, default = default, special = special)

	@classmethod
	def pathThumb(self, icon, default = None, special = SpecialNone):
		return self.path(icon = icon, type = self.TypeThumb, default = default, special = special)

	@classmethod
	def pathPoster(self, icon, default = None, special = SpecialNone):
		return self.path(icon = icon, type = self.TypePoster, default = default, special = special)

	@classmethod
	def pathBanner(self, icon, default = None, special = SpecialNone):
		return self.path(icon = icon, type = self.TypeBanner, default = default, special = special)

	@classmethod
	def select(self):
		id = tools.Extensions.IdGaiaIcons
		items = ['Default', 'White']
		getMore = Format.fontBold(Translation.string(33739))
		if tools.Extensions.installed(id):
			items.extend(['Black', 'Glass (Light)', 'Glass (Dark)', 'Shadow (Grey)', 'Fossil (Grey)', 'Navy (Blue)', 'Cerulean (Blue)', 'Sky (Blue)', 'Pine (Green)', 'Lime (Green)', 'Ruby (Red)', 'Candy (Red)', 'Tiger (Orange)', 'Pineapple (Yellow)', 'Violet (Purple)', 'Magenta (Pink)', 'Amber (Brown)'])
		else:
			items.extend([getMore])
		choice = Dialog.options(title = 33338, items = items)
		if choice >= 0:
			if items[choice] == getMore:
				choice = Dialog.option(title = 33338, message = 33741, labelConfirm = 33736, labelDeny = 33743)
				if choice:
					tools.Extensions.enable(id = id)
			else:
				tools.Settings.set('interface.theme.icon', items[choice])

def formatColorInitialize(customize, type, default):
	if customize:
		color = tools.Settings.getString('interface.color.' + type)
		try: return re.search('\\[.*\\](.*)\\[.*\\]', color, re.IGNORECASE).group(1)
		except: return ''
	else:
		return default

class Format(object):

	ColorCustomize = tools.Settings.getBoolean('interface.color.enabled')

	ColorNone = None
	ColorOrion = formatColorInitialize(ColorCustomize, 'orion', 'FF637385')
	ColorMain = formatColorInitialize(ColorCustomize, 'main', 'FF2396FF')
	ColorAlternative = formatColorInitialize(ColorCustomize, 'alternative', 'FF004F98')
	ColorSpecial = formatColorInitialize(ColorCustomize, 'special', 'FF6C3483')
	ColorUltra = formatColorInitialize(ColorCustomize, 'ultra', 'FF00A177')
	ColorExcellent = formatColorInitialize(ColorCustomize, 'excellent', 'FF1E8449')
	ColorGood = formatColorInitialize(ColorCustomize, 'good', 'FF668D2E')
	ColorMedium = formatColorInitialize(ColorCustomize, 'medium', 'FFB7950B')
	ColorPoor = formatColorInitialize(ColorCustomize, 'poor', 'FFBA4A00')
	ColorBad = formatColorInitialize(ColorCustomize, 'bad', 'FF922B21')
	ColorGaia1 = 'FFA0C12C'
	ColorGaia2 = 'FF3C7DBF'

	FontNewline = '[CR]'
	FontSeparator = ' | '
	FontDivider = ' - '
	FontSplitInterval = 50

	@classmethod
	def settingsColorUpdate(self, type):
		setting = 'interface.color.' + type
		color = Dialog.input(title = 35235, type = Dialog.InputAlphabetic, default = self.settingsColor(tools.Settings.getString(setting)))
		if self.colorIsHex(color):
			while len(color) < 8: color = 'F' + color
			if len(color) > 8: color = color[:8]
			tools.Settings.set(setting, self.fontColor(color, color))
		else:
			Dialog.notification(title = 35235, message = 35236, icon = Dialog.IconNativeError)

		# If this option is disabled and the user enables it and immediately afterwards selects a color, the settings dialog is closed without being saved first.
		# Force enable it here.
		tools.Settings.set('interface.color.enabled', True)

	@classmethod
	def settingsColor(self, color):
		try: return re.search('\\[.*\\](.*)\\[.*\\]', color, re.IGNORECASE).group(1)
		except: return ''

	@classmethod
	def colorIsHex(self, color):
		return re.match('[0-9a-fA-F]*', color)

	@classmethod
	def colorToRgb(self, hex):
		return [int(hex[i:i+2], 16) for i in range(2,8,2)]

	@classmethod
	def colorToHex(self, rgb):
		rgb = [int(i) for i in rgb]
		return 'FF' + ''.join(['0{0:x}'.format(i) if i < 16 else '{0:x}'.format(i) for i in rgb])

	@classmethod
	def colorGradient(self, startHex, endHex, count = 10):
		# http://bsou.io/posts/color-gradients-with-python
		start = self.colorToRgb(startHex)
		end = self.colorToRgb(endHex)
		colors = [start]
		for i in range(1, count):
			vector = [int(start[j] + (float(i) / (count-1)) * (end[j] - start[j])) for j in range(3)]
			colors.append(vector)
		return [self.colorToHex(i) for i in colors]

	@classmethod
	def colorGradientIncrease(self, count = 10):
		return self.colorGradient(self.ColorBad, self.ColorExcellent, count)

	@classmethod
	def colorGradientDecrease(self, count = 10):
		return self.colorGradient(self.ColorExcellent, self.ColorBad, count)

	@classmethod
	def colorChange(self, color, change = 10):
		if color:
			color = self.colorToRgb(color)
			color = [i + change for i in color]
			color = [min(255, max(0, i)) for i in color]
			return self.colorToHex(color)
		else:
			return None

	@classmethod
	def colorLighter(self, color, change = 10):
		return self.colorChange(color, change)

	@classmethod
	def colorDarker(self, color, change = 10):
		return self.colorChange(color, -change)

	@classmethod
	def __translate(self, label):
		return Translation.string(label)

	@classmethod
	def font(self, label, color = None, bold = None, italic = None, light = None, uppercase = None, lowercase = None, capitalcase = None, newline = None, separator = None):
		label = self.__translate(label)
		if label:
			if color:
				label = self.fontColor(label, color)
			if bold:
				label = self.fontBold(label)
			if italic:
				label = self.fontItalic(label)
			if light:
				label = self.fontLight(label)
			if uppercase:
				label = self.fontUppercase(label)
			elif lowercase:
				label = self.fontLowercase(label)
			elif capitalcase:
				label = self.fontCapitalcase(label)
			if newline:
				label += self.fontNewline()
			if separator:
				label += self.fontSeparator()
			return label
		else:
			return ''

	@classmethod
	def fontColor(self, label, color):
		if color == None: return label
		if len(color) == 6: color = 'FF' + color
		label = self.__translate(label)
		return '[COLOR ' + color + ']' + label + '[/COLOR]'

	@classmethod
	def fontBold(self, label):
		label = self.__translate(label)
		return '[B]' + label + '[/B]'

	@classmethod
	def fontItalic(self, label):
		label = self.__translate(label)
		return '[I]' + label + '[/I]'

	@classmethod
	def fontLight(self, label):
		label = self.__translate(label)
		return '[LIGHT]' + label + '[/LIGHT]'

	@classmethod
	def fontUppercase(self, label):
		label = self.__translate(label)
		return '[UPPERCASE]' + label + '[/UPPERCASE]'

	@classmethod
	def fontLowercase(self, label):
		label = self.__translate(label)
		return '[LOWERCASE]' + label + '[/LOWERCASE]'

	@classmethod
	def fontCapitalcase(self, label):
		label = self.__translate(label)
		return '[CAPITALIZE]' + label + '[/CAPITALIZE]'

	@classmethod
	def fontNewline(self):
		return self.FontNewline

	@classmethod
	def fontSeparator(self):
		return self.FontSeparator

	@classmethod
	def fontDivider(self):
		return self.FontDivider

	@classmethod
	def fontSplit(self, label, interval = None, type = None):
		if not interval: interval = self.FontSplitInterval
		if not type: type = self.FontNewline
		return re.sub('(.{' + str(interval) + '})', '\\1' + type, label, 0, re.DOTALL)

	# Synonyms

	@classmethod
	def color(self, label, color):
		return self.fontColor(label, color)

	@classmethod
	def bold(self, label):
		return self.fontBold(label)

	@classmethod
	def italic(self, label):
		return self.fontItalic(label)

	@classmethod
	def light(self, label):
		return self.fontLight(label)

	@classmethod
	def uppercase(self, label):
		return self.fontUppercase(label)

	@classmethod
	def lowercase(self, label):
		return self.fontLowercase(label)

	@classmethod
	def capitalcase(self, label):
		return self.fontCapitalcase(label)

	@classmethod
	def newline(self):
		return self.fontNewline()

	@classmethod
	def separator(self):
		return self.fontSeparator()

	@classmethod
	def divider(self):
		return self.fontDivider()

	@classmethod
	def split(self, label, interval = None, type = None):
		return self.fontSplit(label = label, interval = interval, type = type)

class Changelog(object):

	@classmethod
	def show(self):
		path = os.path.join(tools.System.path(), 'changelog.txt')
		file = open(path)
		text = file.read()
		file.close()
		Dialog.page(title = 33503, message = text)

CoreIntance = None

class Core(object):

	def __init__(self):
		self.mDialog = None
		self.mTitle = None
		self.mTitleBold = None
		self.mMessage = None
		self.mProgress = None
		self.mBackground = self.backgroundSetting()
		self.mClosed = True

		self.mThread = None
		self.mRunning = False
		self.mDots = False
		self.mSuffix = ''

	def __del__(self):
		# If CoreIntance runs out of scope, close the dialog.
		self.close()

	def _dots(self):
		dots = ' '
		self.mRunning = True
		while self.mDots and self.visible():
			dots += '.'
			if len(dots) > 4: dots = ' '
			self.mSuffix = Format.fontBold(dots)
			self._update()
			tools.Time.sleep(0.5)
		self.mRunning = False

	def _set(self, dialog = None, title = None, message = None, progress = None, background = None, dots = None):
		if not dots == None: self.mDots = dots
		if not dialog == None: self.mDialog = dialog

		if not title == None: self.mTitle = title
		if self.mTitle == None: self.mTitle = 35302
		self.mTitleBold = Format.fontBold(self.mTitle)

		if not message == None: self.mMessage = message
		if self.mMessage == None: self.mMessage = 35302

		if not progress == None: self.mProgress = progress
		if self.mProgress == None: self.mProgress = 0

		if not background == None: self.mBackground = background
		if self.mBackground == None: self.mBackground = self.backgroundSetting()

	@classmethod
	def instance(self):
		global CoreIntance
		if CoreIntance == None:
			CoreIntance = Core()
		return CoreIntance

	@classmethod
	def dialog(self):
		return self.instance().mDialog

	@classmethod
	def background(self):
		return self.instance().mBackground

	@classmethod
	def backgroundSetting(self):
		return tools.Settings.getInteger('interface.stream.progress') == 1

	@classmethod
	def canceled(self):
		try: return self.dialog().iscanceled()
		except: return False

	@classmethod
	def visible(self):
		return not self.instance().mClosed and not self.canceled()

	@classmethod
	def create(self, title = None, message = None, progress = None, background = None, close = None, dots = True):
		try:
			core = self.instance()

			if close == None:
				# Background dialog has a lot more problems. Always close.
				# Foreground dialog is more robust as does not need it.
				# This ensures the the foreground dialog stays open, instead of popping up and closing all the time.

				# NB: Currently seems fine with background dialogs as well. In case the interleaving flickering between messages starts again, enable this.
				close = False
				#if background == None: close = core.mBackground
				#else: close = background

			if close or not core.mDialog:
				self.close()

			core._set(title = title, message = message, progress = progress, background = background, dots = dots)

			if core.mClosed or not core.mDialog:
				# If launched for the first time, close all other progress dialogs.
				if not core.mDialog:
					Dialog.closeAllProgress()
					tools.Time.sleep(0.1)
				core.mDialog = Dialog.progress(background = core.mBackground, title = core.mTitle, message = core.mMessage)

			core.mClosed = False
			core._update()

			if core.mDots and (not core.mThread or not core.mRunning):
				core.mThread = threading.Thread(target = core._dots)
				core.mThread.start()

			return core.mDialog
		except:
			tools.Logger.error()

	def _update(self):
		if self.mBackground:
			try: self.mDialog.update(self.mProgress, self.mTitleBold, self.mMessage % self.mSuffix)
			except: self.mDialog.update(self.mProgress, self.mTitleBold, self.mMessage)
		else:
			try: self.mDialog.update(self.mProgress, self.mMessage % self.mSuffix)
			except: self.mDialog.update(self.mProgress, self.mMessage)

	@classmethod
	def update(self, title = None, message = None, progress = None, background = None, dots = None):
		core = self.instance()
		if core.mDialog == None or not self.visible():
			if dots == None: return self.create(title = title, message = message, progress = progress, background = background)
			else: return self.create(title = title, message = message, progress = progress, background = background, dots = dots)
		else:
			core._set(title = title, message = message, progress = progress, dots = dots)
			core._update()
			return core.mDialog

	@classmethod
	def close(self, delay = 0):
		try:
			# NB: Checking DialogCoreClosed is very important.
			# Do not rely on the try-catch statement.
			# Kodi crashes instead of throwing an exception.
			core = self.instance()
			if not core.mClosed:
				core.mClosed = True
				if core.mDialog:
					# Must be set to 100, otherwise it shows up in a later dialog.
					#if core.mBackground: core.mDialog.update(100, ' ', ' ')
					#else: core.mDialog.update(100, ' ')
					core.mProgress = 100
					core._update()

					core.mDialog.close()
				if delay > 0: tools.Time.sleep(delay)
		except:
			pass

class Dialog(object):

	IconPlain = 'logo'
	IconInformation = 'information'
	IconWarning = 'warning'
	IconError = 'error'
	IconSuccess = 'success'

	IconNativeLogo = 'nativelogo'
	IconNativeInformation = 'nativeinformation'
	IconNativeWarning = 'nativewarning'
	IconNativeError = 'nativeerror'

	InputAlphabetic = xbmcgui.INPUT_ALPHANUM # Standard keyboard
	InputNumeric = xbmcgui.INPUT_NUMERIC # Format: #
	InputDate = xbmcgui.INPUT_DATE # Format: DD/MM/YYYY
	InputTime = xbmcgui.INPUT_TIME # Format: HH:MM
	InputIp = xbmcgui.INPUT_IPADDRESS # Format: #.#.#.#
	InputPassword = xbmcgui.INPUT_PASSWORD # Returns MD55 hash of input and the input is masked.

	# Numbers/values must correspond with Kodi
	BrowseFile = 1
	BrowseImage = 2
	BrowseDirectoryRead = 0
	BrowseDirectoryWrite = 3
	BrowseDefault = BrowseFile

	PageId = 10147
	ProgressId = 10101

	# Close all open dialog.
	# Sometimes if you open a dialog right after this, it also clauses. Might need some sleep to prevent this. sleep in ms.
	@classmethod
	def closeAll(self, sleep = None):
		xbmc.executebuiltin('Dialog.Close(all,true)')
		if sleep: time.sleep(sleep / 1000.0)

	@classmethod
	def closeAllProgress(self, sleep = None):
		xbmc.executebuiltin('Dialog.Close(progressdialog,true)')
		if sleep: time.sleep(sleep / 1000.0)

	@classmethod
	def aborted(self):
		return xbmc.abortRequested

	# Current window ID
	@classmethod
	def windowId(self):
		return xbmcgui.getCurrentWindowId()

	# Check if certain window is currently showing.
	@classmethod
	def windowVisible(self, id):
		return self.windowId() == id

	# Current dialog ID
	@classmethod
	def dialogId(self):
		return xbmcgui.getCurrentWindowDialogId()

	# Check if certain dialog is currently showing.
	@classmethod
	def dialogVisible(self, id):
		return self.dialogId() == id

	@classmethod
	def dialogProgressVisible(self):
		return self.dialogVisible(self.ProgressId)

	@classmethod
	def confirm(self, message, title = None):
		return xbmcgui.Dialog().ok(self.title(title), self.__translate(message))

	@classmethod
	def select(self, items, multiple = False, preselect = [], title = None):
		return self.options(items = items, multiple = multiple, preselect = preselect, title = title)

	@classmethod
	def option(self, message, labelConfirm = None, labelDeny = None, title = None):
		if not labelConfirm == None:
			labelConfirm = self.__translate(labelConfirm)
		if not labelDeny == None:
			labelDeny = self.__translate(labelDeny)
		return xbmcgui.Dialog().yesno(self.title(title), self.__translate(message), yeslabel = labelConfirm, nolabel = labelDeny)

	@classmethod
	def options(self, items, multiple = False, preselect = [], title = None):
		if multiple:
			try: return xbmcgui.Dialog().multiselect(self.title(title), items, preselect = preselect)
			except: return xbmcgui.Dialog().multiselect(self.title(title), items)
		else:
			return xbmcgui.Dialog().select(self.title(title), items)

	# icon: icon or path to image file.
	# titleless: Without Gaia at the front of the title.
	@classmethod
	def notification(self, message, icon = None, time = 3000, sound = False, title = None, titleless = False):
		if icon and not (icon.startswith('http') or icon.startswith('ftp') or tools.File.exists(icon)):
			icon = icon.lower()
			if icon == self.IconNativeInformation: icon = xbmcgui.NOTIFICATION_INFO
			elif icon == self.IconNativeWarning: icon = xbmcgui.NOTIFICATION_WARNING
			elif icon == self.IconNativeError: icon = xbmcgui.NOTIFICATION_ERROR
			else:
				if icon == self.IconPlain or icon == self.IconNativeLogo: icon = 'plain'
				elif icon == self.IconWarning: icon = 'warning'
				elif icon == self.IconError: icon = 'error'
				elif icon == self.IconSuccess: icon = 'success'
				else: icon = 'information'
				icon = Icon.pathIcon(icon = icon, special = Icon.SpecialNotifications)
		xbmcgui.Dialog().notification(self.title(title, titleless = titleless), self.__translate(message), icon, time, sound = sound)

	@classmethod
	def progress(self, message = None, background = False, title = None):
		if background:
			dialog = xbmcgui.DialogProgressBG()
		else:
			dialog = xbmcgui.DialogProgress()
		if not message:
			message = ''
		else:
			message = self.__translate(message)
		title = self.title(title)
		dialog.create(title, message)
		if background:
			dialog.update(0, title, message)
		else:
			dialog.update(0, message)
		return dialog

	# verify: Existing MD5 password string to compare against.
	# confirm: Confirm password. Must be entered twice
	# hidden: Hides alphabetic input.
	# default: Default set input.
	@classmethod
	def input(self, type = InputAlphabetic, verify = False, confirm = False, hidden = False, default = None, title = None):
		default = '' if default == None else default
		if verify:
			option = xbmcgui.PASSWORD_VERIFY
			if isinstance(verify, basestring):
				default = verify
		elif confirm:
			option = 0
		elif hidden:
			option = xbmcgui.ALPHANUM_HIDE_INPUT
		else:
			option = None
		# NB: Although the default parameter is given in the docs, it seems that the parameter is not actually called "default". Hence, pass it in as an unmaed parameter.
		if option == None: result = xbmcgui.Dialog().input(self.title(title), default, type = type)
		else: result = xbmcgui.Dialog().input(self.title(title), default, type = type, option = option)

		if verify:
			return not result == ''
		else:
			return result

	@classmethod
	def inputPassword(self, verify = False, confirm = False, title = None):
		return self.input(title = title, type = self.InputPassword, verify = verify, confirm = confirm)

	@classmethod
	def browse(self, type = BrowseDefault, default = None, multiple = False, mask = [], title = None):
		if default == None: default = os.path.join(tools.System.pathHome(), '') # Needs to end with a slash
		if mask == None: mask = []
		elif isinstance(mask, basestring): mask = [mask]
		for i in range(len(mask)):
			mask[i] = mask[i].lower()
			if not mask[i].startswith('.'):
				mask[i] = '.' + mask[i]
		mask = '|'.join(mask)
		return xbmcgui.Dialog().browse(type, self.title(title), 'files', mask, True, False, default, multiple)

	@classmethod
	def page(self, message, title = None):
		xbmc.executebuiltin('ActivateWindow(%d)' % self.PageId)
		time.sleep(0.5)
		window = xbmcgui.Window(self.PageId)
		retry = 50
		while retry > 0:
			try:
				time.sleep(0.01)
				retry -= 1
				window.getControl(1).setLabel(self.title(title))
				window.getControl(5).setText('[CR]' + message)
				break
			except: pass
		return window

	@classmethod
	def pageVisible(self):
		return self.dialogVisible(self.PageId)

	# Creates an information dialog.
	# Either a list of item categories, or a list of items.
	#	[
	#		{'title' : 'Category 1', 'items' : [{'title' : 'Name 1', 'value' : 'Value 1', 'link' : True}, {'title' : 'Name 2', 'value' : 'Value 2'}]}
	#		{'title' : 'Category 2', 'items' : [{'title' : 'Name 3', 'value' : 'Value 3', 'link' : False}, {'title' : 'Name 4', 'value' : 'Value 4'}]}
	#	]
	@classmethod
	def information(self, items, title = None):
		if items == None or len(items) == 0:
			return False

		def decorate(item):
			value = item['value'] if 'value' in item else None
			label = self.__translate(item['title']) if 'title' in item else ''
			if value == None:
				label = Format.font(label, bold = True, uppercase = True)
			else:
				if not label == '':
					if not value == None:
						label += ': '
					label = Format.font(label, bold = True)
				if not value == None:
					label += Format.font(self.__translate(item['value']), italic = ('link' in item and item['link']))
			return label

		result = []
		for item in items:
			if 'items' in item:
				if not len(result) == 0:
					result.append('')
				result.append(decorate(item))
				for i in item['items']:
					result.append(decorate(i))
			else:
				result.append(decorate(item))

		return self.select(result, title = title)

	@classmethod
	def __translate(self, string):
		return Translation.string(string)

	@classmethod
	def title(self, extension = None, bold = True, titleless = False):
		title = '' if titleless else tools.System.name().encode('utf-8')
		if not extension == None:
			if not titleless:
				title += Format.divider()
			title += self.__translate(extension)
		if bold:
			title = Format.fontBold(title)
		return title

class Splash(xbmcgui.WindowDialog):

	# Types
	TypeFull = 'full'
	TypeMini = 'mini'
	TypeName = 'name'
	TypeIcon = 'icon'
	TypeAbout = 'about'
	TypeMessage = 'message'
	TypeDonations = 'donations'

	# Actions
	ActionSelectItem = 7
	ActionPreviousMenu = 10
	ActionNavigationBack = 92
	ActionMoveRight = 2
	ActionMoveLeft = 1
	ActionsCancel = [ActionPreviousMenu, ActionNavigationBack, ActionMoveRight]
	ActionsMaximum = 100 # Mouse other unwanted actions.

	# Duration
	Duration = 2000

	# Size
	SizeLarge = 'large'
	SizeMedium = 'medium'
	SizeSmall = 'small'

	# Format
	FormatWhite = '0xFFFFFFFF'
	FormatCenter = 0x00000002 | 0x00000004

	def __init__(self, type, message = None, donation = None):
		Loader.show()

		from resources.lib.extensions import debrid
		self.mType = type
		self.mSplash = None
		self.mWidth = 1920 # Due to setCoordinateResolution
		self.mHeight = 1080 # Due to setCoordinateResolution

		self.mButtonPremiumize = None
		self.mButtonRealDebrid = None
		self.mButtonEasyNews = None
		self.mButtonFreeHosters = None
		self.mButtonCoinBase = None
		self.mButtonExodus = None
		self.mButtonClose = None

		try:
			self.setCoordinateResolution(0)

			if type == self.TypeMini:
				widthTotal, heightTotal = self.__window(False, True)
			elif type == self.TypeName:
				width = 505
				height = 256
				x = self.__centerX(width)
				y = self.__centerY(height)
				self.addControl(xbmcgui.ControlImage(x, y, width, height, self.__name(True)))
			elif type == self.TypeIcon:
				width = 512
				height = 512
				x = self.__centerX(width)
				y = self.__centerY(height)
				self.addControl(xbmcgui.ControlImage(x, y, width, height, self.__icon(True, self.SizeLarge)))
			elif type == self.TypeFull:
				widthTotal, heightTotal = self.__window(True, True)

				width = widthTotal - 220
				height = 150
				x = self.__centerX(widthTotal) + 110
				y = self.__centerY(heightTotal) + 300
				label = 'Gaia is optimized for the premium services ' + Format.fontBold('Premiumize') + ', ' + Format.fontBold('OffCloud') + ', ' + Format.fontBold('RealDebrid') + ', and ' + Format.fontBold('EasyNews') + ' to facilitate additional, faster, and higher quality streams. Purchase an account by clicking the buttons below and support the addon development at the same time.'
				self.__textbox(x, y, width, height, label)

				# PREMIUMIZE
				self.mButtonPremiumize = self.__button(
					buttonLabel = '        Premiumize',
					buttonX = self.__centerX(widthTotal) + 110,
					buttonY = self.__centerY(heightTotal) + 460,
					buttonWidth = 230,
					buttonHeight = 70,

					iconPath = Icon.path('premiumize.png', type = Icon.ThemeIcon),
					iconX = self.__centerX(widthTotal) + 115,
					iconY = self.__centerY(heightTotal) + 460,
					iconWidth = 70,
					iconHeight = 70,

					infoLabel = 'Torrents | Usenet | Hosters',
					infoX = self.__centerX(widthTotal) + 110,
					infoY = self.__centerY(heightTotal) + 540,
					infoWidth = 230,
					infoHeight = 20
				)

				# REALDEBRID
				self.mButtonRealDebrid = self.__button(
					buttonLabel = '       OffCloud',
					buttonX = self.__centerX(widthTotal) + 360,
					buttonY = self.__centerY(heightTotal) + 460,
					buttonWidth = 230,
					buttonHeight = 70,

					iconPath = Icon.path('realdebrid.png', type = Icon.ThemeIcon),
					iconX = self.__centerX(widthTotal) + 365,
					iconY = self.__centerY(heightTotal) + 460,
					iconWidth = 70,
					iconHeight = 70,

					infoLabel = 'Torrents | Usenet | Hosters',
					infoX = self.__centerX(widthTotal) + 360,
					infoY = self.__centerY(heightTotal) + 540,
					infoWidth = 230,
					infoHeight = 20
				)

				# REALDEBRID
				self.mButtonRealDebrid = self.__button(
					buttonLabel = '       RealDebrid',
					buttonX = self.__centerX(widthTotal) + 610,
					buttonY = self.__centerY(heightTotal) + 460,
					buttonWidth = 230,
					buttonHeight = 70,

					iconPath = Icon.path('realdebrid.png', type = Icon.ThemeIcon),
					iconX = self.__centerX(widthTotal) + 615,
					iconY = self.__centerY(heightTotal) + 460,
					iconWidth = 70,
					iconHeight = 70,

					infoLabel = 'Torrents | Hosters',
					infoX = self.__centerX(widthTotal) + 610,
					infoY = self.__centerY(heightTotal) + 540,
					infoWidth = 230,
					infoHeight = 20
				)

				# EASYNEWS
				self.mButtonEasyNews = self.__button(
					buttonLabel = '       EasyNews',
					buttonX = self.__centerX(widthTotal) + 860,
					buttonY = self.__centerY(heightTotal) + 460,
					buttonWidth = 230,
					buttonHeight = 70,

					iconPath = Icon.path('easynews.png', type = Icon.ThemeIcon),
					iconX = self.__centerX(widthTotal) + 865,
					iconY = self.__centerY(heightTotal) + 460,
					iconWidth = 70,
					iconHeight = 70,

					infoLabel = 'Usenet',
					infoX = self.__centerX(widthTotal) + 860,
					infoY = self.__centerY(heightTotal) + 540,
					infoWidth = 230,
					infoHeight = 20
				)

				# FREE HOSTERS
				self.mButtonFreeHosters = self.__button(
					buttonLabel = '       Free Hosters',
					buttonX = self.__centerX(widthTotal) + 475,
					buttonY = self.__centerY(heightTotal) + 580,
					buttonWidth = 250,
					buttonHeight = 70,

					iconPath = Icon.path('networks.png', type = Icon.ThemeIcon),
					iconX = self.__centerX(widthTotal) + 480,
					iconY = self.__centerY(heightTotal) + 580,
					iconWidth = 70,
					iconHeight = 70,

					infoLabel = 'Free Access | Fewer Streams | Lower Quality',
					infoX = self.__centerX(widthTotal) + 110,
					infoY = self.__centerY(heightTotal) + 660,
					infoWidth = 980,
					infoHeight = 20
				)

			elif type == self.TypeAbout:
				widthTotal, heightTotal = self.__window(True, True)

				width = widthTotal
				height = heightTotal
				x = self.__centerX(widthTotal)
				y = self.__centerY(heightTotal) - 40
				label = Format.fontBold(Translation.string(33359) + ' ' + tools.System.version())
				label += Format.newline() + Format.fontBold(tools.Settings.getString('link.website', raw = True))
				self.addControl(xbmcgui.ControlLabel(x, y, width, height, label, textColor = self.FormatWhite, alignment = self.FormatCenter))

				width = widthTotal - 220
				height = 200
				x = self.__centerX(widthTotal) + 110
				y = self.__centerY(heightTotal) + 380
				label = tools.System.disclaimer()
				self.__textbox(x, y, width, height, label)

				self.mButtonClose = self.__button(
					buttonLabel = '       Close',
					buttonX = self.__centerX(widthTotal) + 500,
					buttonY = self.__centerY(heightTotal) + 600,
					buttonWidth = 200,
					buttonHeight = 70,

					iconPath = Icon.path('error.png', type = Icon.ThemeIcon),
					iconX = self.__centerX(widthTotal) + 505,
					iconY = self.__centerY(heightTotal) + 600,
					iconWidth = 70,
					iconHeight = 70,
				)

			elif type == self.TypeMessage:
				widthTotal, heightTotal = self.__window(True, True)

				width = widthTotal - 220
				height = 280
				x = self.__centerX(widthTotal) + 110
				y = self.__centerY(heightTotal) + 300
				self.__textbox(x, y, width, height, message)

				self.mButtonClose = self.__button(
					buttonLabel = '       Close',
					buttonX = self.__centerX(widthTotal) + 500,
					buttonY = self.__centerY(heightTotal) + 600,
					buttonWidth = 200,
					buttonHeight = 70,

					iconPath = Icon.path('error.png', type = Icon.ThemeIcon),
					iconX = self.__centerX(widthTotal) + 505,
					iconY = self.__centerY(heightTotal) + 600,
					iconWidth = 70,
					iconHeight = 70,
				)

			elif type == self.TypeDonations:
				try:
					try:
						donationIdentifier = donation['identifier']
						donationAddress = donation['address']
						donationQrcode = 'https://api.qrserver.com/v1/create-qr-code/?size=300x300&bgcolor=FFFFFF&color=000000&data=%s' % donationAddress
						donationAddressLabel = Translation.string(33507) + ': ' + donationAddress
					except:
						donationIdentifier = 'other'
						donationAddress = tools.Settings.getString('link.donation', raw = True)
						donationQrcode = ''
						donationAddressLabel = Translation.string(33915) + ': ' + donationAddress

					from resources.lib.extensions import clipboard
					clipboard.Clipboard.copy(donationAddress)

					widthTotal, heightTotal = self.__window(True, True)

					width = 250
					height = 250
					x = self.__centerX(widthTotal) + 140
					y = self.__centerY(heightTotal) + 300
					self.addControl(xbmcgui.ControlImage(x, y, width, height, Icon.path('donations' + donationIdentifier, special = Icon.SpecialDonations, quality = Icon.QualityLarge)))

					width = 190
					height = 190
					x = self.__centerX(widthTotal) + 170
					y = self.__centerY(heightTotal) + 330
					self.addControl(xbmcgui.ControlImage(x, y, width, height, donationQrcode))

					width = 650
					height = 200
					x = self.__centerX(widthTotal) + 390
					y = self.__centerY(heightTotal) + 320
					label = Translation.string(33506)
					self.__textbox(x, y, width, height, label)

					width = widthTotal
					height = 50
					x = self.__centerX(widthTotal)
					y = self.__centerY(heightTotal) + 535
					wallet = xbmcgui.ControlFadeLabel(x, y, width, height, 'font15', self.FormatWhite, self.FormatCenter) # Do not use named parameters, since it causes crashes.
					self.addControl(wallet)
					wallet.addLabel(Format.font(donationAddressLabel, bold = True))

					# COINBASE
					self.mButtonCoinBase = self.__button(
						buttonLabel = '       CoinBase',
						buttonX = self.__centerX(widthTotal) + 170,
						buttonY = self.__centerY(heightTotal) + 600,
						buttonWidth = 250,
						buttonHeight = 70,

						iconPath = Icon.path('coinbase.png', type = Icon.ThemeIcon),
						iconX = self.__centerX(widthTotal) + 175,
						iconY = self.__centerY(heightTotal) + 600,
						iconWidth = 70,
						iconHeight = 70,
					)

					# EXODUS
					self.mButtonExodus = self.__button(
						buttonLabel = '       Exodus',
						buttonX = self.__centerX(widthTotal) + 475,
						buttonY = self.__centerY(heightTotal) + 600,
						buttonWidth = 250,
						buttonHeight = 70,

						iconPath = Icon.path('exodus.png', type = Icon.ThemeIcon),
						iconX = self.__centerX(widthTotal) + 480,
						iconY = self.__centerY(heightTotal) + 600,
						iconWidth = 70,
						iconHeight = 70,
					)

					# CLOSE
					self.mButtonClose = self.__button(
						buttonLabel = '       Close',
						buttonX = self.__centerX(widthTotal) + 780,
						buttonY = self.__centerY(heightTotal) + 600,
						buttonWidth = 250,
						buttonHeight = 70,

						iconPath = Icon.path('error.png', type = Icon.ThemeIcon),
						iconX = self.__centerX(widthTotal) + 785,
						iconY = self.__centerY(heightTotal) + 600,
						iconWidth = 70,
						iconHeight = 70,
					)
				except:
					tools.Logger.error()
					tools.System.openLink(tools.Settings.getString('link.donation', raw = True))
		except:
			pass
		Loader.hide()

	def __theme(self):
		theme = tools.Settings.getString('interface.theme.skin').lower()
		theme = theme.replace(' ', '').lower()
		index = theme.find('(')
		if index >= 0: theme = theme[:index]
		return theme

	def __logo(self, size = SizeMedium):
		return os.path.join(tools.System.pathResources(), 'resources', 'media', 'logo', size)

	def __name(self, force = False, size = SizeMedium):
		theme = self.__theme()
		return os.path.join(self.__logo(size), 'namecolor.png' if force or theme == 'default' or 'gaia' in theme  else 'nameglass.png')

	def __icon(self, force = False, size = SizeMedium):
		theme = self.__theme()
		return os.path.join(self.__logo(size), 'iconcolor.png' if force or theme == 'default' or 'gaia' in theme else 'iconglass.png')

	def __splash(self):
		return os.path.join(tools.System.pathResources(), 'resources', 'media', 'splash')

	def __skin(self):
		theme = self.__theme()
		addon = tools.System.pathResources() if theme == 'default' or 'gaia' in theme else tools.System.pathSkins()
		return os.path.join(addon, 'resources', 'media', 'skins', theme)

	def __window(self, full = True, logo = True):
		if full:
			name = 'windowfull.png'
			width = 1200
			height = 750
			logoWidth = 350
			logoHeight = 177
			logoX = 425
			logoY = 100
		else:
			name = 'windowmini.png'
			width = 700
			height = 420
			logoWidth = 493
			logoHeight = 250
			logoX = 103
			logoY = 85

		x = self.__centerX(width)
		y = self.__centerY(height)

		path = os.path.join(self.__skin(), 'splash', name)
		if tools.File.exists(path):
			self.addControl(xbmcgui.ControlImage(x, y, width, height, path))

		path = os.path.join(self.__splash(), name)
		self.addControl(xbmcgui.ControlImage(x, y, width, height, path))

		if logo:
			logoX = self.__centerX(width) + logoX
			logoY = self.__centerY(height) + logoY
			path = self.__name()
			self.addControl(xbmcgui.ControlImage(logoX, logoY, logoWidth, logoHeight, path))

		return (width, height)

	def __button(self, buttonLabel, buttonX, buttonY, buttonWidth, buttonHeight, iconPath = None, iconX = None, iconY = None, iconWidth = None, iconHeight = None, infoLabel = None, infoX = None, infoY = None, infoWidth = None, infoHeight = None):
		pathNormal = os.path.join(self.__skin(), 'splash', 'buttonnormal.png')
		if not tools.File.exists(pathNormal):
			pathNormal = os.path.join(self.__splash(), 'buttonnormal.png')

		pathFocus = os.path.join(self.__skin(), 'splash', 'buttonfocus.png')
		if not tools.File.exists(pathFocus):
			pathFocus = os.path.join(self.__splash(), 'buttonfocus.png')

		buttonLabel = Format.fontBold(buttonLabel)
		self.addControl(xbmcgui.ControlButton(buttonX, buttonY, buttonWidth, buttonHeight, buttonLabel, focusTexture = pathFocus, noFocusTexture = pathNormal, alignment = self.FormatCenter, textColor = self.FormatWhite, font = 'font12'))

		if not iconPath == None:
			self.addControl(xbmcgui.ControlImage(iconX, iconY, iconWidth, iconHeight, iconPath))

		if not infoLabel == None:
			# Do not use named parameters, since it causes a crash.
			info = xbmcgui.ControlFadeLabel(infoX, infoY, infoWidth, infoHeight, 'font10', self.FormatWhite, self.FormatCenter)
			self.addControl(info)
			info.addLabel(infoLabel)

		return (buttonX, buttonY)

	def __textbox(self, x, y, width, height, label, delay = 3000, time = 4000, repeat = True):
		box = xbmcgui.ControlTextBox(x, y, width, height, textColor = self.FormatWhite, font = 'font12')
		self.addControl(box)
		box.autoScroll(delay, time, repeat)
		box.setText(label)

	def __centerX(self, width):
		return int((self.mWidth - width) / 2)

	def __centerY(self, height):
		return int((self.mHeight - height) / 2)

	def __referalPremiumize(self):
		from resources.lib.extensions import debrid
		debrid.Premiumize.website(open = True)
		self.close()

	def __referalRealDebrid(self):
		from resources.lib.extensions import debrid
		debrid.RealDebrid.website(open = True)
		self.close()

	def __referalEasyNews(self):
		from resources.lib.extensions import debrid
		debrid.EasyNews.website(open = True)
		self.close()

	def __referalCoinBase(self):
		tools.Donations.coinbase(openLink = True)
		self.close()

	def __referalExodus(self):
		tools.Donations.exodus(openLink = True)
		self.close()

	def __continue(self):
		if self.mType == self.TypeFull:
			tools.System.openLink(tools.Settings.getString('link.website', raw = True), popup = False, front = False)
		self.close()

	def onControl(self, control):
		distances = []
		actions = []
		if self.mButtonPremiumize:
			distances.append(abs(control.getX() - self.mButtonPremiumize[0]) + abs(control.getY() - self.mButtonPremiumize[1]))
			actions.append(self.__referalPremiumize)
		if self.mButtonRealDebrid:
			distances.append(abs(control.getX() - self.mButtonRealDebrid[0]) + abs(control.getY() - self.mButtonRealDebrid[1]))
			actions.append(self.__referalRealDebrid)
		if self.mButtonEasyNews:
			distances.append(abs(control.getX() - self.mButtonEasyNews[0]) + abs(control.getY() - self.mButtonEasyNews[1]))
			actions.append(self.__referalEasyNews)
		if self.mButtonFreeHosters:
			distances.append(abs(control.getX() - self.mButtonFreeHosters[0]) + abs(control.getY() - self.mButtonFreeHosters[1]))
			actions.append(self.__continue)
		if self.mButtonCoinBase:
			distances.append(abs(control.getX() - self.mButtonCoinBase[0]) + abs(control.getY() - self.mButtonCoinBase[1]))
			actions.append(self.__referalCoinBase)
		if self.mButtonExodus:
			distances.append(abs(control.getX() - self.mButtonExodus[0]) + abs(control.getY() - self.mButtonExodus[1]))
			actions.append(self.__referalExodus)
		if self.mButtonClose:
			distances.append(abs(control.getX() - self.mButtonClose[0]) + abs(control.getY() - self.mButtonClose[1]))
			actions.append(self.__continue)

		smallestIndex = -1
		smallestDistance = 999999
		for i in range(len(distances)):
			if distances[i] < smallestDistance:
				smallestDistance = distances[i]
				smallestIndex = i

		if smallestIndex < 0:
			self.__continue()
		else:
			actions[smallestIndex]()

	def onAction(self, action):
		action = action.getId()
		if action < self.ActionsMaximum:
			if self.mButtonClose == None:
				if action in self.ActionsCancel or self.mType == self.TypeFull:
					self.__continue()
				else:
					tools.System.openLink(tools.Settings.getString('link.website', raw = True))
			else:
				self.__continue()

	@classmethod
	def popup(self, time = Duration, wait = True):
		try:
			from resources.lib.extensions import debrid

			versionCurrent = tools.System.version()
			version = tools.Settings.getString('general.launch.splash.previous')
			tools.Settings.set('general.launch.splash.previous', versionCurrent)

			# Popup on every minor version update, if and only if the user has now premium account already.
			special = False
			'''special = not versionCurrent == version and versionCurrent.endswith('.0')
			special = special and not debrid.Premiumize().accountValid()
			special = special and not debrid.OffCloud().accountValid()
			special = special and not debrid.RealDebrid().accountValid()
			special = special and not debrid.EasyNews().accountValid()'''

			if version == None or version == '' or special:
				self.popupFull(wait = wait)
				return True
			else:
				# Do not wait on the mini splashes.
				type = tools.Settings.getInteger('general.launch.splash.type')
				if type == 1: self.popupIcon(time = time)
				elif type == 2: self.popupName(time = time)
				elif type == 3: self.popupMini(time = time)
				elif type == 4: self.popupFull(wait = wait)
				else: return False
				return True
		except:
			pass
		return False

	@classmethod
	def popupFull(self, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = workers.Thread(self.__popupFull)
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def popupMini(self, time = Duration, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = workers.Thread(self.__popupMini, time)
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def popupName(self, time = Duration, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = workers.Thread(self.__popupName, time)
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def popupIcon(self, time = Duration, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = workers.Thread(self.__popupIcon, time)
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def popupAbout(self, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = workers.Thread(self.__popupAbout)
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def popupMessage(self, message, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = workers.Thread(self.__popupMessage, message)
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def popupDonations(self, donation = None, wait = False):
		try:
			# So that the interface can load in the background while the splash loads.
			thread = workers.Thread(self.__popupDonations, donation)
			thread.start()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def __popupFull(self):
		try:
			self.mSplash = Splash(self.TypeFull)
			self.mSplash.doModal()
			if wait: thread.join()
		except:
			pass

	@classmethod
	def __popupMini(self, time = Duration):
		try:
			self.mSplash = Splash(self.TypeMini)
			self.mSplash.show()
			tools.System.sleep(time)
			self.mSplash.close()
		except:
			pass

	@classmethod
	def __popupName(self, time = Duration):
		try:
			self.mSplash = Splash(self.TypeName)
			self.mSplash.show()
			tools.System.sleep(time)
			self.mSplash.close()
		except:
			pass

	@classmethod
	def __popupIcon(self, time = Duration):
		try:
			self.mSplash = Splash(self.TypeIcon)
			self.mSplash.show()
			tools.System.sleep(time)
			self.mSplash.close()
		except:
			pass

	@classmethod
	def __popupAbout(self):
		try:
			self.mSplash = Splash(self.TypeAbout)
			self.mSplash.doModal()
		except:
			pass

	@classmethod
	def __popupMessage(self, message):
		try:
			self.mSplash = Splash(self.TypeMessage, message = message)
			self.mSplash.doModal()
		except:
			pass

	@classmethod
	def __popupDonations(self, donation = None):
		try:
			self.mSplash = Splash(self.TypeDonations, donation = donation)
			self.mSplash.doModal()
		except:
			pass

# Spinner loading bar
class Loader(object):

	@classmethod
	def show(self):
		xbmc.executebuiltin('ActivateWindow(busydialog)')

	@classmethod
	def hide(self):
		xbmc.executebuiltin('Dialog.Close(busydialog)')

	@classmethod
	def visible(self):
		return xbmc.getCondVisibility('Window.IsActive(busydialog)') == 1

# Kodi Directory Interface
class Directory(object):

	ContentAddons = 'addons'
	ContentFiles = 'files'
	ContentSongs = 'songs'
	ContentArtists = 'artists'
	ContentAlbums = 'albums'
	ContentMovies = 'movies'
	ContentShows = 'tvshows'
	ContentEpisodes = 'episodes'
	ContentMusicVideos = 'musicvideos'

	def __init__(self, content = ContentAddons, cache = True):
		self.mContent = content
		self.mHandle = tools.System.handle()
		self.mCache = cache

	# context = [{'label', 'action', 'parameters'}]
	# Optional 'command' parameter to specify a custom command instead of construction one from action and parameters.
	def add(self, label, action = None, parameters = None, context = [], folder = False, icon = None, iconDefault = None, iconSpecial = None, fanart = None):
		link = tools.System.pluginCommand(action = action, parameters = parameters, run = False)
		item = xbmcgui.ListItem(label = Translation.string(label))

		if len(context) > 0:
			contextMenu = []
			for c in context:
				contextLabel = Translation.string(c['label'])
				if 'command' in c:
					command = c['command']
				else:
					contextAction = c['action'] if 'action' in c else None
					contextParameters = c['parameters'] if 'parameters' in c else None
					command = tools.System.pluginCommand(action = contextAction, parameters = contextParameters)
				contextMenu.append((contextLabel, command))
			item.addContextMenuItems(contextMenu)

		iconIcon, iconThumb, iconPoster, iconBanner = Icon.pathAll(icon = icon, default = iconDefault, special = iconSpecial)
		item.setArt({'icon': iconIcon, 'thumb': iconThumb, 'poster': iconPoster, 'banner': iconBanner})

		if fanart == None:
			from resources.lib.modules import control
			fanart = control.addonFanart()
		item.setProperty('Fanart_Image', fanart)

		xbmcplugin.addDirectoryItem(handle = self.mHandle, url = link, listitem = item, isFolder = folder)

	def finish(self):
		xbmcplugin.setContent(self.mHandle, self.mContent)
		xbmcplugin.endOfDirectory(self.mHandle, cacheToDisc = self.mCache)

	# Clear: Clear the path history.
	@classmethod
	def refresh(self, clear = False):
		tools.System.execute('Container.Refresh')
		if clear: tools.System.execute('Container.Update(path,replace)')


class Legal(object):

	ChoiceLeft = True
	ChoiceRight = False

	@classmethod
	def _option(self, message, left, right):
		return Dialog.option(title = 35109, message = message, labelConfirm = left, labelDeny = right)

	@classmethod
	def _message(self, message):
		return Dialog.confirm(title = 35109, message = message)

	@classmethod
	def launchInitial(self, exit = True):
		if not tools.Settings.getBoolean('internal.disclaimer.initialzed'):
			if self.show(exit = exit,short = True):
				tools.Settings.set('internal.disclaimer.initialzed', True)
				return True
			else:
				return False
		return True

	@classmethod
	def show(self, exit = True, short = False):
		if short:
			message = Translation.string(35111) + Format.newline() + Translation.string(35112) + Format.newline() + Translation.string(35113)
			choice = self._option(message = message, left = 35116, right = 35115)
		else:
			while True:
				choice = self._option(message = 35111, left = 33743, right = 33821)
				if choice == self.ChoiceLeft: self._message(message = 35114)
				else: break
			while True:
				choice = self._option(message = 35112, left = 33743, right = 33821)
				if choice == self.ChoiceLeft: self._message(message = 35114)
				else: break
			choice = self._option(message = 35113, left = 35116, right = 35115)
		if choice == self.ChoiceLeft:
			tools.Settings.set('internal.disclaimer.initialzed', False)
			tools.System.launchUninitialize()
			tools.System.exit()
			return False
		else:
			return True


class Player(xbmc.Player):

	def __init__ (self):
		xbmc.Player.__init__(self)

	def __del__(self):
		try: xbmc.Player.__del__(self)
		except: pass

	@classmethod
	def playNow(self, link):
		Player().play(link)
