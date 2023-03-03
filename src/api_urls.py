import pandas as pd

from src.utils.instrument_types import SPOT
from src.utils.markets import KRAKEN

DATA_PATH = 'C:/dev/cex-monitor/resources/'


def get_api_url(market, instrument_type):
    apis = pd.read_csv(DATA_PATH + 'markets_to_apis.csv')
    api_url = apis.query('market == @market and instrument_type == @instrument_type')['api_url']
    if len(api_url) == 1:
        return "https://" + api_url.values[0]
    elif len(api_url) > 1:
        raise Exception(f'Multiple api urls for {market} and {instrument_type}')
    elif len(api_url) == 0:
        raise Exception(f'No api url for {market} and {instrument_type}')


def get_api_public_path(market, instrument_type):
    return 'public/' if instrument_type == SPOT and market == KRAKEN else ''


def get_api_private_path(market, instrument_type):
    return 'private/' if instrument_type == SPOT and market == KRAKEN else ''
