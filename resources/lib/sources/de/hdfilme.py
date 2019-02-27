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
import json
import re
import urllib
import urlparse
import requests

from resources.lib.modules import cache
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import directstream
from resources.lib.modules import source_utils
from resources.lib.modules import dom_parser
from resources.lib.modules import cfscrape
from resources.lib.modules import source_faultlog

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['hdfilme.net']
        self.base_link = 'https://hdfilme.net'
        self.search_link = '/movie-search?key=%s'
        self.get_link = 'movie/load-stream/%s/%s?server=1'
        self.scraper = cfscrape.create_scraper()

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            titles = [localtitle] + source_utils.aliases_to_array(aliases)
            url = self.__search(titles, year)
            if not url and title != localtitle: url = self.__search([title] + source_utils.aliases_to_array(aliases), year)
            if not url:
                from resources.lib.modules import duckduckgo
                url = duckduckgo.search(titles, year, self.domains[0], '(.*?)\sstream')
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'localtvshowtitle': localtvshowtitle, 'aliases': aliases, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return

            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            tvshowtitle = data['tvshowtitle']
            aliases = source_utils.aliases_to_array(eval(data['aliases']))
            aliases.append(data['localtvshowtitle'])

            url = self.__search([tvshowtitle] + aliases, data['year'], season)
            if not url: return

            urlWithEpisode = url+"?episode="+str(episode)
            return source_utils.strip_domain(urlWithEpisode)
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []

        try:
            if not url:
                return sources

            moviecontent = cache.get(self.scraper.get, 4, urlparse.urljoin(self.base_link, url))

            url = url.replace('-info', '-stream')
            r = re.findall('(\d+)-stream(?:\?episode=(\d+))?', url)
            r = [(i[0], i[1] if i[1] else '1') for i in r][0]

            if "episode" in url:
                #we want the current link
                streamlink = re.findall(r'stream" data-episode-id="(.*?)"\sonclick\=\"event.preventDefault\(\)\;\sload_episode\(this\)\">((?s).*?)</a>', moviecontent.content)
                episode = int(re.findall(r'\?episode=(.*)', url)[0])
                r = (r[0],streamlink[episode-1][0])
            else:
                streamlink = dom_parser.parse_dom(moviecontent.content, 'a', attrs={'class': 'new'})
                r = (r[0],streamlink[int(r[1])-1].attrs['_episode'])

            moviesource = cache.get(self.scraper.get, 4, urlparse.urljoin(self.base_link, self.get_link % r), headers={'referer': urlparse.urljoin(self.base_link, url)})
            foundsource = re.findall(r'window.urlVideo = (\".*?\");', moviesource.content)
            sourcejson = json.loads(foundsource[0])

            moviesources = cache.get(self.scraper.get, 4, sourcejson)
            streams = re.findall(r'/drive(.*?)\n', moviesources.content)
            qualitys = re.findall(r'RESOLUTION=(.*?)\n', moviesources.content)
            url_stream = re.findall(r'"(.*?)"', foundsource[0])

            for x in range(0, len(qualitys)):
                stream = ('/drive' + streams[x])
                if "1080" in qualitys[x]:
                    sources.append({'source': 'HDFILME.NET', 'quality': '1080p', 'language': 'de', 'url': urlparse.urljoin(url_stream[0], stream), 'direct': True, 'debridonly': False})
                elif "720" in qualitys[x]:
                    sources.append({'source': 'HDFILME.NET', 'quality': '720p', 'language': 'de', 'url': urlparse.urljoin(url_stream[0], stream), 'direct': True, 'debridonly': False})
                else:
                    sources.append({'source': 'HDFILME.NET', 'quality': 'SD', 'language': 'de', 'url': urlparse.urljoin(url_stream[0], stream), 'direct': True, 'debridonly': False})
            return sources
            
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagScrape)
            return sources

    def resolve(self, url):
        return url

    def __search(self, titles, year, season='0'):
        try:
            query = self.search_link % (urllib.quote_plus(cleantitle.query(titles[0])))
            query = urlparse.urljoin(self.base_link, query)

            titles = [cleantitle.get(i) for i in set(titles) if i]

            cache.cache_clear()
            searchResult = cache.get(self.scraper.get, 4, query).content
            results = re.findall(r'<div class="title-product">\n<a href="(.*?)">((?s).*?)</a>', searchResult)
        
            usedIndex = 0
            #Find result with matching name and season
            for x in range(0, len(results)):
                title = cleantitle.get(results[x][1])

                if any(i in title for i in titles):
                    if season == "0" or ("staffel" in title and ("0"+str(season) in title or str(season) in title)):
                        #We have the suspected link!
                        
                        return source_utils.strip_domain(results[x][0])
                usedIndex += 1

            return
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, titles[0])
            except:
                return
            return
