#!/usr/bin/env python
'''
# NAME
  pc_playlist.py: Convert local .m3u playlists into pCloud playlists.

# SYNOPSIS
  python pc_playlist.py [-c cache_file] [-C] [-d playlist_dir]
                        [-e endpoint] [-f config_file]  [-l] [-m music_folder]
                        [-p playlist_prefix] [-s chunk_size] [-r]
                        [-u username] [-v]
                        [m3u_playlist ...]

  See README.md for details.
'''
import sys
import os
import getopt
import urllib.parse
import pcloudapi

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
    the list ids. chunk_size controls how many fileids are uploaded in
    each call to the pCloud API.
    '''
    chunk_ids, next_ids = pcloudapi.chunked(ids, chunk_size)
    result = pcloud.collection_create(name, chunk_ids)
    coll_id = result['collection']['id']
    nchunks = 1
    while next_ids:
        chunk_ids, next_ids = pcloudapi.chunked(next_ids, chunk_size)
        result = pcloud.collection_linkfiles(coll_id, chunk_ids)
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

def upload_playlists(pcloud, fileids, files, playlist_dir, m3u_prefix,
                     chunk_size, verbose):
    '''Convert and upload local m3u playlists to pCloud playlists.'''
    # get existing pCloud playlists dict (name => fileid)
    pcloud_playlists = pcloud_playlist_names(pcloud)
    for file in files:
        if playlist_dir: file = f'{playlist_dir}/{file}'
        file =  os.path.expanduser(os.path.expandvars(file))
        if not os.path.exists(file):
            pcloudapi.error(f'playlist file does not exist: {file}',die=False)
            continue
        m3u = read_m3u_file(file,remove=m3u_prefix)
        pcloud_name = os.path.basename(file).replace('.m3u', '')
        if pcloud_name in pcloud_playlists:
            pcloud.collection_delete(pcloud_playlists[pcloud_name])
        ids = [fileids[track] for track in m3u]
        if verbose:
            print(f'Creating playlist {pcloud_name} ... ', end='')
            sys.stdout.flush()
        nchunks = create_playlist(pcloud, urllib.parse.quote(pcloud_name), ids,
                                  chunk_size=chunk_size)
        if verbose: print(f'done using {nchunks} chunks.')
    return

def merge_config_options(config):
    '''Merge options from command line into configuration file.

    The config argument holds the default configuration dictionary. If
    no config file is specified as an option, the default config file
    is read. Return value is a tuple of the merged configuration
    dictionary and remaining command line arguments.
    '''
    cmd_config = pcloudapi.read_config(config, config['config_file'])
    playlist = cmd_config['playlist']
    try:
        opts,args = getopt.getopt(sys.argv[1:],'c:Cd:e:f:lm:p:rs:u:v')
        for o,v in opts:
            if o == '-c':
                playlist['cache_file'] = v
            elif o == '-C':
                playlist['create_cache_file'] = True
            elif o == '-d':
                playlist['playlist_dir'] = v
            elif o == '-e':
                cmd_config['endpoint'] = v
            elif o =='-f':
                cmd_config['config_file'] = v
                config = pcloudapi.read_config(config, v, optional=False)
            elif o =='-l':
                cmd_config['list_playlists'] = True
            elif o == '-m':
                # this will invalidate the cache; need to figure out
                # how to deal with
                playlist['music_folder'] = v
            elif o == '-p':
                playlist['playlist_prefix'] = v
            elif o == '-r':
                cmd_config['reauth'] = True
            elif o == '-s':
                playlist['chunk_size'] = int(v)
            elif o == '-u':
                cmd_config['username'] = v
            elif o == '-v':
                cmd_config['verbose'] = True
    except getopt.GetoptError as err:
        pcloudapi.error(f'unknown option: -{err.opt}')

    # if music_folder provided on command line, any existing cache must
    # be re-created.
    if playlist['music_folder'] != config['playlist']['music_folder'] and \
       playlist['cache_file']:
        playlist['create_cache_file'] = True

    config.update(cmd_config)

    # validate config
    if config['playlist']['create_cache_file'] and not \
       config['playlist']['cache_file']:
        pcloudapi.error('cache file name must be provided for create')
    chunk_size = config['playlist']['chunk_size']
    if chunk_size <= 0 or chunk_size > 1000:
        pcloudapi.error(f'invalid chunk size specified: {chunk_size}')

    return (config, args)

def main(config):
    pcloud = pcloudapi.PCloud(config)
    config, args = merge_config_options(config)

    cache_file =  os.path.expanduser(os.path.expandvars(
        config['playlist']['cache_file']))
    create_cache_file = config['playlist']['create_cache_file']
    chunk_size = config['playlist']['chunk_size']
    music_folder = config['playlist']['music_folder']
    playlist_dir = config['playlist']['playlist_dir']
    playlist_prefix = config['playlist']['playlist_prefix']
    verbose = config['verbose']

    try:
        pcloud.authenticate('reauth' in config)

        if 'list_playlists' in config:
            playlists = pcloud_playlist_names(pcloud)
            for name in playlists.keys():
                print(name)
            return

        if (cache_file and not os.path.exists(cache_file)) or \
           create_cache_file or not cache_file:
                if verbose: print('Loading music collection from pCloud ...')
                folder = pcloud.list_folder(path=music_folder)
                if create_cache_file or not os.path.exists(cache_file):
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

        upload_playlists(pcloud, fileids, args, playlist_dir, playlist_prefix,
                         chunk_size, verbose)
    except pcloudapi.PCloudException as err:
        pcloudapi.error(f'error: {err.code}; message: {err.msg}\n'\
                        f'Url: {err.url}')
    return

if __name__ == '__main__':
    config = pcloudapi.base_config()
    config['playlist'] = {
        'cache_file': '',
        'create_cache_file': False,
        'chunk_size': 100,
        'music_folder': '/Music',
        'playlist_dir': './',
        'playlist_prefix': ''}

    main(config)
