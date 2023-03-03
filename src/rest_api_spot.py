import base64
import hashlib
import hmac
import urllib.parse
import warnings

from src.sym_utils import format_ticker_for_spot_api
from src.rest_api import CEXRESTAPI

warnings.filterwarnings('ignore')


class CEXRESTAPISpot(CEXRESTAPI):
    def __init__(self, public_key="", private_key="", timeout=10, check_certificate=True, use_nonce=False):
        super().__init__('https://api.kraken.com',
                         public_key, private_key, timeout, check_certificate, use_nonce, '0')

    def query_public(self, method, data=None, timeout=None):
        """
        Performs an API query that does not require a valid key/secret pair.
        :param method: str, API method name
        :param data: dict, (optional) API request parameters
        :param timeout: int or float, (optional) if not ``None``, a :py:exc:`requests.HTTPError`
                        will be thrown after ``timeout`` seconds if a response
                        has not been received
        :returns: :py:meth:`requests.Response.json`-deserialised Python object
        """
        if data is None:
            data = {}

        url_path = '/' + self.api_version + '/public/' + method

        return self._query(url_path, data, timeout=timeout)

    def query_private(self, method, data=None, timeout=None):
        """
        Performs an API query that requires a valid key/secret pair.
        :param method: str, API method name
        :param data: dict, (optional) API request parameters
        :param timeout: int or float, (optional) if not ``None``, a :py:exc:`requests.HTTPError`
                        will be thrown after ``timeout`` seconds if a response
                        has not been received
        :returns: :py:meth:`requests.Response.json`-deserialised Python object
        """
        if data is None:
            data = {}

        if not self.public_key or not self.private_key:
            raise Exception('Either public or private key is not set! (Use `load_key()`.')

        data['nonce'] = self._nonce()

        url_path = '/' + self.api_version + '/private/' + method
        print(f'signing: {url_path}')
        headers = {
            'API-Key': self.public_key,
            'API-Sign': self._sign(data, url_path)
        }

        return self._query(url_path, data, headers, timeout=timeout)

    def _sign(self, data, url_path):
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

    def get_bid(self, ticker):
        ticker_info = self.query_public("Ticker", {"pair": ticker})
        bid = ticker_info['result'][format_ticker_for_spot_api(ticker)]['b'][0]
        return float(bid)

    def get_ask(self, ticker):
        ticker_info = self.query_public("Ticker", {"pair": ticker})
        ask = ticker_info['result'][format_ticker_for_spot_api(ticker)]['a'][0]
        return float(ask)

    def get_mid(self, ticker):
        bid = self.get_bid(ticker)
        ask = self.get_ask(ticker)
        mid = (bid + ask) / 2
        return mid

    def get_balance(self, ccy):
        balances = self.query_private('Balance')['result']
        if ccy in balances.keys():
            return balances[ccy]
        elif "X" + ccy in balances.keys():
            return balances["X" + ccy]
        elif "Z" + ccy in balances.keys():
            return balances["Z" + ccy]
        else:
            return 0.0

    def get_balances(self):
        return self.query_private('Balance')['result']

    def create_order(self, ticker, side, order_type, price, volume):
        response = self.query_private('AddOrder',
                                      {'pair': ticker,
                                       'type': side,
                                       'ordertype': order_type,
                                       'price': price,
                                       'volume': volume,
                                       })
        return response

    def transfer_from_spot_to_future(self, ccy, amount):
        response = self.query_private('WalletTransfer', {'asset': ccy,
                                                         'from': 'Spot Wallet',
                                                         'to': 'Futures Wallet',
                                                         'amount': amount})
        return response

    def get_fees(self, pair):
        result = self.query_public("AssetPairs", {"pair": pair, "info": "fees"})
        return result["result"]

    def get_fees_taker(self, pair):
        fees = self.get_fees(pair)
        return fees[list(fees.keys())[0]]["fees"][0][1] / 100

    def get_fees_maker(self, pair):
        fees = self.get_fees(pair)
        return fees[list(fees.keys())[0]]["fees_maker"][0][1] / 100

    def get_decimals(self, pair, display=False):
        result = self.query_public("Assets", {"asset": pair})["result"]["X" + pair]
        if display:
            return result["display_decimals"]
        else:
            return result["decimals"]

    def get_closed_orders(self):
        return self.query_private("ClosedOrders")["result"]["closed"]

    def get_closed_orders_for_sym(self, sym):
        target_orders = {}
        orders = self.get_closed_orders()
        for order_id in orders.keys():
            order = orders[order_id]
            order_sym = order["descr"]["pair"]
            if order_sym == sym:
                target_orders[order_id] = order
        return target_orders

    def get_open_orders(self):
        return self.query_private("OpenOrders")["result"]["open"]

    def get_open_positions(self):
        return self.query_private("OpenPositions")["result"]
