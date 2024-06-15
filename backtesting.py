import ccxt
import pandas as pd
import pandas_ta as ta
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def synchronize_time_with_exchange(exchange):
    """Synchronize local time with the exchange time."""
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
    """Fetch historical OHLCV data from the exchange."""
    try:
        time_offset = synchronize_time_with_exchange(exchange)
        params = {'recvWindow': 10000, 'timestamp': exchange.milliseconds() + time_offset}
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, params=params)
        
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        logging.info("Fetched OHLCV data for %s", symbol)
        
        return df
    except (ccxt.NetworkError, ccxt.ExchangeError, ccxt.BaseError) as error:
        logging.error("Error fetching data: %s", error)
        raise error

def calculate_indicators(df, sma_short=20, sma_long=50, rsi_period=14, macd_fast=12, macd_slow=26, macd_signal=9):
    """Calculate technical indicators and append to the DataFrame."""
    try:
        df.ta.sma(length=sma_short, append=True)
        df.ta.sma(length=sma_long, append=True)
        df.ta.rsi(length=rsi_period, append=True)
        df.ta.macd(fast=macd_fast, slow=macd_slow, signal=macd_signal, append=True)
        
        logging.info("Calculated SMA, RSI, and MACD indicators")
        return df
    except Exception as e:
        logging.error("Error during technical analysis: %s", e)
        raise e

def detect_signals(df, sma_short=20, sma_long=50, rsi_overbought=70, rsi_oversold=30):
    """Detect trading signals based on technical indicators."""
    try:
        latest = df.iloc[-1]
        previous = df.iloc[-2]

        # Simple Moving Average (SMA) Crossover
        if previous[f'SMA_{sma_short}'] < previous[f'SMA_{sma_long}'] and latest[f'SMA_{sma_short}'] > latest[f'SMA_{sma_long}']:
            logging.info("Bullish SMA crossover detected")
        elif previous[f'SMA_{sma_short}'] > previous[f'SMA_{sma_long}'] and latest[f'SMA_{sma_short}'] < latest[f'SMA_{sma_long}']:
            logging.info("Bearish SMA crossover detected")

        # Relative Strength Index (RSI) Overbought/Oversold
        if latest['RSI_14'] > rsi_overbought:
            logging.info("RSI indicates overbought conditions")
        elif latest['RSI_14'] < rsi_oversold:
            logging.info("RSI indicates oversold conditions")

        # Moving Average Convergence Divergence (MACD) Signal
        if previous['MACD_12_26_9'] < previous['MACDs_12_26_9'] and latest['MACD_12_26_9'] > latest['MACDs_12_26_9']:
            logging.info("Bullish MACD crossover detected")
        elif previous['MACD_12_26_9'] > previous['MACDs_12_26_9'] and latest['MACD_12_26_9'] < latest['MACDs_12_26_9']:
            logging.info("Bearish MACD crossover detected")
    except Exception as e:
        logging.error("Error during signal detection: %s", e)
        raise e

def backtest_strategy(df, starting_capital=10000, rsi_oversold=30, rsi_overbought=70):
    """Backtest trading strategy based on RSI and P&L calculation."""
    try:
        logging.info("Backtesting the trading strategy")

        capital = starting_capital
        position = 0
        entry_price = 0
        pnl = 0
        trades = []

        for i in range(1, len(df)):
            if df['RSI_14'][i] < rsi_oversold and position == 0:
                position = capital / df['close'][i]
                entry_price = df['close'][i]
                capital = 0
                trades.append({'type': 'buy', 'price': entry_price})
                logging.info("Buy at %s", entry_price)
            elif df['RSI_14'][i] > rsi_overbought and position > 0:
                capital = position * df['close'][i]
                pnl += (df['close'][i] - entry_price) * position
                position = 0
                trades.append({'type': 'sell', 'price': df['close'][i], 'pnl': pnl})
                logging.info("Sell at %s | P&L: %s", df['close'][i], pnl)

        logging.info("Backtesting completed")
        logging.info("Final capital: %s", capital)
        logging.info("Total P&L: %s", pnl)
        logging.info("Trades: %s", trades)
    except Exception as e:
        logging.error("Error during backtesting: %s", e)
        raise e

if __name__ == "__main__":
    try:
        api_key = os.getenv('BYBIT_API_KEY')
        api_secret = os.getenv('BYBIT_API_SECRET')

        if not api_key or not api_secret:
            raise ValueError("BYBIT_API_KEY or BYBIT_API_SECRET environment variables are not set.")

        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })

        df = fetch_data(exchange)
        df = calculate_indicators(df)
        detect_signals(df)
        backtest_strategy(df)

    except (ccxt.NetworkError, ccxt.ExchangeError, ValueError) as error:
        logging.error("Error: %s", error)
    except Exception as error:
        logging.error("Unexpected error: %s", error)
