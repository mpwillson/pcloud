# Testing pCloud binary protocol
#
# pCloud have removed username/password authentication for API method
# calls. However, the alternative authentication method (OAUTH2) does
# not work for non-file methods.
#
# Programs like rclone will continue to work, but the playlist
# handling is completely non-functional.

import socket
import ssl
import time

hostname = 'eapi.pcloud.com'
port = 8399

# Constants

# Binary interface types
HASH = 16
ARRAY = 17
BOOL_FALSE = 18
BOOL_TRUE = 19
DATA = 20

def api_connect(msg):
    context = ssl.create_default_context()

    with socket.create_connection((hostname, port)) as sock:
        sock.settimeout(10)
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            print(ssock.version())
            nsent = ssock.send(msg)
            print(f'Bytes sent: {nsent}')
            data = ssock.recv(2048)
            #print(f'Received len: {len(data)}')
            #print(data)
    return data

def ei(value, size):
    bval = value.to_bytes(size, byteorder='little')
    return bval

def encode(method, params = {}, data = None):
    method_len = len(method)
    method_name = method.encode()
    bparams = bytearray()
    bdata = b''
    bdata_len = b''
    if data:
        method_len |= (1 << 7)
        bdata = data.encode()
        bdata_len = ei(len(bdata), 8)
    nparams = len(params)
    if params:
        for k,v in params.items():
            len_param_name = len(k)
            code = 0
            match type(v):
                case __builtins__.str:
                    code = 0
                case __builtins__.int:
                    code = 1
                case __builtins__.bool:
                    code = 2
            param_intro = ei((code << 6) | len_param_name, 1)
            match code:
                case 0:
                    bparams = bparams + param_intro + \
                        k.encode() + ei(len(v), 4) + v.encode()
                case 1:
                    bparams = bparams + param_intro + k.encode() + ei(v, 8)
                case 2:
                    bparams = bparams + param_intro + k.encode() + \
                        ei(1 if v else 0, 1)

    # add 1 byte for method length and 1 byte for param count + optional
    # data length of 8 bytes
    msg_len = ei((len(method_name) + len(bparams) + 2 + (8 if bdata else 0)), 2)
    return msg_len + ei(method_len,1) + bdata_len + \
        method_name + ei(nparams, 1) + bparams + bdata

def di(b):
    return int.from_bytes(b, 'little')

intern_str = []

def is_str(code):
    return (code >= 0 and code <= 7) or (code >= 100 and code <= 199)

def is_int(code):
    return (code >= 8 and code <= 15) or (code >= 200 and code <= 219)

def decode_int(msg):
    code = msg[0]
    vlen = 0
    if (code >= 200 and code <= 219):
        v = code - 200
        i = 1
    elif (code >= 8 and code <= 15):
        vlen = code - 7
        i = 1
        v = di(msg[i:i+vlen])
    return [msg[i+vlen:], v]

def decode_str(msg):
    code = msg[0]
    i = 1
    if (code >= 0 and code <= 3):
        slen = di(msg[i:i+code+1])
        i += code + 1
        s = msg[i:i+slen].decode()
        i += slen + 1
        intern_str.append(s)
    elif (code >= 100 and code <= 149):
        s = msg[i:i+code-100].decode()
        i += code-100
        intern_str.append(s)
        #print(f'short string: {s}, i: {i}')
    elif (code >= 150 and code <= 199):
        s = intern_str[code-150]
    else:
        print(f'invalid string type: {code}')
        s = '*ERROR*'
    return [msg[i:], s]

def decode_hash(msg):
    d = {}
    while len(msg) != 0 and msg[0] != 255:
        msg, k = decode_str(msg)
        msg, v = decode_value(msg)
        d[k] = v
        #print(f'k: {k}, v: {v}')
    return [msg[1:], d]

def decode_array(msg):
    a = []
    while len(msg) != 0 and msg[0] != 255:
        msg, v = decode_value(msg)
        a.append(v)
    return [msg[1:], a]

def decode_value(msg):
    code = msg[0]
    #print(f'decode_value: code: {code}')
    if code == HASH:
        return decode_hash(msg[1:])
    elif is_str(code):
        return decode_str(msg)
    elif is_int(code):
        return decode_int(msg)
    elif code == BOOL_FALSE:
        return [msg[1:], False]
    elif code == BOOL_TRUE:
        return [msg[1:], True]
    elif code == ARRAY:
        return decode_array(msg[1:])
    elif code == DATA:
        dlen = di(msg[1:9])
        return [msg[dlen+9:], msg[10:dlen+10]]
    else:
        print(f'unhandled code: f{code}')
    return [msg, None]

def decode(msg):
    '''Decode pCloud binary API response and return as dict.'''
    intern_str = []
    length = di(msg[0:4])
    #print(f'message length: {length}')
    _, resp = decode_value(msg[4:])
    return resp

sock = None
ssock = None

def open(hostname, port):
    global sock, ssock
    context = ssl.create_default_context()
    sock = socket.create_connection((hostname, port))
    sock.settimeout(10)
    ssock = context.wrap_socket(sock, server_hostname=hostname)
    return

def close():
    global sock, ssock
    if ssock: ssock.close()
    if sock: sock.close()
    ssock = sock = None
    return

def send(method, params, data = None):
    global sock, ssock
    params['access_token'] = \
        'wSm5ZICeuMkN0prkZJB3W5kZ18HpdQDx6fzDzpdaky0rk0511ywV'
    request = encode(method, params, data)
    if ssock:
        nsent = ssock.send(request)
        data = ssock.recv(2048) # TBD if recv data > 2048 must read more
        print(data)
        return decode(data)
    return None

if __name__ == "__main__":
    #print(encode('list'))
    #print(encode('list', {'test': 'value'}))
    #print(encode('list_collection', {'type': 1}))
    open(hostname, port)

    # this api call will fail; pCloud don't allow use of access_token with
    # the collection_list method.
    resp = send('collection_list', {'type': 1})
    print(f'collection_list response: {resp}')

    # this api call is successful; access_token auth works with
    # uploadfile method
    params1 = {'filename': 'test',
              'folderid': 0}
    #resp = send('uploadfile', params1, 'File Contents\n')

    #result = resp.get('result', -1)
    #if result == 0:
    #    print(f'Upload successful: fileid: {resp['metadata'][0]['fileid']}')

    #time.sleep(1)
    # Hmm, downloadfile does not do what I thought. It appears to copy the
    # contents of a page (from url) to a file on pCloud.
    resp = send('downloadfile',
                {'url': 'https://hydrus.org.uk', 'folderid': 0, 'target': 'test'})
    print(resp)

    close()
