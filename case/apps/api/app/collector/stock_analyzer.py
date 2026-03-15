"""股票分析模块 - 多维度共振筛选系统"""

import os
import pandas as pd
import logging
import json
import baostock as bs
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from .industry_normalizer import IndustryNormalizer

logger = logging.getLogger(__name__)


@dataclass
class StockScore:
    """股票评分结果"""
    symbol: str
    name: str
    close: float
    change_pct: float
    score: float
    sector_score: float = 0.0
    capital_score: float = 0.0
    technical_score: float = 0.0
    fundamental_score: float = 0.0
    risk_score: float = 0.0
    reasons: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []
        if self.warnings is None:
            self.warnings = []


class StockAnalyzer:
    """股票多维度共振筛选分析器"""

    def __init__(self, mongodb_config: Dict):
        self.mongo_config = mongodb_config
        self._industry_normalizer = None

    @property
    def industry_normalizer(self) -> IndustryNormalizer:
        if self._industry_normalizer is None:
            self._industry_normalizer = IndustryNormalizer()
        return self._industry_normalizer

    def analyze(self, news_analysis: Dict, llm_client=None, top_n: int = 10) -> Dict:
        """多维度共振筛选分析"""
        if not news_analysis:
            return {"error": "新闻分析数据为空"}

        hot_sectors = news_analysis.get("hot_sectors", [])
        hot_stocks = news_analysis.get("hot_stocks", [])
        if not hot_sectors and not hot_stocks:
            return {"error": "热门行业和热门股票均为空"}

        logger.info(
            f"开始多维度共振筛选: hot_sectors={hot_sectors}, hot_stocks={hot_stocks}"
        )

        try:
            target_stocks = self._get_target_stocks(hot_sectors, hot_stocks)
            logger.info(f"目标股票数量: %s",  {len(target_stocks)})

            if not target_stocks:
                return {"error": "未找到目标股票"}

            kline_data = self._get_klines_with_indicators(target_stocks)
            if kline_data.empty:
                return {"error": "MongoDB中无K线数据"}

            capital_flow_data = self._get_capital_flow_data(target_stocks)
            print("资金流向数据:", capital_flow_data)
            if capital_flow_data.empty:
                logger.warning("MongoDB中无资金流向数据，将跳过资金流向筛选")

            candidates = self._multi_dimensional_filter(
                kline_data, capital_flow_data, news_analysis
            )

            if not candidates:
                return {"error": "无符合条件股票", "candidates": []}

            top_candidates = sorted(candidates, key=lambda x: x.score, reverse=True)[:top_n]

            result = {
                "total_candidates": len(candidates),
                "top_stocks": [
                    {
                        "symbol": c.symbol,
                        "name": c.name,
                        "close": c.close,
                        "change_pct": c.change_pct,
                        "score": round(c.score, 2),
                        "sector_score": round(c.sector_score, 2),
                        "capital_score": round(c.capital_score, 2),
                        "technical_score": round(c.technical_score, 2),
                        "fundamental_score": round(c.fundamental_score, 2),
                        "risk_score": round(c.risk_score, 2),
                        "reasons": c.reasons,
                        "warnings": c.warnings,
                    }
                    for c in top_candidates
                ],
                "summary": self._generate_summary(top_candidates, news_analysis),
            }

            return result

        except Exception as e:
            logger.error(f"多维度共振筛选失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            return {"error": f"分析失败: {str(e)}"}

    def _get_target_stocks(self, hot_sectors: List, hot_stocks: List) -> List[str]:
        target = set()

        if hot_sectors:
            for sector in hot_sectors:
                print("sector", sector)
                stocks = self.industry_normalizer.get_stock_name(sector)
                
                if stocks:
                    target.update(stocks)
                    logger.info(f"从行业 {sector} 获取到 {len(stocks)} 只股票")

        for stock in hot_stocks:
            if isinstance(stock, str):
                symbol = stock.split("(")[-1].rstrip(")") if "(" in stock else stock
                if len(symbol) == 6 and symbol.isdigit():
                    if int(symbol) >= 600000:
                        target.add(f"sh{symbol}")
                    else:
                        target.add(f"sz{symbol}")

        return list(target)

    def _get_klines_with_indicators(
        self, names: List[str], days: int = 60
    ) -> pd.DataFrame:
        from app.storage.mongo_client import MongoStorage

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        mongo = MongoStorage(**self.mongo_config)
        mongo.connect()

        all_data = []
        for name in names[0:10]:
            try:
                data = mongo.get_kline_by_name(
                    name, start_date=start_date, end_date=end_date, limit=100
                )
                if data:
                    df = pd.DataFrame(data)
                    df["name"] = name
                    all_data.append(df)
            except Exception as e:
                logger.warning(f"获取 {name} K线失败: {e}")

        mongo.close()

        if not all_data:
            return pd.DataFrame()

        result = pd.concat(all_data, ignore_index=True)
        result = result.rename(
            columns={
                "code": "symbol",
                "pct_chg": "change_pct",
                "turnover": "turnover_rate",
            }
        )

        numeric_cols = [
            "open",
            "close",
            "high",
            "low",
            "volume",
            "amount",
            "pct_chg",
            "amplitude",
            "turnover",
        ]
        for col in numeric_cols:
            if col in result.columns:
                result[col] = pd.to_numeric(result[col], errors="coerce")

        if "date" in result.columns:
            result["date"] = pd.to_datetime(result["date"])

        from .technical_indicators import TechnicalIndicators

        result = TechnicalIndicators.calculate_all(result)

        return result

    def _get_capital_flow_data(self, names: List[str], days: int = 10) -> pd.DataFrame:
        from app.storage.mongo_client import MongoStorage

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        mongo = MongoStorage(**self.mongo_config)
        mongo.connect()

        all_data = []
        for name in names:
            try:
                data = mongo.get_capital_flow(
                    name, start_date=start_date, end_date=end_date, limit=10
                )
                if data:
                    df = pd.DataFrame(data)
                    df["name"] = name
                    all_data.append(df)
            except Exception as e:
                logger.warning(f"获取 {name} 资金流向失败: {e}")

        mongo.close()

        if not all_data:
            return pd.DataFrame()

        result = pd.concat(all_data, ignore_index=True)

        numeric_cols = [
            "main_net_inflow",
            "main_net_inflow_pct",
            "super_large_net_inflow",
            "large_net_inflow",
            "medium_net_inflow",
            "small_net_inflow",
        ]
        for col in numeric_cols:
            if col in result.columns:
                result[col] = pd.to_numeric(result[col], errors="coerce")

        if "date" in result.columns:
            result["date"] = pd.to_datetime(result["date"])

        return result

    def _multi_dimensional_filter(
        self,
        kline_data: pd.DataFrame,
        capital_flow_data: pd.DataFrame,
        news_analysis: Dict,
    ) -> List[StockScore]:
        if kline_data.empty:
            return []

        kline_data = kline_data.sort_values("date", ascending=False)
        latest_kline = kline_data.groupby("name").first().reset_index()
        print("capital_flow_data", capital_flow_data.columns)
        candidates = []

        for _, row in latest_kline.iterrows():
            name = row["name"]
            stock_kline = kline_data[kline_data["name"] == name].sort_values("date")
            stock_capital = (
                capital_flow_data[capital_flow_data["name"] == name]
                .sort_values("date")
                .copy()
                if not capital_flow_data.empty
                else pd.DataFrame()
            )
            print("资金stock_capital", stock_capital)
            score = StockScore(
                symbol=row.get("code", ""),
                name=name,
                close=row.get("close", 0),
                change_pct=row.get("change_pct", 0),
                score=0.0,
            )

            sector_score = self._evaluate_sector(score, news_analysis)
            if sector_score == 0:
                continue

            score.sector_score = sector_score

            if not stock_capital.empty:
                capital_score = self._evaluate_capital_flow(score, stock_capital, stock_kline)
                if capital_score == 0:
                    continue
                score.capital_score = capital_score

            technical_score = self._evaluate_technical(score, stock_kline)
            if technical_score == 0:
                continue
            score.technical_score = technical_score

            fundamental_score, risk_score = self._evaluate_fundamental_and_risk(
                score, stock_kline
            )
            if risk_score == 0:
                continue
            score.fundamental_score = fundamental_score
            score.risk_score = risk_score

            score.score = (
                score.sector_score * 0.25
                + score.capital_score * 0.25
                + score.technical_score * 0.30
                + score.fundamental_score * 0.15
                + score.risk_score * 0.05
            )

            candidates.append(score)

        return candidates

    def _evaluate_sector(
        self, score: StockScore, news_analysis: Dict
    ) -> float:
        hot_sectors = news_analysis.get("hot_sectors", [])
        hot_concepts = news_analysis.get("hot_concepts", [])
        sentiment = news_analysis.get("sentiment", "中性")

        sector_score = 0.0

        if sentiment == "积极":
            sector_score += 20
        elif sentiment == "中性":
            sector_score += 10

        if score.change_pct > 5:
            sector_score += 20
            score.reasons.append("涨幅超过5%")
        elif score.change_pct > 2:
            sector_score += 15
            score.reasons.append("涨幅超过2%")
        elif score.change_pct > 0:
            sector_score += 10

        if score.change_pct > 0 and score.change_pct < 9.8:
            sector_score += 10
            score.reasons.append("涨幅健康")

        return min(sector_score, 100)

    def _evaluate_capital_flow(
        self,
        score: StockScore,
        capital_data: pd.DataFrame,
        kline_data: pd.DataFrame,
    ) -> float:
        capital_score = 0.0

        if capital_data.empty:
            return 10.0

        latest = capital_data.iloc[0]
        recent_3_days = capital_data.head(3)

        main_inflow = latest.get("main_net_inflow", 0)
        main_inflow_pct = latest.get("main_net_inflow_pct", 0)

        if main_inflow > 100000000:
            capital_score += 25
            score.reasons.append("主力净流入超1亿")
        elif main_inflow > 50000000:
            capital_score += 20
            score.reasons.append("主力净流入超5000万")
        elif main_inflow > 0:
            capital_score += 15
            score.reasons.append("主力净流入")

        if main_inflow_pct > 10:
            capital_score += 15
            score.reasons.append("主力流入占比超10%")
        elif main_inflow_pct > 5:
            capital_score += 10
            score.reasons.append("主力流入占比超5%")

        consecutive_inflow = 0
        for _, row in recent_3_days.iterrows():
            if row.get("main_net_inflow", 0) > 0:
                consecutive_inflow += 1
            else:
                break

        if consecutive_inflow >= 3:
            capital_score += 20
            score.reasons.append("连续3日主力净流入")
        elif consecutive_inflow >= 2:
            capital_score += 15
            score.reasons.append("连续2日主力净流入")

        if not kline_data.empty:
            latest_kline = kline_data.iloc[0]
            volume_ratio = latest_kline.get("volume", 0) / kline_data["volume"].mean()
            turnover_rate = latest_kline.get("turnover_rate", 0)

            if volume_ratio >= 1.5:
                capital_score += 10
                score.reasons.append("量比≥1.5")

            if 3 <= turnover_rate <= 8:
                capital_score += 10
                score.reasons.append("换手率健康(3%-8%)")
            elif turnover_rate > 8:
                capital_score += 5
                score.warnings.append("换手率偏高")

        return min(capital_score, 100)

    def _evaluate_technical(self, score: StockScore, kline_data: pd.DataFrame) -> float:
        technical_score = 0.0

        if kline_data.empty or len(kline_data) < 20:
            return 10.0

        latest = kline_data.iloc[0]
        ma5 = latest.get("ma5", 0)
        ma10 = latest.get("ma10", 0)
        ma20 = latest.get("ma20", 0)
        rsi = latest.get("rsi", 50)
        macd = latest.get("macd", 0)
        macd_signal = latest.get("macd_signal", 0)

        if ma5 > ma10 > ma20:
            technical_score += 25
            score.reasons.append("均线多头排列")
        elif ma5 > ma10:
            technical_score += 15
            score.reasons.append("短期均线向上")

        if score.close > ma20:
            technical_score += 15
            score.reasons.append("站稳20日均线")

        if macd > 0 and macd > macd_signal:
            technical_score += 20
            score.reasons.append("MACD金叉且在零轴上方")
        elif macd > 0:
            technical_score += 10
            score.reasons.append("MACD在零轴上方")

        if 60 <= rsi <= 80:
            technical_score += 20
            score.reasons.append("RSI强势区间(60-80)")
        elif 50 <= rsi < 60:
            technical_score += 15
            score.reasons.append("RSI健康区间(50-60)")
        elif rsi > 80:
            technical_score += 5
            score.warnings.append("RSI超买")

        if len(kline_data) >= 2:
            prev = kline_data.iloc[1]
            if score.close > prev["close"] and latest["volume"] > prev["volume"]:
                technical_score += 10
                score.reasons.append("放量上涨")

        return min(technical_score, 100)

    def _evaluate_fundamental_and_risk(
        self, score: StockScore, kline_data: pd.DataFrame
    ) -> Tuple[float, float]:
        fundamental_score = 0.0
        risk_score = 0.0

        if kline_data.empty:
            return 50.0, 50.0

        latest = kline_data.iloc[0]
        amount = latest.get("amount", 0)
        volume = latest.get("volume", 0)
        close = latest.get("close", 0)

        if amount > 300000000:
            risk_score += 30
            score.reasons.append("成交额超3亿")
        elif amount > 100000000:
            risk_score += 20
            score.reasons.append("成交额超1亿")

        market_cap = close * volume
        if market_cap > 1500000000:
            risk_score += 30
            score.reasons.append("市值超15亿")
        elif market_cap > 500000000:
            risk_score += 20
            score.reasons.append("市值超5亿")

        if score.change_pct > 9.8:
            risk_score += 10
            score.warnings.append("涨停股波动大")
        elif score.change_pct > 7:
            risk_score += 5
            score.warnings.append("涨幅较大")

        if len(kline_data) >= 5:
            recent_5 = kline_data.head(5)
            volatility = recent_5["change_pct"].std()
            if volatility < 3:
                fundamental_score += 20
                score.reasons.append("波动率较低")
            elif volatility < 5:
                fundamental_score += 10
                score.reasons.append("波动率适中")

        return min(fundamental_score, 100), min(risk_score, 100)

    def _generate_summary(
        self, candidates: List[StockScore], news_analysis: Dict
    ) -> Dict:
        if not candidates:
            return {"message": "未找到符合条件的股票"}

        avg_score = sum(c.score for c in candidates) / len(candidates)
        high_score_count = sum(1 for c in candidates if c.score >= 70)

        hot_sectors = news_analysis.get("hot_sectors", [])
        sentiment = news_analysis.get("sentiment", "中性")

        return {
            "message": f"从6000多只A股中筛选出{len(candidates)}只高关注标的",
            "avg_score": round(avg_score, 2),
            "high_score_count": high_score_count,
            "hot_sectors": hot_sectors,
            "market_sentiment": sentiment,
            "disclaimer": (
                "⚠️ 风险提示：本分析基于历史数据和客观指标，不构成投资建议。"
                "市场存在不确定性，请结合自身风险承受能力谨慎决策。"
                "不存在绝对的最优股票，只有当前阶段综合表现更优的候选池。"
            ),
        }
