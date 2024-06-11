import ccxt
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_KEY = 'YOUR_API_KEY'
API_SECRET = 'YOUR_API_SECRET'

def test_api_credentials(api_key, api_secret):
    """
    Test API credentials by fetching account balance.
    """
    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })
        balance = exchange.fetch_balance()
        logging.info("Successfully fetched balance: %s", balance)
        return balance
    except ccxt.BaseError as e:
        logging.error("Error testing API credentials: %s", e)
        raise e

if __name__ == "__main__":
    test_api_credentials(API_KEY, API_SECRET)
