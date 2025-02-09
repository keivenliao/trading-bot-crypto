import logging

import ccxt

from exchanges import send_notification

def example_usage(exchanges):
    for exchange in exchanges:
        try:
            logging.info("Fetching ticker data from Bybit...")
            ticker = exchange.fetch_ticker('BTCUSDT')  # Updated pair format
            logging.info("Ticker data: %s", ticker)

            logging.info("Placing a mock order on Bybit...")
            order = exchange.create_order('BTCUSDT', 'limit', 'buy', 0.0001, 66000)
            logging.info("Order response: %s", order)

            logging.info("Fetching account balance...")
            balance = exchange.fetch_balance()
            logging.info("Account balance: %s", balance)

            send_notification(f"Placed a mock order and fetched balance: {balance}")
        except ccxt.NetworkError as net_error:
            logging.error("A network error occurred with Bybit: %s", net_error)
        except ccxt.ExchangeError as exchange_error:
            logging.error("An exchange error occurred with Bybit: %s", exchange_error)
        except ccxt.BaseError as base_error:
            logging.error("An unexpected error occurred with Bybit: %s", base_error)

# Example usage
if __name__ == "__main__":
    # Assuming 'exchanges' is a list of CCXT exchange instances, e.g., Bybit
    exchanges = [
        ccxt.bybit({
            'apiKey': 'LzvSGu2mYFi2L6VtBL',
            'secret': 'KA3wvyIvMCJjGZEB0KVjH9WJSi30iwc9pIiG',
            'enableRateLimit': True,  # Enables rate limiting to manage API request rate
            # Add other necessary parameters based on Bybit API documentation
        })
    ]
    
    example_usage(exchanges)
