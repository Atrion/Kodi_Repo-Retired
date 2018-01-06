import re
import urllib
import requests
import time

from ..common import clean_title,clean_search, random_agent
from ..scraper import Scraper

class filepursuit(Scraper):
    domains = ['filepursuit.com']
    name = "FilePursuit"

    def __init__(self):
        self.base_link = 'https://filepursuit.com'
        self.sources = []
        self.start_time = time.time()

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            scrape = clean_search(title.lower()) + year
            start_url = '%s/search/%s/type/video' %(self.base_link,scrape.replace(' ','%20'))
            
            #print "filepursuit start>>> " + start_url
            headers = {'User_Agent':random_agent()}
            results_page = requests.get(start_url, headers=headers,timeout=5).content

            grab_html = re.compile('<a href="(/file/.+?)">(.+?)</a>',re.DOTALL).findall(results_page)
            for item_url,title_info in grab_html:
                name_chk = clean_title(title).lower()+year 
                if name_chk in clean_title(title_info).lower():
                    item_url = self.base_link + item_url
                    #print 'Pass this filepursuit> '+ item_url
                    self.get_source(item_url)
            return self.sources
        except Exception, argument:
            return self.sources 
        
    def scrape_episode(self, title, show_year, year, season, episode, imdb, tvdb, debrid=False):
        try:
                        
            season_pull = "s0%s"%season if len(season)<2 else 's'+season
            episode_pull = "e0%s"%episode if len(episode)<2 else 'e'+episode        
            BOTH=season_pull+episode_pull
            
            scrape = clean_search(title.lower()) + BOTH
            
            start_url = '%s/search/%s/type/video' %(self.base_link,scrape.replace(' ','%20'))
            
            #print "filepursuit start>>> " + start_url
            headers = {'User_Agent':random_agent()}
            results_page = requests.get(start_url, headers=headers,timeout=5).content

            grab_html = re.compile('<a href="(/file/.+?)">(.+?)</a>',re.DOTALL).findall(results_page)
            for item_url,title_info in grab_html:

                name_chk = clean_title(title).lower()+BOTH 
                if name_chk in clean_title(title_info).lower():
                    item_url = self.base_link + item_url
                    #print 'Pass this filepursuit> '+ item_url
                    self.get_source(item_url)
            return self.sources
        except Exception, argument:
            return self.sources 

    def get_source(self,item_url):
        try:
            headers = {'User_Agent':random_agent()}
            linkpage = requests.get(item_url, headers=headers, timeout=5).content
            link = re.compile('data-clipboard-text="(.+?)"',re.DOTALL).findall(linkpage)[0]
            if '1080' in link:
                res = '1080p'
            elif '720' in link:
                res  = '720p'
            else:
                res='DVD'
            end_time = time.time()
            total_time = end_time - self.start_time
            print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"    
            self.sources.append({'source': 'IndexLink','quality': res,'scraper': self.name,'url': link,'direct': True})

        except:pass
