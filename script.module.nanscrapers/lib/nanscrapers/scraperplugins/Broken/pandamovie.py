import requests
import re
import xbmc
from ..scraper import Scraper
from ..common import clean_title,clean_search,random_agent,filter_host

  
class pandamovie(Scraper):
    domains = ['https://pandamovie.co/']
    name = "Pandamovie"
    sources = []

    def __init__(self):
        self.base_link = 'https://pandamovie.co/'
        self.search_link = '?s='


    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = self.base_link + self.search_link + search_id.replace(" ","+")
            headers={'User-Agent':random_agent()}
            html = requests.get(start_url,headers=headers,timeout=10).content
            match = re.compile('<span class="overlay"></span>.+?<a href="(.+?)".+?title="(.+?)"',re.DOTALL).findall(html)
            for url,name in match:
                if clean_title(search_id).lower() == clean_title(name).lower():
                    if year in name:
                        self.get_source(url)

            return self.sources
        except Exception as e:
            return[]

    def scrape_episode(self, title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            season_num = "0%s"%season if len(season)<2 else season
            episode_num = "0%s"%episode if len(episode)<2 else episode
            total_num = '-s%se%s' %(season_num,episode_num)     
            url = self.base_link+'tv/watch-'+clean_search(title).replace(" ","-")+total_num+'-tvshow-online-free'
            self.get_source(url)
            return self.sources
        except Exception as e:
            return[]


    def get_source(self,url):
        try:
            headers={'User-Agent':random_agent()}
            html4 = requests.get(url,headers=headers,timeout=10).content
            match4 = re.compile('<div id="pettabs">(.+?)</ul>',re.DOTALL).findall(html4)
            print match4
            match5 = re.compile('href="(.+?)".+?rel="nofollow".+?>(.+?)</a></li>',re.DOTALL).findall(str(match4))
            for link,host in match5:
                print link
                #host = link.split('//')[1].replace('www.','')
                #host = host.split('/')[0].lower()
                #if not filter_host(host):
                #    continue
                self.sources.append({'source': host, 'quality': 'SD', 'scraper': self.name, 'url': link,'direct': False})    
        except:
            pass
            