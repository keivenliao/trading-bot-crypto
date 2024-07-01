from multiprocessing import Value
import os
import numpy as np
import pandas as pd
import ccxt
import logging
import time
from datetime import datetime
from textblob import TextBlob
from pandas_ta import sma, rsi, macd

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

def get_historical_data(exchange: ccxt.Exchange, symbol: str, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
    try:
        time_offset = synchronize_time_with_exchange(exchange)
        params = {
            'recvWindow': 10000,
            'timestamp': exchange.milliseconds() + time_offset
        }
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, params=params)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        logging.info("Fetched OHLCV data for %s", symbol)
        return df
    except ccxt.NetworkError as net_error:
        logging.error("Network error while fetching OHLCV data: %s", net_error)
        raise net_error
    except ccxt.ExchangeError as exchange_error:
        logging.error("Exchange error while fetching OHLCV data: %s", exchange_error)
        raise exchange_error
    except ccxt.BaseError as base_error:
        logging.error("Unexpected error while fetching OHLCV data: %s", base_error)
        raise base_error

def fetch_data(exchange, symbol='BTCUSDT', timeframe='1h', limit=100):
    """Fetch historical OHLCV data from the exchange."""
    attempts = 0
    max_attempts = 5
    while attempts < max_attempts:
        try:
            time_offset = synchronize_time_with_exchange(exchange)
            params = {'recvWindow': 10000, 'timestamp': exchange.milliseconds() + time_offset}
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, params=params)
        
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            logging.info("Fetched OHLCV data for %s", symbol)
            return df
        except (ccxt.NetworkError, ccxt.ExchangeError, ccxt.BaseError) as error:
            attempts += 1
            logging.error(f"Error fetching data (Attempt {attempts}/{max_attempts}): {error}")
            time.sleep(2 ** attempts)
    raise Exception("Failed to fetch data after multiple attempts")


def fetch_ohlcv(exchange: ccxt.Exchange, symbol: str, timeframe: str = '1h', limit: int = 00) -> pd.DataFrame:
    """
    Fetch OHLCV data.
    """
    try:
        params = {'recvWindow': 30000}  # Increase recv_window to 30 seconds
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, params=params)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        logging.info("Fetched OHLCV data")
        return df
    except ccxt.BaseError as e:
        logging.error("Failed to fetch OHLCV data: %s", e)
        raise

def get_tweets(query: str, count: int = 100):
    # Mock function to simulate fetching tweets
    tweets = [f"Tweet {i} about {query}" for i in range(count)]
    logging.info("Fetched %d tweets about %s", count, query)
    return tweets

def analyze_sentiment(tweets: list):
    sentiments = []
    for tweet in tweets:
        analysis = TextBlob(tweet)
        sentiments.append(analysis.sentiment.polarity)
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
    logging.info("Average sentiment polarity: %.2f", avg_sentiment)
    return avg_sentiment

def fetch_real_time_data(exchange: ccxt.Exchange, symbol: str, timeframe: str = '1m', limit: int = 100):
    """
    Fetch real-time OHLCV data for a symbol from the exchange.
    Continuously fetches new data points.
    
    Args:
    - exchange: ccxt.Exchange object
    - symbol: Trading pair symbol (e.g., 'BTC/USDT')
    - timeframe: Timeframe for OHLCV data (default: '1m')
    - limit: Number of data points to initially fetch (default: 100)
    """
    try:
        while True:
            # Fetch new data points
            new_df = fetch_historical_data(exchange, symbol, timeframe, limit)
            
            # Perform technical analysis on new data
            new_df = perform_technical_analysis(new_df)
            
            # Calculate additional indicators
            new_df = calculate_bollinger_bands(new_df)
            new_df = calculate_atr(new_df)
            new_df = calculate_vwma(new_df)
            new_df = calculate_obv(new_df)
            new_df = calculate_ichimoku_cloud(new_df)
            new_df = calculate_fibonacci_levels(new_df, new_df['low'].min(), new_df['high'].max())
            
            # Print or process new data as needed
            print(new_df.tail())  # Example: print last few rows of new data
            
            # Sleep for a minute (or desired interval)
            time.sleep(60)  # Sleep for 60 seconds (1 minute)
            
    except ccxt.NetworkError as net_error:
        logging.error("A network error occurred: %s", net_error)
        # Retry or handle the error as needed
    except ccxt.ExchangeError as exchange_error:
        logging.error("An exchange error occurred: %s", exchange_error)
        # Handle the exchange-specific error
    except Exception as error:
        logging.error("An unexpected error occurred: %s", error)
        # Handle any other unexpected errors

            
    except ccxt.NetworkError as net_error:
        logging.error("A network error occurred: %s", net_error)
        # Retry or handle the error as needed
    except ccxt.ExchangeError as exchange_error:
        logging.error("An exchange error occurred: %s", exchange_error)
        # Handle the exchange-specific error
    except Exception as error:
        logging.error("An unexpected error occurred: %s", error)
        # Handle any other unexpected errors

def fetch_historical_data(exchange: ccxt.Exchange, symbol: str, timeframe: str = '1h', limit: int = 100) -> pd.DataFrame:
    """
    Fetch historical OHLCV data from the specified exchange.
    
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
        logging.error("Network error while fetching OHLCV data: %s", net_error)
        raise net_error
    except ccxt.ExchangeError as exchange_error:
        logging.error("Exchange error while fetching OHLCV data: %s", exchange_error)
        raise exchange_error
    except ccxt.BaseError as base_error:
        logging.error("Unexpected error while fetching OHLCV data: %s", base_error)
        raise base_error

def perform_technical_analysis(df: pd.DataFrame, sma_lengths: tuple = (20, 50), rsi_length: int = 14, macd_params: tuple = (12, 26, 9)) -> pd.DataFrame:
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
        
        # Calculate SMAs
        df[f'SMA_{sma_short}'] = sma(df['close'], length=sma_short)
        df[f'SMA_{sma_long}'] = sma(df['close'], length=sma_long)
        
        # Calculate RSI
        df['RSI'] = rsi(df['close'], length=rsi_length)
        
        # Calculate MACD
        macd_data = macd(df['close'], fast=macd_fast, slow=macd_slow, signal=macd_signal)
        
        # Assign MACD values
        df['MACD'] = macd_data['MACD'] if 'MACD' in macd_data else None
        df['MACD_signal'] = macd_data['MACD_signal'] if 'MACD_signal' in macd_data else None
        
        # Log detected patterns
        logging.info("Calculated SMA (%d, %d), RSI (%d), and MACD (%d, %d, %d) indicators", sma_short, sma_long, rsi_length, macd_fast, macd_slow, macd_signal)
        
        detect_signals(df, sma_lengths)
        
        return df
    
    except Exception as e:
        logging.error("An error occurred during technical analysis: %s", e)
        raise e

def detect_signals(df: pd.DataFrame, sma_lengths: tuple) -> None:
    """
    Detect bullish or bearish signals in the OHLCV data.
    
    Args:
    - df: DataFrame containing OHLCV data
    - sma_lengths: Tuple containing lengths for SMAs
    """
    try:
        sma_short, sma_long = sma_lengths
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Example signal detection for SMA crossover
        if pd.notna(previous[f'SMA_{sma_short}']) and pd.notna(previous[f'SMA_{sma_long}']) and pd.notna(latest[f'SMA_{sma_short}']) and pd.notna(latest[f'SMA_{sma_long}']):
            if previous[f'SMA_{sma_short}'] < previous[f'SMA_{sma_long}'] and latest[f'SMA_{sma_short}'] > latest[f'SMA_{sma_long}']:
                logging.info("Bullish SMA crossover detected")
            elif previous[f'SMA_{sma_short}'] > previous[f'SMA_{sma_long}'] and latest[f'SMA_{sma_short}'] < latest[f'SMA_{sma_long}']:
                logging.info("Bearish SMA crossover detected")
        
        # Example signal detection for RSI conditions (using correct column name)
        if pd.notna(latest['RSI']):
            if latest['RSI'] > 70:
                logging.info("RSI indicates overbought conditions")
            elif latest['RSI'] < 30:
                logging.info("RSI indicates oversold conditions")
        
        # Example signal detection for MACD crossover (using correct column name)
        if pd.notna(previous['MACD']) and pd.notna(previous['MACD_signal']) and pd.notna(latest['MACD']) and pd.notna(latest['MACD_signal']):
            if previous['MACD'] < previous['MACD_signal'] and latest['MACD'] > latest['MACD_signal']:
                logging.info("Bullish MACD crossover detected")
            elif previous['MACD'] > previous['MACD_signal'] and latest['MACD'] < latest['MACD_signal']:
                logging.info("Bearish MACD crossover detected")
        
    except Exception as e:
        logging.error("An error occurred during signal detection: %s", e)
        raise e

def fetch_real_time_data(exchange: ccxt.Exchange, symbol: str, timeframe: str = '1m', limit: int = 100):
    """
    Fetch real-time OHLCV data for a symbol from the exchange.
    Continuously fetches new data points.
    
    Args:
    - exchange: ccxt.Exchange object
    - symbol: Trading pair symbol (e.g., 'BTC/USDT')
    - timeframe: Timeframe for OHLCV data (default: '1m')
    - limit: Number of data points to initially fetch (default: 100)
    """
    try:
        while True:
            # Fetch new data points
            new_df = fetch_historical_data(exchange, symbol, timeframe, limit)
            
            # Perform technical analysis on new data
            new_df = perform_technical_analysis(new_df)
            
            # Print or process new data as needed
            print(new_df.tail())  # Example: print last few rows of new data
            
            # Sleep for a minute (or desired interval)
            time.sleep(60)  # Sleep for 60 seconds (1 minute)
            
    except ccxt.NetworkError as net_error:
        logging.error("A network error occurred: %s", net_error)
        # Retry or handle the error as needed
    except ccxt.ExchangeError as exchange_error:
        logging.error("An exchange error occurred: %s", exchange_error)
        # Handle the exchange-specific error
    except Exception as error:
        logging.error("An unexpected error occurred: %s", error)
        # Handle any other unexpected errors

def calculate_bollinger_bands(df: pd.DataFrame, window: int = 20, std_dev: int = 2) -> pd.DataFrame:
    """
    Calculate Bollinger Bands (BB) for a given DataFrame.
    
    Args:
    - df: DataFrame containing OHLCV data
    - window: Window length for moving average (default: 20)
    - std_dev: Standard deviation multiplier for bands (default: 2)
    
    Returns:
    - df: DataFrame with added Bollinger Bands columns ('BB_Middle', 'BB_Upper', 'BB_Lower')
    """
    try:
        # Calculate rolling mean and standard deviation
        rolling_mean = df['close'].rolling(window=window).mean()
        rolling_std = df['close'].rolling(window=window).std()
        
        # Calculate Bollinger Bands
        df['BB_Middle'] = rolling_mean
        df['BB_Upper'] = rolling_mean + (rolling_std * std_dev)
        df['BB_Lower'] = rolling_mean - (rolling_std * std_dev)
        
        logging.info("Calculated Bollinger Bands with window %d and std dev %d", window, std_dev)
        
        return df
    
    except Exception as e:
        logging.error("An error occurred during Bollinger Bands calculation: %s", e)
        raise e

def calculate_atr(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    """
    Calculate Average True Range (ATR) for a given DataFrame.
    
    Args:
    - df: DataFrame containing OHLCV data
    - window: Window length for ATR calculation (default: 14)
    
    Returns:
    - df: DataFrame with added ATR column ('ATR')
    """
    try:
        # Calculate True Range
        df['TR'] = pd.DataFrame({
            'TR1': df['high'] - df['low'],
            'TR2': (df['high'] - df['close'].shift()).abs(),
            'TR3': (df['low'] - df['close'].shift()).abs()
        }).max(axis=1)
        
        # Calculate ATR
        df['ATR'] = df['TR'].rolling(window=window).mean()
        
        df.drop(columns=['TR'], inplace=True)  # Clean up temporary columns
        
        logging.info("Calculated Average True Range (ATR) with window %d", window)
        
        return df
    
    except Exception as e:
        logging.error("An error occurred during ATR calculation: %s", e)
        raise e

def calculate_vwma(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Calculate Volume Weighted Moving Average (VWMA) for a given DataFrame.
    
    Args:
    - df: DataFrame containing OHLCV data
    - window: Window length for VWMA calculation (default: 20)
    
    Returns:
    - df: DataFrame with added VWMA column ('VWMA')
    """
    try:
        # Calculate VWMA
        df['VWMA'] = (df['close'] * df['volume']).rolling(window=window).sum() / df['volume'].rolling(window=window).sum()
        
        logging.info("Calculated Volume Weighted Moving Average (VWMA) with window %d", window)
        
        return df
    
    except Exception as e:
        logging.error("An error occurred during VWMA calculation: %s", e)
        raise e

def calculate_obv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate On-Balance Volume (OBV) for a given DataFrame.
    
    Args:
    - df: DataFrame containing OHLCV data
    
    Returns:
    - df: DataFrame with added OBV column ('OBV')
    """
    try:
        # Calculate OBV
        df['OBV'] = np.where(df['close'] > df['close'].shift(), df['volume'], np.where(df['close'] < df['close'].shift(), -df['volume'], 0)).cumsum()
        
        logging.info("Calculated On-Balance Volume (OBV)")
        
        return df
    
    except Exception as e:
        logging.error("An error occurred during OBV calculation: %s", e)
        raise e

def calculate_ichimoku_cloud(df: pd.DataFrame, conversion_line_period: int = 9, base_line_period: int = 26, lagging_span2_period: int = 52, displacement: int = 26) -> pd.DataFrame:
    # Implementation remains the same as previously provided

    """
    Calculate Ichimoku Cloud components for a given DataFrame.
    
    Args:
    - df: DataFrame containing OHLCV data
    - conversion_line_period: Period for Conversion Line (default: 9)
    - base_line_period: Period for Base Line (default: 26)
    - lagging_span2_period: Period for Lagging Span 2 (default: 52)
    - displacement: Displacement (default: 26)
    
    Returns:
    - df: DataFrame with added Ichimoku Cloud columns ('Conversion_Line', 'Base_Line', 'Leading_Span_A', 'Leading_Span_B', 'Lagging_Span')
    """
    try:
        # Calculate Conversion Line
        conversion_line_high = df['high'].rolling(window=conversion_line_period).max()
        conversion_line_low = df['low'].rolling(window=conversion_line_period).min()
        df['Conversion_Line'] = (conversion_line_high + conversion_line_low) / 2
        
        # Calculate Base Line
        base_line_high = df['high'].rolling(window=base_line_period).max()
        base_line_low = df['low'].rolling(window=base_line_period).min()
        df['Base_Line'] = (base_line_high + base_line_low) / 2
        
        # Calculate Leading Span A
        df['Leading_Span_A'] = ((df['Conversion_Line'] + df['Base_Line']) / 2).shift(displacement)
        
        # Calculate Leading Span B
        leading_span_b_high = df['high'].rolling(window=lagging_span2_period).max()
        leading_span_b_low = df['low'].rolling(window=lagging_span2_period).min()
        df['Leading_Span_B'] = ((leading_span_b_high + leading_span_b_low) / 2).shift(displacement)
        
        # Calculate Lagging Span
        df['Lagging_Span'] = df['close'].shift(-displacement)
        
        logging.info("Calculated Ichimoku Cloud components with parameters: Conversion Line (%d), Base Line (%d), Lagging Span 2 (%d), Displacement (%d)", conversion_line_period, base_line_period, lagging_span2_period, displacement)
        
        return df
    
    except Exception as e:
        logging.error("An error occurred during Ichimoku Cloud calculation: %s", e)
        raise e

def calculate_fibonacci_levels(df: pd.DataFrame, low: float, high: float) -> pd.DataFrame:
    # Implementation remains the same as previously provided

    """
    Calculate Fibonacci Retracement levels for a given DataFrame.
    
    Args:
    - df: DataFrame containing OHLCV data
    - low: Lowest price in the range for Fibonacci retracement
    - high: Highest price in the range for Fibonacci retracement
    
    Returns:
    - df: DataFrame with added Fibonacci Retracement level columns
    """
    try:
        fib_levels = [0, 0.236, 0.382, 0.5, 0.618, 1.0]
        price_range = high - low
        
        for level in fib_levels:
            df[f'Fib_{int(level * 100)}%'] = low + level * price_range
        
        logging.info("Calculated Fibonacci Retracement levels for price range (%.2f, %.2f)", low, high)
        
        return df
    
    except Exception as e:
        logging.error("An error occurred during Fibonacci Retracement calculation: %s", e)
        raise e


def main():
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

        # Start fetching real-time data
        symbol = 'BTCUSDT'
        fetch_real_time_data(exchange, symbol)

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

if __name__ == "__main__":
    main()
