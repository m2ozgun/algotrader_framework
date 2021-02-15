import talib as ta
from forex_python.converter import CurrencyRates

moving_averages_functions = {
    'SMA': lambda close, time_p: ta.SMA(close, time_p),
    'EMA': lambda close, time_p: ta.EMA(close, time_p),
    'WMA': lambda close, time_p: ta.WMA(close, time_p),
    'LINEAR_REG': lambda close, time_p: ta.LINEARREG(close, time_p),
    'TRIMA': lambda close, time_p: ta.TRIMA(close, time_p),
    'DEMA': lambda close, time_p: ta.DEMA(close, time_p),
    'HT_TRENDLINE': lambda close, time_p: ta.HT_TRENDLINE(close, time_p),
    'TSF': lambda close, time_p: ta.TSF(close, time_p)
}


def get_pip_value(symbol, account_currency):
    first_symbol = symbol[0:3]
    second_symbol = symbol[3:6]
    c = CurrencyRates()
    return c.convert(second_symbol, account_currency, c.convert(first_symbol, second_symbol, 1))
