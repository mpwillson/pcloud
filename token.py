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

def delete_token(pcloud, tokens, delete_ids):
    token_ids = [token['tokenid'] for token in tokens]
    for delete_id in delete_ids:
        if delete_id in token_ids:
            pcloud.delete_token(delete_id)
        else:
            pcloudapi.error(f'no such token_id: {delete_id}')
    return

def list_tokens(tokens):
    '''Print key token details from tokens list.

    Device attribute is truncated to ensure line is no longer than 80
    characters.
    '''
    print('%12s %-26s %s'%('Token-id','Expiry Date','Client'))
    for token in tokens:
        print(f'{token["tokenid"]:12} {token["expires"][:-5]}'\
              f' {token["device"][:40]}')
    return

def main():
    pcloud = pcloudapi.PCloud()
    aspect_opts = ('delete=', 'list')
    aspect_key = 'token'
    pcloud.config[aspect_key] = {}
    config, args = pcloudapi.merge_command_options(pcloud.config, aspect_key,
                                                   aspect_opts)
    try:
        pcloud.authenticate('reauth' in config)
        tokens = pcloud.list_tokens()['tokens']

        if 'list' in config[aspect_key]:
            list_tokens(tokens)
        elif 'delete' in config[aspect_key]:
            delete_tokenids = \
                [int(v) for v in config[aspect_key]['delete'].split(',')]
            delete_token(pcloud, tokens, delete_tokenids)

    except pcloudapi.PCloudException as err:
        pcloudapi.error(f'error: {err.code}; message: {err.msg}\n'\
                        f'Url: {err.url}')
    return

if __name__ == '__main__':
    main()
