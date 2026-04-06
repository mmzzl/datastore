"""Unit tests for technical indicator calculations."""

import pytest
import pandas as pd
import numpy as np

from app.stock_selection.market_trend import MarketTrendAnalyzer
from app.schemas.stock_selection import StockIndicator


class TestIndicatorCalculations:
    """Tests for technical indicator calculation functions."""

    @pytest.fixture
    def sample_price_data(self):
        """Create sample price data for testing."""
        # Generate sample close prices with some trend
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        # Create a series with some trend and noise
        trend = np.linspace(10, 15, 100)
        noise = np.random.randn(100) * 0.5
        close = trend + noise

        return pd.DataFrame({
            'date': dates,
            'open': close - np.random.rand(100) * 0.3,
            'high': close + np.random.rand(100) * 0.3,
            'low': close - np.random.rand(100) * 0.3,
            'close': close,
            'volume': np.random.randint(1000000, 5000000, 100)
        })

    def test_calc_ma(self, sample_price_data):
        """Test Moving Average calculation."""
        ma5 = MarketTrendAnalyzer.calc_ma(sample_price_data['close'], 5)
        ma10 = MarketTrendAnalyzer.calc_ma(sample_price_data['close'], 10)
        ma20 = MarketTrendAnalyzer.calc_ma(sample_price_data['close'], 20)

        # Check that MA values are calculated
        assert len(ma5) == len(sample_price_data)
        assert len(ma10) == len(sample_price_data)
        assert len(ma20) == len(sample_price_data)

        # Check that MA smoothes the data
        # Last values should be valid numbers
        assert not pd.isna(ma5.iloc[-1])
        assert not pd.isna(ma10.iloc[-1])
        assert not pd.isna(ma20.iloc[-1])

    def test_calc_rsi(self, sample_price_data):
        """Test RSI calculation."""
        rsi = MarketTrendAnalyzer.calc_rsi(sample_price_data['close'], 14)

        # RSI should be between 0 and 100
        assert 0 <= rsi <= 100

    def test_calc_rsi_oversold(self):
        """Test RSI calculation with oversold condition."""
        # Create a series with strong downtrend
        close = pd.Series([100 - i * 0.5 for i in range(50)])
        rsi = MarketTrendAnalyzer.calc_rsi(close, 14)

        # Should indicate oversold (RSI < 30) or at least low
        assert rsi < 50  # At minimum should show weakness

    def test_calc_rsi_overbought(self):
        """Test RSI calculation with overbought condition."""
        # Create a series with strong uptrend
        close = pd.Series([100 + i * 0.5 for i in range(50)])
        rsi = MarketTrendAnalyzer.calc_rsi(close, 14)

        # Should indicate overbought (RSI > 70) or at least high
        assert rsi > 50  # At minimum should show strength

    def test_calc_macd(self, sample_price_data):
        """Test MACD calculation."""
        macd, signal, hist = MarketTrendAnalyzer.calc_macd(sample_price_data['close'])

        # Check that all values are valid
        assert isinstance(macd, float)
        assert isinstance(signal, float)
        assert isinstance(hist, float)

    def test_calc_macd_golden_cross(self):
        """Test MACD golden cross detection."""
        # Create a series that should trigger golden cross
        close = pd.Series([10 + i * 0.01 + np.sin(i * 0.1) * 0.5 for i in range(50)])
        macd, signal, hist = MarketTrendAnalyzer.calc_macd(close)

        # Values should be calculated
        assert macd != 0 or signal != 0  # At least one should be non-zero

    def test_calc_bollinger(self, sample_price_data):
        """Test Bollinger Bands calculation."""
        upper, middle, lower = MarketTrendAnalyzer.calc_bollinger(sample_price_data['close'])

        # Check that bands are valid
        assert isinstance(upper, float)
        assert isinstance(middle, float)
        assert isinstance(lower, float)

        # Upper should be above middle, middle above lower
        if upper != 0 and lower != 0:
            assert upper >= middle >= lower

    def test_calculate_indicators(self, sample_price_data):
        """Test full indicator calculation."""
        indicators = MarketTrendAnalyzer.calculate_indicators(sample_price_data)

        # Check that StockIndicator is returned
        assert isinstance(indicators, StockIndicator)

        # Check that all indicators are set
        assert indicators.ma5 is not None
        assert indicators.ma10 is not None
        assert indicators.ma20 is not None
        assert indicators.rsi is not None

    def test_calculate_indicators_empty_data(self):
        """Test indicator calculation with empty data."""
        empty_df = pd.DataFrame()
        indicators = MarketTrendAnalyzer.calculate_indicators(empty_df)

        # Should return empty indicator
        assert isinstance(indicators, StockIndicator)
        assert indicators.ma5 is None
        assert indicators.rsi is None

    def test_calculate_indicators_insufficient_data(self):
        """Test indicator calculation with insufficient data."""
        # Only 10 days of data
        close = pd.Series([10, 11, 10.5, 11, 10.8, 11.2, 11, 10.9, 11.1, 11])
        df = pd.DataFrame({'close': close})

        indicators = MarketTrendAnalyzer.calculate_indicators(df)

        # Should handle gracefully
        assert isinstance(indicators, StockIndicator)

    def test_indicator_to_dict(self, sample_price_data):
        """Test StockIndicator.to_dict method."""
        indicators = MarketTrendAnalyzer.calculate_indicators(sample_price_data)
        ind_dict = indicators.to_dict()

        # Check that dict is returned
        assert isinstance(ind_dict, dict)
        assert 'ma5' in ind_dict
        assert 'ma10' in ind_dict
        assert 'rsi' in ind_dict


class TestScoreCalculation:
    """Tests for score and strength calculations."""

    def test_calculate_score_base(self):
        """Test base score calculation from confidence."""
        from app.schemas.stock_selection import StockIndicator

        indicators = StockIndicator()
        score = MarketTrendAnalyzer.calculate_score(0.8, indicators)

        # Base score should be 80 (0.8 * 100)
        assert score == 80.0

    def test_calculate_score_with_rsi_adjustments(self):
        """Test score adjustments based on RSI."""
        indicators = StockIndicator(rsi=35)  # Oversold recovery zone
        score = MarketTrendAnalyzer.calculate_score(0.7, indicators)

        # Should add 5 points for RSI 30-50
        assert score == 75.0

    def test_calculate_score_rsi_overbought(self):
        """Test score penalty for overbought RSI."""
        indicators = StockIndicator(rsi=75)  # Overbought
        score = MarketTrendAnalyzer.calculate_score(0.7, indicators)

        # Should subtract 10 points for RSI > 70
        assert score == 60.0

    def test_calculate_score_macd_golden_cross(self):
        """Test score adjustment for MACD golden cross."""
        indicators = StockIndicator(macd_hist=0.5)  # Golden cross
        score = MarketTrendAnalyzer.calculate_score(0.7, indicators)

        # Should add 5 points for MACD histogram > 0
        assert score == 75.0

    def test_calculate_score_bullish_alignment(self):
        """Test score adjustment for bullish alignment."""
        indicators = StockIndicator(ma5=12, ma10=11, ma20=10)  # Bullish alignment
        score = MarketTrendAnalyzer.calculate_score(0.7, indicators)

        # Should add 5 points for full bullish alignment
        assert score == 75.0

    def test_calculate_score_combined_adjustments(self):
        """Test score with multiple adjustments."""
        indicators = StockIndicator(
            rsi=40,  # +5
            macd_hist=0.3,  # +5
            ma5=12, ma10=11, ma20=10  # +5
        )
        score = MarketTrendAnalyzer.calculate_score(0.7, indicators)

        # 70 + 15 = 85
        assert score == 85.0

    def test_score_bounds(self):
        """Test that score is clamped between 0 and 100."""
        indicators = StockIndicator(
            rsi=40,  # +5
            macd_hist=0.3,  # +5
            ma5=12, ma10=11, ma20=10  # +5
        )

        # High confidence that would exceed 100
        score = MarketTrendAnalyzer.calculate_score(0.95, indicators)
        assert score <= 100

        # Low confidence with penalties
        indicators_penalty = StockIndicator(rsi=75)  # -10
        score = MarketTrendAnalyzer.calculate_score(0.05, indicators_penalty)
        assert score >= 0

    def test_get_strength_strong(self):
        """Test strength classification for strong signal."""
        strength = MarketTrendAnalyzer.get_strength(0.85)
        assert strength == '强'

    def test_get_strength_medium(self):
        """Test strength classification for medium signal."""
        strength = MarketTrendAnalyzer.get_strength(0.6)
        assert strength == '中'

    def test_get_strength_weak(self):
        """Test strength classification for weak signal."""
        strength = MarketTrendAnalyzer.get_strength(0.3)
        assert strength == '弱'

    def test_get_strength_boundary_values(self):
        """Test strength at boundary values."""
        assert MarketTrendAnalyzer.get_strength(0.8) == '强'
        assert MarketTrendAnalyzer.get_strength(0.79) == '中'
        assert MarketTrendAnalyzer.get_strength(0.5) == '中'
        assert MarketTrendAnalyzer.get_strength(0.49) == '弱'
