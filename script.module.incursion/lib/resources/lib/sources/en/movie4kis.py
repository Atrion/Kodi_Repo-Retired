# -*- coding: utf-8 -*-

"""
    Incursion Add-on

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

import re
import urllib
import urlparse

from resources.lib.modules import cache
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import source_utils
from resources.lib.modules import dom_parser2


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['movie4k.is','movie4k.ws']
        self.base_link = 'http://www.movie4k.is'
        self.search_link = '/?s=%s'


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'title': title, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []

            if url == None: return sources

            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            year = data['year']
            h = {'User-Agent': client.randomagent()}
            title = cleantitle.geturl(data['title']).replace('-', '+')
            url = urlparse.urljoin(self.base_link, self.search_link % title)
            r = client.request(url, headers=h)
            r = dom_parser2.parse_dom(r, 'div', {'class': 'item'})
            r = [dom_parser2.parse_dom(i, 'a', req=['href']) for i in r if i]
            r = client.request(r[0][0].attrs['href'], headers=h)
            quality = dom_parser2.parse_dom(r, 'span', {'class': 'calidad2'})
            url = re.findall('c="(.+)\/"',r)
            if '1080p' in quality[0].content:
                quality = '1080p'
            elif '720p' in quality[0].content:
                quality = '720p'
            else:
                quality = 'SD'
            for i in url:
                valid, host = source_utils.is_host_valid(i, hostDict)
                sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': i, 'direct': False, 'debridonly': False})
            return sources
        except:
            return sources

    def resolve(self, url):
        try:
            return url
        except:
            return
