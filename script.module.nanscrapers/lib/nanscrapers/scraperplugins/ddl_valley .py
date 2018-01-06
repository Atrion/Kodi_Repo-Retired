import re,xbmc,urllib,time
from ..scraper import Scraper
import urlresolver
import requests
from ..common import clean_title,clean_search
User_Agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
from nanscrapers.modules import cfscrape 
# kept movies off

class ddl_valley(Scraper):
    domains = ['http://www.ddlvalley.me']
    name = "DDLValley"
    sources = []

    def __init__(self):
        self.base_link = 'http://www.ddlvalley.me'
        self.scraper = cfscrape.create_scraper()
        self.sources = []
        self.start_time = time.time()

    # def scrape_movie(self, title, year, imdb, debrid=False):
        # try:            
            # start_url = "%s/search/%s+%s/" % (self.base_link, title.replace(' ','+').lower(),year)
            
            # headers = {'User_Agent':User_Agent}
            # OPEN = open_url(start_url,headers=headers,timeout=5).content
            
            # content = re.compile('<h2><a href="([^"]+)"',re.DOTALL).findall(OPEN)
            # for url in content:
                # self.get_source(url)                        
            # return self.sources
        # except Exception, argument:
            # return self.sources           
            

    def scrape_episode(self,title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            if not debrid:
                return []
            season_url = "0%s"%season if len(season)<2 else season
            episode_url = "0%s"%episode if len(episode)<2 else episode
            sea_epi ='s%se%s'%(season_url,episode_url)
            
            start_url = "%s/search/%s+%s/" % (self.base_link, title.replace(' ','+').lower(),sea_epi)
            #print 'SEARCH >>> ::::: '+start_url
            headers = {'Host':'www.ddlvalley.me','User-Agent':User_Agent, 'Referer':'http://www.ddlvalley.me/'}
            OPEN = self.scraper.get(start_url,headers=headers,timeout=5).content
            #print 'search page '+OPEN
            content = re.compile('<h2><a href="([^"]+)"',re.DOTALL).findall(OPEN)
            for url in content:
                
                if clean_title(title).lower() in clean_title(url).lower():
                    #print 'me test ' +url
                    self.get_source(url)                        
            return self.sources
        except Exception, argument:
            return self.sources  

            
    def get_source(self,url):
        try:
            #print 'cfwd'+ url
            headers = {'Host':'www.ddlvalley.me','User-Agent':User_Agent, 'Referer':'http://www.ddlvalley.me/'}
            links = self.scraper.get(url,headers=headers,timeout=3).content 
            #print links
            LINK = re.compile('href="([^"]+)" rel="nofollow"',re.DOTALL).findall(links)
                        
            for url in LINK:
                #print 'DDL link >'+url
                if '1080' in url:
                    res = '1080p'
                elif '720' in url:
                    res = '720p'
                elif 'HDTV' in url:
                    res = 'HD'
                else:
                    pass
                if not '.rar' in url:
                    if not '.srt' in url:
                        if urlresolver.HostedMediaFile(url).valid_url():
                            host = url.split('//')[1].replace('www.','')
                            host = host.split('/')[0].split('.')[0].title()
                            if 'openload' in url:
                                end_time = time.time()
                                total_time = end_time - self.start_time
                                print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"
                                self.sources.append({'source': host,'quality': res,'scraper': self.name,'url': url,'direct': False})
                            else:
                                end_time = time.time()
                                total_time = end_time - self.start_time
                                print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"
                                self.sources.append({'source': host,'quality': res,'scraper': self.name,'url': url,'direct': False, 'debridonly': True})

        except:pass

