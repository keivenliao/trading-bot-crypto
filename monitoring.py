import logging
import pandas as pd

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

# Example usage
if __name__ == "__main__":
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
