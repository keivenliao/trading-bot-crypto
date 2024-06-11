import ccxt
import pandas as pd
import time
import logging
import ta
import os
from synchronize_exchange_time import synchronize_time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Setup environment variables for API credentials
API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')

if not API_KEY or not API_SECRET:
    logging.error("API key and secret must be set as environment variables")
    exit(1)

# Initialize the Bybit exchange
def initialize_exchange(api_key, api_secret):
    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,  # This helps to avoid rate limit errors
        })
        logging.info("Initialized Bybit exchange")
        return exchange
    except ccxt.BaseError as e:
        logging.error("Failed to initialize exchange: %s", e)
        raise e

# Function to fetch historical data
def fetch_ohlcv(exchange, symbol, timeframe='1h', limit=100, time_offset=0):
    params = {
        'recvWindow': 10000,  # Increased to 10000 milliseconds (10 seconds)
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

# Function to calculate indicators
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

# Define the trading strategy
def trading_strategy(df):
    signals = ['hold']  # Initialize with 'hold' for the first entry
    for i in range(1, len(df)):
        if df['SMA_50'][i] > df['SMA_200'][i] and df['SMA_50'][i-1] <= df['SMA_200'][i-1]:
            signals.append('buy')
        elif df['SMA_50'][i] < df['SMA_200'][i] and df['SMA_50'][i-1] >= df['SMA_200'][i-1]:
            signals.append('sell')
        else:
            signals.append('hold')
    df['signal'] = signals
    logging.info("Defined trading strategy")
    return df

# Function to execute trades
def execute_trade(exchange, symbol, signal):
    """
    Execute trades based on signals.
    """
    amount = 1  # Placeholder amount for demonstration purposes
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

# Main function to orchestrate the workflow
def main():
    try:
        # Attempt time synchronization
        time_offset = synchronize_time()
        logging.info("Time synchronized with offset: %d", time_offset)
        
        # Initialize exchange
        exchange = initialize_exchange(API_KEY, API_SECRET)
        
        # Fetch data, calculate indicators, and apply strategy
        df = fetch_ohlcv(exchange, 'BTC/USDT', time_offset=time_offset)
        df = calculate_indicators(df)
        df = trading_strategy(df)
        
        # Execute trades based on signals
        for _, row in df.iterrows():
            execute_trade(exchange, 'BTC/USDT', row['signal'])
        
        # Output the resulting DataFrame
        print(df.tail())
        
    except Exception as e:
        logging.error("An error occurred during the main execution: %s", e)

# Run the main function
if __name__ == "__main__":
    main()
