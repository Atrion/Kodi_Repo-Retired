import requests
import re
import xbmc,time
from ..common import clean_title, clean_search,filter_host
from ..scraper import Scraper
            

s = requests.session()
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
                                           
class wmz(Scraper):
    domains = ['http://www.watchmovieszone.com']
    name = "WatchMoviesZone"
    sources = []

    def __init__(self):
        self.base_link = 'http://www.watchmovieszone.com'
        self.start_time = time.time()

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/Movie/searchMovieName/?movie=%s' %(self.base_link,search_id)

            headers={'User-Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content

            match = re.compile('"ID":"(.+?)","movieName":"(.+?)"',re.DOTALL).findall(html)
            for ID,item_name in match:

                if clean_title(title).lower() in clean_title(item_name).lower():
                    if year in item_name:
                        item_name = item_name.replace(' ','_')
                        url = '%s/Movie/Index/%s/%s' %(self.base_link,ID,item_name)
                        self.get_source(url,ID)
            
            return self.sources
        except:
            pass
            return[]

    def get_source(self,url,ID):
        try:
            # url not needed
            new_url = '%s/Movie/getLinks/?movID=%s' %(self.base_link,ID) 
            headers={'User-Agent':User_Agent}
            OPEN = requests.get(new_url,headers=headers,timeout=5).content
            Regex = re.compile('"picLink":"(.+?)"',re.DOTALL).findall(OPEN)
            for link in Regex:
                host = link.split('//')[1].replace('www.','')
                host = host.split('/')[0].lower()
                if 'streamango.com' in link:
                    holder = requests.get(link).content
                    vid = re.compile('type:"video/mp4".+?height:(.+?),',re.DOTALL).findall(holder)
                    for qual in vid:
                        end_time = time.time()
                        total_time = end_time - self.start_time
                        print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"
                        self.sources.append({'source': host, 'quality': qual, 'scraper': self.name, 'url': link,'direct': False})            
                elif 'openload' in link:
                    try:
                        chk = requests.get(url).content
                        rez = re.compile('"description" content="(.+?)"',re.DOTALL).findall(chk)[0]
                        if '1080' in rez:
                            res='1080p'
                        elif '720' in rez:
                            res='720p'
                        elif '1080' in link:
                            res = '1080p'
                        elif '720' in link:
                            res = '720p'  
                    except: res = 'DVD'
                    end_time = time.time()
                    total_time = end_time - self.start_time
                    print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"
                    self.sources.append({'source': 'Openload', 'quality': res, 'scraper': self.name, 'url': link,'direct': False})              
                else:
                    if not filter_host(host):
                        continue
                    host = host.split('.')[0].title()
                    end_time = time.time()
                    total_time = end_time - self.start_time
                    print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"
                    self.sources.append({'source': host, 'quality': 'DVD', 'scraper': self.name, 'url': link,'direct': False})           
        except:
            pass
