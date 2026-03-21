from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .models import StockKLine, StockInfo


class IDataSource(ABC):
    """数据源统一接口，所有数据源需实现此接口"""

    @abstractmethod
    def get_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
        adjust_flag: str = "3",
    ) -> List[StockKLine]:
        pass

    @abstractmethod
    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        pass

    @abstractmethod
    def get_stock_list(self) -> List[StockInfo]:
        pass

    @abstractmethod
    def get_realtime_data(self, code: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_capital_flow(self, code: str, days: int = 5) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def set_holdings(self, user_id: str, holdings: List[Dict[str, Any]]) -> List[str]:
        pass

    @abstractmethod
    def get_portfolio_summary(self, user_id: str, price_fetcher=None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_settings(self, user_id: str) -> Dict[str, Any]:
        """获取用户的设置（如 watchlist、interval、days、cache TTL 等）"""
        pass

    @abstractmethod
    def set_settings(self, user_id: str, settings: Dict[str, Any]) -> None:
        """保存用户设置"""
        pass

    @abstractmethod
    def remove_holding(self, user_id: str, code: str) -> int:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def provider(self) -> str:
        pass

    @abstractmethod
    def close(self):
        pass
