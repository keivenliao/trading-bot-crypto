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
    except Exception as e:
        logging.error("An unexpected error occurred: %s", str(e))
    return None

if __name__ == "__main__":
    api_key, api_secret = load_api_credentials()
    initialize_exchange(api_key, api_secret)
