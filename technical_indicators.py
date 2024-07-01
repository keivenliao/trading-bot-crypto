import time
import logging
import ccxt
import pandas as pd
import numpy as np
from sympy import series
import ta
import os
from dotenv import load_dotenv
from synchronize_exchange_time import synchronize_system_time
from tradingbot import TradingBot
from utils import calculate_sma

# Load environment variables from .env file
load_dotenv(dotenv_path=r'C:\Users\amrita\Desktop\improvised-code-of-the-pdf-GPT-main\API.env')

# Retrieve API credentials from environment variables
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TechnicalIndicators:
    def __init__(self, api_key, api_secret, data=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange = None
        self.data = data

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

    def calculate_sma(self, window):
        return self.data['close'].rolling(window=window).mean()

    def calculate_rsi(self, window=14):
        delta = self.data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_macd(self, fast=12, slow=26, signal=9):
        exp1 = self.data['close'].ewm(span=fast, adjust=False).mean()
        exp2 = self.data['close'].ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        macd_histogram = macd - macd_signal
        macd_df = pd.DataFrame({
            'MACD_12_26_9': macd,
            'MACDs_12_26_9': macd_signal,
            'MACDh_12_26_9': macd_histogram
        })
        return macd_df['MACD_12_26_9'], macd_df['MACDs_12_26_9']

    def calculate_bollinger_bands(self, window=20):
        sma = calculate_sma(self.data['close'], window)
        std_dev = self.data['close'].rolling(window=window, min_periods=1).std()
        upper_band = sma + 2 * std_dev
        lower_band = sma - 2 * std_dev
        return upper_band, lower_band

    def calculate_atr(self, high_prices, low_prices, close_prices, window=14):
        tr1 = high_prices - low_prices
        tr2 = abs(high_prices - close_prices.shift())
        tr3 = abs(low_prices - close_prices.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=window, min_periods=1).mean()
        return atr

    def calculate_indicators(self):
        try:
            # Calculate SMAs
            self.data['SMA_20'] = self.calculate_sma(window=20)
            self.data['SMA_50'] = self.calculate_sma(window=50)
            self.data['SMA_200'] = self.calculate_sma(window=200)

            # Calculate RSI
            self.data['RSI'] = self.calculate_rsi(window=14)

            # Calculate MACD
            macd_line, signal_line = self.calculate_macd()
            self.data['MACD'] = macd_line
            self.data['MACD_signal'] = signal_line

            # Calculate Bollinger Bands
            upper_band, lower_band = self.calculate_bollinger_bands()
            self.data['BB_upper'] = upper_band
            self.data['BB_lower'] = lower_band

            # Calculate ATR
            self.data['ATR'] = self.calculate_atr(self.data['high'], self.data['low'], self.data['close'], window=14)

            logging.info("Calculated SMA, RSI, MACD, Bollinger Bands, and ATR indicators")
        except Exception as e:
            logging.error("Error during technical analysis: %s", e)
            raise e

    def trading_strategy(self):
        try:
            signals = ['hold']
            for i in range(1, len(self.data)):
                if pd.notna(self.data['SMA_50'][i]) and pd.notna(self.data['SMA_200'][i]) and pd.notna(self.data['SMA_50'][i-1]) and pd.notna(self.data['SMA_200'][i-1]):
                    if self.data['SMA_50'][i] > self.data['SMA_200'][i] and self.data['SMA_50'][i-1] <= self.data['SMA_200'][i-1]:
                        signals.append('buy')
                    elif self.data['SMA_50'][i] < self.data['SMA_200'][i] and self.data['SMA_50'][i-1] >= self.data['SMA_200'][i-1]:
                        signals.append('sell')
                    else:
                        signals.append('hold')
                else:
                    signals.append('hold')  # Handle cases where SMA values are None

                # Additional conditions based on other indicators (example):
                if self.data['RSI'][i] < 30:
                    signals[-1] = 'buy'  # Adjust based on your RSI strategy
                elif self.data['RSI'][i] > 70:
                    signals[-1] = 'sell'  # Adjust based on your RSI strategy

                # Example for MACD:
                if self.data['MACD'][i] > self.data['MACD_signal'][i]:
                    signals[-1] = 'buy'
                elif self.data['MACD'][i] < self.data['MACD_signal'][i]:
                    signals[-1] = 'sell'

            self.data['signal'] = signals
            logging.info("Generated trading signals")
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

def main():
    try:
        time_offset = synchronize_system_time()
        logging.info("System time synchronized with offset: %d ms", time_offset)

        bot = TradingBot(API_KEY, API_SECRET)
        bot.initialize_exchange()

        # Fetch data
        data = bot.fetch_ohlcv('BTCUSDT', time_offset=time_offset)

        # Initialize TechnicalIndicators class with fetched data
        indicators = TechnicalIndicators(API_KEY, API_SECRET, data=data)

        # Calculate indicators
        indicators.calculate_indicators()

        # Apply trading strategy
        indicators.trading_strategy()

        # Execute trades based on signals
        indicators.data.apply(lambda row: indicators.execute_trade('BTCUSDT', row['signal']), axis=1)

        print(indicators.data.tail())

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
