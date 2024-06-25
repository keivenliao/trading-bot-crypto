import os
from dotenv import load_dotenv

from dotenv import load_dotenv, find_dotenv

# Load environment variables from the .env file
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path)
    print(f"Loaded .env file from: {dotenv_path}")
else:
    print("No .env file found")


load_dotenv()

API_KEY = os.getenv('API_KEY')
API_SECRET = os.getenv('API_SECRET')
DB_FILE = 'trading_bot.db'
TRAILING_STOP_PERCENT = 0.02
RISK_REWARD_RATIO = 2.0
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = os.getenv('SMTP_PORT')
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASS = os.getenv('EMAIL_PASS')
SENTIMENT_API_KEY = os.getenv('SENTIMENT_API_KEY', 'LzvSGu2mYFi2L6VtBL')
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY', 'default_bybit_api_key')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET', 'default_bybit_api_secret')

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
