import pyupbit
import pandas as pd
import time
import upbit_functions

access = 'access key'
secret = 'secret key

upbit = pyupbit.Upbit(access, secret)

def load_markets():
    markets = pyupbit.get_tickers()
    for market in markets:
        if 'BTC-' in market:
            btc_markets.append(market)
        elif 'KRW-' in market:
            krw_markets.append(market)
        elif 'ETH-' in market:
            eth_markets.append(market)
        elif 'USDT-' in market:
            usdt_markets.append(market)
        else:
            print('unknown market: {}'.format(market['market']))

krw_markets = []
btc_markets = []
eth_markets = []
usdt_markets = []

load_markets()

while True: 
    for i in range(len(krw_markets)): 
        candle_data = modules.get_candle(krw_markets[i], '3', 200)

        now_rsi = modules.get_rsi(candle_data)
        now_macd = modules.get_macd(candle_data, 1)
        now_mfi = modules.get_mfi(candle_data)

        time.sleep(1)