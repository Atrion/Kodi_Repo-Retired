import re
import xbmc,urlparse
from ..scraper import Scraper
from ..common import clean_title,clean_search, filter_host, get_rd_domains           
import requests

User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
 
class cinemamkv(Scraper):
    domains = ['http://cinemamkv.net']
    name = "CinemaMKV"
    sources = []

    def __init__(self):
        self.base_link = 'http://cinemamkv.net'
           

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = self.base_link + '/?s=' + search_id.replace(' ','+')
            print '@@@@@'+start_url
            headers={'User-Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content
            match = re.compile('<h2><a href="(.+?)".+?>(.+?)</a></h2>',re.DOTALL).findall(html)
            for url,item_name in match:
                movchk= item_name.split('(')[0]
                if clean_title(title).lower() == clean_title(movchk).lower():
                    if year in item_name:
                        self.get_source(url)

            return self.sources
        except:
            pass
            return[]

            
    def get_source(self,url):
        try:
            #print 'CHKURL >'+url
            rez = url.upper()
            if '1080' in rez:
                res = '1080p'
            elif '720' in rez:
                res = '720p'
            else: 
                res = 'DVD'
            headers={'User-Agent':User_Agent}
            OPEN = requests.get(url,headers=headers,timeout=5).content
            print OPEN
            Regex2 = re.compile('<a href="(.+?)"',re.DOTALL).findall(OPEN)
            for link in Regex2:
                if 'facebook' not in link:
                    #print 'this '+link
                    try:
                        host = link.split('//')[1].replace('www.','')
                        host = host.split('/')[0].lower()
                    except:pass
                    if not filter_host(host):
                        continue
                    if '1080' in link:
                        qual = '1080p'
                    elif '720' in link:
                        qual = '720p'
                    else:
                        qual = res
                    self.sources.append({'source': host,'quality': qual,'scraper': self.name,'url': link,'direct': False}) 
                    # if not filter_host(host):
                        # continue
                    # rd_domains = get_rd_domains()
                    # if host in rd_domains:
                        # self.sources.append({'source': host,'quality': res,'scraper': self.name,'url': link,'direct': False,'debridonly': True})
                    # else:
                        # self.sources.append({'source': host,'quality': res,'scraper': self.name,'url': link,'direct': False})                  
        except:
            pass

