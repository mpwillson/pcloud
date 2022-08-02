# NAME
playlist.py: Convert local .m3u playlists into pCloud playlists.

# SYNOPSIS
```
 python playlist.py [common_options]
                    [--cache-file cache-file] [--create-cache]
                    [--dir playlist_dir]
                    [--list] [--music-folder music-folder]
                    [--music-types suffix[,suffix] ...]
                    [--prefix playlist-prefix]
                    [--chunk-size chunk-size]
                    [m3u_playlist ...]
```

# DESCRIPTION

Converts m3u format playlists held locally into pCloud format playlists.

The big assumption `playlist.py` makes is that the music files on pCloud
and those held locally are a mirrored structure.  If that is not the
case, `playlist.py` won't work too well.

The pCloud music player doesn't understand m3u playlists (as far as I
can tell). `playlist.py` uses the contents of local m3u playlists and
writes them to pCloud as playlist collections. The pCloud playlist is
named as the local playlist (shorn of any path information). The music
files listed in the m3u files MUST exist on pCloud, with the same
directory structure as the local music collection. This is because
pCloud identifies files in a playlist collection by a unique number
(fileid), not pathname. These fileids can only be located if the local
and pCloud pathnames are identical.

`playlist.py` must therefore download a description of the pCloud
music collection (by default assumed to be under /Music). To avoid
this download every time a pCloud playlist is created, the description
can be cached in a local file (it's in JSON format). This will be out
of date if new music is uploaded, of course. The cache can be
refreshed by use of the **--create-cache** option. If the pCloud
music collection is small, efficiency gains will likely be too small
to notice.

If a pCloud playlist already exists, it will be deleted before the
upload of a new copy.

`playlist.py` will logon to pCloud to upload the playlist
collections. For the first connection, a username and password must be
provided. The username can be set in the configuration file
(`~/.config/pcloud.json`). However, the program will prompt for the
password (not echoed). Once the initial authentication takes place,
the auth token returned by pCloud is stored in the configuration
file. The token will be used if it exists and has not expired. Further
uses of `playlist.py` will not require authentication, until the auth
token expires.

# OPTIONS

These are the options supported by `playlist.py` in addition to the
pcloud common options, Options may be abbreviated to the shortest
unambiguous string.

`--cache-file cache-file`
: Reads music file data from **cache-file**. If not specified, music file
  data will be read from the pCloud /Music folder. Using a
  **cache-file** will reduce network traffic for extensive music
  collections. If the **cache-file** does not exist, it will be
  created by downloading music data from the pCloud **music-folder**.

`--chunk-size chunk-size`
: Sets the number of pCloud fileids to be uploaded to a playlist in
  a single transaction. Default is 100.

`--create-cache`
: Recreates music file data, read from the pCloud **music-folder**
  folder, into **cache-file**. Use **--create-cache** if the pCloud music
  collection has been updated since the last time the cache was
  created.

`--dir playlist-dir`
: Set location for local m3u playlist files. Default is the empty string.

`--list`
: List the existing pCloud playlists on stdout. No other
  action will be performed.

`--music-folder music-folder`
: Set music folder name on pCloud.  Default is `/Music`. This option
  implies **--create-cache**, as the **cache-file** will need to be
  re-created.

`--music-types suffix[,suffix] ...`
: Set recognised music file suffixes, as a comma separated list.  By
  default, recognised music files are those with one of the following
  suffixes: .mp3, .m4a, .flac or .alac.

`--prefix playlist-prefix`
: Set the location of the local music files, i.e. the common prefix for
  music files in m3u playlists. It is assumed that the directory
  hierarchy under **playlist-prefix** is the same as
  **music-folder**. The default is the empty string.

# CONFIGURATION

The default configuration file is `~/.config/pcloud.json`.
`playlist.py` holds specific configuration details in the "playlist"
component of the **config-file**. An example follows:

``` json
{
  "endpoint": "https://eapi.pcloud.com",
  "username": "user@example.com",
  "verbose": true,
  "playlist": {
    "cache-file": "~/.cache/pcloud/playlist.cache",
    "chunk-size": 100,
    "music-folder": "/Music",
    "music-types": [".aac", ".flac"],
    "dir": "/rep/music/playlists",
    "prefix": "/rep/music"
  }
}

```

Command line options can be made permanent by editing the appropriate
values in the **config-file**.

# NOTES

pCloud collections consist of a name, a type (1 for playlists) and a
set of file identifiers (fileids). Fileids can be provided at the time
of collection creation, or at a later time via the
collection_linkfiles call. `playlist.py` adds fileids to a collection
in **chunk-size** fileids at a time (default 100). Increasing this
value will reduce the number of transactions needed to create a
playlist.

# EXAMPLES

Create three playlists in pCloud from local m3u files:

    `python playlist.py jazz.m3u rock.m3u party1.m3u`

List existing pCloud playlist collections:

    `python playlist.py --list`

Create a cache file for future use:

    `python playlist.py --cache-file folder.json poetry.m3u`

Re-create a cache file:

    `python playlist.py --create-cache -cache-file folder.json`
