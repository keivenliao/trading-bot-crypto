import time
import ccxt
import pandas as pd
import logging
from main import calculate_indicators
from synchronize_exchange_time import synchronize_time
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Retrieve API keys from environment variables
API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')

def initialize_exchange(api_key, api_secret):
    """
    Initialize the Bybit exchange.
    """
    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })
        logging.info("Initialized Bybit exchange")
        return exchange
    except Exception as e:
        logging.error("Failed to initialize exchange: %s", e)
        raise e

def fetch_ohlcv(exchange, symbol, timeframe='1h', limit=100, time_offset=0):
    """
    Fetch OHLCV data from the exchange.
    """
    params = {
        'recvWindow': 10000,
        'timestamp': int(time.time() * 1000 + time_offset)
    }
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, params=params)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        logging.info(f"Fetched OHLCV data for {symbol}")
        return df
    except ccxt.BaseError as e:
        logging.error("Error fetching OHLCV data: %s", e)
        raise e

def generate_trading_signals(df):
    """
    Define the trading strategy based on technical indicators.
    """
    try:
        signals = ['hold']
        for i in range(1, len(df)):
            if df['SMA_50'][i] > df['SMA_200'][i] and df['SMA_50'][i-1] <= df['SMA_200'][i-1]:
                signals.append('buy')
            elif df['SMA_50'][i] < df['SMA_200'][i] and df['SMA_50'][i-1] >= df['SMA_200'][i-1]:
                signals.append('sell')
            else:
                signals.append('hold')
        df['signal'] = signals
        logging.info("Generated trading signals")
        return df
    except Exception as e:
        logging.error("Failed to generate trading signals: %s", e)
        raise e

def execute_trade(exchange, symbol, signal, amount=0.001):
    """
    Execute trades based on trading signals.
    """
    try:
        if signal == 'buy':
            logging.info("Executing Buy Order")
            order = exchange.create_market_buy_order(symbol, amount)
        elif signal == 'sell':
            logging.info("Executing Sell Order")
            order = exchange.create_market_sell_order(symbol, amount)
        else:
            logging.info("No trade action needed (hold signal)")
            return
        
        if 'error' in order:
            logging.error("Failed to execute order: %s", order['error'])
        else:
            logging.info("Order executed successfully: %s", order)
    except ccxt.BaseError as e:
        logging.error("An error occurred during trade execution: %s", e)

def main():
    """
    Main function to orchestrate the workflow.
    """
    try:
        if not API_KEY or not API_SECRET:
            logging.error("API key and secret must be set as environment variables")
            return

        time_offset = synchronize_time()
        logging.info("Time synchronized with offset: %d", time_offset)
        
        exchange = initialize_exchange(API_KEY, API_SECRET)
        
        df = fetch_ohlcv(exchange, 'BTC/USDT', time_offset=time_offset)
        df = calculate_indicators(df)
        df = generate_trading_signals(df)
        
        df.apply(lambda row: execute_trade(exchange, 'BTC/USDT', row['signal']), axis=1)
        
        print(df.tail())
        
    except Exception as e:
        logging.error("An error occurred during the main execution: %s", e)

if __name__ == "__main__":
    main()


'''import pandas_ta as ta
import logging

def calculate_technical_indicators(df):
    """
    Calculate technical indicators for a given DataFrame.
    """
    try:
        df['SMA_50'] = ta.sma(df['close'], length=50)
        df['SMA_200'] = ta.sma(df['close'], length=200)
        df['EMA_12'] = ta.ema(df['close'], length=12)
        df['EMA_26'] = ta.ema(df['close'], length=26)
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        df['MACD'] = macd['MACD_12_26_9']
        df['MACD_signal'] = macd['MACDs_12_26_9']
        df['RSI'] = ta.rsi(df['close'], length=14)
        logging.info("Calculated technical indicators")
        return df
    except Exception as e:
        logging.error("Failed to calculate technical indicators: %s", e)
        raise e'''
