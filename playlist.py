#!/usr/bin/env python
'''
# NAME
  playlist.py: Convert local .m3u playlists into pCloud playlists.

# SYNOPSIS
  python playlist.py [common_options]
                     [--cache-file cache-file] [--create-cache]
                     [--dir playlist-dir]
                     [--list] [--music-folder music-folder]
                     [--music-types suffix[,suffix] ...]
                     [--prefix playlist-prefix] [--chunk-size chunk-size]
                     [m3u_playlist ...]

  See README_playlist.md for details.
'''
import sys
import os
import getopt
import urllib.parse
import pcloudapi
import time

class Key():
    ASPECT = 'playlist'
    CACHE_FILE = 'cache-file'
    CHUNK_SIZE = 'chunk-size'
    MUSIC_FOLDER = 'music-folder'
    MUSIC_TYPES =  'music-types'
    DIR = 'dir'
    PREFIX = 'prefix'
    CREATE_CACHE = 'create-cache'
    LIST = 'list'
    FILEID = 'fileid'
    CONTENTS = 'contents'
    METADATA = 'metadata'
    NAME = 'name'
    COLLECTION = 'collection'
    COLLECTIONS = 'collections'
    ID = 'id'
    PATH = 'path'

def walk(folder, root, fileid, types):
    '''Recursively walk the pCloud directory structure.

    folder contains music data structure.  root is current location in
    folder. fileid is a dictionary to be updated with a mapping of mp3
    file pathname to fileid. Types contains a list of recognised music
    suffixes.

    '''
    for entry in folder:
        name = entry[Key.NAME]
        if name.endswith(types):
            fileid[f'{root}/{name}'] = entry[Key.FILEID]
        if Key.CONTENTS in entry:
            walk(entry[Key.CONTENTS], f'{root}/{name}', fileid, types)
    return

def get_music_dict(root_folder, types):
    '''Walks pCloud root Music folder.

    music pathnames (those matching the suffixes in the types list)
    are stripped of the root directory (e.g. /Music) Returns
    dictionary of music files keyed on name, value is fileid.
    '''
    fileid = dict()
    walk(root_folder, '', fileid, tuple(types))
    return fileid

def read_m3u_file(filename, remove='/rep/music'):
    '''Return list of music file pathnames from m3u filename.
    The prefix identified by remove is stripped from each music file pathname.
    '''
    def make_abs(pathname):
        return pathname if pathname[0] == '/' else '/' + pathname

    with open(filename) as f:
        lines = f.readlines()
    return [make_abs(line.replace(remove, '').strip())  for line in lines]

def create_playlist(pcloud, name, ids):
    '''Create pCloud playlist.

    name contains the playlist name, while tracks are identified by
    the list ids. chunk-size controls how many fileids are uploaded in
    each call to the pCloud API.
    '''
    chunk_size = pcloud.config[Key.ASPECT][Key.CHUNK_SIZE]
    chunk_ids, next_ids = pcloudapi.chunked(ids, chunk_size)
    result = pcloud.collection_create(name, chunk_ids)
    coll_id = result[Key.COLLECTION][Key.ID]
    nchunks = 1
    while next_ids:
        chunk_ids, next_ids = pcloudapi.chunked(next_ids, chunk_size)
        result = pcloud.collection_linkfiles(coll_id, chunk_ids)
        # avoid "pCloud: internal error" by a small sleep?
        time.sleep(.25)
        nchunks += 1
    return nchunks

def pcloud_playlist_names(pcloud):
    '''Return dictionary mapping pCloud playlist colection names to their
    fileid.
    '''
    pcloud_dict = dict()
    pcloud_playlist = pcloud.collection_list()
    for coll in pcloud_playlist[Key.COLLECTIONS]:
        pcloud_dict[coll[Key.NAME]] = coll[Key.ID]
    return pcloud_dict

def upload_playlists(pcloud, fileids, files):
    '''Convert and upload local m3u playlists to pCloud playlists.'''
    chunk_size = pcloud.config[Key.ASPECT][Key.CHUNK_SIZE]
    m3u_prefix = pcloud.config[Key.ASPECT][Key.PREFIX]
    dir = pcloud.config[Key.ASPECT][Key.DIR]
    verbose = pcloud.config[pcloudapi.Key.VERBOSE]
    # get existing pCloud playlists dict (name => fileid)
    pcloud_playlists = pcloud_playlist_names(pcloud)
    for file in files:
        if dir: file = f'{dir}/{file}'
        file =  os.path.expanduser(os.path.expandvars(file))
        if not os.path.exists(file):
            pcloudapi.error(f'playlist file does not exist: {file}',die=False)
            continue
        pcloud_name = os.path.basename(file).replace('.m3u', '')
        if verbose:
            print(f'Creating playlist {pcloud_name} ... ', end='')
            sys.stdout.flush()
        m3u = read_m3u_file(file,remove=m3u_prefix)
        if pcloud_name in pcloud_playlists:
            pcloud.collection_delete(pcloud_playlists[pcloud_name])
            time.sleep(1)
        try:
            ids = [fileids[track] for track in m3u]
        except KeyError as err:
            pcloudapi.error(f'playlist track not found on pCloud '
                            f'(stale cache?): {err}')
        nchunks = create_playlist(pcloud, urllib.parse.quote(pcloud_name), ids)
        if verbose: print(f'done using {nchunks} chunks.')
    return

def validate_config(config):
    playlist = config[Key.ASPECT]

    if Key.CREATE_CACHE in playlist and not playlist[Key.CACHE_FILE]:
        pcloudapi.error('cache file name must be provided for create')

    chunk_size = int(playlist[Key.CHUNK_SIZE])
    # more than 300 fileids seems to cause "Remote end closed
    # connection without response"
    if chunk_size <= 0 or chunk_size > 300:
        pcloudapi.error(f'invalid chunk size specified: {chunk_size}')
    playlist[Key.CHUNK_SIZE] = chunk_size
    # convert command option string to list
    if isinstance(playlist[Key.MUSIC_TYPES], str):
        playlist[Key.MUSIC_TYPES] =  playlist[Key.MUSIC_TYPES].split(',')
    return

def list_playlists(pcloud):
    playlists = pcloud_playlist_names(pcloud)
    for name in sorted(playlists.keys()):
        print(name)
    return

def process_playlists(pcloud, pl_files):
    '''Create pCloud playlist file (collection) for each .m3u file in the
       list pl_files.
    '''

    pl_config = pcloud.config[Key.ASPECT]
    cache_file =  os.path.expanduser(
        os.path.expandvars(pl_config[Key.CACHE_FILE]))
    create_cache = Key.CREATE_CACHE in pl_config
    music_folder = pl_config[Key.MUSIC_FOLDER]
    verbose = pcloud.config[pcloudapi.Key.VERBOSE]

    if (cache_file and not os.path.exists(cache_file)) or \
       create_cache or not cache_file:
            if verbose: print('Loading music collection from pCloud ...')
            folder = pcloud.list_folder(path=music_folder)
            if create_cache or (cache_file and
                                not os.path.exists(cache_file)):
                pcloudapi.save_json(folder, cache_file)
                if verbose:
                    print(f'Cached music collection to {cache_file}')
    else:
        if verbose: print('Loading music collection from cache file ...')
        folder = pcloudapi.load_json(cache_file)
        if pl_config[Key.MUSIC_FOLDER] != folder[Key.METADATA][Key.PATH]:
            if verbose:
                print('Cache file doesn\'t match music-folder: loading '\
                      'music collection from pCloud ...')
            folder = pcloud.list_folder(path=music_folder)
    try:
        fileids = get_music_dict(folder[Key.METADATA][Key.CONTENTS],
                                 pl_config[Key.MUSIC_TYPES])
    except KeyError as err:
        pcloudapi.error(f'unable to decode music_folder; corrupt cache?')

    upload_playlists(pcloud, fileids, pl_files)
    return

def main():
    # default playlist options
    playlist = {
        Key.CACHE_FILE: '',
        Key.CHUNK_SIZE: 100,
        Key.MUSIC_FOLDER: '/Music',
        Key.MUSIC_TYPES: ['.mp3', '.m4a', '.flac', '.alac'],
        Key.DIR: '',
        Key.PREFIX: ''}

    aspect_opts = [opt+'=' for opt in playlist.keys()] + \
        [Key.CREATE_CACHE,Key.LIST]

    pcloud = pcloudapi.PCloud(Key.ASPECT, playlist)
    args = pcloud.merge_command_options(Key.ASPECT, aspect_opts)
    validate_config(pcloud.config)

    try:
        pcloud.authenticate()
        if Key.LIST in pcloud.config[Key.ASPECT]:
            list_playlists(pcloud)
        else:
            process_playlists(pcloud, args)
    except pcloudapi.PCloudException as err:
        pcloudapi.error(f'error: {err.code}; message: {err.msg}\n'\
                        f'Url: {err.url}')
    return

if __name__ == '__main__':
    main()
