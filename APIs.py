import ccxt
from dotenv import load_dotenv
import os

def load_api_credentials():
    load_dotenv()
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    return api_key, api_secret

def create_exchange_instance():
    api_key, api_secret = load_api_credentials()
    exchange = ccxt.bybit({
        'apiKey': api_key,
        'secret': api_secret,
        'options': {
            'defaultType': 'future',  # Setting type to futures
        },
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

