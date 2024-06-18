from cmath import e
import ccxt
import pandas as pd
import pandas_ta as ta
import logging
import os
from APIs import create_exchange_instance, set_leverage
from fetch_data import fetch_ohlcv
from technical_indicators import calculate_indicators
from trading_strategy import detect_signals
from risk_management import calculate_stop_loss, calculate_take_profit, calculate_position_size

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

import pandas as pd

def backtest_strategy(df, strategy_func, initial_balance=1000, leverage=10, risk_percentage=1, risk_reward_ratio=2):
    """Backtest trading strategy on historical data."""
    balance = initial_balance
    trades = []
    position_size = 0
    entry_price = 0
    stop_loss = 0
    take_profit = 0

    try:
        df['signal'] = df.apply(lambda row: strategy_func(df), axis=1)
        df['position'] = 0  # 1 for long, -1 for short, 0 for no position
        df['capital'] = initial_balance
        df['balance'] = initial_balance
        current_position = 0

        for index, row in df.iterrows():
            if position_size > 0:
                # Check if stop loss or take profit is hit
                if row['low'] <= stop_loss or row['high'] >= take_profit:
                    balance += position_size * leverage * (take_profit - entry_price if row['high'] >= take_profit else stop_loss - entry_price)
                    trades.append({'entry_price': entry_price, 'exit_price': take_profit if row['high'] >= take_profit else stop_loss, 'profit': position_size * leverage * (take_profit - entry_price if row['high'] >= take_profit else stop_loss - entry_price)})
                    position_size = 0

            signal = row['signal']

            if signal == 'buy' and position_size == 0:
                entry_price = row['close']
                stop_loss = calculate_stop_loss(entry_price, risk_percentage, leverage)
                take_profit = calculate_take_profit(entry_price, risk_reward_ratio, stop_loss)
                position_size = calculate_position_size(balance, risk_percentage, stop_loss)
                balance -= position_size * leverage * entry_price

            elif signal == 'sell' and position_size == 0:
                entry_price = row['close']
                stop_loss = calculate_stop_loss(entry_price, risk_percentage, leverage)
                take_profit = calculate_take_profit(entry_price, risk_reward_ratio, stop_loss)
                position_size = -calculate_position_size(balance, risk_percentage, stop_loss)
                balance -= position_size * leverage * entry_price

            df.at[index, 'position'] = position_size
            df.at[index, 'capital'] = balance

        final_balance = df.iloc[-1]['balance']
        logging.info("Backtesting completed. Final balance: %.2f", final_balance)
        return df, final_balance, trades

    except Exception as e:
        logging.error("Error during backtesting: %s", e)
        raise e

def perform_backtesting(exchange):
    """
    Perform backtesting on BTC/USDT pair using the provided exchange.
    """
    try:
        # Fetch historical data
        df = fetch_ohlcv(exchange, 'BTC/USDT', timeframe='1h', limit=500)

        # Calculate indicators
        df = calculate_indicators(df)

        # Run backtest
        backtest_df, final_capital = backtest_strategy(exchange, df)

        # Output results
        print(backtest_df.tail())
        logging.info("Final capital after backtesting: %.2f", final_capital)

    except Exception as e:
        logging.error("Error during backtesting: %s", e)
    
def execute_trade(exchange, symbol, signal, df, balance, risk_percentage, leverage, risk_reward_ratio):
    entry_price = df.iloc[-1]['close']
    stop_loss = calculate_stop_loss(entry_price, risk_percentage, leverage)
    take_profit = calculate_take_profit(entry_price, risk_reward_ratio, stop_loss)
    position_size = calculate_position_size(balance, risk_percentage, stop_loss)

    if signal == 'buy':
        exchange.create_market_buy_order(symbol, position_size)
        logging.info(f"Buy order executed at {entry_price}, stop loss at {stop_loss}, take profit at {take_profit}")
    elif signal == 'sell':
        exchange.create_market_sell_order(symbol, position_size)
        logging.info(f"Sell order executed at {entry_price}, stop loss at {stop_loss}, take profit at {take_profit}")
    else:
        logging.info("No trade executed")

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
        
    exchange = create_exchange_instance()
    symbol = 'BTC/USDT'
    timeframe = '1h'
    leverage = 10  # Set desired leverage

    set_leverage(exchange, symbol, leverage)

    df = fetch_ohlcv(exchange, symbol, timeframe)
    df = calculate_indicators(df)

    # Backtest the strategy on historical data
    backtest_df, final_balance = backtest_strategy(df)

    # Execute the trading strategy based on the latest signal
    latest_signal = detect_signals(df)
    balance = 10  # Your total balance
    risk_percentage = 1  # Risk 1% per trade
    risk_reward_ratio = 2  # Risk-reward ratio of 1:2

    execute_trade(exchange, symbol, latest_signal, df, balance, risk_percentage, leverage, risk_reward_ratio)    
        
        # Fetch real-time balance
        
    real_time_balance = fetch_real_time_balance(exchange, currency='USDT')
        
        # Fetch historical data
    
    df = fetch_data(exchange, symbol='BTC/USDT', timeframe='1h', limit=500)
        
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
