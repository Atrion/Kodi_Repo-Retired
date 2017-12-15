# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher platform and emulator information
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

# -------------------------------------------------------------------------------------------------
# New platform engine
# -------------------------------------------------------------------------------------------------
DAT_MAME    = 'MAME'
DAT_NOINTRO = 'No-Intro'
DAT_REDUMP  = 'Redump'
DAT_NONE    = ''
class Platform:
    def __init__(self, name, shortname, DAT, aliasof = ''):
        self.name      = name
        self.shortname = shortname
        self.DAT       = DAT
        self.aliasof   = aliasof

#
# From this list create simplified list to access platform information
#
AEL_platforms = [
    # --- MAME/Arcade ---
    Platform('MAME', 'mame', DAT_MAME),

    # --- Amstrad ---
    Platform('Amstrad CPC', 'cpc', DAT_NONE),

    # --- Atari ---
    Platform('Atari 2600', 'a2600', DAT_NOINTRO),

    # --- Coleco ---
    Platform('Colecovision', 'coleco', DAT_NOINTRO),
]

AEL_p_list = []
AEL_p_short_list = []
for p_obj in AEL_platforms:
    AEL_p_list.append(p_obj.name)
    AEL_p_short_list.append(p_obj.shortname)

# -------------------------------------------------------------------------------------------------
# Old platform engine
# -------------------------------------------------------------------------------------------------
# >> When possible user No-Intro DAT-o-MATIC names
# >> Fallback to Wikipedia names
#
AEL_platform_list = [
    # --- 3DO ---
    '3DO Interactive Multiplayer',

    # --- Amstrad ---
    'Amstrad CPC',

    # --- Atari ---
    'Atari 2600',
    'Atari 5200',
    'Atari 7800',
    'Atari Jaguar',
    'Atari Jaguar CD',
    'Atari Lynx',
    'Atari ST',

    # --- Bandai ---
    'Bandai WonderSwan',
    'Bandai WonderSwan Color',

    # --- Coleco ---
    'Colecovision',

    # --- Commodore ---
    'Commodore 64',
    'Commodore Amiga',
    'Commodore Amiga CD32',
    'Commodore Plus-4',
    'Commodore VIC-20',

    # --- Fujitsu ---
    'Fujitsu FM Towns Marty',

    # --- GCE ---
    'GCE Vectrex',

    # --- Magnavox ---
    'Magnavox Odyssey2',

    # --- MAME/Arcade ---
    'MAME',

    # --- Mattel ---
    'Mattel Intellivision',

    # --- Microsoft ---
    'Microsoft MS-DOS',
    'Microsoft MSX',
    'Microsoft MSX2',
    'Microsoft Windows',
    'Microsoft Xbox',
    'Microsoft Xbox 360',
    'Microsoft Xbox One',

    # --- NEC ---
    'NEC PC Engine',
    'NEC PC Engine CDROM2',
    'NEC TurboGrafx 16',
    'NEC TurboGrafx CD',
    'NEC SuperGrafx',
    'NEC PC-FX',

    # --- Nintendo ---
    'Nintendo 3DS',
    'Nintendo 64',
    'Nintendo 64DD',
    'Nintendo DS',
    'Nintendo DSi',
    'Nintendo Famicom',             # Alias of NES
    'Nintendo Famicom Disk System',
    'Nintendo GameBoy',
    'Nintendo GameBoy Advance',
    'Nintendo GameBoy Color',
    'Nintendo GameCube',
    'Nintendo NES',
    'Nintendo Pokemon Mini',
    'Nintendo SNES',
    'Nintendo Switch',
    'Nintendo Virtual Boy',
    'Nintendo Wii',
    'Nintendo Wii U',

    # --- Philips ---
    'Philips Videopac G7000',      # Alias of 'Magnavox Odyssey2'
    'Philips Videopac Plus G7400',

    # --- ScummVM ---
    'ScummVM',

    # --- Sega ---
    'Sega 32X',
    'Sega Dreamcast',
    'Sega Game Gear',
    'Sega Genesis',
    'Sega Master System',
    'Sega MegaCD', # Alias of 'Sega SegaCD'
    'Sega MegaDrive', # Alias of 'Sega Genesis'
    'Sega PICO',
    'Sega Saturn',
    'Sega SC-3000',
    'Sega SegaCD',
    'Sega SG-1000',

    # --- Sharp ---
    'Sharp X68000',

    # --- Sinclair ---
    'Sinclair ZX Spectrum',

    # --- SNK ---
    'SNK Neo-Geo AES', # Alias of MAME? AES has some exclusive games.
    'SNK Neo-Geo CD',
    'SNK Neo-Geo MVS', # Alias of MAME
    'SNK Neo-Geo Pocket',
    'SNK Neo-Geo Pocket Color',

    # --- SONY ---
    'Sony PlayStation',
    'Sony PlayStation 2',
    'Sony PlayStation 3',
    'Sony PlayStation 4',
    'Sony PlayStation Portable',
    'Sony PlayStation Vita',

    # --- Unknown ---
    'Unknown'
]

#
# Returns the platform numerical index from the platform name. If the platform name is not
# found then returns the index of the 'Unknown' platform
#
def get_AEL_platform_index(platform_name):
    try:
        platform_index = AEL_platform_list.index(platform_name)
    except:
        platform_index = AEL_platform_list.index('Unknown')

    return platform_index

# -------------------------------------------------------------------------------------------------
# Translation of AEL oficial gamesys (platform) name to scraper particular name
# -------------------------------------------------------------------------------------------------
#
# GameDBInfo XML database files.
#
platform_AEL_to_Offline_GameDBInfo_XML = {
    '3DO Interactive Multiplayer' : 'GameDBInfo/Panasonic 3DO.xml',

    'Amstrad CPC'                 : '',

    'Atari 2600'                  : 'GameDBInfo/Atari 2600.xml',
    'Atari 5200'                  : 'GameDBInfo/Atari 5200.xml',
    'Atari 7800'                  : 'GameDBInfo/Atari 7800.xml',
    'Atari Jaguar'                : 'GameDBInfo/Atari Jaguar.xml',
    'Atari Jaguar CD'             : 'GameDBInfo/Atari Jaguar CD.xml',
    'Atari Lynx'                  : 'GameDBInfo/Atari Lynx.xml',
    'Atari ST'                    : 'GameDBInfo/Atari ST.xml',

    'Bandai WonderSwan'           : '',
    'Bandai WonderSwan Color'     : '',

    'Colecovision'                : 'GameDBInfo/Colecovision.xml',

    'Commodore 64'                : 'GameDBInfo/Commodore 64.xml',
    'Commodore Amiga'             : 'GameDBInfo/Commodore Amiga.xml',
    'Commodore Amiga CD32'        : '',
    'Commodore Plus-4'            : 'GameDBInfo/Commodore Plus-4.xml',
    'Commodore VIC-20'            : 'GameDBInfo/Commodore VIC-20.xml',

    'Fujitsu FM Towns Marty'      : '',
    
    'GCE Vectrex'                 : '',

    'Magnavox Odyssey2'           : 'GameDBInfo/Magnavox Odyssey2.xml',

    'MAME'                        : 'GameDBInfo/MAME.xml',

    'Mattel Intellivision'        : '',

    'Microsoft MS-DOS'            : 'GameDBInfo/Microsoft MS-DOS.xml',
    'Microsoft MSX'               : '',
    'Microsoft MSX2'              : 'GameDBInfo/Microsoft MSX 2.xml',
    'Microsoft Windows'           : '',
    'Microsoft Xbox'              : '',
    'Microsoft Xbox 360'          : '',
    'Microsoft Xbox One'          : '',

    'NEC PC Engine'               : 'GameDBInfo/NEC PC Engine.xml',
    'NEC PC Engine CDROM2'        : 'GameDBInfo/NEC PC Engine CDROM2.xml',
    'NEC TurboGrafx 16'           : 'GameDBInfo/NEC TurboGrafx 16.xml',
    'NEC TurboGrafx CD'           : 'GameDBInfo/NEC TurboGrafx CD.xml',
    'NEC SuperGrafx'              : 'GameDBInfo/NEC SuperGrafx.xml',
    'NEC PC-FX'                   : 'GameDBInfo/NEC PC-FX.xml',

    'Nintendo 3DS'                : '',
    'Nintendo 64'                 : 'GameDBInfo/Nintendo 64.xml',
    'Nintendo 64DD'               : '',
    'Nintendo DS'                 : 'GameDBInfo/Nintendo DS.xml',
    'Nintendo DSi'                : '',
    'Nintendo Famicom'            : 'GameDBInfo/Nintendo NES.xml',
    'Nintendo Famicom Disk System': 'GameDBInfo/Nintendo Famicom Disk System.xml',
    'Nintendo GameBoy'            : 'GameDBInfo/Nintendo Game Boy.xml',
    'Nintendo GameBoy Advance'    : 'GameDBInfo/Nintendo Game Boy Advance.xml',
    'Nintendo GameBoy Color'      : 'GameDBInfo/Nintendo Game Boy Color.xml',
    'Nintendo GameCube'           : 'GameDBInfo/Nintendo GameCube.xml',
    'Nintendo NES'                : 'GameDBInfo/Nintendo NES.xml',
    'Nintendo Pokemon Mini'       : '',
    'Nintendo SNES'               : 'GameDBInfo/Nintendo SNES.xml',
    'Nintendo Switch'             : '',
    'Nintendo Virtual Boy'        : 'GameDBInfo/Nintendo Virtual Boy.xml',
    'Nintendo Wii'                : 'GameDBInfo/Nintendo Wii.xml',
    'Nintendo Wii U'              : '',

    'Philips Videopac G7000'      : 'GameDBInfo/Magnavox Odyssey2.xml',
    'Philips Videopac Plus G7400' : '',

    'ScummVM'                     : '',

    'Sega 32X'                    : 'GameDBInfo/Sega 32x.xml',
    'Sega Dreamcast'              : 'GameDBInfo/Sega Dreamcast.xml',
    'Sega Game Gear'              : 'GameDBInfo/Sega Game Gear.xml',
    'Sega Genesis'                : 'GameDBInfo/Sega MegaDrive.xml',
    'Sega Master System'          : 'GameDBInfo/Sega Master System.xml',
    'Sega MegaCD'                 : 'GameDBInfo/Sega CD.xml',
    'Sega MegaDrive'              : 'GameDBInfo/Sega MegaDrive.xml',
    'Sega PICO'                   : '',
    'Sega Saturn'                 : 'GameDBInfo/Sega Saturn.xml',
    'Sega SC-3000'                : '',
    'Sega SegaCD'                 : 'GameDBInfo/Sega CD.xml',
    'Sega SG-1000'                : 'GameDBInfo/Sega SG-1000.xml',

    'Sharp X68000'                : '',

    'Sinclair ZX Spectrum'        : 'GameDBInfo/Sinclair ZX Spectrum.xml',

    'SNK Neo-Geo AES'             : '',
    'SNK Neo-Geo CD'              : 'GameDBInfo/SNK Neo-Geo CD.xml',
    'SNK Neo-Geo MVS'             : '',
    'SNK Neo-Geo Pocket'          : 'GameDBInfo/SNK Neo-Geo Pocket.xml',
    'SNK Neo-Geo Pocket Color'    : 'GameDBInfo/SNK Neo-Geo Pocket Color.xml',

    'Sony PlayStation'            : 'GameDBInfo/Sony PlayStation.xml',
    'Sony PlayStation 2'          : 'GameDBInfo/Sony Playstation 2.xml',
    'Sony PlayStation 3'          : '',
    'Sony PlayStation 4'          : '',
    'Sony PlayStation Portable'   : 'GameDBInfo/Sony PlayStation Portable.xml',
    'Sony PlayStation Vita'       : '',

    'Unknown'                     : ''
}

#
# LaunchBox XML database files.
#
platform_AEL_to_LB_XML = {
    '3DO Interactive Multiplayer' : '',

    'Amstrad CPC'                 : '',

    'Atari 2600'                  : '',
    'Atari 5200'                  : '',
    'Atari 7800'                  : '',
    'Atari Jaguar'                : '',
    'Atari Jaguar CD'             : '',
    'Atari Lynx'                  : '',
    'Atari ST'                    : '',

    'Bandai WonderSwan'           : '',
    'Bandai WonderSwan Color'     : '',

    'Colecovision'                : '',

    'Commodore 64'                : '',
    'Commodore Amiga'             : '',
    'Commodore Amiga CD32'        : '',
    'Commodore Plus-4'            : '',
    'Commodore VIC-20'            : '',

    'Fujitsu FM Towns Marty'      : '',

    'GCE Vectrex'                 : '',

    'Magnavox Odyssey2'           : '',

    'MAME'                        : '',

    'Mattel Intellivision'        : '',

    'Microsoft MS-DOS'            : '',
    'Microsoft MSX'               : '',
    'Microsoft MSX2'              : '',
    'Microsoft Windows'           : '',
    'Microsoft Xbox'              : '',
    'Microsoft Xbox 360'          : '',
    'Microsoft Xbox One'          : '',

    'NEC PC Engine'               : '',
    'NEC PC Engine CDROM2'        : '',
    'NEC TurboGrafx 16'           : '',
    'NEC TurboGrafx CD'           : '',
    'NEC SuperGrafx'              : '',
    'NEC PC-FX'                   : '',

    'Nintendo 3DS'                : '',
    'Nintendo 64'                 : '',
    'Nintendo 64DD'               : '',
    'Nintendo DS'                 : '',
    'Nintendo DSi'                : '',
    'Nintendo Famicom'            : '',
    'Nintendo Famicom Disk System': '',
    'Nintendo GameBoy'            : '',
    'Nintendo GameBoy Advance'    : '',
    'Nintendo GameBoy Color'      : '',
    'Nintendo GameCube'           : '',
    'Nintendo NES'                : '',
    'Nintendo Pokemon Mini'       : '',
    'Nintendo SNES'               : '',
    'Nintendo Switch'             : '',
    'Nintendo Virtual Boy'        : '',
    'Nintendo Wii'                : '',
    'Nintendo Wii U'              : '',

    'Philips Videopac G7000'      : '',
    'Philips Videopac Plus G7400' : '',

    'ScummVM'                     : '',

    'Sega 32X'                    : '',
    'Sega Dreamcast'              : '',
    'Sega Game Gear'              : '',
    'Sega Genesis'                : 'LaunchBox/Sega Genesis.xml',
    'Sega Master System'          : '',
    'Sega MegaCD'                 : '',
    'Sega MegaDrive'              : 'LaunchBox/Sega Genesis.xml',
    'Sega PICO'                   : '',
    'Sega Saturn'                 : '',
    'Sega SC-3000'                : '',
    'Sega SegaCD'                 : '',
    'Sega SG-1000'                : '',

    'Sharp X68000'                : '',

    'Sinclair ZX Spectrum'        : '',

    'SNK Neo-Geo AES'             : '',
    'SNK Neo-Geo CD'              : '',
    'SNK Neo-Geo MVS'             : '',
    'SNK Neo-Geo Pocket'          : '',
    'SNK Neo-Geo Pocket Color'    : '',

    'Sony PlayStation'            : '',
    'Sony PlayStation 2'          : '',
    'Sony PlayStation 3'          : '',
    'Sony PlayStation 4'          : '',
    'Sony PlayStation Portable'   : '',
    'Sony PlayStation Vita'       : '',

    'Unknown'                     : ''
}

#
# Get platform list from http://thegamesdb.net/api/GetPlatformsList.php
# Platform name is inside <name> tag.
#
platform_AEL_to_TheGamesDB_dic = {
    '3DO Interactive Multiplayer' : '3DO',
    'Amstrad CPC'                 : 'Amstrad CPC',
    'Atari 2600'                  : 'Atari 2600',
    'Atari 5200'                  : 'Atari 5200',
    'Atari 7800'                  : 'Atari 7800',
    'Atari Jaguar'                : 'Atari Jaguar',
    'Atari Jaguar CD'             : 'Atari Jaguar CD',
    'Atari Lynx'                  : 'Atari Lynx',
    'Atari ST'                    : 'Atari ST',
    'Bandai WonderSwan'           : 'WonderSwan',
    'Bandai WonderSwan Color'     : 'WonderSwan Color',
    'Colecovision'                : 'Colecovision',
    'Commodore 64'                : 'Commodore 64',
    'Commodore Amiga'             : 'Amiga',
    'Commodore Amiga CD32'        : 'Amiga CD32',
    'Commodore Plus-4'            : '', #  Not found in TheGamesDB
    'Commodore VIC-20'            : 'Commodore VIC-20',
    'Fujitsu FM Towns Marty'      : 'FM Towns Marty',
    'GCE Vectrex'                 : 'Vectrex',
    'Magnavox Odyssey2'           : 'Magnavox Odyssey 2',
    'MAME'                        : 'Arcade',
    'Mattel Intellivision'        : 'Intellivision',
    'Microsoft MS-DOS'            : 'PC',
    'Microsoft MSX'               : 'MSX',
    'Microsoft MSX2'              : 'MSX',
    'Microsoft Windows'           : 'PC',
    'Microsoft Xbox'              : 'Microsoft Xbox',
    'Microsoft Xbox 360'          : 'Microsoft Xbox 360',
    'Microsoft Xbox One'          : 'Microsoft Xbox One',
    'NEC PC Engine'               : 'TurboGrafx 16',
    'NEC PC Engine CDROM2'        : 'TurboGrafx CD',
    'NEC TurboGrafx 16'           : 'TurboGrafx 16',
    'NEC TurboGrafx CD'           : 'TurboGrafx CD',
    'NEC SuperGrafx'              : 'TurboGrafx 16',
    'NEC PC-FX'                   : 'PC-FX',
    'Nintendo 3DS'                : 'Nintendo 3DS',
    'Nintendo 64'                 : 'Nintendo 64',
    'Nintendo 64DD'               : 'Nintendo 64', # Not found in TheGamesDB
    'Nintendo DS'                 : 'Nintendo DS',
    'Nintendo DSi'                : 'Nintendo DS', # Not found in TheGamesDB
    'Nintendo Famicom'            : 'Nintendo Entertainment System (NES)',
    'Nintendo Famicom Disk System': 'Famicom Disk System',
    'Nintendo GameBoy'            : 'Nintendo Game Boy',
    'Nintendo GameBoy Advance'    : 'Nintendo Gameboy Advance',
    'Nintendo GameBoy Color'      : 'Nintendo Gameboy Color',
    'Nintendo GameCube'           : 'Nintendo GameCube',
    'Nintendo NES'                : 'Nintendo Entertainment System (NES)',
    'Nintendo Pokemon Mini'       : 'Nintendo Pokémon Mini',
    'Nintendo SNES'               : 'Super Nintendo (SNES)',
    'Nintendo Switch'             : 'Nintendo Switch',
    'Nintendo Virtual Boy'        : 'Nintendo Virtual Boy',
    'Nintendo Wii'                : 'Nintendo Wii',
    'Nintendo Wii U'              : 'Nintendo Wii U',
    'Philips Videopac G7000'      : 'Magnavox Odyssey 2',
    'Philips Videopac Plus G7400' : 'Magnavox Odyssey 2', # Not found in TheGamesDB
    'ScummVM'                     : '', # Not found in TheGamesDB
    'Sega 32X'                    : 'Sega 32X',
    'Sega Dreamcast'              : 'Sega Dreamcast',
    'Sega Game Gear'              : 'Sega Game Gear',
    'Sega Genesis'                : 'Sega Genesis',
    'Sega Master System'          : 'Sega Master System',
    'Sega MegaCD'                 : 'Sega CD',
    'Sega MegaDrive'              : 'Sega Genesis',
    'Sega PICO'                   : 'Sega Pico',
    'Sega Saturn'                 : 'Sega Saturn',
    'Sega SC-3000'                : '', # Not found in TheGamesDB
    'Sega SegaCD'                 : 'Sega CD',
    'Sega SG-1000'                : 'SEGA SG-1000',
    'Sharp X68000'                : 'Sharp X68000',
    'Sinclair ZX Spectrum'        : 'Sinclair ZX Spectrum',
    'SNK Neo-Geo AES'             : 'Neo Geo',
    'SNK Neo-Geo CD'              : 'Neo Geo CD',
    'SNK Neo-Geo MVS'             : 'Arcade',
    'SNK Neo-Geo Pocket'          : 'Neo Geo Pocket',
    'SNK Neo-Geo Pocket Color'    : 'Neo Geo Pocket Color',
    'Sony PlayStation'            : 'Sony Playstation',
    'Sony PlayStation 2'          : 'Sony Playstation 2',
    'Sony PlayStation 3'          : 'Sony Playstation 3',
    'Sony PlayStation 4'          : 'Sony Playstation 4',
    'Sony PlayStation Portable'   : 'Sony PSP',
    'Sony PlayStation Vita'       : 'Sony Playstation Vita',
}

#
# Platform '0' means all platforms
# Get platform names from https://www.gamefaqs.com/search_advanced?game=ar
#
platform_AEL_to_GameFAQs_dic = {
    '3DO Interactive Multiplayer' : '61',  # <option label="3DO" value="61">3DO</option>
    'Amstrad CPC'                 : '46',  # <option label="Amstrad CPC" value="46">Amstrad CPC</option>
    'Atari 2600'                  : '6',   # <option label="Atari 2600" value="6">Atari 2600</option>
    'Atari 5200'                  : '20',  # <option label="Atari 5200" value="20">Atari 5200</option>
    'Atari 7800'                  : '51',  # <option label="Atari 7800" value="51">Atari 7800</option>
    'Atari Jaguar'                : '72',  # <option label="Jaguar" value="72">Jaguar</option>
    'Atari Jaguar CD'             : '82',  # <option label="Jaguar CD" value="82">Jaguar CD</option>
    'Atari Lynx'                  : '58',  # <option label="Lynx" value="58">Lynx</option>
    'Atari ST'                    : '38',  # <option label="Atari ST" value="38">Atari ST</option>
    'Bandai WonderSwan'           : '90',  # <option label="WonderSwan" value="90">WonderSwan</option>
    'Bandai WonderSwan Color'     : '95',  # <option label="WonderSwan Color" value="95">WonderSwan Color</option>
    'Colecovision'                : '29',  # <option label="Colecovision" value="29">Colecovision</option>
    'Commodore 64'                : '24',  # <option label="Commodore 64" value="24">Commodore 64</option>
    'Commodore Amiga'             : '39',  # <option label="Amiga" value="39">Amiga</option>
    'Commodore Amiga CD32'        : '70',  # <option label="Amiga CD32" value="70">Amiga CD32</option>
    'Commodore Plus-4'            : '0',   # Not found in GameFAQs
    'Commodore VIC-20'            : '11',  # <option label="VIC-20" value="11">VIC-20</option>
    'Fujitsu FM Towns Marty'      : '55',  # <option label="FM Towns" value="55">FM Towns</option>
    'GCE Vectrex'                 : '34',  # <option label="Vectrex" value="34">Vectrex</option>
    'Magnavox Odyssey2'           : '9',   # <option label="Odyssey^2" value="9">Odyssey^2</option>
    'MAME'                        : '2',   # <option label="Arcade Games" value="2">Arcade Games</option>
    'Mattel Intellivision'        : '16',  # <option label="Intellivision" value="16">Intellivision</option>
    'Microsoft MS-DOS'            : '19',  # <option label="PC" value="19">PC</option>
    'Microsoft MSX'               : '40',  # <option label="MSX" value="40">MSX</option>
    'Microsoft MSX2'              : '40',
    'Microsoft Windows'           : '19',  # <option label="PC" value="19">PC</option>
    'Microsoft Xbox'              : '98',  # <option label="Xbox" value="98">Xbox</option>
    'Microsoft Xbox 360'          : '111', # <option label="Xbox 360" value="111">Xbox 360</option>
    'Microsoft Xbox One'          : '121', # <option label="Xbox One" value="121">Xbox One</option>
    'NEC PC Engine'               : '53',  # <option label="TurboGrafx-16" value="53">TurboGrafx-16</option>
    'NEC PC Engine CDROM2'        : '56',  # <option label="Turbo CD" value="56">Turbo CD</option>
    'NEC TurboGrafx 16'           : '53',  # <option label="TurboGrafx-16" value="53">TurboGrafx-16</option>
    'NEC TurboGrafx CD'           : '56',  # <option label="Turbo CD" value="56">Turbo CD</option>
    'NEC SuperGrafx'              : '53',  # Didn't found SuperGrafx on GameFAQs
    'NEC PC-FX'                   : '79',  # <option label="PC-FX" value="79" selected="selected">PC-FX</option>
    'Nintendo 3DS'                : '116', # <option label="3DS" value="116">3DS</option>
    'Nintendo 64'                 : '84',  # <option label="Nintendo 64" value="84">Nintendo 64</option>
    'Nintendo 64DD'               : '92',  # <option label="Nintendo 64DD" value="92">Nintendo 64DD</option>
    'Nintendo DS'                 : '108', # <option label="DS" value="108">DS</option>
    'Nintendo DSi'                : '108', # Not found in GameFAQs
    'Nintendo Famicom'            : '41',  # <option label="NES" value="41">NES</option>
    'Nintendo Famicom Disk System': '47',  # <option label="Famicom Disk System" value="47">Famicom Disk System</option>
    'Nintendo GameBoy'            : '59',  # <option label="Game Boy" value="59">Game Boy</option>
    'Nintendo GameBoy Advance'    : '91',  # <option label="Game Boy Advance" value="91">Game Boy Advance</option>
    'Nintendo GameBoy Color'      : '57',  # <option label="Game Boy Color" value="57">Game Boy Color</option>
    'Nintendo GameCube'           : '99',  # <option label="GameCube" value="99">GameCube</option>
    'Nintendo NES'                : '41',  # <option label="NES" value="41">NES</option>
    'Nintendo Pokemon Mini'       : '0',   # Not found in GameFAQs
    'Nintendo SNES'               : '63',  # <option label="Super Nintendo" value="63">Super Nintendo</option>
    'Nintendo Switch'             : '124', # <option label="Nintendo Switch" value="124">Nintendo Switch</option>
    'Nintendo Virtual Boy'        : '83',  # <option label="Virtual Boy" value="83">Virtual Boy</option>
    'Nintendo Wii'                : '114', # <option label="Wii" value="114">Wii</option>
    'Nintendo Wii U'              : '118', # <option label="Wii U" value="118">Wii U</option>
    'Philips Videopac G7000'      : '9',   # Alias of Odyssey^2
    'Philips Videopac Plus G7400' : '0',   # Not found in GameFAQs
    'ScummVM'                     : '0',   # Not found in GameFAQs
    'Sega 32X'                    : '74',  # <option label="Sega 32X" value="74">Sega 32X</option>
    'Sega Dreamcast'              : '67',  # <option label="Dreamcast" value="67">Dreamcast</option>
    'Sega Game Gear'              : '62',  # <option label="GameGear" value="62">GameGear</option>
    'Sega Genesis'                : '54',  # <option label="Genesis" value="54">Genesis</option>
    'Sega Master System'          : '49',  # <option label="Sega Master System" value="49">Sega Master System</option>
    'Sega MegaCD'                 : '65',  # <option label="Sega CD" value="65">Sega CD</option>
    'Sega MegaDrive'              : '54',  # <option label="Genesis" value="54">Genesis</option>
    'Sega PICO'                   : '0',   # Not found in GameFAQs
    'Sega Saturn'                 : '76',  # <option label="Saturn" value="76">Saturn</option>
    'Sega SC-3000'                : '0',   # Not found in GameFAQs
    'Sega SegaCD'                 : '65',  # <option label="Sega CD" value="65">Sega CD</option>
    'Sega SG-1000'                : '43',  # <option label="SG-1000" value="43">SG-1000</option>
    'Sharp X68000'                : '52',  # <option label="Sharp X68000" value="52">Sharp X68000</option>
    'Sinclair ZX Spectrum'        : '35',  # <option label="Sinclair ZX81/Spectrum" value="35">Sinclair ZX81/Spectrum</option>
    'SNK Neo-Geo AES'             : '64',  # <option label="NeoGeo" value="64">NeoGeo</option>
    'SNK Neo-Geo CD'              : '68',  # <option label="Neo-Geo CD" value="68">Neo-Geo CD</option>
    'SNK Neo-Geo MVS'             : '2',   # Alias of "Arcade Games" (MAME)
    'SNK Neo-Geo Pocket'          : '0',   # Not found in GameFAQs
    'SNK Neo-Geo Pocket Color'    : '89',  # <option label="NeoGeo Pocket Color" value="89">NeoGeo Pocket Color</option>
    'Sony PlayStation'            : '78',  # <option label="PlayStation" value="78">PlayStation</option>
    'Sony PlayStation 2'          : '94',  # <option label="PlayStation 2" value="94">PlayStation 2</option>
    'Sony PlayStation 3'          : '113', # <option label="PlayStation 3" value="113">PlayStation 3</option>
    'Sony PlayStation 4'          : '120', # <option label="PlayStation 4" value="120">PlayStation 4</option>
    'Sony PlayStation Portable'   : '109', # <option label="PSP" value="109">PSP</option>
    'Sony PlayStation Vita'       : '117', # <option label="PlayStation Vita" value="117">PlayStation Vita</option>
}

#
# Get platform names from http://www.mobygames.com/search/quick?q=ar
#
platform_AEL_to_MobyGames_dic = {
    '3DO Interactive Multiplayer' : '35',  # <option value="35">3DO</option>
    'Amstrad CPC'                 : '60',  # <option value="60">Amstrad CPC</option>
    'Atari 2600'                  : '28',  # <option value="28">Atari 2600</option>
    'Atari 5200'                  : '33',  # <option value="33">Atari 5200</option>
    'Atari 7800'                  : '34',  # <option value="34">Atari 7800</option>
    'Atari Jaguar'                : '17',  # <option value="17">Jaguar</option>
    'Atari Jaguar CD'             : '17',  # Not found on MobyGames
    'Atari Lynx'                  : '18',  # <option value="18">Lynx</option>
    'Atari ST'                    : '24',  # <option value="24">Atari ST</option>
    'Bandai WonderSwan'           : '48',  # <option value="48">WonderSwan</option>
    'Bandai WonderSwan Color'     : '49',  # <option value="49">WonderSwan Color</option>
    'Colecovision'                : '29',  # <option value="29">ColecoVision</option>
    'Commodore 64'                : '27',  # <option value="27">Commodore 64</option>
    'Commodore Amiga'             : '19',  # <option value="19">Amiga</option>
    'Commodore Amiga CD32'        : '56',  # <option value="56">Amiga CD32</option>
    'Commodore Plus-4'            : '115', # <option value="115">Commodore 16, Plus/4</option>
    'Commodore VIC-20'            : '43',  # <option value="43">VIC-20</option>
    'Fujitsu FM Towns Marty'      : '102', # <option value="102">FM Towns</option>
    'GCE Vectrex'                 : '37',  # <option value="37">Vectrex</option>
    'Magnavox Odyssey2'           : '78',  # <option value="78">Odyssey 2</option>
    'MAME'                        : '143', # <option value="143">Arcade</option>
    'Mattel Intellivision'        : '30',  # <option value="30">Intellivision</option>
    'Microsoft MS-DOS'            : '2',   # <option value="2">DOS</option>
    'Microsoft MSX'               : '57',  # <option value="57">MSX</option>
    'Microsoft MSX2'              : '57',
    'Microsoft Windows'           : '3',   # <option value="3">Windows</option>
                                           # <option value="5">Windows 3.x</option>
    'Microsoft Xbox'              : '13',  # <option value="13">Xbox</option>
    'Microsoft Xbox 360'          : '69',  # <option value="69">Xbox 360</option>
    'Microsoft Xbox One'          : '142', # <option value="142">Xbox One</option>
    'NEC PC Engine'               : '40',  # <option value="40">TurboGrafx-16</option>
    'NEC PC Engine CDROM2'        : '45',  # <option value="45">TurboGrafx CD</option>
    'NEC TurboGrafx 16'           : '40',  # <option value="40">TurboGrafx-16</option>
    'NEC TurboGrafx CD'           : '45',  # <option value="45">TurboGrafx CD</option>
    'NEC SuperGrafx'              : '127', # <option value="127">SuperGrafx</option>
    'NEC PC-FX'                   : '59',  # <option value="59">PC-FX</option>
    'Nintendo 3DS'                : '101', # <option value="101">Nintendo 3DS</option>
    'Nintendo 64'                 : '9',   # <option value="9">Nintendo 64</option>
    'Nintendo 64DD'               : '9',   # Not found in MobyGames
    'Nintendo DS'                 : '44',  # <option value="44">Nintendo DS</option>
    'Nintendo DSi'                : '87',  # <option value="87">Nintendo DSi</option>
    'Nintendo Famicom'            : '22',  # <option value="22">NES</option>
    'Nintendo Famicom Disk System': '22',  # Does not exist in MobyGames
    'Nintendo GameBoy'            : '10',  # <option value="10">Game Boy</option>
    'Nintendo GameBoy Advance'    : '12',  # <option value="12">Game Boy Advance</option>
    'Nintendo GameBoy Color'      : '11',  # <option value="11">Game Boy Color</option>
    'Nintendo GameCube'           : '14',  # <option value="14">GameCube</option>
    'Nintendo NES'                : '22',  # <option value="22">NES</option>
    'Nintendo Pokemon Mini'       : '152', # <option value="152">Pokémon Mini</option>
    'Nintendo SNES'               : '15',  # <option value="15">SNES</option>
    'Nintendo Switch'             : '203', # <option value="203">Nintendo Switch</option>
    'Nintendo Virtual Boy'        : '38',  # <option value="38">Virtual Boy</option>
    'Nintendo Wii'                : '82',  # <option value="82">Wii</option>
    'Nintendo Wii U'              : '132', # <option value="132">Wii U</option>
    'Philips Videopac G7000'      : '78',  # Not found on MobyGames, alias of "Odyssey 2"
    'Philips Videopac Plus G7400' : '128', # <option value="128">Videopac+ G7400</option>
    'ScummVM'                     : '',    # Not found on MobyGames
    'Sega 32X'                    : '21',  # <option value="21">SEGA 32X</option>
    'Sega Dreamcast'              : '8',   # <option value="8">Dreamcast</option>
    'Sega Game Gear'              : '25',  # <option value="25">Game Gear</option>
    'Sega Genesis'                : '16',  # <option value="16">Genesis</option>
    'Sega Master System'          : '26',  # <option value="26">SEGA Master System</option>
    'Sega MegaCD'                 : '20',  # <option value="20">SEGA CD</option>
    'Sega MegaDrive'              : '16',  # <option value="16">Genesis</option>
    'Sega PICO'                   : '103', # <option value="103">SEGA Pico</option>
    'Sega Saturn'                 : '23',  # <option value="23">SEGA Saturn</option>
    'Sega SC-3000'                : '',    # Not found on MobyGames
    'Sega SegaCD'                 : '20',  # <option value="20">SEGA CD</option>
    'Sega SG-1000'                : '114', # <option value="114">SG-1000</option>
    'Sharp X68000'                : '106', # <option value="106">Sharp X68000</option>
    'Sinclair ZX Spectrum'        : '41',  # <option value="41">ZX Spectrum</option>
    'SNK Neo-Geo AES'             : '36',  # <option value="36">Neo Geo</option>
    'SNK Neo-Geo CD'              : '54',  # <option value="54">Neo Geo CD</option>
    'SNK Neo-Geo MVS'             : '143', # Alias of "Arcade"
    'SNK Neo-Geo Pocket'          : '52',  # <option value="52">Neo Geo Pocket</option>
    'SNK Neo-Geo Pocket Color'    : '53',  # <option value="53">Neo Geo Pocket Color</option>
    'Sony PlayStation'            : '6',   # <option value="6">PlayStation</option>
    'Sony PlayStation 2'          : '7',   # <option value="7">PlayStation 2</option>
    'Sony PlayStation 3'          : '81',  # <option value="81">PlayStation 3</option>
    'Sony PlayStation 4'          : '141', # <option value="141">PlayStation 4</option>
    'Sony PlayStation Portable'   : '46',  # <option value="46">PSP</option>
    'Sony PlayStation Vita'       : '105', # <option value="105">PS Vita</option>
}

def AEL_platform_to_TheGamesDB(platform_AEL):
    try:    platform_TheGamesDB = platform_AEL_to_TheGamesDB_dic[platform_AEL]
    except: platform_TheGamesDB = ''
        
    return platform_TheGamesDB

def AEL_platform_to_GameFAQs(AEL_gamesys):
    try:    platform_GameFAQs = platform_AEL_to_GameFAQs_dic[AEL_gamesys]
    except: platform_GameFAQs = '0' # Platform '0' means all platforms

    return platform_GameFAQs

def AEL_platform_to_MobyGames(platform_AEL):
    try:    platform_MobyGames = platform_AEL_to_MobyGames_dic[platform_AEL]
    except: platform_MobyGames = ''
        
    return platform_MobyGames

# -------------------------------------------------------------------------------------------------
# Miscellaneous emulator and gamesys (platforms) supported.
# -------------------------------------------------------------------------------------------------
def emudata_get_program_arguments(app):
    # Based on the app. name, retrieve the default arguments for the app.
    app = app.lower()
    applications = {
        'mame'        : '"$rom$"',
        'mednafen'    : '-fs 1 "$rom$"',
        'mupen64plus' : '--nogui --noask --noosd --fullscreen "$rom$"',
        'nestopia'    : '"$rom$"',
        'xbmc'        : 'PlayMedia($rom$)',
        'kodi'        : 'PlayMedia($rom$)',
        'retroarch'   : '-L /path/to/core -f "$rom$"',
        'yabause'     : '-a -f -i "$rom$"',
    }
    for application, arguments in applications.iteritems():
        if app.find(application) >= 0:
            return arguments

    return '"$rom$"'

def emudata_get_program_extensions(app):
    # Based on the app. name, retrieve the recognized extension of the app.
    app = app.lower()
    applications = {
        'mame'       : 'zip|7z',
        'mednafen'   : 'zip|cue',
        'mupen64plus': 'z64|zip|n64',
        'nestopia'   : 'nes|zip',
        'retroarch'  : 'zip|cue',
        'yabause'    : 'cue',
    }
    for application, extensions in applications.iteritems():
        if app.find(application) >= 0:
            return extensions

    return ''
