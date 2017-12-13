# -*- coding: utf-8 -*-
import re
import requests
from ..scraper import Scraper
import xbmc
from BeautifulSoup import BeautifulSoup



class bnw(Scraper):
    name = "BnwMovies"
    domains = ['http://www.bnwmovies.com']
    sources = []

    def __init__(self):
        self.base_link = 'http://www.bnwmovies.com'
        self.search_link = "/?s="
        

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            start_url= self.base_link+self.search_link+title.replace(' ','+')
            html = requests.get(start_url,timeout=20).content
            match = re.compile('<div class="post">.+?<h3>.+?href="(.+?)".+?rel="bookmark">(.+?)</a>',re.DOTALL).findall(html)
            for url,alt in match:
                if title.lower() == alt.lower():
                    print alt
                    html2 = requests.get(url).content
                    match2 = re.compile('<title >(.+?)</title>',re.DOTALL).findall(html2)
                    for rel in match2:
                        if year in rel:
                            Link = re.compile('<source.+?src="(.+?)"',re.DOTALL).findall(html2)[-1] 
                            playlink = Link
                            self.sources.append(
                            {'source': 'bnw', 'quality': 'unknown',
                             'scraper': self.name, 'url': playlink,
                             'direct': True})
                    
            return self.sources
        except Exception as e:
            return []

#dll2().scrape_movie('Dracula', '1931','')             
