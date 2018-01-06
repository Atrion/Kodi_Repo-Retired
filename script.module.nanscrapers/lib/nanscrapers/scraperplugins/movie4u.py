import requests
import re
import xbmc,time
from ..common import clean_title, clean_search
from ..scraper import Scraper
            
requests.packages.urllib3.disable_warnings()

s = requests.session()
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
                                           
class movie4u(Scraper):
    domains = ['https://movie4u.ch']
    name = "movie4u"
    sources = []

    def __init__(self):
        self.base_link = 'https://movie4u.ch'
        self.search_url = '/?s='
        self.start_time = time.time()

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s' %(self.base_link,search_id.replace(' ','+'))
            #print 'GW> '+start_url
            headers={'User-Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content
            match = re.compile('<div class="title">.+?href="(.+?)">(.+?)</a>.+?class="year">(.+?)</span>',re.DOTALL).findall(html)
            for url,name,date in match:
                #print name
                if clean_title(title).lower() in clean_title(name).lower():
                    if year in date:
                        self.get_source(url)
            
            return self.sources
        except:
            pass
            return[]

    def get_source(self,url):
        try:
            headers={'User-Agent':User_Agent}
            OPEN = requests.get(url,headers=headers,timeout=10).content
            Regex = re.compile('class="metaframe rptss" src="(.+?)"',re.DOTALL).findall(OPEN)
            for link in Regex:
                host = link.split('//')[1].replace('www.','')
                host = host.split('/')[0].split('.')[0].title()
                if 'streamango.com' in link:
                    #print link
                    holder = requests.get(link).content
                    vid = re.compile('type:"video/mp4".+?height:(.+?),',re.DOTALL).findall(holder)
                    for qual in vid:
                        self.sources.append({'source': host, 'quality': qual, 'scraper': self.name, 'url': url,'direct': False})            
                              
                else:
                    self.sources.append({'source': host, 'quality': '720', 'scraper': self.name, 'url': link,'direct': False})
            end_time = time.time()
            total_time = end_time - self.start_time
            print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"                   
        except:
            pass
