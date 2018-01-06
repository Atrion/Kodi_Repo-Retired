import re
import requests
import xbmc
import urllib
from ..scraper import Scraper
import urlparse
from ..common import clean_title,clean_search  

requests.packages.urllib3.disable_warnings()

user_headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0'}


class grabby(Scraper):
    domains = ['https://moviegrabber.tv']
    name = "GMovie"
    sources = []

    def __init__(self):
        self.base_link = 'https://moviegrabber.tv'
        self.info_link = 'https://moviegrabber.tv/backend/media/getDetails?id='
        self.info_url = 'https://moviegrabber.tv/backend/media/getLinks?id='
        self.search_url ='https://moviegrabber.tv/backend/media/search?q='
        self.sources = []

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = clean_search(title.lower())
            start_url = self.search_url + search_id
            html = requests.get(start_url, headers=user_headers, timeout=5, verify=False).content
            results = re.compile('"showid":(.+?),.+?"showname":"(.+?)","year":(.+?)}',re.DOTALL).findall(html)
            for url_id,link_title,date in results:
                #print '%s %s %s' %(url_id,link_title,date)
                if year == date:               
                    if clean_title(title).lower() in clean_title(link_title).lower():

                        movie_link = 'https://moviegrabber.tv/videos/'+url_id
                        self.get_source(url_id,movie_link)
                
            return self.sources
        except Exception as e:
            print repr(e)
            return self.sources

    def scrape_episode(self,title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            start_url = self.search_url + search_id
            html = requests.get(start_url, headers=user_headers, timeout=5, verify=False).content
            results = re.compile('"showid":(.+?),.+?"showname":"(.+?)"',re.DOTALL).findall(html)
            for url_id,link_title in results:
                #print 'tv check %s %s' %(url_id,link_title)
                if clean_title(title).lower() in clean_title(link_title).lower():
                    movie_link = 'https://moviegrabber.tv/videos/'+url_id
                    
                    self.get_tv_source(url_id,movie_link,season,episode)
            return self.sources
        except Exception, argument:
            return self.sources

    def get_source(self,url_id,movie_link,episode=None,season=None):

        h = requests.get(self.info_link+url_id, verify=False).content
        match = re.findall('"id":"(.+?)","title":"(.+?)"',h)
        for epid,epname in match:
            #print 'EPNAME > '+epname
            refex = movie_link+'/'+epid
            new_url = self.info_url+epid
            #print 'chk this  '+new_url
            headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0','Referer':refex}
            html = requests.get(new_url,headers=headers,verify=False).text
            #print 'new html'+html
            getblock = re.findall('"url":"(.+?)"',html,re.DOTALL)
            for url_ in getblock:
                url_ = urllib.unquote(url_)
                #print 'LINK >> '+url_
                if '/securesc/' in url_:
                    new_url = url_.split('/*/')[1].split('?')[0]
                    url_ = 'https://docs.google.com/file/d/%s/edit' %new_url
                    quality = '720p'
                elif '1080' in url_: 
                    quality = '1080p'
                elif '=m37' in url_:
                    quality = '1080p'
                elif '720' in url_: 
                    quality = '720p'
                elif '=m22' in url_:
                    quality = '720p'
                elif '480' in url_: 
                    quality = '480p'
                elif '=m18' in url_:
                    quality = '480p'
                else:
                    quality = 'Unknown'
                if 'GoogleDrive' not in url_: 
                    if '3D' not in url_: 
                        #print 'send this qual %s  -  url %s' %(quality,url_)                    
                        self.sources.append({'source': 'GoogleVideo','quality': quality,'scraper': self.name,'url': url_,'direct': False})

    def get_tv_source(self,url_id,movie_link,season,episode):

        season_bollox = "0%s"%season if len(season)<2 else season
        episode_bollox = "0%s"%episode if len(episode)<2 else episode
        SE_EP = 'S%sE%s' %(season_bollox,episode_bollox)

        
        h = requests.get(self.info_link+url_id, verify=False).content
        match = re.findall('"id":"(.+?)","title":"(.+?)"',h)
        for epid,epname in match:
            #print '%s   -  name> %s' %(epid,epname)
            if not SE_EP in epname:
                continue
            #print 'correct chk > '+SE_EP
            refex = movie_link+'/'+epid
            new_url = self.info_url+epid
            headers = {'User-Agent':'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:55.0) Gecko/20100101 Firefox/55.0','Referer':refex}
            html = requests.get(new_url,headers=headers,verify=False).text

            getblock = re.findall('"url":"(.+?)"',html,re.DOTALL)
            for url_ in getblock:
                url_ = urllib.unquote(url_)
                #print 'LINK >> '+url_
                if '/securesc/' in url_:
                    new_url = url_.split('/*/')[1].split('?')[0]
                    url_ = 'https://docs.google.com/file/d/%s/edit' %new_url
                    quality = '720p'
                elif '1080' in url_: 
                    quality = '1080p'
                elif '=m37' in url_:
                    quality = '1080p'
                elif '720' in url_: 
                    quality = '720p'
                elif '=m22' in url_:
                    quality = '720p'
                elif '480' in url_: 
                    quality = '480p'
                elif '=m18' in url_:
                    quality = '480p'
                else:
                    quality = 'Unknown'
                if 'GoogleDrive' not in url_: 
                    if '3D' not in url_:
                        #print 'send this qual %s  -  url %s' %(quality,url_) 
                        self.sources.append({'source': 'GoogleVideo','quality': quality,'scraper': self.name,'url': url_,'direct': False})