import time
import ccxt
import pandas as pd
import pandas_ta as ta
import logging
import pandas_ta as ta
from synchronize_exchange_time import synchronize_system_time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradingBot:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange = None

    def initialize_exchange(self):
        try:
            self.exchange = ccxt.bybit({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
            })
            logging.info("Initialized Bybit exchange")
        except Exception as e:
            logging.error("Failed to initialize exchange: %s", e)
            raise e

    def fetch_ohlcv(self, symbol, timeframe='1h', limit=100, time_offset=0):
        params = {
            'recvWindow': 10000,
            'timestamp': int(time.time() * 1000 + time_offset)
        }
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, params=params)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            logging.info(f"Fetched OHLCV data for {symbol}")
            return df
        except ccxt.BaseError as e:
            logging.error("Error fetching OHLCV data: %s", e)
            raise e

    def calculate_indicators(self, df):
        try:
            df['SMA_50'] = ta.sma(df['close'], length=50)
            df['SMA_200'] = ta.sma(df['close'], length=200)
            df['EMA_12'] = ta.ema(df['close'], length=12)
            df['EMA_26'] = ta.ema(df['close'], length=26)
            macd_data = ta.macd(df['close'], fast=12, slow=26, signal=9)
            df['MACD'], df['MACD_signal'], _ = macd_data
            df['RSI'] = ta.rsi(df['close'], length=14)
            logging.info("Calculated technical indicators")
            return df
        except Exception as e:
            logging.error("An error occurred during indicator calculation: %s", e)
            raise e

    def trading_strategy(self, df):
        try:
            signals = ['hold']
            for i in range(1, len(df)):
                if pd.notna(df['SMA_50'][i]) and pd.notna(df['SMA_200'][i]) and pd.notna(df['SMA_50'][i-1]) and pd.notna(df['SMA_200'][i-1]):
                    if df['SMA_50'][i] > df['SMA_200'][i] and df['SMA_50'][i-1] <= df['SMA_200'][i-1]:
                        signals.append('buy')
                    elif df['SMA_50'][i] < df['SMA_200'][i] and df['SMA_50'][i-1] >= df['SMA_200'][i-1]:
                        signals.append('sell')
                    else:
                        signals.append('hold')
                else:
                    signals.append('hold')  # Handle cases where SMA values are None

            df['signal'] = signals
            logging.info("Generated trading signals")
            return df
        except Exception as e:
            logging.error("An error occurred during trading strategy execution: %s", e)
            raise e

    def execute_trade(self, symbol, signal, amount=0.001):
        try:
            if signal == 'buy':
                logging.info("Executing Buy Order")
                order = self.exchange.create_market_buy_order(symbol, amount)
            elif signal == 'sell':
                logging.info("Executing Sell Order")
                order = self.exchange.create_market_sell_order(symbol, amount)
            else:
                logging.info("No trade action needed (hold signal)")
                return
            
            if 'error' in order:
                logging.error("Failed to execute order: %s", order['error'])
            else:
                logging.info("Order executed successfully: %s", order)
                
        except ccxt.BaseError as e:
            logging.error("An error occurred during trade execution: %s", e)
            raise e

def calculate_technical_indicators(df):
    df['SMA_50'] = ta.sma(df['close'], length=50)
    df['SMA_200'] = ta.sma(df['close'], length=200)
    df['EMA_12'] = ta.ema(df['close'], length=12)
    df['EMA_26'] = ta.ema(df['close'], length=26)
    macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
    
    # Ensure the MACD calculation is not None
    if macd is not None:
        df['MACD'] = macd['MACD_12_26_9']
        df['MACD_signal'] = macd['MACDs_12_26_9']
    else:
        df['MACD'] = df['MACD_signal'] = pd.Series([None] * len(df))
    
    df['RSI'] = ta.rsi(df['close'], length=14)
    logging.info("Calculated technical indicators")
    return df

def main():
    try:
        # Replace with your actual API key and secret
        API_KEY = 'LzvSGu2mYFi2L6VtBL'
        API_SECRET = 'KA3wvyIvMCJjGZEB0KVjH9WJSi30iwc9pIiG'

        time_offset = synchronize_system_time()
        logging.info("System time synchronized with offset: %d ms", time_offset)
        
        bot = TradingBot(API_KEY, API_SECRET)
        bot.initialize_exchange()
        
        df = bot.fetch_ohlcv('BTC/USDT', time_offset=time_offset)
        df = bot.calculate_indicators(df)
        df = bot.trading_strategy(df)
        
        df.apply(lambda row: bot.execute_trade('BTC/USDT', row['signal']), axis=1)
        
        print(df.tail())
        
    except ccxt.AuthenticationError as e:
        logging.error("Authentication error: %s. Please check your API key and secret.", e)
    except ccxt.NetworkError as e:
        logging.error("Network error: %s. Please check your internet connection.", e)
    except ccxt.ExchangeError as e:
        logging.error("Exchange error: %s. Please check the exchange status or API documentation.", e)
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)

if __name__ == "__main__":
    main()
