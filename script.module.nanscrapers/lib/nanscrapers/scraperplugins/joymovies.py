import requests
import re
import xbmc
from ..scraper import Scraper
from ..common import clean_title,clean_search            


s = requests.session()
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
                                           
class joymovies(Scraper):
    domains = ['joymovies.com']
    name = "Joymovies"
    sources = []

    def __init__(self):
        self.base_link = 'http://joymovies.com'
                      

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = self.base_link + '/search/movie/%s/' %search_id.replace(' ','%20')
            #print 'STARTURL:::::::::::::::: '+start_url
            headers={'User-Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content
            
            results = re.compile('class="ml-item".+?href="(.+?)" title="(.+?)">',re.DOTALL).findall(html)
            for item_url,name in results:
                if clean_title(title).lower() == clean_title(name).lower():
                    self.get_source(item_url,year)
            return self.sources
        except Exception, argument:
            return self.sources

    def get_source(self,item_url,year):
        try:
            headers={'User-Agent':User_Agent}
            html = requests.get(item_url,headers=headers,timeout=5).content
            chkdate = re.compile('"datePublished" content="(.+?)"',re.DOTALL).findall(html)
            for date in chkdate:
                if year==date:
                    Links = re.compile('<div class="download_btn".+?href="(.+?)"',re.DOTALL).findall(html)
                    for link in Links:
                        if 'm37' in link:
                            qual = '1080p'
                        elif 'm22' in link:
                            qual = '720p'
                        elif 'googleapis' in link:
                            qual = '720p'
                        elif 'apidata.google' in link:
                            qual = '720p'
                        else:
                            qual='SD'
                        self.sources.append({'source': 'GVideo','quality': qual,'scraper': self.name,'url': link,'direct': False})                    
        except:
            pass