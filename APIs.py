import ccxt.bybit
import logging

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
    except ccxt.BaseError as e:
        logging.error("Failed to initialize Bybit exchange: %s", e)
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
            logging.info("Fetching data from Bybit...")
            # Replace the following lines with your actual code
            # data = exchange.fetch_data()
            # place_order = exchange.place_order(symbol, amount, price, side)
        except ccxt.NetworkError as net_error:
            logging.error("A network error occurred with Bybit: %s", net_error)
        except ccxt.BaseError as error:
            logging.error("An error occurred with Bybit: %s", error)

if __name__ == "__main__":
    # Define Bybit API keys and secrets
    bybit_apis = [
        {'api_key': 'YOUR_BYBIT_API_KEY_1', 'api_secret': 'YOUR_BYBIT_API_SECRET_1'},
        {'api_key': 'YOUR_BYBIT_API_KEY_2', 'api_secret': 'YOUR_BYBIT_API_SECRET_2'},
        # Add more Bybit API keys and secrets as needed
    ]

    # Initialize Bybit exchanges
    bybit_exchanges = initialize_exchanges(bybit_apis)

    # Perform example usage with initialized exchanges
    example_usage(bybit_exchanges)
