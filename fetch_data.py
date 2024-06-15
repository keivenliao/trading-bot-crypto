from distutils import errors
import ccxt
import pandas as pd
import logging
import pandas_ta as ta
from typing import Tuple, List
from datetime import datetime
import os
import time

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
    retries = 3
    while retries > 0:
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
            logging.error("Network error while fetching OHLCV data: %s", net_error)
            retries -= 1
            if retries > 0:
                logging.info("Retrying... (%d retries left)", retries)
                time.sleep(5)  # Wait for 5 seconds before retrying
            else:
                raise net_error
        except ccxt.ExchangeError as exchange_error:
            logging.error("Exchange error while fetching OHLCV data: %s", exchange_error)
            raise exchange_error
        except ccxt.BaseError as base_error:
            logging.error("Unexpected error while fetching OHLCV data: %s", base_error)
            raise base_error

def perform_technical_analysis(df: pd.DataFrame, sma_lengths: Tuple[int, int] = (20, 50), rsi_length: int = 14, macd_params: Tuple[int, int, int] = (12, 26, 9)) -> pd.DataFrame:
    """
    Perform technical analysis on the OHLCV data DataFrame.
    
    Args:
    - df: DataFrame containing OHLCV data
    - sma_lengths: Tuple containing lengths for SMAs (default: (20, 50))
    - rsi_length: Length for RSI (default: 14)
    - macd_params: Tuple containing MACD parameters (fast, slow, signal) (default: (12, 26, 9))
    
    Returns:
    - df: DataFrame with added technical indicators
    """
    try:
        # Adding technical indicators
        sma_short, sma_long = sma_lengths
        macd_fast, macd_slow, macd_signal = macd_params
        
        df.ta.sma(length=sma_short, append=True)
        df.ta.sma(length=sma_long, append=True)
        df.ta.rsi(length=rsi_length, append=True)
        df.ta.macd(fast=macd_fast, slow=macd_slow, signal=macd_signal, append=True)
        
        # Log detected patterns
        logging.info("Calculated SMA (%d, %d), RSI (%d), and MACD (%d, %d, %d) indicators", sma_short, sma_long, rsi_length, macd_fast, macd_slow, macd_signal)
        
        # Detecting bullish or bearish signals
        detect_signals(df, sma_lengths)
        
        return df
    except Exception as e:
        logging.error("An error occurred during technical analysis: %s", e)
        raise e

def detect_signals(df: pd.DataFrame, sma_lengths: Tuple[int, int]) -> None:
    """
    Detect bullish or bearish signals in the OHLCV data.
    
    Args:
    - df: DataFrame containing OHLCV data
    - sma_lengths: Tuple containing lengths for SMAs
    """
    try:
        sma_short, sma_long = sma_lengths
        # Example signal detection for educational purposes
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Simple crossover strategy
        if previous[f'SMA_{sma_short}'] < previous[f'SMA_{sma_long}'] and latest[f'SMA_{sma_short}'] > latest[f'SMA_{sma_long}']:
            logging.info("Bullish crossover detected")
        elif previous[f'SMA_{sma_short}'] > previous[f'SMA_{sma_long}'] and latest[f'SMA_{sma_short}'] < latest[f'SMA_{sma_long}']:
            logging.info("Bearish crossover detected")
        
        # RSI Overbought/Oversold
        if latest['RSI_14'] > 70:
            logging.info("RSI indicates overbought conditions")
        elif latest['RSI_14'] < 30:
            logging.info("RSI indicates oversold conditions")
        
        # MACD Bullish/Bearish signal
        if previous['MACD_12_26_9'] < previous['MACDs_12_26_9'] and latest['MACD_12_26_9'] > latest['MACDs_12_26_9']:
            logging.info("Bullish MACD crossover detected")
        elif previous['MACD_12_26_9'] > previous['MACDs_12_26_9'] and latest['MACD_12_26_9'] < latest['MACDs_12_26_9']:
            logging.info("Bearish MACD crossover detected")
        
    except Exception as e:
        logging.error("An error occurred during signal detection: %s", e)
        raise e

def fetch_historical_data(exchange, symbol='BTC/USDT', timeframe='1d', limit=365):
    """
    Fetch historical OHLCV data for a symbol from the exchange.

    Args:
    - exchange: ccxt.Exchange object
    - symbol: Trading pair symbol (default: 'BTC/USDT')
    - timeframe: Timeframe for OHLCV data (default: '1d')
    - limit: Number of data points to fetch (default: 365)

    Returns:
    - df: DataFrame containing OHLCV data
    """
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        logging.info(f"Fetched OHLCV data for {symbol}")
        return df
    except Exception as e:
        logging.error(f"An error occurred while fetching data: {e}")
        raise e

# Example usage
def new_func():
    errors

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

        # Fetch historical data
        symbol = 'BTC/USDT'
        df = fetch_historical_data(exchange, symbol)

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
        # Handle missing environment variables or other value-related
        new_func()
    except Exception as error:
        logging.error("An unexpected error occurred: %s", error)
    # Handle any other unexpected errors