import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.data_source import DataSourceManager

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """情绪分析器 - 基于价格动量和量能趋势作为代理指标"""

    def __init__(self, data_manager: DataSourceManager = None):
        self.data_manager = data_manager or DataSourceManager()

    def analyze(self, code: str, days: int = 3) -> Dict[str, Any]:
        """
        分析股票情绪

        基于近期价格走势和成交量变化推断市场情绪：
        - 近期收益率（动量）
        - 量能变化趋势
        - 收益率发散（近期 vs 长期）
        """
        try:
            logger.info(f"Analyzing sentiment for {code}")

            end_date = datetime.now().strftime("%Y-%m-%d")
            lookback = max(days * 3, 15)
            start_date = (datetime.now() - timedelta(days=lookback)).strftime("%Y-%m-%d")

            klines = self.data_manager.get_kline(
                code, start_date, end_date, frequency="d", adjust_flag="3"
            )

            if not klines or len(klines) < 5:
                logger.warning(f"Insufficient data for sentiment of {code}, using neutral")
                return self._neutral_result()

            closes = [float(k.close) for k in klines]
            volumes = [float(getattr(k, "volume", 0) or 0) for k in klines]

            # 近期 N 日收益率
            recent_return = (closes[-1] - closes[-days]) / closes[-days] if closes[-days] != 0 else 0.0

            # 更长期收益率
            lookback_days = min(len(closes) - 1, days * 3)
            if lookback_days > days and closes[-lookback_days] != 0:
                longer_return = (closes[-1] - closes[-lookback_days]) / closes[-lookback_days]
            else:
                longer_return = recent_return

            # 量能趋势：近期均量 vs 更早均量
            recent_vol = sum(volumes[-days:]) / days if days > 0 else 0
            earlier_end = -days if days > 0 else len(volumes)
            earlier_start = -min(len(volumes), days * 3)
            earlier_slice = volumes[earlier_start:earlier_end]
            earlier_vol = sum(earlier_slice) / len(earlier_slice) if earlier_slice else recent_vol
            vol_ratio = recent_vol / earlier_vol if earlier_vol > 0 else 1.0

            # 动量得分：正涨幅 → 看多
            momentum_score = max(0.0, min(1.0, 0.5 + recent_return * 10))

            # 量能信号：放量 → 1.0，缩量 → 0.0
            if vol_ratio > 1.2:
                volume_signal = 1.0
            elif vol_ratio > 0.8:
                volume_signal = 0.5
            else:
                volume_signal = 0.0

            # 发散得分：近期跑赢长期 → 看多
            divergence = recent_return - longer_return
            divergence_score = max(0.0, min(1.0, 0.5 + divergence * 5))

            score = momentum_score * 0.4 + volume_signal * 0.3 + divergence_score * 0.3
            score = max(0.0, min(1.0, score))

            if score > 0.6:
                trend = "bullish"
            elif score < 0.4:
                trend = "bearish"
            else:
                trend = "neutral"

            return {
                "score": score,
                "news_count": 0,
                "trend": trend,
                "positive_ratio": max(0.0, min(1.0, score)),
                "negative_ratio": max(0.0, min(1.0, 1.0 - score)),
                "neutral_ratio": max(0.0, 1.0 - abs(score - 0.5) * 2),
            }

        except Exception as e:
            logger.error(f"Error analyzing sentiment for {code}: {e}")
            return self._neutral_result()

    def _neutral_result(self) -> Dict[str, Any]:
        """返回中性情绪数据"""
        return {
            "score": 0.5,
            "news_count": 0,
            "trend": "neutral",
            "positive_ratio": 0.5,
            "negative_ratio": 0.3,
            "neutral_ratio": 0.2,
        }

    def close(self):
        """关闭资源"""
        pass
