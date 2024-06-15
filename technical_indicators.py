#HAS ERROR



import time
import ccxt
import pandas as pd
import logging
from synchronize_exchange_time import synchronize_system_time
import pandas_ta as ta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_KEY = 'YOUR_API_KEY'
API_SECRET = 'YOUR_API_SECRET'

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

def calculate_indicators(df):
    """
    Calculate technical indicators.
    """
    df['SMA_50'] = ta.sma(df['close'], length=50)
    df['SMA_200'] = ta.sma(df['close'], length=200)
    df['EMA_12'] = ta.ema(df['close'], length=12)
    df['EMA_26'] = ta.ema(df['close'], length=26)
    df['MACD'], df['MACD_signal'], _ = ta.macd(df['close'], fast=12, slow=26, signal=9)
    df['RSI'] = ta.rsi(df['close'], length=14)
    logging.info("Calculated technical indicators")
    return df

def trading_strategy(df):
    """
    Define the trading strategy based on technical indicators.
    """
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
        time_offset = synchronize_system_time()
        logging.info("Time synchronized with offset: %d ms", time_offset)
        
        exchange = initialize_exchange(API_KEY, API_SECRET)
        
        df = fetch_ohlcv(exchange, 'BTC/USDT', time_offset=time_offset)
        df = calculate_indicators(df)
        df = trading_strategy(df)
        
        df.apply(lambda row: execute_trade(exchange, 'BTC/USDT', row['signal']), axis=1)
        
        print(df.tail())
        
    except Exception as e:
        logging.error("An error occurred during the main execution: %s", e)

if __name__ == "__main__":
    main()
