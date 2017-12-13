import re
import requests
import xbmc
from ..scraper import Scraper
from BeautifulSoup import BeautifulSoup
from ..common import clean_title
requests.packages.urllib3.disable_warnings()

class Watchcartoons(Scraper):
    name = "watchcartoon"
    domains = ['watchcartoononline.io']
    sources = []

    def __init__(self):
        self.base_link_cartoons = 'http://www.watchcartoononline.io/cartoon-list'
        self.dubbed_link_cartoons = 'https://www.watchcartoononline.io/dubbed-anime-list'
        self.base_link_movies = 'https://www.watchcartoononline.io/movie-list'
        
    def scrape_episode(self, title, show_year, year, season, episode, imdb, tvdb, debrid = False):
        try:
            cleaned_title = title.replace(' ', '').replace('amp;', '').replace('\'','').lower()
            for link in [self.base_link_cartoons,self.dubbed_link_cartoons]:
                html = requests.get(link).text
                match = re.compile('<a href="(.+?)" title=".+?">(.+?)</a>').findall(html)
                for url, name in match:
                    link_title = name.replace(' ', '').replace('amp;','').replace('\'','').lower()
                    if link_title == cleaned_title:
                        html2 = requests.get(url).text
                        matches=html2.split('class="menu">')[1]
                        match2 = re.compile(
                            '<li><a href="(.+?)"').findall(matches)
                        for url2 in match2:
                            episode_check = 'episode-%s-' %str(episode)
                            season_check = 'season-%s-'  %str(season)
                            #print episode_check
                            #print season_check
                            if season_check in url2.lower():
                                if episode_check in url2.lower():
                                    self.check_for_play(url2, title, show_year, year, season, episode)
                            if not 'season' in url2:
                                if episode_check in url2.lower():
                                    self.check_for_play(url2, title, show_year, year, season, episode)
            return self.sources

        except:
            return []
            pass

    def scrape_movie(self, title, year, imdb, debrid = False):
        try:
            cleaned_title = clean_title(title)
            html = BeautifulSoup(requests.get(self.base_link_movies).text)
            container = html.findAll('div', attrs={'class': 'ddmcc'})[0]
            links = container.findAll('a')
            for link in links:
                try:
                    link_title = link["title"]
                    href = link["href"]
                    clean_link_title = clean_title(link_title)
                    if cleaned_title == clean_link_title:
                        self.check_for_play(href , title, '', year, '', '')
                except:
                    continue
            return self.sources

            #match = re.compile('<a href="(.+?)" title=".+?">(.+?)</a>').findall(html)
            #for url, name in match:
            #    clean_title = title.replace(' ', '').replace('amp;', '').replace('&#8217;','\'').replace('\'','').lower()
            #    clean_name = name.replace('&#8217;','\'').replace(' ', '').replace('amp;','').replace('\'','').lower()
            #    if clean_title in clean_name:
            #        new_url = 'https://www.watchcartoononline.io/'+title.replace(' ','-')
            #        self.check_for_play(url,title,'',year,'','')
            #return self.sources

        except:
            return []
            pass


    def check_for_play(self, url2, title, show_year, year, season, episode):
        try:
            print 'xxxx GW'+url2
            mobile_url = url2.replace('www', 'm')
            html3 = requests.get(mobile_url, verify=False).text
            match_playlink = re.compile('<source src="(.+?)"').findall(html3)
            for playlink in match_playlink:
                self.sources.append(
                    {'source': 'watchcartoons', 'quality': 'SD', 'scraper': self.name, 'url': playlink, 'direct': True})
        except:
            pass

