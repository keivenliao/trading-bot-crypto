# APIs.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_api_credentials(key_number):
    """
    Load API credentials from environment variables.
    
    Parameters:
    - key_number (int): The index number of the API key to load (1 or 2).
    
    Returns:
    - (str, str): Tuple containing the API key and API secret.
    """
    api_key = os.getenv(f'BYBIT_API_KEY_{key_number}')
    api_secret = os.getenv(f'BYBIT_API_SECRET_{key_number}')
    return api_key, api_secret
