# -*- coding: utf-8 -*-

'''
    Orgiginaly from Elysium Add-on
    adapted for Nanscrapers
    Copyright (C) 2017 Elysium

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


import re,urllib,urlparse,random
from BeautifulSoup import BeautifulSoup
from ..common import clean_title, random_agent, clean_search, replaceHTMLCodes, get_rd_domains, filter_host
from ..scraper import Scraper
import requests
import xbmc


class bmoviez(Scraper):
    domains = ['bestmovies.wz']
    name = "Bmoviez"

    def __init__(self):
        self.domains = ['bestmovies.wz']
        self.base_link = 'http://www.best-moviez.ws'
        self.search_link = '/?s=%s+%s'
        self.blacklist_zips = [
            '.zip', '.rar', '.jpeg', '.img', '.jpg',
            '.RAR', '.ZIP', '.png', '.sub', '.srt'
            ]

    def scrape_movie(self, title, year, imdb, debrid=False):
        if not debrid:
            return []
        else:
            url_list = self.movie(imdb, title, year)
            sources = self.sources(url_list)
            return sources

    def scrape_episode(self, title, show_year, year, season, episode,
                       imdb, tvdb, debrid=False):
        try:
            if not debrid:
                return []
            show_url = self.tvshow(imdb, tvdb, title, show_year)
            url = self.episode(show_url, imdb, tvdb, title,
                               year, season, episode)
            sources = self.sources(url)
            return sources
        except:
            return []

    def movie(self, imdb, title, year):
        self.elysium_url = []
        try:
            self.elysium_url = []

            cleanmovie = clean_title(title)
            title = clean_search(title)
            titlecheck = cleanmovie+year
            query = self.search_link % (urllib.quote_plus(title), year)
            query = urlparse.urljoin(self.base_link, query)

            html = BeautifulSoup(requests.get(query).content)

            containers = html.findAll('h1', attrs={'class': 'entry-title'})

            for result in containers:
                print ("BMOVIES SOURCES movielink", result)
                r_title = result.findAll('a')[0]
                r_title = r_title.string
                r_href = result.findAll('a')[0]["href"]
                r_href = r_href.encode('utf-8')
                r_title = r_title.encode('utf-8')

                r_title2 = clean_title(r_title)
                if titlecheck in r_title2:
                    self.elysium_url.append([r_href, r_title])
            return self.elysium_url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, year):
        try:
            url = {'tvshowtitle': tvshowtitle, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            self.elysium_url = []
            headers = {'Accept-Language': 'en-US,en;q=0.5', 'User-Agent': random_agent()}
            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']

            cleanmovie = clean_title(title)
            data['season'], data['episode'] = season, episode
            ep_search = 'S%02dE%02d' % (
                int(data['season']),
                int(data['episode']))
            episodecheck = str(ep_search).lower()
            query = self.search_link % (urllib.quote_plus(clean_search(title)), ep_search)
            query = urlparse.urljoin(self.base_link, query)
            titlecheck = cleanmovie + episodecheck
            html = BeautifulSoup(requests.get(query).content)

            containers = html.findAll('h1', attrs={'class': 'entry-title'})

            for result in containers:

                r_title = result.findAll('a')[0]
                r_title = r_title.string
                r_href = result.findAll('a')[0]["href"]
                r_href = r_href.encode('utf-8')
                r_title = r_title.encode('utf-8')
                r_title = clean_title(r_title)
                if titlecheck in r_title:
                    self.elysium_url.append([r_href, r_title])

            return self.url
        except:
            return

    def sources(self, url):
        try:
            sources = []
            for movielink, title in self.elysium_url:
                mylink = requests.get(movielink).content
                if "1080" in title:
                    quality = "1080p"
                elif "720" in title:
                    quality = "HD"
                else:
                    quality = "SD"
                print ("BMOVIES SOURCES movielink", movielink)
                for item in parse_dom(mylink, 'div', {'class': 'entry-content'}):
                    match = re.compile('<a href="(.+?)">(.+?)</a>').findall(item)
                    for url,title in match:
                        myurl = str(url)
                        if not any(value in myurl.lower() for value in self.blacklist_zips):
                            loc = urlparse.urlparse(url).netloc # get base host (ex. www.google.com)
                            if not filter_host(loc):
                                rd_domains = get_rd_domains()
                                if loc not in rd_domains:
                                    continue
                            url = replaceHTMLCodes(url)
                            url = url.encode('utf-8')
                            try:
                                host = re.findall('([\w]+[.][\w]+)$', urlparse.urlparse(url.strip().lower()).netloc)[0]
                            except:
                                host = 'Videomega'
                            host = replaceHTMLCodes(host)
                            host = host.encode('utf-8')
                            sources.append({'source': host, 'quality': quality, 'scraper': self.name, 'url': url, 'direct': False, 'debridonly': True})

            return sources
        except Exception as e:
            return sources

    def resolve(self, url):

            return url


def _getDOMContent(html, name, match, ret):
    end_str = "</%s" % (name)
    start_str = '<%s' % (name)

    start = html.find(match)
    end = html.find(end_str, start)
    pos = html.find(start_str, start + 1)

    while pos < end and pos != -1:  # Ignore too early </endstr> return
        tend = html.find(end_str, end + len(end_str))
        if tend != -1:
            end = tend
        pos = html.find(start_str, pos + 1)

    if start == -1 and end == -1:
        result = ''
    elif start > -1 and end > -1:
        result = html[start + len(match):end]
    elif end > -1:
        result = html[:end]
    elif start > -1:
        result = html[start + len(match):]
    else:
        result = ''

    if ret:
        endstr = html[end:html.find(">", html.find(end_str)) + 1]
        result = match + result + endstr

    return result


def _getDOMAttributes(match, name, ret):
    pattern = '''<%s[^>]* %s\s*=\s*(?:(['"])(.*?)\\1|([^'"].*?)(?:>|\s))''' % (name, ret)
    results = re.findall(pattern, match, re.I | re.M | re.S)
    return [result[1] if result[1] else result[2] for result in results]


def _getDOMElements(item, name, attrs):
    if not attrs:
        pattern = '(<%s(?: [^>]*>|/?>))' % (name)
        this_list = re.findall(pattern, item, re.M | re.S | re.I)
    else:
        last_list = None
        for key in attrs:
            pattern = '''(<%s [^>]*%s=['"]%s['"][^>]*>)''' % (name, key, attrs[key])
            this_list = re.findall(pattern, item, re.M | re. S | re.I)
            if not this_list and ' ' not in attrs[key]:
                pattern = '''(<%s [^>]*%s=%s[^>]*>)''' % (name, key, attrs[key])
                this_list = re.findall(pattern, item, re.M | re. S | re.I)

            if last_list is None:
                last_list = this_list
            else:
                last_list = [item for item in this_list if item in last_list]
        this_list = last_list

    return this_list


def parse_dom(html, name='', attrs=None, ret=False):
    if attrs is None:
        attrs = {}
    if isinstance(html, str):
        try:
            html = [html.decode("utf-8")]  # Replace with chardet thingy
        except:
            print "none"
            try:
                html = [html.decode("utf-8", "replace")]
            except:

                html = [html]
    elif isinstance(html, unicode):
        html = [html]
    elif not isinstance(html, list):

        return ''

    if not name.strip():

        return ''

    if not isinstance(attrs, dict):

        return ''

    ret_lst = []
    for item in html:
        for match in re.findall('(<[^>]*\n[^>]*>)', item):
            item = item.replace(match, match.replace('\n', ' ').replace('\r', ' '))

        lst = _getDOMElements(item, name, attrs)

        if isinstance(ret, str):
            lst2 = []
            for match in lst:
                lst2 += _getDOMAttributes(match, name, ret)
            lst = lst2
        else:
            lst2 = []
            for match in lst:
                temp = _getDOMContent(item, name, match, ret).strip()
                item = item[item.find(temp, item.find(match)):]
                lst2.append(temp)
            lst = lst2
        ret_lst += lst

    # log_utils.log("Done: " + repr(ret_lst), xbmc.LOGDEBUG)
    return ret_lst
