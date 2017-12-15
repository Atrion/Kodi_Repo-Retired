# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher main script file
#

# Copyright (c) 2016-2017 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2010-2015 Angelscry
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
import sys, os, shutil, fnmatch, string, time, traceback
import re, urllib, urllib2, urlparse, socket, exceptions, hashlib
from collections import OrderedDict

# --- Kodi stuff ---
import xbmc, xbmcgui, xbmcplugin, xbmcaddon

# --- Modules/packages in this plugin ---
from constants import *
from utils import *
from utils_kodi import *
from disk_IO import *
from net_IO import *
from assets import *
from rom_audit import *
from scrap import *
from autoconfig import *

# --- Addon object (used to access settings) ---
__addon_obj__     = xbmcaddon.Addon()
__addon_id__      = __addon_obj__.getAddonInfo('id').decode('utf-8')
__addon_name__    = __addon_obj__.getAddonInfo('name').decode('utf-8')
__addon_version__ = __addon_obj__.getAddonInfo('version').decode('utf-8')
__addon_author__  = __addon_obj__.getAddonInfo('author').decode('utf-8')
__addon_profile__ = __addon_obj__.getAddonInfo('profile').decode('utf-8')
__addon_type__    = __addon_obj__.getAddonInfo('type').decode('utf-8')

# --- Addon paths and constant definition ---
# _FILE_PATH is a filename
# _DIR is a directory (with trailing /)
ADDONS_DATA_DIR           = FileName('special://profile/addon_data')
PLUGIN_DATA_DIR           = ADDONS_DATA_DIR.pjoin(__addon_id__)
BASE_DIR                  = FileName('special://profile')
HOME_DIR                  = FileName('special://home')
KODI_FAV_FILE_PATH        = FileName('special://profile/favourites.xml')
ADDONS_DIR                = HOME_DIR.pjoin('addons')
CURRENT_ADDON_DIR         = ADDONS_DIR.pjoin(__addon_id__)
ICON_IMG_FILE_PATH        = CURRENT_ADDON_DIR.pjoin('icon.png')
CATEGORIES_FILE_PATH      = PLUGIN_DATA_DIR.pjoin('categories.xml')
FAV_JSON_FILE_PATH        = PLUGIN_DATA_DIR.pjoin('favourites.json')
COLLECTIONS_FILE_PATH     = PLUGIN_DATA_DIR.pjoin('collections.xml')
VCAT_TITLE_FILE_PATH      = PLUGIN_DATA_DIR.pjoin('vcat_title.xml')
VCAT_YEARS_FILE_PATH      = PLUGIN_DATA_DIR.pjoin('vcat_years.xml')
VCAT_GENRE_FILE_PATH      = PLUGIN_DATA_DIR.pjoin('vcat_genre.xml')
VCAT_DEVELOPER_FILE_PATH  = PLUGIN_DATA_DIR.pjoin('vcat_developers.xml')
VCAT_NPLAYERS_FILE_PATH   = PLUGIN_DATA_DIR.pjoin('vcat_nplayers.xml')
VCAT_ESRB_FILE_PATH       = PLUGIN_DATA_DIR.pjoin('vcat_esrb.xml')
VCAT_RATING_FILE_PATH     = PLUGIN_DATA_DIR.pjoin('vcat_rating.xml')
VCAT_CATEGORY_FILE_PATH   = PLUGIN_DATA_DIR.pjoin('vcat_category.xml')
LAUNCH_LOG_FILE_PATH      = PLUGIN_DATA_DIR.pjoin('launcher.log')
RECENT_PLAYED_FILE_PATH   = PLUGIN_DATA_DIR.pjoin('history.json')
MOST_PLAYED_FILE_PATH     = PLUGIN_DATA_DIR.pjoin('most_played.json')
GAMEDB_INFO_DIR           = CURRENT_ADDON_DIR.pjoin('GameDBInfo')
GAMEDB_JSON_BASE_NOEXT    = 'GameDB_info'
LAUNCHBOX_INFO_DIR        = CURRENT_ADDON_DIR.pjoin('LaunchBox')
LAUNCHBOX_JSON_BASE_NOEXT = 'LaunchBox_info'
BIOS_REPORT_FILE_PATH     = PLUGIN_DATA_DIR.pjoin('report_BIOS.txt')
LAUNCHER_REPORT_FILE_PATH = PLUGIN_DATA_DIR.pjoin('report_Launchers.txt')

# --- Artwork and NFO for Categories and Launchers ---
DEFAULT_CAT_ASSET_DIR     = PLUGIN_DATA_DIR.pjoin('asset-categories')
DEFAULT_COL_ASSET_DIR     = PLUGIN_DATA_DIR.pjoin('asset-collections')
DEFAULT_LAUN_ASSET_DIR    = PLUGIN_DATA_DIR.pjoin('asset-launchers')
DEFAULT_FAV_ASSET_DIR     = PLUGIN_DATA_DIR.pjoin('asset-favourites')
VIRTUAL_CAT_TITLE_DIR     = PLUGIN_DATA_DIR.pjoin('db_title')
VIRTUAL_CAT_YEARS_DIR     = PLUGIN_DATA_DIR.pjoin('db_year')
VIRTUAL_CAT_GENRE_DIR     = PLUGIN_DATA_DIR.pjoin('db_genre')
VIRTUAL_CAT_DEVELOPER_DIR = PLUGIN_DATA_DIR.pjoin('db_developer')
VIRTUAL_CAT_NPLAYERS_DIR  = PLUGIN_DATA_DIR.pjoin('db_nplayer')
VIRTUAL_CAT_ESRB_DIR      = PLUGIN_DATA_DIR.pjoin('db_esrb')
VIRTUAL_CAT_RATING_DIR    = PLUGIN_DATA_DIR.pjoin('db_rating')
VIRTUAL_CAT_CATEGORY_DIR  = PLUGIN_DATA_DIR.pjoin('db_category')
ROMS_DIR                  = PLUGIN_DATA_DIR.pjoin('db_ROMs')
COLLECTIONS_DIR           = PLUGIN_DATA_DIR.pjoin('db_Collections')
REPORTS_DIR               = PLUGIN_DATA_DIR.pjoin('reports')

#
# Make AEL to run only 1 single instance
# See http://forum.kodi.tv/showthread.php?tid=310697
#
monitor           = xbmc.Monitor()
main_window       = xbmcgui.Window(10000)
AEL_LOCK_PROPNAME = 'AEL_instance_lock'
AEL_LOCK_VALUE    = 'True'

class SingleInstance:
    def __enter__(self):
        # --- If property is True then another instance of AEL is running ---
        if main_window.getProperty(AEL_LOCK_PROPNAME) == AEL_LOCK_VALUE:
            log_warning('SingleInstance::__enter__() Lock in use. Aborting AEL execution')
            # >> Apparently this message pulls the focus out of the launcher app. Disable it.
            # >> Has not effect. Kodi steals the focus from the launched app even if not message.
            kodi_dialog_OK('Another instance of AEL is running! Wait until the scraper finishes '
                           'or close the launched application before launching a new one and try '
                           'again.')
            raise SystemExit
        if monitor.abortRequested(): 
            log_info('monitor.abortRequested() is True. Exiting plugin ...')
            raise SystemExit

        # --- Acquire lock for this instance ---
        log_debug('SingleInstance::__enter__() Lock not in use. Setting lock')
        main_window.setProperty(AEL_LOCK_PROPNAME, AEL_LOCK_VALUE)
        return True

    def __exit__(self, type, value, traceback):
        # --- Print information about exception if any ---
        # >> If type == value == tracebak == None no exception happened
        if type:
            log_error('SingleInstance::__exit__() Unhandled excepcion in protected code')

        # --- Release lock even if an exception happened ---
        log_debug('SingleInstance::__exit__() Releasing lock')
        main_window.setProperty(AEL_LOCK_PROPNAME, '')

#
# Main code
#
class Main:
    # ---------------------------------------------------------------------------------------------
    # This is the plugin entry point.
    # ---------------------------------------------------------------------------------------------
    def run_plugin(self):
        # --- Initialise log system ---
        # >> Force DEBUG log level for development.
        # >> Place it before settings loading so settings can be dumped during debugging.
        # set_log_level(LOG_DEBUG)

        # --- Fill in settings dictionary using __addon_obj__.getSetting() ---
        self._get_settings()
        set_log_level(self.settings['log_level'])

        # --- Some debug stuff for development ---
        log_debug('---------- Called AEL Main::run_plugin() constructor ----------')
        log_debug('sys.platform   "{0}"'.format(sys.platform))
        # log_debug('WindowId       "{0}"'.format(xbmcgui.getCurrentWindowId()))
        # log_debug('WindowName     "{0}"'.format(xbmc.getInfoLabel('Window.Property(xmlfile)')))
        log_debug('Python version "' + sys.version.replace('\n', '') + '"')
        # log_debug('__a_name__     "{0}"'.format(__addon_name__))
        # log_debug('__a_id__       "{0}"'.format(__addon_id__))
        log_debug('__a_version__  "{0}"'.format(__addon_version__))
        # log_debug('__a_author__   "{0}"'.format(__addon_author__))
        # log_debug('__a_profile__  "{0}"'.format(__addon_profile__))
        # log_debug('__a_type__     "{0}"'.format(__addon_type__))
        for i in range(len(sys.argv)): log_debug('sys.argv[{0}] "{1}"'.format(i, sys.argv[i]))
        # log_debug('PLUGIN_DATA_DIR OP "{0}"'.format(PLUGIN_DATA_DIR.getOriginalPath()))
        # log_debug('PLUGIN_DATA_DIR  P "{0}"'.format(PLUGIN_DATA_DIR.getPath()))
        # log_debug('CURRENT_ADDON_DIR OP "{0}"'.format(CURRENT_ADDON_DIR.getOriginalPath()))
        # log_debug('CURRENT_ADDON_DIR  P "{0}"'.format(CURRENT_ADDON_DIR.getPath()))

        # --- Get DEBUG information for the log --
        if self.settings['log_level'] == LOG_DEBUG:
            json_rpc_start = time.time()

            # >> Properties: Kodi name and version
            c_str = ('{"id" : 1, "jsonrpc" : "2.0",'
                     ' "method" : "Application.GetProperties",'
                     ' "params" : {"properties" : ["name", "version"]} }')
            response = xbmc.executeJSONRPC(c_str)
            log_debug('JSON      ''{0}'''.format(c_str))
            log_debug('Response  ''{0}'''.format(response))

            # >> Skin in use
            c_str = ('{"id" : 1, "jsonrpc" : "2.0",'
                     ' "method" : "Settings.GetSettingValue",'
                     ' "params" : {"setting" : "lookandfeel.skin"} }')
            response = xbmc.executeJSONRPC(c_str)
            log_debug('JSON      ''{0}'''.format(c_str))
            log_debug('Response  ''{0}'''.format(response))
            
            # >> Print time of JSON RPC
            json_rpc_end = time.time()
            log_debug('JSON RPC time {0:.3f} ms'.format((json_rpc_end - json_rpc_start) * 1000))

            # --- Save all settings into a file dor DEBUG ---
            # c_str = ('{"id" : 1, "jsonrpc" : "2.0",'
            #          ' "method" : "Settings.GetSettings",'
            #          ' "params" : {"level":"expert"}}')
            # response = xbmc.executeJSONRPC(c_str)
            # log_debug('JSON      ''{0}'''.format(c_str))
            # log_debug('Response  ''{0}'''.format(response.decode('utf-8')))

        # --- Addon data paths creation ---
        if not PLUGIN_DATA_DIR.exists():           PLUGIN_DATA_DIR.makedirs()
        if not DEFAULT_CAT_ASSET_DIR.exists():     DEFAULT_CAT_ASSET_DIR.makedirs()
        if not DEFAULT_COL_ASSET_DIR.exists():     DEFAULT_COL_ASSET_DIR.makedirs()
        if not DEFAULT_LAUN_ASSET_DIR.exists():    DEFAULT_LAUN_ASSET_DIR.makedirs()
        if not DEFAULT_FAV_ASSET_DIR.exists():     DEFAULT_FAV_ASSET_DIR.makedirs()
        if not VIRTUAL_CAT_TITLE_DIR.exists():     VIRTUAL_CAT_TITLE_DIR.makedirs()
        if not VIRTUAL_CAT_YEARS_DIR.exists():     VIRTUAL_CAT_YEARS_DIR.makedirs()
        if not VIRTUAL_CAT_GENRE_DIR.exists():     VIRTUAL_CAT_GENRE_DIR.makedirs()
        if not VIRTUAL_CAT_DEVELOPER_DIR.exists(): VIRTUAL_CAT_DEVELOPER_DIR.makedirs()
        if not VIRTUAL_CAT_NPLAYERS_DIR.exists():  VIRTUAL_CAT_NPLAYERS_DIR.makedirs()
        if not VIRTUAL_CAT_ESRB_DIR.exists():      VIRTUAL_CAT_ESRB_DIR.makedirs()
        if not VIRTUAL_CAT_RATING_DIR.exists():    VIRTUAL_CAT_RATING_DIR.makedirs()
        if not VIRTUAL_CAT_CATEGORY_DIR.exists():  VIRTUAL_CAT_CATEGORY_DIR.makedirs()
        if not ROMS_DIR.exists():                  ROMS_DIR.makedirs()
        if not COLLECTIONS_DIR.exists():           COLLECTIONS_DIR.makedirs()
        if not REPORTS_DIR.exists():               REPORTS_DIR.makedirs()

        # --- Process URL ---
        self.base_url     = sys.argv[0]
        self.addon_handle = int(sys.argv[1])
        args              = urlparse.parse_qs(sys.argv[2][1:])
        # log_debug('args = {0}'.format(args))
        # >> Interestingly, if plugin is called as type executable then args is empty.
        # >> However, if plugin is called as type video then Kodi adds the following
        # >> even for the first call: 'content_type': ['video']
        self.content_type = args['content_type'] if 'content_type' in args else None
        # log_debug('content_type = {0}'.format(self.content_type))

        # --- Addon first-time initialisation ---
        # >> When the addon is installed and the file categories.xml does not exist, just
        #    create an empty one with a default launcher.
        # >> NOTE Not needed anymore. Skins using shortcuts and/or widgets will call AEL concurrently
        #         and AEL should return an empty list with no GUI warnings or dialogs.
        # if not CATEGORIES_FILE_PATH.exists():
        #     kodi_dialog_OK('It looks it is the first time you run Advanced Emulator Launcher! ' +
        #                    'A default categories.xml has been created. You can now customise it to your needs.')
        #     self._cat_create_default()
        #     fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # --- Load categories.xml and fill categories and launchers dictionaries ---
        self.categories = {}
        self.launchers = {}
        self.update_timestamp = fs_load_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # --- Get addon command ---
        command = args['com'][0] if 'com' in args else 'SHOW_ADDON_ROOT'
        log_debug('command = "{0}"'.format(command))

        # --- Commands that do not modify the databases are allowed to run concurrently ---
        if command == 'SHOW_ADDON_ROOT' or \
           command == 'SHOW_VCATEGORIES_ROOT' or \
           command == 'SHOW_AEL_OFFLINE_LAUNCHERS_ROOT' or command == 'SHOW_LB_OFFLINE_LAUNCHERS_ROOT' or \
           command == 'SHOW_FAVOURITES' or command == 'SHOW_VIRTUAL_CATEGORY' or \
           command == 'SHOW_RECENTLY_PLAYED' or command == 'SHOW_MOST_PLAYED' or \
           command == 'SHOW_COLLECTIONS' or command == 'SHOW_COLLECTION_ROMS' or \
           command == 'SHOW_LAUNCHERS' or command == 'SHOW_ROMS' or \
           command == 'SHOW_VLAUNCHER_ROMS' or \
           command == 'SHOW_AEL_SCRAPER_ROMS' or command == 'SHOW_LB_SCRAPER_ROMS' or \
           command == 'EXEC_SHOW_CLONE_ROMS' or command == 'SHOW_CLONE_ROMS' or \
           command == 'SHOW_ALL_CATEGORIES' or \
           command == 'SHOW_ALL_LAUNCHERS' or \
           command == 'SHOW_ALL_ROMS' or \
           command == 'BUILD_GAMES_MENU':
            self.run_concurrent(command, args)
        else:
            # >> Ensure AEL only runs one instance at a time
            with SingleInstance():
                self.run_protected(command, args)
        log_debug('Advanced Emulator Launcher run_plugin() exit')

    #
    # This function may run concurrently
    #
    def run_concurrent(self, command, args):
        log_debug('Advanced Emulator Launcher run_concurrent() BEGIN')
        
        # --- Name says it all ---
        if command == 'SHOW_ADDON_ROOT':
            self._command_render_categories()

        # --- Render launchers stuff ---
        elif command == 'SHOW_VCATEGORIES_ROOT':
            self._gui_render_vcategories_root()
        elif command == 'SHOW_AEL_OFFLINE_LAUNCHERS_ROOT':
            self._gui_render_AEL_scraper_launchers()
        elif command == 'SHOW_LB_OFFLINE_LAUNCHERS_ROOT':
            self._gui_render_LB_scraper_launchers()
        elif command == 'SHOW_FAVOURITES':
            self._command_render_favourites()
        elif command == 'SHOW_VIRTUAL_CATEGORY':
            self._command_render_virtual_category(args['catID'][0])
        elif command == 'SHOW_RECENTLY_PLAYED':
            self._command_render_recently_played()
        elif command == 'SHOW_MOST_PLAYED':
            self._command_render_most_played()
        elif command == 'SHOW_COLLECTIONS':
            self._command_render_collections()
        elif command == 'SHOW_COLLECTION_ROMS':
            self._command_render_collection_ROMs(args['catID'][0], args['launID'][0])
        elif command == 'SHOW_LAUNCHERS':
            self._command_render_launchers(args['catID'][0])

        # --- Show ROMs in launcher/virtual launcher ---
        elif command == 'SHOW_ROMS':
            self._command_render_roms(args['catID'][0], args['launID'][0])
        elif command == 'SHOW_VLAUNCHER_ROMS':
            self._command_render_virtual_launcher_roms(args['catID'][0], args['launID'][0])
        elif command == 'SHOW_AEL_SCRAPER_ROMS':
            self._command_render_AEL_scraper_roms(args['catID'][0])
        elif command == 'SHOW_LB_SCRAPER_ROMS':
            self._command_render_LB_scraper_roms(args['catID'][0])
        # >> Auxiliar command to render clone ROM list from context menu in 1G1R mode
        elif command == 'EXEC_SHOW_CLONE_ROMS':
            url = self._misc_url('SHOW_CLONE_ROMS', args['catID'][0], args['launID'][0], args['romID'][0])
            xbmc.executebuiltin('Container.Update({0})'.format(url))
        elif command == 'SHOW_CLONE_ROMS':
            self._command_render_clone_roms(args['catID'][0], args['launID'][0], args['romID'][0])

        # --- Skin commands ---
        # >> This commands render Categories/Launcher/ROMs and are used by skins to build shortcuts.
        # >> Do not render virtual launchers.
        elif command == 'SHOW_ALL_CATEGORIES':
            self._command_render_all_categories()
        elif command == 'SHOW_ALL_LAUNCHERS':
            self._command_render_all_launchers()
        elif command == 'SHOW_ALL_ROMS':
            self._command_render_all_ROMs()

        # >> Command to build/fill the menu with categories or launcher using skinshortcuts
        elif command == 'BUILD_GAMES_MENU':
            self._command_buildMenu()

        # >> Unknown command
        else:
            kodi_dialog_OK('Unknown command {0}'.format(args['com'][0]) )
        log_debug('Advanced Emulator Launcher run_concurrent() END')

    #
    # This function is guaranteed to run with no concurrency.
    #
    def run_protected(self, command, args):
        log_debug('Advanced Emulator Launcher run_protected() BEGIN')

        # --- Category management ---
        if command == 'ADD_CATEGORY':
            self._command_add_new_category()
        elif command == 'EDIT_CATEGORY':
            self._command_edit_category(args['catID'][0])

        # --- Launcher management ---
        elif command == 'ADD_LAUNCHER':
            self._command_add_new_launcher(args['catID'][0])
        elif command == 'ADD_LAUNCHER_ROOT':
            self._command_add_new_launcher(VCATEGORY_ADDONROOT_ID)
        elif command == 'EDIT_LAUNCHER':
            self._command_edit_launcher(args['catID'][0], args['launID'][0])

        # --- ROM management ---
        # >> Add/Edit/Delete ROMs in launcher, Favourites or ROM Collections <<
        elif command == 'ADD_ROMS':
            self._command_add_roms(args['launID'][0])
        elif command == 'EDIT_ROM':
            self._command_edit_rom(args['catID'][0], args['launID'][0], args['romID'][0])

        # --- Launch ROM or standalone launcher ---
        elif command == 'LAUNCH_ROM':
            self._command_run_rom(args['catID'][0], args['launID'][0], args['romID'][0])
        elif command == 'LAUNCH_STANDALONE':
            self._command_run_standalone_launcher(args['catID'][0], args['launID'][0])

        # --- Favourite/ROM Collection management ---
        elif command == 'ADD_TO_FAV':
            self._command_add_to_favourites(args['catID'][0], args['launID'][0], args['romID'][0])
        elif command == 'ADD_TO_COLLECTION':
            self._command_add_ROM_to_collection(args['catID'][0], args['launID'][0], args['romID'][0])
        elif command == 'ADD_COLLECTION':
            self._command_add_collection()
        elif command == 'EDIT_COLLECTION':
            self._command_edit_collection(args['catID'][0], args['launID'][0])
        elif command == 'DELETE_COLLECTION':
            self._command_delete_collection(args['catID'][0], args['launID'][0])
        elif command == 'IMPORT_COLLECTION':
            self._command_import_collection()
        elif command == 'EXPORT_COLLECTION':
            self._command_export_collection(args['catID'][0], args['launID'][0])
        elif command == 'MANAGE_FAV':
            self._command_manage_favourites(args['catID'][0], args['launID'][0], args['romID'][0])

        # --- Searches ---
        # This command is issued when user clicks on "Search" on the context menu of a launcher
        # in the launchers view, or context menu inside a launcher. User is asked to enter the
        # search string and the field to search (name, category, etc.). Then, EXEC_SEARCH_LAUNCHER
        # command is called.
        elif command == 'SEARCH_LAUNCHER':
            self._command_search_launcher(args['catID'][0], args['launID'][0])
        elif command == 'EXECUTE_SEARCH_LAUNCHER':
            # >> Deal with empty search strings
            if 'search_string' not in args: args['search_string'] = [ '' ]
            self._command_execute_search_launcher(args['catID'][0], args['launID'][0],
                                                  args['search_type'][0], args['search_string'][0])

        # >> Shows info about categories/launchers/ROMs and reports
        elif command == 'VIEW':
            catID  = args['catID'][0]                              # >> Mandatory
            launID = args['launID'][0] if 'launID' in args else '' # >> Optional
            romID  = args['romID'][0]  if 'romID'  in args else '' # >> Optional
            self._command_view_menu(catID, launID, romID)
        elif command == 'VIEW_OS_ROM':
            self._command_view_offline_scraper_rom(args['catID'][0], args['launID'][0], args['romID'][0])

        # >> Update virtual categories databases
        elif command == 'UPDATE_VIRTUAL_CATEGORY':
            self._command_update_virtual_category_db(args['catID'][0])
        elif command == 'UPDATE_ALL_VCATEGORIES':
            self._command_update_virtual_category_db_all()

        # >> Commands called from addon settings window
        elif command == 'IMPORT_LAUNCHERS':    self._command_import_launchers()
        elif command == 'EXPORT_LAUNCHERS':    self._command_export_launchers()
        elif command == 'CHECK_DATABASE':      self._command_check_database()
        elif command == 'CHECK_LAUNCHERS':     self._command_check_launchers()
        elif command == 'CHECK_RETRO_BIOS':    self._command_check_retro_BIOS()
        elif command == 'IMPORT_AL_LAUNCHERS': self._command_import_legacy_AL()

        # >> Unknown command
        else:
            kodi_dialog_OK('Unknown command {0}'.format(args['com'][0]) )
        log_debug('Advanced Emulator Launcher run_protected() END')

    #
    # Get Addon Settings
    #
    def _get_settings(self):
        # Get the users preference settings
        o = __addon_obj__
        self.settings = {}

        # --- ROM Scanner settings ---
        self.settings['scan_recursive']           = True if o.getSetting('scan_recursive') == 'true' else False
        self.settings['scan_ignore_bios']         = True if o.getSetting('scan_ignore_bios') == 'true' else False
        self.settings['scan_update_NFO_files']    = True if o.getSetting('scan_update_NFO_files') == 'true' else False
        self.settings['scan_ignore_scrap_title']  = True if o.getSetting('scan_ignore_scrap_title') == 'true' else False
        self.settings['scan_clean_tags']          = True if o.getSetting('scan_clean_tags') == 'true' else False
        self.settings['scan_metadata_policy']     = int(o.getSetting('scan_metadata_policy'))
        self.settings['scan_asset_policy']        = int(o.getSetting('scan_asset_policy'))
        self.settings['metadata_scraper_mode']    = int(o.getSetting('metadata_scraper_mode'))
        self.settings['asset_scraper_mode']       = int(o.getSetting('asset_scraper_mode'))

        # --- ROM scraping ---
        self.settings['scraper_metadata']       = int(o.getSetting('scraper_metadata'))
        self.settings['scraper_metadata_MAME']  = int(o.getSetting('scraper_metadata_MAME'))

        self.settings['scraper_title']          = int(o.getSetting('scraper_title'))
        self.settings['scraper_snap']           = int(o.getSetting('scraper_snap'))
        self.settings['scraper_boxfront']       = int(o.getSetting('scraper_boxfront'))
        self.settings['scraper_boxback']        = int(o.getSetting('scraper_boxback'))
        self.settings['scraper_cart']           = int(o.getSetting('scraper_cart'))
        self.settings['scraper_fanart']         = int(o.getSetting('scraper_fanart'))
        self.settings['scraper_banner']         = int(o.getSetting('scraper_banner'))
        self.settings['scraper_clearlogo']      = int(o.getSetting('scraper_clearlogo'))

        self.settings['scraper_title_MAME']     = int(o.getSetting('scraper_title_MAME'))
        self.settings['scraper_snap_MAME']      = int(o.getSetting('scraper_snap_MAME'))
        self.settings['scraper_cabinet_MAME']   = int(o.getSetting('scraper_cabinet_MAME'))
        self.settings['scraper_cpanel_MAME']    = int(o.getSetting('scraper_cpanel_MAME'))
        self.settings['scraper_pcb_MAME']       = int(o.getSetting('scraper_pcb_MAME'))
        self.settings['scraper_fanart_MAME']    = int(o.getSetting('scraper_fanart_MAME'))
        self.settings['scraper_marquee_MAME']   = int(o.getSetting('scraper_marquee_MAME'))
        self.settings['scraper_clearlogo_MAME'] = int(o.getSetting('scraper_clearlogo_MAME'))
        self.settings['scraper_flyer_MAME']     = int(o.getSetting('scraper_flyer_MAME'))

        # --- ROM audit ---
        self.settings['audit_unknown_roms']         = int(o.getSetting('audit_unknown_roms'))
        # self.settings['audit_create_pclone_groups'] = True if o.getSetting('audit_create_pclone_groups') == 'true' else False
        self.settings['audit_pclone_assets']        = True if o.getSetting('audit_pclone_assets') == 'true' else False
        # self.settings['audit_1G1R_main_region']     = int(o.getSetting('audit_1G1R_main_region'))
        # self.settings['audit_1G1R_second_region']   = int(o.getSetting('audit_1G1R_second_region'))

        # --- Scrapers ---
        # self.settings['scraper_region']           = int(o.getSetting('scraper_region'))
        # self.settings['scraper_thumb_size']       = int(o.getSetting('scraper_thumb_size'))
        # self.settings['scraper_fanart_size']      = int(o.getSetting('scraper_fanart_size'))
        # self.settings['scraper_image_type']       = int(o.getSetting('scraper_image_type'))
        # self.settings['scraper_fanart_order']     = int(o.getSetting('scraper_fanart_order'))

        # --- Display ---
        self.settings['display_launcher_notify']  = True if o.getSetting('display_launcher_notify') == 'true' else False
        self.settings['display_hide_finished']    = True if o.getSetting('display_hide_finished') == 'true' else False
        self.settings['display_launcher_roms']    = True if o.getSetting('display_launcher_roms') == 'true' else False

        self.settings['display_rom_in_fav']       = True if o.getSetting('display_rom_in_fav') == 'true' else False
        self.settings['display_nointro_stat']     = True if o.getSetting('display_nointro_stat') == 'true' else False
        self.settings['display_fav_status']       = True if o.getSetting('display_fav_status') == 'true' else False

        self.settings['display_hide_favs']        = True if o.getSetting('display_hide_favs') == 'true' else False
        self.settings['display_hide_collections'] = True if o.getSetting('display_hide_collections') == 'true' else False
        self.settings['display_hide_vlaunchers']  = True if o.getSetting('display_hide_vlaunchers') == 'true' else False
        self.settings['display_hide_AEL_scraper'] = True if o.getSetting('display_hide_AEL_scraper') == 'true' else False
        self.settings['display_hide_LB_scraper']  = True if o.getSetting('display_hide_LB_scraper') == 'true' else False
        self.settings['display_hide_recent']      = True if o.getSetting('display_hide_recent') == 'true' else False
        self.settings['display_hide_mostplayed']  = True if o.getSetting('display_hide_mostplayed') == 'true' else False

        # --- Paths ---
        self.settings['categories_asset_dir']     = o.getSetting('categories_asset_dir').decode('utf-8')
        self.settings['launchers_asset_dir']      = o.getSetting('launchers_asset_dir').decode('utf-8')
        self.settings['favourites_asset_dir']     = o.getSetting('favourites_asset_dir').decode('utf-8')
        self.settings['collections_asset_dir']    = o.getSetting('collections_asset_dir').decode('utf-8')

        # --- I/O ---
        self.settings['io_retroarch_only_mandatory'] = True if o.getSetting('io_retroarch_only_mandatory') == 'true' else False
        self.settings['io_retroarch_sys_dir']        = o.getSetting('io_retroarch_sys_dir').decode('utf-8')

        # --- Advanced ---
        self.settings['media_state_action']       = int(o.getSetting('media_state_action'))
        self.settings['delay_tempo']              = int(round(float(o.getSetting('delay_tempo'))))
        self.settings['suspend_audio_engine']     = True if o.getSetting('suspend_audio_engine') == 'true' else False
        # self.settings['suspend_joystick_engine']  = True if o.getSetting('suspend_joystick_engine') == 'true' else False
        self.settings['escape_romfile']           = True if o.getSetting('escape_romfile') == 'true' else False
        self.settings['lirc_state']               = True if o.getSetting('lirc_state') == 'true' else False
        self.settings['show_batch_window']        = True if o.getSetting('show_batch_window') == 'true' else False
        self.settings['windows_close_fds']        = True if o.getSetting('windows_close_fds') == 'true' else False
        self.settings['windows_cd_apppath']       = True if o.getSetting('windows_cd_apppath') == 'true' else False
        self.settings['log_level']                = int(o.getSetting('log_level'))

        # >> Check if user changed default artwork paths for categories/launchers. If not, set defaults.
        if self.settings['categories_asset_dir']  == '': self.settings['categories_asset_dir']  = DEFAULT_CAT_ASSET_DIR.getOriginalPath()
        if self.settings['launchers_asset_dir']   == '': self.settings['launchers_asset_dir']   = DEFAULT_LAUN_ASSET_DIR.getOriginalPath()
        if self.settings['favourites_asset_dir']  == '': self.settings['favourites_asset_dir']  = DEFAULT_FAV_ASSET_DIR.getOriginalPath()
        if self.settings['collections_asset_dir'] == '': self.settings['collections_asset_dir'] = DEFAULT_COL_ASSET_DIR.getOriginalPath()

        # --- Dump settings for DEBUG ---
        # log_debug('Settings dump BEGIN')
        # for key in sorted(self.settings):
        #     log_debug('{0} --> {1:10s} {2}'.format(key.rjust(21), str(self.settings[key]), type(self.settings[key])))
        # log_debug('Settings dump END')

    #
    # Set Sorting methods
    #
    def _misc_set_default_sorting_method(self):
        # >> This must be called only if self.addon_handle > 0, otherwise Kodi will complain in the log.
        if self.addon_handle < 0: return
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)

    def _misc_set_all_sorting_methods(self):
        # >> This must be called only if self.addon_handle > 0, otherwise Kodi will complain in the log.
        if self.addon_handle < 0: return
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_LABEL_IGNORE_FOLDERS)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_VIDEO_YEAR)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_STUDIO)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_GENRE)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)

    #
    # Set the AEL content type. It is a Window property used by skins to know if AEL is rendering
    # a Window that has categories/launchers or ROMs.
    #
    def _misc_set_AEL_Content(self, AEL_Content_Value):
        if AEL_Content_Value == AEL_CONTENT_VALUE_LAUNCHERS:
            log_debug('_misc_set_AEL_Content() Setting Window({0}) '.format(AEL_CONTENT_WINDOW_ID) +
                      'property "{0}" = "{1}"'.format(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_LAUNCHERS))
            xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_LAUNCHERS)
        elif AEL_Content_Value == AEL_CONTENT_VALUE_ROMS:
            log_debug('_misc_set_AEL_Content() Setting Window({0}) '.format(AEL_CONTENT_WINDOW_ID) +
                      'property "{0}" = "{1}"'.format(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROMS))
            xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_ROMS)
        elif AEL_Content_Value == AEL_CONTENT_VALUE_NONE:
            log_debug('_misc_set_AEL_Content() Setting Window({0}) '.format(AEL_CONTENT_WINDOW_ID) +
                      'property "{0}" = "{1}"'.format(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_NONE))
            xbmcgui.Window(AEL_CONTENT_WINDOW_ID).setProperty(AEL_CONTENT_LABEL, AEL_CONTENT_VALUE_NONE)
        else:
            log_error('_misc_set_AEL_Content() Invalid AEL_Content_Value "{0}"'.format(AEL_Content_Value))

    def _command_add_new_category(self):
        dialog = xbmcgui.Dialog()
        keyboard = xbmc.Keyboard('', 'New Category Name')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return

        category = fs_new_category()
        categoryID = misc_generate_random_SID()
        category['id']     = categoryID
        category['m_name'] = keyboard.getText().decode('utf-8')
        self.categories[categoryID] = category
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_notify('Category {0} created'.format(category['m_name']))
        kodi_refresh_container()

    def _command_edit_category(self, categoryID):
        # --- Shows a select box with the options to edit ---
        dialog = xbmcgui.Dialog()
        finished_display = 'Status: Finished' if self.categories[categoryID]['finished'] == True else 'Status: Unfinished'
        type = dialog.select('Select action for category {0}'.format(self.categories[categoryID]['m_name']),
                             ['Edit Metadata ...', 'Edit Assets/Artwork ...', 'Choose default Assets/Artwork ...',
                              finished_display, 'Delete Category'])
        if type < 0: return

        # --- Edit category metadata ---
        if type == 0:
            NFO_FileName = fs_get_category_NFO_name(self.settings, self.categories[categoryID])
            NFO_str = 'NFO found' if NFO_FileName.exists() else 'NFO not found'
            plot_str = text_limit_string(self.categories[categoryID]['m_plot'], DESCRIPTION_MAXSIZE)
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Edit Category Metadata',
                                  ["Edit Title: '{0}'".format(self.categories[categoryID]['m_name']),
                                   "Edit Genre: '{0}'".format(self.categories[categoryID]['m_genre']),
                                   "Edit Rating: '{0}'".format(self.categories[categoryID]['m_rating']),
                                   "Edit Plot: '{0}'".format(plot_str),
                                   'Import NFO file (default, {0})'.format(NFO_str),
                                   'Import NFO file (browse NFO file) ...',
                                   'Save NFO file (default location)'])
            if type2 < 0: return

            # --- Edition of the category name ---
            if type2 == 0:
                keyboard = xbmc.Keyboard(self.categories[categoryID]['m_name'], 'Edit Title')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                title = keyboard.getText().decode('utf-8')
                if title == '': title = self.categories[categoryID]['m_name']
                self.categories[categoryID]['m_name'] = title.rstrip()
                kodi_notify('Changed Category Title')

            # --- Edition of the category genre ---
            elif type2 == 1:
                keyboard = xbmc.Keyboard(self.categories[categoryID]['m_genre'], 'Edit Genre')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.categories[categoryID]['m_genre'] = keyboard.getText().decode('utf-8')
                kodi_notify('Changed Category Genre')

            # --- Edition of the category rating ---
            elif type2 == 2:
                rating = dialog.select('Edit Category Rating',
                                      ['Not set',  'Rating 0', 'Rating 1', 'Rating 2', 'Rating 3', 'Rating 4',
                                       'Rating 5', 'Rating 6', 'Rating 7', 'Rating 8', 'Rating 9', 'Rating 10'])
                # >> Rating not set, empty string
                if rating == 0:
                    self.categories[categoryID]['m_rating'] = ''
                elif rating >= 1 and rating <= 11:
                    self.categories[categoryID]['m_rating'] = '{0}'.format(rating - 1)
                elif rating < 0:
                    kodi_notify('Category rating not changed')
                    return
                kodi_notify('Set Category Rating to {0}'.format(self.categories[categoryID]['m_rating']))

            # --- Edition of the plot (description) ---
            elif type2 == 3:
                keyboard = xbmc.Keyboard(self.categories[categoryID]['m_plot'], 'Edit Plot')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.categories[categoryID]['m_plot'] = keyboard.getText().decode('utf-8')
                kodi_notify('Changed Category Plot')

            # --- Import category metadata from NFO file (automatic) ---
            elif type2 == 4:
                # >> Returns True if changes were made
                NFO_file = fs_get_category_NFO_name(self.settings, self.categories[categoryID])
                if not fs_import_category_NFO(NFO_file, self.categories, categoryID): return
                kodi_notify('Imported Category NFO file {0}'.format(NFO_FileName.getPath()))

            # --- Browse for category NFO file ---
            elif type2 == 5:
                NFO_file = xbmcgui.Dialog().browse(1, 'Select NFO description file', 'files', '.nfo', False, False).decode('utf-8')
                log_debug('_command_edit_category() Dialog().browse returned "{0}"'.format(NFO_file))
                if not NFO_file: return
                NFO_FileName = FileName(NFO_file)
                if not NFO_FileName.exists(): return
                # >> Returns True if changes were made
                if not fs_import_category_NFO(NFO_FileName, self.categories, categoryID): return
                kodi_notify('Imported Category NFO file {0}'.format(NFO_FileName.getPath()))

            # --- Export category metadata to NFO file ---
            elif type2 == 6:
                NFO_FileName = fs_get_category_NFO_name(self.settings, self.categories[categoryID])
                # >> Returns False if exception happened. If an Exception happened function notifies
                # >> user, so display nothing to not overwrite error notification.
                if not fs_export_category_NFO(NFO_FileName, self.categories[categoryID]): return
                # >> No need to save categories/launchers
                kodi_notify('Exported Category NFO file {0}'.format(NFO_FileName.getPath()))
                return

        # --- Edit Category Assets/Artwork ---
        # >> New in Kodi Krypton: use new xbmcgui.Dialog().select() and get rid of ImgSelectDialog()
        #    class. Get rid of al calls to gui_show_image_select().
        elif type == 1:
            category = self.categories[categoryID]

            # >> Lisitem elements and label2
            label2_icon      = category['s_icon']      if category['s_icon']      else 'Not set'
            label2_fanart    = category['s_fanart']    if category['s_fanart']    else 'Not set'
            label2_banner    = category['s_banner']    if category['s_banner']    else 'Not set'
            label2_poster    = category['s_poster']    if category['s_poster']    else 'Not set'
            label2_clearlogo = category['s_clearlogo'] if category['s_clearlogo'] else 'Not set'
            label2_trailer   = category['s_trailer']   if category['s_trailer']   else 'Not set'
            icon_listitem      = xbmcgui.ListItem(label = 'Edit Icon ...',      label2 = label2_icon)
            fanart_listitem    = xbmcgui.ListItem(label = 'Edit Fanart ...',    label2 = label2_fanart)
            banner_listitem    = xbmcgui.ListItem(label = 'Edit Banner ...',    label2 = label2_banner)
            poster_listitem    = xbmcgui.ListItem(label = 'Edit Poster ...',    label2 = label2_poster)
            clearlogo_listitem = xbmcgui.ListItem(label = 'Edit Clearlogo ...', label2 = label2_clearlogo)
            trailer_listitem   = xbmcgui.ListItem(label = 'Edit Trailer ...',   label2 = label2_trailer)

            # >> Set lisitem artwork with setArt
            img_icon         = category['s_icon']      if category['s_icon']      else 'DefaultAddonNone.png'
            img_fanart       = category['s_fanart']    if category['s_fanart']    else 'DefaultAddonNone.png'
            img_banner       = category['s_banner']    if category['s_banner']    else 'DefaultAddonNone.png'
            img_poster       = category['s_poster']    if category['s_poster']    else 'DefaultAddonNone.png'
            img_clearlogo    = category['s_clearlogo'] if category['s_clearlogo'] else 'DefaultAddonNone.png'
            img_trailer      = 'DefaultAddonVideo.png' if category['s_trailer']   else 'DefaultAddonNone.png'
            icon_listitem.setArt({'icon' : img_icon})
            fanart_listitem.setArt({'icon' : img_fanart})
            banner_listitem.setArt({'icon' : img_banner})
            poster_listitem.setArt({'icon' : img_poster})
            clearlogo_listitem.setArt({'icon' : img_clearlogo})
            trailer_listitem.setArt({'icon' : img_trailer})

            # >> Execute select dialog
            listitems = [icon_listitem, fanart_listitem, banner_listitem,
                         poster_listitem, clearlogo_listitem, trailer_listitem]
            type2 = dialog.select('Edit Category Assets/Artwork', list = listitems, useDetails = True)
            if type2 < 0: return

            # --- Edit Assets ---
            # >> If this function returns False no changes were made. No need to save categories XML
            # >> and update container.
            asset_list = [ASSET_ICON, ASSET_FANART, ASSET_BANNER, ASSET_POSTER, ASSET_CLEARLOGO, ASSET_TRAILER]
            asset_kind = asset_list[type2]
            if not self._gui_edit_asset(KIND_CATEGORY, asset_kind, category): return

        # --- Choose default thumb/fanart ---
        elif type == 2:
            category = self.categories[categoryID]
            # >> Label1 an label2
            asset_icon_str      = assets_get_asset_name_str(category['default_icon'])
            asset_fanart_str    = assets_get_asset_name_str(category['default_fanart'])
            asset_banner_str    = assets_get_asset_name_str(category['default_banner'])
            asset_poster_str    = assets_get_asset_name_str(category['default_poster'])
            asset_clearlogo_str = assets_get_asset_name_str(category['default_clearlogo'])
            label2_icon         = category[category['default_icon']]      if category[category['default_icon']]      else 'Not set'
            label2_fanart       = category[category['default_fanart']]    if category[category['default_fanart']]    else 'Not set'
            label2_banner       = category[category['default_banner']]    if category[category['default_banner']]    else 'Not set'
            label2_poster       = category[category['default_poster']]    if category[category['default_poster']]    else 'Not set'
            label2_clearlogo    = category[category['default_clearlogo']] if category[category['default_clearlogo']] else 'Not set'
            icon_listitem       = xbmcgui.ListItem(label = 'Choose asset for Icon (currently {0})'.format(asset_icon_str),
                                                   label2 = label2_icon)
            fanart_listitem     = xbmcgui.ListItem(label = 'Choose asset for Fanart (currently {0})'.format(asset_fanart_str),
                                                   label2 = label2_fanart)
            banner_listitem     = xbmcgui.ListItem(label = 'Choose asset for Banner (currently {0})'.format(asset_banner_str),
                                                   label2 = label2_banner)
            poster_listitem     = xbmcgui.ListItem(label = 'Choose asset for Poster (currently {0})'.format(asset_poster_str),
                                                   label2 = label2_poster)
            clearlogo_listitem  = xbmcgui.ListItem(label = 'Choose asset for Clearlogo (currently {0})'.format(asset_clearlogo_str),
                                                   label2 = label2_clearlogo)

            # >> Asset image
            img_icon            = category[category['default_icon']]      if category[category['default_icon']]      else 'DefaultAddonNone.png'
            img_fanart          = category[category['default_fanart']]    if category[category['default_fanart']]    else 'DefaultAddonNone.png'
            img_banner          = category[category['default_banner']]    if category[category['default_banner']]    else 'DefaultAddonNone.png'
            img_poster          = category[category['default_poster']]    if category[category['default_poster']]    else 'DefaultAddonNone.png'
            img_clearlogo       = category[category['default_clearlogo']] if category[category['default_clearlogo']] else 'DefaultAddonNone.png'
            icon_listitem.setArt({'icon' : img_icon})
            fanart_listitem.setArt({'icon' : img_fanart})
            banner_listitem.setArt({'icon' : img_banner})
            poster_listitem.setArt({'icon' : img_poster})
            clearlogo_listitem.setArt({'icon' : img_clearlogo})

            # >> Execute select dialog
            listitems = [icon_listitem, fanart_listitem, banner_listitem, poster_listitem, clearlogo_listitem]
            type2 = dialog.select('Edit Category default Assets/Artwork', list = listitems, useDetails = True)
            if type2 < 0: return

            Category_asset_ListItem_list = [
                xbmcgui.ListItem(label = 'Icon',      label2 = category['s_icon'] if category['s_icon'] else 'Not set'),
                xbmcgui.ListItem(label = 'Fanart',    label2 = category['s_fanart'] if category['s_fanart'] else 'Not set'),
                xbmcgui.ListItem(label = 'Banner',    label2 = category['s_banner'] if category['s_banner'] else 'Not set'),
                xbmcgui.ListItem(label = 'Poster',    label2 = category['s_poster'] if category['s_poster'] else 'Not set'),
                xbmcgui.ListItem(label = 'Clearlogo', label2 = category['s_clearlogo'] if category['s_clearlogo'] else 'Not set'),
            ]
            Category_asset_ListItem_list[0].setArt({'icon' : category['s_icon'] if category['s_icon'] else 'DefaultAddonNone.png'})
            Category_asset_ListItem_list[1].setArt({'icon' : category['s_fanart'] if category['s_fanart'] else 'DefaultAddonNone.png'})
            Category_asset_ListItem_list[2].setArt({'icon' : category['s_banner'] if category['s_banner'] else 'DefaultAddonNone.png'})
            Category_asset_ListItem_list[3].setArt({'icon' : category['s_poster'] if category['s_poster'] else 'DefaultAddonNone.png'})
            Category_asset_ListItem_list[4].setArt({'icon' : category['s_clearlogo'] if category['s_clearlogo'] else 'DefaultAddonNone.png'})

            if type2 == 0:
                type_s = dialog.select('Choose default Asset for Icon', list = Category_asset_ListItem_list, useDetails = True)
                if type_s < 0: return
                assets_choose_category_artwork(category, 'default_icon', type_s)
            elif type2 == 1:
                type_s = dialog.select('Choose default Asset for Fanart', list = Category_asset_ListItem_list, useDetails = True)
                if type_s < 0: return
                assets_choose_category_artwork(category, 'default_fanart', type_s)
            elif type2 == 2:
                type_s = dialog.select('Choose default Asset for Banner', list = Category_asset_ListItem_list, useDetails = True)
                if type_s < 0: return
                assets_choose_category_artwork(category, 'default_banner', type_s)
            elif type2 == 3:
                type_s = dialog.select('Choose default Asset for Poster', list = Category_asset_ListItem_list, useDetails = True)
                if type_s < 0: return
                assets_choose_category_artwork(category, 'default_poster', type_s)
            elif type2 == 4:
                type_s = dialog.select('Choose default Asset for Clearlogo', list = Category_asset_ListItem_list, useDetails = True)
                if type_s < 0: return
                assets_choose_category_artwork(category, 'default_clearlogo', type_s)

        # --- Category status ---
        elif type == 3:
            finished = self.categories[categoryID]['finished']
            finished = False if finished else True
            finished_display = 'Finished' if finished == True else 'Unfinished'
            self.categories[categoryID]['finished'] = finished
            kodi_dialog_OK('Category "{0}" status is now {1}'.format(self.categories[categoryID]['m_name'], finished_display))

        # --- Remove category. Also removes launchers in that category ---
        elif type == 4:
            launcherID_list = []
            category_name = self.categories[categoryID]['m_name']
            for launcherID in sorted(self.launchers.iterkeys()):
                if self.launchers[launcherID]['categoryID'] == categoryID:
                    launcherID_list.append(launcherID)

            if len(launcherID_list) > 0:
                ret = kodi_dialog_yesno('Category "{0}" contains {1} launchers. '.format(category_name, len(launcherID_list)) +
                                        'Deleting it will also delete related launchers. ' +
                                        'Are you sure you want to delete "{0}"?'.format(category_name))
                if not ret: return
                log_info('Deleting category "{0}" id {1}'.format(category_name, categoryID))
                # >> Delete launchers and ROM JSON/XML files associated with them
                for launcherID in launcherID_list:
                    log_info('Deleting linked launcher "{0}" id {1}'.format(self.launchers[launcherID]['m_name'], launcherID))
                    fs_unlink_ROMs_database(ROMS_DIR, self.launchers[launcherID])
                    self.launchers.pop(launcherID)
                # >> Delete category from database.
                self.categories.pop(categoryID)
            else:
                ret = kodi_dialog_yesno('Category "{0}" contains no launchers. '.format(category_name) +
                                        'Are you sure you want to delete "{0}"?'.format(category_name))
                if not ret: return
                log_info('Deleting category "{0}" id {1}'.format(category_name, categoryID))
                log_info('Category has no launchers, so no launchers to delete.')
                self.categories.pop(categoryID)
            kodi_notify('Deleted category {0}'.format(category_name))

        # >> If this point is reached then changes to metadata/images were made.
        # >> Save categories and update container contents so user sees those changes inmediately.
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_refresh_container()

    def _command_add_new_launcher(self, categoryID):
        LAUNCHER_STANDALONE  = 1
        LAUNCHER_ROM         = 2
        LAUNCHER_RETROPLAYER = 3
        LAUNCHER_LNK         = 4

        # >> If categoryID not found user is creating a new launcher using the context menu
        # >> of a launcher in addon root.
        if categoryID not in self.categories:
            log_info('Category ID not found. Creating laucher in addon root.')
            launcher_categoryID = VCATEGORY_ADDONROOT_ID
        else:
            # --- Ask user if launcher is created on selected category or on root menu ---
            category_name = self.categories[categoryID]['m_name']
            dialog = xbmcgui.Dialog()
            type = dialog.select('Choose Launcher category',
                                ['Create Launcher in "{0}" category'.format(category_name),
                                 'Create Launcher in addon root'])
            if type < 0:
                return
            elif type == 0:
                launcher_categoryID = categoryID
            elif type == 1:
                launcher_categoryID = VCATEGORY_ADDONROOT_ID
            else:
                kodi_notify_warn('_command_add_new_launcher() Wring type value. Report this bug.')
                return

        # --- Show "Create New Launcher" dialog ---
        dialog = xbmcgui.Dialog()
        if sys.platform == 'win32':
            type = dialog.select('Create New Launcher',
                                 ['Standalone launcher (Game/Application)',
                                  'ROM launcher (Emulator)',
                                  'ROM launcher (Kodi Retroplayer)',
                                  'LNK launcher (Windows only)'])
        else:
            type = dialog.select('Create New Launcher',
                                 ['Standalone launcher (Game/Application)',
                                  'ROM launcher (Emulator)',
                                  'ROM launcher (Kodi Retroplayer)',])
        if type < 0: return

        # --- Select type of new launcher ---
        filter = '.bat|.exe|.cmd|.lnk' if sys.platform == 'win32' else ''
        if   type == 0: launcher_type = LAUNCHER_STANDALONE
        elif type == 1: launcher_type = LAUNCHER_ROM
        elif type == 2: launcher_type = LAUNCHER_RETROPLAYER
        elif type == 3: launcher_type = LAUNCHER_LNK
        else:
            kodi_dialog_OK('Error creating launcher (type = {0}). This is a bug, pleas report it.'.format(type))
            return
        log_info('_command_add_new_launcher() New launcher (launcher_type = {0})'.format(launcher_type))

        # --- Standalone launcher ---
        if launcher_type == LAUNCHER_STANDALONE:
            app = xbmcgui.Dialog().browse(1, 'Select the launcher application', "files", filter).decode('utf-8')
            if not app: return
            appPath = FileName(app)

            argument = ''
            argkeyboard = xbmc.Keyboard(argument, 'Application arguments')
            argkeyboard.doModal()
            args = argkeyboard.getText().decode('utf-8')

            title = appPath.getBase_noext()
            title_formatted = title.replace('.' + title.split('.')[-1], '').replace('.', ' ')
            keyboard = xbmc.Keyboard(title_formatted, 'Set the title of the launcher')
            keyboard.doModal()
            title = keyboard.getText().decode('utf-8')
            if not title:
                title = appPath.getBase_noext()

            # >> Selection of the launcher game system
            dialog = xbmcgui.Dialog()
            sel_platform = dialog.select('Select the platform', AEL_platform_list)
            if sel_platform < 0: return
            launcher_platform = AEL_platform_list[sel_platform]

            # >> Add launcher to the launchers dictionary (using name as index)
            launcherID   = misc_generate_random_SID()
            launcherdata = fs_new_launcher()
            launcherdata['id']                 = launcherID
            launcherdata['m_name']             = title
            launcherdata['platform']           = launcher_platform
            launcherdata['categoryID']         = launcher_categoryID
            launcherdata['application']        = appPath.getOriginalPath()
            launcherdata['args']               = args
            launcherdata['timestamp_launcher'] = time.time()
            self.launchers[launcherID] = launcherdata
            kodi_notify('Created standalone launcher {0}'.format(title))

        #
        # 1) ROM Launcher
        # 2) Retroplayer launcher
        # 3) LNK launcher (Windows only)
        #
        else:
            # --- Launcher application ---
            if launcher_type == LAUNCHER_ROM:
                app = xbmcgui.Dialog().browse(1, 'Select the launcher application', 'files', filter).decode('utf-8')
                if not app: return
            elif launcher_type == LAUNCHER_RETROPLAYER:
                app = RETROPLAYER_LAUNCHER_APP_NAME
            elif launcher_type == LAUNCHER_LNK:
                app = LNK_LAUNCHER_APP_NAME
            app_FName = FileName(app)

            # --- ROM path ---
            if launcher_type == LAUNCHER_ROM or launcher_type == LAUNCHER_RETROPLAYER:
                roms_path = xbmcgui.Dialog().browse(0, 'Select the ROMs path', 'files', '').decode('utf-8')
            elif launcher_type == LAUNCHER_LNK:
                roms_path = xbmcgui.Dialog().browse(0, 'Select the LNKs path', 'files', '').decode('utf-8')
            if not roms_path: return
            roms_path_FName   = FileName(roms_path)

            # --- ROM extensions ---
            if launcher_type == LAUNCHER_ROM or launcher_type == LAUNCHER_RETROPLAYER:
                extensions = emudata_get_program_extensions(app_FName.getBase())
                extkey = xbmc.Keyboard(extensions, 'Set files extensions, use "|" as separator. (e.g lnk|cbr)')
                extkey.doModal()
                if not extkey.isConfirmed(): return
                ext = extkey.getText().decode('utf-8')
            elif launcher_type == LAUNCHER_LNK:
                ext = 'lnk'

            # --- Launcher arguments ---
            if launcher_type == LAUNCHER_ROM:
                default_arguments = emudata_get_program_arguments(app_FName.getBase())
                argkeyboard = xbmc.Keyboard(default_arguments, 'Application arguments')
                argkeyboard.doModal()
                if not argkeyboard.isConfirmed(): return
                args = argkeyboard.getText().decode('utf-8')
            elif launcher_type == LAUNCHER_RETROPLAYER or launcher_type == LAUNCHER_LNK:
                args = '%rom%'

            # --- Launcher title/name ---
            title = app_FName.getBase()
            fixed_title = title.replace('.' + title.split('.')[-1], '').replace('.', ' ')
            initial_title = fixed_title if type == 1 else ''
            keyboard = xbmc.Keyboard(initial_title, 'Set the title of the launcher')
            keyboard.doModal()
            if not keyboard.isConfirmed(): return
            title = keyboard.getText().decode('utf-8')
            if title == '': title = '[ Not set ]'

            # --- Selection of the launcher plaform from official AEL platform names ---
            dialog = xbmcgui.Dialog()
            sel_platform = dialog.select('Select the platform', AEL_platform_list)
            if sel_platform < 0: return
            launcher_platform = AEL_platform_list[sel_platform]

            # --- Select asset path ---
            # A) User chooses one and only one assets path
            # B) If this path is different from the ROM path then asset naming scheme 1 is used.
            # B) If this path is the same as the ROM path then asset naming scheme 2 is used.
            assets_path = xbmcgui.Dialog().browse(0, 'Select asset/artwork directory', 'files', '', False, False, roms_path).decode('utf-8')
            if not assets_path: return
            assets_path_FName = FileName(assets_path)

            # --- Create launcher object data, add to dictionary and write XML file ---
            # Choose launcher ROM XML filename. There may be launchers with same name in different categories, or
            # even launcher with the same name in the same category.
            launcherID      = misc_generate_random_SID()
            category_name   = self.categories[categoryID]['m_name'] if categoryID in self.categories else VCATEGORY_ADDONROOT_ID
            roms_base_noext = fs_get_ROMs_basename(category_name, title, launcherID)

            # --- Create new launcher. categories.xml is save at the end of this function ---
            # NOTE than in the database original paths are always stored.
            launcherdata = fs_new_launcher()
            launcherdata['id']                 = launcherID
            launcherdata['m_name']             = title
            launcherdata['platform']           = launcher_platform
            launcherdata['categoryID']         = launcher_categoryID
            launcherdata['application']        = app_FName.getOriginalPath()
            launcherdata['args']               = args
            launcherdata['rompath']            = roms_path_FName.getOriginalPath()
            launcherdata['romext']             = ext
            launcherdata['roms_base_noext']    = roms_base_noext
            launcherdata['timestamp_launcher'] = time.time()

            # >> Create asset directories. Function detects if we are using naming scheme 1 or 2.
            # >> launcher is edited using Python passing by assignment.
            assets_init_asset_dir(assets_path_FName, launcherdata)
            self.launchers[launcherID] = launcherdata

            # >> Notify user
            if   launcher_type == LAUNCHER_ROM:         kodi_notify('Created ROM launcher {0}'.format(title))
            elif launcher_type == LAUNCHER_RETROPLAYER: kodi_notify('Created Retroplayer launcher {0}'.format(title))
            elif launcher_type == LAUNCHER_LNK:         kodi_notify('Created LNK launcher {0}'.format(title))

        # >> If this point is reached then changes to metadata/images were made.
        # >> Save categories and update container contents so user sees those changes inmediately.
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_refresh_container()

    def _command_edit_launcher(self, categoryID, launcherID):
        # --- Shows a select box with the options to edit ---
        dialog = xbmcgui.Dialog()
        finished_display = 'Status : Finished' if self.launchers[launcherID]['finished'] == True else 'Status : Unfinished'
        if self.launchers[launcherID]['categoryID'] == VCATEGORY_ADDONROOT_ID:
            category_name = 'Addon root (no category)'
        else:
            category_name = self.categories[self.launchers[launcherID]['categoryID']]['m_name']
        if self.launchers[launcherID]['rompath'] == '':
            type = dialog.select('Select action for launcher {0}'.format(self.launchers[launcherID]['m_name']),
                                 ['Edit Metadata ...', 'Edit Assets/Artwork ...', 'Choose default Assets/Artwork ...',
                                  'Change Category: {0}'.format(category_name), finished_display,
                                  'Advanced Modifications ...', 'Delete Launcher'])
        else:
            type = dialog.select('Select action for launcher {0}'.format(self.launchers[launcherID]['m_name']),
                                 ['Edit Metadata ...', 'Edit Assets/Artwork ...', 'Choose default Assets/Artwork ...',
                                  'Change Category: {0}'.format(category_name), finished_display,
                                  'Manage ROMs ...', 'Audit ROMs / Launcher view mode ...',
                                  'Advanced Modifications ...', 'Delete Launcher'])
        if type < 0: return

        # --- Edition of the launcher metadata ---
        type_nb = 0
        if type == type_nb:
            # >> Make a list of available metadata scrapers
            scraper_obj_list  = []
            scraper_menu_list = []
            for scrap_obj in scrapers_metadata:
                scraper_obj_list.append(scrap_obj)
                scraper_menu_list.append('Scrape metadata from {0} ...'.format(scrap_obj.name))
                log_verb('Added metadata scraper {0}'.format(scrap_obj.name))

            # >> Metadata edit dialog
            NFO_FileName = fs_get_launcher_NFO_name(self.settings, self.launchers[launcherID])
            NFO_str = 'NFO found' if NFO_FileName.exists() else 'NFO not found'
            plot_str = text_limit_string(self.launchers[launcherID]['m_plot'], DESCRIPTION_MAXSIZE)
            dialog = xbmcgui.Dialog()
            menu_list = ["Edit Title: '{0}'".format(self.launchers[launcherID]['m_name']),
                         "Edit Platform: {0}".format(self.launchers[launcherID]['platform']),
                         "Edit Release Year: '{0}'".format(self.launchers[launcherID]['m_year']),
                         "Edit Genre: '{0}'".format(self.launchers[launcherID]['m_genre']),
                         "Edit Developer: '{0}'".format(self.launchers[launcherID]['m_developer']),
                         "Edit Rating: '{0}'".format(self.launchers[launcherID]['m_rating']),
                         "Edit Plot: '{0}'".format(plot_str),
                         'Import NFO file (default, {0})'.format(NFO_str),
                         'Import NFO file (browse NFO file) ...',
                         'Save NFO file (default location)']
            type2 = dialog.select('Edit Launcher Metadata', menu_list + scraper_menu_list)
            if type2 < 0: return

            # --- Edition of the launcher name ---
            if type2 == 0:
                launcher = self.launchers[launcherID]
                keyboard = xbmc.Keyboard(launcher['m_name'], 'Edit title')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                title = keyboard.getText().decode('utf-8')
                if title == '': title = launcher['m_name']
                old_launcher_name = launcher['m_name']
                new_launcher_name = title.rstrip()
                log_debug('_command_edit_launcher() Edit Title: old_launcher_name "{0}"'.format(old_launcher_name))
                log_debug('_command_edit_launcher() Edit Title: new_launcher_name "{0}"'.format(new_launcher_name))
                if old_launcher_name == new_launcher_name: return

                # --- Rename ROMs XML/JSON file (if it exists) and change launcher ---
                old_roms_base_noext = self.launchers[launcherID]['roms_base_noext']
                categoryID          = self.launchers[launcherID]['categoryID']
                category_name       = self.categories[categoryID]['m_name'] if categoryID in self.categories else VCATEGORY_ADDONROOT_ID
                new_roms_base_noext = fs_get_ROMs_basename(category_name, new_launcher_name, launcherID)
                log_debug('_command_edit_launcher() old_roms_base_noext "{0}"'.format(old_roms_base_noext))
                log_debug('_command_edit_launcher() new_roms_base_noext "{0}"'.format(new_roms_base_noext))
                if old_roms_base_noext != new_roms_base_noext:
                    log_debug('Renaming JSON/XML launcher databases')
                    launchers[launcherID]['roms_base_noext'] = new_roms_base_noext
                    fs_rename_ROMs_database(ROMS_DIR, old_roms_base_noext, new_roms_base_noext)
                else:
                    log_debug('Not renaming ROM databases (old and new names are equal)')
                launcher['m_name'] = new_launcher_name
                launcher['roms_base_noext'] = new_roms_base_noext
                kodi_notify('Changed Launcher Title')

            # --- Selection of the launcher platform from AEL "official" list ---
            elif type2 == 1:
                p_idx = get_AEL_platform_index(self.launchers[launcherID]['platform'])
                sel_platform = xbmcgui.Dialog().select('Select the platform', AEL_platform_list, preselect = p_idx)
                if sel_platform < 0: return
                self.launchers[launcherID]['platform'] = AEL_platform_list[sel_platform]
                kodi_notify('Launcher Platform is now {0}'.format(AEL_platform_list[sel_platform]))

            # --- Edition of the launcher release date (year) ---
            elif type2 == 2:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]['m_year'], 'Edit release year')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.launchers[launcherID]['m_year'] = keyboard.getText().decode('utf-8')
                kodi_notify('Changed Launcher Year')

            # --- Edition of the launcher genre ---
            elif type2 == 3:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]['m_genre'], 'Edit genre')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.launchers[launcherID]['m_genre'] = keyboard.getText().decode('utf-8')
                kodi_notify('Changed Launcher Genre')

            # --- Edition of the launcher developer ---
            elif type2 == 4:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]['m_developer'], 'Edit developer')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.launchers[launcherID]['m_developer'] = keyboard.getText().decode('utf-8')
                kodi_notify('Changed Launcher Developer')

            # --- Edition of the launcher rating ---
            elif type2 == 5:
                rating = dialog.select('Edit Launcher Rating',
                                      ['Not set',  'Rating 0', 'Rating 1', 'Rating 2', 'Rating 3', 'Rating 4',
                                       'Rating 5', 'Rating 6', 'Rating 7', 'Rating 8', 'Rating 9', 'Rating 10'])
                # >> Rating not set, empty string
                if rating == 0:
                    self.launchers[launcherID]['m_rating'] = ''
                    kodi_notify('Launcher Rating changed to Not Set')
                elif rating >= 1 and rating <= 11:
                    self.launchers[launcherID]['m_rating'] = '{0}'.format(rating - 1)
                    kodi_notify('Changed Launcher Rating')
                elif rating < 0:
                    kodi_dialog_OK("Launcher rating '{0}' not changed".format(self.launchers[launcherID]['m_rating']))
                    return

            # --- Edit launcher description (plot) ---
            elif type2 == 6:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]['m_plot'], 'Edit plot')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.launchers[launcherID]['m_plot'] = keyboard.getText().decode('utf-8')
                kodi_notify('Changed Launcher Plot')

            # --- Import launcher metadata from NFO file (automatic) ---
            elif type2 == 7:
                # >> Get NFO file name for launcher
                # >> Launcher is edited using Python passing by assigment
                # >> Returns True if changes were made
                NFO_file = fs_get_launcher_NFO_name(self.settings, self.launchers[launcherID])
                if not fs_import_launcher_NFO(NFO_file, self.launchers, launcherID): return
                kodi_notify('Imported Launcher NFO file {0}'.format(NFO_FileName.getPath()))

            # --- Browse for NFO file ---
            elif type2 == 8:
                NFO_file = xbmcgui.Dialog().browse(1, 'Select Launcher NFO file', 'files', '.nfo', False, False).decode('utf-8')
                if not NFO_file: return
                NFO_FileName = FileName(NFO_file)
                if not NFO_FileName.exists(): return
                # >> Launcher is edited using Python passing by assigment
                # >> Returns True if changes were made
                if not fs_import_launcher_NFO(NFO_FileName, self.launchers, launcherID): return
                kodi_notify('Imported Launcher NFO file {0}'.format(NFO_FileName.getPath()))

            # --- Export launcher metadata to NFO file ---
            elif type2 == 9:
                NFO_FileName = fs_get_launcher_NFO_name(self.settings, self.launchers[launcherID])
                if not fs_export_launcher_NFO(NFO_FileName, self.launchers[launcherID]): return
                # >> No need to save launchers
                kodi_notify('Exported Launcher NFO file {0}'.format(NFO_FileName.getPath()))
                return

            # --- Scrape launcher metadata ---
            elif type2 >= 10:
                # --- Use the scraper chosen by user ---
                scraper_index = type2 - 10
                scraper_obj   = scraper_obj_list[scraper_index]
                log_debug('_command_edit_launcher() Scraper index {0}'.format(scraper_index))
                log_debug('_command_edit_launcher() User chose scraper "{0}"'.format(scraper_obj.name))

                # --- Initialise asset scraper ---
                scraper_obj.set_addon_dir(CURRENT_ADDON_DIR.getPath())
                log_debug('_command_edit_launcher() Initialised scraper "{0}"'.format(scraper_obj.name))

                # >> If this returns False there were no changes so no need to save categories.xml
                if not self._gui_scrap_launcher_metadata(launcherID, scraper_obj): return

        # --- Edit Launcher Assets/Artwork ---
        type_nb = type_nb + 1
        if type == type_nb:
            launcher = self.launchers[launcherID]

            # >> Create ListItems and label2
            label2_icon       = launcher['s_icon']       if launcher['s_icon']      else 'Not set'
            label2_fanart     = launcher['s_fanart']     if launcher['s_fanart']    else 'Not set'
            label2_banner     = launcher['s_banner']     if launcher['s_banner']    else 'Not set'
            label2_poster     = launcher['s_poster']     if launcher['s_poster']     else 'Not set'
            label2_clearlogo  = launcher['s_clearlogo']  if launcher['s_clearlogo'] else 'Not set'
            label2_controller = launcher['s_controller'] if launcher['s_controller'] else 'Not set'
            label2_trailer    = launcher['s_trailer']    if launcher['s_trailer']   else 'Not set'
            icon_listitem       = xbmcgui.ListItem(label = 'Edit Icon ...', label2 = label2_icon)
            fanart_listitem     = xbmcgui.ListItem(label = 'Edit Fanart ...', label2 = label2_fanart)
            banner_listitem     = xbmcgui.ListItem(label = 'Edit Banner ...', label2 = label2_banner)
            poster_listitem     = xbmcgui.ListItem(label = 'Edit Poster ...', label2 = label2_poster)
            clearlogo_listitem  = xbmcgui.ListItem(label = 'Edit Clearlogo ...', label2 = label2_clearlogo)
            controller_listitem = xbmcgui.ListItem(label = 'Edit Controller ...', label2 = label2_controller)
            trailer_listitem    = xbmcgui.ListItem(label = 'Edit Trailer ...', label2 = label2_trailer)

            # >> Set artwork with setArt()
            img_icon       = launcher['s_icon']       if launcher['s_icon']     else 'DefaultAddonNone.png'
            img_fanart     = launcher['s_fanart']     if launcher['s_fanart']    else 'DefaultAddonNone.png'
            img_banner     = launcher['s_banner']     if launcher['s_banner']    else 'DefaultAddonNone.png'
            img_poster     = launcher['s_poster']     if launcher['s_poster']     else 'DefaultAddonNone.png'
            img_clearlogo  = launcher['s_clearlogo']  if launcher['s_clearlogo'] else 'DefaultAddonNone.png'
            img_controller = launcher['s_controller'] if launcher['s_controller'] else 'DefaultAddonNone.png'
            img_trailer    = 'DefaultAddonVideo.png'  if launcher['s_trailer']   else 'DefaultAddonNone.png'
            icon_listitem.setArt({'icon' : img_icon})
            fanart_listitem.setArt({'icon' : img_fanart})
            banner_listitem.setArt({'icon' : img_banner})
            poster_listitem.setArt({'icon' : img_poster})
            clearlogo_listitem.setArt({'icon' : img_clearlogo})
            controller_listitem.setArt({'icon' : img_controller})
            trailer_listitem.setArt({'icon' : img_trailer})

            # >> Execute select dialog
            listitems = [icon_listitem, fanart_listitem, banner_listitem, poster_listitem,
                         clearlogo_listitem, controller_listitem, trailer_listitem]
            type2 = dialog.select('Edit Launcher Assets/Artwork', list = listitems, useDetails = True)
            if type2 < 0: return

            # --- Edit Assets ---
            # >> If this function returns False no changes were made. No need to save categories XML
            # >> and update container.
            asset_list = [ASSET_ICON, ASSET_FANART, ASSET_BANNER, ASSET_POSTER,
                          ASSET_CLEARLOGO, ASSET_CONTROLLER, ASSET_TRAILER]
            asset_kind = asset_list[type2]
            if not self._gui_edit_asset(KIND_LAUNCHER, asset_kind, launcher): return

        # --- Choose Launcher default thumb/fanart/banner/poster/clearlogo ---
        type_nb = type_nb + 1
        if type == type_nb:
            launcher = self.launchers[launcherID]
            # >> Label1 an label2
            asset_icon_str      = assets_get_asset_name_str(launcher['default_icon'])
            asset_fanart_str    = assets_get_asset_name_str(launcher['default_fanart'])
            asset_banner_str    = assets_get_asset_name_str(launcher['default_banner'])
            asset_poster_str    = assets_get_asset_name_str(launcher['default_poster'])
            asset_clearlogo_str = assets_get_asset_name_str(launcher['default_clearlogo'])
            label2_icon         = launcher[launcher['default_icon']]      if launcher[launcher['default_icon']]      else 'Not set'
            label2_fanart       = launcher[launcher['default_fanart']]    if launcher[launcher['default_fanart']]    else 'Not set'
            label2_banner       = launcher[launcher['default_banner']]    if launcher[launcher['default_banner']]    else 'Not set'
            label2_poster       = launcher[launcher['default_poster']]    if launcher[launcher['default_poster']]    else 'Not set'
            label2_clearlogo    = launcher[launcher['default_clearlogo']] if launcher[launcher['default_clearlogo']] else 'Not set'
            icon_listitem       = xbmcgui.ListItem(label = 'Choose asset for Icon (currently {0})'.format(asset_icon_str),
                                                   label2 = label2_icon)
            fanart_listitem     = xbmcgui.ListItem(label = 'Choose asset for Fanart (currently {0})'.format(asset_fanart_str),
                                                   label2 = label2_fanart)
            banner_listitem     = xbmcgui.ListItem(label = 'Choose asset for Banner (currently {0})'.format(asset_banner_str),
                                                   label2 = label2_banner)
            poster_listitem     = xbmcgui.ListItem(label = 'Choose asset for Poster (currently {0})'.format(asset_poster_str),
                                                   label2 = label2_poster)
            clearlogo_listitem  = xbmcgui.ListItem(label = 'Choose asset for Clearlogo (currently {0})'.format(asset_clearlogo_str),
                                                   label2 = label2_clearlogo)

            # >> Asset image
            img_icon            = launcher[launcher['default_icon']]      if launcher[launcher['default_icon']]      else 'DefaultAddonNone.png'
            img_fanart          = launcher[launcher['default_fanart']]    if launcher[launcher['default_fanart']]    else 'DefaultAddonNone.png'
            img_banner          = launcher[launcher['default_banner']]    if launcher[launcher['default_banner']]    else 'DefaultAddonNone.png'
            img_poster          = launcher[launcher['default_poster']]    if launcher[launcher['default_poster']]    else 'DefaultAddonNone.png'
            img_clearlogo       = launcher[launcher['default_clearlogo']] if launcher[launcher['default_clearlogo']] else 'DefaultAddonNone.png'
            icon_listitem.setArt({'icon' : img_icon})
            fanart_listitem.setArt({'icon' : img_fanart})
            banner_listitem.setArt({'icon' : img_banner})
            poster_listitem.setArt({'icon' : img_poster})
            clearlogo_listitem.setArt({'icon' : img_clearlogo})

            # >> Execute select dialog
            listitems = [icon_listitem, fanart_listitem, banner_listitem, poster_listitem, clearlogo_listitem]
            type2 = dialog.select('Edit Launcher default Assets/Artwork', list = listitems, useDetails = True)
            if type2 < 0: return

            Launcher_asset_ListItem_list = [
                xbmcgui.ListItem(label = 'Icon',       label2 = launcher['s_icon'] if launcher['s_icon'] else 'Not set'),
                xbmcgui.ListItem(label = 'Fanart',     label2 = launcher['s_fanart'] if launcher['s_fanart'] else 'Not set'),
                xbmcgui.ListItem(label = 'Banner',     label2 = launcher['s_banner'] if launcher['s_banner'] else 'Not set'),
                xbmcgui.ListItem(label = 'Poster',     label2 = launcher['s_poster'] if launcher['s_poster'] else 'Not set'),
                xbmcgui.ListItem(label = 'Clearlogo',  label2 = launcher['s_clearlogo'] if launcher['s_clearlogo'] else 'Not set'),
                xbmcgui.ListItem(label = 'Controller', label2 = launcher['s_controller'] if launcher['s_controller'] else 'Not set'),
            ]
            Launcher_asset_ListItem_list[0].setArt({'icon' : launcher['s_icon'] if launcher['s_icon'] else 'DefaultAddonNone.png'})
            Launcher_asset_ListItem_list[1].setArt({'icon' : launcher['s_fanart'] if launcher['s_fanart'] else 'DefaultAddonNone.png'})
            Launcher_asset_ListItem_list[2].setArt({'icon' : launcher['s_banner'] if launcher['s_banner'] else 'DefaultAddonNone.png'})
            Launcher_asset_ListItem_list[3].setArt({'icon' : launcher['s_poster'] if launcher['s_poster'] else 'DefaultAddonNone.png'})
            Launcher_asset_ListItem_list[4].setArt({'icon' : launcher['s_clearlogo'] if launcher['s_clearlogo'] else 'DefaultAddonNone.png'})
            Launcher_asset_ListItem_list[5].setArt({'icon' : launcher['s_controller'] if launcher['s_controller'] else 'DefaultAddonNone.png'})

            if type2 == 0:
                type_s = dialog.select('Choose default Asset for Icon', list = Launcher_asset_ListItem_list, useDetails = True)
                if type_s < 0: return
                assets_choose_launcher_artwork(launcher, 'default_icon', type_s)
            elif type2 == 1:
                type_s = dialog.select('Choose default Asset for Fanart', list = Launcher_asset_ListItem_list, useDetails = True)
                if type_s < 0: return
                assets_choose_launcher_artwork(launcher, 'default_fanart', type_s)
            elif type2 == 2:
                type_s = dialog.select('Choose default Asset for Banner', list = Launcher_asset_ListItem_list, useDetails = True)
                if type_s < 0: return
                assets_choose_launcher_artwork(launcher, 'default_banner', type_s)
            elif type2 == 3:
                type_s = dialog.select('Choose default Asset for Poster', list = Launcher_asset_ListItem_list, useDetails = True)
                if type_s < 0: return
                assets_choose_launcher_artwork(launcher, 'default_poster', type_s)
            elif type2 == 4:
                type_s = dialog.select('Choose default Asset for Clearlogo', list = Launcher_asset_ListItem_list, useDetails = True)
                if type_s < 0: return
                assets_choose_launcher_artwork(launcher, 'default_clearlogo', type_s)

        # --- Change launcher's Category ---
        type_nb = type_nb + 1
        if type == type_nb:
            current_category_ID = self.launchers[launcherID]['categoryID']

            # >> If no Categories there is nothing to change
            if len(self.categories) == 0:
                kodi_dialog_OK('There is no Categories. Nothing to change.')
                return
            dialog = xbmcgui.Dialog()
            # Add special root cateogory at the beginning
            categories_id   = [VCATEGORY_ADDONROOT_ID]
            categories_name = ['Addon root (no category)']
            for key in self.categories:
                categories_id.append(self.categories[key]['id'])
                categories_name.append(self.categories[key]['m_name'])
            selected_cat = dialog.select('Select the category', categories_name)
            if selected_cat < 0: return
            new_categoryID = categories_id[selected_cat]
            self.launchers[launcherID]['categoryID'] = new_categoryID
            log_debug('_command_edit_launcher() current category   ID "{0}"'.format(current_category_ID))
            log_debug('_command_edit_launcher() new     category   ID "{0}"'.format(new_categoryID))
            log_debug('_command_edit_launcher() new     category name "{0}"'.format(categories_name[selected_cat]))

            # >> Save cateogires/launchers
            self.launchers[launcherID]['timestamp_launcher'] = time.time()
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

            # >> Display new category where launcher has moved
            # For some reason ReplaceWindow() does not work, bu Container.Update() does.
            # See http://forum.kodi.tv/showthread.php?tid=293844
            if new_categoryID == VCATEGORY_ADDONROOT_ID:
                plugin_url = self.base_url
            else:
                plugin_url = '{0}?com=SHOW_LAUNCHERS&amp;catID={1}'.format(self.base_url, new_categoryID)
            exec_str = 'Container.Update({0},replace)'.format(plugin_url)
            log_debug('_command_edit_launcher() Plugin URL     "{0}"'.format(plugin_url))
            log_debug('_command_edit_launcher() Executebuiltin "{0}"'.format(exec_str))
            xbmc.executebuiltin(exec_str)
            kodi_notify('Launcher new Category is {0}'.format(categories_name[selected_cat]))
            return

        # --- Launcher status (finished [bool]) ---
        type_nb = type_nb + 1
        if type == type_nb:
            finished = self.launchers[launcherID]['finished']
            finished = False if finished else True
            finished_display = 'Finished' if finished == True else 'Unfinished'
            self.launchers[launcherID]['finished'] = finished
            kodi_dialog_OK('Launcher "{0}" status is now {1}'.format(self.launchers[launcherID]['m_name'], finished_display))

        # --- Launcher's Manage ROMs menu option ---
        # ONLY for ROM launchers, not for standalone launchers
        if self.launchers[launcherID]['rompath'] != '':
            type_nb = type_nb + 1
            if type == type_nb:
                dialog = xbmcgui.Dialog()
                type2 = dialog.select('Manage ROMs',
                                      ['Choose ROMs default assets/artwork ...',
                                       'Manage ROMs asset directories ...',
                                       'Rescan ROMs local assets/artwork',
                                       'Remove dead/missing ROMs',
                                       'Import ROMs metadata from NFO files',
                                       'Export ROMs metadata to NFO files',
                                       'Delete ROMs NFO files',
                                       'Clear ROMs from launcher' ])
                if type2 < 0: return # User canceled select dialog

                # --- Choose default ROMs assets/artwork ---
                if type2 == 0:
                    launcher        = self.launchers[launcherID]
                    asset_thumb     = assets_get_asset_name_str(launcher['roms_default_thumb'])
                    asset_fanart    = assets_get_asset_name_str(launcher['roms_default_fanart'])
                    asset_banner    = assets_get_asset_name_str(launcher['roms_default_banner'])
                    asset_poster    = assets_get_asset_name_str(launcher['roms_default_poster'])
                    asset_clearlogo = assets_get_asset_name_str(launcher['roms_default_clearlogo'])
                    dialog = xbmcgui.Dialog()
                    type3 = dialog.select('Edit ROMs default Assets/Artwork',
                                          ['Choose asset for Thumb (currently {0})'.format(asset_thumb),
                                           'Choose asset for Fanart (currently {0})'.format(asset_fanart),
                                           'Choose asset for Banner (currently {0})'.format(asset_banner),
                                           'Choose asset for Poster (currently {0})'.format(asset_poster),
                                           'Choose asset for Clearlogo (currently {0})'.format(asset_clearlogo)])

                    if type3 == 0:
                        type_s = xbmcgui.Dialog().select('Choose default Asset for Thumb', DEFAULT_ROM_ASSET_LIST)
                        if type_s < 0: return
                        assets_choose_category_ROM(launcher, 'roms_default_thumb', type_s)
                    elif type3 == 1:
                        type_s = xbmcgui.Dialog().select('Choose default Asset for Fanart', DEFAULT_ROM_ASSET_LIST)
                        if type_s < 0: return
                        assets_choose_category_ROM(launcher, 'roms_default_fanart', type_s)
                    elif type3 == 2:
                        type_s = xbmcgui.Dialog().select('Choose default Asset for Banner', DEFAULT_ROM_ASSET_LIST)
                        if type_s < 0: return
                        assets_choose_category_ROM(launcher, 'roms_default_banner', type_s)
                    elif type3 == 3:
                        type_s = xbmcgui.Dialog().select('Choose default Asset for Poster', DEFAULT_ROM_ASSET_LIST)
                        if type_s < 0: return
                        assets_choose_category_ROM(launcher, 'roms_default_poster', type_s)
                    elif type3 == 4:
                        type_s = xbmcgui.Dialog().select('Choose default Asset for Clearlogo', DEFAULT_ROM_ASSET_LIST)
                        if type_s < 0: return
                        assets_choose_category_ROM(launcher, 'roms_default_clearlogo', type_s)
                    # >> User canceled select dialog
                    elif type3 < 0: return

                # --- Manage ROM Asset directories ---
                elif type2 == 1:
                    launcher = self.launchers[launcherID]
                    dialog = xbmcgui.Dialog()
                    type3 = dialog.select('ROM Asset directories ',
                                          ["Change Titles path: '{0}'".format(launcher['path_title']),
                                           "Change Snaps path: '{0}'".format(launcher['path_snap']),
                                           "Change Fanarts path '{0}'".format(launcher['path_fanart']),
                                           "Change Banners path: '{0}'".format(launcher['path_banner']),
                                           "Change Clearlogos path: '{0}'".format(launcher['path_clearlogo']),
                                           "Change Boxfronts path: '{0}'".format(launcher['path_boxfront']),
                                           "Change Boxbacks path: '{0}'".format(launcher['path_boxback']),
                                           "Change Cartridges path: '{0}'".format(launcher['path_cartridge']),
                                           "Change Flyers path: '{0}'".format(launcher['path_flyer']),
                                           "Change Maps path: '{0}'".format(launcher['path_map']),
                                           "Change Manuals path: '{0}'".format(launcher['path_manual']),
                                           "Change Trailers path: '{0}'".format(launcher['path_trailer']) ])

                    if type3 == 0:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Titles path', 'files', '', False, False, launcher['path_title']).decode('utf-8')
                        if not dir_path: return
                        self.launchers[launcherID]['path_title'] = dir_path
                    elif type3 == 1:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Snaps path', 'files', '', False, False, launcher['path_snap']).decode('utf-8')
                        if not dir_path: return
                        self.launchers[launcherID]['path_snap'] = dir_path
                    elif type3 == 2:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Fanarts path', 'files', '', False, False, launcher['path_fanart']).decode('utf-8')
                        if not dir_path: return
                        self.launchers[launcherID]['path_fanart'] = dir_path
                    elif type3 == 3:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Banners path', 'files', '', False, False, launcher['path_banner']).decode('utf-8')
                        if not dir_path: return
                        self.launchers[launcherID]['path_banner'] = dir_path
                    elif type3 == 4:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Clearlogos path', 'files', '', False, False, launcher['path_clearlogo']).decode('utf-8')
                        if not dir_path: return
                        self.launchers[launcherID]['path_clearlogo'] = dir_path
                    elif type3 == 5:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Boxfronts path', 'files', '', False, False, launcher['path_boxfront']).decode('utf-8')
                        if not dir_path: return
                        self.launchers[launcherID]['path_boxfront'] = dir_path
                    elif type3 == 6:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Boxbacks path', 'files', '', False, False, launcher['path_boxback']).decode('utf-8')
                        if not dir_path: return
                        self.launchers[launcherID]['path_boxback'] = dir_path
                    elif type3 == 7:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Cartridges path', 'files', '', False, False, launcher['path_cartridge']).decode('utf-8')
                        if not dir_path: return
                        self.launchers[launcherID]['path_cartridge'] = dir_path
                    elif type3 == 8:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Flyers path', 'files', '', False, False, launcher['path_flyer']).decode('utf-8')
                        if not dir_path: return
                        self.launchers[launcherID]['path_flyer'] = dir_path
                    elif type3 == 9:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Maps path', 'files', '', False, False, launcher['path_map']).decode('utf-8')
                        if not dir_path: return
                        self.launchers[launcherID]['path_map'] = dir_path
                    elif type3 == 10:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Manuals path', 'files', '', False, False, launcher['path_manual']).decode('utf-8')
                        if not dir_path: return
                        self.launchers[launcherID]['path_manual'] = dir_path
                    elif type3 == 11:
                        dialog = xbmcgui.Dialog()
                        dir_path = dialog.browse(0, 'Select Trailers path', 'files', '', False, False, launcher['path_trailer']).decode('utf-8')
                        if not dir_path: return
                        self.launchers[launcherID]['path_trailer'] = dir_path
                    # >> User canceled select dialog
                    elif type3 < 0: return

                    # >> Check for duplicate paths and warn user.
                    duplicated_name_list = asset_get_duplicated_dir_list(self.launchers[launcherID])
                    if duplicated_name_list:
                        duplicated_asset_srt = ', '.join(duplicated_name_list)
                        kodi_dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                                       'AEL will refuse to add/edit ROMs if there are duplicate asset directories.')

                # --- Rescan local assets/artwork ---
                # >> A) First, local assets are searched for every ROM based on the filename.
                # >> B) Next, missing assets are searched in the Parent/Clone group using the files
                #       found in the previous step. This is much faster than searching for files again.
                #
                elif type2 == 2:
                    log_info('_command_edit_launcher() Rescanning local assets ...')
                    launcher = self.launchers[launcherID]

                    # ~~~ Check asset dirs and disable scanning for unset dirs ~~~
                    (enabled_asset_list, unconfigured_name_list) = asset_get_configured_dir_list(launcher)
                    if unconfigured_name_list:
                        unconfigure_asset_srt = ', '.join(unconfigured_name_list)
                        kodi_dialog_OK('Assets directories not set: {0}. '.format(unconfigure_asset_srt) +
                                       'Asset scanner will be disabled for this/those.')

                    # ~~~ Ensure there is no duplicate asset dirs ~~~
                    # >> Cancel scanning if duplicates found
                    duplicated_name_list = asset_get_duplicated_dir_list(launcher)
                    if duplicated_name_list:
                        duplicated_asset_srt = ', '.join(duplicated_name_list)
                        log_info('Duplicated asset dirs: {0}'.format(duplicated_asset_srt))
                        kodi_dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                                       'Change asset directories before continuing.')
                        return
                    else:
                        log_info('No duplicated asset dirs found')

                    # --- Create a cache of assets ---
                    # >> misc_add_file_cache() creates a set with all files in a given directory.
                    # >> That set is stored in a function internal cache associated with the path.
                    # >> Files in the cache can be searched with misc_search_file_cache()
                    pDialog = xbmcgui.DialogProgress()
                    pDialog.create('Advanced Emulator Launcher', 'Scanning files in asset directories ...')
                    for i, asset_kind in enumerate(ROM_ASSET_LIST):
                        AInfo = assets_get_info_scheme(asset_kind)
                        misc_add_file_cache(launcher[AInfo.path_key])
                        pDialog.update((100*i)/len(ROM_ASSET_LIST))
                    pDialog.update(100)
                    pDialog.close()

                    # --- Traverse ROM list and check local asset/artwork ---
                    pDialog.create('Advanced Emulator Launcher', 'Searching for local assets/artwork ...')
                    roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)
                    num_items = len(roms)
                    item_counter = 0
                    for rom_id in roms:
                        # --- Search assets for current ROM ---
                        rom = roms[rom_id]
                        ROMFile = FileName(rom['filename'])
                        rom_basename_noext = ROMFile.getBase_noext()
                        log_verb('Checking ROM "{0}" (ID {1})'.format(ROMFile.getBase(), rom_id))

                        # --- Search assets ---
                        for i, asset in enumerate(ROM_ASSET_LIST):
                            AInfo = assets_get_info_scheme(asset)
                            # log_debug('Search  {0}'.format(AInfo.name))
                            if not enabled_asset_list[i]: continue
                            # >> Only look for local asset if current file do not exists. This avoid
                            # >> clearing user-customised assets. Also, first check if the field
                            # >> is defined (which is very quick) to avoid an extra filesystem 
                            # >> exist check() for missing images.
                            if rom[AInfo.key]:
                                # >> However, if the artwork is a substitution from the PClone group
                                # >> and the user updated the artwork collection for this ROM the 
                                # >> new image will not be picked with the current implementation ...
                                #
                                # >> How to differentiate substituted PClone artwork from user
                                # >> manually customised artwork???
                                # >> If directory is different it is definitely customised.
                                # >> If directory is the same and the basename is from a ROM in the
                                # >> PClone group it is very likely it is substituted.
                                current_asset_FN = FileName(rom[AInfo.key])
                                if current_asset_FN.exists():
                                    log_debug('Local {0:<9} "{1}"'.format(AInfo.name, current_asset_FN.getPath()))
                                    continue
                            # >> Old implementation (slow). Using FileName().exists() to check many
                            # >> files becames really slow.
                            # asset_dir = FileName(launcher[AInfo.path_key])
                            # local_asset = misc_look_for_file(asset_dir, rom_basename_noext, AInfo.exts)
                            # >> New implementation using a cache.
                            local_asset = misc_search_file_cache(launcher[AInfo.path_key], rom_basename_noext, AInfo.exts)
                            if local_asset:
                                rom[AInfo.key] = local_asset.getOriginalPath()
                                log_debug('Found {0:<9} "{1}"'.format(AInfo.name, local_asset.getPath()))
                            else:
                                rom[AInfo.key] = ''
                                log_debug('Miss  {0:<9}'.format(AInfo.name))
                        # --- Update progress dialog ---
                        item_counter += 1
                        pDialog.update((item_counter*100)/num_items)
                    pDialog.update(100)
                    pDialog.close()

                    # --- Crete Parent/Clone dictionaries ---
                    # --- Traverse ROM list and check assets in the PClone group ---
                    # >> This is only available if a No-Intro/Redump DAT is configured. If not, warn the user.
                    if self.settings['audit_pclone_assets'] and not launcher['nointro_xml_file']:
                        log_info('Use assets in the Parent/Clone group is ON. No-Intro/Redump DAT not configured.')
                        kodi_dialog_OK('No-Intro/Redump DAT not configured and audit_pclone_assets is True. ' +
                                       'Cancelling looking for assets in the Parent/Clone group.')
                    elif self.settings['audit_pclone_assets'] and launcher['nointro_xml_file']:
                        log_info('Use assets in the Parent/Clone group is ON. Loading Parent/Clone dictionaries.')
                        roms_pclone_index = fs_load_JSON_file(ROMS_DIR, launcher['roms_base_noext'] + '_index_PClone')
                        clone_parent_dic  = fs_load_JSON_file(ROMS_DIR, launcher['roms_base_noext'] + '_index_CParent')
                        pDialog.create('Advanced Emulator Launcher', 'Searching for assets/artwork in the Parent/Clone group ...')
                        num_items = len(roms)
                        item_counter = 0
                        for rom_id in roms:
                            # --- Search assets for current ROM ---
                            rom = roms[rom_id]
                            ROMFile = FileName(rom['filename'])
                            rom_basename_noext = ROMFile.getBase_noext()
                            log_verb('Checking ROM "{0}" (ID {1})'.format(ROMFile.getBase(), rom_id))

                            # --- Make a PClone group list for this ROM ---
                            if rom_id in roms_pclone_index:
                                parent_id = rom_id
                                num_clones = len(roms_pclone_index[rom_id])
                                log_debug('ROM is a parent (parent ID {0} / {1} clones)'.format(parent_id, num_clones))
                            else:
                                parent_id = clone_parent_dic[rom_id]
                                log_debug('ROM is a clone (parent ID {0})'.format(parent_id))
                            pclone_set_id_list = []
                            pclone_set_id_list.append(parent_id)
                            pclone_set_id_list += roms_pclone_index[parent_id]
                            # >> Remove current ROM from PClone group
                            pclone_set_id_list.remove(rom_id)
                            # log_debug(unicode(pclone_set_id_list))
                            log_debug('PClone group list has {0} ROMs (after stripping current ROM)'.format(len(pclone_set_id_list)))
                            if len(pclone_set_id_list) == 0: continue

                            # --- Search assets ---
                            for i, asset in enumerate(ROM_ASSET_LIST):
                                AInfo = assets_get_info_scheme(asset)
                                # log_debug('Search  {0}'.format(AInfo.name))
                                if not enabled_asset_list[i]: continue
                                asset_DB_file = rom[AInfo.key]
                                # >> Only search for asset in the PClone group if asset is missing
                                # >> from current ROM.
                                if not asset_DB_file:
                                    # log_debug('Search  {0} in PClone set'.format(AInfo.name))
                                    for set_rom_id in pclone_set_id_list:
                                        # ROMFile_t = FileName(roms[set_rom_id]['filename'])
                                        # log_debug('PClone group ROM "{0}" (ID) {1})'.format(ROMFile_t.getBase(), set_rom_id))
                                        asset_DB_file_t = roms[set_rom_id][AInfo.key]
                                        if asset_DB_file_t:
                                            rom[AInfo.key] = asset_DB_file_t
                                            log_debug('Found {0:<9} "{1}"'.format(AInfo.name, asset_DB_file_t))
                                            # >> Stop as soon as one asset is found in the group.
                                            break
                                    # >> The else statement is executed when the loop has exhausted iterating the list.
                                    else:
                                        log_debug('Miss  {0:<9}'.format(AInfo.name))
                                else:
                                    log_debug('Has   {0:<9}'.format(AInfo.name))
                            # >> Update progress dialog
                            item_counter += 1
                            pDialog.update((item_counter*100)/num_items)
                        pDialog.update(100)
                        pDialog.close()

                    # --- Update assets on _parents.json ---
                    # >> Here only assets s_* are changed. I think it is not necessary to audit ROMs again.
                    pDialog.create('Advanced Emulator Launcher', 'Saving ROM JSON database ...')
                    if launcher['nointro_xml_file']:
                        log_verb('Updating artwork on parent JSON database.')
                        parents_roms_base_noext = launcher['roms_base_noext'] + '_parents'
                        parent_roms = fs_load_JSON_file(ROMS_DIR, parents_roms_base_noext)
                        pDialog.update(25)
                        for parent_rom_id in parent_roms:
                            parent_roms[parent_rom_id]['s_banner']    = roms[parent_rom_id]['s_banner']
                            parent_roms[parent_rom_id]['s_boxback']   = roms[parent_rom_id]['s_boxback']
                            parent_roms[parent_rom_id]['s_boxfront']  = roms[parent_rom_id]['s_boxfront']
                            parent_roms[parent_rom_id]['s_cartridge'] = roms[parent_rom_id]['s_cartridge']
                            parent_roms[parent_rom_id]['s_clearlogo'] = roms[parent_rom_id]['s_clearlogo']
                            parent_roms[parent_rom_id]['s_fanart']    = roms[parent_rom_id]['s_fanart']
                            parent_roms[parent_rom_id]['s_flyer']     = roms[parent_rom_id]['s_flyer']
                            parent_roms[parent_rom_id]['s_manual']    = roms[parent_rom_id]['s_manual']
                            parent_roms[parent_rom_id]['s_map']       = roms[parent_rom_id]['s_map']
                            parent_roms[parent_rom_id]['s_snap']      = roms[parent_rom_id]['s_snap']
                            parent_roms[parent_rom_id]['s_title']     = roms[parent_rom_id]['s_title']
                            parent_roms[parent_rom_id]['s_trailer']   = roms[parent_rom_id]['s_trailer']
                        fs_write_JSON_file(ROMS_DIR, parents_roms_base_noext, parent_roms)

                    # ~~~ Save ROMs XML file ~~~
                    pDialog.update(50)
                    fs_write_ROMs_JSON(ROMS_DIR, launcher, roms)
                    pDialog.update(100)
                    pDialog.close()
                    kodi_notify('Rescaning of ROMs local artwork finished')

                # --- Remove Remove dead/missing ROMs ROMs ---
                elif type2 == 3:
                    if self.launchers[launcherID]['nointro_xml_file']:
                        ret = kodi_dialog_yesno('This launcher has an XML DAT configured. Removing '
                                                'dead ROMs will disable the DAT file. '
                                                'Are you sure you want to remove missing/dead ROMs?')
                    else:
                        ret = kodi_dialog_yesno('Are you sure you want to remove missing/dead ROMs?')
                    if not ret: return

                    # --- Load ROMs for this launcher ---
                    roms = fs_load_ROMs_JSON(ROMS_DIR, self.launchers[launcherID])

                    # --- Remove dead ROMs ---
                    num_removed_roms = self._roms_delete_missing_ROMs(roms)

                    # --- If there is a No-Intro XML DAT configured remove it ---
                    if self.launchers[launcherID]['nointro_xml_file']:
                        log_info('Deleting XML DAT file and forcing launcher to Normal view mode.')
                        self.launchers[launcherID]['nointro_xml_file'] = ''

                    # ~~~ Save ROMs XML file ~~~
                    # >> Launcher saved at the end of the function / launcher timestamp updated.
                    pDialog = xbmcgui.DialogProgress()
                    pDialog.create('Advanced Emulator Launcher', 'Saving ROM JSON database ...')
                    fs_write_ROMs_JSON(ROMS_DIR, self.launchers[launcherID], roms)
                    pDialog.update(100)
                    pDialog.close()
                    self.launchers[launcherID]['num_roms'] = len(roms)
                    kodi_notify('Removed {0} dead ROMs'.format(num_removed_roms))

                # --- Import ROM metadata from NFO files ---
                elif type2 == 4:
                    # >> Load ROMs, iterate and import NFO files
                    roms = fs_load_ROMs_JSON(ROMS_DIR, self.launchers[launcherID])
                    num_read_NFO_files = 0
                    for rom_id in roms:
                        if fs_import_ROM_NFO(roms, rom_id, verbose = False): num_read_NFO_files += 1
                    # >> Save ROMs XML file / Launcher/timestamp saved at the end of function
                    pDialog = xbmcgui.DialogProgress()
                    pDialog.create('Advanced Emulator Launcher', 'Saving ROM JSON database ...')
                    fs_write_ROMs_JSON(ROMS_DIR, self.launchers[launcherID], roms)
                    pDialog.update(100)
                    pDialog.close()
                    kodi_notify('Imported {0} NFO files'.format(num_read_NFO_files))

                # --- Export ROM metadata to NFO files ---
                elif type2 == 5:
                    # >> Load ROMs for current launcher, iterate and write NFO files
                    roms = fs_load_ROMs_JSON(ROMS_DIR, self.launchers[launcherID])
                    if not roms: return
                    kodi_busydialog_ON()
                    num_nfo_files = 0
                    for rom_id in roms:
                        # >> Skip No-Intro Added ROMs
                        if not roms[rom_id]['filename']: continue
                        fs_export_ROM_NFO(roms[rom_id], verbose = False)
                        num_nfo_files += 1
                    kodi_busydialog_OFF()
                    # >> No need to save launchers XML / Update container
                    kodi_notify('Created {0} NFO files'.format(num_nfo_files))
                    return

                # --- Delete ROMs metadata NFO files ---
                elif type2 == 6:
                    # --- Get list of NFO files ---
                    ROMPath_FileName = FileName(self.launchers[launcherID]['rompath'])
                    log_verb('_command_edit_launcher() NFO dirname "{0}"'.format(ROMPath_FileName.getPath()))

                    nfo_scanned_files = ROMPath_FileName.recursiveScanFilesInPath('*.nfo')
                    if len(nfo_scanned_files) > 0:
                        log_verb('_command_edit_launcher() Found {0} NFO files.'.format(len(nfo_scanned_files)))
                        #for filename in nfo_scanned_files:
                        #     log_verb('_command_edit_launcher() Found NFO file "{0}"'.format(filename))
                        ret = kodi_dialog_yesno('Found {0} NFO files. Delete them?'.format(len(nfo_scanned_files)))
                        if not ret: return
                    else:
                        kodi_dialog_OK('No NFO files found. Nothing to delete.')
                        return

                    # --- Delete NFO files ---
                    for file in nfo_scanned_files:
                        log_verb('_command_edit_launcher() RM "{0}"'.format(file))
                        FileName(file).unlink()

                    # >> No need to save launchers XML / Update container
                    kodi_notify('Deleted {0} NFO files'.format(len(nfo_scanned_files)))
                    return

                # --- Empty Launcher ROMs ---
                elif type2 == 7:
                    roms = fs_load_ROMs_JSON(ROMS_DIR, self.launchers[launcherID])
                    num_roms = len(roms)

                    # If launcher is empty (no ROMs) do nothing
                    if num_roms == 0:
                        kodi_dialog_OK('Launcher has no ROMs. Nothing to do.')
                        return

                    # Confirm user wants to delete ROMs
                    dialog = xbmcgui.Dialog()
                    ret = dialog.yesno('Advanced Emulator Launcher',
                                       "Launcher '{0}' has {1} ROMs. Are you sure you want to delete them "
                                       "from AEL database?".format(self.launchers[launcherID]['m_name'], num_roms))
                    if not ret: return

                    # --- If there is a No-Intro XML DAT configured remove it ---
                    if self.launchers[launcherID]['nointro_xml_file']:
                        log_info('Deleting XML DAT file and forcing launcher to Normal view mode.')
                        self.launchers[launcherID]['nointro_xml_file'] = ''

                    # Just remove ROMs database files. Keep the value of roms_base_noext to be reused 
                    # when user add more ROMs.
                    fs_unlink_ROMs_database(ROMS_DIR, self.launchers[launcherID])
                    self.launchers[launcherID]['num_roms'] = 0
                    kodi_notify('Cleared ROMs from launcher database')

        # --- Audit ROMs / Launcher view mode ---
        # NOTE ONLY for ROM launchers, not for standalone launchers
        #
        # >>> New No-Intro/Redump DAT file management <<<
        # A) If the user adds a No-Intro/Redump DAT, ROMs will be audited automatically after addition
        #    of the DAT file.
        # B) If the DAT file cannot be loaded or the audit cannot be completed, 'xml_dat_file'
        #    will be set to ''. Hence, if 'xml_dat_file' is not empty launcher ROMs have been audited.
        # C) The audit will be refreshed every time a change is made to the ROMs of the launcher 
        #    to keep Parent/Clone database consistency.
        # D) There is no option to delete the added Missing ROMs, but the user can choose to display 
        #    them or not.
        # E) To remove the audit status and revert the launcher back to normal, user must delete the 
        #    No-Intro/Redump DAT file.
        #
        if self.launchers[launcherID]['rompath'] != '':
            type_nb = type_nb + 1
            if type == type_nb:
                dialog = xbmcgui.Dialog()
                launcher = self.launchers[launcherID]
                has_NoIntro_DAT = True if launcher['nointro_xml_file'] else False
                if has_NoIntro_DAT:
                    nointro_xml_file = launcher['nointro_xml_file']
                    add_delete_NoIntro_str = 'Delete No-Intro/Redump DAT: {0}'.format(nointro_xml_file)
                else:
                    add_delete_NoIntro_str = 'Add No-Intro/Redump XML DAT ...'
                display_mode_str = launcher['launcher_display_mode']
                type2 = dialog.select('Audit ROMs / Launcher view mode',
                                      ['Change launcher display mode (now {0}) ...'.format(display_mode_str),
                                       add_delete_NoIntro_str,
                                       'Create Parent/Clone DAT based on ROM filenames',
                                       'Display ROMs (now {0}) ...'.format(launcher['nointro_display_mode']),
                                       'Update ROM audit'])
                if type2 < 0: return # >> User canceled select dialog

                # --- Change launcher view mode (Normal or PClone) ---
                if type2 == 0:
                    launcher = self.launchers[launcherID]
                    # >> Krypton feature: preselect the current item.
                    # >> NOTE Preselect must be called with named parameter, otherwise it does not work well.
                    display_mode = launcher['launcher_display_mode']
                    if   display_mode == LAUNCHER_DMODE_FLAT:   p_idx = 0
                    elif display_mode == LAUNCHER_DMODE_PCLONE: p_idx = 1
                    elif display_mode == LAUNCHER_DMODE_1G1R:   p_idx = 2
                    else:                                       p_idx = 0
                    log_debug('p_idx = "{0}"'.format(p_idx))
                    type_temp = dialog.select('Launcher display mode', LAUNCHER_DMODE_LIST, preselect = p_idx)
                    if type_temp < 0: return

                    # >> LAUNCHER_DMODE_FLAT
                    if type_temp == 0:
                        # --- Delete PClone index and Parent ROMs DB to save disk space ---

                        # --- Mark status ---
                        launcher['launcher_display_mode'] = LAUNCHER_DMODE_FLAT
                        log_debug('launcher_display_mode = {0}'.format(launcher['launcher_display_mode']))
                        kodi_notify('Launcher view mode set to {0}'.format(LAUNCHER_DMODE_FLAT))

                    # >> LAUNCHER_DMODE_PCLONE = 1
                    # >> LAUNCHER_DMODE_1G1R = 2
                    elif type_temp == 1 or type_temp == 2:
                        # >> Check if user configured a No-Intro DAT. If not configured  or file does
                        # >> not exists refuse to switch to PClone view and force normal mode.
                        nointro_xml_file = launcher['nointro_xml_file']
                        nointro_xml_file_FName = FileName(nointro_xml_file)
                        if not nointro_xml_file:
                            log_info('_command_edit_launcher() No-Intro DAT not configured.')
                            log_info('_command_edit_launcher() Forcing Flat view mode.')
                            kodi_dialog_OK('No-Intro DAT not configured. PClone or 1G1R view mode cannot be set.')
                            launcher['launcher_display_mode'] = LAUNCHER_DMODE_FLAT
                            kodi_notify('Launcher view mode set to {0}'.format(LAUNCHER_DMODE_FLAT))

                        elif not nointro_xml_file_FName.exists():
                            log_info('_command_edit_launcher() No-Intro DAT not found.')
                            log_info('_command_edit_launcher() Forcing Flat view mode.')
                            kodi_dialog_OK('No-Intro DAT cannot be found. PClone or 1G1R view mode cannot be set.')
                            launcher['launcher_display_mode'] = LAUNCHER_DMODE_FLAT
                            kodi_notify('Launcher view mode set to {0}'.format(LAUNCHER_DMODE_FLAT))

                        else:
                            # --- Re/Generate PClone index and Parent ROMs databases ---

                            # >> LAUNCHER_DMODE_PCLONE = 1
                            if type_temp == 1:
                                launcher['launcher_display_mode'] = LAUNCHER_DMODE_PCLONE
                                log_debug('launcher_display_mode = {0}'.format(launcher['launcher_display_mode']))
                                kodi_notify('Launcher view mode set to {0}'.format(LAUNCHER_DMODE_PCLONE))
                            # >> LAUNCHER_DMODE_1G1R = 2
                            elif type_temp == 2:
                                launcher['launcher_display_mode'] = LAUNCHER_DMODE_1G1R
                                log_debug('launcher_display_mode = {0}'.format(launcher['launcher_display_mode']))
                                kodi_notify('Launcher view mode set to {0}'.format(LAUNCHER_DMODE_1G1R))

                # --- Add/Delete No-Intro XML parent-clone DAT ---
                elif type2 == 1:
                    if has_NoIntro_DAT:
                        dialog = xbmcgui.Dialog()
                        ret = dialog.yesno('Advanced Emulator Launcher', 'Delete No-Intro/Redump XML DAT file?')
                        if not ret: return
                        self.launchers[launcherID]['nointro_xml_file'] = ''
                        kodi_dialog_OK('No-Intro DAT deleted. No-Intro Missing ROMs will be removed now.')

                        # --- Remove No-Intro status and delete missing/dead ROMs to revert launcher to normal ---
                        # Note that roms dictionary is updated using Python pass by assigment.
                        # _roms_reset_NoIntro_status() does not save ROMs JSON/XML.
                        launcher = self.launchers[launcherID]
                        roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)
                        self._roms_reset_NoIntro_status(launcher, roms)
                        fs_write_ROMs_JSON(ROMS_DIR, launcher, roms)
                        launcher['num_roms'] = len(roms)
                        kodi_notify('Removed No-Intro/Redump XML DAT file')

                    else:
                        # --- Browse for No-Intro file ---
                        # BUG For some reason *.dat files are not shown on the dialog, but XML files are OK!!!
                        # Fixed in Krypton Beta 6 http://forum.kodi.tv/showthread.php?tid=298161
                        dialog = xbmcgui.Dialog()
                        dat_file = dialog.browse(1, 'Select No-Intro XML DAT (XML|DAT)', 'files', '.dat|.xml').decode('utf-8')
                        if not FileName(dat_file).exists(): return
                        self.launchers[launcherID]['nointro_xml_file'] = dat_file
                        kodi_dialog_OK('DAT file successfully added. Launcher ROMs will be audited now.')

                        # --- Audit ROMs ---
                        # Note that roms and launcher dictionaries are updated using Python pass by assigment.
                        # _roms_update_NoIntro_status() does not save ROMs JSON/XML.
                        launcher = self.launchers[launcherID]
                        roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)
                        nointro_xml_FN = FileName(launcher['nointro_xml_file'])
                        if self._roms_update_NoIntro_status(launcher, roms, nointro_xml_FN):
                            fs_write_ROMs_JSON(ROMS_DIR, launcher, roms)
                            kodi_notify('Added No-Intro/Redump XML DAT. '
                                        'Have {0} / Miss {1} / Unknown {2}'.format(self.audit_have, self.audit_miss, self.audit_unknown))
                        else:
                            # >> ERROR when auditing the ROMs. Unset nointro_xml_file
                            self.launchers[launcherID]['nointro_xml_file'] = ''
                            kodi_notify_warn('Error auditing ROMs. XML DAT file not set.')
                        launcher['num_roms'] = len(roms)

                # --- Create Parent/Clone DAT based on ROM filenames ---
                elif type2 == 2:
                    if has_NoIntro_DAT:
                        d = xbmcgui.Dialog()
                        ret = d.yesno('Advanced Emulator Launcher',
                                      'This Launcher has a DAT file attached. Creating a filename '
                                      'based DAT will remove the No-Intro/Redump DAT. Continue?')
                        if not ret: return
                        # >> Delete No-Intro/Redump DAT and reset ROM audit.
                    
                    # >> Create an artificial <roms_base_noext>_DAT.json file. Keep launcher
                    # >> nointro_xml_file = '' because the artificial DAT is not an official DAT.
                    kodi_dialog_OK('Not implemented yet. Sorry.')
                    return

                # --- Display ROMs ---
                elif type2 == 3:
                    # >> If no DAT configured exit.
                    if not has_NoIntro_DAT:
                        kodi_dialog_OK('No-Intro/Redump XML DAT file not configured.')
                        return

                    # >> In Krypton preselect the current item
                    launcher = self.launchers[launcherID]
                    nointro_display_mode = launcher['nointro_display_mode']
                    if   nointro_display_mode == NOINTRO_DMODE_ALL:       p_idx = 0
                    elif nointro_display_mode == NOINTRO_DMODE_HAVE:      p_idx = 1
                    elif nointro_display_mode == NOINTRO_DMODE_HAVE_UNK:  p_idx = 2
                    elif nointro_display_mode == NOINTRO_DMODE_HAVE_MISS: p_idx = 3
                    elif nointro_display_mode == NOINTRO_DMODE_MISS:      p_idx = 4
                    elif nointro_display_mode == NOINTRO_DMODE_MISS_UNK:  p_idx = 5
                    elif nointro_display_mode == NOINTRO_DMODE_UNK:       p_idx = 6
                    else:                                                 p_idx = 0
                    log_debug('p_idx = "{0}"'.format(p_idx))
                    type_temp = dialog.select('Launcher display mode', NOINTRO_DMODE_LIST, preselect = p_idx)
                    if type_temp < 0: return
                    launcher['nointro_display_mode'] = NOINTRO_DMODE_LIST[type_temp]
                    log_info('Launcher display mode changed to "{0}"'.format(launcher['nointro_display_mode']))
                    kodi_notify('Display ROMs changed to "{0}"'.format(launcher['nointro_display_mode']))

                # --- Update ROM audit ---
                elif type2 == 4:
                    # >> If no DAT configured exit.
                    if not has_NoIntro_DAT:
                        kodi_dialog_OK('No-Intro/Redump XML DAT file not configured.')
                        return

                    # Note that roms and launcher dictionaries are updated using Python pass by assigment.
                    # _roms_update_NoIntro_status() does not save ROMs JSON/XML.
                    launcher = self.launchers[launcherID]
                    roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)
                    nointro_xml_FN = FileName(launcher['nointro_xml_file'])
                    if self._roms_update_NoIntro_status(launcher, roms, nointro_xml_FN):
                        pDialog = xbmcgui.DialogProgress()
                        pDialog.create('Advanced Emulator Launcher', 'Saving ROM JSON database ...')
                        fs_write_ROMs_JSON(ROMS_DIR, launcher, roms)
                        pDialog.update(100)
                        pDialog.close()
                        kodi_notify('Have {0} / Miss {1} / Unknown {2}'.format(self.audit_have, self.audit_miss, self.audit_unknown))
                    else:
                        # >> ERROR when auditing the ROMs. Unset nointro_xml_file
                        self.launchers[launcherID]['nointro_xml_file'] = ''
                        kodi_notify_warn('Error auditing ROMs. XML DAT file unset.')
                    launcher['num_roms'] = len(roms)

        # --- Launcher Advanced Modifications menu option ---
        type_nb = type_nb + 1
        if type == type_nb:
            minimize_str = 'ON' if self.launchers[launcherID]['minimize'] else 'OFF'
            non_blocking_str = 'ON' if self.launchers[launcherID]['non_blocking'] else 'OFF'
            filter_str   = '.bat|.exe|.cmd' if sys.platform == 'win32' else ''
            if self.launchers[launcherID]['application'] == RETROPLAYER_LAUNCHER_APP_NAME:
                launcher_str = 'Kodi Retroplayer'
            elif self.launchers[launcherID]['application'] == LNK_LAUNCHER_APP_NAME:
                launcher_str = 'LNK Launcher'
            else:
                launcher_str = "'{0}'".format(self.launchers[launcherID]['application'])

            # --- ROMS launcher -------------------------------------------------------------------
            if self.launchers[launcherID]['rompath'] == '':
                type2 = dialog.select('Launcher Advanced Modifications',
                                      ["Change Application: {0}".format(launcher_str),
                                       "Modify Arguments: '{0}'".format(self.launchers[launcherID]['args']),
                                       "Modify Aditional arguments ...",
                                       "Toggle Kodi into windowed mode (now {0})".format(minimize_str),
                                       "Non-blocking launcher (now {0})".format(non_blocking_str)])
            # --- Standalone launcher -------------------------------------------------------------
            else:
                type2 = dialog.select('Launcher Advanced Modifications',
                                      ["Change Application: {0}".format(launcher_str),
                                       "Modify Arguments: '{0}'".format(self.launchers[launcherID]['args']),
                                       "Aditional arguments ...",
                                       "Change ROM path: '{0}'".format(self.launchers[launcherID]['rompath']),
                                       "Modify ROM extensions: '{0}'".format(self.launchers[launcherID]['romext']),
                                       "Toggle Kodi into windowed mode (now {0})".format(minimize_str),
                                       "Non-blocking launcher (now {0})".format(non_blocking_str)])

            # --- Launcher application path menu option ---
            type2_nb = 0
            if type2 == type2_nb:
                # >> Choose launching mechanism
                LAUNCHER_ROM         = 1
                LAUNCHER_RETROPLAYER = 2
                LAUNCHER_LNK         = 3
                if sys.platform == 'win32':
                    answer = dialog.select('Choose launcher mechanism',
                                          ['Use Kodi Retroplayer',
                                           'Use Windows LNK launcher',
                                           'Choose launching application'])
                    if answer < 0: return
                    if   answer == 0: launcher_type = LAUNCHER_RETROPLAYER
                    elif answer == 1: launcher_type = LAUNCHER_LNK
                    elif answer == 2: launcher_type = LAUNCHER_ROM
                else:
                    answer = kodi_dialog_yesno('Use Kodi Retroplayer in this launcher? '
                                               'Answer NO to choose a new launching application.')
                    if answer: launcher_type = LAUNCHER_RETROPLAYER
                    else:      launcher_type = LAUNCHER_ROM

                # >> Choose launching application
                if launcher_type == LAUNCHER_RETROPLAYER:
                    self.launchers[launcherID]['application'] = RETROPLAYER_LAUNCHER_APP_NAME
                    kodi_notify('Launcher app is Retroplayer')
                elif launcher_type == LAUNCHER_LNK:
                    self.launchers[launcherID]['application'] = LNK_LAUNCHER_APP_NAME
                    kodi_notify('Launcher app is Windows LNK launcher')
                elif launcher_type == LAUNCHER_ROM:
                    app = xbmcgui.Dialog().browse(1, 'Select the launcher application', 'files', '', 
                                                  False, False, self.launchers[launcherID]['application'])
                    if not app: return
                    self.launchers[launcherID]['application'] = app
                    kodi_notify('Changed launcher application')

            # --- Edition of the launcher arguments ---
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                keyboard = xbmc.Keyboard(self.launchers[launcherID]['args'], 'Edit application arguments')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                self.launchers[launcherID]['args'] = keyboard.getText().decode('utf-8')
                kodi_notify('Changed launcher arguments')

            # --- Launcher Additional arguments ---
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                launcher = self.launchers[launcherID]
                additional_args_list = []
                for extra_arg in launcher['args_extra']:
                    additional_args_list.append("Modify '{0}'".format(extra_arg))
                type_aux = dialog.select('Launcher additional arguments',
                                         ['Add new additional arguments ...'] + additional_args_list)
                if type_aux < 0: return

                # >> Add new additional arguments
                if type_aux == 0:
                    keyboard = xbmc.Keyboard('', 'Edit launcher additional arguments')
                    keyboard.doModal()
                    if not keyboard.isConfirmed(): return
                    launcher['args_extra'].append(keyboard.getText().decode('utf-8'))
                    log_debug('_command_edit_launcher() Appending extra_args to launcher {0}'.format(launcherID))
                    kodi_notify('Added additional arguments in position {0}'.format(len(launcher['args_extra'])))
                elif type_aux >= 1:
                    arg_index = type_aux - 1
                    type_aux_2 = dialog.select('Modify extra arguments {0}'.format(type_aux),
                                               ["Edit '{0}' ...".format(launcher['args_extra'][arg_index]), 
                                                'Delete extra arguments'])
                    if type_aux_2 < 0: return

                    if type_aux_2 == 0:
                        keyboard = xbmc.Keyboard(launcher['args_extra'][arg_index], 'Edit application arguments')
                        keyboard.doModal()
                        if not keyboard.isConfirmed(): return
                        launcher['args_extra'][arg_index] = keyboard.getText().decode('utf-8')
                        log_debug('_command_edit_launcher() Edited args_extra[{0}] to "{1}"'.format(arg_index, launcher['args_extra'][arg_index]))
                        kodi_notify('Changed launcher extra arguments {0}'.format(type_aux))
                    elif type_aux_2 == 1:
                        ret = kodi_dialog_yesno('Are you sure you want to delete Launcher additional arguments {0}?'.format(type_aux))
                        if not ret: return
                        del launcher['args_extra'][arg_index]
                        log_debug("_command_edit_launcher() Deleted launcher['args_extra'][{0}]".format(arg_index))
                        kodi_notify('Changed launcher extra arguments {0}'.format(type_aux))

            if self.launchers[launcherID]['rompath'] != '':
                # --- Launcher roms path menu option ---
                type2_nb = type2_nb + 1
                if type2 == type2_nb:
                    rom_path = dialog.browse(0, 'Select Files path', 'files', '',
                                             False, False, self.launchers[launcherID]['rompath']).decode('utf-8')
                    self.launchers[launcherID]['rompath'] = rom_path
                    kodi_notify('Changed ROM path')

                # --- Edition of the launcher rom extensions (only for emulator launcher) ---
                type2_nb = type2_nb + 1
                if type2 == type2_nb:
                    keyboard = xbmc.Keyboard(self.launchers[launcherID]['romext'],
                                             'Edit ROM extensions, use "|" as separator. (e.g lnk|cbr)')
                    keyboard.doModal()
                    if not keyboard.isConfirmed(): return
                    self.launchers[launcherID]['romext'] = keyboard.getText().decode('utf-8')
                    kodi_notify('Changed ROM extensions')

            # --- Minimise Kodi window flag ---
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                p_idx = 1 if self.launchers[launcherID]['minimize'] else 0
                type3 = dialog.select('Toggle Kodi into windowed mode', ['OFF (default)', 'ON'], preselect = p_idx)
                if type3 < 0: return
                self.launchers[launcherID]['minimize'] = True if type3 == 1 else False
                minimise_str = 'ON' if self.launchers[launcherID]['minimize'] else 'OFF'
                kodi_notify('Toggle Kodi into windowed mode {0}'.format(minimise_str))

            # --- Non-blocking launcher flag ---
            type2_nb = type2_nb + 1
            if type2 == type2_nb:
                p_idx = 1 if self.launchers[launcherID]['non_blocking'] else 0
                type3 = dialog.select('Non-blocking launcher', ['OFF (default)', 'ON'], preselect = p_idx)
                if type3 < 0: return
                self.launchers[launcherID]['non_blocking'] = True if type3 == 1 else False
                non_blocking_str = 'ON' if self.launchers[launcherID]['non_blocking'] else 'OFF'
                kodi_notify('Launcher Non-blocking is {0}'.format(non_blocking_str))

        # --- Remove Launcher menu option ---
        type_nb = type_nb + 1
        if type == type_nb:
            rompath       = self.launchers[launcherID]['rompath']
            launcher_name = self.launchers[launcherID]['m_name']
            # >> Standalone launcher
            if rompath == '':
                ret = kodi_dialog_yesno('Launcher "{0}" is standalone. '.format(launcher_name) +
                                        'Are you sure you want to delete it?')
            # >> ROMs launcher
            else:
                roms = fs_load_ROMs_JSON(ROMS_DIR, self.launchers[launcherID])
                num_roms = len(roms)
                ret = kodi_dialog_yesno('Launcher "{0}" has {1} ROMs. '.format(launcher_name, num_roms) +
                                        'Are you sure you want to delete it?')
            if not ret: return

            # --- Remove JSON/XML file if exist ---
            fs_unlink_ROMs_database(ROMS_DIR, self.launchers[launcherID])

            # --- Remove launcher from database. Categories.xml will be saved at the end of function ---
            self.launchers.pop(launcherID)
            kodi_notify('Deleted launcher {0}'.format(launcher_name))

        # User pressed cancel or close dialog
        if type < 0: return

        # >> If this point is reached then changes to launcher metadata/assets were made.
        # >> Save categories and update container contents so user sees those changes inmediately.
        # NOTE Update edited launcher timestamp only if launcher was not deleted!
        if launcherID in self.launchers:
            self.launchers[launcherID]['timestamp_launcher'] = time.time()
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_refresh_container()

    #
    # Add ROMS to launcher
    #
    def _command_add_roms(self, launcher):
        dialog = xbmcgui.Dialog()
        type = dialog.select('Add/Update ROMs to Launcher', ['Scan for New ROMs', 'Manually Add ROM'])
        if type == 0:
            self._roms_import_roms(launcher)
        elif type == 1:
            self._roms_add_new_rom(launcher)

    #
    # Former _edit_rom()
    # Note that categoryID = VCATEGORY_FAVOURITES_ID, launcherID = VLAUNCHER_FAVOURITES_ID if we are editing
    # a ROM in Favourites.
    #
    def _command_edit_rom(self, categoryID, launcherID, romID):
        # --- ---
        if romID == UNKNOWN_ROMS_PARENT_ID:
            kodi_dialog_OK('You cannot edit this ROM!')
            return

        # --- Load ROMs ---
        if categoryID == VCATEGORY_FAVOURITES_ID:
            log_debug('_command_edit_rom() Editing Favourite ROM')
            roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            log_debug('_command_edit_rom() Editing Collection ROM')
            (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
            collection = collections[launcherID]

            roms_json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
            collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
            # NOTE ROMs in a collection are stored as a list and ROMs in Favourites are stored as
            #      a dictionary. Convert the Collection list into an ordered dictionary and then
            #      converted back the ordered dictionary into a list before saving the collection.
            roms = OrderedDict()
            for collection_rom in collection_rom_list:
                roms[collection_rom['id']] = collection_rom
        else:
            log_debug('_command_edit_rom() Editing ROM in Launcher')
            launcher = self.launchers[launcherID]
            roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)

        # --- Show a dialog with ROM editing options ---
        rom_name = roms[romID]['m_name']
        finished_display = 'Status: Finished' if roms[romID]['finished'] == True else 'Status: Unfinished'
        dialog = xbmcgui.Dialog()
        if categoryID == VCATEGORY_FAVOURITES_ID:
            type = dialog.select('Edit ROM {0}'.format(rom_name),
                                ['Edit Metadata ...', 'Edit Assets/Artwork ...', finished_display,
                                 'Advanced Modifications ...',
                                 'Delete Favourite ROM',
                                 'Manage Favourite ROM object ...'])
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            type = dialog.select('Edit ROM {0}'.format(rom_name),
                                ['Edit Metadata ...', 'Edit Assets/Artwork ...', finished_display,
                                 'Advanced Modifications ...',
                                 'Delete Collection ROM',
                                 'Manage Collection ROM object ...',
                                 'Manage Collection ROM position ...'])
        else:
            type = dialog.select('Edit ROM {0}'.format(rom_name),
                                ['Edit Metadata ...', 'Edit Assets/Artwork ...', finished_display,
                                 'Advanced Modifications ...',
                                 'Delete ROM'])
        if type < 0: return

        # --- Edit ROM metadata ---
        if type == 0:
            # >> Make a list of available metadata scrapers
            scraper_obj_list  = []
            scraper_menu_list = []
            for scrap_obj in scrapers_metadata:
                scraper_obj_list.append(scrap_obj)
                scraper_menu_list.append('Scrape metadata from {0} ...'.format(scrap_obj.name))
                log_verb('Added metadata scraper {0}'.format(scrap_obj.name))

            # >> Metadata edit dialog
            dialog = xbmcgui.Dialog()
            desc_str = text_limit_string(roms[romID]['m_plot'], DESCRIPTION_MAXSIZE)
            menu_list = ["Edit Title: '{0}'".format(roms[romID]['m_name']),
                         "Edit Release Year: '{0}'".format(roms[romID]['m_year']),
                         "Edit Genre: '{0}'".format(roms[romID]['m_genre']),
                         "Edit Developer: '{0}'".format(roms[romID]['m_developer']),
                         "Edit NPlayers: '{0}'".format(roms[romID]['m_nplayers']),
                         "Edit ESRB rating: '{0}'".format(roms[romID]['m_esrb']),
                         "Edit Rating: '{0}'".format(roms[romID]['m_rating']),
                         "Edit Plot: '{0}'".format(desc_str),
                         'Load Plot from TXT file ...',
                         'Import metadata from NFO file ...',
                         'Save metadata to NFO file']
            type2 = dialog.select('Modify ROM metadata', menu_list + scraper_menu_list)
            if type2 < 0: return

            # --- Edit of the rom title ---
            if type2 == 0:
                keyboard = xbmc.Keyboard(roms[romID]['m_name'], 'Edit Title')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                title = keyboard.getText().decode('utf-8')
                if title == '': title = roms[romID]['m_name']
                roms[romID]['m_name'] = title
                kodi_notify('Changed ROM Title')

            # --- Edition of the rom release year ---
            elif type2 == 1:
                keyboard = xbmc.Keyboard(roms[romID]['m_year'], 'Edit Release Year')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]['m_year'] = keyboard.getText().decode('utf-8')
                kodi_notify('Changed ROM Release Year')

            # --- Edition of the rom game genre ---
            elif type2 == 2:
                keyboard = xbmc.Keyboard(roms[romID]['m_genre'], 'Edit genre')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]['m_genre'] = keyboard.getText().decode('utf-8')
                kodi_notify('Changed ROM Genre')

            # --- Edition of the rom developer ---
            elif type2 == 3:
                keyboard = xbmc.Keyboard(roms[romID]['m_developer'], 'Edit developer')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]['m_developer'] = keyboard.getText().decode('utf-8')
                kodi_notify('Changed ROM Developer')

            # --- Edition of launcher NPlayers ---
            elif type2 == 4:
                # >> Show a dialog select with the most used NPlayer entries, and have one option
                # >> for manual entry.
                menu_list = ['Not set', 'Manual entry'] + NPLAYERS_LIST
                np_idx = dialog.select('Edit Launcher NPlayers', menu_list)
                if np_idx < 0: return

                if np_idx == 0:
                    roms[romID]['m_nplayers'] = ''
                    kodi_notify('Launcher NPlayers change to Not Set')
                elif np_idx == 1:
                    # >> Manual entry. Open a text entry dialog.
                    keyboard = xbmc.Keyboard(roms[romID]['m_nplayers'], 'Edit NPlayers')
                    keyboard.doModal()
                    if not keyboard.isConfirmed(): return
                    roms[romID]['m_nplayers'] = keyboard.getText().decode('utf-8')
                    kodi_notify('Changed Launcher NPlayers')
                else:
                    list_idx = np_idx - 2
                    roms[romID]['m_nplayers'] = NPLAYERS_LIST[list_idx]
                    kodi_notify('Changed Launcher NPlayers')

            # --- Edition of launcher ESRB rating ---
            elif type2 == 5:
                # >> Show a dialog select with the available ratings
                # >> Kodi Krypton: preselect current rating in select list
                esrb_index = dialog.select('Edit Launcher ESRB rating', ESRB_LIST)
                if esrb_index < 0: return
                roms[romID]['m_esrb'] = ESRB_LIST[esrb_index]
                kodi_notify('Changed Launcher ESRB rating')

            # --- Edition of the ROM rating ---
            elif type2 == 6:
                rating = dialog.select('Edit ROM Rating',
                                      ['Not set',  'Rating 0', 'Rating 1', 'Rating 2', 'Rating 3', 'Rating 4',
                                       'Rating 5', 'Rating 6', 'Rating 7', 'Rating 8', 'Rating 9', 'Rating 10'])
                # >> Rating not set, empty string
                if rating == 0:
                    roms[romID]['m_rating'] = ''
                    kodi_notify('Changed ROM Rating to Not Set')
                elif rating >= 1 and rating <= 11:
                    roms[romID]['m_rating'] = '{0}'.format(rating - 1)
                    kodi_notify('Changed ROM Rating to {0}'.format(roms[romID]['m_rating']))
                elif rating < 0:
                    kodi_dialog_OK("ROM rating '{0}' not changed".format(roms[romID]['m_rating']))
                    return

            # --- Edit ROM description (plot) ---
            elif type2 == 7:
                keyboard = xbmc.Keyboard(roms[romID]['m_plot'], 'Edit plot')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]['m_plot'] = keyboard.getText().decode('utf-8')
                kodi_notify('Changed ROM Plot')

            # --- Import of the rom game plot from TXT file ---
            elif type2 == 8:
                dialog = xbmcgui.Dialog()
                text_file = dialog.browse(1, 'Select description file (TXT|DAT)', 
                                          'files', '.txt|.dat', False, False).decode('utf-8')
                text_file_path = FileName(text_file)
                if text_file_path.exists():
                    file_data = self._gui_import_TXT_file(text_file_path)
                    roms[romID]['m_plot'] = file_data
                    kodi_notify('Imported ROM Plot')
                else:
                    desc_str = text_limit_string(roms[romID]['m_plot'], DESCRIPTION_MAXSIZE)
                    kodi_dialog_OK("Launcher plot '{0}' not changed".format(desc_str))
                    return

            # --- Import ROM metadata from NFO file ---
            elif type2 == 9:
                if launcherID == VLAUNCHER_FAVOURITES_ID:
                    kodi_dialog_OK('Importing NFO file is not allowed for ROMs in Favourites.')
                    return
                if not fs_import_ROM_NFO(roms, romID): return

            # --- Export ROM metadata to NFO file ---
            elif type2 == 10:
                if launcherID == VLAUNCHER_FAVOURITES_ID:
                    kodi_dialog_OK('Exporting NFO file is not allowed for ROMs in Favourites.')
                    return
                fs_export_ROM_NFO(roms[romID])
                # >> No need to save ROMs
                return

            # --- Scrap ROM metadata ---
            elif type2 >= 11:
                # --- Use the scraper chosen by user ---
                scraper_index = type2 - 11
                scraper_obj   = scraper_obj_list[scraper_index]
                log_debug('_command_edit_rom() Scraper index {0}'.format(scraper_index))
                log_debug('_command_edit_rom() User chose scraper "{0}"'.format(scraper_obj.name))

                # --- Initialise asset scraper ---
                scraper_obj.set_addon_dir(CURRENT_ADDON_DIR.getPath())
                log_debug('_command_edit_rom() Initialised scraper "{0}"'.format(scraper_obj.name))

                # >> If this returns False there were no changes so no need to save ROMs JSON.
                if not self._gui_scrap_rom_metadata(categoryID, launcherID, romID, roms, scraper_obj): return

        # --- Edit Launcher Assets/Artwork ---
        elif type == 1:
            rom = roms[romID]

            # >> Build asset image list for dialog
            label2_title     = rom['s_title']     if rom['s_title']     else 'Not set'
            label2_snap      = rom['s_snap']      if rom['s_snap']      else 'Not set'
            label2_boxfront  = rom['s_boxfront']  if rom['s_boxfront']  else 'Not set'
            label2_boxback   = rom['s_boxback']   if rom['s_boxback']   else 'Not set'
            label2_cartridge = rom['s_cartridge'] if rom['s_cartridge'] else 'Not set'
            label2_fanart    = rom['s_fanart']    if rom['s_fanart']    else 'Not set'
            label2_banner    = rom['s_banner']    if rom['s_banner']    else 'Not set'
            label2_clearlogo = rom['s_clearlogo'] if rom['s_clearlogo'] else 'Not set'
            label2_flyer     = rom['s_flyer']     if rom['s_flyer']     else 'Not set'
            label2_map       = rom['s_map']       if rom['s_map']       else 'Not set'
            label2_manual    = rom['s_manual']    if rom['s_manual']    else 'Not set'
            label2_trailer   = rom['s_trailer']   if rom['s_trailer']   else 'Not set'
            img_title        = rom['s_title']           if rom['s_title']     else 'DefaultAddonNone.png'
            img_snap         = rom['s_snap']            if rom['s_snap']      else 'DefaultAddonNone.png'
            img_boxfront     = rom['s_boxfront']        if rom['s_boxfront']  else 'DefaultAddonNone.png'
            img_boxback      = rom['s_boxback']         if rom['s_boxback']   else 'DefaultAddonNone.png'
            img_cartridge    = rom['s_cartridge']       if rom['s_cartridge'] else 'DefaultAddonNone.png'
            img_fanart       = rom['s_fanart']          if rom['s_fanart']    else 'DefaultAddonNone.png'
            img_banner       = rom['s_banner']          if rom['s_banner']    else 'DefaultAddonNone.png'
            img_clearlogo    = rom['s_clearlogo']       if rom['s_clearlogo'] else 'DefaultAddonNone.png'
            img_flyer        = rom['s_flyer']           if rom['s_flyer']     else 'DefaultAddonNone.png'
            img_map          = rom['s_map']             if rom['s_map']       else 'DefaultAddonNone.png'
            img_manual       = 'DefaultAddonImages.png' if rom['s_manual']    else 'DefaultAddonNone.png'
            img_trailer      = 'DefaultAddonVideo.png'  if rom['s_trailer']   else 'DefaultAddonNone.png'

            # >> Create ListItem objects for select dialog
            title_listitem     = xbmcgui.ListItem(label = 'Edit Title ...',              label2 = label2_title)
            snap_listitem      = xbmcgui.ListItem(label = 'Edit Snap ...',               label2 = label2_snap)
            boxfront_listitem  = xbmcgui.ListItem(label = 'Edit Boxfront / Cabinet ...', label2 = label2_boxfront)
            boxback_listitem   = xbmcgui.ListItem(label = 'Edit Boxback / CPanel ...',   label2 = label2_boxback)
            cartridge_listitem = xbmcgui.ListItem(label = 'Edit Cartridge / PCB ...',    label2 = label2_cartridge)
            fanart_listitem    = xbmcgui.ListItem(label = 'Edit Fanart ...',             label2 = label2_fanart)
            banner_listitem    = xbmcgui.ListItem(label = 'Edit Banner / Marquee ...',   label2 = label2_banner)
            clearlogo_listitem = xbmcgui.ListItem(label = 'Edit Clearlogo ...',          label2 = label2_clearlogo)
            flyer_listitem     = xbmcgui.ListItem(label = 'Edit Flyer ...',              label2 = label2_flyer)
            map_listitem       = xbmcgui.ListItem(label = 'Edit Map ...',                label2 = label2_map)
            manual_listitem    = xbmcgui.ListItem(label = 'Edit Manual ...',             label2 = label2_manual)
            trailer_listitem   = xbmcgui.ListItem(label = 'Edit Trailer ...',            label2 = label2_trailer)
            title_listitem.setArt({'icon' : img_title})
            snap_listitem.setArt({'icon' : img_snap})
            boxfront_listitem.setArt({'icon' : img_boxfront})
            boxback_listitem.setArt({'icon' : img_boxback})
            cartridge_listitem.setArt({'icon' : img_cartridge})
            fanart_listitem.setArt({'icon' : img_fanart})
            banner_listitem.setArt({'icon' : img_banner})
            clearlogo_listitem.setArt({'icon' : img_clearlogo})
            flyer_listitem.setArt({'icon' : img_flyer})
            map_listitem.setArt({'icon' : img_map})
            manual_listitem.setArt({'icon' : img_manual})
            trailer_listitem.setArt({'icon' : img_trailer})

            # >> Execute select dialog
            listitems = [title_listitem, snap_listitem, boxfront_listitem, boxback_listitem, cartridge_listitem,
                         fanart_listitem, banner_listitem, clearlogo_listitem, 
                         flyer_listitem, map_listitem, manual_listitem, trailer_listitem]
            type2 = dialog.select('Edit ROM Assets/Artwork', list = listitems, useDetails = True)
            if type2 < 0: return

            # --- Edit Assets ---
            # >> If this function returns False no changes were made. No need to save categories XML
            # >> and update container.
            asset_list = [ASSET_TITLE, ASSET_SNAP, ASSET_BOXFRONT, ASSET_BOXBACK, ASSET_CARTRIDGE,
                          ASSET_FANART, ASSET_BANNER, ASSET_CLEARLOGO, 
                          ASSET_FLYER, ASSET_MAP, ASSET_MANUAL, ASSET_TRAILER]
            asset_kind = asset_list[type2]
            if not self._gui_edit_asset(KIND_ROM, asset_kind, rom, categoryID, launcherID): return

        # --- Edit status ---
        elif type == 2:
            finished = roms[romID]['finished']
            finished = False if finished else True
            finished_display = 'Finished' if finished == True else 'Unfinished'
            roms[romID]['finished'] = finished
            kodi_dialog_OK("ROM '{0}' status is now {1}".format(roms[romID]['m_name'], finished_display))

        # --- Advanced ROM Modifications ---
        elif type == 3:
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Advanced ROM Modifications',
                                  ["Change ROM file: '{0}'".format(roms[romID]['filename']),
                                   "Alternative application: '{0}'".format(roms[romID]['altapp']),
                                   "Alternative arguments: '{0}'".format(roms[romID]['altarg']) ])
            if type2 < 0: return

            # >> Change ROM file
            if type2 == 0:
                # >> Abort if multidisc ROM
                if roms[romID]['disks']:
                    kodi_dialog_OK('Edition of multidisc ROMs not supported yet.')
                    return
                filename = roms[romID]['filename']
                launcher = self.launchers[launcherID]
                romext   = launcher['romext']
                item_file = xbmcgui.Dialog().browse(1, 'Select the file', 'files', '.' + romext.replace('|', '|.'),
                                                    False, False, filename).decode('utf-8')
                if not item_file: return
                roms[romID]['filename'] = item_file
            # >> Alternative launcher application file path
            elif type2 == 1:
                filter_str = '.bat|.exe|.cmd' if sys.platform == 'win32' else ''
                altapp = xbmcgui.Dialog().browse(1, 'Select ROM custom launcher application',
                                                 'files', filter_str,
                                                 False, False, roms[romID]['altapp']).decode('utf-8')
                # Returns empty browse if dialog was canceled.
                if not altapp: return
                roms[romID]['altapp'] = altapp
            # >> Alternative launcher arguments
            elif type2 == 2:
                keyboard = xbmc.Keyboard(roms[romID]['altarg'], 'Edit ROM custom application arguments')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                roms[romID]['altarg'] = keyboard.getText().decode('utf-8')

        # --- Delete ROM ---
        elif type == 4:
            is_Normal_Launcher = True
            if categoryID == VCATEGORY_FAVOURITES_ID and launcherID == VLAUNCHER_FAVOURITES_ID:
                log_info('_command_remove_rom() Deleting ROM from Favourites (id {0})'.format(romID))
                msg_str = 'Are you sure you want to delete it from Favourites?'
                is_Normal_Launcher = False
            elif categoryID == VCATEGORY_COLLECTIONS_ID:
                log_info('_command_remove_rom() Deleting ROM from Collection (id {0})'.format(romID))
                msg_str = 'Are you sure you want to delete it from Collection "{0}"?'.format(collection['m_name'])
                is_Normal_Launcher = False
            else:
                if launcher['nointro_xml_file'] and roms[romID]['nointro_status'] == NOINTRO_STATUS_MISS:
                    kodi_dialog_OK('You are trying to remove a Missing ROM. You cannot delete '
                                   'a ROM that does not exist! If you want to get rid of all missing '
                                   'ROMs then delete the XML DAT file.')
                    return
                else:
                    log_info('_command_remove_rom() Deleting ROM from Launcher (id {0})'.format(romID))
                    msg_str = 'Are you sure you want to delete it from Launcher "{0}"?'.format(launcher['m_name'])

            # --- Confirm deletion ---
            rom_name = roms[romID]['m_name']
            ret = kodi_dialog_yesno('ROM "{0}". '.format(rom_name) + msg_str)
            if not ret: return
            roms.pop(romID)

            # --- If there is a No-Intro XML configured audit ROMs ---
            if is_Normal_Launcher and launcher['nointro_xml_file']:
                log_info('No-Intro/Redump DAT configured. Starting ROM audit ...')
                nointro_xml_FN = FileName(launcher['nointro_xml_file'])
                if not self._roms_update_NoIntro_status(launcher, roms, nointro_xml_FN):
                    self.launchers[launcherID]['nointro_xml_file'] = ''
                    kodi_notify_warn('Error auditing ROMs. XML DAT file unset.')

            # --- Notify user ---
            kodi_notify('Deleted ROM {0}'.format(rom_name))

        # --- Manage Favourite/Collection ROM object (ONLY for Favourite/Collection ROMs) ---
        elif type == 5:
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Manage ROM object',
                                  ['Choose another parent ROM (launcher info only) ...', # 0
                                   'Choose another parent ROM (update all) ...',         # 1
                                   'Copy launcher info from parent ROM',                # 2
                                   'Copy metadata from parent ROM',                     # 3
                                   'Copy assets/artwork from parent ROM',               # 4
                                   'Copy all from parent ROM',                          # 5
                                   'Manage default Assets/Artwork ...'])
            if type2 < 0: return

            # --- Choose another parent ROM ---
            if type2 == 0 or type2 == 1:
                # --- STEP 1: select new launcher ---
                launcher_IDs = []
                launcher_names = []
                for launcher_id in self.launchers:
                    # >> ONLY SHOW ROMs LAUNCHERS, NOT STANDALONE LAUNCHERS!!!
                    if self.launchers[launcher_id]['rompath'] == '': continue
                    launcher_IDs.append(launcher_id)
                    launcher_names.append(self.launchers[launcher_id]['m_name'])

                # >> Order alphabetically both lists
                sorted_idx = [i[0] for i in sorted(enumerate(launcher_names), key=lambda x:x[1])]
                launcher_IDs   = [launcher_IDs[i] for i in sorted_idx]
                launcher_names = [launcher_names[i] for i in sorted_idx]
                dialog = xbmcgui.Dialog()
                selected_launcher = dialog.select('New launcher for {0}'.format(roms[romID]['m_name']), launcher_names)
                if selected_launcher < 0: return

                # --- STEP 2: select ROMs in that launcher ---
                launcher_id   = launcher_IDs[selected_launcher]
                launcher_roms = fs_load_ROMs_JSON(ROMS_DIR, self.launchers[launcher_id])
                if not launcher_roms: return
                roms_IDs = []
                roms_names = []
                for rom_id in launcher_roms:
                    # ROMs with nointro_status = 'Miss' are invalid! Do not add to the list
                    if launcher_roms[rom_id]['nointro_status'] == 'Miss': continue
                    roms_IDs.append(rom_id)
                    roms_names.append(launcher_roms[rom_id]['m_name'])
                sorted_idx = [i[0] for i in sorted(enumerate(roms_names), key=lambda x:x[1])]
                roms_IDs   = [roms_IDs[i] for i in sorted_idx]
                roms_names = [roms_names[i] for i in sorted_idx]
                selected_rom = dialog.select('New ROM for Favourite {0}'.format(roms[romID]['m_name']), roms_names)
                if selected_rom < 0 : return

                # >> Collect ROM object.
                old_fav_rom_ID  = romID
                new_fav_rom_ID  = roms_IDs[selected_rom]
                old_fav_rom     = roms[romID]
                parent_rom      = launcher_roms[new_fav_rom_ID]
                parent_launcher = self.launchers[launcher_id]

                # >> Check that the selected ROM ID is not already in Favourites
                if new_fav_rom_ID in roms:
                    kodi_dialog_OK('Selected ROM already in Favourites. Exiting.')
                    return

                # >> Relink Favourite ROM. Removed old Favourite before inserting new one.
                if type2 == 0:
                    log_info('_command_edit_ROM() Relinking ROM (launcher info only)')
                    new_fav_rom = fs_repair_Favourite_ROM(0, old_fav_rom, parent_rom, parent_launcher)
                elif type2 == 1:
                    log_info('_command_edit_ROM() Relinking ROM (update all)')
                    new_fav_rom = fs_repair_Favourite_ROM(3, old_fav_rom, parent_rom, parent_launcher)
                else:
                    kodi_dialog_OK('Manage ROM object, relink, wrong type2 = {0}. Please report this bug.'.format(type2))
                    return
                if categoryID == VCATEGORY_COLLECTIONS_ID:
                    # >> Insert the new ROM in a specific position of the OrderedDict.
                    old_fav_position = roms.keys().index(old_fav_rom_ID)
                    dic_index = 0
                    new_roms_orderded_dict = roms.__class__()
                    for key, value in roms.items():
                        # >> Replace old ROM by new ROM
                        if dic_index == old_fav_position: new_roms_orderded_dict[new_fav_rom['id']] = new_fav_rom
                        else:                             new_roms_orderded_dict[key] = value
                        dic_index += 1
                    roms.clear()
                    roms.update(new_roms_orderded_dict)
                else:
                    roms.pop(old_fav_rom_ID)
                    roms[new_fav_rom['id']] = new_fav_rom

                # >> Notify user
                if categoryID == VCATEGORY_FAVOURITES_ID:    kodi_notify('Relinked Favourite ROM')
                elif categoryID == VCATEGORY_COLLECTIONS_ID: kodi_notify('Relinked Collection ROM')

            # --- Copy launcher info from parent ROM ---
            # --- Copy metadata from parent ROM ---
            # --- Copy assets/artwork from parent ROM ---
            # --- Copy all from parent ROM ---
            elif type2 == 2 or type2 == 3 or type2 == 4 or type2 == 5:
                # >> Get launcher and parent ROM
                # >> Check Favourite ROM is linked (parent ROM exists)
                fav_rom         = roms[romID]
                fav_launcher_id = fav_rom['launcherID']
                if fav_launcher_id not in self.launchers:
                    kodi_dialog_OK('Parent Launcher not found. '
                                   'Relink this ROM before copying stuff from parent.')
                    return
                parent_launcher = self.launchers[fav_launcher_id]
                launcher_roms   = fs_load_ROMs_JSON(ROMS_DIR, parent_launcher)
                if romID not in launcher_roms:
                    kodi_dialog_OK('Parent ROM not found in Launcher. '
                                   'Relink this ROM before copying stuff from parent.')
                    return
                parent_rom = launcher_roms[romID]

                # >> Relink Favourite ROM. Removed old Favourite before inserting new one.
                if type2 == 2:
                    info_str = 'launcher info'
                    fs_aux_copy_ROM_launcher_info(parent_launcher, fav_rom)
                elif type2 == 3:
                    info_str = 'metadata'
                    fs_aux_copy_ROM_metadata(parent_rom, fav_rom)
                elif type2 == 4:
                    info_str = 'assets/artwork'
                    fs_aux_copy_ROM_artwork(parent_launcher, parent_rom, fav_rom)
                elif type2 == 5:
                    info_str = 'all info'
                    fs_aux_copy_ROM_launcher_info(parent_launcher, fav_rom)
                    fs_aux_copy_ROM_metadata(parent_rom, fav_rom)
                    fs_aux_copy_ROM_artwork(parent_launcher, parent_rom, fav_rom)
                else:
                    kodi_dialog_OK('Manage ROM object, copy info, wrong type2 = {0}. Please report this bug.'.format(type2))
                    return

                # >> Notify user
                if categoryID == VCATEGORY_FAVOURITES_ID:    kodi_notify('Updated Favourite ROM {0}'.format(info_str))
                elif categoryID == VCATEGORY_COLLECTIONS_ID: kodi_notify('Updated Collection ROM {0}'.format(info_str))

            # --- Choose default Favourite/Collection assets/artwork ---
            elif type2 == 6:
                rom = roms[romID]

                # >> Label1 an label2
                asset_icon_str     = assets_get_asset_name_str(rom['roms_default_thumb'])
                asset_fanart_str    = assets_get_asset_name_str(rom['roms_default_fanart'])
                asset_banner_str    = assets_get_asset_name_str(rom['roms_default_banner'])
                asset_poster_str    = assets_get_asset_name_str(rom['roms_default_poster'])
                asset_clearlogo_str = assets_get_asset_name_str(rom['roms_default_clearlogo'])
                label2_thumb        = rom[rom['roms_default_thumb']]     if rom[rom['roms_default_thumb']]     else 'Not set'
                label2_fanart       = rom[rom['roms_default_fanart']]    if rom[rom['roms_default_fanart']]    else 'Not set'
                label2_banner       = rom[rom['roms_default_banner']]    if rom[rom['roms_default_banner']]    else 'Not set'
                label2_poster       = rom[rom['roms_default_poster']]    if rom[rom['roms_default_poster']]    else 'Not set'
                label2_clearlogo    = rom[rom['roms_default_clearlogo']] if rom[rom['roms_default_clearlogo']] else 'Not set'
                icon_listitem       = xbmcgui.ListItem(label = 'Choose asset for Icon (currently {0})'.format(asset_icon_str),
                                                       label2 = label2_thumb)
                fanart_listitem     = xbmcgui.ListItem(label = 'Choose asset for Fanart (currently {0})'.format(asset_fanart_str),
                                                       label2 = label2_fanart)
                banner_listitem     = xbmcgui.ListItem(label = 'Choose asset for Banner (currently {0})'.format(asset_banner_str),
                                                       label2 = label2_banner)
                poster_listitem     = xbmcgui.ListItem(label = 'Choose asset for Poster (currently {0})'.format(asset_poster_str),
                                                       label2 = label2_poster)
                clearlogo_listitem  = xbmcgui.ListItem(label = 'Choose asset for Clearlogo (currently {0})'.format(asset_clearlogo_str),
                                                       label2 = label2_clearlogo)

                # >> Asset image
                img_icon            = rom[rom['roms_default_thumb']]     if rom[rom['roms_default_thumb']]     else 'DefaultAddonNone.png'
                img_fanart          = rom[rom['roms_default_fanart']]    if rom[rom['roms_default_fanart']]    else 'DefaultAddonNone.png'
                img_banner          = rom[rom['roms_default_banner']]    if rom[rom['roms_default_banner']]    else 'DefaultAddonNone.png'
                img_poster          = rom[rom['roms_default_poster']]    if rom[rom['roms_default_poster']]    else 'DefaultAddonNone.png'
                img_clearlogo       = rom[rom['roms_default_clearlogo']] if rom[rom['roms_default_clearlogo']] else 'DefaultAddonNone.png'
                icon_listitem.setArt({'icon' : img_icon})
                fanart_listitem.setArt({'icon' : img_fanart})
                banner_listitem.setArt({'icon' : img_banner})
                poster_listitem.setArt({'icon' : img_poster})
                clearlogo_listitem.setArt({'icon' : img_clearlogo})

                # >> Execute select dialog
                listitems = [icon_listitem, fanart_listitem, banner_listitem,
                             poster_listitem, clearlogo_listitem]
                type3 = dialog.select('Edit ROMs default Assets/Artwork', list = listitems, useDetails = True)
                if type3 < 0: return

                ROMs_asset_ListItem_list = [
                    xbmcgui.ListItem(label = 'Title',     label2 = rom['s_title'] if rom['s_title'] else 'Not set'),
                    xbmcgui.ListItem(label = 'Snap',      label2 = rom['s_snap'] if rom['s_snap'] else 'Not set'),
                    xbmcgui.ListItem(label = 'Fanart',    label2 = rom['s_fanart'] if rom['s_fanart'] else 'Not set'),
                    xbmcgui.ListItem(label = 'Banner',    label2 = rom['s_banner'] if rom['s_banner'] else 'Not set'),
                    xbmcgui.ListItem(label = 'Clearlogo', label2 = rom['s_clearlogo'] if rom['s_clearlogo'] else 'Not set'),
                    xbmcgui.ListItem(label = 'Boxfront',  label2 = rom['s_boxfront'] if rom['s_boxfront'] else 'Not set'),
                    xbmcgui.ListItem(label = 'Boxback',   label2 = rom['s_boxback'] if rom['s_boxback'] else 'Not set'),
                    xbmcgui.ListItem(label = 'Cartridge', label2 = rom['s_cartridge'] if rom['s_cartridge'] else 'Not set'),
                    xbmcgui.ListItem(label = 'Flyer',     label2 = rom['s_flyer'] if rom['s_flyer'] else 'Not set'),
                    xbmcgui.ListItem(label = 'Map',       label2 = rom['s_map'] if rom['s_map'] else 'Not set'),
                    xbmcgui.ListItem(label = 'Manual',    label2 = rom['s_manual'] if rom['s_manual'] else 'Not set'),
                    xbmcgui.ListItem(label = 'Trailer',   label2 = rom['s_trailer'] if rom['s_trailer'] else 'Not set'),
                ]
                ROMs_asset_ListItem_list[0].setArt({'icon' : rom['s_title'] if rom['s_title'] else 'DefaultAddonNone.png'})
                ROMs_asset_ListItem_list[1].setArt({'icon' : rom['s_snap'] if rom['s_snap'] else 'DefaultAddonNone.png'})
                ROMs_asset_ListItem_list[2].setArt({'icon' : rom['s_fanart'] if rom['s_fanart'] else 'DefaultAddonNone.png'})
                ROMs_asset_ListItem_list[3].setArt({'icon' : rom['s_banner'] if rom['s_banner'] else 'DefaultAddonNone.png'})
                ROMs_asset_ListItem_list[4].setArt({'icon' : rom['s_clearlogo'] if rom['s_clearlogo'] else 'DefaultAddonNone.png'})
                ROMs_asset_ListItem_list[5].setArt({'icon' : rom['s_boxfront'] if rom['s_boxfront'] else 'DefaultAddonNone.png'})
                ROMs_asset_ListItem_list[6].setArt({'icon' : rom['s_boxback'] if rom['s_boxback'] else 'DefaultAddonNone.png'})
                ROMs_asset_ListItem_list[7].setArt({'icon' : rom['s_cartridge'] if rom['s_cartridge'] else 'DefaultAddonNone.png'})
                ROMs_asset_ListItem_list[8].setArt({'icon' : rom['s_flyer'] if rom['s_flyer'] else 'DefaultAddonNone.png'})
                ROMs_asset_ListItem_list[9].setArt({'icon' : rom['s_map'] if rom['s_map'] else 'DefaultAddonNone.png'})
                ROMs_asset_ListItem_list[10].setArt({'icon' : rom['s_manual'] if rom['s_manual'] else 'DefaultAddonNone.png'})
                ROMs_asset_ListItem_list[11].setArt({'icon' : rom['s_trailer'] if rom['s_trailer'] else 'DefaultAddonNone.png'})

                if type3 == 0:
                    type_s = dialog.select('Choose default Asset for Icon', list = ROMs_asset_ListItem_list, useDetails = True)
                    if type_s < 0: return
                    assets_choose_category_ROM(rom, 'roms_default_thumb', type_s)
                elif type3 == 1:
                    type_s = dialog.select('Choose default Asset for Fanart', list = ROMs_asset_ListItem_list, useDetails = True)
                    if type_s < 0: return
                    assets_choose_category_ROM(rom, 'roms_default_fanart', type_s)
                elif type3 == 2:
                    type_s = dialog.select('Choose default Asset for Banner', list = ROMs_asset_ListItem_list, useDetails = True)
                    if type_s < 0: return
                    assets_choose_category_ROM(rom, 'roms_default_banner', type_s)
                elif type3 == 3:
                    type_s = dialog.select('Choose default Asset for Poster', list = ROMs_asset_ListItem_list, useDetails = True)
                    if type_s < 0: return
                    assets_choose_category_ROM(rom, 'roms_default_poster', type_s)
                elif type3 == 4:
                    type_s = dialog.select('Choose default Asset for Clearlogo', list = ROMs_asset_ListItem_list, useDetails = True)
                    if type_s < 0: return
                    assets_choose_category_ROM(rom, 'roms_default_clearlogo', type_s)
                # User canceled select dialog
                elif type3 < 0: return

        # --- Manage Collection ROM position (ONLY for Favourite/Collection ROMs) ---
        elif type == 6:
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Manage ROM position',
                                  ['Choose Collection ROM order ...',
                                   'Move Collection ROM up',
                                   'Move Collection ROM down'])
            if type2 < 0: return

            # --- Choose ROM order ---
            if type2 == 0:
                # >> Get position of current ROM in the list
                num_roms = len(roms)
                current_ROM_position = roms.keys().index(romID)
                if current_ROM_position < 0:
                    kodi_notify_warn('ROM ID not found in Collection. This is a bug!')
                    return
                log_verb('_command_edit_rom() Collection {0} ({1})'.format(collection['m_name'], collection['id']))
                log_verb('_command_edit_rom() Collection has {0} ROMs'.format(num_roms))

                # --- Show a select dialog ---
                rom_menu_list = []
                for key in roms:
                    if key == romID: continue
                    rom_menu_list.append(roms[key]['m_name'])
                rom_menu_list.append('Last')
                type3 = dialog.select('Choose position for ROM {0}'.format(roms[romID]['m_name']),
                                      rom_menu_list)
                if type3 < 0: return
                new_pos_index = type3
                log_verb('_command_edit_rom() new_pos_index = {0}'.format(new_pos_index))

                # --- Reorder Collection OrderedDict ---
                # >> new_oder = [0, 1, ..., num_roms-1]
                new_order = range(num_roms)
                # >> Delete current element
                del new_order[current_ROM_position]
                # >> Insert current element at selected position
                new_order.insert(new_pos_index, current_ROM_position)
                log_verb('_command_edit_rom() old_order = {0}'.format(unicode(range(num_roms))))
                log_verb('_command_edit_rom() new_order = {0}'.format(unicode(new_order)))

                # >> Reorder ROMs
                new_roms = OrderedDict()
                for order_idx in new_order:
                    key_value_tuple = roms.items()[order_idx]
                    new_roms.update({key_value_tuple[0] : key_value_tuple[1]})
                roms = new_roms

            # --- Move Collection ROM up ---
            elif type2 == 1:
                if not roms:
                    kodi_notify('Collection is empty. Add ROMs to this collection first.')
                    return

                # >> Get position of current ROM in the list
                num_roms = len(roms)
                current_ROM_position = roms.keys().index(romID)
                if current_ROM_position < 0:
                    kodi_notify_warn('ROM ID not found in Collection. This is a bug!')
                    return
                log_verb('_command_edit_rom() Collection {0} ({1})'.format(collection['m_name'], collection['id']))
                log_verb('_command_edit_rom() Collection has {0} ROMs'.format(num_roms))
                log_verb('_command_edit_rom() Moving ROM in position {0} up'.format(current_ROM_position))

                # >> If ROM is first of the list do nothing
                if current_ROM_position == 0:
                    kodi_dialog_OK('ROM is in first position of the Collection. Cannot be moved up.')
                    return

                # >> Reorder OrderedDict
                new_order                           = range(num_roms)
                new_order[current_ROM_position - 1] = current_ROM_position
                new_order[current_ROM_position]     = current_ROM_position - 1
                new_roms = OrderedDict()
                # >> http://stackoverflow.com/questions/10058140/accessing-items-in-a-ordereddict
                for order_idx in new_order:
                    key_value_tuple = roms.items()[order_idx]
                    new_roms.update({key_value_tuple[0] : key_value_tuple[1]})
                roms = new_roms

            # --- Move Collection ROM down ---
            elif type2 == 2:
                if not roms:
                    kodi_notify('Collection is empty. Add ROMs to this collection first.')
                    return

                # >> Get position of current ROM in the list
                num_roms = len(roms)
                current_ROM_position = roms.keys().index(romID)
                if current_ROM_position < 0:
                    kodi_notify_warn('ROM ID not found in Collection. This is a bug!')
                    return
                log_verb('_command_edit_rom() Collection {0} ({1})'.format(collection['m_name'], collection['id']))
                log_verb('_command_edit_rom() Collection has {0} ROMs'.format(num_roms))
                log_verb('_command_edit_rom() Moving ROM in position {0} down'.format(current_ROM_position))

                # >> If ROM is first of the list do nothing
                if current_ROM_position == num_roms - 1:
                    kodi_dialog_OK('ROM is in last position of the Collection. Cannot be moved down.')
                    return

                # >> Reorder OrderedDict
                new_order                           = range(num_roms)
                new_order[current_ROM_position]     = current_ROM_position + 1
                new_order[current_ROM_position + 1] = current_ROM_position
                new_roms = OrderedDict()
                # >> http://stackoverflow.com/questions/10058140/accessing-items-in-a-ordereddict
                for order_idx in new_order:
                    key_value_tuple = roms.items()[order_idx]
                    new_roms.update({key_value_tuple[0] : key_value_tuple[1]})
                roms = new_roms

        # --- Save ROMs or Favourites ROMs or Collection ROMs ---
        # >> Always save if we reach this point of the function
        if launcherID == VLAUNCHER_FAVOURITES_ID:
            fs_write_Favourites_JSON(FAV_JSON_FILE_PATH, roms)
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            # >> Convert back the OrderedDict into a list and save Collection
            collection_rom_list = []
            for key in roms:
                collection_rom_list.append(roms[key])

            json_file_path = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
            fs_write_Collection_ROMs_JSON(json_file_path, collection_rom_list)
        else:
            # >> Save categories/launchers to update timestamp
            #    Also update changed launcher timestamp
            self.launchers[launcherID]['num_roms'] = len(roms)
            self.launchers[launcherID]['timestamp_launcher'] = _t = time.time()
            pDialog = xbmcgui.DialogProgress()
            pDialog.create('Advanced Emulator Launcher', 'Saving ROM JSON database ...')
            pDialog.update(10)
            fs_write_ROMs_JSON(ROMS_DIR, self.launchers[launcherID], roms)
            pDialog.update(90)
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
            pDialog.update(100)

            # >> If launcher has a DAT then synchronise the edit ROM in the list of parents
            if launcher['nointro_xml_file']:
                log_verb('Updating ROM in Parents JSON')
                parents_roms_base_noext = launcher['roms_base_noext'] + '_parents'
                pDialog.update(25, 'Loading Parents JSON ...')
                parent_roms = fs_load_JSON_file(ROMS_DIR, parents_roms_base_noext)
                # >> Only edit if ROM is in parent list
                if romID in parent_roms:
                    log_verb('romID in Parent JSON. Updating ...')
                    parent_roms[romID] = roms[romID]
                pDialog.update(10, 'Saving Parents JSON ...')
                fs_write_JSON_file(ROMS_DIR, parents_roms_base_noext, parent_roms)
                pDialog.update(100)
            pDialog.close()

        # It seems that updating the container does more harm than good... specially when having many ROMs
        # By the way, what is the difference between Container.Refresh() and Container.Update()?
        kodi_refresh_container()

    # ---------------------------------------------------------------------------------------------
    # Categories LisItem rendering
    # ---------------------------------------------------------------------------------------------
    #
    # Renders the addon Root window. Categories, categoryless launchers, Favourites, etc.
    #
    def _command_render_categories(self):
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)

        # --- For every category, add it to the listbox. Order alphabetically by name ---
        for key in sorted(self.categories, key = lambda x : self.categories[x]['m_name']):
            self._gui_render_category_row(self.categories[key], key)

        # --- Render categoryless launchers. Order alphabetically by name ---
        catless_launchers = {}
        for launcher_id, launcher in self.launchers.iteritems():
            if launcher['categoryID'] == VCATEGORY_ADDONROOT_ID:
                catless_launchers[launcher_id] = launcher
        for launcher_id in sorted(catless_launchers, key = lambda x : catless_launchers[x]['m_name']):
            self._gui_render_launcher_row(catless_launchers[launcher_id])

        # --- AEL Favourites special category ---
        if not self.settings['display_hide_favs']: self._gui_render_category_favourites_row()

        # --- AEL Collections special category ---
        if not self.settings['display_hide_collections']: self._gui_render_category_collections_row()

        # --- AEL Virtual Categories ---
        if not self.settings['display_hide_vlaunchers']: self._gui_render_virtual_category_root_row()

        # --- Browse Offline Scraper database ---
        if not self.settings['display_hide_AEL_scraper']: self._gui_render_category_AEL_offline_scraper_row()
        if not self.settings['display_hide_LB_scraper']: self._gui_render_category_LB_offline_scraper_row()

        # --- Recently played and most played ROMs ---
        if not self.settings['display_hide_recent']:     self._gui_render_category_recently_played_row()
        if not self.settings['display_hide_mostplayed']: self._gui_render_category_most_played_row()

        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Renders all categories without Favourites, Collections, virtual categories, etc.
    # This function is called by skins to build shortcuts menu.
    #
    def _command_render_all_categories(self):
        # >> If no categories render nothing
        if not self.categories:
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # >> For every category, add it to the listbox. Order alphabetically by name
        for key in sorted(self.categories, key = lambda x : self.categories[x]['m_name']):
            self._gui_render_category_row(self.categories[key], key)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _gui_render_category_row(self, category_dic, key):
        # --- Do not render row if category finished ---
        if category_dic['finished'] and self.settings['display_hide_finished']: return

        # --- Create listitem row ---
        ICON_OVERLAY = 5 if category_dic['finished'] else 4
        listitem = xbmcgui.ListItem(category_dic['m_name'])
        listitem.setInfo('video', {'title'   : category_dic['m_name'],    'genre'   : category_dic['m_genre'],
                                   'plot'    : category_dic['m_plot'],    'rating'  : category_dic['m_rating'],
                                   'trailer' : category_dic['s_trailer'], 'overlay' : ICON_OVERLAY })

        # --- Set Category artwork ---
        # >> Set thumb/fanart/banner/poster/clearlogo based on user preferences
        icon_path      = asset_get_default_asset_Category(category_dic, 'default_icon', 'DefaultFolder.png')
        fanart_path    = asset_get_default_asset_Category(category_dic, 'default_fanart')
        banner_path    = asset_get_default_asset_Category(category_dic, 'default_banner')
        poster_path    = asset_get_default_asset_Category(category_dic, 'default_poster')
        clearlogo_path = asset_get_default_asset_Category(category_dic, 'default_clearlogo')
        listitem.setArt({'icon'   : icon_path,   'fanart' : fanart_path, 
                         'banner' : banner_path, 'poster' : poster_path, 'clearlogo' : clearlogo_path})

        # --- Create context menu ---
        # To remove default entries like "Go to root", etc, see http://forum.kodi.tv/showthread.php?tid=227358
        commands = []
        categoryID = category_dic['id']
        commands.append(('View Category data',  self._misc_url_RunPlugin('VIEW', categoryID)))
        commands.append(('Edit Category',       self._misc_url_RunPlugin('EDIT_CATEGORY', categoryID)))
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher',    self._misc_url_RunPlugin('ADD_LAUNCHER', categoryID)))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', )) # If using window ID then use "10003"
        commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        # In Krypton "Add to favourites" appears always in the last position of context menu.
        listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        url_str = self._misc_url('SHOW_LAUNCHERS', key)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url=url_str, listitem=listitem, isFolder=True)

    def _gui_render_category_favourites_row(self):
        # --- Create listitem row ---
        fav_name = '<Favourites>'
        fav_thumb = 'DefaultFolder.png'
        fav_fanart = ''
        fav_banner = ''
        fav_flyer = ''
        listitem = xbmcgui.ListItem(fav_name)
        listitem.setInfo('video', {'title': fav_name, 'overlay' : 4,
                                   'plot' : 'Shows AEL Favourite ROMs' })
        listitem.setArt({'thumb' : fav_thumb, 'fanart' : fav_fanart, 'banner' : fav_banner, 'poster' : fav_flyer})

        # --- Create context menu ---
        commands = []
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher',    self._misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        url_str = self._misc_url('SHOW_FAVOURITES')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_category_collections_row(self):
        collections_name   = '{ROM Collections}'
        collections_thumb  = 'DefaultFolder.png'
        collections_fanart = ''
        collections_banner = ''
        collections_flyer  = ''
        listitem = xbmcgui.ListItem(collections_name)
        listitem.setInfo('video', {'title': collections_name, 'overlay': 4,
                                   'plot' : 'Shows user defined ROM collections'})
        listitem.setArt({'thumb'  : collections_thumb,  'fanart' : collections_fanart, 
                         'banner' : collections_banner, 'poster' : collections_flyer})

        commands = []
        commands.append(('Create New Collection', self._misc_url_RunPlugin('ADD_COLLECTION')))
        commands.append(('Import Collection',     self._misc_url_RunPlugin('IMPORT_COLLECTION')))
        commands.append(('Create New Category',   self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher',      self._misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_COLLECTIONS')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_virtual_category_root_row(self):
        vcategory_name   = '[Browse by ... ]'
        vcategory_thumb  = 'DefaultFolder.png'
        vcategory_fanart = ''
        vcategory_banner = ''
        vcategory_flyer  = ''
        vcategory_label  = 'Browse by ...'
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'overlay': 4,
                                   'plot' : 'Shows AEL virtual launchers'})
        listitem.setArt({'thumb' : vcategory_thumb, 'fanart' : vcategory_fanart, 
                         'banner' : vcategory_banner, 'poster' : vcategory_flyer})

        commands = []
        update_vcat_all_URL = self._misc_url_RunPlugin('UPDATE_ALL_VCATEGORIES')
        commands.append(('Update all databases'.format(vcategory_label), update_vcat_all_URL))
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher',    self._misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_VCATEGORIES_ROOT')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_category_AEL_offline_scraper_row(self):
        vcategory_name   = '[Browse AEL Offline Scraper]'
        vcategory_thumb  = 'DefaultFolder.png'
        vcategory_fanart = ''
        vcategory_banner = ''
        vcategory_flyer  = ''
        vcategory_label  = 'Browse Offline Scraper'
        vcategory_plot   = 'Allows you to browse the ROMs in the AEL offline scraper database'
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'overlay': 4, 'plot' : vcategory_plot})
        listitem.setArt({'thumb' : vcategory_thumb, 'fanart' : vcategory_fanart,
                         'banner' : vcategory_banner, 'poster' : vcategory_flyer})

        commands = []
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher',    self._misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_AEL_OFFLINE_LAUNCHERS_ROOT')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_category_LB_offline_scraper_row(self):
        vcategory_name   = '[Browse LaunchBox Offline Scraper]'
        vcategory_thumb  = 'DefaultFolder.png'
        vcategory_fanart = ''
        vcategory_banner = ''
        vcategory_flyer  = ''
        vcategory_label  = 'Browse Offline Scraper'
        vcategory_plot   = 'Allows you to browse the ROMs in the LaunchBox offline scraper database'
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'overlay': 4, 'plot' : vcategory_plot})
        listitem.setArt({'thumb' : vcategory_thumb, 'fanart' : vcategory_fanart,
                         'banner' : vcategory_banner, 'poster' : vcategory_flyer})

        commands = []
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher',    self._misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_LB_OFFLINE_LAUNCHERS_ROOT')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_category_recently_played_row(self):
        laun_name = '[Recently played ROMs]'
        fav_thumb = 'DefaultFolder.png'
        fav_fanart = ''
        fav_banner = ''
        fav_flyer = ''
        listitem = xbmcgui.ListItem(laun_name)
        listitem.setInfo('video', {'title': laun_name, 'overlay': 4,
                                   'plot' : 'Shows the ROMs you have recently played'})
        listitem.setArt({'thumb' : fav_thumb, 'fanart' : fav_fanart, 'banner' : fav_banner, 'poster' : fav_flyer})

        commands = []
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher',    self._misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_RECENTLY_PLAYED')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_category_most_played_row(self):
        laun_name = '[Most played ROMs]'
        fav_thumb = 'DefaultFolder.png'
        fav_fanart = ''
        fav_banner = ''
        fav_flyer = ''
        listitem = xbmcgui.ListItem(laun_name)
        listitem.setInfo('video', {'title': laun_name, 'overlay' : 4,
                                   'plot' : 'Displays the ROMs you play most'})
        listitem.setArt({'thumb' : fav_thumb, 'fanart' : fav_fanart, 'banner' : fav_banner, 'poster' : fav_flyer})

        commands = []
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher',    self._misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_MOST_PLAYED')
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    # ---------------------------------------------------------------------------------------------
    # Virtual categories [Browse by ...]
    # ---------------------------------------------------------------------------------------------
    def _gui_render_vcategories_root(self):
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)
        self._gui_render_virtual_category_row(VCATEGORY_TITLE_ID)
        self._gui_render_virtual_category_row(VCATEGORY_YEARS_ID)
        self._gui_render_virtual_category_row(VCATEGORY_GENRE_ID)
        self._gui_render_virtual_category_row(VCATEGORY_DEVELOPER_ID)
        self._gui_render_virtual_category_row(VCATEGORY_NPLAYERS_ID)
        self._gui_render_virtual_category_row(VCATEGORY_ESRB_ID)
        self._gui_render_virtual_category_row(VCATEGORY_RATING_ID)
        self._gui_render_virtual_category_row(VCATEGORY_CATEGORY_ID)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _gui_render_virtual_category_row(self, virtual_category_kind):
        if virtual_category_kind == VCATEGORY_TITLE_ID:
            vcategory_name   = 'Browse ROMs by Title'
            vcategory_thumb  = 'DefaultFolder.png'
            vcategory_fanart = ''
            vcategory_banner = ''
            vcategory_flyer  = ''
            vcategory_label  = 'Title'
        elif virtual_category_kind == VCATEGORY_YEARS_ID:
            vcategory_name   = 'Browse by Year'
            vcategory_thumb  = 'DefaultFolder.png'
            vcategory_fanart = ''
            vcategory_banner = ''
            vcategory_flyer  = ''
            vcategory_label  = 'Year'
        elif virtual_category_kind == VCATEGORY_GENRE_ID:
            vcategory_name   = 'Browse by Genre'
            vcategory_thumb  = 'DefaultFolder.png'
            vcategory_fanart = ''
            vcategory_banner = ''
            vcategory_flyer  = ''
            vcategory_label  = 'Genre'
        elif virtual_category_kind == VCATEGORY_DEVELOPER_ID:
            vcategory_name   = 'Browse by Developer'
            vcategory_thumb  = 'DefaultFolder.png'
            vcategory_fanart = ''
            vcategory_banner = ''
            vcategory_flyer  = ''
            vcategory_label  = 'Developer'
        elif virtual_category_kind == VCATEGORY_NPLAYERS_ID:
            vcategory_name   = 'Browse by Number of Players'
            vcategory_thumb  = 'DefaultFolder.png'
            vcategory_fanart = ''
            vcategory_banner = ''
            vcategory_flyer  = ''
            vcategory_label  = 'NPlayers'
        elif virtual_category_kind == VCATEGORY_ESRB_ID:
            vcategory_name   = 'Browse by ESRB Rating'
            vcategory_thumb  = 'DefaultFolder.png'
            vcategory_fanart = ''
            vcategory_banner = ''
            vcategory_flyer  = ''
            vcategory_label  = 'ESRB'
        elif virtual_category_kind == VCATEGORY_RATING_ID:
            vcategory_name   = 'Browse by User Rating'
            vcategory_thumb  = 'DefaultFolder.png'
            vcategory_fanart = ''
            vcategory_banner = ''
            vcategory_flyer  = ''
            vcategory_label  = 'Rating'
        elif virtual_category_kind == VCATEGORY_CATEGORY_ID:
            vcategory_name   = 'Browse by Category'
            vcategory_thumb  = 'DefaultFolder.png'
            vcategory_fanart = ''
            vcategory_banner = ''
            vcategory_flyer  = ''
            vcategory_label  = 'Category'
        else:
            log_error('_gui_render_virtual_category_row() Wrong virtual_category_kind = {0}'.format(virtual_category_kind))
            kodi_dialog_OK('Wrong virtual_category_kind = {0}'.format(virtual_category_kind))
            return
        listitem = xbmcgui.ListItem(vcategory_name)
        listitem.setInfo('video', {'title': vcategory_name, 'overlay': 4,
                                   'plot' : 'Shows virtual launchers in {0} virtual category'.format(vcategory_label)})
        listitem.setArt({'icon'   : vcategory_thumb,  'fanart' : vcategory_fanart, 
                         'banner' : vcategory_banner, 'poster' : vcategory_flyer})

        commands = []
        update_vcat_URL     = self._misc_url_RunPlugin('UPDATE_VIRTUAL_CATEGORY', virtual_category_kind)
        update_vcat_all_URL = self._misc_url_RunPlugin('UPDATE_ALL_VCATEGORIES')
        commands.append(('Update {0} database'.format(vcategory_label), update_vcat_URL))
        commands.append(('Update all databases', update_vcat_all_URL))
        commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Add New Launcher',    self._misc_url_RunPlugin('ADD_LAUNCHER_ROOT')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_VIRTUAL_CATEGORY', virtual_category_kind)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_AEL_scraper_launchers(self):
        self._misc_set_default_sorting_method()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)

        # >> Open info dictionary
        gamedb_info_dic = fs_load_JSON_file(GAMEDB_INFO_DIR, GAMEDB_JSON_BASE_NOEXT)

        # >> Loop the list of platforms and render a virtual launcher for each platform that
        # >> has a valid XML database.
        for platform in AEL_platform_list:
            # >> Do not show Unknown platform
            if platform == 'Unknown': continue
            db_suffix = platform_AEL_to_Offline_GameDBInfo_XML[platform]
            self._gui_render_AEL_scraper_launchers_row(platform, gamedb_info_dic[platform], db_suffix)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _gui_render_AEL_scraper_launchers_row(self, platform, platform_info, db_suffix):
        # >> Mark platform whose XML DB is not available
        title_str = platform
        if not db_suffix:
            title_str += ' [COLOR red][Not available][/COLOR]'
        else:
            title_str += ' [COLOR orange]({0} ROMs)[/COLOR]'.format(platform_info['numROMs'])
        plot_text = 'Offline Scraper {0} database ROMs.'.format(platform)
        listitem = xbmcgui.ListItem(title_str)
        listitem.setInfo('video', {'title' : title_str,
                                   'genre' : 'Offline Scraper database',
                                   'plot'  : plot_text, 'overlay': 4 } )
        # >> Set platform property to render platform icon on skins.
        listitem.setProperty('platform', platform)

        commands = []
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_AEL_SCRAPER_ROMS', platform)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    def _gui_render_LB_scraper_launchers(self):
        self._misc_set_default_sorting_method()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)

        # >> Open info dictionary
        gamedb_info_dic = fs_load_JSON_file(LAUNCHBOX_INFO_DIR, LAUNCHBOX_JSON_BASE_NOEXT)

        # >> Loop the list of platforms and render a virtual launcher for each platform that
        # >> has a valid XML database.
        for platform in AEL_platform_list:
            # >> Do not show Unknown platform
            if platform == 'Unknown': continue
            db_suffix = platform_AEL_to_LB_XML[platform]
            self._gui_render_LB_scraper_launchers_row(platform, gamedb_info_dic[platform], db_suffix)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _gui_render_LB_scraper_launchers_row(self, platform, platform_info, db_suffix):
        # >> Mark platform whose XML DB is not available
        title_str = platform
        if not db_suffix:
            title_str += ' [COLOR red][Not available][/COLOR]'
        else:
            title_str += ' [COLOR orange]({0} ROMs)[/COLOR]'.format(platform_info['numROMs'])
        plot_text = 'Offline Scraper {0} database ROMs.'.format(platform)
        listitem = xbmcgui.ListItem(title_str)
        listitem.setInfo('video', {'title' : title_str,
                                   'genre' : 'Offline Scraper database',
                                   'plot'  : plot_text, 'overlay': 4 } )
        # >> Set platform property to render platform icon on skins.
        listitem.setProperty('platform', platform)

        commands = []
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
        commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
        listitem.addContextMenuItems(commands, replaceItems = True)

        url_str = self._misc_url('SHOW_LB_SCRAPER_ROMS', platform)
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)

    # ---------------------------------------------------------------------------------------------
    # Launcher LisItem rendering
    # ---------------------------------------------------------------------------------------------
    #
    # Renders the launchers for a given category
    #
    def _command_render_launchers(self, categoryID):
        # >> Set content type
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)

        # --- If the category has no launchers then render nothing ---
        launcher_IDs = []
        for launcher_id in self.launchers:
            if self.launchers[launcher_id]['categoryID'] == categoryID: launcher_IDs.append(launcher_id)
        if not launcher_IDs:
            category_name = self.categories[categoryID]['m_name']
            kodi_notify('Category {0} has no launchers. Add launchers first.'.format(category_name))
            # NOTE If we return at this point Kodi produces and error:
            # ERROR: GetDirectory - Error getting plugin://plugin.program.advanced.emulator.launcher/?catID=8...f&com=SHOW_LAUNCHERS
            # ERROR: CGUIMediaWindow::GetDirectory(plugin://plugin.program.advanced.emulator.launcher/?catID=8...2f&com=SHOW_LAUNCHERS) failed
            #
            # How to avoid that? Rendering the categories again? If I call _command_render_categories() it does not work well, categories
            # are displayed in wrong alphabetical order and if go back clicking on .. the categories window is rendered again (instead of
            # exiting the addon).
            # self._command_render_categories()
            #
            # What about replacewindow? I also get the error, still not clear why...
            # xbmc.executebuiltin('ReplaceWindow(Programs,{0})'.format(self.base_url)) # Does not work
            # xbmc.executebuiltin('ReplaceWindow({0})'.format(self.base_url)) # Does not work
            #
            # Container.Refresh does not work either...
            # kodi_refresh_container()
            #
            # SOLUTION: call xbmcplugin.endOfDirectory(). It will create an empty ListItem wiht only '..' entry.
            #           User cannot open a context menu and the only option is to go back to categories display.
            #           No errors in Kodi log!
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # >> Render launcher rows of this launcher
        for key in sorted(self.launchers, key = lambda x : self.launchers[x]['m_name']):
            if self.launchers[key]['categoryID'] == categoryID:
                self._gui_render_launcher_row(self.launchers[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Renders all launchers belonging to all categories.
    # This function is called by skins to create shortcuts.
    #
    def _command_render_all_launchers(self):
        # >> If no launchers render nothing
        if not self.launchers:
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # >> Render all launchers
        for key in sorted(self.launchers, key = lambda x : self.launchers[x]['m_name']):
            self._gui_render_launcher_row(self.launchers[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _gui_render_launcher_row(self, launcher_dic):
        # --- Do not render row if launcher finished ---
        if launcher_dic['finished'] and self.settings['display_hide_finished']:
            return

        # --- Launcher tags ---
        # >> Do not plot ROM count on standalone launchers! Launcher is standalone if rompath = ''
        launcher_name = launcher_raw_name = launcher_dic['m_name']
        if self.settings['display_launcher_roms']:
            if launcher_dic['rompath']:
                # >> ROM launcher with DAT file and ROM audit information.
                if launcher_dic['nointro_xml_file']:
                    if launcher_dic['launcher_display_mode'] == LAUNCHER_DMODE_FLAT:
                        num_have    = launcher_dic['num_have']
                        num_miss    = launcher_dic['num_miss']
                        num_unknown = launcher_dic['num_unknown']
                        launcher_name = '{0} [COLOR orange]({1} Have / {2} Miss / {3} Unk)[/COLOR]'.format(
                            launcher_raw_name, num_have, num_miss, num_unknown)
                    elif launcher_dic['launcher_display_mode'] == LAUNCHER_DMODE_PCLONE:
                        num_parents = launcher_dic['num_parents']
                        num_clones  = launcher_dic['num_clones']
                        launcher_name = '{0} [COLOR orange]({1} Par / {2} Clo)[/COLOR]'.format(
                            launcher_raw_name, num_parents, num_clones)
                    elif launcher_dic['launcher_display_mode'] == LAUNCHER_DMODE_1G1R:
                        num_parents = launcher_dic['num_parents']
                        launcher_name = '{0} [COLOR orange]({1} Games)[/COLOR]'.format(launcher_raw_name, num_parents)
                    else:
                        launcher_name = '{0} [COLOR red](ERROR)[/COLOR]'.format(launcher_raw_name)
                # >> ROM launcher with no DAT file.
                else:
                    num_roms = launcher_dic['num_roms']
                    if num_roms == 0:
                        launcher_name = '{0} [COLOR orange](No ROMs)[/COLOR]'.format(launcher_raw_name)
                    elif num_roms == 1:
                        launcher_name = '{0} [COLOR orange]({1} ROM)[/COLOR]'.format(launcher_raw_name, num_roms)
                    else:
                        launcher_name = '{0} [COLOR orange]({1} ROMs)[/COLOR]'.format(launcher_raw_name, num_roms)
            else:
                launcher_name = '{0} [COLOR chocolate](Std)[/COLOR]'.format(launcher_raw_name)

        # --- Create listitem row ---
        ICON_OVERLAY = 5 if launcher_dic['finished'] else 4
        listitem = xbmcgui.ListItem(launcher_name)
        # >> BUG in Jarvis/Krypton skins. If 'year' is set to empty string a 0 is displayed on the
        # >>     skin. If year is not set then the correct icon is shown.
        if launcher_dic['m_year']:
            listitem.setInfo('video', {'title'   : launcher_name,             'year'    : launcher_dic['m_year'],
                                       'genre'   : launcher_dic['m_genre'],   'studio'  : launcher_dic['m_developer'],
                                       'rating'  : launcher_dic['m_rating'],  'plot'    : launcher_dic['m_plot'],
                                       'trailer' : launcher_dic['s_trailer'], 'overlay' : ICON_OVERLAY })
        else:
            listitem.setInfo('video', {'title'   : launcher_name,
                                       'genre'   : launcher_dic['m_genre'],   'studio'  : launcher_dic['m_developer'],
                                       'rating'  : launcher_dic['m_rating'],  'plot'    : launcher_dic['m_plot'],
                                       'trailer' : launcher_dic['s_trailer'], 'overlay' : ICON_OVERLAY })
        listitem.setProperty('platform', launcher_dic['platform'])

        # --- Set ListItem artwork ---
        kodi_thumb     = 'DefaultFolder.png' if launcher_dic['rompath'] else 'DefaultProgram.png'
        icon_path      = asset_get_default_asset_Category(launcher_dic, 'default_icon', kodi_thumb)
        fanart_path    = asset_get_default_asset_Category(launcher_dic, 'default_fanart')
        banner_path    = asset_get_default_asset_Category(launcher_dic, 'default_banner')
        poster_path    = asset_get_default_asset_Category(launcher_dic, 'default_poster')
        clearlogo_path = asset_get_default_asset_Category(launcher_dic, 'default_clearlogo')
        listitem.setArt({'icon'   : icon_path,   'fanart' : fanart_path, 'banner' : banner_path,
                         'poster' : poster_path, 'clearlogo' : clearlogo_path,
                         'controller' : launcher_dic['s_controller']})

        # --- Create context menu ---
        # Categories/Launchers/ROMs context menu order
        #  1) View XXXXX
        #  2) Edit XXXXX
        #  3) Add launcher (Categories) | Add ROMs (Launchers)
        #  4) Search XXXX
        #  5) Create new XXXX
        commands = []
        launcherID = launcher_dic['id']
        categoryID = launcher_dic['categoryID']
        commands.append(('View Launcher', self._misc_url_RunPlugin('VIEW', categoryID, launcherID) ))
        commands.append(('Edit Launcher', self._misc_url_RunPlugin('EDIT_LAUNCHER', categoryID, launcherID) ))
        # >> ONLY for ROM launchers
        if launcher_dic['rompath']:
            commands.append(('Add ROMs', self._misc_url_RunPlugin('ADD_ROMS', categoryID, launcherID) ))
        commands.append(('Search ROMs in Launcher', self._misc_url_RunPlugin('SEARCH_LAUNCHER', categoryID, launcherID) ))
        commands.append(('Add New Launcher', self._misc_url_RunPlugin('ADD_LAUNCHER', categoryID) ))
        # >> Launchers in addon root should be able to create a new category
        if categoryID == VCATEGORY_ADDONROOT_ID:
                commands.append(('Create New Category', self._misc_url_RunPlugin('ADD_CATEGORY')))
        commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)' ))
        commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__) ))
        listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add Launcher row to ListItem ---
        if launcher_dic['rompath']:
            url_str = self._misc_url('SHOW_ROMS', categoryID, launcherID)
            folder_flag = True
        else:
            url_str = self._misc_url('LAUNCH_STANDALONE', categoryID, launcherID)
            folder_flag = False
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = folder_flag)

    # ---------------------------------------------------------------------------------------------
    # ROM LisItem rendering
    # ---------------------------------------------------------------------------------------------
    #
    # Render clone ROMs. romID is the parent ROM.
    # This is only called in Parent/Clone and 1G1R display modes.
    #
    def _command_render_clone_roms(self, categoryID, launcherID, romID):
        # --- Set content type and sorting methods ---
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

        # --- Check for errors ---
        if launcherID not in self.launchers:
            log_error('_command_render_clone_roms() Launcher ID not found in self.launchers')
            kodi_dialog_OK('_command_render_clone_roms(): Launcher ID not found in self.launchers. Report this bug.')
            return
        selectedLauncher = self.launchers[launcherID]
        view_mode = selectedLauncher['launcher_display_mode']

        # --- Load ROMs for this launcher ---
        roms_file_path = fs_get_ROMs_JSON_file_path(ROMS_DIR, selectedLauncher['roms_base_noext'])
        if not roms_file_path.exists():
            kodi_notify('Launcher XML/JSON not found. Add ROMs to launcher.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return
        all_roms = fs_load_ROMs_JSON(ROMS_DIR, selectedLauncher)
        if not all_roms:
            kodi_notify('Launcher XML/JSON empty. Add ROMs to launcher.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Load parent/clone index ---
        index_base_noext = selectedLauncher['roms_base_noext'] + '_index_PClone'
        index_file_path = ROMS_DIR.pjoin(index_base_noext + '.json')
        if not index_file_path.exists():
            kodi_notify('Parent list JSON not found.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return
        pclone_index = fs_load_JSON_file(ROMS_DIR, index_base_noext)
        if not pclone_index:
            kodi_notify('Parent list is empty.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Build parent and clones dictionary of ROMs ---
        roms = {}
        # >> Add parent ROM except if the parent if the fake paren ROM
        if romID != UNKNOWN_ROMS_PARENT_ID: roms[romID] = all_roms[romID]
        # >> Add clones, if any
        for rom_id in pclone_index[romID]:
            roms[rom_id] = all_roms[rom_id]
        log_verb('_command_render_clone_roms() Parent ID {0}'.format(romID))
        log_verb('_command_render_clone_roms() Number of clone ROMs = {0}'.format(len(roms)))
        # for key in roms:
        #     log_debug('key   = {0}'.format(key))
        #     log_debug('value = {0}'.format(roms[key]))

        # --- ROM display filter ---
        dp_mode = selectedLauncher['nointro_display_mode']
        if selectedLauncher['nointro_xml_file'] and dp_mode != NOINTRO_DMODE_ALL:
            filtered_roms = {}
            for rom_id in roms:
                rom = roms[rom_id]
                if rom['nointro_status'] == NOINTRO_STATUS_HAVE:
                    if dp_mode == NOINTRO_DMODE_HAVE or \
                       dp_mode == NOINTRO_DMODE_HAVE_UNK or \
                       dp_mode == NOINTRO_DMODE_HAVE_MISS:
                        filtered_roms[rom_id] = rom
                elif rom['nointro_status'] == NOINTRO_STATUS_MISS:
                    if dp_mode == NOINTRO_DMODE_HAVE_MISS or \
                       dp_mode == NOINTRO_DMODE_MISS or \
                       dp_mode == NOINTRO_DMODE_MISS_UNK:
                        filtered_roms[rom_id] = rom
                elif rom['nointro_status'] == NOINTRO_STATUS_UNKNOWN:
                    if dp_mode == NOINTRO_DMODE_HAVE_UNK or \
                       dp_mode == NOINTRO_DMODE_MISS_UNK or \
                       dp_mode == NOINTRO_DMODE_UNK:
                        filtered_roms[rom_id] = rom
                # >> Always copy roms with unknown status (NOINTRO_STATUS_NONE)
                else:
                    filtered_roms[rom_id] = rom
            roms = filtered_roms
            if not roms:
                kodi_notify('No ROMs to show with current filtering settings.')
                xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
                return

        # --- Render ROMs ---
        roms_fav = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        roms_fav_set = set(roms_fav.keys())
        for key in sorted(roms, key = lambda x : roms[x]['m_name']):
            self._gui_render_rom_row(categoryID, launcherID, roms[key], key in roms_fav_set, view_mode, False)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Renders the ROMs listbox for a given standard launcher or the Parent ROMs of a PClone launcher.
    #
    def _command_render_roms(self, categoryID, launcherID):
        # --- Set content type and sorting methods ---
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

        # --- Check for errors ---
        if launcherID not in self.launchers:
            log_error('_command_render_roms() Launcher ID not found in self.launchers')
            kodi_dialog_OK('_command_render_roms(): Launcher ID not found in self.launchers. Report this bug.')
            return
        selectedLauncher = self.launchers[launcherID]
        view_mode = selectedLauncher['launcher_display_mode']

        # --- Render in Flat mode (all ROMs) or Parent/Clone or 1G1R mode---
        # >> Parent/Clone mode and 1G1R modes are very similar in terms of programming.
        loading_ticks_start = time.time()
        if view_mode == LAUNCHER_DMODE_FLAT:
            # --- Load ROMs for this launcher ---
            roms_json_FN = ROMS_DIR.pjoin(selectedLauncher['roms_base_noext'] + '.json')
            if not roms_json_FN.exists():
                kodi_notify('Launcher XML/JSON not found. Add ROMs to launcher.')
                xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
                return
            roms = fs_load_ROMs_JSON(ROMS_DIR, selectedLauncher)
            if not roms:
                kodi_notify('Launcher XML/JSON empty. Add ROMs to launcher.')
                xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
                return
        else:
            # --- Load parent ROMs ---
            parent_roms_base_noext = selectedLauncher['roms_base_noext'] + '_parents'
            parents_FN = ROMS_DIR.pjoin(parent_roms_base_noext + '.json')
            if not parents_FN.exists():
                kodi_notify('Parent ROMs JSON not found.')
                xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
                return
            roms = fs_load_JSON_file(ROMS_DIR, parent_roms_base_noext)
            if not roms:
                kodi_notify('Parent ROMs JSON is empty.')
                xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
                return

            # --- Load parent/clone index ---
            index_base_noext = selectedLauncher['roms_base_noext'] + '_index_PClone'
            index_FN = ROMS_DIR.pjoin(index_base_noext + '.json')
            if not index_FN.exists():
                kodi_notify('PClone index JSON not found.')
                xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
                return
            pclone_index = fs_load_JSON_file(ROMS_DIR, index_base_noext)
            if not pclone_index:
                kodi_notify('PClone index dict is empty.')
                xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
                return

        # --- ROM display filter ---
        dp_mode = selectedLauncher['nointro_display_mode']
        if selectedLauncher['nointro_xml_file'] and dp_mode != NOINTRO_DMODE_ALL:
            filtered_roms = {}
            for rom_id in roms:
                rom = roms[rom_id]
                # >> Always include a parent ROM regardless of filters in 'Parent/Clone mode'
                # >> and '1G1R mode' launcher_display_mode if it has 1 or more clones.
                if not selectedLauncher['launcher_display_mode'] == LAUNCHER_DMODE_FLAT and len(pclone_index[rom_id]):
                    filtered_roms[rom_id] = rom
                    continue
                # >> Filter ROM
                if rom['nointro_status'] == NOINTRO_STATUS_HAVE:
                    if dp_mode == NOINTRO_DMODE_HAVE or \
                       dp_mode == NOINTRO_DMODE_HAVE_UNK or \
                       dp_mode == NOINTRO_DMODE_HAVE_MISS:
                        filtered_roms[rom_id] = rom
                elif rom['nointro_status'] == NOINTRO_STATUS_MISS:
                    if dp_mode == NOINTRO_DMODE_HAVE_MISS or \
                       dp_mode == NOINTRO_DMODE_MISS or \
                       dp_mode == NOINTRO_DMODE_MISS_UNK:
                        filtered_roms[rom_id] = rom
                elif rom['nointro_status'] == NOINTRO_STATUS_UNKNOWN:
                    if dp_mode == NOINTRO_DMODE_HAVE_UNK or \
                       dp_mode == NOINTRO_DMODE_MISS_UNK or \
                       dp_mode == NOINTRO_DMODE_UNK:
                        filtered_roms[rom_id] = rom
                # >> Always copy roms with unknown status (NOINTRO_STATUS_NONE)
                else:
                    filtered_roms[rom_id] = rom
            roms = filtered_roms
            if not roms:
                kodi_notify('No ROMs to show with current filtering settings.')
                xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
                return

        # --- Load favourites ---
        # >> Optimisation: Transform the dictionary keys into a set. Sets are the fastest
        #    when checking if an element exists.
        roms_fav = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        roms_fav_set = set(roms_fav.keys())

        # --- Display ROMs ---
        loading_ticks_end = time.time()
        rendering_ticks_start = time.time()
        if view_mode == LAUNCHER_DMODE_FLAT:
            for key in sorted(roms, key = lambda x : roms[x]['m_name']):
                self._gui_render_rom_row(categoryID, launcherID, roms[key], key in roms_fav_set, view_mode, False)
        else:
            for key in sorted(roms, key = lambda x : roms[x]['m_name']):
                num_clones = len(pclone_index[key])
                self._gui_render_rom_row(categoryID, launcherID, roms[key], key in roms_fav_set, view_mode, True, num_clones)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
        rendering_ticks_end = time.time()

        # --- DEBUG Data loading/rendering statistics ---
        log_debug('Loading seconds   {0}'.format(loading_ticks_end - loading_ticks_start))
        log_debug('Rendering seconds {0}'.format(rendering_ticks_end - rendering_ticks_start))

    #
    # Former _add_rom()
    # Note that if we are rendering favourites, categoryID = VCATEGORY_FAVOURITES_ID
    # Note that if we are rendering virtual launchers, categoryID = VCATEGORY_*_ID
    #
    def _gui_render_rom_row(self, categoryID, launcherID, rom,
                            rom_in_fav = False, view_mode = LAUNCHER_DMODE_FLAT,
                            is_parent_launcher = False, num_clones = 0):
        # --- Do not render row if ROM is finished ---
        if rom['finished'] and self.settings['display_hide_finished']: return

        # --- Default values for flags ---
        AEL_InFav_bool_value     = AEL_INFAV_BOOL_VALUE_FALSE
        AEL_MultiDisc_bool_value = AEL_MULTIDISC_BOOL_VALUE_FALSE
        AEL_Fav_stat_value       = AEL_FAV_STAT_VALUE_NONE
        AEL_NoIntro_stat_value   = AEL_NOINTRO_STAT_VALUE_NONE
        AEL_PClone_stat_value    = AEL_PCLONE_STAT_VALUE_NONE

        # --- Create listitem row ---
        # NOTE A possible optimization is to compute rom_name, asset paths and flags on the calling 
        #      function. A lot of ifs will be avoided here and that will increase speed.
        rom_raw_name = rom['m_name']
        if categoryID == VCATEGORY_FAVOURITES_ID:
            icon_path      = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_icon', 'DefaultProgram.png')
            fanart_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_fanart')
            banner_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_banner')
            poster_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_poster')
            clearlogo_path = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_clearlogo')
            platform        = rom['platform']

            # --- Favourite status flag ---
            if self.settings['display_fav_status']:
                if   rom['fav_status'] == 'OK':                rom_name = '{0} [COLOR green][OK][/COLOR]'.format(rom_raw_name)
                elif rom['fav_status'] == 'Unlinked ROM':      rom_name = '{0} [COLOR yellow][Unlinked ROM][/COLOR]'.format(rom_raw_name)
                elif rom['fav_status'] == 'Unlinked Launcher': rom_name = '{0} [COLOR yellow][Unlinked Launcher][/COLOR]'.format(rom_raw_name)
                elif rom['fav_status'] == 'Broken':            rom_name = '{0} [COLOR red][Broken][/COLOR]'.format(rom_raw_name)
                else:                                          rom_name = rom_raw_name
            else:
                rom_name = rom_raw_name
            if   rom['fav_status'] == 'OK':                AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_OK
            elif rom['fav_status'] == 'Unlinked ROM':      AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_UNLINKED_ROM
            elif rom['fav_status'] == 'Unlinked Launcher': AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_UNLINKED_LAUNCHER
            elif rom['fav_status'] == 'Broken':            AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_BROKEN
            else:                                          AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_UNKNOWN
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            icon_path      = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_icon', 'DefaultProgram.png')
            fanart_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_fanart')
            banner_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_banner')
            poster_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_poster')
            clearlogo_path = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_clearlogo')
            platform       = rom['platform']

            # --- Favourite status flag ---
            if self.settings['display_fav_status']:
                if   rom['fav_status'] == 'OK':                rom_name = '{0} [COLOR green][OK][/COLOR]'.format(rom_raw_name)
                elif rom['fav_status'] == 'Unlinked ROM':      rom_name = '{0} [COLOR yellow][Unlinked ROM][/COLOR]'.format(rom_raw_name)
                elif rom['fav_status'] == 'Unlinked Launcher': rom_name = '{0} [COLOR yellow][Unlinked Launcher][/COLOR]'.format(rom_raw_name)
                elif rom['fav_status'] == 'Broken':            rom_name = '{0} [COLOR red][Broken][/COLOR]'.format(rom_raw_name)
                else:                                          rom_name = rom_raw_name
            else:
                rom_name = rom_raw_name
            if   rom['fav_status'] == 'OK':                AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_OK
            elif rom['fav_status'] == 'Unlinked ROM':      AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_UNLINKED_ROM
            elif rom['fav_status'] == 'Unlinked Launcher': AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_UNLINKED_LAUNCHER
            elif rom['fav_status'] == 'Broken':            AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_BROKEN
            else:                                          AEL_Fav_stat_value = AEL_FAV_STAT_VALUE_UNKNOWN
        elif categoryID == VCATEGORY_RECENT_ID:
            icon_path      = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_icon', 'DefaultProgram.png')
            fanart_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_fanart')
            banner_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_banner')
            poster_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_poster')
            clearlogo_path = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_clearlogo')
            platform       = rom['platform']
            rom_name = rom_raw_name
        elif categoryID == VCATEGORY_MOST_PLAYED_ID:
            icon_path      = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_icon', 'DefaultProgram.png')
            fanart_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_fanart')
            banner_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_banner')
            poster_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_poster')
            clearlogo_path = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_clearlogo')
            platform       = rom['platform']
            # >> Render number of number the ROM has been launched
            if rom['launch_count'] == 1:
                rom_name = '{0} [COLOR orange][{1} time][/COLOR]'.format(rom_raw_name, rom['launch_count'])
            else:
                rom_name = '{0} [COLOR orange][{1} times][/COLOR]'.format(rom_raw_name, rom['launch_count'])
        elif categoryID == VCATEGORY_TITLE_ID    or categoryID == VCATEGORY_YEARS_ID or \
             categoryID == VCATEGORY_GENRE_ID    or categoryID == VCATEGORY_DEVELOPER_ID or \
             categoryID == VCATEGORY_NPLAYERS_ID or categoryID == VCATEGORY_ESRB_ID or \
             categoryID == VCATEGORY_RATING_ID   or categoryID == VCATEGORY_CATEGORY_ID:
            icon_path      = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_icon', 'DefaultProgram.png')
            fanart_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_fanart')
            banner_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_banner')
            poster_path    = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_poster')
            clearlogo_path = asset_get_default_asset_Launcher_ROM(rom, rom, 'roms_default_clearlogo')
            platform       = rom['platform']

            # --- NoIntro status flag ---
            nstat = rom['nointro_status']
            if self.settings['display_nointro_stat']:
                if   nstat == NOINTRO_STATUS_HAVE:    rom_name = '{0} [COLOR green][Have][/COLOR]'.format(rom_raw_name)
                elif nstat == NOINTRO_STATUS_MISS:    rom_name = '{0} [COLOR magenta][Miss][/COLOR]'.format(rom_raw_name)
                elif nstat == NOINTRO_STATUS_UNKNOWN: rom_name = '{0} [COLOR yellow][Unknown][/COLOR]'.format(rom_raw_name)
                elif nstat == NOINTRO_STATUS_NONE:    rom_name = rom_raw_name
                else:                                 rom_name = '{0} [COLOR red][Status error][/COLOR]'.format(rom_raw_name)
            else:
                rom_name = rom_raw_name
            if   nstat == NOINTRO_STATUS_HAVE:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_HAVE
            elif nstat == NOINTRO_STATUS_MISS:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_MISS
            elif nstat == NOINTRO_STATUS_UNKNOWN: AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_UNKNOWN
            elif nstat == NOINTRO_STATUS_NONE:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_NONE

            # --- In Favourites ROM flag ---
            if self.settings['display_rom_in_fav'] and rom_in_fav: rom_name += ' [COLOR violet][Fav][/COLOR]'
            if rom_in_fav: AEL_InFav_bool_value = AEL_INFAV_BOOL_VALUE_TRUE
        # --- Standard launcher ---
        else:
            # >> If ROM has no fanart then use launcher fanart
            launcher = self.launchers[launcherID]
            kodi_def_icon = launcher['s_icon'] if launcher['s_icon'] else 'DefaultProgram.png'
            icon_path      = asset_get_default_asset_Launcher_ROM(rom, launcher, 'roms_default_icon', kodi_def_icon)
            fanart_path    = asset_get_default_asset_Launcher_ROM(rom, launcher, 'roms_default_fanart', launcher['s_fanart'])
            banner_path    = asset_get_default_asset_Launcher_ROM(rom, launcher, 'roms_default_banner')
            poster_path    = asset_get_default_asset_Launcher_ROM(rom, launcher, 'roms_default_poster')
            clearlogo_path = asset_get_default_asset_Launcher_ROM(rom, launcher, 'roms_default_clearlogo')
            platform = launcher['platform']

            # --- parent_launcher is True when rendering Parent ROMs in Parent/Clone view mode ---
            nstat = rom['nointro_status']
            if self.settings['display_nointro_stat']:
                if   nstat == NOINTRO_STATUS_HAVE:    rom_name = '{0} [COLOR green][Have][/COLOR]'.format(rom_raw_name)
                elif nstat == NOINTRO_STATUS_MISS:    rom_name = '{0} [COLOR magenta][Miss][/COLOR]'.format(rom_raw_name)
                elif nstat == NOINTRO_STATUS_UNKNOWN: rom_name = '{0} [COLOR yellow][Unknown][/COLOR]'.format(rom_raw_name)
                elif nstat == NOINTRO_STATUS_NONE:    rom_name = rom_raw_name
                else:                                 rom_name = '{0} [COLOR red][Status error][/COLOR]'.format(rom_raw_name)
            else:
                rom_name = rom_raw_name
            if is_parent_launcher and num_clones > 0:
                rom_name += ' [COLOR orange][{0} clones][/COLOR]'.format(num_clones)
            if   nstat == NOINTRO_STATUS_HAVE:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_HAVE
            elif nstat == NOINTRO_STATUS_MISS:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_MISS
            elif nstat == NOINTRO_STATUS_UNKNOWN: AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_UNKNOWN
            elif nstat == NOINTRO_STATUS_NONE:    AEL_NoIntro_stat_value = AEL_NOINTRO_STAT_VALUE_NONE
            # --- Mark clone ROMs ---
            pclone_status = rom['pclone_status']
            if pclone_status == PCLONE_STATUS_CLONE: rom_name += ' [COLOR orange][Clo][/COLOR]'
            if   pclone_status == PCLONE_STATUS_PARENT: AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_PARENT
            elif pclone_status == PCLONE_STATUS_CLONE:  AEL_PClone_stat_value = AEL_PCLONE_STAT_VALUE_CLONE
            # --- In Favourites ROM flag ---
            if self.settings['display_rom_in_fav'] and rom_in_fav: rom_name += ' [COLOR violet][Fav][/COLOR]'
            if rom_in_fav: AEL_InFav_bool_value = AEL_INFAV_BOOL_VALUE_TRUE

        # --- Set common flags to all launchers---
        if rom['disks']: AEL_MultiDisc_bool_value = AEL_MULTIDISC_BOOL_VALUE_TRUE

        # --- Add ROM to lisitem ---
        ICON_OVERLAY = 5 if rom['finished'] else 4
        listitem = xbmcgui.ListItem(rom_name)

        # Interesting... if text formatting labels are set in xbmcgui.ListItem() do not work. However, if
        # labels are set as Title in setInfo(), then they work but the alphabetical order is lost!
        # I solved this alphabetical ordering issue by placing a coloured tag [Fav] at the and of the ROM name
        # instead of changing the whole row colour.
        # >> BUG in Jarvis/Krypton skins. If 'year' is set to empty string a 0 is displayed on the
        # >>     skin. If year is not set then the correct icon is shown.
        if rom['m_year']:
            listitem.setInfo('video', {'title'   : rom_name,         'year'    : rom['m_year'],
                                       'genre'   : rom['m_genre'],   'studio'  : rom['m_developer'],
                                       'rating'  : rom['m_rating'],  'plot'    : rom['m_plot'],
                                       'trailer' : rom['s_trailer'], 'overlay' : ICON_OVERLAY })
        else:
            listitem.setInfo('video', {'title'   : rom_name,
                                       'genre'   : rom['m_genre'],   'studio'  : rom['m_developer'],
                                       'rating'  : rom['m_rating'],  'plot'    : rom['m_plot'],
                                       'trailer' : rom['s_trailer'], 'overlay' : ICON_OVERLAY })
        listitem.setProperty('nplayers', rom['m_nplayers'])
        listitem.setProperty('esrb', rom['m_esrb'])
        listitem.setProperty('platform', platform)

        # --- Set ROM artwork ---
        # >> AEL custom artwork fields
        listitem.setArt({'title'     : rom['s_title'],     'snap'    : rom['s_snap'],
                         'boxfront'  : rom['s_boxfront'],  'boxback' : rom['s_boxback'], 
                         'cartridge' : rom['s_cartridge'], 'flyer'   : rom['s_flyer'],
                         'map'       : rom['s_map'] })

        # >> Kodi official artwork fields
        listitem.setArt({'icon'   : icon_path,   'fanart' : fanart_path, 'banner' : banner_path,
                         'poster' : poster_path, 'clearlogo' : clearlogo_path})

        # --- ROM extrafanart ---
        # >> Build extrafanart dictionary
        # extrafanart_dic = {}
        # listitem.setArt(extrafanart_dic)

        # http://forum.kodi.tv/showthread.php?tid=221690&pid=1960874#pid1960874
        # This appears to be a common area of confusion with many addon developers, isPlayable doesn't
        # really mean the item is a playable, it only means Kodi will wait for a call to
        # xbmcplugin.setResolvedUrl and when this is called it will play the item. If you are going
        # to play the item using xbmc.Player().play() then as far as Kodi is concerned it isn't playable.
        #
        # http://forum.kodi.tv/showthread.php?tid=173986&pid=1519987#pid1519987
        # Otherwise the plugin is called back with an invalid handle (sys.arg[1]). It took me a lot of time
        # to figure this out...
        # if self._content_type == 'video':
        # listitem.setProperty('IsPlayable', 'false')
        # log_debug('Item Row IsPlayable false')

        # --- ROM flags (Skins will use these flags to render icons) ---
        listitem.setProperty(AEL_INFAV_BOOL_LABEL,     AEL_InFav_bool_value)
        listitem.setProperty(AEL_MULTIDISC_BOOL_LABEL, AEL_MultiDisc_bool_value)
        listitem.setProperty(AEL_FAV_STAT_LABEL,       AEL_Fav_stat_value)
        listitem.setProperty(AEL_NOINTRO_STAT_LABEL,   AEL_NoIntro_stat_value)
        listitem.setProperty(AEL_PCLONE_STAT_LABEL,    AEL_PClone_stat_value)

        # --- Create context menu ---
        romID = rom['id']
        commands = []
        if categoryID == VCATEGORY_FAVOURITES_ID:
            commands.append(('View Favourite ROM',         self._misc_url_RunPlugin('VIEW',              categoryID, launcherID, romID)))
            commands.append(('Edit ROM in Favourites',     self._misc_url_RunPlugin('EDIT_ROM',          categoryID, launcherID, romID)))
            commands.append(('Add ROM to Collection',      self._misc_url_RunPlugin('ADD_TO_COLLECTION', categoryID, launcherID, romID)))
            commands.append(('Search ROMs in Favourites',  self._misc_url_RunPlugin('SEARCH_LAUNCHER',   categoryID, launcherID)))
            commands.append(('Manage Favourite ROMs',      self._misc_url_RunPlugin('MANAGE_FAV',        categoryID, launcherID, romID)))
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            commands.append(('View Collection ROM',        self._misc_url_RunPlugin('VIEW',              categoryID, launcherID, romID)))
            commands.append(('Edit ROM in Collection',     self._misc_url_RunPlugin('EDIT_ROM',          categoryID, launcherID, romID)))
            commands.append(('Add ROM to AEL Favourites',  self._misc_url_RunPlugin('ADD_TO_FAV',        categoryID, launcherID, romID)))
            commands.append(('Search ROMs in Collection',  self._misc_url_RunPlugin('SEARCH_LAUNCHER',   categoryID, launcherID)))
            commands.append(('Manage Collection ROMs',     self._misc_url_RunPlugin('MANAGE_FAV',        categoryID, launcherID, romID)))
        elif categoryID == VCATEGORY_RECENT_ID or categoryID == VCATEGORY_MOST_PLAYED_ID:
            commands.append(('View ROM data', self._misc_url_RunPlugin('VIEW', categoryID, launcherID, romID)))
        elif categoryID == VCATEGORY_TITLE_ID    or categoryID == VCATEGORY_YEARS_ID  or \
             categoryID == VCATEGORY_GENRE_ID    or categoryID == VCATEGORY_DEVELOPER_ID or \
             categoryID == VCATEGORY_NPLAYERS_ID or categoryID == VCATEGORY_ESRB_ID   or \
             categoryID == VCATEGORY_RATING_ID   or categoryID == VCATEGORY_CATEGORY_ID:
            commands.append(('View ROM data',                   self._misc_url_RunPlugin('VIEW',              categoryID, launcherID, romID)))
            commands.append(('Add ROM to AEL Favourites',       self._misc_url_RunPlugin('ADD_TO_FAV',        categoryID, launcherID, romID)))
            commands.append(('Add ROM to Collection',           self._misc_url_RunPlugin('ADD_TO_COLLECTION', categoryID, launcherID, romID)))
            commands.append(('Search ROMs in Virtual Launcher', self._misc_url_RunPlugin('SEARCH_LAUNCHER',   categoryID, launcherID)))
        else:
            commands.append(('View ROM/Launcher',         self._misc_url_RunPlugin('VIEW',              categoryID, launcherID, romID)))
            if is_parent_launcher and num_clones > 0 and view_mode == LAUNCHER_DMODE_1G1R:
                commands.append(('Show clones', self._misc_url_RunPlugin('EXEC_SHOW_CLONE_ROMS', categoryID, launcherID, romID)))
            commands.append(('Edit ROM',                  self._misc_url_RunPlugin('EDIT_ROM',          categoryID, launcherID, romID)))
            commands.append(('Add ROM to AEL Favourites', self._misc_url_RunPlugin('ADD_TO_FAV',        categoryID, launcherID, romID)))
            commands.append(('Add ROM to Collection',     self._misc_url_RunPlugin('ADD_TO_COLLECTION', categoryID, launcherID, romID)))
            commands.append(('Search ROMs in Launcher',   self._misc_url_RunPlugin('SEARCH_LAUNCHER',   categoryID, launcherID)))
            commands.append(('Edit Launcher',             self._misc_url_RunPlugin('EDIT_LAUNCHER',     categoryID, launcherID)))
        commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        # URLs must be different depending on the content type. If not Kodi log will be filled with:
        # WARNING: CreateLoader - unsupported protocol(plugin) in the log. See http://forum.kodi.tv/showthread.php?tid=187954
        if is_parent_launcher and num_clones > 0 and view_mode == LAUNCHER_DMODE_PCLONE:
            url_str = self._misc_url('SHOW_CLONE_ROMS', categoryID, launcherID, romID)
            xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)
        else:
            url_str = self._misc_url('LAUNCH_ROM', categoryID, launcherID, romID)
            xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

    def _gui_render_AEL_scraper_rom_row(self, platform, game):
        # --- Add ROM to lisitem ---
        kodi_def_thumb = 'DefaultProgram.png'
        ICON_OVERLAY = 4
        listitem = xbmcgui.ListItem(game['description'])

        listitem.setInfo('video', {'title'   : game['description'],  'year'    : game['year'],
                                   'genre'   : game['genre'],        'plot'    : game['story'],
                                   'studio'  : game['manufacturer'], 'overlay' : ICON_OVERLAY })
        listitem.setProperty('nplayers', game['player'])
        listitem.setProperty('esrb', game['rating'])
        listitem.setProperty('platform', platform)

        # --- Set ROM artwork ---
        listitem.setArt({'icon' : kodi_def_thumb})

        # --- Create context menu ---
        commands = []
        commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        # When user clicks on a ROM show the raw database entry
        url_str = self._misc_url('VIEW_OS_ROM', 'AEL', platform, game['name'])
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

    def _gui_render_LB_scraper_rom_row(self, platform, game):
        # --- Add ROM to lisitem ---
        kodi_def_thumb = 'DefaultProgram.png'
        ICON_OVERLAY = 4
        listitem = xbmcgui.ListItem(game['Name'])

        listitem.setInfo('video', {'title'   : game['Name'],      'year'    : game['ReleaseYear'],
                                   'genre'   : game['Genres'],    'plot'    : game['Overview'],
                                   'studio'  : game['Publisher'], 'overlay' : ICON_OVERLAY })
        listitem.setProperty('nplayers', game['MaxPlayers'])
        listitem.setProperty('esrb', game['ESRB'])
        listitem.setProperty('platform', platform)

        # --- Set ROM artwork ---
        listitem.setArt({'icon' : kodi_def_thumb})

        # --- Create context menu ---
        commands = []
        commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
        listitem.addContextMenuItems(commands, replaceItems = True)

        # --- Add row ---
        # When user clicks on a ROM show the raw database entry
        url_str = self._misc_url('VIEW_OS_ROM', 'LaunchBox', platform, game['name'])
        xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = False)

    #
    # Renders the special category favourites, which is actually very similar to a ROM launcher
    # Note that only ROMs in a launcher can be added to favourites. Thus, no standalone launchers.
    # If user deletes launcher or favourite ROMs the ROM in favourites remain.
    # Favourites ROM information includes the application launcher and arguments to launch the ROM.
    # Basically, once a ROM is added to favourites is becomes kind of a standalone launcher.
    # Favourites has categoryID = 0 and launcherID = 0. Thus, other functions can differentiate
    # between a standard ROM and a favourite ROM.
    #
    # What if user changes the favourites Thumb/Fanart??? Where do we store them???
    # What about the NFO files of favourite ROMs???
    #
    # PROBLEM If user rescan ROMs then same ROMs will have different ID. An option to "relink"
    #         the favourites with their original ROMs must be provided, provided that the launcher
    #         is the same.
    # IMPROVEMENT Maybe it could be interesting to be able to export the list of favourites
    #             to HTML or something like that.
    #
    def _command_render_favourites(self):
        # >> Content type and sorting method
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

        # --- Load Favourite ROMs ---
        roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        if not roms:
            kodi_notify('Favourites is empty. Add ROMs to Favourites first.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Display Favourites ---
        for key in sorted(roms, key= lambda x : roms[x]['m_name']):
            self._gui_render_rom_row(VCATEGORY_FAVOURITES_ID, VLAUNCHER_FAVOURITES_ID, roms[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    # ---------------------------------------------------------------------------------------------
    # Virtual Launcher LisItem rendering
    # ---------------------------------------------------------------------------------------------
    #
    # Render virtual launchers inside a virtual category: Title, year, Genre, Studio, Category
    #
    def _command_render_virtual_category(self, virtual_categoryID):
        log_error('_command_render_virtual_category() Starting ...')
        # >> Kodi sorting methods
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_SIZE)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)

        # --- Load virtual launchers in this category ---
        if virtual_categoryID == VCATEGORY_TITLE_ID:
            vcategory_db_filename = VCAT_TITLE_FILE_PATH
            vcategory_name        = 'Browse by Title'
        elif virtual_categoryID == VCATEGORY_YEARS_ID:
            vcategory_db_filename = VCAT_YEARS_FILE_PATH
            vcategory_name        = 'Browse by Year'
        elif virtual_categoryID == VCATEGORY_GENRE_ID:
            vcategory_db_filename = VCAT_GENRE_FILE_PATH
            vcategory_name        = 'Browse by Genre'
        elif virtual_categoryID == VCATEGORY_DEVELOPER_ID:
            vcategory_db_filename = VCAT_DEVELOPER_FILE_PATH
            vcategory_name        = 'Browse by Developer'
        elif virtual_categoryID == VCATEGORY_NPLAYERS_ID:
            vcategory_db_filename = VCAT_NPLAYERS_FILE_PATH
            vcategory_name        = 'Browse by Number of Players'
        elif virtual_categoryID == VCATEGORY_ESRB_ID:
            vcategory_db_filename = VCAT_ESRB_FILE_PATH
            vcategory_name        = 'Browse by ESRB Rating'
        elif virtual_categoryID == VCATEGORY_RATING_ID:
            vcategory_db_filename = VCAT_RATING_FILE_PATH
            vcategory_name        = 'Browse by User Rating'
        elif virtual_categoryID == VCATEGORY_CATEGORY_ID:
            vcategory_db_filename = VCAT_CATEGORY_FILE_PATH
            vcategory_name        = 'Browse by Category'
        else:
            log_error('_command_render_virtual_category() Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            kodi_dialog_OK('Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            return

        # --- If the virtual category has no launchers then render nothing ---
        # >> Also, tell the user to update the virtual launcher database
        if not vcategory_db_filename.exists():
            kodi_dialog_OK('{0} database not found. '.format(vcategory_name) +
                           'Update the virtual category database first.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Load Virtual launchers XML file ---
        (VLauncher_timestamp, vcategory_launchers) = fs_load_VCategory_XML(vcategory_db_filename)

        # --- Check timestamps and warn user if database should be regenerated ---
        if VLauncher_timestamp < self.update_timestamp:
            kodi_dialog_OK('Categories/Launchers/ROMs were modified. Virtual category database should be updated!')

        # --- Render virtual launchers rows ---
        for vlauncher_id in vcategory_launchers:
            vlauncher = vcategory_launchers[vlauncher_id]
            vlauncher_name = vlauncher['name'] + '  ({0} ROM/s)'.format(vlauncher['rom_count'])
            listitem = xbmcgui.ListItem(vlauncher_name)
            listitem.setInfo('video', {'title'    : 'Title text',
                                       # 'label'    : 'Label text',
                                       # 'plot'     : 'Plot text',
                                       # 'genre'    : 'Genre text',
                                       # 'year'     : 'Year text',
                                       'overlay'  : 4,
                                       'size'     : vlauncher['rom_count'] })
            listitem.setArt({'icon': 'DefaultFolder.png'})

            # --- Create context menu ---
            commands = []
            commands.append(('Search ROMs in Virtual Launcher', self._misc_url_RunPlugin('SEARCH_LAUNCHER', virtual_categoryID, vlauncher_id)))
            commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)', ))
            commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__), ))
            listitem.addContextMenuItems(commands, replaceItems = True)

            url_str = self._misc_url('SHOW_VLAUNCHER_ROMS', virtual_categoryID, vlauncher_id)
            xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Renders ROMs in a virtual launcher.
    #
    def _command_render_virtual_launcher_roms(self, virtual_categoryID, virtual_launcherID):
        log_error('_command_render_virtual_launcher_roms() Starting ...')
        # >> Content type and sorting method
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

        # --- Load virtual launchers in this category ---
        if   virtual_categoryID == VCATEGORY_TITLE_ID:     vcategory_db_dir = VIRTUAL_CAT_TITLE_DIR
        elif virtual_categoryID == VCATEGORY_YEARS_ID:     vcategory_db_dir = VIRTUAL_CAT_YEARS_DIR
        elif virtual_categoryID == VCATEGORY_GENRE_ID:     vcategory_db_dir = VIRTUAL_CAT_GENRE_DIR
        elif virtual_categoryID == VCATEGORY_DEVELOPER_ID: vcategory_db_dir = VIRTUAL_CAT_DEVELOPER_DIR
        elif virtual_categoryID == VCATEGORY_NPLAYERS_ID:  vcategory_db_dir = VIRTUAL_CAT_NPLAYERS_DIR
        elif virtual_categoryID == VCATEGORY_ESRB_ID:      vcategory_db_dir = VIRTUAL_CAT_ESRB_DIR
        elif virtual_categoryID == VCATEGORY_RATING_ID:    vcategory_db_dir = VIRTUAL_CAT_RATING_DIR
        elif virtual_categoryID == VCATEGORY_CATEGORY_ID:  vcategory_db_dir = VIRTUAL_CAT_CATEGORY_DIR
        else:
            log_error('_command_render_virtual_launcher_roms() Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            kodi_dialog_OK('Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            return

        # --- Load Virtual Launcher DB ---
        hashed_db_filename = vcategory_db_dir.pjoin(virtual_launcherID + '.json')
        if not hashed_db_filename.exists():
            kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
            return
        roms = fs_load_VCategory_ROMs_JSON(vcategory_db_dir, virtual_launcherID)
        if not roms:
            kodi_notify('Virtual category ROMs XML empty. Add items to favourites first.')
            return

        # --- Load favourites ---
        # >> Optimisation: Transform the dictionary keys into a set. Sets are the fastest
        #    when checking if an element exists.
        roms_fav = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        roms_fav_set = set(roms_fav.keys())

        # --- Display Favourites ---
        for key in sorted(roms, key= lambda x : roms[x]['m_name']):
            self._gui_render_rom_row(virtual_categoryID, virtual_launcherID, roms[key], key in roms_fav_set)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Renders ROMs in a AEL offline Scraper virtual launcher (aka platform)
    #
    def _command_render_AEL_scraper_roms(self, platform):
        log_debug('_command_render_AEL_scraper_roms() platform = "{0}"'.format(platform))
        # >> Content type and sorting method
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

        # >> If XML DB not available tell user and leave
        xml_file = platform_AEL_to_Offline_GameDBInfo_XML[platform]
        if not xml_file:
            kodi_notify_warn('{0} database not available yet.'.format(platform))
            # kodi_refresh_container()
            return

        # --- Load offline scraper XML file ---
        loading_ticks_start = time.time()
        xml_path_FN = CURRENT_ADDON_DIR.pjoin(xml_file)
        log_debug('xml_path_FN OP {0}'.format(xml_path_FN.getOriginalPath()))
        log_debug('xml_path_FN  P {0}'.format(xml_path_FN.getPath()))
        games = audit_load_OfflineScraper_XML(xml_path_FN.getPath())

        # --- Display offline scraper ROMs ---
        loading_ticks_end = time.time()
        rendering_ticks_start = time.time()
        for key in sorted(games, key= lambda x : games[x]['name']):
            self._gui_render_AEL_scraper_rom_row(platform, games[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
        rendering_ticks_end = time.time()

        # --- DEBUG Data loading/rendering statistics ---
        log_debug('Loading seconds   {0}'.format(loading_ticks_end - loading_ticks_start))
        log_debug('Rendering seconds {0}'.format(rendering_ticks_end - rendering_ticks_start))

    #
    # Renders ROMs in a LaunchBox offline Scraper virtual launcher (aka platform)
    #
    def _command_render_LB_scraper_roms(self, platform):
        log_debug('_command_render_LB_scraper_roms() platform = "{0}"'.format(platform))
        # >> Content type and sorting method
        self._misc_set_all_sorting_methods()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

        # >> If XML DB not available tell user and leave
        xml_file = platform_AEL_to_LB_XML[platform]
        if not xml_file:
            kodi_notify_warn('{0} database not available yet.'.format(platform))
            # kodi_refresh_container()
            return

        # --- Load offline scraper XML file ---
        loading_ticks_start = time.time()
        xml_path_FN = CURRENT_ADDON_DIR.pjoin(xml_file)
        log_debug('xml_path_FN OP {0}'.format(xml_path_FN.getOriginalPath()))
        log_debug('xml_path_FN  P {0}'.format(xml_path_FN.getPath()))
        games = audit_load_OfflineScraper_XML(xml_path_FN.getPath())

        # --- Display offline scraper ROMs ---
        loading_ticks_end = time.time()
        rendering_ticks_start = time.time()
        for key in sorted(games, key= lambda x : games[x]['name']):
            self._gui_render_LB_scraper_rom_row(platform, games[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
        rendering_ticks_end = time.time()

        # --- DEBUG Data loading/rendering statistics ---
        log_debug('Loading seconds   {0}'.format(loading_ticks_end - loading_ticks_start))
        log_debug('Rendering seconds {0}'.format(rendering_ticks_end - rendering_ticks_start))

    #
    # Render the Recently played and Most Played virtual launchers.
    #
    def _command_render_recently_played(self):
        # >> Content type and sorting method
        self._misc_set_default_sorting_method()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

        # --- Load Recently Played favourite ROM list and create and OrderedDict ---
        rom_list = fs_load_Collection_ROMs_JSON(RECENT_PLAYED_FILE_PATH)
        if not rom_list:
            kodi_notify('Recently played list is empty. Play some ROMs first!')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Display recently player ROM list ---
        for rom in rom_list:
            self._gui_render_rom_row(VCATEGORY_RECENT_ID, VLAUNCHER_RECENT_ID, rom)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _command_render_most_played(self):
        # >> Content type and sorting method
        self._misc_set_default_sorting_method()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

        # --- Load Most Played favourite ROMs ---
        roms = fs_load_Favourites_JSON(MOST_PLAYED_FILE_PATH)
        if not roms:
            kodi_notify('Most played ROMs list  is empty. Play some ROMs first!.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Display most played ROMs, order by number of launchs ---
        for key in sorted(roms, key = lambda x : roms[x]['launch_count'], reverse = True):
            self._gui_render_rom_row(VCATEGORY_MOST_PLAYED_ID, VLAUNCHER_MOST_PLAYED_ID, roms[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Render all ROMs
    # This command is called by skins. Not advisable to use it if there are many ROMs...
    #
    def _command_render_all_ROMs(self):
        # --- Make a dictionary having all ROMs in all Launchers ---
        log_debug('_command_render_all_ROMs() Creating list of all ROMs in all Launchers')
        all_roms = {}
        for launcher_id in self.launchers:
            launcher = self.launchers[launcher_id]
            # If launcher is standalone skip
            if launcher['rompath'] == '': continue
            roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)
            temp_roms = {}
            for rom_id in roms:
                temp_rom                = roms[rom_id].copy()
                temp_rom['launcher_id'] = launcher_id
                temp_rom['category_id'] = launcher['categoryID']
                temp_roms[rom_id] = temp_rom
            all_roms.update(temp_roms)

        # --- Load favourites ---
        roms_fav = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        roms_fav_set = set(roms_fav.keys())

        # --- Set content type and sorting methods ---
        self._misc_set_default_sorting_method()

        # --- Render ROMs ---
        for rom_id in sorted(all_roms, key = lambda x : all_roms[x]['m_name']):
            self._gui_render_rom_row(all_roms[rom_id]['category_id'], all_roms[rom_id]['launcher_id'],
                                     all_roms[rom_id], rom_id in roms_fav_set)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Adds ROM to favourites
    #
    def _command_add_to_favourites(self, categoryID, launcherID, romID):
        # >> ROM in Virtual Launcher
        if categoryID == VCATEGORY_TITLE_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_TITLE_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_YEARS_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_YEARS_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_GENRE_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_GENRE_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_DEVELOPER_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_DEVELOPER_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_CATEGORY_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_CATEGORY_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        # >> ROMs in standard launcher
        else:
            launcher = self.launchers[launcherID]
            roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)

        # >> Sanity check
        if not roms:
            kodi_dialog_OK('Empty roms launcher in _command_add_to_favourites(). This is a bug, please report it.')
            return

        # --- Load favourites ---
        roms_fav = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)

        # --- DEBUG info ---
        log_verb('_command_add_to_favourites() Adding ROM to Favourites')
        log_verb('_command_add_to_favourites() romID  {0}'.format(romID))
        log_verb('_command_add_to_favourites() m_name {0}'.format(roms[romID]['m_name']))

        # Check if ROM already in favourites an warn user if so
        if romID in roms_fav:
            log_verb('Already in favourites')
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher',
                               'ROM {0} is already on AEL Favourites. Overwrite it?'.format(roms[romID]['m_name']))
            if not ret:
                log_verb('User does not want to overwrite. Exiting.')
                return
        # Confirm if rom should be added
        else:
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher',
                                'ROM {0}. Add this ROM to AEL Favourites?'.format(roms[romID]['m_name']))
            if not ret:
                log_verb('User does not confirm addition. Exiting.')
                return

        # --- Add ROM to favourites ROMs and save to disk ---
        roms_fav[romID] = fs_get_Favourite_from_ROM(roms[romID], launcher)
        # >> If thumb is empty then use launcher thum. / If fanart is empty then use launcher fanart.
        # if roms_fav[romID]['thumb']  == '': roms_fav[romID]['thumb']  = launcher['thumb']
        # if roms_fav[romID]['fanart'] == '': roms_fav[romID]['fanart'] = launcher['fanart']
        fs_write_Favourites_JSON(FAV_JSON_FILE_PATH, roms_fav)
        kodi_notify('ROM {0} added to Favourites'.format(roms[romID]['m_name']))
        kodi_refresh_container()

    #
    # Manage Favourite/Collection ROMs as a whole.
    #
    def _command_manage_favourites(self, categoryID, launcherID, romID):
        # --- Load ROMs ---
        if categoryID == VCATEGORY_FAVOURITES_ID:
            log_debug('_command_manage_favourites() Managing Favourite ROMs')
            roms_fav = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            log_debug('_command_manage_favourites() Managing Collection ROMs')
            (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
            collection = collections[launcherID]
            roms_json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
            collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
            # NOTE ROMs in a collection are stored as a list and ROMs in Favourites are stored as
            #      a dictionary. Convert the Collection list into an ordered dictionary and then
            #      converted back the ordered dictionary into a list before saving the collection.
            roms_fav = OrderedDict()
            for collection_rom in collection_rom_list:
                roms_fav[collection_rom['id']] = collection_rom
        else:
            kodi_dialog_OK('_command_manage_favourites() should be called for Favourites or Collections. '
                           'This is a bug, please report it.')
            return

        # --- Show selection dialog ---
        dialog = xbmcgui.Dialog()
        if categoryID == VCATEGORY_FAVOURITES_ID:
            type = dialog.select('Manage Favourite ROMs',
                                ['Check Favourite ROMs',
                                 'Repair Unlinked Launcher/Broken ROMs (by filename)',
                                 'Repair Unlinked Launcher/Broken ROMs (by basename)',
                                 'Repair Unlinked ROMs'])
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            type = dialog.select('Manage Collection ROMs',
                                ['Check Collection ROMs',
                                 'Repair Unlinked Launcher/Broken ROMs (by filename)',
                                 'Repair Unlinked Launcher/Broken ROMs (by basename)',
                                 'Repair Unlinked ROMs'])

        # --- Check Favourite ROMs ---
        if type == 0:
            # >> This function opens a progress window to notify activity
            self._fav_check_favourites(roms_fav)

            # --- Print a report of issues found ---
            if categoryID == VCATEGORY_FAVOURITES_ID:
                kodi_dialog_OK('You have {0} ROMs in Favourites. '.format(self.num_fav_roms) +
                               '{0} Unlinked Launcher, '.format(self.num_fav_ulauncher) +
                               '{0} Unliked ROM and '.format(self.num_fav_urom) +
                               '{0} Broken.'.format(self.num_fav_broken))
            elif categoryID == VCATEGORY_COLLECTIONS_ID:
                kodi_dialog_OK('You have {0} ROMs in Collection "{1}". '.format(self.num_fav_roms, collection['m_name']) +
                               '{0} Unlinked Launcher, '.format(self.num_fav_ulauncher) +
                               '{0} Unliked ROM and '.format(self.num_fav_urom) +
                               '{0} are Broken.'.format(self.num_fav_broken))

        # --- Repair all Unlinked Launcher/Broken ROMs ---
        # type == 1 --> Repair by filename match
        # type == 2 --> Repair by ROM basename match
        elif type == 1 or type == 2:
            # 1) Traverse list of Favourites.
            # 2) For each favourite traverse all Launchers.
            # 3) Search for a ROM with same filename or same rom_base.
            #    If found, then replace romID in Favourites with romID of found ROM. Do not copy
            #    any metadata because user maybe customised the Favourite ROM.
            log_info('Repairing Unlinked Launcher/Broken ROMs (type = {0}) ...'.format(type))

            # --- Ask user about how to repair the Fav ROMs ---
            dialog = xbmcgui.Dialog()
            repair_mode = dialog.select('How to repair ROMs?',
                                        ['Relink and update launcher info',
                                         'Relink and update metadata',
                                         'Relink and update artwork',
                                         'Relink and update everything'])
            if repair_mode < 0: return
            log_verb('_command_manage_favourites() Repair mode {0}'.format(repair_mode))

            # >> Refreshing Favourite status will locate Unlinked/Broken ROMs.
            self._fav_check_favourites(roms_fav)

            # >> Repair Unlinked Launcher/Broken ROMs, Step 1
            # NOTE Dictionaries cannot change size when iterating them. Make a list of found ROMs
            #      and repair broken Favourites on a second pass
            pDialog = xbmcgui.DialogProgress()
            xbmc.sleep(100)
            num_progress_items = len(roms_fav)
            i = 0
            pDialog.create('Advanced Emulator Launcher', 'Repairing Unlinked Launcher/Broken ROMs ...')
            repair_rom_list = []
            num_broken_ROMs = 0
            for rom_fav_ID in roms_fav:
                pDialog.update(i * 100 / num_progress_items)
                if pDialog.iscanceled():
                    pDialog.close()
                    kodi_dialog_OK('Repair cancelled. No changes has been done.')
                    return
                i += 1

                # >> Only process Unlinked Launcher ROMs
                if roms_fav[rom_fav_ID]['fav_status'] == 'OK': continue
                if roms_fav[rom_fav_ID]['fav_status'] == 'Unlinked ROM': continue
                fav_name = roms_fav[rom_fav_ID]['m_name']
                num_broken_ROMs += 1
                log_info('_command_manage_favourites() Repairing Fav ROM "{0}"'.format(fav_name))
                log_info('_command_manage_favourites() Fav ROM status "{0}"'.format(roms_fav[rom_fav_ID]['fav_status']))

                # >> Traverse all launchers and find rom by filename or base name
                ROM_FN_FAV = FileName(roms_fav[rom_fav_ID]['filename'])
                filename_found = False
                for launcher_id in self.launchers:
                    # >> Load launcher ROMs
                    roms = fs_load_ROMs_JSON(ROMS_DIR, self.launchers[launcher_id])
                    for rom_id in roms:
                        ROM_FN = FileName(roms[rom_id]['filename'])
                        fav_name = roms_fav[rom_fav_ID]['m_name']
                        if type == 1 and roms_fav[rom_fav_ID]['filename'] == roms[rom_id]['filename']:
                            log_info('_command_manage_favourites() Favourite {0} matched by filename!'.format(fav_name))
                            log_info('_command_manage_favourites() Launcher {0}'.format(launcher_id))
                            log_info('_command_manage_favourites() ROM {0}'.format(rom_id))
                        elif type == 2 and ROM_FN_FAV.getBase() == ROM_FN.getBase():
                            log_info('_command_manage_favourites() Favourite {0} matched by basename!'.format(fav_name))
                            log_info('_command_manage_favourites() Launcher {0}'.format(launcher_id))
                            log_info('_command_manage_favourites() ROM {0}'.format(rom_id))
                        else:
                            continue
                        # >> Match found. Break all for loops inmediately.
                        filename_found      = True
                        new_fav_rom_ID      = rom_id
                        new_fav_rom_laun_ID = launcher_id
                        break
                    if filename_found: break

                # >> Add ROM to the list of ROMs to be repaired.
                if filename_found:
                    rom_repair = {}
                    rom_repair['old_fav_rom_ID']      = rom_fav_ID
                    rom_repair['new_fav_rom_ID']      = new_fav_rom_ID
                    rom_repair['new_fav_rom_laun_ID'] = new_fav_rom_laun_ID
                    rom_repair['old_fav_rom']         = roms_fav[rom_fav_ID]
                    rom_repair['parent_rom']          = roms[new_fav_rom_ID]
                    rom_repair['parent_launcher']     = self.launchers[new_fav_rom_laun_ID]
                    repair_rom_list.append(rom_repair)
                else:
                    log_verb('_command_manage_favourites() ROM {0} filename not found in any launcher'.format(fav_name))
            log_info('_command_manage_favourites() Step 1 found {0} unlinked launcher/broken ROMs'.format(num_broken_ROMs))
            log_info('_command_manage_favourites() Step 1 found {0} ROMs to be repaired'.format(len(repair_rom_list)))
            pDialog.update(i * 100 / num_progress_items)
            pDialog.close()

            # >> Pass 2. Repair Favourites. Changes roms_fav dictionary.
            # >> Step 2 is very fast, so no progress dialog.
            num_repaired_ROMs = 0
            for rom_repair in repair_rom_list:
                old_fav_rom_ID      = rom_repair['old_fav_rom_ID']
                new_fav_rom_ID      = rom_repair['new_fav_rom_ID']
                new_fav_rom_laun_ID = rom_repair['new_fav_rom_laun_ID']
                old_fav_rom         = rom_repair['old_fav_rom']
                parent_rom          = rom_repair['parent_rom']
                parent_launcher     = rom_repair['parent_launcher']
                log_debug('_command_manage_favourites() Repairing ROM {0}'.format(old_fav_rom_ID))
                log_debug('_command_manage_favourites() Name          {0}'.format(old_fav_rom['m_name']))
                log_debug('_command_manage_favourites() New ROM       {0}'.format(new_fav_rom_ID))
                log_debug('_command_manage_favourites() New Launcher  {0}'.format(new_fav_rom_laun_ID))

                # >> Relink Favourite ROM. Removed old Favourite before inserting new one.
                new_fav_rom = fs_repair_Favourite_ROM(repair_mode, old_fav_rom, parent_rom, parent_launcher)
                roms_fav.pop(old_fav_rom_ID)
                roms_fav[new_fav_rom['id']] = new_fav_rom
                num_repaired_ROMs += 1
            log_debug('_command_manage_favourites() Repaired {0} ROMs'.format(num_repaired_ROMs))

            # >> Show info to user
            if type == 1:
                kodi_dialog_OK('Found {0} Unlinked Launcher/Broken ROMs. '.format(num_broken_ROMs) +
                               'Of those, {0} were repaired by filename match.'.format(num_repaired_ROMs))
            elif type == 2:
                kodi_dialog_OK('Found {0} Unlinked Launcher/Broken ROMs. '.format(num_broken_ROMs) +
                               'Of those, {0} were repaired by rombase match.'.format(num_repaired_ROMs))
            else:
                log_error('_command_manage_favourites() type = {0} unknown value!'.format(type))
                kodi_dialog_OK('Unknown type = {0}. This is a bug, please report it.'.format(type))
                return

        # --- Repair Unliked ROMs ---
        elif type == 3:
            # 1) Traverse list of Favourites.
            # 2) If romID not found in launcher, then search for a ROM with same basename.
            log_info('Repairing Repair Unliked ROMs (type = {0}) ...'.format(type))

            # --- Ask user about how to repair the Fav ROMs ---
            dialog = xbmcgui.Dialog()
            repair_mode = dialog.select('How to repair ROMs?',
                                        ['Relink and update launcher info',
                                         'Relink and update metadata',
                                         'Relink and update artwork',
                                         'Relink and update everything'])
            if repair_mode < 0: return
            log_verb('_command_manage_favourites() Repair mode {0}'.format(repair_mode))

            # >> Refreshing Favourite status will locate Unlinked ROMs.
            self._fav_check_favourites(roms_fav)

            # >> Repair Unlinked ROMs
            pDialog = xbmcgui.DialogProgress()
            num_progress_items = len(roms_fav)
            i = 0
            pDialog.create('Advanced Emulator Launcher', 'Repairing Unlinked Favourite ROMs...')
            repair_rom_list = []
            num_unlinked_ROMs = 0
            for rom_fav_ID in roms_fav:
                pDialog.update(i * 100 / num_progress_items)
                i += 1

                # >> Only process Unlinked ROMs
                rom_fav = roms_fav[rom_fav_ID]
                if rom_fav['fav_status'] != 'Unlinked ROM': continue
                num_unlinked_ROMs += 1
                fav_name = roms_fav[rom_fav_ID]['m_name']
                log_info('_command_manage_favourites() Repairing Fav ROM "{0}"'.format(fav_name))
                log_info('_command_manage_favourites() Fav ROM status "{0}"'.format(rom_fav['fav_status']))

                # >> Get ROMs of launcher
                launcher_id   = rom_fav['launcherID']
                launcher_roms = fs_load_ROMs_JSON(ROMS_DIR, self.launchers[launcher_id])

                # >> Is there a ROM with same basename (including extension) as the Favourite ROM?
                filename_found = False
                ROM_FAV_FN = FileName(rom_fav['filename'])
                for rom_id in launcher_roms:
                    ROM_FN = FileName(launcher_roms[rom_id]['filename'])
                    if ROM_FAV_FN.getBase() == ROM_FN.getBase():
                        filename_found = True
                        new_fav_rom_ID = rom_id
                        break

                # >> Add ROM to the list of ROMs to be repaired. A dictionary cannot change when
                # >> it's being iterated! An Excepcion will be raised if so.
                if filename_found:
                    log_debug('_command_manage_favourites() Relinked to {0}'.format(new_fav_rom_ID))
                    rom_repair = {}
                    rom_repair['old_fav_rom_ID']      = rom_fav_ID
                    rom_repair['new_fav_rom_ID']      = new_fav_rom_ID
                    rom_repair['new_fav_rom_laun_ID'] = launcher_id
                    rom_repair['old_fav_rom']         = roms_fav[rom_fav_ID]
                    rom_repair['parent_rom']          = launcher_roms[new_fav_rom_ID]
                    rom_repair['parent_launcher']     = self.launchers[launcher_id]
                    repair_rom_list.append(rom_repair)
                else:
                    log_debug('_command_manage_favourites() Filename in launcher not found')
            pDialog.update(i * 100 / num_progress_items)
            pDialog.close()

            # >> Pass 2. Repair Favourites. Changes roms_fav dictionary.
            # >> Step 2 is very fast, so no progress dialog.
            num_repaired_ROMs = 0
            for rom_repair in repair_rom_list:
                old_fav_rom_ID      = rom_repair['old_fav_rom_ID']
                new_fav_rom_ID      = rom_repair['new_fav_rom_ID']
                new_fav_rom_laun_ID = rom_repair['new_fav_rom_laun_ID']
                old_fav_rom         = rom_repair['old_fav_rom']
                parent_rom          = rom_repair['parent_rom']
                parent_launcher     = rom_repair['parent_launcher']
                log_debug('_command_manage_favourites() Repairing ROM {0}'.format(old_fav_rom_ID))
                log_debug('_command_manage_favourites()  New ROM      {0}'.format(new_fav_rom_ID))
                log_debug('_command_manage_favourites()  New Launcher {0}'.format(new_fav_rom_laun_ID))

                # >> Relink Favourite ROM. Removed old Favourite before inserting new one.
                new_fav_rom = fs_repair_Favourite_ROM(repair_mode, old_fav_rom, parent_rom, parent_launcher)
                roms_fav.pop(old_fav_rom_ID)
                roms_fav[new_fav_rom['id']] = new_fav_rom
                num_repaired_ROMs += 1
            log_debug('_command_manage_favourites() Repaired {0} ROMs'.format(num_repaired_ROMs))

            # >> Show info to user
            kodi_dialog_OK('Found {0} Unlinked ROMs. '.format(num_unlinked_ROMs) +
                           'Of those, {0} were repaired.'.format(num_repaired_ROMs))

        # --- User cancelled dialog ---
        elif type < 0:
            return

        # --- If we reach this point save favourites and refresh container ---
        if categoryID == VCATEGORY_FAVOURITES_ID:
            fs_write_Favourites_JSON(FAV_JSON_FILE_PATH, roms_fav)
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            # >> Convert back the OrderedDict into a list and save Collection
            collection_rom_list = []
            for key in roms_fav:
                collection_rom_list.append(roms_fav[key])
            json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
            fs_write_Collection_ROMs_JSON(json_file, collection_rom_list)
        kodi_refresh_container()

    #
    # Check ROMs in favourites and set fav_status field.
    # roms_fav edited by passing by assigment, dictionaries are mutable.
    #
    def _fav_check_favourites(self, roms_fav):
        # --- Statistics ---
        self.num_fav_roms = len(roms_fav)
        self.num_fav_ulauncher = 0
        self.num_fav_urom      = 0
        self.num_fav_broken    = 0

        # --- Reset fav_status filed for all favourites ---
        log_debug('_fav_check_favourites() STEP 0: Reset status')
        for rom_fav_ID in roms_fav:
            roms_fav[rom_fav_ID]['fav_status'] = 'OK'

        # --- Progress dialog ---
        # >> Important to avoid multithread execution of the plugin and race conditions
        pDialog = xbmcgui.DialogProgress()

        # STEP 1: Find Favourites with missing launchers
        log_debug('_fav_check_favourites() STEP 1: Search unlinked Launchers')
        num_progress_items = len(roms_fav)
        i = 0
        pDialog.create('Advanced Emulator Launcher', 'Checking Favourite ROMs. Step 1 of 3 ...')
        for rom_fav_ID in roms_fav:
            pDialog.update(i * 100 / num_progress_items)
            i += 1
            if roms_fav[rom_fav_ID]['launcherID'] not in self.launchers:
                log_verb('Fav ROM "{0}" Unlinked Launcher because launcherID not in self.launchers'.format(roms_fav[rom_fav_ID]['m_name']))
                roms_fav[rom_fav_ID]['fav_status'] = 'Unlinked Launcher'
                self.num_fav_ulauncher += 1
        pDialog.update(i * 100 / num_progress_items)
        pDialog.close()

        # STEP 2: Find missing ROM ID
        # >> Get a list of launchers Favourite ROMs belong
        log_debug('_fav_check_favourites() STEP 2: Search unlinked ROMs')
        launchers_fav = set()
        for rom_fav_ID in roms_fav: launchers_fav.add(roms_fav[rom_fav_ID]['launcherID'])

        # >> Traverse list of launchers. For each launcher, load ROMs it and check all favourite ROMs
        # >> that belong to that launcher.
        num_progress_items = len(launchers_fav)
        i = 0
        pDialog.create('Advanced Emulator Launcher', 'Checking Favourite ROMs. Step 2 of 3...')
        for launcher_id in launchers_fav:
            pDialog.update(i * 100 / num_progress_items)
            i += 1

            # >> If Favourite does not have launcher skip it. It has been marked as 'Unlinked Launcher'
            # >> in step 1.
            if launcher_id not in self.launchers: continue

            # >> Load launcher ROMs
            roms = fs_load_ROMs_JSON(ROMS_DIR, self.launchers[launcher_id])

            # Traverse all favourites and check them if belong to this launcher.
            # This should be efficient because traversing favourites is cheap but loading ROMs is expensive.
            for rom_fav_ID in roms_fav:
                if roms_fav[rom_fav_ID]['launcherID'] == launcher_id:
                    # Check if ROM ID exists
                    if roms_fav[rom_fav_ID]['id'] not in roms:
                        log_verb('Fav ROM "{0}" Unlinked ROM because romID not in launcher ROMs'.format(roms_fav[rom_fav_ID]['m_name']))
                        roms_fav[rom_fav_ID]['fav_status'] = 'Unlinked ROM'
                        self.num_fav_urom += 1
        pDialog.update(i * 100 / num_progress_items)
        pDialog.close()

        # STEP 3: Check if file exists. Even if the ROM ID is not there because user
        # deleted ROM or launcher, the file may still be there.
        log_debug('_fav_check_favourites() STEP 3: Search broken ROMs')
        num_progress_items = len(launchers_fav)
        i = 0
        pDialog.create('Advanced Emulator Launcher', 'Checking Favourite ROMs. Step 3 of 3 ...')
        for rom_fav_ID in roms_fav:
            pDialog.update(i * 100 / num_progress_items)
            i += 1
            romFile = FileName(roms_fav[rom_fav_ID]['filename'])
            if not romFile.exists():
                log_verb('Fav ROM "{0}" broken because filename does not exist'.format(roms_fav[rom_fav_ID]['m_name']))
                roms_fav[rom_fav_ID]['fav_status'] = 'Broken'
                self.num_fav_broken += 1
        pDialog.update(i * 100 / num_progress_items)
        pDialog.close()

    #
    # Renders a listview with all collections
    #
    def _command_render_collections(self):
        # >> Kodi sorting method
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_LABEL)
        xbmcplugin.addSortMethod(handle = self.addon_handle, sortMethod = xbmcplugin.SORT_METHOD_UNSORTED)
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_LAUNCHERS)

        # --- Load collection index ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)

        # --- If the virtual category has no launchers then render nothing ---
        if not collections:
            kodi_notify('No collections in database. Add a collection first.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Render ROM Collections as Categories ---
        for collection_id in collections:
            # --- Create listitem ---
            collection = collections[collection_id]
            collection_name = collection['m_name']
            listitem = xbmcgui.ListItem(collection_name)
            listitem.setInfo('video', {'title'   : collection['m_name'],    'genre'   : collection['m_genre'],
                                       'plot'    : collection['m_plot'],    'rating'  : collection['m_rating'],
                                       'trailer' : collection['s_trailer'], 'overlay' : 4 })
            icon_path      = asset_get_default_asset_Category(collection, 'default_icon', 'DefaultFolder.png')
            fanart_path    = asset_get_default_asset_Category(collection, 'default_fanart')
            banner_path    = asset_get_default_asset_Category(collection, 'default_banner')
            poster_path    = asset_get_default_asset_Category(collection, 'default_poster')
            clearlogo_path = asset_get_default_asset_Category(collection, 'default_clearlogo')
            listitem.setArt({'icon'   : icon_path,   'fanart' : fanart_path,
                             'banner' : banner_path, 'poster' : poster_path, 'clearlogo' : clearlogo_path})

            # --- Extrafanart ---
            collections_asset_dir = FileName(self.settings['collections_asset_dir'])
            extrafanart_dir = collections_asset_dir + collection['m_name']
            log_debug('_command_render_collections() EF dir {0}'.format(extrafanart_dir.getPath()))
            extrafanart_dic = {}
            for i in range(25):
                # --- PNG ---
                extrafanart_file = extrafanart_dir + 'fanart{0}.png'.format(i)
                log_debug('_command_render_collections() test   {0}'.format(extrafanart_file.getPath()))
                if extrafanart_file.exists():
                    log_debug('_command_render_collections() Adding extrafanart #{0}'.format(i))
                    extrafanart_dic['extrafanart{0}'.format(i)] = extrafanart_file.getOriginalPath()
                    continue
                # --- JPG ---
                extrafanart_file = extrafanart_dir + 'fanart{0}.jpg'.format(i)
                log_debug('_command_render_collections() test   {0}'.format(extrafanart_file.getPath()))
                if extrafanart_file.exists():
                    log_debug('_command_render_collections() Adding extrafanart #{0}'.format(i))
                    extrafanart_dic['extrafanart{0}'.format(i)] = extrafanart_file.getOriginalPath()
                    continue
                # >> No extrafanart found, exit loop.
                break
            if extrafanart_dic:
                log_debug('_command_render_collections() Extrafanart setArt() "{0}"'.format(unicode(extrafanart_dic)))
                listitem.setArt(extrafanart_dic)

            # --- Create context menu ---
            commands = []
            commands.append(('View ROM Collection data', self._misc_url_RunPlugin('VIEW', VCATEGORY_COLLECTIONS_ID, collection_id)))
            commands.append(('Export Collection',        self._misc_url_RunPlugin('EXPORT_COLLECTION', VCATEGORY_COLLECTIONS_ID, collection_id)))
            commands.append(('Edit Collection',          self._misc_url_RunPlugin('EDIT_COLLECTION', VCATEGORY_COLLECTIONS_ID, collection_id)))
            commands.append(('Delete Collection',        self._misc_url_RunPlugin('DELETE_COLLECTION', VCATEGORY_COLLECTIONS_ID, collection_id), ))
            commands.append(('Create New Collection',    self._misc_url_RunPlugin('ADD_COLLECTION')))
            commands.append(('Import Collection',        self._misc_url_RunPlugin('IMPORT_COLLECTION')))
            commands.append(('Kodi File Manager', 'ActivateWindow(filemanager)'))
            commands.append(('Add-on settings', 'Addon.OpenSettings({0})'.format(__addon_id__)))
            listitem.addContextMenuItems(commands, replaceItems = True)

            # >> Use ROMs renderer to display collection ROMs
            url_str = self._misc_url('SHOW_COLLECTION_ROMS', VCATEGORY_COLLECTIONS_ID, collection_id)
            xbmcplugin.addDirectoryItem(handle = self.addon_handle, url = url_str, listitem = listitem, isFolder = True)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    def _command_render_collection_ROMs(self, categoryID, launcherID):
        self._misc_set_default_sorting_method()
        self._misc_set_AEL_Content(AEL_CONTENT_VALUE_ROMS)

        # --- Load Collection index and ROMs ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
        collection = collections[launcherID]
        roms_json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
        collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
        if not collection_rom_list:
            kodi_notify('Collection is empty. Add ROMs to this collection first.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- Display Collection ---
        for rom in collection_rom_list:
            self._gui_render_rom_row(categoryID, launcherID, rom)
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # Adds a new collection
    #
    def _command_add_collection(self):
        # --- Load collection index ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)

        # --- Get new collection name ---
        dialog = xbmcgui.Dialog()
        keyboard = xbmc.Keyboard('', 'New Collection name')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return

        # --- Add new collection to database ---
        collection           = fs_new_collection()
        collection_name      = keyboard.getText()
        collection_id_md5    = hashlib.md5(collection_name.encode('utf-8'))
        collection_UUID      = collection_id_md5.hexdigest()
        collection_base_name = fs_get_collection_ROMs_basename(collection_name, collection_UUID)
        collection['id']              = collection_UUID
        collection['m_name']          = collection_name
        collection['roms_base_noext'] = collection_base_name
        collections[collection_UUID]  = collection
        log_debug('_command_add_collection() id              "{0}"'.format(collection['id']))
        log_debug('_command_add_collection() m_name          "{0}"'.format(collection['m_name']))
        log_debug('_command_add_collection() roms_base_noext "{0}"'.format(collection['roms_base_noext']))

        # --- Save collections XML database ---
        fs_write_Collection_index_XML(COLLECTIONS_FILE_PATH, collections)
        kodi_refresh_container()
        kodi_notify('Created ROM Collection "{0}"'.format(collection_name))

    #
    # Edits collection artwork
    #
    def _command_edit_collection(self, categoryID, launcherID):
        # --- Load collection index ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
        collection = collections[launcherID]

        # --- Shows a select box with the options to edit ---
        dialog = xbmcgui.Dialog()
        type = dialog.select('Select action for ROM Collection {0}'.format(collection['m_name']),
                            ['Edit Metadata ...', 'Edit Assets/Artwork ...',
                             'Choose default Assets/Artwork ...'])
        # >> User cancelled select dialog
        if type < 0: return

        # --- Edit category metadata ---
        if type == 0:
            NFO_FileName = fs_get_collection_NFO_name(self.settings, collection)            
            NFO_str = 'NFO found' if NFO_FileName.exists() else 'NFO not found'
            plot_str = text_limit_string(collection['m_plot'], DESCRIPTION_MAXSIZE)
            dialog = xbmcgui.Dialog()
            type2 = dialog.select('Edit Category Metadata',
                                  ["Edit Title: '{0}'".format(collection['m_name']),
                                   "Edit Genre: '{0}'".format(collection['m_genre']),
                                   "Edit Rating: '{0}'".format(collection['m_rating']),
                                   "Edit Plot: '{0}'".format(plot_str),
                                   'Import NFO file (default, {0})'.format(NFO_str),
                                   'Import NFO file (browse NFO file) ...',
                                   'Save NFO file (default location)'])
            if type2 < 0: return

            # --- Edition of the collection name ---
            if type2 == 0:
                keyboard = xbmc.Keyboard(collection['m_name'], 'Edit Title')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                title = keyboard.getText().decode('utf-8')
                if title == '': title = collection['m_name']
                collection['m_name'] = title.rstrip()
                kodi_notify('Changed Collection Title')

            # --- Edition of the collection genre ---
            elif type2 == 1:
                keyboard = xbmc.Keyboard(collection['m_genre'], 'Edit Genre')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                collection['m_genre'] = keyboard.getText().decode('utf-8')
                kodi_notify('Changed Collection Genre')

            # --- Edition of the collection rating ---
            elif type2 == 2:
                rating = dialog.select('Edit Collection Rating',
                                      ['Not set',  'Rating 0', 'Rating 1', 'Rating 2', 'Rating 3', 'Rating 4',
                                       'Rating 5', 'Rating 6', 'Rating 7', 'Rating 8', 'Rating 9', 'Rating 10'])
                # >> Rating not set, empty string
                if rating == 0:
                    collection['m_rating'] = ''
                elif rating >= 1 and rating <= 11:
                    collection['m_rating'] = '{0}'.format(rating - 1)
                elif rating < 0:
                    kodi_dialog_OK("Collection rating '{0}' not changed".format(collection['m_rating']))
                    return

            # --- Edition of the plot (description) ---
            elif type2 == 3:
                keyboard = xbmc.Keyboard(collection['m_plot'], 'Edit Plot')
                keyboard.doModal()
                if not keyboard.isConfirmed(): return
                collection['m_plot'] = keyboard.getText().decode('utf-8')
                kodi_notify('Changed Collection Plot')

            # --- Import collection metadata from NFO file (automatic) ---
            elif type2 == 4:
                # >> Returns True if changes were made
                NFO_FileName = fs_get_collection_NFO_name(self.settings, collection)
                if not fs_import_collection_NFO(NFO_FileName, collections, launcherID): return
                kodi_notify('Imported Collection NFO file {0}'.format(NFO_FileName.getPath()))

            # --- Browse for collection NFO file ---
            elif type2 == 5:
                NFO_file = xbmcgui.Dialog().browse(1, 'Select NFO description file', 'files', '.nfo', False, False).decode('utf-8')
                log_debug('_command_edit_category() Dialog().browse returned "{0}"'.format(NFO_file))
                if not NFO_file: return
                NFO_FileName = FileName(NFO_file)
                if not NFO_FileName.exists(): return
                # >> Returns True if changes were made
                if not fs_import_collection_NFO(NFO_FileName, collections, launcherID): return
                kodi_notify('Imported Collection NFO file {0}'.format(NFO_FileName.getPath()))

            # --- Export collection metadata to NFO file ---
            elif type2 == 6:
                NFO_FileName = fs_get_collection_NFO_name(self.settings, collection)
                # >> Returns False if exception happened. If an Exception happened function notifies
                # >> user, so display nothing to not overwrite error notification.
                if not fs_export_collection_NFO(NFO_FileName, collection): return
                # >> No need to save categories/launchers
                kodi_notify('Exported Collection NFO file {0}'.format(NFO_FileName.getPath()))
                return

        # --- Edit artwork ---
        elif type == 1:
            # >> Create label2 and image ListItem fields
            label2_icon      = collection['s_icon']      if collection['s_icon']      else 'Not set'
            label2_fanart    = collection['s_fanart']    if collection['s_fanart']    else 'Not set'
            label2_banner    = collection['s_banner']    if collection['s_banner']    else 'Not set'
            label2_poster    = collection['s_poster']    if collection['s_poster']    else 'Not set'
            label2_clearlogo = collection['s_clearlogo'] if collection['s_clearlogo'] else 'Not set'
            label2_trailer   = collection['s_trailer']   if collection['s_trailer']   else 'Not set'
            img_icon         = collection['s_icon']      if collection['s_icon']      else 'DefaultAddonNone.png'
            img_fanart       = collection['s_fanart']    if collection['s_fanart']    else 'DefaultAddonNone.png'
            img_banner       = collection['s_banner']    if collection['s_banner']    else 'DefaultAddonNone.png'
            img_poster       = collection['s_poster']    if collection['s_poster']    else 'DefaultAddonNone.png'
            img_clearlogo    = collection['s_clearlogo'] if collection['s_clearlogo'] else 'DefaultAddonNone.png'
            img_trailer      = 'DefaultAddonVideo.png'   if collection['s_trailer']   else 'DefaultAddonNone.png'

            # >> Create ListItem objects for select dialog
            icon_listitem      = xbmcgui.ListItem(label = 'Edit Icon ...',      label2 = label2_icon)
            fanart_listitem    = xbmcgui.ListItem(label = 'Edit Fanart ...',    label2 = label2_fanart)
            banner_listitem    = xbmcgui.ListItem(label = 'Edit Banner ...',    label2 = label2_banner)
            poster_listitem    = xbmcgui.ListItem(label = 'Edit Poster ...',    label2 = label2_poster)
            clearlogo_listitem = xbmcgui.ListItem(label = 'Edit Clearlogo ...', label2 = label2_clearlogo)
            trailer_listitem   = xbmcgui.ListItem(label = 'Edit Trailer ...',   label2 = label2_trailer)
            icon_listitem.setArt({'icon' : img_icon})
            fanart_listitem.setArt({'icon' : img_fanart})
            banner_listitem.setArt({'icon' : img_banner})
            poster_listitem.setArt({'icon' : img_poster})
            clearlogo_listitem.setArt({'icon' : img_clearlogo})
            trailer_listitem.setArt({'icon' : img_trailer})

            # >> Execute select dialog
            listitems = [icon_listitem, fanart_listitem, banner_listitem, poster_listitem,
                         clearlogo_listitem, trailer_listitem]
            type2 = dialog.select('Edit Collection Assets/Artwork', list = listitems, useDetails = True)
            if type2 < 0: return
            asset_list = [ASSET_ICON, ASSET_FANART, ASSET_BANNER, ASSET_POSTER, ASSET_CLEARLOGO, ASSET_TRAILER]
            asset_kind = asset_list[type2]
            if not self._gui_edit_asset(KIND_COLLECTION, asset_kind, collection): return

        # --- Change default artwork ---
        elif type == 2:
            # >> Label1 an label2
            asset_icon_str      = assets_get_asset_name_str(collection['default_icon'])
            asset_fanart_str    = assets_get_asset_name_str(collection['default_fanart'])
            asset_banner_str    = assets_get_asset_name_str(collection['default_banner'])
            asset_poster_str    = assets_get_asset_name_str(collection['default_poster'])
            asset_clearlogo_str = assets_get_asset_name_str(collection['default_clearlogo'])
            label2_icon         = collection[collection['default_icon']]      if collection[collection['default_icon']]      else 'Not set'
            label2_fanart       = collection[collection['default_fanart']]    if collection[collection['default_fanart']]    else 'Not set'
            label2_banner       = collection[collection['default_banner']]    if collection[collection['default_banner']]    else 'Not set'
            label2_poster       = collection[collection['default_poster']]    if collection[collection['default_poster']]    else 'Not set'
            label2_clearlogo    = collection[collection['default_clearlogo']] if collection[collection['default_clearlogo']] else 'Not set'
            icon_listitem       = xbmcgui.ListItem(label = 'Choose asset for Icon (currently {0})'.format(asset_icon_str),
                                                   label2 = label2_icon)
            fanart_listitem     = xbmcgui.ListItem(label = 'Choose asset for Fanart (currently {0})'.format(asset_fanart_str),
                                                   label2 = label2_fanart)
            banner_listitem     = xbmcgui.ListItem(label = 'Choose asset for Banner (currently {0})'.format(asset_banner_str),
                                                   label2 = label2_banner)
            poster_listitem     = xbmcgui.ListItem(label = 'Choose asset for Poster (currently {0})'.format(asset_poster_str),
                                                   label2 = label2_poster)
            clearlogo_listitem  = xbmcgui.ListItem(label = 'Choose asset for Clearlogo (currently {0})'.format(asset_clearlogo_str),
                                                   label2 = label2_clearlogo)

            # >> Asset image
            img_icon            = collection[collection['default_icon']]      if collection[collection['default_icon']]      else 'DefaultAddonNone.png'
            img_fanart          = collection[collection['default_fanart']]    if collection[collection['default_fanart']]    else 'DefaultAddonNone.png'
            img_banner          = collection[collection['default_banner']]    if collection[collection['default_banner']]    else 'DefaultAddonNone.png'
            img_poster          = collection[collection['default_poster']]    if collection[collection['default_poster']]    else 'DefaultAddonNone.png'
            img_clearlogo       = collection[collection['default_clearlogo']] if collection[collection['default_clearlogo']] else 'DefaultAddonNone.png'
            icon_listitem.setArt({'icon' : img_icon})
            fanart_listitem.setArt({'icon' : img_fanart})
            banner_listitem.setArt({'icon' : img_banner})
            poster_listitem.setArt({'icon' : img_poster})
            clearlogo_listitem.setArt({'icon' : img_clearlogo})

            # >> Execute select dialog
            listitems = [icon_listitem, fanart_listitem, banner_listitem, poster_listitem, clearlogo_listitem]
            type2 = dialog.select('Edit Collection default Assets/Artwork', list = listitems, useDetails = True)
            if type2 < 0: return

            Category_asset_ListItem_list = [
                xbmcgui.ListItem(label = 'Icon',      label2 = collection['s_icon'] if collection['s_icon'] else 'Not set'),
                xbmcgui.ListItem(label = 'Fanart',    label2 = collection['s_fanart'] if collection['s_fanart'] else 'Not set'),
                xbmcgui.ListItem(label = 'Banner',    label2 = collection['s_banner'] if collection['s_banner'] else 'Not set'),
                xbmcgui.ListItem(label = 'Poster',    label2 = collection['s_poster'] if collection['s_poster'] else 'Not set'),
                xbmcgui.ListItem(label = 'Clearlogo', label2 = collection['s_clearlogo'] if collection['s_clearlogo'] else 'Not set'),
            ]
            Category_asset_ListItem_list[0].setArt({'icon' : collection['s_icon'] if collection['s_icon'] else 'DefaultAddonNone.png'})
            Category_asset_ListItem_list[1].setArt({'icon' : collection['s_fanart'] if collection['s_fanart'] else 'DefaultAddonNone.png'})
            Category_asset_ListItem_list[2].setArt({'icon' : collection['s_banner'] if collection['s_banner'] else 'DefaultAddonNone.png'})
            Category_asset_ListItem_list[3].setArt({'icon' : collection['s_poster'] if collection['s_poster'] else 'DefaultAddonNone.png'})
            Category_asset_ListItem_list[4].setArt({'icon' : collection['s_clearlogo'] if collection['s_clearlogo'] else 'DefaultAddonNone.png'})

            if type2 == 0:
                type_s = dialog.select('Choose default Asset for Icon', list = Category_asset_ListItem_list, useDetails = True)
                if type_s < 0: return
                assets_choose_category_artwork(collection, 'default_icon', type_s)
            elif type2 == 1:
                type_s = dialog.select('Choose default Asset for Fanart', list = Category_asset_ListItem_list, useDetails = True)
                if type_s < 0: return
                assets_choose_category_artwork(collection, 'default_fanart', type_s)
            elif type2 == 2:
                type_s = dialog.select('Choose default Asset for Banner', list = Category_asset_ListItem_list, useDetails = True)
                if type_s < 0: return
                assets_choose_category_artwork(collection, 'default_banner', type_s)
            elif type2 == 3:
                type_s = dialog.select('Choose default Asset for Poster', list = Category_asset_ListItem_list, useDetails = True)
                if type_s < 0: return
                assets_choose_category_artwork(collection, 'default_poster', type_s)
            elif type2 == 4:
                type_s = dialog.select('Choose default Asset for Clearlogo', list = Category_asset_ListItem_list, useDetails = True)
                if type_s < 0: return
                assets_choose_category_artwork(collection, 'default_clearlogo', type_s)

        # --- Save collection index and refresh view ---
        fs_write_Collection_index_XML(COLLECTIONS_FILE_PATH, collections)
        kodi_refresh_container()

    #
    # Deletes a collection and associated ROMs.
    #
    def _command_delete_collection(self, categoryID, launcherID):
        # --- Load collection index and ROMs ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
        collection = collections[launcherID]
        roms_json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
        collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)

        # --- Confirm deletion ---
        num_roms = len(collection_rom_list)
        collection_name = collection['m_name']
        ret = kodi_dialog_yesno('Collection "{0}" has {1} ROMs. '.format(collection_name, num_roms) +
                                'Are you sure you want to delete it?')
        if not ret: return

        # --- Remove JSON file and delete collection object ---
        collection_file_path = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
        log_debug('Removing Collection JSON "{0}"'.format(collection_file_path.getOriginalPath()))
        try:
            if collection_file_path.exists(): collection_file_path.unlink()
        except OSError:
            log_error('_gui_remove_launcher() (OSError) exception deleting "{0}"'.format(collection_file_path.getOriginalPath()))
            kodi_notify_warn('OSError exception deleting collection JSON')
        collections.pop(launcherID)
        fs_write_Collection_index_XML(COLLECTIONS_FILE_PATH, collections)
        kodi_refresh_container()
        kodi_notify('Deleted ROM Collection "{0}"'.format(collection_name))

    #
    # Imports a ROM Collection.
    #
    def _command_import_collection(self):
        # --- Choose collection to import ---
        dialog = xbmcgui.Dialog()
        collection_file_str = dialog.browse(1, 'Select the ROM Collection file', 'files', '.json', False, False).decode('utf-8')
        if not collection_file_str: return

        # --- Load ROM Collection file ---
        collection_FN = FileName(collection_file_str)
        control_dic, collection_dic, collection_rom_list = fs_import_ROM_collection(collection_FN)
        if not collection_dic:
            kodi_dialog_OK('Error reading Collection JSON file. JSON file corrupted or wrong.')
            return
        if not collection_rom_list:
            kodi_dialog_OK('Collection is empty.')
            return
        if control_dic['control'] != 'Advanced Emulator Launcher Collection ROMs':
            kodi_dialog_OK('JSON file is not an AEL ROM Collection file.')
            return

        # --- Check if asset JSON exist. If so, ask the user about importing it. ---
        collection_asset_FN = FileName(collection_FN.getPath_noext() + '_assets.json')
        log_debug('_command_import_collection() collection_asset_FN "{0}"'.format(collection_asset_FN.getPath()))
        import_collection_assets = False
        if collection_asset_FN.exists():
            log_debug('_command_import_collection() Collection asset JSON found')
            ret = kodi_dialog_yesno('Collection asset JSON found. Import collection assets as well?')
            if ret: 
                import_collection_assets = True
                asset_control_dic, assets_dic = fs_import_ROM_collection_assets(collection_asset_FN)
        else:
            log_debug('_command_import_collection() Collection asset JSON NOT found')

        # --- Load collection indices ---
        collections, update_timestamp = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)

        # --- If collectionID already on index warn the user ---
        if collection_dic['id'] in collections:
            log_info('_command_import_collection() Collection {0} already in AEL'.format(collection_dic['m_name']))
            ret = kodi_dialog_yesno('A Collection with same ID exists. Overwrite?')
            if not ret: return

        # --- Regenrate roms_base_noext field ---
        collection_base_name = fs_get_collection_ROMs_basename(collection_dic['m_name'], collection_dic['id'])
        collection_dic['roms_base_noext'] = collection_base_name
        log_debug('_command_import_collection() roms_base_noext "{0}"'.format(collection_dic['roms_base_noext']))

        # --- Also import assets if loaded ---
        if import_collection_assets:
            collections_asset_dir_FN = FileName(self.settings['collections_asset_dir'])

            # --- Import Collection assets ---
            log_info('_command_import_collection() Importing ROM Collection assets ...')
            for asset_kind in CATEGORY_ASSET_LIST:
                # >> Get asset filename with no extension
                AInfo = assets_get_info_scheme(asset_kind)
                asset_noext_FN = assets_get_path_noext_SUFIX(AInfo, collections_asset_dir_FN,
                                                             collection_dic['m_name'], collection_dic['id'])
                log_debug('{0:<9s} base_noext "{1}"'.format(AInfo.name, asset_noext_FN.getBase()))
                if asset_noext_FN.getBase() not in assets_dic:
                    # >> Asset not found. Make sure asset is unset in imported Collection.
                    collection_dic[AInfo.key] = ''
                    log_debug('{0:<9s} NOT found in imported asset dictionary'.format(AInfo.name))
                    continue
                log_debug('{0:<9s} found in imported asset dictionary'.format(AInfo.name))
                asset_dic = assets_dic[asset_noext_FN.getBase()]
                new_asset_FN = collections_asset_dir_FN.pjoin(asset_dic['basename'])

                # >> Create asset file
                asset_base64_data = asset_dic['data']
                asset_filesize    = asset_dic['filesize']
                fileData = base64.b64decode(asset_base64_data)
                log_debug('{0:<9s} Creating OP "{1}"'.format(AInfo.name, new_asset_FN.getOriginalPath()))
                log_debug('{0:<9s} Creating P  "{1}"'.format(AInfo.name, new_asset_FN.getPath()))
                with open(new_asset_FN.getPath(), mode = 'wb') as file: # b is important -> binary
                    file.write(fileData)
                statinfo = new_asset_FN.stat()
                file_size = statinfo.st_size
                if asset_filesize != file_size:
                    # >> File creation/Unpacking error. Make sure asset is unset in imported Collection.
                    collection_dic[AInfo.key] = ''
                    log_error('{0:<9s} wrong file size {1} (must be {2})'.format(A.name, file_size, asset_filesize))
                    return
                else:
                    log_debug('{0:<9s} file size OK ({1} bytes)'.format(AInfo.name, asset_filesize))
                # >> Update imported asset filename in database.
                collection_dic[AInfo.key] = new_asset_FN.getOriginalPath()

            # --- Import ROM assets ---
            log_info('_command_import_collection() Importing ROM assets ...')
            for rom_item in collection_rom_list:
                log_debug('_command_import_collection() ROM "{0}"'.format(rom_item['m_name']))
                for asset_kind in ROM_ASSET_LIST:
                    # >> Get assets filename with no extension
                    AInfo = assets_get_info_scheme(asset_kind)
                    ROM_FN = FileName(rom_item['filename'])                    
                    ROM_asset_noext_FN = assets_get_path_noext_SUFIX(AInfo, collections_asset_dir_FN, 
                                                                     ROM_FN.getBase_noext(), rom_item['id'])
                    ROM_asset_FN = ROM_asset_noext_FN.append(ROM_asset_noext_FN.getExt())
                    log_debug('{0:<9s} base_noext "{1}"'.format(AInfo.name, ROM_asset_FN.getBase_noext()))
                    if ROM_asset_FN.getBase_noext() not in assets_dic:
                        # >> Asset not found. Make sure asset is unset in imported Collection.
                        rom_item[AInfo.key] = ''
                        log_debug('{0:<9s} NOT found in imported asset dictionary'.format(AInfo.name))
                        continue
                    log_debug('{0:<9s} found in imported asset dictionary'.format(AInfo.name))
                    asset_dic = assets_dic[ROM_asset_FN.getBase_noext()]                        
                    new_asset_FN = collections_asset_dir_FN.pjoin(asset_dic['basename'])

                    # >> Create asset file
                    asset_base64_data = asset_dic['data']
                    asset_filesize    = asset_dic['filesize']
                    fileData = base64.b64decode(asset_base64_data)
                    log_debug('{0:<9s} Creating OP "{1}"'.format(AInfo.name, new_asset_FN.getOriginalPath()))
                    log_debug('{0:<9s} Creating P  "{1}"'.format(AInfo.name, new_asset_FN.getPath()))
                    with open(new_asset_FN.getPath(), mode = 'wb') as file: # b is important -> binary
                        file.write(fileData)
                    statinfo = new_asset_FN.stat()
                    file_size = statinfo.st_size
                    if asset_filesize != file_size:
                        # >> File creation/Unpacking error. Make sure asset is unset in imported Collection.
                        rom_item[AInfo.key] = ''
                        log_error('{0:<9s} wrong file size {1} (must be {2})'.format(AInfo.name, file_size, asset_filesize))
                        return
                    else:
                        log_debug('{0:<9s} file size OK ({1} bytes)'.format(AInfo.name, asset_filesize))
                    # >> Update asset info in database
                    rom_item[AInfo.key] = new_asset_FN.getOriginalPath()
            log_debug('_command_import_collection() Finished importing assets')

        # --- Add imported collection to database ---
        collections[collection_dic['id']] = collection_dic
        log_info('_command_import_collection() Imported Collection "{0}" (id {1})'.format(collection_dic['m_name'], collection_dic['id']))

        # --- Write ROM Collection databases ---
        fs_write_Collection_index_XML(COLLECTIONS_FILE_PATH, collections)
        fs_write_Collection_ROMs_JSON(COLLECTIONS_DIR.pjoin(collection_base_name + '.json'), collection_rom_list)
        if import_collection_assets:
            kodi_dialog_OK("Imported ROM Collection '{0}' metadata and assets.".format(collection_dic['m_name']))
        else:
            kodi_dialog_OK("Imported ROM Collection '{0}' metadata.".format(collection_dic['m_name']))

    #
    # Exports a ROM Collection
    #
    def _command_export_collection(self, categoryID, launcherID):
        # --- Export database only or database + assets ---
        dialog = xbmcgui.Dialog()
        export_type = dialog.select('Export ROM Collection',
                                   ['Export only metadata', 'Export metadata and assets'])
        if export_type < 0: return

        # --- Choose output directory ---
        dialog = xbmcgui.Dialog()
        output_dir = dialog.browse(3, 'Select Collection output directory', 'files').decode('utf-8')
        if not output_dir: return
        output_dir_FileName = FileName(output_dir)

        # --- Load collection ROMs ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
        collection = collections[launcherID]
        roms_json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
        collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
        if not collection_rom_list:
            kodi_notify('Collection is empty. Add ROMs to this collection first.')
            xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)
            return

        # --- If exporting assets, copy assets from parent into Collection assets directory ---
        # 1) Traverse all collection ROMs.
        # 2) For each ROM, traverse all assets. If assets is in parent ROM directory then copy
        #    to ROM Collections directory.
        # 3) For every asset copied update ROM Collection database.
        if export_type == 1:
            ret = kodi_dialog_yesno('Exporting ROM Collection assets. '
                                    'Parent ROM assets will be copied into the ROM Collection '
                                    'asset directory before exporting.')
            if not ret:
                kodi_dialog_OK('ROM Collection export cancelled.')
                return

            # --- Copy Collection assets to Collection asset directory ---
            log_info('_command_export_collection() Copying ROM Collection assets ...')
            collections_asset_dir_FN = FileName(self.settings['collections_asset_dir'])
            collection_assets_were_copied = False
            for asset_kind in CATEGORY_ASSET_LIST:
                AInfo = assets_get_info_scheme(asset_kind)
                asset_FileName = FileName(collection[AInfo.key])
                new_asset_noext_FileName = assets_get_path_noext_SUFIX(AInfo, collections_asset_dir_FN,
                                                                       collection['m_name'], collection['id'])
                new_asset_FileName = new_asset_noext_FileName.append(asset_FileName.getExt())
                if not collection[AInfo.key]:
                    log_debug('{0:<9s} not set.'.format(AInfo.name))
                    continue
                elif asset_FileName.getPath() == new_asset_FileName.getPath():
                    log_debug('{0:<9s} in Collection asset dir'.format(AInfo.name))
                    continue
                # >> If asset cannot be found then ignore it. Do not touch JSON database.
                elif not asset_FileName.exists():
                    log_debug('{0:<9s} not found "{1}"'.format(AInfo.name, asset_FileName.getOriginalPath()))
                    log_debug('{0:<9s} ignored'.format(AInfo.name))
                    continue
                else:
                    log_debug('{0:<9s} in external dir'.format(AInfo.name))
                    log_debug('{0:<9s} OP COPY "{1}"'.format(AInfo.name, asset_FileName.getOriginalPath()))
                    log_debug('{0:<9s} OP   TO "{1}"'.format(AInfo.name, new_asset_FileName.getOriginalPath()))
                    log_debug('{0:<9s} P  COPY "{1}"'.format(AInfo.name, asset_FileName.getPath()))
                    log_debug('{0:<9s} P    TO "{1}"'.format(AInfo.name, new_asset_FileName.getPath()))
                    try:
                        source_path = asset_FileName.getPath().decode(get_fs_encoding(), 'ignore')
                        dest_path   = new_asset_FileName.getPath().decode(get_fs_encoding(), 'ignore')
                        log_debug('source_path "{0}"'.format(source_path))
                        log_debug('dest_path   "{0}"'.format(dest_path))
                        shutil.copy(source_path, dest_path)
                    except OSError:
                        log_error('_command_export_collection() OSError exception copying image')
                        kodi_notify_warn('OSError exception copying image')
                        return
                    except IOError:
                        log_error('_command_export_collection() IOError exception copying image')
                        kodi_notify_warn('IOError exception copying image')
                        return

                    # >> Asset were copied. Update ROM Collection database.
                    collection[AInfo.key] = new_asset_FileName.getOriginalPath()
                    collection_assets_were_copied = True

            # --- Copy Collection ROM assets ---
            log_info('_command_export_collection() Copying parent ROM assets into ROM Collections asset directory ...')
            ROM_assets_were_copied = False
            for rom_item in collection_rom_list:
                log_debug('_command_export_collection() ROM "{0}"'.format(rom_item['m_name']))
                for asset_kind in ROM_ASSET_LIST:
                    AInfo = assets_get_info_scheme(asset_kind)
                    asset_FileName = FileName(rom_item[AInfo.key])
                    ROM_FileName = FileName(rom_item['filename'])
                    new_asset_noext_FileName = assets_get_path_noext_SUFIX(AInfo, collections_asset_dir_FN, 
                                                                           ROM_FileName.getBase_noext(), rom_item['id'])
                    new_asset_FileName = new_asset_noext_FileName.append(asset_FileName.getExt())
                    if not rom_item[AInfo.key]:
                        log_debug('{0:<9s} not set.'.format(AInfo.name))
                        continue
                    elif asset_FileName.getPath() == new_asset_FileName.getPath():
                        log_debug('{0:<9s} in Collection asset dir'.format(AInfo.name))
                        continue
                    # >> If asset cannot be found then ignore it. Do not touch JSON database.
                    elif not asset_FileName.exists():
                        log_debug('{0:<9s} not found "{1}"'.format(AInfo.name, asset_FileName.getOriginalPath()))
                        log_debug('{0:<9s} ignored'.format(AInfo.name))
                        continue
                    else:
                        # >> Copy asset from parent into ROM Collection asset dir
                        log_debug('{0:<9s} in external dir'.format(AInfo.name))
                        log_debug('{0:<9s} OP COPY "{1}"'.format(AInfo.name, asset_FileName.getOriginalPath()))
                        log_debug('{0:<9s} OP   TO "{1}"'.format(AInfo.name, new_asset_FileName.getOriginalPath()))
                        log_debug('{0:<9s} P  COPY "{1}"'.format(AInfo.name, asset_FileName.getPath()))
                        log_debug('{0:<9s} P    TO "{1}"'.format(AInfo.name, new_asset_FileName.getPath()))
                        try:
                            source_path = asset_FileName.getPath().decode(get_fs_encoding(), 'ignore')
                            dest_path   = new_asset_FileName.getPath().decode(get_fs_encoding(), 'ignore')
                            shutil.copy(source_path, dest_path)
                        except OSError:
                            log_error('_command_export_collection() OSError exception copying image')
                            kodi_notify_warn('OSError exception copying image')
                            return
                        except IOError:
                            log_error('_command_export_collection() IOError exception copying image')
                            kodi_notify_warn('IOError exception copying image')
                            return

                        # >> Asset were copied. Update ROM Collection database.
                        rom_item[AInfo.key] = new_asset_FileName.getOriginalPath()
                        ROM_assets_were_copied = True

            # >> Write ROM Collection DB.
            if collection_assets_were_copied:
                fs_write_Collection_index_XML(COLLECTIONS_FILE_PATH, collections)
                log_info('_command_export_collection() Collection assets were copied. Saving Collection index ...')
            if ROM_assets_were_copied:
                json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
                fs_write_Collection_ROMs_JSON(json_file, collection_rom_list)
                log_info('_command_export_collection() Collection ROM assets were copied. Saving Collection database ...')

        # --- Export collection metadata (Always) ---
        output_FileName = output_dir_FileName.pjoin(collection['m_name'] + '.json')
        fs_export_ROM_collection(output_FileName, collection, collection_rom_list)

        # --- Export collection assets (Optional) ---
        if export_type == 1:
            output_FileName = output_dir_FileName.pjoin(collection['m_name'] + '_assets.json')
            fs_export_ROM_collection_assets(output_FileName, collection, collection_rom_list, collections_asset_dir_FN)

        # >> User info
        if   export_type == 0:
            kodi_notify('Exported ROM Collection {0} metadata.'.format(collection['m_name']))
        elif export_type == 1:
            kodi_notify('Exported ROM Collection {0} metadata and assets.'.format(collection['m_name']))

    def _command_add_ROM_to_collection(self, categoryID, launcherID, romID):
        # >> ROM in Virtual Launcher
        if categoryID == VCATEGORY_TITLE_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_TITLE_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_YEARS_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_YEARS_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_GENRE_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_GENRE_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        elif categoryID == VCATEGORY_DEVELOPER_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_DEVELOPER_DIR, launcherID)
            launcher = self.launchers[roms[romID]['launcherID']]
        # >> ROMs in standard launcher
        else:
            launcher = self.launchers[launcherID]
            roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)

        # >> Sanity check
        if not roms:
            kodi_dialog_OK('Empty roms launcher in _command_add_to_favourites(). This is a bug, please report it.')
            return

        # --- Load Collection index ---
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)

        # --- If no collections so long and thanks for all the fish ---
        if not collections:
            kodi_dialog_OK('You have no Collections! Create a collection first before adding ROMs.')
            return

        # --- Ask user which Collection wants to add the ROM to ---
        dialog = xbmcgui.Dialog()
        collections_id = []
        collections_name = []
        for key in sorted(collections, key = lambda x : collections[x]['m_name']):
            collections_id.append(collections[key]['id'])
            collections_name.append(collections[key]['m_name'])
        selected_idx = dialog.select('Select the collection', collections_name)
        if selected_idx < 0: return
        collectionID = collections_id[selected_idx]

        # --- Load Collection ROMs ---
        collection = collections[collectionID]
        roms_json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
        collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
        log_info('Adding ROM to Collection')
        log_info('Collection {0}'.format(collection['m_name']))
        log_info('romID      {0}'.format(romID))
        log_info('ROM m_name {0}'.format(roms[romID]['m_name']))

        # >> Check if ROM already in this collection an warn user if so
        rom_already_in_collection = False
        for rom in collection_rom_list:
            if romID == rom['id']:
                rom_already_in_collection = True
                break
        if rom_already_in_collection:
            log_info('ROM already in collection')
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher',
                               'ROM {0} is already on Collection {1}. Overwrite it?'.format(roms[romID]['m_name'], collection['m_name']))
            if not ret:
                log_verb('User does not want to overwrite. Exiting.')
                return
        # >> Confirm if rom should be added
        else:
            dialog = xbmcgui.Dialog()
            ret = dialog.yesno('Advanced Emulator Launcher',
                               "ROM '{0}'. Add this ROM to Collection '{1}'?".format(roms[romID]['m_name'], collection['m_name']))
            if not ret:
                log_verb('User does not confirm addition. Exiting.')
                return

        # --- Add ROM to favourites ROMs and save to disk ---
        # >> Add ROM to the last position in the collection
        collection_rom = fs_get_Favourite_from_ROM(roms[romID], launcher)
        collection_rom_list.append(collection_rom)
        json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
        fs_write_Collection_ROMs_JSON(json_file, collection_rom_list)
        kodi_refresh_container()
        kodi_notify('Added ROM to Collection "{0}"'.format(collection['m_name']))

    #
    # Search ROMs in launcher
    #
    def _command_search_launcher(self, categoryID, launcherID):
        log_debug('_command_search_launcher() categoryID {0}'.format(categoryID))
        log_debug('_command_search_launcher() launcherID {0}'.format(launcherID))

        # --- Load ROMs ---
        if categoryID == VCATEGORY_FAVOURITES_ID:
            roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        elif categoryID == VCATEGORY_TITLE_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_TITLE_DIR, launcherID)
        elif categoryID == VCATEGORY_YEARS_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_YEARS_DIR, launcherID)
        elif categoryID == VCATEGORY_GENRE_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_GENRE_DIR, launcherID)
        elif categoryID == VCATEGORY_DEVELOPER_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_DEVELOPER_DIR, launcherID)
        elif categoryID == VCATEGORY_CATEGORY_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_CATEGORY_DIR, launcherID)
        else:
            rom_file_path = ROMS_DIR.pjoin(self.launchers[launcherID]['roms_base_noext'] + '.json')
            log_debug('_command_search_launcher() rom_file_path "{0}"'.format(rom_file_path.getOriginalPath()))
            if not rom_file_path.exists():
                kodi_notify('Launcher JSON not found. Add ROMs to Launcher')
                return
            roms = fs_load_ROMs_JSON(ROMS_DIR, self.launchers[launcherID])

        # --- Empty ROM dictionary / Loading error ---
        if not roms:
            kodi_notify('Launcher JSON is empty. Add ROMs to Launcher')
            return

        # --- Ask user what field category to search ---
        dialog = xbmcgui.Dialog()
        type = dialog.select('Search ROMs ...', ['By ROM Title', 'By Release Year', 'By Genre', 'By Studio', 'By Rating'])
        if type < 0: return

        # --- Search by ROM Title ---
        type_nb = 0
        if type == type_nb:
            keyboard = xbmc.Keyboard('', 'Enter the ROM Title search string ...')
            keyboard.doModal()
            if not keyboard.isConfirmed(): return
            search_string = keyboard.getText()
            url = self._misc_url_search('EXECUTE_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_TITLE', search_string)

        # --- Search by Release Date ---
        type_nb = type_nb + 1
        if type == type_nb:
            searched_list = self._search_launcher_field('m_year', roms)
            dialog = xbmcgui.Dialog()
            selected_value = dialog.select('Select a release year ...', searched_list)
            if selected_value < 0: return
            search_string = searched_list[selected_value]
            url = self._misc_url_search('EXECUTE_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_YEAR', search_string)

        # --- Search by System Platform ---
        # >> Note that search by platform does not make sense when searching a launcher because all items have
        # >> the same platform! It only makes sense for global searches... which AEL does not.
        # >> I keep this AL old code for reference, though.
        # type_nb = type_nb + 1
        # if type == type_nb:
        #     search = []
        #     search = _search_category(self, "platform")
        #     dialog = xbmcgui.Dialog()
        #     selected = dialog.select('Select a Platform...', search)
        #     if not selected == -1:
        #         xbmc.executebuiltin("ReplaceWindow(Programs,%s?%s/%s)" % (self.base_url, search[selected], SEARCH_PLATFORM_COMMAND))

        # --- Search by Genre ---
        type_nb = type_nb + 1
        if type == type_nb:
            searched_list = self._search_launcher_field('m_genre', roms)
            dialog = xbmcgui.Dialog()
            selected_value = dialog.select('Select a Genre ...', searched_list)
            if selected_value < 0: return
            search_string = searched_list[selected_value]
            url = self._misc_url_search('EXECUTE_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_GENRE', search_string)

        # --- Search by Studio ---
        type_nb = type_nb + 1
        if type == type_nb:
            searched_list = self._search_launcher_field('m_studio', roms)
            dialog = xbmcgui.Dialog()
            selected_value = dialog.select('Select a Studio ...', searched_list)
            if selected_value < 0: return
            search_string = searched_list[selected_value]
            url = self._misc_url_search('EXECUTE_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_STUDIO', search_string)

        # --- Search by Rating ---
        type_nb = type_nb + 1
        if type == type_nb:
            searched_list = self._search_launcher_field('m_rating', roms)
            dialog = xbmcgui.Dialog()
            selected_value = dialog.select('Select a Rating ...', searched_list)
            if selected_value < 0: return
            search_string = searched_list[selected_value]
            url = self._misc_url_search('EXECUTE_SEARCH_LAUNCHER', categoryID, launcherID, 'SEARCH_RATING', search_string)

        # --- Replace current window by search window ---
        # When user press Back in search window it returns to the original window (either showing
        # launcher in a cateogory or displaying ROMs in a launcher/virtual launcher).
        #
        # NOTE ActivateWindow() / RunPlugin() / RunAddon() seem not to work here
        log_debug('_command_search_launcher() Container.Update URL {0}'.format(url))
        xbmc.executebuiltin('Container.Update({0})'.format(url))

    #
    # Auxiliar function used in Launcher searches.
    #
    def _search_launcher_field(self, search_dic_field, roms):
        # Maybe this can be optimized a bit to make the search faster...
        search = []
        for keyr in sorted(roms.iterkeys()):
            if roms[keyr][search_dic_field] == '':
                search.append('[ Not Set ]')
            else:
                search.append(roms[keyr][search_dic_field])
        # Search may have a lot of repeated entries. Converting them to a set makes them unique.
        search = list(set(search))
        search.sort()

        return search

    def _command_execute_search_launcher(self, categoryID, launcherID, search_type, search_string):
        if   search_type == 'SEARCH_TITLE'  : rom_search_field = 'm_name'
        elif search_type == 'SEARCH_YEAR'   : rom_search_field = 'm_year'
        elif search_type == 'SEARCH_STUDIO' : rom_search_field = 'm_studio'
        elif search_type == 'SEARCH_GENRE'  : rom_search_field = 'm_genre'
        elif search_type == 'SEARCH_RATING' : rom_search_field = 'm_rating'
        else: return

        # --- Load Launcher ROMs ---
        if categoryID == VCATEGORY_FAVOURITES_ID:
            roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        elif categoryID == VCATEGORY_TITLE_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_TITLE_DIR, launcherID)
        elif categoryID == VCATEGORY_YEARS_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_YEARS_DIR, launcherID)
        elif categoryID == VCATEGORY_GENRE_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_GENRE_DIR, launcherID)
        elif categoryID == VCATEGORY_DEVELOPER_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_DEVELOPER_DIR, launcherID)
        elif categoryID == VCATEGORY_CATEGORY_ID:
            roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_CATEGORY_DIR, launcherID)
        else:
            rom_file_path = ROMS_DIR.pjoin(self.launchers[launcherID]['roms_base_noext'] + '.json')
            if not rom_file_path.exists():
                kodi_notify('Launcher JSON not found. Add ROMs to Launcher')
                return
            roms = fs_load_ROMs_JSON(ROMS_DIR, self.launchers[launcherID])

        # --- Empty ROM dictionary / Loading error ---
        if not roms:
            kodi_notify('Launcher JSON is empty. Add ROMs to Launcher')
            return

        # --- Go through rom list and search for user input ---
        rl = {}
        notset = ('[ Not Set ]')
        text = search_string.lower()
        empty = notset.lower()
        for keyr in roms:
            rom_field_str = roms[keyr][rom_search_field].lower()
            if rom_field_str == '' and text == empty: rl[keyr] = roms[keyr]

            if rom_search_field == 'm_name':
                if not rom_field_str.find(text) == -1:
                    rl[keyr] = roms[keyr]
            else:
                if rom_field_str == text:
                    rl[keyr] = roms[keyr]

        # --- Render ROMs ---
        self._misc_set_all_sorting_methods()
        if not rl:
            kodi_dialog_OK('Search returned no results')
        for key in sorted(rl.iterkeys()):
            self._gui_render_rom_row(categoryID, launcherID, rl[key])
        xbmcplugin.endOfDirectory(handle = self.addon_handle, succeeded = True, cacheToDisc = False)

    #
    # View all kinds of information
    #
    def _command_view_menu(self, categoryID, launcherID, romID):
        VIEW_CATEGORY          = 100
        VIEW_LAUNCHER          = 200
        VIEW_COLLECTION        = 300
        VIEW_ROM_LAUNCHER      = 400
        VIEW_ROM_VLAUNCHER     = 500
        VIEW_ROM_COLLECTION    = 500

        ACTION_VIEW_CATEGORY          = 100
        ACTION_VIEW_LAUNCHER          = 200
        ACTION_VIEW_COLLECTION        = 300
        ACTION_VIEW_ROM               = 400
        ACTION_VIEW_LAUNCHER_STATS    = 500
        ACTION_VIEW_LAUNCHER_METADATA = 600
        ACTION_VIEW_LAUNCHER_ASSETS   = 700
        ACTION_VIEW_LAUNCHER_SCANNER  = 800
        ACTION_VIEW_MANUAL            = 900
        ACTION_VIEW_MAP               = 1000
        ACTION_VIEW_EXEC_OUTPUT       = 1100

        # >> Determine if we are in a cateogory, launcher or ROM
        log_debug('_command_view_menu() categoryID = {0}'.format(categoryID))
        log_debug('_command_view_menu() launcherID = {0}'.format(launcherID))
        log_debug('_command_view_menu() romID      = {0}'.format(romID))
        if launcherID and romID:
            if categoryID == VCATEGORY_FAVOURITES_ID or \
               categoryID == VCATEGORY_RECENT_ID or \
               categoryID == VCATEGORY_MOST_PLAYED_ID or \
               categoryID == VCATEGORY_TITLE_ID    or categoryID == VCATEGORY_YEARS_ID or \
               categoryID == VCATEGORY_GENRE_ID    or categoryID == VCATEGORY_DEVELOPER_ID or \
               categoryID == VCATEGORY_NPLAYERS_ID or categoryID == VCATEGORY_ESRB_ID or \
               categoryID == VCATEGORY_RATING_ID   or categoryID == VCATEGORY_CATEGORY_ID:
                view_type = VIEW_ROM_VLAUNCHER
            elif categoryID == VCATEGORY_COLLECTIONS_ID:
                view_type = VIEW_ROM_COLLECTION
            else:
                view_type = VIEW_ROM_LAUNCHER
        elif launcherID and not romID:
            if categoryID == VCATEGORY_COLLECTIONS_ID:
                view_type = VIEW_COLLECTION
            else:
                view_type = VIEW_LAUNCHER
        else:
            view_type = VIEW_CATEGORY
        log_debug('_command_view_menu() view_type = {0}'.format(view_type))

        # --- Build menu base on view_type ---
        if LAUNCH_LOG_FILE_PATH.exists():
            stat_stdout = LAUNCH_LOG_FILE_PATH.stat()
            size_stdout = stat_stdout.st_size
            STD_status = '{0} bytes'.format(size_stdout)
        else:
            STD_status = 'not found'
        if view_type == VIEW_LAUNCHER or view_type == VIEW_ROM_LAUNCHER:
            launcher = self.launchers[launcherID]
            launcher_report_FN = REPORTS_DIR.pjoin(launcher['roms_base_noext'] + '_report.txt')
            if launcher_report_FN.exists():
                stat_stdout = launcher_report_FN.stat()
                size_stdout = stat_stdout.st_size
                Report_status = '{0} bytes'.format(size_stdout)
            else:
                Report_status = 'not found'

        if view_type == VIEW_CATEGORY:
            d_list = [
                'View Category data',
                'View last execution output ({0})'.format(STD_status),
            ]
        elif view_type == VIEW_LAUNCHER:
            d_list = [
                'View Launcher data',
                'View Launcher statistics',
                'View Launcher metadata/audit report',
                'View Launcher assets report',
                'View Launcher scanner report ({0})'.format(Report_status),
                'View last execution output ({0})'.format(STD_status),
            ]
        elif view_type == VIEW_COLLECTION:
            d_list = [
                'View Collection data',
                'View last execution output ({0})'.format(STD_status),
            ]
        elif view_type == VIEW_ROM_LAUNCHER:
            d_list = [
                'View ROM manual',
                'View ROM map',
                'View ROM data',
                'View Launcher statistics',
                'View Launcher metadata/audit report',
                'View Launcher assets report',
                'View Launcher scanner report ({0})'.format(Report_status),
                'View last execution output ({0})'.format(STD_status),
            ]
        elif view_type == VIEW_ROM_VLAUNCHER:
            # >> ROM in Favourites or Virtual Launcher (no launcher report)
            d_list = [
                'View ROM manual',
                'View ROM map',
                'View ROM data',
                'View last execution output ({0})'.format(STD_status),
            ]
        elif view_type == VIEW_ROM_COLLECTION:
            d_list = [
                'View ROM manual',
                'View ROM map',
                'View ROM data',
                'View last execution output ({0})'.format(STD_status),
            ]
        else:
            kodi_dialog_OK('Wrong view_type = {0}. This is a bug, please report it.'.format(view_type))
            return
        selected_value = xbmcgui.Dialog().select('View', d_list)
        if selected_value < 0: return

        # --- Polymorphic menu. Determine action to do. ---
        if view_type == VIEW_CATEGORY:
            if   selected_value == 0: action = ACTION_VIEW_CATEGORY
            elif selected_value == 1: action = ACTION_VIEW_EXEC_OUTPUT
            else:
                kodi_dialog_OK('view_type == VIEW_CATEGORY and selected_value = {0}. '.format(selected_value) +
                               'This is a bug, please report it.')
                return
        elif view_type == VIEW_LAUNCHER:
            if   selected_value == 0: action = ACTION_VIEW_LAUNCHER
            elif selected_value == 1: action = ACTION_VIEW_LAUNCHER_STATS
            elif selected_value == 2: action = ACTION_VIEW_LAUNCHER_METADATA
            elif selected_value == 3: action = ACTION_VIEW_LAUNCHER_ASSETS
            elif selected_value == 4: action = ACTION_VIEW_LAUNCHER_SCANNER
            elif selected_value == 5: action = ACTION_VIEW_EXEC_OUTPUT
            else:
                kodi_dialog_OK('view_type == VIEW_LAUNCHER and selected_value = {0}. '.format(selected_value) +
                               'This is a bug, please report it.')
                return
        elif view_type == VIEW_COLLECTION:
            if   selected_value == 0: action = ACTION_VIEW_COLLECTION
            elif selected_value == 1: action = ACTION_VIEW_EXEC_OUTPUT
            else:
                kodi_dialog_OK('view_type == VIEW_COLLECTION and selected_value = {0}. '.format(selected_value) +
                               'This is a bug, please report it.')
                return
        elif view_type == VIEW_ROM_LAUNCHER:
            if   selected_value == 0: action = ACTION_VIEW_MANUAL
            elif selected_value == 1: action = ACTION_VIEW_MAP
            elif selected_value == 2: action = ACTION_VIEW_ROM
            elif selected_value == 3: action = ACTION_VIEW_LAUNCHER_STATS
            elif selected_value == 4: action = ACTION_VIEW_LAUNCHER_METADATA
            elif selected_value == 5: action = ACTION_VIEW_LAUNCHER_ASSETS
            elif selected_value == 6: action = ACTION_VIEW_LAUNCHER_SCANNER
            elif selected_value == 7: action = ACTION_VIEW_EXEC_OUTPUT
            else:
                kodi_dialog_OK('view_type == VIEW_ROM_LAUNCHER and selected_value = {0}. '.format(selected_value) +
                               'This is a bug, please report it.')
                return
        elif view_type == VIEW_ROM_VLAUNCHER:
            if   selected_value == 0: action = ACTION_VIEW_MANUAL
            elif selected_value == 1: action = ACTION_VIEW_MAP
            elif selected_value == 2: action = ACTION_VIEW_ROM
            elif selected_value == 3: action = ACTION_VIEW_EXEC_OUTPUT
            else:
                kodi_dialog_OK('view_type == VIEW_ROM_VLAUNCHER and selected_value = {0}. '.format(selected_value) +
                               'This is a bug, please report it.')
                return
        elif view_type == VIEW_ROM_COLLECTION:
            if   selected_value == 0: action = ACTION_VIEW_MANUAL
            elif selected_value == 1: action = ACTION_VIEW_MAP
            elif selected_value == 2: action = ACTION_VIEW_ROM
            elif selected_value == 3: action = ACTION_VIEW_EXEC_OUTPUT
            else:
                kodi_dialog_OK('view_type == VIEW_ROM_COLLECTION and selected_value = {0}. '.format(selected_value) +
                               'This is a bug, please report it.')
                return
        else:
            kodi_dialog_OK('Wrong view_type == {0}. '.format(view_type) +
                           'This is a bug, please report it.')
            return
        log_debug('_command_view_menu() action = {0}'.format(action))

        # --- Execute action ---
        if action == ACTION_VIEW_CATEGORY or action == ACTION_VIEW_LAUNCHER or \
           action == ACTION_VIEW_COLLECTION or action == ACTION_VIEW_ROM:
            if view_type == VIEW_CATEGORY:
                window_title = 'Category data'
                category = self.categories[categoryID]
                info_text  = '[COLOR orange]Category information[/COLOR]\n'
                info_text += self._misc_print_string_Category(category)
            elif view_type == VIEW_LAUNCHER:
                window_title = 'Launcher data'
                if categoryID == VCATEGORY_ADDONROOT_ID: category = None
                else:                                    category = self.categories[categoryID]
                launcher = self.launchers[launcherID]
                info_text  = '[COLOR orange]Launcher information[/COLOR]\n'
                info_text += self._misc_print_string_Launcher(launcher)
                if category:
                    info_text += '\n[COLOR orange]Category information[/COLOR]\n'
                    info_text += self._misc_print_string_Category(category)
            elif view_type == VIEW_COLLECTION:
                window_title = 'ROM Collection data'
                (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
                collection = collections[launcherID]
                info_text = '[COLOR orange]ROM Collection information[/COLOR]\n'
                info_text += self._misc_print_string_Collection(collection)
            else:
                # --- Read ROMs ---
                regular_launcher = True
                if categoryID == VCATEGORY_FAVOURITES_ID:
                    log_info('_command_view_menu() Viewing ROM in Favourites ...')
                    roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
                    rom = roms[romID]
                    window_title = 'Favourite ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Favourite'

                elif categoryID == VCATEGORY_MOST_PLAYED_ID:
                    log_info('_command_view_menu() Viewing ROM in Most played ROMs list ...')
                    most_played_roms = fs_load_Favourites_JSON(MOST_PLAYED_FILE_PATH)
                    rom = most_played_roms[romID]
                    window_title = 'Most Played ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Most Played ROM'

                elif categoryID == VCATEGORY_RECENT_ID:
                    log_info('_command_view_menu() Viewing ROM in Recently played ROMs ...')
                    recent_roms_list = fs_load_Collection_ROMs_JSON(RECENT_PLAYED_FILE_PATH)
                    current_ROM_position = fs_collection_ROM_index_by_romID(romID, recent_roms_list)
                    if current_ROM_position < 0:
                        kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
                        return
                    rom = recent_roms_list[current_ROM_position]
                    window_title = 'Recently played ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Recently played ROM'

                elif categoryID == VCATEGORY_TITLE_ID:
                    log_info('_command_view_menu() Viewing ROM in Title Virtual Launcher ...')
                    hashed_db_filename = VIRTUAL_CAT_TITLE_DIR.pjoin(launcherID + '.json')
                    if not hashed_db_filename.exists():
                        log_error('_command_view_menu() Cannot find file "{0}"'.format(hashed_db_filename.getPath()))
                        kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                        return
                    roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_TITLE_DIR, launcherID)
                    rom = roms[romID]
                    window_title = 'Virtual Launcher Title ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Virtual Launcher Title'

                elif categoryID == VCATEGORY_YEARS_ID:
                    log_info('_command_view_menu() Viewing ROM in Year Virtual Launcher ...')
                    hashed_db_filename = VIRTUAL_CAT_YEARS_DIR.pjoin(launcherID + '.json')
                    if not hashed_db_filename.exists():
                        log_error('_command_view_menu() Cannot find file "{0}"'.format(hashed_db_filename.getPath()))
                        kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                        return
                    roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_YEARS_DIR, launcherID)
                    rom = roms[romID]
                    window_title = 'Virtual Launcher Year ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Virtual Launcher Year'

                elif categoryID == VCATEGORY_GENRE_ID:
                    log_info('_command_view_menu() Viewing ROM in Genre Virtual Launcher ...')
                    hashed_db_filename = VIRTUAL_CAT_GENRE_DIR.pjoin(launcherID + '.json')
                    if not hashed_db_filename.exists():
                        log_error('_command_view_menu() Cannot find file "{0}"'.format(hashed_db_filename.getPath()))
                        kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                        return
                    roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_GENRE_DIR, launcherID)
                    rom = roms[romID]
                    window_title = 'Virtual Launcher Genre ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Virtual Launcher Genre'

                elif categoryID == VCATEGORY_DEVELOPER_ID:
                    log_info('_command_view_menu() Viewing ROM in Developer Virtual Launcher ...')
                    hashed_db_filename = VIRTUAL_CAT_DEVELOPER_DIR.pjoin(launcherID + '.json')
                    if not hashed_db_filename.exists():
                        log_error('_command_view_menu() Cannot find file "{0}"'.format(hashed_db_filename.getPath()))
                        kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                        return
                    roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_DEVELOPER_DIR, launcherID)
                    rom = roms[romID]
                    window_title = 'Virtual Launcher Studio ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Virtual Launcher Studio'

                elif categoryID == VCATEGORY_NPLAYERS_ID:
                    log_info('_command_view_menu() Viewing ROM in NPlayers Virtual Launcher ...')
                    hashed_db_filename = VIRTUAL_CAT_NPLAYERS_DIR.pjoin(launcherID + '.json')
                    if not hashed_db_filename.exists():
                        log_error('_command_view_menu() Cannot find file "{0}"'.format(hashed_db_filename.getPath()))
                        kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                        return
                    roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_NPLAYERS_DIR, launcherID)
                    rom = roms[romID]
                    window_title = 'Virtual Launcher NPlayer ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Virtual Launcher NPlayer'

                elif categoryID == VCATEGORY_ESRB_ID:
                    log_info('_command_view_menu() Viewing ROM in ESRB Launcher ...')
                    hashed_db_filename = VIRTUAL_CAT_ESRB_DIR.pjoin(launcherID + '.json')
                    if not hashed_db_filename.exists():
                        log_error('_command_view_menu() Cannot find file "{0}"'.format(hashed_db_filename.getPath()))
                        kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                        return
                    roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_ESRB_DIR, launcherID)
                    rom = roms[romID]
                    window_title = 'Virtual Launcher ESRB ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Virtual Launcher ESRB'

                elif categoryID == VCATEGORY_RATING_ID:
                    log_info('_command_view_menu() Viewing ROM in Rating Launcher ...')
                    hashed_db_filename = VIRTUAL_CAT_RATING_DIR.pjoin(launcherID + '.json')
                    if not hashed_db_filename.exists():
                        log_error('_command_view_menu() Cannot find file "{0}"'.format(hashed_db_filename.getPath()))
                        kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                        return
                    roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_RATING_DIR, launcherID)
                    rom = roms[romID]
                    window_title = 'Virtual Launcher Rating ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Virtual Launcher Rating'

                elif categoryID == VCATEGORY_CATEGORY_ID:
                    log_info('_command_view_menu() Viewing ROM in Category Virtual Launcher ...')
                    hashed_db_filename = VIRTUAL_CAT_CATEGORY_DIR.pjoin(launcherID + '.json')
                    if not hashed_db_filename.exists():
                        log_error('_command_view_menu() Cannot find file "{0}"'.format(hashed_db_filename.getPath()))
                        kodi_dialog_OK('Virtual launcher XML/JSON file not found.')
                        return
                    roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_CATEGORY_DIR, launcherID)
                    rom = roms[romID]
                    window_title = 'Virtual Launcher Category ROM data'
                    regular_launcher = False
                    vlauncher_label = 'Virtual Launcher Category'

                # --- ROM in Collection ---
                elif categoryID == VCATEGORY_COLLECTIONS_ID:
                    log_info('_command_view_menu() Viewing ROM in Collection ...')
                    (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
                    collection = collections[launcherID]
                    roms_json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
                    collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
                    current_ROM_position = fs_collection_ROM_index_by_romID(romID, collection_rom_list)
                    if current_ROM_position < 0:
                        kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
                        return
                    rom = collection_rom_list[current_ROM_position]
                    window_title = '{0} Collection ROM data'.format(collection['m_name'])
                    regular_launcher = False
                    vlauncher_label = 'Collection'

                # --- ROM in regular launcher ---
                else:
                    log_info('_command_view_menu() Viewing ROM in Launcher ...')
                    if romID == UNKNOWN_ROMS_PARENT_ID:
                        kodi_dialog_OK('You cannot view this ROM!')
                        return
                    # >> Check launcher is OK
                    if launcherID not in self.launchers:
                        kodi_dialog_OK('launcherID not found in self.launchers')
                        return
                    launcher_in_category = False if categoryID == VCATEGORY_ADDONROOT_ID else True
                    if launcher_in_category: category = self.categories[categoryID]
                    launcher = self.launchers[launcherID]
                    roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)
                    rom = roms[romID]
                    window_title = 'Launcher ROM data'

                # --- Make information string ---
                info_text  = '[COLOR orange]ROM information[/COLOR]\n'
                info_text += self._misc_print_string_ROM(rom)

                # --- Display category/launcher information ---
                if regular_launcher:
                    info_text += '\n[COLOR orange]Launcher information[/COLOR]\n'
                    info_text += self._misc_print_string_Launcher(launcher)
                    info_text += '\n[COLOR orange]Category information[/COLOR]\n'
                    if launcher_in_category:
                        info_text += self._misc_print_string_Category(category)
                    else:
                        info_text += 'No Category (Launcher in addon root)'
                else:
                    info_text += '\n[COLOR orange]{0} ROM additional information[/COLOR]\n'.format(vlauncher_label)
                    info_text += self._misc_print_string_ROM_additional(rom)

            # --- Show information window ---
            log_debug('Setting Window(10000) Property "FontWidth" = "monospaced"')
            xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
            dialog = xbmcgui.Dialog()
            dialog.textviewer(window_title, info_text)
            log_debug('Setting Window(10000) Property "FontWidth" = "proportional"')
            xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

        # --- Launcher statistical reports ---
        elif action == ACTION_VIEW_LAUNCHER_STATS or \
             action == ACTION_VIEW_LAUNCHER_METADATA or \
             action == ACTION_VIEW_LAUNCHER_ASSETS:
            # --- Standalone launchers do not have reports! ---
            if categoryID in self.categories: category_name = self.categories[categoryID]['m_name']
            else:                             category_name = VCATEGORY_ADDONROOT_ID
            launcher = self.launchers[launcherID]
            if not launcher['rompath']:
                kodi_notify_warn('Cannot create report for standalone launcher')
                return
            # --- If no ROMs in launcher do nothing ---
            launcher = self.launchers[launcherID]
            roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)
            if not roms:
                kodi_notify_warn('No ROMs in launcher. Report not created')
                return
            # --- Regenerate reports if don't exist or are outdated ---
            self._roms_regenerate_launcher_reports(categoryID, launcherID, roms)

            # --- Get report filename ---
            roms_base_noext  = fs_get_ROMs_basename(category_name, launcher['m_name'], launcherID)
            report_stats_FN  = REPORTS_DIR.pjoin(roms_base_noext + '_stats.txt')
            report_meta_FN   = REPORTS_DIR.pjoin(roms_base_noext + '_metadata.txt')
            report_assets_FN = REPORTS_DIR.pjoin(roms_base_noext + '_assets.txt')
            log_verb('_command_view_menu() Stats  OP "{0}"'.format(report_stats_FN.getOriginalPath()))
            log_verb('_command_view_menu() Meta   OP "{0}"'.format(report_meta_FN.getOriginalPath()))
            log_verb('_command_view_menu() Assets OP "{0}"'.format(report_assets_FN.getOriginalPath()))

            # --- Read report file ---
            try:
                if action == ACTION_VIEW_LAUNCHER_STATS:
                    window_title = 'Launcher "{0}" Statistics Report'.format(launcher['m_name'])
                    file = open(report_stats_FN.getPath(), 'r')
                    info_text = file.read().decode('utf-8')
                    file.close()
                elif action == ACTION_VIEW_LAUNCHER_METADATA:
                    window_title = 'Launcher "{0}" Metadata Report'.format(launcher['m_name'])
                    file = open(report_meta_FN.getPath(), 'r')
                    info_text = file.read().decode('utf-8')
                    file.close()
                elif action == ACTION_VIEW_LAUNCHER_ASSETS:
                    window_title = 'Launcher "{0}" Asset Report'.format(launcher['m_name'])
                    file = open(report_assets_FN.getPath(), 'r')
                    info_text = file.read().decode('utf-8')
                    file.close()
            except IOError:
                log_error('_command_view_menu() (IOError) Exception reading report TXT file')
                window_title = 'Error'
                info_text = '[COLOR red]Exception reading report TXT file.[/COLOR]'
            info_text = info_text.replace('<No-Intro Audit Statistics>', '[COLOR orange]<No-Intro Audit Statistics>[/COLOR]')
            info_text = info_text.replace('<Metadata statistics>', '[COLOR orange]<Metadata statistics>[/COLOR]')
            info_text = info_text.replace('<Asset statistics>', '[COLOR orange]<Asset statistics>[/COLOR]')

            # --- Show information window ---
            log_debug('Setting Window(10000) Property "FontWidth" = "monospaced"')
            xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
            dialog = xbmcgui.Dialog()
            dialog.textviewer(window_title, info_text)
            log_debug('Setting Window(10000) Property "FontWidth" = "proportional"')
            xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

        # --- Launcher ROM scanner report ---
        elif action == ACTION_VIEW_LAUNCHER_SCANNER:
            # --- Ckeck for errors and read file ---
            if not launcher_report_FN.exists():
                kodi_dialog_OK('ROM scanner report not found.')
                return
            info_text = ''
            with open(launcher_report_FN.getPath(), 'r') as myfile:
                info_text = myfile.read()

            # --- Show information window ---
            window_title = 'ROM scanner report'
            log_debug('Setting Window(10000) Property "FontWidth" = "monospaced"')
            xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
            dialog = xbmcgui.Dialog()
            dialog.textviewer(window_title, info_text)
            log_debug('Setting Window(10000) Property "FontWidth" = "proportional"')
            xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

        # --- View ROM Manual ---
        # >> Use Ghostscript like HyperLauncher?
        # >> Or use plugin.image.pdfreader plugin?
        # >> Or ask core developers to incorporate a native PDF reader?
        elif action == ACTION_VIEW_MANUAL:
            kodi_dialog_OK('View ROM manual not implemented yet. Sorry.')

        # --- View ROM Map ---
        elif action == ACTION_VIEW_MAP:
            # >> Load ROMs
            if categoryID == VCATEGORY_FAVOURITES_ID:
                roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
                rom = roms[romID]
            elif categoryID == VCATEGORY_MOST_PLAYED_ID:
                most_played_roms = fs_load_Favourites_JSON(MOST_PLAYED_FILE_PATH)
                rom = most_played_roms[romID]
            elif categoryID == VCATEGORY_RECENT_ID:
                recent_roms_list = fs_load_Collection_ROMs_JSON(RECENT_PLAYED_FILE_PATH)
                current_ROM_position = fs_collection_ROM_index_by_romID(romID, recent_roms_list)
                if current_ROM_position < 0:
                    kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
                    return
                rom = recent_roms_list[current_ROM_position]
            elif categoryID == VCATEGORY_COLLECTIONS_ID:
                (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
                collection = collections[launcherID]
                roms_json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
                collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
                current_ROM_position = fs_collection_ROM_index_by_romID(romID, collection_rom_list)
                if current_ROM_position < 0:
                    kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
                    return
                rom = collection_rom_list[current_ROM_position]
            elif categoryID == VCATEGORY_TITLE_ID    or categoryID == VCATEGORY_YEARS_ID or \
                 categoryID == VCATEGORY_GENRE_ID    or categoryID == VCATEGORY_DEVELOPER_ID or \
                 categoryID == VCATEGORY_NPLAYERS_ID or categoryID == VCATEGORY_ESRB_ID or \
                 categoryID == VCATEGORY_RATING_ID   or categoryID == VCATEGORY_CATEGORY_ID:
                kodi_dialog_OK('ROM-loading factory not implemented yet. '
                               'Until then you cannot see maps in Virtual Launchers. '
                               'Sorry.')
                return
            else:
                launcher = self.launchers[launcherID]
                roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)
                rom = roms[romID]

            # >> Show map image
            s_map = rom['s_map']
            if not s_map:
                kodi_dialog_OK('Map image file not set for ROM "{0}"'.format(rom['m_name']))
                return
            map_FN = FileName(s_map)
            if not map_FN.exists():
                kodi_dialog_OK('Map image file not found.')
                return
            xbmc.executebuiltin('ShowPicture("{0}")'.format(map_FN.getPath()))

        # --- View last execution output ---
        elif action == ACTION_VIEW_EXEC_OUTPUT:
            log_debug('_command_view_menu() Executing action == ACTION_VIEW_EXEC_OUTPUT')

            # --- Ckeck for errors and read file ---
            if not LAUNCH_LOG_FILE_PATH.exists():
                kodi_dialog_OK('Log file not found. Try to run the emulator/application.')
                return
            # >> Kodi BUG: if the log file size is 0 (it is empty) then Kodi displays in the
            # >> text window the last displayed text.
            info_text = ''
            with open(LAUNCH_LOG_FILE_PATH.getPath(), 'r') as myfile:
                log_debug('_command_view_menu() Reading launcher.log ...')
                info_text = myfile.read()

            # --- Show information window ---
            window_title = 'Launcher last execution stdout'
            log_debug('Setting Window(10000) Property "FontWidth" = "monospaced"')
            xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
            xbmcgui.Dialog().textviewer(window_title, info_text)
            log_debug('Setting Window(10000) Property "FontWidth" = "proportional"')
            xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

        else:
            kodi_dialog_OK('Wrong action == {0}. This is a bug, please report it.'.format(action))

    def _misc_print_string_ROM(self, rom):
        info_text  = ''
        info_text += "[COLOR violet]id[/COLOR]: '{0}'\n".format(rom['id'])
        # >> Metadata
        info_text += "[COLOR violet]m_name[/COLOR]: '{0}'\n".format(rom['m_name'])
        info_text += "[COLOR violet]m_year[/COLOR]: '{0}'\n".format(rom['m_year'])
        info_text += "[COLOR violet]m_genre[/COLOR]: '{0}'\n".format(rom['m_genre'])
        info_text += "[COLOR violet]m_developer[/COLOR]: '{0}'\n".format(rom['m_developer'])
        info_text += "[COLOR violet]m_nplayers[/COLOR]: '{0}'\n".format(rom['m_nplayers'])
        info_text += "[COLOR violet]m_esrb[/COLOR]: '{0}'\n".format(rom['m_esrb'])
        info_text += "[COLOR violet]m_rating[/COLOR]: '{0}'\n".format(rom['m_rating'])
        info_text += "[COLOR violet]m_plot[/COLOR]: '{0}'\n".format(rom['m_plot'])
        # >> Info
        info_text += "[COLOR violet]filename[/COLOR]: '{0}'\n".format(rom['filename'])        
        info_text += "[COLOR skyblue]disks[/COLOR]: {0}\n".format(rom['disks'])
        info_text += "[COLOR violet]altapp[/COLOR]: '{0}'\n".format(rom['altapp'])
        info_text += "[COLOR violet]altarg[/COLOR]: '{0}'\n".format(rom['altarg'])
        info_text += "[COLOR skyblue]finished[/COLOR]: {0}\n".format(rom['finished'])
        info_text += "[COLOR violet]nointro_status[/COLOR]: '{0}'\n".format(rom['nointro_status'])
        info_text += "[COLOR violet]pclone_status[/COLOR]: '{0}'\n".format(rom['pclone_status'])
        info_text += "[COLOR violet]cloneof[/COLOR]: '{0}'\n".format(rom['cloneof'])
        # >> Assets/artwork
        info_text += "[COLOR violet]s_title[/COLOR]: '{0}'\n".format(rom['s_title'])
        info_text += "[COLOR violet]s_snap[/COLOR]: '{0}'\n".format(rom['s_snap'])
        info_text += "[COLOR violet]s_boxfront[/COLOR]: '{0}'\n".format(rom['s_boxfront'])
        info_text += "[COLOR violet]s_boxback[/COLOR]: '{0}'\n".format(rom['s_boxback'])
        info_text += "[COLOR violet]s_cartridge[/COLOR]: '{0}'\n".format(rom['s_cartridge'])
        info_text += "[COLOR violet]s_fanart[/COLOR]: '{0}'\n".format(rom['s_fanart'])
        info_text += "[COLOR violet]s_banner[/COLOR]: '{0}'\n".format(rom['s_banner'])
        info_text += "[COLOR violet]s_clearlogo[/COLOR]: '{0}'\n".format(rom['s_clearlogo'])
        info_text += "[COLOR violet]s_flyer[/COLOR]: '{0}'\n".format(rom['s_flyer'])
        info_text += "[COLOR violet]s_map[/COLOR]: '{0}'\n".format(rom['s_map'])
        info_text += "[COLOR violet]s_manual[/COLOR]: '{0}'\n".format(rom['s_manual'])
        info_text += "[COLOR violet]s_trailer[/COLOR]: '{0}'\n".format(rom['s_trailer'])

        return info_text

    def _misc_print_string_ROM_additional(self, rom):
        info_text  = ''
        info_text += "[COLOR violet]launcherID[/COLOR]: '{0}'\n".format(rom['launcherID'])
        info_text += "[COLOR violet]platform[/COLOR]: '{0}'\n".format(rom['platform'])
        info_text += "[COLOR violet]application[/COLOR]: '{0}'\n".format(rom['application'])
        info_text += "[COLOR violet]args[/COLOR]: '{0}'\n".format(rom['args'])
        info_text += "[COLOR skyblue]args_extra[/COLOR]: {0}\n".format(rom['args_extra'])
        info_text += "[COLOR violet]rompath[/COLOR]: '{0}'\n".format(rom['rompath'])
        info_text += "[COLOR violet]romext[/COLOR]: '{0}'\n".format(rom['romext'])
        info_text += "[COLOR skyblue]minimize[/COLOR]: {0}\n".format(rom['minimize'])
        info_text += "[COLOR skyblue]non_blocking[/COLOR]: {0}\n".format(rom['non_blocking'])
        info_text += "[COLOR violet]roms_default_icon[/COLOR]: '{0}'\n".format(rom['roms_default_icon'])
        info_text += "[COLOR violet]roms_default_fanart[/COLOR]: '{0}'\n".format(rom['roms_default_fanart'])
        info_text += "[COLOR violet]roms_default_banner[/COLOR]: '{0}'\n".format(rom['roms_default_banner'])
        info_text += "[COLOR violet]roms_default_poster[/COLOR]: '{0}'\n".format(rom['roms_default_poster'])
        info_text += "[COLOR violet]roms_default_clearlogo[/COLOR]: '{0}'\n".format(rom['roms_default_clearlogo'])

        # >> Favourite ROMs unique fields.
        info_text += "[COLOR violet]fav_status[/COLOR]: '{0}'\n".format(rom['fav_status'])
        # >> 'launch_count' only in Favourite ROMs in "Most played ROMs"
        if 'launch_count' in rom:
            info_text += "[COLOR skyblue]launch_count[/COLOR]: {0}\n".format(rom['launch_count'])

        return info_text

    def _misc_print_string_Launcher(self, launcher):
        info_text  = ''
        info_text += "[COLOR violet]id[/COLOR]: '{0}'\n".format(launcher['id'])
        info_text += "[COLOR violet]m_name[/COLOR]: '{0}'\n".format(launcher['m_name'])
        info_text += "[COLOR violet]m_year[/COLOR]: '{0}'\n".format(launcher['m_year'])
        info_text += "[COLOR violet]m_genre[/COLOR]: '{0}'\n".format(launcher['m_genre'])
        info_text += "[COLOR violet]m_developer[/COLOR]: '{0}'\n".format(launcher['m_developer'])
        info_text += "[COLOR violet]m_rating[/COLOR]: '{0}'\n".format(launcher['m_rating'])
        info_text += "[COLOR violet]m_plot[/COLOR]: '{0}'\n".format(launcher['m_plot'])

        info_text += "[COLOR violet]platform[/COLOR]: '{0}'\n".format(launcher['platform'])
        info_text += "[COLOR violet]categoryID[/COLOR]: '{0}'\n".format(launcher['categoryID'])
        info_text += "[COLOR violet]application[/COLOR]: '{0}'\n".format(launcher['application'])
        info_text += "[COLOR violet]args[/COLOR]: '{0}'\n".format(launcher['args'])
        info_text += "[COLOR skyblue]args_extra[/COLOR]: {0}\n".format(launcher['args_extra'])
        info_text += "[COLOR violet]rompath[/COLOR]: '{0}'\n".format(launcher['rompath'])
        info_text += "[COLOR violet]romext[/COLOR]: '{0}'\n".format(launcher['romext'])
        info_text += "[COLOR skyblue]finished[/COLOR]: {0}\n".format(launcher['finished'])
        info_text += "[COLOR skyblue]minimize[/COLOR]: {0}\n".format(launcher['minimize'])
        info_text += "[COLOR skyblue]non_blocking[/COLOR]: {0}\n".format(launcher['non_blocking'])
        info_text += "[COLOR violet]roms_base_noext[/COLOR]: '{0}'\n".format(launcher['roms_base_noext'])

        info_text += "[COLOR violet]nointro_xml_file[/COLOR]: '{0}'\n".format(launcher['nointro_xml_file'])
        info_text += "[COLOR violet]nointro_display_mode[/COLOR]: '{0}'\n".format(launcher['nointro_display_mode'])
        info_text += "[COLOR violet]launcher_display_mode[/COLOR]: '{0}'\n".format(launcher['launcher_display_mode'])
        info_text += "[COLOR skyblue]num_roms[/COLOR]: {0}\n".format(launcher['num_roms'])
        info_text += "[COLOR skyblue]num_parents[/COLOR]: {0}\n".format(launcher['num_parents'])
        info_text += "[COLOR skyblue]num_clones[/COLOR]: {0}\n".format(launcher['num_clones'])
        info_text += "[COLOR skyblue]num_have[/COLOR]: {0}\n".format(launcher['num_have'])
        info_text += "[COLOR skyblue]num_miss[/COLOR]: {0}\n".format(launcher['num_miss'])
        info_text += "[COLOR skyblue]num_unknown[/COLOR]: {0}\n".format(launcher['num_unknown'])
        info_text += "[COLOR skyblue]timestamp_launcher[/COLOR]: {0}\n".format(launcher['timestamp_launcher'])
        info_text += "[COLOR skyblue]timestamp_report[/COLOR]: {0}\n".format(launcher['timestamp_report'])

        info_text += "[COLOR violet]default_icon[/COLOR]: '{0}'\n".format(launcher['default_icon'])
        info_text += "[COLOR violet]default_fanart[/COLOR]: '{0}'\n".format(launcher['default_fanart'])
        info_text += "[COLOR violet]default_banner[/COLOR]: '{0}'\n".format(launcher['default_banner'])
        info_text += "[COLOR violet]default_poster[/COLOR]: '{0}'\n".format(launcher['default_poster'])
        info_text += "[COLOR violet]default_clearlogo[/COLOR]: '{0}'\n".format(launcher['default_clearlogo'])
        info_text += "[COLOR violet]default_controller[/COLOR]: '{0}'\n".format(launcher['default_controller'])
        info_text += "[COLOR violet]Asset_Prefix[/COLOR]: '{0}'\n".format(launcher['Asset_Prefix'])
        info_text += "[COLOR violet]s_icon[/COLOR]: '{0}'\n".format(launcher['s_icon'])
        info_text += "[COLOR violet]s_fanart[/COLOR]: '{0}'\n".format(launcher['s_fanart'])
        info_text += "[COLOR violet]s_banner[/COLOR]: '{0}'\n".format(launcher['s_banner'])
        info_text += "[COLOR violet]s_poster[/COLOR]: '{0}'\n".format(launcher['s_poster'])
        info_text += "[COLOR violet]s_clearlogo[/COLOR]: '{0}'\n".format(launcher['s_clearlogo'])
        info_text += "[COLOR violet]s_controller[/COLOR]: '{0}'\n".format(launcher['s_controller'])
        info_text += "[COLOR violet]s_trailer[/COLOR]: '{0}'\n".format(launcher['s_trailer'])

        info_text += "[COLOR violet]roms_default_icon[/COLOR]: '{0}'\n".format(launcher['roms_default_icon'])
        info_text += "[COLOR violet]roms_default_fanart[/COLOR]: '{0}'\n".format(launcher['roms_default_fanart'])
        info_text += "[COLOR violet]roms_default_banner[/COLOR]: '{0}'\n".format(launcher['roms_default_banner'])
        info_text += "[COLOR violet]roms_default_poster[/COLOR]: '{0}'\n".format(launcher['roms_default_poster'])
        info_text += "[COLOR violet]roms_default_clearlogo[/COLOR]: '{0}'\n".format(launcher['roms_default_clearlogo'])
        info_text += "[COLOR violet]ROM_asset_path[/COLOR]: '{0}'\n".format(launcher['ROM_asset_path'])
        info_text += "[COLOR violet]path_title[/COLOR]: '{0}'\n".format(launcher['path_title'])
        info_text += "[COLOR violet]path_snap[/COLOR]: '{0}'\n".format(launcher['path_snap'])
        info_text += "[COLOR violet]path_boxfront[/COLOR]: '{0}'\n".format(launcher['path_boxfront'])
        info_text += "[COLOR violet]path_boxback[/COLOR]: '{0}'\n".format(launcher['path_boxback'])
        info_text += "[COLOR violet]path_cartridge[/COLOR]: '{0}'\n".format(launcher['path_cartridge'])
        info_text += "[COLOR violet]path_fanart[/COLOR]: '{0}'\n".format(launcher['path_fanart'])
        info_text += "[COLOR violet]path_banner[/COLOR]: '{0}'\n".format(launcher['path_banner'])
        info_text += "[COLOR violet]path_clearlogo[/COLOR]: '{0}'\n".format(launcher['path_clearlogo'])
        info_text += "[COLOR violet]path_flyer[/COLOR]: '{0}'\n".format(launcher['path_flyer'])
        info_text += "[COLOR violet]path_map[/COLOR]: '{0}'\n".format(launcher['path_map'])
        info_text += "[COLOR violet]path_manual[/COLOR]: '{0}'\n".format(launcher['path_manual'])
        info_text += "[COLOR violet]path_trailer[/COLOR]: '{0}'\n".format(launcher['path_trailer'])

        return info_text

    def _misc_print_string_Category(self, category):
        info_text  = ''
        info_text += "[COLOR violet]id[/COLOR]: '{0}'\n".format(category['id'])
        info_text += "[COLOR violet]m_name[/COLOR]: '{0}'\n".format(category['m_name'])
        info_text += "[COLOR violet]m_genre[/COLOR]: '{0}'\n".format(category['m_genre'])
        info_text += "[COLOR violet]m_rating[/COLOR]: '{0}'\n".format(category['m_rating'])
        info_text += "[COLOR violet]m_plot[/COLOR]: '{0}'\n".format(category['m_plot'])
        info_text += "[COLOR skyblue]finished[/COLOR]: {0}\n".format(category['finished'])
        info_text += "[COLOR violet]default_icon[/COLOR]: '{0}'\n".format(category['default_icon'])
        info_text += "[COLOR violet]default_fanart[/COLOR]: '{0}'\n".format(category['default_fanart'])
        info_text += "[COLOR violet]default_banner[/COLOR]: '{0}'\n".format(category['default_banner'])
        info_text += "[COLOR violet]default_poster[/COLOR]: '{0}'\n".format(category['default_poster'])
        info_text += "[COLOR violet]default_clearlogo[/COLOR]: '{0}'\n".format(category['default_clearlogo'])
        info_text += "[COLOR violet]Asset_Prefix[/COLOR]: '{0}'\n".format(category['Asset_Prefix'])
        info_text += "[COLOR violet]s_icon[/COLOR]: '{0}'\n".format(category['s_icon'])
        info_text += "[COLOR violet]s_fanart[/COLOR]: '{0}'\n".format(category['s_fanart'])
        info_text += "[COLOR violet]s_banner[/COLOR]: '{0}'\n".format(category['s_banner'])
        info_text += "[COLOR violet]s_poster[/COLOR]: '{0}'\n".format(category['s_poster'])
        info_text += "[COLOR violet]s_clearlogo[/COLOR]: '{0}'\n".format(category['s_clearlogo'])
        info_text += "[COLOR violet]s_trailer[/COLOR]: '{0}'\n".format(category['s_trailer'])

        return info_text

    def _misc_print_string_Collection(self, collection):
        info_text  = ''
        info_text += "[COLOR violet]id[/COLOR]: '{0}'\n".format(collection['id'])
        info_text += "[COLOR violet]m_name[/COLOR]: '{0}'\n".format(collection['m_name'])
        info_text += "[COLOR violet]m_genre[/COLOR]: '{0}'\n".format(collection['m_genre'])
        info_text += "[COLOR violet]m_rating[/COLOR]: '{0}'\n".format(collection['m_rating'])
        info_text += "[COLOR violet]m_plot[/COLOR]: '{0}'\n".format(collection['m_plot'])
        info_text += "[COLOR violet]roms_base_noext[/COLOR]: {0}\n".format(collection['roms_base_noext'])
        info_text += "[COLOR violet]default_icon[/COLOR]: '{0}'\n".format(collection['default_icon'])
        info_text += "[COLOR violet]default_fanart[/COLOR]: '{0}'\n".format(collection['default_fanart'])
        info_text += "[COLOR violet]default_banner[/COLOR]: '{0}'\n".format(collection['default_banner'])
        info_text += "[COLOR violet]default_poster[/COLOR]: '{0}'\n".format(collection['default_poster'])
        info_text += "[COLOR violet]default_clearlogo[/COLOR]: '{0}'\n".format(collection['default_clearlogo'])
        info_text += "[COLOR violet]s_icon[/COLOR]: '{0}'\n".format(collection['s_icon'])
        info_text += "[COLOR violet]s_fanart[/COLOR]: '{0}'\n".format(collection['s_fanart'])
        info_text += "[COLOR violet]s_banner[/COLOR]: '{0}'\n".format(collection['s_banner'])
        info_text += "[COLOR violet]s_poster[/COLOR]: '{0}'\n".format(collection['s_poster'])
        info_text += "[COLOR violet]s_clearlogo[/COLOR]: '{0}'\n".format(collection['s_clearlogo'])
        info_text += "[COLOR violet]s_trailer[/COLOR]: '{0}'\n".format(collection['s_trailer'])

        return info_text

    def _command_view_offline_scraper_rom(self, scraper, platform, game_name):
        log_debug('_command_view_offline_scraper_rom() scraper   "{0}"'.format(scraper))
        log_debug('_command_view_offline_scraper_rom() platform  "{0}"'.format(platform))
        log_debug('_command_view_offline_scraper_rom() game_name "{0}"'.format(game_name))

        # --- Load Offline Scraper database ---
        # --- Load offline scraper XML file ---
        loading_ticks_start = time.time()
        if scraper == 'AEL':
            xml_file = platform_AEL_to_Offline_GameDBInfo_XML[platform]
            xml_path = os.path.join(CURRENT_ADDON_DIR.getPath(), xml_file)
            # log_debug('xml_file = {0}'.format(xml_file))
            log_debug('Loading AEL XML {0}'.format(xml_path))
            games = audit_load_OfflineScraper_XML(xml_path)
            game = games[game_name]

            info_text  = '[COLOR orange]ROM information[/COLOR]\n'
            info_text += "[COLOR violet]game_name[/COLOR]: '{0}'\n".format(game_name)
            info_text += "[COLOR violet]platform[/COLOR]: '{0}'\n".format(platform)
            info_text += '\n[COLOR orange]Metadata[/COLOR]\n'
            info_text += "[COLOR violet]description[/COLOR]: '{0}'\n".format(game['description'])
            info_text += "[COLOR violet]year[/COLOR]: '{0}'\n".format(game['year'])
            info_text += "[COLOR violet]rating[/COLOR]: '{0}'\n".format(game['rating'])
            info_text += "[COLOR violet]manufacturer[/COLOR]: '{0}'\n".format(game['manufacturer'])
            info_text += "[COLOR violet]dev[/COLOR]: '{0}'\n".format(game['dev'])
            info_text += "[COLOR violet]genre[/COLOR]: '{0}'\n".format(game['genre'])
            info_text += "[COLOR violet]score[/COLOR]: '{0}'\n".format(game['score'])
            info_text += "[COLOR violet]player[/COLOR]: '{0}'\n".format(game['player'])
            info_text += "[COLOR violet]story[/COLOR]: '{0}'\n".format(game['story'])
            info_text += "[COLOR violet]enabled[/COLOR]: '{0}'\n".format(game['enabled'])
            info_text += "[COLOR violet]crc[/COLOR]: '{0}'\n".format(game['crc'])
            info_text += "[COLOR violet]cloneof[/COLOR]: '{0}'\n".format(game['cloneof'])
        elif scraper == 'LaunchBox':
            xml_file = platform_AEL_to_LB_XML[platform]
            xml_path = os.path.join(CURRENT_ADDON_DIR.getPath(), xml_file)
            # log_debug('xml_file = {0}'.format(xml_file))
            log_debug('Loading LaunchBox XML {0}'.format(xml_path))
            games = audit_load_OfflineScraper_XML(xml_path)
            game = games[game_name]
            # log_debug(unicode(game))

            info_text  = '[COLOR orange]ROM information[/COLOR]\n'
            info_text += "[COLOR violet]game_name[/COLOR]: '{0}'\n".format(game_name)
            info_text += "[COLOR violet]platform[/COLOR]: '{0}'\n".format(platform)
            info_text += '\n[COLOR orange]Metadata[/COLOR]\n'
            info_text += "[COLOR violet]Name[/COLOR]: '{0}'\n".format(game['Name'])
            info_text += "[COLOR violet]ReleaseYear[/COLOR]: '{0}'\n".format(game['ReleaseYear'])            
            info_text += "[COLOR violet]Overview[/COLOR]: '{0}'\n".format(game['Overview'])
            info_text += "[COLOR violet]MaxPlayers[/COLOR]: '{0}'\n".format(game['MaxPlayers'])
            info_text += "[COLOR violet]Cooperative[/COLOR]: '{0}'\n".format(game['Cooperative'])
            info_text += "[COLOR violet]VideoURL[/COLOR]: '{0}'\n".format(game['VideoURL'])
            info_text += "[COLOR violet]DatabaseID[/COLOR]: '{0}'\n".format(game['DatabaseID'])
            info_text += "[COLOR violet]CommunityRating[/COLOR]: '{0}'\n".format(game['CommunityRating'])
            info_text += "[COLOR violet]Platform[/COLOR]: '{0}'\n".format(game['Platform'])
            info_text += "[COLOR violet]Genres[/COLOR]: '{0}'\n".format(game['Genres'])
            info_text += "[COLOR violet]Publisher[/COLOR]: '{0}'\n".format(game['Publisher'])
            info_text += "[COLOR violet]Developer[/COLOR]: '{0}'\n".format(game['Developer'])
        else:
            kodi_dialog_OK('Wrong scraper name {0}'.format(scraper))
            return

        # --- Show information window ---
        window_title = 'Offline Scraper ROM information'
        log_debug('Setting Window(10000) Property "FontWidth" = "monospaced"')
        xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
        dialog = xbmcgui.Dialog()
        dialog.textviewer(window_title, info_text)
        log_debug('Setting Window(10000) Property "FontWidth" = "proportional"')
        xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

    #
    # Updated all virtual categories DB
    #
    def _command_update_virtual_category_db_all(self):
        # --- Sanity checks ---
        if len(self.launchers) == 0:
            kodi_dialog_OK('You do not have any ROM Launcher. Add a ROM Launcher first.')
            return

        # --- Make a big dictionary will all the ROMs ---
        # Pass all_roms dictionary to the catalg create functions so this has not to be
        # recomputed for every virtual launcher.
        log_verb('_command_update_virtual_category_db_all() Creating list of all ROMs in all Launchers')
        all_roms = {}
        num_launchers = len(self.launchers)
        i = 0
        pDialog = xbmcgui.DialogProgress()
        pDialog_canceled = False
        pDialog.create('Advanced Emulator Launcher', 'Making ROM list ...')
        for launcher_id in self.launchers:
            # >> Update dialog
            pDialog.update(i * 100 / num_launchers)
            i += 1

            # >> Get current launcher
            launcher = self.launchers[launcher_id]
            categoryID = launcher['categoryID']
            if categoryID in self.categories:
                category_name = self.categories[categoryID]['m_name']
            elif categoryID == VCATEGORY_ADDONROOT_ID:
                category_name = 'Root category'
            else:
                log_error('_command_update_virtual_category_db_all() Wrong categoryID = {0}'.format(categoryID))
                kodi_dialog_OK('Wrong categoryID = {0}. Report this bug please.'.format(categoryID))
                return

            # >> If launcher is standalone skip
            if launcher['rompath'] == '': continue

            # >> Open launcher and add roms to the big list
            roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)

            # >> Add additional fields to ROM to make a Favourites ROM
            # >> Virtual categories/launchers are like Favourite ROMs that cannot be edited.
            # >> NOTE roms is updated by assigment, dictionaries are mutable
            fav_roms = {}
            for rom_id in roms:
                fav_rom = fs_get_Favourite_from_ROM(roms[rom_id], launcher)
                # >> Add the category this ROM belongs to.
                fav_rom['category_name'] = category_name
                fav_roms[rom_id] = fav_rom

            # >> Update dictionary
            all_roms.update(fav_roms)
        pDialog.update(100)
        pDialog.close()

        # --- Update all virtual launchers ---
        self._command_update_virtual_category_db(VCATEGORY_TITLE_ID, all_roms)
        self._command_update_virtual_category_db(VCATEGORY_YEARS_ID, all_roms)
        self._command_update_virtual_category_db(VCATEGORY_GENRE_ID, all_roms)
        self._command_update_virtual_category_db(VCATEGORY_DEVELOPER_ID, all_roms)
        self._command_update_virtual_category_db(VCATEGORY_NPLAYERS_ID, all_roms)
        self._command_update_virtual_category_db(VCATEGORY_ESRB_ID, all_roms)
        self._command_update_virtual_category_db(VCATEGORY_RATING_ID, all_roms)
        self._command_update_virtual_category_db(VCATEGORY_CATEGORY_ID, all_roms)
        kodi_notify('All virtual categories updated')

    #
    # Makes a virtual category database
    #
    def _command_update_virtual_category_db(self, virtual_categoryID, all_roms_external = None):
        # --- Customise function depending on virtual category ---
        if virtual_categoryID == VCATEGORY_TITLE_ID:
            log_info('_command_update_virtual_category_db() Updating Title DB')
            vcategory_db_directory = VIRTUAL_CAT_TITLE_DIR
            vcategory_db_filename  = VCAT_TITLE_FILE_PATH
            vcategory_field_name   = 'm_name'
            vcategory_name         = 'Titles'
        elif virtual_categoryID == VCATEGORY_YEARS_ID:
            log_info('_command_update_virtual_category_db() Updating Year DB')
            vcategory_db_directory = VIRTUAL_CAT_YEARS_DIR
            vcategory_db_filename  = VCAT_YEARS_FILE_PATH
            vcategory_field_name   = 'm_year'
            vcategory_name         = 'Years'
        elif virtual_categoryID == VCATEGORY_GENRE_ID:
            log_info('_command_update_virtual_category_db() Updating Genre DB')
            vcategory_db_directory = VIRTUAL_CAT_GENRE_DIR
            vcategory_db_filename  = VCAT_GENRE_FILE_PATH
            vcategory_field_name   = 'm_genre'
            vcategory_name         = 'Genres'
        elif virtual_categoryID == VCATEGORY_DEVELOPER_ID:
            log_info('_command_update_virtual_category_db() Updating Developer DB')
            vcategory_db_directory = VIRTUAL_CAT_DEVELOPER_DIR
            vcategory_db_filename  = VCAT_DEVELOPER_FILE_PATH
            vcategory_field_name   = 'm_developer'
            vcategory_name         = 'Developers'
        elif virtual_categoryID == VCATEGORY_NPLAYERS_ID:
            log_info('_command_update_virtual_category_db() Updating NPlayer DB')
            vcategory_db_directory = VIRTUAL_CAT_NPLAYERS_DIR
            vcategory_db_filename  = VCAT_NPLAYERS_FILE_PATH
            vcategory_field_name   = 'm_nplayers'
            vcategory_name         = 'NPlayers'
        elif virtual_categoryID == VCATEGORY_ESRB_ID:
            log_info('_command_update_virtual_category_db() Updating ESRB DB')
            vcategory_db_directory = VIRTUAL_CAT_ESRB_DIR
            vcategory_db_filename  = VCAT_ESRB_FILE_PATH
            vcategory_field_name   = 'm_esrb'
            vcategory_name         = 'ESRB'
        elif virtual_categoryID == VCATEGORY_RATING_ID:
            log_info('_command_update_virtual_category_db() Updating Rating DB')
            vcategory_db_directory = VIRTUAL_CAT_RATING_DIR
            vcategory_db_filename  = VCAT_RATING_FILE_PATH
            vcategory_field_name   = 'm_rating'
            vcategory_name         = 'Rating'
        elif virtual_categoryID == VCATEGORY_CATEGORY_ID:
            log_info('_command_update_virtual_category_db() Updating Category DB')
            vcategory_db_directory = VIRTUAL_CAT_CATEGORY_DIR
            vcategory_db_filename  = VCAT_CATEGORY_FILE_PATH
            vcategory_field_name   = ''
            vcategory_name         = 'Categories'
        else:
            log_error('_command_update_virtual_category_db() Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            kodi_dialog_OK('Wrong virtual_category_kind = {0}'.format(virtual_categoryID))
            return

        # --- Sanity checks ---
        if len(self.launchers) == 0:
            kodi_dialog_OK('You do not have any ROM Launcher. Add a ROM Launcher first.')
            return

        # --- Delete previous hashed database XMLs ---
        log_info('_command_update_virtual_category_db() Cleaning hashed database old XMLs')
        for the_file in vcategory_db_directory.scanFilesInPathAsPaths('*.*'):
            file_extension = the_file.getExt()
            if file_extension.lower() != '.xml' and file_extension.lower() != '.json':
                # >> There should be only XMLs or JSON in this directory
                log_error('_command_update_virtual_category_db() Non XML/JSON file "{0}"'.format(the_file.getPath()))
                log_error('_command_update_virtual_category_db() Skipping it from deletion')
                continue
            log_verb('_command_update_virtual_category_db() Deleting "{0}"'.format(the_file.getPath()))
            try:
                if the_file.exists():
                    the_file.unlink()
            except Exception as e:
                log_error('_command_update_virtual_category_db() Excepcion deleting hashed DB XMLs')
                log_error('_command_update_virtual_category_db() {0}'.format(e))
                return

        # --- Progress dialog ---
        # >> Important to avoid multithread execution of the plugin and race conditions
        pDialog = xbmcgui.DialogProgress()
        pDialog_canceled = False

        # --- Make a big dictionary will all the ROMs ---
        if all_roms_external:
            log_verb('_command_update_virtual_category_db() Using cached all_roms dictionary')
            all_roms = all_roms_external
        else:
            log_verb('_command_update_virtual_category_db() Creating list of all ROMs in all Launchers')
            all_roms = {}
            num_launchers = len(self.launchers)
            i = 0
            pDialog.create('Advanced Emulator Launcher', 'Making ROM list ...')
            for launcher_id in self.launchers:
                # >> Update dialog
                pDialog.update(i * 100 / num_launchers)
                i += 1

                # >> Get current launcher
                launcher = self.launchers[launcher_id]
                categoryID = launcher['categoryID']
                if categoryID in self.categories:
                    category_name = self.categories[categoryID]['m_name']
                elif categoryID == VCATEGORY_ADDONROOT_ID:
                    category_name = 'Root category'
                else:
                    log_error('_command_update_virtual_category_db() Wrong categoryID = {0}'.format(categoryID))
                    kodi_dialog_OK('Wrong categoryID = {0}. Report this bug please.'.format(categoryID))
                    return

                # >> If launcher is standalone skip
                if launcher['rompath'] == '': continue

                # >> Open launcher and add roms to the big list
                roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)

                # >> Add additional fields to ROM to make a Favourites ROM
                # >> Virtual categories/launchers are like Favourite ROMs that cannot be edited.
                # >> NOTE roms is updated by assigment, dictionaries are mutable
                fav_roms = {}
                for rom_id in roms:
                    fav_rom = fs_get_Favourite_from_ROM(roms[rom_id], launcher)
                    # >> Add the category this ROM belongs to.
                    fav_rom['category_name'] = category_name
                    fav_roms[rom_id] = fav_rom

                # >> Update dictionary
                all_roms.update(fav_roms)
            pDialog.update(100)
            pDialog.close()

        # --- Create a dictionary with key the virtual category name and value a dictionay of roms
        #     belonging to that virtual category ---
        # TODO It would be nice to have a progress dialog here...
        log_verb('_command_update_virtual_category_db() Creating hashed database')
        virtual_launchers = {}
        for rom_id in all_roms:
            rom = all_roms[rom_id]
            if virtual_categoryID == VCATEGORY_TITLE_ID:
                vcategory_key = rom['m_name'][0].upper()
            elif virtual_categoryID == VCATEGORY_CATEGORY_ID:
                vcategory_key = rom['category_name']
            else:
                vcategory_key = rom[vcategory_field_name]
            # >> '' is a special case
            if vcategory_key == '': vcategory_key = '[ Not set ]'
            if vcategory_key in virtual_launchers:
                virtual_launchers[vcategory_key][rom['id']] = rom
            else:
                virtual_launchers[vcategory_key] = {rom['id'] : rom}

        # --- Write hashed distributed database XML files ---
        # TODO It would be nice to have a progress dialog here...
        log_verb('_command_update_virtual_category_db() Writing hashed database JSON files')
        vcategory_launchers = {}
        num_vlaunchers = len(virtual_launchers)
        i = 0
        pDialog.create('Advanced Emulator Launcher', 'Writing {0} hashed database ...'.format(vcategory_name))
        for vlauncher_id in virtual_launchers:
            # >> Update progress dialog
            pDialog.update(i * 100 / num_vlaunchers)
            i += 1

            # >> Create VLauncher UUID
            vlauncher_id_md5   = hashlib.md5(vlauncher_id.encode('utf-8'))
            hashed_db_UUID     = vlauncher_id_md5.hexdigest()
            log_debug('_command_update_virtual_category_db() vlauncher_id       "{0}"'.format(vlauncher_id))
            log_debug('_command_update_virtual_category_db() hashed_db_UUID     "{0}"'.format(hashed_db_UUID))

            # >> Virtual launcher ROMs are like Favourite ROMs. They contain all required fields to launch
            # >> the ROM, and also share filesystem I/O functions with Favourite ROMs.
            vlauncher_roms = virtual_launchers[vlauncher_id]
            log_debug('_command_update_virtual_category_db() Number of ROMs = {0}'.format(len(vlauncher_roms)))
            fs_write_VCategory_ROMs_JSON(vcategory_db_directory, hashed_db_UUID, vlauncher_roms)

            # >> Create virtual launcher
            vcategory_launchers[hashed_db_UUID] = {'id'              : hashed_db_UUID,
                                                   'name'            : vlauncher_id,
                                                   'rom_count'       : str(len(vlauncher_roms)),
                                                   'roms_base_noext' : hashed_db_UUID }
        pDialog.update(100)
        pDialog.close()

        # --- Write virtual launchers XML file ---
        # >> This file is small, no progress dialog
        log_verb('_command_update_virtual_category_db() Writing virtual category XML index')
        fs_write_VCategory_XML(vcategory_db_filename, vcategory_launchers)

    #
    # Launchs a standalone application.
    #
    def _command_run_standalone_launcher(self, categoryID, launcherID):
        # --- Check launcher is OK ---
        if launcherID not in self.launchers:
            kodi_dialog_OK('launcherID not found in self.launchers')
            return
        launcher = self.launchers[launcherID]
        minimize_flag = launcher['minimize']

        # --- Execute Kodi built-in function under certain conditions ---
        application = FileName(launcher['application'])
        if application.getBase().lower().replace('.exe' , '') == 'xbmc'  or \
           'xbmc-fav-' in launcher['application'] or 'xbmc-sea-' in launcher['application']:
            xbmc.executebuiltin('XBMC.{0}'.format(launcher['args']))
            return

        # ~~~~~ External application ~~~~~
        app_basename   = application.getBase()
        app_ext        = application.getExt()
        arguments      = launcher['args']
        launcher_title = launcher['m_name']
        log_info('_run_standalone_launcher() categoryID {0}'.format(categoryID))
        log_info('_run_standalone_launcher() launcherID {0}'.format(launcherID))
        log_info('_run_standalone_launcher() application   "{0}"'.format(application.getPath()))
        log_info('_run_standalone_launcher() apppath       "{0}"'.format(application.getDir()))
        log_info('_run_standalone_launcher() app_basename  "{0}"'.format(app_basename))
        log_info('_run_standalone_launcher() app_ext       "{0}"'.format(app_ext))
        log_info('_run_standalone_launcher() launcher name "{0}"'.format(launcher_title))

        # ~~~ Argument substitution ~~~
        log_info('_run_standalone_launcher() raw arguments   "{0}"'.format(arguments))
        arguments = arguments.replace('$apppath%' , application.getDir())
        log_info('_run_standalone_launcher() final arguments "{0}"'.format(arguments))

        # --- Check for errors and abort if errors found ---
        if not application.exists():
            log_error('Launching app not found "{0}"'.format(application.getPath()))
            kodi_notify_warn('App {0} not found.'.format(application.getOriginalPath()))
            return

        # ~~~~~ Execute external application ~~~~~
        non_blocking_flag = False
        self._run_before_execution(launcher_title, minimize_flag)
        self._run_process(application.getPath(), arguments, application.getDir(), app_ext, non_blocking_flag)
        self._run_after_execution(minimize_flag)

    #
    # Launchs a ROM
    # NOTE args_extre maybe present or not in Favourite ROM. In newer version of AEL always present.
    #
    def _command_run_rom(self, categoryID, launcherID, romID):
        # --- ROM in Favourites ---
        if categoryID == VCATEGORY_FAVOURITES_ID and launcherID == VLAUNCHER_FAVOURITES_ID:
            log_info('_command_run_rom() Launching ROM in Favourites ...')
            roms = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
            rom = roms[romID]
            recent_rom = rom
            minimize_flag     = rom['minimize']
            non_blocking_flag = rom['non_blocking']
            romext            = rom['romext']
            standard_app      = rom['application']
            standard_args     = rom['args']
            args_extra        = rom['args_extra'] if 'args_extra' in rom else list()
        # --- ROM in Recently played ROMs list ---
        elif categoryID == VCATEGORY_MOST_PLAYED_ID and launcherID == VLAUNCHER_MOST_PLAYED_ID:
            log_info('_command_run_rom() Launching ROM in Recently Played ROMs ...')
            recent_roms_list = fs_load_Collection_ROMs_JSON(RECENT_PLAYED_FILE_PATH)
            current_ROM_position = fs_collection_ROM_index_by_romID(romID, recent_roms_list)
            if current_ROM_position < 0:
                kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
                return
            rom = recent_roms_list[current_ROM_position]
            recent_rom = rom
            minimize_flag     = rom['minimize']
            non_blocking_flag = rom['non_blocking']
            romext            = rom['romext']
            standard_app      = rom['application']
            standard_args     = rom['args']
            args_extra        = rom['args_extra'] if 'args_extra' in rom else list()
        # --- ROM in Most played ROMs ---
        elif categoryID == VCATEGORY_RECENT_ID and launcherID == VLAUNCHER_RECENT_ID:
            log_info('_command_run_rom() Launching ROM in Most played ROMs ...')
            most_played_roms = fs_load_Favourites_JSON(MOST_PLAYED_FILE_PATH)
            rom = most_played_roms[romID]
            recent_rom = rom
            minimize_flag     = rom['minimize']
            non_blocking_flag = rom['non_blocking']
            romext            = rom['romext']
            standard_app      = rom['application']
            standard_args     = rom['args']
            args_extra        = rom['args_extra'] if 'args_extra' in rom else list()
        # --- ROM in Collection ---
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            log_info('_command_run_rom() Launching ROM in Collection ...')
            (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
            collection = collections[launcherID]
            roms_json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
            collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
            current_ROM_position = fs_collection_ROM_index_by_romID(romID, collection_rom_list)
            if current_ROM_position < 0:
                kodi_dialog_OK('Collection ROM not found in list. This is a bug!')
                return
            rom = collection_rom_list[current_ROM_position]
            recent_rom = rom
            minimize_flag     = rom['minimize']
            non_blocking_flag = rom['non_blocking']
            romext            = rom['romext']
            standard_app      = rom['application']
            standard_args     = rom['args']
            args_extra        = rom['args_extra'] if 'args_extra' in rom else list()
        # --- ROM in Virtual Launcher ---
        elif categoryID == VCATEGORY_TITLE_ID or categoryID == VCATEGORY_YEARS_ID or \
             categoryID == VCATEGORY_GENRE_ID or categoryID == VCATEGORY_DEVELOPER_ID or \
             categoryID == VCATEGORY_CATEGORY_ID:
            if categoryID == VCATEGORY_TITLE_ID:
                log_info('_command_run_rom() Launching ROM in Virtual Launcher ...')
                roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_TITLE_DIR, launcherID)
            elif categoryID == VCATEGORY_YEARS_ID:
                log_info('_command_run_rom() Launching ROM in Year Virtual Launcher ...')
                roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_YEARS_DIR, launcherID)
            elif categoryID == VCATEGORY_GENRE_ID:
                log_info('_command_run_rom() Launching ROM in Gender Virtual Launcher ...')
                roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_GENRE_DIR, launcherID)
            elif categoryID == VCATEGORY_DEVELOPER_ID:
                log_info('_command_run_rom() Launching ROM in Developer Virtual Launcher ...')
                roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_DEVELOPER_DIR, launcherID)
            elif categoryID == VCATEGORY_CATEGORY_ID:
                log_info('_command_run_rom() Launching ROM in Category Virtual Launcher ...')
                roms = fs_load_VCategory_ROMs_JSON(VIRTUAL_CAT_CATEGORY_DIR, launcherID)

            rom = roms[romID]
            recent_rom = rom
            minimize_flag     = rom['minimize']
            non_blocking_flag = rom['non_blocking']
            romext            = rom['romext']
            standard_app      = rom['application']
            standard_args     = rom['args']
            args_extra        = rom['args_extra'] if 'args_extra' in rom else list()
        # --- ROM in standard ROM launcher ---
        else:
            log_info('_command_run_rom() Launching ROM in Launcher ...')
            # --- Check launcher is OK and load ROMs ---
            if launcherID not in self.launchers:
                kodi_dialog_OK('launcherID not found in self.launchers')
                return
            launcher = self.launchers[launcherID]
            roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)
            # --- Check ROM is in XML data just read ---
            if romID not in roms:
                kodi_dialog_OK('romID not in roms dictionary')
                return
            rom = roms[romID]
            recent_rom = fs_get_Favourite_from_ROM(rom, launcher)
            minimize_flag     = launcher['minimize']
            non_blocking_flag = launcher['non_blocking']
            romext            = launcher['romext']
            standard_app      = launcher['application']
            standard_args     = launcher['args']
            args_extra        = launcher['args_extra']

        # ~~~~~ Substitue altapp/altarg or additional arguments ~~~~~
        # >> If ROM has altapp configured, then use altapp/altarg
        # >> If Launcher has args_extra configured then show a dialog to the user to selec the
        # >> arguments to launch ROM.
        if rom['altapp'] or rom['altarg']:
            log_info('_command_run_rom() Using ROM altapp/altarg')
            application = rom['altapp'] if rom['altapp'] else standard_app
            arguments   = rom['altarg'] if rom['altarg'] else standard_args
        elif args_extra:
            # >> Ask user what arguments to launch application
            log_info('_command_run_rom() Using Launcher args_extra')
            arg_list = [standard_args] + args_extra
            dialog = xbmcgui.Dialog()
            dselect_ret = dialog.select('Select launcher arguments', arg_list)
            if dselect_ret < 0: return
            log_info('_command_run_rom() User chose args index {0} ({1})'.format(dselect_ret, arg_list[dselect_ret]))
            application = standard_app
            arguments   = arg_list[dselect_ret]
        else:
            log_info('_command_run_rom() Using Launcher standard arguments')
            application = standard_app
            arguments   = standard_args

        # ~~~ Choose file to launch in multidisc ROM sets ~~~
        if rom['disks']:
            log_info('_command_run_rom() Multidisc ROM set detected')
            dialog = xbmcgui.Dialog()
            dselect_ret = dialog.select('Select ROM to launch in multidisc set', rom['disks'])
            if dselect_ret < 0: return
            selected_rom_base = rom['disks'][dselect_ret]
            log_info('_command_run_rom() Selected ROM "{0}"'.format(selected_rom_base))
            ROM_temp = FileName(rom['filename'])
            ROM_dir = FileName(ROM_temp.getDir())
            ROMFileName = ROM_dir.pjoin(selected_rom_base)
        else:
            log_info('_command_run_rom() Sigle ROM detected (no multidisc)')
            ROMFileName = FileName(rom['filename'])
        log_info('_command_run_rom() ROMFileName OP "{0}"'.format(ROMFileName.getOriginalPath()))
        log_info('_command_run_rom() ROMFileName  P "{0}"'.format(ROMFileName.getPath()))

        # ~~~~~ Launch ROM ~~~~~
        application   = FileName(application)
        apppath       = application.getDir()
        rompath       = ROMFileName.getDir()
        rombase       = ROMFileName.getBase()
        rombase_noext = ROMFileName.getBase_noext()
        romtitle      = rom['m_name']
        log_info('_command_run_rom() categoryID   {0}'.format(categoryID))
        log_info('_command_run_rom() launcherID   {0}'.format(launcherID))
        log_info('_command_run_rom() romID        {0}'.format(romID))
        log_info('_command_run_rom() romfile      "{0}"'.format(ROMFileName.getPath()))
        log_info('_command_run_rom() rompath      "{0}"'.format(rompath))
        log_info('_command_run_rom() rombase      "{0}"'.format(rombase))
        log_info('_command_run_rom() rombasenoext "{0}"'.format(rombase_noext))
        log_info('_command_run_rom() romtitle     "{0}"'.format(romtitle))
        log_info('_command_run_rom() application  "{0}"'.format(application.getPath()))
        log_info('_command_run_rom() apppath      "{0}"'.format(apppath))
        log_info('_command_run_rom() romext       "{0}"'.format(romext))

        # --- Check for errors and abort if found --- todo: CHECK
        if not application.exists() and (
            application.getOriginalPath() != RETROPLAYER_LAUNCHER_APP_NAME and
            application.getOriginalPath() != LNK_LAUNCHER_APP_NAME ):
            log_error('Launching app not found "{0}"'.format(application.getPath()))
            kodi_notify_warn('Launching app not found {0}'.format(application.getOriginalPath()))
            return
        else:
            log_info('Launching app found "{0}"'.format(application.getPath()))

        if not ROMFileName.exists():
            log_error('ROM not found "{0}"'.format(ROMFileName.getPath()))
            kodi_notify_warn('ROM not found "{0}"'.format(ROMFileName.getOriginalPath()))
            return
        else:
            log_info('ROM found "{0}"'.format(ROMFileName.getPath()))

        # --- Escape quotes and double quotes in ROMFileName ---
        # >> This maybe useful to Android users with complex command line arguments
        if self.settings['escape_romfile']:
            log_info("_command_run_rom() Escaping ROMFileName ' and \"")
            ROMFileName.escapeQuotes()

        # ~~~~ Argument substitution ~~~~~
        log_info('_command_run_rom() raw arguments   "{0}"'.format(arguments))
        arguments = arguments.replace('$categoryID$', categoryID)
        arguments = arguments.replace('$launcherID$', launcherID)
        arguments = arguments.replace('$romID$', romID)
        arguments = arguments.replace('$rom$', ROMFileName.getPath())
        arguments = arguments.replace('$romfile$', ROMFileName.getPath())
        arguments = arguments.replace('$rompath$', rompath)
        arguments = arguments.replace('$rombase$', rombase)
        arguments = arguments.replace('$rombasenoext$', rombase_noext)
        arguments = arguments.replace('$romtitle$', romtitle)
        arguments = arguments.replace('$apppath$', apppath)
        # >> Legacy names for argument substitution
        arguments = arguments.replace('%rom%', ROMFileName.getPath())
        arguments = arguments.replace('%ROM%', ROMFileName.getPath())
        log_info('_command_run_rom() final arguments "{0}"'.format(arguments))

        # --- Compute ROM recently played list ---
        MAX_RECENT_PLAYED_ROMS = 100
        recent_roms_list = fs_load_Collection_ROMs_JSON(RECENT_PLAYED_FILE_PATH)
        recent_roms_list = [rom for rom in recent_roms_list if rom['id'] != recent_rom['id']]
        recent_roms_list.insert(0, recent_rom)
        if len(recent_roms_list) > MAX_RECENT_PLAYED_ROMS:
            log_debug('_command_run_rom() len(recent_roms_list) = {0}'.format(len(recent_roms_list)))
            log_debug('_command_run_rom() Trimming list to {0} ROMs'.format(MAX_RECENT_PLAYED_ROMS))
            temp_list        = recent_roms_list[:MAX_RECENT_PLAYED_ROMS]
            recent_roms_list = temp_list
        fs_write_Collection_ROMs_JSON(RECENT_PLAYED_FILE_PATH, recent_roms_list)

        # --- Compute most played ROM statistics ---
        most_played_roms = fs_load_Favourites_JSON(MOST_PLAYED_FILE_PATH)
        if recent_rom['id'] in most_played_roms:
            rom_id = recent_rom['id']
            most_played_roms[rom_id]['launch_count'] += 1
        else:
            # >> Add field launch_count to recent_rom to count how many times have been launched.
            recent_rom['launch_count'] = 1
            most_played_roms[recent_rom['id']] = recent_rom
        fs_write_Favourites_JSON(MOST_PLAYED_FILE_PATH, most_played_roms)

        # --- Execute Kodi Retroplayer if launcher configured to do so ---
        # See https://github.com/Wintermute0110/plugin.program.advanced.emulator.launcher/issues/33
        # See https://forum.kodi.tv/showthread.php?tid=295463&pid=2620489#pid2620489
        if application.getOriginalPath() == RETROPLAYER_LAUNCHER_APP_NAME:
            log_info('_command_run_rom() Executing ROM with Kodi Retroplayer ...')
            # >> Create listitem object
            label_str = ROMFileName.getBase()
            listitem = xbmcgui.ListItem(label = label_str, label2 = label_str)
            # >> Listitem metadata
            # >> How to fill gameclient = string (game.libretro.fceumm) ???
            genre_list = list(rom['m_genre'])
            listitem.setInfo('game', {'title'    : label_str,     'platform'  : 'Test platform',
                                      'genres'   : genre_list,    'developer' : rom['m_developer'],
                                      'overview' : rom['m_plot'], 'year'      : rom['m_year'] })
            log_info('_command_run_rom() application.getOriginalPath() "{0}"'.format(application.getOriginalPath()))
            log_info('_command_run_rom() ROMFileName.getPath()         "{0}"'.format(ROMFileName.getPath()))
            log_info('_command_run_rom() label_str                     "{0}"'.format(label_str))

            # --- User notification ---
            if self.settings['display_launcher_notify']:
                kodi_notify('Launching "{0}" with Retroplayer'.format(romtitle))

            log_verb('_command_run_rom() Calling xbmc.Player().play() ...')
            xbmc.Player().play(ROMFileName.getPath(), listitem)
            log_verb('_command_run_rom() Calling xbmc.Player().play() returned. Leaving function.')
        else:
            log_info('_command_run_rom() Launcher is not Kodi Retroplayer.')
            self._run_before_execution(romtitle, minimize_flag)
            self._run_process(application.getPath(), arguments, apppath, romext, non_blocking_flag)
            self._run_after_execution(minimize_flag)

    #
    # Launchs a ROM launcher or standalone launcher
    # For standalone launchers romext is the extension of the application (only used in Windoze)
    #
    def _run_process(self, application, arguments, apppath, romext, non_blocking_flag):
        import shlex
        import subprocess

        # >> Determine platform and launch application
        # >> See http://stackoverflow.com/questions/446209/possible-values-from-sys-platform

        # >> Decompose arguments to call subprocess module
        arg_list  = shlex.split(arguments, posix = True)
        exec_list = [application] + arg_list
        log_debug('_run_process() arguments = "{0}"'.format(arguments))
        log_debug('_run_process() arg_list  = {0}'.format(arg_list))
        log_debug('_run_process() exec_list = {0}'.format(exec_list))

        # >> Windoze
        # NOTE subprocess24_hack.py was hacked to always set CreateProcess() bInheritHandles to 0.
        # bInheritHandles [in] If this parameter TRUE, each inheritable handle in the calling 
        # process is inherited by the new process. If the parameter is FALSE, the handles are not 
        # inherited. Note that inherited handles have the same value and access rights as the original handles.
        # See https://msdn.microsoft.com/en-us/library/windows/desktop/ms682425(v=vs.85).aspx
        #
        # Same behaviour can be achieved in current version of subprocess with close_fds.
        # If close_fds is true, all file descriptors except 0, 1 and 2 will be closed before the 
        # child process is executed. (Unix only). Or, on Windows, if close_fds is true then no handles 
        # will be inherited by the child process. Note that on Windows, you cannot set close_fds to 
        # true and also redirect the standard handles by setting stdin, stdout or stderr.
        #
        # If I keep old launcher behaviour in Windows (close_fds = True) then program output cannot
        # be redirected to a file.
        #
        if sys.platform == 'win32':
            app_ext = application.split('.')[-1]
            log_debug('_run_process() (Windows) application = "{0}"'.format(application))
            log_debug('_run_process() (Windows) arguments   = "{0}"'.format(arguments))
            log_debug('_run_process() (Windows) apppath     = "{0}"'.format(apppath))
            log_debug('_run_process() (Windows) romext      = "{0}"'.format(romext))
            log_debug('_run_process() (Windows) app_ext     = "{0}"'.format(app_ext))
            # >> Standalone launcher where application is a LNK file
            if app_ext == 'lnk' or app_ext == 'LNK':
                log_debug('_run_process() (Windows) Launching LNK application')
                # os.system('start "AEL" /b "{0}"'.format(application).encode('utf-8'))
                retcode = subprocess.call('start "AEL" /b "{0}"'.format(application).encode('utf-8'), shell = True)
                log_info('_run_process() (Windows) LNK app retcode = {0}'.format(retcode))

            # >> ROM launcher where ROMs are LNK files
            elif romext == 'lnk' or romext == 'LNK':
                log_debug('_run_process() (Windows) Launching LNK ROM')
                # os.system('start "AEL" /b "{0}"'.format(arguments).encode('utf-8'))
                retcode = subprocess.call('start "AEL" /b "{0}"'.format(arguments).encode('utf-8'), shell = True)
                log_info('_run_process() (Windows) LNK ROM retcode = {0}'.format(retcode))

            # >> CMD/BAT files in Windows
            elif app_ext == 'bat' or app_ext == 'BAT':
                log_debug('_run_process() (Windows) Launching BAT application')
                log_debug('_run_process() (Windows) Ignoring setting windows_cd_apppath')
                log_debug('_run_process() (Windows) Ignoring setting windows_close_fds')
                log_debug('_run_process() (Windows) show_batch_window = {0}'.format(self.settings['show_batch_window']))
                info = subprocess.STARTUPINFO()
                info.dwFlags = 1
                info.wShowWindow = 5 if self.settings['show_batch_window'] else 0
                retcode = subprocess.call(exec_list, cwd = apppath.encode('utf-8'), close_fds = True, startupinfo = info)
                log_info('_run_process() (Windows) Process BAR retcode = {0}'.format(retcode))

            else:
                # --- Workaround to run UNC paths in Windows ---
                # >> Retroarch now support ROMs in UNC paths (Samba remotes)
                new_exec_list = list(exec_list)
                for i, _ in enumerate(exec_list):
                    if exec_list[i][0] == '\\':
                        new_exec_list[i] = '\\' + exec_list[i]
                        log_debug('_run_process() (Windows) Before arg #{0} = "{1}"'.format(i, exec_list[i]))
                        log_debug('_run_process() (Windows) Now    arg #{0} = "{1}"'.format(i, new_exec_list[i]))
                exec_list = list(new_exec_list)
                log_debug('_run_process() (Windows) exec_list = {0}'.format(exec_list))

                # >> cwd = apppath.encode('utf-8') fails if application path has Unicode on Windows
                # >> A workaraound is to use cwd = apppath.encode(sys.getfilesystemencoding()) --> DOES NOT WORK
                # >> For the moment AEL cannot launch executables on Windows having Unicode paths.
                windows_cd_apppath = self.settings['windows_cd_apppath']
                windows_close_fds  = self.settings['windows_close_fds']
                log_debug('_run_process() (Windows) Launching regular application')
                log_debug('_run_process() (Windows) windows_cd_apppath = {0}'.format(windows_cd_apppath))
                log_debug('_run_process() (Windows) windows_close_fds  = {0}'.format(windows_close_fds))
                # >>  Note that on Windows, you cannot set close_fds to true and also redirect the 
                # >> standard handles by setting stdin, stdout or stderr.
                if windows_cd_apppath and windows_close_fds:
                    retcode = subprocess.call(exec_list, cwd = apppath.encode('utf-8'), close_fds = True)
                elif windows_cd_apppath and not windows_close_fds:
                    with open(LAUNCH_LOG_FILE_PATH.getPath(), 'w') as f:
                        retcode = subprocess.call(exec_list, cwd = apppath.encode('utf-8'), close_fds = False,
                                                  stdout = f, stderr = subprocess.STDOUT)
                elif not windows_cd_apppath and windows_close_fds:
                    retcode = subprocess.call(exec_list, close_fds = True)
                elif not windows_cd_apppath and not windows_close_fds:
                    with open(LAUNCH_LOG_FILE_PATH.getPath(), 'w') as f:
                        retcode = subprocess.call(exec_list, close_fds = False,
                                                  stdout = f, stderr = subprocess.STDOUT)
                else:
                    raise Exception('Logical error')
                log_info('_run_process() (Windows) Process retcode = {0}'.format(retcode))

        # >> Linux and Android
        # >> New in 0.9.7: always close all file descriptions except 0, 1 and 2 on the child
        # >> process. This is to avoid Kodi opens sockets be inherited by the child process. A
        # >> wrapper script may terminate Kodi using JSON RPC and if file descriptors are not
        # >> closed Kodi will complain that the remote interfacte cannot be initialised. I believe
        # >> the cause is that the socket is kept open by the wrapper script.
        elif sys.platform.startswith('linux'):
            # >> Old way of launching child process. os.system() is deprecated and should not
            # >> be used anymore.
            # os.system('"{0}" {1}'.format(application, arguments).encode('utf-8'))

            # >> New way of launching, uses subproces module. Also, save child process stdout.
            if non_blocking_flag:
                # >> In a non-blocking launch stdout/stderr of child process cannot be recorded.
                log_info('_run_process() (Linux) Launching non-blocking process subprocess.Popen()')
                p = subprocess.Popen(exec_list, close_fds = True)
            else:
                if self.settings['lirc_state']: xbmc.executebuiltin('LIRC.stop')
                log_info('_run_process() (Linux) Launching blocking process subprocess.call()')
                with open(LAUNCH_LOG_FILE_PATH.getPath(), 'w') as f:
                    retcode = subprocess.call(exec_list, stdout = f, stderr = subprocess.STDOUT, close_fds = True)
                log_info('_run_process() Process retcode = {0}'.format(retcode))
                if self.settings['lirc_state']: xbmc.executebuiltin('LIRC.start')

        # >> OS X
        elif sys.platform.startswith('darwin'):
            # >> Old way
            # os.system('"{0}" {1}'.format(application, arguments).encode('utf-8'))
            
            # >> New way.
            with open(LAUNCH_LOG_FILE_PATH.getPath(), 'w') as f:
                retcode = subprocess.call(exec_list, stdout = f, stderr = subprocess.STDOUT)
            log_info('_run_process() Process retcode = {0}'.format(retcode))

        else:
            kodi_notify_warn('Cannot determine the running platform')

    #
    # These two functions do things like stopping music before lunch, toggling full screen, etc.
    # Variables set in this function:
    # self.kodi_was_playing      True if Kodi player was ON, False otherwise
    # self.kodi_audio_suspended  True if Kodi audio suspended before launching
    #
    def _run_before_execution(self, rom_title, toggle_screen_flag):
        # --- User notification ---
        if self.settings['display_launcher_notify']:
            kodi_notify('Launching {0}'.format(rom_title))

        # --- Stop/Pause Kodi mediaplayer if requested in settings ---
        self.kodi_was_playing = False
        # id="media_state_action" default="0" values="Stop|Pause|Let Play"
        media_state_action = self.settings['media_state_action']
        media_state_str = ['Stop', 'Pause', 'Let Play'][media_state_action]
        log_verb('_run_before_execution() media_state_action is "{0}" ({1})'.format(media_state_str, media_state_action))
        if media_state_action == 0 and xbmc.Player().isPlaying():
            log_verb('_run_before_execution() Calling xbmc.Player().stop()')
            xbmc.Player().stop()
            xbmc.sleep(100)
            self.kodi_was_playing = True
        elif media_state_action == 1 and xbmc.Player().isPlaying():
            log_verb('_run_before_execution() Calling xbmc.Player().pause()')
            xbmc.Player().pause()
            xbmc.sleep(100)
            self.kodi_was_playing = True

        # --- Force audio suspend if requested in "Settings" --> "Advanced"
        # >> See http://forum.kodi.tv/showthread.php?tid=164522
        self.kodi_audio_suspended = False
        if self.settings['suspend_audio_engine']:
            log_verb('_run_before_execution() Suspending Kodi audio engine')
            xbmc.audioSuspend()
            xbmc.enableNavSounds(False)
            xbmc.sleep(100)
            self.kodi_audio_suspended = True
        else:
            log_verb('_run_before_execution() DO NOT suspend Kodi audio engine')

        # --- Force joystick suspend if requested in "Settings" --> "Advanced"
        # >> See https://forum.kodi.tv/showthread.php?tid=287826&pid=2627128#pid2627128
        # >> See https://forum.kodi.tv/showthread.php?tid=157499&pid=1722549&highlight=input.enablejoystick#pid1722549
        # >> See https://forum.kodi.tv/showthread.php?tid=313615
        self.kodi_joystick_suspended = False
        # if self.settings['suspend_joystick_engine']:
            # log_verb('_run_before_execution() Suspending Kodi joystick engine')
            # >> Research. Get the value of the setting first
            # >> Apparently input.enablejoystick is not supported on Kodi Krypton anymore.
            # c_str = ('{"id" : 1, "jsonrpc" : "2.0",'
            #          ' "method" : "Settings.GetSettingValue",'
            #          ' "params" : {"setting":"input.enablejoystick"}}')
            # response = xbmc.executeJSONRPC(c_str)
            # log_debug('JSON      ''{0}'''.format(c_str))
            # log_debug('Response  ''{0}'''.format(response))

            # c_str = ('{"id" : 1, "jsonrpc" : "2.0",'
            #          ' "method" : "Settings.SetSettingValue",'
            #          ' "params" : {"setting" : "input.enablejoystick", "value" : false} }')
            # response = xbmc.executeJSONRPC(c_str)
            # log_debug('JSON      ''{0}'''.format(c_str))
            # log_debug('Response  ''{0}'''.format(response))
            # self.kodi_joystick_suspended = True

            # log_error('_run_before_execution() Suspending Kodi joystick engine not supported on Kodi Krypton!')
        # else:
            # log_verb('_run_before_execution() DO NOT suspend Kodi joystick engine')

        # --- Toggle Kodi windowed/fullscreen if requested ---
        if toggle_screen_flag:
            log_verb('_run_before_execution() Toggling Kodi fullscreen')
            kodi_toogle_fullscreen()
        else:
            log_verb('_run_before_execution() Toggling Kodi fullscreen DEACTIVATED in Launcher')

        # --- Pause Kodi execution some time ---
        delay_tempo_ms = self.settings['delay_tempo']
        log_verb('_run_before_execution() Pausing {0} ms'.format(delay_tempo_ms))
        xbmc.sleep(delay_tempo_ms)
        log_debug('_run_before_execution() function ENDS')

    def _run_after_execution(self, toggle_screen_flag):
        # --- Stop Kodi some time ---
        delay_tempo_ms = self.settings['delay_tempo']
        log_verb('_run_after_execution() Pausing {0} ms'.format(delay_tempo_ms))
        xbmc.sleep(delay_tempo_ms)

        # --- Toggle Kodi windowed/fullscreen if requested ---
        if toggle_screen_flag:
            log_verb('_run_after_execution() Toggling Kodi fullscreen')
            kodi_toogle_fullscreen()
        else:
            log_verb('_run_after_execution() Toggling Kodi fullscreen DEACTIVATED in Launcher')

        # --- Resume audio engine if it was suspended ---
        # Calling xmbc.audioResume() takes a loong time (2/4 secs) if audio was not properly suspended!
        # Also produces this in Kodi's log:
        # WARNING: CActiveAE::StateMachine - signal: 0 from port: OutputControlPort not handled for state: 7
        #   ERROR: ActiveAE::Resume - failed to init
        if self.kodi_audio_suspended:
            log_verb('_run_after_execution() Kodi audio engine was suspended before launching')
            log_verb('_run_after_execution() Resuming Kodi audio engine')
            xbmc.audioResume()
            xbmc.enableNavSounds(True)
            xbmc.sleep(100)
        else:
            log_verb('_run_after_execution() DO NOT resume Kodi audio engine')

        # --- Resume joystick engine if it was suspended ---
        if self.kodi_joystick_suspended:
            log_verb('_run_after_execution() Kodi joystick engine was suspended before launching')
            log_verb('_run_after_execution() Resuming Kodi joystick engine')
            # response = xbmc.executeJSONRPC(c_str)
            # log_debug('JSON      ''{0}'''.format(c_str))
            # log_debug('Response  ''{0}'''.format(response))
            log_verb('_run_before_execution() Not supported on Kodi Krypton!')
        else:
            log_verb('_run_after_execution() DO NOT resume Kodi joystick engine')

        # --- Resume Kodi playing if it was paused. If it was stopped, keep it stopped. ---
        media_state_action = self.settings['media_state_action']
        media_state_str = ['Stop', 'Pause', 'Let Play'][media_state_action]
        log_verb('_run_after_execution() media_state_action is "{0}" ({1})'.format(media_state_str, media_state_action))
        log_verb('_run_after_execution() self.kodi_was_playing is {0}'.format(self.kodi_was_playing))
        if self.kodi_was_playing and media_state_action == 1:
            log_verb('_run_after_execution() Calling xbmc.Player().play()')
            xbmc.Player().play()
        log_debug('_run_after_execution() function ENDS')

    #
    # Check if Launcher reports must be created/regenrated
    #
    def _roms_regenerate_launcher_reports(self, categoryID, launcherID, roms):
        # --- Get report filename ---
        if categoryID in self.categories: category_name = self.categories[categoryID]['m_name']
        else:                             category_name = VCATEGORY_ADDONROOT_ID
        roms_base_noext  = fs_get_ROMs_basename(category_name, self.launchers[launcherID]['m_name'], launcherID)
        report_stats_FN  = REPORTS_DIR.pjoin(roms_base_noext + '_stats.txt')
        log_verb('_command_view_menu() Stats  OP "{0}"'.format(report_stats_FN.getOriginalPath()))

        # --- If report doesn't exists create it automatically ---
        log_debug('_command_view_Launcher_Report() Testing report file "{0}"'.format(report_stats_FN.getPath()))
        if not report_stats_FN.exists():
            kodi_dialog_OK('Report file not found. Will be generated now.')
            self._roms_create_launcher_reports(categoryID, launcherID, roms)
            # >> Update report timestamp
            self.launchers[launcherID]['timestamp_report'] = time.time()
            # >> Save Categories/Launchers
            # >> DO NOT update the timestamp of categories/launchers of report will always be obsolete!!!
            # >> Keep same timestamp as before.
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers, self.update_timestamp)

        # --- If report timestamp is older than launchers last modification, recreate it ---
        if self.launchers[launcherID]['timestamp_report'] <= self.launchers[launcherID]['timestamp_launcher']:
            kodi_dialog_OK('Report is outdated. Will be regenerated now.')
            self._roms_create_launcher_reports(categoryID, launcherID, roms)
            self.launchers[launcherID]['timestamp_report'] = time.time()
            fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers, self.update_timestamp)

    #
    # Creates a Launcher report having:
    #  1) Launcher statistics
    #  2) Report of ROM metadata
    #  3) Report of ROM artwork
    #  4) If No-Intro file, then No-Intro audit information.
    #
    def _roms_create_launcher_reports(self, categoryID, launcherID, roms):
        ROM_NAME_LENGHT = 50

        # >> Report file name
        if categoryID in self.categories: category_name = self.categories[categoryID]['m_name']
        else:                             category_name = VCATEGORY_ADDONROOT_ID
        launcher = self.launchers[launcherID]
        roms_base_noext  = fs_get_ROMs_basename(category_name, launcher['m_name'], launcherID)
        report_stats_FN  = REPORTS_DIR.pjoin(roms_base_noext + '_stats.txt')
        report_meta_FN   = REPORTS_DIR.pjoin(roms_base_noext + '_metadata.txt')
        report_assets_FN = REPORTS_DIR.pjoin(roms_base_noext + '_assets.txt')
        log_verb('_roms_create_launcher_reports() Stats  OP "{0}"'.format(report_stats_FN.getOriginalPath()))
        log_verb('_roms_create_launcher_reports() Meta   OP "{0}"'.format(report_meta_FN.getOriginalPath()))
        log_verb('_roms_create_launcher_reports() Assets OP "{0}"'.format(report_assets_FN.getOriginalPath()))
        roms_base_noext = fs_get_ROMs_basename(category_name, launcher['m_name'], launcherID)
        report_file_name = REPORTS_DIR.pjoin(roms_base_noext + '.txt')
        log_verb('_roms_create_launcher_reports() Report filename "{0}"'.format(report_file_name.getOriginalPath()))

        # >> Step 1: Build report data
        num_roms = len(roms)
        missing_m_year      = missing_m_genre    = missing_m_developer = missing_m_nplayers  = 0
        missing_m_esrb      = missing_m_rating   = missing_m_plot      = 0
        missing_s_title     = missing_s_snap     = missing_s_fanart    = missing_s_banner    = 0
        missing_s_clearlogo = missing_s_boxfront = missing_s_boxback   = missing_s_cartridge = 0
        missing_s_flyer     = missing_s_map      = missing_s_manual    = missing_s_trailer   = 0
        audit_none = audit_have = audit_miss = audit_unknown = 0
        audit_num_parents = audit_num_clones = 0
        check_list = []
        path_title_P = FileName(launcher['path_title']).getPath()
        path_snap_P = FileName(launcher['path_snap']).getPath()
        path_boxfront_P = FileName(launcher['path_boxfront']).getPath()
        path_boxback_P = FileName(launcher['path_boxback']).getPath()
        path_cartridge_P = FileName(launcher['path_cartridge']).getPath()
        for rom_id in sorted(roms, key = lambda x : roms[x]['m_name']):
            rom = roms[rom_id]
            rom_info = {}
            rom_info['m_name'] = rom['m_name']
            rom_info['m_nointro_status'] = rom['nointro_status']
            rom_info['m_pclone_status'] = rom['pclone_status']
            # --- Metadata ---
            if rom['m_year']:                 rom_info['m_year']      = 'YES'
            else:                             rom_info['m_year']      = '---'; missing_m_year += 1
            if rom['m_genre']:                rom_info['m_genre']     = 'YES'
            else:                             rom_info['m_genre']     = '---'; missing_m_genre += 1
            if rom['m_developer']:            rom_info['m_developer'] = 'YES'
            else:                             rom_info['m_developer'] = '---'; missing_m_developer += 1
            if rom['m_nplayers']:             rom_info['m_nplayers']  = 'YES'
            else:                             rom_info['m_nplayers']  = '---'; missing_m_nplayers += 1
            if rom['m_esrb'] == ESRB_PENDING: rom_info['m_esrb']      = '---'; missing_m_esrb += 1
            else:                             rom_info['m_studio']    = 'YES'
            if rom['m_rating']:               rom_info['m_rating']    = 'YES'
            else:                             rom_info['m_rating']    = '---'; missing_m_rating += 1
            if rom['m_plot']:                 rom_info['m_plot']      = 'YES'
            else:                             rom_info['m_plot']      = '---'; missing_m_plot += 1
            # --- Assets ---
            # >> Y means the asset exists and has the Base_noext of the ROM.
            # >> S means the asset exists and is a PClone group substitution.
            # >> C means the asset exists and is a user customised asset.
            # >> X means the asset exists, getDir() is same but Base_noext() is different
            # path_* and art getDir() different ==> Custom asset (user customised it) C
            # path_* and art getDir() equal and Base_noext() equal ==> Own artwork Y
            # path_* and art getDir() equal and Base_noext() different ==> Maybe S or maybe C => O
            # To differentiate between S and C a test in the PClone group must be done.
            #
            romfile_FN = FileName(rom['filename'])
            romfile_getBase_noext = romfile_FN.getBase_noext()
            if rom['s_title']:
                rom_info['s_title'] = self._aux_get_info(FileName(rom['s_title']), path_title_P, romfile_getBase_noext)
            else:
                rom_info['s_title'] = '-'
                missing_s_title += 1
            if rom['s_snap']:
                rom_info['s_snap'] = self._aux_get_info(FileName(rom['s_snap']), path_snap_P, romfile_getBase_noext)
            else:
                rom_info['s_snap'] = '-'
                missing_s_snap += 1
            if rom['s_boxfront']:
                rom_info['s_boxfront'] = self._aux_get_info(FileName(rom['s_boxfront']), path_boxfront_P, romfile_getBase_noext)
            else:
                rom_info['s_boxfront'] = '-'
                missing_s_boxfront += 1
            if rom['s_boxback']:
                rom_info['s_boxback'] = self._aux_get_info(FileName(rom['s_boxback']), path_boxback_P, romfile_getBase_noext)
            else:
                rom_info['s_boxback'] = '-'
                missing_s_boxback += 1
            if rom['s_cartridge']:
                rom_info['s_cartridge'] = self._aux_get_info(FileName(rom['s_cartridge']), path_cartridge_P, romfile_getBase_noext)
            else:                  
                rom_info['s_cartridge'] = '-'
                missing_s_cartridge += 1
            if rom['s_fanart']:    rom_info['s_fanart']    = 'Y'
            else:                  rom_info['s_fanart']    = '-'; missing_s_fanart += 1
            if rom['s_banner']:    rom_info['s_banner']    = 'Y'
            else:                  rom_info['s_banner']    = '-'; missing_s_banner += 1
            if rom['s_clearlogo']: rom_info['s_clearlogo'] = 'Y'
            else:                  rom_info['s_clearlogo'] = '-'; missing_s_clearlogo += 1
            if rom['s_flyer']:     rom_info['s_flyer']     = 'Y'
            else:                  rom_info['s_flyer']     = '-'; missing_s_flyer += 1
            if rom['s_map']:       rom_info['s_map']       = 'Y'
            else:                  rom_info['s_map']       = '-'; missing_s_map += 1
            if rom['s_manual']:    rom_info['s_manual']    = 'Y'
            else:                  rom_info['s_manual']    = '-'; missing_s_manual += 1
            if rom['s_trailer']:   rom_info['s_trailer']   = 'Y'
            else:                  rom_info['s_trailer']   = '-'; missing_s_trailer += 1
            # --- ROM audit ---
            if   rom['nointro_status'] == NOINTRO_STATUS_NONE:    audit_none += 1
            elif rom['nointro_status'] == NOINTRO_STATUS_HAVE:    audit_have += 1
            elif rom['nointro_status'] == NOINTRO_STATUS_MISS:    audit_miss += 1
            elif rom['nointro_status'] == NOINTRO_STATUS_UNKNOWN: audit_unknown += 1
            else:
                log_error('Unknown audit status {0}.'.format(rom['nointro_status']))
                kodi_dialog_OK('Unknown audit status {0}. This is a bug, please report it.'.format(rom['nointro_status']))
                return
            if   rom['pclone_status'] == PCLONE_STATUS_PARENT: audit_num_parents += 1
            elif rom['pclone_status'] == PCLONE_STATUS_CLONE:  audit_num_clones += 1
            elif rom['pclone_status'] == PCLONE_STATUS_NONE:   pass
            else:
                log_error('Unknown pclone status {0}.'.format(rom['pclone_status']))
                kodi_dialog_OK('Unknown pclone status {0}. This is a bug, please report it.'.format(rom['pclone_status']))
                return

            # >> Add to list
            check_list.append(rom_info)

        # >> Math
        have_m_year = num_roms - missing_m_year
        have_m_genre = num_roms - missing_m_genre
        have_m_developer = num_roms - missing_m_developer
        have_m_nplayers = num_roms - missing_m_nplayers
        have_m_esrb = num_roms - missing_m_esrb
        have_m_rating = num_roms - missing_m_rating
        have_m_plot = num_roms - missing_m_plot

        have_s_year_pcent = float(have_m_year*100) / num_roms
        have_s_genre_pcent = float(have_m_genre*100) / num_roms
        have_s_developer_pcent = float(have_m_developer*100) / num_roms
        have_s_nplayers_pcent = float(have_m_nplayers*100) / num_roms
        have_s_esrb_pcent = float(have_m_esrb*100) / num_roms
        have_s_rating_pcent = float(have_m_rating*100) / num_roms
        have_s_plot_pcent = float(have_m_plot*100) / num_roms

        miss_s_year_pcent = float(missing_m_year*100) / num_roms
        miss_s_genre_pcent = float(missing_m_genre*100) / num_roms
        miss_s_developer_pcent = float(missing_m_developer*100) / num_roms
        miss_s_nplayers_pcent = float(missing_m_nplayers*100) / num_roms
        miss_s_esrb_pcent = float(missing_m_esrb*100) / num_roms
        miss_s_rating_pcent = float(missing_m_rating*100) / num_roms
        miss_s_plot_pcent = float(missing_m_plot*100) / num_roms

        have_s_title = num_roms - missing_s_title
        have_s_snap = num_roms - missing_s_snap
        have_s_boxfront = num_roms - missing_s_boxfront
        have_s_boxback = num_roms - missing_s_boxback
        have_s_cartridge = num_roms - missing_s_cartridge
        have_s_fanart = num_roms - missing_s_fanart
        have_s_banner = num_roms - missing_s_banner
        have_s_clearlogo = num_roms - missing_s_clearlogo
        have_s_flyer = num_roms - missing_s_flyer
        have_s_map = num_roms - missing_s_map
        have_s_manual = num_roms - missing_s_manual
        have_s_trailer = num_roms - missing_s_trailer

        miss_s_title_pcent = float(missing_s_title*100) / num_roms
        miss_s_snap_pcent = float(missing_s_snap*100) / num_roms
        miss_s_boxfront_pcent = float(missing_s_boxfront*100) / num_roms
        miss_s_boxback_pcent = float(missing_s_boxback*100) / num_roms
        miss_s_cartridge_pcent = float(missing_s_cartridge*100) / num_roms
        miss_s_fanart_pcent = float(missing_s_fanart*100) / num_roms
        miss_s_banner_pcent = float(missing_s_banner*100) / num_roms
        miss_s_clearlogo_pcent = float(missing_s_clearlogo*100) / num_roms
        miss_s_flyer_pcent = float(missing_s_flyer*100) / num_roms
        miss_s_map_pcent = float(missing_s_map*100) / num_roms
        miss_s_manual_pcent = float(missing_s_manual*100) / num_roms
        miss_s_trailer_pcent = float(missing_s_trailer*100) / num_roms

        # --- Step 2: Statistics report ---
        # >> Launcher name printed on window title
        # >> Audit statistics
        str_list = []
        str_list.append('<No-Intro Audit Statistics>\n')
        str_list.append('Number of ROMs   {0:5d}\n'.format(num_roms))
        str_list.append('Not checked ROMs {0:5d}\n'.format(audit_none))
        str_list.append('Have ROMs        {0:5d}\n'.format(audit_have))
        str_list.append('Missing ROMs     {0:5d}\n'.format(audit_miss))
        str_list.append('Unknown ROMs     {0:5d}\n'.format(audit_unknown))
        str_list.append('Parent           {0:5d}\n'.format(audit_num_parents))
        str_list.append('Clones           {0:5d}\n'.format(audit_num_clones))
        # >> Metadata
        str_list.append('\n<Metadata statistics>\n')
        str_list.append('Year      {0:5d} have {1:6.2f}% / {2:5d} miss {3:6.2f}%\n'.format(
            have_m_year, have_s_year_pcent, missing_m_year, miss_s_year_pcent))
        str_list.append('Genre     {0:5d} have {1:6.2f}% / {2:5d} miss {3:6.2f}%\n'.format(
            have_m_genre, have_s_genre_pcent, missing_m_genre, miss_s_genre_pcent))
        str_list.append('Developer {0:5d} have {1:6.2f}% / {2:5d} miss {3:6.2f}%\n'.format(
            have_m_developer, have_s_developer_pcent, missing_m_developer, miss_s_developer_pcent))
        str_list.append('NPlayers  {0:5d} have {1:6.2f}% / {2:5d} miss {3:6.2f}%\n'.format(
            have_m_nplayers, have_s_nplayers_pcent, missing_m_nplayers, miss_s_nplayers_pcent))
        str_list.append('ESRB      {0:5d} have {1:6.2f}% / {2:5d} miss {3:6.2f}%\n'.format(
            have_m_esrb, have_s_esrb_pcent, missing_m_esrb, miss_s_esrb_pcent))
        str_list.append('Rating    {0:5d} have {1:6.2f}% / {2:5d} miss {3:6.2f}%\n'.format(
            have_m_rating, have_s_rating_pcent, missing_m_rating, miss_s_rating_pcent))
        str_list.append('Plot      {0:5d} have {1:6.2f}% / {2:5d} miss {3:6.2f}%\n'.format(
            have_m_plot, have_s_plot_pcent, missing_m_plot, miss_s_plot_pcent))
        # >> Assets statistics
        str_list.append('\n<Asset statistics>\n')
        str_list.append('Title     {0:5d} have, {1:5d} miss  {2:6.2f}%\n'.format(have_s_title, missing_s_title, miss_s_title_pcent))
        str_list.append('Snap      {0:5d} have, {1:5d} miss  {2:6.2f}%\n'.format(have_s_snap, missing_s_snap, miss_s_snap_pcent))
        str_list.append('Boxfront  {0:5d} have, {1:5d} miss  {2:6.2f}%\n'.format(have_s_boxfront, missing_s_boxfront, miss_s_boxfront_pcent))
        str_list.append('Boxback   {0:5d} have, {1:5d} miss  {2:6.2f}%\n'.format(have_s_boxback, missing_s_boxback, miss_s_boxback_pcent))
        str_list.append('Cartridge {0:5d} have, {1:5d} miss  {2:6.2f}%\n'.format(have_s_cartridge, missing_s_cartridge, miss_s_cartridge_pcent))
        str_list.append('Fanart    {0:5d} have, {1:5d} miss  {2:6.2f}%\n'.format(have_s_fanart, missing_s_fanart, miss_s_fanart_pcent))
        str_list.append('Banner    {0:5d} have, {1:5d} miss  {2:6.2f}%\n'.format(have_s_banner, missing_s_banner, miss_s_banner_pcent))
        str_list.append('Clearlogo {0:5d} have, {1:5d} miss  {2:6.2f}%\n'.format(have_s_clearlogo, missing_s_clearlogo, miss_s_clearlogo_pcent))
        str_list.append('Flyer     {0:5d} have, {1:5d} miss  {2:6.2f}%\n'.format(have_s_flyer, missing_s_flyer, miss_s_flyer_pcent))
        str_list.append('Map       {0:5d} have, {1:5d} miss  {2:6.2f}%\n'.format(have_s_map, missing_s_map, miss_s_map_pcent))
        str_list.append('Manual    {0:5d} have, {1:5d} miss  {2:6.2f}%\n'.format(have_s_manual, missing_s_manual, miss_s_manual_pcent))
        str_list.append('Trailer   {0:5d} have, {1:5d} miss  {2:6.2f}%\n'.format(have_s_trailer, missing_s_trailer, miss_s_trailer_pcent))

        # >> Step 3: Metadata report
        str_meta_list = []
        str_meta_list.append('{0} Year Genre Developer Rating Plot Audit    PClone\n'.format('Name'.ljust(ROM_NAME_LENGHT)))
        str_meta_list.append('{0}\n'.format('-' * 99))
        for m in check_list:
            # >> Limit ROM name string length
            name_str = text_limit_string(m['m_name'], ROM_NAME_LENGHT)
            str_meta_list.append('{0} {1}  {2}   {3}       {4}    {5}  {6:<7}  {7}\n'.format(
                            name_str.ljust(ROM_NAME_LENGHT),
                            m['m_year'], m['m_genre'], m['m_developer'],
                            m['m_rating'], m['m_plot'], m['m_nointro_status'], m['m_pclone_status']))

        # >> Step 4: Asset report
        str_asset_list = []
        str_asset_list.append('{0} Tit Sna Fan Ban Clr Bxf Bxb Car Fly Map Man Tra\n'.format('Name'.ljust(ROM_NAME_LENGHT)))
        str_asset_list.append('{0}\n'.format('-' * 98))
        for m in check_list:
            # >> Limit ROM name string length
            name_str = text_limit_string(m['m_name'], ROM_NAME_LENGHT)
            str_asset_list.append('{0}  {1}   {2}   {3}   {4}   {5}   {6}   {7}   {8}   {9}   {10}   {11}   {12}\n'.format(
                            name_str.ljust(ROM_NAME_LENGHT),
                            m['s_title'],     m['s_snap'],     m['s_fanart'],  m['s_banner'],
                            m['s_clearlogo'], m['s_boxfront'], m['s_boxback'], m['s_cartridge'],
                            m['s_flyer'],     m['s_map'],      m['s_manual'],  m['s_trailer']))

        # >> Step 5: Join string and write TXT reports
        try:
            # >> Stats report
            full_string = ''.join(str_list).encode('utf-8')
            file = open(report_stats_FN.getPath(), 'w')
            file.write(full_string)
            file.close()

            # >> Metadata report
            full_string = ''.join(str_meta_list).encode('utf-8')
            file = open(report_meta_FN.getPath(), 'w')
            file.write(full_string)
            file.close()

            # >> Asset report
            full_string = ''.join(str_asset_list).encode('utf-8')
            file = open(report_assets_FN.getPath(), 'w')
            file.write(full_string)
            file.close()
        except OSError:
            log_error('Cannot write Launcher Report file (OSError)')
            kodi_notify_warn('Cannot write Launcher Report (OSError)')
        except IOError:
            log_error('Cannot write categories.xml file (IOError)')
            kodi_notify_warn('Cannot write Launcher Report (IOError)')

        
    def _aux_get_info(self, asset_FN, path_asset_P, romfile_getBase_noext):
        # log_debug('title_FN.getDir() "{0}"'.format(title_FN.getDir()))
        # log_debug('path_title_P      "{0}"'.format(path_title_P))
        if path_asset_P != asset_FN.getDir():
            ret_str = 'C'
        else:
            if romfile_getBase_noext == asset_FN.getBase_noext():
                ret_str = 'Y'
            else:
                ret_str = 'O'

        return ret_str

    #
    # Deletes missing ROMs
    #
    def _roms_delete_missing_ROMs(self, roms):
        num_removed_roms = 0
        num_roms = len(roms)
        log_info('_roms_delete_missing_ROMs() Launcher has {0} ROMs'.format(num_roms))
        if num_roms > 0:
            log_verb('_roms_delete_missing_ROMs() Starting dead items scan')
            for rom_id in sorted(roms.iterkeys()):
                if not roms[rom_id]['filename']:
                    log_debug('_roms_delete_missing_ROMs() Skip "{0}"'.format(roms[rom_id]['m_name']))
                    continue
                ROMFileName = FileName(roms[rom_id]['filename'])
                log_debug('_roms_delete_missing_ROMs() Test "{0}"'.format(ROMFileName.getBase()))
                # --- Remove missing ROMs ---
                if not ROMFileName.exists():
                    log_debug('_roms_delete_missing_ROMs() RM   "{0}"'.format(ROMFileName.getBase()))
                    del roms[rom_id]
                    num_removed_roms += 1
            if num_removed_roms > 0:
                log_info('_roms_delete_missing_ROMs() {0} dead ROMs removed successfully'.format(num_removed_roms))
            else:
                log_info('_roms_delete_missing_ROMs() No dead ROMs found.')
        else:
            log_info('_roms_delete_missing_ROMs() Launcher is empty. No dead ROM check.')

        return num_removed_roms

    #
    # Resets the No-Intro status
    # 1) Remove all ROMs which does not exist.
    # 2) Set status of remaining ROMs to nointro_status = NOINTRO_STATUS_NONE
    #
    def _roms_reset_NoIntro_status(self, launcher, roms):
        log_info('_roms_reset_NoIntro_status() Launcher has {0} ROMs'.format(len(roms)))
        if len(roms) < 1: return

        # >> Step 1) Delete missing/dead ROMs
        num_removed_roms = self._roms_delete_missing_ROMs(roms)
        log_info('_roms_reset_NoIntro_status() Removed {0} dead/missing ROMs'.format(num_removed_roms))

        # >> Step 2) Set No-Intro status to NOINTRO_STATUS_NONE and
        #            set PClone status to PCLONE_STATUS_NONE
        log_info('_roms_reset_NoIntro_status() Resetting No-Intro status of all ROMs to None')
        for rom_id in sorted(roms.iterkeys()): 
            roms[rom_id]['nointro_status'] = NOINTRO_STATUS_NONE
            roms[rom_id]['pclone_status']  = PCLONE_STATUS_NONE
        log_info('_roms_reset_NoIntro_status() Now launcher has {0} ROMs'.format(len(roms)))

        # >> Step 3) Delete PClone index and Parent ROM list.
        roms_base_noext         = launcher['roms_base_noext']
        CParent_roms_base_noext = roms_base_noext + '_index_CParent'
        PClone_roms_base_noext  = roms_base_noext + '_index_PClone'
        parents_roms_base_noext = roms_base_noext + '_parents'
        CParent_FN = ROMS_DIR.pjoin(CParent_roms_base_noext + '.json')
        PClone_FN  = ROMS_DIR.pjoin(PClone_roms_base_noext + '.json')
        parents_FN = ROMS_DIR.pjoin(parents_roms_base_noext + '.json')
        if CParent_FN.exists():
            log_info('_roms_reset_NoIntro_status() Deleting {0}'.format(CParent_FN.getPath()))
            CParent_FN.unlink()
        if PClone_FN.exists():
            log_info('_roms_reset_NoIntro_status() Deleting {0}'.format(PClone_FN.getPath()))
            PClone_FN.unlink()
        if parents_FN.exists():
            log_info('_roms_reset_NoIntro_status() Deleting {0}'.format(parents_FN.getPath()))
            parents_FN.unlink()

    #
    # Helper function to update ROMs No-Intro status if user configured a No-Intro DAT file.
    # Dictionaries are mutable, so roms can be changed because passed by assigment.
    # This function also creates the Parent/Clone indices:
    #   1) ADDON_DATA_DIR/db_ROMs/roms_base_noext_PClone_index.json
    #   2) ADDON_DATA_DIR/db_ROMs/roms_base_noext_parents.json
    #
    # A) If there are Unkown ROMs, a fake rom with name [Unknown ROMs] and id UNKNOWN_ROMS_PARENT_ID
    #    is created. This fake ROM is the parent of all Unknown ROMs.
    #    This fake ROM is added to roms_base_noext_parents.json database.
    #    This fake ROM is not present in the main JSON ROM database.
    # 
    # Returns:
    #   True  -> ROM audit was OK
    #   False -> There was a problem with the audit.
    #
    def _roms_update_NoIntro_status(self, launcher, roms, nointro_xml_file_FileName):
        __debug_progress_dialogs = False
        __debug_time_step = 0.0005

        # --- Reset the No-Intro status and removed No-Intro missing ROMs ---
        audit_have = audit_miss = audit_unknown = 0
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Advanced Emulator Launcher', 'Deleting Missing/Dead ROMs and clearing flags ...')
        self._roms_reset_NoIntro_status(launcher, roms)
        pDialog.update(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Check if DAT file exists ---
        if not nointro_xml_file_FileName.exists():
            log_warning('_roms_update_NoIntro_status() Not found {0}'.format(nointro_xml_file_FileName.getPath()))
            return False
        pDialog.update(0, 'Loading No-Intro/Redump XML DAT file ...')
        roms_nointro = audit_load_NoIntro_XML_file(nointro_xml_file_FileName)
        pDialog.update(100)
        if __debug_progress_dialogs: time.sleep(0.5)
        if not roms_nointro:
            log_warning('_roms_update_NoIntro_status() Error loading {0}'.format(nointro_xml_file_FileName.getPath()))
            return False

        # --- Remove BIOSes from No-Intro ROMs ---
        if self.settings['scan_ignore_bios']:
            log_info('_roms_update_NoIntro_status() Removing BIOSes from No-Intro ROMs ...')
            pDialog.update(0, 'Removing BIOSes from No-Intro ROMs ...')
            num_items = len(roms_nointro)
            item_counter = 0
            filtered_roms_nointro = {}
            for rom_id in roms_nointro:
                rom = roms_nointro[rom_id]
                BIOS_str_list = re.findall('\[BIOS\]', rom['name'])
                if not BIOS_str_list:
                    filtered_roms_nointro[rom_id] = rom
                else:
                    log_debug('_roms_update_NoIntro_status() Removed BIOS "{0}"'.format(rom['name']))
                item_counter += 1
                pDialog.update((item_counter*100)/num_items)
                if __debug_progress_dialogs: time.sleep(__debug_time_step)
            roms_nointro = filtered_roms_nointro
            pDialog.update(100)
        else:
            log_info('_roms_update_NoIntro_status() User wants to include BIOSes.')

        # --- Put No-Intro ROM names in a set ---
        # >> Set is the fastest Python container for searching elements (implements hashed search).
        # >> No-Intro names include tags
        pDialog.update(0, 'Creating No-Intro and ROM sets ...')
        roms_nointro_set = set(roms_nointro.keys())
        roms_set = set()
        for rom_id in roms:
            # >> Use the ROM basename.
            ROMFileName = FileName(roms[rom_id]['filename'])
            roms_set.add(ROMFileName.getBase_noext())
        pDialog.update(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Traverse Launcher ROMs and check if they are in the No-Intro ROMs list ---
        pDialog.update(0, 'Audit Step 1/4: Checking Have and Unknown ROMs ...')
        num_items = len(roms)
        item_counter = 0
        for rom_id in roms:
            ROMFileName = FileName(roms[rom_id]['filename'])
            if ROMFileName.getBase_noext() in roms_nointro_set:
                roms[rom_id]['nointro_status'] = NOINTRO_STATUS_HAVE
                audit_have += 1
                log_debug('_roms_update_NoIntro_status() HAVE    "{0}"'.format(ROMFileName.getBase_noext()))
            else:
                roms[rom_id]['nointro_status'] = NOINTRO_STATUS_UNKNOWN
                audit_unknown += 1
                log_debug('_roms_update_NoIntro_status() UNKNOWN "{0}"'.format(ROMFileName.getBase_noext()))
            item_counter += 1
            pDialog.update((item_counter*100)/num_items)
            if __debug_progress_dialogs: time.sleep(__debug_time_step)
        pDialog.update(100)

        # --- Mark Launcher dead ROMs as missing ---
        pDialog.update(0, 'Audit Step 2/4: Checking Missing ROMs ...')
        num_items = len(roms)
        item_counter = 0
        for rom_id in roms:
            ROMFileName = FileName(roms[rom_id]['filename'])
            if not ROMFileName.exists():
                roms[rom_id]['nointro_status'] = NOINTRO_STATUS_MISS
                audit_miss += 1
                log_debug('_roms_update_NoIntro_status() MISSING "{0}"'.format(ROMFileName.getBase_noext()))
            item_counter += 1
            pDialog.update((item_counter*100)/num_items)
            if __debug_progress_dialogs: time.sleep(__debug_time_step)
        pDialog.update(100)

        # --- Now add missing ROMs to Launcher ---
        # >> Traverse the No-Intro set and add the No-Intro ROM if it's not in the Launcher
        # >> Added/Missing ROMs have their own romID.
        pDialog.update(0, 'Audit Step 3/4: Adding Missing ROMs ...')
        num_items = len(roms_nointro_set)
        item_counter = 0
        ROMPath = FileName(launcher['rompath'])
        for nointro_rom in sorted(roms_nointro_set):
            # log_debug('_roms_update_NoIntro_status() Checking "{0}"'.format(nointro_rom))
            if nointro_rom not in roms_set:
                # Add new "fake" missing ROM. This ROM cannot be launched!
                # Added ROMs have special extension .nointro
                rom = fs_new_rom()
                rom_id                = misc_generate_random_SID()
                rom['id']             = rom_id
                rom['filename']       = ROMPath.pjoin(nointro_rom + '.nointro').getOriginalPath()
                rom['m_name']         = nointro_rom
                rom['nointro_status'] = NOINTRO_STATUS_MISS
                roms[rom_id]          = rom
                audit_miss += 1
                log_debug('_roms_update_NoIntro_status() ADDED   "{0}"'.format(rom['m_name']))
                # log_debug('_roms_update_NoIntro_status()    OP   "{0}"'.format(rom['filename']))
            item_counter += 1
            pDialog.update((item_counter*100)/num_items)
            if __debug_progress_dialogs: time.sleep(__debug_time_step)
        pDialog.update(100)

        # --- Detect if the DAT file has PClone information or not ---
        dat_pclone_dic = audit_make_NoIntro_PClone_dic(roms_nointro)
        num_dat_clones = 0
        for parent_name in dat_pclone_dic: num_dat_clones += len(dat_pclone_dic[parent_name])
        log_verb('No-Intro/Redump DAT has {0} clone ROMs'.format(num_dat_clones))

        # --- Generate main pclone dictionary ---
        # >> audit_unknown_roms is an int of list = ['Parents', 'Clones']
        # log_debug("settings['audit_unknown_roms'] = {0}".format(self.settings['audit_unknown_roms']))
        unknown_ROMs_are_parents = True if self.settings['audit_unknown_roms'] == 0 else False
        log_debug('unknown_ROMs_are_parents = {0}'.format(unknown_ROMs_are_parents))
        # if num_dat_clones == 0 and self.settings['audit_create_pclone_groups']:
        #     # --- If DAT has no PClone information and user want then generate filename-based PClone groups ---
        #     # >> This feature is taken from NARS (NARS Advanced ROM Sorting)
        #     log_verb('Generating filename-based Parent/Clone groups')
        #     pDialog.update(0, 'Building filename-based Parent/Clone index ...')
        #     roms_pclone_index = audit_generate_filename_PClone_index(roms, roms_nointro, unknown_ROMs_are_parents)
        #     pDialog.update(100)
        #     if __debug_progress_dialogs: time.sleep(0.5)
        # else:
        #     # --- Make a DAT-based Parent/Clone index ---
        #     # >> Here we build a roms_pclone_index with info from the DAT file. 2 issues:
        #     # >> A) Redump DATs do not have cloneof information.
        #     # >> B) Also, it is at this point where a region custom parent may be chosen instead of
        #     # >>    the default one.
        #     log_verb('Generating DAT-based Parent/Clone groups')
        #     pDialog.update(0, 'Building DAT-based Parent/Clone index ...')
        #     roms_pclone_index = audit_generate_DAT_PClone_index(roms, roms_nointro, unknown_ROMs_are_parents)
        #     pDialog.update(100)
        #     if __debug_progress_dialogs: time.sleep(0.5)

        # --- Make a DAT-based Parent/Clone index ---
        # >> For 0.9.7 only use the DAT to make the PClone groups. In 0.9.8 decouple the audit
        # >> code from the PClone generation code.
        log_verb('Generating DAT-based Parent/Clone groups')
        pDialog.update(0, 'Building DAT-based Parent/Clone index ...')
        roms_pclone_index = audit_generate_DAT_PClone_index(roms, roms_nointro, unknown_ROMs_are_parents)
        pDialog.update(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Make a Clone/Parent index ---
        # >> This is made exclusively from the Parent/Clone index
        pDialog.update(0, 'Building Clone/Parent index ...')
        clone_parent_dic = {}
        for parent_id in roms_pclone_index:
            for clone_id in roms_pclone_index[parent_id]:
                clone_parent_dic[clone_id] = parent_id
        pDialog.update(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Set ROMs pclone_status flag and update launcher statistics ---
        pDialog.update(0, 'Audit Step 4/4: Setting Parent/Clone status and cloneof fields...')
        num_items = len(roms)
        item_counter = 0
        audit_parents = audit_clones = 0
        for rom_id in roms:
            if rom_id in roms_pclone_index:
                roms[rom_id]['pclone_status'] = PCLONE_STATUS_PARENT
                audit_parents += 1
            else:
                roms[rom_id]['cloneof'] = clone_parent_dic[rom_id]
                roms[rom_id]['pclone_status'] = PCLONE_STATUS_CLONE
                audit_clones += 1
            item_counter += 1
            pDialog.update((item_counter*100)/num_items)
            if __debug_progress_dialogs: time.sleep(__debug_time_step)
        pDialog.update(100)
        launcher['num_roms']    = len(roms)
        launcher['num_parents'] = audit_parents
        launcher['num_clones']  = audit_clones
        launcher['num_have']    = audit_have
        launcher['num_miss']    = audit_miss
        launcher['num_unknown'] = audit_unknown

        # --- Make a Parent only ROM list and save JSON ---
        # >> This is to speed up rendering of launchers in 1G1R display mode
        pDialog.update(0, 'Building Parent/Clone index and Parent dictionary ...')
        parent_roms = audit_generate_parent_ROMs_dic(roms, roms_pclone_index)
        pDialog.update(100)
        if __debug_progress_dialogs: time.sleep(0.5)

        # --- Save JSON databases ---
        pDialog.update(0, 'Saving NO-Intro/Redump JSON databases ...')
        fs_write_JSON_file(ROMS_DIR, launcher['roms_base_noext'] + '_index_PClone', roms_pclone_index)
        pDialog.update(30)
        fs_write_JSON_file(ROMS_DIR, launcher['roms_base_noext'] + '_index_CParent', clone_parent_dic)
        pDialog.update(60)
        fs_write_JSON_file(ROMS_DIR, launcher['roms_base_noext'] + '_parents', parent_roms)
        pDialog.update(100)
        pDialog.close()

        # --- Update launcher number of ROMs ---
        self.audit_have    = audit_have
        self.audit_miss    = audit_miss
        self.audit_unknown = audit_unknown
        self.audit_total   = len(roms)
        self.audit_parents = audit_parents
        self.audit_clones  = audit_clones

        # --- Report ---
        log_info('********** No-Intro/Redump audit finished. Report ***********')
        log_info('Have ROMs    {0:6d}'.format(self.audit_have))
        log_info('Miss ROMs    {0:6d}'.format(self.audit_miss))
        log_info('Unknown ROMs {0:6d}'.format(self.audit_unknown))
        log_info('Total ROMs   {0:6d}'.format(self.audit_total))
        log_info('Parent ROMs  {0:6d}'.format(self.audit_parents))
        log_info('Clone ROMs   {0:6d}'.format(self.audit_clones))

        return True

    #
    # Manually add a new ROM instead of a recursive scan.
    #   A) User chooses a ROM file
    #   B) Title is formatted. No metadata scraping.
    #   C) Thumb and fanart are searched locally only.
    # Later user can edit this ROM if he wants.
    #
    def _roms_add_new_rom(self, launcherID):
        # --- Grab launcher information ---
        launcher = self.launchers[launcherID]
        romext   = launcher['romext']
        rompath  = launcher['rompath']
        log_verb('_roms_add_new_rom() launcher name "{0}"'.format(launcher['m_name']))

        # --- Load ROMs for this launcher ---
        roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)

        # --- Choose ROM file ---
        dialog = xbmcgui.Dialog()
        extensions = '.' + romext.replace('|', '|.')
        romfile = dialog.browse(1, 'Select the ROM file', 'files', extensions, False, False, rompath).decode('utf-8')
        if not romfile: return
        log_verb('_roms_add_new_rom() romfile "{0}"'.format(romfile))

        # --- Format title ---
        scan_clean_tags = self.settings['scan_clean_tags']
        ROMFile = FileName(romfile)
        rom_name = text_format_ROM_title(ROMFile.getBase_noext(), scan_clean_tags)

        # ~~~ Check asset dirs and disable scanning for unset dirs ~~~
        # >> Do not warn about unconfigured dirs here
        (enabled_asset_list, unconfigured_name_list) = asset_get_configured_dir_list(launcher)

        # ~~~ Ensure there is no duplicate asset dirs ~~~
        duplicated_name_list = asset_get_duplicated_dir_list(launcher)
        if duplicated_name_list:
            duplicated_asset_srt = ', '.join(duplicated_name_list)
            log_debug('_roms_add_new_rom() Duplicated asset dirs: {0}'.format(duplicated_asset_srt))
            kodi_dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                           'Change asset directories before continuing.')
            return
        else:
            log_debug('_roms_add_new_rom() No duplicated asset dirs found')

        # ~~~ Search for local artwork/assets ~~~
        local_asset_list = assets_search_local_assets(launcher, ROMFile, enabled_asset_list)

        # --- Create ROM data structure ---
        romdata = fs_new_rom()
        romdata['id']          = misc_generate_random_SID()
        romdata['filename']    = ROMFile.getOriginalPath()
        romdata['m_name']      = rom_name
        for index, asset_kind in enumerate(ROM_ASSET_LIST):
            A = assets_get_info_scheme(asset_kind)
            romdata[A.key] = local_asset_list[index]
        roms[romdata['id']] = romdata
        log_info('_roms_add_new_rom() Added a new ROM')
        log_info('_roms_add_new_rom() romID       "{0}"'.format(romdata['id']))
        log_info('_roms_add_new_rom() filename    "{0}"'.format(romdata['filename']))
        log_info('_roms_add_new_rom() m_name      "{0}"'.format(romdata['m_name']))
        log_verb('_roms_add_new_rom() s_title     "{0}"'.format(romdata['s_title']))
        log_verb('_roms_add_new_rom() s_snap      "{0}"'.format(romdata['s_snap']))
        log_verb('_roms_add_new_rom() s_fanart    "{0}"'.format(romdata['s_fanart']))
        log_verb('_roms_add_new_rom() s_banner    "{0}"'.format(romdata['s_banner']))
        log_verb('_roms_add_new_rom() s_clearlogo "{0}"'.format(romdata['s_clearlogo']))
        log_verb('_roms_add_new_rom() s_boxfront  "{0}"'.format(romdata['s_boxfront']))
        log_verb('_roms_add_new_rom() s_boxback   "{0}"'.format(romdata['s_boxback']))
        log_verb('_roms_add_new_rom() s_cartridge "{0}"'.format(romdata['s_cartridge']))
        log_verb('_roms_add_new_rom() s_flyer     "{0}"'.format(romdata['s_flyer']))
        log_verb('_roms_add_new_rom() s_map       "{0}"'.format(romdata['s_map']))
        log_verb('_roms_add_new_rom() s_manual    "{0}"'.format(romdata['s_manual']))
        log_verb('_roms_add_new_rom() s_trailer   "{0}"'.format(romdata['s_trailer']))

        # --- If there is a No-Intro XML configured audit ROMs ---
        if launcher['nointro_xml_file']:
            log_info('No-Intro/Redump DAT configured. Starting ROM audit ...')
            nointro_xml_FN = FileName(launcher['nointro_xml_file'])
            if not self._roms_update_NoIntro_status(launcher, roms, nointro_xml_FN):
                self.launchers[launcherID]['nointro_xml_file'] = ''
                kodi_dialog_OK('Error auditing ROMs. XML DAT file unset.')
        else:
            log_info('No No-Intro/Redump DAT configured. Do not audit ROMs.')

        # ~~~ Save ROMs XML file ~~~
        # >> Also save categories/launchers to update timestamp
        launcher['num_roms'] = len(roms)
        launcher['timestamp_launcher'] = time.time()
        fs_write_ROMs_JSON(ROMS_DIR, launcher, roms)
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_refresh_container()
        kodi_notify('Added ROM. Launcher has now {0} ROMs'.format(len(roms)))

    #
    # ROM scanner. Called when user chooses "Add items" -> "Scan items"
    #
    def _roms_import_roms(self, launcherID):
        log_debug('========== _roms_import_roms() BEGIN ==================================================')

        # --- Get information from launcher ---
        launcher      = self.launchers[launcherID]
        launcher_path = FileName(launcher['rompath'])
        launcher_exts = launcher['romext']
        log_info('_roms_import_roms() Starting ROM scanner ...')
        log_info('Launcher name "{0}"'.format(launcher['m_name']))
        log_info('launcher ID   "{0}"'.format(launcher['id']))
        log_info('ROM path      "{0}"'.format(launcher_path.getPath()))
        log_info('ROM ext       "{0}"'.format(launcher_exts))
        log_info('Platform      "{0}"'.format(launcher['platform']))

        # --- Open ROM scanner report file ---
        launcher_report_FN = REPORTS_DIR.pjoin(launcher['roms_base_noext'] + '_report.txt')
        log_info('Report file OP "{0}"'.format(launcher_report_FN.getOriginalPath()))
        log_info('Report file  P "{0}"'.format(launcher_report_FN.getPath()))
        report_fobj = open(launcher_report_FN.getPath(), "w")
        report_fobj.write('*** Starting ROM scanner ... ***\n'.format())
        report_fobj.write('  Launcher name "{0}"\n'.format(launcher['m_name']))
        report_fobj.write('  launcher ID   "{0}"\n'.format(launcher['id']))
        report_fobj.write('  ROM path      "{0}"\n'.format(launcher_path.getPath()))
        report_fobj.write('  ROM ext       "{0}"\n'.format(launcher_exts))
        report_fobj.write('  Platform      "{0}"\n'.format(launcher['platform']))

        # >> Check if there is an XML for this launcher. If so, load it.
        # >> If file does not exist or is empty then return an empty dictionary.
        report_fobj.write('Loading launcher ROMs ...\n')
        roms = fs_load_ROMs_JSON(ROMS_DIR, launcher)
        num_roms = len(roms)
        report_fobj.write('{0} ROMs currently in database\n'.format(num_roms))
        log_info('Launcher ROM database contain {0} items'.format(num_roms))

        # --- Load metadata/asset scrapers --------------------------------------------------------
        # >> Create a dictionary with references to the asset srapers
        self.scraper_dic = {}

        # >> Scrapers for MAME platform are different than rest of the platforms
        if launcher['platform'] == 'MAME':
            # --- Metadata scraper ---
            # Scraper objects are created and inserted into a list. This list order matches
            # exactly the number returned by the settings. If scrapers are changed make sure the
            # list in scrapers.py and in settings.xml have same values!
            self.scraper_data = scrapers_metadata_MAME[self.settings['scraper_metadata_MAME']]
            self.scraper_data.set_addon_dir(CURRENT_ADDON_DIR.getPath())
            log_verb('Loaded metadata MAME scraper "{0}"'.format(self.scraper_data.name))

            # --- Asset scrapers ---
            A = assets_get_info_scheme(ASSET_TITLE)
            self.scraper_dic[A.key] = scrapers_title_MAME[self.settings['scraper_title_MAME']]
            log_verb('Loaded {0:<10} MAME scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            A = assets_get_info_scheme(ASSET_SNAP)
            self.scraper_dic[A.key] = scrapers_snap_MAME[self.settings['scraper_snap_MAME']]
            log_verb('Loaded {0:<10} MAME scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            # >> Boxfront -> Cabinet
            A = assets_get_info_scheme(ASSET_BOXFRONT)
            self.scraper_dic[A.key] = scrapers_cabinet_MAME[self.settings['scraper_cabinet_MAME']]
            log_verb('Loaded {0:<10} MAME scraper "{1}" (MAME Cabinets)'.format(A.name, self.scraper_dic[A.key].name))

            # >> Boxback -> Control Panel
            A = assets_get_info_scheme(ASSET_BOXBACK)
            self.scraper_dic[A.key] = scrapers_cpanel_MAME[self.settings['scraper_cpanel_MAME']]
            log_verb('Loaded {0:<10} MAME scraper "{1}" (MAME CPanels)'.format(A.name, self.scraper_dic[A.key].name))

            # >> Cartridge -> PCB
            A = assets_get_info_scheme(ASSET_CARTRIDGE)
            self.scraper_dic[A.key] = scrapers_pcb_MAME[self.settings['scraper_pcb_MAME']]
            log_verb('Loaded {0:<10} MAME scraper "{1}" (MAME PCBs)'.format(A.name, self.scraper_dic[A.key].name))

            A = assets_get_info_scheme(ASSET_FANART)
            self.scraper_dic[A.key] = scrapers_fanart_MAME[self.settings['scraper_fanart_MAME']]
            log_verb('Loaded {0:<10} MAME scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            # >> Banner -> Marquee
            A = assets_get_info_scheme(ASSET_BANNER)
            self.scraper_dic[A.key] = scrapers_marquee_MAME[self.settings['scraper_marquee_MAME']]
            log_verb('Loaded {0:<10} MAME scraper "{1}" (MAME Marquees)'.format(A.name, self.scraper_dic[A.key].name))

            A = assets_get_info_scheme(ASSET_CLEARLOGO)
            self.scraper_dic[A.key] = scrapers_clearlogo_MAME[self.settings['scraper_clearlogo_MAME']]
            log_verb('Loaded {0:<10} MAME scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            A = assets_get_info_scheme(ASSET_FLYER)
            self.scraper_dic[A.key] = scrapers_flyer_MAME[self.settings['scraper_flyer_MAME']]
            log_verb('Loaded {0:<10} MAME scraper "{1}" (MAME flyers)'.format(A.name, self.scraper_dic[A.key].name))

            # >> Map (not supported yet, use a null scraper)
            A = assets_get_info_scheme(ASSET_MAP)
            self.scraper_dic[A.key] = NULL_obj
            log_verb('Loaded {0:<10} MAME scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            # >> Manual (not supported yet, use a null scraper)
            A = assets_get_info_scheme(ASSET_MANUAL)
            self.scraper_dic[A.key] = NULL_obj
            log_verb('Loaded {0:<10} MAME scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            # >> Trailer (not supported yet, use a null scraper)
            A = assets_get_info_scheme(ASSET_TRAILER)
            self.scraper_dic[A.key] = NULL_obj
            log_verb('Loaded {0:<10} MAME scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        else:
            # --- Metadata scraper ---
            self.scraper_data = scrapers_metadata[self.settings['scraper_metadata']]
            self.scraper_data.set_addon_dir(CURRENT_ADDON_DIR.getPath())
            log_verb('Loaded metadata scraper "{0}"'.format(self.scraper_data.name))

            # --- Asset scrapers ---
            A = assets_get_info_scheme(ASSET_TITLE)
            self.scraper_dic[A.key] = scrapers_title[self.settings['scraper_title']]
            log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            A = assets_get_info_scheme(ASSET_SNAP)
            self.scraper_dic[A.key] = scrapers_snap[self.settings['scraper_snap']]
            log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            A = assets_get_info_scheme(ASSET_BOXFRONT)
            self.scraper_dic[A.key] = scrapers_boxfront[self.settings['scraper_boxfront']]
            log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            A = assets_get_info_scheme(ASSET_BOXBACK)
            self.scraper_dic[A.key] = scrapers_boxback[self.settings['scraper_boxback']]
            log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            A = assets_get_info_scheme(ASSET_CARTRIDGE)
            self.scraper_dic[A.key] = scrapers_cartridge[self.settings['scraper_cart']]
            log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            A = assets_get_info_scheme(ASSET_FANART)
            self.scraper_dic[A.key] = scrapers_fanart[self.settings['scraper_fanart']]
            log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            A = assets_get_info_scheme(ASSET_BANNER)
            self.scraper_dic[A.key] = scrapers_banner[self.settings['scraper_banner']]
            log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            A = assets_get_info_scheme(ASSET_CLEARLOGO)
            self.scraper_dic[A.key] = scrapers_clearlogo[self.settings['scraper_clearlogo']]
            log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            # >> Flyers only supported by ArcadeDB (for MAME). If platform is not MAME then deactivate
            # >> this scraper.
            A = assets_get_info_scheme(ASSET_FLYER)
            self.scraper_dic[A.key] = NULL_obj
            log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            # >> Map (not supported yet, use a null scraper)
            A = assets_get_info_scheme(ASSET_MAP)
            self.scraper_dic[A.key] = NULL_obj
            log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            # >> Manual (not supported yet, use a null scraper)
            A = assets_get_info_scheme(ASSET_MANUAL)
            self.scraper_dic[A.key] = NULL_obj
            log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

            # >> Trailer (not supported yet, use a null scraper)
            A = assets_get_info_scheme(ASSET_TRAILER)
            self.scraper_dic[A.key] = NULL_obj
            log_verb('Loaded {0:<10} asset scraper "{1}"'.format(A.name, self.scraper_dic[A.key].name))

        # >> Initialise options of the thumb scraper (NOT SUPPORTED YET)
        # region = self.settings['scraper_region']
        # thumb_imgsize = self.settings['scraper_thumb_size']
        # self.scraper_asset.set_options(region, thumb_imgsize)

        # --- Initialise cache used in _roms_scrap_asset() ---
        # >> This cache is used to store the selected game from the get_search() returned list.
        # >> The idea is that get_search() is used only once for each asset.
        self.scrap_asset_cached_dic = {}

        # --- Assets/artwork stuff ----------------------------------------------------------------
        # ~~~ Check asset dirs and disable scanning for unset dirs ~~~
        log_info('Checking for unset artwork directories ...')
        (self.enabled_asset_list, unconfigured_name_list) = asset_get_configured_dir_list(launcher)
        if unconfigured_name_list:
            unconfigured_asset_srt = ', '.join(unconfigured_name_list)
            kodi_dialog_OK('Assets directories not set: {0}. '.format(unconfigured_asset_srt) +
                           'Asset scanner will be disabled for this/those.')

        # ~~~ Ensure there is no duplicate asset dirs ~~~
        # >> Abort scanning of assets if duplicates found
        log_info('Checking for duplicated artwork directories ...')
        duplicated_name_list = asset_get_duplicated_dir_list(launcher)
        if duplicated_name_list:
            duplicated_asset_srt = ', '.join(duplicated_name_list)
            log_info('Duplicated asset dirs: {0}'.format(duplicated_asset_srt))
            kodi_dialog_OK('Duplicated asset directories: {0}. '.format(duplicated_asset_srt) +
                           'Change asset directories before continuing.')
            return
        else:
            log_info('No duplicated asset dirs found')

        # --- Create a cache of assets ---
        # >> misc_add_file_cache() creates a set with all files in a given directory.
        # >> That set is stored in a function internal cache associated with the path.
        # >> Files in the cache can be searched with misc_search_file_cache()
        log_info('Scanning and caching files in asset directories ...')
        pDialog = xbmcgui.DialogProgress()
        pDialog.create('Advanced Emulator Launcher', 'Scanning files in asset directories ...')
        for i, asset_kind in enumerate(ROM_ASSET_LIST):
            AInfo = assets_get_info_scheme(asset_kind)
            misc_add_file_cache(launcher[AInfo.path_key])
            pDialog.update((100*i)/len(ROM_ASSET_LIST))
        pDialog.update(100)
        pDialog.close()

        # --- Progress dialog ---
        # >> Put in in object variables so it can be access in helper functions.
        self.pDialog_verbose = True
        self.pDialog = pDialog
        self.pDialog_canceled = False

        # --- Remove dead entries -----------------------------------------------------------------
        log_info('Removing dead ROMs ...'.format())
        report_fobj.write('Removing dead ROMs ...\n')
        num_removed_roms = 0
        if num_roms > 0:
            log_debug('Starting dead items scan')
            i = 0
            self.pDialog.create('Advanced Emulator Launcher', 'Checking for dead ROMs ...')
            for key in sorted(roms.iterkeys()):
                log_debug('Searching {0}'.format(roms[key]['filename']))
                self.pDialog.update(i * 100 / num_roms)
                i += 1
                fileName = FileName(roms[key]['filename'])
                if not fileName.exists():
                    log_debug('Not found')
                    log_debug('Deleting from DB {0}'.format(roms[key]['filename']))
                    del roms[key]
                    num_removed_roms += 1
            self.pDialog.update(i * 100 / num_roms)
            self.pDialog.close()
            if num_removed_roms > 0:
                kodi_notify('{0} dead ROMs removed successfully'.format(num_removed_roms))
                log_info('{0} dead ROMs removed successfully'.format(num_removed_roms))
            else:
                log_info('No dead ROMs found')
        else:
            log_info('Launcher is empty. No dead ROM check.')

        # ~~~ Scan for new files (*.*) and put them in a list ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        kodi_busydialog_ON()
        files = []
        log_info('Scanning files in {0}'.format(launcher_path.getPath()))
        report_fobj.write('Scanning files ...\n')
        report_fobj.write('  Directory {0}\n'.format(launcher_path.getPath()))
        if self.settings['scan_recursive']:
            log_info('Recursive scan activated')
            files = launcher_path.recursiveScanFilesInPath('*.*')
        else:
            log_info('Recursive scan not activated')
            files = launcher_path.scanFilesInPath('*.*')
        kodi_busydialog_OFF()
        num_files = len(files)
        log_info('File scanner found {0} files'.format(num_files))
        report_fobj.write('  File scanner found {0} files\n'.format(num_files))

        # ~~~ Now go processing file by file ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.pDialog.create('Advanced Emulator Launcher', 'Scanning {0}'.format(launcher_path))
        log_debug('============================== Processing ROMs ==============================')
        report_fobj.write('Processing files ...\n')
        num_new_roms = 0
        num_files_checked = 0
        for f_path in sorted(files):
            # --- Get all file name combinations ---
            ROM = FileName(f_path)
            log_debug('========== Processing File ==========')
            log_debug('ROM.getPath()         "{0}"'.format(ROM.getPath()))
            log_debug('ROM.getOriginalPath() "{0}"'.format(ROM.getOriginalPath()))
            # log_debug('ROM.getPath_noext()   "{0}"'.format(ROM.getPath_noext()))
            # log_debug('ROM.getDir()          "{0}"'.format(ROM.getDir()))
            # log_debug('ROM.getBase()         "{0}"'.format(ROM.getBase()))
            # log_debug('ROM.getBase_noext()   "{0}"'.format(ROM.getBase_noext()))
            # log_debug('ROM.getExt()          "{0}"'.format(ROM.getExt()))
            report_fobj.write('>>> {0}\n'.format(ROM.getPath()).encode('utf-8'))

            # ~~~ Update progress dialog ~~~
            self.progress_number = num_files_checked * 100 / num_files
            self.file_text = 'ROM {0}'.format(ROM.getBase())
            if not self.pDialog_verbose:
                self.pDialog.update(self.progress_number, self.file_text)
            else:
                activity_text = 'Checking if has ROM extension ...'
                self.pDialog.update(self.progress_number, self.file_text, activity_text)
            num_files_checked += 1

            # --- Check if filename matchs ROM extensions ---
            # The recursive scan has scanned all files. Check if this file matches some of 
            # the ROM extensions. If this file isn't a ROM skip it and go for next one in the list.
            processROM = False
            for ext in launcher_exts.split("|"):
                if ROM.getExt() == '.' + ext:
                    log_debug("Expected '{0}' extension detected".format(ext))
                    report_fobj.write("  Expected '{0}' extension detected\n".format(ext))
                    processROM = True
            if not processROM: 
                log_debug('File has not an expected extension. Skipping file.')
                report_fobj.write('  File has not an expected extension. Skipping file.\n')
                continue

            # --- Check if ROM belongs to a multidisc set ---
            MultiDiscInROMs = False
            MDSet = text_get_multidisc_info(ROM)
            if MDSet.isMultiDisc:
                log_info('ROM belongs to a multidisc set.')
                log_info('isMultiDisc "{0}"'.format(MDSet.isMultiDisc))
                log_info('setName     "{0}"'.format(MDSet.setName))
                log_info('discName    "{0}"'.format(MDSet.discName))
                log_info('extension   "{0}"'.format(MDSet.extension))
                log_info('order       "{0}"'.format(MDSet.order))
                report_fobj.write('  ROM belongs to a multidisc set.\n')

                # >> Check if the set is already in launcher ROMs.
                MultiDisc_rom_id = None
                for rom_id, rom_dic in roms.iteritems():
                    temp_FN = FileName(rom_dic['filename'])
                    if temp_FN.getBase() == MDSet.setName:
                        MultiDiscInROMs  = True
                        MultiDisc_rom_id = rom_id
                        break
                log_info('MultiDiscInROMs is {0}'.format(MultiDiscInROMs))

                # >> If the set is not in the ROMs then this ROM is the first of the set.
                # >> Add the set
                if not MultiDiscInROMs:
                    log_info('First ROM in the set. Adding to ROMs ...')
                    # >> Manipulate ROM so filename is the name of the set
                    ROM_dir = FileName(ROM.getDir())
                    ROM_temp = ROM_dir.pjoin(MDSet.setName)
                    log_info('ROM_temp OP "{0}"'.format(ROM_temp.getOriginalPath()))
                    log_info('ROM_temp  P "{0}"'.format(ROM_temp.getPath()))
                    ROM = ROM_temp
                # >> If set already in ROMs, just add this disk into the set disks field.
                else:
                    log_info('Adding additional disk "{0}"'.format(MDSet.discName))
                    roms[MultiDisc_rom_id]['disks'].append(MDSet.discName)
                    # >> Reorder disks like Disk 1, Disk 2, ...
                    
                    # >> Process next file
                    log_info('Processing next file ...')
                    continue
            else:
                log_info('ROM does not belong to a multidisc set.')
                report_fobj.write('  ROM does not belong to a multidisc set.\n')

            # --- Check that ROM is not already in the list of ROMs ---
            # >> If file already in ROM list skip it
            repeatedROM = False
            for rom_id in roms:
                if roms[rom_id]['filename'] == f_path: repeatedROM = True
            if repeatedROM:
                log_debug('File already into launcher ROM list. Skipping file.')
                report_fobj.write('  File already into launcher ROM list. Skipping file.\n')
                continue
            else:
                log_debug('File not in launcher ROM list. Processing it ...')
                report_fobj.write('  File not in launcher ROM list. Processing it ...\n')

            # --- Ignore BIOS ROMs ---
            # Name of bios is: '[BIOS] Rom name example (Rev A).zip'
            if self.settings['scan_ignore_bios']:
                BIOS_re = re.findall('\[BIOS\]', ROM.getBase())
                if len(BIOS_re) > 0:
                    log_info("BIOS detected. Skipping ROM '{0}'".format(ROM.path))
                    continue

            # ~~~~~ Process new ROM and add to the list ~~~~~
            romdata     = self._roms_process_scanned_ROM(launcherID, ROM)
            romID       = romdata['id']
            roms[romID] = romdata
            num_new_roms += 1

            # --- This was the first ROM in a multidisc set ---
            if MDSet.isMultiDisc and not MultiDiscInROMs:
                log_info('Adding first disk "{0}"'.format(MDSet.discName))
                roms[romID]['disks'].append(MDSet.discName)
            
            # ~~~ Check if user pressed the cancel button ~~~
            if self.pDialog.iscanceled() or self.pDialog_canceled:
                self.pDialog.close()
                kodi_dialog_OK('Stopping ROM scanning. No changes have been made.')
                log_info('User pressed Cancel button when scanning ROMs. ROM scanning stopped.')
                return
        self.pDialog.close()
        log_info('********** ROM scanner finished. Report **********')
        log_info('Removed dead ROMs {0:6d}'.format(num_removed_roms))
        log_info('Files checked     {0:6d}'.format(num_files_checked))
        log_info('New added ROMs    {0:6d}'.format(num_new_roms))
        report_fobj.write('********** ROM scanner finished **********\n')
        report_fobj.write('Removed dead ROMs {0:6d}\n'.format(num_removed_roms))
        report_fobj.write('Files checked     {0:6d}\n'.format(num_files_checked))
        report_fobj.write('New added ROMs    {0:6d}\n'.format(num_new_roms))

        if len(roms) == 0:
            report_fobj.write('WARNING Launcher has no ROMs!\n')
            report_fobj.close()
            kodi_dialog_OK('No ROMs found! Make sure launcher directory and file extensions are correct.')
            return

        # --- If we have a No-Intro XML then audit roms after scanning ----------------------------
        if launcher['nointro_xml_file']:
            log_info('No-Intro/Redump DAT configured. Starting ROM audit ...')
            report_fobj.write('No-Intro/Redump DAT configured. Starting ROM audit ...\n')
            roms_base_noext = launcher['roms_base_noext']
            nointro_xml_FN = FileName(launcher['nointro_xml_file'])
            if self._roms_update_NoIntro_status(launcher, roms, nointro_xml_FN):
                fs_write_ROMs_JSON(ROMS_DIR, self.launchers[launcherID], roms)
                kodi_notify('ROM scanner and audit finished. '
                            'Have {0} / Miss {1} / Unknown {2}'.format(self.audit_have, self.audit_miss, self.audit_unknown))
                # >> _roms_update_NoIntro_status() already prints and audit report on Kodi log
                report_fobj.write('********** No-Intro/Redump audit finished. Report ***********\n')
                report_fobj.write('Have ROMs    {0:6d}\n'.format(self.audit_have))
                report_fobj.write('Miss ROMs    {0:6d}\n'.format(self.audit_miss))
                report_fobj.write('Unknown ROMs {0:6d}\n'.format(self.audit_unknown))
                report_fobj.write('Total ROMs   {0:6d}\n'.format(self.audit_total))
                report_fobj.write('Parent ROMs  {0:6d}\n'.format(self.audit_parents))
                report_fobj.write('Clone ROMs   {0:6d}\n'.format(self.audit_clones))
            else:
                # >> ERROR when auditing the ROMs. Unset nointro_xml_file
                self.launchers[launcherID]['nointro_xml_file'] = ''
                kodi_notify_warn('Error auditing ROMs. XML DAT file unset.')
        else:
            log_info('No-Intro/Redump DAT not configured. Do not audit ROMs.')
            report_fobj.write('No-Intro/Redump DAT not configured. Do not audit ROMs.\n')
            if num_new_roms == 0:
                kodi_notify('Added no new ROMs. Launcher has {0} ROMs'.format(len(roms)))
            else:
                kodi_notify('Added {0} new ROMs'.format(num_new_roms))

        # --- Close ROM scanner report file ---
        report_fobj.write('*** END of the ROM scanner report ***\n')
        report_fobj.close()

        # ~~~ Save ROMs XML file ~~~
        # >> Also save categories/launchers to update timestamp.
        # >> Update launcher timestamp to update VLaunchers and reports.
        self.launchers[launcherID]['num_roms'] = len(roms)
        self.launchers[launcherID]['timestamp_launcher'] = time.time()
        self.pDialog.create('Advanced Emulator Launcher', 'Saving ROM JSON database ...')
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        self.pDialog.update(10)
        fs_write_ROMs_JSON(ROMS_DIR, launcher, roms)
        self.pDialog.update(100)
        self.pDialog.close()
        kodi_refresh_container()

    #
    # launcherID -> [string] MD5 hash (32 hexadecimal digits)
    # ROM        -> [FileName object]
    #
    # Returns a ROM dictionary created with fs_new_rom()
    #
    def _roms_process_scanned_ROM(self, launcherID, ROM):
        # --- "Constants" ---
        META_TITLE_ONLY = 100
        META_NFO_FILE   = 200
        META_SCRAPER    = 300

        # --- Create new rom dictionary ---
        # >> Database always stores the original (non transformed/manipulated) path
        launcher = self.launchers[launcherID]
        platform = launcher['platform']
        romdata  = fs_new_rom()
        romdata['id']       = misc_generate_random_SID()
        romdata['filename'] = ROM.getOriginalPath()

        # ~~~~~ Scrape game metadata information ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # >> Test if NFO file exists
        NFO_file = FileName(ROM.getPath_noext() + '.nfo')
        log_debug('Testing NFO file "{0}"'.format(NFO_file.getPath()))
        found_NFO_file = True if NFO_file.exists() else False

        # >> Determine metadata action based on policy
        # >> scan_metadata_policy -> values="None|NFO Files|NFO Files + Scrapers|Scrapers"
        scan_metadata_policy       = self.settings['scan_metadata_policy']
        scan_clean_tags            = self.settings['scan_clean_tags']
        scan_ignore_scrapped_title = self.settings['scan_ignore_scrap_title']
        metadata_action = META_TITLE_ONLY
        if scan_metadata_policy == 0:
            log_verb('Metadata policy: No NFO reading, no scraper. Only cleaning ROM name.')
            metadata_action = META_TITLE_ONLY
        elif scan_metadata_policy == 1:
            log_verb('Metadata policy: Read NFO file only | Scraper OFF')
            metadata_action = META_NFO_FILE
        elif scan_metadata_policy == 2 and found_NFO_file:
            log_verb('Metadata policy: Read NFO file ON, if not NFO then Scraper ON')
            log_verb('Metadata policy: NFO file found | Scraper OFF')
            metadata_action = META_NFO_FILE
        elif scan_metadata_policy == 2 and not found_NFO_file:
            log_verb('Metadata policy: Read NFO file ON, if not NFO then Scraper ON')
            log_verb('Metadata policy: NFO file not found | Scraper ON')
            metadata_action = META_SCRAPER
        elif scan_metadata_policy == 3:
            log_verb('Metadata policy: Read NFO file OFF | Scraper ON')
            log_verb('Metadata policy: Forced scraper ON')
            metadata_action = META_SCRAPER
        else:
            log_error('Invalid scan_metadata_policy value = {0}'.format(scan_metadata_policy))

        # >> Do metadata action based on policy
        if metadata_action == META_TITLE_ONLY:
            if self.pDialog_verbose:
                scraper_text = 'Formatting ROM name.'
                self.pDialog.update(self.progress_number, self.file_text, scraper_text)
            romdata['m_name'] = text_format_ROM_title(ROM.getBase_noext(), scan_clean_tags)
        elif metadata_action == META_NFO_FILE:
            nfo_file_path = FileName(ROM.getPath_noext() + ".nfo")
            if self.pDialog_verbose:
                scraper_text = 'Loading NFO file {0}'.format(nfo_file_path.getOriginalPath())
                self.pDialog.update(self.progress_number, self.file_text, scraper_text)
            log_debug('Testing NFO file "{0}"'.format(nfo_file_path.getPath()))
            if nfo_file_path.exists():
                log_debug('NFO file found. Loading it.')
                nfo_dic = fs_import_NFO_file_scanner(nfo_file_path)
                # NOTE <platform> is chosen by AEL, never read from NFO files
                romdata['m_name']      = nfo_dic['title']     # <title>
                romdata['m_year']      = nfo_dic['year']      # <year>
                romdata['m_genre']     = nfo_dic['genre']     # <genre>
                romdata['m_developer'] = nfo_dic['publisher'] # <publisher> rename to <developer>
                # romdata['m_nplayers']  = nfo_dic['nplayers']  # <nplayers>
                # romdata['m_esrb']      = nfo_dic['esrb']      # <esrb>
                # romdata['m_rating']    = nfo_dic['rating']    # <rating>
                romdata['m_plot']      = nfo_dic['plot']      # <plot>
            else:
                log_debug('NFO file not found. Only cleaning ROM name.')
                romdata['m_name'] = text_format_ROM_title(ROM.getBase_noext(), scan_clean_tags)
        elif metadata_action == META_SCRAPER:
            if self.pDialog_verbose:
                scraper_text = 'Scraping metadata with {0}. Searching for matching games ...'.format(self.scraper_data.name)
                self.pDialog.update(self.progress_number, self.file_text, scraper_text)

            # --- Do a search and get a list of games ---
            rom_name_scraping = text_format_ROM_name_for_scraping(ROM.getBase_noext())
            results = self.scraper_data.get_search(rom_name_scraping, ROM.getBase_noext(), platform)
            log_debug('Metadata scraper found {0} result/s'.format(len(results)))
            if results:
                # id="metadata_scraper_mode" values="Semi-automatic|Automatic"
                if self.settings['metadata_scraper_mode'] == 0:
                    log_debug('Metadata semi-automatic scraping')
                    # >> Close progress dialog (and check it was not canceled)
                    if self.pDialog.iscanceled(): self.pDialog_canceled = True
                    self.pDialog.close()

                    # >> Display corresponding game list found so user choses
                    dialog = xbmcgui.Dialog()
                    rom_name_list = []
                    for game in results: rom_name_list.append(game['display_name'])
                    selectgame = dialog.select('Select game for ROM {0}'.format(ROM.getBase_noext()), rom_name_list)
                    if selectgame < 0: selectgame = 0

                    # >> Open progress dialog again
                    self.pDialog.create('Advanced Emulator Launcher')
                    if not self.pDialog_verbose: self.pDialog.update(self.progress_number, self.file_text)
                elif self.settings['metadata_scraper_mode'] == 1:
                    log_debug('Metadata automatic scraping. Selecting first result.')
                    selectgame = 0
                else:
                    log_error('Invalid metadata_scraper_mode {0}'.format(self.settings['metadata_scraper_mode']))
                    selectgame = 0
                if self.pDialog_verbose:
                    scraper_text = 'Scraping metadata with {0}. Getting metadata ...'.format(self.scraper_data.name)
                    self.pDialog.update(self.progress_number, self.file_text, scraper_text)

                # --- Grab metadata for selected game ---
                gamedata = self.scraper_data.get_metadata(results[selectgame])

                # --- Put metadata into ROM dictionary ---
                if scan_ignore_scrapped_title:
                    romdata['m_name'] = text_format_ROM_title(ROM.getBase_noext(), scan_clean_tags)
                    log_debug("User wants to ignore scraper name. Setting name to '{0}'".format(romdata['m_name']))
                else:
                    romdata['m_name'] = gamedata['title']
                    log_debug("User wants scrapped name. Setting name to '{0}'".format(romdata['m_name']))
                romdata['m_year']      = gamedata['year']
                romdata['m_genre']     = gamedata['genre']
                romdata['m_developer'] = gamedata['developer']
                romdata['m_nplayers']  = gamedata['nplayers']
                romdata['m_esrb']      = gamedata['esrb']
                romdata['m_plot']      = gamedata['plot']

                # --- Update ROM NFO file after scraping ---
                if self.settings['scan_update_NFO_files']:
                    log_debug('User wants to update NFO file after scraping')
                    fs_export_ROM_NFO(romdata, False)
            else:
                log_verb('Metadata scraper found no games after searching. Only cleaning ROM name.')
                romdata['m_name'] = text_format_ROM_title(ROM.getBase_noext(), scan_clean_tags)
        else:
            log_error('Invalid metadata_action value = {0}'.format(metadata_action))

        # ~~~~~ Search for local artwork/assets ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        local_asset_list = assets_search_local_cached_assets(launcher, ROM, self.enabled_asset_list)

        # ~~~ Asset scraping ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # settings.xml -> id="scan_asset_policy" default="0" values="Local Assets|Local Assets + Scrapers|Scrapers only"
        scan_asset_policy = self.settings['scan_asset_policy']
        if scan_asset_policy == 0:
            log_verb('Asset policy: local images only | Scraper OFF')
            for i, asset_kind in enumerate(ROM_ASSET_LIST):
                A = assets_get_info_scheme(asset_kind)
                romdata[A.key] = local_asset_list[i]

        elif scan_asset_policy == 1:
            log_verb('Asset policy: if not Local Image then Scraper ON')
            # selected_title = self._roms_process_asset_policy_2(ASSET_TITLE, local_title, ROM, launcher)
            for i, asset_kind in enumerate(ROM_ASSET_LIST):
                A = assets_get_info_scheme(asset_kind)
                if not self.enabled_asset_list[i]:
                    romdata[A.key] = ''
                    log_verb('Skipped {0} (dir not configured)'.format(A.name))
                    continue
                if local_asset_list[i]:
                    log_verb('Asset policy: local {0} FOUND | Scraper OFF'.format(A.name))
                    romdata[A.key] = local_asset_list[i]
                else:
                    log_verb('Asset policy: local {0} NOT found | Scraper ON'.format(A.name))
                    # >> Set the asset-specific scraper before calling _roms_scrap_asset()
                    romdata[A.key] = self._roms_scrap_asset(self.scraper_dic[A.key], asset_kind,
                                                            local_asset_list[i], ROM, launcher)

        elif scan_asset_policy == 2:
            log_verb('Asset policy: scraper will overwrite local assets | Scraper ON')
            # selected_title = self._roms_scrap_asset(ASSET_TITLE, local_title, ROM, launcher)
            for i, asset_kind in enumerate(ROM_ASSET_LIST):
                A = assets_get_info_scheme(asset_kind)
                if not self.enabled_asset_list[i]:
                    romdata[A.key] = ''
                    log_verb('Skipped {0} (dir not configured)'.format(A.name))
                    continue
                log_verb('Asset policy: local {0} NOT found | Scraper ON'.format(A.name))
                # >> Set the asset-specific scraper before calling _roms_scrap_asset()
                romdata[A.key] = self._roms_scrap_asset(self.scraper_dic[A.key], asset_kind, 
                                                        local_asset_list[i], ROM, launcher)

        log_verb('Set Title     file "{0}"'.format(romdata['s_title']))
        log_verb('Set Snap      file "{0}"'.format(romdata['s_snap']))
        log_verb('Set Boxfront  file "{0}"'.format(romdata['s_boxfront']))
        log_verb('Set Boxback   file "{0}"'.format(romdata['s_boxback']))
        log_verb('Set Cartridge file "{0}"'.format(romdata['s_cartridge']))
        log_verb('Set Fanart    file "{0}"'.format(romdata['s_fanart']))
        log_verb('Set Banner    file "{0}"'.format(romdata['s_banner']))
        log_verb('Set Clearlogo file "{0}"'.format(romdata['s_clearlogo']))
        log_verb('Set Flyer     file "{0}"'.format(romdata['s_flyer']))
        log_verb('Set Map       file "{0}"'.format(romdata['s_map']))
        log_verb('Set Manual    file "{0}"'.format(romdata['s_manual']))
        log_verb('Set Trailer   file "{0}"'.format(romdata['s_trailer']))

        return romdata

    #
    # Returns a valid filename of the downloaded scrapped image, filename of local image
    # or empty string if scraper finds nothing or download failed.
    #
    def _roms_scrap_asset(self, scraper_obj, asset_kind, local_asset_path, ROM, launcher):
        # >> By default always use local image in case scraper fails
        ret_asset_path = local_asset_path

        # --- Customise function depending of image_king ---
        A = assets_get_info_scheme(asset_kind)
        asset_directory  = FileName(launcher[A.path_key])
        asset_path_noext_FN = assets_get_path_noext_DIR(A, asset_directory, ROM)
        platform = launcher['platform']

        # --- Updated progress dialog ---
        if self.pDialog_verbose:
            scraper_text = 'Scraping {0} with {1}. Searching for matching games ...'.format(A.name, scraper_obj.name)
            self.pDialog.update(self.progress_number, self.file_text, scraper_text)
        log_verb('_roms_scrap_asset() Scraping {0} with {1}'.format(A.name, scraper_obj.name))
        log_debug('_roms_scrap_asset() local_asset_path "{0}"'.format(local_asset_path))
        log_debug('_roms_scrap_asset() asset_path_noext "{0}"'.format(asset_path_noext_FN.getPath()))

        # --- If scraper does not support particular asset return inmediately ---
        if not scraper_obj.supports_asset(asset_kind):
            log_debug('_roms_scrap_asset() Scraper {0} does not support asset {1}. '
                      'Skipping.'.format(scraper_obj.name, A.name))
            return ret_asset_path

        # --- Set scraping mode ---
        # settings.xml: id="asset_scraper_mode"  default="0" values="Semi-automatic|Automatic"
        scraping_mode = self.settings['asset_scraper_mode']

        # --- Check cache to check if user choose a game previously ---
        # >> id(object)
        # >> This is an integer (or long integer) which is guaranteed to be unique and constant for 
        # >> this object during its lifetime.
        scraper_id = id(scraper_obj)
        log_debug('_roms_scrap_asset() Scraper ID          "{0}"'.format(scraper_id))
        log_debug('_roms_scrap_asset() Scraper obj name    "{0}"'.format(scraper_obj.name))
        log_debug('_roms_scrap_asset() ROM.getBase_noext() "{0}"'.format(ROM.getBase_noext()))
        log_debug('_roms_scrap_asset() platform            "{0}"'.format(platform))
        log_debug('_roms_scrap_asset() Entries in cache    {0}'.format(len(self.scrap_asset_cached_dic)))
        if scraper_id in self.scrap_asset_cached_dic and \
           self.scrap_asset_cached_dic[scraper_id]['ROM_base_noext'] == ROM.getBase_noext() and \
           self.scrap_asset_cached_dic[scraper_id]['platform'] == platform:
            selected_game = self.scrap_asset_cached_dic[scraper_id]['game_dic']
            log_debug('_roms_scrap_asset() Cache HIT. Using cached game "{0}"'.format(selected_game['display_name']))
        else:
            log_debug('_roms_scrap_asset() Cache MISS. Calling scraper_obj.get_search()')
            # --- Call scraper and get a list of games ---
            rom_name_scraping = text_format_ROM_name_for_scraping(ROM.getBase_noext())
            search_results = scraper_obj.get_search(rom_name_scraping, ROM.getBase_noext(), platform)
            log_debug('{0} scraper found {1} result/s'.format(A.name, len(search_results)))
            if not search_results:
                log_debug('{0} scraper did not found any game'.format(A.name))
                return ret_asset_path

            # --- Choose game to download image ---
            if scraping_mode == 0:
                if len(search_results) == 1:
                    log_debug('get_search() returned 1 game. Automatically selected.')
                    selected_game_index = 0
                else:
                    log_debug('{0} semi-automatic scraping. User chooses game.'.format(A.name))
                    # >> Close progress dialog (and check it was not canceled)
                    if self.pDialog.iscanceled(): self.pDialog_canceled = True
                    self.pDialog.close()

                    # >> Display game list found so user choses
                    rom_name_list = []
                    for game in search_results:
                        rom_name_list.append(game['display_name'])
                    selected_game_index = xbmcgui.Dialog().select(
                        '{0} game for ROM "{1}"'.format(scraper_obj.name, ROM.getBase_noext()),
                        rom_name_list)
                    if selected_game_index < 0: selected_game_index = 0

                    # >> Open progress dialog again
                    self.pDialog.create('Advanced Emulator Launcher')
                    if not self.pDialog_verbose: self.pDialog.update(self.progress_number, self.file_text)
            elif scraping_mode == 1:
                log_debug('{0} automatic scraping. Selecting first result.'.format(A.name))
                selected_game_index = 0
            else:
                log_error('{0} invalid scraping_mode {1}'.format(A.name, scraping_mode))
                selected_game_index = 0

            # --- Cache selected game from get_search() ---
            self.scrap_asset_cached_dic[scraper_id] = {
                'ROM_base_noext' : ROM.getBase_noext(),
                'platform' : platform,
                'game_dic' : search_results[selected_game_index]
            }
            selected_game = self.scrap_asset_cached_dic[scraper_id]['game_dic']
            log_error('_roms_scrap_asset() Caching selected game "{0}"'.format(selected_game['display_name']))
            log_error('_roms_scrap_asset() Scraper object ID {0} (name {1})'.format(id(scraper_obj), scraper_obj.name))

        # --- Grab list of images for the selected game ---
        # >> ::get_images() always caches URLs for a given selected_game internally.
        if self.pDialog_verbose:
            scraper_text = 'Scraping {0} with {1}. Getting list of images ...'.format(A.name, scraper_obj.name)
            self.pDialog.update(self.progress_number, self.file_text, scraper_text)
        image_list = scraper_obj.get_images(selected_game, asset_kind)
        log_verb('{0} scraper returned {1} images'.format(A.name, len(image_list)))
        if not image_list:
            log_debug('{0} scraper get_images() returned no images.'.format(A.name))
            return ret_asset_path

        # --- Semi-automatic scraping (user choses an image from a list) ---
        if scraping_mode == 0:
            # >> If there is a local image add it to the list and show it to the user
            if os.path.isfile(local_asset_path):
                image_list.insert(0, {'name'       : 'Current local image', 
                                      'id'         : local_asset_path,
                                      'URL'        : local_asset_path,
                                      'asset_kind' : asset_kind})

            # >> If image_list has only 1 element do not show select dialog. Note that the length
            # >> of image_list is 1 only if scraper returned 1 image and a local image does not exist.
            if len(image_list) == 1:
                image_selected_index = 0
            else:
                # >> Close progress dialog before opening image chosing dialog
                if self.pDialog.iscanceled(): self.pDialog_canceled = True
                self.pDialog.close()

                # >> Convert list returned by scraper into a list the select window uses
                ListItem_list = []
                for item in image_list:
                    listitem_obj = xbmcgui.ListItem(label = item['name'], label2 = item['URL'])
                    listitem_obj.setArt({'icon' : item['URL']})
                    ListItem_list.append(listitem_obj)
                image_selected_index = xbmcgui.Dialog().select('Select {0} image'.format(A.name),
                                                               list = ListItem_list, useDetails = True)
                log_debug('{0} dialog returned index {1}'.format(A.name, image_selected_index))
                if image_selected_index < 0: image_selected_index = 0

                # >> Reopen progress dialog
                self.pDialog.create('Advanced Emulator Launcher')
                if not self.pDialog_verbose: self.pDialog.update(self.progress_number, self.file_text)
        # --- Automatic scraping. Pick first image. ---
        else:
            image_selected_index = 0
        selected_image = image_list[image_selected_index]

        # --- Update progress dialog ---
        if self.pDialog_verbose:
            scraper_text = 'Scraping {0} with {1}. Downloading image ...'.format(A.name, scraper_obj.name)
            self.pDialog.update(self.progress_number, self.file_text, scraper_text)

        # --- If user chose the local image don't download anything ---
        if selected_image['id'] != local_asset_path:
            log_debug('_roms_scrap_asset() Downloading selected image ...')

            # --- Resolve image URL ---
            image_url, image_ext = scraper_obj.resolve_image_URL(selected_image)
            log_debug('Selected image URL "{1}"'.format(A.name, image_url))

            # ~~~ Download image ~~~
            image_path = asset_path_noext_FN.append(image_ext).getPath()
            log_verb('Downloading URL  "{0}"'.format(image_url))
            log_verb('Into local file  "{0}"'.format(image_path))
            try:
                net_download_img(image_url, image_path)
            except socket.timeout:
                kodi_notify_warn('Cannot download {0} image (Timeout)'.format(A.name))

            # ~~~ Update Kodi cache with downloaded image ~~~
            # Recache only if local image is in the Kodi cache, this function takes care of that.
            kodi_update_image_cache(image_path)

            # --- Return value is downloaded image ---
            ret_asset_path = image_path
        else:
            log_debug('_roms_scrap_asset() User chose local {0} "{1}"'.format(A.name, local_asset_path))
            ret_asset_path = local_asset_path

        # --- Returned value ---
        return ret_asset_path

    # ---------------------------------------------------------------------------------------------
    # Metadata scrapers
    # ---------------------------------------------------------------------------------------------
    #
    # Called when editing a ROM by _command_edit_rom()
    # Always do semi-automatic scraping when editing ROMs/Launchers.
    # launcherID = '0' if scraping ROM in Favourites
    # roms are editing using Python arguments passed by assignment. Caller is responsible of
    # saving the ROMs XML file.
    #
    # Returns:
    #   True   Changes were made.
    #   False  Changes not made. No need to save ROMs XML/Update container
    #
    def _gui_scrap_rom_metadata(self, categoryID, launcherID, romID, roms, scraper_obj):
        # --- Grab ROM info and metadata scraper settings ---
        # >> ROM in favourites
        if categoryID == VCATEGORY_FAVOURITES_ID:
            platform = roms[romID]['platform']
        elif categoryID == VCATEGORY_COLLECTIONS_ID:
            platform = roms[romID]['platform']
        else:
            launcher = self.launchers[launcherID]
            platform = launcher['platform']
        ROM      = FileName(roms[romID]['filename'])
        rom_name = roms[romID]['m_name']
        scan_clean_tags            = self.settings['scan_clean_tags']
        scan_ignore_scrapped_title = self.settings['scan_ignore_scrap_title']
        log_info('_gui_scrap_rom_metadata() ROM "{0}"'.format(rom_name))

        # --- Ask user to enter ROM metadata search string ---
        keyboard = xbmc.Keyboard(rom_name, 'Enter the ROM search string ...')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return False
        search_string = keyboard.getText()

        # --- Do a search and get a list of games ---
        # >> Prevent race conditions
        kodi_busydialog_ON()
        results = scraper_obj.get_search(search_string, ROM.getBase_noext(), platform)
        kodi_busydialog_OFF()
        log_verb('_gui_scrap_rom_metadata() Metadata scraper found {0} result/s'.format(len(results)))
        if not results:
            kodi_notify_warn('Scraper found no game matches')
            return False

        # --- Display corresponding game list found so user choses ---
        rom_name_list = []
        for game in results: rom_name_list.append(game['display_name'])
        # >> If there is only one item in the list then don't show select dialog
        if len(rom_name_list) == 1:
            selectgame = 0
        else:
            selectgame = xbmcgui.Dialog().select('Select game for ROM {0}'.format(rom_name), rom_name_list)
            if selectgame < 0: return False
        log_verb('_gui_scrap_rom_metadata() User chose game "{0}"'.format(rom_name_list[selectgame]))

        # --- Grab metadata for selected game ---
        # >> Prevent race conditions
        kodi_busydialog_ON()
        gamedata = scraper_obj.get_metadata(results[selectgame])
        kodi_busydialog_OFF()
        if not gamedata:
            kodi_notify_warn('Cannot download game metadata.')
            return False

        # --- Put metadata into ROM dictionary ---
        # >> Ignore scraped title
        if scan_ignore_scrapped_title:
            roms[romID]['m_name'] = text_format_ROM_title(ROM.getBase_noext(), scan_clean_tags)
            log_debug('User wants to ignore scraper name. Setting name to "{0}"'.format(roms[romID]['m_name']))
        # >> Use scraped title
        else:
            roms[romID]['m_name'] = gamedata['title']
            log_debug('User wants scrapped name. Setting name to "{0}"'.format(roms[romID]['m_name']))
        roms[romID]['m_year']      = gamedata['year']
        roms[romID]['m_genre']     = gamedata['genre']
        roms[romID]['m_developer'] = gamedata['developer']
        roms[romID]['m_nplayers']  = gamedata['nplayers']
        roms[romID]['m_esrb']      = gamedata['esrb']
        roms[romID]['m_plot']      = gamedata['plot']

        # >> Changes were made, return True
        kodi_notify('ROM metadata updated')

        return True

    #
    # Called when editing a launcher by _command_edit_launcher()
    # Note that launcher maybe a ROM launcher or a standalone launcher (game, app)
    # Scrap standalone launcher (typically a game) metadata
    # Called when editing a launcher...
    # Always do semi-automatic scraping when editing ROMs/Launchers
    #
    # Returns:
    #   True   Changes were made.
    #   False  Changes not made. No need to save ROMs XML/Update container
    #
    def _gui_scrap_launcher_metadata(self, launcherID, scraper_obj):
        launcher = self.launchers[launcherID]
        launcher_name = launcher['m_name']
        platform = launcher['platform']

        # Edition of the launcher name
        keyboard = xbmc.Keyboard(launcher_name, 'Enter the launcher search string ...')
        keyboard.doModal()
        if not keyboard.isConfirmed(): return False
        search_string = keyboard.getText()

        # Scrap and get a list of matches
        kodi_busydialog_ON()
        results = scraper_obj.get_search(search_string, '', platform)
        kodi_busydialog_OFF()
        log_debug('_gui_scrap_launcher_metadata() Metadata scraper found {0} result/s'.format(len(results)))
        if not results:
            kodi_notify_warn('Scraper found no matches')
            return False

        # Display corresponding game list found so user choses
        rom_name_list = []
        for game in results: rom_name_list.append(game['display_name'])
        if len(rom_name_list) == 1:
            selectgame = 0
        else:
            selectgame = xbmcgui.Dialog().select('Select item for Launcher {0}'.format(launcher_name), rom_name_list)
            if selectgame < 0: return False

        # --- Grab metadata for selected game ---
        # >> Prevent race conditions
        kodi_busydialog_ON()
        gamedata = scraper_obj.get_metadata(results[selectgame])
        kodi_busydialog_OFF()
        if not gamedata:
            kodi_notify_warn('Cannot download game metadata.')
            return False

        # --- Put metadata into launcher dictionary ---
        # >> Scraper should not change launcher title
        self.launchers[launcherID]['m_year']   = gamedata['year']
        self.launchers[launcherID]['m_genre']  = gamedata['genre']
        self.launchers[launcherID]['m_studio'] = gamedata['studio']
        self.launchers[launcherID]['m_plot']   = gamedata['plot']

        # >> Changes were made
        return True

    #
    # Edit category/launcher/rom asset.
    #
    # NOTE Scrapers are loaded by the _command_edit_* functions (caller of this function).
    # NOTE When editing ROMs optional parameter launcher_dic is required.
    # NOTE Caller is responsible for saving the Categories/Launchers/ROMs.
    # NOTE if image is changed container should be updated so the user sees new image instantly.
    # NOTE object_dic is edited by assigment.
    # NOTE A ROM in Favourites has categoryID = VCATEGORY_FAVOURITES_ID.
    #      a ROM in a collection categoryID = VCATEGORY_COLLECTIONS_ID.
    #
    # Returns:
    #   True   Changes made. Categories/Launchers/ROMs must be saved and container updated
    #   False  No changes were made. No necessary to refresh container
    #
    def _gui_edit_asset(self, object_kind, asset_kind, object_dic, categoryID = '', launcherID = ''):
        # --- Get asset object information ---
        # Select/Import require: object_name, A, asset_path_noext
        #
        # Scraper additionaly requires: current_asset_path, scraper_obj, platform, rom_base_noext
        #
        if object_kind == KIND_CATEGORY:
            # --- Grab asset information for editing ---
            object_name = 'Category'
            AInfo = assets_get_info_scheme(asset_kind)
            asset_directory = FileName(self.settings['categories_asset_dir'])
            asset_path_noext = assets_get_path_noext_SUFIX(AInfo, asset_directory, object_dic['m_name'], object_dic['id'])
            log_info('_gui_edit_asset() Editing Category "{0}"'.format(AInfo.name))
            log_info('_gui_edit_asset() ID {0}'.format(object_dic['id']))
            log_debug('_gui_edit_asset() asset_directory  "{0}"'.format(asset_directory.getOriginalPath()))
            log_debug('_gui_edit_asset() asset_path_noext "{0}"'.format(asset_path_noext.getOriginalPath()))
            if not asset_directory.isdir():
                kodi_dialog_OK('Directory to store Category artwork not configured or not found. '
                               'Configure it before you can edit artwork.')
                return False

        elif object_kind == KIND_COLLECTION:
            # --- Grab asset information for editing ---
            object_name = 'Collection'
            AInfo = assets_get_info_scheme(asset_kind)
            asset_directory = FileName(self.settings['collections_asset_dir'])
            asset_path_noext = assets_get_path_noext_SUFIX(AInfo, asset_directory, object_dic['m_name'], object_dic['id'])
            log_info('_gui_edit_asset() Editing Collection "{0}"'.format(AInfo.name))
            log_info('_gui_edit_asset() ID {0}'.format(object_dic['id']))
            log_debug('_gui_edit_asset() asset_directory  "{0}"'.format(asset_directory.getOriginalPath()))
            log_debug('_gui_edit_asset() asset_path_noext "{0}"'.format(asset_path_noext.getOriginalPath()))
            if not asset_directory.isdir():
                kodi_dialog_OK('Directory to store Collection artwork not configured or not found. '
                               'Configure it before you can edit artwork.')
                return False

        elif object_kind == KIND_LAUNCHER:
            # --- Grab asset information for editing ---
            object_name = 'Launcher'
            AInfo = assets_get_info_scheme(asset_kind)
            asset_directory = FileName(self.settings['launchers_asset_dir'])
            asset_path_noext = assets_get_path_noext_SUFIX(AInfo, asset_directory, object_dic['m_name'], object_dic['id'])
            log_info('_gui_edit_asset() Editing Launcher "{0}"'.format(AInfo.name))
            log_info('_gui_edit_asset() ID {0}'.format(object_dic['id']))
            log_debug('_gui_edit_asset() asset_directory  "{0}"'.format(asset_directory.getOriginalPath()))
            log_debug('_gui_edit_asset() asset_path_noext "{0}"'.format(asset_path_noext.getOriginalPath()))
            if not asset_directory.isdir():
                kodi_dialog_OK('Directory to store Launcher artwork not configured or not found. '
                               'Configure it before you can edit artwork.')
                return False

        elif object_kind == KIND_ROM:
            # --- Grab asset information for editing ---
            object_name = 'ROM'
            ROMfile = FileName(object_dic['filename'])
            AInfo   = assets_get_info_scheme(asset_kind)
            if categoryID == VCATEGORY_FAVOURITES_ID:
                log_info('_gui_edit_asset() ROM is in Favourites')
                asset_directory  = FileName(self.settings['favourites_asset_dir'])
                platform         = object_dic['platform']
                asset_path_noext = assets_get_path_noext_SUFIX(AInfo, asset_directory, ROMfile.getBase_noext(), object_dic['id'])
            elif categoryID == VCATEGORY_COLLECTIONS_ID:
                log_info('_gui_edit_asset() ROM is in Collection')
                asset_directory  = FileName(self.settings['collections_asset_dir'])
                platform         = object_dic['platform']
                asset_path_noext = assets_get_path_noext_SUFIX(AInfo, asset_directory, ROMfile.getBase_noext(), object_dic['id'])
            else:
                log_info('_gui_edit_asset() ROM is in Launcher id {0}'.format(launcherID))
                launcher         = self.launchers[launcherID]
                asset_directory  = FileName(launcher[AInfo.path_key])
                platform         = launcher['platform']
                asset_path_noext = assets_get_path_noext_DIR(AInfo, asset_directory, ROMfile)
            current_asset_path = FileName(object_dic[AInfo.key])
            log_info('_gui_edit_asset() Editing ROM {0}'.format(AInfo.name))
            log_info('_gui_edit_asset() ROM ID {0}'.format(object_dic['id']))
            log_debug('_gui_edit_asset() asset_directory    "{0}"'.format(asset_directory.getOriginalPath()))
            log_debug('_gui_edit_asset() asset_path_noext   "{0}"'.format(asset_path_noext.getOriginalPath()))
            log_debug('_gui_edit_asset() current_asset_path "{0}"'.format(current_asset_path.getOriginalPath()))
            log_debug('_gui_edit_asset() platform           "{0}"'.format(platform))

            # --- Do not edit asset if asset directory not configured ---
            if not asset_directory.isdir():
                kodi_dialog_OK('Directory to store {0} not configured or not found. '.format(AInfo.name) + \
                               'Configure it before you can edit artwork.')
                return False

        else:
            log_error('_gui_edit_asset() Unknown object_kind = {0}'.format(object_kind))
            kodi_notify_warn("Unknown object_kind '{0}'".format(object_kind))
            return False

        # --- Only enable scraper if support the asset ---
        # >> Scrapers only loaded if editing a ROM
        if object_kind == KIND_ROM:
            scraper_obj_list  = []
            scraper_menu_list = []
            for scrap_obj in scrapers_asset:
                if scrap_obj.supports_asset(asset_kind):
                    scraper_obj_list.append(scrap_obj)
                    scraper_menu_list.append('Scrape {0} from {1}'.format(AInfo.name, scrap_obj.name))
                    log_verb('Scraper {0} supports scraping {1}'.format(scrap_obj.name, AInfo.name))
                else:
                    log_verb('Scraper {0} does not support scraping {1}'.format(scrap_obj.name, AInfo.name))
                    log_verb('Scraper DISABLED')

        # --- Show image editing options ---
        # >> Scrape only supported for ROMs (for the moment)
        dialog = xbmcgui.Dialog()
        common_menu_list = ['Select local {0}'.format(AInfo.kind_str),
                            'Import local {0} (copy and rename)'.format(AInfo.kind_str),
                            'Unset artwork/asset',]
        if object_kind == KIND_ROM:
            type2 = dialog.select('Change {0} {1}'.format(AInfo.name, AInfo.kind_str),
                                  common_menu_list + scraper_menu_list)
        else:
            type2 = dialog.select('Change {0} {1}'.format(AInfo.name, AInfo.kind_str), common_menu_list)
        # >> User canceled select box ---
        if type2 < 0: return False

        # --- Link to a local image ---
        if type2 == 0:
            image_dir = FileName(object_dic[AInfo.key]).getDir() if object_dic[AInfo.key] else ''

            log_debug('_gui_edit_asset() Initial path "{0}"'.format(image_dir))
            # >> ShowAndGetFile dialog
            dialog = xbmcgui.Dialog()
            if asset_kind == ASSET_MANUAL or asset_kind == ASSET_TRAILER:
                image_file = dialog.browse(1, 'Select {0} {1}'.format(AInfo.name, AInfo.kind_str), 'files',
                                           AInfo.exts_dialog, True, False, image_dir)
            # >> ShowAndGetImage dialog
            else:
                image_file = dialog.browse(2, 'Select {0} {1}'.format(AInfo.name, AInfo.kind_str), 'files',
                                           AInfo.exts_dialog, True, False, image_dir)
            if not image_file: return False
            image_file_path = FileName(image_file)
            if not image_file or not image_file_path.exists(): return False

            # --- Update object by assigment. XML/JSON will be save by parent ---
            log_debug('_gui_edit_asset() AInfo.key "{0}"'.format(AInfo.key))
            object_dic[AInfo.key] = image_file_path.getOriginalPath()
            kodi_notify('{0} {1} has been updated'.format(object_name, AInfo.name))
            log_info('_gui_edit_asset() Linked {0} {1} "{2}"'.format(object_name, AInfo.name, image_file_path.getOriginalPath()))

            # --- Update Kodi image cache ---
            kodi_update_image_cache(image_file_path.getOriginalPath())

        # --- Import an image ---
        # >> Copy and rename a local image into asset directory
        elif type2 == 1:
            # >> If assets exists start file dialog from current asset directory
            image_dir = ''
            if object_dic[AInfo.key]: image_dir = FileName(object_dic[AInfo.key]).getDir()
            log_debug('_gui_edit_asset() Initial path "{0}"'.format(image_dir))
            image_file = xbmcgui.Dialog().browse(2, 'Select {0} image'.format(AInfo.name), 'files',
                                                 AInfo.exts_dialog, True, False, image_dir)
            image_FileName = FileName(image_file)
            if not image_FileName.exists(): return False

            # >> Determine image extension and dest filename. Check for errors.
            dest_path_FileName = asset_path_noext.append(image_FileName.getExt())
            log_debug('_gui_edit_asset() image_file   "{0}"'.format(image_FileName.getOriginalPath()))
            log_debug('_gui_edit_asset() img_ext      "{0}"'.format(image_FileName.getExt()))
            log_debug('_gui_edit_asset() dest_path    "{0}"'.format(dest_path_FileName.getOriginalPath()))
            if image_FileName.getPath() == dest_path_FileName.getPath():
                log_info('_gui_edit_asset() image_FileName and dest_path_FileName are the same. Returning.')
                kodi_notify_warn('image_FileName and dest_path_FileName are the same. Returning')
                return False

            # --- Copy image file ---
            try:
                fs_encoding = get_fs_encoding()
                shutil.copy(image_FileName.getPath().decode(fs_encoding), dest_path_FileName.getPath().decode(fs_encoding))
            except OSError:
                log_error('_gui_edit_asset() OSError exception copying image')
                kodi_notify_warn('OSError exception copying image')
                return False
            except IOError:
                log_error('_gui_edit_asset() IOError exception copying image')
                kodi_notify_warn('IOError exception copying image')
                return False

            # >> Update object by assigment. XML will be save by parent.
            # >> Always store original/raw paths in database.
            object_dic[AInfo.key] = dest_path_FileName.getOriginalPath()
            kodi_notify('{0} {1} has been updated'.format(object_name, AInfo.name))
            log_info('_gui_edit_asset() Copied file  "{0}"'.format(image_FileName.getOriginalPath()))
            log_info('_gui_edit_asset() Into         "{0}"'.format(dest_path_FileName.getOriginalPath()))
            log_info('_gui_edit_asset() Selected {0} {1} "{2}"'.format(object_name, AInfo.name, dest_path_FileName.getOriginalPath()))

            # --- Update Kodi image cache ---
            kodi_update_image_cache(dest_path_FileName.getOriginalPath())

        # --- Unset asset ---
        elif type2 == 2:
            object_dic[AInfo.key] = ''
            kodi_notify('{0} {1} has been unset'.format(object_name, AInfo.name))
            log_info('_gui_edit_asset() Unset {0} {1}'.format(object_name, AInfo.name))

        # --- Manual scrape and choose from a list of images ---
        # >> Copy asset scrape code into here and remove function _gui_scrap_image_semiautomatic()
        elif type2 >= 3:
            # --- Use the scraper chosen by user ---
            scraper_index = type2 - 3
            scraper_obj   = scraper_obj_list[scraper_index]
            log_debug('_gui_edit_asset() Scraper index {0}'.format(scraper_index))
            log_debug('_gui_edit_asset() User chose scraper "{0}"'.format(scraper_obj.name))

            # --- Initialise asset scraper ---
            # region        = self.settings['scraper_region']
            # thumb_imgsize = self.settings['scraper_thumb_size']
            # scraper_obj.set_options(region, thumb_imgsize)
            # >> Must be like this: scraper_obj.set_options(self.settings)
            # log_debug('_gui_edit_asset() Initialised scraper "{0}"'.format(scraper_obj.name))

            # --- Ask user to edit the image search string ---
            keyboard = xbmc.Keyboard(object_dic['m_name'], 'Enter the string to search for ...')
            keyboard.doModal()
            if not keyboard.isConfirmed(): return False
            search_string = keyboard.getText().decode('utf-8')

            # --- Call scraper and get a list of games ---
            # IMPORTANT Setting Kodi busy notification prevents the user to control the UI when a dialog with handler -1
            #           has been called and nothing is displayed.
            #           THIS PREVENTS THE RACE CONDITIONS THAT CAUSE TROUBLE IN ADVANCED LAUNCHER!!!
            kodi_busydialog_ON()
            results = scraper_obj.get_search(search_string, ROMfile.getBase_noext(), platform)
            kodi_busydialog_OFF()
            log_debug('{0} scraper found {1} result/s'.format(AInfo.name, len(results)))
            if not results:
                kodi_dialog_OK('Scraper found no matching games.')
                log_debug('{0} scraper did not found any game'.format(AInfo.name))
                return False

            # --- Choose game to download image ---
            if len(results) == 1:
                selectgame = 0
            else:
                # >> Display corresponding game list found so user choses
                rom_name_list = []
                for game in results:
                    rom_name_list.append(game['display_name'])
                selectgame = xbmcgui.Dialog().select('Select game for "{0}"'.format(search_string), rom_name_list)
                if selectgame < 0: return False

            # --- Grab list of images for the selected game ---
            # >> Prevent race conditions
            kodi_busydialog_ON()
            image_list = scraper_obj.get_images(results[selectgame], asset_kind)
            kodi_busydialog_OFF()
            log_verb('{0} scraper returned {1} images'.format(AInfo.name, len(image_list)))
            if not image_list:
                kodi_dialog_OK('Scraper found no {0} '.format(AInfo.name) + 
                               'images for game "{0}".'.format(results[selectgame]['display_name']))
                return False

            # --- Always do semi-automatic scraping when editing images ---
            # If there is a local image add it to the list and show it to the user
            if current_asset_path.exists():
                image_list.insert(0, {'name'       : 'Current local image', 
                                      'id'         : current_asset_path.getPath(),
                                      'URL'        : current_asset_path.getPath(),
                                      'asset_kind' : asset_kind})

            # >> Convert list returned by scraper into a list the select window uses
            ListItem_list = []
            for item in image_list:
                listitem_obj = xbmcgui.ListItem(label = item['name'], label2 = item['URL'])
                listitem_obj.setArt({'icon' : item['URL']})
                ListItem_list.append(listitem_obj)
            # >> If there are no items in the list is because there is no current asst and scraper
            # >> found nothing. Return.
            if len(ListItem_list) == 0:
                log_debug('_gui_edit_asset() ListItem_list is empty. Returning.')
                return False
            # >> If there is only one item in the list do not show select dialog
            elif len(ListItem_list) == 1:
                log_debug('_gui_edit_asset() ListItem_list has one element. Do not show select dialog.')
                image_selected_index = 0
            else:
                image_selected_index = xbmcgui.Dialog().select('Select image', list = ListItem_list, useDetails = True)
                log_debug('{0} dialog returned index {1}'.format(AInfo.name, image_selected_index))
            # >> User cancelled dialog
            if image_selected_index < 0:
                log_debug('_gui_edit_asset() User cancelled image select dialog. Returning.')
                return False

            # >> User choose local image
            if image_list[image_selected_index]['URL'] == current_asset_path.getPath():
               log_debug('_gui_edit_asset() Selected current image "{0}"'.format(current_asset_path.getPath()))
               return False
            else:
                log_debug('_gui_edit_asset() Downloading selected image ...')
                # >> Resolve asset URL
                kodi_busydialog_ON()
                image_url, image_ext = scraper_obj.resolve_image_URL(image_list[image_selected_index])
                kodi_busydialog_OFF()
                log_debug('Resolved {0} URL "{1}"'.format(AInfo.name, image_url))
                log_debug('URL extension "{0}"'.format(image_ext))
                if not image_url or not image_ext:
                    log_error('_gui_edit_asset() image_url or image_ext empty/not set')
                    return False

                # ~~~ Download image ~~~
                image_local_path = asset_path_noext.append(image_ext).getPath()
                log_verb('Downloading URL "{0}"'.format(image_url))
                log_verb('Into local file "{0}"'.format(image_local_path))
                kodi_busydialog_ON()
                try:
                    net_download_img(image_url, image_local_path)
                except socket.timeout:
                    kodi_notify_warn('Cannot download {0} image (Timeout)'.format(image_name))
                kodi_busydialog_OFF()

                # ~~~ Update Kodi cache with downloaded image ~~~
                # Recache only if local image is in the Kodi cache, this function takes care of that.
                kodi_update_image_cache(image_local_path)

                # --- Notify user ---
                kodi_notify('Downloaded {0} with {1} scraper'.format(AInfo.name, scraper_obj.name))

            # --- Edit using Python pass by assigment ---
            # >> If we reach this point is because an image was downloaded
            # >> Caller is responsible to save Categories/Launchers/ROMs
            object_dic[AInfo.key] = image_local_path

        # >> If we reach this point, changes were made.
        # >> Categories/Launchers/ROMs must be saved, container must be refreshed.
        return True

    #
    # Creates default categories data struct.
    # CAREFUL deletes current categories!
    #
    def _cat_create_default(self):
        # The key in the categories dictionary is an MD5 hash generate with current time plus some 
        # random number. This will make it unique and different for every category created.
        category = fs_new_category()
        category_key = misc_generate_random_SID()
        category['id']      = category_key
        category['m_name']  = 'Emulators'
        category['m_genre'] = 'Emulators'
        category['m_plot']  = 'Initial AEL category.'
        self.categories = {}
        self.launchers = {}
        self.categories[category_key] = category

    #
    # Checks if the category is empty (no launchers defined)
    # Returns True if the category is empty. Returns False if non-empty
    def _cat_is_empty(self, categoryID):
        for launcherID in self.launchers.iterkeys():
            if self.launchers[launcherID]['categoryID'] == categoryID: return False

        return True

    #
    # Reads a text file with category/launcher plot. 
    # Checks file size to avoid importing binary files!
    #
    def _gui_import_TXT_file(text_file):
        # Warn user in case he chose a binary file or a very big one. Avoid categories.xml corruption.
        log_debug('_gui_import_TXT_file() Importing plot from "{0}"'.format(text_file.getOriginalPath()))
        statinfo = text_file.stat()
        file_size = statinfo.st_size
        log_debug('_gui_import_TXT_file() File size is {0}'.format(file_size))
        if file_size > 16384:
            ret = kodi_dialog_yesno('File "{0}" has {1} bytes and it is very big.'.format(text_file.getPath(), file_size) +
                                    'Are you sure this is the correct file?')
            if not ret: return ''

        # Import file
        log_debug('_gui_import_TXT_file() Importing description from "{0}"'.format(text_file.getOriginalPath()))
        text_plot = open(text_file.getPath(), 'rt')
        file_data = text_plot.read()
        text_plot.close()

        return file_data

    def _command_import_launchers(self):
        # >> If enableMultiple = True this function always returns a list of strings in UTF-8
        file_list = xbmcgui.Dialog().browse(1, 'Select XML category/launcher configuration file',
                                            'files', '.xml', enableMultiple = True)

        # >> Process file by file
        for xml_file in file_list:
            xml_file_unicode = xml_file.decode('utf-8')
            log_debug('_command_import_launchers() Importing "{0}"'.format(xml_file_unicode))
            import_FN = FileName(xml_file_unicode)
            if not import_FN.exists(): continue
            # >> This function edits self.categories, self.launchers dictionaries
            autoconfig_import_launchers(CATEGORIES_FILE_PATH, ROMS_DIR, self.categories, self.launchers, import_FN)

        # --- Save Categories/Launchers, update timestamp and notify user ---
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        kodi_refresh_container()
        kodi_notify('Finished importing Categories/Launchers')

    #
    # Export AEL launcher configuration
    #
    def _command_export_launchers(self):
        # >> Ask path to export launcher configuration
        dialog = xbmcgui.Dialog()
        dir_path = dialog.browse(0, 'Select XML export directory', 'files', '', False, False).decode('utf-8')
        if not dir_path: return
        export_FN = FileName(dir_path)
        export_FN = export_FN.pjoin('AEL_configuration.xml')

        # --- Export stuff ---        
        # >> This function notifies the user if exporting is succesful.
        autoconfig_export_all(self.categories, self.launchers, export_FN)

    #
    # Checks all databases and tries to update to newer version if possible
    #
    def _command_check_database(self):
        log_debug('_command_check_database() Beginning ....')
        pDialog = xbmcgui.DialogProgress()
        pDialog_canceled = False

        # >> Open Categories/Launchers XML.
        #    XML should be updated automatically on load.
        pDialog.create('Advanced Emulator Launcher', 'Checking Categories/Launchers ...')
        self.categories = {}
        self.launchers = {}
        self.update_timestamp = fs_load_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # >> Traverse and fix Categories.
        for category_id in self.categories:
            category = self.categories[category_id]
            # >> Fix s_thumb -> s_icon renaming
            if category['default_icon'] == 's_thumb':      category['default_icon'] = 's_icon'
            if category['default_fanart'] == 's_thumb':    category['default_fanart'] = 's_icon'
            if category['default_banner'] == 's_thumb':    category['default_banner'] = 's_icon'
            if category['default_poster'] == 's_thumb':    category['default_poster'] = 's_icon'
            if category['default_clearlogo'] == 's_thumb': category['default_clearlogo'] = 's_icon'

            # >> Fix s_flyer -> s_poster renaming
            if category['default_icon'] == 's_flyer':      category['default_icon'] = 's_poster'
            if category['default_fanart'] == 's_flyer':    category['default_fanart'] = 's_poster'
            if category['default_banner'] == 's_flyer':    category['default_banner'] = 's_poster'
            if category['default_poster'] == 's_flyer':    category['default_poster'] = 's_poster'
            if category['default_clearlogo'] == 's_flyer': category['default_clearlogo'] = 's_poster'

        # >> Traverse and fix Launchers.
        for launcher_id in self.launchers:
            launcher = self.launchers[launcher_id]
            # >> Fix s_thumb -> s_icon renaming
            if launcher['default_icon'] == 's_thumb':       launcher['default_icon'] = 's_icon'
            if launcher['default_fanart'] == 's_thumb':     launcher['default_fanart'] = 's_icon'
            if launcher['default_banner'] == 's_thumb':     launcher['default_banner'] = 's_icon'
            if launcher['default_poster'] == 's_thumb':     launcher['default_poster'] = 's_icon'
            if launcher['default_clearlogo'] == 's_thumb':  launcher['default_clearlogo'] = 's_icon'
            if launcher['default_controller'] == 's_thumb': launcher['default_controller'] = 's_icon'

            # >> Fix s_flyer -> s_poster renaming
            if launcher['default_icon'] == 's_flyer':       launcher['default_icon'] = 's_poster'
            if launcher['default_fanart'] == 's_flyer':     launcher['default_fanart'] = 's_poster'
            if launcher['default_banner'] == 's_flyer':     launcher['default_banner'] = 's_poster'
            if launcher['default_poster'] == 's_flyer':     launcher['default_poster'] = 's_poster'
            if launcher['default_clearlogo'] == 's_flyer':  launcher['default_clearlogo'] = 's_poster'
            if launcher['default_controller'] == 's_flyer': launcher['default_controller'] = 's_poster'

        # >> Save categories.xml
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        pDialog.update(100)

        # >> Traverse all launchers. Load ROMs and check every ROMs.
        pDialog.update(0, 'Checking Launcher ROMs ...')
        num_launchers = len(self.launchers)
        processed_launchers = 0
        for launcher_id in self.launchers:
            log_debug('_command_edit_rom() Checking Launcher "{0}"'.format(self.launchers[launcher_id]['m_name']))
            # --- Load standard ROM database ---
            roms = fs_load_ROMs_JSON(ROMS_DIR, self.launchers[launcher_id])
            for rom_id in roms: self._misc_fix_rom_object(roms[rom_id])
            fs_write_ROMs_JSON(ROMS_DIR, self.launchers[launcher_id], roms)

            # --- If exists, load Parent ROM database ---
            parents_roms_base_noext = self.launchers[launcher_id]['roms_base_noext'] + '_parents'
            parents_FN = ROMS_DIR.pjoin(parents_roms_base_noext + '.json')
            if parents_FN.exists():
                roms = fs_load_JSON_file(ROMS_DIR, parents_roms_base_noext)
                for rom_id in roms: self._misc_fix_rom_object(roms[rom_id])
                fs_write_JSON_file(ROMS_DIR, parents_roms_base_noext, roms)

            # >> This updates timestamps and forces regeneration of Virtual Launchers.
            self.launchers[launcher_id]['timestamp_launcher'] = time.time()            

            # >> Update dialog
            processed_launchers += 1
            update_number = (processed_launchers * 100) / num_launchers
            pDialog.update(update_number)
        # >> Save categories.xml because launcher timestamps changed
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)
        pDialog.update(100)

        # >> Load Favourite ROMs and update JSON
        pDialog.update(0, 'Checking Favourite ROMs ...')
        roms_fav = fs_load_Favourites_JSON(FAV_JSON_FILE_PATH)
        num_fav_roms = len(roms_fav)
        processed_fav_roms = 0
        for rom_id in roms_fav:
            # >> Get ROM object
            rom = roms_fav[rom_id]
            self._misc_fix_Favourite_rom_object(rom)
            # >> Update dialog
            processed_fav_roms += 1
            update_number = (float(processed_fav_roms) / float(num_fav_roms)) * 100 
            pDialog.update(int(update_number))
        fs_write_Favourites_JSON(FAV_JSON_FILE_PATH, roms_fav)
        pDialog.update(100)

        # >> Traverse every ROM Collection database and check/update Favourite ROMs.
        (collections, update_timestamp) = fs_load_Collection_index_XML(COLLECTIONS_FILE_PATH)
        pDialog.update(0, 'Checking Collection ROMs ...')
        num_collections = len(collections)
        processed_collections = 0
        for collection_id in collections:
            collection = collections[collection_id]
            # >> Fix collection
            if 'default_thumb' in collection:
                collection['default_icon'] = collection['default_thumb']
                collection.pop('default_thumb')
            if 's_thumb' in collection:
                collection['s_icon'] = collection['s_thumb']
                collection.pop('s_thumb')
            if 's_flyer' in collection:
                collection['s_poster'] = collection['s_flyer']
                collection.pop('s_flyer')
            # >> Fix s_thumb -> s_icon renaming
            if collection['default_icon'] == 's_thumb':      collection['default_icon'] = 's_icon'
            if collection['default_fanart'] == 's_thumb':    collection['default_fanart'] = 's_icon'
            if collection['default_banner'] == 's_thumb':    collection['default_banner'] = 's_icon'
            if collection['default_poster'] == 's_thumb':    collection['default_poster'] = 's_icon'
            if collection['default_clearlogo'] == 's_thumb': collection['default_clearlogo'] = 's_icon'
            # >> Fix s_flyer -> s_poster renaming
            if collection['default_icon'] == 's_flyer':      collection['default_icon'] = 's_poster'
            if collection['default_fanart'] == 's_flyer':    collection['default_fanart'] = 's_poster'
            if collection['default_banner'] == 's_flyer':    collection['default_banner'] = 's_poster'
            if collection['default_poster'] == 's_flyer':    collection['default_poster'] = 's_poster'
            if collection['default_clearlogo'] == 's_flyer': collection['default_clearlogo'] = 's_poster'

            # >> Fix collection ROMs
            roms_json_file = COLLECTIONS_DIR.pjoin(collection['roms_base_noext'] + '.json')
            collection_rom_list = fs_load_Collection_ROMs_JSON(roms_json_file)
            for rom in collection_rom_list: self._misc_fix_Favourite_rom_object(rom)
            fs_write_Collection_ROMs_JSON(roms_json_file, collection_rom_list)
            # >> Update progress dialog
            processed_collections += 1
            update_number = (float(processed_collections) / float(num_collections)) * 100 
            pDialog.update(int(update_number))
        # >> Save ROM Collection index
        fs_write_Collection_index_XML(COLLECTIONS_FILE_PATH, collections)
        pDialog.update(100)

        # >> Load Most Played ROMs and check/update.
        pDialog.update(0, 'Checking Most Played ROMs ...')
        most_played_roms = fs_load_Favourites_JSON(MOST_PLAYED_FILE_PATH)
        for rom_id in most_played_roms:
            rom = most_played_roms[rom_id]
            self._misc_fix_Favourite_rom_object(rom)
        fs_write_Favourites_JSON(MOST_PLAYED_FILE_PATH, most_played_roms)
        pDialog.update(100)

        # >> Load Recently Played ROMs and check/update.
        pDialog.update(0, 'Checking Recently Played ROMs ...')
        recent_roms_list = fs_load_Collection_ROMs_JSON(RECENT_PLAYED_FILE_PATH)
        for rom in recent_roms_list: self._misc_fix_Favourite_rom_object(rom)
        fs_write_Collection_ROMs_JSON(RECENT_PLAYED_FILE_PATH, recent_roms_list)
        pDialog.update(100)
        pDialog.close()

        # >> So long and thanks for all the fish.
        kodi_notify('All databases checked')
        log_debug('_command_check_database() Exiting')

    #
    # ROM dictionary is edited by Python passing by assigment
    #
    def _misc_fix_rom_object(self, rom):
        # --- Add new fields if not present ---
        if 'm_nplayers'    not in rom: rom['m_nplayers']    = ''
        if 'm_esrb'        not in rom: rom['m_esrb']        = ESRB_PENDING
        if 'disks'         not in rom: rom['disks']         = []
        if 'pclone_status' not in rom: rom['pclone_status'] = PCLONE_STATUS_NONE
        if 'cloneof'       not in rom: rom['cloneof']       = ''
        # --- Delete unwanted/obsolete stuff ---
        if 'nointro_isClone' in rom: rom.pop('nointro_isClone')
        # --- DB field renamings ---
        if 'm_studio' in rom:
            rom['m_developer'] = rom['m_studio']
            rom.pop('m_studio')

    def _misc_fix_Favourite_rom_object(self, rom):
        # --- Fix standard ROM fields ---
        self._misc_fix_rom_object(rom)

        # --- Favourite ROMs additional stuff ---
        if 'args_extra' not in rom: rom['args_extra'] = []
        if 'non_blocking' not in rom: rom['non_blocking'] = False
        if 'roms_default_thumb' in rom:
            rom['roms_default_icon'] = rom['roms_default_thumb']
            rom.pop('roms_default_thumb')

    def _command_check_launchers(self):
        log_info('_command_check_launchers() Checking all Launchers configuration ...')

        main_str_list = []
        main_str_list.append('Number of launchers: {0}\n\n'.format(len(self.launchers)))
        for launcher_id in sorted(self.launchers, key = lambda x : self.launchers[x]['m_name']):
            launcher = self.launchers[launcher_id]
            l_str = []
            main_str_list.append('[COLOR orange]Launcher "{0}"[/COLOR]\n'.format(launcher['m_name']))

            # >> Check that platform is on AEL official platform list
            platform = launcher['platform']
            if platform not in AEL_platform_list:
                l_str.append('Unrecognised platform "{0}"\n'.format(platform))

            # >> Check that category exists
            categoryID = launcher['categoryID']
            if categoryID != VCATEGORY_ADDONROOT_ID and categoryID not in self.categories:
                l_str.append('Category not found (unlinked launcher)\n')

            # >> Check that application exists
            app_FN = FileName(launcher['application'])
            if not app_FN.exists():
                l_str.append('Application "{0}" not found\n'.format(app_FN.getPath()))

            # >> Check that rompath exists if rompath is not empty
            # >> Empty rompath means standalone launcher
            rompath = launcher['rompath']
            rompath_FN = FileName(rompath)
            if rompath and not rompath_FN.exists():
                l_str.append('ROM path "{0}" not found\n'.format(rompath_FN.getPath()))

            # >> Check that DAT file exists if not empty
            nointro_xml_file = launcher['nointro_xml_file']
            nointro_xml_file_FN = FileName(nointro_xml_file)
            if nointro_xml_file and not nointro_xml_file_FN.exists():
                l_str.append('DAT file "{0}" not found\n'.format(nointro_xml_file_FN.getPath()))

            # >> Test that artwork files exist if not empty (s_* fields)
            self._aux_check_for_file(l_str, 's_icon', launcher)
            self._aux_check_for_file(l_str, 's_fanart', launcher)
            self._aux_check_for_file(l_str, 's_banner', launcher)
            self._aux_check_for_file(l_str, 's_poster', launcher)
            self._aux_check_for_file(l_str, 's_clearlogo', launcher)
            self._aux_check_for_file(l_str, 's_controller', launcher)
            self._aux_check_for_file(l_str, 's_trailer', launcher)

            # >> Test that ROM_asset_path exists if not empty
            ROM_asset_path = launcher['ROM_asset_path']
            ROM_asset_path_FN = FileName(ROM_asset_path)
            if ROM_asset_path and not ROM_asset_path_FN.exists():
                l_str.append('ROM_asset_path "{0}" not found\n'.format(ROM_asset_path_FN.getPath()))

            # >> Test that ROM asset paths exist if not empty (path_* fields)
            self._aux_check_for_file(l_str, 'path_title', launcher)
            self._aux_check_for_file(l_str, 'path_snap', launcher)
            self._aux_check_for_file(l_str, 'path_boxfront', launcher)
            self._aux_check_for_file(l_str, 'path_boxback', launcher)
            self._aux_check_for_file(l_str, 'path_cartridge', launcher)
            self._aux_check_for_file(l_str, 'path_fanart', launcher)
            self._aux_check_for_file(l_str, 'path_banner', launcher)
            self._aux_check_for_file(l_str, 'path_clearlogo', launcher)
            self._aux_check_for_file(l_str, 'path_flyer', launcher)
            self._aux_check_for_file(l_str, 'path_map', launcher)
            self._aux_check_for_file(l_str, 'path_manual', launcher)
            self._aux_check_for_file(l_str, 'path_trailer', launcher)

            # >> Check for duplicate asset paths
            
            # >> If l_str is empty is because no problems were found.
            if l_str:
                main_str_list.extend(l_str)
            else:
                main_str_list.append('No problems found\n')
            main_str_list.append('\n')

        # >> Stats report
        log_info('Writing report file "{0}"'.format(LAUNCHER_REPORT_FILE_PATH.getPath()))
        full_string = ''.join(main_str_list).encode('utf-8')
        file = open(LAUNCHER_REPORT_FILE_PATH.getPath(), 'w')
        file.write(full_string)
        file.close()

        # >> Display report TXT file.
        log_debug('Setting Window(10000) Property "FontWidth" = "monospaced"')
        xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
        dialog = xbmcgui.Dialog()
        dialog.textviewer('Launchers report', full_string)
        log_debug('Setting Window(10000) Property "FontWidth" = "proportional"')
        xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

    def _aux_check_for_file(self, str_list, dic_key_name, launcher):
        path = launcher[dic_key_name]
        path_FN = FileName(path)
        if path and not path_FN.exists():
            problems_found = True
            str_list.append('{0} "{1}" not found\n'.format(dic_key_name, path_FN.getPath()))

    def _command_check_retro_BIOS(self):
        log_info('_command_check_retro_BIOS() Checking Retroarch BIOSes ...')
        check_only_mandatory = self.settings['io_retroarch_only_mandatory']
        log_info('_command_check_retro_BIOS() check_only_mandatory = {0}'.format(check_only_mandatory))

        # >> If Retroarch System dir not configured or found abort.
        sys_dir_FN = FileName(self.settings['io_retroarch_sys_dir'])
        if not sys_dir_FN.exists():
            kodi_dialog_OK('Retroarch System directory not found. Please configure it.')
            return

        # >> Progress dialog
        pDialog = xbmcgui.DialogProgress()
        pDialog_canceled = False
        pDialog.create('Advanced Emulator Launcher', 'Checking Retroarch BIOSes ...')
        num_BIOS = len(Libretro_BIOS_list)
        file_count = 0

        # >> Algorithm:
        #    1) Traverse list of BIOS. For every BIOS:
        #    2) Check if file exists. If not exists -> missing BIOS.
        #    3) If BIOS exists check file size.
        #    3) If BIOS exists check MD5
        #    4) Unknwon files in Retroarch System dir are ignored and non-reported.
        #    5) Write results into a report TXT file.
        BIOS_status_dic = {}
        BIOS_status_dic_colour = {}
        for BIOS_dic in Libretro_BIOS_list:
            if check_only_mandatory and not BIOS_dic['mandatory']:
                log_debug('BIOS "{0}" is not mandatory. Skipping check.'.format(BIOS_dic['filename']))
                continue

            BIOS_file_FN = sys_dir_FN.pjoin(BIOS_dic['filename'])
            log_debug('Testing BIOS "{0}"'.format(BIOS_file_FN.getPath()))

            if not BIOS_file_FN.exists():
                log_info('Not found "{0}"'.format(BIOS_file_FN.getPath()))
                BIOS_status_dic[BIOS_dic['filename']] = 'Not found'
                BIOS_status_dic_colour[BIOS_dic['filename']] = '[COLOR orange]Not found[/COLOR]'
                continue

            BIOS_stat = BIOS_file_FN.stat()
            file_size = BIOS_stat.st_size
            if file_size != BIOS_dic['size']:
                log_info('Wrong size "{0}"'.format(BIOS_file_FN.getPath()))
                log_info('It is {0} and must be {1}'.format(file_size, BIOS_dic['size']))
                BIOS_status_dic[BIOS_dic['filename']] = 'Wrong size'
                BIOS_status_dic_colour[BIOS_dic['filename']] = '[COLOR orange]Wrong size[/COLOR]'
                continue

            hash_md5 = hashlib.md5()
            with open(BIOS_file_FN.getPath(), "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            file_MD5 = hash_md5.hexdigest()
            log_debug('MD5 is "{0}"'.format(file_MD5))
            if file_MD5 != BIOS_dic['md5']:
                log_info('Wrong MD5 "{0}"'.format(BIOS_file_FN.getPath()))
                log_info('It is       "{0}"'.format(file_MD5))
                log_info('and must be "{0}"'.format(BIOS_dic['md5']))
                BIOS_status_dic[BIOS_dic['filename']] = 'Wrong MD5'
                BIOS_status_dic_colour[BIOS_dic['filename']] = '[COLOR orange]Wrong MD5[/COLOR]'
                continue
            log_info('BIOS OK "{0}"'.format(BIOS_file_FN.getPath()))
            BIOS_status_dic[BIOS_dic['filename']] = 'OK'
            BIOS_status_dic_colour[BIOS_dic['filename']] = '[COLOR lime]OK[/COLOR]'

            # >> Update progress
            file_count += 1
            update_number = (float(file_count) / float(num_BIOS)) * 100
            pDialog.update(int(update_number))
        pDialog.update(100)
        pDialog.close()

        # >> Output format:
        #    BIOS name             Mandatory  Status      Cores affected 
        #    -------------------------------------------------
        #    5200.rom              YES        OK          ---            
        #    7800 BIOS (E).rom     NO         Wrong MD5   core a name    
        #                                                 core b name    
        #    7800 BIOS (U).rom     YES        OK          ---            
        #
        max_size_BIOS_filename = 0
        for BIOS_dic in Libretro_BIOS_list:
            if len(BIOS_dic['filename']) > max_size_BIOS_filename:
                max_size_BIOS_filename = len(BIOS_dic['filename'])

        max_size_status = 0
        for key in BIOS_status_dic:
            if len(BIOS_status_dic[key]) > max_size_status:
                max_size_status = len(BIOS_status_dic[key])

        str_list = []
        str_list.append('Retroarch system dir "{0}"\n'.format(sys_dir_FN.getPath()))
        if check_only_mandatory:
            str_list.append('Checking only mandatory BIOSes.\n\n')
        else:
            str_list.append('Checking mandatory and optional BIOSes.\n\n')
        bios_str      = '{0}{1}'.format('BIOS name', ' ' * (max_size_BIOS_filename - len('BIOS name')))
        mandatory_str = 'Mandatory'
        status_str    = '{0}{1}'.format('Status', ' ' * (max_size_status - len('Status')))
        cores_str     = 'Cores affected'
        size_total = len(bios_str) + len(mandatory_str) + len(status_str) + len(cores_str) + 6
        str_list.append('{0}  {1}  {2}  {3}\n'.format(bios_str, mandatory_str, status_str, cores_str))
        str_list.append('{0}\n'.format('-' * size_total))

        for BIOS_dic in Libretro_BIOS_list:
            BIOS_filename = BIOS_dic['filename']
            # >> If BIOS was skipped continue loop
            if BIOS_filename not in BIOS_status_dic: continue
            status_text = BIOS_status_dic[BIOS_filename]
            status_text_colour = BIOS_status_dic_colour[BIOS_filename]
            filename_str = '{0}{1}'.format(BIOS_filename, ' ' * (max_size_BIOS_filename - len(BIOS_filename)))
            mandatory_str = 'YES      ' if BIOS_dic['mandatory'] else 'NO       '
            status_str = '{0}{1}'.format(status_text_colour, ' ' * (max_size_status - len(status_text)))
            len_status_str = len('{0}{1}'.format(status_text, ' ' * (max_size_status - len(status_text))))

            # >> Print affected core list
            core_list = BIOS_dic['cores']
            if len(core_list) == 0:
                line_str = '{0}  {1}  {2}\n'.format(filename_str, mandatory_str, status_str)
                str_list.append(line_str)
            else:
                num_spaces = len(filename_str) + 9 + len_status_str + 4
                for i, core_name in enumerate(core_list):
                    beautiful_core_name = Retro_core_dic[core_name] if core_name in Retro_core_dic else core_name
                    if i == 0:
                        line_str = '{0}  {1}  {2}  {3}\n'.format(filename_str, mandatory_str, status_str, beautiful_core_name)
                        str_list.append(line_str)
                    else:
                        line_str = '{0}  {1}\n'.format(' ' * num_spaces, beautiful_core_name)
                        str_list.append(line_str)

        # >> Stats report
        log_info('Writing report file "{0}"'.format(BIOS_REPORT_FILE_PATH.getPath()))
        full_string = ''.join(str_list).encode('utf-8')
        file = open(BIOS_REPORT_FILE_PATH.getPath(), 'w')
        file.write(full_string)
        file.close()

        # >> Display report TXT file.
        log_debug('Setting Window(10000) Property "FontWidth" = "monospaced"')
        xbmcgui.Window(10000).setProperty('FontWidth', 'monospaced')
        dialog = xbmcgui.Dialog()
        dialog.textviewer('Retroarch BIOS report', full_string)
        log_debug('Setting Window(10000) Property "FontWidth" = "proportional"')
        xbmcgui.Window(10000).setProperty('FontWidth', 'proportional')

    #
    # Import legacy Advanced Launcher launchers.xml
    #
    def _command_import_legacy_AL(self):
        # >> Confirm action with user
        ret = kodi_dialog_yesno('Are you sure you want to import Advanced Launcher launchers.xml?')
        if not ret: return

        kodi_notify('Importing AL launchers.xml ...')
        AL_DATA_DIR = FileName('special://profile/addon_data/plugin.program.advanced.launcher')
        LAUNCHERS_FILE_PATH = AL_DATA_DIR.pjoin('launchers.xml')
        FIXED_LAUNCHERS_FILE_PATH = PLUGIN_DATA_DIR.pjoin('fixed_launchers.xml')

        # >> Check that launchers.xml exist
        if not LAUNCHERS_FILE_PATH.exists():
            log_error("_command_import_legacy_AL() Cannot find '{0}'".format(LAUNCHERS_FILE_PATH.getPath()))
            kodi_dialog_OK('launchers.xml not found! Nothing imported.')
            return

        # >> Try to correct ilegal XML characters in launchers.xml
        # >> Also copies fixed launchers.xml into AEL data directory.
        fs_fix_launchers_xml(LAUNCHERS_FILE_PATH, FIXED_LAUNCHERS_FILE_PATH)

        # >> Read launchers.xml
        AL_categories = {}
        AL_launchers = {}
        kodi_busydialog_ON()
        fs_load_legacy_AL_launchers(FIXED_LAUNCHERS_FILE_PATH, AL_categories, AL_launchers)
        kodi_busydialog_OFF()

        # >> Traverse AL data and create categories/launchers/ROMs
        num_categories = 0
        num_launchers = 0
        num_ROMs = 0
        default_SID = misc_generate_random_SID()
        for AL_category_key in AL_categories:
            num_categories += 1
            AL_category = AL_categories[AL_category_key]
            category = fs_new_category()
            # >> Do translation
            category['id']       = default_SID if AL_category['id'] == 'default' else AL_category['id']
            category['m_name']   = AL_category['name']
            category['m_genre']  = AL_category['genre']
            category['m_plot']   = AL_category['plot']
            category['s_thumb']  = AL_category['thumb']
            category['s_fanart'] = AL_category['fanart']
            category['finished'] = False if AL_category['finished'] == 'false' else True
            self.categories[category['id']] = category

        for AL_launcher_key in AL_launchers:
            num_launchers += 1
            AL_launcher = AL_launchers[AL_launcher_key]
            launcher = fs_new_launcher()
            # >> Do translation
            launcher['id']           = AL_launcher['id']
            launcher['m_name']       = AL_launcher['name']
            launcher['m_year']       = AL_launcher['release']
            launcher['m_genre']      = AL_launcher['genre']
            launcher['m_studio']     = AL_launcher['studio']
            launcher['m_plot']       = AL_launcher['plot']
            # >> 'gamesys' ignored, set to unknown to avoid trouble with scrapers
            # launcher['platform']    = AL_launcher['gamesys']
            launcher['platform']     = 'Unknown'
            launcher['categoryID']   = default_SID if AL_launcher['category'] == 'default' else AL_launcher['category']
            launcher['application']  = AL_launcher['application']
            launcher['args']         = AL_launcher['args']
            launcher['rompath']      = AL_launcher['rompath']
            launcher['romext']       = AL_launcher['romext']
            launcher['finished']     = False if AL_launcher['finished'] == 'false' else True
            launcher['minimize']     = False if AL_launcher['minimize'] == 'false' else True
            # >> 'lnk' ignored, always active in AEL
            launcher['s_thumb']      = AL_launcher['thumb']
            launcher['s_fanart']     = AL_launcher['fanart']
            launcher['path_title']   = AL_launcher['thumbpath']
            launcher['path_fanart']  = AL_launcher['fanartpath']
            launcher['path_trailer'] = AL_launcher['trailerpath']
            # --- Import ROMs if ROMs launcher ---
            AL_roms = AL_launcher['roms']
            if AL_roms:
                roms = {}
                category_name = self.categories[launcher['categoryID']]['m_name']
                roms_base_noext = fs_get_ROMs_basename(category_name, launcher['m_name'], launcher['id'])
                launcher['roms_base_noext'] = roms_base_noext
                launcher['num_roms'] = len(AL_roms)
                for AL_rom_ID in AL_roms:
                    num_ROMs += 1
                    AL_rom = AL_roms[AL_rom_ID]
                    rom = fs_new_rom()
                    # >> Do translation
                    rom['id']        = AL_rom['id']
                    rom['m_name']    = AL_rom['name']
                    rom['m_year']    = AL_rom['release']
                    rom['m_genre']   = AL_rom['genre']
                    rom['m_studio']  = AL_rom['studio']
                    rom['m_plot']    = AL_rom['plot']
                    rom['filename']  = AL_rom['filename']
                    rom['altapp']    = AL_rom['altapp']
                    rom['altarg']    = AL_rom['altarg']
                    rom['finished']  = False if AL_rom['finished'] == 'false' else True
                    rom['s_title']   = AL_rom['thumb']
                    rom['s_fanart']  = AL_rom['fanart']
                    rom['s_trailer'] = AL_rom['trailer']

                    # >> Add to ROM dictionary
                    roms[rom['id']] = rom

                # >> Save ROMs XML
                fs_write_ROMs_JSON(ROMS_DIR, launcher, roms)
            else:
                launcher['roms_xml_file'] = ''
            # --- Add launcher to AEL launchers ---
            launcher['timestamp_launcher'] = time.time()
            self.launchers[launcher['id']] = launcher

        # >> Save AEL categories.xml
        fs_write_catfile(CATEGORIES_FILE_PATH, self.categories, self.launchers)

        # --- Show some information to user ---
        kodi_dialog_OK('Imported {0} Category/s, {1} Launcher/s '.format(num_categories, num_launchers) +
                       'and {0} ROM/s.'.format(num_ROMs))
        kodi_refresh_container()

    #
    # A set of functions to help making plugin URLs
    # NOTE probably this can be implemented in a more elegant way with optinal arguments...
    #
    def _misc_url_RunPlugin(self, command, categoryID = None, launcherID = None, romID = None):
        if romID is not None:
            return 'XBMC.RunPlugin({0}?com={1}&catID={2}&launID={3}&romID={4})'.format(self.base_url, command, categoryID, launcherID, romID)
        elif launcherID is not None:
            return 'XBMC.RunPlugin({0}?com={1}&catID={2}&launID={3})'.format(self.base_url, command, categoryID, launcherID)
        elif categoryID is not None:
            return 'XBMC.RunPlugin({0}?com={1}&catID={2})'.format(self.base_url, command, categoryID)

        return 'XBMC.RunPlugin({0}?com={1})'.format(self.base_url, command)

    def _misc_url(self, command, categoryID = None, launcherID = None, romID = None):
        if romID is not None:
            return '{0}?com={1}&catID={2}&launID={3}&romID={4}'.format(self.base_url, command, categoryID, launcherID, romID)
        elif launcherID is not None:
            return '{0}?com={1}&catID={2}&launID={3}'.format(self.base_url, command, categoryID, launcherID)
        elif categoryID is not None:
            return '{0}?com={1}&catID={2}'.format(self.base_url, command, categoryID)

        return '{0}?com={1}'.format(self.base_url, command)

    def _misc_url_search(self, command, categoryID, launcherID, search_type, search_string):
        return '{0}?com={1}&catID={2}&launID={3}&search_type={4}&search_string={5}'.format(
            self.base_url, command, categoryID, launcherID, search_type, search_string)

    def _command_buildMenu(self):
        log_debug('_command_buildMenu() Starting ...')

        hasSkinshortcuts = xbmc.getCondVisibility('System.HasAddon(script.skinshortcuts)') == 1
        if hasSkinshortcuts == False:
            log_warning("Addon skinshortcuts is not installed, cannot build games menu")
            warnAddonMissingDialog = xbmcgui.Dialog()
            warnAddonMissingDialog.notification('Missing addon', 'Addon skinshortcuts is not installed', xbmcgui.NOTIFICATION_WARNING, 5000)
            return

        path = ""
        try:
            skinshortcutsAddon = xbmcaddon.Addon('script.skinshortcuts')
            path = FileName(skinshortcutsAddon.getAddonInfo('path'))

            libPath = path.pjoin('resources', 'lib')
            sys.path.append(libPath.getPath())

            unidecodeModule = xbmcaddon.Addon('script.module.unidecode')
            libPath = FileName(unidecodeModule.getAddonInfo('path'))
            libPath = libPath.pjoin('lib')
            sys.path.append(libPath.getPath())

            sys.modules[ "__main__" ].ADDON    = skinshortcutsAddon
            sys.modules[ "__main__" ].ADDONID  = skinshortcutsAddon.getAddonInfo('id').decode( 'utf-8' )
            sys.modules[ "__main__" ].CWD      = path.getPath()
            sys.modules[ "__main__" ].LANGUAGE = skinshortcutsAddon.getLocalizedString

            import gui, datafunctions

        except Exception as ex:
            log_error("(Exception) Failed to load skinshortcuts addon")
            log_error("(Exception) {0}".format(ex))
            traceback.print_exc()
            warnAddonMissingDialog = xbmcgui.Dialog()
            warnAddonMissingDialog.notification('Failure', 'Could not load skinshortcuts addon', xbmcgui.NOTIFICATION_WARNING, 5000)
            return
        log_debug('_command_buildMenu() Loaded SkinsShortCuts addon')

        startToBuildDialog = xbmcgui.Dialog()
        startToBuild = startToBuildDialog.yesno('Games menu', 'Want to automatically fill the menu?')
        if not startToBuild: return

        menuStore = datafunctions.DataFunctions()
        ui = gui.GUI( "script-skinshortcuts.xml", path, "default", group="mainmenu", defaultGroup=None, nolabels="false", groupname="" )
        ui.currentWindow = xbmcgui.Window()

        mainMenuItems = []
        mainMenuItemLabels = []
        shortcuts = menuStore._get_shortcuts( "mainmenu", defaultGroup =None )
        for shortcut in shortcuts.getroot().findall( "shortcut" ):
            item = ui._parse_shortcut( shortcut )
            mainMenuItemLabels.append(item[1].getLabel())
            mainMenuItems.append(item[1])

        selectMenuToFillDialog = xbmcgui.Dialog()
        selectedMenuIndex = selectMenuToFillDialog.select("Select menu", mainMenuItemLabels)

        selectedMenuItem = mainMenuItems[selectedMenuIndex]

        typeOfContentsDialog = xbmcgui.Dialog()
        typeOfContent = typeOfContentsDialog.select("Select content to create in %s" % selectedMenuItem.getLabel(), ['Categories', 'Launchers'])

        selectedMenuID = selectedMenuItem.getProperty("labelID")
        selectedMenuItems = []

        selectedMenuItemsFromStore = menuStore._get_shortcuts(selectedMenuID, defaultGroup =None )
        amount = len(selectedMenuItemsFromStore.getroot().findall( "shortcut" ))

        if amount < 1:
            selectedDefaultID = selectedMenuItem.getProperty("defaultID")
            selectedMenuItemsFromStore = menuStore._get_shortcuts(selectedDefaultID, defaultGroup =None )

        for shortcut in selectedMenuItemsFromStore.getroot().findall( "shortcut" ):
            item = ui._parse_shortcut( shortcut )
            selectedMenuItems.append(item[1])

        ui.group = selectedMenuID
        count = len(selectedMenuItems)

        if typeOfContent == 0:
            for key in sorted(self.categories, key = lambda x : self.categories[x]['m_name']):
                category_dic = self.categories[key]
                name = category_dic['m_name']
                url_str =  "ActivateWindow(Programs,\"%s\",return)" % self._misc_url('SHOW_LAUNCHERS', key)
                fanart = asset_get_default_asset_Category(category_dic, 'default_fanart')
                thumb = asset_get_default_asset_Category(category_dic, 'default_thumb', 'DefaultFolder.png')

                log_debug('_command_buildMenu() Adding Category "{0}"'.format(name))
                listitem = self._buildMenuItem(key, name, url_str, thumb, fanart, count, ui)
                selectedMenuItems.append(listitem)

        if typeOfContent == 1:
            for key in sorted(self.launchers, key = lambda x : self.launchers[x]['application']):
                launcher_dic = self.launchers[key]
                name = launcher_dic['m_name']
                launcherID = launcher_dic['id']
                categoryID = launcher_dic['categoryID']
                url_str =  "ActivateWindow(Programs,\"%s\",return)" % self._misc_url('SHOW_ROMS', categoryID, launcherID)
                fanart = asset_get_default_asset_Category(launcher_dic, 'default_fanart')
                thumb = asset_get_default_asset_Category(launcher_dic, 'default_thumb', 'DefaultFolder.png')

                log_debug('_command_buildMenu() Adding Launcher "{0}"'.format(name))
                listitem = self._buildMenuItem(key, name, url_str, thumb, fanart, count, ui)
                selectedMenuItems.append(listitem)

        ui.changeMade = True
        ui.allListItems = selectedMenuItems
        ui._save_shortcuts()
        ui.close()
        log_info("Saved shortcuts for AEL")
        notifyDialog = xbmcgui.Dialog()
        notifyDialog.notification('Done building', 'The menu is updated with AEL content', xbmcgui.NOTIFICATION_INFO, 5000)
        #xmlfunctions.ADDON = xbmcaddon.Addon('script.skinshortcuts')
        #xmlfunctions.ADDONVERSION = xmlfunctions.ADDON.getAddonInfo('version')
        #xmlfunctions.LANGUAGE = xmlfunctions.ADDON.getLocalizedString
        #xml = XMLFunctions()
        #xml.buildMenu("9000","","0",None,"","0")
        #log_info("Done building menu for AEL")

    def _buildMenuItem(self, key, name, action, thumb, fanart, count, ui):

        listitem = xbmcgui.ListItem(name)
        listitem.setProperty( "defaultID", key)
        listitem.setProperty( "Path", action )
        listitem.setProperty( "displayPath", action )
        listitem.setProperty( "icon", thumb )
        listitem.setProperty( "skinshortcuts-orderindex", str( count ) )
        listitem.setProperty( "additionalListItemProperties", "[]" )
        ui._add_additional_properties( listitem )
        ui._add_additionalproperty( listitem, "background", fanart )
        ui._add_additionalproperty( listitem, "backgroundName", fanart )

        return listitem
