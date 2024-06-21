import subprocess
import sys

# Ensure the required library is installed
subprocess.check_call([sys.executable, "-m", "pip", "install", "scikit-learn"])

import ccxt
import pandas as pd
import pandas_ta as ta
import logging
import os
import time
import ntplib
import numpy as np
import gym
from stable_baselines3 import PPO
from sklearn.preprocessing import MinMaxScaler
from keras.models import Sequential
from keras.layers import LSTM, Dense
from datetime import datetime
import ta
from fetch_data import main


# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Environment variables for API credentials
API_KEY = os.getenv('BYBIT_API_KEY')
API_SECRET = os.getenv('BYBIT_API_SECRET')

class TradingEnv(gym.Env):
    def __init__(self, df):
        super(TradingEnv, self).__init__()
        self.df = df
        self.current_step = 0
        self.action_space = gym.spaces.Discrete(3)  # 0: Hold, 1: Buy, 2: Sell
        self.observation_space = gym.spaces.Box(low=0, high=1, shape=(len(df.columns),))

    def reset(self):
        self.current_step = 0
        return self.df.iloc[self.current_step].values

    def step(self, action):
        self.current_step += 1
        reward = self.df.iloc[self.current_step]['profit'] if action == 1 else -self.df.iloc[self.current_step]['loss']
        done = self.current_step == len(self.df) - 1
        obs = self.df.iloc[self.current_step].values
        return obs, reward, done, {}

def train_rl_model(df):
    env = TradingEnv(df)
    model = PPO('MlpPolicy', env, verbose=1)
    model.learn(total_timesteps=10000)
    return model

def rl_trading_decision(model, obs):
    action, _ = model.predict(obs)
    return action

def synchronize_system_time():
    """
    Synchronize system time with an NTP server.
    """
    try:
        response = ntplib.NTPClient().request('pool.ntp.org')
        current_time = datetime.fromtimestamp(response.tx_time)
        logging.info(f"System time synchronized: {current_time}")
        return int((current_time - datetime.utcnow()).total_seconds() * 1000)  # Return time offset in milliseconds
    except Exception as e:
        logging.error("Time synchronization failed: %s", e)
        return 0  # Return zero offset in case of failure

# tradingbot/trading_strategy.py

def detect_signals(df):
    latest = df.iloc[-1]
    previous = df.iloc[-2]

    # Example strategy combining SMA crossover and RSI
    if (previous['SMA_20'] < previous['SMA_50'] and latest['SMA_20'] > latest['SMA_50']) and latest['RSI'] < 70:
        return 'buy'
    elif (previous['SMA_20'] > previous['SMA_50'] and latest['SMA_20'] < latest['SMA_50']) and latest['RSI'] > 30:
        return 'sell'
    return 'hold'


def generate_signals(df):
    """
    Generate trading signals based on technical analysis of OHLCV data.
    
    Parameters:
    df (pd.DataFrame): DataFrame containing OHLCV data with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume'].

    Returns:
    pd.DataFrame: DataFrame with additional columns for trading signals.
    """
    # Calculate technical indicators
    df['SMA_50'] = ta.sma(df['close'], length=50)
    df['SMA_200'] = ta.sma(df['close'], length=200)
    df['RSI'] = ta.rsi(df['close'], length=14)

    # Generate signals based on indicators
    signals = []
    for i in range(len(df)):
        if df['SMA_50'][i] > df['SMA_200'][i] and df['RSI'][i] > 50:
            signals.append('buy')
        elif df['SMA_50'][i] < df['SMA_200'][i] and df['RSI'][i] < 50:
            signals.append('sell')
        else:
            signals.append('hold')

    df['signal'] = signals

    logging.info("Generated buy and sell signals")
    return df


def initialize_exchange(api_key, api_secret):
    """
    Initialize the Bybit exchange.
    """
    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })
        logging.info("Initialized Bybit exchange")
        return exchange
    except ccxt.BaseError as e:
        logging.error("Failed to initialize exchange: %s", e)
        raise e

def fetch_ohlcv(exchange, symbol, timeframe='1h', limit=100, time_offset=0):
    """
    Fetch OHLCV data from the exchange.
    """
    params = {
        'recvWindow': 10000,
        'timestamp': int(time.time() * 1000 + time_offset)
    }
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit, params=params)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        logging.info(f"Fetched OHLCV data for {symbol}")
        return df
    except ccxt.BaseError as e:
        logging.error("Error fetching OHLCV data: %s", e)
        raise e

def calculate_indicators(df):
    """
    Calculate technical indicators using ta library.
    """
    try:
        # Simple Moving Averages
        df['SMA_50'] = ta.trend.sma_indicator(df['close'], window=50)
        df['SMA_200'] = ta.trend.sma_indicator(df['close'], window=200)
        
        # Exponential Moving Averages
        df['EMA_12'] = ta.trend.ema_indicator(df['close'], window=12)
        df['EMA_26'] = ta.trend.ema_indicator(df['close'], window=26)
        
        # MACD
        macd = ta.trend.MACD(df['close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        
        # RSI
        df['RSI'] = ta.momentum.rsi(df['close'], window=14)
        
        logging.info("Calculated technical indicators")
    except Exception as e:
        logging.error("Error calculating indicators: %s", e)
        raise e
    return df

def prepare_data(df, n_features):
    data = df.values
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_data = scaler.fit_transform(data)
    X, y = [], []
    for i in range(len(scaled_data)-n_features-1):
        X.append(scaled_data[i:(i+n_features), 0])
        y.append(scaled_data[i + n_features, 0])
    return np.array(X), np.array(y), scaler

def build_and_train_model(df):
    n_features = 60
    X, y, scaler = prepare_data(df, n_features)

    model = Sequential()
    model.add(LSTM(50, return_sequences=True, input_shape=(n_features, 1)))
    model.add(LSTM(50))
    model.add(Dense(1))
    model.compile(optimizer='adam', loss='mean_squared_error')
    model.fit(X, y, epochs=20, batch_size=32)

    return model, scaler

def predict_prices(model, scaler, df):
    n_features = 60
    X, _, _ = prepare_data(df, n_features)
    predicted = model.predict(X)
    return scaler.inverse_transform(predicted)

def trading_strategy(df):
    """
    Define the trading strategy based on SMA crossover.
    """
    signals = ['hold']  # Initialize with 'hold' for the first entry
    for i in range(1, len(df)):
        if df['SMA_50'][i] > df['SMA_200'][i] and df['SMA_50'][i-1] <= df['SMA_200'][i-1]:
            signals.append('buy')
        elif df['SMA_50'][i] < df['SMA_200'][i] and df['SMA_50'][i-1] >= df['SMA_200'][i-1]:
            signals.append('sell')
        else:
            signals.append('hold')
    df['signal'] = signals
    logging.info("Defined trading strategy")
    return df

def execute_trade(exchange, symbol, signal, amount=1):
    """
    Execute trades based on signals.
    """
    try:
        if signal == 'buy':
            logging.info("Executing Buy Order")
            exchange.create_market_buy_order(symbol, amount)
        elif signal == 'sell':
            logging.info("Executing Sell Order")
            exchange.create_market_sell_order(symbol, amount)
    except ccxt.BaseError as e:
        logging.error(f"Error executing {signal} order: {e}")
        raise e
    
if __name__ == "__main__":
    main()
