#!/usr/bin/env python
'''
NAME
  token.py - manage pCloud authentication tokens

SYNOPSIS
  python token.py [common_options]
                  {[--delete token_id[,token_id] ...] | [--list] }

For more, see README_token.md

'''

import pcloudapi
import sys

class Key():
    ASPECT = 'token'
    DELETE = 'delete'
    LIST = 'list'
    TOKENS = 'tokens'
    TOKENID = 'tokenid'
    EXPIRES = 'expires'
    DEVICE = 'device'

def delete_token(pcloud, tokens, delete_ids):
    token_ids = [token[Key.TOKENID] for token in tokens]
    for delete_id in delete_ids:
        if delete_id in token_ids:
            pcloud.delete_token(delete_id)
        else:
            pcloudapi.error(f'no such token-id: {delete_id}')
    return

def list_tokens(tokens):
    '''Print key token details from tokens list.

    Device attribute is truncated to ensure line is no longer than 80
    characters.
    '''
    print('%12s %-26s %s'%('Token-id','Expiry Date','Client'))
    for token in tokens:
        print(f'{token[Key.TOKENID]:12} {token[Key.EXPIRES][:-5]}'\
              f' {token[Key.DEVICE][:40]}')
    return

def main():
    pcloud = pcloudapi.PCloud()
    aspect_opts = (Key.DELETE+'=', Key.LIST)
    pcloud.config[Key.ASPECT] = {}
    args = pcloud.merge_command_options(Key.ASPECT, aspect_opts)
    try:
        pcloud.authenticate()
        tokens = pcloud.list_tokens()[Key.TOKENS]

        if Key.LIST in pcloud.config[Key.ASPECT]:
            list_tokens(tokens)
        elif Key.DELETE in pcloud.config[Key.ASPECT]:
            try:
                delete_tokenids = \
                    [int(v) for v in \
                     pcloud.config[Key.ASPECT][Key.DELETE].split(',')]
            except ValueError as err:
                pcloudapi.error(f'invalid token-id: {err}')
                return
            delete_token(pcloud, tokens, delete_tokenids)

    except pcloudapi.PCloudException as err:
        pcloudapi.error(f'error: {err.code}; message: {err.msg}\n'\
                        f'Url: {err.url}')
    return

if __name__ == '__main__':
    main()
