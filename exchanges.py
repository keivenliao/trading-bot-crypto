import os
import ccxt
import logging
from APIs import load_api_credentials  # Absolute import

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def initialize_exchange(api_key, api_secret):
    """
    Initialize a Bybit exchange using API credentials.
    """
    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,  # This helps to avoid rate limit errors
        })
        logging.info("Initialized Bybit exchange")
        return exchange
    except ccxt.AuthenticationError as auth_error:
        logging.error("Authentication failed with Bybit: %s", auth_error)
    except ccxt.ExchangeError as exchange_error:
        logging.error("Exchange error with Bybit: %s", exchange_error)
    except ccxt.NetworkError as net_error:
        logging.error("A network error occurred with Bybit: %s", net_error)
    except Exception as e:
        logging.error("An unexpected error occurred: %s", str(e))
        raise e
    return None


def initialize_multiple_exchanges():
    """
    Initialize multiple Bybit exchanges using different API keys and secrets.
    """
    api_keys = [os.getenv('BYBIT_API_KEY_1'), os.getenv('BYBIT_API_KEY_2')]
    api_secrets = [os.getenv('BYBIT_API_SECRET_1'), os.getenv('BYBIT_API_SECRET_2')]

    exchanges = []
    for key, secret in zip(api_keys, api_secrets):
        exchanges.append(initialize_exchange(key, secret))

    return exchanges


'''def initialize_multiple_exchanges():
    """
    Initialize multiple exchanges based on API credentials.
    """
    try:
        api_key, api_secret = load_api_credentials()

        # Define API keys and secrets for multiple exchanges
        exchanges = [
            {'api_key': api_key, 'api_secret': api_secret},
            # Add more exchanges as needed
        ]

        # Initialize exchanges
        initialized_exchanges = [initialize_exchange(api['api_key'], api['api_secret']) for api in exchanges]

        logging.info("Exchanges initialized successfully")
        return initialized_exchanges

    except Exception as e:
        logging.error("Error initializing exchanges: %s", e)
        return []'''

if __name__ == "__main__":
    exchanges = initialize_multiple_exchanges()
    # Now 'exchanges' is a list containing initialized exchange objects for each set of API credentials.
