# -*- coding: UTF-8 -*-
#######################################################################
 # ----------------------------------------------------------------------------
 # "THE BEER-WARE LICENSE" (Revision 42):
 # @Daddy_Blamo wrote this file.  As long as you retain this notice you
 # can do whatever you want with this stuff. If we meet some day, and you think
 # this stuff is worth it, you can buy me a beer in return. - Muad'Dib
 # ----------------------------------------------------------------------------
#######################################################################

# Addon Name: Wraith
# Addon id: script.extendedinfo
# Addon Provider: Mr.Blamo


import os
import sys
import urllib
import urlparse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

lang = xbmcaddon.Addon().getLocalizedString

setting = xbmcaddon.Addon().getSetting

setSetting = xbmcaddon.Addon().setSetting

addon = xbmcaddon.Addon

addonInfo = xbmcaddon.Addon().getAddonInfo

infoLabel = xbmc.getInfoLabel

jsonrpc = xbmc.executeJSONRPC

dialog = xbmcgui.Dialog()

progressDialog = xbmcgui.DialogProgress()

keyboard = xbmc.Keyboard

execute = xbmc.executebuiltin

def infoDialog(message, heading=addonInfo('name'), icon='', time=3000, sound=False):
    #if icon == '': icon = addonIcon()
    if icon == '': icon = xbmcgui.NOTIFICATION_INFO
    elif icon == 'INFO': icon = xbmcgui.NOTIFICATION_INFO
    elif icon == 'WARNING': icon = xbmcgui.NOTIFICATION_WARNING
    elif icon == 'ERROR': icon = xbmcgui.NOTIFICATION_ERROR
    dialog.notification(heading, message, icon, time, sound=sound)

def yesnoDialog(line1, line2, line3, heading=addonInfo('name'), nolabel='', yeslabel=''):
    return dialog.yesno(heading, line1, line2, line3, nolabel, yeslabel)

def selectDialog(list, heading=addonInfo('name')):
    return dialog.select(heading, list)

def openSettings(query=None, id=addonInfo('id')):
    try:
        idle()
        execute('Addon.OpenSettings(%s)' % id)
        if query == None: raise Exception()
        c, f = query.split('.')
        execute('SetFocus(%i)' % (int(c) + 100))
        execute('SetFocus(%i)' % (int(f) + 200))
    except:
        return

def idle():
    return execute('Dialog.Close(busydialog)')
