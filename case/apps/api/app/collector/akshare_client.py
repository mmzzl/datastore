import akshare as ak
import pandas as pd
import baostock as bs
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import time
import requests
import os

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
        self.stock_zh_a_spot_df = self.load_data()
    
    def load_data(self):
        """加载股票数据"""
        csv_file = 'stock_zh_a_daily.csv'
        today_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            # 检查 CSV 文件是否存在
            if os.path.exists(csv_file):
                logger.info(f"从本地文件 {csv_file} 加载股票数据")
                stock_zh_a_spot_df = pd.read_csv(csv_file)
                
                # 检查是否有当前交易日期的数据
                if 'date' in stock_zh_a_spot_df.columns:
                    latest_date = pd.to_datetime(stock_zh_a_spot_df['date']).max().strftime('%Y-%m-%d')
                    logger.info(f"文件中最新数据日期: {latest_date}")
                    
                    if latest_date >= today_date:
                        logger.info(f"文件中已有最新数据，直接使用")
                        self.data = stock_zh_a_spot_df
                        return stock_zh_a_spot_df
                    else:
                        logger.info(f"文件中数据不是最新的，需要获取历史数据")
                        return self._fetch_historical_data()
                else:
                    logger.warning(f"文件中没有 date 列，需要获取历史数据")
                    return self._fetch_historical_data()
            else:
                logger.info(f"文件不存在，需要获取历史数据")
                return self._fetch_historical_data()
                
        except Exception as e:
            logger.error(f"加载股票数据失败: {e}")
            return pd.DataFrame()
    
    def _fetch_historical_data(self):
        """获取所有股票最近一个月的历史数据"""
        csv_file = 'stock_zh_a_daily.csv'
        sp_csv_file = 'stock_zh_a_spot.csv'
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        
        try:
            logger.info(f"开始获取历史数据，时间范围: {start_date} - {end_date}")
            
            # 从 stock_zh_a_spot.csv 文件中读取股票列表
            logger.info(f"从 {sp_csv_file} 读取股票列表...")
            if os.path.exists(sp_csv_file):
                stock_list_df = pd.read_csv(sp_csv_file)
                
                # 检查文件中是否有必要的列
                if 'symbol' in stock_list_df.columns and 'name' in stock_list_df.columns:
                    logger.info(f"从文件中读取到 {len(stock_list_df)} 只股票")
                    stock_list = stock_list_df[['symbol', 'name']].drop_duplicates()
                else:
                    logger.warning(f"{sp_csv_file} 文件格式不正确，使用 API 获取股票列表")
                    stock_list_df = ak.stock_zh_a_spot_em()
                    stock_list = stock_list_df[['代码', '名称']].rename(columns={'代码': 'symbol', '名称': 'name'})
            else:
                logger.warning(f"{sp_csv_file} 文件不存在，使用 API 获取股票列表")
                stock_list_df = ak.stock_zh_a_spot_em()
                stock_list = stock_list_df[['代码', '名称']].rename(columns={'代码': 'symbol', '名称': 'name'})
            
            all_data = []
            for idx, row in stock_list.iterrows():
                symbol = row['symbol']
                name = row['name']
                
                try:
                    # 转换股票代码格式
                    ak_symbol = symbol.replace('.', '')
                    
                    logger.info(f"正在获取 {name}({symbol}) 的历史数据... ({idx+1}/{len(stock_list)})")
                    
                    # 获取历史数据
                    historical_df = ak.stock_zh_a_daily(
                        symbol=ak_symbol,
                        start_date=start_date,
                        end_date=end_date,
                        adjust="qfq"
                    )
                    
                    if not historical_df.empty:
                        # 添加股票名称和代码
                        historical_df['symbol'] = symbol
                        historical_df['name'] = name
                        
                        # 计算涨跌幅
                        historical_df['change_pct'] = historical_df['close'].pct_change() * 100
                        
                        all_data.append(historical_df)
                    
                except Exception as e:
                    logger.warning(f"获取 {name}({symbol}) 历史数据失败: {e}")
                    continue
            
            if all_data:
                # 合并所有数据
                result_df = pd.concat(all_data, ignore_index=True)
                
                # 转换日期格式
                result_df['date'] = pd.to_datetime(result_df['date'])
                
                # 按日期和股票代码排序
                result_df = result_df.sort_values(['symbol', 'date'])
                
                # 保存到文件
                result_df.to_csv(csv_file, index=False)
                logger.info(f"历史数据已保存到 {csv_file}，共 {len(result_df)} 条记录")
                
                self.data = result_df
                return result_df
            else:
                logger.error("未能获取到任何历史数据")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return pd.DataFrame()
    
    def refresh_data(self):
        """刷新股票数据，强制从 API 获取"""
        logger.info(f"强制刷新股票数据")
        self._indicators_calculated = False
        return self._fetch_historical_data()

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
            self.calculate_ma(20, self.data)
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
            if len(df) < window:
                logger.warning(f"数据量不足（{len(df)} 条），无法计算 MA{window}，使用收盘价代替")
                df[f'ma{window}'] = df['close']
            else:
                df[f'ma{window}'] = df.groupby('symbol')['close'].transform(
                    lambda x: x.rolling(window=window, min_periods=1).mean()
                )
        return df
    
    def calculate_rsi(self, window: int = 14, df: pd.DataFrame = None) -> pd.DataFrame:
        """计算RSI指标"""
        if df is None:
            df = self.data
        if 'close' not in df.columns or 'rsi' in df.columns:
            return df
        
        # 检查是否有足够的数据来计算RSI
        if len(df) < window:
            logger.warning(f"数据量不足（{len(df)} 条），无法计算 RSI，使用默认值 50")
            df['rsi'] = 50.0
            return df
        
        def rsi_series(series, period=14):
            delta = series.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            return 100 - (100 / (1 + rs))
        
        df['rsi'] = df.groupby('symbol')['close'].transform(rsi_series)
        return df
    
    def analyze_technical_signals(self, date: str = None, top_n: int = 20) -> Dict:
        """维度6: 技术信号与趋势"""
        if date is None:
            date = self.get_latest_date()
        
        self._ensure_indicators()
        
        # 匹配日期（支持 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS 格式）
        df_date = self.data[self.data['date'].astype(str).str[:10] == date].copy()
        
        if df_date.empty:
            return {"error": "No data for this date"}
        
        # 去重：每个股票只保留一条记录
        df_date = df_date.drop_duplicates(subset=['symbol'], keep='first')
        
        # 检查是否有足够的历史数据来计算技术指标
        if len(self.data) < 100000:
            logger.warning(f"数据量不足（{len(self.data)} 条），技术指标可能不准确")
            return {
                "date": date,
                "warning": "数据量不足，无法准确计算技术指标。需要至少20个交易日的数据来计算MA和RSI指标。",
                "golden_cross_count": 0,
                "golden_cross": [],
                "overbought_count": 0,
                "overbought": [],
                "oversold_count": 0,
                "oversold": []
            }
        
        # 金叉（MA5 > MA20）
        golden_cross = df_date[df_date['ma5'] > df_date['ma20']][['symbol', 'close', 'ma5', 'ma20']]
        
        # 超买（RSI > 80）
        overbought = df_date[df_date['rsi'] > 80][['symbol', 'close', 'rsi']]
        
        # 超卖（RSI < 20）
        oversold = df_date[df_date['rsi'] < 20][['symbol', 'close', 'rsi']]
        
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
        logger.info("brief: %s", brief)
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
                lines.append(f"**MA5金叉MA20: {tech['golden_cross_count']}只**")
                if tech['golden_cross']:
                    for stock in tech['golden_cross'][:3]:
                        symbol = stock['symbol']
                        name = stock_names.get(symbol, symbol)
                        lines.append(f"  - {name}({symbol}): 收盘{stock['close']:.2f} | MA5:{stock['ma5']:.2f} | MA20:{stock['ma20']:.2f}")
                
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
        
        lines.append("---")
        lines.append("*数据来源：baostock | 生成时间：自动生成*")
        
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

    
    


    