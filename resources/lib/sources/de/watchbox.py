# -*- coding: utf-8 -*-

import re
import requests
import simplejson

from resources.lib.modules import cache
from resources.lib.modules import cleantitle
from resources.lib.modules import dom_parser
from resources.lib.modules import tvmaze

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            title = cleantitle.get(title)
            localtitle = cleantitle.get(localtitle)
            url = 'https://apis.justwatch.com/content/titles/de_DE/popular?body=%7B"languages":"de","content_types":["movie"],"providers":["nfx","wbx","ntz"],"monetization_types":["flatrate","ads","free"],"page":1,"page_size":10,"query":"{}"%7D'.format(localtitle)
            req = cache.get(requests.get, 6, url)
            data = req.json()

            # Loop through hits
            for hit in data['items']:
                # Compare year and title
                if (hit['original_release_year'] == int(year)
                        and localtitle == cleantitle.get(hit['title'])
                        or localtitle == cleantitle.get(hit['original_title'])
                        or title == cleantitle.get(hit['original_title'])
                        or title == cleantitle.get(hit['title'])):

                    for offer in hit['offers']:
                        # Watchbox
                        if offer['provider_id'] == 171:
                            url = offer['urls']['standard_web']
                            break

            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:

            url = 'https://apis.justwatch.com/content/titles/de_DE/popular?body=%7B"languages":"de","content_types":["show"],"providers":["wbx"],"monetization_types":["ads","free"],"page":1,"page_size":5,"query":"{}"%7D'.format(localtvshowtitle)
            req = cache.get(requests.get, 12, url)
            soup = req.json()
            tvshowtitle = cleantitle.get(tvshowtitle)
            localtvshowtitle = cleantitle.get(localtvshowtitle)
            # Loop through hits
            for hit in soup['items']:
                # Compare year
                if (hit['original_release_year'] == int(year)
                        and cleantitle.get(hit['title']) == localtvshowtitle or tvshowtitle == cleantitle.get(hit['title'])):
                    show_id = hit['id']
                    return show_id
                    break


        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode_n):
        try:
            show_id = url
            link = ''
            e_nr = tvmaze.tvMaze().episodeAbsoluteNumber(tvdb, season, episode_n)

            if int(season) == 1:
                s_nr = int(season)
            if int(season) >= 2:
                s_nr = int(season) -1

            url = 'https://apis.justwatch.com/content/titles/show/{}/locale/de_DE/'.format(show_id)
            req = cache.get(requests.get, 6, url)
            data = req.json()

            while link == '':
                s_id = data['seasons'][s_nr -1]['id']
                # 2te anfrage um aus der season id die folge zu bekommen
                url = 'https://apis.justwatch.com/content/titles/show_season/{}/locale/de_DE'.format(s_id)
                req = cache.get(requests.get, 6, url)
                soup = req.json()

                if soup['max_episode_number'] > int(e_nr):
                    for episode in soup['episodes']:
                        if episode['episode_number'] == int(e_nr):
                            for offer in episode['offers']:
                                if offer['provider_id'] == 171:
                                    link = offer['urls']['standard_web']
                                    return link
                                    break

                s_nr += 1
                if int(season) + 1 == s_nr:
                    link = 'no hit'
                    break
            return
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []

        try:
            if not url:
                return sources

            html = cache.get(requests.get, 6, url)
            url_regex = "hls.*?(http.*?m3u8)"
            link = re.findall(url_regex, html.content)
            link=link[0].replace("\\","")
            sources.append({'source': 'CDN', 'quality': 'SD', 'language': 'de', 'url': link, 'direct': True, 'debridonly': False,'info': ''})

            return sources
        except:
            return sources

    def resolve(self, url):
        return url




