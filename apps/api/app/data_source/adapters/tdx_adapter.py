import logging
import re
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

try:
    from mootdx.quotes import Quotes

    MOOTDX_AVAILABLE = True
except ImportError:
    MOOTDX_AVAILABLE = False
    logger.warning("mootdx library not available, TDX adapter will not work")

from ..interface import IDataSource
from ..models import StockKLine, StockInfo, MarketBreadth, CorrelatedAssets


class TDXAdapter(IDataSource):
    """通达信（TDX）数据源适配器"""

    def __init__(self):
        self._name = "通达信"
        self._provider = "tdx"
        self._client = None

    def _get_client(self):
        """获取或创建通达信客户端（单例）"""
        if self._client is None and MOOTDX_AVAILABLE:
            try:
                self._client = Quotes.factory(market="std", multithread=True, heartbeat=False)
                logger.info("通达信适配器初始化成功")
            except Exception as e:
                logger.error(f"初始化通达信适配器失败: {e}")
        return self._client

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
        frequency: int = 9,
        adjust_flag: str = "qfq",
    ) -> List[StockKLine]:
        """获取K线数据 - 使用mootdx"""
        if not MOOTDX_AVAILABLE:
            logger.warning("mootdx库不可用，无法获取K线数据")
            return []

        try:
            # 转换代码格式 sh.600000 -> 600000, sz.000001 -> 000001
            stock_code = code.split(".")[-1] if "." in code else code
            # 兼容 SH600619 格式，去掉前缀字母
            stock_code = re.sub(r'^[A-Za-z]+', '', stock_code)
            client = self._get_client()
            if client is None:
                return []
            # 获取K线数据
            # 使用 bars 方法获取K线数据
            frequency = 9
            adjust_flag = "qfq"
            df = client.bars(
                symbol=stock_code, frequency=frequency, offset=100
            )
            if df is None or df.empty:
                logger.warning(f"未获取到 {code} 的K线数据")
                return []

            # 转换为统一格式
            data_list = []
            for _, row in df.iterrows():
                # 处理日期
                date_str = str(row.get("datetime", ""))
                if not date_str:
                    continue
                # 解析日期
                try:
                    if len(date_str) == 8:  # YYYYMMDD
                        date = datetime.strptime(date_str, "%Y%m%d")
                    elif len(date_str) == 14:  # YYYYMMDD HHMMSS
                        date = datetime.strptime(date_str[:8], "%Y%m%d")
                    else:
                        continue
                except:
                    continue

                kline = StockKLine(
                    code=code,
                    date=date.strftime("%Y-%m-%d"),
                    open=float(row.get("open", 0)),
                    high=float(row.get("high", 0)),
                    low=float(row.get("low", 0)),
                    close=float(row.get("close", 0)),
                    volume=int(row.get("volume", 0)),
                    amount=float(row.get("amount", 0)),
                    turnover_rate=None,  # 可选字段
                    change_pct=None,  # 可选字段
                )
                data_list.append(kline)
            # 按日期排序
            data_list.sort(key=lambda x: x.date)
            return data_list

        except Exception as e:
            logger.error(f"获取K线数据异常: {e}")
            return []

    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        """获取股票基本信息"""
        if not MOOTDX_AVAILABLE:
            return None
        try:
            # 转换代码格式
            stock_code = code.split(".")[-1] if "." in code else code
            # 兼容 SH600619 格式，去掉前缀字母
            stock_code = re.sub(r'^[A-Za-z]+', '', stock_code)

                # 判断市场代码
            if stock_code.startswith("6") or stock_code.startswith("9"):
                market = 0 # 沪市
            else:
                market = 1 # 深市

            client = self._get_client()
            if client is None:
                return None

            # 获取实时数据
            data = client.quotes(symbol=stock_code, market=market)

            if data is not None and len(data) > 0:
                row = data.iloc[0]
                # 确定交易所
                exchange = "SH" if market == 0 else "SZ"
                return StockInfo(
                            code=code,
                            name=stock_code,  # 通达信不提供股票名称，使用代码
                            exchange=exchange,
                            industry=None,
                            market_value=None,
                        )
            return None

        except Exception as e:
            logger.error(f"获取股票信息失败: {e}")
            return None

    def get_stock_list(self) -> List[StockInfo]:
        """获取股票列表 - 通达信不支持批量获取"""
        logger.info("通达信不支持批量获取股票列表，建议使用其他数据源")
        return []

    def get_realtime_data(self, code: str) -> Dict[str, Any]:
        """获取实时数据 - 通达信的主要功能"""
        if not MOOTDX_AVAILABLE:
            return {}

        try:
            # 转换代码格式
            stock_code = code.split(".")[-1] if "." in code else code
            # 兼容 SH600619 格式，去掉前缀字母
            stock_code = re.sub(r'^[A-Za-z]+', '', stock_code)

            # 判断市场代码
            if stock_code.startswith("6") or stock_code.startswith("9"):
                market = 0 # 沪市
            else:
                market = 1 # 深市

            client = self._get_client()
            if client is None:
                return {}

            # 获取实时数据
            data = client.quotes(symbol=stock_code, market=market)

            if data is not None and len(data) > 0:
                row = data.iloc[0]

                # 确定交易所
                exchange = "SH" if market == 0 else "SZ"

                # 计算涨跌幅
                price = float(row.get("price", 0))
                last_close = float(row.get("last_close", 0))
                change = price - last_close
                change_pct = (change / last_close * 100) if last_close != 0 else 0

                return {
                    "code": f"{exchange}.{stock_code}",
                    "name": stock_code,
                    "price": price,
                    "change": change,
                    "change_pct": change_pct,
                    "volume": int(row.get("volume", 0)),
                    "amount": float(row.get("amount", 0)) if "amount" in row else 0,
                    "open": float(row.get("open", 0)),
                    "high": float(row.get("high", 0)),
                    "low": float(row.get("low", 0)),
                    "close": price,
                    "last_close": last_close,
                }
            return {}

        except Exception as e:
            logger.error(f"获取实时数据失败: {e}")
            return {}

    def get_capital_flow(self, code: str, days: int = 5) -> List[Dict[str, Any]]:
        """通达信不直接提供资金流向数据"""
        return []

    def set_holdings(self, user_id: str, holdings: List[Dict[str, Any]]) -> List[str]:
        """TDX 不实现持仓存储，返回空列表作为兼容实现"""
        return []

    def get_portfolio_summary(self, user_id: str, price_fetcher=None) -> Dict[str, Any]:
        """返回兼容的空持仓汇总数据结构"""
        return {
            "user_id": user_id,
            "holdings_count": 0,
            "total_cost": 0.0,
            "market_value": None,
            "unrealized_pnl": None,
            "holdings": [],
        }

    def close(self):
        """关闭通达信连接"""
        if self._client:
            # mootdx不需要显式关闭
            logger.info("通达信客户端已关闭")

    def get_settings(self, user_id: str) -> Dict[str, Any]:
        return {"watchlist": [], "interval_sec": 60, "days": 5, "cache_ttl": 60}

    def set_settings(self, user_id: str, settings: Dict[str, Any]) -> None:
        return None

    def remove_holding(self, user_id: str, code: str) -> int:
        """TDX 不实现持仓删除，返回 0 作为兼容实现"""
        return 0

    def get_market_breadth(self) -> Optional[MarketBreadth]:
        return None

    def get_correlated_assets(self) -> Optional[CorrelatedAssets]:
        return None

    def get_minute_kline(
        self, code: str, frequency: str = "5", days: int = 5
    ) -> List[StockKLine]:
        return []
