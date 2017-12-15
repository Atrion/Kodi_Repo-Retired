# -*- coding: utf-8 -*-
# Advanced Emulator Launcher asset (artwork) related stuff
#

# Copyright (c) 2016-2017 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# --- Python standard library ---
from __future__ import unicode_literals
import os

# --- AEL packages ---
from utils import *
from utils_kodi import *

# --- Define "constants" ---
ASSET_ICON       = 100
ASSET_FANART     = 200
ASSET_BANNER     = 300
ASSET_POSTER     = 400
ASSET_CLEARLOGO  = 500
ASSET_CONTROLLER = 600
ASSET_TRAILER    = 700
ASSET_TITLE      = 800
ASSET_SNAP       = 900
ASSET_BOXFRONT   = 1000
ASSET_BOXBACK    = 1100
ASSET_CARTRIDGE  = 1200
ASSET_FLYER      = 1300  # ROMs have FLYER, Categories/Launchers/Collections have POSTER
ASSET_MAP        = 1400
ASSET_MANUAL     = 1500

#
# The order of this list must match order in dialog.select() in the GUI, or bad things will happen.
#
CATEGORY_ASSET_LIST = [
    ASSET_ICON, ASSET_FANART, ASSET_BANNER, ASSET_POSTER, ASSET_CLEARLOGO, ASSET_TRAILER
]

LAUNCHER_ASSET_LIST = [
    ASSET_ICON, ASSET_FANART, ASSET_BANNER, ASSET_POSTER, ASSET_CLEARLOGO, ASSET_CONTROLLER, ASSET_TRAILER
]

ROM_ASSET_LIST = [
    ASSET_TITLE,     ASSET_SNAP,   ASSET_BOXFRONT, ASSET_BOXBACK,
    ASSET_CARTRIDGE, ASSET_FANART, ASSET_BANNER,   ASSET_CLEARLOGO,  
    ASSET_FLYER,     ASSET_MAP,    ASSET_MANUAL,   ASSET_TRAILER
]

# --- Plugin will search these file extensions for assets ---
# >> Check http://kodi.wiki/view/advancedsettings.xml#videoextensions
IMAGE_EXTENSIONS   = ['png', 'jpg', 'gif', 'bmp']
MANUAL_EXTENSIONS  = ['pdf']
TRAILER_EXTENSIONS = ['mov', 'divx', 'xvid', 'wmv', 'avi', 'mpg', 'mpeg', 'mp4', 'mkv', 'avc']

#
# Get extensions to search for files
# Input : ['png', 'jpg']
# Output: ['png', 'jpg', 'PNG', 'JPG']
#
def asset_get_filesearch_extension_list(exts):
    ext_list = list(exts)
    for ext in exts:
        ext_list.append(ext.upper())

    return ext_list

#
# Gets extensions to be used in Kodi file dialog.
# Input : ['png', 'jpg']
# Output: '.png|.jpg'
#
def asset_get_dialog_extension_list(exts):
    ext_string = ''
    for ext in exts:
        ext_string += '.' + ext + '|'
    # >> Remove trailing '|' character
    ext_string = ext_string[:-1]

    return ext_string

#
# Gets extensions to be used in regular expressions.
# Input : ['png', 'jpg']
# Output: '(png|jpg)'
#
def asset_get_regexp_extension_list(exts):
    ext_string = ''
    for ext in exts:
        ext_string += ext + '|'
    # >> Remove trailing '|' character
    ext_string = ext_string[:-1]

    return '(' + ext_string + ')'

# -------------------------------------------------------------------------------------------------
# Asset functions
# -------------------------------------------------------------------------------------------------
# Creates path for assets (artwork) and automatically fills in the path_ fields in the launcher
# struct.
# 
def assets_init_asset_dir(assets_path_FName, launcher):
    log_verb('assets_init_asset_dir() asset_path "{0}"'.format(assets_path_FName.getPath()))

    # --- Fill in launcher fields and create asset directories ---
    if launcher['platform'] == 'MAME':
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_title', 'titles')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_snap', 'snaps')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_boxfront', 'cabinets')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_boxback', 'cpanels')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_cartridge', 'PCBs')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_fanart', 'fanarts')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_banner', 'marquees')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_clearlogo', 'clearlogos')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_flyer', 'flyers')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_map', 'maps')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_manual', 'manuals')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_trailer', 'trailers')
    else:
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_title', 'titles')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_snap', 'snaps')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_boxfront', 'boxfronts')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_boxback', 'boxbacks')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_cartridge', 'cartridges')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_fanart', 'fanarts')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_banner', 'banners')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_clearlogo', 'clearlogos')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_flyer', 'flyers')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_map', 'maps')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_manual', 'manuals')
        assets_parse_asset_dir(launcher, assets_path_FName, 'path_trailer', 'trailers')

#
# Create asset path and assign it to Launcher dictionary.
#
def assets_parse_asset_dir(launcher, assets_path_FName, key, pathName):
    subPath       = assets_path_FName.pjoin(pathName)
    launcher[key] = subPath.getOriginalPath()
    log_debug('assets_parse_asset_dir() Creating dir "{0}"'.format(subPath.getPath()))
    subPath.makedirs()

#
# Get artwork user configured to be used as thumb/fanart/... for Categories/Launchers
#
def asset_get_default_asset_Category(object_dic, object_key, default_asset = ''):
    conf_asset_key = object_dic[object_key]
    thumb_path     = object_dic[conf_asset_key] if object_dic[conf_asset_key] else default_asset

    return thumb_path

#
# Same for ROMs
#
def asset_get_default_asset_Launcher_ROM(rom, launcher, object_key, default_asset = ''):
    conf_asset_key = launcher[object_key]
    thumb_path     = rom[conf_asset_key] if rom[conf_asset_key] else default_asset

    return thumb_path

#
# Gets a human readable name string for the asset field name.
#
def assets_get_asset_name_str(default_asset):
    asset_name_str = ''

    # >> ROMs
    if   default_asset == 's_title':     asset_name_str = 'Title'
    elif default_asset == 's_snap':      asset_name_str = 'Snap'
    elif default_asset == 's_boxfront':  asset_name_str = 'Boxfront'
    elif default_asset == 's_boxback':   asset_name_str = 'Boxback'
    elif default_asset == 's_cartridge': asset_name_str = 'Cartridge'
    elif default_asset == 's_fanart':    asset_name_str = 'Fanart'
    elif default_asset == 's_banner':    asset_name_str = 'Banner'
    elif default_asset == 's_clearlogo': asset_name_str = 'Clearlogo'
    elif default_asset == 's_flyer':     asset_name_str = 'Flyer'
    elif default_asset == 's_map':       asset_name_str = 'Map'
    elif default_asset == 's_manual':    asset_name_str = 'Manual'
    elif default_asset == 's_trailer':   asset_name_str = 'Trailer'
    # >> Categories/Launchers
    elif default_asset == 's_icon':       asset_name_str = 'Icon'
    elif default_asset == 's_poster':     asset_name_str = 'Poster'
    elif default_asset == 's_controller': asset_name_str = 'Controller'
    else:
        kodi_notify_warn('Wrong asset key {0}'.format(default_asset))
        log_error('assets_get_asset_name_str() Wrong default_thumb {0}'.format(default_asset))
    
    return asset_name_str

#
# Used in Category context menu, "Choose defaul Assets/Artwork ..."
# Order here must match order in list Category_asset_ListItem_list
#
def assets_choose_category_artwork(dict_object, key, index):
    if   index == 0: dict_object[key] = 's_icon'
    elif index == 1: dict_object[key] = 's_fanart'
    elif index == 2: dict_object[key] = 's_banner'
    elif index == 3: dict_object[key] = 's_poster'
    elif index == 4: dict_object[key] = 's_clearlogo'

#
# Used in Launcher context menu, "Choose defaul Assets/Artwork ..."
# Order here must match order in list Launcher_asset_ListItem_list
#
def assets_choose_launcher_artwork(dict_object, key, index):
    if   index == 0: dict_object[key] = 's_icon'
    elif index == 1: dict_object[key] = 's_fanart'
    elif index == 2: dict_object[key] = 's_banner'
    elif index == 3: dict_object[key] = 's_poster'
    elif index == 4: dict_object[key] = 's_clearlogo'
    elif index == 5: dict_object[key] = 's_controller'

def assets_choose_category_ROM(dict_object, key, index):
    if   index == 0: dict_object[key] = 's_title'
    elif index == 1: dict_object[key] = 's_snap'
    elif index == 5: dict_object[key] = 's_boxfront'
    elif index == 6: dict_object[key] = 's_boxback'
    elif index == 7: dict_object[key] = 's_cartridge'
    elif index == 2: dict_object[key] = 's_fanart'
    elif index == 3: dict_object[key] = 's_banner'
    elif index == 4: dict_object[key] = 's_clearlogo'
    elif index == 8: dict_object[key] = 's_flyer'
    elif index == 9: dict_object[key] = 's_map'

# -------------------------------------------------------------------------------------------------
# Gets all required information about an asset: path, name, etc.
# Returns an object with all the information
# -------------------------------------------------------------------------------------------------
class AssetInfo:
    kind        = 0
    key         = ''
    name        = ''
    fname_infix = '' # Used only when searching assets when importing XML
    kind_str    = ''
    exts        = []
    exts_dialog = []
    path_key    = ''

def assets_get_info_scheme(asset_kind):
    A = AssetInfo()

    if asset_kind == ASSET_ICON:
        A.kind        = ASSET_ICON
        A.key         = 's_icon'
        A.name        = 'Icon'
        A.fname_infix = 'icon'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_icon'
    elif asset_kind == ASSET_FANART:
        A.kind        = ASSET_FANART
        A.key         = 's_fanart'
        A.name        = 'Fanart'
        A.fname_infix = 'fanart'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_fanart'
    elif asset_kind == ASSET_BANNER:
        A.kind        = ASSET_BANNER
        A.key         = 's_banner'
        A.name        = 'Banner'
        A.fname_infix = 'banner'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_banner'
    elif asset_kind == ASSET_POSTER:
        A.kind        = ASSET_POSTER
        A.key         = 's_poster'
        A.name        = 'Poster'
        A.fname_infix = 'poster'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_poster'
    elif asset_kind == ASSET_CLEARLOGO:
        A.kind        = ASSET_CLEARLOGO
        A.key         = 's_clearlogo'
        A.name        = 'Clearlogo'
        A.fname_infix = 'clearlogo'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_clearlogo'
    elif asset_kind == ASSET_CONTROLLER:
        A.kind        = ASSET_CONTROLLER
        A.key         = 's_controller'
        A.name        = 'Controller'
        A.fname_infix = 'controller'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_controller'
    elif asset_kind == ASSET_TRAILER:
        A.kind        = ASSET_TRAILER
        A.key         = 's_trailer'
        A.name        = 'Trailer'
        A.fname_infix = 'trailer'
        A.kind_str    = 'video'
        A.exts        = asset_get_filesearch_extension_list(TRAILER_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(TRAILER_EXTENSIONS)
        A.path_key    = 'path_trailer'
    elif asset_kind == ASSET_TITLE:
        A.kind        = ASSET_TITLE
        A.key         = 's_title'
        A.name        = 'Title'
        A.fname_infix = 'title'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_title'
    elif asset_kind == ASSET_SNAP:
        A.kind        = ASSET_SNAP
        A.key         = 's_snap'
        A.name        = 'Snap'
        A.fname_infix = 'snap'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_snap'
    elif asset_kind == ASSET_BOXFRONT:
        A.kind        = ASSET_BOXFRONT
        A.key         = 's_boxfront'
        A.name        = 'Boxfront'
        A.fname_infix = 'boxfront'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_boxfront'
    elif asset_kind == ASSET_BOXBACK:
        A.kind        = ASSET_BOXBACK
        A.key         = 's_boxback'
        A.name        = 'Boxback'
        A.fname_infix = 'boxback'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_boxback'
    elif asset_kind == ASSET_CARTRIDGE:
        A.kind        = ASSET_CARTRIDGE
        A.key         = 's_cartridge'
        A.name        = 'Cartridge'
        A.fname_infix = 'cartridge'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_cartridge'
    elif asset_kind == ASSET_FLYER:
        A.kind        = ASSET_FLYER
        A.key         = 's_flyer'
        A.name        = 'Flyer'
        A.fname_infix = 'flyer'
        A.kind_str    = 'image'
        A.fname_infix = 'poster'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_flyer'
    elif asset_kind == ASSET_MAP:
        A.kind        = ASSET_MAP
        A.key         = 's_map'
        A.name        = 'Map'
        A.fname_infix = 'map'
        A.kind_str    = 'image'
        A.exts        = asset_get_filesearch_extension_list(IMAGE_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(IMAGE_EXTENSIONS)
        A.path_key    = 'path_map'
    elif asset_kind == ASSET_MANUAL:
        A.kind        = ASSET_MANUAL
        A.key         = 's_manual'
        A.name        = 'Manual'
        A.fname_infix = 'manual'
        A.kind_str    = 'manual'
        A.exts        = asset_get_filesearch_extension_list(MANUAL_EXTENSIONS)
        A.exts_dialog = asset_get_dialog_extension_list(MANUAL_EXTENSIONS)
        A.path_key    = 'path_manual'
    else:
        log_error('assets_get_info_scheme() Wrong asset_kind = {0}'.format(asset_kind))

    # --- Ultra DEBUG ---
    # log_debug('assets_get_info_scheme() asset_kind    {0}'.format(asset_kind))
    # log_debug('assets_get_info_scheme() A.key         {0}'.format(A.key))
    # log_debug('assets_get_info_scheme() A.name        {0}'.format(A.name))
    # log_debug('assets_get_info_scheme() A.fname_infix {0}'.format(A.fname_infix))
    # log_debug('assets_get_info_scheme() A.kind_str    {0}'.format(A.kind_str))
    # log_debug('assets_get_info_scheme() A.exts        {0}'.format(A.exts))
    # log_debug('assets_get_info_scheme() A.exts_dialog {0}'.format(A.exts_dialog))
    # log_debug('assets_get_info_scheme() A.path_key    {0}'.format(A.path_key))

    return A

#
# Scheme DIR uses different directories for artwork and no sufixes.
#
# Assets    -> Assets info object
# AssetPath -> FileName object
# ROM       -> ROM name FileName object
#
# Returns a FileName object
#
def assets_get_path_noext_DIR(Asset, AssetPath, ROM):

    return AssetPath + ROM.getBase_noext()

#
# Scheme SUFIX uses suffixes for artwork. All artwork assets are stored in the same directory.
# Name example: "Sonic The Hedgehog (Europe)_a3e_title"
# First 3 characters of the objectID are added to avoid overwriting of images. For example, in the
# Favourites special category there could be ROMs with the same name for different systems.
#
# Assets    -> Assets info object
# AssetPath -> FileName object
# asset_base_noext -> Unicode string
# objectID -> Object MD5 ID fingerprint (Unicode string)
#
# Returns a FileName object
#
def assets_get_path_noext_SUFIX(Asset, AssetPath, asset_base_noext, objectID = '000'):
    # >> Returns asset/artwork path_noext
    asset_path_noext_FileName = FileName('')
    objectID_str = '_' + objectID[0:3]

    if   Asset.kind == ASSET_ICON:       asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_icon')
    elif Asset.kind == ASSET_FANART:     asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_fanart')
    elif Asset.kind == ASSET_BANNER:     asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_banner')
    elif Asset.kind == ASSET_POSTER:     asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_poster')
    elif Asset.kind == ASSET_CLEARLOGO:  asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_clearlogo')
    elif Asset.kind == ASSET_CONTROLLER: asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_controller')
    elif Asset.kind == ASSET_TRAILER:    asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_trailer')
    elif Asset.kind == ASSET_TITLE:      asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_title')
    elif Asset.kind == ASSET_SNAP:       asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_snap')
    elif Asset.kind == ASSET_BOXFRONT:   asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_boxfront')
    elif Asset.kind == ASSET_BOXBACK:    asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_boxback')
    elif Asset.kind == ASSET_CARTRIDGE:  asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_cartridge')
    elif Asset.kind == ASSET_FLYER:      asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_flyer')
    elif Asset.kind == ASSET_MAP:        asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_map')
    elif Asset.kind == ASSET_MANUAL:     asset_path_noext_FileName = AssetPath.pjoin(asset_base_noext + objectID_str + '_manual')
    else:
        log_error('assets_get_path_noext_SUFIX() Wrong asset kind = {0}'.format(Asset.kind))

    return asset_path_noext_FileName

#
# Get a list of enabled assets.
#
# Returns tuple:
# configured_bool_list    List of boolean values. It has all assets defined in ROM_ASSET_LIST
# unconfigured_name_list  List of disabled asset names
#
def asset_get_configured_dir_list(launcher):
    configured_bool_list   = [False] * len(ROM_ASSET_LIST)
    unconfigured_name_list = []

    # >> Check if asset paths are configured or not
    for i, asset in enumerate(ROM_ASSET_LIST):
        A = assets_get_info_scheme(asset)
        configured_bool_list[i] = True if launcher[A.path_key] else False
        if not configured_bool_list[i]: 
            unconfigured_name_list.append(A.name)
            log_verb('asset_get_enabled_asset_list() {0:<9} path unconfigured'.format(A.name))
        else:
            log_debug('asset_get_enabled_asset_list() {0:<9} path configured'.format(A.name))

    return (configured_bool_list, unconfigured_name_list)

#
# Get a list of assets with duplicated paths. Refuse to do anything if duplicated paths found.
#
def asset_get_duplicated_dir_list(launcher):
    duplicated_bool_list   = [False] * len(ROM_ASSET_LIST)
    duplicated_name_list   = []

    # >> Check for duplicated asset paths
    for i, asset_i in enumerate(ROM_ASSET_LIST[:-1]):
        A_i = assets_get_info_scheme(asset_i)
        for j, asset_j in enumerate(ROM_ASSET_LIST[i+1:]):
            A_j = assets_get_info_scheme(asset_j)
            # >> Exclude unconfigured assets (empty strings).
            if not launcher[A_i.path_key] or not launcher[A_j.path_key]: continue
            # log_debug('asset_get_duplicated_asset_list() Checking {0:<9} vs {1:<9}'.format(A_i.name, A_j.name))
            if launcher[A_i.path_key] == launcher[A_j.path_key]:
                duplicated_bool_list[i] = True
                duplicated_name_list.append('{0} and {1}'.format(A_i.name, A_j.name))
                log_info('asset_get_duplicated_asset_list() DUPLICATED {0} and {1}'.format(A_i.name, A_j.name))

    return duplicated_name_list

#
# Search for local assets and place found files into a list. List all has assets as defined 
# in ROM_ASSET_LIST.
#
# launcher               -> launcher dictionary
# ROMFile                -> FileName object
# enabled_ROM_asset_list -> list of booleans
#
def assets_search_local_cached_assets(launcher, ROMFile, enabled_ROM_asset_list):
    log_verb('assets_search_local_cached_assets() Searching for ROM local assets...')
    local_asset_list = [''] * len(ROM_ASSET_LIST)
    rom_basename_noext = ROMFile.getBase_noext()
    for i, asset_kind in enumerate(ROM_ASSET_LIST):
        AInfo = assets_get_info_scheme(asset_kind)
        if not enabled_ROM_asset_list[i]:
            log_verb('assets_search_local_cached_assets() Disabled {0:<9}'.format(AInfo.name))
            continue
        local_asset = misc_search_file_cache(launcher[AInfo.path_key], rom_basename_noext, AInfo.exts)

        if local_asset:
            local_asset_list[i] = local_asset.getOriginalPath()
            log_verb('assets_search_local_cached_assets() Found    {0:<9} "{1}"'.format(AInfo.name, local_asset_list[i]))
        else:
            local_asset_list[i] = ''
            log_verb('assets_search_local_cached_assets() Missing  {0:<9}'.format(AInfo.name))

    return local_asset_list

#
# A) This function checks if all path_* share a common root directory. If so
#    this function returns that common directory as an Unicode string.
# B) If path_* do not share a common root directory this function returns ''.
#
def assets_get_ROM_asset_path(launcher):
    ROM_asset_path = ''
    duplicated_bool_list = [False] * len(ROM_ASSET_LIST)
    AInfo_first = assets_get_info_scheme(ROM_ASSET_LIST[0])
    path_first_asset_FN = FileName(launcher[AInfo_first.path_key])
    log_debug('assets_get_ROM_asset_path() path_first_asset OP  "{0}"'.format(path_first_asset_FN.getOriginalPath()))
    log_debug('assets_get_ROM_asset_path() path_first_asset Dir "{0}"'.format(path_first_asset_FN.getDir()))
    for i, asset_kind in enumerate(ROM_ASSET_LIST):
        AInfo = assets_get_info_scheme(asset_kind)
        current_path_FN = FileName(launcher[AInfo.path_key])
        if current_path_FN.getDir() == path_first_asset_FN.getDir():
            duplicated_bool_list[i] = True

    return path_first_asset_FN.getDir() if all(duplicated_bool_list) else ''
