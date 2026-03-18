import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .config import MonitorConfig
from .analysis.technical import TechnicalAnalyzer
from .analysis.signal import SignalGenerator
from .models import StockData, TechnicalData, Signal, MonitorResult, MonitorNotification
from .brain.analyzer import BrainAnalyzer
from .brain.unhook import UnhookEngine
from .brain.backtest import BacktestEngine
from app.data_source import DataSourceManager
from .data_source import get_data_source_manager, MultiDataSourceManager
from ..notify import DingTalkNotifier
from ..storage import MongoStorage
from ..collector import AkshareClient

logger = logging.getLogger(__name__)

class StockMonitor:
    """股票监控核心类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitor_config = MonitorConfig()
        self.technical_analyzer = TechnicalAnalyzer()
        self.signal_generator = SignalGenerator()
        # Brain System
        self.brain_analyzer = BrainAnalyzer()
        self.unhook_engine = UnhookEngine()
        self.backtest_engine = BacktestEngine()
        # Unified Data Source
        self.data_manager = DataSourceManager()
        
        self.akshare_client = None
        self.dingtalk_notifier = None
        self.storage = None
        
        self._ensure_clients()
    
    def _ensure_clients(self):
        """确保所有客户端已初始化"""
        # 初始化Akshare客户端
        if self.akshare_client is None:
            self.akshare_client = AkshareClient()
            logger.info("Using Akshare data source for stock data")
        
        # 初始化钉钉通知器
        if self.dingtalk_notifier is None:
            after_market_config = self.config.get("after_market", {})
            self.dingtalk_notifier = DingTalkNotifier(
                after_market_config.get("dingtalk_webhook", ""),
                after_market_config.get("dingtalk_secret", ""),
                self.akshare_client
            )
        
        # 初始化存储客户端
        if self.storage is None:
            db_config = self.config.get("database", {})
            self.storage = MongoStorage(
                db_config.get("host", "localhost"),
                db_config.get("port", 27017),
                db_config.get("name", "after_market"),
                db_config.get("username"),
                db_config.get("password")
            )
            self.storage.connect()
    
    def get_stock_data(self, stock_code: str) -> Optional[StockData]:
        """
        获取股票数据 - 使用统一数据源接口
        
        参数:
            stock_code: 股票代码
            
        返回:
            股票数据
        """
        try:
            # 使用统一数据源接口获取实时数据
            realtime_data = self.data_manager.get_realtime_data(stock_code)
            
            if not realtime_data:
                logger.warning(f"Failed to get stock data for {stock_code}")
                return None
            
            return StockData(
                code=stock_code,
                name=realtime_data.get("name", stock_code),
                current_price=realtime_data.get("close", 0.0),
                high_price=realtime_data.get("high", 0.0),
                low_price=realtime_data.get("low", 0.0),
                open_price=realtime_data.get("open", 0.0),
                close_price=realtime_data.get("close", 0.0),
                change=realtime_data.get("change", 0.0),
                change_pct=realtime_data.get("change_pct", 0.0),
                volume=realtime_data.get("volume", 0),
                amount=realtime_data.get("amount", 0.0)
            )
        except Exception as e:
            logger.error(f"Error getting stock data for {stock_code}: {e}")
            return None
    
    def get_stock_history_data(self, stock_code: str, days: int = 30) -> Dict[str, List[float]]:
        """
        获取股票历史数据 - 使用统一数据源接口
        
        参数:
            stock_code: 股票代码
            days: 历史天数
            
        返回:
            历史数据
        """
        try:
            # 使用统一数据源接口获取历史K线数据
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            klines = self.data_manager.get_kline(
                code=stock_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if not klines:
                logger.warning(f"Failed to get history data for {stock_code}")
                return {}
            
            return {
                "close": [k.close for k in klines],
                "high": [k.high for k in klines],
                "low": [k.low for k in klines]
            }
        except Exception as e:
            logger.error(f"Error getting history data for {stock_code}: {e}")
            return {}
    
    def analyze_stock(self, stock_config: Dict[str, Any]) -> Optional[MonitorResult]:
        """
        分析股票 - 集成Brain系统
        
        参数:
            stock_config: 股票配置
            
        返回:
            监控结果
        """
        stock_code = stock_config.get("code")
        if not stock_code:
            logger.warning("Stock code is required")
            return None
        
        # 获取股票数据
        stock_data = self.get_stock_data(stock_code)
        if not stock_data:
            return None
        
        # 获取历史数据
        history_data = self.get_stock_history_data(stock_code)
        
        # 分析技术指标
        technical_result = self.technical_analyzer.analyze_stock(history_data)
        
        # === Brain系统分析 ===
        try:
            # 准备技术数据供Brain使用
            brain_technical_data = {
                "rsi": technical_result.get("rsi", 50.0),
                "macd": technical_result.get("macd", {}),
                "kdj": technical_result.get("kdj", {}),
                "bollinger": technical_result.get("bollinger", {}),
                "close": history_data.get("close", [])
            }
            
            # Brain分析
            brain_decision = self.brain_analyzer.analyze(
                code=stock_code,
                technical_data=brain_technical_data,
                current_price=stock_data.current_price
            )
            
            logger.info(f"Brain决策 - {stock_code}: {brain_decision.action}, 置信度: {brain_decision.confidence:.2f}")
            
            # 如果是持仓股票，生成解套策略
            unhook_strategy = None
            if stock_config.get("hold", False):
                cost_price = stock_config.get("cost_price", 0.0)
                if cost_price > 0:
                    unhook_strategy = self.unhook_engine.calculate_strategy(
                        code=stock_code,
                        current_price=stock_data.current_price,
                        cost_price=cost_price
                    )
                    logger.info(f"解套策略 - {stock_code}: {unhook_strategy.suggestion}")
            
        except Exception as e:
            logger.error(f"Brain分析出错: {e}")
            brain_decision = None
            unhook_strategy = None
        
        # 生成信号（保留原有逻辑，但可以结合Brain决策）
        stock_config["current_price"] = stock_data.current_price
        signal_result = self.signal_generator.generate_signal(technical_result, stock_config)
        
        # 如果有Brain决策，优先使用Brain的信号
        if brain_decision:
            signal_result = {
                "signal": brain_decision.action,
                "strength": int(brain_decision.confidence * 10),
                "strength_percentage": brain_decision.confidence * 100,
                "reasons": brain_decision.reasons,
                "suggestion": f"Brain建议: {brain_decision.action}"
            }
        
        # 构建监控结果
        monitor_result = MonitorResult(
            stock=stock_data,
            technical_data=TechnicalData(
                rsi=type('obj', (object,), {"value": technical_result.get("rsi", 50.0), "period": 14})(),
                macd=type('obj', (object,), technical_result.get("macd", {}))(),
                kdj=type('obj', (object,), technical_result.get("kdj", {}))(),
                bollinger=type('obj', (object,), technical_result.get("bollinger", {}))()
            ),
            signal=Signal(
                signal=signal_result.get("signal", "hold"),
                strength=signal_result.get("strength", 0),
                strength_percentage=signal_result.get("strength_percentage", 0.0),
                reasons=signal_result.get("reasons", []),
                suggestion=signal_result.get("suggestion", "建议持有")
            )
        )
        
        # 存储监控历史
        self._save_monitor_history(monitor_result)
        
        # 如果有解套策略，存储解套建议
        if unhook_strategy:
            self._save_unhook_strategy(unhook_strategy)
        
        # 检查股票是否适合继续监控
        # 如果信号为hold且信号强度较低，可能意味着股票走势走坏
        if signal_result.get("signal") == "hold" and signal_result.get("strength") < 2:
            # 从监控股票池中移除
            try:
                self.storage.remove_monitor_stock(stock_code)
                logger.info(f"股票 {stock_code} 走势走坏，已从监控股票池移除")
            except Exception as e:
                logger.error(f"移除股票失败: {e}")
        
        return monitor_result
    
    def _save_unhook_strategy(self, unhook_strategy):
        """
        存储解套策略
        
        参数:
            unhook_strategy: 解套策略
        """
        try:
            if not self.storage:
                return
            
            strategy_data = {
                "code": unhook_strategy.code,
                "current_price": unhook_strategy.current_price,
                "cost_price": unhook_strategy.cost_price,
                "suggestion": unhook_strategy.suggestion,
                "details": unhook_strategy.details,
                "expected_recovery_time": unhook_strategy.expected_recovery_time,
                "timestamp": unhook_strategy.timestamp
            }
            
            # 存储到MongoDB
            # 这里可以根据需要存储到特定的集合
            logger.info(f"存储解套策略 - {unhook_strategy.code}: {unhook_strategy.suggestion}")
            
        except Exception as e:
            logger.error(f"Error saving unhook strategy: {e}")
    
    def _save_monitor_history(self, monitor_result: MonitorResult):
        """
        存储监控历史
        
        参数:
            monitor_result: 监控结果
        """
        try:
            history_data = {
                "stock_code": monitor_result.stock.code,
                "stock_name": monitor_result.stock.name,
                "timestamp": monitor_result.timestamp,
                "signal": monitor_result.signal.signal,
                "signal_strength": monitor_result.signal.strength,
                "price": monitor_result.stock.current_price,
                "technical_data": {
                    "rsi": monitor_result.technical_data.rsi.value,
                    "macd": {
                        "macd": monitor_result.technical_data.macd.macd,
                        "signal": monitor_result.technical_data.macd.signal,
                        "histogram": monitor_result.technical_data.macd.histogram
                    },
                    "kdj": {
                        "k": monitor_result.technical_data.kdj.k,
                        "d": monitor_result.technical_data.kdj.d,
                        "j": monitor_result.technical_data.kdj.j
                    },
                    "bollinger": {
                        "upper": monitor_result.technical_data.bollinger.upper,
                        "middle": monitor_result.technical_data.bollinger.middle,
                        "lower": monitor_result.technical_data.bollinger.lower
                    }
                },
                "reasons": monitor_result.signal.reasons
            }
            self.storage.save(history_data)
        except Exception as e:
            logger.error(f"Error saving monitor history: {e}")
    
    def generate_notification(self, monitor_result: MonitorResult) -> Optional[MonitorNotification]:
        """
        生成通知
        
        参数:
            monitor_result: 监控结果
            
        返回:
            通知
        """
        signal = monitor_result.signal.signal
        if signal not in ["buy", "sell"]:
            return None
        
        # 构建通知消息
        if signal == "buy":
            message = f"【买入信号】\n"
            message += f"股票：{monitor_result.stock.name} ({monitor_result.stock.code})\n"
            message += f"当前价格：{monitor_result.stock.current_price:.2f}\n"
            message += f"分析结果：{monitor_result.signal.suggestion}\n"
            message += f"买入理由：\n"
            for reason in monitor_result.signal.reasons:
                message += f"- {reason}\n"
            message += f"技术指标：\n"
            message += f"- RSI: {monitor_result.technical_data.rsi.value:.2f}\n"
            message += f"- MACD: {monitor_result.technical_data.macd.macd:.4f}\n"
            message += f"- KDJ: K={monitor_result.technical_data.kdj.k:.2f}, D={monitor_result.technical_data.kdj.d:.2f}, J={monitor_result.technical_data.kdj.j:.2f}\n"
            message += f"建议操作：立即买入"
        else:
            # 计算盈利/亏损
            stock_config = self.monitor_config.get_stock_config(monitor_result.stock.code)
            cost_price = stock_config.get("cost_price", 0.0)
            current_price = monitor_result.stock.current_price
            profit_loss = 0.0
            if cost_price > 0:
                profit_loss = (current_price - cost_price) / cost_price * 100
            
            message = f"【卖出信号】\n"
            message += f"股票：{monitor_result.stock.name} ({monitor_result.stock.code})\n"
            message += f"当前价格：{monitor_result.stock.current_price:.2f}\n"
            if cost_price > 0:
                message += f"持仓成本：{cost_price:.2f}\n"
                message += f"盈利/亏损：{profit_loss:.2f}%\n"
            message += f"分析结果：{monitor_result.signal.suggestion}\n"
            message += f"卖出理由：\n"
            for reason in monitor_result.signal.reasons:
                message += f"- {reason}\n"
            message += f"技术指标：\n"
            message += f"- RSI: {monitor_result.technical_data.rsi.value:.2f}\n"
            message += f"- MACD: {monitor_result.technical_data.macd.macd:.4f}\n"
            message += f"- KDJ: K={monitor_result.technical_data.kdj.k:.2f}, D={monitor_result.technical_data.kdj.d:.2f}, J={monitor_result.technical_data.kdj.j:.2f}\n"
            message += f"建议操作：立即卖出"
        
        return MonitorNotification(
            type=signal,
            stock=monitor_result.stock,
            signal=monitor_result.signal,
            message=message
        )
    
    def send_notification(self, notification: MonitorNotification):
        """
        发送通知
        
        参数:
            notification: 通知
        """
        try:
            self.dingtalk_notifier.send(notification.message)
            logger.info(f"Notification sent for {notification.stock.code}: {notification.type}")
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def monitor_stocks(self) -> List[MonitorResult]:
        """
        监控所有股票
        
        返回:
            监控结果列表
        """
        results = []
        stocks = self.monitor_config.get_stocks()
        
        for stock_config in stocks:
            logger.info(f"Monitoring stock: {stock_config.get('name', stock_config.get('code'))}")
            result = self.analyze_stock(stock_config)
            if result:
                results.append(result)
                
                # 生成并发送通知
                notification = self.generate_notification(result)
                if notification:
                    self.send_notification(notification)
        
        return results
    
    def close(self):
        """
        关闭资源
        """
        if self.storage:
            self.storage.close()
        logger.info("Stock monitor closed")
