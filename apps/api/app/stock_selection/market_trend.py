"""
Market Trend Analyzer

Analyzes market trend based on technical indicators across stock pool.
"""

import logging
from typing import Dict, Any

import pandas as pd
import numpy as np

from ..schemas.stock_selection import StockIndicator, MarketTrendData

logger = logging.getLogger(__name__)


class MarketTrendAnalyzer:
    """
    Analyzes market trend based on technical indicators.

    Calculates golden cross ratios, bullish alignment ratios,
    and RSI distribution to determine market strength.
    """

    @staticmethod
    def calc_ma(series: pd.Series, period: int) -> pd.Series:
        """Calculate Moving Average."""
        return series.rolling(window=period).mean()

    @staticmethod
    def calc_rsi(series: pd.Series, period: int = 14) -> float:
        """
        Calculate Relative Strength Index.

        Args:
            series: Price series (typically close prices)
            period: RSI period (default 14)

        Returns:
            RSI value (0-100)
        """
        if len(series) < period + 1:
            return 50.0  # Neutral if insufficient data

        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss.replace(0, np.inf)
        rsi = 100 - (100 / (1 + rs))

        return round(float(rsi.iloc[-1]), 2) if not pd.isna(rsi.iloc[-1]) else 50.0

    @staticmethod
    def calc_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
        """
        Calculate MACD indicator.

        Args:
            series: Price series
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            Tuple of (macd, signal_line, histogram)
        """
        if len(series) < slow + signal:
            return 0.0, 0.0, 0.0

        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return (
            round(float(macd_line.iloc[-1]), 4) if not pd.isna(macd_line.iloc[-1]) else 0.0,
            round(float(signal_line.iloc[-1]), 4) if not pd.isna(signal_line.iloc[-1]) else 0.0,
            round(float(histogram.iloc[-1]), 4) if not pd.isna(histogram.iloc[-1]) else 0.0,
        )

    @staticmethod
    def calc_bollinger(series: pd.Series, period: int = 20, std_dev: float = 2.0) -> tuple:
        """
        Calculate Bollinger Bands.

        Args:
            series: Price series
            period: MA period
            std_dev: Standard deviation multiplier

        Returns:
            Tuple of (upper, middle, lower)
        """
        if len(series) < period:
            last_val = series.iloc[-1] if len(series) > 0 else 0
            return round(float(last_val), 2), round(float(last_val), 2), round(float(last_val), 2)

        middle = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return (
            round(float(upper.iloc[-1]), 2) if not pd.isna(upper.iloc[-1]) else 0.0,
            round(float(middle.iloc[-1]), 2) if not pd.isna(middle.iloc[-1]) else 0.0,
            round(float(lower.iloc[-1]), 2) if not pd.isna(lower.iloc[-1]) else 0.0,
        )

    @staticmethod
    def calculate_indicators(df: pd.DataFrame) -> StockIndicator:
        """
        Calculate all technical indicators for a stock.

        Args:
            df: DataFrame with OHLCV data

        Returns:
            StockIndicator object
        """
        if df.empty or "close" not in df.columns:
            return StockIndicator()

        close = df["close"]

        # Calculate MA
        ma5 = MarketTrendAnalyzer.calc_ma(close, 5).iloc[-1]
        ma10 = MarketTrendAnalyzer.calc_ma(close, 10).iloc[-1]
        ma20 = MarketTrendAnalyzer.calc_ma(close, 20).iloc[-1]

        # Calculate RSI
        rsi = MarketTrendAnalyzer.calc_rsi(close, 14)

        # Calculate MACD
        macd, macd_signal, macd_hist = MarketTrendAnalyzer.calc_macd(close)

        # Calculate Bollinger Bands
        boll_upper, boll_mid, boll_lower = MarketTrendAnalyzer.calc_bollinger(close)

        # Volume ratio and turnover (if data available)
        volume_ratio = None
        turnover_rate = None
        if "volume" in df.columns and len(df) >= 5:
            avg_volume = df["volume"].rolling(5).mean().iloc[-1]
            if avg_volume and avg_volume > 0:
                volume_ratio = round(float(df["volume"].iloc[-1] / avg_volume), 2)

        return StockIndicator(
            ma5=round(float(ma5), 2) if not pd.isna(ma5) else None,
            ma10=round(float(ma10), 2) if not pd.isna(ma10) else None,
            ma20=round(float(ma20), 2) if not pd.isna(ma20) else None,
            rsi=rsi,
            macd=macd,
            macd_signal=macd_signal,
            macd_hist=macd_hist,
            boll_upper=boll_upper,
            boll_mid=boll_mid,
            boll_lower=boll_lower,
            volume_ratio=volume_ratio,
            turnover_rate=turnover_rate,
        )

    @staticmethod
    def calculate_score(confidence: float, indicators: StockIndicator) -> float:
        """
        Calculate composite score for a stock.

        Args:
            confidence: Strategy confidence (0-1)
            indicators: Technical indicators

        Returns:
            Score (0-100)
        """
        base_score = confidence * 100
        adjustments = 0

        # RSI adjustment
        if indicators.rsi is not None:
            if 30 <= indicators.rsi <= 50:
                adjustments += 5  # Oversold recovery zone, good entry
            elif indicators.rsi > 70:
                adjustments -= 10  # Overbought, risky
            elif indicators.rsi < 30:
                adjustments += 3  # Oversold, potential bounce

        # MACD adjustment
        if indicators.macd_hist is not None and indicators.macd_hist > 0:
            adjustments += 5  # MACD golden cross

        # Moving average alignment
        if indicators.ma5 and indicators.ma10 and indicators.ma20:
            if indicators.ma5 > indicators.ma10 > indicators.ma20:
                adjustments += 5  # Full bullish alignment
            elif indicators.ma5 > indicators.ma10:
                adjustments += 2  # Partial bullish

        # Bollinger Band position
        if indicators.boll_upper and indicators.boll_lower and indicators.boll_mid:
            # Price near lower band = potential bounce
            if indicators.ma5 and indicators.ma5 < indicators.boll_lower * 1.02:
                adjustments += 3

        return min(100, max(0, base_score + adjustments))

    @staticmethod
    def get_strength(confidence: float) -> str:
        """
        Get signal strength label.

        Args:
            confidence: Strategy confidence (0-1)

        Returns:
            Strength label (强/中/弱)
        """
        if confidence >= 0.8:
            return "强"
        elif confidence >= 0.5:
            return "中"
        else:
            return "弱"

    @staticmethod
    def analyze_market_trend(
        all_indicators: Dict[str, StockIndicator],
        selected_codes: set = None
    ) -> MarketTrendData:
        """
        Analyze market trend based on all stock indicators.

        Args:
            all_indicators: Dict of code -> StockIndicator
            selected_codes: Set of selected stock codes (for additional stats)

        Returns:
            MarketTrendData object
        """
        total = len(all_indicators)
        if total == 0:
            return MarketTrendData()

        # Count golden crosses
        macd_golden = sum(
            1 for ind in all_indicators.values()
            if ind.macd_hist is not None and ind.macd_hist > 0
        )
        ma_golden = sum(
            1 for ind in all_indicators.values()
            if ind.ma5 is not None and ind.ma10 is not None and ind.ma5 > ind.ma10
        )

        # Count bullish alignments
        full_bullish = sum(
            1 for ind in all_indicators.values()
            if ind.ma5 and ind.ma10 and ind.ma20
            and ind.ma5 > ind.ma10 > ind.ma20
        )
        partial_bullish = sum(
            1 for ind in all_indicators.values()
            if ind.ma5 and ind.ma10 and ind.ma5 > ind.ma10
        )

        # Count RSI distribution
        rsi_oversold = sum(
            1 for ind in all_indicators.values()
            if ind.rsi is not None and ind.rsi < 30
        )
        rsi_overbought = sum(
            1 for ind in all_indicators.values()
            if ind.rsi is not None and ind.rsi > 70
        )
        rsi_neutral = total - rsi_oversold - rsi_overbought

        # Selected stock stats
        selected_macd_golden = 0
        selected_bullish = 0
        if selected_codes:
            for code in selected_codes:
                if code in all_indicators:
                    ind = all_indicators[code]
                    if ind.macd_hist and ind.macd_hist > 0:
                        selected_macd_golden += 1
                    if ind.ma5 and ind.ma10 and ind.ma20 and ind.ma5 > ind.ma10 > ind.ma20:
                        selected_bullish += 1

        # Calculate ratios
        macd_ratio = round(macd_golden / total * 100, 1) if total > 0 else 0
        ma_ratio = round(ma_golden / total * 100, 1) if total > 0 else 0
        bullish_ratio = round(full_bullish / total * 100, 1) if total > 0 else 0
        partial_ratio = round(partial_bullish / total * 100, 1) if total > 0 else 0

        # Determine trend direction and strength
        if macd_ratio > 60 and bullish_ratio > 50:
            direction, strength = "看多", "强"
        elif macd_ratio >= 40 and bullish_ratio >= 30:
            if macd_ratio > 50 and bullish_ratio > 40:
                direction, strength = "震荡", "中"
            else:
                direction, strength = "震荡", "弱"
        elif macd_ratio < 30 or bullish_ratio < 20:
            if macd_ratio < 20 or bullish_ratio < 10:
                direction, strength = "看空", "强"
            else:
                direction, strength = "看空", "弱"
        else:
            direction, strength = "震荡", "中"

        return MarketTrendData(
            total_stocks=total,
            analyzed_stocks=total,
            macd_golden_cross_count=macd_golden,
            macd_golden_cross_ratio=macd_ratio,
            ma_golden_cross_count=ma_golden,
            ma_golden_cross_ratio=ma_ratio,
            full_bullish_alignment_count=full_bullish,
            full_bullish_alignment_ratio=bullish_ratio,
            partial_bullish_alignment_count=partial_bullish,
            partial_bullish_alignment_ratio=partial_ratio,
            selected_macd_golden_cross=selected_macd_golden,
            selected_bullish_alignment=selected_bullish,
            rsi_oversold_count=rsi_oversold,
            rsi_overbought_count=rsi_overbought,
            rsi_neutral_count=rsi_neutral,
            trend_direction=direction,
            trend_strength=strength,
        )
