import pykka
import requests
import json
import re
import random
import time
import hashlib

from urllib.parse import parse_qs
from mopidy import backend
from mopidy_youtubemusic import logger
from ytmusicapi.ytmusic import YTMusic
from ytmusicapi.parsers.utils import nav, get_continuations, CAROUSEL_TITLE, TITLE, TITLE_TEXT, NAVIGATION_BROWSE_ID, SINGLE_COLUMN_TAB, SECTION_LIST

from .repeating_timer import RepeatingTimer
from .scrobble_fe import YoutubeMusicScrobbleListener
from .playback import YoutubeMusicPlaybackProvider
from .library import YoutubeMusicLibraryProvider
from .playlist import YoutubeMusicPlaylistsProvider


class YoutubeMusicBackend(pykka.ThreadingActor, backend.Backend, YoutubeMusicScrobbleListener):
    def __init__(self, config, audio):
        super().__init__()
        self.config = config
        self.audio = audio
        self.uri_schemes = ["youtubemusic"]
        self.auth = False

        self._auto_playlist_refresh_rate = config["youtubemusic"]["auto_playlist_refresh"] * 60
        self._auto_playlist_refresh_timer = None

        self._youtube_player_refresh_rate = config["youtubemusic"]["youtube_player_refresh"] * 60
        self._youtube_player_refresh_timer = None

        self.playlist_item_limit = config["youtubemusic"]["playlist_item_limit"]
        self.subscribed_artist_limit = config["youtubemusic"]["subscribed_artist_limit"]
        self.history = config["youtubemusic"]["enable_history"]
        self.liked_songs = config["youtubemusic"]["enable_liked_songs"]
        self.mood_genre = config["youtubemusic"]["enable_mood_genre"]
        self.stream_preference = config["youtubemusic"]["stream_preference"]

        self.api = None
        if config["youtubemusic"]["auth_json"]:
            self._ytmusicapi_auth_json = config["youtubemusic"]["auth_json"]
            self.auth = True

        self.playback = YoutubeMusicPlaybackProvider(audio=audio, backend=self)
        self.library = YoutubeMusicLibraryProvider(backend=self)
        if self.auth:
            self.playlists = YoutubeMusicPlaylistsProvider(backend=self)

    def on_start(self):
        if self.auth:
            self.api = YTMusic(self._ytmusicapi_auth_json)
        else:
            self.api = YTMusic()

        if self._auto_playlist_refresh_rate:
            self._auto_playlist_refresh_timer = RepeatingTimer(
                self._refresh_auto_playlists, self._auto_playlist_refresh_rate
            )
            self._auto_playlist_refresh_timer.start()

        self._youtube_player_refresh_timer = RepeatingTimer(
            self._refresh_youtube_player, self._youtube_player_refresh_rate
        )
        self._youtube_player_refresh_timer.start()

    def on_stop(self):
        if self._auto_playlist_refresh_timer:
            self._auto_playlist_refresh_timer.cancel()
            self._auto_playlist_refresh_timer = None
        if self._youtube_player_refresh_timer:
            self._youtube_player_refresh_timer.cancel()
            self._youtube_player_refresh_timer = None

    def _refresh_youtube_player(self):
        t0 = time.time()
        self.playback.Youtube_Player_URL = self._get_youtube_player()
        t = time.time() - t0
        logger.debug("Youtube Player URL refreshed in %.2fs", t)

    def _get_youtube_player(self):
        # Refresh our js player URL so YDL can decode the signature correctly.
        response = requests.get('https://music.youtube.com', headers=self.api.headers, proxies=self.api.proxies)
        m = re.search(r'jsUrl"\s*:\s*"([^"]+)"', response.text)
        if m:
            url = m.group(1)
            logger.debug('YoutubeMusic updated player URL to %s', url)
            return(url)
        else:
            logger.error('YoutubeMusic unable to extract player URL.')
            return(None)

    def _refresh_auto_playlists(self):
        t0 = time.time()
        self._get_auto_playlists()
        t = time.time() - t0
        logger.debug("YoutubeMusic Auto Playlists refreshed in %.2fs", t)

    def _get_auto_playlists(self):
        try:
            logger.debug('YoutubeMusic loading auto playlists')
            response = self.api._send_request('browse', {})
            tab = nav(response, SINGLE_COLUMN_TAB)
            browse = parse_auto_playlists(nav(tab, SECTION_LIST))
            if 'continuations' in tab['sectionListRenderer']:
                request_func = lambda additionalParams: self.api._send_request('browse', {}, additionalParams)
                parse_func = lambda contents: parse_auto_playlists(contents)
                browse.extend(get_continuations(tab['sectionListRenderer'], 'sectionListContinuation', 100, request_func, parse_func))
            # Delete empty sections
            for i in range(len(browse) - 1, 0, -1):
                if len(browse[i]['items']) == 0:
                    browse.pop(i)
            logger.debug('YoutubeMusic loaded %d auto playlists sections', len(browse))
            self.library.ytbrowse = browse
        except Exception:
            logger.exception('YoutubeMusic failed to load auto playlists')
        return(None)

    def scrobble_track(self, bId):
        # Called through YoutubeMusicScrobbleListener
        # Let YouTube Music know we're playing this track so it will be added to our history.
        endpoint = "https://www.youtube.com/get_video_info"
        params = {"video_id": bId, "hl": self.api.language, "el": "detailpage", "c": "WEB_REMIX", "cver": "0.1"}
        response = requests.get(endpoint, params, headers=self.api.headers, proxies=self.api.proxies)
        text = parse_qs(response.text)
        player_response = json.loads(text['player_response'][0])
        trackurl = re.sub(r'plid=', 'list=', player_response['playbackTracking']['videostatsPlaybackUrl']['baseUrl'])
        CPN_ALPHABET = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_'
        params = {
            'cpn': ''.join((CPN_ALPHABET[random.randint(0, 256) & 63] for _ in range(0, 16))),
            'referrer': "https://music.youtube.com",
            'cbr': text['cbr'][0],
            'cbrver': text['cbrver'][0],
            'c': text['c'][0],
            'cver': text['cver'][0],
            'cos': text['cos'][0],
            'cosver': text['cosver'][0],
            'cr': text['cr'][0],
            'ver': 2,
        }
        tr = requests.get(trackurl, params=params, headers=self.api.headers, proxies=self.api.proxies)
        logger.debug("%d code from '%s'", tr.status_code, tr.url)


def parse_auto_playlists(res):
    browse = []
    for sect in res:
        car = []
        if 'musicImmersiveCarouselShelfRenderer' in sect:
            car = nav(sect, ['musicImmersiveCarouselShelfRenderer'])
        elif 'musicCarouselShelfRenderer' in sect:
            car = nav(sect, ['musicCarouselShelfRenderer'])
        else:
            continue
        stitle = nav(car, CAROUSEL_TITLE + ['text']).strip()
        browse.append({'name': stitle, 'uri': 'youtubemusic: auto: ' + hashlib.md5(stitle.encode('utf-8')).hexdigest(), 'items': []})
        for item in nav(car, ['contents']):
            brId = nav(item, ['musicTwoRowItemRenderer'] + TITLE + NAVIGATION_BROWSE_ID, True)
            if brId is None or brId == 'VLLM':
                continue
            pagetype = nav(item, ['musicTwoRowItemRenderer', 'navigationEndpoint', 'browseEndpoint', 'browseEndpointContextSupportedConfigs', 'browseEndpointContextMusicConfig', 'pageType'], True)
            ititle = nav(item, ['musicTwoRowItemRenderer'] + TITLE_TEXT).strip()
            if pagetype == 'MUSIC_PAGE_TYPE_PLAYLIST':
                if 'subtitle' in item['musicTwoRowItemRenderer']:
                    ititle += ' ('
                    for st in item['musicTwoRowItemRenderer']['subtitle']['runs']:
                        ititle += st['text']
                    ititle += ')'
                browse[-1]['items'].append({'type': 'playlist', 'uri': f"youtubemusic: playlist: {brId}", 'name': ititle})
            elif pagetype == 'MUSIC_PAGE_TYPE_ARTIST':
                browse[-1]['items'].append({'type': 'artist', 'uri': f"youtubemusic: artist: {brId}", 'name': ititle + ' (Artist)'})
            elif pagetype == 'MUSIC_PAGE_TYPE_ALBUM':
                artist = nav(item, ['musicTwoRowItemRenderer', 'subtitle', 'runs', -1, 'text'], True)
                ctype = nav(item, ['musicTwoRowItemRenderer', 'subtitle', 'runs', 0, 'text'], True)
                if artist is not None:
                    browse[-1]['items'].append({'type': 'album', 'uri': f"youtubemusic: album: {brId}", 'name': artist + ' - ' + ititle + ' (' + ctype + ')'})
                else:
                    browse[-1]['items'].append({'type': 'album', 'uri': f"youtubemusic: album: {brId}", 'name': ititle + ' (' + ctype + ')'})
    return(browse)
