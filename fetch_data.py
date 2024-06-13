import ccxt
import pandas as pd
import logging
import pandas_ta as ta
from typing import Tuple, List
from datetime import datetime
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def synchronize_time_with_exchange(exchange: ccxt.Exchange) -> int:
    """
    Synchronize the local system time with the exchange server time.
    
    Args:
    - exchange: ccxt.Exchange object
    
    Returns:
    - time_offset: Time offset in milliseconds
    """
    try:
        server_time = exchange.milliseconds()
        local_time = int(datetime.now().timestamp() * 1000)
        time_offset = server_time - local_time
        logging.info("Time synchronized with exchange. Offset: %d milliseconds", time_offset)
        return time_offset
    except ccxt.BaseError as sync_error:
        logging.error("Failed to synchronize time with exchange: %s", sync_error)
        raise sync_error

def fetch_ohlcv(exchange: ccxt.Exchange, symbol: str, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
    """
    Fetch OHLCV data for a given symbol and timeframe from the exchange.
    
    Args:
    - exchange: ccxt.Exchange object
    - symbol: Trading pair symbol (e.g., 'BTC/USDT')
    - timeframe: Timeframe for OHLCV data (default: '1h')
    - limit: Number of data points to fetch (default: 100)
    
    Returns:
    - df: DataFrame containing OHLCV data
    """
    try:
        # Synchronize time with exchange
        time_offset = synchronize_time_with_exchange(exchange)
        
        # Fetch OHLCV data
        params = {
            'recvWindow': 10000,  # Adjust recvWindow as needed
            'timestamp': exchange.milliseconds() + time_offset
        }
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, params=params)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        logging.info("Fetched OHLCV data for %s", symbol)
        
        return df
    except ccxt.NetworkError as net_error:
        logging.error("A network error occurred while fetching OHLCV data: %s", net_error)
        raise net_error
    except ccxt.ExchangeError as exchange_error:
        logging.error("An exchange error occurred while fetching OHLCV data: %s", exchange_error)
        raise exchange_error
    except ccxt.BaseError as base_error:
        logging.error("An unexpected error occurred while fetching OHLCV data: %s", base_error)
        raise base_error

def perform_technical_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform technical analysis on the OHLCV data DataFrame.
    
    Args:
    - df: DataFrame containing OHLCV data
    
    Returns:
    - df: DataFrame with added technical indicators
    """
    try:
        # Adding technical indicators
        df.ta.sma(length=20, append=True)
        df.ta.sma(length=50, append=True)
        df.ta.rsi(length=14, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        
        # Log detected patterns
        logging.info("Calculated SMA, RSI, and MACD indicators")
        
        # Detecting bullish or bearish signals
        detect_signals(df)
        
        return df
    except Exception as e:
        logging.error("An error occurred during technical analysis: %s", e)
        raise e

def detect_signals(df: pd.DataFrame) -> None:
    """
    Detect bullish or bearish signals in the OHLCV data.
    
    Args:
    - df: DataFrame containing OHLCV data
    """
    try:
        # Example signal detection for educational purposes
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Simple crossover strategy
        if previous['SMA_20'] < previous['SMA_50'] and latest['SMA_20'] > latest['SMA_50']:
            logging.info("Bullish crossover detected")
        elif previous['SMA_20'] > previous['SMA_50'] and latest['SMA_20'] < latest['SMA_50']:
            logging.info("Bearish crossover detected")
        
        # RSI Overbought/Oversold
        if latest['RSI'] > 70:
            logging.info("RSI indicates overbought conditions")
        elif latest['RSI'] < 30:
            logging.info("RSI indicates oversold conditions")
        
        # MACD Bullish/Bearish signal
        if previous['MACD'] < previous['MACD_signal'] and latest['MACD'] > latest['MACD_signal']:
            logging.info("Bullish MACD crossover detected")
        elif previous['MACD'] > previous['MACD_signal'] and latest['MACD'] < latest['MACD_signal']:
            logging.info("Bearish MACD crossover detected")
        
    except Exception as e:
        logging.error("An error occurred during signal detection: %s", e)
        raise e

# Example usage
if __name__ == "__main__":
    try:
        # Retrieve API keys and secrets from environment variables
        api_key = os.getenv('BYBIT_API_KEY')
        api_secret = os.getenv('BYBIT_API_SECRET')

        if not api_key or not api_secret:
            raise ValueError("BYBIT_API_KEY or BYBIT_API_SECRET environment variables are not set.")

        # Initialize the Bybit exchange
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,  # This helps to avoid rate limit errors
        })

        # Fetch data
        symbol = 'BTC/USDT'
        df = fetch_ohlcv(exchange, symbol)

        # Perform technical analysis
        df = perform_technical_analysis(df)

        # Print first few rows of data
        print(df.head())
    
    except ccxt.NetworkError as net_error:
        logging.error("A network error occurred: %s", net_error)
        # Retry or handle the error as needed
    except ccxt.ExchangeError as exchange_error:
        logging.error("An exchange error occurred: %s", exchange_error)
        # Handle the exchange-specific error
    except ValueError as value_error:
        logging.error("Value error occurred: %s", value_error)
        # Handle missing environment variables or other value-related errors
    except Exception as error:
        logging.error("An unexpected error occurred: %s", error)
        # Handle any other unexpected errors
