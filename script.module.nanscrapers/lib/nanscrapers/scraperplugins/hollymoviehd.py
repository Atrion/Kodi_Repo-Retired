import requests,base64
import re
import xbmc
from ..scraper import Scraper
from ..common import clean_title,clean_search

            
requests.packages.urllib3.disable_warnings()

s = requests.session()
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
                                           
class hollymoviehd(Scraper):
    domains = ['https://www.hollymoviehd.com']
    name = "HollyMovieHD"
    sources = []

    def __init__(self):
        self.base_link = 'https://www.hollymoviehd.com'

                        

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = '%s/?s=%s' %(self.base_link,search_id.replace(' ','+'))
            #print ':::::::::::::######################## '+start_url
            headers={'User-Agent':User_Agent,'referer':self.base_link}
            html = requests.get(start_url,headers=headers,timeout=5).content
            #print ':::::::::::::######################## '+html
            match = re.compile('data-movie-id=.+?href="(.+?)" .+?class="mli-info"><h2>(.+?)</h2>',re.DOTALL).findall(html)
            for item_url, name in match:
                if year in name:
                    name=name.split('(')[0]
                    if clean_title(search_id).lower() == clean_title(name).lower():
                        self.get_source(item_url)
            return self.sources
        except:
            pass
            return[]

    # def scrape_episode(self,title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        # try:
            # search_id = clean_search(title.lower())
            # start_url = '%s/?s=%s' %(self.base_link,search_id.replace(' ','+'))

            # headers={'User-Agent':User_Agent}
            # html = requests.get(start_url,headers=headers,timeout=5).content

            # match = re.compile("<a class='suf-mosaic-post-title' href='(.+?)'>(.+?)</a>",re.DOTALL).findall(html)
            # for item_url, name in match:
                # name = name.replace('Second','2').replace('Third','3').replace('Fourth','4').replace('Fifth','5').replace('Sixth','6').replace('Seventh','7').replace('Eighth','8')
                # if clean_title(search_id).lower() in clean_title(name).lower():
                    # if '-season' in item_url:
                        # if season in name:
                            # if episode == '1':
                                # item_url=item_url
                            # else:
                                # item_url = item_url + '/%s' %(episode)
                            # print '@@' +item_url
                            # self.get_source(item_url)
            # return self.sources
                
            # return self.sources
        # except Exception, argument:
            # return self.sources
            
    def get_source(self,item_url):
        try:
            print 'MOVIE '+item_url
            headers={'User-Agent':User_Agent}
            OPEN = requests.get(item_url,headers=headers,timeout=5).content
            #print OPEN
            holder = re.compile('data-lazy-src="(.+?)"',re.DOTALL).findall(OPEN)[0]
            if holder.startswith('//'):
                holder = 'https:' + holder
            #print 'embfile'+holder
            headers={'User-Agent':User_Agent}
            
            Page = requests.get(holder,headers=headers,timeout=5).content
            Endlinks = re.compile('file.+?(https://lh3.+?)"',re.DOTALL).findall(Page)
            for link in Endlinks:
                if '=m37' in link:
                    label = '1080p'
                elif '=m22' in link:
                    label = '720p'
                elif '=m59' in link:
                    label = 'DVD'
                else:
                    label = 'SD'
                #print 'HOLLYHEADendlink> %s - %s'%(link,label)
                self.sources.append({'source': 'GoogleLink', 'quality': label, 'scraper': self.name, 'url': link,'direct': True})           
        except:
            pass

