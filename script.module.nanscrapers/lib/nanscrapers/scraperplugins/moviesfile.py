import requests
import base64
import re
import xbmc
from ..scraper import Scraper
from nanscrapers import jsunpack
from ..common import clean_title,clean_search,filter_host

s = requests.session()
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
                                           
class moviesfile(Scraper):
    domains = ['http://moviesfilelinks.com']
    name = "MoviesFileLinks"
    sources = []

    def __init__(self):
        self.base_link = 'http://moviesfilelinks.com'
                     

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = self.base_link + '/?s=' + search_id.replace(' ','+')
            #print 'GW> '+start_url
            headers={'User-Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content

            match = re.compile('<h2 class="entry-title"><a href="(.+?)">(.+?)</a></h2>',re.DOTALL).findall(html)
            for url,name in match:
                if clean_title(name).lower() == clean_title(title).lower():
                    if year in name:
                        
                        self.get_source(url)
            return self.sources
        except:
            pass
            return[]

    def get_source(self,url):
        try:
            #print 'CHECK Passed '+url
            headers={'User-Agent':User_Agent}
            OPEN = requests.get(url,headers=headers,timeout=5).content
            Regex = re.compile('iframe.+?src="(.+?)"',re.DOTALL).findall(OPEN)
            for link in Regex:
                #print link
                if 'streamdor' in link:

                    link = 'https:'+link
                    headers = {'User_Agent':User_Agent}
                    get_vid=requests.get(link,headers=headers,timeout=5).content
                    #print get_vid
                    data = re.findall('JuicyCodes([^<>]*)<', str(get_vid), re.I|re.DOTALL)[0]
                    data = data.replace('.Run(','').replace('"+"','').decode('base64')
                    #print 'mydata : ' +data
                    js_data = jsunpack.unpack(data)
                    #print 'jsdata '+js_data
                    match = re.findall(r'"eName":"([^"]+)".*?"fileEmbed":"([^"]+)"', str(js_data), re.I|re.DOTALL)
                    for res,final_url in match:
                        if '1080' in res:
                            qual='1080p'
                        elif '720' in res:
                            qual = '720p'
                        else: qual = 'DVD'
                        self.sources.append({'source': 'Streamango','quality': qual,'scraper': self.name,'url': final_url,'direct': False})
                        
                elif 'openload' in link:
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
                    host = link.split('//')[1].replace('www.','')
                    host = host.split('/')[0].split('.')[0].lower()
                    if not filter_host(host):
                            continue
                    self.sources.append({'source': host, 'quality': qual, 'scraper': self.name, 'url': link,'direct': False})           
        except:
            pass

