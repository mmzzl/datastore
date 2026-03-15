"""Baostock K线数据获取器"""
import baostock as bs
import pandas as pd
import logging
from typing import List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BaostockKlineFetcher:
    """Baostock K线数据获取器"""
    
    def __init__(self):
        self._connected = False
    
    def _ensure_connected(self):
        """确保已连接到baostock"""
        if not self._connected:
            lg = bs.login()
            if lg.error_code != '0':
                raise Exception(f"Baostock登录失败: {lg.error_msg}")
            self._connected = True
            logger.info("Baostock登录成功")
    
    def get_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
        adjustflag: str = "3"
    ) -> Optional[pd.DataFrame]:
        """
        获取K线数据
        
        Args:
            code: 股票代码，格式如 sh.600000 或 sz.000001
            start_date: 开始日期，格式 YYYY-MM-DD
            end_date: 结束日期，格式 YYYY-MM-DD
            frequency: 数据频率，d=日k线，w=周，m=月
            adjustflag: 复权类型，1=后复权，2=前复权，3=不复权
        
        Returns:
            K线数据DataFrame，如果失败返回None
        """
        try:
            self._ensure_connected()
            
            rs = bs.query_history_k_data_plus(
                code,
                "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
                adjustflag=adjustflag
            )
            
            if rs.error_code != '0':
                logger.error(f"获取 {code} K线数据失败: {rs.error_msg}")
                return None
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                logger.warning(f"{code} 无K线数据")
                return None
            
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            # 转换数据类型
            numeric_cols = ['open', 'high', 'low', 'close', 'preclose', 'volume', 'amount', 'turn', 'pctChg', 'peTTM', 'pbMRQ', 'psTTM', 'pcfNcfTTM']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
            
            # 重命名列以匹配MongoDB格式
            df = df.rename(columns={
                'code': 'symbol',
                'pctChg': 'change_pct',
                'turn': 'turnover_rate',
                'tradestatus': 'trade_status'
            })
            
            logger.info(f"获取 {code} K线数据成功，共 {len(df)} 条")
            return df
            
        except Exception as e:
            logger.error(f"获取 {code} K线数据异常: {e}")
            return None
    
    def get_klines_batch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        frequency: str = "d",
        adjustflag: str = "3"
    ) -> pd.DataFrame:
        """
        批量获取K线数据
        
        Args:
            codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
            adjustflag: 复权类型
        
        Returns:
            合并后的K线数据DataFrame
        """
        all_data = []
        
        for code in codes:
            try:
                df = self.get_kline(code, start_date, end_date, frequency, adjustflag)
                if df is not None and not df.empty:
                    df['name'] = code
                    all_data.append(df)
            except Exception as e:
                logger.warning(f"获取 {code} K线数据失败: {e}")
                continue
        
        if not all_data:
            return pd.DataFrame()
        
        result = pd.concat(all_data, ignore_index=True)
        logger.info(f"批量获取K线数据完成，共 {len(result)} 条记录")
        return result
    
    def close(self):
        """关闭连接"""
        if self._connected:
            bs.logout()
            self._connected = False
            logger.info("Baostock连接已关闭")
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
