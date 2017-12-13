import re
import requests
import xbmc
import urllib
from ..scraper import Scraper
from ..common import clean_title,clean_search

User_Agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 8_4 like Mac OS X) AppleWebKit/600.1.4 (KHTML, like Gecko) Version/8.0 Mobile/12H143 Safari/600.1.4'


class moviesco(Scraper):
    domains = ['moviesco.cc']
    name = "moviesco"
    sources = []

    def __init__(self):
        self.base_link = 'http://moviesco.cc'
        self.sources = []

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/search?q=%s' %(self.base_link,search_id.replace(' ','+'))
            headers = {'User_Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content
            Regex = re.compile('<h4 class="showRow showRowName showRowText"><a href="(.+?)" >(.+?)</a></h4>',re.DOTALL).findall(html)
            for item_url,name in Regex:
                if clean_title(title).lower() == clean_title(name).lower():
                    movie_link = self.base_link + item_url
                    self.get_source(movie_link,year)
                
            return self.sources
        except Exception, argument:
            return self.sources

    def get_source(self,movie_link,year):
        try:
            html = requests.get(movie_link).content
            chkdate = re.compile('showValueRelease">(.+?)</div>',re.DOTALL).findall(html)
            for date in chkdate:
                if year==date:
                    links = re.compile('<div class="linkHidden linkHiddenUrl".+?>(.+?)</div>',re.DOTALL).findall(html)
                    for link in links:
                        if 'openload' in link:
                            try:
                                headers = {'User_Agent':User_Agent}
                                get_res=requests.get(link,headers=headers,timeout=5).content
                                rez = re.compile('description" content="(.+?)"',re.DOTALL).findall(get_res)[0]
                                if '1080p' in rez:
                                    qual = '1080p'
                                elif '720p' in rez:
                                    qual='720p'
                                else:
                                    qual='DVD'
                            except: qual='DVD'        
                            self.sources.append({'source': 'Openload','quality': qual,'scraper': self.name,'url': link,'direct': False})
                        elif 'streamango' in link:
                            try:
                                headers = {'User_Agent':User_Agent}
                                get_res=requests.get(link,headers=headers,timeout=5).content
                                rez = re.compile('description" content="(.+?)"',re.DOTALL).findall(get_res)[0]
                                if '1080p' in rez:
                                    qual = '1080p'
                                elif '720p' in rez:
                                    qual='720p'
                                else:
                                    qual='DVD'
                            except: qual='DVD'        
                            self.sources.append({'source': 'streamango','quality': qual,'scraper': self.name,'url': link,'direct': False})
                        else:
                            qual = 'DVD'
                            host = link.split('//')[1].replace('www.','')
                            host = host.split('/')[0].split('.')[0].title()
                            self.sources.append({'source': host,'quality': qual,'scraper': self.name,'url': link,'direct': False})
        except:
            pass

