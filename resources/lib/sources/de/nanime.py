# -*- coding: utf-8 -*-
import re
import urllib
import urlparse

from resources.lib.modules import anilist
from resources.lib.modules import cache
from resources.lib.modules import cfscrape
from resources.lib.modules import cleantitle
from resources.lib.modules import dom_parser
from resources.lib.modules import source_faultlog
from resources.lib.modules import source_utils
from resources.lib.modules import tvmaze


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']
        self.genre_filter = ['animation', 'anime']
        self.domains = ['nanime.to']
        self.base_link = 'https://nanime.to'
        self.search_link = '/?s=%s'
        self.scraper = cfscrape.create_scraper()

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            return self._search([title, localtitle, anilist.getAlternativTitle(title)] + source_utils.aliases_to_array(aliases), year)
        except:
            return


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            return self._search([tvshowtitle, localtvshowtitle, tvmaze.tvMaze().showLookup('thetvdb', tvdb).get('name')] + source_utils.aliases_to_array(aliases), year)
        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return

            query = urlparse.urljoin(self.base_link, url)
            content = cache.get(self.scraper.get, 4, query).content

            links = dom_parser.parse_dom(content, 'div', attrs={'id': 'seasons'})
            links = dom_parser.parse_dom(links, 'div', attrs={'class': 'se-c'})
            links = [(dom_parser.parse_dom(i, 'span', attrs={'class': 'se-t'})[0].content, dom_parser.parse_dom(i, 'li')) for i in links]
            links = [i[1] for i in links if season == i[0]][0]
            links = dom_parser.parse_dom(links, 'div', attrs={'class': 'episodiotitle'})
            links = dom_parser.parse_dom(links, 'a')
            links = [(i.attrs['href'], re.findall("x(\d+)", i.attrs['href'])[0]) for i in links]
            links = [i[0] for i in links if episode == i[1]]

            if len(links) > 0:
                return source_utils.strip_domain(links[0])
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if not url:
                return sources

            query = urlparse.urljoin(self.base_link, url)
            content = cache.get(self.scraper.get, 4, query).content

            quality = dom_parser.parse_dom(content, 'span', attrs={'class': 'qualityx'})[0].content
            links = dom_parser.parse_dom(content, 'div', attrs={'id': 'playex'})[0]
            links = dom_parser.parse_dom(links, 'div', attrs={'class': 'fixidtab'})
            links = [dom_parser.parse_dom(i, 'iframe')[0].attrs['src'] if 'iframe' in i.content else re.findall("(http.*?)&", i.content)[0].replace('\\', '') for i in links]

            for url in links:
                valid, hoster = source_utils.is_host_valid(url, hostDict)
                if not valid and not 'nanime.to' in hoster: continue

                sources.append({'source': hoster, 'quality': quality, 'language': 'de', 'url': url, 'direct': True if 'nanime.to' else False, 'debridonly': False, 'checkquality': False})

            return sources
        except:
            source_faultlog.logFault(__name__, source_faultlog.tagScrape, url)
            return sources

    def resolve(self, url):
        return url

    def _search(self, titles, year):
        try:
            t = [cleantitle.get(i) for i in set(titles) if i]

            query = self.search_link % (urllib.quote_plus(titles[0]))
            query = urlparse.urljoin(self.base_link, query)

            content = cache.get(self.scraper.get, 4, query).content

            links = dom_parser.parse_dom(content, 'div', attrs={'class': 'result-item'})
            links = [(dom_parser.parse_dom(i, 'div', attrs={'class': 'title'})[0], dom_parser.parse_dom(i, 'span', attrs={'class': 'year'})[0].content) for i in links]
            links = [(dom_parser.parse_dom(i[0], 'a')[0], i[1]) for i in links]
            links = [(i[0].attrs['href'], i[0].content, i[1]) for i in links]
            links = sorted(links, key=lambda i: int(i[2]), reverse=True)

            links = [i[0] for i in links if any([a in cleantitle.get(i[1]) for a in t]) and i[2] == year]

            if len(links) > 0:
                return source_utils.strip_domain(links[0])
        except:
            try:
                source_faultlog.logFault(__name__, source_faultlog.tagSearch, titles[0])
            except:
                return
            return
