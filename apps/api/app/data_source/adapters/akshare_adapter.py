import logging
import re
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import akshare as ak
import pandas as pd
import requests

from ..interface import IDataSource
from ..models import StockKLine, StockInfo, MarketBreadth, CorrelatedAssets

logger = logging.getLogger(__name__)

DEFAULT_VIX = 18.0
DEFAULT_USDCNH = 7.25
DEFAULT_DXY = 104.0


class AkshareAdapter(IDataSource):
    """Akshare数据源适配器"""

    def __init__(self):
        self._name = "Akshare"
        self._provider = "akshare"
        # 内存缓存：存储 (data, timestamp) 元组
        self._capital_flow_cache: Dict[str, Tuple[List[Dict[str, Any]], datetime]] = {}
        self._realtime_cache: Optional[Tuple[pd.DataFrame, datetime]] = None
        # 缓存有效期（秒）：市场数据缓存1分钟
        self._cache_ttl = timedelta(minutes=60)
        self._realtime_cache_ttl = timedelta(seconds=30)

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

    def _get_realtime_df(self) -> pd.DataFrame:
        """获取全市场实时行情DataFrame（带缓存）"""
        now = datetime.now()
        if (
            self._realtime_cache is not None
            and (now - self._realtime_cache[1]) < self._realtime_cache_ttl
        ):
            return self._realtime_cache[0]
        try:
            df = ak.stock_zh_a_spot_em()
            self._realtime_cache = (df, now)
            logger.info(f"刷新全市场实时行情缓存，共 {len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"获取全市场实时行情失败: {e}")
            if self._realtime_cache is not None:
                return self._realtime_cache[0]
            return pd.DataFrame()

    def get_realtime_data(self, code: str) -> Dict[str, Any]:
        try:
            stock_code = code.split(".")[-1] if "." in code else code

            df = self._get_realtime_df()
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

    def remove_holding(self, user_id: str, code: str) -> int:
        """Akshare 不直接管理持仓，作为兼容实现返回 0"""
        return 0

    def get_market_breadth(self) -> Optional[MarketBreadth]:
        """获取市场广度数据（使用新浪接口，不依赖东方财富）"""
        try:
            headers = {
                "Referer": "https://finance.sina.com.cn",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }

            # 从新浪行业板块数据获取涨跌家数和板块排名
            url = "https://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php"
            r = requests.get(url, headers=headers, timeout=15)
            r.encoding = "gbk"
            text = r.text

            match = re.search(r"\{(.+)\}", text)
            if not match:
                logger.warning("新浪行业板块数据解析失败")
                return None

            items = re.findall(r'"(\w+)":"([^"]+)"', match.group(0))

            total_advance = 0
            sectors = []
            for _key, val in items:
                parts = val.split(",")
                if len(parts) < 9:
                    continue
                try:
                    up_count = int(parts[2])
                    chg_pct = float(parts[3])
                    name = parts[1]
                    total_advance += up_count
                    sectors.append({"name": name, "change_pct": chg_pct})
                except (ValueError, IndexError):
                    continue

            # 获取A股总数来估算下跌家数
            total_url = "https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeStockCount?node=hs_a"
            total_r = requests.get(total_url, headers=headers, timeout=10)
            total_count = int(re.search(r"\d+", total_r.text).group()) if total_r.ok else 5500
            total_decline = max(total_count - total_advance, 0)

            # 板块按涨跌幅排序取前10
            sectors.sort(key=lambda x: x["change_pct"], reverse=True)
            sector_rankings = sectors[:10]

            return MarketBreadth(
                timestamp=datetime.now(),
                advance_count=total_advance,
                decline_count=total_decline,
                advance_decline_ratio=round(total_advance / total_decline, 2)
                if total_decline > 0
                else 99.0,
                sector_rankings=sector_rankings,
                north_bound_flow=0.0,  # 北向资金需东方财富，暂不可用
                vix=DEFAULT_VIX,
            )
        except Exception as e:
            logger.warning(f"get_market_breadth failed: {e}")
            return None

    def get_correlated_assets(self) -> Optional[CorrelatedAssets]:
        """获取关联资产数据"""
        try:
            from datetime import datetime
            import akshare as ak

            try:
                a50_df = ak.stock_zh_index_daily(symbol="sh000001")
                a50_change = (
                    float(a50_df["close"].pct_change().iloc[-1] * 100)
                    if not a50_df.empty
                    else 0.0
                )
            except Exception:
                a50_change = 0.0

            try:
                usdcnh_df = ak.currency_usdt_cny_hist()
                usdcnh = (
                    float(usdcnh_df["中行折算价"].iloc[-1])
                    if not usdcnh_df.empty
                    else DEFAULT_USDCNH
                )
            except Exception:
                usdcnh = DEFAULT_USDCNH

            try:
                dxy_df = ak.currency_usdkline()
                dxy = (
                    float(dxy_df["close"].iloc[-1]) if not dxy_df.empty else DEFAULT_DXY
                )
            except Exception:
                dxy = DEFAULT_DXY

            return CorrelatedAssets(
                timestamp=datetime.now(),
                a50_future=0.0,
                a50_change_pct=a50_change,
                usdcnh=usdcnh,
                dxy=dxy,
            )
        except Exception as e:
            logger.warning(f"get_correlated_assets failed: {e}")
            return None

    def get_minute_kline(
        self, code: str, frequency: str = "5", days: int = 5
    ) -> List[StockKLine]:
        """获取分钟K线数据"""
        try:
            import akshare as ak
            from datetime import datetime, timedelta

            if not code.startswith(("SH", "SZ")):
                if code.startswith("6"):
                    code = f"SH{code}"
                else:
                    code = f"SZ{code}"

            freq_map = {"1": "1", "5": "5", "15": "15", "30": "30", "60": "60"}
            freq = freq_map.get(frequency, "5")

            end_date = datetime.now().strftime("%Y%m%d %H:%M:%S")
            start_date = (datetime.now() - timedelta(days=days)).strftime(
                "%Y%m%d %H:%M:%S"
            )

            df = ak.stock_zh_a_hist_min_em(
                symbol=code,
                period=freq,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",
            )

            if df is None or df.empty:
                return []

            result = []
            for _, row in df.iterrows():
                try:
                    result.append(
                        StockKLine(
                            code=code,
                            date=str(row["时间"]),
                            open=float(row["开盘"]),
                            high=float(row["最高"]),
                            low=float(row["最低"]),
                            close=float(row["收盘"]),
                            volume=int(row["成交量"]),
                            amount=float(row.get("成交额", 0)),
                            change_pct=float(row.get("涨跌幅", 0)),
                        )
                    )
                except Exception:
                    continue
            return result
        except Exception as e:
            logger.warning(f"get_minute_kline({code}, {frequency}) failed: {e}")
            return []
