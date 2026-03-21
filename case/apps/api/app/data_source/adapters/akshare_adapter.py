import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import akshare as ak
import pandas as pd

from ..interface import IDataSource
from ..models import StockKLine, StockInfo

logger = logging.getLogger(__name__)


class AkshareAdapter(IDataSource):
    """Akshare数据源适配器"""

    def __init__(self):
        self._name = "Akshare"
        self._provider = "akshare"
        # 内存缓存：存储 (data, timestamp) 元组
        self._capital_flow_cache: Dict[str, Tuple[List[Dict[str, Any]], datetime]] = {}
        # 缓存有效期（秒）：市场数据缓存1分钟
        self._cache_ttl = timedelta(minutes=60)

    @property
    def name(self) -> str:
        return self._name

    @property
    def provider(self) -> str:
        return self._provider

    def get_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
        adjust_flag: str = "3",
    ) -> List[StockKLine]:
        try:
            # 转换代码格式 sh.600000 -> 600000
            stock_code = code.split(".")[-1] if "." in code else code

            # 获取K线数据
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date.replace("-", ""),
                end_date=end_date.replace("-", ""),
                adjust="qfq"
                if adjust_flag == "1"
                else "hfq"
                if adjust_flag == "2"
                else "",
            )

            data_list = []
            for _, row in df.iterrows():
                kline = StockKLine(
                    code=code,
                    date=str(row["日期"]),
                    open=float(row["开盘"]),
                    high=float(row["最高"]),
                    low=float(row["最低"]),
                    close=float(row["收盘"]),
                    volume=int(row["成交量"]),
                    amount=float(row["成交额"]),
                    change_pct=float(row["涨跌幅"]) if "涨跌幅" in df.columns else None,
                )
                data_list.append(kline)

            return data_list

        except Exception as e:
            logger.error(f"获取K线数据异常: {e}")
            return []

    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        try:
            # Akshare获取股票信息
            stock_code = code.split(".")[-1] if "." in code else code

            # 从实时数据获取基本信息
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df["代码"] == stock_code]

            if not stock_data.empty:
                return StockInfo(
                    code=code,
                    name=stock_data.iloc[0]["名称"],
                    exchange=code[:2] if "." in code else "SH",
                )
            return None

        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return None

    def get_stock_list(self) -> List[StockInfo]:
        try:
            df = ak.stock_zh_a_spot_em()
            stock_list = []

            for _, row in df.iterrows():
                code = row["代码"]
                exchange = "SH" if code.startswith("6") else "SZ"
                stock_list.append(
                    StockInfo(
                        code=f"{exchange}.{code}", name=row["名称"], exchange=exchange
                    )
                )

            return stock_list

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []

    def get_realtime_data(self, code: str) -> Dict[str, Any]:
        try:
            stock_code = code.split(".")[-1] if "." in code else code

            df = ak.stock_zh_a_spot_em()
            stock_data = df[df["代码"] == stock_code]

            if not stock_data.empty:
                row = stock_data.iloc[0]
                return {
                    "code": code,
                    "name": row["名称"],
                    "price": row["最新价"],
                    "change": row["涨跌额"],
                    "change_pct": row["涨跌幅"],
                    "volume": row["成交量"],
                    "amount": row["成交额"],
                    "open": row["开盘"],
                    "high": row["最高"],
                    "low": row["最低"],
                    "close": row["最新价"],
                }
            return {}

        except Exception as e:
            logger.error(f"获取实时数据失败: {e}")
            return {}

    def get_capital_flow(self, code: str, days: int = 5) -> List[Dict[str, Any]]:
        """获取市场资金流向排名（带内存缓存）"""
        try:
            # 根据天数选择对应的排行参数
            if days <= 1:
                period = "即时"
            elif days <= 3:
                period = "3日排行"
            elif days <= 5:
                period = "5日排行"
            elif days <= 10:
                period = "10日排行"
            else:
                period = "20日排行"

            # 创建缓存键
            cache_key = f"capital_flow_{period}"
            now = datetime.now()

            # 检查缓存是否有效
            if cache_key in self._capital_flow_cache:
                cached_data, cached_time = self._capital_flow_cache[cache_key]
                if now - cached_time < self._cache_ttl:
                    logger.debug(f"使用缓存的市场资金流向数据，周期: {period}")
                    return cached_data
                else:
                    logger.debug(f"缓存已过期，周期: {period}")
                    # 删除过期缓存
                    del self._capital_flow_cache[cache_key]

            # 使用akshare获取市场资金流向排名数据
            df = ak.stock_fund_flow_individual(period)

            if df is None or df.empty:
                logger.warning(f"未获取到市场资金流向数据，周期: {period}")
                return []

            result = []
            for idx, row in df.iterrows():
                try:
                    # 安全地获取和转换数据
                    serial_val = row["序号"]
                    code_val = row["股票代码"]
                    name_val = row["股票简称"]
                    price_val = row["最新价"]
                    change_pct_val = row["阶段涨跌幅"]
                    turnover_val = row["连续换手率"]
                    inflow_val = row["资金流入净额"]

                    # 处理数据，确保类型正确
                    serial_int = int(serial_val) if pd.notna(serial_val) else 0
                    code_str = str(code_val) if pd.notna(code_val) else ""
                    name_str = str(name_val) if pd.notna(name_val) else ""
                    price_float = float(price_val) if pd.notna(price_val) else 0.0

                    # 处理百分比字符串（如"34.30%"或"-31.26%"）
                    change_pct_float = 0.0
                    if pd.notna(change_pct_val):
                        change_pct_str = str(change_pct_val).strip()
                        if change_pct_str.endswith("%"):
                            change_pct_str = change_pct_str[:-1]  # 移除%符号
                        try:
                            change_pct_float = float(change_pct_str)
                        except ValueError:
                            change_pct_float = 0.0

                    # 处理百分比字符串（如"16.21%"或"6.25%"）
                    turnover_float = 0.0
                    if pd.notna(turnover_val):
                        turnover_str = str(turnover_val).strip()
                        if turnover_str.endswith("%"):
                            turnover_str = turnover_str[:-1]  # 移除%符号
                        try:
                            turnover_float = float(turnover_str)
                        except ValueError:
                            turnover_float = 0.0

                    # 处理金额字符串（如"2.65亿"或"-7288.95万"）
                    inflow_float = 0.0
                    if pd.notna(inflow_val):
                        inflow_str = str(inflow_val).strip()
                        try:
                            if inflow_str.endswith("亿"):
                                inflow_float = float(inflow_str[:-1]) * 100000000
                            elif inflow_str.endswith("万"):
                                inflow_float = float(inflow_str[:-1]) * 10000
                            else:
                                inflow_float = float(inflow_str)
                        except ValueError:
                            inflow_float = 0.0

                    result.append(
                        {
                            "serial": serial_int,
                            "code": code_str,
                            "name": name_str,
                            "price": price_float,
                            "change_pct": change_pct_float,
                            "turnover_rate": turnover_float,
                            "net_inflow": inflow_float,
                            "period": period,
                        }
                    )
                except Exception as row_error:
                    logger.warning(f"处理市场资金流向数据行失败: {row_error}")
                    continue

            # 存储到缓存
            self._capital_flow_cache[cache_key] = (result, now)
            logger.debug(
                f"获取市场资金流向数据并缓存，周期: {period}, 条数: {len(result)}"
            )

            return result
        except Exception as e:
            logger.error(f"获取市场资金流向失败: {e}")
            return []

    def close(self):
        """Akshare不需要关闭连接"""
        pass

    def get_settings(self, user_id: str) -> Dict[str, Any]:
        return {"watchlist": [], "interval_sec": 60, "days": 5, "cache_ttl": 60}

    def set_settings(self, user_id: str, settings: Dict[str, Any]) -> None:
        return None

    def set_holdings(self, user_id: str, holdings: List[Dict[str, Any]]) -> List[str]:
        """Akshare 不直接管理持仓，作为兼容实现返回空列表"""
        return []

    def get_portfolio_summary(self, user_id: str, price_fetcher=None) -> Dict[str, Any]:
        """返回一个兼容的空持仓汇总数据结构，供统一接口调用"""
        return {
            "user_id": user_id,
            "holdings_count": 0,
            "total_cost": 0.0,
            "market_value": None,
            "unrealized_pnl": None,
            "holdings": [],
        }
