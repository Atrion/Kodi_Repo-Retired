import re,time
import requests,urlresolver
import xbmc
import urllib
from ..scraper import Scraper
from ..common import clean_title,clean_search
from ..modules import cfscrape


User_Agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'


class full4movies(Scraper):
    domains = ['full4movies.co']
    name = "full4movies"
    sources = []

    def __init__(self):
        self.base_link = 'http://www.full4movies.co'
        self.sources = []
        self.scraper = cfscrape.create_scraper()
        self.start_time = time.time()

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s' %(self.base_link,search_id.replace(' ','+'))
            #print 'search>>>'+start_url
            headers = {'User_Agent':User_Agent}
            html = self.scraper.get(start_url,headers=headers,timeout=5).content
            #print html
            xbmc.log('passed'+repr(html),xbmc.LOGNOTICE)
            
            Regex = re.compile('<div class="boxinfo">.+?<a href="(.+?)">.+?<span class="tt">(.+?)</span>',re.DOTALL).findall(html)
            for item_url,name in Regex:
                if 'English' in name:
                    xbmc.log('passed'+repr(item_url),xbmc.LOGNOTICE)
                    if clean_title(title).lower() == clean_title(name).lower():
                        movie_link = item_url
                        #print movie_link
                        xbmc.log('passed'+repr(movie_link),xbmc.LOGNOTICE)
                        self.get_source(movie_link,year)
            
                
            return self.sources
        except Exception, argument:
            return self.sources

    def get_source(self,movie_link,year):
        try:
            html = self.scraper.get(movie_link).content
            chkdate = re.compile('<span itemprop="contentRating".+?rel="tag">(.+?)</a>',re.DOTALL).findall(html)
            for date in chkdate:
                if year==date:
                    links = re.compile('<a class="myButton" href="(.+?)"',re.DOTALL).findall(html)
                    for link in links:
                        if urlresolver.HostedMediaFile(link).valid_url():
                            host = link.split('//')[1].replace('www.','')
                            host = host.split('/')[0].split('.')[0].title()
                            self.sources.append({'source': host,'quality': 'DVD','scraper': self.name,'url': link,'direct': False})
            end_time = time.time()
            total_time = end_time - self.start_time
            print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"
        except:
            pass

#ull4movies().scrape_movie('jungle', '2017','') 