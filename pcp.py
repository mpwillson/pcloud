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
    return resp['metadata']['contents']

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
    if resp['result'] == 0 and resp['metadata']['isfolder']:
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
            url = f'https://{resp["hosts"][0]}{resp["path"]}'
            data = pcloudapi.get_url(url)
    else:
        pcloudapi.error(f'no such remote file: {pathname}')
    return data

def write_file(filename, data):
    try:
        with open(filename, mode='wb') as f:
            f.write(data)
    except Exception as e:
        pcloudapi.error(f'unable to open local file for writing: {e}')
    return

def copy(pcloud, files):
    if files[0]['remote']:
        data = download_file(pcloud, files[0]['filename'])
        if data:
            destination = files[1]['filename']
            if os.path.isdir(destination):
                source = os.path.basename(files[0]['filename'])
                destination = os.path.join(destination, source)
            write_file(destination, data)
        else:
            pcloudapi.error('empty remote file contents: ' \
                            f'{files[0]["filename"]}')
    else:
        try:
            data = open(files[0]['filename'],'rb').read()
        except Exception as e:
            pcloudapi.error(f'unable to open file: {e}')
        destination = files[1]['filename']
        folderid = get_folderid(pcloud, destination)
        if folderid >= 0:
            source = os.path.basename(files[0]['filename'])
            destination = os.path.join(destination, source)
        upload_file(pcloud, destination, data)
    return

def parse_filenames(source, destination):
    remote = [False, False]
    remote[0] = source.startswith('p:')
    remote[1] = destination.startswith('p:')
    if remote[0] == remote[1]:
        pcloudapi.error('source and destination locations must be different')
    if remote[0]:
        source = source[2:]
    else:
        source = os.path.expanduser(os.path.expandvars(source))
    if remote[1]:
        destination = destination[2:]
    else:
        destination = os.path.expanduser(os.path.expandvars(destination))
    if destination == '.':
        destination = os.path.basename(source)
    return [{'remote': remote[0], 'filename': source},
            {'remote': remote[1], 'filename': destination}]

def main():
    pcloud = pcloudapi.PCloud()
    aspect_opts = []
    pcloud.config[Key.ASPECT] = {}
    args = pcloud.merge_command_options(Key.ASPECT, aspect_opts)
    if len(args) != 2:
        pcloudapi.error('usage: pcp.py source destination')
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
