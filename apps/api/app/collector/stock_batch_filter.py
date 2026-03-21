"""股票批量筛选器 - 从6000+只股票中筛选最值得买的"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import baostock as bs

logger = logging.getLogger(__name__)


class StockBatchFilter:
    """股票批量筛选器"""

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

    def __init__(self, mongo_config: Dict, industry_csv_path: str = None):
        self.mongo_config = mongo_config
        self.industry_csv_path = industry_csv_path
        self._industry_df = None
        self._all_stocks_cache = None

    def get_industry_df(self) -> pd.DataFrame:
        """获取行业分类数据"""
        if self._industry_df is not None:
            return self._industry_df

        import os

        csv_path = self.industry_csv_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "data",
            "stock_industry.csv",
        )

        if os.path.exists(csv_path):
            logger.info(f"读取行业缓存: {csv_path}")
            self._industry_df = pd.read_csv(csv_path, encoding="utf-8")
            return self._industry_df

        # 从 baostock 获取
        logger.info("从 baostock 获取行业数据...")
        lg = bs.login()
        if lg.error_code != "0":
            raise Exception(f"登录失败: {lg.error_msg}")

        rs = bs.query_stock_industry()
        if rs.error_code != "0":
            bs.logout()
            raise Exception(f"查询失败: {rs.error_msg}")

        industry_list = []
        while rs.next():
            industry_list.append(rs.get_row_data())

        result = pd.DataFrame(industry_list, columns=rs.fields)
        result.to_csv(csv_path, encoding="utf-8", index=False)
        bs.logout()

        self._industry_df = result
        return result

    def map_hot_sectors_to_industries(self, hot_sectors: List[str]) -> List[str]:
        """将热门行业映射到 Baostock 行业分类"""
        industry_df = self.get_industry_df()
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

    def get_stocks_by_industries(self, industries: List[str]) -> List[str]:
        """根据行业获取股票代码列表"""
        if not industries:
            return []

        industry_df = self.get_industry_df()
        if industry_df.empty:
            return []

        # 过滤行业
        mask = industry_df["industry"].isin(industries)
        stocks = industry_df[mask]["code"].tolist()

        # 转换格式: sh.600000 -> sh600000
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

    def get_all_stock_codes(self, limit: int = None) -> List[str]:
        """获取所有股票代码（排除指数）"""
        if self._all_stocks_cache is not None:
            return self._all_stocks_cache

        industry_df = self.get_industry_df()
        if industry_df.empty:
            return []

        # 过滤指数: sh.000000 ~ sh.599999 是指数
        mask = ~industry_df["code"].str.match(r"^sh\.[0-5]\d{5}$")
        stock_df = industry_df[mask]

        # 获取股票代码
        codes = stock_df["code"].tolist()

        # 转换格式
        result = []
        for code in codes:
            if isinstance(code, str):
                if code.startswith("sh."):
                    result.append(f"sh{code[3:]}")
                elif code.startswith("sz."):
                    result.append(f"sz{code[3:]}")
                else:
                    result.append(code)

        if limit:
            result = result[:limit]

        self._all_stocks_cache = result
        logger.info(f"获取到 {len(result)} 只股票（排除指数）")
        return result

    def get_kline_data_batch(self, symbols: List[str], days: int = 30) -> pd.DataFrame:
        """批量获取K线数据"""
        from app.storage.mongo_client import MongoStorage

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        mongo = MongoStorage(**self.mongo_config)
        mongo.connect()

        all_data = []
        batch_size = 100  # 分批查询，避免一次查询太多

        for i in range(0, len(symbols), batch_size):
            batch = symbols[i : i + batch_size]
            logger.info(
                f"正在获取批次 {i // batch_size + 1}/{(len(symbols) + batch_size - 1) // batch_size} ({len(batch)} 只股票)"
            )

            for symbol in batch:
                try:
                    data = mongo.get_kline(
                        symbol, start_date=start_date, end_date=end_date, limit=days
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

        # 转换数值列
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

        return result

    def filter_top_stocks(self, hot_sectors: List[str], top_n: int = 5) -> Dict:
        """筛选最值得买的股票"""
        logger.info(f"开始筛选: hot_sectors={hot_sectors}, top_n={top_n}")

        # 步骤1: 映射行业
        industries = self.map_hot_sectors_to_industries(hot_sectors)

        if industries:
            # 方式A: 从目标行业筛选
            target_stocks = self.get_stocks_by_industries(industries)
            logger.info(f"从目标行业获取到 {len(target_stocks)} 只股票")

            if len(target_stocks) > 200:
                # 太多股票，限制数量
                target_stocks = target_stocks[:200]
                logger.info(f"限制为前200只股票进行分析")
        else:
            # 方式B: 从全部股票筛选（前500只）
            target_stocks = self.get_all_stock_codes(limit=500)
            logger.info(f"从全部股票获取到 {len(target_stocks)} 只股票")

        if not target_stocks:
            return {"error": "未找到目标股票"}

        # 步骤2: 获取K线数据
        logger.info("正在获取K线数据...")
        kline_df = self.get_kline_data_batch(target_stocks, days=30)

        if kline_df.empty:
            return {"error": "未获取到K线数据"}

        # 步骤3: 计算技术指标
        logger.info("正在计算技术指标...")
        from .technical_indicators import TechnicalIndicators

        kline_df = TechnicalIndicators.calculate_all(kline_df)

        # 步骤4: 筛选和评分
        logger.info("正在筛选股票...")
        result = self._score_and_filter(kline_df, top_n)

        return result

    def _score_and_filter(self, df: pd.DataFrame, top_n: int) -> Dict:
        """计算得分并筛选Top N"""
        if df.empty:
            return {"error": "无有效数据"}

        # 获取最新数据
        df_sorted = df.sort_values("date", ascending=False)
        latest = df_sorted.groupby("symbol").first().reset_index()

        # 计算得分（多维度评分）
        # 1. 涨幅得分（越大越好）
        change_score = latest["change_pct"].clip(-10, 10) / 10  # 归一化到[-1, 1]

        # 2. RSI得分（70以下为好）
        rsi_score = (70 - latest["rsi"]).clip(0, 70) / 70

        # 3. 均线金叉得分
        ma_score = (latest["ma5"] - latest["ma10"]) / latest["ma10"] * 100
        ma_score = ma_score.clip(-5, 5) / 5  # 归一化

        # 4. 波动率得分（适中为好）
        amplitude = latest.get("amplitude", pd.Series([3] * len(latest)))
        amplitude_score = (amplitude - 2).clip(-2, 2) / 2  # 适中(2-4%)为好

        # 5. 成交量得分（放大为好）
        volume_score = pd.Series([0] * len(latest))  # 暂时未实现

        # 综合得分
        latest["score"] = (
            change_score * 0.35
            + rsi_score * 0.25
            + ma_score * 0.25
            + amplitude_score * 0.15
        )

        # 筛选条件：RSI < 70, MA5 > MA10
        conditions = (latest["rsi"] < 70) & (latest["ma5"] > latest["ma10"])
        candidates = latest[conditions].copy()

        if candidates.empty:
            # 放宽条件
            conditions = latest["rsi"] < 80
            candidates = latest[conditions].copy()

        if candidates.empty:
            return {"error": "无符合条件股票", "total_analyzed": len(latest)}

        # 获取Top N
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
                "industry": self._get_stock_industry(row["symbol"]),
            }
            for _, row in top.iterrows()
        ]

        return {
            "total_analyzed": len(latest),
            "total_candidates": len(candidates),
            "top_stocks": result,
        }

    def _get_stock_industry(self, symbol: str) -> str:
        """获取股票的行业分类"""
        if self._industry_df is None:
            return ""

        # 转换符号格式
        if symbol.startswith("sh"):
            code = f"sh.{symbol[2:]}"
        elif symbol.startswith("sz"):
            code = f"sz.{symbol[2:]}"
        else:
            code = symbol

        rows = self._industry_df[self._industry_df["code"] == code]
        if not rows.empty:
            return rows.iloc[0].get("industry", "")
        return ""
