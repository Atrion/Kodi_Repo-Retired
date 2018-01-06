import requests
import re
import xbmc
from ..scraper import Scraper
from ..common import clean_title,clean_search,random_agent

  
class MovieTV(Scraper):
    domains = ['http://movietv.ws/']
    name = "MovieTV"
    sources = []

    def __init__(self):
        self.base_link = 'http://movietv.ws/'


    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s?s=%s' %(self.base_link,search_id.replace(' ','+'))
            html = requests.get(start_url,timeout=10).content
            block = re.compile('class="page-category">(.+?)alert-bottom-content"><p',re.DOTALL).findall(html)
            match = re.compile('class="mli-quality">(.+?)</span>.+?<h2>(.+?)</h2>.+?rel="tag">(.+?)</a>.+?class="jtip-bottom">.+?href="(.+?)".+?class="btn\s*btn-block').findall(str(block))
            for qaul,name,yrs,item_url in match:
                item_url = 'http:%s' % (item_url)
                if year in yrs:
                    if clean_title(search_id).lower() == clean_title(name).lower():
                        self.get_source(item_url,qaul)
            return self.sources
        except:
            pass
            return[]

            
    def get_source(self,item_url,qaul):
        try:
            OPEN = requests.get(item_url,timeout=10).content
            block1 = re.compile('id="content-embed"(.+?)id="button-favorite">',re.DOTALL).findall(OPEN)
            Endlinks = re.compile('src="(.+?)"\s*scrolling',re.DOTALL).findall(str(block1))
            for link in Endlinks:
                link = 'http:%s' % (link)
                host = link.split('//')[1].replace('www.','')
                host = host.split('/')[0].lower()
                host = host.split('.')[0]
                #print link
                self.sources.append({'source': host, 'quality': qaul, 'scraper': self.name, 'url': link,'direct': True})
        except:
            pass