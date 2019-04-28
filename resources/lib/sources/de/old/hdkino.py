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

from resources.lib.modules import cleantitle
from resources.lib.modules import duckduckgo
from resources.lib.modules import dom_parser
from resources.lib.modules import source_utils
from resources.lib.modules import source_faultlog
from resources.lib.modules.handler.requestHandler import cRequestHandler

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['hdkino.to']
        self.base_link = 'https://hdkino.to'
        self.search_link = '/search/%s'
        self.stream_link = '/embed.php?video_id=%s&provider=%s'
        self.year_link = self.base_link + '/index.php?a=year&q=%s&page=%s'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = duckduckgo.search([localtitle] + source_utils.aliases_to_array(aliases), year, self.domains[0], '<b>(.*?)\\(')
            if not url:
                url = self._getMovieLink([year, localtitle] + source_utils.aliases_to_array(aliases), year)
            return url
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []

        try:
            if not url:
                return sources

            query = urlparse.urljoin(self.base_link, url)
            oRequest = cRequestHandler(query)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            r = oRequest.request()

            links = re.findall('data-video-id="(.*?)"\sdata-provider="(.*?)"', r)

            for id, hoster in links:
                valid, hoster = source_utils.is_host_valid(hoster, hostDict)
                if not valid: continue

                sources.append({'source': hoster, 'quality': '720p', 'language': 'de', 'url': (id, hoster), 'direct': False, 'debridonly': False, 'checkquality': True})

            if len(sources) == 0:
                raise Exception()
            return sources
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagScrape, url)
            return sources

    def resolve(self, url):
        try:
            link = self.stream_link % (url[0], url[1])
            link = urlparse.urljoin(self.base_link, link)
            oRequest = cRequestHandler(link)
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            content = oRequest.request()
            stream =  re.findall('src=\"(.*?)" /></body>', content)[0]
            return stream
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagResolve)
            return

    def _getMovieLink(self, titles, year):
        try:
            t = [cleantitle.get(i) for i in set(titles) if i]

            link = self.year_link % (year, "%s")
            stream = ""
            for i in range(1, 100, 1):
                oRequest = cRequestHandler(link % str(i))
                oRequest.removeBreakLines(False)
                oRequest.removeNewLines(False)
                content = oRequest.request()
                links = re.findall(r'<a href=\"(.*?)\"(.*?)alt=\"(.*?)\"', content)
                if len(links) == 0: return

                for x in range(0, len(links) -1):
                    title = cleantitle.get(links[x][2])
                    if t[1] in title:
                        stream = links[x][0]

                if len(stream) > 0:
                    return source_utils.strip_domain(stream)
            return
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, titles[0])
            except:
                return
            return
