import requests,base64
import re
import xbmc
from ..scraper import Scraper
from ..common import clean_title,clean_search
from nanscrapers import jsunpack
            
requests.packages.urllib3.disable_warnings()

s = requests.session()
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
                                           
class moviefullhd(Scraper):
    domains = ['https://moviefull-hd.com']
    name = "MovieFullHD"
    sources = []

    def __init__(self):
        self.base_link = 'https://moviefull-hd.com'

                        

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s+%s' %(self.base_link,search_id.replace(' ','+'),year)

            headers={'User-Agent':User_Agent}
            html = requests.get(start_url,headers=headers,timeout=5).content

            match = re.compile("<a class='suf-mosaic-post-title' href='(.+?)'>(.+?)</a>",re.DOTALL).findall(html)
            for item_url, name in match:
                if clean_title(search_id).lower() in clean_title(name).lower():
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

            match = re.compile("<a class='suf-mosaic-post-title' href='(.+?)'>(.+?)</a>",re.DOTALL).findall(html)
            for item_url, name in match:
                name = name.replace('Second','2').replace('Third','3').replace('Fourth','4').replace('Fifth','5').replace('Sixth','6').replace('Seventh','7').replace('Eighth','8')
                if clean_title(search_id).lower() in clean_title(name).lower():
                    if '-season' in item_url:
                        if season in name:
                            if episode == '1':
                                item_url=item_url
                            else:
                                item_url = item_url + '/%s' %(episode)
                            print '@@' +item_url
                            self.get_source(item_url)
            return self.sources
                
            return self.sources
        except Exception, argument:
            return self.sources
            
    def get_source(self,item_url):
        try:
            headers={'User-Agent':User_Agent}
            OPEN = requests.get(item_url,headers=headers,timeout=5).content
            print OPEN
            embFile = re.compile('<iframe.+?src="(.+?)"',re.DOTALL).findall(OPEN)[0]
            print 'embfile'+embFile
            headers={'User-Agent':User_Agent,'Referer':item_url}
            
            getjuicy = requests.get(embFile,headers=headers,timeout=5).content
            print 'embfile'+getjuicy
            data = re.findall('type="text/javascript">([^<>]*)<', str(getjuicy), re.I|re.DOTALL)[0]
            data = data.replace('JuicyCodes.Run(','').replace('"+"','').decode('base64')
            js_data = jsunpack.unpack(data)
            match = re.findall(r'"file":"([^"]+)".*?"label":"([^"]+)"', str(js_data), re.I|re.DOTALL)
            for link,label in match:
                label = label.lower()
                print 'endlink %s - %s'%(link,label)
                if '.srt' not in link:
                    link = link + '|User-Agent=Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36&Referer='+embFile
                    self.sources.append({'source': 'DirectLink', 'quality': label, 'scraper': self.name, 'url': link,'direct': True})           
        except:
            pass

