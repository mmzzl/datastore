"""Tests for ST stock filtering in the daily scanner."""
import pytest
from unittest.mock import MagicMock, patch

from app.monitor.daily_scanner import DailySignalScanner
from app.monitor.utils.st_filter import is_st_stock, filter_st_tickers


class TestSTFilter:
    """Test ST stock filtering logic."""

    def test_is_st_stock_detects_st_prefix(self):
        """Test that ST prefix is detected."""
        assert is_st_stock("ST某某") is True
        assert is_st_stock("*ST某某") is True
        assert is_st_stock("ST某某A") is True

    def test_is_st_stock_allows_normal_stocks(self):
        """Test that normal stocks pass through."""
        assert is_st_stock("平安银行") is False
        assert is_st_stock("贵州茅台") is False
        assert is_st_stock("招商银行") is False

    def test_filter_st_tickers_removes_st_stocks(self):
        """Test that ST stocks are filtered from ticker list."""
        tickers = ["000001", "000002", "000003", "000004"]
        name_map = {
            "000001": "平安银行",
            "000002": "ST某某",
            "000003": "贵州茅台",
            "000004": "*ST某某"
        }

        filtered = filter_st_tickers(tickers, name_map)

        assert "000001" in filtered
        assert "000002" not in filtered
        assert "000003" in filtered
        assert "000004" not in filtered
        assert len(filtered) == 2

    def test_daily_scanner_filters_st_stocks(self):
        """Test that DailySignalScanner filters ST stocks during scan."""
        mock_storage = MagicMock()

        # Create data that would trigger a pattern
        mock_klines = []
        for i in range(60):
            if i < 55:
                price = 11.0 - i * 0.02
            elif i < 59:
                price = 10.0 + (i - 55) * 0.03
            else:
                price = 10.5
            mock_klines.append({
                "date": f"2024-01-{(i+1):02d}",
                "close": price,
                "volume": 1000000
            })

        mock_storage.get_kline.return_value = mock_klines
        mock_storage.add_to_watch_list = MagicMock()

        scanner = DailySignalScanner(mock_storage)

        # Mock index stocks with mix of ST and non-ST
        stocks_map = {
            "000001": "平安银行",      # Normal
            "000002": "ST某某",        # ST - should be filtered
            "000003": "贵州茅台",      # Normal
            "000004": "*ST某某"        # *ST - should be filtered
        }

        with patch.object(scanner, '_get_index_stocks', return_value=stocks_map):
            scanner.scan()

        # Verify add_to_watch_list was called only for non-ST stocks
        called_tickers = [call[0][0] for call in mock_storage.add_to_watch_list.call_args_list]

        # ST stocks should never be in the call list
        assert "000002" not in called_tickers
        assert "000004" not in called_tickers

    def test_st_filter_handles_empty_name(self):
        """Test that empty names don't cause errors."""
        assert is_st_stock("") is False
        assert is_st_stock(None) is False

    def test_st_filter_case_insensitive(self):
        """Test that ST detection is case insensitive."""
        assert is_st_stock("st某某") is True
        assert is_st_stock("St某某") is True
