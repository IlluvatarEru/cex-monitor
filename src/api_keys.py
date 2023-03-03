from src.exceptions import raise_instrument_type_not_supported_for_market_exception, raise_market_not_supported
from src.utils.instrument_types import SPOT, FUTURE
from src.utils.markets import KRAKEN, BINANCE


def get_api_keys(market, instrument_type, account):
    with open(f"C:/dev/data/{market.lower()}/k" + account + "_" + instrument_type + ".txt") as f:
        content = f.readlines()
    public_key = content[0][:-1]
    private_key = content[1]
    return public_key, private_key


def get_header_key_col(market, instrument_type):
    if market == KRAKEN:
        if instrument_type == SPOT:
            return 'API-Key'
        elif instrument_type == FUTURE:
            return 'APIKey'
        else:
            raise_instrument_type_not_supported_for_market_exception(instrument_type, market)
    elif market == BINANCE:
        if instrument_type == SPOT:
            return 'API-Key'
        else:
            raise_instrument_type_not_supported_for_market_exception(instrument_type, market)
    else:
        raise_market_not_supported(market)


def get_header_signature_col(market, instrument_type):
    if market == KRAKEN:
        if instrument_type == SPOT:
            return 'API-Sign'
        elif instrument_type == FUTURE:
            return 'Authent'
        else:
            raise_instrument_type_not_supported_for_market_exception(instrument_type, market)
    elif market == BINANCE:
        if instrument_type == SPOT:
            return ''
        else:
            raise_instrument_type_not_supported_for_market_exception(instrument_type, market)
    else:
        raise_market_not_supported(market)
