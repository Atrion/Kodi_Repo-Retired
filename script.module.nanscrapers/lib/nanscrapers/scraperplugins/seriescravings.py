import re,urllib,urlparse
import xbmc
from ..scraper import Scraper
import requests
from ..common import clean_title,clean_search, filter_host
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'

# kept movies off

class seriescravings(Scraper):
    domains = ['http://series-cravings.tv']# domain to .tv from .me
    name = "SeriesCraving"
    sources = []

    def __init__(self):
        self.base_link = 'http://series-cravings.tv'# changed base_link to .tv from .me
        self.sources = []
                     

    def scrape_episode(self,title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:

            episode_bollox ='-season-%s-episode-%s' %(season,episode)
            
            start_url = "%s/?s=%s" % (self.base_link, title.replace(' ','+').lower())#changed search from/search/ to /?s=
            #xbmc.log('final_url:'+repr(start_url),xbmc.LOGNOTICE)
            headers = {'User_Agent':User_Agent}
            OPEN = requests.get(start_url,headers=headers,timeout=5).content
            #xbmc.log('final_url:'+repr(OPEN),xbmc.LOGNOTICE)

            content = re.compile('<h1 class="entry-title".+?href="(.+?)" rel="bookmark">(.+?)</a>',re.DOTALL).findall(OPEN)
            for show_url,item_title in content:

                item_title=item_title.replace('Watch','').replace('Online','').replace('Free','')
                #print item_title

                if clean_title(title).lower() == clean_title(item_title).lower():
                    #xbmc.log('show_url:'+repr(show_url),xbmc.LOGNOTICE)
                    headers = {'User_Agent':User_Agent}
                    page = requests.get(show_url,headers=headers,timeout=5).content 
                    epis = re.compile('<li>.+?href="(.+?)"',re.DOTALL).findall(page)
                    for url in epis:
                        #xbmc.log('_url:'+repr(url),xbmc.LOGNOTICE)
                        if episode_bollox in url:
                            #xbmc.log('bolox_url:'+repr(url),xbmc.LOGNOTICE)
                            self.get_source(url)                        
            return self.sources
        except Exception, argument:
            return self.sources  

            
    def get_source(self,url):
        try:        
            headers = {'User_Agent':User_Agent}
            links = requests.get(url,headers=headers,timeout=3).content   
            LINK = re.compile('<iframe.+?src="(.+?)"',re.DOTALL).findall(links)
                        
            for final_url in LINK:
                #xbmc.log('final_url:'+repr(final_url),xbmc.LOGNOTICE)
                host = final_url.split('//')[1].replace('www.','')
                host = host.split('/')[0].lower()
                if 'openload' in final_url:
                    chk = requests.get(final_url).content
                    rez = re.compile('"description" content="(.+?)"',re.DOTALL).findall(chk)[0]
                    if '1080' in rez:
                        res='1080p'
                    elif '720' in rez:
                        res='720p'
                    else:
                        res ='DVD'
                else: res = 'DVD'
                if not filter_host(host):
                    continue
                self.sources.append({'source': host,'quality': res,'scraper': self.name,'url': final_url,'direct': False})

        except:pass

#seriescravings().scrape_episode('the walking dead', '', '', '8', '8', '', '')