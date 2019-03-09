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
import requests
import json

from resources.lib.modules import source_utils
from resources.lib.modules import duckduckgo

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.vodster_api_key = "ea469466-1fa9-420c-994e-42bdbbb32a38"
        

    def movie(self, imdb, title, localtitle, aliases, year):
        url = "http://api.vodster.de/avogler/links.php?api_key=%s&format=json&imdb=%s" % (self.vodster_api_key, imdb)
        movie_id = self.get_netflix_id(url)

        return movie_id

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):        
        url = "http://api.vodster.de/avogler/links.php?api_key=%s&format=json&tvdb=%s" % (self.vodster_api_key, tvdb)
        tv_show_id = self.get_netflix_id(url)

        return tv_show_id

    def episode(self, tvshowid, imdb, tvdb, title, premiered, season, episode):        
        url = "http://api.vodster.de/avogler/links.php?api_key=&format=json&tvdb=%s&season=%s&episode=%s" % (self.vodster_api_key, tvdb, season, episode)
        episode_id = self.get_netflix_id(url)

        return episode_id



    def sources(self, url, hostDict, hostprDict):
        sources = []
        
        try:
            if not url:
                return sources
            #print "print NF source url",url
            sources.append({'source': 'Account', 'quality': '1080p', 'language': 'de', 'url': 'plugin://plugin.video.netflix/?action=play_video&video_id='+url, 'info': '', 'direct': True,'local': True, 'debridonly': False})
           
            return sources
        except:
            return sources

    def resolve(self, url):
        return url

    def get_netflix_id(self, url):
        id = 0
        data = requests.get(url).json()
        
        for provider in data:
            if (provider["provider"] == "Netflix"):
                id = re.findall('(\d+)', provider["url"])[0]
                break

        return id

