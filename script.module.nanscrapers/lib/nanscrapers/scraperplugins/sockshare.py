import re
import requests
import xbmc
import urllib
from ..scraper import Scraper
from ..common import clean_title,clean_search

User_Agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H143 Safari/600.1.4'


class sockshare(Scraper):
    domains = ['sockshare.online']
    name = "sockshare"
    sources = []

    def __init__(self):
        self.base_link = 'http://sockshare.online'
        self.sources = []

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s' %(self.base_link,search_id.replace(' ','+'))
            headers = {'User_Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content
            Regex = re.compile('class="caption">.+?href="(.+?)" ><span >(.+?)</span>',re.DOTALL).findall(html)
            for item_url,name in Regex:
                if year in name:
                    if clean_title(title).lower() == clean_title(name).lower():
                        movie_link = item_url
                        self.get_source(movie_link)
                
            return self.sources
        except Exception, argument:
            return self.sources

    def get_source(self,movie_link):
        try:
            html = requests.get(movie_link).content
            links = re.compile('allowfullscreen=.+?src="(.+?)">',re.DOTALL).findall(html) 
            for link in links:
                if 'vidzstore' in link:              
                    try:
                        
                        headers = {'User_Agent':User_Agent}
                        Open_Vid_Url=requests.get(link,headers=headers,timeout=5).content   
                        final_url = re.compile('file: "(.+?)"',re.DOTALL).findall(Open_Vid_Url)[0]   
                    except: pass        
                    self.sources.append({'source': 'vidzstore','quality': 'DVD','scraper': self.name,'url': final_url,'direct': False})
        except:
            pass

