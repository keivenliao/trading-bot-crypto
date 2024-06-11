import ccxt
import pandas as pd
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def initialize_exchange(api_key, api_secret):
    """
    Initialize the exchange with API key and secret.
    """
    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })
        logging.info("Initialized Bybit exchange")
        return exchange
    except Exception as e:
        logging.error("Failed to initialize exchange: %s", e)
        raise e

def fetch_ohlcv(exchange, symbol, timeframe='1h', limit=100):
    """
    Fetch OHLCV data.
    """
    try:
        params = {'recvWindow': 10000}
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, params=params)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        logging.info("Fetched OHLCV data")
        return df
    except ccxt.BaseError as e:
        logging.error("Failed to fetch OHLCV data: %s", e)
        raise e

def trading_strategy(df):
    """
    Define the trading strategy.
    """
    signals = ['hold']
    for i in range(1, len(df)):
        if df['SMA_50'][i] > df['SMA_200'][i] and df['SMA_50'][i-1] <= df['SMA_200'][i-1]:
            signals.append('buy')
        elif df['SMA_50'][i] < df['SMA_200'][i] and df['SMA_50'][i-1] >= df['SMA_200'][i-1]:
            signals.append('sell')
        else:
            signals.append('hold')
    df['signal'] = signals
    logging.info("Applied trading strategy")
    return df

def place_order(exchange, symbol, order_type, side, amount, price=None):
    """
    Place an order on the exchange.
    """
    try:
        if order_type == 'market':
            order_params = {'type': order_type}
        else:
            order_params = {'type': order_type, 'price': price}
        
        order = exchange.create_order(symbol, side, amount, **order_params)
        logging.info("Placed order: %s", order)
        return order
    except ccxt.InsufficientFunds as insf:
        logging.error("Insufficient funds: %s", insf)
    except ccxt.InvalidOrder as invord:
        logging.error("Invalid order: %s", invord)
    except ccxt.NetworkError as neterr:
        logging.error("Network error: %s", neterr)
    except ccxt.BaseError as e:
        logging.error("An error occurred: %s", e)

def execute_trading_strategy(exchange, df, symbol):
    """
    Execute the trading strategy based on signals.
    """
    for i in range(len(df)):
        if df['signal'][i] == 'buy':
            logging.info("Buy Signal - Placing Buy Order")
            # Uncomment the following line to actually place the order
            # place_order(exchange, symbol, 'market', 'buy', 0.001)
        elif df['signal'][i] == 'sell':
            logging.info("Sell Signal - Placing Sell Order")
            # Uncomment the following line to actually place the order
            # place_order(exchange, symbol, 'market', 'sell', 0.001)

def main():
    """
    Main function to execute the trading strategy.
    """
    api_key = 'YOUR_API_KEY'
    api_secret = 'YOUR_API_SECRET'
    symbol = 'BTC/USDT'
    
    try:
        # Initialize exchange
        exchange = initialize_exchange(api_key, api_secret)
        
        # Fetch historical data
        df = fetch_ohlcv(exchange, symbol)
        
        # Calculate technical indicators
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        df['SMA_200'] = df['close'].rolling(window=200).mean()
        
        # Apply trading strategy
        df = trading_strategy(df)
        
        # Execute trading strategy
        execute_trading_strategy(exchange, df, symbol)
                
    except ccxt.NetworkError as e:
        logging.error("A network error occurred: %s", e)
    except ccxt.BaseError as e:
        logging.error("An error occurred: %s", e)

if __name__ == "__main__":
    main()
