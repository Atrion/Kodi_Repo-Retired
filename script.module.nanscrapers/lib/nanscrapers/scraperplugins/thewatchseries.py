import re
import requests
import xbmc
import urllib
from ..scraper import Scraper
import urlparse
from ..common import random_agent, clean_title, filter_host, clean_search
#requests.packages.urllib3.disable_warnings()

User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'


class thewatchseries(Scraper):
    domains = ['http://watchseriesmovie.net']
    name = "TheWatchSeries"
    sources = []

    def __init__(self):
        self.base_link = 'http://watchseriesmovie.net'
        self.sources = []

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            scrape = urllib.quote_plus(title.lower())
            start_url = '%s/search.html?keyword=%s' %(self.base_link,scrape)
            #print 'SEARCH  > '+start_url
            headers = {'User_Agent':User_Agent}
            html = requests.get(start_url, headers=headers,timeout=5).content
            thumbs = re.compile('<ul class="listing items">(.+?)</ul> ',re.DOTALL).findall(html)
            thumb = re.compile('href="(.+?)".+?alt="(.+?)"',re.DOTALL).findall(str(thumbs))  
            for link,link_title in thumb:
                if clean_title(title).lower() == clean_title(link_title).lower():
                    page_link = self.base_link+link
                    headers = {'User_Agent':User_Agent}
                    holdpage = requests.get(page_link, headers=headers,timeout=5).content
                    datecheck = re.compile('<span>Release: </span>(.+?)</li>',re.DOTALL).findall(holdpage)[0]
                    if year in datecheck:
                        movie_link = re.compile('<li class="child_episode".+?href="(.+?)"',re.DOTALL).findall(holdpage)[0]
                        movie_link = self.base_link + movie_link
                        #print 'GW >>>'+movie_link
                        self.get_source(movie_link)
                    else:pass
            return self.sources
        except Exception, argument:
            return self.sources

    def scrape_episode(self,title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            scrape = urllib.quote_plus(title.lower())
            start_url = '%s/search.html?keyword=%s' %(self.base_link,scrape)
            #print 'SEARCH  > '+start_url
            headers = {'User_Agent':User_Agent}
            html = requests.get(start_url, headers=headers,timeout=5).content
            thumbs = re.compile('<ul class="listing items">(.+?)</ul> ',re.DOTALL).findall(html)
            thumb = re.compile('href="(.+?)".+?alt="(.+?)"',re.DOTALL).findall(str(thumbs))  
            for link,link_title in thumb:
                if clean_title(title).lower() in clean_title(link_title).lower():
                    season_chk = '-season-%s' %season
                    #print 'season chk% '+season_chk
                    if season_chk in link:
                        page_link = self.base_link + link
                        #print 'page_link:::::::::::::: '+page_link
                        headers = {'User_Agent':User_Agent}
                        holdpage = requests.get(page_link, headers=headers,timeout=5).content
                        series_links = re.compile('<li class="child_episode".+?href="(.+?)"',re.DOTALL).findall(holdpage)
                        for movie_link in series_links:
                            episode_chk = '-episode-%s' %episode
                            #print 'episode chk% '+episode_chk
                            if episode_chk in movie_link:
                                movie_link = self.base_link + movie_link
                                self.get_source(movie_link)
                    else:pass
            return self.sources
        except Exception, argument:
            return self.sources

    def get_source(self,movie_link):
        try:
            html = requests.get(movie_link).content
            links = re.compile('data-video="(.+?)"',re.DOTALL).findall(html)
            for link in links:
                #print '::::::::::::::::::::::final link> ' + link
                if 'vidnode.net' in link:
                    link = 'http:'+link
                    page = requests.get(link,timeout=3).content
                    vids = re.compile("<source rel.+?src='(.+?)'",re.DOTALL).findall(page)
                    for vid_url in vids:
                        if '=m18' in vid_url:
                            res='360p'
                        elif '=m59' in vid_url:
                            res='480p'
                        elif 'm=22' in vid_url:
                            res = '720p'
                        elif '=m37' in vid_url:
                            res= '1080p'
                        else: pass
                        self.sources.append({'source': 'GoogleLink','quality': res,'scraper': self.name,'url': vid_url,'direct': True})
                elif 'openload' in link:
                    try:
                        chk = requests.get(link).content
                        rez = re.compile('"description" content="(.+?)"',re.DOTALL).findall(chk)[0]
                        if '1080' in rez:
                            res='1080p'
                        elif '720' in rez:
                            res='720p'
                        else:
                            res ='DVD'
                    except: res = 'DVD'
                    self.sources.append({'source': 'Openload', 'quality': res, 'scraper': self.name, 'url': link,'direct': False})
                elif 'streamango.com' in link:
                    get_res=requests.get(link).content
                    res = re.compile('{type:"video/mp4".+?height:(.+?),',re.DOTALL).findall(get_res)[0]
                    self.sources.append({'source': 'Streamango', 'quality': res, 'scraper': self.name, 'url': link,'direct': False})
                else:
                    host = link.split('//')[1].replace('www.','')
                    host = host.split('/')[0].split('.')[0].title()
                    self.sources.append({'source': host,'quality': 'DVD','scraper': self.name,'url': link,'direct': False})
        except:
            pass
