import ccxt.bybit
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def initialize_exchange(api_key, api_secret):
    """
    Initialize a Bybit exchange with the provided API key and secret.
    """
    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })
        logging.info("Initialized Bybit exchange")
        return exchange
    except ccxt.AuthenticationError as auth_error:
        logging.error("Authentication failed with Bybit: %s", auth_error)
    except ccxt.ExchangeError as exchange_error:
        logging.error("Exchange error with Bybit: %s", exchange_error)
    except ccxt.NetworkError as net_error:
        logging.error("A network error occurred with Bybit: %s", net_error)
    except ccxt.BaseError as base_error:
        logging.error("An unexpected error occurred with Bybit: %s", base_error)
    return None

def initialize_exchanges(api_info_list):
    """
    Initialize Bybit exchanges using a list of API key and secret information.
    """
    exchanges = []
    for api_info in api_info_list:
        api_key = api_info.get('api_key')
        api_secret = api_info.get('api_secret')
        if api_key and api_secret:
            exchange = initialize_exchange(api_key, api_secret)
            if exchange:
                exchanges.append(exchange)
    return exchanges

def example_usage(exchanges):
    """
    Perform example operations with each Bybit exchange.
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
    bybit_api_key_1 = os.getenv('BYBIT_API_KEY_1')
    bybit_api_secret_1 = os.getenv('BYBIT_API_SECRET_1')
    bybit_api_key_2 = os.getenv('BYBIT_API_KEY_2')
    bybit_api_secret_2 = os.getenv('BYBIT_API_SECRET_2')

    # Define Bybit API keys and secrets
    bybit_apis = [
        {'api_key': bybit_api_key_1, 'api_secret': bybit_api_secret_1},
        {'api_key': bybit_api_key_2, 'api_secret': bybit_api_secret_2},
        # Add more Bybit API keys and secrets as needed
    ]

    # Initialize Bybit exchanges
    bybit_exchanges = initialize_exchanges(bybit_apis)

    # Perform example usage with initialized exchanges
    example_usage(bybit_exchanges)
