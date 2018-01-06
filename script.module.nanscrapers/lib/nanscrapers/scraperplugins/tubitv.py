import requests
import re
import xbmc
import time
from ..scraper import Scraper
from ..common import clean_title,clean_search,random_agent

  
class tubitv(Scraper):
    domains = ['tubitv.com']
    name = "TubiTv"
    sources = []

    def __init__(self):
        self.base_link = 'https://tubitv.com'
        self.start_time = time.time()                                                   


    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/search/%s' %(self.base_link,search_id.replace(' ','%20'))
            #print '::::::::::::: START URL '+start_url
            
            headers={'User-Agent':random_agent()}
            html = requests.get(start_url,headers=headers,timeout=5).content
            #print html
            match = re.compile('"@type":"Movie","name":"(.+?)","url":"(.+?)".+?"dateCreated":"(.+?)"',re.DOTALL).findall(html)
            for name ,item_url, rel in match:
                #print 'item_url>>>>>>>>>>>>>> '+item_url
                #print 'name>>>>>>>>>>>>>> '+name
                if year in rel:
                    
                    if clean_title(search_id).lower() == clean_title(name).lower():
                        #print 'Send this URL> ' + item_url
                        self.get_source(item_url)
            return self.sources
        except:
            pass
            return[]

            
    def get_source(self,item_url):
        try:
            headers={'User-Agent':random_agent()}
            OPEN = requests.get(item_url,headers=headers,timeout=5).content

            Endlinks = re.compile('"video":.+?"url":"(.+?)"',re.DOTALL).findall(OPEN)
            for link in Endlinks:
                link = 'https:'+link.replace('\u002F','/')
                if '1080' in link:
                    label = '1080p'
                elif '720' in link:
                    label = '720p'
                else:
                    label = 'HD'
                self.sources.append({'source': 'TubiTv', 'quality': label, 'scraper': self.name, 'url': link,'direct': True})
            end_time = time.time()  # stops the timer
            total_time = end_time - self.start_time   # finds the total time the scraper ran
            print (repr(total_time))+"<<<<<<<<<<<<<<<<<<<<<<<<<"+self.name+">>>>>>>>>>>>>>>>>>>>>>>>>total_time"         
        except:
            pass
#tubitv().scrape_movie('bullet boy', '2005','') 
# you will need to regex/split or rename to get host name if required from link unless available on page it self 