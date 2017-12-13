import re
import requests,base64
import xbmc
import urllib
from ..scraper import Scraper
from ..common import clean_title,clean_search

User_Agent = 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'

class kisscartoon(Scraper):
    domains = ['http://www.cartoonson.com']
    name = "CartoonsOn"
    sources = []

    def __init__(self):
        self.base_link = 'http://www.cartoonson.com'
        self.sources = []

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/search/search/q/%s' %(self.base_link,search_id.replace(' ','%20'))
            #print 'SEARCH > '+start_url
            headers = {'User_Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content
            Regex = re.compile('class="search-item".+?href="(.+?)".+?class="search-matched">(.+?)</a>',re.DOTALL).findall(html)
            for item_url,name in Regex:
                if clean_title(search_id).lower() in clean_title(name).lower():
                    if year in name:
                        
                        movie_link = self.base_link + item_url.replace('/view/id/','/watch/id/')
                        self.get_source(movie_link)
                
            return self.sources
        except Exception, argument:
            return self.sources

    def scrape_episode(self,title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/search/search/q/%s' %(self.base_link,search_id.replace(' ','%20'))
            #print 'SEARCH > '+start_url
            headers = {'User_Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content
            Regex = re.compile('class="search-item".+?href="(.+?)".+?class="search-matched">(.+?)</a>',re.DOTALL).findall(html)
            for item_url,name in Regex:
                if clean_title(search_id).lower() in clean_title(name).lower():
                        movie_link = self.base_link + item_url.replace('/view/id/','/watch/id/') + '/season/%s/episode/%s' %(season,episode)
                        self.get_source(movie_link)
                
            return self.sources
        except Exception, argument:
            return self.sources

    def get_source(self,movie_link):
        try:
            #print 'cfwd:::::::::'+movie_link
            html = requests.get(movie_link,timeout=5).content
            link = re.compile('embed-responsive.+?src="(.+?)"',re.DOTALL).findall(html)[0]
            if 'openload' in link:

                get_res=requests.get(link,timeout=5).content
                try:
                    rez = re.compile('description" content="(.+?)"',re.DOTALL).findall(get_res)[0]
                    if '1080p' in rez:
                        qual = '1080p'
                    elif '720p' in rez:
                        qual='720p'
                    else:
                        qual='DVD'
                except: qual='DVD'
                self.sources.append({'source': 'Openload','quality': qual,'scraper': self.name,'url': link,'direct': False})
            else:
                self.sources.append({'source': 'Google','quality': 'DVD','scraper': self.name,'url': link,'direct': True})
                        
        except:
            pass
