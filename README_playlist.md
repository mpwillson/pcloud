# NAME
playlist.py: Convert local .m3u playlists into pCloud playlists.

# SYNOPSIS
 python playlist.py [-c cache_file] [-C] [-d playlist_dir]
                    [-e endpoint] [-f config_file]  [-l] [-m music_folder]
                    [-p playlist_prefix] [-s chunk_size] [-r]
                    [-u username] [-v]
                    [m3u_playlist ...]

# DESCRIPTION
Converts m3u format playlists held locally into pCloud format playlists.

The big assumption `playlist.py` makes is that the mp3 files on pCloud
and those held locally are a mirrored structure.  If that is not the
case, `playlist.py` won't work too well.

The pCloud music player doesn't understand m3u playlists (as far as I
can tell). `playlist.py` uses the contents of local m3u playlists and
writes them to pCloud as playlist collections. The pCloud playlist is
named as the local playlist (shorn of any path information). The music
files listed in the m3u files MUST exist on pCloud, with the same
directory structure as the local mp3 collection. This is because
pCloud identifies files in a playlist collection by a unique number
(fileid), not pathname. These fileids can only be located if the local
and pCloud pathnames are identical.

`playlist.py` must therefore download a description of the pCloud
music collection (by default assumed to be under /Music). To avoid
this download every time a pCloud playlist is created, the description
can be cached in a local file (it's in JSON format). This will be out
of date if new music is uploaded, of course. The cache can be
refereshed by use of the **-C** option. If the pCloud music collection
is small, efficiency gains will likely be too small to notice.

If a pCloud playlist already exists, it will be deleted before the
upload of a new copy.

`playlist.py` will logon to pCloud to upload the playlist
collections. For the first connection, a username and password must be
provided. The username can be set in the configuration file
(`/.config/pcloud.json`}. However, the program will prompt for the
password (not echoed). Once the initial authentication takes place,
the auth token returned by pCloud is stored in the configuration
file. The token will be used if it exists and has not expired. Further
uses of `playlist.py` will not required authentication.

# OPTIONS
-c cache_file
: Reads mp3 file data from **cache_file**. If not specified, mp3 file
  data will be read from the pCloud /Music folder. Using a
  **cache_file** will reduce network traffic for extensive music
  collections. If the **cache_file** does not exist, it will be
  created by downloading mp3 data from the pCloud **music_folder**.

-C
: Recreates mp3 file data, read from the pCloud **music_folder**
  folder, into **cache_file**. Use **-C** if the pCloud music
  collection has been updated since the last time the cache was
  created.

-d playlist_dir
: Set location for m3u playlist files. Default is './'.

-e endpoint
: Set endpoint for pCloud API.  Default is `https://eapi.pcloud.com`

-f config_file
: Set name of configuration file. The default is
  `~/.config/pcloud.json`. Configuration files are in JSON
  format. See CONFIGURATION, below.

-l
: Causes `playlist.py` to just list the existing pCloud playlists on
  stdout. No other action will be performed.

-m music_folder
: Set music folder name on pCloud.  Default is `/Music`. This option
  implies **-C**, as the **cache_file** will need to be re-created.

-p playlist_prefix
: Set the common prefix for mp3 files in playlists. It is assumed that
  the directory hierarchy under **playlist_prefix** is the same as
  **music_folder**. The default is ''.

-r
: Force login reauthentication. Specify this option if use of the
  existing authentication token produces a 'Login failed' message. The
  auth token may have been deleted from the pCloud server. A username
  (if not already provided in the **config_file**) and password will
  be requested. If a username is not present in the **config_file**,
  the one entered will be saved.

-s chunk_size
: Sets the number of pCloud fileids to be uploaded to a playlist in
  a single transaction. Default is 100.

-u username
: Set pCloud username. This value is required and defaults to ''.

-v
: Cause `playlist.py` to issue messages on its actions. Default is False.

# CONFIGURATION
The default configuration file is `./config/pcloud.json`. Here's an
example with all possible configuration options presented:

``` json
{
  "endpoint": "https://eapi.pcloud.com",
  "username": "user@example.com",
  "verbose": true,
  "playlist": {
    "cache_file": "~/.cache/pcloud/playlist.cache",
    "chunk_size": 100,
    "music_folder": "/Music",
    "playlist_dir": "/rep/music/playlists",
    "playlist_prefix": "/rep/music"
    }
  }

```
Authentication token details will be added to the configuration
file once a successful login is effected. Username and password will
not be requred again, until the authentication token expires (one
year).

The authentication details are held as:

``` json
"auth": {
  "token": "some random string",
  "expires": "Sat Mar 18 21:39:17 2023"
}
```

The configuration file location can be overridden by the **-f**
command option. Options provided on the command line override those
obtained from the configuration file.

# NOTES

`playlist.sh` is written in Python 3. Tested with versions 3.8 and
3.9.

pCloud collections consist of a name, a type (1 for playlists) and a
set of file identifiers (fileids). Fileids can be provided at the time
of collection creation, or at a later time via the
collection_linkfiles call. `playlist.py` adds fileids to a collection
in **chunk_size** fileids at a time (default 100). Increasing this
value will reduce the number of transactions needed to create a
playlist.

# EXAMPLES

Create three playlists in pCloud from local m3u files:
    `python playlist.py jazz.m3u rock.m3u party1.m3u`

List existing pCloud playlist collections:
    `python playlist.py -l`

Create a cache file for future use:
    `python playlist.py -c folder.json poetry.m3u`

Re-create a cache file:
    `python playlist.py -C -c folder.json`
