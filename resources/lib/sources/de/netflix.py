# -*- coding: UTF-8 -*-

"""
    Lastship Add-on (C) 2019
    Credits to Placenta and Covenant; our thanks go to their creators

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

# Addon Name: Lastship
# Addon id: plugin.video.lastship
# Addon Provider: LastShip

import base64
import re
import requests
import simplejson

from resources.lib.modules import cache
from resources.lib.modules import cleantitle
from resources.lib.modules import dom_parser

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.base_link = 'https://www.werstreamt.es'
        self.vodster_api_key = base64.b64decode("ZWE0Njk0NjYtMWZhOS00MjBjLTk5NGUtNDJiZGJiYjMyYTM4")


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
                        # Netflix
                        if (offer['provider_id'] == 8
                                and offer['presentation_type'] == 'hd'
                                and offer['monetization_type'] == 'flatrate'):

                            nfx_id = [offer['urls']['standard_web'].split("title/")[-1], 'API Justwatch']
                            break
                break
            return nfx_id
        except:
            try:
                url = "http://api.vodster.de/avogler/links.php?api_key=%s&format=json&imdb=%s" % (self.vodster_api_key, imdb)
                nfx_id = [self.get_netflix_id(url), 'API Vodster']
                return nfx_id

            except:
                return


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = self.base_link + '/serien/anbieter-netflix/?q=' + tvshowtitle
            req = cache.get(requests.get, 12, url)
            dom = dom_parser.parse_dom(req.text, 'a', attrs={'itemprop': 'url'})

            for a in dom:
                titl = dom_parser.parse_dom(a, 'strong')[0].content
                yea = dom_parser.parse_dom(a, 'span')[0].content[-4:]

                if tvshowtitle == titl:
                    link =  self.base_link + '/' + a.attrs['href']
                    return link
                    break
        except:
            return 'Kein Hit'



    def episode(self, url, imdb, tvdb, title, premiered, season_n, episode_n):
        nfx_id = []
        try:
            if url == 'Kein Hit':
                url = "http://api.vodster.de/avogler/links.php?api_key=%s&format=json&tvdb=%s&season=%s&episode=%s" % (self.vodster_api_key, tvdb, season_n, episode_n)
                nfx_id = [self.get_netflix_id(url),'API Vodster']
                return nfx_id

            if url != 'Kein Hit':
                req = cache.get(requests.get, 6, url)

                netflix = dom_parser.parse_dom(req.text, 'div', attrs={'id': 'provider-11'})
                seasons = dom_parser.parse_dom(netflix[0].content, 'li')

                for season in seasons:
                    season_number = dom_parser.parse_dom(season, 'strong')[0].content.lstrip('Staffel ')

                    if str(season_number) == str(season_n):

                        data = dom_parser.parse_dom(season, 'form', attrs={'rel': 'nofollow'})
                        ep_nr = int(episode_n) - 1

                        url = self.base_link + data[ep_nr].attrs['action']
                        req = requests.head(url)

                        nfx_id = [req.headers['Location'].split('=')[-1], 'API Justwatch']
                        return nfx_id
                        break
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []

        try:
            if not url:
                return sources
            # 'info': url[1] for debug output
            sources.append({'source': 'Account', 'quality': '1080p', 'language': 'de', 'url': 'plugin://plugin.video.netflix/?action=play_video&video_id='+url[0], 'info': '', 'direct': True,'local': True, 'debridonly': False})
            return sources

        except:
            return sources

    def resolve(self, url):
        return url

    def get_netflix_id(self, url):
        n_id = 0
        req = cache.get(requests.get, 6, url)
        data = req.json()
        for provider in data:
            if (provider["provider"] == "Netflix"):
                n_id = re.findall('(\d+)', provider["url"])[0]
                break

        return n_id

