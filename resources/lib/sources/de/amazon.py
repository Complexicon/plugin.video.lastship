# -*- coding: utf-8 -*-

import re
import os
import xbmc
import urllib

import requests
import simplejson

import difflib


from resources.lib.modules import control
from resources.lib.modules import source_utils
from resources.lib.modules import cleantitle

BaseUrl = 'https://www.amazon.de'
ATVUrl = 'https://atv-ps-eu.amazon.de'
MarketID = 'A1PA6795UKMFR9'
pkg = 'com.fivecent.amazonvideowrapper'
act = ''

class source:
    def __init__(self):
        self.priority = 1
        self.language = ['de']


    

    def movie(self, imdb, title, localtitle, aliases, year):
        try:

            url = self.__search(localtitle,year)
           
            return url
        except:
            return url

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):

        url=cleantitle.getsearch(localtvshowtitle)
                
        return url

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):        
        localtitle=url
        
            
        ### Query Serie

        url="https://atv-ps-eu.amazon.de/cdp/catalog/Search?firmware=fmw:17-app:2.0.45.1210&deviceTypeID=A2M4YX06LWP8WI&deviceID=1&format=json&version=2&formatVersion=3&marketplaceId=A1PA6795UKMFR9&IncludeAll=T&AID=1&searchString="+localtitle+"&OfferGroups=B0043YVHMY&SuppressBlackedoutEST=T&NumberOfResults=40&StartIndex=0"
        #print "print AP query series url", url
        
        easin=""
        data = requests.get(url).json()
       
        for i in data['message']['body']['titles']:
            
            ## Titel abgleich ##
            try:
                #print "print AP episode local title VS. amazon clena title", localtitle,cleantitle.getsearch(str(i['ancestorTitles'][0]['title']))
                #amazontitle =re.sub("\[dt.\/OV\]","",str(i['title']))
                ## try-block weil ChildTitles manchmal leeres ergebnis liefern
                if localtitle in cleantitle.getsearch(str(i['ancestorTitles'][0]['title'])) and not "[ov]" in cleantitle.getsearch(str(i['ancestorTitles'][0]['title'])):
                    #print "print AP TvSow Title found!"
                    ## Season abgleich ##
                    #print "print AP str(season) == str(i['number']", str(season), str(i['number'])
                    try:
                        if str(season) == str(i['number']):
                            #print "print AP TRY S VS S"
                            easin=str(i['childTitles'][0]['feedUrl'])
                            break;
                    except:
                            easin="ERROR"
                    
            except:
                continue

            
      
        
        
        ## if notempty ##
        if easin:
            
            url="https://atv-ps-eu.amazon.de/cdp/catalog/Browse?firmware=fmw:17-app:2.0.45.1210&deviceTypeID=A2M4YX06LWP8WI&deviceID=d24ff55e99d2e8d6353cd941f9f63fbb3d242b92576e09b6b8a90660&format=json&version=2&formatVersion=3&marketplaceId=A1PA6795UKMFR9&"+easin
            data = requests.get(url).json()

            for i in data['message']['body']['titles']:
            
            ## Titel abgleich ##
                try:
                    ## try-block weil ChildTitles manchmal leeres ergebnis liefern
                    prime=i['formats'][0]['offers'][0]['offerType']
                    
                    if prime == "SUBSCRIPTION":
                        #print "print AP Prime Subrsciption",prime
                        if str(episode)==str(i['number']):
                            #print "print Title/EpisodeMAthc "
                            videoid=i['titleId']
                            break;
                except:
                    continue
        
          
           
                
        
            #print "print AP Return URL!!",videoid
            return videoid
        else:
            return

    def sources(self, url, hostDict, hostprDict):
        sources = []
        #print "print AP sources Video ID",url
        try:
            if not url:
                return sources

            

                         
            sources.append({'source': 'Prime', 'quality': '1080p', 'language': 'de', 'url':'plugin://plugin.video.amazon-test/?mode=PlayVideo&asin='+url , 'info': '', 'direct': True,'local': True, 'debridonly': False})
           
            return sources
        except:
            return sources

    def resolve(self, url):        
        return url

    def __search(self, localtitle,year):
        localtitle=cleantitle.getsearch(localtitle)
        
        query="https://atv-ps-eu.amazon.de/cdp/catalog/Search?firmware=fmw:17-app:2.0.45.1210&deviceTypeID=A2M4YX06LWP8WI&deviceID=1&format=json&version=2&formatVersion=3&marketplaceId=A1PA6795UKMFR9&IncludeAll=T&AID=1&searchString="+str(localtitle)+"&NumberOfResults=10&StartIndex=0&Detailed=T"

      
        data = requests.get(query).json()
       

        ## Ende JSON ReponseObjekt ##

        ## 1. korrekten Titel bestimmen ##

        for i in data['message']['body']['titles']:            
            #jahr=str(i['releaseOrFirstAiringDate']['valueFormatted'])
            #print "print AP Titel &Jahr, Jahr Trakt",jahr,i['title'],year
            #amazontitle=str(i['title'])
            ### Release Date stimmt nicht immer ueberein!! ##
            try:
                amazontitle =re.sub("\[dt.\/OV\]","",str(i['title']))
                ratio=difflib.SequenceMatcher(None, localtitle, amazontitle).ratio()
                #print "print AP Title ratio",amazontitle,ratio
            except:
                continue
        
            
            

            
                
            
            #if str(year)==jahr[0:4]:
            if float(ratio) > float(0.5):       
                
                

                ## 2. bestimmen ob im Prime Abo ##
                prime=i['formats'][0]['offers'][0]['offerType']
                
                if prime == "SUBSCRIPTION":                    
                    asin = i['titleId']#data['message']['body']['titles'][0]['titleId']
                    #print "print AP search asin",asin
                
                ## break Release Date ##
                break;
            
        return asin

    

        
