import xbmc,time
import json
import re
import urllib
import urlparse

import requests
from BeautifulSoup import BeautifulSoup as BS
from nanscrapers.common import clean_title, random_agent, replaceHTMLCodes
from ..scraper import Scraper

session = requests.Session()
headers = {"User-Agent": random_agent()}

class freemusic(Scraper):
    domains = ['freemusicdownloads']
    name = "Freemusic"
    sources = []
    

    def __init__(self):
        self.base_link = 'http://down.freemusicdownloads.world/'
        self.sources = []
        self.start_time = time.time()
    
    def scrape_music(self, title, artist, debrid=False):
        try:
            song_search = clean_title(title.lower()).replace(' ','+')
            artist_search = clean_title(artist.lower()).replace(' ','+')
            start_url = '%sresults?search=%s+%s'    %(self.base_link,artist_search,song_search)
            html = requests.get(start_url, headers=headers, timeout=20).content
            match = re.compile('<h4 class="card-title">(.+?)</h4>.+?<button type="submit".+?value="MP3@(.+?)"',re.DOTALL).findall(html)
            for m, link in match:
                match4 = m.replace('\n','').replace('\t','').replace('  ',' ').replace('   ',' ').replace('    ',' ').replace('     ',' ')
                match5 = re.sub('&#(\d+);', '', match4)
                match5 = re.sub('(&#[0-9]+)([^;^0-9]+)', '\\1;\\2', match5)
                match5 = match5.replace('&quot;', '\"').replace('&amp;', '&')
                match5 = re.sub('\\\|/|\(|\)|\[|\]|\{|\}|-|:|;|\*|\?|"|\'|<|>|\_|\.|\?', ' ', match5)
                match5 = ' '.join(match5.split())
                match2 = m.replace('\n','').replace('\t','').replace(' ','')
                if clean_title(title).lower() in clean_title(match2).lower():
                    if clean_title(artist).lower() in clean_title(match2).lower():
                        self.sources.append({'source':self.name, 'quality':'SD', 'scraper':match5, 'url':link, 'direct': True})
            end_time = time.time()
            total_time = end_time - self.start_time
            print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"             

            return self.sources    
        except Exception, argument:
            return self.sources
