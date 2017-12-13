import re
import requests
import xbmc
import urllib,base64
from ..scraper import Scraper
from ..common import clean_title,clean_search, filter_host, get_rd_domains  

User_Agent = 'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36'


class zoocinema(Scraper):
    domains = ['http://zoocine.net/']
    name = "ZooCinema"
    sources = []

    def __init__(self):
        self.base_link = 'http://zoocine.net/'
        self.sources = []

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            name = clean_search(title.lower())
            
            search = {'do':'search', 'subaction':'search', 'story':name}
            headers = {'User_Agent':User_Agent}
            link = requests.post(self.base_link, data=search,headers=headers, timeout=3).content
            print 'xmxmx'+link
            links = link.split('-in">')[1:]
            
            for p in links:

                media_url = re.compile('href="(.+?)"').findall(p)[0]
                if self.base_link not in media_url:
                   media_url = self.base_link + media_url
                media_title = re.compile('title="(.+?)"').findall(p)[0]
                if name in clean_search(media_title).lower():
                    if year in media_title:
                        print '###########zoo#####################'+str(media_url)
            
                        self.get_source(media_url)
                
            return self.sources
        except Exception, argument:
            return self.sources

    def scrape_episode(self,title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            name = clean_search(title.lower())
            
            season_pull = '0%s' %season if len(season) <2 else season
            episode_pull = '0%s' %episode if len(episode) <2 else episode
            sep = 'S%sE%s' %(season_pull,episode_pull)

            search = {'do':'search', 'subaction':'search', 'story':'%s %s' %(name,sep)}            

            link = requests.post(self.base_link, data=search, timeout=3).content
            
            links = link.split('-in">')[1:]
            
            for p in links:

                media_url = re.compile('href="(.+?)"').findall(p)[0]
                if self.base_link not in media_url:
                   media_url = self.base_link + media_url
                media_title = re.compile('title="(.+?)"').findall(p)[0]
               
                if name in clean_search(media_title).lower():
                    if sep.lower() in media_title.lower():
                        #print '###########zoo#####################'+str(media_url)
                        self.get_source(media_url)
                
            return self.sources
        except Exception, argument:
            return self.sources

    def get_source(self,movie_url):
        try:
            #print ':::::::::::::::::::::::'+movie_url
            link = requests.get(movie_url, timeout=3).content
            qual = link.split('>Source:<')[1:]
            for p in qual:
                res = re.findall(r'class="finfo-text">([^<]+)</div>', str(link), re.I|re.DOTALL)[0]
                if '1080' in res:
                    res='1080p'                   
                elif '720' in res:
                    res='720p'
                elif  '480' in res:
                    res='DVD'
                else:
                    res='SD'
                print 'quality ######## = ' + res
            try:

                iframe = link.split('"video-responsive"')[1:]
                for p in iframe:

                    iframe_url = re.findall(r'iframe.*?src="([^"]+)"', p, re.I|re.DOTALL)[0]
                    if 'goo.gl' not in iframe_url:
                        if 'youtube' not in iframe_url:
                            host = iframe_url.split('//')[1].replace('www.','')
                            host = host.split('/')[0].lower()
                            if not filter_host(host):
                                continue
                            rd_domains = get_rd_domains()
                            if host in rd_domains:
                                self.sources.append({'source': host,'quality': res,'scraper': self.name,'url': iframe_url,'direct': False,'debridonly': True})
                            else:
                                self.sources.append({'source': host,'quality': res,'scraper': self.name,'url': iframe_url,'direct': False})

            except:pass

            try:
                    
                match2 = re.findall(r'<a href="([^"]+)"  .+?</a>', str(link), re.I|re.DOTALL)
                if not match2:
                    match2 = re.findall(r'target="_blank" href="(.+?)">Watch',str(link), re.I|re.DOTALL)
                for a in match2:
                    if '=' in a:
                        base64_url = a.split('=')[1]
                        base64_url = urllib.unquote(base64_url).decode('base64')
                        host = base64_url.split('//')[1].replace('www.','')
                        host = host.split('/')[0].lower()
                        if not filter_host(host):
                            continue
                        rd_domains = get_rd_domains()
                        
                        if host in rd_domains:
                            self.sources.append({'source': host,'quality': res,'scraper': self.name,'url': base64_url,'direct': False,'debridonly': True})
                        else:
                            self.sources.append({'source': host,'quality': res,'scraper': self.name,'url': base64_url,'direct': False})
                    else:
                        host = a.split('//')[1].replace('www.','')
                        host = host.split('/')[0].lower()
                        if not filter_host(host):
                            continue
                        rd_domains = get_rd_domains()
                        if host in rd_domains:
                            self.sources.append({'source': host,'quality': res,'scraper': self.name,'url': a,'direct': False, 'debridonly': True})
                        else:
                            self.sources.append({'source': host,'quality': res,'scraper': self.name,'url': a,'direct': False})

            except:pass
                    
        except:
            pass
