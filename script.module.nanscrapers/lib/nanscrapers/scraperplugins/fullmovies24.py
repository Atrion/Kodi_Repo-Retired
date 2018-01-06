import re,time
import requests
import xbmc
import urllib
from ..scraper import Scraper
from ..common import clean_title,clean_search
from ..modules import cfscrape
requests.packages.urllib3.disable_warnings()

s = requests.session()
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'

class fullmovies24(Scraper):
    domains = ['http://fullmovies24.net']
    name = "Fullmovies24"
    sources = []

    def __init__(self):
        self.base_link = 'http://fullmovies24.net'
        self.sources = []
        self.scraper = cfscrape.create_scraper()
        self.start_time = time.time()

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = clean_search(title.lower())
            movie_url = '%s/?s=%s' %(self.base_link,search_id.replace(' ','+'))
            #print movie_url
            
            headers = {'User_Agent':User_Agent}
            link = self.scraper.get(movie_url,headers=headers).content
            

            links = link.split('class="title"')[1]
            
            m_url = re.compile('href="(.+?)"',re.DOTALL).findall(links)[0]
            m_title = re.compile('title="(.+?)"',re.DOTALL).findall(links)[0]
            if clean_title(title).lower() in clean_title(m_title).lower():
                if year in m_title:
                    headers={'User-Agent':User_Agent}
        
                    content = self.scraper.get(m_url,headers=headers).content
                    #print content
                    link1 = re.compile('"#player".+?(http.+?)"',re.DOTALL).findall(content)
                    for page in link1:
                        #print page
                        pg_link = self.scraper.get(page,headers=headers).content
                        link = re.compile('<iframe src="(.+?)"',re.DOTALL).findall(pg_link)[0]
                        host = link.split('//')[1].replace('www.','')
                        host = host.split('/')[0].lower()
                        try:
                            holder = requests.get(link).content
                            #print 'holder>'+holder
                            qual = re.compile('type:"video/mp4".+?height:(.+?),',re.DOTALL).findall(holder)[0]
                            if '1080' in qual:
                                res = '1080p'
                            elif '720' in qual:
                                res= '720p'
                            else: res = 'SD'
                        except:res = 'SD'
                        self.sources.append({'source': host, 'quality': res, 'scraper': self.name, 'url': link,'direct': False})
            end_time = time.time()
            total_time = end_time - self.start_time
            print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"

                 
            return self.sources
        except Exception, argument:
            return self.sources


#fullmovies24().scrape_movie('the dark tower', '2017','') 