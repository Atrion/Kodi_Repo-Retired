# -*- coding: utf-8 -*-

"""
    sports.py --- Collection of functions related to scraping sport sources
    Copyright (C) 2017, Midraal

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import time
import xbmc
import requests
from BeautifulSoup import BeautifulSoup
from datetime import datetime, timedelta
from koding import route
from resources.lib.util.url import proxy_get
from resources.lib.util.xml import BobList
from resources.lib.util.xml import display_list


@route("sport_acesoplisting")
def get_acesoplisting():
    """
get listings from acespoplisting.in
    :return: listing from website in bob list xml format
    :rtype: str
    """
    xml = "<fanart>https://www.dropbox.com/s/x3zg9ovot6vipjh/smoke_men-wallpaper-1920x1080.jpg?raw=true</fanart>\n\n\n" \
          "<item>\n" \
          "\t<title>[COLORred]Will require Plexus addon to watch Acestream links.[/COLOR]</title>\n" \
          "\t<link> </link>\n" \
          "\t<thumbnail> </thumbnail>\n" \
          "</item>\n\n" \
          "<item>\n" \
          "\t<title>[COLORred]Download in Community Portal.[/COLOR]</title>\n" \
          "\t<link> </link>\n" \
          "\t<thumbnail> </thumbnail>\n" \
          "</item>\n\n" \
          "<item>\n" \

    try:
        html = proxy_get("http://www.acesoplisting.in/", 'id="listing"')
        scraped_html = BeautifulSoup(html)
        table = scraped_html.findAll("table", attrs={'id': 'listing'})[-1]
        rows = table.findAll("tr")
        is_today = False
        day_xml = ""
        found_links = False
        for row in rows:
            cells = row.findAll("td")
            if row.get("class", "") == "info" and not is_today:
                if not cells:
                    continue
                date = cells[0].text.strip()
                today_number = time.gmtime().tm_mday
                if str(today_number) in date:
                    is_today = True
                if is_today:
                    day_xml = "\n" \
                              "<item>\n" \
                              "\t<title>%s</title>\n" \
                              "\t<link></link>\n" \
                              "\t<thumbnail></thumbnail>\n" \
                              "</item>\n" % date
            elif is_today:
                if len(cells) < 5:
                    continue
                event_time = cells[1].text.strip()
                split_time = event_time.split(":")
                event_hours = int(split_time[0])
                event_minutes = split_time[1]
                est_event_hours = event_hours - 4

                if est_event_hours >= 4:
                    xml += day_xml
                    day_xml = ""
                if est_event_hours < 0:
                    est_event_hours = 24 - abs(est_event_hours)
                if est_event_hours >= 12:
                    if not est_event_hours == 12:
                        est_event_hours -= 12
                    suffix = "PM"
                else:
                    suffix = "AM"
                event_time = "%s:%s %s" % (est_event_hours, event_minutes, suffix)

                sport = cells[3].text.strip()
                match = cells[5].text.replace("\n", "").strip()
                match = " ".join(match.split())
                league = cells[6].text.strip()
                if league == "USA NFL":
                    thumbnail = "http://organizationalphysics.com/wp-content/uploads/2013/12/NFLShield.png"
                elif league == "WWE":
                    thumbnail = "http://i.imgur.com/UsYsZ.png"
                elif league == "USA NBA PLAYOFFS":
                    thumbnail = "http://www.fmuweb.com/rjordan/NBA-logo.jpg"
                elif league == "PREMIER LEAGUE":
                    thumbnail = "https://d1fy1ym40biffm.cloudfront.net/images/logos/leagues/f633765f43fafaf2120a1bb9b2a7babd4f0d9380ed1bc72925c29ba18ace9269.png"
                elif league == "SPANISH LA LIGA":
                    thumbnail= "http://a2.espncdn.com/combiner/i?img=%2Fi%2Fleaguelogos%2Fsoccer%2F500%2F15.png"
                elif league == "ITALIA SERIE A":
                    thumbnail = "https://www.expressvpn.com/stream-sports/wp-content/uploads/sites/3/2016/06/serie-a.png"
                elif league == "USA MLS":
                    thumbnail = "https://s-media-cache-ak0.pinimg.com/originals/45/91/a0/4591a0e85db9cc3e799540aad3de0f61.png"
                elif league == "BUNDESLIGA":
                    thumbnail = "http://vignette3.wikia.nocookie.net/the-football-database/images/c/cd/Germany_Competitions_001.png/revision/latest?cb=20131013133441"
                elif league == "FRENCH LIGUE 1":
                    thumbnail = "http://a2.espncdn.com/combiner/i?img=%2Fi%2Fleaguelogos%2Fsoccer%2F500%2F9.png"
                elif league == "CHILE LEAGUE":
                    thumbnail = "https://hdlogo.files.wordpress.com/2015/07/chile-hd-logo.png"
                elif league == "SPANISH LA LIGA 2":
                    thumbnail = "https://1.bp.blogspot.com/-WzlJoteHQM4/V7Tb1xWMACI/AAAAAAAACiM/WEphYXfV_Bgoh7__SPxO7JjQIHSDqGzwACLcB/s1600/15.%2BLaLiga%2B2.png"
                elif league == "SPANISH ACB":
                    thumbnail = "http://www.thesportsdb.com/images/media/league/badge/txqrru1422788047.png"
                elif league == "PORTUGAL A LIGA":
                    thumbnail = "http://vignette2.wikia.nocookie.net/logopedia/images/b/b3/Liga_Portugal_logo.png/revision/latest?cb=20130413151721"
                elif league == "COLOMBIA PRIMERA":
                    thumbnail = "https://hdlogo.files.wordpress.com/2016/02/atlc3a9tico-bucaramanga-hd-logo.png"
                elif league	== "MEXICO LIGA MX":
                    thumbnail = "http://img.new.livestream.com/accounts/0000000000597860/3443e018-53b9-4679-9ccb-268eff9f66a4.png"
                elif league == "URUGUAY PRIMERA":
                    thumbnail = "http://www.webcup.com.br/static/images/league/200x200/campeonato-uruguayo-1460050724.jpg"
                elif league == "ITALY SERIE A":
                    thumbnail = "https://www.expressvpn.com/stream-sports/wp-content/uploads/sites/3/2016/06/serie-a.png"
                elif league == "ATP WORLD TOUR":
                    thumbnail = "https://lh6.googleusercontent.com/-Mq2jXXTjaI8/AAAAAAAAAAI/AAAAAAAAQdw/e-0yuIJKJl8/s0-c-k-no-ns/photo.jpg"
                elif sport == "SOCCER":
                    thumbnail = "http://themes.zozothemes.com/mist/sports/wp-content/uploads/sites/6/2015/10/soccer-player.png"
                elif sport == "MOTOGP":
                    thumbnail = "https://www.bestvpnprovider.com/wp-content/uploads/2015/05/MotoGp_Logo.jpg"
                elif sport == "FORMULA 1":
                    thumbnail = "http://d3t1wwu6jp9wzs.cloudfront.net/wp-content/uploads/2016/05/photo.jpg"
                elif sport == "MMA":
                    thumbnail = "http://img3.wikia.nocookie.net/__cb20130511014401/mixedmartialarts/images/c/c5/UFC_logo.png"
                else:
                    thumbnail = ""

                links = cells[7].findAll("a")

                if len(links) != 0:
                    found_links = True
                for link in links:
                    href = link["href"]
                    if "acestream://" in href:
                        xml += "\n" \
                               "<item>\n" \
                               "\t<title>[COLORlime]%s -[COLORorange]  %s[COLORred]  Acestreams[COLORwhite] %s EST[/COLOR]</title>\n" \
                               "\t<link>plugin://program.plexus/?mode=1&url=%s&name=TA+Sports</link>\n" \
                               "\t<thumbnail>%s</thumbnail>\n" \
                               "</item>\n" % (sport, match, event_time, href, thumbnail)
                    elif "sop://" in href:
                        xml += "\n" \
                               "<item>\n" \
                               "\t<title>[COLORlime]%s -[COLORorange]  %s[COLORblue]  Sopcast[COLORwhite] %s EST[/COLOR]</title>\n" \
                               "\t<link>plugin://program.plexus/?url=%s&mode=2&name=TASPORTS</link>\n" \
                               "\t<thumbnail>%s</thumbnail>\n" \
                               "</item>\n" % (sport, match, event_time, href, thumbnail)
        if not found_links:
            xml = "<fanart>https://www.dropbox.com/s/x3zg9ovot6vipjh/smoke_men-wallpaper-1920x1080.jpg?raw=true</fanart>\n\n\n" \
                  "<item>\n" \
                  "\t<title>[COLORred]Will require Plexus addon to watch Acestream links.[/COLOR]</title>\n" \
                  "\t<link> </link>\n" \
                  "\t<thumbnail> </thumbnail>\n" \
                  "</item>\n\n" \
                  "<item>\n" \
                  "\t<title>[COLORred]Download in Community Portal.[/COLOR]</title>\n" \
                  "\t<link> </link>\n" \
                  "\t<thumbnail> </thumbnail>\n" \
                  "</item>\n\n" \
                  "<item>\n" \
                  "\t<title>[COLORred]| [COLORcyan] Live Sporting Events [COLORred]|[/COLOR]</title>\n" \
                  "\t<link> </link>\n" \
                  "\t<thumbnail> </thumbnail>\n" \
                  "</item>\n" \
                  "\n" \
                  "<item>\n" \
                  "\t<title>Currently No Games Available</title>\n" \
                  "\t<link></link>\n" \
                  "\t<thumbnail></thumbnail>\n" \
                  "</item>\n"
        boblist = BobList(xml)
        display_list(boblist.get_list(), boblist.get_content_type())
    except Exception as e:
        xbmc.log("e:" + repr(e))


@route("get_hockey_recaps", args=["url"])
def get_hockey_recaps(page):
    """
get game recap listings from nhl
    :param str page: page of results to scrape
    :return: listing from website in bob list xml format
    :rtype: str
    """
    if page.endswith("a"):
        page = page[:-1]
    xml = "<fanart>http://www.shauntmax30.com/data/out/29/1189697-100-hdq-nhl-wallpapers.png</fanart>\n\n\n" \
          "<item>\n" \
          "\t<title>[COLORred]| [COLORorange] NHL Condensed Games [COLORred]|[/COLOR]</title>\n" \
          "\t<link></link>\n" \
          "\t<thumbnail>https://s20.postimg.org/5x0bndh2l/betweenthepipes.png</thumbnail>\n" \
          "</item>\n\n"

    recaps_json = requests.get(
        "http://search-api.svc.nhl.com/svc/search/v2/nhl_global_en/tag/content/gameRecap?page={0}&sort=new&type=video&hl=false&expand=image.cuts.640x360,image.cuts.1136x640".format(
            page), verify=False).json()
    for doc in recaps_json['docs']:
        referer = "{0}?tag=content&tagValue=gameRecap".format(doc['url'])
        asset_id = doc['asset_id']
        title = doc['title'].replace('Recap: ', '')
        game_date = None
        tags = doc["tags"]
        for tag in tags:
            if "type" in tag and tag["type"].lower() == "calendarEventId".lower() and "displayName" in tag:
                title = tag["displayName"]
            if "type" in tag and tag["type"].lower() == "gameId".lower() and "displayName" in tag:
                game_date_tag = tag["displayName"].split("-")
                if len(game_date_tag) > 1:
                    game_date = game_date_tag[1]
        if game_date:
            title = "{0} ({1})".format(title.encode("latin-1"), game_date)
        image = doc['image']['cuts']['640x360']['src']
        try:
            url = "http://nhl.bamcontent.com/nhl/id/v1/{0}/details/web-v1.json".format(asset_id)
            video_json = requests.get(url, headers={'Referer': referer}, verify=False).json()
        except:
            continue
        max_width = 0
        selected_url = ""
        for video_info in video_json['playbacks']:
            width = video_info['width']
            height = video_info['height']
            if width and width != 'null' and height and height != 'null':
                if width >= max_width:
                    max_width = width
                    selected_url = video_info["url"]
        xml += "<item>\n" \
               "\t<title>{0}</title>\n" \
               "\t<link>{1}</link>\n" \
               "\t<thumbnail>{2}</thumbnail>\n" \
               "</item>\n".format(title, selected_url, image)

    xml += "<dir>\n" \
           "\t<title>Next Page >></title>\n" \
           "\t<link>sport_hockeyrecaps{0}</link>\n" \
           "\t<thumbnail></thumbnail>\n" \
           "</dir>\n".format(int(page) + 1)
    boblist = BobList(xml)
    display_list(boblist.get_list(), boblist.get_content_type())


@route("sport_nhl_games", ["url"])
def get_nhl_games(epg_date=""):
    import string
    if epg_date == "":
        epg_date = datetime.now()
        now_time = time.gmtime().tm_hour
        if now_time <= 4 or now_time >= 23:
            epg_date -= timedelta(hours=4)
        epg_date = epg_date.strftime("%Y-%m-%d")
    if epg_date.endswith("a"):
        epg_date = epg_date[:-1]
    xml = ""
    epgurl = "http://statsapi.web.nhl.com/api/v1/schedule?startDate=%s&endDate=%s&expand=schedule.teams,schedule.game.content.media.epg" \
             % (epg_date, epg_date)
    content = requests.get(epgurl, verify=False).json()
    if not "totalItems" in content or content['totalItems'] <= 0 or not "dates" in content or len(
            content["dates"]) == 0:
        return xml
    start_xmls = {}
    for game_date in content["dates"]:
        if game_date["totalItems"] > 0:
            xml += "\n" \
                   "<item>\n" \
                   "\t<title>[COLORred]%s NHL Schedule in 5000K[/COLOR]</title>\n" \
                   "\t<link></link>\n" \
                   "\t<thumbnail>https://upload.wikimedia.org/wikipedia/en/thumb/e/e4/NHL_Logo_former.svg/996px-NHL_Logo_former.svg.png</thumbnail>\n" \
                   "\t<fanart>http://cdn.wallpapersafari.com/41/55/dqIYaC.jpg</fanart>\n" \
                   "</item>\n" % (datetime.strptime(game_date["date"], "%Y-%m-%d").strftime("%A, %b %d"))
            for game in game_date["games"]:
                try:
                    start_time = datetime.strptime(game["gameDate"], "%Y-%m-%dT%H:%M:%SZ")
                    start_time -= timedelta(hours=5)
                    start_time += timedelta(hours=1)
                    start_time = start_time.strftime("%I:%M %p EST")
                    if not start_time in start_xmls:
                        start_xmls[start_time] = "\n" \
                                                 "<item>\n" \
                                                 "\t<title>[COLORred]| [COLORorange]%s [COLORred]|[/COLOR]</title>\n" \
                                                 "\t<link></link>\n" \
                                                 "\t<thumbnail>https://upload.wikimedia.org/wikipedia/en/thumb/e/e4/NHL_Logo_former.svg/996px-NHL_Logo_former.svg.png</thumbnail>\n" \
                                                 "\t<fanart>http://cdn.wallpapersafari.com/41/55/dqIYaC.jpg</fanart>\n" \
                                                 "</item>\n" % (start_time)
                    home = game['teams']['home']['team']['name'].encode("utf-8").replace("\xc3\xa9", "e")
                    away = game['teams']['away']['team']['name'].encode("utf-8").replace("\xc3\xa9", "e")
                    title = "[COLORwhite]%s @ %s[/COLOR]" % (away, home)
                    image = "https://upload.wikimedia.org/wikipedia/en/thumb/e/e4/NHL_Logo_former.svg/996px-NHL_Logo_former.svg.png"
                    for stream in game["content"]["media"]["epg"]:
                        if stream["title"] == "Recap":
                            try:
                                image = stream['items'][0]['image']['cuts']['640x360']['src']
                            except:
                                pass

                    for stream in game["content"]["media"]["epg"]:
                        if stream["title"] == "NHLTV":
                            game_title = ""
                            home_content_url = ""
                            away_content_url = ""
                            for item in stream['items']:
                                game_title = item["mediaFeedType"].lower()
                                if game_title not in ["home", "away"]:
                                    continue
                                feed_id = item["mediaPlaybackId"]
                                if game_title == "home":
                                    home_content_url = "http://mf.svc.nhl.com/m3u8/%s/%s%s" % (epg_date, feed_id, 'l3c')
                                elif game_title == "away":
                                    away_content_url = "http://mf.svc.nhl.com/m3u8/%s/%s%s" % (epg_date, feed_id, 'l3c')
                            start_xmls[start_time] += "\n" \
                                                      "<dir>\n" \
                                                      "\t<title>%s</title>\n" \
                                                      "\t<link>sport_nhl_home_away(%s,%s,%s,%s)</link>\n" \
                                                      "\t<thumbnail>%s</thumbnail>\n" \
                                                      "\t<fanart>http://cdn.wallpapersafari.com/41/55/dqIYaC.jpg</fanart>\n" \
                                                      "</dir>\n" % (
                                                          title, title, home_content_url, away_content_url, image,
                                                          image)
                except:
                    continue
            keys = sorted(start_xmls.keys())
            for key in keys:
                xml += start_xmls[key]

            boblist = BobList(xml)
            display_list(boblist.get_list(), boblist.get_content_type())
        else:
            continue


@route("nhl_home_away", ["url"])
def get_nhl_home_away(args):
    import xbmc
    if args == "":
        return ""
    args = args.split(",")
    title = args[0]
    home_content_url = args[1]
    away_content_url = args[2]
    image = args[3]
    import xbmc
    import random, string
    seed = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(241))
    xml = ""
    for content_url in [home_content_url, away_content_url]:
        if content_url == home_content_url:
            game_title = "[COLORblue]HOME[/COLOR]"
        elif content_url == away_content_url:
            game_title = "[COLORyellow]AWAY[/COLOR]"
        else:
            game_title = title
        try:
            request = requests.get(content_url, verify=False)
            if request.status_code < 400:
                play_url = request.content
            else:
                play_url = ""
                game_title += " [COLORred]NOT PLAYING YET DUDE!![/COLOR]"
        except:
            continue
        if not play_url is "" and not requests.request('HEAD', play_url, cookies={'mediaAuth': seed}).status_code < 400:
            play_url = play_url.replace('l3c', 'akc')
        game_xml = "<item>\n" \
                   "\t<title>{0}</title>\n" \
                   "\t<link>{1}</link>\n" \
                   "\t<thumbnail>{2}</thumbnail>\n" \
                   "\t<fanart>http://cdn.wallpapersafari.com/41/55/dqIYaC.jpg</fanart>\n" \
                   "</item>\n".format(game_title, play_url, image)
        xml += game_xml
    xbmc.log("xml:" + repr(xml), xbmc.LOGNOTICE)
    boblist = BobList(xml)
    display_list(boblist.get_list(), boblist.get_content_type())


@route("sport_nfl_games", ["url"])
def get_nfl_games(args):
    import xmltodict
    if args == "":
        season = ""
        week = ""
    else:
        season = args[0]
        week = args[1]

    username = 'condor13'
    password = 'condor13'

    base_url = 'https://gamepass.nfl.com/nflgp'
    servlets_url = base_url + '/servlets'
    simlple_console_url = servlets_url + '/simpleconsole'
    login_url = base_url + '/secure/nfllogin'
    session = requests.Session()

    session.post(login_url, data={'username': username, 'password': password})  # login

    simlple_console_data = session.post(simlple_console_url, data={'isflex': 'true'}).content
    simlple_console_dict = xmltodict.parse(simlple_console_data)
    current_season = simlple_console_dict['result']['currentSeason']
    current_week = simlple_console_dict['result']['currentWeek']
    if season == "":
        season = current_season
    if week == "":
        week = current_week

    game_data = session.post(servlets_url + '/games',
                             data={'isFlex': 'true', 'season': season, 'week': week}).content

    game_data_dict = xmltodict.parse(game_data)['result']
    games = game_data_dict['games']['game']
    if isinstance(games, dict):
        games = [games]
    xml = ""
    start_xmls = {}
    thumbnail = "http://www.officialpsds.com/images/thumbs/NFL-Logo-psd95853.png"
    fanart = "http://wallpapercave.com/wp/8iHFIg1.png"
    for game in games:
        if not 'hasProgram' in game:  # no stream
            continue
        if "programId" in game:  # only full games
            homecity = game["homeTeam"]["city"] or ""
            homename = game["homeTeam"]["name"] or ""
            home = "%s %s" % (homecity, homename)
            awaycity = game["awayTeam"]["city"] or ""
            awayname = game["awayTeam"]["name"] or ""
            away = "%s %s" % (awaycity, awayname)
            start_time = datetime(*(time.strptime(game['gameTimeGMT'], '%Y-%m-%dT%H:%M:%S.000')[0:6]))
            start_time -= timedelta(hours=5)
            start_time = start_time.strftime("%Y-%m-%d %I:%M %p EST")
            start_xmls[start_time] = "\n" \
                                     "<item>\n" \
                                     "\t<title>[COLORred]| [COLORorange]%s [COLORred]|[/COLOR]</title>\n" \
                                     "\t<link></link>\n" \
                                     "\t<thumbnail>%s</thumbnail>\n" \
                                     "\t<fanart>%s</fanart>\n" \
                                     "</item>\n" % (start_time, thumbnail, fanart)
            game_title = home + " vs. " + away
            game_title = " ".join(game_title.split())
            game_id = game["id"]

            start_xmls[start_time] += "<dir>\n" \
                                      "\t<title>{0}</title>\n" \
                                      "\t<link>sport_nfl_get_game({1})</link>\n" \
                                      "\t<thumbnail>{2}</thumbnail>\n" \
                                      "\t<fanart>{3}</fanart>\n" \
                                      "</dir>\n".format(game_title, game_id, thumbnail, fanart)

    keys = sorted(start_xmls.keys())
    for key in keys:
        xml += start_xmls[key]

    boblist = BobList(xml)
    display_list(boblist.get_list(), boblist.get_content_type())


@route("get_nfl_game", ["url"])
def get_nfl_game(game_id):
    import xmltodict
    import m3u8
    import urllib
    import xbmc
    streams = {}
    username = 'condor13'
    password = 'condor13'

    base_url = 'https://gamepass.nfl.com/nflgp'
    servlets_url = base_url + '/servlets'
    simlple_console_url = servlets_url + '/simpleconsole'
    login_url = base_url + '/secure/nfllogin'
    session = requests.Session()

    session.post(login_url, data={'username': username, 'password': password})  # login
    simlple_console_data = session.post(simlple_console_url, data={'isflex': 'true'}).content
    simlple_console_dict = xmltodict.parse(simlple_console_data)
    current_season = simlple_console_dict['result']['currentSeason']
    current_week = simlple_console_dict['result']['currentWeek']

    thumbnail = "http://www.officialpsds.com/images/thumbs/NFL-Logo-psd95853.png"
    fanart = "http://wallpapercave.com/wp/8iHFIg1.png"

    url = servlets_url + '/publishpoint'

    headers = {'User-Agent': 'iPad'}
    post_data = {'id': game_id, 'type': 'game', 'nt': '1', 'gt': 'archive'}
    m3u8_data = session.post(url, data=post_data, headers=headers).content

    try:
        m3u8_dict = xmltodict.parse(m3u8_data)['result']
    except:
        post_data = {'id': game_id, 'type': 'game', 'nt': '1', 'gt': 'live'}
        m3u8_data = session.post(url, data=post_data, headers=headers).content
        m3u8_dict = xmltodict.parse(m3u8_data)['result']

    m3u8_url = m3u8_dict['path'].replace('_ipad', '')
    m3u8_param = m3u8_url.split('?', 1)[-1]
    m3u8_header = {'Cookie': 'nlqptid=' + m3u8_param,
                   'User-Agent': 'Safari/537.36 Mozilla/5.0 AppleWebKit/537.36 Chrome/31.0.1650.57',
                   'Accept-encoding': 'identity, gzip, deflate',
                   'Connection': 'keep-alive'}

    try:
        m3u8_manifest = session.get(m3u8_url).content
    except:
        m3u8_manifest = False

    if m3u8_manifest:
        m3u8_obj = m3u8.loads(m3u8_manifest)
        if m3u8_obj.is_variant:  # if this m3u8 contains links to other m3u8s
            for playlist in m3u8_obj.playlists:
                bitrate = int(playlist.stream_info.bandwidth) / 1000
                streams[str(bitrate)] = m3u8_url[:m3u8_url.rfind('/') + 1] + playlist.uri + '?' + m3u8_url.split('?')[
                    1] + '|' + urllib.urlencode(m3u8_header)
        else:
            game_xml = "<item>\n" \
                       "\t<title>stream</title>\n" \
                       "\t<link>{1}</link>\n" \
                       "\t<thumbnail>{2}</thumbnail>\n" \
                       "\t<fanart>{3}</fanart>\n" \
                       "</item>\n".format(m3u8_url, thumbnail, fanart)
            return game_xml

    xml = ''

    keys = sorted(streams.keys(), key=lambda key: int(key))
    for key in keys:
        game_xml = "<item>\n" \
                   "\t<title>{0} kbps</title>\n" \
                   "\t<link>{1}</link>\n" \
                   "\t<thumbnail>{2}</thumbnail>\n" \
                   "\t<fanart>{3}</fanart>\n" \
                   "</item>\n".format(key, streams[key], thumbnail, fanart)

        xml += game_xml
    boblist = BobList(xml)
    display_list(boblist.get_list(), boblist.get_content_type())


@route("sport_condensed_nfl_games", ["url"])
def get_condensed_nfl_games(args):
    import xmltodict
    username = 'condor13'
    password = 'condor13'

    if args == "":
        season = ""
        week = ""
    else:
        season = args[0]
        week = args[1]

    base_url = 'https://gamepass.nfl.com/nflgp'
    servlets_url = base_url + '/servlets'
    simlple_console_url = servlets_url + '/simpleconsole'
    login_url = base_url + '/secure/nfllogin'
    session = requests.Session()

    session.post(login_url, data={'username': username, 'password': password})  # login

    simlple_console_data = session.post(simlple_console_url, data={'isflex': 'true'}).content
    simlple_console_dict = xmltodict.parse(simlple_console_data)
    current_season = simlple_console_dict['result']['currentSeason']
    current_week = simlple_console_dict['result']['currentWeek']
    if season == "":
        season = current_season
    if week == "":
        week = current_week

    game_data = session.post(servlets_url + '/games',
                             data={'isFlex': 'true', 'season': season, 'week': week}).content
    game_data_dict = xmltodict.parse(game_data)['result']
    games = game_data_dict['games']['game']
    if isinstance(games, dict):
        games = [games]

    xml = ""
    start_xmls = {}
    thumbnail = "http://www.officialpsds.com/images/thumbs/NFL-Logo-psd95853.png"
    fanart = "http://wallpapercave.com/wp/8iHFIg1.png"
    for game in games:
        if not 'hasProgram' in game:  # no stream
            continue
        if "condensedId" in game:  # only condensed
            homecity = game["homeTeam"]["city"] or ""
            homename = game["homeTeam"]["name"] or ""
            home = "%s %s" % (homecity, homename)
            awaycity = game["awayTeam"]["city"] or ""
            awayname = game["awayTeam"]["name"] or ""
            away = "%s %s" % (awaycity, awayname)
            start_time = datetime(*(time.strptime(game['gameTimeGMT'], '%Y-%m-%dT%H:%M:%S.000')[0:6]))
            start_time -= timedelta(hours=5)
            start_time = start_time.strftime("%Y-%m-%d %I:%M %p EST")
            start_xmls[start_time] = "\n" \
                                     "<item>\n" \
                                     "\t<title>[COLORred]| [COLORorange]%s [COLORred]|[/COLOR]</title>\n" \
                                     "\t<link></link>\n" \
                                     "\t<thumbnail>%s</thumbnail>\n" \
                                     "\t<fanart>%s</fanart>\n" \
                                     "</item>\n" % (start_time, thumbnail, fanart)
            game_title = home + " vs. " + away
            game_title = " ".join(game_title.split())
            game_id = game["id"]

            start_xmls[start_time] += "<dir>\n" \
                                      "\t<title>{0}</title>\n" \
                                      "\t<link>sport_condensed_nfl_get_game({1})</link>\n" \
                                      "\t<thumbnail>{2}</thumbnail>\n" \
                                      "\t<fanart>{3}</fanart>\n" \
                                      "</dir>\n".format(game_title, game_id, thumbnail, fanart)

    keys = sorted(start_xmls.keys())
    for key in keys:
        xml += start_xmls[key]

    boblist = BobList(xml)
    display_list(boblist.get_list(), boblist.get_content_type())


@route("sport_condensed_nfl_get_game", ["url"])
def get_condensed_nfl_game(game_id):
    import xmltodict
    import m3u8
    import urllib
    import xbmc
    streams = {}
    username = 'condor13'
    password = 'condor13'

    base_url = 'https://gamepass.nfl.com/nflgp'
    servlets_url = base_url + '/servlets'
    simlple_console_url = servlets_url + '/simpleconsole'
    login_url = base_url + '/secure/nfllogin'
    session = requests.Session()

    session.post(login_url, data={'username': username, 'password': password})  # login
    simlple_console_data = session.post(simlple_console_url, data={'isflex': 'true'}).content
    simlple_console_dict = xmltodict.parse(simlple_console_data)
    current_season = simlple_console_dict['result']['currentSeason']
    current_week = simlple_console_dict['result']['currentWeek']

    thumbnail = "http://www.officialpsds.com/images/thumbs/NFL-Logo-psd95853.png"
    fanart = "http://wallpapercave.com/wp/8iHFIg1.png"

    url = servlets_url + '/publishpoint'

    headers = {'User-Agent': 'iPad'}
    post_data = {'id': game_id, 'type': 'game', 'nt': '1', 'gt': 'condensed'}
    m3u8_data = session.post(url, data=post_data, headers=headers).content

    try:
        m3u8_dict = xmltodict.parse(m3u8_data)['result']
    except:
        return ""

    m3u8_url = m3u8_dict['path'].replace('_ipad', '')
    m3u8_param = m3u8_url.split('?', 1)[-1]
    m3u8_header = {'Cookie': 'nlqptid=' + m3u8_param,
                   'User-Agent': 'Safari/537.36 Mozilla/5.0 AppleWebKit/537.36 Chrome/31.0.1650.57',
                   'Accept-encoding': 'identity, gzip, deflate',
                   'Connection': 'keep-alive'}

    try:
        m3u8_manifest = session.get(m3u8_url).content
    except:
        m3u8_manifest = False

    if m3u8_manifest:
        m3u8_obj = m3u8.loads(m3u8_manifest)
        if m3u8_obj.is_variant:  # if this m3u8 contains links to other m3u8s
            for playlist in m3u8_obj.playlists:
                bitrate = int(playlist.stream_info.bandwidth) / 1000
                streams[str(bitrate)] = m3u8_url[:m3u8_url.rfind('/') + 1] + playlist.uri + '?' + m3u8_url.split('?')[
                    1] + '|' + urllib.urlencode(m3u8_header)
        else:
            game_xml = "<item>\n" \
                       "\t<title>stream</title>\n" \
                       "\t<link>{1}</link>\n" \
                       "\t<thumbnail>{2}</thumbnail>\n" \
                       "\t<fanart>{3}</fanart>\n" \
                       "</item>\n".format(m3u8_url, thumbnail, fanart)
            return game_xml

    xml = ''

    keys = sorted(streams.keys(), key=lambda key: int(key))
    for key in keys:
        game_xml = "<item>\n" \
                   "\t<title>{0} kbps</title>\n" \
                   "\t<link>{1}</link>\n" \
                   "\t<thumbnail>{2}</thumbnail>\n" \
                   "\t<fanart>{3}</fanart>\n" \
                   "</item>\n".format(key, streams[key], thumbnail, fanart)

        xml += game_xml
    boblist = BobList(xml)
    display_list(boblist.get_list(), boblist.get_content_type())

#  LocalWords:  acesoplisting
