import datetime
import json

import pandas as pd

from src.f import get_leverage


def get_all_future_tickers(api_future):
    tickers = []
    for instrument in json.loads(api_future.get_instruments())["instruments"]:
        sym = instrument["symbol"]
        if len(sym.split("_")) == 3:
            tickers.append(sym.split("_")[1])
    return list(set(tickers))


def get_future_expiry(ticker_future):
    future_expiry_info = ticker_future.split("_")[2]
    y = 2000 + int(future_expiry_info[:2])
    m = future_expiry_info[2:4]
    m = int(m.replace("0", "") if int(m) < 10 else m)
    d = int(future_expiry_info[4:].replace("0", ""))
    return datetime.datetime(y, m, d)


def get_future_balance(api_future, ticker):
    t = "fi_" + ticker
    return api_future.get_accounts()["accounts"][t]


def get_open_futures_positions(api_future):
    warnings = ""
    df = pd.DataFrame(columns=["Ticker", "Size (USD)", "Days to expiry", "PnL (USD)", "Return (%)", "Leverage"])
    res = api_future.get_openpositions()
    positions = res["openPositions"]
    for pos in positions:
        ticker = pos["symbol"]
        leverage = get_leverage(ticker)
        entry_price = pos["price"]
        mtm_price = api_future.get_ask(ticker)
        pnl = entry_price - mtm_price
        ret = round(100 * pnl / entry_price, 2)
        days_to_expiry = api_future.get_time_to_expiry(ticker)
        if days_to_expiry <= 7:
            warnings += "WARNING:" + ticker + " expiring in " + str(days_to_expiry) + " days. <br>"
        size = pos["size"]
        df = df.append({'Ticker': ticker,
                        "Size (USD)": size,
                        "Days to expiry": days_to_expiry,
                        "PnL (USD)": round(pnl, 2),
                        "Return (%)": ret,
                        "Leverage": leverage}, ignore_index=True)
    return df, warnings
