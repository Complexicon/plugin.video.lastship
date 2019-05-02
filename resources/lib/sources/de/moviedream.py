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

from resources.lib.modules import dom_parser
from resources.lib.modules import source_utils
from resources.lib.modules import source_faultlog
from resources.lib.modules import hdgo
from resources.lib.modules.handler.requestHandler import cRequestHandler
from resources.lib.modules.handler.ParameterHandler import ParameterHandler

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['moviedream.ws']
        self.base_link = 'https://moviedream.ws'
        self.search_link = '/suchergebnisse.php?imdbid=%s&sprache=Deutsch'
        self.hoster_link = '/episodeholen3.php'

        
    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            imdb = re.sub('[^0-9]', '', imdb)
            url = self.__search(imdb)
            return urllib.urlencode({'url': url, 'imdb': imdb}) if url else None
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            imdb = re.sub('[^0-9]', '', imdb)
            url = self.__search(imdb)
            return urllib.urlencode({'url': url, 'imdb': imdb}) if url else None
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return

            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            data.update({'season': season, 'episode': episode})
            return urllib.urlencode(data)
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources

            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            url = urlparse.urljoin(self.base_link, data['url'])
            season = data.get('season')
            episode = data.get('episode')

            if season and episode:
                r = urllib.urlencode({'imdbid': data['imdb'], 'language': 'de', 'season': season, 'episode': episode})
                oRequest = cRequestHandler(urlparse.urljoin(self.base_link, self.hoster_link))
                oRequest.addHeaderEntry("X-Requested-With", "XMLHttpRequest")
                oRequest.setRequestType(1)
                oRequest.addParameters('imdbid', data['imdb'])
                oRequest.addParameters('language', 'de')
                oRequest.addParameters('season', season)
                oRequest.addParameters('episode', episode)
                r = oRequest.request()
            else:
                oRequest = cRequestHandler(url)
                oRequest.removeBreakLines(False)
                oRequest.removeNewLines(False)
                r = oRequest.request()
            
            r = re.findall(r'<a href=\"https(.*?)\" targe(.*?)<img class=\"(.*?)linkbutton\"', r)

            for link, nothing, quli in r:
                link = 'https' + link.replace("\r", "")
                if 'verystream' in link:
                    sources = hdgo.getStreams(link, sources)
                else:
                    valid, host = source_utils.is_host_valid(link, hostDict)
                    if not valid: continue
                    
                    if quli == "hd":
                        quli = '720p'
                    else:
                        quli = 'SD'

                    sources.append({'source': host, 'quality': quli, 'language': 'de', 'url': link, 'direct': False, 'debridonly': False})

            if len(sources) == 0:
                raise Exception()
            return sources
        except:
            source_faultlog.logFault(__name__,source_faultlog.tagScrape, url)
            return sources

    def resolve(self, url):
        return url

    def __search(self, imdb):
        try:
            oRequest = cRequestHandler(urlparse.urljoin(self.base_link, self.search_link % imdb))
            oRequest.removeBreakLines(False)
            oRequest.removeNewLines(False)
            r = oRequest.request()
            r = re.findall(r'linkto\".href=\"(.*?)\"\>', r)

            url = None
            if len(r) > 1:
                for i in r:
                    oRequest = cRequestHandler(urlparse.urljoin(self.base_link, i))
                    oRequest.removeBreakLines(False)
                    oRequest.removeNewLines(False)
                    data = oRequest.request()
                    data = re.compile('(imdbid\s*[=|:]\s*"%s"\s*,)' % imdb, re.DOTALL).findall(data)

                    if len(data) >= 1:
                        url = i
            elif len(r) > 0:
                url = r[0]

            if url:
                return source_utils.strip_domain(url)

        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, imdb)
            except:
                return
            return
