# -*- coding: utf-8 -*-
"""
界面检查模块 - 检查游戏界面状态和图片识别
"""

import os
import time
import pyautogui
from config import IMAGES_DIR, EGG_IMAGES, CONFIRM_IMAGE, MOVE_UP_IMAGE, AUTO_EGG_IMAGE, UI_CHECK_WAIT_TIME


class UIChecker:
    """界面检查器"""
    
    def __init__(self, window_manager, logger=None):
        """
        初始化界面检查器
        Args:
            window_manager: 窗口管理器实例
            logger: 日志实例
        """
        self.window_manager = window_manager
        self.logger = logger
    
    def is_image_exist(self, image_path, confidence=0.8, only_active_window=True):
        """
        判断目标图片是否存在（支持仅在激活窗口内查找）
        Args:
            image_path (str): 目标图片路径
            confidence (float): 匹配精度（0-1，值越高越精准，建议 0.7-0.9）
            only_active_window (bool): 是否仅在当前激活窗口内查找
        Returns:
            tuple or None: 找到返回图片位置元组 (left, top, width, height)，未找到返回 None
        """
        # 1. 确定查找区域
        region = self.window_manager.get_active_window_region() if only_active_window else None

        try:
            # 2. 查找图片（grayscale=True 灰度查找，提高匹配成功率）
            image_position = pyautogui.locateOnScreen(
                image_path,
                confidence=confidence,
                grayscale=True,
                region=region  # 限制查找范围（仅激活窗口）
            )
            # 3. 判断结果
            if image_position:
                # 计算图片中心点坐标（屏幕绝对坐标）
                center_x, center_y = pyautogui.center(image_position)
                # 计算图片在激活窗口内的相对坐标（如果有激活窗口）
                if region:
                    relative_x = center_x - region[0]
                    relative_y = center_y - region[1]
                    if self.logger:
                        self.logger.debug(f"找到图片！")
                        self.logger.debug(f"图片屏幕坐标：左上角({image_position.left}, {image_position.top}) → 中心点({center_x}, {center_y})")
                        self.logger.debug(f"图片在窗口内相对坐标：({relative_x}, {relative_y})")
                else:
                    if self.logger:
                        self.logger.debug(f"找到图片！")
                        self.logger.debug(f"图片屏幕坐标：左上角({image_position.left}, {image_position.top}) → 中心点({center_x}, {center_y})")
                return image_position
            else:
                if self.logger:
                    self.logger.debug(f"未找到图片「{image_path}」（匹配精度：{confidence}）")
                return None
        except Exception as e:
            return None
    
    def is_on_hatching_screen(self):
        """
        检查当前窗口是否在孵蛋界面
        Returns:
            bool: 是否在孵蛋界面
        """
        retry_count = 15  # 减少重试次数从15到8
        while retry_count:
            for image in EGG_IMAGES:
                file_path = os.path.join(IMAGES_DIR, image)
                if os.path.exists(file_path):
                    try:
                        result = pyautogui.locateOnScreen(file_path, confidence=0.9)
                        self.logger.info(f"检查{image}结果: {result}")
                        if result:
                            return True
                    except Exception as e:
                        if self.logger:
                            self.logger.debug(f"检查{image}失败: {e}")
            retry_count -= 1
        return False
    
    def check_confirm_capture(self):
        """
        检查是否有确定按钮
        Returns:
            bool: 是否有确定按钮
        """
        file_path = os.path.join(IMAGES_DIR, CONFIRM_IMAGE)
        retry_count = 3  # 减少重试次数从5到3
        while retry_count:
            if self.is_image_exist(file_path):
                return True
            time.sleep(UI_CHECK_WAIT_TIME)
            retry_count -= 1
        return False
    
    def needs_to_capture(self):
        """
        判断是否需要收服
        Returns:
            bool: 是否需要收服
        """
        file_path = os.path.join(IMAGES_DIR, MOVE_UP_IMAGE)
        retry_count = 2 
        while retry_count:
            if self.is_image_exist(file_path, confidence=0.9):
                return True 
            time.sleep(UI_CHECK_WAIT_TIME)
            retry_count -= 1
        return False
    
    def check_auto_hatch_button(self):
        """
        检查是否有自动孵蛋按钮
        Returns:
            bool: 是否有自动孵蛋按钮
        """
        file_path = os.path.join(IMAGES_DIR, AUTO_EGG_IMAGE)
        if os.path.exists(file_path):
            try:
                result = pyautogui.locateOnScreen(file_path, confidence=0.9)
                if result:
                    return True
            except Exception as e:
                if self.logger:
                    self.logger.debug(f"检查自动孵蛋按钮失败: {e}")
        return self.is_image_exist(file_path)