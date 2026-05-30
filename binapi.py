# Testing pCloud binapi.ry protocol
#
# pCloud have removed username/password authentication for API method
# calls. However, the alternative authentication method (OAUTH2) does
# not work for non-file methods.
#
# Programs like rclone will continue to work, but the playlist
# handling is completely non-functional.

import socket
import ssl
import urllib.parse
import urllib.request

hostname = 'eapi.pcloud.com'
port = 8399

# Globals
sock = None
ssock = None
intern_str = [] # Holds reused strings within method response

# Constants
# Binary interface types
HASH = 16
ARRAY = 17
BOOL_FALSE = 18
BOOL_TRUE = 19
DATA = 20

def ei(value, size):
    'Encode integer to bytes in little endian format'
    bval = value.to_bytes(size, byteorder='little')
    return bval

def encode(method, params = {}, data = b''):
    'Encode pCloud API call into binary format'
    method_len = len(method)
    method_name = method.encode()
    bparams = bytearray()
    data_len = b''
    if len(data) != 0:
        method_len |= (1 << 7)
        data_len = ei(len(data), 8)
    nparams = len(params)
    if params:
        for k,v in params.items():
            len_param_name = len(k)
            code = 0
            code = [str, int, bool].index(type(v))
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
    msg_len = ei((len(method_name) + len(bparams) + 2 + (8 if data else 0)), 2)
    return msg_len + ei(method_len,1) + data_len + \
        method_name + ei(nparams, 1) + bparams + data

def di(b):
    'Decode bytes in little endian format to an int'
    return int.from_bytes(b, 'little')

def is_str(code):
    'Is pCloud string?'
    return (code >= 0 and code <= 7) or (code >= 100 and code <= 199)

def is_int(code):
    'Is pCloud int?'
    return (code >= 8 and code <= 15) or (code >= 200 and code <= 219)

def decode_int(msg):
    'Decode int from msg. Return tuple of remaining msg contents and int.'
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
    'Decode string from msg. Return tuple of remaining msg contents and string.'
    code = msg[0]
    i = 1
    if (code >= 0 and code <= 3):
        slen = di(msg[i:i+code+1])
        i += code + 1
        s = msg[i:i+slen].decode()
        i += slen
        intern_str.append(s)
    elif (code >= 4 and code <= 7):
        t = di(msg[i:i+code-3])
        i += code - 3
        s = intern_str[t]
    elif (code >= 100 and code <= 149):
        s = msg[i:i+code-100].decode()
        i += code-100
        intern_str.append(s)
    elif (code >= 150 and code <= 199):
        s = intern_str[code-150]
    else:
        raise TypeError(f'Invalid string type: {code}')
    return [msg[i:], s]

def decode_hash(msg):
    'Decode hash from msg. Return tuple of remaining msg contents and hash.'
    d = {}
    while len(msg) != 0 and msg[0] != 255:
        msg, k = decode_str(msg)
        msg, v = decode_value(msg)
        d[k] = v
    return [msg[1:], d]

def decode_array(msg):
    'Decode array from msg. Return tuple of remaining msg contents and array.'
    a = []
    while len(msg) != 0 and msg[0] != 255:
        msg, v = decode_value(msg)
        a.append(v)
    return [msg[1:], a]

def decode_value(msg):
    'Decode value from msg. Return tuple of remaining msg contents and value.'
    code = msg[0]
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
        raise TypeError(f'binapi: Unhandled type code: f{code}')
    return [msg, None]

def decode(msg):
    'Decode pCloud binary API response and return as dict.'
    global intern_str
    intern_str = []
    _, resp = decode_value(msg)
    return resp

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

def send_request(method, params = {}, data = b''):
    global sock, ssock
    response = None
    if ssock:
        request = encode(method, params, data)
        nsent = ssock.send(request)
        byte_length = di(ssock.recv(4))
        response = ssock.recv(byte_length)
        if len(response) == 0:
            # always return valid dict with helpful? error message
            return {'result': 9000, 'error': 'Null return from binary request'}
    return decode(response)

if __name__ == "__main__":
    bytes_val = encode('method', {'int': 0, 'str': 'string', 'bool': True})
    assert(bytes_val == b'(\x00\x06method\x03Cint\x00\x00\x00\x00\x00\x00\x00\x00\x03str\x06\x00\x00\x00string\x84bool\x01')

    open(hostname, port)

    # this api call will fail; pCloud don't allow use of access_token with
    # the collection_list method.
    resp = send_request('collection_list', {'type': 1})
    if resp and resp.get('result') == 0:
        print(resp)
    else:
        print(f'collection_list: error: code: {resp['result']}, '\
              f'msg: {resp['error']}')
    close()
