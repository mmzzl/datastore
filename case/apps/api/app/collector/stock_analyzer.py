"""股票分析模块 - 根据新闻分析结果推荐买入股票"""

import os
import pandas as pd
import logging
import json
import baostock as bs
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class IndustryStockFinder:
    """行业股票查找器"""

    def __init__(self):
        self._industry_cache = None

    def get_industry_data(self) -> pd.DataFrame:
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)
        csv_path = os.path.join(base_dir, "data", "stock_industry.csv")
        logger.info("csv_path: %s", csv_path)
        if self._industry_cache is not None:
            return self._industry_cache

        # Check if CSV file exists
        if os.path.exists(csv_path):
            logger.info(f"Reading cached file: {csv_path}")
            df = pd.read_csv(csv_path, encoding="utf-8")
            self._industry_cache = df
            return df

        # Login to baostock
        logger.info("Logging into baostock...")
        lg = bs.login()
        if lg.error_code != "0":
            raise Exception(f"Login failed: {lg.error_msg}")
        logger.info(f"Login successful: {lg.error_msg}")

        # Get industry classification data
        logger.info("Fetching industry classification data...")
        rs = bs.query_stock_industry()
        if rs.error_code != "0":
            bs.logout()
            raise Exception(f"Query failed: {rs.error_msg}")

        # Parse results
        industry_list = []
        while rs.next():
            industry_list.append(rs.get_row_data())

        result = pd.DataFrame(industry_list, columns=rs.fields)

        # Save to CSV
        result.to_csv(csv_path, encoding="utf-8", index=False)
        logger.info(f"Data saved to: {csv_path}")

        # Logout
        bs.logout()
        logger.info("Logged out from baostock")

        self._industry_cache = result
        return result

    def get_stocks_by_industry(self, industry_names: List[str]) -> List[str]:
        df = self.get_industry_data()
        if df.empty:
            return []

        stocks = []
        for industry in industry_names:
            matched = df[df["industry"] == industry]["code"].tolist()
            stocks.extend(matched)

        result = []
        for code in stocks:
            if isinstance(code, str):
                if code.startswith("sh."):
                    result.append(f"sh{code[3:]}")
                elif code.startswith("sz."):
                    result.append(f"sz{code[3:]}")
                else:
                    result.append(code)

        return list(set(result))


class StockAnalyzer:
    """股票买入机会分析器"""

    # 行业映射表：热门行业关键词 -> Baostock行业分类
    INDUSTRY_MAPPING = {
        # 能源相关
        "能源/油气": ["能源", "石油", "煤炭", "采掘"],
        "油气": ["石油", "能源", "采掘"],
        "储能": ["电力设备", "新能源", "电池", "储能"],
        "固态电池": ["电池", "新能源材料", "化学制品", "电力设备"],
        # 人工智能相关
        "人工智能/金融科技": ["计算机", "软件", "信息技术", "金融科技"],
        "人工智能": ["计算机", "软件", "信息技术"],
        "金融科技": ["银行", "证券", "保险", "金融科技"],
        # 其他
        "新能源": ["电力设备", "新能源", "电池"],
        "半导体": ["电子", "半导体"],
        "医药": ["医药生物", "医疗器械"],
        "消费": ["食品饮料", "家用电器", "消费"],
    }

    def __init__(self, mongodb_config: Dict):
        self.mongo_config = mongodb_config
        self._industry_finder = None

    @property
    def industry_finder(self) -> IndustryStockFinder:
        if self._industry_finder is None:
            self._industry_finder = IndustryStockFinder()
        return self._industry_finder

    def analyze(self, news_analysis: Dict, llm_client=None, top_n: int = 5) -> Dict:
        """根据新闻分析结果分析最佳买入机会"""
        if not news_analysis:
            return {"error": "新闻分析数据为空"}

        hot_sectors = news_analysis.get("hot_sectors", [])
        hot_stocks = news_analysis.get("hot_stocks", [])

        if not hot_sectors and not hot_stocks:
            return {"error": "热门行业和热门股票均为空"}

        logger.info(
            f"开始分析买入机会: hot_sectors={hot_sectors}, hot_stocks={hot_stocks}"
        )

        # Step 1: 获取目标股票
        target_stocks = self._get_target_stocks(hot_sectors, hot_stocks)

        if not target_stocks:
            return {"error": "未找到目标股票"}

        # Step 2: 获取K线数据并计算指标
        kline_data = self._get_klines_with_indicators(target_stocks)

        if kline_data.empty:
            return {"error": "MongoDB中无K线数据"}

        # Step 3: 筛选分析
        if llm_client:
            return self._analyze_with_llm(kline_data, news_analysis, top_n, llm_client)
        else:
            return self._filter_by_rules(kline_data, top_n)

    def _get_target_stocks(self, hot_sectors: List, hot_stocks: List) -> List[str]:
        target = set()

        if hot_sectors:
            # 尝试直接匹配行业
            stocks = self.industry_finder.get_stocks_by_industry(hot_sectors)
            target.update(stocks)
            logger.info(f"从行业获取到 {len(stocks)} 只股票")

            # 如果没有匹配到，尝试使用映射表
            if not stocks:
                mapped_industries = self._map_hot_sectors(hot_sectors)
                stocks = self.industry_finder.get_stocks_by_industry(mapped_industries)
                target.update(stocks)
                logger.info(f"从映射行业获取到 {len(stocks)} 只股票")

        for stock in hot_stocks:
            if isinstance(stock, str):
                symbol = stock.split("(")[-1].rstrip(")") if "(" in stock else stock
                if len(symbol) == 6 and symbol.isdigit():
                    # 添加A股代码前缀
                    if int(symbol) >= 600000:
                        target.add(f"sh{symbol}")
                    else:
                        target.add(f"sz{symbol}")

        return list(target)

    def _map_hot_sectors(self, hot_sectors: List[str]) -> List[str]:
        """将热门行业映射到 Baostock 行业分类"""
        industry_df = self.industry_finder.get_industry_data()
        if industry_df.empty:
            return []

        # 获取所有唯一行业名称
        all_industries = industry_df["industry"].unique().tolist()

        matched_industries = set()

        for hot_sector in hot_sectors:
            # 尝试直接匹配
            if hot_sector in all_industries:
                matched_industries.add(hot_sector)
                continue

            # 使用映射表
            if hot_sector in self.INDUSTRY_MAPPING:
                mapped = self.INDUSTRY_MAPPING[hot_sector]
                for m in mapped:
                    if m in all_industries:
                        matched_industries.add(m)

            # 关键词模糊匹配
            for industry in all_industries:
                if isinstance(industry, str):
                    for keyword in hot_sector.split("/"):
                        if keyword in industry:
                            matched_industries.add(industry)

        logger.info(f"热门行业 {hot_sectors} -> 映射到 {list(matched_industries)}")
        return list(matched_industries)

    def _get_klines_with_indicators(
        self, symbols: List[str], days: int = 60
    ) -> pd.DataFrame:
        from app.storage.mongo_client import MongoStorage

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        mongo = MongoStorage(**self.mongo_config)
        mongo.connect()

        all_data = []
        for symbol in symbols:
            try:
                data = mongo.get_kline(
                    symbol, start_date=start_date, end_date=end_date, limit=100
                )
                if data:
                    df = pd.DataFrame(data)
                    df["symbol"] = symbol
                    all_data.append(df)
            except Exception as e:
                logger.warning(f"获取 {symbol} K线失败: {e}")

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

        # 计算技术指标
        from .technical_indicators import TechnicalIndicators

        result = TechnicalIndicators.calculate_all(result)

        return result

    def _filter_by_rules(self, df: pd.DataFrame, top_n: int) -> Dict:
        if df.empty:
            return {"error": "无有效数据"}

        required_cols = ["ma5", "ma10", "rsi"]
        if not all(col in df.columns for col in required_cols):
            return {"error": "缺少技术指标列"}

        df_valid = df.dropna(subset=required_cols)
        if df_valid.empty:
            return {"error": "无有效技术指标数据"}

        df_valid = df_valid.sort_values("date", ascending=False)
        latest = df_valid.groupby("symbol").first().reset_index()

        # 筛选条件
        conditions = (
            (latest["change_pct"] > 0)
            & (latest["rsi"] < 70)
            & (latest["ma5"] > latest["ma10"])
        )
        candidates = latest[conditions].copy()

        if candidates.empty:
            conditions = (latest["rsi"] < 80) & (latest["ma5"] > latest["ma10"])
            candidates = latest[conditions].copy()

        if candidates.empty:
            return {"error": "无符合条件股票", "candidates": []}

        # 计算得分
        candidates["score"] = (
            candidates["change_pct"] * 0.3
            + (70 - candidates["rsi"]) * 0.3
            + ((candidates["ma5"] - candidates["ma10"]) / candidates["ma10"] * 100)
            * 0.2
            + candidates.get("amplitude", pd.Series([5] * len(candidates))) * 0.2
        )

        top = candidates.nlargest(top_n, "score")

        result = [
            {
                "symbol": row["symbol"],
                "close": round(row.get("close", 0), 2),
                "change_pct": round(row.get("change_pct", 0), 2),
                "rsi": round(row.get("rsi", 0), 2),
                "ma5": round(row.get("ma5", 0), 2),
                "ma10": round(row.get("ma10", 0), 2),
                "score": round(row.get("score", 0), 2),
            }
            for _, row in top.iterrows()
        ]

        return {"total_candidates": len(candidates), "top_stocks": result}

    def _analyze_with_llm(
        self, df: pd.DataFrame, news_analysis: Dict, top_n: int, llm_client
    ) -> Dict:
        if df.empty:
            return {"error": "无数据可供分析"}

        required_cols = ["ma5", "ma10", "rsi"]
        if not all(col in df.columns for col in required_cols):
            return self._filter_by_rules(df, top_n)

        df_valid = df.dropna(subset=required_cols).sort_values("date", ascending=False)
        latest = df_valid.groupby("symbol").first().reset_index()

        stock_list = [
            {
                "symbol": row.get("symbol", ""),
                "close": round(row.get("close", 0), 2),
                "change_pct": round(row.get("change_pct", 0), 2),
                "rsi": round(row.get("rsi", 0), 2),
                "ma5": round(row.get("ma5", 0), 2),
                "ma10": round(row.get("ma10", 0), 2),
            }
            for _, row in latest.head(30).iterrows()
        ]

        hot_sectors = news_analysis.get("hot_sectors", [])

        try:
            return llm_client.analyze_stocks(stock_list, hot_sectors, top_n)
        except Exception as e:
            logger.warning(f"LLM调用失败，使用规则筛选: {e}")
            return self._filter_by_rules(latest, top_n)
