import datetime

from src.f import get_equivalent_annual_yield
from src.future_utils import get_all_future_tickers, get_future_expiry


def get_best_opportunity_ticker_arb_future_spot(api_spot, api_future, monthly_only=False, fee=None):
    best_performing_sym = ""
    max_perf_an = -1
    tickers = get_all_future_tickers(api_future)
    trace_all = ""
    for ticker in tickers:
        try:
            perf, perf_an, trace, ticker_future = compute_spot_fut_arb_performance_monthly(api_spot, api_future, ticker, 1e3, debug=True
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
                perf, perf_an, trace, ticker_future = compute_spot_fut_arb_performance_quarterly(api_spot, api_future, ticker, 1e3
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


def compute_spot_fut_arb_performance_monthly(api_spot, api_future, ticker, notional_usd, debug=True, fee="taker"):
    ticker_future = api_future.get_ticker("fi_" + ticker, "M")
    price_future = api_future.get_bid(ticker_future)
    price_spot = api_spot.get_ask(ticker)
    # buy token spot
    notional_crypto = (notional_usd / price_spot)
    if fee == "taker":
        notional_crypto = notional_crypto * (1 - api_spot.get_fees_taker(ticker))
    if fee == "maker":
        notional_crypto = notional_crypto * (1 - api_spot.get_fees_maker(ticker))
    # short btc fut for same notional
    trade_profit_future = notional_crypto * price_future
    if fee == "taker":
        trade_profit_future = trade_profit_future * (1 - api_future.get_fees_taker()) * (1 - api_future.get_fees_taker()) * (
                1 - api_spot.get_fees_taker(ticker))
    if fee == "maker":
        trade_profit_future = trade_profit_future * (1 - api_future.get_fees_maker()) * (1 - api_future.get_fees_maker()) * (
                1 - api_spot.get_fees_maker(ticker))
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


def compute_spot_fut_arb_performance_quarterly(api_spot, api_future, ticker, notional_usd, debug=True, fee=None):
    """
    ticker: str, ethusd
    """
    ticker_future = api_future.get_ticker("fi_" + ticker, "Q")
    price_future = api_future.get_bid(ticker_future)
    # price_spot = api_spot.get_ask(format_ticker_for_spot_api(ticker))
    price_spot = api_spot.get_ask(ticker)

    # buy btc spot
    notional_crypto = (notional_usd / price_spot)
    if fee == "taker":
        notional_crypto = notional_crypto * (1 - api_spot.get_fees_taker(ticker))
    if fee == "maker":
        notional_crypto = notional_crypto * (1 - api_spot.get_fees_maker(ticker))
    # short btc fut for same notional
    trade_profit_future = notional_crypto * price_future
    if fee == "taker":
        trade_profit_future = trade_profit_future * (1 - api_future.get_fees_taker()) * (1 - api_future.get_fees_taker()) * (
                1 - api_spot.get_fees_taker(ticker))
    if fee == "maker":
        trade_profit_future = trade_profit_future * (1 - api_future.get_fees_maker()) * (1 - api_future.get_fees_maker()) * (
                1 - api_spot.get_fees_maker(ticker))
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
