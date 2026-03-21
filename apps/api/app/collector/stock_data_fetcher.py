"""数据获取模块 - 从MongoDB/API获取股票数据"""

import pandas as pd
import logging
from typing import Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class StockDataFetcher:
    """股票数据获取器"""

    def __init__(self, config: dict = None):
        self.config = config or {}
        self.spot_csv_file = "stock_zh_a_spot.csv"

    def load_daily_data(self, date: str) -> pd.DataFrame:
        """加载指定日期的股票数据"""
        from app.storage.mongo_client import MongoStorage
        from app.core.config import settings

        mongo = MongoStorage(
            host=settings.mongodb_host,
            port=settings.mongodb_port,
            db_name=settings.mongodb_database,
            username=settings.mongodb_username,
            password=settings.mongodb_password,
        )
        mongo.connect()

        kline_data = mongo.get_all_kline_by_date(date, limit=10000)
        mongo.close()

        if not kline_data:
            logger.warning(f"MongoDB中没有 {date} 的数据")
            return pd.DataFrame()

        df = pd.DataFrame(kline_data)

        # 过滤掉指数相关数据 (sh.000000 ~ sh.600000 之前)
        # sh.000000-sh.599999 是指数
        df = df.rename(
            columns={
                "code": "symbol",
                "pct_chg": "change_pct",
                "turnover": "turnover_rate",
            }
        )

        if "symbol" in df.columns:
            df["symbol"] = df["symbol"].apply(self._convert_code)
            logger.info(f"原始 {date} 数据共 {len(df)} 条")
            df = df[~df["symbol"].str.match(r"^sh\.[0-5]\d{5}$")]
            logger.info(f"过滤后 {date} 数据共 {len(df)} 条")
        # df = self._add_stock_names(df)
        return df

    def load_klines(self, symbols: List[str], days: int = 60) -> pd.DataFrame:
        """批量加载K线数据"""
        from app.storage.mongo_client import MongoStorage
        from app.core.config import settings

        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        mongo = MongoStorage(
            host=settings.mongodb_host,
            port=settings.mongodb_port,
            db_name=settings.mongodb_database,
            username=settings.mongodb_username,
            password=settings.mongodb_password,
        )
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
            columns={"pct_chg": "change_pct", "turnover": "turnover_rate"}
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

        return result

    def _convert_code(self, code) -> str:
        """转换股票代码格式"""
        try:
            code_str = str(code)
            if "." in code_str:
                parts = code_str.split(".")
                exchange = parts[0]
                stock_code = parts[1]
                if exchange == "1":
                    return f"sh.{stock_code}"
                elif exchange == "0":
                    return f"sz.{stock_code}"
            return code_str
        except:
            return str(code)

    def _add_stock_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加股票名称"""
        import os

        if not os.path.exists(self.spot_csv_file):
            return df

        try:
            stock_list_df = pd.read_csv(self.spot_csv_file)
            if "symbol" in stock_list_df.columns and "name" in stock_list_df.columns:
                symbol_name_map = dict(
                    zip(stock_list_df["symbol"], stock_list_df["name"])
                )
                df["name"] = df["symbol"].map(symbol_name_map)
        except Exception as e:
            logger.warning(f"读取股票名称失败: {e}")

        return df

    def get_stock_data(self, stock_code: str) -> dict:
        """
        获取单只股票的实时数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            股票数据字典
        """
        try:
            from app.storage.mongo_client import MongoStorage
            from app.core.config import settings
            
            # 获取当前日期
            today = datetime.now().strftime("%Y-%m-%d")
            
            mongo = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_database,
                username=settings.mongodb_username,
                password=settings.mongodb_password,
            )
            mongo.connect()
            
            # 获取最新K线数据
            kline_data = mongo.get_kline_by_date(stock_code, today)
            mongo.close()
            
            if not kline_data:
                logger.warning(f"MongoDB中没有 {stock_code} 在 {today} 的数据")
                return {}
            
            return {
                "name": kline_data.get("name", stock_code),
                "close": float(kline_data.get("close", 0)),
                "high": float(kline_data.get("high", 0)),
                "low": float(kline_data.get("low", 0)),
                "open": float(kline_data.get("open", 0)),
                "change": float(kline_data.get("change", 0)),
                "change_pct": float(kline_data.get("pct_chg", 0)),
                "volume": int(kline_data.get("volume", 0)),
                "amount": float(kline_data.get("amount", 0))
            }
            
        except Exception as e:
            logger.error(f"获取股票数据失败 {stock_code}: {e}")
            return {}

    def get_stock_history(self, stock_code: str, days: int = 30) -> dict:
        """
        获取股票历史数据
        
        Args:
            stock_code: 股票代码
            days: 获取天数
            
        Returns:
            历史数据字典
        """
        try:
            from app.storage.mongo_client import MongoStorage
            from app.core.config import settings
            
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            mongo = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_database,
                username=settings.mongodb_username,
                password=settings.mongodb_password,
            )
            mongo.connect()
            
            kline_data = mongo.get_kline(
                stock_code, start_date=start_date, end_date=end_date, limit=days
            )
            mongo.close()
            
            if not kline_data:
                logger.warning(f"MongoDB中没有 {stock_code} 的历史数据")
                return {}
            
            # 转换为所需格式
            df = pd.DataFrame(kline_data)
            
            return {
                "close": df["close"].tolist() if "close" in df.columns else [],
                "high": df["high"].tolist() if "high" in df.columns else [],
                "low": df["low"].tolist() if "low" in df.columns else [],
                "open": df["open"].tolist() if "open" in df.columns else [],
                "volume": df["volume"].tolist() if "volume" in df.columns else [],
                "date": df["date"].tolist() if "date" in df.columns else []
            }
            
        except Exception as e:
            logger.error(f"获取股票历史数据失败 {stock_code}: {e}")
            return {}
