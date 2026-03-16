from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
import logging

from ..monitor import StockMonitor

logger = logging.getLogger(__name__)

class MonitorJob:
    """盯盘任务"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitor = None
    
    def run(self, target_date: Optional[str] = None) -> str:
        """
        执行盯盘任务
        
        参数:
            target_date: 目标日期，格式为 YYYY-MM-DD
            
        返回:
            执行结果消息
        """
        if target_date:
            target = datetime.strptime(target_date, "%Y-%m-%d")
        else:
            target = datetime.now()
        date_str = target.strftime("%Y-%m-%d")
        
        logger.info(f"Starting monitor job for {date_str}")
        
        try:
            # 初始化监控器
            if self.monitor is None:
                self.monitor = StockMonitor(self.config)
            
            # 执行监控
            results = self.monitor.monitor_stocks()
            
            # 统计结果
            buy_signals = sum(1 for r in results if r.signal.signal == "buy")
            sell_signals = sum(1 for r in results if r.signal.signal == "sell")
            hold_signals = sum(1 for r in results if r.signal.signal == "hold")
            
            logger.info(f"Monitor job completed for {date_str}")
            logger.info(f"Signals: buy={buy_signals}, sell={sell_signals}, hold={hold_signals}")
            
            return f"盯盘任务完成: {date_str} (买入信号: {buy_signals}, 卖出信号: {sell_signals}, 持有信号: {hold_signals})"
            
        except Exception as e:
            logger.error(f"Monitor job failed for {date_str}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
        finally:
            if self.monitor:
                self.monitor.close()
