import re
import requests
import xbmc,xbmcaddon,time
import urllib
from ..scraper import Scraper
from ..common import clean_title,clean_search,send_log,error_log

dev_log = xbmcaddon.Addon('script.module.nanscrapers').getSetting("dev_log")

User_Agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'


class uwatchfree(Scraper):
    domains = ['https://www.uwatchfree.tv']
    name = "uwatchfree"
    sources = []

    def __init__(self):
        self.base_link = 'https://www.uwatchfree.tv/'
        self.sources = []
        if dev_log=='true':
            self.start_time = time.time()

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s?s=%s' %(self.base_link,search_id.replace(' ','+'))
            #print 'start_url > '+start_url
            headers = {'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8','accept-encoding':'gzip, deflate, br',
                       'accept-language':'en-US,en;q=0.8','content-type':'text/html; charset=utf-8',
                       'User-Agent':User_Agent,'referer':self.base_link}
            html = requests.get(start_url,headers=headers,timeout=5).content
            #print html
            Regex = re.compile('class="entry-title"><a href="(.+?)".+?rel="bookmark">(.+?)</a>',re.DOTALL).findall(html)
            for item_url,name in Regex:
                #print '%s %s' %(item_url,name)
                if 'Dubbed' not in name:
                    if not clean_title(title).lower() == clean_title(name).lower():
                        continue
                    if not year in name:
                        continue
                    movie_link = item_url
                    #print 'uwatch pass '+movie_link
                    self.get_source(movie_link)
                
            return self.sources
        except Exception, argument:        
            if dev_log == 'true':
                error_log(self.name,'Check Search')
            return self.sources

    def scrape_episode(self,title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            season_get = '0%s' %season if len(season) <2 else season
            episode_get = '0%s' %episode if len(episode) <2 else episode
            s_ep = 's%se%s' %(season_get,episode_get)
            start_url = '%s?s=%s+%s' %(self.base_link,search_id.replace(' ','+'),s_ep)
            headers = {'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8','accept-encoding':'gzip, deflate, br',
                       'accept-language':'en-US,en;q=0.8','content-type':'text/html; charset=utf-8',
                       'User-Agent':User_Agent,'referer':self.base_link}
            html = requests.get(start_url,headers=headers,timeout=5).content
            Regex = re.compile('class="entry-title"><a href="(.+?)".+?rel="bookmark">(.+?)</a>',re.DOTALL).findall(html)
            for item_url,name in Regex:
                if 'Dubbed' not in name:
                    if clean_title(title).lower() in clean_title(name).lower():
                        show_link = item_url
                        self.get_source(show_link)
                
            return self.sources
        except Exception, argument:        
            if dev_log == 'true':
                error_log(self.name,'Check Search')
            return self.sources

    def get_source(self,movie_link):
        try:
            print 'uwatch passed '+movie_link
            headers = {'User-Agent':User_Agent,'referer':self.base_link}
            html = requests.get(movie_link,headers=headers,timeout=5).content
            #print 'thishtmlpage' +html
            sources = re.compile('style="text-align:center".+?href="(.+?)"',re.DOTALL).findall(html)
            count = 0
            for link in sources:
                #print 'catch '+link
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

