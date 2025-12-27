# -*- coding: utf-8 -*-
"""
鼠标操作模块 - 处理鼠标移动和点击
"""

import pyautogui
from config import (
    AUTO_HATCH_BUTTONS, CAPTURE_BUTTON, SELL_BUTTON, 
    CONFIRM_BUTTON, STOP_AUTO_HATCH_BUTTON, CLICK_WAIT_TIME
)


class MouseController:
    """鼠标控制器"""
    
    def __init__(self, window_manager, logger=None):
        """
        初始化鼠标控制器
        Args:
            window_manager: 窗口管理器实例
            logger: 日志实例
        """
        self.window_manager = window_manager
        self.logger = logger
    
    def move_mouse_to_window_relative(self, relative_x, relative_y, smooth=True):
        """
        移动鼠标到当前激活窗口内的相对位置并点击
        Args:
            relative_x (int): 窗口内的相对X坐标
            relative_y (int): 窗口内的相对Y坐标
            smooth (bool): 是否使用平滑移动
        """
        region = self.window_manager.get_active_window_region()
        
        if not region:
            print("无法获取窗口区域")
            return
        
        # 确保坐标在窗口范围内
        clamped_x = max(0, min(relative_x, region[2]))
        clamped_y = max(0, min(relative_y, region[3]))
        
        # 计算绝对位置
        absolute_x = region[0] + clamped_x
        absolute_y = region[1] + clamped_y
        
        if self.logger:
            self.logger.debug(f"移动鼠标：窗口内相对坐标 ({clamped_x}, {clamped_y}) → 屏幕绝对坐标 ({absolute_x}, {absolute_y})")
        
        # 移动鼠标并点击
        duration = 1 if smooth else 0
        pyautogui.moveTo(absolute_x, absolute_y, duration=duration)
        if self.logger:
            self.logger.debug("鼠标移动完成！")
        
        pyautogui.sleep(CLICK_WAIT_TIME)
        pyautogui.click()
        
        if self.logger:
            self.logger.debug(f"已点击窗口内坐标{clamped_x}, {clamped_y}")
    
    def click_auto_hatch_button(self):
        """点击自动孵蛋按钮"""
        if self.logger:
            self.logger.info("点击自动孵蛋按钮")
        
        for button in AUTO_HATCH_BUTTONS:
            self.move_mouse_to_window_relative(button['x'], button['y'])
    
    def click_capture_button(self):
        """点击收服按钮"""
        self.move_mouse_to_window_relative(CAPTURE_BUTTON['x'], CAPTURE_BUTTON['y'])
    
    def click_sell_button(self):
        """点击出售按钮"""
        self.move_mouse_to_window_relative(SELL_BUTTON['x'], SELL_BUTTON['y'])
    
    def click_confirm_button(self):
        """点击确定按钮"""
        self.move_mouse_to_window_relative(CONFIRM_BUTTON['x'], CONFIRM_BUTTON['y'])
    
    def click_stop_auto_hatch_button(self):
        """点击停止自动孵蛋按钮"""
        self.move_mouse_to_window_relative(STOP_AUTO_HATCH_BUTTON['x'], STOP_AUTO_HATCH_BUTTON['y'])