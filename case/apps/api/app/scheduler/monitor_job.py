from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional
import logging
import calendar

from ..monitor import StockMonitor

logger = logging.getLogger(__name__)

class MonitorJob:
    """盯盘任务"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.monitor = None
    
    def is_trading_time(self) -> bool:
        """
        判断当前是否为交易时间
        
        返回:
            bool: 是否为交易时间
        """
        now = datetime.now()
        
        # 检查是否为工作日
        if now.weekday() >= 5:  # 周六、周日
            # logger.info("当前为非工作日，跳过盯盘")
            return False
        
        # 检查是否为交易日（这里简化处理，实际应该检查法定节假日）
        # 这里可以添加更复杂的节假日判断逻辑
        
        # 检查是否为交易时间
        trading_start = now.replace(hour=9, minute=30, second=0, microsecond=0)
        trading_end = now.replace(hour=15, minute=0, second=0, microsecond=0)
        
        if not (trading_start <= now <= trading_end):
            # logger.info(f"当前非交易时间 ({now.strftime('%H:%M:%S')})，跳过盯盘")
            return False
        
        return True
    
    def run(self, target_date: Optional[str] = None) -> str:
        """
        执行盯盘任务
        
        参数:
            target_date: 目标日期，格式为 YYYY-MM-DD
            
        返回:
            执行结果消息
        """
        # 检查是否为交易时间
        if not self.is_trading_time():
            return "当前非交易时间，跳过盯盘任务"
        
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
