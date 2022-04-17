#!/usr/bin/env python
'''
# NAME
  pc_playlist.py: Convert local .m3u playlists into pCloud playlists.

# SYNOPSIS
  python pc_playlist.py [common_options]
                        [--cache-file cache-file] [--create-cache]
                        [--dir playlist-dir]
                        [--list] [--music-folder music-folder]
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

def walk(folder, root, fileid):
    '''Recursively walk the pCloud directory structure.

    folder contains music data structure.  root is current location in
    folder. fileid is a dictionary to be updated with a mapping of mp3
    file pathname to fileid.

    '''
    for entry in folder:
        name = entry['name']
        if name.endswith('.mp3'):
            fileid[f'{root}/{name}'] = entry['fileid']
        if 'contents' in entry:
            walk(entry['contents'], f'{root}/{name}', fileid)
    return

def mp3_dict(root_folder):
    '''Walks pCloud root Music folder.

    mp3 pathnames are stripped of the root directory (e.g. /Music)
    Returns dictionary of mp3 files keyed on name, value is fileid.
    '''
    fileid = dict()
    walk(root_folder, '', fileid)
    return fileid

def read_m3u_file(filename, remove='/rep/music'):
    '''Return list of mp3 pathnames from m3u filename.  The prefix
    identified by remove is stripped from each mp3 pathname.
    '''
    with open(filename) as f:
        lines = f.readlines()
    return [line.replace(remove, '').strip()  for line in lines]

def create_playlist(pcloud, name, ids, chunk_size=100):
    '''Create pCloud playlist.

    name contains the playlist name, while tracks are identified by
    the list ids. chunk-size controls how many fileids are uploaded in
    each call to the pCloud API.
    '''
    chunk_ids, next_ids = pcloudapi.chunked(ids, chunk_size)
    result = pcloud.collection_create(name, chunk_ids)
    coll_id = result['collection']['id']
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
    for coll in pcloud_playlist['collections']:
        pcloud_dict[coll['name']] = coll['id']
    return pcloud_dict

def upload_playlists(pcloud, fileids, files, dir, m3u_prefix,
                     chunk_size, verbose):
    '''Convert and upload local m3u playlists to pCloud playlists.'''
    # get existing pCloud playlists dict (name => fileid)
    pcloud_playlists = pcloud_playlist_names(pcloud)
    for file in files:
        if dir: file = f'{dir}/{file}'
        file =  os.path.expanduser(os.path.expandvars(file))
        if not os.path.exists(file):
            pcloudapi.error(f'playlist file does not exist: {file}',die=False)
            continue
        m3u = read_m3u_file(file,remove=m3u_prefix)
        pcloud_name = os.path.basename(file).replace('.m3u', '')
        if pcloud_name in pcloud_playlists:
            pcloud.collection_delete(pcloud_playlists[pcloud_name])
            time.sleep(1)
        try:
            ids = [fileids[track] for track in m3u]
        except KeyError as err:
            pcloudapi.error(f'playlist track not found on pCloud '
                            f'(stale cache?): {err}')
        if verbose:
            print(f'Creating playlist {pcloud_name} ... ', end='')
            sys.stdout.flush()
        nchunks = create_playlist(pcloud, urllib.parse.quote(pcloud_name), ids,
                                  chunk_size=chunk_size)
        if verbose: print(f'done using {nchunks} chunks.')
    return

def validate_config(cmd_config, config):
    playlist = cmd_config['playlist']

    # if music-folder provided on command line, any existing cache must
    # be re-created.
    if playlist['music-folder'] != config['playlist']['music-folder'] and \
       playlist['cache-file']:
        playlist['create_cache'] = True

    # validate config
    if 'create_cache' in playlist and not \
       playlist['cache-file']:
        pcloudapi.error('cache file name must be provided for create')

    chunk_size = int(playlist['chunk-size'])
    # more than 300 fileids seems to cause "Remote end closed
    # connection without response"
    if chunk_size <= 0 or chunk_size > 300:
        pcloudapi.error(f'invalid chunk size specified: {chunk_size}')
    playlist['chunk-size'] = chunk_size

    return

def list_playlists(pcloud):
    playlists = pcloud_playlist_names(pcloud)
    for name in playlists.keys():
        print(name)
    return

def process_playlists(pcloud, pl_config, verbose, pl_files):
    cache_file =  os.path.expanduser(
        os.path.expandvars(pl_config['cache-file']))
    create_cache = 'create-cache' in pl_config
    chunk_size = pl_config['chunk-size']
    music_folder = pl_config['music-folder']
    dir = pl_config['dir']
    prefix = pl_config['prefix']

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

    try:
        fileids = mp3_dict(folder['metadata']['contents'])
    except KeyError as err:
        pcloudapi.error(f'unable to decode music_folder; corrupt cache?')

    upload_playlists(pcloud, fileids, pl_files, dir, prefix, chunk_size,
                     verbose)
    return

def main():
    # default playlist options
    playlist = {
        'cache-file': '',
        'chunk-size': 100,
        'music-folder': '/Music',
        'dir': '',
        'prefix': ''}
    aspect_key = 'playlist'
    aspect_opts = [opt+'=' for opt in playlist.keys()] + \
        ['create-cache','list']

    pcloud = pcloudapi.PCloud(aspect_key, playlist)
    config, args = pcloudapi.merge_command_options(pcloud.config, aspect_key,
                                                   aspect_opts)
    validate_config(config, pcloud.config)

    try:
        pcloud.authenticate('reauth' in config)
        if 'list' in config[aspect_key]:
            list_playlists(pcloud)
        else:
            process_playlists(pcloud, config[aspect_key], config['verbose'],
                              args)
    except pcloudapi.PCloudException as err:
        pcloudapi.error(f'error: {err.code}; message: {err.msg}\n'\
                        f'Url: {err.url}')
    return

if __name__ == '__main__':
    main()
