import re
import requests
import base64
from ..scraper import Scraper
from ..common import clean_title, clean_search

class cinemamega(Scraper):
    domains = ['cinemamega.net']
    name = "CinemaMega"
    sources = []

    def __init__(self):
        self.base_link = 'http://cinemamega.net'
        self.sources = []
        
    def scrape_episode(self,title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/search-movies/%s+season+%s.html' %(self.base_link,search_id.replace(' ','+'),season)
            
            html = requests.get(start_url,timeout=3).content
            match = re.compile('<div class="ml-item">.+?href="(.+?)".+?onmouseover.+?<i>(.+?)</i>.+?Release: (.+?)<',re.DOTALL).findall(html)
            for url,name,release_year in match:
                clean_title_,clean_season = re.findall('(.+?): Season (.+?)>',str(name)+'>')[0]
                if clean_title(clean_title_)==clean_title(title) and clean_season == season:
                    html2 = requests.get(url).content
                    match = re.findall('<a class="episode.+?href="(.+?)">(.+?)</a>',html2)
                    for url2,episode_ in match:
                        if episode_ == episode:
                            link = url2
                            self.get_source(link)
            return self.sources
        except Exception as e:
            print str(e)
            return []                           

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/search-movies/%s.html' %(self.base_link,search_id.replace(' ','+'))
            print 'START URL>> '+start_url
            html = requests.get(start_url,timeout=3).content
            match = re.compile('<div class="ml-item">.+?href="(.+?)".+?onmouseover.+?<i>(.+?)</i>.+?Release: (.+?)<',re.DOTALL).findall(html)
            for url,name,release_year in match:
                print 'GW_chck1 %s %s %s' %(url,name,release_year)
                if clean_title(name)==clean_title(title) and year == release_year:
                    print 'GW_chck2 %s %s %s' %(url,name,release_year)
                    link = url
                    self.get_source(link)
            return self.sources
        except Exception as e:
            print str(e)
            return []                           

    def get_source(self, link):
        try:
            html = requests.get(link,timeout=3).content
            frame = base64.decodestring(re.findall('Base64.decode.+?"(.+?)"',str(html))[0])
            playlink = re.findall('src="(.+?)"',str(frame))[0]
            source = re.findall('//(.+?)/',str(playlink))[0]
            self.sources.append({'source': source, 'quality': 'SD', 'scraper': self.name, 'url': playlink,'direct': False})
        except Exception as e:
            print str(e)
            return []
