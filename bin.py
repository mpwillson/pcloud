import socket
import ssl

hostname = 'eapi.pcloud.com'
port = 8399

def api_connect(msg):
    context = ssl.create_default_context()

    with socket.create_connection((hostname, port)) as sock:
        sock.settimeout(10)
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            print(ssock.version())
            nsent = ssock.send(msg)
            print(f'Bytes sent: {nsent}')
            data = ssock.recv(2048)
            print(f'Received len: {len(data)}')
            print(data)
    return

def ei(value, size):
    bval = value.to_bytes(size, byteorder='little')
    return bval

def encode(method, params = {}, data = None):
    method_len = len(method)
    method_name = method.encode()
    bparams = bytearray()
    if data: method_len |= (1 << 7)
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
    msg_len = ei(len(method_name) + len(bparams) + 2 + \
                 (8 if data else 0), 2)
    if data:
        return msg_len + ei(method_len, 1) + ei(len(data), 8) + method_name + \
            ei(nparams, 1) + bparams + data
    else:
        return msg_len + ei(method_len,1) + method_name + ei(nparams, 1) + \
            bparams

def send_command():
    return

if __name__ == "__main__":
    #print(encode('list'))
    #print(encode('list', {'test': 'value'}))
    #print(encode('list_collection', {'type': 1}))

    # this api call will fail; pCloud don't allow use of access_token with
    # the collection_list method.
    params = {'type': 1, #}
              'access_token':
              'wSm5ZICeuMkN0prkZJB3W5kZ18HpdQDx6fzDzpdaky0rk0511ywV'}
    msg = encode('collection_list', params)

    # this api call is successful; access_token auth works with
    # uploadfile method
    params1 = {'filename': 'test',
              'folderid': 0,
              'access_token':
              'wSm5ZICeuMkN0prkZJB3W5kZ18HpdQDx6fzDzpdaky0rk0511ywV'}
    msg = encode('uploadfile', params1, b'File Contents\n')
    #print(msg)
    #print(f'len msg: {len(msg)}')
    api_connect(msg)
