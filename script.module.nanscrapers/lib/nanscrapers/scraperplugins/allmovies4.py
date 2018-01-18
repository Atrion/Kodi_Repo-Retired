import re,xbmcaddon,time,requests
from ..scraper import Scraper
from ..common import clean_title,clean_search,send_log,error_log
dev_log = xbmcaddon.Addon('script.module.nanscrapers').getSetting("dev_log")
User_Agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'


class allmovies4(Scraper):
    domains = ['allmovies4.me']
    name = "allmovies4"
    sources = []

    def __init__(self):
        self.base_link = 'http://allmovies4.me'
        if dev_log=='true':
            self.start_time = time.time() 

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s&post_type=amy_movie&amy_type=movie' %(self.base_link,search_id.replace(' ','+'))
            #error_log(self.name + ' Search',start_url)
            headers = {'User_Agent':User_Agent}
            html = requests.get(start_url,headers=headers,allow_redirects=False,timeout=10).content
            #print html
            Regex = re.compile('class="entry-title"><a href="(.+?)">(.+?)</a>.+?Release:(.+?)</span>',re.DOTALL).findall(html)
            for item_url,name,date in Regex:
                if clean_title(title).lower() == clean_title(name).lower():
                    if year in date:
                        movie_link = item_url
                        #error_log(self.name + ' movie_link',movie_link)
                        self.get_source(movie_link)
                
            return self.sources
        except Exception, argument:        
            if dev_log == 'true':
                error_log(self.name,'Check Search')
            return self.sources

    def get_source(self,movie_link):
        try:
            headers = {'User_Agent':User_Agent}
            html = requests.get(movie_link,headers=headers,timeout=5).content
            source = re.compile('"#player".+?load.+?"(.+?)"',re.DOTALL).findall(html)
            count = 0
            for load in source:
                if 'b.php' in load:
                    headers = {'User_Agent':User_Agent}
                    holder = requests.get(load,headers=headers,verify=False,timeout=5).content
                    link = re.compile('file: "(.+?)"').findall(holder)[0]
                    
                    count +=1
                    self.sources.append({'source': 'DirectLink','quality': '720p','scraper': self.name,'url': link,'direct': False})

                
                
                else:
                    headers = {'User_Agent':User_Agent}
                    holder = requests.get(load,headers=headers,verify=False,timeout=10).content
                    links = re.compile('<iframe src="(.+?)"').findall(holder)
                    for link in links:
                        if 'streamango' in link:                   
                            try:
                                headers = {'User_Agent':User_Agent}
                                get_res=requests.get(link,headers=headers,timeout=10).content
                                rez = re.compile('type:"video/mp4".+?height:(.+?),',re.DOTALL).findall(get_res)[0]
                                if '1080' in rez:
                                    qual = '1080p'
                                elif '720' in rez:
                                    qual='720p'
                                else:
                                    qual='DVD'
                            except: qual='DVD'
                            count +=1
                            self.sources.append({'source': 'Streamango','quality': qual,'scraper': self.name,'url': link,'direct': False})
                        else:pass

            if dev_log=='true':
                end_time = time.time() - self.start_time
                send_log(self.name,end_time,count)
        except:
            pass

