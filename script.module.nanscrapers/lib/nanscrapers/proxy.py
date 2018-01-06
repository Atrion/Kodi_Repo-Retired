import random
import urllib
import urllib2
import urlparse

from nanscrapers.common import random_agent


def get(url, check, headers=None, data=None):
    if headers is None:
        headers = {
            'User-Agent': random_agent(),
        }
        try:
            request = urllib2.Request(url, headers=headers, data=data)
            html = urllib2.urlopen(request, timeout=10).read()
            if check in str(html): return html
        except:
            pass

    try:
        new_url = get_proxy_url() % urllib.quote_plus(url)
        headers['Referer'] = 'http://%s/' % urlparse.urlparse(new_url).netloc
        request = urllib2.Request(new_url, headers=headers)
        response = urllib2.urlopen(request, timeout=10)
        html = response.read()
        response.close()
        if check in html: return html
    except:
        pass

    try:
        new_url = get_proxy_url() % urllib.quote_plus(url)
        headers['Referer'] = 'http://%s/' % urlparse.urlparse(new_url).netloc
        request = urllib2.Request(new_url, headers=headers)
        html = urllib2.urlopen(request, timeout=10).read()
        if check in html: return html
    except:
        pass

    return


def get_raw(url, headers=None, data=None):
    if headers is None:
        headers = {
            'User-Agent': random_agent(),
        }

    try:
        new_url = get_proxy_url() % urllib.quote_plus(url)
        headers['Referer'] = 'http://%s/' % urlparse.urlparse(new_url).netloc
        request = urllib2.Request(new_url, headers=headers)
        response = urllib2.urlopen(request, timeout=10)
        return response
    except:
        pass


def get_proxy_url():
    return random.choice([
        
        'http://proxite.net/browse.php?u=%s&b=20',   #(yes)
        'http://dontfilter.us/browse.php?b=20&u=%s',  #(yes)
        'http://unblockthatsite.net/browse.php?u=%s&b=0', #(yes)

        #'http://www.justproxy.co.uk/index.php?q=%s',
        #'http://www.englandproxy.co.uk/%s/',
        #'http://free-webproxy.com/browse.php?u=%s&b=29',
        #'http://protectproxy.com/browse.php?u=%s&b=20',
        #'http://free-proxyserver.com/browse.php?b=20&u=%s',
        #'http://www.freeopenproxy.com/browse.php?b=20&u=%s',
        #'http://www.justproxy.co.uk/index.php?hl=2e5&q=%s',
        #'http://alter-ip.com/index.php?hl=3c0&q=%s',
        #'http://www.proxythis.info/index.php?hl=2e5&q=%s',
        #'http://quickprox.com/browse.php?b=20&u=%s',
        #'https://unblock-proxy.com/browse.php?b=20&u=%s&b=0&f=norefer',
        #'http://www.unblockmyweb.com/browse.php?b=20&u=%s',
        #'http://unblocksite.org/view.php?b=20&u=%s',
    ])
