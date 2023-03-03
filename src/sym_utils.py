def format_ticker_for_spot_api(ticker):
    if ticker == "bchusd" or ticker == "BCHUSD":
        return "BCHUSD"
    elif ticker[0] == "X" and ticker[4] == "Z":
        return ticker
    else:
        return "X" + ticker.upper()[:3] + "Z" + ticker.upper()[3:]


def get_lhs(ticker):
    i = int(len(ticker) / 2)
    return ticker[:i]


def get_rhs(ticker):
    i = int(len(ticker) / 2)
    return ticker[i:]


def get_spot_ticker(future_ticker):
    return future_ticker.split("_")[1]


def get_sym_from_future_ticker(ticker):
    return ticker.split("_")[1].upper()
