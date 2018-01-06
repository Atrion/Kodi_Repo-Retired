import requests
import re
import xbmc,time
from ..common import clean_title, clean_search
from ..scraper import Scraper
            
requests.packages.urllib3.disable_warnings()

s = requests.session()
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
                                           
class moviewatcher(Scraper):
    domains = ['http://moviewatcher.is/']
    name = "moviewatcher"
    sources = []

    def __init__(self):
        self.base_link = 'http://moviewatcher.is'
        self.start_time = time.time()

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/search?query=%s' %(self.base_link,search_id.replace(' ','+'))
            headers={'User-Agent':User_Agent}
            r = requests.get(start_url,headers=headers,timeout=5)
            page = r.url
            if 'search?query' in page:
                match = re.compile('class="movie-title" href="(.+?)">(.+?)</a>.+?<span class="qual" data-title="Quality">(.+?)</span>',re.DOTALL).findall(r.content)
                for url,name,qual in match:
                    if clean_title(title).lower() in clean_title(name).lower():
                        if year in url:
                            url = self.base_link + url
                            self.get_source(url,qual)
            else:
                self.get_source(page,'unknown')
            
            return self.sources
        except:
            pass
            return[]

    def get_source(self,url,qual):
        try:
            OPEN = requests.get(url).content
            Regex = re.compile("Version.+?window.open.+?'(.+?)'",re.DOTALL).findall(OPEN)
            for link in Regex:
                link = self.base_link + link
                headers={'User-Agent':User_Agent}
                r = requests.get(link,headers=headers,allow_redirects=False)
                stream_url = r.headers['location']
                host = stream_url.split('//')[1].replace('www.','')
                host = host.split('/')[0].split('.')[0].lower()
                self.sources.append({'source': host, 'quality': qual, 'scraper': self.name, 'url': stream_url,'direct': False})
            end_time = time.time()
            total_time = end_time - self.start_time
            print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"               
        except:
            pass
