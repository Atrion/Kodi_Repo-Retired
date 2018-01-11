
'''
    Incursion Add-on
    Copyright (C) 2016 Incursion

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

import requests
import json,sys
from bs4 import BeautifulSoup
import re
from resources.lib.modules import cleantitle
from resources.lib.modules import directstream

class source:

    def __init__(self):
        self.priority = 0
        self.language = ['en']
        self.domain = 'cartoonhd.zone'
        self.base_link = 'https://cartoonhd.zone'
        self.search_link = 'https://cartoonhd.zone/show/'
        self.headers = {'x-requested-with': 'XMLHttpRequest'}

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):

        url = tvshowtitle
        return url

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        with requests.Session() as s:
            url = cleantitle.geturl(url)
            link = self.search_link + url + '/season/' + season + "/episode/" + episode
            p = s.get(link)
            soup = BeautifulSoup(p.text, 'html.parser')
            soup = soup.find_all('script', src=False, type=False)

            try:
                idEl = re.findall(r'^(?=.*elid = "\d+").+$', soup[2].prettify(), re.MULTILINE)
                idEl = re.findall(r'\d+', idEl[0])[0]
                token = re.findall(r"   = '.*'", soup[0].prettify(), re.MULTILINE)
                token = re.findall(r'\w+', token[0])
                url = {}
                url['idEl'] = idEl
                url['token'] = token
            except:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print(exc_type, exc_tb.tb_lineno)
                url = None
                pass

        return url

    def sources(self, url, hostDict, hostprDict):
        sources = []
        links = []
        if not url: return sources
        data = {'action': 'getEpisodeEmb', 'idEl': url['idEl'], 'token': url['token'], 'nopop': ''}
        with requests.Session() as s:
            p = s.post('https://cartoonhd.zone/ajax/vsozrflxcw.php', data=data, headers=self.headers)
            embed = json.loads(p.text)
            for i in embed:
                links.append((BeautifulSoup(embed[i]['embed'], 'html.parser').find_all('iframe')[0])['src'])

        for i in links:
            if 'openload' in i:
                sources.append(
                    {'source': "openload.co", 'quality': "720p", 'language': "en",
                     'url': i, 'info': "",
                     'direct': False, 'debridonly': False})
            else:
                sources.append(
                    {'source': "vidcdn.pro", 'quality': "SD", 'language': "en",
                     'url': i, 'info': "",
                     'direct': False, 'debridonly': False})

        return sources

    def resolve(self, url):
        if 'google' in url:
            return directstream.googlepass(url)
        else:
            return url
