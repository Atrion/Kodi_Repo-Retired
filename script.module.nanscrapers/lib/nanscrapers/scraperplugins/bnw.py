# -*- coding: utf-8 -*-
import requests,re
import xbmc,time
from ..common import clean_title,clean_search
from ..scraper import Scraper

User_Agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36'

class bnw(Scraper):
    name = "BnwMovies"
    domains = ['http://www.bnwmovies.com']
    sources = []

    def __init__(self):
        self.base_link = 'http://www.bnwmovies.com'
        self.start_time = time.time()
        

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            movie_id = clean_search(title.lower()).replace(' ','+')
            start_url = '%s/?s=%s' %(self.base_link,movie_id)
            headers = headers = {'User-Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=10,allow_redirects=False).content
            match = re.compile('<div class="post">.+?href="(.+?)".+?rel="bookmark">(.+?)</a>',re.DOTALL).findall(html)
            for url,alt in match:
                if clean_title(title).lower() == clean_title(alt).lower():
                    print alt
                    html2 = requests.get(url,headers=headers,allow_redirects=False).content
                    match2 = re.compile('<title >(.+?)</title>',re.DOTALL).findall(html2)
                    for rel in match2:
                        if year in rel:
                            Link = re.compile('<source.+?src="(.+?)"',re.DOTALL).findall(html2)[-1] 
                            playlink = Link
                            self.sources.append(
                            {'source': self.name, 'quality': 'SD',
                             'scraper': self.name, 'url': playlink,
                             'direct': True})
            end_time = time.time()
            total_time = end_time - self.start_time
            print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"        
            return self.sources
        except Exception as e:
            return []

#dll2().scrape_movie('Dracula', '1931','')             
