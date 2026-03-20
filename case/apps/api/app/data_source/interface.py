from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from .models import StockKLine, StockInfo


class IDataSource(ABC):
    """
    数据源统一接口
    所有数据源必须实现此接口
    """

    @abstractmethod
    def get_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
        adjust_flag: str = "3",
    ) -> List[StockKLine]:
        """
        获取K线数据

        Args:
            code: 股票代码
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            frequency: 数据频率 d=日, w=周, m=月
            adjust_flag: 复权类型 1=后复权, 2=前复权, 3=不复权

        Returns:
            K线数据列表
        """
        pass

    @abstractmethod
    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        """
        获取股票基本信息

        Args:
            code: 股票代码

        Returns:
            股票信息
        """
        pass

    @abstractmethod
    def get_stock_list(self) -> List[StockInfo]:
        """
        获取股票列表

        Returns:
            股票信息列表
        """
        pass

    @abstractmethod
    def get_realtime_data(self, code: str) -> Dict[str, Any]:
        """
        获取实时数据

        Args:
            code: 股票代码

        Returns:
            实时数据字典
        """
        pass

    @abstractmethod
    def get_capital_flow(self, code: str, days: int = 5) -> List[Dict[str, Any]]:
        """
        获取资金流向数据

        Args:
            code: 股票代码
            days: 获取天数

        Returns:
            资金流向数据列表
        """
        pass

    @abstractmethod
    def get_holdings(self, user_id: str) -> List[Dict[str, Any]]:
        """获取指定用户的持仓列表"""
        pass

    @abstractmethod
    def get_portfolio_summary(self, user_id: str, price_fetcher=None) -> Dict[str, Any]:
        """返回用户持仓的汇总信息，包括成本、市值与未实现盈亏"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """数据源名称"""
        pass

    @property
    @abstractmethod
    def provider(self) -> str:
        """数据源提供商"""
        pass

    @abstractmethod
    def close(self):
        """关闭连接/清理资源"""
        pass
