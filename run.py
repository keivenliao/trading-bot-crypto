import os
from dotenv import load_dotenv
from exchanges import initialize_exchange

def main():
    # Load environment variables from .env file
    dotenv_path = 'C:/Users/amrita/Desktop/improvised-code-of-the-pdf-GPT-main/API.env'
    load_dotenv(dotenv_path=dotenv_path)

    # Retrieve API credentials from environment variables
    api_key = os.getenv("BYBIT_API_KEY")
    api_secret = os.getenv("BYBIT_API_SECRET")

    # Check if API credentials are available
    if not api_key or not api_secret:
        raise ValueError("API key and secret must be set in the environment variables.")

    # Initialize the exchange
    exchange = initialize_exchange(api_key, api_secret)
    print("Exchange initialized:", exchange)

if __name__ == "__main__":
    main()
