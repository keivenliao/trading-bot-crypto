# trading_bot.py

from datetime import datetime
import signal
import time
import logging
import pandas as pd
import pandas_ta as ta
import ntplib
import ccxt
from APIs import load_api_credentials, create_exchange_instance
from fetch_data import fetch_data, fetch_ohlcv
from risk_management import calculate_stop_loss, calculate_take_profit, calculate_position_size, calculate_technical_indicators, calculate_sma, calculate_rsi, calculate_macd, calculate_bollinger_bands, calculate_atr, risk_management
from sentiment_analysis import fetch_real_time_sentiment, analyze_sentiment
from config import API_KEY, API_SECRET, DB_FILE, TRAILING_STOP_PERCENT, RISK_REWARD_RATIO
from utils import send_email

# Logging Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradingBot:
    def __init__(self, api_key, api_secret, ntp_server='time.google.com', max_retries=3, backoff_factor=1, exchange_id='binance', symbol='BTCUSDT', timeframe='1h'):
        self.api_key = api_key
        self.api_secret = api_secret
        self.ntp_server = ntp_server
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.exchange = create_exchange_instance(self.api_key, self.api_secret)
        self.symbol = symbol
        self.timeframe = timeframe
        self.technical_indicators = None
        self.leverage = 50
        self.set_leverage(self.leverage)

    def initialize_exchange(self):
        try:
            self.exchange = ccxt.bybit({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
            })
            logging.info("Initialized Bybit exchange")
        except Exception as e:
            logging.error(f"Failed to initialize exchange: {e}")
            raise e

    def synchronize_time(self):
        try:
            client = ntplib.NTPClient()
            retries = 0
            while retries < self.max_retries:
                try:
                    response = client.request(self.ntp_server)
                    offset = response.offset
                    logging.info(f"Time synchronized with {self.ntp_server}. Offset: {offset} seconds")
                    return offset
                except ntplib.NTPException as e:
                    logging.warning(f"Failed to synchronize time on attempt {retries + 1} with {self.ntp_server}: {e}")
                    retries += 1
                    time.sleep(self.backoff_factor * retries)
            logging.error(f"Max retries ({self.max_retries}) reached. Unable to synchronize time with {self.ntp_server}.")
            return 0
        except Exception as e:
            logging.error(f"An unexpected error occurred during time synchronization: {e}")
            return 0

    def set_leverage(self, leverage):
        try:
            markets = self.exchange.load_markets()
            if self.symbol in markets:
                market = markets[self.symbol]
                self.exchange.fapiPrivate_post_leverage({
                    'symbol': market['id'],
                    'leverage': leverage,
                })
                logging.info(f"Leverage set to {leverage} for {self.symbol}")
        except Exception as e:
            logging.error(f"Error setting leverage: {e}")
            send_email("Trading Bot Error", f"Error setting leverage: {e}")
            raise

    def fetch_market_data(self, symbol, timeframe='1d', limit=100):
        return fetch_data(self.exchange, symbol, timeframe, limit)

    def fetch_data(self, symbol, timeframe='1h', limit=100):
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            logging.info(f"Fetched OHLCV data for {symbol}")
            return df
        except ccxt.BaseError as e:
            logging.error(f"Error fetching OHLCV data: {e}")
            raise e

    def update_indicators(self, df):
        from technical_indicators import TechnicalIndicators
        self.technical_indicators = TechnicalIndicators(df)

    def calculate_macd(self, close_prices, fast=12, slow=26, signal=9):
        try:
            exp1 = close_prices.ewm(span=fast, adjust=False).mean()
            exp2 = close_prices.ewm(span=slow, adjust=False).mean()
            macd = exp1 - exp2
            macd_signal = macd.ewm(span=signal, adjust=False).mean()
            macd_histogram = macd - macd_signal
            macd_df = pd.DataFrame({
                'MACD_12_26_9': macd,
                'MACDs_12_26_9': macd_signal,
                'MACDh_12_26_9': macd_histogram
            })
            return macd_df['MACD_12_26_9'], macd_df['MACDs_12_26_9']
        except Exception as e:
            print(f"Error calculating MACD: {e}")
            return None, None

    def calculate_rsi(self, series, window=14, period=14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_indicators(self, df, sma_short=20, sma_long=50, sma_longest=200,
                             ema_short=9, ema_mid=12, ema_long=26,
                             rsi_length=14, macd_fast=12, macd_slow=26, macd_signal=9):
        try:
            df['SMA_20'] = calculate_sma(df['close'], sma_short)
            df['SMA_50'] = calculate_sma(df['close'], sma_long)
            df['SMA_200'] = calculate_sma(df['close'], sma_longest)
        
            df['EMA_9'] = ta.ema(df['close'], length=ema_short)
            df['EMA_12'] = ta.ema(df['close'], length=ema_mid)
            df['EMA_26'] = ta.ema(df['close'], length=ema_long)
        
            df['RSI'] = calculate_rsi(df['close'], rsi_length)
        
            macd, macd_signal = self.calculate_macd(df['close'], macd_fast, macd_slow, macd_signal)
            df['MACD'] = macd
            df['MACD_signal'] = macd_signal
        
            upper_band, lower_band = calculate_bollinger_bands(df['close'], window=20)
            df['BB_upper'] = upper_band
            df['BB_lower'] = lower_band
        
            df['ATR'] = calculate_atr(df['high'], df['low'], df['close'], window=14)

            indicators = calculate_technical_indicators(df)
            logging.info("Technical indicators calculated successfully.")
            return indicators
        except Exception as e:
            logging.error(f"Error calculating technical indicators: {e}")
            send_email("Trading Bot Error", f"Error calculating technical indicators: {e}")
            raise

    def detect_signals(self, df):
        try:
            df['Buy_Signal'] = (df['close'] > df['SMA_50']) & (df['SMA_50'] > df['SMA_200']) & (df['MACD'] > df['MACD_signal']) & (df['RSI'] < 70)
            df['Sell_Signal'] = (df['close'] < df['SMA_50']) & (df['SMA_50'] < df['SMA_200']) & (df['MACD'] < df['MACD_signal']) & (df['RSI'] > 30)
            logging.info("Generated buy and sell signals")
            return df
        except Exception as e:
            logging.error(f"An error occurred while generating signals: {e}")
            raise e

    def trading_strategy(self, df):
        try:
            signals = ['hold']
            for i in range(1, len(df)):
                if pd.notna(df['SMA_50'][i]) and pd.notna(df['SMA_200'][i]) and pd.notna(df['SMA_50'][i-1]) and pd.notna(df['SMA_200'][i-1]):
                    if df['SMA_50'][i] > df['SMA_200'][i-1]:
                        signal = 'buy'
                    elif df['SMA_50'][i] < df['SMA_200'][i-1]:
                        signal = 'sell'

                    position_size = calculate_position_size()
                    stop_loss = calculate_stop_loss()
                    take_profit = calculate_take_profit()

                    if signal == 'buy':
                        self.exchange.create_market_buy_order(self.symbol, position_size)
                        logging.info(f"Buy order executed: Stop Loss ${stop_loss}, Take Profit ${take_profit}")
                    elif signal == 'sell':
                        self.exchange.create_market_sell_order(self.symbol, position_size)
                        logging.info(f"Sell order executed: Stop Loss ${stop_loss}, Take Profit ${take_profit}")

        except ccxt.BaseError as e:
            logging.error(f"Error executing {signal} order: {e}")
            raise e

    def execute_order(self, side, amount):
        try:
            order = self.exchange.create_order(self.symbol, 'market', side, amount)
            logging.info(f"Order executed: {order}")
            return order
        except Exception as e:
            logging.error(f"Error executing order: {e}")
            send_email("Trading Bot Error", f"Error executing order: {e}")
            raise

    def run(self, symbol='BTCUSDT', timeframe='1h', limit=100):
        try:
            self.initialize_exchange()
            self.synchronize_time()
            data = self.fetch_data(symbol, timeframe, limit)
            self.update_indicators(data)
            analyzed_data = self.calculate_indicators(data)
            signals = self.detect_signals(analyzed_data)
            self.trading_strategy(signals)
            
            if signals['buy'].iloc[-1]:
                logging.info("Buy signal detected.")
                self.execute_order('buy', 1)
            elif signals['sell'].iloc[-1]:
                logging.info("Sell signal detected.")
                self.execute_order('sell', 1)
            else:
                logging.info("No trading signal detected.")
            
        except Exception as e:
            logging.error(f"An unexpected error occurred during bot execution: {e}")
            raise e

if __name__ == "__main__":
    bot = TradingBot(API_KEY, API_SECRET)
    bot.run()
    time.sleep(1800)
