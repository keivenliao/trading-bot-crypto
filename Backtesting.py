import ccxt
import pandas as pd
import pandas_ta as ta
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def synchronize_time_with_exchange(exchange):
    try:
        server_time = exchange.milliseconds()
        local_time = pd.Timestamp.now().timestamp() * 1000
        time_offset = server_time - local_time
        logging.info("Time synchronized with exchange. Offset: %d milliseconds", time_offset)
        return time_offset
    except ccxt.BaseError as sync_error:
        logging.error("Failed to synchronize time with exchange: %s", sync_error)
        raise sync_error

def fetch_data(exchange, symbol='BTC/USDT', timeframe='1h', limit=100):
    try:
        # Synchronize time with exchange
        time_offset = synchronize_time_with_exchange(exchange)
        
        # Fetch OHLCV data
        params = {'recvWindow': 10000, 'timestamp': exchange.milliseconds() + time_offset}
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, params=params)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        logging.info("Fetched OHLCV data for %s", symbol)
        
        return df
    except ccxt.NetworkError as net_error:
        logging.error("A network error occurred while fetching data: %s", net_error)
        raise net_error
    except ccxt.ExchangeError as exchange_error:
        logging.error("An exchange error occurred while fetching data: %s", exchange_error)
        raise exchange_error
    except ccxt.BaseError as base_error:
        logging.error("An unexpected error occurred while fetching data: %s", base_error)
        raise base_error

def perform_technical_analysis(df, sma_short=20, sma_long=50, rsi_period=14, macd_fast=12, macd_slow=26, macd_signal=9):
    try:
        # Adding technical indicators
        df.ta.sma(length=sma_short, append=True)
        df.ta.sma(length=sma_long, append=True)
        df.ta.rsi(length=rsi_period, append=True)
        df.ta.macd(fast=macd_fast, slow=macd_slow, signal=macd_signal, append=True)
        
        # Log detected patterns
        logging.info("Calculated SMA, RSI, and MACD indicators")
        
        # Detecting bullish or bearish signals
        detect_signals(df)
        
        return df
    except Exception as e:
        logging.error("An error occurred during technical analysis: %s", e)
        raise e

def detect_signals(df, sma_short=20, sma_long=50):
    try:
        # Example signal detection for educational purposes
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Simple crossover strategy
        if previous['SMA_{}'.format(sma_short)] < previous['SMA_{}'.format(sma_long)] and latest['SMA_{}'.format(sma_short)] > latest['SMA_{}'.format(sma_long)]:
            logging.info("Bullish crossover detected")
        elif previous['SMA_{}'.format(sma_short)] > previous['SMA_{}'.format(sma_long)] and latest['SMA_{}'.format(sma_short)] < latest['SMA_{}'.format(sma_long)]:
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

def backtest_strategy(df, starting_capital=10000, rsi_oversold=30, rsi_overbought=70):
    try:
        # Define backtesting logic here
        logging.info("Backtesting the trading strategy")
        
        capital = starting_capital  # Starting capital
        position = 0  # Initial position
        entry_price = 0  # Price at which position was entered
        pnl = 0  # Profit and Loss
        trades = []  # Store trade details
        
        for i in range(1, len(df)):
            if df['RSI'][i] < rsi_oversold and position == 0:  # RSI is oversold and no position
                position = capital / df['close'][i]  # Buy position
                entry_price = df['close'][i]
                capital = 0
                trades.append({'type': 'buy', 'price': entry_price})
                logging.info("Buy at %s", entry_price)
            elif df['RSI'][i] > rsi_overbought and position > 0:  # RSI is overbought and long position exists
                capital = position * df['close'][i]  # Sell position
                pnl += (df['close'][i] - entry_price) * position
                position = 0
                trades.append({'type': 'sell', 'price': df['close'][i], 'pnl': pnl})
                logging.info("Sell at %s | P&L: %s", df['close'][i], pnl)
        
        logging.info("Backtesting completed")
        logging.info("Final capital: %s", capital)
        logging.info("Total P&L: %s", pnl)
        logging.info("Trades: %s", trades)
    except Exception as e:
        logging.error("An error occurred during backtesting: %s", e)
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
        df = fetch_data(exchange)

        # Perform technical analysis
        df = perform_technical_analysis(df)

        # Backtest trading strategy
        backtest_strategy(df)
    
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
