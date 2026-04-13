import pytest
import pandas as pd
import numpy as np
from apps.api.app.monitor.daily_scanner import DailySignalScanner
from unittest.mock import MagicMock

def test_calculate_indicators_accuracy():
    # Create a mock storage and scanner
    mock_storage = MagicMock()
    scanner = DailySignalScanner(mock_storage)
    
    # Create a synthetic dataset to verify indicators
    # 30 days of data to ensure windows are full
    data = {
        "date": pd.date_range(start="2024-01-01", periods=30),
        "close": [
            10.0, 10.2, 10.1, 10.5, 11.0, # Day 1-5
            10.8, 10.7, 10.9, 11.2, 11.5, # Day 6-10
            11.3, 11.1, 11.0, 10.8, 10.6, # Day 11-15
            10.5, 10.7, 11.0, 11.5, 12.0, # Day 16-20
            12.2, 12.5, 12.8, 13.0, 13.2, # Day 21-25
            13.1, 13.0, 12.9, 13.1, 13.5  # Day 26-30
        ]
    }
    df = pd.DataFrame(data)
    
    result = scanner.calculate_indicators(df)
    
    # 1. Verify MA5 and MA20
    # Day 5 MA5 should be mean([10, 10.2, 10.1, 10.5, 11.0]) = 10.36
    assert np.isclose(result["MA5"].iloc[4], 10.36)
    # Day 20 MA20 should be mean of first 20 elements
    assert np.isclose(result["MA20"].iloc[19], df["close"].iloc[:20].mean())
    
    # 2. Verify RSI (14)
    # Using Wilder's smoothing, we check if it's computed and within [0, 100]
    assert not result["RSI"].isnull().iloc[-1]
    assert 0 <= result["RSI"].iloc[-1] <= 100
    
    # 3. Verify MACD (12, 26, 9)
    # MACD line = EMA(12) - EMA(26)
    ema12 = df["close"].ewm(span=12, adjust=False).mean()
    ema26 = df["close"].ewm(span=26, adjust=False).mean()
    expected_macd = ema12 - ema26
    assert np.isclose(result["MACD"].iloc[-1], expected_macd.iloc[-1])
    
    # Signal line = EMA(9) of MACD
    expected_signal = expected_macd.ewm(span=9, adjust=False).mean()
    assert np.isclose(result["Signal"].iloc[-1], expected_signal.iloc[-1])

def test_check_patterns_golden_cross():
    mock_storage = MagicMock()
    scanner = DailySignalScanner(mock_storage)

    # Create a scenario for MA Golden Cross: MA5 crosses above MA20
    # prev: MA5=10, MA20=11 -> last: MA5=12, MA20=11
    # Need 20+ rows to pass len(df) < 20 check
    base_data = {
        "MA5": [10.0] * 18 + [10.0, 12.0],
        "MA20": [11.0] * 20,
        "RSI": [50.0] * 20,
        "MACD": [0.0] * 20,
        "Signal": [0.0] * 20
    }
    df = pd.DataFrame(base_data)

    patterns = scanner.check_patterns(df)
    assert "ma_golden_cross" in patterns

def test_check_patterns_rsi_oversold():
    mock_storage = MagicMock()
    scanner = DailySignalScanner(mock_storage)

    # Scenario: RSI < 30
    base_data = {
        "MA5": [10.0] * 20,
        "MA20": [11.0] * 20,
        "RSI": [50.0] * 19 + [25.0],
        "MACD": [0.0] * 20,
        "Signal": [0.0] * 20
    }
    df = pd.DataFrame(base_data)

    patterns = scanner.check_patterns(df)
    assert "rsi_oversold" in patterns

def test_check_patterns_macd_golden_cross():
    mock_storage = MagicMock()
    scanner = DailySignalScanner(mock_storage)

    # Scenario: MACD crosses above Signal
    base_data = {
        "MA5": [10.0] * 20,
        "MA20": [11.0] * 20,
        "RSI": [50.0] * 20,
        "MACD": [-1.0] * 19 + [1.0],
        "Signal": [0.0] * 20
    }
    df = pd.DataFrame(base_data)

    patterns = scanner.check_patterns(df)
    assert "macd_golden_cross" in patterns
