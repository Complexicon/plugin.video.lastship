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
import urllib
import urlparse

from resources.lib.modules import cache
from resources.lib.modules import cfscrape
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import source_utils
from resources.lib.modules import dom_parser
from resources.lib.modules import source_faultlog


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['movietown.org']
        self.base_link = 'http://movietown.org'
        self.search_link = '/search?q=%s'
        self.scraper = cfscrape.create_scraper()

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = self.__search([localtitle] + source_utils.aliases_to_array(aliases), year)
            if not url and title != localtitle: url = self.__search([title] + source_utils.aliases_to_array(aliases), year)
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = self.__search([localtvshowtitle] + source_utils.aliases_to_array(aliases), year)
            if not url and tvshowtitle != localtvshowtitle: url = self.__search([tvshowtitle] + source_utils.aliases_to_array(aliases), year)
            return url
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return

            s = '/seasons/%s/episodes/%s' % (season, episode)

            url = url.rstrip('/')
            url = url + s
            url = urlparse.urljoin(self.base_link, url)

            return url
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources

            query = urlparse.urljoin(self.base_link, url)

            r = cache.get(self.scraper.get, 4, query).content

            r = dom_parser.parse_dom(r, 'div', attrs={'id': 'ko-bind'})
            r = dom_parser.parse_dom(r, 'table', attrs={'class': 'links-table'})
            r = dom_parser.parse_dom(r, 'tbody')
            r = dom_parser.parse_dom(r, 'tr')
            
            for i in r:
                x = dom_parser.parse_dom(i, 'td', attrs={'class': 'name'}, req='data-bind')

                if len(x) == 0:
                    continue

                hoster = re.search("(?<=>).*$", x[0][1])
                hoster = hoster.group().lower()

                link = re.search("http(.*?)(?=')", x[0][0]['data-bind'])
                link = link.group()

                valid, hoster = source_utils.is_host_valid(hoster, hostDict)
                if not valid: continue

                sources.append({'source': hoster, 'quality': 'SD', 'language': 'de', 'url': link, 'direct': False, 'debridonly': False})

            if len(sources) == 0:
                raise Exception()
            return sources
        except:
            source_faultlog.logFault(__name__,source_faultlog.tagScrape, url)
            return sources

    def resolve(self, url):
        return url

    def __search(self, titles, year):
        try:
            query = self.search_link % (urllib.quote_plus(cleantitle.query(titles[0] + ' ' + year)))
            query = urlparse.urljoin(self.base_link, query)

            t = [cleantitle.get(i) for i in set(titles) if i]

            r = cache.get(self.scraper.get, 4, query).content

            r = dom_parser.parse_dom(r, 'figure', attrs={'class': 'pretty-figure'})
            r = dom_parser.parse_dom(r, 'figcaption')

            for i in r:
                title = client.replaceHTMLCodes(i[0]['title'])
                title = cleantitle.get(title)

                if title in t:
                    x = dom_parser.parse_dom(i, 'a', req='href')
                    return source_utils.strip_domain(x[0][0]['href'])

            return
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, titles[0])
            except:
                return
            return
