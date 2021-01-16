****************************
Mopidy-YoutubeMusic
****************************

.. image:: https://img.shields.io/pypi/v/Mopidy-YoutubeMusic
    :target: https://pypi.org/project/Mopidy-YoutubeMusic/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/github/commits-since/impliedchaos/mopidy-youtubemusic/latest
    :alt: commits since latest release
    :target: https://github.com/impliedchaos/mopidy-youtubemusic/commits

Mopidy extension for playing music from YouTube Music

Forked from `Mopidy-YTMusic <https://github.com/OzymandiasTheGreat/mopidy-ytmusic>`_ by `Tomas Ravinskas <https://github.com/OzymandiasTheGreat>`_.

Installation
============

Install by running::

    python3 -m pip install Mopidy-YoutubeMusic


Configuration
=============

Before starting Mopidy, you need to enable Mopidy-YoutubeMusic in your Mopidy configuration file::

    [youtubemusic]
    enabled = true

By default Mopidy-YoutubeMusic will connect to YouTube Music as a guest account.  This
has limited options.  If you would like to connect to YouTube Music with your
account (free or premium) you'll need to generate an :code:`auth.json` file and configure
Mopidy-YoutubeMusic to use it.

To create an auth.json file run :code:`mopidy youtubemusic setup` and follow instructions
in the terminal. When you're done it will tell you what config options (e.g. :code:`auth = /path/to/auth.json`)
you need to add to your Mopidy configuration file.

Authenticated users have access to their listening history, likes,
playlists and uploaded music.  Premium users have access to high quality audio
streams and other premium content. 

Other configuration options are as follows:

- :code:`auto_playlist_refresh` - time (in minutes) to refresh the Auto playlists.  Default: 60. Set to 0 to disable auto playlists.
- :code:`youtube_player_refresh` - time (in minutes) to refresh the Youtube player url (used for decoding the signature).  Default: 15
- :code:`playlist_item_limit` - Number of items to grab from playlists.  This is not exact.  Default: 100
- :code:`subscribed_artist_limit` - Number of subscriptions to list. Default: 100. Set to 0 to disable subscription list.
- :code:`enable_history` - Show Recently Played playlist. Default: yes
- :code:`enable_liked_songs` - Show Liked Songs playlist. Default: yes
- :code:`enable_mood_genre` - Show Mood & Genre playlists from YouTube Music's Explore directory. Default: yes
- :code:`enable_scrobbling` - Mark tracks as played on YouTube Music after listening.  Default: yes
- :code:`stream_preference` - Comma separated list of itags in the order of preference you want for stream.  Default: "141, 251, 140, 250, 249"

Information on YouTube Music streams:

+----------+-------+-------------+----------+
| itag     | Codec | Sample Rate | Bit Rate |
+==========+=======+=============+==========+
| 141 [*]_ | AAC   | 44.1kHz     | ~260kbps |
+----------+-------+-------------+----------+
| 251      | Opus  | 48kHz       | ~150kbps |
+----------+-------+-------------+----------+
| 140      | AAC   | 44.1kHz     | ~132kbps |
+----------+-------+-------------+----------+
| 250      | Opus  | 48kHz       | ~80kbps  |
+----------+-------+-------------+----------+
| 249      | Opus  | 48kHz       | ~64kbps  |
+----------+-------+-------------+----------+

.. [*] Available to premium accounts only.

Build for Local Install
=======================

1. Install `poetry <https://python-poetry.org/docs/#installation>`
2. Run :code:`poetry build` to create the build tarball
3. The :code:`dist/Mopidy-YoutubeMusic-x.x.x.tar.gz` file is what you'll use to install.
4. With pip: :code:`python3 -m pip install dist/Mopidy-YoutubeMusic-x.x.x.tar.gz` to install or reinstall over an existing version.
5. Do configuration stuff if you haven't already.  

Project resources
=================

- `Source code <https://github.com/impliedchaos/mopidy-youtubemusic>`_
- `Issue tracker <https://github.com/impliedchaos/mopidy-youtubemusic/issues>`_
- `Changelog <https://github.com/impliedchaos/mopidy-youtubemusic/blob/master/CHANGELOG.rst>`_


Credits
=======

- Original author: `Tomas Ravinskas <https://github.com/OzymandiasTheGreat>`__
- Current maintainer: `Dave Maez <https://github.com/impliedchaos>`__
- `Contributors <https://github.com/impliedchaos/mopidy-youtubemusic/graphs/contributors>`_
