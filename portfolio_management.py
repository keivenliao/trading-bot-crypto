import logging
import pandas as pd
import ccxt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Bybit exchange
exchange = ccxt.bybit({
    'apiKey': 'LzvSGu2mYFi2L6VtBL',
    'secret': 'KA3wvyIvMCJjGZEB0KVjH9WJSi30iwc9pIiG',
    'enableRateLimit': True,
})

def fetch_derivative_positions():
    """Fetch current derivative positions from Bybit."""
    try:
        positions = exchange.fetch_positions()
        derivative_positions = []
        for position in positions:
            if position['info']['side'] != 'None':  # Only consider positions that are open
                derivative_positions.append({
                    'symbol': position['symbol'],
                    'side': position['side'],
                    'quantity': position['contracts'],
                    'entry_price': position['entryPrice']
                })
        logging.info(f"Fetched derivative positions: {derivative_positions}")
        return derivative_positions
    except Exception as e:
        logging.error(f"Error fetching derivative positions: {e}")
        return []

def fetch_current_prices(assets):
    """Fetch current prices for given assets from the exchange."""
    prices = {}
    for asset in assets:
        try:
            ticker = exchange.fetch_ticker(asset)
            prices[asset] = ticker['last']
            logging.info(f"Fetched price for {asset}: {ticker['last']}")
        except Exception as e:
            logging.error(f"Error fetching price for {asset}: {e}")
    return prices

def track_portfolio_performance(portfolio):
    """Track and log the performance of the portfolio."""
    if portfolio.empty:
        logging.warning("Portfolio is empty. No performance to track.")
        return

    total_value = portfolio['value'].sum()
    portfolio['weighted_performance'] = portfolio['value'] * portfolio['weight']
    total_weighted_performance = portfolio['weighted_performance'].sum()

    logging.info(f"Total Portfolio Value: {total_value:.2f}")
    logging.info(f"Total Weighted Performance: {total_weighted_performance:.2f}")
    logging.info("Individual Asset Performance:")
    for index, row in portfolio.iterrows():
        logging.info(f"Asset: {row['asset']}, Quantity: {row['quantity']:.6f}, Value: {row['value']:.2f}, Weight: {row['weight']:.2f}, Weighted Performance: {row['weighted_performance']:.2f}")

def rebalance_portfolio(portfolio, target_weights):
    """Rebalance the portfolio according to target weights."""
    if portfolio.empty:
        logging.warning("Portfolio is empty. Cannot rebalance.")
        return
    
    assets = portfolio['asset'].tolist()
    current_prices = fetch_current_prices(assets)
    total_value = portfolio['value'].sum()

    for index, row in portfolio.iterrows():
        asset = row['asset']
        if asset in target_weights:
            target_weight = target_weights[asset]
            target_value = total_value * target_weight
            current_price = current_prices.get(asset, 0)
            target_quantity = target_value / current_price if current_price else 0
            logging.info(f"Rebalancing {asset}: current value = {row['value']:.2f}, target value = {target_value:.2f}, current quantity = {row['quantity']:.6f}, target quantity = {target_quantity:.6f}")
            portfolio.at[index, 'weight'] = target_weight
            portfolio.at[index, 'value'] = target_value
            portfolio.at[index, 'quantity'] = target_quantity
        else:
            logging.warning(f"Target weight for {asset} not found. Skipping.")
    
    logging.info("Portfolio rebalanced.")
    logging.info(portfolio)

def main():
    """Main function to manage and rebalance the portfolio."""
    # Fetch real-time derivative positions
    derivative_positions = fetch_derivative_positions()
    
    if not derivative_positions:
        logging.error("No derivative positions found. Ensure your account has open positions and API credentials are correct.")
        return

    # Create a portfolio DataFrame based on derivative positions
    portfolio_data = {
        'asset': [pos['symbol'] for pos in derivative_positions],
        'quantity': [pos['quantity'] for pos in derivative_positions],
        'entry_price': [pos['entry_price'] for pos in derivative_positions],
        'side': [pos['side'] for pos in derivative_positions]
    }
    portfolio = pd.DataFrame(portfolio_data)

    # Fetch current prices and update portfolio values
    current_prices = fetch_current_prices(portfolio['asset'].tolist())
    
    def calculate_position_value(row):
        current_price = current_prices.get(row['asset'], 0)
        if row['side'] == 'long':
            return row['quantity'] * (current_price - row['entry_price'])
        else:  # 'short'
            return row['quantity'] * (row['entry_price'] - current_price)
    
    portfolio['value'] = portfolio.apply(calculate_position_value, axis=1)
    
    # Set initial weights (assuming equal weighting initially, adjust as needed)
    total_value = portfolio['value'].sum()
    if total_value != 0:
        portfolio['weight'] = portfolio['value'] / total_value
    else:
        portfolio['weight'] = 0

    # Track portfolio performance
    track_portfolio_performance(portfolio)
    
    # Define target weights for rebalancing (adjust as needed)
    target_weights = {
        'BTCUSDT:USDT': 0.33,
        'ETH/USDT:USDT': 0.33,
        'XRP/USDT:USDT': 0.34,
    }
    
    # Rebalance the portfolio
    rebalance_portfolio(portfolio, target_weights)
    
    # Track portfolio performance after rebalancing``
    track_portfolio_performance(portfolio)

if __name__ == "__main__":
    main()
