from config import API_KEY, API_SECRET
from tradingbot import TradingBot

def main():
    bot = TradingBot(API_KEY, API_SECRET)
    bot.run()
    data = bot.fetch_market_data('BTCUSDT')
    print(data)

if __name__ == "__main__":
    main()
