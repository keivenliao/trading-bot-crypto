import ccxt
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

API_KEY = 'YOUR_API_KEY'
API_SECRET = 'YOUR_API_SECRET'

def test_api_credentials(api_key, api_secret):
    """
    Test API credentials by fetching account balance, open orders, and placing a test order.
    """
    try:
        exchange = ccxt.bybit({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
        })

        # Fetch account balance
        balance = exchange.fetch_balance()
        logging.info("Successfully fetched balance: %s", balance)

        # Fetch open orders
        orders = exchange.fetch_open_orders()
        logging.info("Successfully fetched open orders: %s", orders)

        # Example: Place a test order (uncomment to execute)
        # test_order = exchange.create_limit_buy_order('BTC/USDT', 0.001, 35000)
        # logging.info("Test order placed successfully: %s", test_order)

        return balance, orders

    except ccxt.BaseError as e:
        logging.error("Error testing API credentials: %s", e)
        raise e

if __name__ == "__main__":
    test_api_credentials(API_KEY, API_SECRET)
