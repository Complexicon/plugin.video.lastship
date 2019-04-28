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

import json
import urllib3
import base64
from resources.lib.modules import source_utils
from resources.lib.modules import source_faultlog

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.base_link_api = 'https://movies.gg/MovieAPI?'
        self.getimdb = 'movie_info_imdb=%s'
        self.getlinks = 'get_links=%s'
        self.key = base64.b64decode('JmtleT15a0RGS2JOSlpwSUF5NGZYc1dYWA==')

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = (self.base_link_api+self.getimdb % imdb+self.key)
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        return url

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources

            ## urllib 3 ##

            ## getmovieID & Quality from imdbID ##
            http = urllib3.PoolManager()
            request = http.request('GET', url)
            request_json = json.loads(request.data.decode('utf8'))
            request.release_conn()
            movie_id = request_json['id']
            movie_type = request_json['movie_type']

            ## getlinks from movieID ##
            link = (self.base_link_api + self.getlinks % movie_id + self.key)
            http = urllib3.PoolManager()
            request = http.request('GET', link)
            request_json = json.loads(request.data.decode('utf8'))
            request.release_conn()

            if movie_type == 'movie':
                q = 'HD'
            else:
                q = 'SD'

            ## return list with links ##
            
            for link in request_json:
                valid, host = source_utils.is_host_valid(link, hostDict)
                if not valid: continue
                                
                sources.append({'source': host, 'quality': q, 'language': 'de', 'url': link, 'direct': False, 'debridonly': False,'checkquality':True})

            if len(sources) == 0:
                raise Exception()
            return sources
        except:
            source_faultlog.logFault(__name__,source_faultlog.tagScrape, url)
            return sources

    def resolve(self, url):
        return url