import requests
import re,xbmcaddon,time
from ..scraper import Scraper
from ..common import clean_title,clean_search,send_log,error_log
dev_log = xbmcaddon.Addon('script.module.nanscrapers').getSetting("dev_log")

requests.packages.urllib3.disable_warnings()
User_Agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36'
session = requests.Session()

class oneonline(Scraper):
    domains = ['https://1movies.to/']
    name = "OneOnline"
    sources = []

    def __init__(self):
        self.base_link = 'https://1movies.to'
        if dev_log=='true':
            self.start_time = time.time()
        self.sources = []

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = clean_search(title.lower())
            start_url = self.base_link+'/search_all/'+search_id.replace(' ','%20')+'/movies'
            #print '####' + start_url
            headers = {'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8','accept-encoding':'gzip','accept-language':'en-US,en;q=0.9',
                       'User-Agent':User_Agent,'origin':self.base_link,'referer':self.base_link,'x-requested-with':'XMLHttpRequest'}
            response = session.get('https://1movies.to',headers=headers)
            html = requests.get(start_url,headers=headers).content
            #print 'htmlxxx'+ html
            Regex = re.compile('title=.+?"(.+?):.+?href=.+?"(.+?)"',re.DOTALL).findall(html)
            for name,url in Regex:
                #print '%s %s' %(name,url)
                if clean_title(title).lower() == clean_title(name).lower():
                    url = url.replace('\\','')
                    movie_link = '%s%s-watch-online-free.html' %(self.base_link,url)
                    #print 'check movie>>  '+movie_link
                    self.get_source(movie_link)
                
            return self.sources
        except Exception, argument:
            return self.sources

    # def scrape_episode(self,title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        # try:
            # search_id = clean_search(title.lower())
            # start_url = self.base_link + '/search_all/'+search_id.replace(' ','%20')+'%20season%20'+season+'/series'
            # headers = {'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8','accept-encoding':'gzip','accept-language':'en-US,en;q=0.9',
                       # 'User-Agent':User_Agent,'origin':self.base_link,'referer':self.base_link,'x-requested-with':'XMLHttpRequest'}
            # response = session.get('https://1movies.to',headers=headers)
            # html = requests.get(start_url,headers=headers).content
            # print 'PAGE>>>>>>>>>>>>>>>>>'+html
            # Regex = re.compile('title=.+?"(.+?):.+?href=.+?"(.+?)"',re.DOTALL).findall(html)
            # for name,item_url in Regex:
                # print 'vvv'+name
                # print 'urluyrl'+item_url
                # if clean_title(title).lower() in clean_title(name).lower():
                        # item_url = item_url.replace('\\','')
                        # season_page = '%s%s' %(self.base_link,item_url)
                        # print 'CHECH SEASOIN '+season_page
                        # headers = {'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8','accept-encoding':'gzip','accept-language':'en-US,en;q=0.9',
                                    # 'User-Agent':User_Agent,'origin':self.base_link,'referer':self.base_link,'x-requested-with':'XMLHttpRequest'}
                        # html2 = requests.get(season_page,headers=headers).content
                        # print html2
                        # episode_block = html2.findAll('div',attrs={'id':'scroll_block_episodes'})
                        # for block in episode_block:
                            # a_block = re.findall('<a(.+?)</a>',str(block),re.DOTALL)
                            # for anchor in a_block:
                                # episode_title = re.findall('title="(.+?)"',str(anchor))[0]
                                # url_ = re.findall('href="(.+?)"',str(anchor))[0]
                                # movie_link = self.base_link+url_
                                # if 'season '+season in episode_title.lower():
                                    # if len(episode)==1:
                                        # episode = '0'+episode
                                    # if 'episode '+episode in episode_title.lower():
                                        # self.get_source(movie_link,quality)
               
            # return self.sources
        # except Exception, argument:
            # return self.sources

    def get_source(self,url):
        try:
            #print url
            headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:56.0) Gecko/20100101 Firefox/56.0',
                       'Referer':url,
                       'X-Requested-With':'XMLHttpRequest'}
            spare_nums = ['1','2','3']
            count = 0
            for num in spare_nums:
                    html = requests.get(url+'/newLink?spare_num='+num,headers=headers).content
                    if html != '[]':
                        items = re.findall('\{(.+?)\}',str(html))
                        for item in items:
                            playlink = None
                            try:
                                playlink = re.findall('"src":"(.+?)"',str(item))[0]
                            except:
                                try:
                                    playlink = re.findall('"file":"(.+?)"',str(item))[0]
                                except:
                                    playlink = re.findall('"link":"(.+?)"',str(item))[0]
                               
                            try:
                                quality = re.findall('"label":"(.+?)"',str(item))[0]
                            except:
                                quality = 'SHIT'
                            if 'SHIT' not in quality:
                                if playlink != None:
                                    playlink = playlink.replace('\\','')
                                    host = playlink.split('//')[1].replace('www.','')
                                    host = host.split('/')[0].split('.')[0].title()
                                    if 'srv' in host.lower():
                                        host = 'DirectLink'
                                    count +=1
                                    self.sources.append({'source': host,'quality': quality,'scraper': self.name,'url': playlink,'direct': False})
            if dev_log=='true':
                end_time = time.time() - self.start_time
                send_log(self.name,end_time,count)

        except:
            pass

#oneonline().scrape_movie('moana','2016','')
#oneonline().scrape_episode('the blacklist','2013','2014','2','2','','')
