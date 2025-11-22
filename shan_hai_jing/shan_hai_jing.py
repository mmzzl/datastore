# -*- coding: utf-8 -*-
import os
import time
import pygetwindow as gw
import pyautogui 

class ShanHaiJing:
    def __init__(self, keyword="山海北荒卷"):
        self.keyword = keyword
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.filtered_windows = self.filter_windows_by_title(self.keyword)
        if not self.filtered_windows:
            print(f"未找到包含关键词: [{self.keyword}]的窗口")
            return
        self.filtered_windows[0].activate()
    
    def get_active_window_region(self):
        """
        获取当前激活窗口的查找区域
        
        Returns:
            tuple: 窗口区域坐标 (x, y, width, height)
        """
        active_window = self.filtered_windows[0]
        active_window.activate() 
        # 处理最小化窗口
        if active_window.isMinimized:
            active_window.restore()
            time.sleep(0.5)
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

    
    
    def move_mouse_to_window_relative(self, relative_x, relative_y, smooth=True):
        """
        移动鼠标到当前激活窗口内的相对位置并点击
        
        Args:
            relative_x (int): 窗口内的相对X坐标
            relative_y (int): 窗口内的相对Y坐标
            smooth (bool): 是否使用平滑移动
        """
        region = self.get_active_window_region()
        
        # 确保坐标在窗口范围内
        clamped_x = max(0, min(relative_x, region[2]))
        clamped_y = max(0, min(relative_y, region[3]))
        
        # 计算绝对位置
        absolute_x = region[0] + clamped_x
        absolute_y = region[1] + clamped_y
        print(f"移动鼠标：窗口内相对坐标 ({clamped_x}, {clamped_y}) → 屏幕绝对坐标 ({absolute_x}, {absolute_y})")
        
        # 移动鼠标并点击
        duration = 1 if smooth else 0
        pyautogui.moveTo(absolute_x, absolute_y, duration=duration)
        print("鼠标移动完成！")
        pyautogui.sleep(0.5)
        pyautogui.click()
        print(f"已点击窗口内坐标{clamped_x}, {clamped_y}")
    
    def click_auto_hatch_button(self):
        """
        点击自动孵蛋按钮
        """
        file_path = os.path.join(self.base_dir, "auto_egg.png")
        if self.is_image_exist(file_path):
            # 点击相关按钮执行自动孵蛋操作
            self.move_mouse_to_window_relative(259, 888)  # 第一个按钮位置
            self.move_mouse_to_window_relative(243, 690)  # 第二个按钮位置
    
    def needs_to_capture(self):
        """
        判断是否需要收服
        """
        file_path = os.path.join(self.base_dir, "move_up.png")
        retry_count = 2 
        while retry_count:
            if self.is_image_exist(file_path, confidence=0.9):
                return True 
            time.sleep(1)
            retry_count -= 1
        return False
        
    
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
        region = self.get_active_window_region() if only_active_window else None

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
                    print(f"找到图片！")
                    print(f"图片屏幕坐标：左上角({image_position.left}, {image_position.top}) → 中心点({center_x}, {center_y})")
                    print(f"图片在窗口内相对坐标：({relative_x}, {relative_y})")
                else:
                    print(f"找到图片！")
                    print(f"图片屏幕坐标：左上角({image_position.left}, {image_position.top}) → 中心点({center_x}, {center_y})")
                return image_position
            else:
                print(f"未找到图片「{image_path}」（匹配精度：{confidence}）")
                return None
        except Exception as e:
            # import traceback
            # print(traceback.format_exc())
            # print(f"{image_path}查找图片失败：{e}")
            # print("提示:1. 检查图片路径是否正确；2. Linux/macOS需安装 opencv-python（pip install opencv-python）；3. 图片需清晰无多余背景")
            return None
    
    def is_on_hatching_screen(self):
        """
        检查当前窗口是否在孵蛋界面
        """
        file_path = os.path.join(self.base_dir, "egg.png")
        retry_count = 20
        while retry_count:
            if self.is_image_exist(file_path):
                return True
            time.sleep(1)
            retry_count -= 1
        return False

    def check_confim_capture(self):
        """
        检查是否有确定按钮
        """

        file_path = os.path.join(self.base_dir, "confirm.png")
        retry_count = 20
        while retry_count:
            if self.is_image_exist(file_path):
                return True
            time.sleep(1)
            retry_count -= 1
        return False
    
    def check_egg_screen(self):
        """
        检查当前窗口是否在蛋界面并执行相应操作
        """
        # 检查是否在孵蛋界面
        if self.is_on_hatching_screen():
            print("当前在孵蛋界面")
        else:
            # 先点击
            self.move_mouse_to_window_relative(272,754)
            if self.needs_to_capture():
                print("需要收服")
                self.move_mouse_to_window_relative(350, 748)  # 收服按钮位置
                # 再点击出售按钮
                self.move_mouse_to_window_relative(168, 748)  # 出售按钮位置
            else:
                print("不需要收服,点击出售")
                # 直接点击出售按钮
                self.move_mouse_to_window_relative(168, 748)  # 出售按钮位置

    def run(self):
        """
        主循环 - 持续执行自动孵蛋和检查蛋界面的操作
        """
        try:
            print("开始运行山海北荒卷自动化脚本...")
            time.sleep(5)
            while True:
                if self.check_confim_capture():
                    self.move_mouse_to_window_relative(231, 608)  # 确认按钮位置
                    time.sleep(1)  # 循环间隔
                self.click_auto_hatch_button()
                self.check_egg_screen()
                time.sleep(1)  # 循环间隔
        except KeyboardInterrupt:
            print("\n程序被用户中断")
        except Exception as error:
            print(f"程序运行出错：{error}")
            # 出错后尝试重新点击自动孵蛋按钮
            self.click_auto_hatch_button()

if __name__ == '__main__':
    app = ShanHaiJing("山海北荒卷")
    app.run()
    