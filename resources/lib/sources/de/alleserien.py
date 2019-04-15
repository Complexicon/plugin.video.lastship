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

import re
import urlparse

from resources.lib.modules import cache
from resources.lib.modules import client
from resources.lib.modules import dom_parser
from resources.lib.modules import source_faultlog
from resources.lib.modules import source_utils
from resources.lib.modules import duckduckgo


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['alleserien.com']
        self.base_link = 'http://alleserien.com'
        self.search_link = '/filme'
        self.link_url = '/getpart'
        self.link_url_movie = '/film-getpart'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            return duckduckgo.search([localtitle] + source_utils.aliases_to_array(aliases), year, self.domains[0], "(.*)\sHD\sStream")
        except:
            return ""

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            return duckduckgo.search([localtvshowtitle] + source_utils.aliases_to_array(aliases), year, self.domains[0], "(.*)\sStaffel")
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return
            url = urlparse.urljoin(self.base_link, url)

            r = cache.get(client.request, 4, url)

            seasons = dom_parser.parse_dom(r, "div", attrs={"class": "section-watch-season"})
            seasons = seasons[len(seasons)-int(season)]
            episodes = dom_parser.parse_dom(seasons, "tr")
            episodes = [(dom_parser.parse_dom(i, "th")[0].content, i.attrs["onclick"]) for i in episodes if "onclick" in i.attrs]
            episodes = [re.findall("'(.*?)'", i[1])[0] for i in episodes if i[0] == episode][0]

            return source_utils.strip_domain(episodes)
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, title)
            except:
                return
            return ""

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources
            url = urlparse.urljoin(self.base_link, url)
            content = cache.get(client.request, 4, url)

            links = dom_parser.parse_dom(content, 'tr', attrs={'class': 'partItem'})
            links = [(i.attrs['data-id'], i.attrs['data-controlid'], re.findall("(.*)\.png", i.content)[0].split("/")[-1]) for i in
                     links if 'data-id' in i[0]]

            temp = [i for i in links if i[2].lower() == 'vip']

            for id, controlId, host in temp:
                link = self.resolve((url, id, controlId, 'film' in url))
                import json
                params = {
                    'Referer': url,
                    'Host': 'www.alleserienplayer.com',
                    'Upgrade-Insecure-Requests': '1'
                }

                result = client.request(link, headers=params)
                result = re.findall('sources:\s(.*?])', result, flags=re.S)[0]
                result = json.loads(result)
                [sources.append({'source': 'CDN', 'quality': source_utils.label_to_quality(i['label']), 'language': 'de', 'url': i['file'],
                                'direct': True, 'debridonly': False, 'checkquality': False}) for i in result]

            for i in links:
                multiPart = re.findall('(.*?)-part-\d+', i[2])
                if(len(multiPart) > 0):
                    links = [(i[0], i[1], i[2] + '-part-1' if i[2] == multiPart[0] else i[2]) for i in links]

            links = [(i[0], i[1], re.findall('(.*?)-part-\d+', i[2])[0] if len(re.findall('\d+', i[2])) > 0 else i[2], 'Multi-Part ' + re.findall('\d+', i[2])[0] if len(re.findall('\d+', i[2])) > 0 else None) for i in links]

            for id, controlId, host, multiPart in links:
                valid, hoster = source_utils.is_host_valid(host, hostDict)
                if not valid: continue

                sources.append({'source': hoster, 'quality': 'SD', 'language': 'de', 'url': (url, id, controlId, 'film' in url),
                                'info': multiPart if multiPart else '', 'direct': False, 'debridonly': False, 'checkquality': False})

            return sources
        except Exception as e:
            source_faultlog.logFault(__name__, source_faultlog.tagScrape)
            return sources

    def resolve(self, url):
        try:
            if 'google' in url:
                return url
            url, id, controlId, movieSearch = url

            content = client.request(url)
            token = re.findall("_token':'(.*?)'", content)[0]

            params = {
                '_token': token,
                'PartID': id,
                'ControlID': controlId
            }

            link = urlparse.urljoin(self.base_link, self.link_url_movie if movieSearch else self.link_url)
            result = client.request(link, post=params)
            if 'false' in result:
                return
            else:
                return dom_parser.parse_dom(result, 'iframe')[0].attrs['src']
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagResolve)
            return