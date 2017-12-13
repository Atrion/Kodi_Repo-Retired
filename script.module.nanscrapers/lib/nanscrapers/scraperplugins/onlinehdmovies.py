import re
import requests
import xbmc
import urllib
from ..scraper import Scraper
from ..common import clean_title,clean_search
from nanscrapers.modules import cfscrape

User_Agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H143 Safari/600.1.4'


class onlinehdmovies(Scraper):
    domains = ['onlinehdmovies.org']
    name = "onlinehdmovies"
    sources = []

    def __init__(self):
        self.base_link = 'http://onlinehdmovies.org'
        self.sources = []
        self.scraper = cfscrape.create_scraper()

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s' %(self.base_link,search_id.replace(' ','+'))
            headers = {'User_Agent':User_Agent}
            html = self.scraper.get(start_url,headers=headers,timeout=5).content
            Regex = re.compile('<div class="imagen">.+?<a href="(.+?)">.+?alt="(.+?)" /></a>',re.DOTALL).findall(html)
            for item_url,name in Regex:
                if clean_title(title).lower() == clean_title(name).lower():
                    if year in name:
                        movie_link = item_url
                        self.get_source(movie_link)
                
            return self.sources
        except Exception, argument:
            return self.sources

    def get_source(self,movie_link):
        try:
            html = self.scraper.get(movie_link).content
            links = re.compile('<div id=.+?href="(.+?)"',re.DOTALL).findall(html)
            for link in links:
                if 'openload' in link:
                    try:
                        headers = {'User_Agent':User_Agent}
                        get_res=self.scraper.get(link,headers=headers,timeout=5).content
                        rez = re.compile('description" content="(.+?)"',re.DOTALL).findall(get_res)[0]
                        if '1080p' in rez:
                            qual = '1080p'
                        elif '720p' in rez:
                            qual='720p'
                        else:
                            qual='DVD'
                    except: qual='DVD'        
                    self.sources.append({'source': 'openload','quality': qual,'scraper': self.name,'url': link,'direct': False})
                elif 'vidoza' in link:
                    try:
                        headers = {'User_Agent':User_Agent}
                        get_res=requests.get(link,headers=headers,timeout=5).content
                        rez = re.compile('label:"(.+?)"',re.DOTALL).findall(get_res)[0]
                        if '1080p' in rez:
                            qual = '1080p'
                        elif '720p' in rez:
                            qual='720p'
                        else:
                            qual='DVD'
                    except: qual='DVD'        
                    self.sources.append({'source': 'vidoza','quality': qual,'scraper': self.name,'url': link,'direct': False})
        except:
            pass

