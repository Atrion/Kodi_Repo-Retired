import requests
import re
import xbmc,time
from ..scraper import Scraper
from ..common import clean_title,clean_search,random_agent            


                                           
class bobmovies(Scraper):
    domains = ['bobmovies.com']
    name = "Bobmovies"
    sources = []

    def __init__(self):
        self.base_link = 'https://bobmovies.net'
        self.goog = 'https://www.google.co.uk'
        self.sources = []
        self.start_time = time.time()

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
        
            scrape = clean_search(title.lower()).replace(' ','+')

            start_url = '%s/search?q=bobmovies.net+%s+%s' %(self.goog,scrape,year)

            headers = {'User-Agent':random_agent()}

            html = requests.get(start_url,headers=headers).content

            results = re.compile('href="(.+?)"',re.DOTALL).findall(html)
            for url in results:

                if self.base_link in url:

                    if scrape.replace('+','-') in url:
                        if 'webcache' in url:
                            continue
                        self.get_source(url,title)
                        
            return self.sources
        except Exception, argument:
            return self.sources

    def get_source(self,url,title):
        try:
            headers={'User-Agent':random_agent()}
            html = requests.get(url,headers=headers,timeout=5).content
            
            chktitle =re.compile('property="og:title" content="(.+?)" ',re.DOTALL).findall(html)[0]
            
            if clean_title(title).lower() == clean_title(chktitle).lower():
                vidpage = re.compile('id="tab-movie".+?data-file="(.+?)"',re.DOTALL).findall(html)
            
                for link in vidpage:
                    if 'trailer' not in link.lower():
                        link = self.base_link + link
                        self.sources.append({'source': 'DirectLink','quality': '720p','scraper': self.name,'url': link,'direct': False})
                end_time = time.time()
                total_time = end_time - self.start_time
                print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"                            
        except:
            pass