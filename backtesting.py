import ccxt
import pandas as pd
import pandas_ta as ta
import logging
import os

from fetch_data import fetch_ohlcv

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

def fetch_data(exchange, symbol='BTCUSDT', timeframe='1h', limit=100):
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
    try:
        df.ta.sma(length=sma_short, append=True)
        df.ta.sma(length=sma_long, append=True)
        df.ta.rsi(length=rsi_period, append=True)
        df.ta.macd(fast=macd_fast, slow=macd_slow, signal=macd_signal, append=True)
        df.ta.bbands(length=20, std=2, append=True)  # Bollinger Bands
        df.ta.atr(length=14, append=True)  # Average True Range
        logging.info("Calculated SMA, RSI, MACD, Bollinger Bands, and ATR indicators")
        return df
    except Exception as e:
        logging.error("Error during technical analysis: %s", e)
        raise e


def detect_signals(df, sma_short=20, sma_long=50, rsi_overbought=70, rsi_oversold=30):
    """Detect trading signals based on technical indicators."""
    try:
        latest = df.iloc[-1]
        previous = df.iloc[-2]

        # Check if required columns are available
        if f'SMA_{sma_short}' not in df.columns or f'SMA_{sma_long}' not in df.columns:
            raise ValueError("Required SMA columns are not present in the DataFrame")
        if 'RSI_14' not in df.columns:
            raise ValueError("RSI column is not present in the DataFrame")

        # Fill NaN values with previous values
        df.fillna(method='ffill', inplace=True)

        # Simple Moving Average (SMA) Crossover
        if previous[f'SMA_{sma_short}'] < previous[f'SMA_{sma_long}'] and latest[f'SMA_{sma_short}'] > latest[f'SMA_{sma_long}']:
            return 'buy'
        elif previous[f'SMA_{sma_short}'] > previous[f'SMA_{sma_long}'] and latest[f'SMA_{sma_short}'] < latest[f'SMA_{sma_long}']:
            return 'sell'
        
        # Relative Strength Index (RSI)
        if latest['RSI_14'] > rsi_overbought:
            return 'sell'
        elif latest['RSI_14'] < rsi_oversold:
            return 'buy'

        return 'hold'
    except Exception as e:
        logging.error("Error detecting signals: %s", e)
        raise e

def fetch_real_time_balance(exchange, currency='USDT'):
    """Fetch real-time balance from the exchange."""
    try:
        balance = exchange.fetch_balance()
        real_time_balance = balance['total'][currency]
        logging.info("Fetched real-time balance: %.2f %s", real_time_balance, currency)
        return real_time_balance
    except (ccxt.NetworkError, ccxt.ExchangeError, ccxt.BaseError) as error:
        logging.error("Error fetching real-time balance: %s", error)
        raise error

def backtest_strategy(df, initial_capital=1000, position_size=1, transaction_cost=0.001):
    try:
        df['signal'] = df.apply(lambda row: detect_signals(df), axis=1)
        df['position'] = 0  # 1 for long, -1 for short, 0 for no position
        df['capital'] = initial_capital
        df['balance'] = initial_capital
        current_position = 0

        for i in range(1, len(df)):
            if df.at[i, 'signal'] == 'buy' and current_position == 0:
                current_position = position_size
                df.at[i, 'position'] = current_position
                df.at[i, 'capital'] -= df.at[i, 'close'] * position_size * (1 + transaction_cost)  # Deduct cost of buying including transaction cost

                df.at[i, 'balance'] = df.at[i - 1, 'balance'] - df.at[i, 'close'] * position_size * (1 + transaction_cost)

            elif df.at[i, 'signal'] == 'sell' and current_position == position_size:
                current_position = 0
                df.at[i, 'position'] = current_position
                df.at[i, 'capital'] += df.at[i, 'close'] * position_size * (1 - transaction_cost)  # Add profit from selling minus transaction cost

                df.at[i, 'balance'] = df.at[i - 1, 'balance'] + df.at[i, 'close'] * position_size * (1 - transaction_cost)

        final_balance = df.iloc[-1]['balance']
        logging.info("Backtesting completed. Final balance: %.2f", final_balance)
        return df, final_balance
    except Exception as e:
        logging.error("Error during backtesting: %s", e)
        raise e

def calculate_position_size(capital, risk_per_trade, entry_price, stop_loss_price):
    risk_amount = capital * (risk_per_trade / 100)
    position_size = risk_amount / abs(entry_price - stop_loss_price)
    return position_size


def perform_backtesting(exchange):
    """
    Perform backtesting on BTCUSDT pair using the provided exchange.
    """
    try:
        # Fetch historical data
        df = fetch_ohlcv(exchange, 'BTCUSDT', timeframe='1h', limit=500)

        # Calculate indicators
        df = calculate_indicators(df)

        # Run backtest
        backtest_df, final_capital = backtest_strategy(exchange, df)

        # Output results
        print(backtest_df.tail())
        logging.info("Final capital after backtesting: %.2f", final_capital)

    except Exception as e:
        logging.error("Error during backtesting: %s", e)
    


def main():
    """Main function to run backtesting."""
    try:
        # Initialize the exchange
        api_key = os.getenv('BYBIT_API_KEY')
        api_secret = os.getenv('BYBIT_API_SECRET')
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True
        })
        
        # Fetch real-time balance
        real_time_balance = fetch_real_time_balance(exchange, currency='USDT')
        
        # Fetch historical data
        df = fetch_data(exchange, symbol='BTCUSDT', timeframe='1h', limit=500)
        
        # Calculate indicators
        df = calculate_indicators(df)
        
        # Run backtest
        backtest_df, final_capital = backtest_strategy(df, initial_capital=real_time_balance)
        
        # Output results
        print(backtest_df.tail())
        logging.info("Final capital after backtesting: %.2f", final_capital)
    except Exception as e:
        logging.error("An error occurred in the main function: %s", e)

if __name__ == "__main__":
    main()
