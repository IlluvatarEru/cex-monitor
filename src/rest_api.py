import base64
import hashlib
import hmac
import time
import urllib.parse

import requests

from src.api_keys import get_header_key_col, get_header_signature_col
from src.api_urls import get_api_url, get_api_private_path, get_api_public_path
from src.utils.instrument_types import FUTURE


class KrakenAPI:
    def __init__(self, market, instrument_type, public_key, private_key):
        self.market = market
        self.instrument_type = instrument_type
        self.public_key = public_key
        self.private_key = private_key
        self.session = requests.Session()
        self.api_url = get_api_url(market, instrument_type)
        self.public_path = get_api_public_path(market, instrument_type)
        self.private_path = get_api_private_path(market, instrument_type)
        self.header_key_col = get_header_key_col(market, instrument_type)
        self.header_signature_col = get_header_signature_col(market, instrument_type)

    @staticmethod
    def _nonce():
        """
        Nonce counter.
        :returns: an always-increasing unsigned integer (up to 64 bits wide)
        """
        return int(1000 * time.time())

    def _sign_spot(self, data, url_path):
        """
        Sign request data according to Kraken's scheme.
        :param data: dict, API request parameters
        :param url_path: str, API URL path sans host
        :returns: signature digest
        """
        post_data = urllib.parse.urlencode(data)

        # Unicode-objects must be encoded before hashing
        encoded = (str(data['nonce']) + post_data).encode()
        message = url_path.encode() + hashlib.sha256(encoded).digest()

        signature = hmac.new(base64.b64decode(self.private_key),
                             message, hashlib.sha512)
        sig_digest = base64.b64encode(signature.digest())

        return sig_digest.decode()

    def _sign_future(self, endpoint, post_data, nonce=""):
        # step 1: concatenate postData, nonce + endpoint
        message = post_data + nonce + endpoint

        # step 2: hash the result of step 1 with SHA256
        sha256_hash = hashlib.sha256()
        sha256_hash.update(message.encode('utf8'))
        hash_digest = sha256_hash.digest()

        # step 3: base64 decode private_key
        secret_decoded = base64.b64decode(self.private_key)

        # step 4: use result of step 3 to has the result of step 2 with HMAC-SHA512
        hmac_digest = hmac.new(secret_decoded, hash_digest, hashlib.sha512).digest()

        # step 5: base64 encode the result of step 4 and return
        return base64.b64encode(hmac_digest)

    def query_public(self, method, timeout=10, headers=None, data=None):
        if headers is None:
            headers = {}
        if data is None:
            data = {}

        method_path = self.public_path + method
        url = self.api_url + method_path
        print(url)

        response = self.session.get(url, data=data, headers=headers, timeout=timeout)

        return response.json()

    def query_private(self, method, timeout=10, headers=None, data=None, request_type='GET'):

        if data is None:
            data = {}
        data['nonce'] = self._nonce()

        method_path = self.private_path + method
        url = self.api_url + method_path
        print(url)

        if headers is None:
            if not self.public_key:
                raise Exception('Public key is not set!')
            if not self.private_key:
                raise Exception('Private key is not set!')
            if self.instrument_type == FUTURE:
                print(f's:{"/api/v3/" + method_path}')
                signature = self._sign_future('/api/v3/' + method_path, '')
            else:
                signature = self._sign_spot(data, '/0/' + method_path)
            headers = {
                self.header_key_col: self.public_key,
                self.header_signature_col: signature
            }
        if request_type == 'GET':
            response = self.session.get(url, data=data, headers=headers, timeout=timeout)
        elif request_type == 'POST':
            response = self.session.post(url, data=data, headers=headers, timeout=timeout)
        else:
            raise Exception(f'Request type {request_type} not supported. Only GET and POST supported.')
        return response.json()
