import os
import ccxt
import pandas as pd
import pandas_ta as ta
import logging
import time
import ntplib
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()
API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')

if not API_KEY or not API_SECRET:
    logging.error("API key and secret must be set as environment variables")
    exit(1)

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
            self.exchange = ccxt.bybit({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,  # This helps to avoid rate limit errors
            })
            logging.info("Initialized Bybit exchange")
        except Exception as e:
            logging.error(f"Failed to initialize exchange: {e}")
            raise e

    def fetch_data(self, symbol='BTC/USDT'):
        try:
            params = {
                'recvWindow': 10000,
                'timestamp': int(time.time() * 1000 + self.synchronize_time())
            }
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe='1h', limit=100, params=params)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            logging.info(f"Fetched OHLCV data for {symbol}")
            return df
        except Exception as e:
            logging.error(f"An error occurred while fetching data: {e}")
            raise e

    def calculate_indicators(self, df):
        df.ta.sma(length=50, append=True)
        df.ta.sma(length=200, append=True)
        df.ta.ema(length=12, append=True)
        df.ta.ema(length=26, append=True)
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        df['MACD'] = macd['MACD_12_26_9']
        df['MACD_signal'] = macd['MACDs_12_26_9']
        df.ta.rsi(length=14, append=True)
        df.ta.sar(append=True)
        logging.info("Calculated technical indicators")
        return df

    def generate_signals(self, df):
        df['Buy_Signal'] = (df['close'] > df['SMA_50']) & (df['SMA_50'] > df['SMA_200']) & (df['MACD'] > df['MACD_signal']) & (df['RSI'] < 70)
        df['Sell_Signal'] = (df['close'] < df['SMA_50']) & (df['SMA_50'] < df['SMA_200']) & (df['MACD'] < df['MACD_signal']) & (df['RSI'] > 30)
        logging.info("Generated buy and sell signals")
        return df

    def place_order_with_risk_management(self, symbol, side, amount, stop_loss_pct, take_profit_pct):
        try:
            order = self.exchange.create_market_order(symbol, side, amount)
            price = order['price']

            stop_loss_price = price * (1 - stop_loss_pct) if side == 'buy' else price * (1 + stop_loss_pct)
            take_profit_price = price * (1 + take_profit_pct) if side == 'buy' else price * (1 - take_profit_pct)

            self.exchange.create_order(symbol, 'stop', 'sell' if side == 'buy' else 'buy', amount, stop_loss_price)
            self.exchange.create_order(symbol, 'limit', 'sell' if side == 'buy' else 'buy', amount, take_profit_price)

            logging.info(f"Placed {side} order for {amount} {symbol} at {price} with SL at {stop_loss_price} and TP at {take_profit_price}")

        except Exception as e:
            logging.error(f"Failed to place order with risk management: {e}")
            raise e

    def execute_trades(self, df):
        for i in range(len(df)):
            if df['Buy_Signal'].iloc[i]:
                self.place_order_with_risk_management('BTC/USDT', 'buy', 0.001, 0.05, 0.10)
            elif df['Sell_Signal'].iloc[i]:
                self.place_order_with_risk_management('BTC/USDT', 'sell', 0.001, 0.05, 0.10)

# Main function to orchestrate the workflow
def main():
    try:
        bot = TradingBot(API_KEY, API_SECRET)
        time_offset = bot.synchronize_time()
        logging.info("Time synchronized with offset: %d", time_offset)
        
        bot.initialize_exchange()
        
        df = bot.fetch_data('BTC/USDT')
        df = bot.calculate_indicators(df)
        df = bot.generate_signals(df)
        
        bot.execute_trades(df)
        
        print(df.tail())
        
    except Exception as e:
        logging.error(f"An error occurred during the main execution: {e}")

# Run the main function
if __name__ == "__main__":
    main()
