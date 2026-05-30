#!/usr/bin/env python

# Copy files to/from pCloud

import pcloudapi
import binapi
import os
import sys

class Key():
    ASPECT = 'pcp'

# Walking the pCloud filesystem takes a long time.
# The server-side recursive options seems to have been removed
# Handling the recursive walk on the client makes it slow

def get_contents(pcloud, fileid):
    'Return contents of pCloud folder.'
    resp = pcloud.binary_request('listfolder',
                                 {'folderid': fileid, 'recursive': 0,
                                  'nofiles': 0, 'noshares': 0})
    if resp['result'] == 0:
        return resp['metadata']['contents']
    else:
         raise pcloudapi.PCloudException(pcloud.config[Key.ENDPOINT],
                                         resp['result'], resp['error'])

def get_folder_structure(pcloud, path, fileid, fs = {}):
    'Return dict mapping pathnames to fileid.'
    contents = get_contents(pcloud, fileid)
    for entry in contents:
        if entry['isfolder']:
            get_folder_structure(pcloud, f'{path}/{entry['name']}',
                                 entry['folderid'], fs)
        else:
            fs[f'{path}/{entry["name"]}'] = entry['fileid']
    return fs

def get_folderid(pcloud, path):
    if path == '/': return 0
    resp = pcloud.binary_request('stat', {'path': path})
    if resp['result'] == 0 and resp['metadata']['isfolder'] == 0:
        return resp['metadata']['folderid']
    return -1

def upload_file(pcloud, pathname, data):
    path, filename = os.path.split(pathname)
    folderid = get_folderid(pcloud, path)
    if folderid >= 0:
        resp = pcloud.binary_request('uploadfile',
                                     {'filename': filename,
                                      'folderid': folderid},
                                     data)
        if resp['result'] != 0:
            pcloudapi.error(f'upload failed: {resp["error"]}')
    else:
        pcloudapi.error(f'unable to locate remote folder: {path}')
    return

def download_file(pcloud, pathname):
    data = None
    resp = pcloud.binary_request('stat', {'path': pathname})
    if resp['result'] == 0:
        meta = resp['metadata']
        if meta['isfolder']:
            pcloudapi.error('cannot copy a folder: {pathname}')
        else:
            resp = pcloud.binary_request('getfilelink',
                                         {'fileid': meta['fileid']})
            if resp['result'] == 0:
                url = f'https://{resp["hosts"][0]}{resp["path"]}'
                data = pcloudapi.get_url(url)
            else:
                pcloudapi.error('getfilelink failed: {resp["error"]}')
    return data

def write_file(filename, data):
    f = open(filename, mode='wb')
    if f:
        f.write(data)
        f.close()
    else:
        pcloudapi.error('unable to open local file for writing')
    return

def copy(pcloud, files):
    if files[0]['remote']:
        data = download_file(pcloud, files[0]['filename'])
        if data:
            write_file(files[1]['filename'], data)
    else:
        data = open(files[0]['filename'],'r').read().encode()
        upload_file(pcloud, files[1]['filename'], data)
    return

def parse_filenames(from_file, to_file):
    remote = [False, False]
    remote[0] = from_file.startswith('p:')
    remote[1] = to_file.startswith('p:')
    if remote[0] == remote[1]:
        pcloudapi.error('from and to files must be at different locations')
    if remote[0]:
        from_file = from_file[2:]
    else:
        from_file = os.path.expanduser(os.path.expandvars(from_file))
    if remote[1]:
        to_file = to_file[2:]
    else:
        to_file = os.path.expanduser(os.path.expandvars(to_file))
    if to_file == '.':
        to_file = os.path.basename(from_file)
    return [{'remote': remote[0], 'filename': from_file},
            {'remote': remote[1], 'filename': to_file}]

def main():
    pcloud = pcloudapi.PCloud()
    aspect_opts = []
    pcloud.config[Key.ASPECT] = {}
    args = pcloud.merge_command_options(Key.ASPECT, aspect_opts)
    if len(args) != 2:
        pcloudapi.error('usage: pcp.py from_file to_file')
    try:
        pcloud.authenticate()
        files = parse_filenames(args[0], args[1])
        copy(pcloud, files)

    except pcloudapi.PCloudException as err:
        pcloudapi.error(f'error: {err.code}; message: {err.msg}\n'\
                        f'Url: {err.url}')
    return

if __name__ == '__main__':
    main()
