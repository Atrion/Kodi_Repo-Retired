import re
import urllib
import requests

from ..common import clean_title,clean_search, random_agent,filter_host
from ..scraper import Scraper

User_Agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H143 Safari/600.1.4'


class Watchepisodes(Scraper):
    domains = ['watch-episodes.co']
    name = "Watchepisodes"

    def __init__(self):
        self.base_link = 'http://www.watchepisodes4.com/'
        self.sources = []

    def scrape_episode(self, title, show_year, year, season, episode, imdb, tvdb, debrid=False):
        try:
            scrape = clean_search(title.lower())
            start_url = '%ssearch/ajax_search?q=%s' %(self.base_link,scrape)
            #print 'SEARCH  > '+start_url
            headers = {'User_Agent':User_Agent}
            html = requests.get(start_url, headers=headers,timeout=5).content
            #print html
            regex = re.compile('"value":"(.+?)","seo":"(.+?)"',re.DOTALL).findall(html) 
            for name,link_title in regex:
                if clean_title(title).lower() == clean_title(name).lower():
                    show_page = self.base_link + link_title
                    
                    format_grab = 'season-%s-episode-%s' %(season, episode)
                    #print 'format ' + format_grab
                    headers = {'User_Agent':User_Agent}
                    linkspage = requests.get(show_page, headers=headers,timeout=5).content
                    series_links = re.compile('<div class="el-item.+?href="(.+?)"',re.DOTALL).findall(linkspage)
                    for episode_url in series_links:
                        if format_grab in episode_url:
                            #print 'PASS ME >>>>>>>> '+episode_url
                            self.get_sources(episode_url)
 
            return self.sources
        except Exception, argument:
            return self.sources 

    def get_sources(self, episode_url):
        #print '::::::::::::::'+episode_url
        try:
            headers = {'User_Agent':User_Agent}
            links = requests.get(episode_url,headers=headers,timeout=5).content   
            LINK = re.compile('<div class="link-number".+?data-actuallink="(.+?)"',re.DOTALL).findall(links)
                        
            for final_url in LINK:
                #print final_url
                host = final_url.split('//')[1].replace('www.','')
                host = host.split('/')[0].lower()
                if not filter_host(host):
                    continue
                host = host.split('.')[0].title()
                self.sources.append({'source': host,'quality': 'DVD','scraper': self.name,'url': final_url,'direct': False})

        except:pass
