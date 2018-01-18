import re
import requests
import xbmc,xbmcaddon,time
import urllib
from ..scraper import Scraper
from ..common import clean_title,clean_search,send_log,error_log

dev_log = xbmcaddon.Addon('script.module.nanscrapers').getSetting("dev_log")

User_Agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H143 Safari/600.1.4'


class hdmovieswatch9(Scraper):
    domains = ['http://www.hdmovieswatch9.org']
    name = "hdmovieswatch9"
    sources = []

    def __init__(self):
        self.base_link = 'http://www.hdmovieswatch9.org'
        if dev_log=='true':
            self.start_time = time.time()

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s' %(self.base_link,search_id.replace(' ','+'))
            headers = {'User_Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content
            Regex = re.compile('class="item.+?href="(.+?)".+?alt="(.+?)"',re.DOTALL).findall(html)
            for item_url,name in Regex:
                movie_name, movie_year = re.findall("(.*?)\((\d+)\)", name)[0]
                if not clean_title(title).lower() == clean_title(movie_name).lower():
                    continue
                if not year in movie_year:  
                    continue                
                movie_link = item_url
                self.get_source(movie_link)
                
            return self.sources
        except Exception, argument:        
            if dev_log == 'true':
                error_log(self.name,'Check Search')
            return self.sources

    def get_source(self,movie_link):
        try:
            html = requests.get(movie_link).content
            links = re.compile('<div class="movieplay">.+?<iframe src="(.+?)"',re.DOTALL).findall(html)
            count = 0
            for link in links:
                if '1080' in link:
                    qual = '1080p'
                elif '720' in link:
                    qual='720p'
                else:
                    qual='DVD'
                host = link.split('//')[1].replace('www.','')
                host = host.split('/')[0].split('.')[0].title()
                count +=1
                self.sources.append({'source': host,'quality': qual,'scraper': self.name,'url': link,'direct': False})
            if dev_log=='true':
                end_time = time.time() - self.start_time
                send_log(self.name,end_time,count)
        except:
            pass

