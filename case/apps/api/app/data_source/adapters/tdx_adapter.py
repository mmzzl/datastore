import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    from mootdx.quotes import Quotes
    MOOTDX_AVAILABLE = True
except ImportError:
    MOOTDX_AVAILABLE = False
    logger.warning("mootdx library not available, TDX adapter will not work")

from ..interface import IDataSource
from ..models import StockKLine, StockInfo

class TDXAdapter(IDataSource):
    """通达信（TDX）数据源适配器"""
    
    def __init__(self):
        self._name = "通达信"
        self._provider = "tdx"
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """初始化通达信客户端"""
        if not MOOTDX_AVAILABLE:
            logger.warning("mootdx library not available")
            return
        
        try:
            self._client = Quotes.factory(market='std')
            logger.info("通达信客户端初始化成功")
        except Exception as e:
            logger.error(f"初始化通达信客户端失败: {e}")
            self._client = None
    
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
        """通达信主要用于实时数据，K线数据获取功能有限"""
        if not self._client:
            return []
        
        try:
            # 转换代码格式 sh.600000 -> 600000
            stock_code = code.split('.')[-1] if '.' in code else code
            
            # 通达信主要用于实时数据，这里返回空列表
            # 可以通过其他方式获取K线数据
            logger.info(f"通达信主要用于实时数据，K线数据建议使用其他数据源")
            return []
            
        except Exception as e:
            logger.error(f"获取K线数据异常: {e}")
            return []
    
    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        """获取股票基本信息"""
        if not self._client:
            return None
        
        try:
            # 转换代码格式
            stock_code = code.split('.')[-1] if '.' in code else code
            
            # 获取实时数据
            data = self._client.quotes(symbol=stock_code)
            
            if data is not None and len(data) > 0:
                row = data.iloc[0]
                
                # 确定交易所
                market = row.get('market', 1)
                exchange = "SH" if market == 1 else "SZ"
                
                return StockInfo(
                    code=code,
                    name=code,  # 通达信返回的数据中没有股票名称
                    exchange=exchange
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
        if not self._client:
            return {}
        
        try:
            # 转换代码格式
            stock_code = code.split('.')[-1] if '.' in code else code
            
            # 获取实时数据
            data = self._client.quotes(symbol=stock_code)
            
            if data is not None and len(data) > 0:
                row = data.iloc[0]
                
                # 确定交易所
                market = row.get('market', 1)
                exchange = "SH" if market == 1 else "SZ"
                
                return {
                    "code": f"{exchange}.{stock_code}",
                    "name": stock_code,
                    "price": float(row.get('price', 0)),
                    "change": float(row.get('price', 0)) - float(row.get('last_close', 0)),
                    "change_pct": ((float(row.get('price', 0)) - float(row.get('last_close', 0))) / float(row.get('last_close', 0)) * 100) if float(row.get('last_close', 0)) != 0 else 0,
                    "volume": int(row.get('volume', 0)),
                    "amount": float(row.get('amount', 0)) if 'amount' in row else 0,
                    "open": float(row.get('open', 0)),
                    "high": float(row.get('high', 0)),
                    "low": float(row.get('low', 0)),
                    "close": float(row.get('price', 0)),
                    "last_close": float(row.get('last_close', 0))
                }
            return {}
            
        except Exception as e:
            logger.error(f"获取实时数据失败: {e}")
            return {}
    
    def get_capital_flow(self, code: str, days: int = 5) -> List[Dict[str, Any]]:
        """通达信不直接提供资金流向数据"""
        return []
    
    def close(self):
        """关闭通达信连接"""
        if self._client:
            # mootdx不需要显式关闭
            logger.info("通达信客户端已关闭")
