"""
Integration test for the full signal pipeline:
Technical Pattern -> watch_list -> IntradayMonitor trigger -> market_signals record
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import pandas as pd

from app.monitor.daily_scanner import DailySignalScanner
from app.monitor.intraday_monitor import IntradayMonitor


class TestSignalPipeline:
    """Test the complete signal flow from pattern detection to market signal."""

    def test_technical_pattern_to_watch_list(self):
        """Test that technical patterns result in stocks being added to watch_list."""
        mock_storage = MagicMock()

        # Mock get_kline to return data that triggers MA golden cross
        mock_klines = []
        for i in range(60):
            if i < 55:
                # Slow decline - MA5 below MA20
                price = 11.0 - i * 0.02
            elif i < 59:
                # Slow recovery - still below
                price = 10.0 + (i - 55) * 0.03
            else:
                # Sharp spike at last bar to cross above MA20
                price = 10.5
            mock_klines.append({
                "date": f"2024-01-{(i+1):02d}",
                "close": price,
                "open": price - 0.01,
                "high": price + 0.02,
                "low": price - 0.02,
                "volume": 1000000
            })

        mock_storage.get_kline.return_value = mock_klines
        mock_storage.add_to_watch_list = MagicMock()

        scanner = DailySignalScanner(mock_storage)

        # Mock _get_index_stocks and filter_st_tickers
        with patch.object(scanner, '_get_index_stocks', return_value={"000001": "平安银行"}):
            with patch('app.monitor.daily_scanner.filter_st_tickers', return_value=["000001"]):
                scanner.scan()

        # Verify add_to_watch_list was called
        assert mock_storage.add_to_watch_list.called

    def test_watch_list_to_intraday_trigger(self):
        """Test that stocks in watch_list are monitored and signals are generated."""
        mock_storage = MagicMock()

        # Mock watch_list with one stock
        mock_storage.get_watch_list.return_value = ["000001"]

        # Mock fresh kline data that triggers volume surge
        now = datetime.now()
        mock_klines = []
        for i in range(30):
            mock_klines.append({
                "date": now - timedelta(minutes=30 - i),
                "close": 10.0 + i * 0.01,
                "high": 10.0 + i * 0.01 + 0.02,
                "volume": 1000000 if i < 29 else 5000000  # Last bar has 5x volume
            })
        mock_storage.get_kline.return_value = mock_klines
        mock_storage.save_market_signal = MagicMock()

        monitor = IntradayMonitor(mock_storage)

        # Mock freshness check by patching datetime
        with patch.object(monitor, '_check_data_freshness', return_value=True):
            monitor.run_cycle()

        # Verify save_market_signal was called
        assert mock_storage.save_market_signal.called

    def test_full_pipeline_integration(self):
        """Test complete flow: pattern detection -> watch_list -> intraday signal."""
        mock_storage = MagicMock()

        # Step 1: Daily scanner detects pattern
        mock_klines_daily = []
        for i in range(60):
            if i < 55:
                # Slow decline - MA5 below MA20
                price = 11.0 - i * 0.02
            elif i < 59:
                # Slow recovery - still below
                price = 10.0 + (i - 55) * 0.03
            else:
                # Sharp spike at last bar to cross above MA20
                price = 10.5
            mock_klines_daily.append({
                "date": f"2024-01-{(i+1):02d}",
                "close": price,
                "open": price - 0.01,
                "high": price + 0.02,
                "low": price - 0.02,
                "volume": 1000000
            })

        mock_storage.get_kline.return_value = mock_klines_daily
        mock_storage.add_to_watch_list = MagicMock()

        scanner = DailySignalScanner(mock_storage)

        with patch.object(scanner, '_get_index_stocks', return_value={"000001": "平安银行"}):
            with patch('app.monitor.daily_scanner.filter_st_tickers', return_value=["000001"]):
                scanner.scan()

        # Verify pattern was detected and stock added to watch_list
        assert mock_storage.add_to_watch_list.called

        # Step 2: Stock appears in watch_list
        mock_storage.get_watch_list.return_value = ["000001"]

        # Step 3: Intraday monitor picks it up
        now = datetime.now()
        mock_klines_intraday = []
        for i in range(30):
            mock_klines_intraday.append({
                "date": now - timedelta(minutes=30 - i),
                "close": 10.0 + i * 0.01,
                "high": 10.0 + i * 0.01 + 0.02,
                "volume": 1000000 if i < 29 else 5000000
            })
        mock_storage.get_kline.return_value = mock_klines_intraday
        mock_storage.save_market_signal = MagicMock()

        monitor = IntradayMonitor(mock_storage)
        with patch.object(monitor, '_check_data_freshness', return_value=True):
            monitor.run_cycle()

        # Verify market signal was saved
        assert mock_storage.save_market_signal.called

        # Verify signal structure
        saved_signal = mock_storage.save_market_signal.call_args[0][0]
        assert "symbol" in saved_signal
        assert "signal_type" in saved_signal
        assert saved_signal["symbol"] == "000001"


class TestSignalCooldown:
    """Test signal cooldown logic to prevent duplicate notifications."""

    def test_cooldown_prevents_duplicate_signals(self):
        """Test that cooldown prevents duplicate signals for same stock/pattern."""
        mock_storage = MagicMock()
        mock_storage.get_watch_list.return_value = ["000001"]

        now = datetime.now()
        mock_klines = []
        for i in range(30):
            mock_klines.append({
                "date": now - timedelta(minutes=30 - i),
                "close": 10.0 + i * 0.01,
                "high": 10.0 + i * 0.01 + 0.02,
                "volume": 1000000 if i < 29 else 5000000
            })
        mock_storage.get_kline.return_value = mock_klines
        mock_storage.save_market_signal = MagicMock()

        monitor = IntradayMonitor(mock_storage)

        with patch.object(monitor, '_check_data_freshness', return_value=True):
            # First run - should trigger signal
            monitor.run_cycle()
            first_call_count = mock_storage.save_market_signal.call_count

            # Second run immediately - should be blocked by cooldown
            monitor.run_cycle()
            second_call_count = mock_storage.save_market_signal.call_count

            # Should not have increased
            assert second_call_count == first_call_count

    def test_cooldown_expires_after_period(self):
        """Test that cooldown expires after COOLDOWN_PERIOD."""
        mock_storage = MagicMock()
        mock_storage.get_watch_list.return_value = ["000001"]

        now = datetime.now()
        mock_klines = []
        for i in range(30):
            mock_klines.append({
                "date": now - timedelta(minutes=30 - i),
                "close": 10.0 + i * 0.01,
                "high": 10.0 + i * 0.01 + 0.02,
                "volume": 1000000 if i < 29 else 5000000
            })
        mock_storage.get_kline.return_value = mock_klines
        mock_storage.save_market_signal = MagicMock()

        monitor = IntradayMonitor(mock_storage)

        with patch.object(monitor, '_check_data_freshness', return_value=True):
            # First run
            monitor.run_cycle()

            # Manually expire cooldown by setting past time
            for key in monitor.signal_cooldowns:
                monitor.signal_cooldowns[key] = datetime.now() - timedelta(hours=5)

            # Second run after cooldown expired
            monitor.run_cycle()

            # Should have been called twice
            assert mock_storage.save_market_signal.call_count == 2
