from cmath import e
import ccxt
import logging
import pandas as pd
from datetime import date, datetime, timedelta
import os
import ntplib

from fetch_data import detect_signals

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def synchronize_system_time():
    """
    Synchronize system time with an NTP server.
    """
    try:
        response = ntplib.NTPClient().request('pool.ntp.org', timeout=10)
        current_time = datetime.fromtimestamp(response.tx_time)
        logging.info(f"System time synchronized: {current_time}")
        return current_time
    except Exception as e:
        logging.error("Time synchronization failed: %s", e)
        return datetime.now()  # Return current system time if NTP fails

def initialize_exchange(api_key, api_secret):
    """
    Initialize the exchange with the provided API key and secret.
    """
    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {'recvWindow': 10000}
        })
        logging.info("Initialized Bybit exchange")
        return exchange
    except Exception as e:
        logging.error("Failed to initialize exchange: %s", e)
        raise e

def fetch_historical_data(exchange, symbol, timeframe='1h', limit=100):
    """
    Fetch historical OHLCV data for the specified symbol and timeframe.
    """
    try:
        since = exchange.parse8601(exchange.iso8601(datetime.utcnow() - timedelta(days=limit)))
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since)
        data = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')
        logging.info(f"Fetched historical data for {symbol}")
        return data
    except Exception as e:
        logging.error("Failed to fetch historical data: %s", e)
        raise e

def calculate_technical_indicators(data, sma_periods=(50, 200), ema_periods=(12, 26), rsi_period=14):
    """
    Calculate technical indicators.
    """
    try:
        data['SMA_50'] = data['close'].rolling(window=sma_periods[0]).mean()
        data['SMA_200'] = data['close'].rolling(window=sma_periods[1]).mean()
        data['EMA_12'] = data['close'].ewm(span=ema_periods[0], adjust=False).mean()
        data['EMA_26'] = data['close'].ewm(span=ema_periods[1], adjust=False).mean()
        data['MACD'] = data['EMA_12'] - data['EMA_26']
        data['MACD_signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
        data['RSI'] = calculate_rsi(data['close'], rsi_period)
        logging.info("Calculated technical indicators")
        return data
    except Exception as e:
        logging.error("Failed to calculate technical indicators: %s", e)
        raise e

def calculate_rsi(series, period):
    """
    Calculate Relative Strength Index (RSI).
    """
    try:
        delta = series.diff(1)
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    except Exception as e:
        logging.error("Failed to calculate RSI: %s", e)
        raise e

def detect_patterns(data):
    """
    Detect patterns in the data.
    """
    try:
        data['HeadAndShoulders'] = detect_head_and_shoulders(data)
        data['DoubleTop'] = detect_double_top(data)
        logging.info("Detected patterns")
        return data
    except Exception as e:
        logging.error("Failed to detect patterns: %s", e)
        raise e

def detect_head_and_shoulders(data):
    """
    Detect the Head and Shoulders pattern in the data.
    """
    try:
        pattern = [0] * len(data)
        for i in range(2, len(data) - 1):
            if (data['high'].iloc[i - 2] < data['high'].iloc[i - 1] > data['high'].iloc[i] and
                data['high'].iloc[i - 1] > data['high'].iloc[i + 1] and
                data['low'].iloc[i - 2] > data['low'].iloc[i - 1] < data['low'].iloc[i] and
                data['low'].iloc[i - 1] < data['low'].iloc[i + 1]):
                pattern[i] = 1
        return pattern
    except Exception as e:
        logging.error("Failed to detect Head and Shoulders pattern: %s", e)
        raise e

def detect_double_top(data):
    """
    Detect the Double Top pattern in the data.
    """
    try:
        pattern = [0] * len(data)
        for i in range(1, len(data) - 1):
            if (data['high'].iloc[i - 1] < data['high'].iloc[i] > data['high'].iloc[i + 1] and
                data['high'].iloc[i] == data['high'].iloc[i + 1]):
                pattern[i] = 1
        return pattern
    except Exception as e:
        logging.error("Failed to detect Double Top pattern: %s", e)
        raise e

def calculate_position_size(balance, risk_percentage, entry_price, stop_loss):
    risk_amount = balance * (risk_percentage / 100)
    position_size = risk_amount / abs(entry_price - stop_loss)
    return min(position_size, balance / entry_price)  # Ensure position size does not exceed available balance

def calculate_atr(data, period=14):
    high_low_range = data['high'] - data['low']
    high_close_range = abs(data['high'] - data['close'].shift())
    low_close_range = abs(data['low'] - data['close'].shift())
    ranges = pd.concat([high_low_range, high_close_range, low_close_range], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(window=period).mean()
    return atr

def calculate_stop_loss(entry_price, atr_multiplier, data):
    atr = calculate_atr(data)  # Implement calculate_atr function
    stop_loss = entry_price - atr_multiplier * atr
    return stop_loss

def calculate_take_profit(entry_price, risk_reward_ratio, stop_loss):
    take_profit_distance = abs(entry_price - stop_loss) * risk_reward_ratio
    take_profit = entry_price + take_profit_distance if entry_price > stop_loss else entry_price - take_profit_distance
    return take_profit

def apply_trailing_stop_loss(entry_price, current_price, trailing_percent):
    trailing_stop = entry_price * (1 - trailing_percent)
    if current_price > trailing_stop:
        trailing_stop = current_price * (1 - trailing_percent)
    return trailing_stop

def calculate_risk_reward(entry_price, stop_loss_price, take_profit_price):
    risk = abs(entry_price - stop_loss_price)
    reward = abs(take_profit_price - entry_price)
    risk_reward_ratio = reward / risk
    return risk_reward_ratio

def adjust_stop_loss_take_profit(data, entry_price):
    # Example: Adjust based on SMA and RSI
    if data['SMA_50'].iloc[-1] > data['SMA_200'].iloc[-1]:
        stop_loss = calculate_stop_loss(entry_price, 1.5, data)
        take_profit = calculate_take_profit(entry_price, 2.0, stop_loss)
    elif data['SMA_50'].iloc[-1] < data['SMA_200'].iloc[-1]:
        stop_loss = calculate_stop_loss(entry_price, 2.0, data)
        take_profit = calculate_take_profit(entry_price, 1.5, stop_loss)
    else:
        stop_loss = calculate_stop_loss(entry_price, 1.0, data)
        take_profit = calculate_take_profit(entry_price, 1.0, stop_loss)  
    return stop_loss, take_profit

def place_order_with_risk_management(exchange, symbol, side, amount, stop_loss=None, take_profit=None):
    try:
        order = exchange.create_order(symbol, 'market', side, amount)
        logging.info(f"Market order placed: {order}")
        
        order_price = order.get('price')
        if order_price:
            if not stop_loss:
                stop_loss = calculate_stop_loss(order_price, 1.5, date)  # Ensure data is passed
            if not take_profit:
                take_profit = calculate_take_profit(order_price, 2.0, stop_loss)  # Ensure data is passed
            
            logging.info(f"Stop Loss: {stop_loss}, Take Profit: {take_profit}")
            
            if side == 'buy':
                exchange.create_order(symbol, 'stop', 'sell', amount, stop_loss)
                exchange.create_order(symbol, 'limit', 'sell', amount, take_profit)
            else:
                exchange.create_order(symbol, 'stop', 'buy', amount, stop_loss)
                exchange.create_order(symbol, 'limit', 'buy', amount, take_profit)
            
        else:
            logging.warning("Order price not available, cannot calculate stop-loss and take-profit.")
    except ccxt.BaseError as e:
        logging.error(f"An error occurred: {e}")

def apply_position_sizing(df, risk_percentage):
    """
    Apply position sizing logic based on risk percentage of capital.
    
    Parameters:
    - df: DataFrame containing trading signals and indicators.
    - risk_percentage: Maximum percentage of capital to risk per trade (e.g., 1.5 for 1.5%).
    
    Returns:
    - df: DataFrame with 'position_size' column added.
    """
    # Assuming capital is available in a global variable or passed through another mechanism
    capital = 10  # Example: Starting capital of $10,000
    
    # Calculate position size based on risk percentage
    df['position_size'] = (capital * risk_percentage / 100) / df['close']
    
    return df

def apply_stop_loss(df, stop_loss_percentage):
    """
    Apply stop loss logic based on stop loss percentage from entry price.
    
    Parameters:
    - df: DataFrame containing trading signals and indicators.
    - stop_loss_percentage: Maximum percentage loss to tolerate (e.g., 3 for 3%).
    
    Returns:
    - df: DataFrame with 'stop_loss' column added.
    """
    # Calculate stop loss price based on entry price
    df['stop_loss'] = df['entry_price'] * (1 - stop_loss_percentage / 100)
    
    return df

def risk_management(balance, entry_price, stop_loss, take_profit):
    risk_amount = balance * 0.02  # Risk 2% of the balance
    position_size = risk_amount / abs(entry_price - stop_loss)
    adjusted_position_size = min(position_size, balance / entry_price)
    risk_reward_ratio = calculate_risk_reward(entry_price, stop_loss, take_profit)
    if risk_reward_ratio < 1.0:
        adjusted_position_size = 0  # Do not take the trade if the risk-reward ratio is less than 1.0
    return adjusted_position_size, stop_loss, take_profit

def place_order(exchange, symbol, side, quantity, price, stop_loss, take_profit):
    try:
        order = exchange.create_order(symbol, 'limit', side, quantity, price)
        logging.info(f"Placed {side} order for {symbol}: {order}")
        # Additional logic for stop loss and take profit can be added here
    except Exception as e:
        logging.error(f"Failed to place {side} order for {symbol}: %s", e)
        raise e

def backtest_strategy(df, initial_capital=1000, position_size=1, transaction_cost=0.001, stop_loss_pct=0.02, take_profit_pct=0.05):
    try:
        sma_lengths = (50, 200)  # Define sma_lengths or get this from configuration
        df['signal'] = df.apply(lambda row: detect_signals(df, sma_lengths), axis=1)
        df['position'] = 0  # 1 for long, -1 for short, 0 for no position
        df['capital'] = initial_capital
        df['balance'] = initial_capital
        current_position = 0
        entry_price = 0

        for i in range(1, len(df)):
            if df.at[i, 'signal'] == 'buy' and current_position == 0:
                current_position = position_size
                entry_price = df.at[i, 'close']
                df.at[i, 'position'] = current_position
                df.at[i, 'capital'] -= df.at[i, 'close'] * position_size * (1 + transaction_cost)
                df.at[i, 'balance'] -= df.at[i, 'close'] * position_size * (1 + transaction_cost)

            elif df.at[i, 'signal'] == 'sell' and current_position == position_size:
                current_position = 0
                df.at[i, 'position'] = current_position
                df.at[i, 'capital'] += df.at[i, 'close'] * position_size * (1 - transaction_cost)
                df.at[i, 'balance'] += df.at[i, 'close'] * position_size * (1 - transaction_cost)

            if current_position == position_size:
                if df.at[i, 'close'] <= entry_price * (1 - stop_loss_pct):
                    current_position = 0
                    df.at[i, 'position'] = current_position
                    df.at[i, 'capital'] += df.at[i, 'close'] * position_size * (1 - transaction_cost)
                    df.at[i, 'balance'] += df.at[i, 'close'] * position_size * (1 - transaction_cost)
                    logging.info("Stop-loss triggered")

                if df.at[i, 'close'] >= entry_price * (1 + take_profit_pct):
                    current_position = 0
                    df.at[i, 'position'] = current_position
                    df.at[i, 'capital'] += df.at[i, 'close'] * position_size * (1 - transaction_cost)
                    df.at[i, 'balance'] += df.at[i, 'close'] * position_size * (1 - transaction_cost)
                    logging.info("Take-profit triggered")

        final_balance = df['balance'].iloc[-1]  # Ensure to use the last balance value
        logging.info("Backtesting completed. Final balance: %.2f", final_balance)
        return df, final_balance
    except Exception as e:
        logging.error("Error during backtesting: %s", e)
        raise e



def main():
    try:
        # Retrieve API keys and secrets from environment variables
        api_key = os.getenv('BYBIT_API_KEY')
        api_secret = os.getenv('BYBIT_API_SECRET')

        if not api_key or not api_secret:
            logging.error("API key and secret must be set as environment variables")
            return

        synchronize_system_time()
        exchange = initialize_exchange(api_key, api_secret)
        
        symbol = 'BTCUSDT'
        
        data = fetch_historical_data(exchange, symbol)
        data = calculate_technical_indicators(data)
        data = detect_patterns(data)
        
        # Perform backtesting
        data, final_balance = backtest_strategy(data)
        
        # Trading logic
        balance = 10000  # Example balance
        entry_price = data['close'].iloc[-1]
        stop_loss, take_profit = adjust_stop_loss_take_profit(data, entry_price)
        position_size, stop_loss, take_profit = risk_management(balance, entry_price, stop_loss, take_profit)
    
        if position_size > 0:
            place_order(exchange, symbol, 'buy', position_size, entry_price, stop_loss, take_profit)
        
        # Add the print statements and fillna method here
        print(data['SMA_50'])
        print(data['SMA_200'])
        print(data['SMA_50'].iloc[-1])
        print(data['SMA_200'].iloc[-1])
        
        data['SMA_50'].fillna(method='ffill', inplace=True)
        data['SMA_200'].fillna(method='ffill', inplace=True)
        
        data = detect_patterns(data)
        
        # Example of market analysis (hypothetical)
        if data['SMA_50'].iloc[-1] > data['SMA_200'].iloc[-1]:
            trend = 'bullish'
        elif data['SMA_50'].iloc[-1] < data['SMA_200'].iloc[-1]:
            trend = 'bearish'
        else:
            trend = 'neutral'
            
        # Example of determining trend based on SMA indicators
        if data['SMA_50'].iloc[-1] > data['SMA_200'].iloc[-1]:
            trend = 'bullish'
        elif data['SMA_50'].iloc[-1] < data['SMA_200'].iloc[-1]:
            trend = 'bearish'
        else:
            trend = 'neutral'

        logging.info(f"Determined trend: {trend}")

        # Example of applying condition explicitly
        if data['SMA_50'].iloc[-1] > data['SMA_200'].iloc[-1]:
            logging.info("SMA_50 is greater than SMA_200 for the last row")
        else:
            logging.info("SMA_50 is NOT greater than SMA_200 for the last row")


        # Continue with other trading logic based on the determined trend

        # Example of risk management parameters based on trend analysis
        if trend == 'bullish':
            stop_loss, take_profit = adjust_stop_loss_take_profit(data, data.iloc[-1]['close'])
            side = 'buy'
            amount = 0.003  # Example: Adjust based on your strategy
        elif trend == 'bearish':
            stop_loss, take_profit = adjust_stop_loss_take_profit(data, data.iloc[-1]['close'])
            side = 'sell'
            amount = 0.003  # Example: Adjust based on your strategy
        else:
            logging.info("No clear trend identified, skipping order placement")
            return

        # Example of determining trend based on SMA indicators
        if not data['SMA_50'].empty and not data['SMA_200'].empty:
            sma_50_last = data['SMA_50'].iloc[-1]
            sma_200_last = data['SMA_200'].iloc[-1]

            if sma_50_last > sma_200_last:
                trend = 'bullish'
            elif sma_50_last < sma_200_last:
                trend = 'bearish'
            else:
                trend = 'neutral'

            logging.info(f"Determined trend: {trend}")

            # Example of checking condition for the last row explicitly
            if sma_50_last > sma_200_last:
                logging.info("SMA_50 is greater than SMA_200 for the last row")
            else:
                logging.info("SMA_50 is NOT greater than SMA_200 for the last row")
        else:
            logging.warning("SMA_50 or SMA_200 data is empty, cannot determine trend.")

        # Add your logic here based on the condition

        # Do something when SMA_50 is greater than SMA_200 for any row

        # Uncomment the line below to place a real order
        place_order_with_risk_management(exchange, symbol, side, amount, stop_loss, take_profit)

    except ccxt.NetworkError as e:
        logging.error("A network error occurred: %s", e)
    except ccxt.BaseError as e:
        logging.error("An error occurred: %s", e)
    except ValueError as e:
        logging.error("Value error occurred: %s", e)

if __name__ == "__main__":
    main()
