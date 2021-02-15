from datetime import datetime

import MetaTrader5 as mt5
import pandas as pd
import pytz


def get_order_history(date_from, date_to):
    res = mt5.history_deals_get(date_from, date_to)

    if res is not None and res != ():
        df = pd.DataFrame(list(res), columns=res[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    return pd.DataFrame()


def calc_daily_lost_trades():
    now = datetime.now().astimezone(pytz.timezone('Europe/Athens'))
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    res = get_order_history(midnight, now)
    if res.empty:
        return 0
    else:
        lost_trade_count = 0
        for i, row in res.iterrows():
            profit = float(row['profit'])
            if profit < 0:
                lost_trade_count = lost_trade_count + 1

        return lost_trade_count


def close_positions_by_symbol(symbol):
    open_positions = get_positions(symbol)
    open_positions['ticket'].apply(lambda x: close_position(x))


def close_position(deal_id):
    open_positions = get_positions()
    open_positions = open_positions[open_positions["ticket"] == deal_id]

    order_type = open_positions["type"][0]
    symbol = open_positions["symbol"][0]
    volume = open_positions["volume"][0]

    if order_type == mt5.ORDER_TYPE_BUY:
        order_type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
    else:
        order_type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(volume),
        "type": order_type,
        "position": deal_id,
        "price": price,
        "magic": 234000,
        "comment": "Close trade",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = None
    try:
        result = mt5.order_send(request)
    except result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        print("Unable to close order")
        return

    print(f"{symbol} Order closed")
    return result.retcode


def get_positions(symbol=None):
    if symbol is None:
        res = mt5.positions_get()
    else:
        res = mt5.positions_get(symbol=symbol)

    if res is not None and res != ():
        df = pd.DataFrame(list(res), columns=res[0]._asdict().keys())
        df["time"] = pd.to_datetime(df["time"], unit='s')
        return df

    return pd.DataFrame()


def open_position(symbol, order_type, volume, tp_distance=None, stop_distance=None):
    symbol_info = mt5.symbol_info(symbol)
    sl, tp, order, price = None, None, None, None

    if symbol_info is None:
        print(f"{symbol} is not found")
        return

    if not symbol_info.visible:
        print(f"{symbol} is not visible, trying to switch on")
        if not mt5.symbol_select(symbol, True):
            print(f"symbol_select for {symbol} is failed, exiting")
            return
    print(f"{symbol} found")

    point = symbol_info.point

    if order_type == "BUY":
        order = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask
        if stop_distance:
            sl = price - (stop_distance * point)
        if tp_distance:
            tp = price + (tp_distance * point)

    if order_type == "SELL":
        order = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
        if stop_distance:
            sl = price + (stop_distance * point)
        if tp_distance:
            tp = price - (tp_distance * point)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(volume),
        "type": order,
        "price": price,
        "sl": sl,
        "tp": tp,
        "magic": 234000,
        "comment": "",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC
    }

    result = None
    try:
        result = mt5.order_send(request)
    except result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
        print("Unable to send order")
        return

    print(f"{symbol} Order sent")
    return result.retcode