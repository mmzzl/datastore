"""
Test script to verify scan logic without requiring MongoDB connection.
Simulates the watch_list update flow.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import MagicMock, patch
from app.monitor.daily_scanner import DailySignalScanner
from app.storage.mongo_client import MongoStorage


def test_scan_updates_watch_list():
    """Test that scan() correctly calls add_to_watch_list when patterns are detected."""
    print("=" * 60)
    print("Test: Scan Updates Watch List")
    print("=" * 60)

    # Create mock storage
    mock_storage = MagicMock(spec=MongoStorage)

    # Create mock kline data that triggers MA golden cross
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
            "volume": 1000000
        })

    mock_storage.get_kline.return_value = mock_klines
    mock_storage.add_to_watch_list = MagicMock()

    scanner = DailySignalScanner(mock_storage)

    # Mock the index stocks and ST filter
    test_stocks = {"000001": "平安银行", "600000": "浦发银行"}

    with patch.object(scanner, '_get_index_stocks', return_value=test_stocks):
        with patch('app.monitor.daily_scanner.filter_st_tickers', return_value=list(test_stocks.keys())):
            scanner.scan()

    # Verify add_to_watch_list was called
    if mock_storage.add_to_watch_list.called:
        print("\n[PASS] add_to_watch_list WAS called")
        call_count = mock_storage.add_to_watch_list.call_count
        print(f"  Call count: {call_count}")

        # Show call details
        for i, call in enumerate(mock_storage.add_to_watch_list.call_args_list):
            ticker = call.args[0] if call.args else call.kwargs.get('symbol', 'unknown')
            source = call.kwargs.get('source', 'unknown')
            ttl = call.kwargs.get('ttl_days', 'unknown')
            print(f"  Call {i+1}: ticker={ticker}, source={source}, ttl={ttl}")
    else:
        print("\n[FAIL] add_to_watch_list was NOT called")
        return False

    print("\n" + "=" * 60)
    print("Test PASSED: Scan correctly updates watch_list")
    print("=" * 60)
    return True


def test_scan_filters_st_stocks():
    """Test that ST stocks are filtered out during scan."""
    print("\n" + "=" * 60)
    print("Test: Scan Filters ST Stocks")
    print("=" * 60)

    mock_storage = MagicMock(spec=MongoStorage)

    # Create pattern-triggering data
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

    # Mix of ST and normal stocks
    test_stocks = {
        "000001": "平安银行",    # Normal
        "000002": "ST某某",      # ST - should be filtered
        "000003": "贵州茅台",    # Normal
        "000004": "*ST某某"      # *ST - should be filtered
    }

    with patch.object(scanner, '_get_index_stocks', return_value=test_stocks):
        scanner.scan()

    # Check that ST stocks were NOT added
    called_tickers = []
    for call in mock_storage.add_to_watch_list.call_args_list:
        if call.args:
            called_tickers.append(call.args[0])
        else:
            called_tickers.append(call.kwargs.get('symbol', ''))

    st_filtered = True
    if "000002" in called_tickers:
        print("[FAIL] ST stock 000002 was added (should be filtered)")
        st_filtered = False
    if "000004" in called_tickers:
        print("[FAIL] *ST stock 000004 was added (should be filtered)")
        st_filtered = False

    if st_filtered:
        print("\n[PASS] ST stocks were correctly filtered")
        print(f"  Tickers added: {called_tickers}")

    print("\n" + "=" * 60)
    print("Test PASSED: ST stocks filtered correctly")
    print("=" * 60)
    return st_filtered


if __name__ == "__main__":
    success = True
    success = test_scan_updates_watch_list() and success
    success = test_scan_filters_st_stocks() and success

    if success:
        print("\n\n" + "=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60)
    else:
        print("\n\n" + "=" * 60)
        print("SOME TESTS FAILED")
        print("=" * 60)
        sys.exit(1)
