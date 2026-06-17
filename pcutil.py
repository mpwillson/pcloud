#!/usr/bin/env python

# Copy files to/from pCloud
#
# Usage:
#  python pcutil.py [common_options]
#                   {cp [-dr] source destination | rm [-dr] file [file ...]}
#
#  For the cp command, the pCLoud location in source or destination
#  is indicated by a p:/ prefix. The prefix is not required for the rm
#  command; it is assumed.  All pCloud locations are absolute.
#

import pcloudapi
import binapi
import os
import sys
import getopt

DEBUG = True

class Key():
    ASPECT = 'pcutil'
    DRYRUN = 'dryrun'
    RECURSIVE = 'recursive'

# Walking the pCloud filesystem takes a long time. Hence, unused.
#
# The server-side recursive option seems to have been removed.
# Handling the recursive walk on the client makes it slow

def get_contents(pcloud, fileid):
    '''Return contents of pCloud folder.'''
    resp = pcloud.binary_request('listfolder',
                                 {'folderid': fileid, 'recursive': 0,
                                  'nofiles': 0, 'noshares': 0})
    return resp['metadata']['contents']

def get_folder_structure(pcloud, path, fileid, fs = {}):
    '''Return dict mapping pathnames to fileid, starting at path.'''
    entries = get_contents(pcloud, fileid)
    for entry in entries:
        if entry['isfolder']:
            get_folder_structure(pcloud, f'{path}/{entry["name"]}',
                                 entry['folderid'], fs)
        else:
            fs[f'{path}/{entry["name"]}'] = entry['fileid']
    return fs

def pwalk(pcloud, folderid, folder_name):
    '''Walks pCloud filesystem ala os.walk.'''
    entries = get_contents(pcloud, folderid)
    folders = [(entry['folderid'], entry['name'])
               for entry in entries if entry['isfolder']]
    files = [(entry['fileid'], entry['name'])
             for entry in entries if not entry['isfolder']]
    yield [(folderid, folder_name), folders, files]
    for folder in folders:
        yield from pwalk(pcloud, folder[0], folder[1])

def create_folder(pcloud, folderid, name):
    '''Create folder on pCloud, located in folderid, named name.'''
    resp = pcloud.binary_request('createfolderifnotexists',
                                 {'folderid': folderid,
                                  'name': name})
    return resp['metadata']['folderid']

def create_folders(pcloud, path):
    '''Create pcloud folders named in absolute path, if they don't
       already exist. Returns id of deepest folder.'''
    folders = path.strip('/').split('/')
    folderid = 0
    for folder in folders:
        if folder:
            folderid = create_folder(pcloud, folderid, folder)
    return folderid

def get_pathinfo(pcloud, path):
    '''Return tuple of isfolder and id (for either file or folder.'''
    if path == '/': return (True, 0)
    resp = pcloud.binary_request('stat', {'path': path})
    if resp['result'] == 0:
        isfolder = resp['metadata']['isfolder']
        return (isfolder, resp['metadata']['folderid'] if isfolder \
                else resp['metadata']['fileid'])
    return (False, -1)

def upload_file(pcloud, folderid, filename, data):
    params = {'filename': filename, 'folderid': folderid}
    resp = pcloud.binary_request('uploadfile', params, data)
    return

def download_file(pcloud, pathname):
    '''Download file from pCloud, named in pathname.'''
    data = None
    isfolder, fileid = get_pathinfo(pcloud, pathname)
    if isfolder:
        pcloudapi.error('cannot copy a folder: {pathname}')
    else:
        if fileid > 0:
            resp = pcloud.binary_request('getfilelink',
                                         {'fileid': fileid})
            url = f'https://{resp["hosts"][0]}{resp["path"]}'
            data = pcloudapi.get_url(url)
        else:
            pcloudapi.error(f'no such remote file: {pathname}')
    return data

def download_file_id(pcloud, fileid):
    '''Download file identified by fileid from pCloud.'''
    data = None
    if fileid > 0:
        resp = pcloud.binary_request('getfilelink',
                                     {'fileid': fileid})
        url = f'https://{resp["hosts"][0]}{resp["path"]}'
        data = pcloudapi.get_url(url)
    else:
        pcloudapi.error(f'no such remote file: {pathname}')
    return data

def write_file(filename, data):
    '''Create filename, with data as contents.'''
    try:
        with open(filename, mode='wb') as f:
            f.write(data)
    except Exception as e:
        pcloudapi.error(f'unable to open local file for writing: {e}')
    return

def read_file(filename):
    '''Return contents of local file identified by filenname.'''
    try:
        data = open(filename, 'rb').read()
    except Exception as e:
        pcloudapi.error(f'unable to open file: {e}')
    return data

def copy_file(pcloud, source, dest):
    '''Copy single file from source to dest.'''
    dryrun = Key.DRYRUN in pcloud.config[Key.ASPECT]
    if source['remote']:
        if source['isfolder']:
            pcloudapi.error(f'cannot copy folder; use --recusive: ' \
                            f'{source["filename"]}')
        if source['id'] < 0:
            pcloudapi.error(f'source file does not exist: ' \
                            f'p:{source["filename"]}')
        if dryrun:
            data = 'dummy'
        else:
            data = download_file_id(pcloud, source['id'])
        if data:
            source_file = source['filename']
            destination = dest['filename']
            if dest['isfolder']:
                source_file = os.path.basename(source_file.strip('/'))
                destination = os.path.join(destination, source_file)
            else:
                if dest['id'] < 0:
                    base, filename = os.path.split(destination)
                    if base and not os.path.exists(base): os.makedirs(base)

            if dryrun:
                print(f'cp {("p:/"+source_file).replace("//", "/")} '\
                      f'{destination}')
            else:
                write_file(destination, data)
        else:
            pcloudapi.error('empty remote file contents: ' \
                            f'{source["filename"]}')
    else:
        source_file = source['filename']
        if source['isfolder']:
            pcloudapi.error('cannot copy folder; use -r: '\
                            f'{source_file}')
        data = read_file(source_file)
        destination = dest['filename']
        filename = os.path.basename(source_file)
        folderid = dest['id']
        folder = ''
        if dest['id'] < 0:
            folder, filename = os.path.split(destination)
            if folder:
                isfolder, folderid = get_pathinfo(pcloud, folder)
                if folderid < 0:
                    if dryrun:
                        print(f'mkfolder p:/{folder.strip('/')}')
                    else:
                        folderid = create_folders(pcloud, folder)
        elif dest['isfolder']:
            filename = os.path.basename(source_file)
            folder = destination
        else:
            folder, filename = os.path.split(destination)
            _, folderid = get_pathinfo(pcloud, folder)
        if dryrun:
            # kludge, sigh
            dest_path = (folder+"/"+filename).strip('/')
            print(f'cp {source_file} p:/{dest_path}')

        else:
            upload_file(pcloud, folderid, filename, data)
    return

def copy_from_remote(pcloud, source_file, sourceid, dest):
    '''Copy files recursively from pCloud.'''
    dryrun = Key.DRYRUN in pcloud.config[Key.ASPECT]
    if os.path.exists(dest):
        if not os.path.isdir(dest):
            pcloudapi.error(f'invalid destination: {dest}')
    else:
        if dryrun:
            print(f'mkdir {dest}')
        else:
            os.makedirs(dest)
    #print(dest)
    entries = get_contents(pcloud, sourceid)
    folders = [entry for entry in entries if entry['isfolder']]
    files = [entry for entry in entries if not entry['isfolder']]

    for folder in folders:
        edest = os.path.normpath(f'{dest}/{folder["name"]}')
        copy_from_remote(pcloud, folder['name'], folder['folderid'], edest)

    for file_entry in files:
        edest = os.path.normpath(f'{dest}/{file_entry["name"]}')
        if dryrun:
            print(f'cp p:[{file_entry["fileid"]}] {edest}')
        else:
            data = download_file_id(pcloud, file_entry['fileid'])
            if data: write_file(edest, data)
    return

def copy_to_remote(pcloud, source, folderid, folder_name):
    '''Copy files recursively to pCloud.'''
    dryrun = Key.DRYRUN in pcloud.config[Key.ASPECT]
    source_dir = source['filename']
    folders = {}
    if folderid < 0:
        if dryrun:
            print(f'mkfolder p:{folder_name}')
        else:
            folderid = create_folders(pcloud, folder_name)
    folders = {folder_name: folderid}
    for root, dirs, files in os.walk(source_dir):
        if source_dir: root = root.replace(source_dir, '')
        print('new root: '+root)
        base, folder = os.path.split(root)
        if not base:
            base = folder_name
        elif base == '/':
            base = folder_name
        else:
            base = (folder_name + '/' + base).replace('//', '/')
        if base in folders:
            baseid = folders[base]
            if folder:
                new_folder = base+'/'+folder
                if dryrun:
                    print(f'mkfolder {os.path.normpath("p:/"+new_folder)}')
                    folders[new_folder] = '[0]'
                else:
                    folders[new_folder] = baseid = \
                        create_folder(pcloud, baseid, folder)
        else:
            pcloudapi.error(f'internal error: target folder doesn\'t exist: ' \
                            f'{base}')
        for file in files:
            if dryrun:
                print('cp ' \
                      f'{os.path.normpath(source_dir+"/"+root+"/"+file)} ' \
                      f'{os.path.normpath("p:"+folder_name+"/"+root+"/"+file)}')
            else:
                data = read_file(f'{source_dir}/{root}/{file}')
                upload_file(pcloud, baseid, file, data)
    return

def copy(pcloud, files):
    '''Handles single file and recursive copies to/from pCloud.'''
    recursive = Key.RECURSIVE in pcloud.config[Key.ASPECT]
    source = files['source']
    dest = files['dest']
    if not recursive:
        copy_file(pcloud, source, dest)
        return

    source_dir = source['filename']
    if source['id'] < 0:
        pcloudapi.error(f'source does not exist: {source_dir}')
    dest_file = dest['filename']

    if not dest['isfolder'] and dest['id'] >= 0:
        # dest is file
        pcloudapi.error(f'invalid recursive destination: {dest_file}')
    if source['remote']:
         copy_from_remote(pcloud, source['filename'], source['id'], dest_file)
    else:
        if not source['isfolder']:
            pcloudapi.error(f'source is not a directory: {source_dir}')
        copy_to_remote(pcloud, source, dest['id'], dest_file)

    return

def local_file_munge(filename):
    if filename.startswith('..'):
        filename = filename.replace('..', os.path.dirname(os.getcwd()), 1)
    elif filename.startswith('.'):
        filename = filename.replace('.', os.getcwd(), 1)
    filename = os.path.expanduser(os.path.expandvars(filename))
    return filename

def parse_filenames(pcloud, source_file, dest_file):
    '''Returns dict based on parsing source and destination paths.'''
    remote = [False, False]
    source = {}
    dest = {}
    source['remote'] = source_file.startswith('p:')
    dest['remote'] = dest_file.startswith('p:')
    if source['remote'] == dest['remote']:
        pcloudapi.error('cp: source and destination cannot be at same location')

    if source_file.endswith('/'):
        source_file = source_file[:-1]
    elif Key.RECURSIVE in pcloud.config[Key.ASPECT]:
        dest_file = (dest_file + '/' +
                     os.path.basename(source_file)).replace('//', '/')

    if source['remote']:
        source_file = source_file[2:].replace('//', '/')
        isfolder, id = get_pathinfo(pcloud, source_file)
        source['isfolder'] = isfolder
        source['id'] = id
    else:
        source_file = local_file_munge(source_file)
        source['isfolder'] = os.path.isdir(source_file)
        source['id'] = 0 if os.path.exists(source_file) else -1
    source['filename'] = source_file

    if dest['remote']:
        dest_file = dest_file[2:]
    else:
        dest_file = local_file_munge(dest_file)
    dest['filename'] = dest_file
    if dest['remote']:
        isfolder, id = get_pathinfo(pcloud, dest_file)
        dest['isfolder'] = isfolder
        dest['id'] = id
    else:
        dest['isfolder'] = os.path.isdir(dest_file)
        dest['id'] = 0 if os.path.exists(dest_file) else -1

    return {'source': source, 'dest': dest}

def rm(pcloud, pathnames):
    recursive = Key.RECURSIVE in pcloud.config[Key.ASPECT]
    dryrun = Key.DRYRUN in pcloud.config[Key.ASPECT]
    for pathname in pathnames:
        if pathname.startswith('p:'): pathname = pathname[2:]
        if not pathname.startswith('/'): pathname = '/' + pathname
        isfolder, id = get_pathinfo(pcloud, pathname)
        if id < 0:
            pcloudapi.error(f'no such file/folder: {pathname}', False)
            continue
        if isfolder:
            if not recursive:
                contents = get_contents(pcloud, id)
                if len(contents) == 0:
                    resp = pcloud.binary_request('deletefolder',
                                                 {'folderid': id})
                else:
                    pcloudapi.error(f'cannot rm non-empty folder: use -r: ' \
                                    f'{pathname}')
            else:
                if dryrun:
                    print(f'rm -r {pathname}')
                else:
                    resp = pcloud.binary_request('deletefolderrecursive',
                                                 {'folderid': id})
                    print(f'{pathname}: {resp["deletedfolders"]} folder(s), ' \
                           f'{resp["deletedfiles"]} file(s) deleted.')
        else:
            if dryrun:
                print(f'rm {pathname}')
            else:
                resp = pcloud.binary_request('deletefile', {'fileid': id})
    return

def main():
    pcloud = pcloudapi.PCloud()
    pcloud.config[Key.ASPECT] = {}
    args = pcloud.merge_command_options(Key.ASPECT, {})
    if len(args) == 0:
        pcloudapi.error('usage: pcutil.py ' \
                        '[common_options] ' \
                        '{cp [-dr] source destination | ' \
                        'rm [-dr] file [file...]}')
    # parse cmd args
    try:
        opts, largs = getopt.getopt(args[1:], 'dr')
        for o,v in opts:
            if o == '-r':
                pcloud.config[Key.ASPECT][Key.RECURSIVE] = True
            elif o == '-d':
                pcloud.config[Key.ASPECT][Key.DRYRUN] = True
    except getopt.GetoptError as err:
        pcloudapi.error(f'{args[0]}: {err}')

    args[1:] = largs
    if args[0] == 'cp' and len(args) != 3:
        pcloudapi.error('usage: cp [-dr] source destination')
    elif args[0] == 'rm' and len(args) < 2:
        pcloudapi.error('usage: rm [-dr] {file|folder}  [{file|folder} ...]')

    try:
        pcloud.authenticate()
        if args[0] == 'cp':
            files = parse_filenames(pcloud, args[1], args[2])
            if DEBUG: print(files)
            copy(pcloud, files)
        elif args[0] == 'rm':
            rm(pcloud, args[1:])
        else:
            pcloudapi.error(f'unknown command: {args[0]}')
    except pcloudapi.PCloudException as err:
        pcloudapi.error(f'error: {err.code}; message: {err.msg}')
    return

if __name__ == '__main__':
    main()
