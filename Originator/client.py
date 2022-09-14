#!/usr/bin/env python3
import os

import requests
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from flask import Flask, jsonify, render_template, request

app = Flask(__name__,
            static_url_path='',
            static_folder='static',
            template_folder='templates')


def generate_rsa_key():
    """Generate a new RSA key pair which will be stored
    as `private.pem` and `public.pem`.
    """
    key = RSA.generate(2048)
    private_key = key.export_key()
    private_file = open('private.pem', "wb")
    private_file.write(private_key)
    private_file.close()
    public_file = open('public.pem', "wb")
    public_file.write(key.publickey().export_key())
    public_file.close()


def encrypt(public_key, content):
    """Encrypt the content with AES and RSA.
    First generates a random AES key which is used to encrypt the content,
    then the AES key itself is encrypted with the given public key.

    Args:
        public_key (str): The public key as a string.
        content (str): The content that should be encrypted.

    Returns:
        (bytes, bytes, bytes): encrypted AES key, AES key nonce, encrypted content
    """
    public_key = RSA.importKey(public_key)
    session_key = get_random_bytes(32)  # Random AES key
    cipher_rsa = PKCS1_OAEP.new(public_key)
    enc_key = cipher_rsa.encrypt(session_key)  # Encrypt AES key with RSA key
    cipher_aes = AES.new(session_key, AES.MODE_EAX)
    enc_content = cipher_aes.encrypt(content)  # Encrypt content with AES key
    return enc_key, cipher_aes.nonce, enc_content


def decrypt(enc_key, nonce, enc_content):
    """Decrypt the AES key using the public key of the client
    and then the content with the decrypted key and the nonce.

    Args:
        enc_key (bytes): The encrypted AES key.
        nonce (bytes): The AES nonce needed for decryption.
        enc_content (bytes): The encrypted content.

    Returns:
        str: Decrypted content.
    """
    private_key = RSA.import_key(open('private.pem').read())  # Get private key
    cipher_rsa = PKCS1_OAEP.new(private_key)
    key = cipher_rsa.decrypt(enc_key)
    cipher_aes = AES.new(key, AES.MODE_EAX, nonce)
    return cipher_aes.decrypt(enc_content)


def parse_package(data):
    """Parse the received data package and return the received key and content.
    The returned key is still encrypted and has to be decrypted with this nodes
    private RSA key. The nonce is needed by the crypto library used.
    The content is encrypted with the decrypted AES key.

    Follows this protocol:
    |    4 Bytes   |      4 Bytes     |      4 Bytes     | ks Bytes | 16 Bytes  |    as Bytes    |  cs Bytes  |
    | keySize (ks) | addressSize (as) | contentSize (cs) | AES key  | AES nonce |  next address  |  content   |

    Args:
        data (bytes): The received bytes package.

    Returns:
        str, str, str: Encrypted AES key, Nonce for AES decryption, encrypted content
    """
    key_size = int.from_bytes(data[:4], byteorder='big')
    address_size = int.from_bytes(data[4:8], byteorder='big')
    content_size = int.from_bytes(data[8:12], byteorder='big')
    enc_key = data[12:12 + key_size]
    idx = 12 + key_size + 16
    nonce = data[12 + key_size:idx]
    enc_content = data[idx + address_size:idx + address_size + content_size]
    return enc_key, nonce, enc_content


def client(service, route):
    """Starts the wrapping, sending and unwrapping process.

    The package protocol is:
    |    4 Bytes   |      4 Bytes     |      4 Bytes     | ks Bytes | 16 Bytes  |    as Bytes    |  cs Bytes  |
    | keySize (ks) | addressSize (as) | contentSize (cs) | AES key  | AES nonce |  next address  |  content   |

    Args:
        service (str): Service URL.
        route (List[str]): A list of node URLs like ['first', 'second', 'third'].

    Returns:
        bool, str|dict: Success, Error string on failure | {'result': Response data} else
    """
    try:
        # Build up the route with the services address
        addresses = route
        addresses.reverse()
        public_keys = [
            requests.get(address + '/get-public-key').text
            for address in addresses
        ]
        addresses = [service] + addresses
        if any(['404 Page not found' in k for k in public_keys]):
            raise Exception(f'/get-public-key of {addresses} not found')
        print(
            f'[{addresses[-1]}] -> [{addresses[-2]}] -> [{addresses[1]}] -> [{addresses[0]}]'
        )
        first_address = addresses.pop()
    except Exception as e:
        return False, f'[ERROR] Getting public keys from nodes: {str(e)}'

    try:
        # Create the onion request
        # Predefined request
        content = b'GET / HTTP/1.1\r\nHost: ' + service.encode() + b'\r\n\r\n'
        # Wrap up the content multiple times according to the protocol
        for i, address in enumerate(addresses):
            key, nonce, content = encrypt(public_keys[i], content)
            content = (len(key).to_bytes(4, byteorder='big') +
                       len(address).to_bytes(4, byteorder='big') +
                       len(content).to_bytes(4, byteorder='big') + key +
                       nonce + address.encode() + content)
    except Exception as e:
        return False, f'[ERROR] Wrapping up package: {str(e)}'

    try:
        # Make the connection
        response = requests.post(
            url=first_address,
            data=content,
            headers={'Content-Type': 'application/x-binary'})
    except Exception as e:
        return False, f'[ERROR] Making request to first node: {str(e)}'

    try:
        # Wait for the response and unwrap it
        data = response.content
        for i in range(len(addresses)):
            enc_key, nonce, data = parse_package(data)
            data = decrypt(enc_key, nonce, data)
        print(data.decode())
    except Exception as e:
        return False, f'[ERROR] Encryption of package: {str(e)}'

    return True, {'result': data.decode()}


@app.route('/')
def index():
    """
    The client interface. Returns a simple HTML page.
    The web interface asks the directory node for a route.
    """
    if not os.path.exists('public.pem'):
        generate_rsa_key()
    public_key = open('public.pem').read()
    return render_template('index.html', public_key=public_key)


@app.route('/connect', methods=['POST'])
def start_client():
    """
    Gets called by the 'index.html' (route: /) with the input of the form fields
    to send the wrapped package to the service.

    Expects a POST request with {'service': service_url, 'route': ['first', 'second', 'third']}
    """
    service = request.json['service']
    route = request.json['route']
    if not service or not route:
        status, msg = False, 'Service URL and route have to be given as URL parameters'
    else:
        status, msg = client(service, route)
    result = {'status': status}
    if status:
        result['data'] = msg
    else:
        result['error'] = msg
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=os.getenv('PORT', 8080))
