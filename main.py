import logging

import ccxt
import pandas_ta as ta
from APIs import load_api_credentials
from exchanges import initialize_exchange
from technical_indicators import calculate_technical_indicators


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def example_usage(exchanges):
    """
    Perform example operations with each exchange.
    """
    for exchange in exchanges:
        try:
            # Example operations with each exchange
            logging.info("Fetching ticker data from Bybit...")
            ticker = exchange.fetch_ticker('BTC/USD')
            logging.info("Ticker data: %s", ticker)

            logging.info("Placing a mock order on Bybit...")
            order = exchange.create_order('BTC/USD', 'limit', 'buy', 0.001, 50000)
            logging.info("Order response: %s", order)
        
        except ccxt.NetworkError as net_error:
            logging.error("A network error occurred with Bybit: %s", net_error)
        except ccxt.ExchangeError as exchange_error:
            logging.error("An exchange error occurred with Bybit: %s", exchange_error)
        except ccxt.BaseError as base_error:
            logging.error("An unexpected error occurred with Bybit: %s", base_error)

if __name__ == "__main__":
    # Retrieve Bybit API keys and secrets from environment variables
    api_key_1, api_secret_1 = load_api_credentials()
    api_key_2, api_secret_2 = load_api_credentials()

    # Define Bybit API keys and secrets
    bybit_apis = [
        {'api_key': api_key_1, 'api_secret': api_secret_1},
        {'api_key': api_key_2, 'api_secret': api_secret_2},
        # Add more Bybit API keys and secrets as needed
    ]

    # Initialize Bybit exchanges
    bybit_exchanges = [initialize_exchange(api['api_key'], api['api_secret']) for api in bybit_apis if api['api_key'] and api['api_secret']]

    # Perform example usage with initialized exchanges
    example_usage(bybit_exchanges)


