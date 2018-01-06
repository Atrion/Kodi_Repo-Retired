import re
import requests
import xbmc,time
from ..scraper import Scraper

class WatchFrees(Scraper):
    domains = ['watchfrees.com']
    name = "watchfrees"
    sources = []

    def __init__(self):
        self.base_link = 'https://watchfrees.com'
        self.search_link = '/search.html?keyword='
        self.start_time = time.time()
#        self.scrape_episode('the blacklist', '2000', '2000', '1', '4', '', '')
#        self.scrape_movie('moana', '2016', '')

    def scrape_episode(self, title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            start_url = self.base_link+self.search_link+title.replace(' ','+')
            html = requests.get(start_url).content
            match = re.compile('<figure>.+?href="(.+?)".+?title="(.+?)"',re.DOTALL).findall(html)
            for url,name in match:
                url = self.base_link+url
                if title.lower().replace(' ','').replace(':','') in name.lower().replace(' ','').replace(':',''):
                    if 'Season '+season in name:
                        html2 = requests.get(url).content
                        ul = re.compile('<ul>(.+?)</ul>',re.DOTALL).findall(html2)
                        for u in ul:
                            li = re.compile('<li(.+?)</li>',re.DOTALL).findall(str(u))
                            for l in li:
                                match2 = re.compile('<a href="(.+?)".+?title="(.+?)"',re.DOTALL).findall(str(l))
                                for u2, t in match2:
                                    u2 = self.base_link+u2
                                    ep = re.compile('Episode (.+?) -').findall(str(t))
                                    for e in ep:
                                        if e[0] == '0':
                                            if len(episode)==1:
                                                episode = '0'+episode
                                            if episode == e:
                                                self.get_source(u2)
                                        else:
                                            if episode == e:
                                                self.get_source(u2)

            return self.sources
                                        
        except:
            pass
            return []                           

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            start_url = self.base_link+self.search_link+title.replace(' ','+')
            html = requests.get(start_url).content
            match = re.compile('<figure>.+?href="(.+?)".+?title="(.+?)"',re.DOTALL).findall(html)
            for url,name in match:
                url = self.base_link+url
                if title.lower().replace(' ','').replace(':','') in name.lower().replace(' ','').replace(':',''):
                    self.get_source(url)
            return self.sources
        except:
            pass
            return[]

    def get_source(self,link):
        try:
            html = requests.get(link).content
            match = re.compile('var link_server.+?"(.+?)"',re.DOTALL).findall(html)
            for m in match:
                if not m.startswith('http:'):
                    m = 'http:' + m
                if 'vidnode' in m:
                    response = requests.get(m).content
                    link = re.compile("source src='(.+?)'.+?label='(.+?)'").findall(response)
                    for playlink,qual in link:
                        qual = qual+'p'
                        self.sources.append({'source': 'GVideo', 'quality': qual, 'scraper': self.name, 'url': playlink, 'direct': True})
                    end_time = time.time()
                    total_time = end_time - self.start_time
                    print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"    
                    l = re.compile('<iframe.+?src="(.+?)"').findall(response)
                    for n in l:
                        m = n
                        self.get_single(m)
                else:
                    self.get_single(m)
        except:
            pass

    def get_single(self,m):
        try:
            if 'estream' in m:
                h = requests.get(m).content
                ma = re.compile('<source src="(.+?)/>').findall(h)
                for s in ma:
                    if 'm3u8' in str(s):
                        p = re.compile('(.+?)"').findall(str(s))
                        for playlink in p:
                            self.sources.append({'source': 'GVideo', 'quality': 'HD', 'scraper': self.name, 'url': playlink, 'direct': True})
                        end_time = time.time()
                        total_time = end_time - self.start_time
                        print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"    
                    else:
                        p = re.compile('(.+?)".+?label=\'.+?x(.+?)\'').findall(str(s))
                        for playlink,qual in p:
                            qual = qual+'p'
                            self.sources.append({'source': 'GVideo', 'quality': qual, 'scraper': self.name, 'url': playlink, 'direct': True})
                        end_time = time.time()
                        total_time = end_time - self.start_time
                        print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"    
            elif 'thevideo' in m:
                self.sources.append({'source': 'thevideo', 'quality': 'SD', 'scraper': self.name, 'url': m, 'direct': False})
                end_time = time.time()
                total_time = end_time - self.start_time
                print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"
            elif 'openload' in m:
                self.sources.append({'source': 'openload', 'quality': 'SD', 'scraper': self.name, 'url': m, 'direct': False})
                end_time = time.time()
                total_time = end_time - self.start_time
                print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"
        except:
            pass
