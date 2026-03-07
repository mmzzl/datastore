"""
AKShare股票数据客户端 - 重构版本
提供高效的股票数据获取、技术指标计算和市场分析功能
"""

import akshare as ak
import pandas as pd
import baostock as bs
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from functools import lru_cache
import logging
import time
import requests
import os
from pathlib import Path

from ..core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class StockDataConfig:
    """股票数据配置"""
    csv_file: str = 'stock_zh_a_daily.csv'
    spot_csv_file: str = 'stock_zh_a_spot.csv'
    default_date: str = '2026-03-06'
    api_timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 2
    historical_data_days: int = 60
    technical_indicator_threshold: int = 6000


class DataCache:
    """数据缓存管理"""
    
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str) -> Optional[pd.DataFrame]:
        """获取缓存数据"""
        return self._cache.get(key)
    
    def set(self, key: str, data: pd.DataFrame) -> None:
        """设置缓存数据"""
        self._cache[key] = data
    
    def clear(self) -> None:
        """清空缓存"""
        self._cache.clear()
    
    def has(self, key: str) -> bool:
        """检查缓存是否存在"""
        return key in self._cache


def retry_on_failure(max_retries: int = 3, delay: int = 2):
    """失败重试装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"{func.__name__} attempt {attempt + 1} failed: {e}, retrying...")
                        time.sleep(delay * (attempt + 1))
                    else:
                        logger.error(f"{func.__name__} failed after {max_retries} attempts")
                        raise last_exception
        return wrapper
    return decorator


class StockSymbolConverter:
    """股票代码格式转换工具"""
    
    @staticmethod
    def to_baostock_format(symbol: str) -> str:
        """转换为baostock格式"""
        symbol_upper = symbol.upper()
        
        if symbol_upper.startswith('SH'):
            return f"sh.{symbol_upper[2:]}"
        elif symbol_upper.startswith('SZ'):
            return f"sz.{symbol_upper[2:]}"
        elif symbol_upper.startswith('BJ'):
            return f"bj.{symbol_upper[2:]}"
        else:
            if len(symbol) == 6:
                if symbol.startswith('6'):
                    return f"sh.{symbol}"
                elif symbol.startswith('0') or symbol.startswith('3'):
                    return f"sz.{symbol}"
                elif symbol.startswith('8') or symbol.startswith('4'):
                    return f"bj.{symbol}"
            return symbol
    
    @staticmethod
    def to_industry_format(symbol: str) -> str:
        """转换为行业数据格式"""
        return f"sh.{symbol[2:].lower()}" if symbol.startswith('SH') else f"sz.{symbol[2:].lower()}"


class TechnicalIndicators:
    """技术指标计算器"""
    
    @staticmethod
    def calculate_ma(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
        """计算移动平均线"""
        if 'close' not in df.columns:
            logger.warning("缺少close列，无法计算MA")
            return df
        
        column_name = f'ma{window}'
        if column_name in df.columns:
            return df
        
        symbol_counts = df.groupby('symbol').size()
        valid_symbols = symbol_counts[symbol_counts >= window].index
        
        if len(valid_symbols) == 0:
            logger.warning(f"没有股票有足够的数据（{len(df)} 条），无法计算 MA{window}")
            df[column_name] = None
            return df
        
        logger.info(f"计算MA{window}: 总数据{len(df)}条, 股票数{len(symbol_counts)}只, 有效股票{len(valid_symbols)}只")
        
        df[column_name] = df.groupby('symbol')['close'].transform(
            lambda x: x.rolling(window=window, min_periods=window).mean() if len(x) >= window else None
        )
        logger.info(f"MA{window}计算完成")
        return df
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """计算RSI指标"""
        if 'close' not in df.columns or 'rsi' in df.columns:
            return df
        
        symbol_counts = df.groupby('symbol').size()
        valid_symbols = symbol_counts[symbol_counts >= window].index
        
        if len(valid_symbols) == 0:
            logger.warning(f"没有股票有足够的数据（{len(df)} 条），无法计算 RSI")
            df['rsi'] = None
            return df
        
        def rsi_series(series: pd.Series, period: int = 14) -> pd.Series:
            """计算RSI序列"""
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss.replace(0, float('inf'))
            return 100 - (100 / (1 + rs))
        
        df['rsi'] = df.groupby('symbol')['close'].transform(
            lambda x: rsi_series(x, period=window) if len(x) >= window else None
        )
        return df
    
    @staticmethod
    def calculate_amplitude(df: pd.DataFrame) -> pd.DataFrame:
        """计算振幅"""
        if 'high' not in df.columns or 'low' not in df.columns:
            return df
        
        if 'amplitude' in df.columns:
            return df
        
        df['amplitude'] = ((df['high'] - df['low']) / df['low']) * 100
        return df
    
    @classmethod
    def calculate_all(cls, df: pd.DataFrame, ma_windows: List[int] = None, rsi_window: int = 14) -> pd.DataFrame:
        """计算所有技术指标"""
        if ma_windows is None:
            ma_windows = [5, 10]
        
        df = cls.calculate_amplitude(df)
        for window in ma_windows:
            df = cls.calculate_ma(df, window)
        df = cls.calculate_rsi(df, rsi_window)
        
        return df


class AkshareClient:
    """AKShare股票数据客户端"""
    
    def __init__(self, config: StockDataConfig = None):
        self.config = config or StockDataConfig()
        self.cache = DataCache()
        self.data: Optional[pd.DataFrame] = None
        self.historical_data: Optional[pd.DataFrame] = None
        self._indicators_calculated = False
        
        # 初始化时加载数据
        self.stock_zh_a_spot_df = self.load_data()
    
    @retry_on_failure(max_retries=3, delay=2)
    def load_data(self) -> pd.DataFrame:
        """加载股票数据"""
        try:
            logger.info("从接口获取股票数据...")
            today_date = self.config.default_date
            api_url = f"{settings.after_market_kline_api_url}/stock/kline/all/{today_date}?limit=10000"
            
            df = self._fetch_data_from_api(api_url)
            
            if not df.empty:
                df = self._add_stock_names(df)
                df = self._ensure_date_format(df)
                self._save_data_to_file(df, self.config.csv_file)
                self.data = df
                logger.info(f"成功加载 {len(df)} 条股票数据")
                return df
            
            # 如果API失败，尝试从本地文件加载
            return self._load_data_from_file(self.config.csv_file)
            
        except Exception as e:
            logger.error(f"加载股票数据失败: {e}")
            return self._load_data_from_file(self.config.csv_file)
    
    def _fetch_data_from_api(self, api_url: str) -> pd.DataFrame:
        """从API获取数据"""
        try:
            response = requests.get(api_url, timeout=self.config.api_timeout, verify=False)
            response.raise_for_status()
            api_data = response.json()
            
            if 'data' not in api_data or not api_data['data']:
                logger.warning("接口返回数据为空")
                return pd.DataFrame()
            
            df = pd.DataFrame(api_data['data'])
            logger.info(f"从接口获取到 {len(df)} 条数据")
            
            # 重命名列
            column_mapping = {
                'code': 'symbol',
                'pct_chg': 'change_pct',
                'turnover': 'turnover_rate'
            }
            df = df.rename(columns=column_mapping)
            return df
            
        except requests.RequestException as e:
            logger.error(f"从接口获取数据失败: {e}")
            return pd.DataFrame()
    
    def _add_stock_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加股票名称"""
        if not os.path.exists(self.config.spot_csv_file):
            logger.warning(f"{self.config.spot_csv_file} 文件不存在")
            return df
        
        try:
            logger.info(f"从 {self.config.spot_csv_file} 读取股票名称...")
            stock_list_df = pd.read_csv(self.config.spot_csv_file)
            
            if 'symbol' in stock_list_df.columns and 'name' in stock_list_df.columns:
                symbol_name_map = dict(zip(stock_list_df['symbol'], stock_list_df['name']))
                df['name'] = df['symbol'].map(symbol_name_map)
                matched_count = df['name'].notna().sum()
                logger.info(f"成功添加股票名称，匹配到 {matched_count} 只股票")
            else:
                logger.warning(f"{self.config.spot_csv_file} 文件格式不正确")
        except Exception as e:
            logger.error(f"读取股票名称失败: {e}")
        
        return df
    
    def _ensure_date_format(self, df: pd.DataFrame) -> pd.DataFrame:
        """确保日期格式正确"""
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        return df
    
    def _save_data_to_file(self, df: pd.DataFrame, filename: str) -> None:
        """保存数据到文件"""
        try:
            df.to_csv(filename, index=False)
            logger.info(f"数据已保存到 {filename}")
        except Exception as e:
            logger.error(f"保存数据到文件失败: {e}")
    
    def _load_data_from_file(self, filename: str) -> pd.DataFrame:
        """从文件加载数据"""
        if not os.path.exists(filename):
            logger.error(f"本地文件 {filename} 不存在")
            return pd.DataFrame()
        
        try:
            logger.info(f"从本地文件 {filename} 加载数据")
            df = pd.read_csv(filename)
            df = self._ensure_date_format(df)
            self.data = df
            return df
        except Exception as e:
            logger.error(f"从文件加载数据失败: {e}")
            return pd.DataFrame()
    
    def load_historical_data(self, days: int = None) -> pd.DataFrame:
        """加载历史数据用于计算技术指标"""
        days = days or self.config.historical_data_days
        
        if self.historical_data is not None:
            logger.info(f"使用缓存的历史数据，共 {len(self.historical_data)} 条")
            return self.historical_data
        
        logger.info(f"从 API 获取历史数据（最近 {days} 天）...")
        
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            api_df = self.load_kline_data_from_api(start_date, end_date)
            
            if not api_df.empty:
                self.historical_data = api_df
                self._log_historical_data_stats(api_df)
                return api_df
            else:
                logger.warning("获取历史数据失败")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
            return pd.DataFrame()
    
    def _log_historical_data_stats(self, df: pd.DataFrame) -> None:
        """记录历史数据统计信息"""
        symbol_counts = df.groupby('symbol').size()
        logger.info(f"成功获取历史数据，共 {len(df)} 条")
        logger.info(f"股票数量: {len(symbol_counts)}")
        logger.info(f"平均每只股票数据量: {len(df) / len(symbol_counts):.1f} 条")
        
        count_ge_20 = (symbol_counts >= 20).sum()
        count_ge_14 = (symbol_counts >= 14).sum()
        
        logger.info(f"数据量 >= 20的股票: {count_ge_20} 只")
        logger.info(f"数据量 >= 14的股票: {count_ge_14} 只")
        logger.info(f"数据量分布: 最小{symbol_counts.min()}条, 最大{symbol_counts.max()}条, 中位数{symbol_counts.median():.1f}条")
    
    @retry_on_failure(max_retries=3, delay=2)
    def load_kline_data_from_api(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """从 API 接口加载 K 线数据"""
        try:
            base_url = settings.after_market_kline_api_url.rstrip('/')
            api_url = f"{base_url}/stock/klines"
            
            params = {}
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            
            logger.info(f"从 API 获取 K 线数据: {api_url}")
            logger.info(f"请求参数: {params}")
            
            response = requests.get(api_url, params=params, timeout=300, verify=False)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('success') and result.get('data'):
                df = self._process_kline_data(result['data'])
                logger.info(f"从 API 获取到 {len(df)} 条 K 线数据")
                return df
            else:
                logger.warning(f"API 返回数据为空: {result.get('message', '未知错误')}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"从 API 获取 K 线数据失败: {e}")
            return pd.DataFrame()
    
    def _process_kline_data(self, data: List[Dict]) -> pd.DataFrame:
        """处理K线数据"""
        df = pd.DataFrame(data)
        
        # 转换日期格式
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        
        # 转换数值类型
        numeric_columns = ['open', 'close', 'high', 'low', 'volume', 'amount', 'pct_chg', 'amplitude', 'turnover']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 添加 symbol 列
        if 'code' in df.columns and 'symbol' not in df.columns:
            df['symbol'] = df['code']
        
        return df
    
    def _filter_data_by_date(self, df: pd.DataFrame, date: str) -> pd.DataFrame:
        """按日期过滤数据并去重"""
        if df.empty:
            return df
        
        # 匹配日期
        df_filtered = df[df['date'].astype(str).str[:10] == date].copy()
        
        if df_filtered.empty:
            return df_filtered
        
        # 去重：每个股票只保留一条记录
        df_filtered = df_filtered.drop_duplicates(subset=['symbol'], keep='first')
        
        return df_filtered
    
    def _ensure_indicators_calculated(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """确保技术指标已计算"""
        if df is None:
            df = self.data
        
        if df is None or df.empty:
            return df
        
        if not self._indicators_calculated:
            logger.info("正在计算指标...")
            df = TechnicalIndicators.calculate_all(df)
            self._indicators_calculated = True
            logger.info("指标计算完成")
        
        return df
    
    def get_latest_date(self) -> Optional[str]:
        """获取最新日期"""
        if self.data is None or 'date' not in self.data.columns:
            return None
        return str(self.data['date'].max())[:10]
    
    def get_industry_data(self, date: str = None) -> pd.DataFrame:
        """获取行业分类数据"""
        try:
            lg = bs.login()
            if lg.error_code != '0':
                logger.error(f"baostock login failed: {lg.error_msg}")
                return pd.DataFrame()
            
            rs = bs.query_stock_industry()
            bs.logout()
            
            if rs.error_code == '0' and len(rs.data) > 0:
                return pd.DataFrame(rs.data, columns=rs.fields)
            return pd.DataFrame()
        except Exception as e:
            logger.error(f"获取行业数据失败: {e}")
            return pd.DataFrame()
    
    def get_stock_history_from_baostock(self, symbol: str, days: int = 60) -> pd.DataFrame:
        """从 baostock 获取股票历史数据"""
        try:
            lg = bs.login()
            if lg.error_code != '0':
                logger.error(f"baostock login failed: {lg.error_msg}")
                return pd.DataFrame()
            
            bs_symbol = StockSymbolConverter.to_baostock_format(symbol)
            logger.debug(f"转换股票代码: {symbol} -> {bs_symbol}")
            
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            rs = bs.query_history_k_data_plus(
                code=bs_symbol,
                fields="date,code,open,high,low,close,volume,amount",
                start_date=start_date,
                end_date=end_date,
                frequency="d",
                adjustflag="3"
            )
            bs.logout()
            
            if rs.error_code == '0' and len(rs.data) > 0:
                df = pd.DataFrame(rs.data, columns=rs.fields)
                df['symbol'] = symbol
                df['date'] = pd.to_datetime(df['date'])
                logger.info(f"从 baostock 获取到 {symbol} 的 {len(df)} 条历史数据")
                return df
            else:
                logger.warning(f"baostock 返回数据为空: {rs.error_msg}, 股票代码: {bs_symbol}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"从 baostock 获取历史数据失败: {e}")
            return pd.DataFrame()
    
    def analyze_market_overview(self, date: str = None) -> Dict[str, Union[int, float, str]]:
        """维度1: 大盘与市场环境"""
        date = date or self.get_latest_date()
        
        if not date:
            return {"error": "无法获取日期"}
        
        df = self._filter_data_by_date(self.data, date)
        
        if df.empty:
            return {"error": "No data for this date"}
        
        # 计算统计数据
        up_count = len(df[df['change_pct'] > 0])
        down_count = len(df[df['change_pct'] < 0])
        flat_count = len(df[df['change_pct'] == 0])
        avg_change = df['change_pct'].mean()
        limit_up = len(df[df['change_pct'] >= 9.9])
        limit_down = len(df[df['change_pct'] <= -9.9])
        
        return {
            "date": date,
            "total_stocks": len(df),
            "up_count": up_count,
            "down_count": down_count,
            "flat_count": flat_count,
            "avg_change_pct": round(avg_change, 2),
            "limit_up": limit_up,
            "limit_down": limit_down,
            "market_sentiment": self._judge_market_sentiment(up_count, down_count)
        }
    
    def _judge_market_sentiment(self, up_count: int, down_count: int) -> str:
        """判断市场情绪"""
        total = up_count + down_count
        if total == 0:
            return "无数据"
        
        up_ratio = up_count / total
        
        sentiment_map = {
            (0.7, 1.0): "普涨",
            (0.5, 0.7): "偏涨",
            (0.3, 0.5): "分化",
            (0.1, 0.3): "偏跌",
            (0.0, 0.1): "普跌"
        }
        
        for (lower, upper), sentiment in sentiment_map.items():
            if lower <= up_ratio < upper:
                return sentiment
        
        return "普跌"
    
    def analyze_sector_performance(self, date: str = None, top_n: int = 20) -> Dict:
        """维度2: 板块热点与轮动"""
        date = date or self.get_latest_date()
        
        if not date:
            return {"error": "无法获取日期"}
        
        df = self._filter_data_by_date(self.data, date)
        
        if df.empty:
            return {"error": "No data for this date"}
        
        # 获取行业分类
        industry_df = self.get_industry_data(date)
        
        if industry_df.empty:
            return {"error": "Failed to get industry data"}
        
        # 转换股票代码格式
        df['code'] = df['symbol'].apply(StockSymbolConverter.to_industry_format)
        
        # 合并数据
        merged_df = pd.merge(df, industry_df[['code', 'industry']], on='code', how='left')
        
        # 过滤掉没有行业分类的股票
        merged_df = merged_df[merged_df['industry'].notna() & (merged_df['industry'] != '')]
        
        if merged_df.empty:
            return {"error": "No industry data available"}
        
        # 按行业分组统计
        sector_stats = merged_df.groupby('industry').agg({
            'change_pct': 'mean',
            'symbol': 'count'
        }).reset_index()
        sector_stats.columns = ['industry', 'avg_change_pct', 'stock_count']
        
        # 排序
        sector_stats = sector_stats.sort_values('avg_change_pct', ascending=False)
        
        return {
            "date": date,
            "total_sectors": len(sector_stats),
            "top_gainers": sector_stats.head(top_n).to_dict('records'),
            "top_losers": sector_stats.sort_values('avg_change_pct', ascending=True).head(top_n).to_dict('records')
        }
    
    def analyze_stock_performance(self, date: str = None, top_n: int = 20) -> Dict:
        """维度4: 个股表现与活跃度"""
        date = date or self.get_latest_date()
        
        if not date:
            return {"error": "无法获取日期"}
        
        df = self._filter_data_by_date(self.data, date)
        
        if df.empty:
            return {"error": "No data for this date"}
        
        # 计算各种排行榜
        columns = ['symbol', 'change_pct', 'amplitude', 'volume', 'amount']
        
        return {
            "date": date,
            "top_gainers": df.nlargest(top_n, 'change_pct')[columns].to_dict('records'),
            "top_losers": df.nsmallest(top_n, 'change_pct')[columns].to_dict('records'),
            "top_amplitude": df.nlargest(top_n, 'amplitude')[columns].to_dict('records'),
            "top_amount": df.nlargest(top_n, 'amount')[columns].to_dict('records')
        }
    
    def analyze_technical_signals(self, date: str = None, top_n: int = 20) -> Dict:
        """维度6: 技术信号与趋势"""
        date = date or self.get_latest_date()
        
        if not date:
            return {"error": "无法获取日期"}
        
        logger.info(f"开始分析技术信号，日期: {date}")
        
        # 检查数据量，决定是否需要加载历史数据
        if len(self.data) < self.config.technical_indicator_threshold:
            logger.warning(f"当前数据量不足（{len(self.data)} 条），加载历史数据计算技术指标")
            df = self._load_and_calculate_historical_indicators(date)
        else:
            logger.info(f"当前数据量充足（{len(self.data)} 条），使用当前数据计算技术指标")
            df = self._calculate_current_data_indicators(date)
        
        if df is None or df.empty:
            return self._get_empty_technical_signals(date, "数据量不足或加载失败")
        
        # 检查技术指标列
        if not all(col in df.columns for col in ['ma5', 'ma10', 'rsi']):
            return self._get_empty_technical_signals(date, "技术指标计算失败，缺少必要的列")
        
        # 过滤有效数据
        df_valid = df.dropna(subset=['ma5', 'ma10', 'rsi'])
        
        if df_valid.empty:
            return self._get_empty_technical_signals(date, f"没有有效技术指标数据（有效数据: {len(df_valid)} 条）")
        
        # 计算技术信号
        signals = self._calculate_technical_signals(df_valid, top_n)
        
        logger.info(f"技术信号统计: 金叉{signals['golden_cross_count']}只, 超买{signals['overbought_count']}只, 超卖{signals['oversold_count']}只")
        
        return signals
    
    def _load_and_calculate_historical_indicators(self, date: str) -> Optional[pd.DataFrame]:
        """加载历史数据并计算指标"""
        api_df = self.load_historical_data()
        
        if api_df.empty:
            return None
        
        # 过滤日期
        api_df = api_df[api_df['date'].astype(str).str[:10] <= date].copy()
        logger.info(f"过滤后历史数据，共 {len(api_df)} 条（日期 <= {date}）")
        
        if not api_df.empty:
            min_date = api_df['date'].min()
            max_date = api_df['date'].max()
            logger.info(f"历史数据日期范围: {min_date} ~ {max_date}")
        
        # 计算技术指标
        api_df = TechnicalIndicators.calculate_all(api_df)
        
        # 匹配指定日期的数据
        df_date = self._filter_data_by_date(api_df, date)
        logger.info(f"使用历史数据计算技术指标，匹配到 {len(df_date)} 条数据")
        
        return df_date
    
    def _calculate_current_data_indicators(self, date: str) -> Optional[pd.DataFrame]:
        """使用当前数据计算指标"""
        self._ensure_indicators_calculated()
        df_date = self._filter_data_by_date(self.data, date)
        
        if df_date.empty:
            logger.error(f"未找到日期 {date} 的数据")
            return None
        
        logger.info(f"使用当前数据计算技术指标，匹配到 {len(df_date)} 条数据")
        return df_date
    
    def _calculate_technical_signals(self, df: pd.DataFrame, top_n: int) -> Dict:
        """计算技术信号"""
        # 金叉（MA5 > MA10）
        golden_cross = df[df['ma5'] > df['ma10']][['symbol', 'close', 'ma5', 'ma10']]
        
        # 超买（RSI > 80）
        overbought = df[df['rsi'] > 80][['symbol', 'close', 'rsi']]
        
        # 超卖（RSI < 20）
        oversold = df[df['rsi'] < 20][['symbol', 'close', 'rsi']]
        
        return {
            "date": str(df['date'].iloc[0])[:10] if 'date' in df.columns else "",
            "golden_cross_count": len(golden_cross),
            "golden_cross": golden_cross.head(top_n).to_dict('records'),
            "overbought_count": len(overbought),
            "overbought": overbought.head(top_n).to_dict('records'),
            "oversold_count": len(oversold),
            "oversold": oversold.head(top_n).to_dict('records')
        }
    
    def _get_empty_technical_signals(self, date: str, warning: str) -> Dict:
        """获取空的技术信号结果"""
        return {
            "date": date,
            "warning": warning,
            "golden_cross_count": 0,
            "golden_cross": [],
            "overbought_count": 0,
            "overbought": [],
            "oversold_count": 0,
            "oversold": []
        }
    
    def generate_daily_brief(self, date: str = None) -> Dict:
        """生成完整的每日简报"""
        date = date or self.get_latest_date()
        date = self.config.default_date  # 使用配置的默认日期
        
        logger.info(f"生成每日简报，日期: {date}")
        
        return {
            "date": date,
            "market_overview": self.analyze_market_overview(date),
            "sector_performance": self.analyze_sector_performance(date),
            "stock_performance": self.analyze_stock_performance(date),
            "technical_signals": self.analyze_technical_signals(date)
        }
    
    def format_brief_for_dingtalk(self, date: str = None) -> str:
        """格式化简报为钉钉机器人消息格式"""
        brief = self.generate_daily_brief(date)
        
        # 收集需要的股票代码
        needed_symbols = self._collect_needed_symbols(brief)
        
        # 加载股票名称
        stock_names = self._load_stock_names_for_symbols(list(needed_symbols))
        
        # 生成格式化消息
        lines = self._build_dingtalk_message(brief, stock_names)
        
        return "\n".join(lines)
    
    def _collect_needed_symbols(self, brief: Dict) -> set:
        """收集需要加载名称的股票代码"""
        needed_symbols = set()
        
        # 从个股表现中提取
        if 'stock_performance' in brief and 'error' not in brief['stock_performance']:
            for category in ['top_gainers', 'top_losers', 'top_amplitude']:
                for stock in brief['stock_performance'].get(category, [])[:5]:
                    needed_symbols.add(stock['symbol'])
        
        # 从技术信号中提取
        if 'technical_signals' in brief and 'error' not in brief['technical_signals']:
            for category in ['golden_cross', 'overbought', 'oversold']:
                for stock in brief['technical_signals'].get(category, [])[:3]:
                    needed_symbols.add(stock['symbol'])
        
        return needed_symbols
    
    def _load_stock_names_for_symbols(self, symbols: List[str]) -> Dict[str, str]:
        """加载股票代码对应的名称"""
        if not symbols:
            return {}
        
        try:
            stock_names = {}
            for symbol in symbols:
                if self.data is not None and not self.data.empty:
                    stock_row = self.data[self.data['symbol'] == symbol]
                    if not stock_row.empty:
                        stock_names[symbol] = stock_row.iloc[0]['name']
                    else:
                        stock_names[symbol] = symbol
                else:
                    stock_names[symbol] = symbol
            
            return stock_names
        except Exception as e:
            logger.error(f"加载股票名称失败: {e}")
            return {symbol: symbol for symbol in symbols}
    
    def _build_dingtalk_message(self, brief: Dict, stock_names: Dict[str, str]) -> List[str]:
        """构建钉钉消息"""
        lines = []
        lines.append(f"## 📊 每日收盘简报 - {brief['date']}")
        lines.append("")
        
        # 维度1: 大盘与市场环境
        self._add_market_overview_section(lines, brief.get('market_overview', {}))
        
        # 维度2: 板块热点与轮动
        self._add_sector_performance_section(lines, brief.get('sector_performance', {}))
        
        # 维度4: 个股表现与活跃度
        self._add_stock_performance_section(lines, brief.get('stock_performance', {}), stock_names)
        
        # 维度6: 技术信号与趋势
        self._add_technical_signals_section(lines, brief.get('technical_signals', {}), stock_names)
        
        return lines
    
    def _add_market_overview_section(self, lines: List[str], market: Dict) -> None:
        """添加大盘概览部分"""
        if 'error' in market:
            return
        
        lines.append("### 📈 大盘与市场环境")
        lines.append("")
        
        sentiment_emoji = {
            "普涨": "🚀",
            "偏涨": "📈",
            "分化": "⚖️",
            "偏跌": "📉",
            "普跌": "🔻"
        }
        emoji = sentiment_emoji.get(market.get('market_sentiment', "📊"), "📊")
        
        lines.append(f"- 总股票数: **{market.get('total_stocks', 0)}**")
        lines.append(f"- 上涨: **{market.get('up_count', 0)}** | 下跌: **{market.get('down_count', 0)}** | 平盘: **{market.get('flat_count', 0)}**")
        
        avg_change = market.get('avg_change_pct', 0)
        avg_color = "🔴" if avg_change < 0 else "🟢"
        lines.append(f"- 平均涨跌幅: {avg_color} **{avg_change:.2f}%**")
        
        lines.append(f"- 涨停: **{market.get('limit_up', 0)}** | 跌停: **{market.get('limit_down', 0)}**")
        lines.append(f"- 市场情绪: **{emoji} {market.get('market_sentiment', '未知')}**")
        lines.append("")
    
    def _add_sector_performance_section(self, lines: List[str], sector: Dict) -> None:
        """添加板块表现部分"""
        if 'error' in sector:
            return
        
        lines.append("### 🏢 板块热点与轮动")
        lines.append("")
        lines.append(f"**行业板块数: {sector.get('total_sectors', 0)}**")
        lines.append("")
        
        lines.append("**📈 涨幅榜 TOP5**")
        for i, sec in enumerate(sector.get('top_gainers', [])[:5], 1):
            pct = sec.get('avg_change_pct', 0)
            emoji = "🟢" if pct > 0 else "🔴"
            lines.append(f"{i}. {sec.get('industry', '未知')} {emoji} **{pct:.2f}%** ({int(sec.get('stock_count', 0))}只)")
        
        lines.append("")
        lines.append("**📉 跌幅榜 TOP5**")
        for i, sec in enumerate(sector.get('top_losers', [])[:5], 1):
            pct = sec.get('avg_change_pct', 0)
            emoji = "🔴" if pct < 0 else "🟢"
            lines.append(f"{i}. {sec.get('industry', '未知')} {emoji} **{pct:.2f}%** ({int(sec.get('stock_count', 0))}只)")
        lines.append("")
    
    def _add_stock_performance_section(self, lines: List[str], perf: Dict, stock_names: Dict[str, str]) -> None:
        """添加个股表现部分"""
        if 'error' in perf:
            return
        
        lines.append("### 💹 个股表现与活跃度")
        lines.append("")
        
        # 涨幅榜
        lines.append("**🚀 涨幅榜 TOP5**")
        for i, stock in enumerate(perf.get('top_gainers', [])[:5], 1):
            pct = stock.get('change_pct', 0)
            emoji = "🟢" if pct > 0 else "🔴"
            symbol = stock.get('symbol', '')
            name = stock_names.get(symbol, symbol)
            lines.append(f"{i}. {name}({symbol}) {emoji} **{pct:.2f}%** | 振幅: {stock.get('amplitude', 0):.2f}%")
        
        # 跌幅榜
        lines.append("")
        lines.append("**🔻 跌幅榜 TOP5**")
        for i, stock in enumerate(perf.get('top_losers', [])[:5], 1):
            pct = stock.get('change_pct', 0)
            emoji = "🔴" if pct < 0 else "🟢"
            symbol = stock.get('symbol', '')
            name = stock_names.get(symbol, symbol)
            lines.append(f"{i}. {name}({symbol}) {emoji} **{pct:.2f}%** | 振幅: {stock.get('amplitude', 0):.2f}%")
        
        # 振幅榜
        lines.append("")
        lines.append("**📊 振幅榜 TOP5**")
        for i, stock in enumerate(perf.get('top_amplitude', [])[:5], 1):
            pct = stock.get('change_pct', 0)
            emoji = "🟢" if pct > 0 else "🔴"
            symbol = stock.get('symbol', '')
            name = stock_names.get(symbol, symbol)
            lines.append(f"{i}. {name}({symbol}) 振幅: **{stock.get('amplitude', 0):.2f}%** | 涨跌: {emoji} {pct:.2f}%")
        lines.append("")
    
    def _add_technical_signals_section(self, lines: List[str], tech: Dict, stock_names: Dict[str, str]) -> None:
        """添加技术信号部分"""
        if 'error' in tech:
            return
        
        lines.append("### 📉 技术信号与趋势")
        lines.append("")
        
        if 'warning' in tech:
            lines.append(f"⚠️ {tech['warning']}")
            lines.append("")
            return
        
        lines.append(f"**MA5金叉MA10: {tech.get('golden_cross_count', 0)}只**")
        for stock in tech.get('golden_cross', [])[:3]:
            symbol = stock.get('symbol', '')
            name = stock_names.get(symbol, symbol)
            lines.append(f"  - {name}({symbol}): 收盘{stock.get('close', 0):.2f} | MA5:{stock.get('ma5', 0):.2f} | MA10:{stock.get('ma10', 0):.2f}")
        
        lines.append("")
        lines.append(f"**超买(RSI>80): {tech.get('overbought_count', 0)}只**")
        for stock in tech.get('overbought', [])[:3]:
            symbol = stock.get('symbol', '')
            name = stock_names.get(symbol, symbol)
            lines.append(f"  - {name}({symbol}): 收盘{stock.get('close', 0):.2f} | RSI:{stock.get('rsi', 0):.2f}")
        
        lines.append("")
        lines.append(f"**超卖(RSI<20): {tech.get('oversold_count', 0)}只**")
        for stock in tech.get('oversold', [])[:3]:
            symbol = stock.get('symbol', '')
            name = stock_names.get(symbol, symbol)
            lines.append(f"  - {name}({symbol}): 收盘{stock.get('close', 0):.2f} | RSI:{stock.get('rsi', 0):.2f}")
        lines.append("")
