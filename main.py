import sys
import time

import MetaTrader5 as mt5
import schedule

from strategy_utils import load_strategy
from trader import Trader


def trade(trader):
    schedule.every().hour.at(":00").do(trader.run, mt5.TIMEFRAME_M15)
    schedule.every().hour.at(":15").do(trader.run, mt5.TIMEFRAME_M15)
    schedule.every().hour.at(":30").do(trader.run, mt5.TIMEFRAME_M15)
    schedule.every().hour.at(":45").do(trader.run, mt5.TIMEFRAME_M15)

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    # Create strategy
    strategy = sys.argv[1]
    print(f"Trader started with strategy: {strategy}")
    strategy_json = load_strategy(strategy)

    trader = Trader(41452978, strategy_json)

    trade(trader)
