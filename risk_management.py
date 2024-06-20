import ccxt
import logging
import pandas as pd
from datetime import datetime, timedelta
import os
import ntplib

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
            if (data['high'][i - 2] < data['high'][i - 1] > data['high'][i] and
                data['high'][i - 1] > data['high'][i + 1] and
                data['low'][i - 2] > data['low'][i - 1] < data['low'][i] and
                data['low'][i - 1] < data['low'][i + 1]):
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
            if (data['high'][i - 1] < data['high'][i] > data['high'][i + 1] and
                data['high'][i] == data['high'][i + 1]):
                pattern[i] = 1
        return pattern
    except Exception as e:
        logging.error("Failed to detect Double Top pattern: %s", e)
        raise e
    
    
def calculate_position_size(capital, risk_per_trade, entry_price, stop_loss_price):
    risk_amount = capital * (risk_per_trade / 100)
    position_size = risk_amount / abs(entry_price - stop_loss_price)
    return position_size

def calculate_stop_loss(entry_price, risk_percentage, leverage):
    stop_loss_distance = entry_price * (risk_percentage / 100) / leverage
    stop_loss = entry_price - stop_loss_distance if entry_price > 0 else entry_price + stop_loss_distance
    return stop_loss

def calculate_take_profit(entry_price, risk_reward_ratio, stop_loss):
    take_profit_distance = abs(entry_price - stop_loss) * risk_reward_ratio
    take_profit = entry_price + take_profit_distance if entry_price > stop_loss else entry_price - take_profit_distance
    return take_profit




def place_order_with_risk_management(exchange, symbol, side, amount, stop_loss, take_profit):
    """
    Place an order with stop-loss and take-profit.
    """
    try:
        order = exchange.create_order(symbol, 'market', side, amount)
        logging.info(f"Market order placed: {order}")
        
        order_price = order.get('price')
        if order_price:
            stop_loss_price = order_price * (1 - stop_loss) if side == 'buy' else order_price * (1 + stop_loss)
            take_profit_price = order_price * (1 + take_profit) if side == 'buy' else order_price * (1 - take_profit)
            
            logging.info(f"Stop Loss: {stop_loss_price}, Take Profit: {take_profit_price}")
            
            if side == 'buy':
                exchange.create_order(symbol, 'stop', 'sell', amount, stop_loss_price)
                exchange.create_order(symbol, 'limit', 'sell', amount, take_profit_price)
            else:
                exchange.create_order(symbol, 'stop', 'buy', amount, stop_loss_price)
                exchange.create_order(symbol, 'limit', 'buy', amount, take_profit_price)
            
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
    capital = 10000  # Example: Starting capital of $10,000
    
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
        
        symbol = 'BTC/USDT'
        data = fetch_historical_data(exchange, symbol)
        data = calculate_technical_indicators(data)
        data = detect_patterns(data)

        # Example of placing an order with stop-loss and take-profit
        # Configure risk management parameters here
        side = 'buy'
        amount = 0.001
        stop_loss = 0.01  # 1%
        take_profit = 0.02  # 2%
        
        # Uncomment the line below to place a real order
        # place_order_with_risk_management(exchange, symbol, side, amount, stop_loss, take_profit)

    except ccxt.NetworkError as e:
        logging.error("A network error occurred: %s", e)
    except ccxt.BaseError as e:
        logging.error("An error occurred: %s", e)
    except ValueError as e:
        logging.error("Value error occurred: %s", e)

if __name__ == "__main__":
    main()
