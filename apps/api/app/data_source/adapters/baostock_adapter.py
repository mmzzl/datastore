import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import baostock as bs

from ..interface import IDataSource
from ..models import StockKLine, StockInfo, MarketBreadth, CorrelatedAssets

logger = logging.getLogger(__name__)


class BaostockAdapter(IDataSource):
    """Baostock数据源适配器"""

    def __init__(self):
        self._connected = False
        self._name = "Baostock"
        self._provider = "baostock"

    @property
    def name(self) -> str:
        return self._name

    @property
    def provider(self) -> str:
        return self._provider

    def _ensure_connected(self):
        """确保已连接到baostock"""
        if not self._connected:
            lg = bs.login()
            if lg.error_code != "0":
                raise Exception(f"Baostock登录失败: {lg.error_msg}")
            self._connected = True
            logger.info("Baostock登录成功")

    def get_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
        adjust_flag: str = "3",
    ) -> List[StockKLine]:
        try:
            self._ensure_connected()

            rs = bs.query_history_k_data_plus(
                code,
                "date,code,open,high,low,close,volume,amount,adjustflag,turn,tradestatus,pctChg",
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                adjustflag=adjust_flag,
            )

            if rs.error_code != "0":
                logger.error(f"获取 {code} K线数据失败: {rs.error_msg}")
                return []

            data_list = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                kline = StockKLine(
                    code=row[1],
                    date=row[0],
                    open=float(row[2]),
                    high=float(row[3]),
                    low=float(row[4]),
                    close=float(row[5]),
                    volume=int(row[6]),
                    amount=float(row[7]),
                    turnover_rate=float(row[9]) if row[9] else None,
                    change_pct=float(row[11]) if row[11] else None,
                )
                data_list.append(kline)

            return data_list

        except Exception as e:
            logger.error(f"获取K线数据异常: {e}")
            return []

    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        try:
            self._ensure_connected()

            rs = bs.query_stock_basic(code)
            if rs.error_code != "0":
                return None

            if rs.next():
                row = rs.get_row_data()
                return StockInfo(
                    code=row[0], name=row[1], exchange=row[2][:2] if row[2] else "SH"
                )
            return None

        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return None

    def get_stock_list(self) -> List[StockInfo]:
        try:
            self._ensure_connected()

            rs = bs.query_all_stock()
            stock_list = []

            while rs.next():
                row = rs.get_row_data()
                if row[1] == "1":  # 交易状态正常
                    stock_list.append(
                        StockInfo(code=row[0], name=row[2], exchange=row[0][:2])
                    )

            return stock_list

        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []

    def get_realtime_data(self, code: str) -> Dict[str, Any]:
        """Baostock不提供实时数据，返回空字典"""
        return {}

    def get_capital_flow(self, code: str, days: int = 5) -> List[Dict[str, Any]]:
        """Baostock不提供资金流向数据，返回空列表"""
        return []

    def set_holdings(self, user_id: str, holdings: List[Dict[str, Any]]) -> List[str]:
        """无持仓设定实现的占位方法，Baostock 不提供持仓存储"""
        return []

    def get_portfolio_summary(self, user_id: str, price_fetcher=None) -> Dict[str, Any]:
        """返回一个空的持仓汇总结构，供统一接口调用"""
        return {
            "user_id": user_id,
            "holdings_count": 0,
            "total_cost": 0.0,
            "market_value": None,
            "unrealized_pnl": None,
            "holdings": [],
        }

    def close(self):
        """关闭Baostock连接"""
        if self._connected:
            bs.logout()
            self._connected = False
            logger.info("Baostock连接已关闭")

    def __del__(self):
        """析构函数中关闭连接"""
        self.close()

    # 兼容性接口：Settings 相关
    def get_settings(self, user_id: str) -> Dict[str, Any]:
        return {
            "watchlist": [],
            "interval_sec": 60,
            "days": 5,
            "cache_ttl": 60,
        }

    def set_settings(self, user_id: str, settings: Dict[str, Any]) -> None:
        # Baostock 不管理设置，保持接口兼容性，但不持久化
        return None

    def remove_holding(self, user_id: str, code: str) -> int:
        """无持仓删除实现的占位方法，Baostock 不提供持仓存储"""
        return 0

    def get_market_breadth(self) -> Optional[MarketBreadth]:
        return None

    def get_correlated_assets(self) -> Optional[CorrelatedAssets]:
        return None

    def get_minute_kline(
        self, code: str, frequency: str = "5", days: int = 5
    ) -> List[StockKLine]:
        return []
