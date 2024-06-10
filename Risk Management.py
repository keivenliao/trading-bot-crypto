import ccxt
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import ntplib
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def synchronize_system_time():
    """
    Synchronize system time with an NTP server.
    """
    try:
        client = ntplib.NTPClient()
        response = client.request('pool.ntp.org')
        current_time = datetime.fromtimestamp(response.tx_time)
        logging.info(f"System time synchronized: {current_time}")
        return current_time
    except Exception as e:
        logging.error("Time synchronization failed: %s", e)
        raise e

def initialize_exchange(api_key, api_secret):
    """
    Initialize the exchange with the provided API key and secret.
    """
    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'options': {
                'recvWindow': 10000,
            }
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

def calculate_indicators(data):
    """
    Calculate technical indicators.
    """
    data['SMA_50'] = data['close'].rolling(window=50).mean()
    data['SMA_200'] = data['close'].rolling(window=200).mean()
    data['EMA_12'] = data['close'].ewm(span=12, adjust=False).mean()
    data['EMA_26'] = data['close'].ewm(span=26, adjust=False).mean()
    data['MACD'] = data['EMA_12'] - data['EMA_26']
    data['MACD_signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['RSI'] = calculate_rsi(data['close'], 14)
    logging.info("Calculated technical indicators")
    return data

def calculate_rsi(series, period):
    """
    Calculate Relative Strength Index (RSI).
    """
    delta = series.diff(1)
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def detect_patterns(data):
    """
    Detect patterns in the data.
    """
    data['HeadAndShoulders'] = detect_head_and_shoulders(data)
    data['DoubleTop'] = detect_double_top(data)
    logging.info("Detected patterns")
    return data

def detect_head_and_shoulders(data):
    """
    Detect the Head and Shoulders pattern in the data.
    """
    pattern = [0] * len(data)
    for i in range(2, len(data) - 1):
        if data['high'][i - 2] < data['high'][i - 1] > data['high'][i] and \
           data['high'][i - 1] > data['high'][i + 1] and \
           data['low'][i - 2] > data['low'][i - 1] < data['low'][i] and \
           data['low'][i - 1] < data['low'][i + 1]:
            pattern[i] = 1
    return pattern

def detect_double_top(data):
    """
    Detect the Double Top pattern in the data.
    """
    pattern = [0] * len(data)
    for i in range(1, len(data) - 1):
        if data['high'][i - 1] < data['high'][i] > data['high'][i + 1] and \
           data['high'][i] == data['high'][i + 1]:
            pattern[i] = 1
    return pattern

def place_order_with_risk_management(exchange, symbol, side, amount, stop_loss, take_profit):
    """
    Place an order with stop-loss and take-profit.
    """
    try:
        order = exchange.create_order(symbol, 'market', side, amount)
        logging.info(f"Market order placed: {order}")
        
        order_price = order['price'] if 'price' in order else None
        
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

def main():
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    
    if not api_key or not api_secret:
        logging.error("API key and secret must be set as environment variables")
        return
    
    synchronize_system_time()
    exchange = initialize_exchange(api_key, api_secret)
    
    symbol = 'BTC/USDT'
    data = fetch_historical_data(exchange, symbol)
    data = calculate_indicators(data)
    data = detect_patterns(data)

    # Example of placing an order with stop-loss and take-profit
    # Uncomment the line below to place a real order
    # place_order_with_risk_management(exchange, symbol, 'buy', 0.001, 0.01, 0.02)

if __name__ == "__main__":
    main()
