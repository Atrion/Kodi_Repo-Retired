import requests
import re
import xbmc,xbmcaddon,time
from ..scraper import Scraper
from ..common import clean_title,clean_search,send_log,error_log
from nanscrapers.modules import cfscrape

dev_log = xbmcaddon.Addon('script.module.nanscrapers').getSetting("dev_log")            
requests.packages.urllib3.disable_warnings()

s = requests.session()
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
                                           
class Dudmovies(Scraper):
    domains = ['http://dudmovies.com/']
    name = "Dudmovies"
    sources = []

    def __init__(self):
        self.base_link = 'http://dudmovies.com'
        self.scraper = cfscrape.create_scraper()
        if dev_log=='true':
            self.start_time = time.time()        

    # def scrape_episode(self, title, show_year, year, season, episode, imdb, tvdb, debrid = False):
    #     try:
    #         start_url = self.base_link + '/episodes/' + title.replace(' ','-') + '-' + season + 'x' + episode
    #         #print 'GW> '+start_url
    #         html = requests.get(start_url).content
    #         #print 'PAGE > '+html
    #         match = re.compile('class="metaframe rptss" src="(.+?)"').findall(html)
    #         for link in match: 
    #             host = link.split('//')[1].replace('www.','')
    #             host = host.split('/')[0].split('.')[0].title()
    #             if 'streamango.com' in link:
    #                 holder = requests.get(link).content
    #                 vid = re.compile('type:"video/mp4",src:"(.+?)",height:(.+?),',re.DOTALL).findall(holder)
    #                 for url,qual in vid:
    #                     self.sources.append({'source': host, 'quality': qual, 'scraper': self.name, 'url': 'http:'+url,'direct': True})            
    #             else:
    #                 self.sources.append({'source': host, 'quality': '720', 'scraper': self.name, 'url': link,'direct': False})
                                    
  
    #         return self.sources
    #     except Exception, argument:
    #         return self.sources                          

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = self.base_link + '/?s=' + search_id.replace(' ','+')
            #print 'dud_search> '+start_url
            headers={'User-Agent':User_Agent,'referer':'https://dudmovies.com/'}
            html = self.scraper.get(start_url,headers=headers,timeout=5).content
            #print html
            match = re.compile('class="ml-item".+?href="(.+?)".+?oldtitle="(.+?)"',re.DOTALL).findall(html)
            uniques = []
            for url,name in match:
                if clean_title(title).lower() in clean_title(name).lower():
                    url = 'https:'+url
                    if url not in uniques:
                        uniques.append(url)
                        self.get_source(url,year)
            return self.sources
        except Exception, argument:        
            if dev_log == 'true':
                error_log(self.name,'Check Search')
            return self.sources

    def get_source(self,url,year):
        try:
            #print 'CHECK #################################### '+url
            headers={'User-Agent':User_Agent}
            OPEN = self.scraper.get(url,headers=headers,timeout=10).content
            check = re.compile('<span class="quality">(.+?)</span>.+?rel="tag">(.+?)</a>',re.DOTALL).findall(OPEN)
            for qual,date in check:
                if year in date:
                    Regex = re.compile('<div class="movieplay.+?src="(.+?)"',re.DOTALL).findall(OPEN)
                    count = 0
                    for link in Regex:
                        link = 'https:'+link
                        host = link.split('//')[1].replace('www.','')
                        host = host.split('/')[0].split('.')[0].title()
                        count +=1

                        self.sources.append({'source': host, 'quality': qual, 'scraper': self.name, 'url': link,'direct': False})
                    if dev_log=='true':
                        end_time = time.time() - self.start_time
                        send_log(self.name,end_time,count)               
        except:
            pass

