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

import re,sys,json,time,xbmc,xbmcaddon
import hashlib,urllib,os,base64,codecs,xmlrpclib
import gzip, StringIO, AddonSignals

try: from sqlite3 import dbapi2 as database
except: from pysqlite2 import dbapi2 as database

try:
    from urlparse import parse_qsl, parse_qs, unquote, urlparse
    from urllib import urlencode, quote_plus, quote
except:
    from urllib.parse import parse_qsl, urlencode, quote_plus, parse_qs, quote, unquote, urlparse

from resources.lib.modules import control
from resources.lib.modules import cleantitle
from resources.lib.modules import playcount



class player(xbmc.Player):
    def __init__ (self):
        xbmc.Player.__init__(self)

    def run(self, title, year, season, episode, imdb, tvdb, url, meta):
        try:
            control.sleep(200)

            self.totalTime = 0 ; self.currentTime = 0

            self.content = 'movie' if season == None or episode == None else 'episode'

            self.title = title ; self.year = year
            self.name = urllib.quote_plus(title) + urllib.quote_plus(' (%s)' % year) if self.content == 'movie' else urllib.quote_plus(title) + urllib.quote_plus(' S%02dE%02d' % (int(season), int(episode)))
            self.name = urllib.unquote_plus(self.name)
            self.season = '%01d' % int(season) if self.content == 'episode' else None
            self.episode = '%01d' % int(episode) if self.content == 'episode' else None

            self.DBID = None
            self.imdb = imdb if not imdb == None else '0'
            self.tvdb = tvdb if not tvdb == None else '0'
            self.ids = {'imdb': self.imdb, 'tvdb': self.tvdb}
            self.ids = dict((k,v) for k, v in self.ids.iteritems() if not v == '0')
            self.meta = meta
            
            self.offset = bookmarks().get(self.name, season, episode, imdb, self.year)

            poster, thumb, meta = self.getMeta(meta)

            item = control.item(path=url)
            item.setArt({'icon': thumb, 'thumb': thumb, 'poster': poster, 'tvshow.poster': poster, 'season.poster': poster})
            item.setInfo(type='Video', infoLabels = meta)
            # temp. foxx fix start
            if "foxx.to" in url:
                item.setContentLookup(False)
                item.setMimeType('video/mp4')
            # temp. foxx fix ende
            if 'plugin' in control.infoLabel('Container.PluginName'):
                control.player.play(url, item)

            control.resolve(int(sys.argv[1]), True, item)

            control.window.setProperty('script.trakt.ids', json.dumps(self.ids))

            self.keepPlaybackAlive()

            control.window.clearProperty('script.trakt.ids')
        except:
            return


    def getMeta(self, meta):
        try:
            poster = meta['poster'] if 'poster' in meta else '0'
            thumb = meta['thumb'] if 'thumb' in meta else poster

            if poster == '0': poster = control.addonPoster()

            return (poster, thumb, meta)
        except:
            pass

        try:
            if not self.content == 'movie': raise Exception()

            meta = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetMovies", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties" : ["title", "originaltitle", "year", "genre", "studio", "country", "runtime", "rating", "votes", "mpaa", "director", "writer", "plot", "plotoutline", "tagline", "thumbnail", "file"]}, "id": 1}' % (self.year, str(int(self.year)+1), str(int(self.year)-1)))
            meta = unicode(meta, 'utf-8', errors='ignore')
            meta = json.loads(meta)['result']['movies']

            t = cleantitle.get(self.title)
            meta = [i for i in meta if self.year == str(i['year']) and (t == cleantitle.get(i['title']) or t == cleantitle.get(i['originaltitle']))][0]

            for k, v in meta.iteritems():
                if type(v) == list:
                    try: meta[k] = str(' / '.join([i.encode('utf-8') for i in v]))
                    except: meta[k] = ''
                else:
                    try: meta[k] = str(v.encode('utf-8'))
                    except: meta[k] = str(v)

            if not 'plugin' in control.infoLabel('Container.PluginName'):
                self.DBID = meta['movieid']

            poster = thumb = meta['thumbnail']

            return (poster, thumb, meta)
        except:
            pass

        try:
            if not self.content == 'episode': raise Exception()

            meta = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetTVShows", "params": {"filter":{"or": [{"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}, {"field": "year", "operator": "is", "value": "%s"}]}, "properties" : ["title", "year", "thumbnail", "file"]}, "id": 1}' % (self.year, str(int(self.year)+1), str(int(self.year)-1)))
            meta = unicode(meta, 'utf-8', errors='ignore')
            meta = json.loads(meta)['result']['tvshows']

            t = cleantitle.get(self.title)
            meta = [i for i in meta if self.year == str(i['year']) and t == cleantitle.get(i['title'])][0]

            tvshowid = meta['tvshowid'] ; poster = meta['thumbnail']

            meta = control.jsonrpc('{"jsonrpc": "2.0", "method": "VideoLibrary.GetEpisodes", "params":{ "tvshowid": %d, "filter":{"and": [{"field": "season", "operator": "is", "value": "%s"}, {"field": "episode", "operator": "is", "value": "%s"}]}, "properties": ["title", "season", "episode", "showtitle", "firstaired", "runtime", "rating", "director", "writer", "plot", "thumbnail", "file"]}, "id": 1}' % (tvshowid, self.season, self.episode))
            meta = unicode(meta, 'utf-8', errors='ignore')
            meta = json.loads(meta)['result']['episodes'][0]

            for k, v in meta.iteritems():
                if type(v) == list:
                    try: meta[k] = str(' / '.join([i.encode('utf-8') for i in v]))
                    except: meta[k] = ''
                else:
                    try: meta[k] = str(v.encode('utf-8'))
                    except: meta[k] = str(v)

            if not 'plugin' in control.infoLabel('Container.PluginName'):
                self.DBID = meta['episodeid']

            thumb = meta['thumbnail']

            return (poster, thumb, meta)
        except:
            pass


        poster, thumb, meta = '', '', {'title': self.name}
        return (poster, thumb, meta)


    def keepPlaybackAlive(self):
        pname = '%s.player.overlay' % control.addonInfo('id')
        control.window.clearProperty(pname)

        if self.content == 'movie':
            overlay = playcount.getMovieOverlay(playcount.getMovieIndicators(), self.imdb)

        elif self.content == 'episode':
            overlay = playcount.getEpisodeOverlay(playcount.getTVShowIndicators(), self.imdb, self.tvdb, self.season, self.episode)
        
        else:
            overlay = '6'


        for i in range(0, 240):
            if self.isPlayingVideo(): break
            xbmc.sleep(1000)


        if overlay == '7':

            while self.isPlayingVideo():
                try:
                    self.totalTime = self.getTotalTime()
                    self.currentTime = self.getTime()
                except:
                    pass
                xbmc.sleep(2000)


        elif self.content == 'movie':

            while self.isPlayingVideo():
                try:
                    self.totalTime = self.getTotalTime()
                    self.currentTime = self.getTime()

                    watcher = (self.currentTime / self.totalTime >= .9)
                    property = control.window.getProperty(pname)

                    if watcher == True and not property == '7':
                        control.window.setProperty(pname, '7')
                        playcount.markMovieDuringPlayback(self.imdb, '7')

                    elif watcher == False and not property == '6':
                        control.window.setProperty(pname, '6')
                        playcount.markMovieDuringPlayback(self.imdb, '6')
                except:
                    pass
                xbmc.sleep(2000)


        elif self.content == 'episode':

            while self.isPlayingVideo():
                try:
                    self.totalTime = self.getTotalTime()
                    self.currentTime = self.getTime()

                    watcher = (self.currentTime / self.totalTime >= .9)
                    property = control.window.getProperty(pname)

                    if watcher == True and not property == '7':
                        control.window.setProperty(pname, '7')
                        playcount.markEpisodeDuringPlayback(self.imdb, self.tvdb, self.season, self.episode, '7')

                    elif watcher == False and not property == '6':
                        control.window.setProperty(pname, '6')
                        playcount.markEpisodeDuringPlayback(self.imdb, self.tvdb, self.season, self.episode, '6')
                except:
                    pass
                xbmc.sleep(2000)

        control.window.clearProperty(pname)


    def libForPlayback(self):
        try:
            if self.DBID == None: raise Exception()

            if self.content == 'movie':
                rpc = '{"jsonrpc": "2.0", "method": "VideoLibrary.SetMovieDetails", "params": {"movieid" : %s, "playcount" : 1 }, "id": 1 }' % str(self.DBID)
            elif self.content == 'episode':
                rpc = '{"jsonrpc": "2.0", "method": "VideoLibrary.SetEpisodeDetails", "params": {"episodeid" : %s, "playcount" : 1 }, "id": 1 }' % str(self.DBID)

            control.jsonrpc(rpc) ; control.refresh()
        except:
            pass


    def idleForPlayback(self):
        for i in range(0, 200):
            if control.condVisibility('Window.IsActive(busydialog)') == 1: control.idle()
            else: break
            control.sleep(100)

    # Kodi 17 relevant, broken in Kodi 18
    # TODO: Remove when Kodi 18 is in stable
    def onPlayBackStarted(self):
        control.execute('Dialog.Close(all,true)')
        if not self.offset == '0': self.seekTime(float(self.offset))
        subtitles().get(self.name, self.imdb, self.season, self.episode)
        self.idleForPlayback()
        kodiVersion = int(xbmc.getInfoLabel("System.BuildVersion")[:2])
        if kodiVersion > 17:
            return
        self.play_next_triggered = False
        self.upnext_Trigger()
        
    # Exposed by kodi core in v18 when a video starts playing 
    # https://forum.kodi.tv/showthread.php?tid=334929
    def onAVStarted(self):
        xbmc.sleep(1000)
        control.execute('Dialog.Close(all,true)')
        if not self.offset == '0': self.seekTime(float(self.offset))
        subtitles().get(self.name, self.imdb, self.season, self.episode)
        self.idleForPlayback()
        kodiVersion = int(xbmc.getInfoLabel("System.BuildVersion")[:2])
        if kodiVersion > 17:
            return
        self.play_next_triggered = False
        self.upnext_Trigger()
        
    def onPlayBackStopped(self):
        playList = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        playList.clear()
        self.play_next_triggered = False
        bookmarks().reset(self.currentTime, self.totalTime, self.name, self.year)
        if control.setting('crefresh') == 'true':
            xbmc.executebuiltin('Container.Refresh')

        try:
            if (self.currentTime / self.totalTime) >= .90:
                self.libForPlayback()
        except: pass

    def onPlayBackEnded(self):
        self.play_next_triggered = False
        self.libForPlayback()
        self.onPlayBackStopped()
        if control.setting('crefresh') == 'true':
            xbmc.executebuiltin('Container.Refresh')

    def upnext_Trigger(self):
        self.media_length = self.getTotalTime()
        print(self.content)
        if self.content == 'episode':
            source_id = 'plugin.video.lastship'
            return_id = 'plugin.video.lastship_play_action'
            try:
                next_info = self.next_info()
                AddonSignals.sendSignal('upnext_data', next_info, source_id=source_id)
                AddonSignals.registerSlot('upnextprovider', return_id, self.signals_callback)
            except:
                import traceback
                traceback.print_exc()
                pass
                    
    def signals_callback(self, data):
        if not self.play_next_triggered:
            self.play_next_triggered = True
            # Using a seek here as playnext causes Kodi gui to wig out. So we seek instead so it looks more graceful
            self.seekTime(self.media_length)
                    
    def next_info(self):
        current_episode = {}
        current_episode["episodeid"] = self.tvdb
        current_episode["tvshowid"] = self.imdb
        current_episode["title"] = self.title
        current_episode["art"] = {}
        current_episode["art"]["tvshow.poster"] = self.meta['poster']
        current_episode["art"]["thumb"] = self.meta['thumb']
        current_episode["art"]["tvshow.fanart"] = self.meta['thumb']
        current_episode["art"]["tvshow.landscape"] = ''
        current_episode["art"]["tvshow.clearart"] = ''
        current_episode["art"]["tvshow.clearlogo"] = ''
        current_episode["plot"] = self.meta['plot']
        current_episode["showtitle"] = self.meta['tvshowtitle']
        current_episode["playcount"] = 0
        current_episode["season"] = self.season
        current_episode["episode"] = self.episode
        current_episode["rating"] = self.meta['rating']
        current_episode["firstaired"] = self.meta['premiered']
        
        playList = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)        
        current_position = playList.getposition()
        url = playList[current_position + 1].getPath()
        params = dict(parse_qsl(url.replace('?','')))
        next_info = json.loads(params.get('meta'))
        
        next_episode = {}
        next_episode["episodeid"] = next_info['thumb']
        next_episode["tvshowid"] = next_info['imdb']
        next_episode["title"] = next_info['title']
        next_episode["art"] = {}
        next_episode["art"]["tvshow.poster"] = next_info['poster']
        next_episode["art"]["thumb"] = next_info['thumb']
        next_episode["art"]["tvshow.fanart"] = next_info['fanart']
        next_episode["art"]["tvshow.landscape"] = next_info['banner']
        next_episode["art"]["tvshow.clearart"] = ''
        next_episode["art"]["tvshow.clearlogo"] = ''
        next_episode["plot"] = next_info["plot"]
        next_episode["showtitle"] = next_info['tvshowtitle']
        next_episode["playcount"] = 0
        next_episode["season"] = next_info['season']
        next_episode["episode"] = next_info['episode']
        next_episode["rating"] = next_info['rating']
        next_episode["firstaired"] = next_info['premiered']
        
        play_info = {}
        play_info["item_id"] = current_episode['episodeid']
        
        next_info = {
            "current_episode": current_episode,
            "next_episode": next_episode,
            "play_info": play_info,
            "notification_time": int(90)
            # "notification_time": int(IN DIE LASTSHIP EINSTELLUNGEN EINBAUEN?)
        }

        return next_info


class subtitles:
    def get(self, name, imdb, season, episode):
        try:
            if not control.setting('subtitles') == 'true': raise Exception()

            langDict = {'Afrikaans': 'afr', 'Albanian': 'alb', 'Arabic': 'ara', 'Armenian': 'arm', 'Basque': 'baq', 'Bengali': 'ben', 'Bosnian': 'bos', 'Breton': 'bre', 'Bulgarian': 'bul', 'Burmese': 'bur', 'Catalan': 'cat', 'Chinese': 'chi', 'Croatian': 'hrv', 'Czech': 'cze', 'Danish': 'dan', 'Dutch': 'dut', 'English': 'eng', 'Esperanto': 'epo', 'Estonian': 'est', 'Finnish': 'fin', 'French': 'fre', 'Galician': 'glg', 'Georgian': 'geo', 'German': 'ger', 'Greek': 'ell', 'Hebrew': 'heb', 'Hindi': 'hin', 'Hungarian': 'hun', 'Icelandic': 'ice', 'Indonesian': 'ind', 'Italian': 'ita', 'Japanese': 'jpn', 'Kazakh': 'kaz', 'Khmer': 'khm', 'Korean': 'kor', 'Latvian': 'lav', 'Lithuanian': 'lit', 'Luxembourgish': 'ltz', 'Macedonian': 'mac', 'Malay': 'may', 'Malayalam': 'mal', 'Manipuri': 'mni', 'Mongolian': 'mon', 'Montenegrin': 'mne', 'Norwegian': 'nor', 'Occitan': 'oci', 'Persian': 'per', 'Polish': 'pol', 'Portuguese': 'por,pob', 'Portuguese(Brazil)': 'pob,por', 'Romanian': 'rum', 'Russian': 'rus', 'Serbian': 'scc', 'Sinhalese': 'sin', 'Slovak': 'slo', 'Slovenian': 'slv', 'Spanish': 'spa', 'Swahili': 'swa', 'Swedish': 'swe', 'Syriac': 'syr', 'Tagalog': 'tgl', 'Tamil': 'tam', 'Telugu': 'tel', 'Thai': 'tha', 'Turkish': 'tur', 'Ukrainian': 'ukr', 'Urdu': 'urd'}

            codePageDict = {'ara': 'cp1256', 'ar': 'cp1256', 'ell': 'cp1253', 'el': 'cp1253', 'heb': 'cp1255', 'he': 'cp1255', 'tur': 'cp1254', 'tr': 'cp1254', 'rus': 'cp1251', 'ru': 'cp1251'}

            quality = ['bluray', 'hdrip', 'brrip', 'bdrip', 'dvdrip', 'webrip', 'hdtv']


            langs = []
            try:
                try: langs = langDict[control.setting('subtitles.lang.1')].split(',')
                except: langs.append(langDict[control.setting('subtitles.lang.1')])
            except: pass
            try:
                try: langs = langs + langDict[control.setting('subtitles.lang.2')].split(',')
                except: langs.append(langDict[control.setting('subtitles.lang.2')])
            except: pass

            try: subLang = xbmc.Player().getSubtitles()
            except: subLang = ''
            if subLang == langs[0]: raise Exception()

            server = xmlrpclib.Server('http://api.opensubtitles.org/xml-rpc', verbose=0)
            token = server.LogIn('', '', 'en', 'XBMC_Subtitles_v1')['token']

            sublanguageid = ','.join(langs) ; imdbid = re.sub('[^0-9]', '', imdb)

            if not (season == None or episode == None):
                result = server.SearchSubtitles(token, [{'sublanguageid': sublanguageid, 'imdbid': imdbid, 'season': season, 'episode': episode}])['data']
                fmt = ['hdtv']
            else:
                result = server.SearchSubtitles(token, [{'sublanguageid': sublanguageid, 'imdbid': imdbid}])['data']
                try: vidPath = xbmc.Player().getPlayingFile()
                except: vidPath = ''
                fmt = re.split('\.|\(|\)|\[|\]|\s|\-', vidPath)
                fmt = [i.lower() for i in fmt]
                fmt = [i for i in fmt if i in quality]

            filter = []
            result = [i for i in result if i['SubSumCD'] == '1']

            for lang in langs:
                filter += [i for i in result if i['SubLanguageID'] == lang and any(x in i['MovieReleaseName'].lower() for x in fmt)]
                filter += [i for i in result if i['SubLanguageID'] == lang and any(x in i['MovieReleaseName'].lower() for x in quality)]
                filter += [i for i in result if i['SubLanguageID'] == lang]

            try: lang = xbmc.convertLanguage(filter[0]['SubLanguageID'], xbmc.ISO_639_1)
            except: lang = filter[0]['SubLanguageID']

            content = [filter[0]['IDSubtitleFile'],]
            content = server.DownloadSubtitles(token, content)
            content = base64.b64decode(content['data'][0]['data'])
            content = gzip.GzipFile(fileobj=StringIO.StringIO(content)).read()

            subtitle = xbmc.translatePath('special://temp/')
            subtitle = os.path.join(subtitle, 'TemporarySubs.%s.srt' % lang)

            codepage = codePageDict.get(lang, '')
            if codepage and control.setting('subtitles.utf') == 'true':
                try:
                    content_encoded = codecs.decode(content, codepage)
                    content = codecs.encode(content_encoded, 'utf-8')
                except:
                    pass

            file = control.openFile(subtitle, 'w')
            file.write(str(content))
            file.close()

            xbmc.sleep(1000)
            xbmc.Player().setSubtitles(subtitle)
        except:
            pass


class bookmarks:
    def get(self, name, season, episode, imdb, year='0'):
        offset = '0'

        if control.setting('bookmarks') == 'true':
            if control.setting('bookmarks.trakt') == 'true':
                try:
                    from resources.lib.modules import trakt

                    if not episode is None:

                        # Looking for a Episode progress

                        traktInfo = trakt.getTraktAsJson('https://api.trakt.tv/sync/playback/episodes?extended=full')
                        for i in traktInfo:
                            if imdb == i['show']['ids']['imdb']:
                                # Checking Episode Number
                                if int(season) == i['episode']['season'] and int(episode) == i['episode']['number']:
                                    # Calculating Offset to seconds
                                    offset = (float(i['progress'] / 100) * int(i['episode']['runtime']) * 60)
                    else:

                        # Looking for a Movie Progress
                        traktInfo = trakt.getTraktAsJson('https://api.trakt.tv/sync/playback/episodes?extended=full')
                        for i in traktInfo:
                            if imdb == i['movie']['ids']['imdb']:
                                # Calculating Offset to seconds
                                offset = (float(i['progress'] / 100) * int(i['movie']['runtime']) * 60)

                    if offset == '0': raise Exception()

                    if control.setting('bookmarks.auto') == 'false':
                        try:
                            yes = control.dialog.contextmenu(["Fortsetzen", "Vom Anfang abspielen", ])
                        except:
                            yes = control.yesnoDialog("Fortsetzen", '', '', str(name), "Fortsetzen",
                                                      "Vom Anfang abspielen")
                        if yes: offset = '0'

                    return offset

                except:
                    return '0'
            else:
                try:
                    offset = '0'

                    if not control.setting('bookmarks') == 'true': raise Exception()

                    idFile = hashlib.md5()
                    for i in name: idFile.update(str(i))
                    for i in year: idFile.update(str(i))
                    idFile = str(idFile.hexdigest())

                    dbcon = database.connect(control.bookmarksFile)
                    dbcur = dbcon.cursor()
                    dbcur.execute("SELECT * FROM bookmark WHERE idFile = '%s'" % idFile)
                    match = dbcur.fetchone()
                    self.offset = str(match[1])
                    dbcon.commit()
                    if self.offset == '0': raise Exception()

                    minutes, seconds = divmod(float(self.offset), 60);
                    hours, minutes = divmod(minutes, 60)
                    label = '%02d:%02d:%02d' % (hours, minutes, seconds)
                    label = "Fortsetzen ab: %s" % label

                    if control.setting('bookmarks.auto') == 'false':

                        try:
                            yes = control.dialog.contextmenu([label, "Vom Anfang abspielen", ])
                        except:
                            yes = control.yesnoDialog(label, '', '', str(name), "Fortsetzen",
                                                      "Vom Anfang abspielen")
                        if yes: self.offset = '0'

                    return self.offset
                except:
                    return offset
        else:
            return offset


    def reset(self, currentTime, totalTime, name, year='0'):
        try:
            if not control.setting('bookmarks') == 'true': raise Exception()

            timeInSeconds = str(currentTime)
            ok = int(currentTime) > 180 and (currentTime / totalTime) <= .92

            idFile = hashlib.md5()
            for i in name: idFile.update(str(i))
            for i in year: idFile.update(str(i))
            idFile = str(idFile.hexdigest())
            control.makeFile(control.dataPath)
            dbcon = database.connect(control.bookmarksFile)
            dbcur = dbcon.cursor()
            dbcur.execute("CREATE TABLE IF NOT EXISTS bookmark (""idFile TEXT, ""timeInSeconds TEXT, ""UNIQUE(idFile)"");")
            dbcur.execute("DELETE FROM bookmark WHERE idFile = '%s'" % idFile)
            if ok: dbcur.execute("INSERT INTO bookmark Values (?, ?)", (idFile, timeInSeconds))
            dbcon.commit()
        except:
            pass
