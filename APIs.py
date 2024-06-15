import os
from dotenv import load_dotenv

def load_api_credentials():
    """
    Load API credentials from environment variables.
    """
    load_dotenv()
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    
    if not api_key or not api_secret:
        raise ValueError("API key and secret must be set as environment variables")
    
    return api_key, api_secret
