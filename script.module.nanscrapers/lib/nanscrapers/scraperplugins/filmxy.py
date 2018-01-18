import re,xbmcaddon,time
from ..common import clean_title, clean_search,send_log,error_log
from ..scraper import Scraper
import requests 
import urlresolver      

dev_log = xbmcaddon.Addon('script.module.nanscrapers').getSetting("dev_log")
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
# cant log fully without getting multi prints 
                                           
class filmxy(Scraper):
    domains = ['http://www.filmxy.me']
    name = "FilmXY"
    sources = []

    def __init__(self):
        self.base_link = 'http://www.filmxy.me'
        #self.start_time = ''
        #self.count = 0

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            uniques = []
            # if dev_log=='true':
                # self.start_time = time.time()        
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s' %(self.base_link,search_id.replace(' ','+'))
            #print 'filmxy> '+start_url
            headers={'User-Agent':User_Agent,'referrer':self.base_link}
            html = requests.get(start_url,headers=headers,timeout=10).content
            #print 'filmxysearcg> '+html
            match = re.compile('class="post-thumbnail".+?href="(.+?)".+?class="post-title".+?<h2>(.+?)</h2>',re.DOTALL).findall(html)
            
            for mov_url,mov_tit in match:
                chk_tit=mov_tit.split('(')[0]
                if not clean_title(title).lower() == clean_title(chk_tit).lower():
                    continue
                if not year in mov_tit:
                    continue
                #print 'filmxypassed1 ' +mov_url
                if mov_url not in uniques:
                    uniques.append(mov_url)
                    #print 'filmxypassed2 ## ' +mov_url
                    self.get_source(mov_url)
            
            return self.sources
        except Exception, argument:        
            if dev_log == 'true':
                error_log(self.name,'Check Search')
            return self.sources

    def get_source(self,mov_url):
        try:
            try:
                headers={'User-Agent':User_Agent,'referrer':self.base_link}
                OPEN = requests.get(mov_url,headers=headers,timeout=5).content
                #print 'linkpage'+OPEN
                block720 = re.compile('class="links_720p"(.+?)</ul>',re.DOTALL).findall(OPEN)
                Regex = re.compile('href="(.+?)"',re.DOTALL).findall(str(block720)) 
                for link in Regex:
                    #print 'GRABBED'+link
                    if not urlresolver.HostedMediaFile(link):
                        continue
                    host = link.split('//')[1].replace('www.','')
                    host = host.split('/')[0].split('.')[0].title()
                    #self.count +=1   
                    self.sources.append({'source': host, 'quality': '720p', 'scraper': self.name, 'url': link,'direct': False}) 
            except:pass
            try:
                block1080 = re.compile('class="links_1080p"(.+?)</ul>',re.DOTALL).findall(OPEN)
                Regex2 = re.compile('href="(.+?)"',re.DOTALL).findall(str(block1080)) 
                for link in Regex2:
                    #print 'GRABBED'+link
                    if not urlresolver.HostedMediaFile(link):
                        continue
                    host = link.split('//')[1].replace('www.','')
                    host = host.split('/')[0].split('.')[0].title()
                    #self.count +=1    
                    self.sources.append({'source': host, 'quality': '1080p', 'scraper': self.name, 'url': link,'direct': False})  
            except:pass
            # if dev_log=='true':
                # end_time = time.time()
                # total_time = end_time - self.start_time 
                # send_log(self.name,total_time,self.count)                
        except:pass
