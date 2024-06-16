import ccxt
import pandas as pd
import logging
import os
import time
import ntplib
import ta
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables for API credentials
API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')

def synchronize_system_time():
    """
    Synchronize system time with an NTP server.
    """
    try:
        response = ntplib.NTPClient().request('pool.ntp.org')
        current_time = datetime.fromtimestamp(response.tx_time)
        logging.info(f"System time synchronized: {current_time}")
        return int((current_time - datetime.utcnow()).total_seconds() * 1000)  # Return time offset in milliseconds
    except Exception as e:
        logging.error("Time synchronization failed: %s", e)
        return 0  # Return zero offset in case of failure

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
    except ccxt.BaseError as e:
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
    Calculate technical indicators using pandas_ta library.
    """
    try:
        df.ta.sma(length=50, append=True)
        df.ta.sma(length=200, append=True)
        df.ta.ema(length=12, append=True)
        df.ta.ema(length=26, append=True)
        df.ta.macd(append=True)
        df.ta.rsi(length=14, append=True)
        logging.info("Calculated technical indicators")
    except Exception as e:
        logging.error("Error calculating indicators: %s", e)
        raise e
    return df

def trading_strategy(df, sma_short=50, sma_long=200):
    """
    Define the trading strategy based on SMA crossover.
    """
    signals = ['hold']  # Initialize with 'hold' for the first entry
    for i in range(1, len(df)):
        if df['SMA_' + str(sma_short)][i] > df['SMA_' + str(sma_long)][i] and df['SMA_' + str(sma_short)][i-1] <= df['SMA_' + str(sma_long)][i-1]:
            signals.append('buy')
        elif df['SMA_' + str(sma_short)][i] < df['SMA_' + str(sma_long)][i] and df['SMA_' + str(sma_short)][i-1] >= df['SMA_' + str(sma_long)][i-1]:
            signals.append('sell')
        else:
            signals.append('hold')
    df['signal'] = signals
    logging.info("Defined trading strategy")
    return df

def execute_trade(exchange, symbol, signal, amount=1):
    """
    Execute trades based on signals.
    """
    try:
        if signal == 'buy':
            logging.info("Executing Buy Order")
            exchange.create_market_buy_order(symbol, amount)
        elif signal == 'sell':
            logging.info("Executing Sell Order")
            exchange.create_market_sell_order(symbol, amount)
    except ccxt.BaseError as e:
        logging.error(f"Error executing {signal} order: {e}")
        raise e
    

def generate_signals(df):
    # Calculate Moving Averages
    df['SMA_50'] = ta.sma(df['close'], length=50)
    df['SMA_200'] = ta.sma(df['close'], length=200)
    
    # Calculate MACD
    macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
    df['MACD'] = macd['MACD_12_26_9']
    df['MACD_signal'] = macd['MACDs_12_26_9']
    
    # Calculate RSI
    df['RSI'] = ta.rsi(df['close'], length=14)
    
    # Generate Buy and Sell Signals
    df['Buy_Signal'] = (df['close'] > df['SMA_50']) & (df['SMA_50'] > df['SMA_200']) & (df['MACD'] > df['MACD_signal']) & (df['RSI'] < 70)
    df['Sell_Signal'] = (df['close'] < df['SMA_50']) & (df['SMA_50'] < df['SMA_200']) & (df['MACD'] < df['MACD_signal']) & (df['RSI'] > 30)
    
    return df


def main():
    try:
        # Synchronize time with NTP server
        time_offset = synchronize_system_time()
        logging.info("Time synchronized with offset: %d", time_offset)
        
        # Initialize exchange
        exchange = initialize_exchange(API_KEY, API_SECRET)
        
        # Fetch OHLCV data
        df = fetch_ohlcv(exchange, 'BTC/USDT', time_offset=time_offset)
        
        # Calculate technical indicators
        df = calculate_indicators(df)
        
        # Define trading strategy
        df = trading_strategy(df)
        
        # Execute trades based on signals
        for _, row in df.iterrows():
            execute_trade(exchange, 'BTC/USDT', row['signal'])
        
        # Output the resulting DataFrame
        print(df.tail())
        
    except Exception as e:
        logging.error("An error occurred during the main execution: %s", e)

if __name__ == "__main__":
    main()
