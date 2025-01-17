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

import urlparse
import re

from resources.lib.modules import dom_parser
from resources.lib.modules import source_utils
from resources.lib.modules import cleantitle
from resources.lib.modules import source_faultlog
from resources.lib.modules import hdgo
from resources.lib.modules.handler.requestHandler import cRequestHandler
from resources.lib.modules.handler.ParameterHandler import ParameterHandler

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['cinemaxx.cc']
        self.base_link = 'https://cinemaxx.cc'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = self.__search([localtitle] + source_utils.aliases_to_array(aliases))
            if not url and title != localtitle: url = self.__search([title] + source_utils.aliases_to_array(aliases))
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = self.__search([localtvshowtitle] + source_utils.aliases_to_array(aliases))
            if not url and tvshowtitle != localtvshowtitle:
                url = self.__search([tvshowtitle] + source_utils.aliases_to_array(aliases))

            return url
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return
            return [season, episode, url]
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources
            episode = None
            season = None
            if isinstance(url, list):
                season, episode, url = url
            url = urlparse.urljoin(self.base_link, url)
            

            oRequest = cRequestHandler(url, caching=False)
            content = oRequest.request()
            link = dom_parser.parse_dom(content, 'div', attrs={'id': 'full-video'})
            if season:
                try:
                    link = re.findall("vk.show\(\d+,(.*?)\)", link[0].content)[0]
                    link = re.findall("\[(.*?)\]", link)[int(season)-1]
                    link = re.findall("'(.*?)'", link)
                    sources = hdgo.getStreams(link[int(episode)-1], sources)
                except:
                    #we have a tvshow, but no seasons to choose
                    #cinemaxx can host specific seasons, its stated in the url (i.e. http://cinemaxx.cc/serien/743-homeland-7-staffel.html)
                    if season+"-staffel" in url:
                        link = dom_parser.parse_dom(link, 'iframe')
                        episode_links = hdgo.getPlaylistLinks(link[0].attrs['src'])
                        hdgo.getStreams(episode_links[int(episode)-1],sources,skiplast=False)
                    else:
                        pass

            else:
                link = dom_parser.parse_dom(link, 'iframe')
                sources = hdgo.getStreams(link[0].attrs['src'], sources)

            if len(sources) == 0:
                raise Exception()
            return sources
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagScrape, url)
            return sources



    def resolve(self, url):
        try:
            return url
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagResolve)
            return url

    def __search(self, titles):
        try:
            t = [cleantitle.get(i) for i in set(titles) if i]

            for title in titles:

                oRequest = cRequestHandler(self.base_link + "/")
                oRequest.addHeaderEntry('Referer', 'https://cinemaxx.cc/')
                oRequest.addParameters('do', 'search')
                oRequest.addParameters('full_search', '0')
                oRequest.addParameters('search_start', '0')
                oRequest.addParameters('story', title)
                oRequest.addParameters('subaction', 'search')
                oRequest.addParameters('result_from', '1')
                oRequest.addParameters('submit', 'submit')
                oRequest.setRequestType(1)
                result = oRequest.request()
                

                links = dom_parser.parse_dom(result, 'div', attrs={'class': 'shortstory-in'})
                links = [dom_parser.parse_dom(i, 'a')[0] for i in links]
                links = [(i.attrs['href'], i.attrs['title']) for i in links]
                links = [i[0] for i in links if any(a in cleantitle.get(i[1]) for a in t)]

                if len(links) > 0:
                    return source_utils.strip_domain(links[0])
            return
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, titles[0])
            except:
                return
            return
