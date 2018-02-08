import re
import requests
import xbmc,time
import urllib
from ..scraper import Scraper
from ..common import clean_title,clean_search 


session = requests.Session()
User_Agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'

class imdark(Scraper):
    domains = ['http://imdark.com']
    name = "ImDark"
    sources = []

    def __init__(self):
        self.base_link = 'http://imdark.com'
        self.sources = []
        self.start_time = time.time()

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            headers={'User-Agent':User_Agent}
            get_search_value = requests.get(self.base_link,headers=headers,timeout=5).content
            search_value = re.compile('id="darkestsearch".+?value="(.+?)"',re.DOTALL).findall(get_search_value)[0]
            #print search_value
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s&darkestsearch=%s&_wp_http_referer=/&quality=&genre=&year=&lang=en' %(self.base_link,search_id.replace(' ','+'),search_value)
            headers={'User-Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content
            
            match = re.compile('style="color:white.+?href="(.+?)">(.+?)</a>',re.DOTALL).findall(html)
            for url,name in match:
                check_name = name.split('(')[0]
                if clean_title(title).lower() == clean_title(check_name).lower():
                    if year in name:
                        print 'pass >>>>>>>> '+url
                        self.get_source(url)
            return self.sources
        except Exception, argument:
            return self.sources

    def get_source(self,url):
        try:
            headers={'User-Agent':User_Agent}
            OPEN = requests.get(url,headers=headers,timeout=5).content
            uniques = []
            Regex = re.compile('"src":"(.+?)".+?"data-res":"(.+?)"',re.DOTALL).findall(OPEN)
            for link,qual in Regex:
                link = link+'|Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36&Referer='+url
                if '1080' in qual:
                    rez='1080p'
                elif '720' in qual:
                    rez = '720p'
                else:
                    rez = 'SD'
                if link not in uniques:
                    uniques.append(link)
                    self.sources.append({'source': 'DirectLink', 'quality': rez, 'scraper': self.name, 'url': link,'direct': True})
            end_time = time.time()
            total_time = end_time - self.start_time
            print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"               
        except:
            pass

