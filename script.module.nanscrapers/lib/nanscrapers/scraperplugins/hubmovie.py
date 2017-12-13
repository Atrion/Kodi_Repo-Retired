import re
import requests
import xbmc
import urllib
from ..scraper import Scraper
from ..common import clean_title,clean_search
session = requests.Session()

User_Agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H143 Safari/600.1.4'


class hubmovie(Scraper):
    domains = ['http://hubmovie.cc']
    name = "Hubmovie"
    sources = []

    def __init__(self):
        self.base_link = 'http://hubmovie.cc'
        self.sources = []

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/pages/search/%s' %(self.base_link,search_id.replace(' ','%20'))
            #print 'SEARCH url > '+start_url
            headers = {'accept':'*/*','accept-encoding':'gzip, deflate, br','accept-language':'en-US,en;q=0.8','content-type':'text/html; charset=utf-8',
                       'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0',
                       'origin':self.base_link,'referer':self.base_link,'x-requested-with':'XMLHttpRequest'}
            response = session.get(self.base_link,headers=headers,timeout=5)
            html = requests.get(start_url,headers=headers,timeout=5).content
            #print html
            page = html.split('<div id="movies_cont">')[1]
            Regex = re.compile('href="(.+?)".+?<h1>(.+?)</h1>.+?class="poster_tag">(.+?)</li>',re.DOTALL).findall(page)
            for item_url,name,date in Regex:
                #print '%s %s %s' %(item_url,name,date)
                if clean_title(title).lower() == clean_title(name).lower():
                    if year in date:
                        movie_link = item_url.replace('.',self.base_link)
                        #print 'CHECK here '+movie_link
                        self.get_source(movie_link)
                
            return self.sources
        except Exception, argument:
            return self.sources

    def scrape_episode(self,title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/pages/search/%s' %(self.base_link,search_id.replace(' ','%20'))
            #print 'SEARCH url > '+start_url
            headers = {'accept':'*/*','accept-encoding':'gzip, deflate, br','accept-language':'en-US,en;q=0.8','content-type':'text/html; charset=utf-8',
                       'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0',
                       'origin':self.base_link,'referer':self.base_link,'x-requested-with':'XMLHttpRequest'}
            response = session.get(self.base_link,headers=headers,timeout=5)
            html = requests.get(start_url,headers=headers,timeout=5).content
            page = html.split('<div id="movies_cont">')[1]
            Regex = re.compile('href="(.+?)".+?<h1>(.+?)</h1>',re.DOTALL).findall(page)
            for item_url,name in Regex:
                if clean_title(title).lower() == clean_title(name).lower():
                    movie_link = item_url.replace('.',self.base_link)
                    movie_link = movie_link + '/season-%s-episode-%s' %(season,episode)
                    self.get_source(movie_link)
                
            return self.sources
        except Exception, argument:
            return self.sources

    def get_source(self,movie_link):
        try:
            #print ':::::::::::::::::::::::'+movie_link
            headers = {'accept':'*/*','accept-encoding':'gzip, deflate, br','accept-language':'en-US,en;q=0.8','content-type':'text/html; charset=utf-8',
                       'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0',
                       'origin':self.base_link,'referer':self.base_link,'x-requested-with':'XMLHttpRequest'}
            response = session.get(self.base_link,headers=headers,timeout=5)
            html = requests.get(movie_link,headers=headers,timeout=5).content
            #print 'new'+html
            sources = re.compile('<div class="link_go".+?href="(.+?)"',re.DOTALL).findall(html)
            for link in sources:
                #print link
                if 'openload' in link:
                    headers = {'User_Agent':User_Agent}
                    get_res=requests.get(link,headers=headers,timeout=5).content
                    rez = re.compile('description" content="(.+?)"',re.DOTALL).findall(get_res)[0]
                    if '1080p' in rez:
                        qual = '1080p'
                    elif '720p' in rez:
                        qual='720p'
                    else:
                        qual='DVD'
                else: qual = 'DVD'
                host = link.split('//')[1].replace('www.','')
                host = host.split('/')[0].split('.')[0].title()
                self.sources.append({'source': host,'quality': qual,'scraper': self.name,'url': link,'direct': False})
        except:
            pass
