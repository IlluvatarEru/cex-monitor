import datetime
import decimal
import json
import math
import smtplib
import warnings
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd

warnings.filterwarnings('ignore')


def get_best_opportunity_ticker_arb_future_spot(monthly_only=False, fee=None):
    best_performing_sym = ""
    max_perf_an = -1
    tickers = get_all_future_tickers()
    trace_all = ""
    for ticker in tickers:
        try:
            perf, perf_an, trace, ticker_future = compute_spot_fut_arb_performance_monthly(ticker, 1e3, debug=True
                                                                                           , fee=fee)
            trace_all += "\n" + trace
            if perf_an > max_perf_an:
                max_perf_an = perf_an
                max_perf = perf
                best_performing_sym = ticker_future
        except Exception as e:
            print("error for ", ticker)
            print(e)
            pass
        if not monthly_only:
            try:
                perf, perf_an, trace, ticker_future = compute_spot_fut_arb_performance_quarterly(ticker, 1e3
                                                                                                 , debug=True, fee=fee)
                trace_all += "\n" + trace
                if perf_an > max_perf_an:
                    max_perf_an = perf_an
                    max_perf = perf
                    best_performing_sym = ticker_future
            except Exception as e:
                print("error for ", ticker)
                print(e)
                pass
    days_to_expiry = (get_future_expiry(best_performing_sym) - datetime.datetime.now()).days
    final_msg = "Best opportunity for spot/future arb with  " + best_performing_sym
    final_msg += " with a  " + str(round(100 * max_perf, 2)) + "% return "
    final_msg += "over the coming  " + str(days_to_expiry) + " days."
    final_msg += "\n This is an equivalent  " + str \
        (round(100 * get_equivalent_annual_yield(max_perf, days_to_expiry), 2)) + "% annual return "
    trace_all += final_msg
    print(final_msg)
    return best_performing_sym, max_perf, trace_all, days_to_expiry


def get_all_future_tickers(apif):
    tickers = []
    for instrument in json.loads(apif.get_instruments())["instruments"]:
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


def format_ticker_for_spot_api(ticker):
    if ticker == "bchusd" or ticker == "BCHUSD":
        return "BCHUSD"
    elif ticker[0] == "X" and ticker[4] == "Z":
        return ticker
    else:
        return "X" + ticker.upper()[:3] + "Z" + ticker.upper()[3:]


def compute_spot_fut_arb_performance_monthly(apis, apif, ticker, notional_usd, debug=True, fee=None):
    ticker_future = apif.get_ticker("fi_ " + ticker, "M")
    price_future = apif.get_bid(ticker_future)
    # price_spot = apis.get_ask(format_ticker_for_spot_api(ticker))
    price_spot = apis.get_ask(ticker)
    # buy btc spot
    notional_crypto = (notional_usd / price_spot)
    if fee == "taker":
        notional_crypto = notional_crypto * (1 - apis.get_fees_taker(ticker))
    if fee == "maker":
        notional_crypto = notional_crypto * (1 - apis.get_fees_maker(ticker))
    # short btc fut for same notional
    trade_profit_future = notional_crypto * price_future
    if fee == "taker":
        trade_profit_future = trade_profit_future * (1 - apif.get_fees_taker()) * (1 - apif.get_fees_taker()) * (
                1 - apis.get_fees_taker(ticker))
    if fee == "maker":
        trade_profit_future = trade_profit_future * (1 - apif.get_fees_maker()) * (1 - apif.get_fees_maker()) * (
                1 - apis.get_fees_maker(ticker))
    profit = trade_profit_future - notional_usd
    days_to_expiry = (get_future_expiry(ticker_future) - datetime.datetime.now()).days
    y = profit / notional_usd
    y_an = get_equivalent_annual_yield(y, days_to_expiry)
    trace = ""
    if debug:
        trace += "Performance of " + ticker_future + " spot/future arb strategy:" + "\n"
        trace += "    Spot price: " + str(price_spot) + "\n"
        trace += "    Future price: " + str(price_future) + "\n"
        trace += "    N days to expiry: " + str(days_to_expiry) + "\n"
        trace += "    Profit: $" + str(round(profit, 2)) + "\n"
        trace += "    Yield: " + str(round(y * 100, 2)) + "%" + "\n"
        trace += "    Equivalent annual yield: " + str(round(y_an * 100, 2)) + "%" + "\n"
        trace += "-----------------------------------------------------------------------" + "\n"
        print(trace)
    return y, y_an, trace, ticker_future


def compute_spot_fut_arb_performance_quarterly(apis, apif, ticker, notional_usd, debug=True, fee=None):
    """
    ticker: str, ethusd
    """
    ticker_future = apif.get_ticker("fi_" + ticker, "Q")
    price_future = apif.get_bid(ticker_future)
    # price_spot = apis.get_ask(format_ticker_for_spot_api(ticker))
    price_spot = apis.get_ask(ticker)

    # buy btc spot
    notional_crypto = (notional_usd / price_spot)
    if fee == "taker":
        notional_crypto = notional_crypto * (1 - apis.get_fees_taker(ticker))
    if fee == "maker":
        notional_crypto = notional_crypto * (1 - apis.get_fees_maker(ticker))
    # short btc fut for same notional
    trade_profit_future = notional_crypto * price_future
    if fee == "taker":
        trade_profit_future = trade_profit_future * (1 - apif.get_fees_taker()) * (1 - apif.get_fees_taker()) * (
                1 - apis.get_fees_taker(ticker))
    if fee == "maker":
        trade_profit_future = trade_profit_future * (1 - apif.get_fees_maker()) * (1 - apif.get_fees_maker()) * (
                1 - apis.get_fees_maker(ticker))
    profit = trade_profit_future - notional_usd
    days_to_expiry = (get_future_expiry(ticker_future) - datetime.datetime.now()).days
    y = profit / notional_usd
    y_an = get_equivalent_annual_yield(y, days_to_expiry)
    trace = ""
    if debug:
        trace += "Performance of " + ticker_future + " spot/future arb strategy:" + "\n"
        trace += "    Spot price: " + str(price_spot) + "\n"
        trace += "    Future price: " + str(price_future) + "\n"
        trace += "    N days to expiry: " + str(days_to_expiry) + "\n"
        trace += "    Profit: $" + str(profit) + "\n"
        trace += "    Yield: " + str(round(y * 100, 2)) + "%" + "\n"
        trace += "    Equivalent annual yield: " + str(
            round(get_equivalent_annual_yield(y, days_to_expiry) * 100, 2)) + "%" + "\n"
        trace += "-----------------------------------------------------------------------" + "\n"
        print(trace)
    return y, y_an, trace, ticker_future


def get_equivalent_annual_yield(y, days_to_expiry):
    return y * 365 / days_to_expiry


def execute_spot_fut_arb(apis, apif, ticker, notional):
    """
    ticker: str, "xbtusd"
    """
    spot_ticker = format_ticker_for_spot_api(ticker)
    future_ticker = apif.get_ticker("fi_" + ticker, "M")

    # check we have the notional on kraken spot
    status = "not done"
    if float(apis.get_balance("ZUSD")) * 1.1 > notional:
        # buy the notional in ticker
        spot_p = apis.get_mid("XXBTZUSD")
        notional_crypto = notional / spot_p
        res = apis.create_order(spot_ticker, "buy", "limit", spot_p, notional_crypto)
        if res["error"] == []:
            order_id = res["txid"]
        # check order exectuted
        # send the notional to kraken futures
        apis.transfer_from_spot_to_future("XXBT", )
        return status
    else:
        raise ValueError("Not enough USD!")

    # short the future
    return status


def get_open_orders_id(apis, apif):
    open_orders = []
    res = apis.query_private("OpenOrders")
    for order in res["result"]['open']:
        open_orders.append(order)
    return open_orders


def get_closed_orders_id(apis, apif):
    closed_orders = []
    res = apis.query_private("ClosedOrders")
    for order in res["result"]['closed']:
        closed_orders.append(order)
    return closed_orders


def get_lhs(ticker):
    i = int(len(ticker) / 2)
    return ticker[:i]


def get_rhs(ticker):
    i = int(len(ticker) / 2)
    return ticker[i:]


def get_spot_ticker(future_ticker):
    return future_ticker.split("_")[1]


def get_future_balance(apif, ticker):
    t = "fi_" + ticker
    return apif.get_accounts()["accounts"][t]


def get_leverage(apis, apif, future_ticker):
    spot_ticker = get_spot_ticker(future_ticker)
    account = apif.get_accounts()["accounts"]["_".join(future_ticker.split("_")[:2])]
    balances = account["balances"]
    if future_ticker in balances.keys():
        size = 0
        for sym in balances.keys():
            if spot_ticker in sym:
                size += balances[sym]
        pv = account["auxiliary"]['pv']
        mtmPrice = apif.get_mid(future_ticker)
        return abs(size) / (pv * mtmPrice)
    else:
        print("No position in", future_ticker)
        return 1.0


def get_size_to_short_to_get_leverage_to_one(apif, future_ticker):
    account = apif.get_accounts()["accounts"]["_".join(future_ticker.split("_")[:2])]
    size = 0
    for ticker in account["balances"]:
        if ticker[:3] == "fi_":
            size += account["balances"][ticker]
    pv = account["auxiliary"]['pv']
    mtmPrice = apif.get_mid(future_ticker)
    return int(pv * mtmPrice - abs(size))




def send_email_str(message, to="arthurimbagourdov@gmail.com"):
    sender = "arthurbdauphine@gmail.com"
    receiver = [to]

    try:
        session = smtplib.SMTP('smtp.gmail.com', 587)
        session.ehlo()
        session.starttls()
        session.ehlo()
        session.login(sender, 'pirbro2157484')
        session.sendmail(sender, receiver, message)
        session.quit()
    except smtplib.SMTPException as e:
        print('Error', e)


def get_sym_from_future_ticker(ticker):
    return ticker.split("_")[1].upper()


def get_ticksize_future(spot_ticker):
    if spot_ticker == "XBT":
        return 0.5
    elif spot_ticker == "ETH":
        return 0.05
    elif spot_ticker == "LTC":
        return 0.01
    elif spot_ticker == "BCH":
        return 0.1
    elif spot_ticker == "XRP":
        return 0.0001


def get_ticksize_spot(spot_ticker):
    if spot_ticker == "XBT":
        return 0.5
    elif spot_ticker == "ETH":
        return 0.01
    elif spot_ticker == "LTC":
        return 0.01
    elif spot_ticker == "BCH":
        return 0.1
    elif spot_ticker == "XRP":
        return 0.0001


def roundup(x, ticksize):
    return math.ceil(x / ticksize) * ticksize


def rounddown(x, ticksize):
    return math.floor(x / ticksize) * ticksize


def roundtick(x, ticksize):
    if ticksize > 1:
        return round(x / ticksize) * ticksize
    else:
        ticksize = decimal.Decimal(str(ticksize))
        return round(x, -ticksize.as_tuple().exponent)


def send_email_html(html, subject, to="arthurimbagourdov@gmail.com"):
    sender = "arthurbdauphine@gmail.com"
    receiver = [to]

    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    part1 = MIMEText(html, 'html')
    msg.attach(part1)
    message = msg.as_string()

    try:
        session = smtplib.SMTP('smtp.gmail.com', 587)
        session.ehlo()
        session.starttls()
        session.ehlo()
        session.login(sender, 'pirbro2157484')
        session.sendmail(sender, receiver, message)
        session.quit()
    except smtplib.SMTPException as e:
        print('Error', e)


def get_open_futures_positions(apif):
    warnings = ""
    df = pd.DataFrame(columns=["Ticker", "Size (USD)", "Days to expiry", "PnL (USD)", "Return (%)", "Leverage"])
    res = apif.get_openpositions()
    positions = res["openPositions"]
    for pos in positions:
        ticker = pos["symbol"]
        leverage = get_leverage(ticker)
        entry_price = pos["price"]
        mtm_price = apif.get_ask(ticker)
        pnl = entry_price - mtm_price
        ret = round(100 * pnl / entry_price, 2)
        days_to_expiry = apif.get_time_to_expiry(ticker)
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


def round_price(price, sym):
    if sym == "BCHUSD":
        return round(price, 2)
    else:
        return price


2
