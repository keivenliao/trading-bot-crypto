import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
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
        mock_response.offset = 0.5  # Example offset
        mock_ntp_client.return_value.request.return_value = mock_response
        time_offset = self.trading_bot.synchronize_time()
        self.assertEqual(time_offset, 0.5)

        # Test failure case for time synchronization (e.g., NTP server unavailable)
        mock_ntp_client.return_value.request.side_effect = ntplib.NTPException('NTP server unavailable')
        time_offset = self.trading_bot.synchronize_time()
        self.assertEqual(time_offset, 0)  # Should return 0 offset if synchronization fails

    @patch('tradingbot.ccxt.bybit')
    def test_fetch_data(self, mock_bybit):
        mock_exchange = MagicMock()
        mock_bybit.return_value = mock_exchange

        mock_ohlcv = [
            [1625097600000, 34000, 35000, 33000, 34500, 100],
            [1625184000000, 34500, 35500, 34000, 35000, 150],
        ]
        mock_exchange.fetch_ohlcv.return_value = mock_ohlcv

        self.trading_bot.exchange = mock_exchange

        df = self.trading_bot.fetch_data(symbol='BTC/USDT', timeframe='1h', limit=2)

        self.assertEqual(len(df), 2)
        self.assertEqual(list(df.columns), ['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        self.assertEqual(df.iloc[0]['open'], 34000)
        self.assertEqual(df.iloc[1]['close'], 35000)

    def test_calculate_indicators(self):
        df = pd.DataFrame({
            'timestamp': [1625097600000, 1625184000000],
            'open': [34000, 34500],
            'high': [35000, 35500],
            'low': [33000, 34000],
            'close': [34500, 35000],
            'volume': [100, 150]
        })
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        df = self.trading_bot.calculate_indicators(df)
        self.assertIn('SMA_50', df.columns)
        self.assertIn('SMA_200', df.columns)
        self.assertIn('MACD', df.columns)
        self.assertIn('RSI', df.columns)

    def test_place_order_with_risk_management(self):
        # Mock create_order method response
        self.exchange.create_order = MagicMock(return_value={'price': 50000})
        self.trading_bot.exchange = self.exchange

        # Test placing order with risk management
        self.trading_bot.place_order('buy', 50000, 'BTC/USDT', 0.001)
        
        # Verify expected order calls
        self.exchange.create_order.assert_called_with('BTC/USDT', 'market', 'buy', 0.001)

        # Test handling order creation failures
        self.exchange.create_order.side_effect = ccxt.NetworkError('Network error')
        with self.assertRaises(ccxt.NetworkError):
            self.trading_bot.place_order('buy', 50000, 'BTC/USDT', 0.001)

if __name__ == '__main__':
    unittest.main()
