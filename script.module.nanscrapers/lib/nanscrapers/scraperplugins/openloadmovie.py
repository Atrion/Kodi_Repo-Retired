import re
import requests
import xbmc,xbmcaddon,time
from ..scraper import Scraper
from ..common import clean_title,clean_search,send_log,error_log 

dev_log = xbmcaddon.Addon('script.module.nanscrapers').getSetting("dev_log")

User_Agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H143 Safari/600.1.4'


class OpenLoadMovie(Scraper):
    domains = ['https://openloadmovie.me']
    name = "openloadmovie"
    sources = []

    def __init__(self):
        self.base_link = 'https://openloadmovie.me'
        if dev_log=='true':
            self.start_time = time.time()

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s' %(self.base_link,search_id.replace(' ','+'))
            headers = {'User_Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content
            #xbmc.log('************ Passed'+repr(html),xbmc.LOGNOTICE)
            Regex = re.compile('class="result-item".+?href="(.+?)".+?alt="(.+?)"',re.DOTALL).findall(html)   
            for item_url,name in Regex:    # removed date as date isnt seperate
                if not clean_title(title).lower() == clean_title(name).lower():
                    continue
                if not year in name:
                    continue
                movie_link = item_url
                #print 'Grabbed movie url to pass > ' + movie_link   # check whats passed in log 
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
            Regex = re.compile('class="result-item".+?href="(.+?)".+?alt="(.+?)"',re.DOTALL).findall(html)
            for item_url,name in Regex:
                if not clean_title(title).lower() == clean_title(name).lower():
                    continue
                if "/tvshows/" in item_url:
                    movie_link = item_url[:-5].replace('/tvshows/','/episodes/')+'%sx%s/'%(season,episode)
                        
                    self.get_source(movie_link)
                
            return self.sources
        except Exception, argument:        
            if dev_log == 'true':
                error_log(self.name,'Check Search')
            return self.sources

    def get_source(self,movie_link):
        try:
            #print 'passed show '+movie_link
            html = requests.get(movie_link).content
            links = re.compile('data-lazy-src="(.+?)"',re.DOTALL).findall(html) # edit for url in tis case openload link
            count = 0
            for link in links:
                ##usually open openload to get res but shown in url on this site
                # if 'openload' in link:                  
                    # try:
                        # headers = {'User_Agent':User_Agent}
                        # get_res=requests.get(link,headers=headers,timeout=5).content
                        # rez = re.compile('"description" content="(.+?)"',re.DOTALL).findall(get_res)[0]
                        # if '1080p' in rez:
                            # qual = '1080p'
                        # elif '720p' in rez:
                            # qual='720p'
                        # else:
                            # qual='DVD'
                    # except: qual='DVD'        
                    # self.sources.append({'source': 'Openload','quality': qual,'scraper': self.name,'url': link,'direct': False})
                    # end_time = time.time()
                    # total_time = end_time - self.start_time
                    # print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"
                
                if 'youtube' not in link:    # miss trailers
                    if '1080p' in link:
                        qual = '1080p'
                    elif '720p' in link:
                        qual='720p'
                    else:
                        qual='SD'

                    host = link.split('//')[1].replace('www.','')
                    host = host.split('/')[0].split('.')[0].title()
                    count +=1
                    self.sources.append({'source': host,'quality': qual,'scraper': self.name,'url': link,'direct': False})
            if dev_log=='true':
                end_time = time.time() - self.start_time
                send_log(self.name,end_time,count)
        except:
            pass

