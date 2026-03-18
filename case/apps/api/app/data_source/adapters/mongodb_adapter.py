import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..interface import IDataSource
from ..models import StockKLine, StockInfo
from ...storage.mongo_client import MongoStorage
from ...core.config import settings

logger = logging.getLogger(__name__)

class MongoDBAdapter(IDataSource):
    """MongoDB数据源适配器"""
    
    def __init__(self):
        self._name = "MongoDB"
        self._provider = "mongodb"
        self.storage = None
        self._init_storage()
    
    def _init_storage(self):
        """初始化存储连接"""
        try:
            self.storage = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_database,
                username=settings.mongodb_username,
                password=settings.mongodb_password
            )
            self.storage.connect()
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB: {e}")
            self.storage = None
    
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
        if not self.storage:
            return []
        
        try:
            kline_data = self.storage.get_kline(
                code=code,
                start_date=start_date,
                end_date=end_date,
                limit=1000
            )
            
            data_list = []
            for item in kline_data:
                kline = StockKLine(
                    code=item.get('code', code),
                    date=item.get('date', ''),
                    open=float(item.get('open', 0)),
                    high=float(item.get('high', 0)),
                    low=float(item.get('low', 0)),
                    close=float(item.get('close', 0)),
                    volume=int(item.get('volume', 0)),
                    amount=float(item.get('amount', 0)),
                    turnover_rate=float(item.get('turnover', 0)) if item.get('turnover') else None,
                    change_pct=float(item.get('pct_chg', 0)) if item.get('pct_chg') else None
                )
                data_list.append(kline)
            
            return data_list
            
        except Exception as e:
            logger.error(f"获取MongoDB K线数据失败: {e}")
            return []
    
    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        # MongoDB通常存储K线数据，股票基本信息可以从其他数据源获取
        # 这里返回基本信息
        return StockInfo(
            code=code,
            name=code,
            exchange=code[:2] if '.' in code else "SH"
        )
    
    def get_stock_list(self) -> List[StockInfo]:
        """从K线数据中提取股票列表"""
        if not self.storage:
            return []
        
        try:
            # 获取所有股票的最新数据
            kline_data = self.storage.get_all_klines(limit=10000)
            
            # 去重获取股票列表
            stock_dict = {}
            for item in kline_data:
                code = item.get('code')
                if code and code not in stock_dict:
                    stock_dict[code] = StockInfo(
                        code=code,
                        name=item.get('name', code),
                        exchange=code[:2] if '.' in code else "SH"
                    )
            
            return list(stock_dict.values())
            
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    def get_realtime_data(self, code: str) -> Dict[str, Any]:
        """MongoDB不提供实时数据"""
        return {}
    
    def get_capital_flow(self, code: str, days: int = 5) -> List[Dict[str, Any]]:
        """从MongoDB获取资金流向数据"""
        if not self.storage:
            return []
        
        try:
            # 获取资金流向数据
            capital_data = self.storage.get_capital_flow(
                name=code,
                limit=days
            )
            return capital_data
            
        except Exception as e:
            logger.error(f"获取资金流向失败: {e}")
            return []
    
    def close(self):
        """关闭MongoDB连接"""
        if self.storage:
            self.storage.close()
            logger.info("MongoDB连接已关闭")
