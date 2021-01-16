from mopidy import backend
from mopidy_youtubemusic import logger
from mopidy.models import Ref, Playlist

class YoutubeMusicPlaylistsProvider(backend.PlaylistsProvider):
    def as_list(self):
        logger.debug("YoutubeMusic getting user playlists")
        refs = []
        try:
            playlists = self.backend.api.get_library_playlists(limit=100)
        except Exception:
            logger.exception("YoutubeMusic failed getting a list of playlists")
            playlists = []
        for pls in playlists:
            refs.append(Ref.playlist(
                uri=f"youtubemusic:playlist:{pls['playlistId']}", name=pls["title"],
            ))
        return refs

    def lookup(self, uri):
        bId = parse_uri(uri)
        logger.debug("YoutubeMusic looking up playlist \"%s\"", bId)
        try:
            pls = self.backend.api.get_playlist(bId, limit=self.backend.playlist_item_limit)
        except Exception:
            logger.exception("YoutubeMusic playlist lookup failed")
            pls = None
        if pls:
            tracks = self.backend.library.playlistToTracks(pls)
            return Playlist(
                uri=f"youtubemusic:playlist:{pls['id']}",
                name=pls["title"],
                tracks=tracks,
                last_modified=None,
            )

    def get_items(self, uri):
        bId = parse_uri(uri)
        logger.debug("YoutubeMusic getting playlist items for \"%s\"", bId)
        try:
            pls = self.backend.api.get_playlist(bId, limit=self.backend.playlist_item_limit)
        except Exception:
            logger.exception("YoutubeMusic failed getting playlist items")
            pls = None
        if pls:
            tracks = self.backend.library.playlistToTracks(pls)
            return [ Ref.track(uri=t.uri, name=t.name) for t in tracks ]
        return None

    def create(self, name):
        logger.debug("YoutubeMusic creating playlist \"%s\"", name)
        try:
            bId = self.backend.api.create_playlist(name, "")
        except Exception:
            logger.exception("YoutubeMusic playlist creation failed")
            bId = None
        if bId:
            uri = f"youtubemusic:playlist:{bId}"
            logger.debug("YoutubeMusic created playlist \"%s\"", uri)
            return Playlist(
                uri=uri,
                name=name,
                tracks=[],
                last_modified=None,
            )
        return None

    def delete(self, uri):
        logger.debug("YoutubeMusic deleting playlist \"%s\"", uri)
        bId = parse_uri(uri)
        try:
            self.backend.api.delete_playlist(bId)
            return True
        except Exception:
            logger.exception("YoutubeMusic failed to delete playlist")
            return False

    def refresh(self):
        pass

    def save(self, playlist):
        bId = parse_uri(playlist.uri)
        logger.debug("YoutubeMusic saving playlist \"%s\" \"%s\"", playlist.name, bId)
        try:
            pls = self.backend.api.get_playlist(bId, limit=self.backend.playlist_item_limit)
        except Exception:
            logger.exception("YoutubeMusic saving playlist failed")
            return None
        oldIds = set([t["videoId"] for t in pls["tracks"]])
        newIds = set([parse_uri(p.uri)[0] for p in playlist.tracks])
        common = oldIds & newIds
        remove = oldIds ^ common
        add = newIds ^ common
        if len(remove):
            logger.debug("YoutubeMusic removing items \"%s\" from playlist", remove)
            try:
                videos = [t for t in pls["tracks"] if t["videoId"] in remove]
                self.backend.api.remove_playlist_items(bId, videos)
            except Exception:
                logger.exception("YoutubeMusic failed removing items from playlist")
        if len(add):
            logger.debug("YoutubeMusic adding items \"%s\" to playlist", add)
            try:
                self.backend.api.add_playlist_items(bId, list(add))
            except Exception:
                logger.exception("YoutubeMusic failed adding items to playlist")
        if pls["title"] != playlist.name:
            logger.debug("Renaming playlist to \"%s\"", playlist.name)
            try:
                self.backend.api.edit_playlist(bId, title=playlist.name)
            except Exception:
                logger.exception("YoutubeMusic failed renaming playlist")
        return playlist

def parse_uri(uri):
    return(uri.split(':')[2])