"""
Strategy Factory

Factory class for creating strategy instances.
"""

import logging
import importlib
from typing import Dict, Any, Optional, Type
from enum import Enum

from .base import BaseStrategy
from .ma_cross import MACrossStrategy
from .rsi import RSIStrategy
from .bollinger import BollingerStrategy
from .macd import MACDStrategy
from .qlib_model import QlibModelStrategy
from ...core.config import settings
from ...storage.mongo_client import MongoStorage

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Supported strategy types."""
    MA_CROSS = "ma_cross"
    RSI = "rsi"
    BOLLINGER = "bollinger"
    MACD = "macd"
    QLIB_MODEL = "qlib_model"
    PLUGIN = "plugin"  # Plugin strategy type


class StrategyFactory:
    """
    Factory for creating strategy instances.
    
    Supported strategy types:
    - "ma_cross": Moving Average Crossover
    - "rsi": Relative Strength Index
    - "bollinger": Bollinger Bands
    - "macd": MACD
    - "qlib_model": Qlib Model-based
    - "plugin": Plugin-based strategy
    
    Example:
        >>> factory = StrategyFactory()
        >>> strategy = factory.create("ma_cross", fast_period=5, slow_period=20)
        >>> signal = strategy.generate_signals(data)
    """
    
    _strategies: Dict[str, Type[BaseStrategy]] = {
        StrategyType.MA_CROSS.value: MACrossStrategy,
        StrategyType.RSI.value: RSIStrategy,
        StrategyType.BOLLINGER.value: BollingerStrategy,
        StrategyType.MACD.value: MACDStrategy,
        StrategyType.QLIB_MODEL.value: QlibModelStrategy,
    }
    
    @classmethod
    def create(
        cls,
        strategy_type: str,
        **params: Any,
    ) -> BaseStrategy:
        """
        Create a strategy instance.
        
        Args:
            strategy_type: Type of strategy to create
            **params: Strategy-specific parameters
        
        Returns:
            Strategy instance
        
        Raises:
            ValueError: If strategy type is not supported
        """
        strategy_type = strategy_type.lower()
        
        # Check if it's a plugin strategy
        if strategy_type == StrategyType.PLUGIN.value:
            plugin_id = params.pop('plugin_id', None)
            if not plugin_id:
                raise ValueError("Plugin strategy requires plugin_id parameter")
            return cls._create_plugin_strategy(plugin_id, **params)
        
        # Check if it's a built-in strategy
        if strategy_type not in cls._strategies:
            supported = ", ".join(cls._strategies.keys())
            raise ValueError(
                f"Unknown strategy type: {strategy_type}. "
                f"Supported types: {supported}"
            )
        
        strategy_class = cls._strategies[strategy_type]
        
        try:
            strategy = strategy_class(**params)
            logger.info(f"Created {strategy.get_name()} with params: {params}")
            return strategy
        except Exception as e:
            logger.error(f"Failed to create strategy {strategy_type}: {e}")
            raise
    
    @classmethod
    def _create_plugin_strategy(
        cls,
        plugin_id: str,
        **params: Any,
    ) -> BaseStrategy:
        """
        Create a plugin strategy instance.
        
        Args:
            plugin_id: Plugin ID
            **params: Strategy-specific parameters
        
        Returns:
            Strategy instance
        
        Raises:
            ValueError: If plugin not found or failed to load
        """
        # Get plugin info from MongoDB
        storage = MongoStorage(
            host=settings.mongodb_host,
            port=settings.mongodb_port,
            db_name=settings.mongodb_database,
            username=settings.mongodb_username,
            password=settings.mongodb_password,
        )
        
        try:
            storage.connect()
            plugin = storage.get_strategy_plugin(plugin_id)
            if not plugin:
                raise ValueError(f"Plugin with ID {plugin_id} not found")
            
            # Extract plugin info
            module_name = plugin.get("module_name")
            class_name = plugin.get("class_name")
            
            if not module_name or not class_name:
                raise ValueError("Invalid plugin metadata")
            
            # Dynamically import the plugin module
            try:
                module = importlib.import_module(f"app.backtest.strategies.plugins.{module_name}")
                strategy_class = getattr(module, class_name)
                
                # Create strategy instance
                strategy = strategy_class(**params)
                logger.info(f"Created plugin strategy {strategy.get_name()} with params: {params}")
                return strategy
            except Exception as e:
                logger.error(f"Failed to load plugin strategy: {e}")
                raise ValueError(f"Failed to load plugin strategy: {str(e)}")
        finally:
            storage.close()
    
    @classmethod
    def get_supported_types(cls) -> list:
        """
        Get list of supported strategy types.
        
        Returns:
            List of strategy type names
        """
        return list(cls._strategies.keys()) + [StrategyType.PLUGIN.value]
    
    @classmethod
    def get_default_params(cls, strategy_type: str, **kwargs) -> Dict[str, Any]:
        """
        Get default parameters for a strategy type.
        
        Args:
            strategy_type: Strategy type name
            **kwargs: Additional parameters (e.g., plugin_id for plugin strategies)
        
        Returns:
            Dictionary of default parameters
        """
        strategy_type = strategy_type.lower()
        
        # Check if it's a plugin strategy
        if strategy_type == StrategyType.PLUGIN.value:
            plugin_id = kwargs.get('plugin_id')
            if plugin_id:
                return cls._get_plugin_default_params(plugin_id)
            return {}
        
        # Built-in strategies
        defaults = {
            StrategyType.MA_CROSS.value: {
                "fast_period": 5,
                "slow_period": 20,
            },
            StrategyType.RSI.value: {
                "period": 14,
                "oversold": 30.0,
                "overbought": 70.0,
            },
            StrategyType.BOLLINGER.value: {
                "period": 20,
                "num_std": 2.0,
            },
            StrategyType.MACD.value: {
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9,
            },
            StrategyType.QLIB_MODEL.value: {
                "model_id": None,
                "topk": 50,
            },
        }
        
        return defaults.get(strategy_type, {})
    
    @classmethod
    def _get_plugin_default_params(cls, plugin_id: str) -> Dict[str, Any]:
        """
        Get default parameters for a plugin strategy.
        
        Args:
            plugin_id: Plugin ID
        
        Returns:
            Dictionary of default parameters
        """
        storage = MongoStorage(
            host=settings.mongodb_host,
            port=settings.mongodb_port,
            db_name=settings.mongodb_database,
            username=settings.mongodb_username,
            password=settings.mongodb_password,
        )
        
        try:
            storage.connect()
            plugin = storage.get_strategy_plugin(plugin_id)
            if not plugin:
                return {}
            
            parameters = plugin.get("parameters", {})
            default_params = {}
            for param_name, param_info in parameters.items():
                default_params[param_name] = param_info.get("default")
            
            return default_params
        finally:
            storage.close()
    
    @classmethod
    def register_strategy(
        cls,
        strategy_type: str,
        strategy_class: Type[BaseStrategy],
    ) -> None:
        """
        Register a custom strategy class.
        
        Args:
            strategy_type: Name for the strategy type
            strategy_class: Strategy class to register
        """
        if not issubclass(strategy_class, BaseStrategy):
            raise ValueError(f"Strategy class must inherit from BaseStrategy")
        
        cls._strategies[strategy_type.lower()] = strategy_class
        logger.info(f"Registered custom strategy: {strategy_type}")
