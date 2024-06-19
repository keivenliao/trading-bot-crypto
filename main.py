import logging
import os
import ccxt
from retrying import retry
import pandas as pd
import time
from datetime import datetime
import ta

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_api_credentials():
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    if not api_key or not api_secret:
        raise ValueError("BYBIT_API_KEY or BYBIT_API_SECRET environment variables are not set.")
    return api_key, api_secret

def initialize_exchange(api_key, api_secret):
    exchange = ccxt.bybit({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    })
    logging.info("Initialized Bybit exchange")
    return exchange

@retry(stop_max_attempt_number=3, wait_fixed=2000)
def fetch_ohlcv_with_retry(exchange, symbol, timeframe='1h', limit=500):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        logging.info(f"Fetched OHLCV data for {symbol}")
        return df
    except ccxt.BaseError as e:
        logging.error("Error fetching OHLCV data: %s", e)
        raise e

def calculate_indicators(df):
    try:
        df['SMA_50'] = ta.trend.sma_indicator(df['close'], window=50)
        df['SMA_200'] = ta.trend.sma_indicator(df['close'], window=200)
        df['EMA_12'] = ta.trend.ema_indicator(df['close'], window=12)
        df['EMA_26'] = ta.trend.ema_indicator(df['close'], window=26)
        macd = ta.trend.MACD(df['close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['RSI'] = ta.momentum.rsi(df['close'], window=14)
        logging.info("Calculated technical indicators")
        return df
    except Exception as e:
        logging.error("Error calculating indicators: %s", e)
        raise e

def trading_strategy(df, sma_short=50, sma_long=200):
    try:
        signals = ['hold']
        for i in range(1, len(df)):
            if df['SMA_' + str(sma_short)].iloc[i] > df['SMA_' + str(sma_long)].iloc[i] and df['SMA_' + str(sma_short)].iloc[i-1] <= df['SMA_' + str(sma_long)].iloc[i-1]:
                signals.append('buy')
            elif df['SMA_' + str(sma_short)].iloc[i] < df['SMA_' + str(sma_long)].iloc[i] and df['SMA_' + str(sma_short)].iloc[i-1] >= df['SMA_' + str(sma_long)].iloc[i-1]:
                signals.append('sell')
            else:
                signals.append('hold')
        df['signal'] = signals
        logging.info("Defined trading strategy")
        return df
    except KeyError as e:
        logging.error("Error detecting signals: %s", e)
        raise e

def execute_trade(exchange, symbol, signal, amount=1):
    try:
        if signal == 'buy':
            logging.info("Executing Buy Order")
            exchange.create_market_buy_order(symbol, amount)
        elif signal == 'sell':
            logging.info("Executing Sell Order")
            exchange.create_market_sell_order(symbol, amount)
    except ccxt.BaseError as e:
        logging.error(f"Error executing {signal} order: %s", e)
        raise e

def perform_backtesting(exchange):
    try:
        df = fetch_ohlcv_with_retry(exchange, 'BTCUSDT', timeframe='1h', limit=500)
        df = calculate_indicators(df)
        df = trading_strategy(df)
        logging.info("Backtesting complete")
        print(df.tail())
    except Exception as e:
        logging.error("Error during backtesting: %s", e)

def main():
    try:
        setup_logging()
        api_key, api_secret = load_api_credentials()
        exchange = initialize_exchange(api_key, api_secret)
        perform_backtesting(exchange)
    except ccxt.AuthenticationError as e:
        logging.error("Authentication error: %s. Please check your API key and secret.", e)
    except ccxt.NetworkError as e:
        logging.error("Network error: %s. Please check your internet connection.", e)
    except ccxt.ExchangeError as e:
        logging.error("Exchange error: %s. Please check the exchange status or API documentation.", e)
    except ValueError as e:
        logging.error("ValueError: %s", e)
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)

if __name__ == "__main__":
    main()
