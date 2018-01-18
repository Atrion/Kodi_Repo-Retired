import re,requests,xbmc,time,urlresolver,xbmcaddon
from ..scraper import Scraper
from ..common import clean_title,clean_search,send_log,error_log
User_Agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
requests.packages.urllib3.disable_warnings()
dev_log = xbmcaddon.Addon('script.module.nanscrapers').getSetting("dev_log")
## multi logs
class Hddizi(Scraper):
    name = "HDdizi"
    domains = ['hddizifilmbox.com/']
    sources = []

    def __init__(self):
        self.base_link = 'https://www.hddizifilmbox.net/'
        if dev_log=='true':
            self.start_time = time.time()

    def scrape_episode(self, title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            count = 0
            new_no = int(episode)+1
            search_id = clean_search(title.lower())
            start_url = self.base_link+search_id.replace(' ','-')+'-'+season+'-sezon-izle/'+str(new_no) +'/'

            #print '1############'+start_url
            headers = {'User-Agent': User_Agent,'Referer':self.base_link}
            html = requests.get(start_url,headers=headers,timeout=10).content
            #print html
            match = re.compile('<[iI][fF][rR][aA][mM][eE].+?[sS][rR][cC]="(.+?)"').findall(html)
            for url in match:
                if not 'facebook' in url:
                    #print 'xxxxxxxxxx'+url
                    self.get_source(url)
                    
            alt_url = start_url.replace('-sezon-izle/','-sezon-seyret/')
            #print '2############'+alt_url
            html2 = requests.get(alt_url,headers=headers,timeout=10).content 
            match2 = re.compile('<[iI][fF][rR][aA][mM][eE].+?[sS][rR][cC]="(.+?)"').findall(html2)
            for url in match2:
                if not 'facebook' in url:
                    #print 'xxxxxxxxxx'+url
                    self.get_source(url)              
            return self.sources
        except Exception, argument:        
            if dev_log == 'true':
                error_log(self.name,'Check Search')
            return self.sources

    def get_source(self,url):
        count = 0
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
                count +=1
                self.sources.append({'source': 'Openload', 'quality': res, 'scraper': self.name, 'url': url,'direct': False})
            elif 'goo.gl' in url:
                headers = {'User-Agent': User_Agent}
                r = requests.get(url,headers=headers,allow_redirects=False)
                new_url = r.headers['location']
                count +=1              
                self.sources.append({'source': 'HQQ', 'quality': '720P', 'scraper': self.name, 'url': new_url,'direct': False})
            elif 'dailymotion' in url:
                count +=1
                self.sources.append({'source': 'Dailymotion', 'quality': '720P', 'scraper': self.name, 'url': url,'direct': False})
            elif 'streamango.com' in url:
                holder = requests.get(url).content
                qual = re.compile('type:"video/mp4".+?height:(.+?),',re.DOTALL).findall(holder)[0]
                count +=1
                self.sources.append({'source': 'Streamango.com', 'quality': qual, 'scraper': self.name, 'url': url,'direct': False})

            else:
                if urlresolver.HostedMediaFile(url).valid_url():
                    host = url.split('//')[1].replace('www.','')
                    host = host.split('/')[0].split('.')[0].title()
                    count +=1
                    self.sources.append({'source': host, 'quality': 'SD', 'scraper': self.name, 'url': url,'direct': False})


        except:pass
        if dev_log=='true':
            end_time = time.time() - self.start_time
            send_log(self.name,end_time,count)


