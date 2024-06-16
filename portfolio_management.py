import logging
import pandas as pd
import ccxt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the Bybit exchange
exchange = ccxt.bybit()

def fetch_current_prices(assets):
    """
    Fetch current prices for the given assets from Bybit.

    Parameters:
    - assets (list): List of asset symbols (e.g., ['BTC/USDT', 'ETH/USDT']).
    
    Returns:
    - dict: Dictionary with asset symbols as keys and current prices as values.
    """
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
    """
    Track and log the performance of the portfolio.
    
    Parameters:
    - portfolio (pd.DataFrame): DataFrame containing portfolio data with columns ['asset', 'quantity', 'value', 'weight'].
    """
    if portfolio.empty:
        logging.warning("Portfolio is empty. No performance to track.")
        return

    # Calculate total value of the portfolio
    total_value = portfolio['value'].sum()
    
    # Calculate the weighted performance
    portfolio['weighted_performance'] = portfolio['value'] * portfolio['weight']
    total_weighted_performance = portfolio['weighted_performance'].sum()
    
    # Log the performance metrics
    logging.info(f"Total Portfolio Value: {total_value:.2f}")
    logging.info(f"Total Weighted Performance: {total_weighted_performance:.2f}")
    logging.info("Individual Asset Performance:")
    for index, row in portfolio.iterrows():
        logging.info(f"Asset: {row['asset']}, Quantity: {row['quantity']:.6f}, Value: {row['value']:.2f}, Weight: {row['weight']:.2f}, Weighted Performance: {row['weighted_performance']:.2f}")

def rebalance_portfolio(portfolio, target_weights):
    """
    Rebalance the portfolio to the target weights.
    
    Parameters:
    - portfolio (pd.DataFrame): DataFrame containing portfolio data with columns ['asset', 'quantity', 'value', 'weight'].
    - target_weights (dict): Dictionary with asset symbols as keys and target weights as values.
    """
    if portfolio.empty:
        logging.warning("Portfolio is empty. Cannot rebalance.")
        return
    
    # Fetch current prices
    assets = portfolio['asset'].tolist()
    current_prices = fetch_current_prices(assets)
    
    # Calculate total value of the portfolio
    total_value = portfolio['value'].sum()
    
    # Rebalance each asset to the target weight
    for index, row in portfolio.iterrows():
        asset = row['asset']
        if asset in target_weights:
            target_weight = target_weights[asset]
            target_value = total_value * target_weight
            current_price = current_prices[asset]
            target_quantity = target_value / current_price
            logging.info(f"Rebalancing {asset}: current value = {row['value']:.2f}, target value = {target_value:.2f}, current quantity = {row['quantity']:.6f}, target quantity = {target_quantity:.6f}")
            portfolio.at[index, 'weight'] = target_weight
            portfolio.at[index, 'value'] = target_value
            portfolio.at[index, 'quantity'] = target_quantity
        else:
            logging.warning(f"Target weight for {asset} not found. Skipping.")
    
    logging.info("Portfolio rebalanced.")
    logging.info(portfolio)

# Example usage
if __name__ == "__main__":
    # Sample portfolio for demonstration purposes
    portfolio_data = {
        'asset': ['BTC/USDT', 'ETH/USDT', 'XRP/USDT'],
        'quantity': [0.5, 10, 1000],
        'value': [15000, 20000, 25000],  # These values should be updated to reflect current prices * quantity
        'weight': [0.3, 0.4, 0.3]
    }
    portfolio = pd.DataFrame(portfolio_data)
    
    # Update portfolio values with current prices
    current_prices = fetch_current_prices(portfolio['asset'].tolist())
    portfolio['value'] = portfolio.apply(lambda row: row['quantity'] * current_prices[row['asset']], axis=1)
    
    # Track portfolio performance
    track_portfolio_performance(portfolio)
    
    # Define target weights for rebalancing
    target_weights = {
        'BTC/USDT': 0.33,
        'ETH/USDT': 0.33,
        'XRP/USDT': 0.34
    }
    
    # Rebalance the portfolio
    rebalance_portfolio(portfolio, target_weights)
    
    # Track portfolio performance after rebalancing
    track_portfolio_performance(portfolio)
