# -*- coding: utf-8 -*-

import re
import requests
import simplejson

from resources.lib.modules import cache
from resources.lib.modules import cleantitle
from resources.lib.modules import dom_parser


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']    

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = 'https://apis.justwatch.com/content/titles/de_DE/popular?body=%7B"languages":"de","content_types":["movie"],"providers":["nfx","amp","wbx","max","ntz"],"monetization_types":["flatrate","ads","free"],"page":1,"page_size":20,"query":"{}"%7D'.format(localtitle)
            req = cache.get(requests.get, 12, url)
            data = req.json()

            # Loop through hits
            for hit in data['items']:
                # Compare year and title
                if (hit['original_release_year'] == int(year)
                        and hit['title'] == localtitle or title == hit['title']):

                    for offer in hit['offers']:

                        # Watchbox
                        if offer['provider_id'] == 171:
                            url = offer['urls']['standard_web']            
                
                    return url
                    break
        except:
            return

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):         
        try:
           
            url = 'https://apis.justwatch.com/content/titles/de_DE/popular?body=%7B"languages":"de","content_types":["show"],"providers":["nfx","amp","wbx","max"],"monetization_types":["flatrate","ads","free"],"page":1,"page_size":20,"query":"{}"%7D'.format(localtvshowtitle)
            req = cache.get(requests.get, 12, url)
            data = req.json()

            # Loop through hits
            for hit in data['items']:
                # Compare year and title
                if (hit['original_release_year'] == int(year)):

                    for offer in hit['offers']:

                        if offer['provider_id'] == 171:
                            url = offer['urls']['standard_web'].rsplit("/", 2)[0]

                            return url
                            break

        except:
            return

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):  
        try:
            if int(season) == 1:
                s_nr = int(season)
            if int(season) > 1:
                s_nr = int(season) -1
            
            en_title = cleantitle.replaceUmlaute(title)
            n_url = url + '/staffel-' + str(s_nr) + '/'
    
            req = cache.get(requests.get, 12, n_url)
            data = dom_parser.parse_dom(req.text, 'a', attrs={'class': 'teaser_season-tab'}, req='href')[:-1]
    
            for i in data:
                tit = cleantitle.replaceUmlaute(i.attrs['data-asset-title'].encode('utf-8'))
    
                if tit == en_title or tit[:-1].rstrip() == en_title:
                    link = 'https://www.watchbox.de' + str(i.attrs['href'])
                    break
                         
            if not link:
                s_nr += 1   
                n_url = url + '/staffel-' + str(s_nr) + '/'
                
                req = cache.get(requests.get, 12, n_url)
                data = dom_parser.parse_dom(req.text, 'a', attrs={'class': 'teaser_season-tab'}, req='href')[:-1]
            
                for i in data:
                    tit = cleantitle.replaceUmlaute(i.attrs['data-asset-title'].encode('utf-8'))
    
                    if tit == en_title or tit[:-1].rstrip() == en_title:
                        link = 'https://www.watchbox.de' + str(i.attrs['href'])
                        break
    
            return link        
        except:
            return
            
    def sources(self, url, hostDict, hostprDict):
        sources = []
        
        try:
            if not url:
                return sources
            
            html = cache.get(requests.get, 12, url)          
            url_regex = "hls.*?(http.*?m3u8)"
            link = re.findall(url_regex, html.content)            
            link=link[0].replace("\\","")   
            sources.append({'source': 'CDN', 'quality': '720p', 'language': 'de', 'url': link, 'direct': True, 'debridonly': False,'info': ''})
           
            return sources
        except:
            return sources

    def resolve(self, url): 
        return url

   
        
   
