from typing import Dict, Any, List
from app.core.config import settings
import json
import os

class MonitorConfig:
    """监控配置管理"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载配置
        
        返回:
            配置字典
        """
        # 从settings加载配置
        default_config = {
            "enabled": getattr(settings, "monitor_enabled", True),
            "interval": getattr(settings, "monitor_interval", 300),  # 监控间隔（秒）
            "stocks": getattr(settings, "monitor_stocks", []),
            "indicators": {
                "rsi": {
                    "period": 14,
                    "buy_level": 30,
                    "sell_level": 70
                },
                "macd": {
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9
                },
                "kdj": {
                    "period": 9,
                    "k_buy_level": 20,
                    "k_sell_level": 80
                },
                "bollinger": {
                    "period": 20,
                    "num_std": 2.0
                }
            }
        }
        
        # 确保股票列表格式正确
        stocks = default_config.get("stocks", [])
        for stock in stocks:
            # 确保必要字段存在
            stock.setdefault("code", "")
            stock.setdefault("name", "")
            stock.setdefault("hold", False)
            stock.setdefault("buy_threshold", 0.05)
            stock.setdefault("sell_threshold", 0.03)
            stock.setdefault("cost_price", 0.0)
            stock.setdefault("profit_target", 0.1)
            stock.setdefault("stop_loss", 0.05)
            stock.setdefault("rsi_buy_level", 30)
            stock.setdefault("rsi_sell_level", 70)
            stock.setdefault("k_buy_level", 20)
            stock.setdefault("k_sell_level", 80)
        
        return default_config
    
    def get_config(self) -> Dict[str, Any]:
        """
        获取完整配置
        
        返回:
            完整配置字典
        """
        return self.config
    
    def get_stocks(self) -> List[Dict[str, Any]]:
        """
        获取监控股票列表
        
        返回:
            监控股票列表
        """
        return self.config.get("stocks", [])
    
    def get_holding_stocks(self) -> List[Dict[str, Any]]:
        """
        获取持仓股票列表
        
        返回:
            持仓股票列表
        """
        return [stock for stock in self.get_stocks() if stock.get("hold", False)]
    
    def get_non_holding_stocks(self) -> List[Dict[str, Any]]:
        """
        获取非持仓股票列表
        
        返回:
            非持仓股票列表
        """
        return [stock for stock in self.get_stocks() if not stock.get("hold", False)]
    
    def get_indicator_config(self, indicator_name: str) -> Dict[str, Any]:
        """
        获取指标配置
        
        参数:
            indicator_name: 指标名称
            
        返回:
            指标配置
        """
        indicators = self.config.get("indicators", {})
        return indicators.get(indicator_name, {})
    
    def get_interval(self) -> int:
        """
        获取监控间隔
        
        返回:
            监控间隔（秒）
        """
        return self.config.get("interval", 300)
    
    def is_enabled(self) -> bool:
        """
        检查监控是否启用
        
        返回:
            是否启用
        """
        return self.config.get("enabled", True)
    
    def get_stock_config(self, stock_code: str) -> Dict[str, Any]:
        """
        获取股票配置
        
        参数:
            stock_code: 股票代码
            
        返回:
            股票配置
        """
        for stock in self.get_stocks():
            if stock.get("code") == stock_code:
                return stock
        return {}
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        更新配置
        
        参数:
            new_config: 新配置
        """
        self.config.update(new_config)
    
    def update_stock_config(self, stock_code: str, stock_config: Dict[str, Any]):
        """
        更新股票配置
        
        参数:
            stock_code: 股票代码
            stock_config: 股票配置
        """
        for i, stock in enumerate(self.get_stocks()):
            if stock.get("code") == stock_code:
                self.config["stocks"][i].update(stock_config)
                break
    
    def add_stock(self, stock_config: Dict[str, Any]):
        """
        添加股票
        
        参数:
            stock_config: 股票配置
        """
        # 确保必要字段存在
        stock_config.setdefault("code", "")
        stock_config.setdefault("name", "")
        stock_config.setdefault("hold", False)
        stock_config.setdefault("buy_threshold", 0.05)
        stock_config.setdefault("sell_threshold", 0.03)
        stock_config.setdefault("cost_price", 0.0)
        stock_config.setdefault("profit_target", 0.1)
        stock_config.setdefault("stop_loss", 0.05)
        stock_config.setdefault("rsi_buy_level", 30)
        stock_config.setdefault("rsi_sell_level", 70)
        stock_config.setdefault("k_buy_level", 20)
        stock_config.setdefault("k_sell_level", 80)
        
        self.config["stocks"].append(stock_config)
    
    def remove_stock(self, stock_code: str):
        """
        删除股票
        
        参数:
            stock_code: 股票代码
        """
        self.config["stocks"] = [stock for stock in self.get_stocks() if stock.get("code") != stock_code]
