import logging
from typing import Dict, Optional, List, Any
from contextlib import contextmanager

from .interface import IDataSource
from .models import DataSourceConfig, StockKLine, StockInfo
from .adapters.baostock_adapter import BaostockAdapter
from .adapters.mongodb_adapter import MongoDBAdapter
from .adapters.akshare_adapter import AkshareAdapter
from .adapters.tdx_adapter import TDXAdapter

logger = logging.getLogger(__name__)


class DataSourceManager:
    """
    数据源管理器
    负责管理多个数据源适配器，提供统一的数据访问接口
    """

    def __init__(self, config: List[DataSourceConfig] = None):
        self._adapters: Dict[str, IDataSource] = {}
        self._config = config or self._get_default_config()
        self._initialize_adapters()

    def _get_default_config(self) -> List[DataSourceConfig]:
        """获取默认数据源配置"""
        return [
            DataSourceConfig(
                provider="tdx",
                name="通达信实时数据源",
                enabled=True,
                priority=1,
                config={},
            ),
            DataSourceConfig(
                provider="baostock",
                name="Baostock免费数据源",
                enabled=True,
                priority=2,
                config={},
            ),
            DataSourceConfig(
                provider="mongodb",
                name="MongoDB缓存数据源",
                enabled=True,
                priority=3,
                config={},
            ),
            DataSourceConfig(
                provider="akshare",
                name="Akshare数据源",
                enabled=True,
                priority=4,
                config={},
            ),
        ]

    def _initialize_adapters(self):
        """初始化数据源适配器"""
        for config in self._config:
            if not config.enabled:
                continue

            try:
                if config.provider == "baostock":
                    adapter = BaostockAdapter()
                elif config.provider == "mongodb":
                    adapter = MongoDBAdapter()
                elif config.provider == "akshare":
                    adapter = AkshareAdapter()
                elif config.provider == "tdx":
                    adapter = TDXAdapter()
                else:
                    logger.warning(f"未知的数据源提供商: {config.provider}")
                    continue

                self._adapters[config.provider] = adapter
                logger.info(f"初始化数据源: {adapter.name} (优先级: {config.priority})")

            except Exception as e:
                logger.error(f"初始化数据源 {config.provider} 失败: {e}")

    def register_adapter(self, provider: str, adapter: IDataSource):
        """注册自定义数据源适配器"""
        self._adapters[provider] = adapter
        logger.info(f"注册自定义数据源: {provider}")

    def get_adapter(self, provider: str) -> Optional[IDataSource]:
        """获取指定的数据源适配器"""
        return self._adapters.get(provider)

    def get_best_adapter(self, data_type: str = "kline") -> Optional[IDataSource]:
        """
        获取最适合的数据源适配器
        根据优先级和数据类型选择
        """
        # 按优先级排序
        sorted_adapters = sorted(
            self._adapters.items(), key=lambda x: self._get_adapter_priority(x[0])
        )

        for provider, adapter in sorted_adapters:
            # 根据数据类型选择合适的数据源
            if data_type == "kline" and hasattr(adapter, "get_kline"):
                return adapter
            elif data_type == "realtime" and hasattr(adapter, "get_realtime_data"):
                return adapter
            elif data_type == "capital_flow" and hasattr(adapter, "get_capital_flow"):
                return adapter

        return None

    def _get_adapter_priority(self, provider: str) -> int:
        """获取适配器优先级"""
        for config in self._config:
            if config.provider == provider:
                return config.priority
        return 999

    # 统一数据访问接口

    def get_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        frequency: str = "d",
        adjust_flag: str = "3",
        provider: str = None,
    ) -> List[StockKLine]:
        """
        获取K线数据

        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
            adjust_flag: 复权类型
            provider: 指定数据源，None则自动选择

        Returns:
            K线数据列表
        """
        if provider:
            adapter = self._adapters.get(provider)
            if adapter:
                return adapter.get_kline(
                    code, start_date, end_date, frequency, adjust_flag
                )
        else:
            # 自动选择最佳数据源
            adapter = self.get_best_adapter("kline")
            if adapter:
                return adapter.get_kline(
                    code, start_date, end_date, frequency, adjust_flag
                )

        return []

    def get_stock_info(self, code: str, provider: str = None) -> Optional[StockInfo]:
        """获取股票信息"""
        if provider:
            adapter = self._adapters.get(provider)
            if adapter:
                return adapter.get_stock_info(code)
        else:
            for adapter in self._adapters.values():
                info = adapter.get_stock_info(code)
                if info:
                    return info
        return None

    def get_stock_list(self, provider: str = None) -> List[StockInfo]:
        """获取股票列表"""
        if provider:
            adapter = self._adapters.get(provider)
            if adapter:
                return adapter.get_stock_list()
        else:
            # 合并所有数据源的股票列表
            all_stocks = {}
            for adapter in self._adapters.values():
                stocks = adapter.get_stock_list()
                for stock in stocks:
                    all_stocks[stock.code] = stock
            return list(all_stocks.values())
        return []

    def get_realtime_data(self, code: str, provider: str = None) -> Dict[str, Any]:
        """获取实时数据"""
        if provider:
            adapter = self._adapters.get(provider)
            if adapter:
                return adapter.get_realtime_data(code)
        else:
            for adapter in self._adapters.values():
                data = adapter.get_realtime_data(code)
                if data:
                    return data
        return {}

    def get_capital_flow(
        self, code: str, days: int = 5, provider: str = None
    ) -> List[Dict[str, Any]]:
        """获取资金流向数据"""
        if provider:
            adapter = self._adapters.get(provider)
            if adapter:
                return adapter.get_capital_flow(code, days)
        else:
            for adapter in self._adapters.values():
                data = adapter.get_capital_flow(code, days)
                if data:
                    return data
        return []

    # 新增 holdings 的统一入口（按优先级使用第一个实现了 holdings 的数据源）
    def get_holdings(self, user_id: str) -> List[Dict[str, Any]]:
        """获取指定用户的持仓列表（若某数据源实现了 holdings，将优先使用）"""
        if user_id is None:
            return []
        for provider, adapter in self._adapters.items():
            try:
                if hasattr(adapter, "get_holdings"):
                    data = adapter.get_holdings(user_id)
                    if data:
                        return data
            except Exception:
                continue
        return []

    def get_portfolio_summary(self, user_id: str, price_fetcher=None) -> Dict[str, Any]:
        """获取用户持仓汇总信息，若有价格回填则计算市场价值"""
        for provider, adapter in self._adapters.items():
            try:
                if hasattr(adapter, "get_portfolio_summary"):
                    return adapter.get_portfolio_summary(user_id, price_fetcher)
            except Exception:
                continue
        # 回退：如果没有实现，返回空结构
        return {
            "user_id": user_id,
            "holdings_count": 0,
            "total_cost": 0.0,
            "market_value": None,
            "unrealized_pnl": None,
            "holdings": [],
        }

    def close_all(self):
        """关闭所有数据源连接"""
        for provider, adapter in self._adapters.items():
            try:
                adapter.close()
                logger.info(f"关闭数据源连接: {provider}")
            except Exception as e:
                logger.error(f"关闭数据源 {provider} 失败: {e}")

    @contextmanager
    def get_connection(self):
        """上下文管理器"""
        try:
            yield self
        finally:
            self.close_all()
