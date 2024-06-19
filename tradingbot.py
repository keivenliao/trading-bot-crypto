import ccxt
import pandas as pd
import logging
import os
import time
import ntplib
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import pandas_ta as ta

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv(dotenv_path='C:/Users/amrita/Desktop/improvised-code-of-the-pdf-GPT-main/API.env')

app = Flask(__name__)

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

    def fetch_data(self, symbol='BTCUSDT', timeframe='1h', limit=100):
        try:
            params = {
                'recvWindow': 10000,
                'timestamp': int(time.time() * 1000 + self.synchronize_time())
            }
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit, params)
            
            # Print the fetched OHLCV data for debugging
            logging.info(f"Fetched OHLCV raw data: {ohlcv}")
            
            # Example handling of unexpected nested structures
            if isinstance(ohlcv, list):
                # Check if all items are lists, if not handle the nested structure
                if all(isinstance(item, list) for item in ohlcv):
                    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                else:
                    # Handle case where each item might be a dictionary or another nested structure
                    ohlcv_flat = [[item.get('timestamp'), item.get('open'), item.get('high'), item.get('low'), item.get('close'), item.get('volume')] if isinstance(item, dict) else item for item in ohlcv]
                    df = pd.DataFrame(ohlcv_flat, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                logging.info(f"Fetched OHLCV data for {symbol}")
                return df
            else:
                logging.error(f"Unexpected data structure: {ohlcv}")
                raise ValueError("Unexpected data structure from fetch_ohlcv")
        except Exception as e:
            logging.error(f"An error occurred while fetching data: {e}")
            raise e

    def calculate_indicators(self, df):
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

    def generate_signals(self, df):
        df['Buy_Signal'] = (df['close'] > df['SMA_50']) & (df['SMA_50'] > df['SMA_200']) & (df['MACD'] > df['MACD_signal']) & (df['RSI'] < 70)
        df['Sell_Signal'] = (df['close'] < df['SMA_50']) & (df['SMA_50'] < df['SMA_200']) & (df['MACD'] < df['MACD_signal']) & (df['RSI'] > 30)
        logging.info("Generated buy and sell signals")
        return df

    def place_order(self, side, symbol, amount):
        try:
            logging.info(f"Placing {side} order for {amount} {symbol}")
            self.exchange.create_market_order(symbol, side, amount)
            logging.info(f"Order placed: {side} {amount} {symbol}")
        except Exception as e:
            logging.error(f"Failed to place {side} order: {e}")
            raise e

    def manage_leverage(self, symbol, amount, risk_percent):
        try:
            balance = self.exchange.fetch_balance()
            available_margin = balance['total']['USDT']
            logging.info(f"Available margin: {available_margin} USDT")
            
            max_loss = available_margin * risk_percent
            max_leverage = max_loss / (amount * self.exchange.fetch_ticker(symbol)['last'])
            max_leverage = min(max_leverage, self.exchange.markets[symbol]['limits']['leverage']['max'])
            
            self.exchange.set_leverage(max_leverage, symbol)
            logging.info(f"Dynamically set leverage to {max_leverage:.2f} for {symbol} based on risk management")
            return max_leverage
        except ccxt.BaseError as e:
            logging.error(f"Failed to manage leverage: {e}")
            raise

    def execute_trading_strategy(self, df, symbol, amount, risk_percent):
        try:
            self.exchange.load_markets()
            for i in range(len(df)):
                logging.info(f"Processing signal: {df['signal'][i]} at index {i}")
                if df['signal'][i] in ['buy', 'sell']:
                    self.manage_leverage(symbol, amount, risk_percent)
                    if df['signal'][i] == 'buy':
                        logging.info("Buy Signal - Placing Buy Order")
                        self.place_order('buy', symbol, amount)
                    elif df['signal'][i] == 'sell':
                        logging.info("Sell Signal - Placing Sell Order")
                        self.place_order('sell', symbol, amount)
        except ccxt.BaseError as e:
            logging.error(f"An error occurred: {e}")
            raise

    def simulate_trading(self, df, amount=0.001):
        try:
            for i in range(len(df)):
                if df['Buy_Signal'].iloc[i]:
                    self.place_order('buy', 'BTCUSDT', amount)
                elif df['Sell_Signal'].iloc[i]:
                    self.place_order('sell', 'BTCUSDT', amount)
            logging.info("Simulated trading completed")
        except Exception as e:
            logging.error(f"Error occurred during simulated trading: {e}")
            raise e

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    logging.info(f"Received webhook data: {data}")

    symbol = 'BTCUSDT'
    amount = 0.001  # Example amount to trade
    risk_percent = 0.01  # Risk 1% of the available margin per trade

    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')

    if not api_key or not api_secret:
        return jsonify({"error": "BYBIT_API_KEY or BYBIT_API_SECRET environment variables are not set."}), 400

    bot = TradingBot(api_key, api_secret)
    bot.initialize_exchange()

    try:
        if data['action'] == 'buy':
            logging.info("Webhook Buy Signal - Placing Buy Order")
            bot.place_order('buy', symbol, amount)
        elif data['action'] == 'sell':
            logging.info("Webhook Sell Signal - Placing Sell Order")
            bot.place_order('sell', symbol, amount)
        return jsonify({"status": "success"}), 200

    except Exception as e:
        logging.error(f"Failed to process webhook data: {e}")
        return jsonify({"error": str(e)}), 500

def main():
    try:
        api_key = os.getenv('BYBIT_API_KEY')
        api_secret = os.getenv('BYBIT_API_SECRET')

        bot = TradingBot(api_key, api_secret)
        bot.initialize_exchange()
        
        historical_data = bot.fetch_data(symbol='BTCUSDT', timeframe='1d', limit=365)
        
        df_with_indicators = bot.calculate_indicators(historical_data)
        
        signals_df = bot.generate_signals(df_with_indicators)
        
        bot.simulate_trading(signals_df)
        
        logging.info("Trading bot executed successfully.")
    except Exception as e:
        logging.error(f"An error occurred during the main execution: {e}")

if __name__ == "__main__":
    main()
    app.run(port=5000)
