import logging
import os
import ccxt
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(dotenv_path='C:/Users/amrita/Desktop/improvised-code-of-the-pdf-GPT-main/API.env')

def load_api_credentials(key_number):
    """
    Load API credentials from environment variables.
    
    Parameters:
    - key_number (int): The index number of the API key to load (1 or 2).
    
    Returns:
    - (str, str): Tuple containing the API key and API secret.
    """
    api_key = os.getenv(f'BYBIT_API_KEY_{key_number}')
    api_secret = os.getenv(f'BYBIT_API_SECRET_{key_number}')
    logging.info(f"Loaded API credentials for key_number {key_number}: API_KEY={api_key[:4]}****, API_SECRET={api_secret[:4]}****")
    return api_key, api_secret

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def track_performance_metrics(df):
    """
    Track and log basic performance metrics of the provided DataFrame.
    
    Parameters:
    - df (pd.DataFrame): DataFrame containing historical price data with columns ['timestamp', 'open', 'high', 'low', 'close', 'volume'].
    """
    if df.empty:
        logging.warning("DataFrame is empty. No metrics to track.")
        return
    
    # Calculate basic metrics
    mean_close = df['close'].mean()
    std_close = df['close'].std()
    moving_average_10 = df['close'].rolling(window=10).mean()
    moving_average_50 = df['close'].rolling(window=50).mean()
    
    # Log the metrics
    logging.info(f"Mean Close Price: {mean_close}")
    logging.info(f"Standard Deviation of Close Price: {std_close}")
    logging.info("10-period Moving Average of Close Price:")
    logging.info(moving_average_10.tail())
    logging.info("50-period Moving Average of Close Price:")
    logging.info(moving_average_50.tail())
    
    # Check for crossing moving averages (simple example of a trading signal)
    if moving_average_10.iloc[-1] > moving_average_50.iloc[-1]:
        send_notification("10-period moving average crossed above 50-period moving average.")
    elif moving_average_10.iloc[-1] < moving_average_50.iloc[-1]:
        send_notification("10-period moving average crossed below 50-period moving average.")

def send_notification(message):
    """
    Send a notification with the provided message.
    
    Parameters:
    - message (str): The notification message to be sent.
    """
    # Here you can implement the actual notification sending logic (e.g., email, SMS, etc.)
    # For the purpose of this example, we will just log the message.
    logging.info(message)

def initialize_exchange(api_key, api_secret):
    """
    Initialize a Bybit exchange using API credentials.
    """
    if not api_key or not api_secret:
        error_message = "API key or secret is missing."
        logging.error(error_message)
        send_notification(error_message)
        return None
    
    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,  # This helps to avoid rate limit errors
        })
        logging.info("Initialized Bybit exchange")
        send_notification(f"Initialized Bybit exchange with API key: {api_key[:4]}****")
        return exchange
    except ccxt.AuthenticationError as auth_error:
        error_message = f"Authentication failed with Bybit: {auth_error}"
        logging.error(error_message)
        send_notification(error_message)
    except ccxt.ExchangeError as exchange_error:
        error_message = f"Exchange error with Bybit: {exchange_error}"
        logging.error(error_message)
        send_notification(error_message)
    except ccxt.NetworkError as net_error:
        error_message = f"A network error occurred with Bybit: {net_error}"
        logging.error(error_message)
        send_notification(error_message)
    except Exception as e:
        error_message = f"An unexpected error occurred: {str(e)}"
        logging.error(error_message)
        send_notification(error_message)
        raise e
    return None

def initialize_multiple_exchanges():
    """
    Initialize multiple Bybit exchanges using different API keys and secrets.
    """
    exchanges = []
    for i in range(1, 3):  # Assuming two sets of API keys and secrets
        api_key, api_secret = load_api_credentials(i)
        if api_key and api_secret:
            exchange = initialize_exchange(api_key, api_secret)
            if exchange:
                exchanges.append(exchange)
        else:
            error_message = f"API key or secret is missing for key: {api_key} secret: {api_secret}"
            logging.error(error_message)
            send_notification(error_message)

    return exchanges

if __name__ == "__main__":
    exchanges = initialize_multiple_exchanges()
    if exchanges:
        success_message = "Successfully initialized all exchanges."
        logging.info(success_message)
        send_notification(success_message)
    else:
        error_message = "Failed to initialize exchanges."
        logging.error(error_message)
        send_notification(error_message)

    # Example usage
    # Sample DataFrame for demonstration purposes
    data = {
        'timestamp': pd.date_range(start='2021-01-01', periods=100, freq='h'),
        'open': pd.Series(range(100)),
        'high': pd.Series(range(1, 101)),
        'low': pd.Series(range(100)),
        'close': pd.Series(range(1, 101)),
        'volume': pd.Series(range(100, 200))
    }
    df = pd.DataFrame(data)
    
    track_performance_metrics(df)
