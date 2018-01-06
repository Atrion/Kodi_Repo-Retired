import base64
import re,time
import urlresolver
import requests
from ..common import clean_title,clean_search,random_agent,filter_host
from ..scraper import Scraper
import xbmcaddon



class Primewire(Scraper):
    domains = ['primewire.ag']
    name = "Primewire"
    sources = []

    def __init__(self):
        self.grabaproxy = 'https://proxyportal.net/primewire-proxy'
        self.sources = []
        self.start_time = time.time()

    def scrape_movie(self, title, year, imdb, debrid=False):  
        try:
            headers={'User-Agent':random_agent()}
            get_base = requests.get(self.grabaproxy,headers=headers,timeout=5).content
            url_get = re.compile('class="panel-body".+?href="(.+?)"',re.DOTALL).findall(get_base)[0]
            # headers = {'User-Agent': random_agent()}
            # r = requests.get(url_get,headers=headers,allow_redirects=False)
            # proxy_base_link = r.headers['location'][:-1]
            # print 'BASE _ ' + proxy_base_link
            proxy_base_link = url_get
            
            mov_id = clean_search(title.lower().replace(' ','+'))
            search_page_url = proxy_base_link + '/index.php?search'

            headers={'User-Agent':random_agent()}
            
            search_page_content = requests.get(search_page_url,headers=headers,timeout=5).content
            
            search_key = re.compile('input type="hidden" name="key" value="([0-9a-f]*)"',re.DOTALL).findall(search_page_content)[0]
            
            start_url = "%s/index.php?search_keywords=%s&key=%s&search_section=1" % (proxy_base_link, mov_id,search_key)
            #print 'Search primeURL>  '+start_url
            headers = {'User_Agent':random_agent()}
            OPEN = requests.get(start_url,headers=headers,timeout=5).content
            content = re.compile('class="index_item index_item.+?href="(.+?)".+?title="(.+?)"',re.DOTALL).findall(OPEN)
            for show_url,item_title in content:
                item_title = item_title.replace('Watch','')
                if clean_title(title).lower() == clean_title(item_title).lower():
                    if year in item_title:  
                        show_url = proxy_base_link + show_url
                        #print 'prime movie pass>> ' + show_url
                        self.get_source(show_url)                        
            return self.sources
        except Exception, argument:
            return self.sources 
            
    def scrape_episode(self, title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            headers={'User-Agent':random_agent()}
            get_base = requests.get(self.grabaproxy,headers=headers,timeout=5).content
            url_get = re.compile('class="panel-body".+?href="(.+?)"',re.DOTALL).findall(get_base)[0]
            # headers = {'User-Agent': random_agent()}
            # r = requests.get(url_get,headers=headers,allow_redirects=False)
            # proxy_base_link = r.headers['location'][:-1]
            # print 'BASE _ ' + proxy_base_link
            proxy_base_link = url_get
            
            show_id = clean_search(title.lower().replace(' ','+'))
            search_page_url = proxy_base_link + '/index.php?search'

            headers={'User-Agent':random_agent()}
            
            search_page_content = requests.get(search_page_url,headers=headers,timeout=5).content
            
            search_key = re.compile('input type="hidden" name="key" value="([0-9a-f]*)"',re.DOTALL).findall(search_page_content)[0]
            
            start_url = "%s/index.php?search_keywords=%s&key=%s&search_section=2" % (proxy_base_link, show_id,search_key)
            #print 'Search primeURL>  '+start_url
            headers = {'User_Agent':random_agent()}
            OPEN = requests.get(start_url,headers=headers,timeout=5).content
            content = re.compile('class="index_item index_item.+?href="(.+?)".+?title="(.+?)".+?alt="(.+?)"',re.DOTALL).findall(OPEN)
            for show_url,match_year,item_title in content:
                item_title = item_title.replace('Watch','')
                if clean_title(title).lower() == clean_title(item_title).lower():
                    #if year in match_year:   ##year not passed in bob

                        show_url = re.sub('watch-', 'tv-', show_url).replace('-online-free','')

                        show_url = proxy_base_link + show_url + '/season-' + season + '-episode-' + episode

                        self.get_source(show_url)                        
            return self.sources
        except Exception, argument:
            return self.sources  






    def get_source(self,show_url):
        try: 
            #print 'xxx PassedPrimewire URL >'+show_url       
            headers = {'User_Agent':random_agent()}
            content = requests.get(show_url,headers=headers,timeout=3).content 

            links = re.compile("quality_(.+?)>.+?url=(.+?)&",re.DOTALL).findall(content)
            for quality,host_url in links:
                
                if quality == 'UNKNOWN':
                    continue
                final_url = base64.b64decode(host_url)

                host = final_url.split('//')[1].replace('www.','')
                host = host.split('/')[0].lower()
                if not filter_host(host):
                    continue
                host = host.split('.')[0].title()
                end_time = time.time()
                total_time = end_time - self.start_time
                print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"
                self.sources.append({'source': host,'quality': 'SD','scraper': self.name,'url': final_url,'direct': False})

        except:pass


