import requests
import re
import xbmc,time
from ..scraper import Scraper
requests.packages.urllib3.disable_warnings()
s = requests.session()
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
                                           
class watchstream(Scraper):
    domains = ['https://putlockers.movie']
    name = "Watchstream"
    sources = []

    def __init__(self):
        self.base_link = 'https://putlockers.movie/embed/'
        self.start_time = time.time()
                      
    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            get_link = self.base_link + '%s/' %(imdb)
            headers={'User-Agent':User_Agent}
            html = requests.get(get_link,headers=headers,verify=False,timeout=5).content
            link = re.compile('<iframe src="(.+?)"',re.DOTALL).findall(html)[0]
            try:
                chk = requests.get(link).content
                rez = re.compile('"description" content="(.+?)"',re.DOTALL).findall(chk)[0]
                if '1080' in rez:
                    res='1080p'
                elif '720' in rez:
                    res='720p'
                else:
                    res ='DVD'
            except: res = 'DVD'
            self.sources.append({'source': 'Openload', 'quality': res, 'scraper': self.name, 'url': link,'direct': False})
            end_time = time.time()
            total_time = end_time - self.start_time
            print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"
            
            return self.sources
        except:
            pass
            return[]