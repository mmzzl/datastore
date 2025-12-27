# -*- coding: utf-8 -*-
"""
电源管理模块
功能：防止系统锁屏和进入睡眠状态
"""

import ctypes
import logging
from typing import Optional


class PowerManager:
    """
    电源管理器类
    用于防止系统锁屏和进入睡眠状态
    """
    
    # Windows API 常量
    ES_CONTINUOUS = 0x80000000
    ES_SYSTEM_REQUIRED = 0x00000001
    ES_DISPLAY_REQUIRED = 0x00000002
    ES_AWAYMODE_REQUIRED = 0x00000040
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化电源管理器
        Args:
            logger: 日志记录器
        """
        self.logger = logger or logging.getLogger(__name__)
        self._is_active = False
        
        # 加载 Windows API
        try:
            self._set_thread_execution_state = ctypes.windll.kernel32.SetThreadExecutionState
            self.logger.info("电源管理模块初始化成功")
        except Exception as e:
            self.logger.error(f"电源管理模块初始化失败: {e}")
            self._set_thread_execution_state = None
    
    def prevent_sleep(self, prevent_display: bool = True, prevent_system: bool = True) -> bool:
        """
        防止系统进入睡眠状态
        Args:
            prevent_display: 是否防止显示器关闭（锁屏）
            prevent_system: 是否防止系统进入睡眠状态
        Returns:
            bool: 是否成功设置
        """
        if not self._set_thread_execution_state:
            self.logger.error("电源管理API不可用")
            return False
        
        try:
            # 构建标志位
            flags = self.ES_CONTINUOUS
            
            if prevent_display:
                flags |= self.ES_DISPLAY_REQUIRED
            
            if prevent_system:
                flags |= self.ES_SYSTEM_REQUIRED
            
            # 调用 Windows API
            result = self._set_thread_execution_state(flags)
            
            if result != 0:
                self._is_active = True
                self.logger.info(f"已启用防锁屏模式 (显示器: {'是' if prevent_display else '否'}, 系统: {'是' if prevent_system else '否'})")
                return True
            else:
                self.logger.error("设置防锁屏失败")
                return False
                
        except Exception as e:
            self.logger.error(f"设置防锁屏时发生错误: {e}")
            return False
    
    def restore_sleep(self) -> bool:
        """
        恢复正常的电源管理（允许系统锁屏和睡眠）
        Returns:
            bool: 是否成功恢复
        """
        if not self._set_thread_execution_state:
            return False
        
        try:
            # 恢复正常的电源管理
            result = self._set_thread_execution_state(self.ES_CONTINUOUS)
            
            if result != 0:
                self._is_active = False
                self.logger.info("已恢复正常的电源管理")
                return True
            else:
                self.logger.error("恢复电源管理失败")
                return False
                
        except Exception as e:
            self.logger.error(f"恢复电源管理时发生错误: {e}")
            return False
    
    def is_active(self) -> bool:
        """
        检查防锁屏是否处于激活状态
        Returns:
            bool: 是否激活
        """
        return self._is_active
    
    def __enter__(self):
        """
        上下文管理器入口
        """
        self.prevent_sleep()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口
        """
        self.restore_sleep()
