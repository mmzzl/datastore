"""Unit tests for MarketTrendData calculation."""

import pytest
from app.stock_selection.market_trend import MarketTrendAnalyzer
from app.schemas.stock_selection import StockIndicator, MarketTrendData


class TestMarketTrendAnalysis:
    """Tests for market trend analysis."""

    def test_analyze_empty_indicators(self):
        """Test analysis with empty indicators dict."""
        result = MarketTrendAnalyzer.analyze_market_trend({})
        assert isinstance(result, MarketTrendData)
        assert result.total_stocks == 0

    def test_analyze_bullish_market(self):
        """Test analysis in bullish market conditions."""
        # Create indicators for bullish market
        # Most stocks have golden crosses and bullish alignment
        indicators = {}
        for i in range(100):
            ind = StockIndicator(
                ma5=100 + i,
                ma10=99 + i,  # ma5 > ma10 (golden cross)
                ma20=98 + i,  # full bullish alignment
                rsi=50 + (i % 20),  # neutral RSI
                macd_hist=0.1 + i * 0.01  # positive MACD histogram (golden cross)
            )
            indicators[f'stock_{i}'] = ind

        result = MarketTrendAnalyzer.analyze_market_trend(indicators)

        # Should indicate bullish conditions
        assert result.total_stocks == 100
        assert result.macd_golden_cross_ratio > 60  # Most have golden cross
        assert result.full_bullish_alignment_ratio > 50  # Most have bullish alignment
        assert result.trend_direction == '看多'
        assert result.trend_strength == '强'

    def test_analyze_bearish_market(self):
        """Test analysis in bearish market conditions."""
        # Create indicators for bearish market
        indicators = {}
        for i in range(100):
            ind = StockIndicator(
                ma5=98 - i * 0.01,
                ma10=99 - i * 0.01,  # ma5 < ma10 (no golden cross)
                ma20=100 - i * 0.01,  # bearish alignment
                rsi=40 + (i % 20),
                macd_hist=-0.1 - i * 0.01  # negative MACD histogram
            )
            indicators[f'stock_{i}'] = ind

        result = MarketTrendAnalyzer.analyze_market_trend(indicators)

        # Should indicate bearish conditions
        assert result.total_stocks == 100
        assert result.macd_golden_cross_ratio < 40
        assert result.trend_direction in ['看空', '震荡']

    def test_analyze_neutral_market(self):
        """Test analysis in neutral/oscillating market."""
        # Create mixed indicators
        indicators = {}

        # 40% bullish
        for i in range(40):
            indicators[f'bull_{i}'] = StockIndicator(
                ma5=101, ma10=100, ma20=99,
                macd_hist=0.1,
                rsi=50
            )

        # 60% bearish/neutral
        for i in range(60):
            indicators[f'bear_{i}'] = StockIndicator(
                ma5=99, ma10=100, ma20=101,
                macd_hist=-0.05,
                rsi=50
            )

        result = MarketTrendAnalyzer.analyze_market_trend(indicators)

        # Should indicate neutral/oscillating conditions
        assert result.total_stocks == 100
        assert result.macd_golden_cross_ratio == 40.0
        assert result.trend_direction == '震荡'

    def test_rsi_distribution(self):
        """Test RSI distribution calculation."""
        indicators = {}

        # 20 oversold (RSI < 30)
        for i in range(20):
            indicators[f'oversold_{i}'] = StockIndicator(rsi=20 + i * 0.5)

        # 60 neutral (30 <= RSI <= 70)
        for i in range(60):
            indicators[f'neutral_{i}'] = StockIndicator(rsi=50)

        # 20 overbought (RSI > 70)
        for i in range(20):
            indicators[f'overbought_{i}'] = StockIndicator(rsi=80 + i * 0.5)

        result = MarketTrendAnalyzer.analyze_market_trend(indicators)

        assert result.rsi_oversold_count == 20
        assert result.rsi_overbought_count == 20
        assert result.rsi_neutral_count == 60

    def test_selected_stock_stats(self):
        """Test statistics for selected stocks."""
        indicators = {}

        # Create indicators with some selected stocks
        for i in range(50):
            ind = StockIndicator(
                ma5=100, ma10=99, ma20=98,
                macd_hist=0.1 if i < 30 else -0.1
            )
            indicators[f'stock_{i}'] = ind

        # Selected stocks are the first 10
        selected = {f'stock_{i}' for i in range(10)}

        result = MarketTrendAnalyzer.analyze_market_trend(indicators, selected)

        # Check selected stock stats
        assert result.selected_macd_golden_cross == 10  # First 10 have positive macd_hist
        assert result.selected_bullish_alignment == 10  # All 10 have bullish alignment

    def test_trend_strength_levels(self):
        """Test trend strength classification."""
        # Strong bullish
        indicators_strong = {
            f'stock_{i}': StockIndicator(
                ma5=100, ma10=99, ma20=98, macd_hist=0.1, rsi=55
            )
            for i in range(100)
        }
        result = MarketTrendAnalyzer.analyze_market_trend(indicators_strong)
        assert result.trend_strength == '强'

        # Medium
        indicators_medium = {}
        for i in range(100):
            if i < 50:
                indicators_medium[f'stock_{i}'] = StockIndicator(
                    ma5=100, ma10=99, ma20=98, macd_hist=0.1, rsi=55
                )
            else:
                indicators_medium[f'stock_{i}'] = StockIndicator(
                    ma5=99, ma10=100, ma20=101, macd_hist=-0.1, rsi=45
                )
        result = MarketTrendAnalyzer.analyze_market_trend(indicators_medium)
        assert result.trend_strength in ['中', '弱']

    def test_to_dict(self):
        """Test MarketTrendData.to_dict method."""
        result = MarketTrendData(
            total_stocks=100,
            macd_golden_cross_count=60,
            macd_golden_cross_ratio=60.0,
            trend_direction='看多',
            trend_strength='强'
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict['total_stocks'] == 100
        assert result_dict['macd_golden_cross_count'] == 60
        assert result_dict['trend_direction'] == '看多'

    def test_partial_vs_full_bullish_alignment(self):
        """Test distinction between partial and full bullish alignment."""
        indicators = {}

        # 30 with full bullish alignment (ma5 > ma10 > ma20)
        for i in range(30):
            indicators[f'full_{i}'] = StockIndicator(
                ma5=103, ma10=102, ma20=101
            )

        # 20 with partial bullish alignment (ma5 > ma10 only)
        for i in range(20):
            indicators[f'partial_{i}'] = StockIndicator(
                ma5=102, ma10=101, ma20=102  # ma5 > ma10 but ma10 < ma20
            )

        # 50 with no bullish alignment
        for i in range(50):
            indicators[f'none_{i}'] = StockIndicator(
                ma5=99, ma10=100, ma20=101
            )

        result = MarketTrendAnalyzer.analyze_market_trend(indicators)

        assert result.full_bullish_alignment_count == 30
        assert result.full_bullish_alignment_ratio == 30.0
        assert result.partial_bullish_alignment_count == 50  # 30 full + 20 partial = 50 where ma5 > ma10
