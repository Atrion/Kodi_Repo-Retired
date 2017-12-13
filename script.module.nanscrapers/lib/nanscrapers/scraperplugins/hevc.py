import re
import requests
import xbmc
import urllib
from ..scraper import Scraper
from ..common import random_agent, filter_host,get_rd_domains
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'

class hevc(Scraper):
    domains = ['http://hevcbluray.info']
    name = "HevcBluray"
    sources = []

    def __init__(self):
        self.base_link = 'http://hevcbluray.info'
        self.sources = []

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = title.lower()
            movie_url = '%s/search/%s/feed/rss2/' %(self.base_link,search_id.replace(' ','+'))
            #print 'HEVC:::::::::::::::::::::::::::::'+movie_url
            headers = {'User_Agent':random_agent()}
            LINK = requests.get(movie_url,headers=headers, timeout=5).content
            
            match = re.compile('<a rel="nofollow" href="(.+?)">(.+?)<',re.DOTALL).findall(LINK)
            uniques=[]
            for item_url ,TITLE in match:
                if not 'http' in item_url:
                    item_url = 'http://'+item_url
                if item_url not in uniques:
                    uniques.append(item_url)
                    if year in TITLE.lower():
                            
                        self.get_source(item_url)
                
            return self.sources
        except Exception, argument:
            return self.sources

    def get_source(self,item_url):
        #print 'SOURCES pass> '+item_url
        try:
            headers = {'User_Agent':random_agent()}
            LINK = requests.get(item_url,headers=headers, timeout=5).content
            res = item_url.upper()
            #link = LINK.split('Download Links')[0]
            #link = LINK.split('<h3 style="text-align: center;">')
            
           
            try:
                links = re.compile('class="elemento".+?href="([^"]+)"',re.DOTALL).findall(LINK)
                for final_url in links:
                    if '4K' in res:
                        res='4K'
                    elif '3D' in res:
                        res='3D'
                    elif '1080' in res:
                        res='1080p'                   
                    elif '720' in res:
                        res='720p'
                    elif 'HD' in res:
                        res='HD'
                    else:
                        res='SD'
                    HOST = final_url.split('//')[1].replace('www.','')
                    HOST = HOST.split('/')[0].lower()
                    if 'amazon.com' in final_url:
                        self.sources.append({'source': HOST,'quality': res,'scraper': self.name,'url': final_url,'direct': False})
                    if not filter_host(HOST):
                            continue
                    rd_domains = get_rd_domains()
                    if HOST in rd_domains:
                        self.sources.append({'source': HOST,'quality': res,'scraper': self.name,'url': final_url,'direct': False, 'debridonly': True})
                    else:
                        self.sources.append({'source': HOST,'quality': res,'scraper': self.name,'url': final_url,'direct': False})
            except:
                pass
            return self.sources
        except Exception, argument:
            return self.sources