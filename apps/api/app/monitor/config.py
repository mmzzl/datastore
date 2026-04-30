from typing import Dict, Any, List
from datetime import datetime
from app.core.config import settings
from app.storage.mongo_client import MongoStorage
import json
import os
import logging

logger = logging.getLogger(__name__)


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
                "rsi": {"period": 14, "buy_level": 30, "sell_level": 70},
                "macd": {"fast_period": 12, "slow_period": 26, "signal_period": 9},
                "kdj": {"period": 9, "k_buy_level": 20, "k_sell_level": 80},
                "bollinger": {"period": 20, "num_std": 2.0},
            },
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
            监控股票列表，包含配置文件中的股票和新闻分析后的股票
        """
        # 从配置文件获取股票
        config_stocks = self.config.get("stocks", [])

        # 从MongoDB获取新闻分析后的股票（只获取今天的）
        news_stocks = []
        try:
            # 构建MongoDB配置
            mongo_config = {
                "host": settings.mongodb_host,
                "port": settings.mongodb_port,
                "db_name": settings.mongodb_dbname,
                "username": settings.mongodb_username,
                "password": settings.mongodb_password,
            }

            mongo = MongoStorage(**mongo_config)
            mongo.connect()

            # 只获取今天的新闻分析股票
            today = datetime.now().strftime("%Y-%m-%d")
            news_stocks = mongo.get_news_stocks(today)

            # 获取当前监控股票池
            monitor_stocks = mongo.get_monitor_stocks()

            # 从持仓集合获取股票
            holdings_coll = mongo.db.get_collection("holdings")
            holding_codes = set()
            holding_costs = {}
            if holdings_coll is not None:
                for h in holdings_coll.find({"quantity": {"$gt": 0}}):
                    code = h.get("code", "")
                    if code:
                        holding_codes.add(code)
                        holding_costs[code] = h.get("average_cost", 0)

            # 如果监控股票池为空，初始化监控股票池
            if not monitor_stocks:
                # 合并配置文件中的股票和新闻分析后的股票
                all_stocks = []
                seen_codes = set()

                # 先添加配置文件中的股票
                for stock in config_stocks:
                    code = stock.get("code")
                    if code and code not in seen_codes:
                        seen_codes.add(code)
                        if code in holding_codes:
                            stock["hold"] = True
                            stock["cost_price"] = holding_costs.get(code, 0)
                        all_stocks.append(stock)

                # 再添加新闻分析后的股票
                for stock in news_stocks:
                    code = stock.get("code")
                    if code and code not in seen_codes:
                        seen_codes.add(code)
                        if code in holding_codes:
                            stock["hold"] = True
                            stock["cost_price"] = holding_costs.get(code, 0)
                        all_stocks.append(stock)

                # 添加持仓中但不在配置和新闻中的股票
                for code in holding_codes:
                    if code not in seen_codes:
                        seen_codes.add(code)
                        all_stocks.append({
                            "code": code,
                            "name": "",
                            "hold": True,
                            "cost_price": holding_costs.get(code, 0),
                            "rsi_buy_level": 30,
                            "rsi_sell_level": 70,
                            "k_buy_level": 20,
                            "k_sell_level": 80,
                        })

                # 保存到监控股票池
                if all_stocks:
                    mongo.save_monitor_stocks(all_stocks)
                mongo.close()
                logger.info(f"初始化监控股票池，共 {len(all_stocks)} 只股票（持仓 {len(holding_codes)} 只）")
                return all_stocks
            else:
                # 检查是否有新的新闻分析股票需要添加
                seen_codes = set(stock.get("code") for stock in monitor_stocks)
                new_stocks = []
                updated = False

                # 添加新的新闻分析股票
                for stock in news_stocks:
                    code = stock.get("code")
                    if code and code not in seen_codes:
                        seen_codes.add(code)
                        monitor_stocks.append(stock)
                        new_stocks.append(stock)

                # 同步持仓股票到监控股票池
                for stock in monitor_stocks:
                    code = stock.get("code", "")
                    if code in holding_codes and not stock.get("hold"):
                        stock["hold"] = True
                        stock["cost_price"] = holding_costs.get(code, 0)
                        updated = True

                for code in holding_codes:
                    if code not in seen_codes:
                        seen_codes.add(code)
                        monitor_stocks.append({
                            "code": code,
                            "name": "",
                            "hold": True,
                            "cost_price": holding_costs.get(code, 0),
                            "rsi_buy_level": 30,
                            "rsi_sell_level": 70,
                            "k_buy_level": 20,
                            "k_sell_level": 80,
                        })
                        new_stocks.append({"code": code})

                # 如果有新股票或持仓更新，更新监控股票池
                if new_stocks or updated:
                    mongo.save_monitor_stocks(monitor_stocks)
                    logger.info(f"更新监控股票池：新增 {len(new_stocks)} 只，持仓同步 {len(holding_codes)} 只")

                mongo.close()
                logger.info(f"从监控股票池获取到 {len(monitor_stocks)} 只股票")
                return monitor_stocks
        except Exception as e:
            logger.error(f"获取监控股票失败: {e}")
            # 失败时返回配置文件中的股票
            return config_stocks

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
        self.config["stocks"] = [
            stock for stock in self.get_stocks() if stock.get("code") != stock_code
        ]
