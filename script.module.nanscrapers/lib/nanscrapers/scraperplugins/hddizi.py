import re
import requests
from ..scraper import Scraper
import xbmc,time
import urlresolver
from ..common import clean_title,clean_search
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
requests.packages.urllib3.disable_warnings()
from nanscrapers.modules import cfscrape 

class Hddizi(Scraper):
    name = "HDdizi"
    domains = ['hddizifilmbox.com/']
    sources = []

    def __init__(self):
        self.base_link = 'https://www.hddizifilmbox.net/'
        self.scraper = cfscrape.create_scraper()
        self.start_time = time.time()

    def scrape_episode(self, title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            new_no = int(episode)+1
            search_id = clean_search(title.lower())
            start_url = self.base_link+search_id.replace(' ','-')+'-'+season+'-sezon-izle/'+str(new_no)
            #start2_url = self.base_link+title.replace(' ','-')+'-'+season+'-sezon-izle/'+str(new_no)
            #print '############'+start_url
            headers = {'User-Agent': User_Agent,'Referer':self.base_link}
            html = self.scraper.get(start_url,headers=headers,timeout=5).content
            #print html
            match = re.compile('<[iI][fF][rR][aA][mM][eE].+?[sS][rR][cC]="(.+?)"').findall(html)
            for url in match:
                if not 'facebook' in url:
                    #print 'xxxxxxxxxx'+url
                    self.get_source(url)                   
            html2 = self.scraper.get(start_url.replace('-sezon-izle/','-sezon-seyret/'),headers=headers,timeout=5).content 
            match2 = re.compile('<[iI][fF][rR][aA][mM][eE].+?[sS][rR][cC]="(.+?)"').findall(html2)
            for url in match2:
                if not 'facebook' in url:
                   #print 'xxxxxxxxxx'+url
                    self.get_source(url)              
            return self.sources
        except:
            pass
            return []

    def get_source(self,url):
        try:
            if not 'http' in url:
                url = 'http:'+url
            if 'openload' in url:
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
            elif 'goo.gl' in url:
                headers = {'User-Agent': User_Agent}
                r = requests.get(url,headers=headers,allow_redirects=False)
                new_url = r.headers['location']
                #print ':::::::::::::::'+new_url                
                self.sources.append({'source': 'HQQ', 'quality': '720P', 'scraper': self.name, 'url': new_url,'direct': False})
            elif 'dailymotion' in url:
                self.sources.append({'source': 'Dailymotion', 'quality': '720P', 'scraper': self.name, 'url': url,'direct': False})
            elif 'streamango.com' in url:
                holder = requests.get(url).content
                qual = re.compile('type:"video/mp4".+?height:(.+?),',re.DOTALL).findall(holder)[0]
                self.sources.append({'source': 'Streamango.com', 'quality': qual, 'scraper': self.name, 'url': url,'direct': False})

            else:
                if urlresolver.HostedMediaFile(url).valid_url():
                    host = url.split('//')[1].replace('www.','')
                    host = host.split('/')[0].split('.')[0].title()
                    self.sources.append({'source': host, 'quality': 'SD', 'scraper': self.name, 'url': url,'direct': False})
            end_time = time.time()
            total_time = end_time - self.start_time
            print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time" 

        except:pass



