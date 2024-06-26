import os
import logging
import ccxt
from retrying import retry
import pandas as pd
import ta
from database import init_db, create_db_connection, fetch_historical_data, close_db_connection
from fetch_data import main as fetch_data_main, get_historical_data, get_tweets, analyze_sentiment
from risk_management import adjust_stop_loss_take_profit, calculate_stop_loss, calculate_take_profit, calculate_technical_indicators, detect_patterns, place_order_with_risk_management
from trading_strategy import build_and_train_model, predict_prices, train_rl_model, rl_trading_decision
from portfolio_management import calculate_returns, optimize_portfolio
import tradingbot

# Constants
DB_FILE = 'trading_bot.db'
TABLE_NAME = 'historical_data'

# Initialize the database and tables
init_db(DB_FILE)
fetch_data_main()  # Fetch and store historical data

# Logging Setup
def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load API Credentials
def load_api_credentials():
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    if not api_key or not api_secret:
        raise ValueError("BYBIT_API_KEY or BYBIT_API_SECRET environment variables are not set.")
    return api_key, api_secret

# Initialize Exchange
def initialize_exchange(api_key, api_secret):
    exchange = ccxt.bybit({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
    })
    logging.info("Initialized Bybit exchange")
    return exchange

# Fetch OHLCV Data with Retry
@retry(stop_max_attempt_number=3, wait_fixed=2000)
def fetch_ohlcv_with_retry(exchange, symbol, timeframe='1h', limit=500):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        logging.info(f"Fetched OHLCV data for {symbol}")
        return df
    except ccxt.BaseError as e:
        logging.error("Error fetching OHLCV data: %s", e)
        raise e

# Calculate Technical Indicators
def calculate_indicators(df):
    try:
        df['SMA_50'] = ta.trend.sma_indicator(df['close'], window=50)
        df['SMA_200'] = ta.trend.sma_indicator(df['close'], window=200)
        df['EMA_12'] = ta.trend.ema_indicator(df['close'], window=12)
        df['EMA_26'] = ta.trend.ema_indicator(df['close'], window=26)
        macd = ta.trend.MACD(df['close'])
        df['MACD'] = macd.macd()
        df['MACD_signal'] = macd.macd_signal()
        df['RSI'] = ta.momentum.rsi(df['close'], window=14)
        logging.info("Calculated technical indicators")
        return df
    except Exception as e:
        logging.error("Error calculating indicators: %s", e)
        raise e

# Define Trading Strategy
def trading_strategy(df, sma_short=50, sma_long=200):
    try:
        signals = ['hold']
        for i in range(1, len(df)):
            if df['SMA_' + str(sma_short)].iloc[i] > df['SMA_' + str(sma_long)].iloc[i] and df['SMA_' + str(sma_short)].iloc[i-1] <= df['SMA_' + str(sma_long)].iloc[i-1]:
                signals.append('buy')
            elif df['SMA_' + str(sma_short)].iloc[i] < df['SMA_' + str(sma_long)].iloc[i] and df['SMA_' + str(sma_short)].iloc[i-1] >= df['SMA_' + str(sma_long)].iloc[i-1]:
                signals.append('sell')
            else:
                signals.append('hold')
        df['signal'] = signals
        logging.info("Defined trading strategy")
        return df
    except KeyError as e:
        logging.error("Error detecting signals: %s", e)
        raise e

# Fetch Data for Backtesting
def get_data_for_backtesting():
    conn = create_db_connection(DB_FILE)
    if conn:
        data = fetch_historical_data(conn, TABLE_NAME)
        close_db_connection(conn)
        return data

# Execute Trade
def execute_trade(exchange, symbol, signal, amount=1):
    try:
        if signal == 'buy':
            logging.info("Executing Buy Order")
            exchange.create_market_buy_order(symbol, amount)
        elif signal == 'sell':
            logging.info("Executing Sell Order")
            exchange.create_market_sell_order(symbol, amount)
    except ccxt.BaseError as e:
        logging.error(f"Error executing {signal} order: %s", e)
        raise e

# Perform Backtesting
def perform_backtesting(exchange):
    try:
        df = fetch_ohlcv_with_retry(exchange, 'BTCUSDT', timeframe='1h', limit=500)
        df = calculate_indicators(df)
        df = trading_strategy(df)
        logging.info("Backtesting complete")
        print(df.tail())
    except Exception as e:
        logging.error("Error during backtesting: %s", e)
        if 'df' in locals() and len(df) < 30:  # Ensure enough data points for the longest SMA
            logging.error("Not enough data points to calculate SMAs")
            return

# Execute Trading Decision
def execute_trading_decision(exchange, symbol, decision, amount=1):
    try:
        if decision == 'buy':
            logging.info("Executing Buy Decision")
            execute_trade(exchange, symbol, 'buy', amount)
        elif decision == 'sell':
            logging.info("Executing Sell Decision")
            execute_trade(exchange, symbol, 'sell', amount)
        else:
            logging.info("Holding Position")
    except Exception as e:
        logging.error("Error executing trading decision: %s", e)
        raise e

# Main Function
def main():
    setup_logging()
    api_key, api_secret = load_api_credentials()
    exchange = initialize_exchange(api_key, api_secret)
    
    try:
        # Synchronize time (optional)
        time_offset = tradingbot.synchronize_time()
        print(f"Time offset: {time_offset} seconds")

        # Fetch data
        symbol = 'BTCUSDT'
        timeframe = '1h'
        limit = 100
        df = tradingbot.fetch_data(symbol, timeframe, limit)
        print(f"Fetched data:\n{df.head()}")

        # Calculate indicators
        df_with_indicators = tradingbot.calculate_indicators(df)
        print(f"Data with indicators:\n{df_with_indicators.head()}")

        # Example usage of historical data and technical indicators
        data = fetch_historical_data(exchange, symbol)
        data = calculate_technical_indicators(data)
        data = detect_patterns(data)

        # Example: Determine current market conditions
        if data.iloc[-1]['SMA_50'] > data.iloc[-1]['SMA_200']:
            stop_loss, take_profit = adjust_stop_loss_take_profit(data, data.iloc[-1]['close'])
            place_order_with_risk_management(exchange, symbol, 'buy', 0.001, stop_loss, take_profit)  # Place the order with stop loss and take profit
        elif data.iloc[-1]['SMA_50'] < data.iloc[-1]['SMA_200']:
            stop_loss, take_profit = adjust_stop_loss_take_profit(data, data.iloc[-1]['close'])
            place_order_with_risk_management(exchange, symbol, 'sell', 0.001, stop_loss, take_profit)  # Place the order with stop loss and take profit
        else:
            stop_loss = calculate_stop_loss(data.iloc[-1]['close'], 1.0, data)
            take_profit = calculate_take_profit(data.iloc[-1]['close'], 1.0, stop_loss)

        # Example: Place order with dynamic SL and TP
        # place_order_with_risk_management(exchange, symbol, 'buy', 0.001, stop_loss, take_profit)
    
    except ccxt.AuthenticationError as e:
        logging.error("Authentication error: %s. Please check your API key and secret.", e)
    except ccxt.NetworkError as e:
        logging.error("Network error: %s. Please check your internet connection.", e)
    except ccxt.ExchangeError as e:
        logging.error("Exchange error: %s. Please check the exchange status or API documentation.", e)
    except ValueError as e:
        logging.error("ValueError: %s", e)
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)

    # Fetch historical data
    df = get_historical_data('historical_data.csv')

    # Build and train predictive model
    model, scaler = build_and_train_model(df)

    # Predict prices
    predicted_prices = predict_prices(model, scaler, df)

    # Sentiment analysis
    tweets = get_tweets(api_key, api_secret, 'BTC')
    sentiment_score = analyze_sentiment(tweets)

    # RL model training
    rl_model = train_rl_model(df)

    # Portfolio optimization
    returns, cov_matrix = calculate_returns(df)
    optimal_weights = optimize_portfolio(returns, cov_matrix)
    print(f"Optimal asset allocation: {optimal_weights}")

    # Make trading decisions
    obs = df.iloc[-1].values  # Current observation
    rl_action = rl_trading_decision(rl_model, obs)

    if sentiment_score > 0.1:
        decision = 'buy'
    elif sentiment_score < -0.1:
        decision = 'sell'
    else:
        decision = 'hold'

    # Execute trading decision
    execute_trading_decision(exchange, symbol, decision)

if __name__ == "__main__":
    main()
