import akshare as ak
import pandas as pd
import baostock as bs
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import time
import requests
import os
from ..core.config import settings

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries=3, delay=2):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"{func.__name__} attempt {attempt+1} failed: {e}, retrying...")
                        time.sleep(delay * (attempt + 1))
                    else:
                        raise
        return wrapper
    return decorator


class AkshareClient:
    def __init__(self):
        self.data = None
        self._indicators_calculated = False
        self.historical_data = None
        self.stock_zh_a_spot_df = self.load_data()
    
    def load_data(self):
        """加载股票数据"""
        csv_file = 'stock_zh_a_daily.csv'
        sp_csv_file = 'stock_zh_a_spot.csv'
        # today_date = datetime.now().strftime('%Y-%m-%d')
        today_date = '2026-03-06'
        try:
            # 从接口获取数据
            logger.info(f"从接口获取股票数据...")
            api_url = f"{settings.after_market_kline_api_url}/stock/kline/all/{today_date}?limit=10000"
            
            try:
                response = requests.get(api_url, timeout=30, verify=False)
                response.raise_for_status()
                api_data = response.json()
                
                if 'data' not in api_data or not api_data['data']:
                    logger.warning(f"接口返回数据为空")
                    return pd.DataFrame()
                
                # 转换为 DataFrame
                df = pd.DataFrame(api_data['data'])
                logger.info(f"从接口获取到 {len(df)} 条数据")
                
                # 重命名列以匹配现有格式
                column_mapping = {
                    'code': 'symbol',
                    'pct_chg': 'change_pct',
                    'turnover': 'turnover_rate'
                }
                df = df.rename(columns=column_mapping)
                
                # 从 stock_zh_a_spot.csv 获取股票名称
                if os.path.exists(sp_csv_file):
                    logger.info(f"从 {sp_csv_file} 读取股票名称...")
                    stock_list_df = pd.read_csv(sp_csv_file)
                    
                    # 检查文件中是否有必要的列
                    if 'symbol' in stock_list_df.columns and 'name' in stock_list_df.columns:
                        # 创建股票代码到名称的映射
                        symbol_name_map = dict(zip(stock_list_df['symbol'], stock_list_df['name']))
                        
                        # 添加股票名称
                        df['name'] = df['symbol'].map(symbol_name_map)
                        
                        logger.info(f"成功添加股票名称，匹配到 {df['name'].notna().sum()} 只股票")
                    else:
                        logger.warning(f"{sp_csv_file} 文件格式不正确")
                else:
                    logger.warning(f"{sp_csv_file} 文件不存在")
                
                # 确保日期格式正确
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                
                # 保存到文件
                df.to_csv(csv_file, index=False)
                logger.info(f"数据已保存到 {csv_file}")
                
                self.data = df
                return df
                
            except requests.RequestException as e:
                logger.error(f"从接口获取数据失败: {e}")
                
                # 如果接口失败，尝试从本地文件加载
                if os.path.exists(csv_file):
                    logger.info(f"从本地文件 {csv_file} 加载股票数据")
                    self.data = pd.read_csv(csv_file)
                    return self.data
                else:
                    logger.error(f"本地文件也不存在，无法加载数据")
                    return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"加载股票数据失败: {e}")
            return pd.DataFrame()
    
    def load_historical_data(self, days: int = 60):
        """加载历史数据用于计算技术指标"""
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
                
                # 统计每只股票的数据量
                symbol_counts = api_df.groupby('symbol').size()
                logger.info(f"成功获取历史数据，共 {len(api_df)} 条")
                logger.info(f"股票数量: {len(symbol_counts)}")
                logger.info(f"平均每只股票数据量: {len(api_df) / len(symbol_counts):.1f} 条")
                
                # 详细统计
                count_ge_20 = (symbol_counts >= 20).sum()
                count_ge_14 = (symbol_counts >= 14).sum()
                count_lt_20 = (symbol_counts < 20).sum()
                count_lt_14 = (symbol_counts < 14).sum()
                
                logger.info(f"数据量 >= 20的股票: {count_ge_20} 只")
                logger.info(f"数据量 >= 14的股票: {count_ge_14} 只")
                logger.info(f"数据量 < 20的股票: {count_lt_20} 只")
                logger.info(f"数据量 < 14的股票: {count_lt_14} 只")
                logger.info(f"数据量分布: 最小{symbol_counts.min()}条, 最大{symbol_counts.max()}条, 中位数{symbol_counts.median():.1f}条")
                
                # 显示部分股票的数据量
                logger.info(f"前10只股票的数据量: {symbol_counts.nlargest(10).to_dict()}")
                
                return api_df
            else:
                logger.warning(f"获取历史数据失败")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"加载历史数据失败: {e}")
            return pd.DataFrame()
    
    def calculate_change_pct(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """计算涨跌幅"""
        if df is None:
            df = self.data
        # 新的数据结构已经包含了 change_pct，不需要再计算
        return df
    
    def _ensure_indicators(self):
        """确保所有指标都已计算"""
        if not self._indicators_calculated:
            print("正在计算指标...")
            self.calculate_change_pct(self.data)
            self.calculate_amplitude(self.data)
            self.calculate_ma(5, self.data)
            self.calculate_ma(10, self.data)
            self.calculate_rsi(14, self.data)
            self._indicators_calculated = True
            print("指标计算完成")
    
    def calculate_amplitude(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """计算振幅"""
        if df is None:
            df = self.data
        if 'high' in df.columns and 'low' in df.columns and 'amplitude' not in df.columns:
            df['amplitude'] = ((df['high'] - df['low']) / df['low']) * 100
        return df
    
    def get_industry_data(self, date: str = None) -> pd.DataFrame:
        """获取行业分类数据"""
        lg = bs.login()
        if lg.error_code != '0':
            print(f"baostock login failed: {lg.error_msg}")
            return pd.DataFrame()
        
        if date is None:
            date = self.get_latest_date()
        
        # 获取行业分类
        rs = bs.query_stock_industry()
        bs.logout()
        
        if rs.error_code == '0' and len(rs.data) > 0:
            industry_df = pd.DataFrame(rs.data, columns=rs.fields)
            return industry_df
        return pd.DataFrame()
    
    def load_kline_data_from_api(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """从 API 接口加载 K 线数据"""
        try:
            import requests
            
            # 构建 API URL
            base_url = settings.after_market_kline_api_url.rstrip('/')
            api_url = f"{base_url}/stock/klines"
            
            # 构建请求参数
            params = {}
            if start_date:
                params['start_date'] = start_date
            if end_date:
                params['end_date'] = end_date
            
            # 发送请求
            logger.info(f"从 API 获取 K 线数据: {api_url}")
            logger.info(f"请求参数: {params}")
            logger.info(f"完整URL: {api_url}?{ '&'.join([f'{k}={v}' for k, v in params.items()])}")
            
            response = requests.get(api_url, params=params, timeout=300, verify=False)
            logger.info(f"响应状态码: {response.status_code}")
            response.raise_for_status()
            
            # 解析响应
            result = response.json()
            logger.info(f"响应内容: {str(result)[:200]}...")
            
            if result.get('success') and result.get('data'):
                # 转换为 DataFrame
                df = pd.DataFrame(result['data'])
                
                # 转换日期格式
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                
                # 转换数值类型
                numeric_columns = ['open', 'close', 'high', 'low', 'volume', 'amount', 'pct_chg', 'amplitude', 'turnover']
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # 添加 symbol 列（从 code 列转换）
                if 'code' in df.columns and 'symbol' not in df.columns:
                    df['symbol'] = df['code']
                
                logger.info(f"从 API 获取到 {len(df)} 条 K 线数据")
                return df
            else:
                logger.warning(f"API 返回数据为空: {result.get('message', '未知错误')}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"从 API 获取 K 线数据失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            return pd.DataFrame()
    
    def get_stock_history_from_baostock(self, symbol: str, days: int = 60) -> pd.DataFrame:
        """从 baostock 获取股票历史数据"""
        try:
            lg = bs.login()
            if lg.error_code != '0':
                logger.error(f"baostock login failed: {lg.error_msg}")
                return pd.DataFrame()
            
            # 转换股票代码格式
            # 处理各种可能的格式：SH600000, sh600000, 600000, SZ000001, sz000001, 000001
            symbol_upper = symbol.upper()
            
            if symbol_upper.startswith('SH'):
                bs_symbol = f"sh.{symbol_upper[2:]}"
            elif symbol_upper.startswith('SZ'):
                bs_symbol = f"sz.{symbol_upper[2:]}"
            elif symbol_upper.startswith('BJ'):
                bs_symbol = f"bj.{symbol_upper[2:]}"
            else:
                # 如果没有前缀，根据数字判断
                if len(symbol) == 6:
                    if symbol.startswith('6'):
                        bs_symbol = f"sh.{symbol}"
                    elif symbol.startswith('0') or symbol.startswith('3'):
                        bs_symbol = f"sz.{symbol}"
                    elif symbol.startswith('8') or symbol.startswith('4'):
                        bs_symbol = f"bj.{symbol}"
                    else:
                        bs_symbol = symbol
                else:
                    bs_symbol = symbol
            
            logger.debug(f"转换股票代码: {symbol} -> {bs_symbol}")
            
            # 获取最近 N 天的数据
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
    
    def analyze_sector_performance(self, date: str = None, top_n: int = 20) -> Dict:
        """维度2: 板块热点与轮动"""
        if date is None:
            date = self.get_latest_date()
        
        self._ensure_indicators()
        
        # 匹配日期（支持 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS 格式）
        df_date = self.data[self.data['date'].astype(str).str[:10] == date].copy()
        
        if df_date.empty:
            return {"error": "No data for this date"}
        
        # 去重：每个股票只保留一条记录
        df_date = df_date.drop_duplicates(subset=['symbol'], keep='first')
        
        # 获取行业分类
        industry_df = self.get_industry_data(date)
        
        if industry_df.empty:
            return {"error": "Failed to get industry data"}
        
        # 将股票代码转换为统一格式
        df_date['code'] = df_date['symbol'].apply(lambda x: f"sh.{x[2:].lower()}" if x.startswith('SH') else f"sz.{x[2:].lower()}")
        
        # 合并数据
        merged_df = pd.merge(df_date, industry_df[['code', 'industry']], on='code', how='left')
        
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
        
        # 涨幅榜
        top_gainers = sector_stats.head(top_n)
        
        # 跌幅榜
        top_losers = sector_stats.sort_values('avg_change_pct', ascending=True).head(top_n)
        
        return {
            "date": date,
            "total_sectors": len(sector_stats),
            "top_gainers": top_gainers.to_dict('records'),
            "top_losers": top_losers.to_dict('records')
        }
    
    def get_latest_date(self) -> str:
        """获取最新日期"""
        if 'date' in self.data.columns:
            return str(self.data['date'].max())[:10]
        return None
    
    def get_latest_trade_date(self) -> str:
        """获取最新交易日"""
        lg = bs.login()
        if lg.error_code != '0':
            print(f"baostock login failed: {lg.error_msg}")
            return None
        
        # 获取最近一个月的交易日历
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        rs = bs.query_trade_dates(start_date=start_date, end_date=end_date)
        bs.logout()
        
        if rs.error_code == '0' and len(rs.data) > 0:
            return rs.data[-1][0]  # 返回最新交易日
        return None
    
    def analyze_market_overview(self, date: str = None) -> Dict:
        """维度1: 大盘与市场环境"""
        if date is None:
            date = self.get_latest_date()
        
        self._ensure_indicators()
        
        # 匹配日期（支持 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS 格式）
        df_date = self.data[self.data['date'].astype(str).str[:10] == date].copy()
        
        if df_date.empty:
            return {"error": "No data for this date"}
        
        # 去重：每个股票只保留一条记录（按收盘价去重）
        df_date = df_date.drop_duplicates(subset=['symbol'], keep='first')
        
        # 计算涨跌家数
        up_count = len(df_date[df_date['change_pct'] > 0])
        down_count = len(df_date[df_date['change_pct'] < 0])
        flat_count = len(df_date[df_date['change_pct'] == 0])
        
        # 平均涨跌幅
        avg_change = df_date['change_pct'].mean()
        
        # 涨停跌停（假设涨跌幅 >= 9.9% 为涨停，<= -9.9% 为跌停）
        limit_up = len(df_date[df_date['change_pct'] >= 9.9])
        limit_down = len(df_date[df_date['change_pct'] <= -9.9])
        
        return {
            "date": date,
            "total_stocks": len(df_date),
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
        
        if up_ratio >= 0.7:
            return "普涨"
        elif up_ratio >= 0.5:
            return "偏涨"
        elif up_ratio >= 0.3:
            return "分化"
        elif up_ratio >= 0.1:
            return "偏跌"
        else:
            return "普跌"
    
    def analyze_stock_performance(self, date: str = None, top_n: int = 20) -> Dict:
        """维度4: 个股表现与活跃度"""
        if date is None:
            date = self.get_latest_date()
        
        self._ensure_indicators()
        
        # 匹配日期（支持 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS 格式）
        df_date = self.data[self.data['date'].astype(str).str[:10] == date].copy()
        
        if df_date.empty:
            return {"error": "No data for this date"}
        
        # 去重：每个股票只保留一条记录
        df_date = df_date.drop_duplicates(subset=['symbol'], keep='first')
        
        # 涨幅榜
        top_gainers = df_date.nlargest(top_n, 'change_pct')[['symbol', 'change_pct', 'amplitude', 'volume', 'amount']]
        
        # 跌幅榜
        top_losers = df_date.nsmallest(top_n, 'change_pct')[['symbol', 'change_pct', 'amplitude', 'volume', 'amount']]
        
        # 振幅榜
        top_amplitude = df_date.nlargest(top_n, 'amplitude')[['symbol', 'change_pct', 'amplitude', 'volume', 'amount']]
        
        # 成交额榜
        top_amount = df_date.nlargest(top_n, 'amount')[['symbol', 'change_pct', 'amplitude', 'volume', 'amount']]
        
        return {
            "date": date,
            "top_gainers": top_gainers.to_dict('records'),
            "top_losers": top_losers.to_dict('records'),
            "top_amplitude": top_amplitude.to_dict('records'),
            "top_amount": top_amount.to_dict('records')
        }
    
    def calculate_ma(self, window: int = 5, df: pd.DataFrame = None) -> pd.DataFrame:
        """计算移动平均线"""
        if df is None:
            df = self.data
        if 'close' in df.columns and f'ma{window}' not in df.columns:
            # 检查是否有足够的数据来计算MA
            # 按股票分组，检查每只股票是否有足够的数据
            symbol_counts = df.groupby('symbol').size()
            valid_symbols = symbol_counts[symbol_counts >= window].index
            
            logger.info(f"计算MA{window}: 总数据{len(df)}条, 股票数{len(symbol_counts)}只, 有效股票{len(valid_symbols)}只")
            
            if len(valid_symbols) == 0:
                logger.warning(f"没有股票有足够的数据（{len(df)} 条），无法计算 MA{window}")
                df[f'ma{window}'] = None
            else:
                # 只为有足够数据的股票计算MA
                df[f'ma{window}'] = df.groupby('symbol')['close'].transform(
                    lambda x: x.rolling(window=window, min_periods=window).mean() if len(x) >= window else None
                )
                logger.info(f"MA{window}计算完成，有效股票{len(valid_symbols)}只")
        return df
    
    def calculate_rsi(self, window: int = 14, df: pd.DataFrame = None) -> pd.DataFrame:
        """计算RSI指标"""
        if df is None:
            df = self.data
        if 'close' not in df.columns or 'rsi' in df.columns:
            return df
        
        # 按股票分组，检查每只股票是否有足够的数据
        symbol_counts = df.groupby('symbol').size()
        valid_symbols = symbol_counts[symbol_counts >= window].index
        
        if len(valid_symbols) == 0:
            logger.warning(f"没有股票有足够的数据（{len(df)} 条），无法计算 RSI")
            df['rsi'] = None
            return df
        
        def rsi_series(series, period=14):
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        
        # 只为有足够数据的股票计算RSI
        df['rsi'] = df.groupby('symbol')['close'].transform(
            lambda x: rsi_series(x, period=window) if len(x) >= window else None
        )
        return df
    
    def analyze_technical_signals(self, date: str = None, top_n: int = 20) -> Dict:
        """维度6: 技术信号与趋势"""
        if date is None:
            date = self.get_latest_date()
        
        logger.info(f"开始分析技术信号，日期: {date}")
        logger.info(f"当前数据量: {len(self.data)} 条")
        
        # 检查是否有足够的历史数据来计算技术指标
        # 如果当前数据只有一天，需要加载历史数据
        if len(self.data) < 6000:
            logger.warning(f"当前数据量不足（{len(self.data)} 条），加载历史数据计算技术指标")
            # 加载历史数据
            api_df = self.load_historical_data()
            if not api_df.empty:
                # 只保留匹配日期及其之前的数据
                api_df = api_df[api_df['date'].astype(str).str[:10] <= date].copy()
                logger.info(f"过滤后历史数据，共 {len(api_df)} 条（日期 <= {date}）")
                
                # 显示日期范围
                if not api_df.empty:
                    min_date = api_df['date'].min()
                    max_date = api_df['date'].max()
                    logger.info(f"历史数据日期范围: {min_date} ~ {max_date}")
                
                # 计算技术指标
                api_df = self.calculate_ma(5, api_df)
                api_df = self.calculate_ma(10, api_df)
                api_df = self.calculate_rsi(14, api_df)
                
                # 匹配指定日期的数据
                df_date = api_df[api_df['date'].astype(str).str[:10] == date].copy()
                df_date = df_date.drop_duplicates(subset=['symbol'], keep='first')
                
                logger.info(f"使用历史数据计算技术指标，匹配到 {len(df_date)} 条数据")
                
                # 检查技术指标列
                if 'ma5' in df_date.columns:
                    ma5_count = df_date['ma5'].notna().sum()
                    logger.info(f"匹配数据中MA5非空: {ma5_count} 条")
                if 'ma10' in df_date.columns:
                    ma10_count = df_date['ma10'].notna().sum()
                    logger.info(f"匹配数据中MA10非空: {ma10_count} 条")
                if 'rsi' in df_date.columns:
                    rsi_count = df_date['rsi'].notna().sum()
                    logger.info(f"匹配数据中RSI非空: {rsi_count} 条")
            else:
                logger.error(f"历史数据为空，无法计算技术指标")
                return {
                    "date": date,
                    "warning": "数据量不足，无法准确计算技术指标。获取历史数据失败。",
                    "golden_cross_count": 0,
                    "golden_cross": [],
                    "overbought_count": 0,
                    "overbought": [],
                    "oversold_count": 0,
                    "oversold": []
                }
        else:
            logger.info(f"当前数据量充足（{len(self.data)} 条），使用当前数据计算技术指标")
            # 使用当前数据
            self._ensure_indicators()
            
            # 匹配日期（支持 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS 格式）
            df_date = self.data[self.data['date'].astype(str).str[:10] == date].copy()
            
            if df_date.empty:
                logger.error(f"未找到日期 {date} 的数据")
                return {"error": "No data for this date"}
            
            # 去重：每个股票只保留一条记录
            df_date = df_date.drop_duplicates(subset=['symbol'], keep='first')
            
            logger.info(f"使用当前数据计算技术指标，匹配到 {len(df_date)} 条数据")
        
        # 检查是否有技术指标列
        if 'ma5' not in df_date.columns or 'ma10' not in df_date.columns or 'rsi' not in df_date.columns:
            logger.warning(f"技术指标列缺失，无法计算技术信号")
            return {
                "date": date,
                "warning": "技术指标计算失败，缺少必要的列（ma5, ma10, rsi）",
                "golden_cross_count": 0,
                "golden_cross": [],
                "overbought_count": 0,
                "overbought": [],
                "oversold_count": 0,
                "oversold": []
            }
        
        # 过滤掉技术指标为None的股票
        df_valid = df_date.dropna(subset=['ma5', 'ma10', 'rsi'])
        
        if df_valid.empty:
            logger.warning(f"没有有效技术指标数据（原始数据: {len(df_date)} 条，有效数据: {len(df_valid)} 条）")
            return {
                "date": date,
                "warning": f"没有足够的历史数据计算技术指标（有效数据: {len(df_valid)} 条）",
                "golden_cross_count": 0,
                "golden_cross": [],
                "overbought_count": 0,
                "overbought": [],
                "oversold_count": 0,
                "oversold": []
            }
        
        # 金叉（MA5 > MA10）
        golden_cross = df_valid[df_valid['ma5'] > df_valid['ma10']][['symbol', 'close', 'ma5', 'ma10']]
        
        # 超买（RSI > 80）
        overbought = df_valid[df_valid['rsi'] > 80][['symbol', 'close', 'rsi']]
        
        # 超卖（RSI < 20）
        oversold = df_valid[df_valid['rsi'] < 20][['symbol', 'close', 'rsi']]
        
        logger.info(f"技术信号统计: 金叉{len(golden_cross)}只, 超买{len(overbought)}只, 超卖{len(oversold)}只")
        
        return {
            "date": date,
            "golden_cross_count": len(golden_cross),
            "golden_cross": golden_cross.head(top_n).to_dict('records'),
            "overbought_count": len(overbought),
            "overbought": overbought.head(top_n).to_dict('records'),
            "oversold_count": len(oversold),
            "oversold": oversold.head(top_n).to_dict('records')
        }
        
    def generate_daily_brief(self, date: str = None) -> Dict:
        """生成完整的每日简报"""
        if date is None:
            date = self.get_latest_date()
        logger.info("date: %s", date)
        date = '2026-03-06'
        brief = {
            "date": date,
            "market_overview": self.analyze_market_overview(date),
            "sector_performance": self.analyze_sector_performance(date),
            "stock_performance": self.analyze_stock_performance(date),
            "technical_signals": self.analyze_technical_signals(date)
        }
        return brief
    
    def format_brief_for_dingtalk(self, date: str = None) -> str:
        """格式化简报为钉钉机器人消息格式"""
        brief = self.generate_daily_brief(date)
        # 加载需要的股票名称
        needed_symbols = set()
        
        # 从个股表现中提取
        if 'stock_performance' in brief and 'error' not in brief['stock_performance']:
            for stock in brief['stock_performance']['top_gainers'][:5]:
                needed_symbols.add(stock['symbol'])
            for stock in brief['stock_performance']['top_losers'][:5]:
                needed_symbols.add(stock['symbol'])
            for stock in brief['stock_performance']['top_amplitude'][:5]:
                needed_symbols.add(stock['symbol'])
        
        # 从技术信号中提取
        if 'technical_signals' in brief and 'error' not in brief['technical_signals']:
            for stock in brief['technical_signals']['golden_cross'][:3]:
                needed_symbols.add(stock['symbol'])
            for stock in brief['technical_signals']['overbought'][:3]:
                needed_symbols.add(stock['symbol'])
            for stock in brief['technical_signals']['oversold'][:3]:
                needed_symbols.add(stock['symbol'])
        
        # 加载股票名称
        stock_names = self._load_stock_names_for_symbols(list(needed_symbols))
        
        lines = []
        lines.append(f"## 📊 每日收盘简报 - {brief['date']}")
        lines.append("")
        
        # 维度1: 大盘与市场环境
        market = brief['market_overview']
        if 'error' not in market:
            lines.append("### 📈 大盘与市场环境")
            lines.append("")
            
            sentiment_emoji = {
                "普涨": "🚀",
                "偏涨": "📈",
                "分化": "⚖️",
                "偏跌": "📉",
                "普跌": "🔻"
            }
            emoji = sentiment_emoji.get(market['market_sentiment'], "📊")
            
            lines.append(f"- 总股票数: **{market['total_stocks']}**")
            lines.append(f"- 上涨: **{market['up_count']}** | 下跌: **{market['down_count']}** | 平盘: **{market['flat_count']}**")
            
            avg_change = market['avg_change_pct']
            avg_color = "🔴" if avg_change < 0 else "🟢"
            lines.append(f"- 平均涨跌幅: {avg_color} **{avg_change:.2f}%**")
            
            lines.append(f"- 涨停: **{market['limit_up']}** | 跌停: **{market['limit_down']}**")
            lines.append(f"- 市场情绪: **{emoji} {market['market_sentiment']}**")
            lines.append("")
        
        # 维度2: 板块热点与轮动
        sector = brief['sector_performance']
        if 'error' not in sector:
            lines.append("### 🏢 板块热点与轮动")
            lines.append("")
            lines.append(f"**行业板块数: {sector['total_sectors']}**")
            lines.append("")
            
            lines.append("**📈 涨幅榜 TOP5**")
            for i, sec in enumerate(sector['top_gainers'][:5], 1):
                pct = sec['avg_change_pct']
                emoji = "🟢" if pct > 0 else "🔴"
                lines.append(f"{i}. {sec['industry']} {emoji} **{pct:.2f}%** ({int(sec['stock_count'])}只)")
            
            lines.append("")
            lines.append("**📉 跌幅榜 TOP5**")
            for i, sec in enumerate(sector['top_losers'][:5], 1):
                pct = sec['avg_change_pct']
                emoji = "🔴" if pct < 0 else "🟢"
                lines.append(f"{i}. {sec['industry']} {emoji} **{pct:.2f}%** ({int(sec['stock_count'])}只)")
            lines.append("")
        
        # 维度4: 个股表现与活跃度
        perf = brief['stock_performance']
        if 'error' not in perf:
            lines.append("### 💹 个股表现与活跃度")
            lines.append("")
            
            lines.append("**🚀 涨幅榜 TOP5**")
            for i, stock in enumerate(perf['top_gainers'][:5], 1):
                pct = stock['change_pct']
                emoji = "🟢" if pct > 0 else "🔴"
                symbol = stock['symbol']
                name = stock_names.get(symbol, symbol)
                lines.append(f"{i}. {name}({symbol}) {emoji} **{pct:.2f}%** | 振幅: {stock['amplitude']:.2f}%")
            
            lines.append("")
            lines.append("**🔻 跌幅榜 TOP5**")
            for i, stock in enumerate(perf['top_losers'][:5], 1):
                pct = stock['change_pct']
                emoji = "🔴" if pct < 0 else "🟢"
                symbol = stock['symbol']
                name = stock_names.get(symbol, symbol)
                lines.append(f"{i}. {name}({symbol}) {emoji} **{pct:.2f}%** | 振幅: {stock['amplitude']:.2f}%")
            
            lines.append("")
            lines.append("**📊 振幅榜 TOP5**")
            for i, stock in enumerate(perf['top_amplitude'][:5], 1):
                pct = stock['change_pct']
                emoji = "🟢" if pct > 0 else "🔴"
                symbol = stock['symbol']
                name = stock_names.get(symbol, symbol)
                lines.append(f"{i}. {name}({symbol}) 振幅: **{stock['amplitude']:.2f}%** | 涨跌: {emoji} {pct:.2f}%")
            lines.append("")
        
        # 维度6: 技术信号与趋势
        tech = brief['technical_signals']
        if 'error' not in tech:
            lines.append("### 📉 技术信号与趋势")
            lines.append("")
            
            # 检查是否有警告信息
            if 'warning' in tech:
                lines.append(f"⚠️ {tech['warning']}")
                lines.append("")
            else:
                lines.append(f"**MA5金叉MA10: {tech['golden_cross_count']}只**")
                if tech['golden_cross']:
                    for stock in tech['golden_cross'][:3]:
                        symbol = stock['symbol']
                        name = stock_names.get(symbol, symbol)
                        lines.append(f"  - {name}({symbol}): 收盘{stock['close']:.2f} | MA5:{stock['ma5']:.2f} | MA10:{stock['ma10']:.2f}")
                
                lines.append("")
                lines.append(f"**超买(RSI>80): {tech['overbought_count']}只**")
                if tech['overbought']:
                    for stock in tech['overbought'][:3]:
                        symbol = stock['symbol']
                        name = stock_names.get(symbol, symbol)
                        lines.append(f"  - {name}({symbol}): 收盘{stock['close']:.2f} | RSI:{stock['rsi']:.2f}")
                
                lines.append("")
                lines.append(f"**超卖(RSI<20): {tech['oversold_count']}只**")
                if tech['oversold']:
                    for stock in tech['oversold'][:3]:
                        symbol = stock['symbol']
                        name = stock_names.get(symbol, symbol)
                        lines.append(f"  - {name}({symbol}): 收盘{stock['close']:.2f} | RSI:{stock['rsi']:.2f}")
            lines.append("") 
        return "\n".join(lines)
    
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

    
    


    