import unittest
from unittest.mock import MagicMock, patch
from tradingbot import TradingBot

class TestTradingFunctions(unittest.TestCase):

    def setUp(self):
        self.api_key = 'test_api_key'
        self.api_secret = 'test_api_secret'
        self.trading_bot = TradingBot(self.api_key, self.api_secret)
        self.exchange = MagicMock()

    @patch('tradingbot.ccxt.bybit')
    def test_initialize_exchange(self, mock_bybit):
        mock_exchange = MagicMock()
        mock_bybit.return_value = mock_exchange
        self.trading_bot.initialize_exchange()
        self.assertEqual(self.trading_bot.exchange, mock_exchange)
        mock_bybit.assert_called_once_with({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
        })

    @patch('tradingbot.ntplib.NTPClient')
    def test_synchronize_time(self, mock_ntp_client):
        mock_ntp_client.return_value.request.return_value.offset = 0.123
        time_offset = self.trading_bot.synchronize_time()
        self.assertEqual(time_offset, 0.123)

    def test_place_order_with_risk_management(self):
        self.exchange.create_order = MagicMock(return_value={'price': 50000})
        self.trading_bot.exchange = self.exchange
        
        self.trading_bot.place_order_with_risk_management('BTC/USDT', 'buy', 0.001, 0.01, 0.02)
        self.exchange.create_order.assert_any_call('BTC/USDT', 'market', 'buy', 0.001)
        self.exchange.create_order.assert_any_call('BTC/USDT', 'stop', 'sell', 0.001, 49500.0)
        self.exchange.create_order.assert_any_call('BTC/USDT', 'limit', 'sell', 0.001, 51000.0)

if __name__ == '__main__':
    unittest.main()
