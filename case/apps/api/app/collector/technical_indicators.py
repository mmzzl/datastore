"""技术指标计算模块"""

import pandas as pd
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """技术指标计算器"""
    
    @staticmethod
    def calculate_ma(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
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
        if 'close' not in df.columns or 'rsi' in df.columns:
            return df
        
        symbol_counts = df.groupby('symbol').size()
        valid_symbols = symbol_counts[symbol_counts >= window].index
        
        if len(valid_symbols) == 0:
            logger.warning(f"没有股票有足够的数据（{len(df)} 条），无法计算 RSI")
            df['rsi'] = None
            return df
        
        def rsi_series(series: pd.Series, period: int = 14) -> pd.Series:
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
        if 'high' not in df.columns or 'low' not in df.columns:
            return df
        
        if 'amplitude' in df.columns:
            return df
        
        df['amplitude'] = ((df['high'] - df['low']) / df['low']) * 100
        return df
    
    @classmethod
    def calculate_all(cls, df: pd.DataFrame, ma_windows: list = None, rsi_window: int = 14) -> pd.DataFrame:
        if ma_windows is None:
            ma_windows = [5, 10]
        
        df = cls.calculate_amplitude(df)
        for window in ma_windows:
            df = cls.calculate_ma(df, window)
        df = cls.calculate_rsi(df, rsi_window)
        
        return df
