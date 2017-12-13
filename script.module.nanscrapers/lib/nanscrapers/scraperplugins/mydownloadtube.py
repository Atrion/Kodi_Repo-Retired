import re
import requests
import xbmc
import urllib
import base64
from ..common import clean_title,clean_search
from ..scraper import Scraper

requests.packages.urllib3.disable_warnings()

s = requests.session()
User_Agent = 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'

class mydownloadtube(Scraper):
    domains = ['https://www.mydownloadtube.to']
    name = "MyDownloadtube"
    sources = []

    def __init__(self):
        self.base_link = 'https://www.mydownloadtube.to/'
        self.base_tv_link = 'https://www.mydownloadtube.video/'
        self.sources = []

    def scrape_movie(self, title, year, imdb, debrid=False):
        try:
            search_id = urllib.quote_plus(title.lower())
            movie_url = '%ssearch/%s' %(self.base_link,search_id.replace('+','-'))
            #print 'Search URL :::::::::::::: ' + movie_url
            headers = {'User_Agent':User_Agent}
            link = requests.get(movie_url,headers=headers,verify=False).content

            results = re.compile('<ul id=first-carousel1(.+?)</ul>',re.DOTALL).findall(link)
            result = re.compile('alt="(.+?)".+?<h2><a href="(.+?)".+?</h2>.+?>(.+?)</p>',re.DOTALL).findall(str(results))
            for link_title,url,date in result:
                new_url = self.base_link + url
                if clean_title(title).lower() == clean_title(link_title).lower():
                    if year in date:
                        #print 'NEW URL '+new_url
                        headers = {'User-Agent': User_Agent}
                        mov_page = requests.get(new_url,headers=headers,allow_redirects=True).content

                        mov_id = re.compile('id=movie value=(.+?)/>',re.DOTALL).findall(mov_page)[0]
                        mov_id = mov_id.rstrip()

                        headers = {'Origin':'https://mydownloadtube.to', 'Referer':new_url,
                                   'X-Requested-With':'XMLHttpRequest', 'User_Agent':User_Agent}

                        request_url = 'https://mydownloadtube.to/movies/play_online' 
                        
                        form_data = {'movie':mov_id}
                        
                        links_page = requests.post(request_url, data=form_data,verify=False, headers=headers).content

                        matches = re.compile("sources:(.+?)controlbar",re.DOTALL).findall(links_page)
                        match = re.compile("file:window.atob.+?'(.+?)'.+?label:\"(.+?)\"",re.DOTALL).findall(str(matches))
                        for link,res in match:
                            print 'LINK B64'+ link
                            vid = base64.b64decode(link).replace(' ','%20')
                            res = res.replace('3Dp','3D').replace(' HD','')
                            self.sources.append({'source': 'DirectLink','quality': res,'scraper': self.name,'url': vid,'direct': True})
                        
                        match2 = re.compile('<[iI][fF][rR][aA][mM][eE].+?[sS][rR][cC]="(.+?)"',re.DOTALL).findall(links_page) #other links
                        for link in match2:
                            print 'Link > '+link 
                            host = link.split('//')[1].replace('www.','')
                            host = host.split('/')[0].split('.')[0].title()
                            if '1080' in link:
                                res='1080p'
                            elif '720' in link:
                                res='720p'
                            else:res = 'SD'
                            if 'flashx' not in link:
                                self.sources.append({'source': host,'quality': res,'scraper': self.name,'url': link,'direct': False})
            return self.sources
        except Exception, argument:
            return self.sources


    def scrape_episode(self,title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            search_id = clean_search(title.lower())
            show_url = '%sseries/%s' %(self.base_tv_link,search_id.replace(' ','-'))
            #print 'NEW URL '+show_url
            headers = {'User-Agent': User_Agent}
            mov_page = requests.get(show_url,headers=headers,timeout=5).content
            #print mov_page            
            season_chk = '<h4>Season %s' %(season)
            epi_chk = 'Episode %s' %(episode)
           
            block = re.compile('<div class=flt-box-wrp>(.+?)</table>',re.DOTALL).findall(mov_page)
            for seas in block:
                if not season_chk in seas:
                    continue
                newreg = re.compile('<a href="(.+?)">(.+?)</a>',re.DOTALL).findall(seas) 
                for epi_url,epi_name in newreg:
                    if epi_chk in epi_name:
                        #print 'this be >> ' +epi_url                                   
                        
                        headers = {'User-Agent': User_Agent}
                        mov_page = requests.get(epi_url,headers=headers,allow_redirects=True).content

                        mov_id = re.compile('name=idBox value=(.+?)>',re.DOTALL).findall(mov_page)[0]
                        #print 'gwid '+mov_id      
                        
                        headers = {'Origin':self.base_tv_link, 'referer':epi_url,
                                   'X-Requested-With':'XMLHttpRequest', 'User_Agent':User_Agent}

                        request_url = '%sseries/play_online' %(self.base_tv_link)
                        
                        form_data = {'episode':mov_id}
                        
                        links_page = requests.post(request_url, data=form_data,verify=False, headers=headers).content
                        #print links_page
                        matches = re.compile("sources:(.+?)controlbar",re.DOTALL).findall(links_page)
                        match = re.compile("file:window.atob.+?'(.+?)'.+?label:\"(.+?)\"",re.DOTALL).findall(str(matches))
                        for link,res in match:
                            #print 'LINK B64'+ link
                            vid = base64.b64decode(link).replace(' ','%20')
                            #print 'vid > '+vid
                            res = res.replace('3Dp','3D').replace(' HD','')
                            self.sources.append({'source': 'DirectLink','quality': res,'scraper': self.name,'url': vid,'direct': True})
                        
                        match2 = re.compile('<[iI][fF][rR][aA][mM][eE].+?[sS][rR][cC]="(.+?)"',re.DOTALL).findall(links_page) #other links
                        for link in match2:
                            #print 'Link > '+link 
                            host = link.split('//')[1].replace('www.','')
                            host = host.split('/')[0].split('.')[0].title()
                            if '1080' in link:
                                res='1080p'
                            elif '720' in link:
                                res='720p'
                            else:res = 'DVD'
                            if 'flashx' not in link:
                                self.sources.append({'source': host,'quality': res,'scraper': self.name,'url': link,'direct': False})
            return self.sources
        except Exception, argument:
            return self.sources