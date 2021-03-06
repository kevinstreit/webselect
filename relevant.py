#!/usr/bin/env python2

import random
import re


def visible(element):
    if element.parent.name in ['style', 'script', '[document]', 'head',
                               'title']:
        return False
    elif re.match('<!--.*-->', element.encode('utf-8')):
        return False
    return True


def siteWords(url):
    from urllib import urlopen
    from bs4 import BeautifulSoup

    html = urlopen(url).read()
    soup = BeautifulSoup(html, "lxml")
    texts = soup.findAll(text=True)

    visible_texts = filter(visible, texts)

    for txt in visible_texts:
        for wd in filter(lambda wd: re.match('^[\w-]{5,}$', wd), txt.split()):
            yield wd


def collectWords(urls):
    wds = set()
    for url in urls:
        wds |= set(siteWords(url))
    return wds


class ApiError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def getRelevantURLForWord(wd, api_key):
    from bing_search_api import BingSearchAPI

    bing = BingSearchAPI(api_key)
    params = {'$format': 'json', '$skip': '10'}
    result = bing.search_web(wd, payload=params)
    if result.status_code == 200:
        entries = result.json()['d']['results']
        if entries:
            rank = random.randint(0, len(entries)-1)
            url = entries[rank]['Url']
            return url, rank+10
        else:
            return None
    else:
        raise ApiError("Web search api error: {}".format(result.status_code))


def getRelevantURLs(wds, n, api_key):
    from urlparse import urlparse

    hosts = set()
    urls = []

    for wd in wds:
        url, rank = getRelevantURLForWord(wd, api_key)
        if url is not None:
            pr = urlparse(url)
            host = pr.hostname
            if host is not None and host not in hosts:
                hosts.add(host)
                urls.append((url, rank))
                if len(urls) >= n:
                    break

    return urls


if (__name__ == '__main__'):
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('urls', metavar='<url>', type=str, nargs='+',
                        help='Entry point(s) for relevant word extraction.')
    parser.add_argument('-n', '--nr', metavar='<n>', type=int, default=100,
                        help='Number of URLs to find.')
    parser.add_argument('-k', '--apikey', metavar='<key>', type=str, nargs=1,
                        required=True, help='API key for search engine \
                                             requests (currently Microsoft \
                                             Bing Search API)')
    args = parser.parse_args()
    wds = collectWords(args.urls)

    try:
        urls = getRelevantURLs(wds, args.nr, args.apikey[0])
        for url, rank in urls:
            print "{} ({})".format(url, rank)
    except ApiError as e:
        print e.value
