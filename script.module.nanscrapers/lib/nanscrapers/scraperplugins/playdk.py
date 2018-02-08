import requests,urlresolver
import re,xbmcaddon,time  
from ..scraper import Scraper
from ..common import clean_title,clean_search,send_log,error_log
dev_log = xbmcaddon.Addon('script.module.nanscrapers').getSetting("dev_log")
User_Agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H143 Safari/600.1.4'


class playdk(Scraper):
    domains = ['playdk.net']
    name = "playdk"
    sources = []

    def __init__(self):
        self.base_link = 'http://playdk.net'
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
            Regex = re.compile('<div class="result-item">.+?<a href="(.+?)">.+?alt="(.+?)" />.+?<span class="year">(.+?)</span>',re.DOTALL).findall(html)
            for item_url,name,date in Regex:
                if clean_title(title).lower() == clean_title(name).lower():
                    if year in date:
                        movie_link = item_url
                        self.get_source(movie_link)
                
            return self.sources
        except Exception, argument:        
            if dev_log == 'true':
                error_log(self.name,'Check Search')
            return self.sources

    def scrape_episode(self, title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s' %(self.base_link,search_id.replace(' ','+'))
            headers = {'User_Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content
            Regex = re.compile('<div class="result-item">.+?<a href="(.+?)">.+?alt="(.+?)"',re.DOTALL).findall(html)
            for item_url,name in Regex:
                if not clean_title(title).lower() == clean_title(name).lower():
                    continue
                if "/tvshows/" in item_url:
                    movie_link = item_url[:-1].replace('/tvshows/','/episodes/')+'-%sx%s/'%(season,episode)
                    #print 'show to pass '+movie_link
                    self.get_source(movie_link)
                
            return self.sources
        except Exception, argument:        
            if dev_log == 'true':
                error_log(self.name,'Check Search')
            return self.sources

    def get_source(self,movie_link):
        try:
            headers = {'User_Agent':User_Agent}
            html = requests.get(movie_link,headers=headers,timeout=5).content
            links = re.compile('<iframe class="metaframe rptss" src="(.+?)"',re.DOTALL).findall(html)
            count = 0
            for link in links:
                if urlresolver.HostedMediaFile(link):
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

            source = re.compile('"label":"(.+?)".+?"file":"(.+?)"',re.DOTALL).findall(html)
            for label,link in source:
                if '1080' in label:
                    qual = '1080p'
                elif '720' in label:
                    qual='720p'
                else:
                    qual='DVD'
 
                #host = link.split('//')[1].replace('www.','')
                #host = host.split('/')[0].split('.')[0].title()
                count +=1
                self.sources.append({'source': 'Google Video','quality': qual,'scraper': self.name,'url': link,'direct': False})     
            if dev_log=='true':
                end_time = time.time() - self.start_time
                send_log(self.name,end_time,count)                

        except:
            pass

