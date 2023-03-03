import decimal
import math


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
