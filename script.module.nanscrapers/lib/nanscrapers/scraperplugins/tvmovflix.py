import requests
import re
import xbmc,time
from ..scraper import Scraper
from ..common import clean_title,clean_search
from nanscrapers.modules import cfscrape          

s = requests.session()
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
                                           
class tvmovflix(Scraper):
    domains = ['tvmovieflix.com']
    name = "TV MovieFlix"
    sources = []

    def __init__(self):
        self.base_link = 'http://tvmovieflix.com'
        self.scraper = cfscrape.create_scraper()
        self.start_time = time.time()
  
    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = self.base_link + '/index.php?menu=search&query=' + search_id.replace(' ','+')
            #print 'GW> '+start_url
            headers={'User-Agent':User_Agent}
            html = self.scraper.get(start_url,headers=headers,timeout=10).content
            match = re.compile('class="item".+?href="(.+?)".+?<h2>(.+?)</h2>.+?class="year">(.+?)</span>',re.DOTALL).findall(html)
            for url,name,date in match:
                #print '%s  %s  %s'  %(url,name,date)
                if clean_title(title).lower() == clean_title(name).lower():
                    if year in date:
                        #print 'moviflix CHK Movie> ' + url
                        self.get_source(url)
            
            return self.sources
        except:
            pass
            return[]

    def scrape_episode(self, title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            search_id = clean_search(title.lower().replace(' ','-'))
            episode_url = '%s/show/%s/season/%s/episode/%s' % (self.base_link,search_id,season,episode)
            
            #print 'moviflix CHECK TV URL ' + episode_url
            url = episode_url
            self.get_source(url)

            return self.sources
        except Exception, argument:
            return self.sources  
            
    def get_source(self,url):
        try:
            headers={'User-Agent':User_Agent}
            OPEN = self.scraper.get(url,headers=headers,timeout=10).content
            Regex = re.compile('href="(http://tvmovieflix.com/m/.+?)" rel="nofollow"',re.DOTALL).findall(OPEN)
            for link in Regex:
                holder = self.scraper.get(link).content  
                vid = re.compile('<[iI][fF][rR][aA][mM][eE].+?[sS][rR][cC]="(.+?)"',re.DOTALL).findall(holder)
                for end_url in vid:
                    if 'realtalksociety' in end_url:
                        new = self.scraper.get(end_url).content 
                        get = re.compile('source src="(.+?)"',re.DOTALL).findall(new)
                        for play in get:
                            self.sources.append({'source': 'DirectLink', 'quality': '720p', 'scraper': self.name, 'url': play,'direct': True})
                        end_time = time.time()
                        total_time = end_time - self.start_time
                        print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"            
                    else:
                        # print 'mechech '+end_url
                        host = end_url.split('//')[1].replace('www.','')
                        host = host.split('/')[0].split('.')[0].title()
                        self.sources.append({'source': host, 'quality': 'DVD', 'scraper': self.name, 'url': end_url,'direct': False})
                        end_time = time.time()
                        total_time = end_time - self.start_time
                        print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"           
        except:
            pass

