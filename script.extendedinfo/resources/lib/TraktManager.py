# -*- coding: UTF-8 -*-
#######################################################################
 # ----------------------------------------------------------------------------
 # "THE BEER-WARE LICENSE" (Revision 42):
 # @Daddy_Blamo wrote this file.  As long as you retain this notice you
 # can do whatever you want with this stuff. If we meet some day, and you think
 # this stuff is worth it, you can buy me a beer in return. - Muad'Dib
 # ----------------------------------------------------------------------------
#######################################################################

# Addon Name: Wraith
# Addon id: script.extendedinfo
# Addon Provider: Mr.Blamo

import json
import re
import time
import urllib
import urlparse

from tmtools import control
from tmtools import utils
from tmtools import client
from tmtools import log_utils

BASE_URL = 'http://api.trakt.tv'
V2_API_KEY = 'a8b9b75c9eb2f2344062edef4248064047427ad1effa1b2578cb7d33d7554f9f'
CLIENT_SECRET = 'c039105944686ca335704386ed7e549641e4bf0d9fdee73ca772f385ef1f483f'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

def __getTrakt(url, post=None):
    try:
        url = urlparse.urljoin(BASE_URL, url)
        post = json.dumps(post) if post else None
        headers = {'Content-Type': 'application/json', 'trakt-api-key': V2_API_KEY, 'trakt-api-version': 2}

        if getTraktCredentialsInfo():
            headers.update({'Authorization': 'Bearer %s' % control.setting('trakt.token')})

        result = client.request(url, post=post, headers=headers, output='extended', error=True)
        
        resp_code = result[1]
        resp_header = result[2]
        result = result[0]

        if resp_code in ['500', '502', '503', '504', '520', '521', '522', '524']:
            log_utils.log('Temporary Trakt Error: %s' % resp_code, log_utils.LOGWARNING)
            return
        elif resp_code in ['404']:
            log_utils.log('Object Not Found : %s' % resp_code, log_utils.LOGWARNING)
            return
        elif resp_code in ['429']:
            log_utils.log('Trakt Rate Limit Reached: %s' % resp_code, log_utils.LOGWARNING)
            return

        if resp_code not in ['401', '405']:
            return result, resp_header

        oauth = urlparse.urljoin(BASE_URL, '/oauth/token')
        opost = {'client_id': V2_API_KEY, 'client_secret': CLIENT_SECRET, 'redirect_uri': REDIRECT_URI, 'grant_type': 'refresh_token', 'refresh_token': control.setting('trakt.refresh')}

        result = client.request(oauth, post=json.dumps(opost), headers=headers)
        result = utils.json_loads_as_str(result)

        token, refresh = result['access_token'], result['refresh_token']

        control.setSetting(id='trakt.token', value=token)
        control.setSetting(id='trakt.refresh', value=refresh)

        headers['Authorization'] = 'Bearer %s' % token

        result = client.request(url, post=post, headers=headers, output='extended', error=True)
        return result[0], result[2]
    except Exception as e:
        log_utils.log('Unknown Trakt Error: %s' % e, log_utils.LOGWARNING)
        pass
        
def getTraktAsJson(url, post=None):
    try:
        r, res_headers = __getTrakt(url, post)
        r = utils.json_loads_as_str(r)
        if 'X-Sort-By' in res_headers and 'X-Sort-How' in res_headers:
            r = sort_list(res_headers['X-Sort-By'], res_headers['X-Sort-How'], r)
        return r
    except:
        pass
        
def authTrakt():
    try:
        if getTraktCredentialsInfo() == True:
            if control.yesnoDialog(control.lang(32251).encode('utf-8'), control.lang(32252).encode('utf-8'), '', 'Trakt'):
                control.setSetting(id='trakt.user', value='')
                control.setSetting(id='trakt.token', value='')
                control.setSetting(id='trakt.refresh', value='')
            raise Exception()

        result = getTraktAsJson('/oauth/device/code', {'client_id': V2_API_KEY})
        verification_url = (control.lang(32253) % result['verification_url']).encode('utf-8')
        user_code = (control.lang(32254) % result['user_code']).encode('utf-8')
        expires_in = int(result['expires_in'])
        device_code = result['device_code']
        interval = result['interval']
        
        progressDialog = control.progressDialog
        progressDialog.create('Trakt', verification_url, user_code)

        for i in range(0, expires_in):
            try:
                if progressDialog.iscanceled(): break
                time.sleep(1)
                if not float(i) % interval == 0: raise Exception()
                r = getTraktAsJson('/oauth/device/token', {'client_id': V2_API_KEY, 'client_secret': CLIENT_SECRET, 'code': device_code})
                if 'access_token' in r: break
            except:
                pass

        try: progressDialog.close()
        except: pass


        token, refresh = r['access_token'], r['refresh_token']

        headers = {'Content-Type': 'application/json', 'trakt-api-key': V2_API_KEY, 'trakt-api-version': 2, 'Authorization': 'Bearer %s' % token}


        result = client.request(urlparse.urljoin(BASE_URL, '/users/me'), headers=headers)
        result = utils.json_loads_as_str(result)

        user = result['username']

        control.setSetting(id='trakt.user', value=user)
        control.setSetting(id='trakt.token', value=token)
        control.setSetting(id='trakt.refresh', value=refresh)
        raise Exception()
    except:
        control.openSettings('3.1')

def getTraktCredentialsInfo():
    user = control.setting('trakt.user').strip()
    token = control.setting('trakt.token')
    refresh = control.setting('trakt.refresh')
    if (user == '' or token == '' or refresh == ''): return False
    return True

def manager(name, tmdb, content):
    try:
        post = {"movies": [{"ids": {"tmdb": tmdb}}]} if content == 'movie' else {"shows": [{"ids": {"tmdb": tmdb}}]}

        items = [(control.lang(32256).encode('utf-8'), '/sync/collection')]
        items += [(control.lang(32257).encode('utf-8'), '/sync/collection/remove')]
        items += [(control.lang(32258).encode('utf-8'), '/sync/watchlist')]
        items += [(control.lang(32259).encode('utf-8'), '/sync/watchlist/remove')]
        items += [(control.lang(32260).encode('utf-8'), '/users/me/lists/%s/items')]

        result = getTraktAsJson('/users/me/lists')
        lists = [(i['name'], i['ids']['slug']) for i in result]
        lists = [lists[i//2] for i in range(len(lists)*2)]
        for i in range(0, len(lists), 2):
            lists[i] = ((control.lang(32261) % lists[i][0]).encode('utf-8'), '/users/me/lists/%s/items' % lists[i][1])
        for i in range(1, len(lists), 2):
            lists[i] = ((control.lang(32262) % lists[i][0]).encode('utf-8'), '/users/me/lists/%s/items/remove' % lists[i][1])
        items += lists

        select = control.selectDialog([i[0] for i in items], control.lang(32255).encode('utf-8'))

        if select == -1:
            return
        elif select == 4:
            t = control.lang(32260).encode('utf-8')
            k = control.keyboard('', t) ; k.doModal()
            new = k.getText() if k.isConfirmed() else None
            if (new == None or new == ''): return
            result = __getTrakt('/users/me/lists', post={"name": new, "privacy": "private"})[0]

            try: slug = utils.json_loads_as_str(result)['ids']['slug']
            except: return control.infoDialog(control.lang(32255).encode('utf-8'), heading=str(name), sound=True, icon='ERROR')
            result = __getTrakt(items[select][1] % slug, post=post)[0]
        else:
            result = __getTrakt(items[select][1], post=post)[0]

        icon = control.infoLabel('ListItem.Icon') if not result == None else 'ERROR'

        control.infoDialog(control.lang(32255).encode('utf-8'), heading=str(name), sound=True, icon=icon)
    except:
        return

def sort_list(sort_key, sort_direction, list_data):
    reverse = False if sort_direction == 'asc' else True
    if sort_key == 'rank':
        return sorted(list_data, key=lambda x: x['rank'], reverse=reverse)
    elif sort_key == 'added':
        return sorted(list_data, key=lambda x: x['listed_at'], reverse=reverse)
    elif sort_key == 'title':
        return sorted(list_data, key=lambda x: utils.title_key(x[x['type']].get('title')), reverse=reverse)
    elif sort_key == 'released':
        return sorted(list_data, key=lambda x: _released_key(x[x['type']]), reverse=reverse)
    elif sort_key == 'runtime':
        return sorted(list_data, key=lambda x: x[x['type']].get('runtime', 0), reverse=reverse)
    elif sort_key == 'popularity':
        return sorted(list_data, key=lambda x: x[x['type']].get('votes', 0), reverse=reverse)
    elif sort_key == 'percentage':
        return sorted(list_data, key=lambda x: x[x['type']].get('rating', 0), reverse=reverse)
    elif sort_key == 'votes':
        return sorted(list_data, key=lambda x: x[x['type']].get('votes', 0), reverse=reverse)
    else:
        return list_data

