#!/usr/bin/env python
'''
NAME
  token.py - manage pCloud authentication tokens

SYNOPSIS
  python token.py [-d token_id] [-e endpoint] [-f config_file]
                  [-l] [-r] [-u username ] [-v]

For more, see README_token.md

'''

import pcloudapi
import getopt
import sys


def delete_token(pcloud, tokens, target):
    for token in tokens:
        if token['tokenid'] == target:
            pcloud.delete_token(token['tokenid'])
            break
        pcloudapi.error(f'no such token_id: {target}')
    return

def merge_config_options(config):
    '''Merge options from command line into configuration file.

    The config argument holds the default configuration dictionary. If
    no config file is specified as an option, the default config file
    is read. Return value is a tuple of the merged configuration
    dictionary and remaining command line arguments.
    '''
    cmd_config = pcloudapi.read_config(config, config['config_file'])
    try:
        opts,args = getopt.getopt(sys.argv[1:],'d:e:f:lru:v')
        for o,v in opts:
            if o == '-d':
                cmd_config['delete_tokenid'] = int(v)
            elif o == '-l':
                cmd_config['auth_list'] = True
            elif o == '-e':
                cmd_config['endpoint'] = v
            elif o =='-f':
                cmd_config['config_file'] = v
                config = read_config(config, v, optional=False)
            elif o == '-r':
                config['reauth'] = True
            elif o == '-u':
                cmd_config['username'] = v
            elif o == '-v':
                cmd_config['verbose'] = True
    except getopt.GetoptError as err:
        error(f'unknown option: -{err.opt}')

    config.update(cmd_config)
    return (config, args)

def main(config):
    config, args = merge_config_options(config)
    try:
        pcloud = pcloudapi.PCloud(config)
        pcloud.authenticate('reauth' in config)
        tokens = pcloud.list_tokens()['tokens']

        if 'auth_list' in config:
            for token in tokens:
                print(f'{token["tokenid"]:10}: {token["expires"][:-5]}'\
                      f' {token["device"]}')
            return

        if 'delete_tokenid' in config:
            delete_token(pcloud, tokens, config['delete_tokenid'])

    except pcloudapi.PCloudException as err:
        pcloudapi.error(f'error: {err.code}; message: {err.msg}\n'\
                        f'Url: {err.url}')
    return

if __name__ == '__main__':
    main(pcloudapi.base_config())
