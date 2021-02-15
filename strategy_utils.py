import json
import os

def load_strategy(strategy_file):
    with open(strategy_file) as json_file:
        data = json.load(json_file)
        return data

