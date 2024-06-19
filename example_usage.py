import logging
import ccxt

def example_usage(exchanges):
    """
    Perform example operations with each exchange.
    """
    for exchange in exchanges:
        try:
            # Example operations with each exchange
            logging.info("Fetching ticker data from Bybit...")
            ticker = exchange.fetch_ticker('BTCUSDT')
            logging.info("Ticker data: %s", ticker)

            logging.info("Placing a mock order on Bybit...")
            # Reduced amount to 0.0001 BTC for testing
            order = exchange.create_order('BTCUSDT', 'limit', 'buy', 0.0001, 66000)  # Adjusted price for the order
            logging.info("Order response: %s", order)
        
        except ccxt.NetworkError as net_error:
            logging.error("A network error occurred with Bybit: %s", net_error)
        except ccxt.ExchangeError as exchange_error:
            logging.error("An exchange error occurred with Bybit: %s", exchange_error)
        except ccxt.BaseError as base_error:
            logging.error("An unexpected error occurred with Bybit: %s", base_error)
