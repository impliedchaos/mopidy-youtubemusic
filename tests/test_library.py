import unittest

from mopidy.models import Ref
from mopidy_youtubemusic import backend as backend_lib

from tests.test_extension import ExtensionTest

class LibraryTest(unittest.TestCase):
        def setUp(self):
            cfg = ExtensionTest.get_config()
            self.backend = backend_lib.YoutubeMusicBackend(config=cfg,audio=None)
        
        def test_browse_none(self):
            refs = self.backend.library.browse(None)
            assert refs == []
        
        def test_browse_root(self):
            refs = self.backend.library.browse('youtubemusic:root')
            found = False
            for ref in refs:
                if ref.uri == "youtubemusic:watch":
                    found = True
                    break
            assert found, "ref 'youtubemusic:watch' not found"
            found = False
            for ref in refs:
                if ref.uri == "youtubemusic:mood":
                    found = True
                    break
            assert found, "ref 'youtubemusic:mood' not found"
            found = False
            for ref in refs:
                if ref.uri == "youtubemusic:auto":
                    found = True
                    break
            assert found, "ref 'youtubemusic:auto' not found"

        def test_browse_moods(self):
            refs = self.backend.library.browse('youtubemusic:mood')
            assert refs is not None