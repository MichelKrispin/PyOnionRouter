#!/usr/bin/env python3
import os

import requests
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from flask import Flask, Response, request

app = Flask(__name__)

LOG_PREFIX = f'\x1b[42m[Node {os.getenv("PORT")}]\x1b[0m'
DIRECTORY_NODE = os.getenv('DIRECTORY_NODE', 'http://127.0.0.1:8888')


def generate_rsa_key():
    """Generate a new RSA key pair which will be stored
    as `private.pem` and `public.pem`.
    Returns the public key.

    Returns:
        Crypto.PublicKey.RSA.RsaKey: The newly generated public key.
    """
    key = RSA.generate(2048)
    private_key = key.export_key()
    private_file = open('private.pem', 'wb')
    private_file.write(private_key)
    private_file.close()
    public_file = open('public.pem', 'wb')
    public_file.write(key.publickey().export_key())
    public_file.close()
    return key.publickey().export_key()


def get_private_rsa_key():
    """Read the private.pem key and return it.

    Returns:
        str: The private RSA key
    """
    key_name = 'private.pem'
    return RSA.import_key(open(key_name).read())


def encrypt(content):
    """Encrypt the content with AES and RSA.
    First generates a random AES key which is used to encrypt the content,
    then the AES key itself is encrypted with the given public key.

    Args:
        public_key (str): The public key as a string.
        content (str): The content that should be encrypted.

    Returns:
        (bytes, bytes, bytes): encrypted AES key, AES key nonce, encrypted content
    """
    # Get public client key
    key_name = os.getenv('PUBLIC_KEY')
    public_key = RSA.import_key(key_name)
    session_key = get_random_bytes(32)  # Random AES key
    cipher_rsa = PKCS1_OAEP.new(public_key)
    enc_key = cipher_rsa.encrypt(session_key)  # Encrypt AES key with RSA key
    cipher_aes = AES.new(session_key, AES.MODE_EAX)
    enc_content = cipher_aes.encrypt(content)  # Encrypt content with AES key
    return enc_key, cipher_aes.nonce, enc_content


def decrypt(enc_key, nonce, enc_content):
    """Decrypt the AES key using the public key of this node
    and then the content with the decrypted key and the nonce.

    Args:
        enc_key (bytes): The encrypted AES key.
        nonce (bytes): The AES nonce needed for decryption.
        enc_content (bytes): The encrypted content.

    Returns:
        str: Decrypted content.
    """
    private_key = get_private_rsa_key()
    cipher_rsa = PKCS1_OAEP.new(private_key)
    key = cipher_rsa.decrypt(enc_key)
    cipher_aes = AES.new(key, AES.MODE_EAX, nonce)
    return cipher_aes.decrypt(enc_content)


def parse_package(data):
    """Parse the received data package and return the next host and content.
    The package will have an AES key which will be decrypted with the private RSA key,
    then used to decrypt the content which will then be returned together with the next host.

    Follows this protocol:
    |    4 Bytes   |      4 Bytes     |      4 Bytes     | ks Bytes | 16 Bytes  |    as Bytes    |  cs Bytes  |
    | keySize (ks) | addressSize (as) | contentSize (cs) | AES key  | AES nonce |  next address  |  content   |

    Args:
        data (bytes): The received bytes package.

    Returns:
        str, str: The next host, the decrypted content (might still be encrypted)
    """
    key_size = int.from_bytes(data[:4], byteorder='big')
    address_size = int.from_bytes(data[4:8], byteorder='big')
    content_size = int.from_bytes(data[8:12], byteorder='big')
    enc_key = data[12:12 + key_size]
    idx = 12 + key_size + 16
    nonce = data[12 + key_size:idx]

    next_host = data[idx:idx + address_size].decode()
    idx += address_size
    enc_content = data[idx:idx + content_size]
    content = decrypt(enc_key, nonce, enc_content)
    return next_host, content


@app.route('/', methods=['POST'])
def node():
    """
    The default access point.
    Send the binary package data to this route.
    This will:
        - try to unwrap the data,
        - notify the directory node,
        - wrap the response,
        - return the response.
    """
    notification_url = DIRECTORY_NODE + '/notify'
    status = 'success'

    # Unpack the received data
    try:
        received_data = request.get_data()
        next_host, content = parse_package(received_data)
    except Exception as e:
        status = str(e)
        return Response(f'Error: {str(e)}')
    # Notify on parsing
    requests.post(notification_url,
                  json={
                      'status': status,
                      'node_address': os.getenv('THIS_NODE'),
                      'tracking_id': os.getenv('TRACKING_ID')
                  })

    # Make next connection
    try:
        if b'GET ' in content:  # Last hop
            request_response = requests.get(next_host)
        else:  # Intermediate hop
            request_response = requests.post(
                url=next_host,
                data=content,
                headers={'Content-Type': 'application/x-binary'})
        key, nonce, response_content = encrypt(request_response.content)
        address = b'none:0000'
        response = (len(key).to_bytes(4, byteorder='big') +
                    len(address).to_bytes(4, byteorder='big') +
                    len(response_content).to_bytes(4, byteorder='big') + key +
                    nonce + address + response_content)
    except Exception as e:
        status = str(e)
        return Response(f'Error: {str(e)}')

    # Notify on encryption and packaging
    requests.post(notification_url,
                  json={
                      'status': status,
                      'public_key': os.getenv('PUBLIC_KEY')
                  })
    return Response(response,
                    mimetype="application/x-binary",
                    direct_passthrough=True)


@app.route('/get-public-key', methods=['GET'])
def get_public_key():
    """Get the public key of this node.
    A new pair will be created so it shouldn't be called multiple times.
    """
    return generate_rsa_key()


@app.route('/info', methods=['GET'])
def info():
    """Show information for logging purposes."""
    msg = f'''\
Directory: {DIRECTORY_NODE}
PORT: {os.getenv("PORT", "undefined")}
SUFFIX: {os.getenv("SUFFIX", "undefined")}
THIS_NODE: {os.getenv("THIS_NODE", "undefined")}
TRACKING_ID: {os.getenv("TRACKING_ID", "undefined")}
PUBLIC_KEY: {os.getenv("PUBLIC_KEY", "undefined")}
    '''
    print(LOG_PREFIX + msg)
    return msg.replace('\n', '<br>')


"""Notes:
Needed environment variables are
PORT: The port this node is running on
PUBLIC_KEY: The public key of the client used for encryption
THIS_NODE: Only if deployed in the cloud, then the URL of this node as passed on by the directory node.
SUFFIX (optional): Only for development if multiple private/public keys are existent in the folder
"""
if __name__ == '__main__':
    port = os.getenv('PORT')
    if not port:
        print(
            f'\x1b[31mERROR: Port not set. An env variable called "PORT" has to be set!\x1b[0m'
        )
    port = int(port)
    app.run(debug=True, host="0.0.0.0", port=port)
