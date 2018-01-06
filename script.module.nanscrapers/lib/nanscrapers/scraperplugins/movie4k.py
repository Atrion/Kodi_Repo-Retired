import re,time
import requests
import xbmc
import urllib
import urlresolver
from ..scraper import Scraper
from ..common import clean_title,clean_search,random_agent



User_Agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H143 Safari/600.1.4'


class movie4k(Scraper):
    domains = ['movie4k.is']
    name = "Movie4k"
    sources = []

    def __init__(self):
        self.base_link = 'https://movie4k.is'
        self.sources = []
        self.start_time = time.time()

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s' %(self.base_link,search_id.replace(' ','+'))
            headers = {'User_Agent':random_agent()}
            html = requests.get(start_url,headers=headers,timeout=5).content
            #print html
            
            Regex = re.compile('<div class="boxinfo">.+?<a href="(.+?)">.+?<span class="tt">(.+?)</span>.+?<span class="year">(.+?)<',re.DOTALL).findall(html)
            for item_url,name,rel in Regex:
                if clean_title(title).lower() == clean_title(name).lower():
                    if year == rel:
                        movie_link = item_url
                        #print movie_link,name,rel
                        self.get_source(movie_link,year)
            
                
            return self.sources
        except Exception, argument:
            return self.sources

    def get_source(self,movie_link,year):
        try:
            html = requests.get(movie_link).content
            qual = re.compile('<span class="calidad2">(.+?)</span>',re.DOTALL).findall(html)[0]
            links = re.compile('data-lazy-src="(.+?)/"',re.DOTALL).findall(html)
            for link in links:
                if urlresolver.HostedMediaFile(link).valid_url():
                    host = link.split('//')[1].replace('www.','')
                    host = host.split('/')[0].split('.')[0].title()
                    self.sources.append({'source': host,'quality': qual,'scraper': self.name,'url': link,'direct': False})
            end_time = time.time()
            total_time = end_time - self.start_time
            print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"            
        except:
            pass

#movie4k().scrape_movie('bright', '2017','') 