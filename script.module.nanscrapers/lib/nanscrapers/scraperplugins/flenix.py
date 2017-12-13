import re
import requests
import xbmc
import urllib
from ..scraper import Scraper
from ..common import clean_title, random_agent, clean_search
requests.packages.urllib3.disable_warnings()

session = requests.Session()
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'

class flenix(Scraper):
    domains = ['https://flenix.net']
    name = "Flenix"
    sources = []

    def __init__(self):
        self.base_link = 'https://flenix.net/'
        self.goog = 'https://www.google.co.uk'
        self.sources = []

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
        
            scrape = clean_search(title.lower()).replace(' ','+')

            start_url = '%s/search?q=flenix.net+%s+%s' %(self.goog,scrape,year)

            headers = {'User-Agent':random_agent()}

            html = requests.get(start_url,headers=headers).content

            results = re.compile('href="(.+?)"',re.DOTALL).findall(html)
            for url in results:

                if self.base_link in url:

                    if scrape.replace('+','-') in url:

                        ID = url.split('movies/')[1].split('-')[0]
                        #print ':::::::::::::'+ID
                        headers = {'User-Agent': random_agent()}
                        page = requests.get(url,headers=headers,allow_redirects=False)
                        c = page.cookies
                        i = c.items()
                        for grab,value in i:
                            #print (grab,value)
                            if 'PHP' in grab:
                                cookie = 'PHPSESSID=%s; path=/; HttpOnly' %grab
                        
                        
                        headers = {'User-Agent': random_agent(),'cookie':cookie,'referer':url}
                        page_url= 'https://flenix.net/movies/%s/watch/'%ID
                        page = session.get(page_url,headers=headers)
                        req_url = 'https://flenix.net/?do=player_ajax&id=%s&xfn=player2' %ID
                        
                        end_url = session.get(req_url, headers=headers).content
                        link = end_url
                        self.sources.append({'source': 'DirectLink','quality': '720P','scraper': self.name,'url': link,'direct': True})
            return self.sources
        except Exception, argument:
            return self.sources


