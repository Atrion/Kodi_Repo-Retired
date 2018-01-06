import requests
import re
import xbmc,time
from ..scraper import Scraper
from ..common import clean_title,clean_search,random_agent

class pinoytva(Scraper):
    domains = ['https://pinoytva.su']
    name = "Pinoytva"
    sources = []

    def __init__(self):
        self.base_link = 'https://pinoytva.su'
        self.start_time = time.time()

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            search_link = '/search/%s.html' %(search_id.replace(" ","-"))
            start_url = self.base_link+search_link
            headers={'User-Agent':random_agent()}
            html = requests.get(start_url,headers=headers,timeout=5).content
            match = re.compile('<li class="film-item ">.+?<a href="(.+?)".+?title="(.+?)"',re.DOTALL).findall(html)
            for link,name in match:
                #print '>>>>>>>>>>>>>>link>>>>>>> '+link
                if clean_title(search_id).lower() == clean_title(name).lower():
                    html2 = requests.get(link).content
                    block = re.compile('<script src="/jwplayer7/jwplayer.js"></script>(.+?)<div class="loading-container">',re.DOTALL).findall(html2)
                    match2 = re.compile('file.+?"(.+?)"',re.DOTALL).findall(str(block))
                    for link2 in match2:
                        final_link = link2.replace("\\","")
                        self.sources.append({'source': self.name, 'quality': 'SD', 'scraper': self.name, 'url': final_link,'direct': True})
            end_time = time.time()
            total_time = end_time - self.start_time
            print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"            
                    
            return self.sources
        except:
            pass
            return[]



