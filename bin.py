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
            while True:
                data = ssock.recv(2048)
                print(f'Received len: {len(data)}')
                if ( len(data) < 1 ) :
                    break
                print(data)
    return

def encode_int(value, size):
    bval = value.to_bytes(size)
    return bval

def encode(method, data={}):
    method_len = len(method)
    method_name = method.encode()
    params = bytearray()
    #method_len |= (1 << 7) # always parameters (maybe of zero length)
    nparams = len(data)
    if data:
        for k,v in data.items():
            len_param_name = len(k)
            code = 0
            match type(v):
                case __builtins__.str:
                    code = 0
                case __builtins__.int:
                    code = 1
                case __builtins__.bool:
                    code = 2
            param_intro = (code << 6) | len_param_name
            match code:
                case 0:
                    params = params+param_intro.to_bytes()+\
                        k.encode()+len(v).to_bytes(4)+\
                        v.encode()
                case 1:
                    params = params+param_intro.to_bytes()+k.encode()+\
                        v.to_bytes(8)
                case 2:
                    params = params+param_intro.to_bytes()+k.encode()+\
                        (1 if v else 0).to_bytes()

    # 1 byte for method length + 8 bytes for parameter length
    msg_len = len(method_name) + len(params) + 2
    return msg_len.to_bytes(2)+method_len.to_bytes(1)+method_name+\
        nparams.to_bytes()+params
    #return msg_len.to_bytes(2)+method_len.to_bytes(1)+len(params).to_bytes(8)+\
     #   method_name+nparams.to_bytes()+params

def send_command():
    return

if __name__ == "__main__":
    #print(encode('list'))
    #print(encode('list', {'test': 'value'}))
    #print(encode('list_collection', {'type': 1}))

    params = {'type': 1, #}
              'access_token': 'wSm5ZICeuMkN0prkZJB3W5kZ18HpdQDx6fzDzpdaky0rk0511ywV'}
    msg = encode('collection_list', params)
    print(msg)
    print(f'len msg: {len(msg)}')
    api_connect(msg)
