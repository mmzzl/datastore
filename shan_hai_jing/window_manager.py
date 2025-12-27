# -*- coding: utf-8 -*-
"""
窗口管理模块 - 处理窗口查找、激活和区域获取
"""

import pygetwindow as gw
import time
from config import WINDOW_KEYWORD, WINDOW_OPERATION_WAIT_TIME


class WindowManager:
    """窗口管理器"""
    
    def __init__(self, keyword=None, logger=None):
        """
        初始化窗口管理器
        Args:
            keyword: 窗口标题关键词
            logger: 日志实例
        """
        self.keyword = keyword or WINDOW_KEYWORD
        self.logger = logger
        self.filtered_windows = self.filter_windows_by_title(self.keyword)
    
    def filter_windows_by_title(self, keyword):
        """
        根据关键词过滤窗口列表
        Args:
            keyword (str): 窗口标题中需要包含的关键词
        Returns:
            list: 符合条件的窗口列表
        """
        all_windows = gw.getAllWindows()
        print(f"\n包含关键词: [{keyword}]的窗口")
        filtered_windows = [window for window in all_windows if keyword in window.title]
        return filtered_windows
    
    def get_active_window_region(self):
        """
        获取当前激活窗口的查找区域
        Returns:
            tuple: 窗口区域坐标 (x, y, width, height)
        """
        if not self.filtered_windows:
            print("未找到可用窗口")
            return None
        
        active_window = self.filtered_windows[0]
        try:
            active_window.activate() 
        except Exception as e:
            # pygetwindow 的一个已知问题：错误代码0表示操作成功，但仍会抛出异常
            # 这种情况下可以忽略异常，因为窗口实际上已经激活了
            error_msg = str(e)
            if "Error code from Windows: 0" in error_msg:
                pass  # 忽略这个已知问题
            else:
                print(f"激活窗口时出错: {e}")
                return None
        
        # 处理最小化窗口
        if active_window.isMinimized:
            active_window.restore()
            time.sleep(WINDOW_OPERATION_WAIT_TIME)
        
        # 窗口查找区域：(x, y, width, height)
        region = (
            active_window.left,    # 查找区域左上角x
            active_window.top,     # 查找区域左上角y
            active_window.width,   # 查找区域宽度
            active_window.height   # 查找区域高度
        )
        
        print(f"查找范围：当前激活窗口「{active_window.title}」")
        print(f"窗口区域：(x={active_window.left}, y={active_window.top}, 宽={active_window.width}, 高={active_window.height})")
        
        return region
    
    def activate_window(self):
        """
        激活窗口（强制激活，包括恢复最小化窗口）
        Returns:
            bool: 是否激活成功
        """
        if not self.filtered_windows:
            print(f"未找到包含关键词: [{self.keyword}]的窗口")
            return False
        
        active_window = self.filtered_windows[0]
        
        try:
            # 如果窗口被最小化，先恢复
            if active_window.isMinimized:
                active_window.restore()
                if self.logger:
                    self.logger.info(f"窗口「{active_window.title}」已从最小化状态恢复")
                time.sleep(WINDOW_OPERATION_WAIT_TIME)
            
            # 尝试激活窗口
            active_window.activate()
            
            # 再次尝试强制激活（使用Windows API）
            try:
                import win32gui
                import win32con
                hwnd = active_window._hWnd
                if hwnd:
                    # 强制置顶
                    win32gui.SetForegroundWindow(hwnd)
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    if self.logger:
                        self.logger.info(f"已强制激活窗口「{active_window.title}」")
            except ImportError:
                # 如果没有安装pywin32，使用备用方法
                if self.logger:
                    self.logger.info("未安装pywin32，使用基础激活方法")
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"强制激活窗口失败: {e}")
            
            return True
        except Exception as e:
            error_msg = str(e)
            if "Error code from Windows: 0" in error_msg:
                if self.logger:
                    self.logger.info(f"窗口激活成功（忽略pygetwindow的已知问题）")
                return True
            else:
                if self.logger:
                    self.logger.error(f"激活窗口时出错: {e}")
                return False