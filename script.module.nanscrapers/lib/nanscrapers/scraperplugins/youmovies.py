import requests
import re,xbmcaddon,time  
from ..scraper import Scraper
from ..common import clean_title,clean_search,send_log,error_log
dev_log = xbmcaddon.Addon('script.module.nanscrapers').getSetting("dev_log")
User_Agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H143 Safari/600.1.4'


class wyoumovies(Scraper):
    domains = ['youmovies.tv']
    name = "youmovies"
    sources = []

    def __init__(self):
        self.base_link = 'http://youmovies.tv'
        self.sources = []
        self.start_time = ''

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            if dev_log=='true':
                self.start_time = time.time() 
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s' %(self.base_link,search_id.replace(' ','+'))
            headers = {'User_Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content
            Regex = re.compile('class="item">.+?<a href="(.+?)">.+?alt="(.+?)"',re.DOTALL).findall(html)
            for item_url,name in Regex:
                if clean_title(title).lower() == clean_title(name).lower():
                        movie_link = item_url
                        self.get_source(movie_link,year)
                
            return self.sources
        except Exception, argument:        
            if dev_log == 'true':
                error_log(self.name,'Check Search')
            return self.sources

    def get_source(self,movie_link,year):
        try:
            html = requests.get(movie_link).content
            chkdate = re.compile('<p class="meta">.+?rel="tag">(.+?)</a>',re.DOTALL).findall(html)
            for date in chkdate:
                if year==date:
                    links = re.compile('<div class="movieplay">.+?<iframe src="(.+?)"',re.DOTALL).findall(html)
                    count = 0
                    for link in links:
                        if 'openload' in link:
                            try:
                                headers = {'User_Agent':User_Agent}
                                get_res=requests.get(link,headers=headers,timeout=5).content
                                rez = re.compile('description" content="(.+?)"',re.DOTALL).findall(get_res)[0]
                                if '1080p' in rez:
                                    qual = '1080p'
                                elif '720p' in rez:
                                    qual='720p'
                                else:
                                    qual='DVD'
                            except: qual='DVD' 
                            count +=1
                            self.sources.append({'source': 'Openload','quality': qual,'scraper': self.name,'url': link,'direct': False})
                        else:
                            qual = 'DVD'
                            host = link.split('//')[1].replace('www.','')
                            host = host.split('/')[0].split('.')[0].title()
                            count +=1
                            self.sources.append({'source': host,'quality': qual,'scraper': self.name,'url': link,'direct': False})
                    if dev_log=='true':
                        end_time = time.time() - self.start_time
                        send_log(self.name,end_time,count)
        except:
            pass

