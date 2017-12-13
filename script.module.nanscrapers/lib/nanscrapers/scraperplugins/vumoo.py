import re
import requests
import difflib
import xbmc
import urlparse
from ..scraper import Scraper
from ..common import clean_title, random_agent, clean_search

class vumoo(Scraper):
    domains = ['vumoo.li']
    name = "Vumoo"
    sources = []
    name_list = []

    def __init__(self):
        self.base_link = 'http://vumoo.li'
        self.goog = 'https://www.google.co.uk'

    def scrape_episode(self, title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            #scrape = clean_search(title.lower())

            start_url = '%s/videos/category/trending-television' %(self.base_link)
            print 'start ##'+start_url
            headers = {'User-Agent':random_agent()}

            html = requests.get(start_url,headers=headers).content

            results = re.compile('class="movie_item".+?href="(.+?)".+?alt="(.+?)"',re.DOTALL).findall(html)
            for url,media_title in results:

                if clean_search(title.lower()) in clean_search(media_title.lower()):
                  
                
                
                    #url = url.replace('/videos/play','/tv/play')
                    url = self.base_link +url
                    
                    print 'showurl>> ' +url
                    self.tv_source(url,season,episode)

            return self.sources
        except Exception as e:
            print("e:" + repr(e))
            return self.sources

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            scrape = clean_search(title.lower()).replace(' ','+')

            start_url = '%s/search?q=vumoo.li+%s+%s' %(self.goog,scrape,year)
            print 'start >>'+start_url
            headers = {'User-Agent':random_agent()}

            html = requests.get(start_url,headers=headers).content
            
            results = re.compile('href="(.+?)"',re.DOTALL).findall(html)
            for url in results:
                #print 'found results? > '+url
                if self.base_link in url:
                    url = url.replace('/tv/','/videos/')
                    if scrape.replace('+','-') in url:
                        #print 'send result > '+url
                        self.get_source(url)
            return self.sources
        except Exception as e:
            print("e:" + repr(e))
            return self.sources

    def tv_source(self,url, season, episode):
        try:
            #print 'GWCHECK url= %s season= %s episode= %s' %(url,season,episode)
            html = requests.get(url).content
            #print 'page>>>>>>>>>>>>>>>>'+html
            info = re.findall('<span class="season-info">(.+?)</span>(.+?)</div> </div>',html)
            for i,rest in info:
                se = re.findall('Season (.+?),',str(i))
                ep = re.findall('Episode (.+?)>',str(i)+'>')
                for sea in se:
                    seas = sea
                for epi in ep:
                    epis = epi
                if season == seas:
                    if episode == epis:
                        url = re.findall('data-click="(.+?)"',str(rest))
                        for fin_link in url:
                            if 'http' in fin_link:
                                if 'openload' in fin_link:
                                    try:
                                        chk = requests.get(fin_link).content
                                        rez = re.compile('"description" content="(.+?)"',re.DOTALL).findall(chk)[0]
                                        if '1080' in rez:
                                            res='1080p'
                                        elif '720' in rez:
                                            res='720p'
                                        else:
                                            res ='DVD'
                                    except: res = 'DVD'
                                    self.sources.append({'source': 'Openload', 'quality': res, 'scraper': self.name, 'url': fin_link,'direct': False})
                            elif 'api' in fin_link:
                                if '=1080' in fin_link:
                                    res='1080p'
                                elif '=720' in fin_link:
                                    res='720p'
                                else: res='SD'
                                fin_link = self.base_link+fin_link
                                self.sources.append({'source': 'GoogleLink', 'quality': res, 'scraper': self.name, 'url': fin_link,'direct': True})

           
        except:
            pass

    def get_source(self,url):
        try:
            print 'sent over> '+url
            #headers = {'User-Agent':random_agent(),'Referer':self.base_link}

            OPEN = requests.get(url).content
            #print 'page'+OPEN
            Regex = re.compile("var p_link_id='(.+?)'.+?&p=(.+?)&imdb=(.+?)\"",re.DOTALL).findall(OPEN)
            for var,p,imdb in Regex:
                page = 'http://vumoo.li/api/getContents?id='+var+'&p='+p+'imdb='+imdb   #correct to here
                #print 'gw#page'+page
                links = requests.get(page).content
                regex2 = re.compile('"src":"(.+?)","label":"(.+?)"',re.DOTALL).findall(links)
                for url2,name2 in regex2:
                    url2=self.base_link+url2.replace('\\','')
                    self.sources.append({'source': 'GoogleLink', 'quality': name2, 'scraper': self.name, 'url': url2,'direct': True})

            OLOAD = re.compile("var openloadLink = '(.+?)'",re.DOTALL).findall(OPEN)
            for url in OLOAD:
                try:
                    chk = requests.get(url).content
                    rez = re.compile('"description" content="(.+?)"',re.DOTALL).findall(chk)[0]
                    if '1080' in rez:
                        res='1080p'
                    elif '720' in rez:
                        res='720p'
                    else:
                        res ='DVD'
                except: res = 'DVD'
                self.sources.append({'source': 'Openload', 'quality': res, 'scraper': self.name, 'url': url,'direct': False})

           
        except:
            pass

#Vumoo().scrape_movie('moana','2016','')
#Vumoo().scrape_episode('the blacklist', '', '', '2', '2', '', '')

