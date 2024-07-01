# load_api_credentials.py
import ccxt
from dotenv import load_dotenv
import os

def load_api_credentials():
    # Specify the explicit path to the .env file
    dotenv_path = r'C:\Users\amrita\Desktop\improvised-code-of-the-pdf-GPT-main\API.env'
    
    # Check if the .env file exists at the specified path
    if os.path.exists(dotenv_path):
        print(f".env file found at: {dotenv_path}")
        if load_dotenv(dotenv_path):
            print(".env file loaded successfully")
        else:
            print("Failed to load .env file")
    else:
        print("No .env file found at the specified path")

    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    
    if api_key and api_secret:
        print("API credentials loaded successfully")
    else:
        print("Failed to load API credentials")
        
    return api_key, api_secret

# APIs.py

def create_exchange_instance(api_key, api_secret):
    exchange = ccxt.bybit({
        'apiKey': api_key,
        'secret': api_secret,
    })
    return exchange

def set_leverage(exchange, symbol, leverage):
    markets = exchange.load_markets()
    if symbol in markets:
        market = markets[symbol]
        exchange.fapiPrivate_post_leverage({
            'symbol': market['id'],
            'leverage': leverage,
        })

# Example usage
if __name__ == "__main__":
    api_key, api_secret = load_api_credentials()
    if api_key and api_secret:
        exchange = create_exchange_instance(api_key, api_secret)
        print("Exchange instance created successfully")
    else:
        print("Failed to create exchange instance due to missing API credentials")
