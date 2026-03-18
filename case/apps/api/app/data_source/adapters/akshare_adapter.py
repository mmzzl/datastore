import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import akshare as ak

from ..interface import IDataSource
from ..models import StockKLine, StockInfo

logger = logging.getLogger(__name__)

class AkshareAdapter(IDataSource):
    """Akshare数据源适配器"""
    
    def __init__(self):
        self._name = "Akshare"
        self._provider = "akshare"
    
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
        adjust_flag: str = "3"
    ) -> List[StockKLine]:
        try:
            # 转换代码格式 sh.600000 -> 600000
            stock_code = code.split('.')[-1] if '.' in code else code
            
            # 获取K线数据
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date.replace('-', ''),
                end_date=end_date.replace('-', ''),
                adjust="qfq" if adjust_flag == "1" else "hfq" if adjust_flag == "2" else ""
            )
            
            data_list = []
            for _, row in df.iterrows():
                kline = StockKLine(
                    code=code,
                    date=str(row['日期']),
                    open=float(row['开盘']),
                    high=float(row['最高']),
                    low=float(row['最低']),
                    close=float(row['收盘']),
                    volume=int(row['成交量']),
                    amount=float(row['成交额']),
                    change_pct=float(row['涨跌幅']) if '涨跌幅' in df.columns else None
                )
                data_list.append(kline)
            
            return data_list
            
        except Exception as e:
            logger.error(f"获取K线数据异常: {e}")
            return []
    
    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        try:
            # Akshare获取股票信息
            stock_code = code.split('.')[-1] if '.' in code else code
            
            # 从实时数据获取基本信息
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df['代码'] == stock_code]
            
            if not stock_data.empty:
                return StockInfo(
                    code=code,
                    name=stock_data.iloc[0]['名称'],
                    exchange=code[:2] if '.' in code else "SH"
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
                code = row['代码']
                exchange = "SH" if code.startswith('6') else "SZ"
                stock_list.append(StockInfo(
                    code=f"{exchange}.{code}",
                    name=row['名称'],
                    exchange=exchange
                ))
            
            return stock_list
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    def get_realtime_data(self, code: str) -> Dict[str, Any]:
        try:
            stock_code = code.split('.')[-1] if '.' in code else code
            
            df = ak.stock_zh_a_spot_em()
            stock_data = df[df['代码'] == stock_code]
            
            if not stock_data.empty:
                row = stock_data.iloc[0]
                return {
                    "code": code,
                    "name": row['名称'],
                    "price": row['最新价'],
                    "change": row['涨跌额'],
                    "change_pct": row['涨跌幅'],
                    "volume": row['成交量'],
                    "amount": row['成交额'],
                    "open": row['开盘'],
                    "high": row['最高'],
                    "low": row['最低'],
                    "close": row['最新价']
                }
            return {}
            
        except Exception as e:
            logger.error(f"获取实时数据失败: {e}")
            return {}
    
    def get_capital_flow(self, code: str, days: int = 5) -> List[Dict[str, Any]]:
        """Akshare资金流向数据"""
        try:
            stock_code = code.split('.')[-1] if '.' in code else code
            
            # 获取历史K线数据
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=(datetime.now() - timedelta(days=days)).strftime('%Y%m%d'),
                end_date=datetime.now().strftime('%Y%m%d')
            )
            
            # 简化处理，返回基本的资金流向信息
            # 注意：Akshare不直接提供资金流向，这里返回模拟数据
            result = []
            for _, row in df.iterrows():
                result.append({
                    "date": str(row['日期']),
                    "net_inflow": 0,  # Akshare不直接提供，需要计算
                    "code": code
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取资金流向失败: {e}")
            return []
    
    def close(self):
        """Akshare不需要关闭连接"""
        pass
