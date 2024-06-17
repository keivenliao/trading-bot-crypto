import os


def load_api_credentials():
    """
    Load API credentials from environment variables.
    """
    api_key = os.getenv('BYBIT_API_KEY')
    api_Key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    api_secret = os.getenv('BYBIT_API_SECRET')
    return api_key, api_secret
    return api_Key, api_secret
