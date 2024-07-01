import os
from dotenv import load_dotenv

# Specify the explicit path to the .env file
dotenv_path = r'C:\Users\amrita\Desktop\improvised-code-of-the-pdf-GPT-main\API.env'

# Load environment variables from the .env file
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"Loaded .env file from: {dotenv_path}")
else:
    print("No .env file found")

# API and database configuration
API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
DB_FILE = 'trading_bot.db'

# Trading parameters
TRAILING_STOP_PERCENT = 0.02
RISK_REWARD_RATIO = 2.0

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = os.getenv('SMTP_PORT')
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')

# Sentiment analysis API key
SENTIMENT_API_KEY = os.getenv('SENTIMENT_API_KEY', 'LzvSGu2mYFi2L6VtBL')

# Bybit API key and secret (with default values for safety)
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', 'default_bybit_api_key')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', 'default_bybit_api_secret')

# Print loaded environment variables for verification
print("API_KEY:", API_KEY)
print("API_SECRET:", API_SECRET)
print("DB_FILE:", DB_FILE)
print("TRAILING_STOP_PERCENT:", TRAILING_STOP_PERCENT)
print("RISK_REWARD_RATIO:", RISK_REWARD_RATIO)
print("SMTP_SERVER:", SMTP_SERVER)
print("SMTP_PORT:", SMTP_PORT)
print("EMAIL_USER:", EMAIL_USER)
print("EMAIL_PASS:", EMAIL_PASS)
print("SENTIMENT_API_KEY:", SENTIMENT_API_KEY)
print("BYBIT_API_KEY:", BYBIT_API_KEY)
print("BYBIT_API_SECRET:", BYBIT_API_SECRET)
