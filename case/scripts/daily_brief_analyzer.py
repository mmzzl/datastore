# -*- coding: utf-8 -*-
# 每日收盘简报 - 数据分析模块
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from pathlib import Path
import baostock as bs
from datetime import datetime, timedelta
import json
import os


class DailyBriefAnalyzer:
    def __init__(self, csv_dir: str):
        self.csv_dir = Path(csv_dir).expanduser()
        self._data = None
        self.stock_names = {}
        self._indicators_calculated = False
        self.stock_names_cache_file = self.csv_dir / "stock_names_cache.json"
    
    @property
    def data(self):
        """延迟加载数据"""
        if self._data is None:
            print("正在加载数据...")
            self._data = self.load_all_data()
            print(f"数据加载完成，共 {len(self._data)} 条记录")
        return self._data
    
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
    
    def _load_stock_names_from_cache(self) -> Dict[str, str]:
        """从本地缓存加载股票名称"""
        if self.stock_names_cache_file.exists():
            try:
                with open(self.stock_names_cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    stock_names = cache_data.get('stock_names', {})
                    cache_time = cache_data.get('cache_time', '')
                    
                    if stock_names:
                        print(f"从缓存加载股票名称，共 {len(stock_names)} 个（缓存时间: {cache_time}）")
                    return stock_names
            except Exception as e:
                print(f"加载缓存失败: {e}")
        
        return {}
    
    def _save_stock_names_to_cache(self, stock_names: Dict[str, str]):
        """保存股票名称到本地缓存"""
        try:
            cache_data = {
                'stock_names': stock_names,
                'cache_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            with open(self.stock_names_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            print(f"股票名称已缓存到本地")
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def load_stock_names(self) -> Dict[str, str]:
        """加载股票名称映射（只加载TOP榜单的股票）"""
        stock_names = {}
        
        # 只加载需要的股票名称（涨幅榜、跌幅榜、振幅榜、技术信号）
        # 先获取所有可能需要的股票代码
        needed_symbols = set()
        
        # 从涨幅榜、跌幅榜、振幅榜中提取（需要先运行一次分析）
        # 这里暂时返回空字典，后续在需要时再加载
        return stock_names
    
    def _load_stock_names_for_symbols(self, symbols: list) -> Dict[str, str]:
        """为指定股票列表加载名称"""
        stock_names = {}
        
        if not symbols:
            return stock_names
        
        # 先尝试从缓存加载所有股票名称
        all_stock_names = self._load_stock_names_from_cache()
        
        if not all_stock_names:
            # 缓存不存在，从 API 获取所有股票名称
            print("缓存不存在，从 API 获取所有股票名称...")
            lg = bs.login()
            if lg.error_code != '0':
                print(f"baostock login failed: {lg.error_msg}")
                return stock_names
            
            # 一次性获取所有股票基本信息
            rs = bs.query_stock_basic()
            
            if rs.error_code == '0' and len(rs.data) > 0:
                for row in rs.data:
                    code = row[0]
                    name = row[1]
                    if code.startswith('sh.'):
                        symbol = f"SH{code[3:].upper()}"
                    else:
                        symbol = f"SZ{code[3:].upper()}"
                    all_stock_names[symbol] = name
                
                # 保存到缓存
                self._save_stock_names_to_cache(all_stock_names)
            
            bs.logout()
        
        # 从所有股票名称中筛选出需要的股票
        for symbol in symbols:
            if symbol in all_stock_names:
                stock_names[symbol] = all_stock_names[symbol]
        
        print(f"已加载 {len(stock_names)} 个股票名称")
        return stock_names
    
    def load_all_data(self) -> pd.DataFrame:
        """加载所有股票数据"""
        import glob
        csv_files = glob.glob(str(self.csv_dir / "*.csv"))
        
        if not csv_files:
            return pd.DataFrame()
        
        try:
            df = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame()
    
    def calculate_change_pct(self, df: pd.DataFrame = None) -> pd.DataFrame:
        """计算涨跌幅"""
        if df is None:
            df = self.data
        if 'close' in df.columns and 'change_pct' not in df.columns:
            df['change_pct'] = df.groupby('symbol')['close'].pct_change() * 100
        return df
    
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
        
        # 去重：每个股票只保留一条记录
        df_date = df_date.drop_duplicates(subset=['symbol'], keep='first')
        
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
    
    def print_brief(self, date: str = None):
        """打印每日简报"""
        brief = self.generate_daily_brief(date)
        
        # 加载需要的股票名称
        needed_symbols = set()
        
        # 从个股表现中提取
        if 'stock_performance' in brief and 'error' not in brief['stock_performance']:
            for stock in brief['stock_performance']['top_gainers'][:10]:
                needed_symbols.add(stock['symbol'])
            for stock in brief['stock_performance']['top_losers'][:10]:
                needed_symbols.add(stock['symbol'])
            for stock in brief['stock_performance']['top_amplitude'][:10]:
                needed_symbols.add(stock['symbol'])
        
        # 从技术信号中提取
        if 'technical_signals' in brief and 'error' not in brief['technical_signals']:
            for stock in brief['technical_signals']['golden_cross'][:5]:
                needed_symbols.add(stock['symbol'])
            for stock in brief['technical_signals']['overbought'][:5]:
                needed_symbols.add(stock['symbol'])
            for stock in brief['technical_signals']['oversold'][:5]:
                needed_symbols.add(stock['symbol'])
        
        # 加载股票名称
        stock_names = self._load_stock_names_for_symbols(list(needed_symbols))
        
        print("=" * 80)
        print(f"每日收盘简报 - {brief['date']}")
        print("=" * 80)
        
        # 维度1: 大盘与市场环境
        print("\n【维度1: 大盘与市场环境】")
        market = brief['market_overview']
        if 'error' not in market:
            print(f"  总股票数: {market['total_stocks']}")
            print(f"  上涨: {market['up_count']} | 下跌: {market['down_count']} | 平盘: {market['flat_count']}")
            print(f"  平均涨跌幅: {market['avg_change_pct']}%")
            print(f"  涨停: {market['limit_up']} | 跌停: {market['limit_down']}")
            print(f"  市场情绪: {market['market_sentiment']}")
        
        # 维度2: 板块热点与轮动
        print("\n【维度2: 板块热点与轮动】")
        sector = brief['sector_performance']
        if 'error' not in sector:
            print(f"  行业板块数: {sector['total_sectors']}")
            print("\n  涨幅榜 TOP10:")
            for i, sec in enumerate(sector['top_gainers'][:10], 1):
                print(f"    {i}. {sec['industry']}: {sec['avg_change_pct']:.2f}% | 股票数: {int(sec['stock_count'])}")
            
            print("\n  跌幅榜 TOP10:")
            for i, sec in enumerate(sector['top_losers'][:10], 1):
                print(f"    {i}. {sec['industry']}: {sec['avg_change_pct']:.2f}% | 股票数: {int(sec['stock_count'])}")
        
        # 维度4: 个股表现与活跃度
        print("\n【维度4: 个股表现与活跃度】")
        perf = brief['stock_performance']
        if 'error' not in perf:
            print("\n  涨幅榜 TOP10:")
            for i, stock in enumerate(perf['top_gainers'][:10], 1):
                symbol = stock['symbol']
                name = stock_names.get(symbol, symbol)
                print(f"    {i}. {name}({symbol}): {stock['change_pct']:.2f}% | 振幅: {stock['amplitude']:.2f}%")
            
            print("\n  跌幅榜 TOP10:")
            for i, stock in enumerate(perf['top_losers'][:10], 1):
                symbol = stock['symbol']
                name = stock_names.get(symbol, symbol)
                print(f"    {i}. {name}({symbol}): {stock['change_pct']:.2f}% | 振幅: {stock['amplitude']:.2f}%")
            
            print("\n  振幅榜 TOP10:")
            for i, stock in enumerate(perf['top_amplitude'][:10], 1):
                symbol = stock['symbol']
                name = stock_names.get(symbol, symbol)
                print(f"    {i}. {name}({symbol}): {stock['amplitude']:.2f}% | 涨跌: {stock['change_pct']:.2f}%")
        
        # 维度6: 技术信号与趋势
        print("\n【维度6: 技术信号与趋势】")
        tech = brief['technical_signals']
        if 'error' not in tech:
            print(f"  MA5金叉MA20: {tech['golden_cross_count']}只")
            if tech['golden_cross']:
                print("    金叉股票:")
                for stock in tech['golden_cross'][:5]:
                    symbol = stock['symbol']
                    name = stock_names.get(symbol, symbol)
                    print(f"      {name}({symbol}): 收盘{stock['close']:.2f} | MA5:{stock['ma5']:.2f} | MA20:{stock['ma20']:.2f}")
            
            print(f"\n  超买(RSI>80): {tech['overbought_count']}只")
            if tech['overbought']:
                print("    超买股票:")
                for stock in tech['overbought'][:5]:
                    symbol = stock['symbol']
                    name = stock_names.get(symbol, symbol)
                    print(f"      {name}({symbol}): 收盘{stock['close']:.2f} | RSI:{stock['rsi']:.2f}")
            
            print(f"\n  超卖(RSI<20): {tech['oversold_count']}只")
            if tech['oversold']:
                print("    超卖股票:")
                for stock in tech['oversold'][:5]:
                    symbol = stock['symbol']
                    name = stock_names.get(symbol, symbol)
                    print(f"      {name}({symbol}): 收盘{stock['close']:.2f} | RSI:{stock['rsi']:.2f}")
        
        print("\n" + "=" * 80)
    
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


if __name__ == "__main__":
    analyzer = DailyBriefAnalyzer("~/.qlib/stock_data/source/all_1d_original")
    analyzer.print_brief()
