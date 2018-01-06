import requests
import re
import xbmc,time
from ..scraper import Scraper
from ..common import clean_title,clean_search

            
requests.packages.urllib3.disable_warnings()

s = requests.session()
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
                                           
class filmapik(Scraper):
    domains = ['https://www.filmapik.tv']
    name = "Filmapik"
    sources = []

    def __init__(self):
        self.base_link = 'https://www.filmapik.tv'
        self.start_time = time.time()

                        

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s' %(self.base_link,search_id.replace(' ','+'))
            #print 'start>>>>  '+start_url
            headers={'User-Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content

            match = re.compile('class="item".+?href="(.+?)".+?<h2>(.+?)</h2>',re.DOTALL).findall(html)
            for item_url, name in match:
                #print 'clean name >  '+clean_title(name).lower()
                if clean_title(search_id).lower() == clean_title(name).lower():
                    if year in name:
                        item_url = item_url + '/play'
                        self.get_source(item_url)
            return self.sources
        except:
            pass
            return[]

    def scrape_episode(self,title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s' %(self.base_link,search_id.replace(' ','+'))

            headers={'User-Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content

            match = re.compile('class="item".+?href="(.+?)".+?<h2>(.+?)</h2>',re.DOTALL).findall(html)
            for item_url, name in match:
                if clean_title(search_id).lower() == clean_title(name).lower():
                        item_url = item_url.replace('/tvshows/','/episodes/') + '-%sx%s' %(season,episode)
                        self.get_source(item_url)
            return self.sources 
        except:
            pass
            return[]
            
    def get_source(self,item_url):
        try:
            #print 'cfwd > '+item_url
            headers={'User-Agent':User_Agent}
            OPEN = requests.get(item_url,headers=headers,timeout=5).content
            sources = re.compile("Onclick=\"loadPage.+?'(.+?)'",re.DOTALL).findall(OPEN)
            for embFile in sources:
                #print embFile
                if 'dbmovies' in embFile:
                    headers={'User-Agent':User_Agent}
                    getlinks = requests.get(embFile,headers=headers,timeout=5).content
                    if 'sources:' in getlinks:
                        links = re.compile('"label":"(.+?)".+?"file":"(.+?)"',re.DOTALL).findall(getlinks)
                        for label,link in links:
                            self.sources.append({'source': 'DirectLink', 'quality': label, 'scraper': self.name, 'url': link,'direct': True})
                    else:pass
                else:            
                    if 'streamango' in embFile:
                        holder = requests.get(embFile).content
                        qual = re.compile('type:"video/mp4".+?height:(.+?),',re.DOTALL).findall(holder)[0]
                        self.sources.append({'source': 'Streamango', 'quality': qual, 'scraper': self.name, 'url': embFile,'direct': False})
                    elif 'drive.google' in embFile:
                        self.sources.append({'source': 'GoogleLink', 'quality': '720p', 'scraper': self.name, 'url': embFile,'direct': False}) 
                    else:
                        host = embFile.split('//')[1].replace('www.','')
                        host = host.split('/')[0].split('.')[0].title()
                        self.sources.append({'source': host, 'quality': 'DVD', 'scraper': self.name, 'url': embFile,'direct': False})
            end_time = time.time()
            total_time = end_time - self.start_time
            print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"                       
        except:
            pass

