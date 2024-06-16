import os
from dotenv import load_dotenv

def load_api_credentials():
    """
    Load API credentials from environment variables and print them for verification.
    """
    load_dotenv()
    api_key = os.getenv('BYBIT_API_KEY')
    api_secret = os.getenv('BYBIT_API_SECRET')
    
    if not api_key or not api_secret:
        raise ValueError("API key and secret must be set as environment variables")
    
    # Print API credentials for verification
    print(f"API Key: {api_key}")
    print(f"API Secret: {api_secret}")
    
    return api_key, api_secret

# Example usage
if __name__ == "__main__":
    try:
        api_key, api_secret = load_api_credentials()
    except ValueError as e:
        print(e)
