import re
import xbmc
from ..common import clean_title, clean_search, filter_host,get_rd_domains
from ..scraper import Scraper
import requests       

User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
                                           
class filmxy(Scraper):
    domains = ['http://www.filmxy.me']
    name = "FilmXY"
    sources = []

    def __init__(self):
        self.base_link = 'http://www.filmxy.me'

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s' %(self.base_link,search_id.replace(' ','+'))
            print 'GW> '+start_url
            headers={'User-Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=10).content
            match = re.compile('class="post-thumbnail".+?href="(.+?)".+?class="post-title".+?<h2>(.+?)</h2>',re.DOTALL).findall(html)
            for mov_url,mov_tit in match:
                #print 'FILMXY grabs %s %s' %(mov_url,mov_tit)
                chk_tit = mov_tit.split('(')[0]
                #print chk_tit
                if clean_title(title).lower() == clean_title(chk_tit).lower():
                    if year in mov_tit:
                        if '/links/' in mov_url:
                            print 'NEW passthis CHECK XY > '+mov_url
                            self.get_source(mov_url)
            
            return self.sources
        except:
            pass
            return[]

    def get_source(self,mov_url):
        try:
            headers={'User-Agent':User_Agent}
            OPEN = requests.get(mov_url,headers=headers,timeout=10).content
            
            block720 = re.compile('class="links_720p"(.+?)</ul>',re.DOTALL).findall(OPEN)
            Regex = re.compile('href="(.+?)"',re.DOTALL).findall(str(block720)) 
            for link in Regex:
                print 'gw link'+link
                host = link.split('//')[1].replace('www.','')
                host = host.split('/')[0].lower()
                if not filter_host(host):
                    continue
                rd_domains = get_rd_domains()
                if host in rd_domains:
                    self.sources.append({'source': host, 'quality': '720p', 'scraper': self.name, 'url': link,'direct': False, 'debridonly': True})
                else: 
                    self.sources.append({'source': host, 'quality': '720p', 'scraper': self.name, 'url': link,'direct': False}) 
            
            block1080 = re.compile('class="links_1080p"(.+?)</ul>',re.DOTALL).findall(OPEN)
            Regex2 = re.compile('href="(.+?)"',re.DOTALL).findall(str(block1080)) 
            for link in Regex2:
                host = link.split('//')[1].replace('www.','')
                host = host.split('/')[0].lower()
                if not filter_host(host):
                    continue
                rd_domains = get_rd_domains()
                if host in rd_domains:
                    self.sources.append({'source': host, 'quality': '1080p', 'scraper': self.name, 'url': link,'direct': False, 'debridonly': True})
                else: 
                    self.sources.append({'source': host, 'quality': '1080p', 'scraper': self.name, 'url': link,'direct': False})         
        except:
            pass
