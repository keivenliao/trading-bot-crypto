import logging
import time
import ntplib
import pandas as pd
import numpy as np
import ccxt
from APIs import create_exchange_instance, load_api_credentials
from fetch_data import fetch_ohlcv
from risk_management import calculate_stop_loss, calculate_take_profit, calculate_position_size

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradingBot:
    def __init__(self, api_key, api_secret, ntp_server='time.google.com', max_retries=3, backoff_factor=1):
        self.api_key = api_key
        self.api_secret = api_secret
        self.ntp_server = ntp_server
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.exchange = None

    def synchronize_time(self):
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
                time.sleep(self.backoff_factor * retries)  # Exponential backoff
        logging.error(f"Max retries ({self.max_retries}) reached. Unable to synchronize time with {self.ntp_server}.")
        return 0  # Return 0 offset if synchronization fails

    def initialize_exchange(self):
        try:
            self.exchange = create_exchange_instance(self.api_key, self.api_secret)
            logging.info("Initialized exchange")
        except Exception as e:
            logging.error(f"Failed to initialize exchange: {e}")
            raise e

    def fetch_data(self, symbol='BTC/USDT', timeframe='1h', limit=100):
        try:
            params = {
                'recvWindow': 10000,
                'timestamp': int(time.time() * 1000 + self.synchronize_time())
            }
            df = fetch_ohlcv(self.exchange, symbol, timeframe, limit, params=params)
            logging.info(f"Fetched OHLCV data for {symbol}")
            return df
        except Exception as e:
            logging.error(f"An error occurred while fetching data: {e}")
            raise e

    def calculate_sma(self, series, window):
        return series.rolling(window=window, min_periods=1).mean()

    def calculate_ema(self, series, span):
        return series.ewm(span=span, adjust=False).mean()

    def calculate_macd(self, series, fast_period=12, slow_period=26, signal_period=9):
        exp1 = series.ewm(span=fast_period, adjust=False).mean()
        exp2 = series.ewm(span=slow_period, adjust=False).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        return macd_line, signal_line

    def calculate_rsi(self, series, window=14):
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(window=window, min_periods=1).mean()
        avg_loss = loss.rolling(window=window, min_periods=1).mean()
        rs = avg_gain / avg_loss.replace(to_replace=0, method='ffill').replace(to_replace=0, method='bfill')
        return 100 - (100 / (1 + rs))

    def calculate_indicators(self, df):
        try:
            df['SMA_50'] = self.calculate_sma(df['close'], window=50)
            df['SMA_200'] = self.calculate_sma(df['close'], window=200)
            df['EMA_12'] = self.calculate_ema(df['close'], span=12)
            df['EMA_26'] = self.calculate_ema(df['close'], span=26)
            macd_line, signal_line = self.calculate_macd(df['close'])
            df['MACD'] = macd_line
            df['MACD_signal'] = signal_line
            df['RSI'] = self.calculate_rsi(df['close'])
            logging.info("Calculated technical indicators")
            return df
        except Exception as e:
            logging.error(f"An error occurred while calculating indicators: {e}")
            raise e

    def detect_signals(self, df):
        try:
            df['Buy_Signal'] = (df['close'] > df['SMA_50']) & (df['SMA_50'] > df['SMA_200']) & (df['MACD'] > df['MACD_signal']) & (df['RSI'] < 70)
            df['Sell_Signal'] = (df['close'] < df['SMA_50']) & (df['SMA_50'] < df['SMA_200']) & (df['MACD'] < df['MACD_signal']) & (df['RSI'] > 30)
            logging.info("Generated buy and sell signals")
            return df
        except Exception as e:
            logging.error(f"An error occurred while generating signals: {e}")
            raise e

    def simulate_trading(self, df, amount=0.001):
        try:
            for i in range(len(df)):
                if df['Buy_Signal'].iloc[i]:
                    self.execute_trade('buy', df.iloc[i], amount)
                elif df['Sell_Signal'].iloc[i]:
                    self.execute_trade('sell', df.iloc[i], amount)
            logging.info("Simulated trading completed")
        except Exception as e:
            logging.error(f"An error occurred during simulated trading: {e}")
            raise e

    def execute_trade(self, signal, data_row, amount, balance=10, risk_percentage=1, risk_reward_ratio=2):
        try:
            entry_price = data_row['close']
            stop_loss = calculate_stop_loss(entry_price, risk_percentage, 10)  # Assuming leverage is always 10
            take_profit = calculate_take_profit(entry_price, risk_reward_ratio, stop_loss)
            position_size = calculate_position_size(balance, risk_percentage, stop_loss)
            
            if signal == 'buy':
                self.exchange.create_market_buy_order('BTC/USDT', position_size)
                logging.info(f"Buy order executed at {entry_price}, stop loss at {stop_loss}, take profit at {take_profit}")
            elif signal == 'sell':
                self.exchange.create_market_sell_order('BTC/USDT', position_size)
                logging.info(f"Sell order executed at {entry_price}, stop loss at {stop_loss}, take profit at {take_profit}")
            else:
                logging.info("No trade executed")
        except Exception as e:
            logging.error(f"Error executing trade: {e}")
            raise e

    def main():
        try:
            # Load API credentials
            api_key, api_secret = load_api_credentials()

            # Initialize TradingBot instance
            bot = TradingBot(api_key, api_secret)

            # Initialize exchange and fetch historical data
            bot.initialize_exchange()
            historical_data = bot.fetch_data(symbol='BTC/USDT', timeframe='1d', limit=365)

            # Calculate indicators, generate signals, and simulate trading
            df_with_indicators = bot.calculate_indicators(historical_data)
            signals_df = bot.detect_signals(df_with_indicators)
            bot.simulate_trading(signals_df)

                    
            logging.info("Trading bot executed successfully.")

        except Exception as e:
            logging.error(f"An error occurred during the main execution: {e}")

    if __name__ == "__main__":
        
        main()
