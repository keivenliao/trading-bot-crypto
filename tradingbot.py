import ccxt
import pandas as pd
import pandas_ta as ta
import time
import logging
import ntplib

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradingBot:
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret
        self.exchange = None
        self.ntp_server = 'time.google.com'
        self.max_retries = 3
        self.backoff_factor = 1

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
            logging.error("Failed to initialize exchange: %s", e)
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
            logging.info("Fetched OHLCV data for %s", symbol)
            return df
        except Exception as e:
            logging.error("An error occurred while fetching data: %s", e)
            raise e

    def calculate_indicators(self, df):
        df['SMA50'] = ta.sma(df['close'], length=50)
        df['SMA200'] = ta.sma(df['close'], length=200)
        df['EMA12'] = ta.ema(df['close'], length=12)
        df['EMA26'] = ta.ema(df['close'], length=26)
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        df['MACD'] = macd['MACD_12_26_9']
        df['MACD_signal'] = macd['MACDs_12_26_9']
        df['RSI'] = ta.rsi(df['close'], length=14)
        df['SAR'] = ta.sar(df['high'], df['low'], df['close'])
        return df

    def generate_signals(self, df):
        df['Buy_Signal'] = (df['close'] > df['SMA50']) & (df['SMA50'] > df['SMA200']) & (df['MACD'] > df['MACD_signal']) & (df['RSI'] < 70)
        df['Sell_Signal'] = (df['close'] < df['SMA50']) & (df['SMA50'] < df['SMA200']) & (df['MACD'] < df['MACD_signal']) & (df['RSI'] > 30)
        return df

    def place_order_with_risk_management(self, symbol, side, amount, stop_loss_pct, take_profit_pct):
        try:
            # Place market order
            order = self.exchange.create_order(symbol, 'market', side, amount)
            price = order['price']

            # Calculate stop loss and take profit prices
            if side == 'buy':
                stop_loss_price = price * (1 - stop_loss_pct)
                take_profit_price = price * (1 + take_profit_pct)
                stop_loss_side = 'sell'
                take_profit_side = 'sell'
            else:
                stop_loss_price = price * (1 + stop_loss_pct)
                take_profit_price = price * (1 - take_profit_pct)
                stop_loss_side = 'buy'
                take_profit_side = 'buy'

            # Place stop loss and take profit orders
            self.exchange.create_order(symbol, 'stop', stop_loss_side, amount, stop_loss_price)
            self.exchange.create_order(symbol, 'limit', take_profit_side, amount, take_profit_price)

            logging.info(f"Placed {side} order for {amount} {symbol} at {price} with stop loss at {stop_loss_price} and take profit at {take_profit_price}")

        except Exception as e:
            logging.error(f"Failed to place order with risk management: {e}")
            raise e

    def execute_trades(self, df):
        position = None
        stop_loss = None
        take_profit = None
        
        for i in range(len(df)):
            if df['Buy_Signal'].iloc[i] and position is None:
                position = 'long'
                stop_loss = df['close'].iloc[i] * 0.95
                take_profit = df['close'].iloc[i] * 1.10
                logging.info(f"Buy at {df['close'].iloc[i]}, Stop Loss: {stop_loss}, Take Profit: {take_profit}")
                self.place_order_with_risk_management('BTC/USDT', 'buy', 0.001, 0.05, 0.10)
            
            elif df['Sell_Signal'].iloc[i] and position == 'long':
                position = None
                logging.info(f"Sell at {df['close'].iloc[i]}")
                self.place_order_with_risk_management('BTC/USDT', 'sell', 0.001, 0.05, 0.10)
            
            elif position == 'long' and df['close'].iloc[i] <= stop_loss:
                position = None
                logging.info(f"Stop Loss Hit at {df['close'].iloc[i]}")
                self.place_order_with_risk_management('BTC/USDT', 'sell', 0.001, 0.05, 0.10)
            
            elif position == 'long' and df['close'].iloc[i] >= take_profit:
                position = None
                logging.info(f"Take Profit Hit at {df['close'].iloc[i]}")
                self.place_order_with_risk_management('BTC/USDT', 'sell', 0.001, 0.05, 0.10)

