# -*- coding: utf-8 -*-

import re,xbmc,urllib
from ..scraper import Scraper
import requests,time
from ..common import clean_title,clean_search, filter_host, get_rd_domains,random_agent


class sceper(Scraper):
    domains = ['sceper.ws']
    name = "Sceper.ws"
    sources = []
    
    def __init__(self):
        self.domains = ['sceper.ws']
        self.base_link = 'http://sceper.ws/'
        self.sources = []
        self.start_time = time.time()

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            if not debrid:
                return []
            scrape = clean_search(title.lower())

            headers = {'User-Agent':random_agent(),'referrer':self.base_link}
            
            params = '%s &sites=sceper.ws' %(scrape)
            
            data = {'q': params}
            LINK = 'https://duckduckgo.com/html'
            html = requests.post(LINK,headers=headers,data=data,verify=False).content

            results = re.compile('href="(.+?)"',re.DOTALL).findall(html)
            for url in results:
                if 'sceper' in url:
                    if '/page/' not in url:
                        if 'usunblock' not in url:
                            #print ' pass > '+ url
                        
                            self.get_source(url,title,year)                     
            return self.sources
        except Exception, argument:
            return self.sources  

    def scrape_episode(self,title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            if not debrid:
                return []
            season_url = "0%s"%season if len(season)<2 else season
            episode_url = "0%s"%episode if len(episode)<2 else episode
            sea_epi ='s%se%s'%(season_url,episode_url)
            
            scrape = clean_search(title.lower()) + sea_epi 

            headers = {'User-Agent':random_agent(),'referrer':self.base_link}
            
            params = '%s &sites=sceper.ws' %(scrape)
            
            data = {'q': params}
            LINK = 'https://duckduckgo.com/html'
            html = requests.post(LINK,headers=headers,data=data,verify=False).content

            results = re.compile('href="(.+?)"',re.DOTALL).findall(html)
            for url in results:
                if 'sceper' in url:
                    
                    if sea_epi in url:
                        
                        self.get_tv_source(url,title)                     
            return self.sources
        except Exception, argument:
            return self.sources  

    def get_source(self,url,title,year):
        try:        
            headers = {'User_Agent':random_agent()}
            linkpage = requests.get(url,headers=headers,timeout=3).content
            title_chk = re.compile('<h1 class="title">(.+?)</h1>',re.DOTALL).findall(linkpage)[0]
            #print 'CHECK TIT> ' + title_chk 
            if clean_title(title).lower() in clean_title(title_chk).lower():
                if year in title_chk:
                    Regex = re.compile('class="meta">Download Links</div>(.+?)</div>',re.DOTALL).findall(linkpage)           
                    LINK = re.compile('href="([^"]+)"',re.DOTALL).findall(str(Regex))
                    uniques = []    
                    for url in LINK:
                        if '.rar' not in url:
                            if '.srt' not in url:
                                if '1080' in url:
                                    res = '1080p'
                                elif '720' in url:
                                    res = '720p'
                                elif 'HDTV' in url:
                                    res = 'DVD'
                                else:
                                    pass

                                host = url.split('//')[1].replace('www.','')
                                host = host.split('/')[0].lower()

                                rd_domains = get_rd_domains()
                                if host in rd_domains:
                                    if url not in uniques:
                                        uniques.append(url)
                                        #print '####sceper passed final url check > '+url
                                        end_time = time.time()
                                        total_time = end_time - self.start_time
                                        print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"
                                        self.sources.append({'source': host,'quality': res,'scraper': self.name,'url': url,'direct': False, 'debridonly': True})

        except:pass

    def get_tv_source(self,url,title):
        try:        
            headers = {'User_Agent':random_agent()}
            linkpage = requests.get(url,headers=headers,timeout=3).content
            title_chk = re.compile('<h1 class="title">(.+?)</h1>',re.DOTALL).findall(linkpage)[0]
            #print 'CHECK TIT> ' + title_chk 
            if clean_title(title).lower() in clean_title(title_chk).lower():
                    Regex = re.compile('class="meta">Download Links</div>(.+?)</div>',re.DOTALL).findall(linkpage)           
                    LINK = re.compile('href="([^"]+)"',re.DOTALL).findall(str(Regex))
                    uniques = []    
                    for url in LINK:
                        if '.rar' not in url:
                            if '.srt' not in url:
                                if '1080' in url:
                                    res = '1080p'
                                elif '720' in url:
                                    res = '720p'
                                elif 'HDTV' in url:
                                    res = 'DVD'
                                else:
                                    pass

                                host = url.split('//')[1].replace('www.','')
                                host = host.split('/')[0].lower()

                                rd_domains = get_rd_domains()
                                if host in rd_domains:
                                    if url not in uniques:
                                        uniques.append(url)
                                        #print '####sceper passed final url check > '+url
                                        end_time = time.time()
                                        total_time = end_time - self.start_time
                                        print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"
                                        self.sources.append({'source': host,'quality': res,'scraper': self.name,'url': url,'direct': False, 'debridonly': True})

        except:pass
        