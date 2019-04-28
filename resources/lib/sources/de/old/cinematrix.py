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
import requests

from resources.lib.modules import cache
from resources.lib.modules import cfscrape
from resources.lib.modules import dom_parser
from resources.lib.modules import source_utils
from resources.lib.modules import cleantitle
from resources.lib.modules import source_faultlog


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.domains = ['cinematrix.to']
        self.base_link = 'http://cinematrix.to/'
        self.search_link = 'de/suche.html?q=%s'
        self.hoster_link = self.base_link + 'ajax/getHoster%s.php'
        self.hoster_mirror_link = self.base_link + 'ajax/refresh%sMirror.php'
        self.stream_link = self.base_link + 'ajax/get%sStream.php'
        self.get_Episodes = self.base_link + '/ajax/getEpisodes.php'
        self.scraper = cfscrape.create_scraper()

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = self.__search(imdb, [title, localtitle] + source_utils.aliases_to_array(aliases))
            return url
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = self.__search(imdb, [tvshowtitle, localtvshowtitle] + source_utils.aliases_to_array(aliases))
            return url
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            urlparts = re.findall('(.*staffel\/)\d+(.*?)\d+(.*)', url)[0]
            url = urlparts[0] + season + urlparts[1] + episode + urlparts[2]
            return url
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources

            url = urlparse.urljoin(self.base_link, url)
            content = self.scraper.get(url).content
            cookies = requests.utils.dict_from_cookiejar(self.scraper.cookies)

            content_id = re.findall('\d+', dom_parser.parse_dom(content, 'body')[0].attrs['onload'])[0]

            link = self.hoster_link % ('Filme' if 'film' in url else 'Serien')
            if 'film' in url:
                params = self.getParams(content_id, cookies)
            else:
                temp = re.findall('.*staffel\/(\d+).*?(\d+)', url)[0]
                if not self.isEpisodeAvailable(content_id, url, cookies, temp[0], temp[1]):
                    return sources
                params = self.getParams(content_id, cookies, s=temp[0], e=temp[1])

            content = cache.get(self.scraper.post, 4, link, headers=self.getHeader(url), data=params).content

            links = dom_parser.parse_dom(content, 'li')
            links = [(i.attrs['title'], i.attrs['onclick'], dom_parser.parse_dom(i, 'img')[0].attrs['title'], re.findall('/(\d+)', dom_parser.parse_dom(i, 'div', attrs={'class': 'col2'})[0].content)[0]) for i in links]

            for hoster, params, quality, mirrorcount in links:
                valid, hoster = source_utils.is_host_valid(hoster, hostDict)
                if not valid: continue

                url_dict = self.get_url_dict(params, url, True if 'film' in url else False)
                quality = source_utils.get_release_quality(quality)[0]
                for i in range(1, int(mirrorcount)+1):
                    url_dict['zm'] = unicode(i)
                    sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'url': url_dict.copy(), 'direct': False, 'debridonly': False, 'checkquality': False})

            if len(sources) == 0:
                raise Exception()
            return sources
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagScrape, url)
            return sources

    def isEpisodeAvailable(self, content_id, url, cookies, season, episode):
        params = {'c': cookies, 'v': content_id, 'st': season}
        content = cache.get(self.scraper.post, 4, self.get_Episodes, headers=self.getHeader(url), data=params).content
        episodes = dom_parser.parse_dom(content, 'option')
        return any([i.attrs['value'] for i in episodes if i.attrs['value'] == episode])

    def resolve(self, url):
        try:
            self.scraper = cache.get(self.scraper.get, 4, url['url'])
            cookies = requests.utils.dict_from_cookiejar(self.scraper.cookies)
            link = self.hoster_mirror_link % ('Movie' if url['isMovie'] else 'Series')

            params = self.getParams(url['content_id'], cookies, h=url['h'], ut=url['ut'], zm=url['zm'], bq=url['bq'], sq=url['sq'], st=url['bq'], fo=url['sq'])

            content = cache.get(self.scraper.post, 4,link, headers=self.getHeader(url['url']), data=params).content
            link = self.stream_link % ('Movie' if url['isMovie'] else 'Series')

            params = self.getParams(url['content_id'], cookies, h=url['h'], m=content, s=url['bq'], e=url['sq'])

            content = cache.get(self.scraper.post, 4, link, headers=self.getHeader(url['url']), data=params).content
            link = re.findall('(http.*?)"', content)[0]

            return link
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagResolve)
            return

    def __search(self, imdb, titles):
        try:
            t = [cleantitle.get(i) for i in set(titles) if i]
            result = cache.get(self.scraper.get, 4, urlparse.urljoin(self.base_link, self.search_link % imdb)).content

            links = dom_parser.parse_dom(result, 'ul', attrs={'id': 'dataHover'})
            links = dom_parser.parse_dom(links, 'li')
            links = [(dom_parser.parse_dom(i, 'a')[0].attrs['href'], dom_parser.parse_dom(i, 'span')[0]) for i in links]
            links = [(i[0], re.findall('(.*?)<', i[1].content)[0]) for i in links]

            links = [i[0] for i in links if cleantitle.get(i[1]) in t]

            if len(links) > 0:
                return source_utils.strip_domain(links[0])
            return
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, imdb)
            except:
                return
            return

    def getHeader(self, url):
        return {'Referer': url, 'Host': 'www.%s' % self.domains[0], 'Origin': 'http://www.%s' % self.domains[0]}

    def getParams(self, content_id, cookies, h='', ut='', zm='', bq='', sq='', st='', fo='', s='', e='', m=''):
        return {'c': cookies, 'v': content_id, 'h': h, 'ut': ut, 'zm': zm, 'bq': bq, 'sq': sq, 'st': st, 'fo': fo, 's': s, 'e': e, 'm': m}

    def get_url_dict(self, params, url, isMovie):
        url_dict = {}
        onclick = params.split(';')
        splitted = re.findall('\((.*?)\)', onclick[0])[0].split(',')
        url_dict['content_id'] = splitted[0]
        url_dict['h'] = splitted[1]
        splitted = re.findall('\((.*?)\)', onclick[1])[0].split(',')
        url_dict['ut'] = splitted[5]
        url_dict['bq'] = splitted[6]
        url_dict['sq'] = splitted[7]
        url_dict['isMovie'] = isMovie
        url_dict['url'] = url
        return url_dict
