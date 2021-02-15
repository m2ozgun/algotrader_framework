import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
import pytz
import strategy_utils
import constants
import sys

from agent_utils import calc_daily_lost_trades, close_positions_by_symbol, close_position, get_positions, open_position

my_acc = 41452978


class Trader:
    def __init__(self, account_id, trader_strategy):
        self.account_id = account_id
        self.authorized = False
        self.moving_averages = trader_strategy['moving_averages']
        self.max_losses = trader_strategy["max_losses"]
        self.account_currency = trader_strategy["account_currency"]
        self.risk = trader_strategy["risk"]
        self.stop_loss = trader_strategy["stop_loss"]
        self.take_profit = trader_strategy["take_profit"]
        self.pairs = trader_strategy["pairs"]

    def connect(self):
        account = int(self.account_id)
        mt5.initialize()

        try:
            self.authorized = mt5.login(self.account_id)
        except not self.authorized:
            print(f"Failed to connect at account #{account}, error code: {mt5.last_error()}")

    def run(self, time_frame):
        print("Running trader at", datetime.now())
        self.connect()
        pair_data = self.get_data(time_frame)
        self.check_trades(time_frame, pair_data)

    def get_data(self, time_frame):
        pair_data = dict()
        for pair in self.pairs:
            utc_from = datetime(2021, 1, 1)
            date_to = datetime.now().astimezone(pytz.timezone('Europe/Athens'))
            date_to = datetime(date_to.year, date_to.month, date_to.day, hour=date_to.hour, minute=date_to.minute)
            rates = mt5.copy_rates_range(pair, time_frame, utc_from, date_to)
            rates_df = pd.DataFrame(rates)
            rates_df["time"] = pd.to_datetime(rates_df["time"], unit='s')
            rates_df.drop(rates_df.tail(1).index, inplace=True)
            pair_data[pair] = rates_df

        return pair_data

    def check_trades(self, time_frame, pair_data):

        for pair, data in pair_data.items():
            for m in self.moving_averages:
                ma_fnc = constants.moving_averages_functions[m]
                val = self.moving_averages[m]['val']
                data[m] = ma_fnc(data['close'], val)

            last_row = data.tail(1)
            open_positions = get_positions(pair)
            current_dt = datetime.now().astimezone(pytz.timezone('Europe/Athens'))

            # Time limit
            for index, position in open_positions.iterrows():
                trade_open_dt = position['time'].replace(tzinfo=pytz.timezone('Europe/Athens'))
                deal_id = position["ticket"]
                if current_dt - trade_open_dt >= timedelta(minutes=1):
                    close_position(deal_id)

            for index, last in last_row.iterrows():
                # SELL strategy
                if last['EMA'] > last['close'] > last['SMA']:
                    close_positions_by_symbol(pair)

                lost_trade_count = calc_daily_lost_trades()

                if lost_trade_count > self.max_losses:
                    print("Daily losses have been exceeded, no more trading for today")
                    continue

                # BUY strategy
                if last['EMA'] < last['close'] < last['SMA']:
                    lot_size = self.calc_position_size(pair)
                    open_position(pair, "BUY", lot_size, float(self.take_profit),
                                  float(self.stop_loss))

    def calc_position_size(self, symbol):
        print(f"Calculation position size for: {symbol}")
        balance = mt5.account_info().balance
        pip_value = constants.get_pip_value(symbol, self.account_currency)

        # Lot size = (balance * risk) / pip value * stop loss
        lot_size = (float(balance) * (float(self.risk) / 100)) / (pip_value * self.stop_loss)
        lot_size = round(lot_size, 2)
        return lot_size



