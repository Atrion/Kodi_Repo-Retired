import re,time
import requests
import xbmc
import urllib
import urlresolver
from ..scraper import Scraper
from ..common import clean_title,clean_search
from nanscrapers.modules import cfscrape
requests.packages.urllib3.disable_warnings()
User_Agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H143 Safari/600.1.4'


class series9(Scraper):
    domains = ['https://series9.co']
    name = "series9"
    sources = []

    def __init__(self):
        self.base_link = 'https://series9.co'
        self.scraper = cfscrape.create_scraper()
        self.start_time = time.time()
        self.sources = []
        

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/movie/search/%s' %(self.base_link,search_id.replace(' ','-'))
            #print 'search movie series9 >>>> '+start_url
            headers = {'User_Agent':User_Agent}
            html = self.scraper.get(start_url,headers=headers,timeout=5).content
            #print html
            Regex = re.compile('<div class="ml-item">.+?href="(.+?)".+?title="(.+?)">',re.DOTALL).findall(html)
            for item_url,name in Regex:
                if clean_title(title).lower() == clean_title(name).lower():
                    movie_link = self.base_link + item_url+'/watching.html'
                    #print 'series9 movieLINK>>>'+ movie_link
                    self.get_source(movie_link,year)
                
            return self.sources
        except Exception, argument:
            return self.sources

    def scrape_episode(self, title, show_year, year, season, episode, imdb, tvdb, debrid = False):

        try:
            search_id = clean_search(title.lower())
            start_url = '%s/movie/search/%s' %(self.base_link,search_id.replace(' ','-'))
            #print 'search TV series9>>>> '+start_url
            headers = {'User_Agent':User_Agent}
            html = self.scraper.get(start_url,headers=headers,timeout=5).content
            #print html
            Regex = re.compile('<div class="ml-item">.+?href="(.+?)".+?title="(.+?)">',re.DOTALL).findall(html)
            for item_url,name in Regex:
                strip_name = name.split('-')[0]
                if clean_title(title).lower() == clean_title(strip_name).lower():
                    season_chk = '-season-%s' %(season)
                    if season_chk in item_url:
                    
                        movie_link = self.base_link + item_url+'/watching.html'
                        #print 'series9 TV LINK>>>'+ movie_link
                        self.get_tv_source(movie_link,episode)
                
            return self.sources
        except Exception, argument:
            return self.sources
                                    
            
    def get_source(self,movie_link,year):
        try:
            headers = {'User_Agent':User_Agent}
            movpage = self.scraper.get(movie_link,headers=headers,timeout=5).content

            chkdate = re.compile('Release:(.+?)</p>',re.DOTALL).findall(movpage)
            for date in chkdate:
                if year in date:
                    sources = re.compile('player-data="(.+?)"',re.DOTALL).findall(movpage)
                    for link in sources:
                        
                        if 'vidnode' in link:
                            if not link.startswith('http:'):
                                link = 'http:' + link
                            link = link.replace('/streaming','/load')
                            headers = {'User_Agent':User_Agent}
                            holder = self.scraper.get(link,headers=headers,verify=False,timeout=5).content
                            #print 'Movie holder'+holder
                            links = re.compile("file: '(.+?)',label: '(.+?)'",re.DOTALL).findall(holder)
                            for final_url,rez in links:
                                if '1080' in rez:
                                    res='1080p'
                                elif '720' in rez:
                                    res = '720p'
                                elif 'auto' in rez:
                                    res = '720p'
                                else:
                                    res = 'DVD'
                                if not final_url.startswith('http'):
                                    final_url = 'http:' + final_url

                                self.sources.append({'source': 'DirectLink','quality': res,'scraper': self.name,'url': final_url,'direct': True})
                        else:
                            if urlresolver.HostedMediaFile(link).valid_url():
                                host = link.split('//')[1].replace('www.','')
                                host = host.split('/')[0].split('.')[0].title()
                                #print 'appended >>> ' + final_url
                                self.sources.append({'source': host,'quality': 'DVD','scraper': self.name,'url': link,'direct': False})
            end_time = time.time()
            total_time = end_time - self.start_time 
            SEND2LOG(self.name,total_time)
        except:
            pass
           
    def get_tv_source(self,movie_link,episode):
        try:
            #print 'PASSED URL tv> '+movie_link
            headers = {'User_Agent':User_Agent}
            movpage = self.scraper.get(movie_link,headers=headers,timeout=5).content
            #print 'newge '+movpage
            sources = re.compile('player-data="(.+?)" episode-data="(.+?)"',re.DOTALL).findall(movpage)
            for link,epis_no in sources:
                if epis_no == episode:
                    #print 'link grab ' + link 
                    #print 'episode grab ' + epis_no                
                    if 'vidnode' in link:
                        if not link.startswith('http:'):
                            link = 'http:' + link
                        link = link.replace('/streaming','/load')
                        #print 'gw check link > ' + link
                        headers = {'User_Agent':User_Agent}
                        holder = self.scraper.get(link,headers=headers,verify=False,timeout=5).content

                        links = re.compile("file: '(.+?)',label: '(.+?)'",re.DOTALL).findall(holder)
                        for final_url,rez in links:
                            if '1080' in rez:
                                res='1080p'
                            elif '720' in rez:
                                res = '720p'
                            else:
                                res = 'DVD'
                            if not final_url.startswith('http'):
                                final_url = 'http:' + final_url
                            #print 'appended >>> ' + final_url
                            self.sources.append({'source': 'DirectLink','quality': res,'scraper': self.name,'url': final_url,'direct': True})
                    else:
                        if urlresolver.HostedMediaFile(link).valid_url():
                            host = link.split('//')[1].replace('www.','')
                            host = host.split('/')[0].split('.')[0].title()
                            #print 'appended >>> ' + final_url
                            self.sources.append({'source': host,'quality': 'DVD','scraper': self.name,'url': link,'direct': False})
            end_time = time.time()
            total_time = end_time - self.start_time 
            SEND2LOG(self.name,total_time)
        except:
            pass
            
def SEND2LOG(name,Txt):
    print '#################################################################################'
    print '#'
    print '#  Scraper : %s   Time for Completion: %s  ' %(name,(str(Txt)))
    print '#'
    print '#################################################################################'  
    return 