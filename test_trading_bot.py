import unittest
from unittest.mock import MagicMock, patch
from tradingbot import TradingBot
import ccxt
import ntplib

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

        # Test successful exchange initialization
        self.trading_bot.initialize_exchange()
        self.assertEqual(self.trading_bot.exchange, mock_exchange)
        mock_bybit.assert_called_once_with({
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'enableRateLimit': True,
        })

        # Test failure case for exchange initialization (e.g., invalid API key/secret)
        mock_bybit.side_effect = ccxt.AuthenticationError('Invalid API Key')
        with self.assertRaises(ccxt.AuthenticationError):
            self.trading_bot.initialize_exchange()

    @patch('tradingbot.ntplib.NTPClient')
    def test_synchronize_time(self, mock_ntp_client):
        # Test successful time synchronization
        mock_response = MagicMock()
        mock_response.tx_time = 1625072400  # Example timestamp
        mock_ntp_client.return_value.request.return_value = mock_response
        time_offset = self.trading_bot.synchronize_time()
        self.assertIsNotNone(time_offset)

        # Test failure case for time synchronization (e.g., NTP server unavailable)
        mock_ntp_client.return_value.request.side_effect = ntplib.NTPException('NTP server unavailable')
        with self.assertRaises(ntplib.NTPException):
            self.trading_bot.synchronize_time()

    def test_place_order_with_risk_management(self):
        # Mock create_order method response
        self.exchange.create_order = MagicMock(return_value={'price': 50000})
        self.trading_bot.exchange = self.exchange

        # Test placing order with risk management
        self.trading_bot.place_order_with_risk_management('BTC/USDT', 'buy', 0.001, 0.01, 0.02)
        
        # Verify expected order calls
        self.exchange.create_order.assert_any_call('BTC/USDT', 'market', 'buy', 0.001)
        self.exchange.create_order.assert_any_call('BTC/USDT', 'stop', 'sell', 0.001, 49500.0)
        self.exchange.create_order.assert_any_call('BTC/USDT', 'limit', 'sell', 0.001, 51000.0)

        # Test handling order creation failures
        self.exchange.create_order.side_effect = ccxt.NetworkError('Network error')
        with self.assertRaises(ccxt.NetworkError):
            self.trading_bot.place_order_with_risk_management('BTC/USDT', 'buy', 0.001, 0.01, 0.02)

if __name__ == '__main__':
    unittest.main()
