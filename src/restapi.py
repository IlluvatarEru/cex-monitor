import warnings
import time
import requests

warnings.filterwarnings('ignore')


class RestAPI:
    """
    Class that represents an API, be it spot/future, it's very generic
    """

    def __init__(self,
                 api_url,
                 public_key="",
                 private_key="",
                 timeout=10,
                 check_certificate=True,
                 use_nonce=False,
                 api_version='0'):
        self.apiPath = api_url
        self.public_key = public_key
        self.private_key = private_key
        self.timeout = timeout
        self.nonce = 0
        self.api_version = api_version
        self.session = requests.Session()
        self.check_certificate = check_certificate
        self.use_nonce = use_nonce
        self.response = None
        self._json_options = {}

    def get_api_version(self):
        return self.api_version

    @staticmethod
    def _nonce():
        """
        Nonce counter.
        :returns: an always-increasing unsigned integer (up to 64 bits wide)
        """
        return int(1000 * time.time())

    def json_options(self, **kwargs):
        """
        Set keyword arguments to be passed to JSON deserialization.
        :param kwargs: passed to :py:meth:`requests.Response.json`
        :returns: this instance for chaining
        """
        self._json_options = kwargs
        return self

    def close(self):
        """
        Close this session.
        :returns: None
        """
        self.session.close()
        return

    def load_key(self, path):
        """
        Load key and secret from file.
        Expected file format is key and secret on separate lines.
        :param path:  str, path to keyfile
        :returns: None
        """
        with open(path, 'r') as f:
            self.public_key = f.readline().strip()
            self.private_key = f.readline().strip()
        return

    def _query(self, url_path, data, headers=None, timeout=None):
        """
        Low-level query handling.
        :param url_path: str, API URL path sans host
        :param data: dict, API request parameters
        :param headers: dict, (optional) HTTPS headers
        :param timeout: int or float,(optional) if not ``None``, a :py:exc:`requests.HTTPError`
                        will be thrown after ``timeout`` seconds if a response
                        has not been received
        :returns: :py:meth:`requests.Response.json`-deserialised Python object
        :raises: :py:exc:`requests.HTTPError`: if response status not successful
        """
        if data is None:
            data = {}
        if headers is None:
            headers = {}

        url = self.apiPath + url_path
        print(url)

        self.response = self.session.post(url, data=data, headers=headers, timeout=timeout)

        return self.response#.json(**self._json_options)
