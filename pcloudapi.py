'''
NAME
 pcloudapi.py - provides a python interface to the pCloud API

DESCRIPTION
 Provides:
  PCloudException
  pCloud class

  and a number of supporting functions.

TBD
'''

import urllib.parse
import urllib.request
import json
import sys
import os
import getpass
import time
import copy
import getopt

class PCloudException(Exception):
    '''Exception class for pCloud class. '''
    def __init__(self, url, code, msg):
        if (l := url.rfind('password')) > 0: url = url[:l]+'*password elided*'
        self.url = url
        self.code = code
        self.msg = msg
        return

class PCloud:
    '''Encapsulate pCloud API calls.

    All methods return the result from pCloud as a python data
    structure.

    '''
    def __init__(self, aspect_key=None, aspect_dict=None):
        '''Instantiate PCloud instance.

        If default configuration file exists, read it. Otherwise, use
        base configuration. If aspect options are provided, add to
        configuration if they do not already exist. Write updated or
        new configuration back to the default configuration file.

        '''
        save_required = False
        config = _base_config()
        config_file = os.path.expanduser(os.path.expandvars(
            config['config-file']))
        if os.path.exists(config_file):
            config = read_config(config, config_file)
        else:
            save_required = True
        if aspect_key:
            if not aspect_dict: raise ValueError('no aspect_dict provided')
            if not aspect_key in config:
                config[aspect_key] = aspect_dict
                save_required = True
        if save_required: save_json(config, config_file, indent="  ")

        self.config = config
        self.auth = None
        return

    def _request(self,action):
        result = 0
        payload = None
        try:
            url = f'{self.config["endpoint"]}/{action}'
            req = urllib.request.Request(url, headers={'User-Agent': 'hydrus'})
            resp = urllib.request.urlopen(req)
            payload = json.loads(resp.read().decode('utf-8'))
            result = payload['result']
            if result != 0:
                raise PCloudException(url, result, payload['error'])
        except urllib.error.HTTPError as err:
            raise PCloudException(url, err.code, 'http request failed')
        except urllib.error.URLError as err:
            raise PCloudException(url, -1, err)
        except json.decoder.JSONDecodeError as err:
            raise PCloudException(url, -1, 'invalid response from endpoint')
        except UnicodeError as err:
            raise PCloudException(url, -1, err)
        return payload

    def userinfo(self, username, password):
        request = f'userinfo?getauth=1&logout=1&username={username}&'\
            f'password={password}'
        payload = self._request(request)
        if payload: self.auth = payload['auth']
        return payload

    def collection_list(self, type=1):
        request = f'collection_list?auth={self.auth}&type={type}'
        return self._request(request)

    def collection_delete(self, coll_id):
        request = f'collection_delete?auth={self.auth}&collectionid='\
            f'{coll_id}'
        return self._request(request)

    def collection_create(self, name, ids):
        request = f'collection_create?auth={self.auth}&name={name}&fileids='
        for id in ids:
            request = request + f'{id},'
        request = request[:-1]
        return self._request(request)

    def collection_linkfiles(self, coll_id, file_ids):
        request = f'collection_linkfiles?auth={self.auth}&'\
            f'collectionid={coll_id}&fileids='
        for id in file_ids:
            request = request + f'{id},'
        request = request[:-1]
        return self._request(request)

    def list_folder(self, path='/', recursive=1):
        request = f'listfolder?auth={self.auth}&path={path}&'\
            f'recursive={recursive}'
        return self._request(request)

    def list_tokens(self):
        request = f'listtokens?auth={self.auth}'
        return self._request(request)

    def delete_token(self, tokenid):
        request = f'deletetoken?auth={self.auth}&tokenid={tokenid}'
        return self._request(request)

    def _login(self):
        '''Handles login to pCloud.

        A username (if not already provided) and password are
        requested to invoke the userinfo call. The resulting auth
        token is saved in an instance variable. It is also saved in
        the configuration dict and configuration file, along with the
        computed auth token expiry.

        '''
        if sys.stdin.isatty():
            if self.config['username']:
                username = self.config['username']
            else:
                username = input('Enter pCloud username: ')
            password = getpass.getpass('Enter pCloud password: ')
            payload = self.userinfo(username, password)
            self.auth = payload['auth']
            # pCloud token expires at (now + 31536000 seconds i.e. 1 year)
            auth = {"token": payload['auth'],
                    "expires": time.asctime(time.localtime(
                        time.time() + 31536000))}
            self._add_auth_to_config(self.config['config-file'], auth, username)
        else:
            error('username/password required: need terminal device.')
        return

    def _add_auth_to_config(self, config_file, auth, username):
        '''Update config file with auth token and (possibly) username.
        '''
        config = load_json(config_file)
        if 'username' in config and not config['username']:
            config['username'] = username
        config['auth'] = auth
        save_json(config, config_file, indent="  ")
        self.config = config
        return

    def authenticate(self, reauth=False):
        '''Authenticate to pCloud endpoint.

        If we have a valid auth token, no username/password is
        required. Otherwise, invoke a login to pCloud. If reauth is
        True, login is forced.

        '''
        if not reauth:
            if 'auth' in self.config:
                expired =  _expired(self.config['auth']['expires'])
                if not expired:
                    self.auth = self.config['auth']['token']
                    return
                else:
                    error('auth token expired; re-authentication required.',
                          die=False)
        self._login()
        return

def _expired(expires):
    expiry = time.mktime(time.strptime(expires))
    return time.time() > expiry

def error(msg, die=True):
    print(f'\n** {sys.argv[0]}: {msg}', file=sys.stderr)
    if die: sys.exit(1)
    return

def chunked(array, chunk_size):
    '''Return array in chunks of chunk_size.

    Return tuple of chunk and remaining values in array, which should
    be passed in to the next call as array.
    '''
    if chunk_size >= len(array):
        return (array, None)
    else:
        return (array[:chunk_size], array[chunk_size:])

def save_json(data, filename, indent=None):
    '''Write data to filename in JSON format.

    Creates directories as necessary.

    '''
    filename = os.path.expanduser(os.path.expandvars(filename))
    dirname = os.path.dirname(filename)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
    with open(filename,'w') as f:
        json.dump(data, f, indent=indent)
        f.write('\n')
    return

def load_json(filename):
    filename = os.path.expanduser(os.path.expandvars(filename))
    try:
        with open(filename) as f:
            contents = json.load(f)
    except json.decoder.JSONDecodeError as err:
        error(f'unable to read: {filename}: {err}')
    return contents

def read_config(config, config_file, optional=True):
    '''Read JSON-format configuration file.

    Merge into config dict. If optional is True, the config file need
    not exist. The merged config dict is returned.

    '''
    n_config = copy.deepcopy(config)
    config_file = os.path.expanduser(os.path.expandvars(config_file))
    if os.path.exists(config_file):
        r_config = load_json(config_file)
        n_config.update(r_config)
    else:
        if not optional: error(f'config file does not exist: {config_file}')
    return n_config

def merge_command_options(config, aspect_key, aspect_opts):
    '''Merge options from command line into configuration file.

    The config argument holds the configuration dictionary, either the
    default, or that read from the configuration file. The core config
    options on the command line are handled. Additional configuration
    for an aspect (client program of pcloudapi), that is the aspect
    key name and the command line option flags, are passed in
    aspect_key and aspect opts, respectively.

    Return value is a tuple of the merged configuration dictionary and
    remaining, non-option, command line arguments.

    '''
    cmd_config = copy.deepcopy(config)
    try:
        opts,args = getopt.getopt(sys.argv[1:],'e:f:ru:v', aspect_opts)
        for o,v in opts:
            if o == '-e':
                cmd_config['endpoint'] = v
            elif o =='-f':
                cmd_config['config_-ile'] = v
                config = read_config(config, v, optional=False)
            elif o == '-u':
                cmd_config['username'] = v
            elif o == '-v':
                cmd_config['verbose'] = True
            else:
                cmd_config[aspect_key][o[2:]] = \
                    v if o[2:]+'=' in aspect_opts else True
    except getopt.GetoptError as err:
        error(err)

    return (cmd_config, args)

def _base_config():
    '''Return config dictionary with minimal default config information.

    '''
    config = {'config-file': '~/.config/pcloud.json',
              'endpoint': 'https://eapi.pcloud.com',
              'username': '',
              'verbose': False
              }
    return config

def main():
    return

if __name__ == '__main__':
    main()
