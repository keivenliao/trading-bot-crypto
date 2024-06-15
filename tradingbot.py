import logging
import time
import ntplib
import ccxt
import pandas as pd
import pandas_ta as ta
from APIs import load_api_credentials
from fetch_data import fetch_historical_data
from technical_indicators import calculate_technical_indicators
from trading_strategy import generate_signals
from risk_management import apply_position_sizing, apply_stop_loss
from portfolio_management import track_portfolio_performance, rebalance_portfolio
from monitoring import track_performance_metrics, send_notification
from backtesting import backtest_strategy

# Setup logging
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
            self.exchange = ccxt.bybit({
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,  # This helps to avoid rate limit errors
            })
            logging.info("Initialized Bybit exchange")
        except Exception as e:
            logging.error(f"Failed to initialize exchange: {e}")
            raise e

    def fetch_data(self, symbol='BTC/USDT', timeframe='1h', limit=100):
        try:
            params = {
                'recvWindow': 10000,
                'timestamp': int(time.time() * 1000 + self.synchronize_time())
            }
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, params=params)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            logging.info(f"Fetched OHLCV data for {symbol}")
            return df
        except Exception as e:
            logging.error(f"An error occurred while fetching data: {e}")
            raise e

    def calculate_indicators(self, df):
        df['SMA_50'] = ta.sma(df['close'], length=50)
        df['SMA_200'] = ta.sma(df['close'], length=200)
        df['EMA_12'] = ta.ema(df['close'], length=12)
        df['EMA_26'] = ta.ema(df['close'], length=26)
        macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
        df['MACD'] = macd['MACD_12_26_9']
        df['MACD_signal'] = macd['MACDs_12_26_9']
        df['RSI'] = ta.rsi(df['close'], length=14)
        logging.info("Calculated technical indicators")
        return df

    def generate_signals(self, df):
        df['Buy_Signal'] = (df['close'] > df['SMA_50']) & (df['SMA_50'] > df['SMA_200']) & (df['MACD'] > df['MACD_signal']) & (df['RSI'] < 70)
        df['Sell_Signal'] = (df['close'] < df['SMA_50']) & (df['SMA_50'] < df['SMA_200']) & (df['MACD'] < df['MACD_signal']) & (df['RSI'] > 30)
        logging.info("Generated buy and sell signals")
        return df

    def simulate_trading(self, df):
        try:
            for i in range(len(df)):
                if df['Buy_Signal'].iloc[i]:
                    self.place_order('buy', df['close'].iloc[i], 'BTC/USDT', 0.001)
                elif df['Sell_Signal'].iloc[i]:
                    self.place_order('sell', df['close'].iloc[i], 'BTC/USDT', 0.001)
            logging.info("Simulated trading completed")
        except Exception as e:
            logging.error(f"Error occurred during simulated trading: {e}")
            raise e

    def place_order(self, side, price, symbol, amount):
        try:
            logging.info(f"Simulating {side} order for {amount} {symbol} at {price}")
            # Implement logic to log simulated trades or adjust portfolio
        except Exception as e:
            logging.error(f"Failed to simulate {side} order: {e}")
            raise e

def main():
    try:
        # Load API credentials #
        api_key, api_secret = load_api_credentials()

        # Initialize TradingBot instance
        bot = TradingBot(api_key, api_secret)
        bot.initialize_exchange()
        
        # Fetch historical data
        historical_data = fetch_historical_data(bot.exchange, symbol='BTC/USDT', timeframe='1d', limit=365)
        
        # Calculate technical indicators
        df_with_indicators = bot.calculate_indicators(historical_data)
        
        # Generate trading signals
        signals_df = bot.generate_signals(df_with_indicators)
        
        # Apply risk management
        apply_position_sizing(signals_df, risk_percentage=0.02)  # Example: Risk 2% per trade
        apply_stop_loss(signals_df, stop_loss_percentage=0.05)  # Example: 5% stop loss
        
        # Perform backtesting
        backtest_strategy(signals_df)
        
        # Monitor portfolio performance
        track_portfolio_performance()
        
        # Rebalance portfolio if necessary
        rebalance_portfolio()
        
        # Track bot performance metrics
        track_performance_metrics(signals_df)
        
        # Send notifications/alerts
        send_notification("Trading bot executed successfully.")
        
    except Exception as e:
        logging.error(f"An error occurred during the main execution: {e}")

if __name__ == "__main__":
    main()
