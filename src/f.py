import warnings

from src.sym_utils import format_ticker_for_spot_api, get_spot_ticker

warnings.filterwarnings('ignore')


def get_equivalent_annual_yield(y, days_to_expiry):
    return y * 365 / days_to_expiry


def execute_spot_fut_arb(api_spot, api_future, ticker, notional):
    """
    ticker: str, "xbtusd"
    """
    spot_ticker = format_ticker_for_spot_api(ticker)
    future_ticker = api_future.get_ticker("fi_" + ticker, "M")

    # check we have the notional on kraken spot
    status = "not done"
    if float(api_spot.get_balance("ZUSD")) * 1.1 > notional:
        # buy the notional in ticker
        spot_p = api_spot.get_mid("XXBTZUSD")
        notional_crypto = notional / spot_p
        res = api_spot.create_order(spot_ticker, "buy", "limit", spot_p, notional_crypto)
        if res["error"] == []:
            order_id = res["txid"]
        # check order exectuted
        # send the notional to kraken futures
        api_spot.transfer_from_spot_to_future("XXBT", )
        return status
    else:
        raise ValueError("Not enough USD!")

    # short the future
    return status


def get_open_orders_id(api_spot, api_future):
    open_orders = []
    res = api_spot.query_private("OpenOrders")
    for order in res["result"]['open']:
        open_orders.append(order)
    return open_orders


def get_closed_orders_id(api_spot, api_future):
    closed_orders = []
    res = api_spot.query_private("ClosedOrders")
    for order in res["result"]['closed']:
        closed_orders.append(order)
    return closed_orders


def get_leverage(api_spot, api_future, future_ticker):
    spot_ticker = get_spot_ticker(future_ticker)
    account = api_future.get_accounts()["accounts"]["_".join(future_ticker.split("_")[:2])]
    balances = account["balances"]
    if future_ticker in balances.keys():
        size = 0
        for sym in balances.keys():
            if spot_ticker in sym:
                size += balances[sym]
        pv = account["auxiliary"]['pv']
        mtmPrice = api_future.get_mid(future_ticker)
        return abs(size) / (pv * mtmPrice)
    else:
        print("No position in", future_ticker)
        return 1.0


def get_size_to_short_to_get_leverage_to_one(api_future, future_ticker):
    account = api_future.get_accounts()["accounts"]["_".join(future_ticker.split("_")[:2])]
    size = 0
    for ticker in account["balances"]:
        if ticker[:3] == "fi_":
            size += account["balances"][ticker]
    pv = account["auxiliary"]['pv']
    mtmPrice = api_future.get_mid(future_ticker)
    return int(pv * mtmPrice - abs(size))


def round_price(price, sym):
    if sym == "BCHUSD":
        return round(price, 2)
    else:
        return price


2
