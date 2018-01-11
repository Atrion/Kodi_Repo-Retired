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

import requests, sys
from bs4 import BeautifulSoup
from resources.lib.modules import cleantitle, directstream, source_utils
import re

class source:

    def __init__(self):
        self.priority = 0
        self.language = ['en']
        self.domain = 'filepursuit.com'
        self.search_link = 'https://filepursuit.com/search/'

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = tvshowtitle.replace(' ', '-')
        except:
            print("Unexpected error in Filepursuit Script: TV", sys.exc_info()[0])
            return url
        return url

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if len(episode) == 1:
                episode = "0" + episode
            if len(season) == 1:
                season = "0" + season
            url = {'tvshowtitle': url, 'season': season, 'episode': episode}
            return url
        except:
            print("Unexpected error in Filepursuit Script: episode", sys.exc_info()[0])
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print(exc_type, exc_tb.tb_lineno)
            return url

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            with requests.Session() as s:
                link = cleantitle.clean_search_query(url['tvshowtitle']) + ".s" + \
                       url['season'] + "e" + url['episode']
                p = s.get(self.search_link + link + "/type/video")

                soup = BeautifulSoup(p.text, 'html.parser').find_all('table')[0]
                soup = soup.find_all('button')
                for i in soup:
                    fileUrl = i['data-clipboard-text']
                    if re.sub('[^0-9a-zA-Z]+', '.', link).lower() in fileUrl.lower():
                        hoster = fileUrl.split('/')[2]
                        quality = source_utils.check_sd_url(fileUrl)
                        sources.append({
                            'source': hoster,
                            'quality': quality,
                            'language': 'en',
                            'url': fileUrl,
                            'direct': False,
                            'debridonly': False,
                            'info':'FilePursuit App Available on the Play Store'
                        })
            return sources

        except:
            print("Unexpected error in Filepursuit Script: Sources", sys.exc_info()[0])
            exc_type, exc_obj, exc_tb = sys.exc_info()
            print(exc_type, exc_tb.tb_lineno)
            return sources

    def resolve(self, url):
      return url