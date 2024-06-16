import logging
import ccxt
from APIs import load_api_credentials
from exchanges import initialize_exchange
from example_usage import example_usage
from fetch_data import fetch_ohlcv
from synchronize_exchange_time import synchronize_system_time
from technical_indicators import calculate_indicators, execute_trade, trading_strategy

def setup_logging():
    """
    Set up logging configuration.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Main function to orchestrate the workflow.
    """
    try:
        setup_logging()

        # Retrieve Bybit API keys and secrets from environment variables or API module
        api_key_, api_secret_ = load_api_credentials()
        

        # Define Bybit API keys and secrets
        bybit_apis = [
            {'api_key': api_key_, 'api_secret': api_secret_},
            {'api_key': api_key_, 'api_secret': api_secret_},
            # Add more Bybit API keys and secrets as needed
        ]

        # Initialize Bybit exchanges
        bybit_exchanges = [initialize_exchange(api['api_key'], api['api_secret']) for api in bybit_apis if api['api_key'] and api['api_secret']]

        # Perform example usage with initialized exchanges
        example_usage(bybit_exchanges)

        # Optional: Uncomment the following if you want to execute a trading strategy
        # time_offset = synchronize_system_time()
        # logging.info("System time synchronized with offset: %d ms", time_offset)
        
        # exchange = initialize_exchange(API_KEY, API_SECRET)
        
        # df = fetch_ohlcv(exchange, 'BTC/USDT', time_offset=time_offset)
        # df = calculate_indicators(df)
        # df = trading_strategy(df)
        
        # df.apply(lambda row: execute_trade(exchange, 'BTC/USDT', row['signal']), axis=1)
        
        # print(df.tail())
        
    except ccxt.AuthenticationError as e:
        logging.error("Authentication error: %s. Please check your API key and secret.", e)
    except ccxt.NetworkError as e:
        logging.error("Network error: %s. Please check your internet connection.", e)
    except ccxt.ExchangeError as e:
        logging.error("Exchange error: %s. Please check the exchange status or API documentation.", e)
    except Exception as e:
        logging.error("An unexpected error occurred: %s", e)

if __name__ == "__main__":
    main()
