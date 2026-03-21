# -*- coding: utf-8 -*-
"""
山海北荒卷自动化脚本
功能：自动孵蛋、识别异兽属性、智能收服
"""

import os
import sys
import time
import datetime
import signal
import traceback 
import pyautogui
from filelock import FileLock 
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler

# 导入自定义模块
from config import (
    WINDOW_KEYWORD, TARGET_ATTRIBUTES, STRATEGY,
    SLOTS_FILE, CAPTURE_BUTTON, CONFIRM_BUTTON, SCHEDULER_INTERVAL,
    CHARACTER_BUTTON, BACK_BUTTON, SELL_BUTTON_ALT,
    UI_CHECK_WAIT_TIME, MAIN_LOOP_WAIT_TIME, IMAGES_DIR, AUTO_EGG_IMAGE, RELOGIN_BUTTON
)
from logger import setup_logger
from window_manager import WindowManager
from mouse_controller import MouseController
from ui_checker import UIChecker
from ocr_recognizer import OCRRecognizer
from attribute_parser import AttributeParser
from capture_strategy import CaptureStrategy
from slot_manager import SlotManager
from power_manager import PowerManager


class ShanHaiJing:
    """
    山海北荒卷自动化主类
    """
    
    def __init__(self, keyword="山海北荒卷", skip_initial_ocr=True):
        """
        初始化山海北荒卷自动化脚本
        Args:
            keyword: 窗口标题关键词
            skip_initial_ocr: 是否跳过初始OCR识别（用于复用缓存的属性）
        """
        self.keyword = keyword
        
        # 运行标志
        self.running = True
        
        # 记录异兽属性
        self.previous_beast = None  # 记录之前的异兽属性
        self.current_beast = None  # 记录当前异兽属性
        
        # 初始化各个模块
        self.logger = setup_logger()
        self.window_manager = WindowManager(self.keyword, self.logger)
        self.mouse_controller = MouseController(self.window_manager, self.logger)
        self.ui_checker = UIChecker(self.window_manager, self.logger)
        self.ocr_recognizer = OCRRecognizer(self.window_manager, self.logger)
        self.attribute_parser = AttributeParser(self.logger)
        self.capture_strategy = CaptureStrategy(self.attribute_parser, self.logger)
        self.slot_manager = SlotManager(self.logger)
        self.power_manager = PowerManager(self.logger)
        
        # 收服策略配置
        self.strategy = STRATEGY
        self.target_attributes = TARGET_ATTRIBUTES
        
        # 激活窗口
        if not self.window_manager.filtered_windows:
            self.logger.error(f"未找到包含关键词: [{self.keyword}]的窗口")
            return

        # 先激活窗口
        if self.window_manager.activate_window():
            self.logger.info("窗口已激活")
        else:
            self.logger.warning("窗口激活失败")
            return 
        
        # 如果不是跳过OCR，则加载属性格子状态并识别当前异兽
        if not skip_initial_ocr:
            self.load_attribute_slots()
    
    def load_attribute_slots(self):
        """
        从文件加载属性格子状态，并通过OCR获取当前异兽属性
        """
        # 点击当前人物按钮
        self.mouse_controller.move_mouse_to_window_relative(CHARACTER_BUTTON['x'], CHARACTER_BUTTON['y'])
        time.sleep(UI_CHECK_WAIT_TIME)
        
        # OCR识别当前异兽属性
        text_list = self.ocr_recognizer.recognize_current_beast(save_screenshot=True)
        
        if text_list:
            # 解析当前异兽属性
            current_attribute = self._parse_current_beast(text_list)
            if current_attribute:
                self.current_beast = current_attribute
                self.logger.info(f"【OCR识别】当前异兽属性: {current_attribute}")
        
        # 点击返回按钮
        self.mouse_controller.move_mouse_to_window_relative(BACK_BUTTON['x'], BACK_BUTTON['y'])
    
    def _parse_current_beast(self, text_list):
        """
        解析当前异兽属性（用于启动时识别）
        Args:
            text_list: OCR识别的文字列表
        Returns:
            dict: 异兽属性字典
        """
        if not text_list:
            return None
        
        # 辅助函数：解析属性值
        def parse_attribute_value(value_str):
            """解析属性值，去除百分号和逗号，转换为数字"""
            if not value_str:
                return 0
            value_str = value_str.replace('%', '').replace(',', '').replace('，', '')
            try:
                return float(value_str)
            except:
                return 0
        
        # 基础属性映射
        basic_attr_map = {
            '生命': 'hp',
            '攻击': 'attack',
            '防御': 'defense',
            '速度': 'speed'
        }
        
        # 特殊属性列表（按优先级排序）
        special_attr_priority = ['暴击', '连击', '闪避', '吸血', '反击', '击晕']
        
        # 解析属性
        current_attribute = {}
        
        for text in text_list:
            if '：' in text or ':' in text:
                if '：' in text:
                    attr_name, attr_value = text.split('：', 1)
                else:
                    attr_name, attr_value = text.split(':', 1)
                
                attr_name = attr_name.strip()
                attr_value = attr_value.strip()
                
                # 解析基础属性
                if attr_name in basic_attr_map:
                    current_attribute[basic_attr_map[attr_name]] = int(parse_attribute_value(attr_value))
                
                # 解析特殊属性（只记录优先级最高的一个）
                elif attr_name in special_attr_priority and 'special_attribute' not in current_attribute:
                    current_attribute['special_attribute'] = attr_name
                    current_attribute['special_value'] = parse_attribute_value(attr_value)
        
        # 设置默认值
        if 'hp' not in current_attribute:
            current_attribute['hp'] = 0
        if 'attack' not in current_attribute:
            current_attribute['attack'] = 0
        if 'defense' not in current_attribute:
            current_attribute['defense'] = 0
        if 'speed' not in current_attribute:
            current_attribute['speed'] = 0
        if 'special_attribute' not in current_attribute:
            current_attribute['special_attribute'] = ''
            current_attribute['special_value'] = 0
        
        return current_attribute
    
    def check_egg_screen(self):
        """
        检查孵蛋界面并执行收服决策
        Returns:
            bool: 是否成功处理
        """
        try:
            # 检查是否在孵蛋界面
            if self.ui_checker.is_on_hatching_screen():
                self.logger.info("当前在孵蛋界面")
                return False    
            # 检查是否需要收服
            self.mouse_controller.move_mouse_to_window_relative(269, 735)
            time.sleep(UI_CHECK_WAIT_TIME)
            # OCR识别异兽属性
            text_list = self.ocr_recognizer.capture_and_recognize(save_screenshot=True)
            self.logger.info(f"识别到数据：{text_list}")
            if not text_list:
                self.logger.warning("OCR识别失败，无法判断")
                return False
            
            # 解析异兽属性（使用收服界面专用解析方法）
            beast_list = self.parse_capture_screen_attributes(text_list)
            if not beast_list or len(beast_list) < 2:
                self.logger.warning("属性解析失败，无法判断")
                return False
            
            # 判断是否收服
            captured = self.should_capture(beast_list)
            
            if captured:
                # 点击收服按钮
                self.mouse_controller.click_capture_button()
                
                # 检查确定按钮
                if self.ui_checker.check_confirm_capture():
                    self.logger.info("点击确定按钮")
                    self.mouse_controller.move_mouse_to_window_relative(CONFIRM_BUTTON['x'], CONFIRM_BUTTON['y'])
                    
                    # 更新当前异兽属性
                    self.current_beast = beast_list[1]
                    self.logger.info(f"已收服新异兽，更新当前人物属性: {self.current_beast}")
                    
                    # 更新属性格子
                    old_special = beast_list[0].get('special_attribute')
                    new_special = beast_list[1].get('special_attribute')
                    self.slot_manager.update_attribute_slots(beast_list[1])
                    
                    self.logger.info("收服成功！")
                else:
                    self.logger.warning("未找到确定按钮")
            else:
                # 点击出售按钮
                self.mouse_controller.move_mouse_to_window_relative(SELL_BUTTON_ALT['x'], SELL_BUTTON_ALT['y'])
                self.logger.info("已出售异兽")
                if self.ui_checker.check_confirm_capture():
                    self.logger.info("点击确定按钮")
                    self.mouse_controller.move_mouse_to_window_relative(CONFIRM_BUTTON['x'], CONFIRM_BUTTON['y'])
            self.click_auto_hatch_button()
            return True
        except Exception as e:
            self.logger.error(f"检查孵蛋界面出错: {e}")
            traceback.print_exc()
            return False

    def parse_capture_screen_attributes(self, text_list):
        """
        解析收服界面异兽属性（属性名和值相邻，无冒号分隔）
        Args:
            text_list: OCR识别的文字列表
        Returns:
            list: 包含两个异兽属性的列表 [当前异兽, 新获异兽]
        """
        if not text_list or len(text_list) < 10:
            self.logger.info(f"OCR识别结果太少，无法解析（只有{len(text_list) if text_list else 0}个文本片段）")
            return None
        
        try:
            # 辅助函数：解析属性值（处理带方括号的名称）
            def parse_attribute_value(text):
                """解析属性值，处理可能的格式"""
                text = text.strip()
                # 移除百分号
                text = text.replace('%', '')
                # 移除逗号
                text = text.replace(',', '').replace('，', '')
                # 尝试转换为数字
                try:
                    return float(text) if '.' in text else int(text)
                except:
                    return text
            
            # 特殊属性优先级列表
            special_attributes = ['暴击', '连击', '闪避', '吸血', '反击', '击晕']
            
            # 辅助函数：解析单个异兽
            def parse_single_beast(text_list, start_idx, end_idx):
                """解析单个异兽的属性"""
                beast = {}
                i = start_idx
                
                while i < end_idx:
                    text = text_list[i].strip()
                    
                    # 检查是否是名称（通常带方括号）
                    if text.startswith('[') and ']' in text or text.startswith('【'):
                        beast['name'] = text
                        i += 1
                        continue
                    
                    # 检查是否是类型
                    if text.endswith('系') or text in ['玄武系', '白虎系', '青龙系', '朱雀系', '麒麟系']:
                        beast['type'] = text
                        i += 1
                        continue
                    
                    # 检查基础属性
                    if text in ['生命', '攻击', '防御', '速度', '命']:
                        if i + 1 < end_idx:
                            value = parse_attribute_value(text_list[i + 1])
                            if isinstance(value, (int, float)):
                                if text == '生命' or text == '命':
                                    beast['hp'] = int(value)
                                elif text == '攻击':
                                    beast['attack'] = int(value)
                                elif text == '防御':
                                    beast['defense'] = int(value)
                                elif text == '速度':
                                    beast['speed'] = int(value)
                                i += 2
                                continue
                    
                    # 检查特殊属性
                    if text in special_attributes:
                        if i + 1 < end_idx:
                            value = parse_attribute_value(text_list[i + 1])
                            if isinstance(value, (int, float)):
                                beast['special_attribute'] = text
                                beast['special_value'] = value
                                i += 2
                                continue
                    
                    i += 1
                
                return beast
            
            # 定位"当前异兽"和"新获异兽"标记
            current_idx = -1
            new_idx = -1
            
            for i, text in enumerate(text_list):
                if '当前' in text:
                    current_idx = i
                elif '新获异兽' in text or '新异兽' in text:
                    new_idx = i
                    break
            
            if current_idx == -1:
                self.logger.warning("未找到'当前异兽'标记")
                return None
            
            if new_idx == -1:
                self.logger.warning("未找到'新获异兽'标记")
                return None
            print(text_list)
            # 解析当前异兽（从"当前异兽"之后到"新获异兽"之前）
            current_beast = parse_single_beast(text_list, current_idx + 1, new_idx)
            
            # 解析新获异兽（从"新获异兽"之后到列表末尾）
            new_beast = parse_single_beast(text_list, new_idx + 1, len(text_list))
            
            # 设置默认值
            for beast in [current_beast, new_beast]:
                if 'name' not in beast:
                    beast['name'] = '未知'
                if 'type' not in beast:
                    beast['type'] = '普通'
                if 'hp' not in beast:
                    beast['hp'] = 0
                if 'attack' not in beast:
                    beast['attack'] = 0
                if 'defense' not in beast:
                    beast['defense'] = 0
                if 'speed' not in beast:
                    beast['speed'] = 0
                if 'special_attribute' not in beast:
                    beast['special_attribute'] = ''
                    beast['special_value'] = 0
            
            self.logger.info(f"解析收服界面成功 - 当前异兽: {current_beast}, 新获异兽: {new_beast}")
            return [current_beast, new_beast]
            
        except Exception as e:
            self.logger.error(f"解析收服界面属性出错: {e}")
            traceback.print_exc()
            return None

    def parse_beast_attributes(self, text_list):
        """
        解析异兽属性（基础属性界面，使用冒号分隔）
        Args:
            text_list: OCR识别的文字列表
        Returns:
            list: 包含两个异兽属性的列表 [旧异兽, 新异兽]
        """
        if not text_list or len(text_list) < 10:
            self.logger.info(f"OCR识别结果太少，无法解析（只有{len(text_list) if text_list else 0}个文本片段）")
            return None
        
        try:
            # 辅助函数：根据关键词查找对应的数值
            def find_value_by_keyword(text_list, keyword, search_start=0, search_end=None):
                """在指定范围内查找关键词后的数值"""
                for i in range(search_start, len(text_list) if search_end is None else search_end):
                    if keyword in text_list[i]:
                        for j in range(i+1, min(i+5, len(text_list))):
                            try:
                                value = text_list[j].replace(',', '').replace('，', '')
                                if value.isdigit():
                                    return int(value)
                            except:
                                continue
                return None
            
            # 将OCR结果分为上下两部分
            count = len(text_list) // 2
            upper_part = text_list[:count]
            lower_part = text_list[count:]
            
            # 解析旧异兽属性
            old_beast = {}
            for i, text in enumerate(upper_part):
                if '：' in text or ':' in text:
                    if '：' in text:
                        attr_name, attr_value = text.split('：', 1)
                    else:
                        attr_name, attr_value = text.split(':', 1)
                    
                    attr_name = attr_name.strip()
                    attr_value = attr_value.strip()
                    
                    if attr_name == '名称':
                        old_beast['name'] = attr_value
                    elif attr_name == '类型':
                        old_beast['type'] = attr_value
                    elif attr_name == '生命':
                        old_beast['hp'] = int(attr_value.replace(',', '').replace('，', ''))
                    elif attr_name == '攻击':
                        old_beast['attack'] = int(attr_value.replace(',', '').replace('，', ''))
                    elif attr_name == '防御':
                        old_beast['defense'] = int(attr_value.replace(',', '').replace('，', ''))
                    elif attr_name == '速度':
                        old_beast['speed'] = int(attr_value.replace(',', '').replace('，', ''))
                    elif attr_name in ['暴击', '连击', '闪避', '吸血', '反击', '击晕']:
                        old_beast['special_attribute'] = attr_name
                        old_beast['special_value'] = float(attr_value.replace('%', '').replace(',', '').replace('，', ''))
            
            # 解析新异兽属性
            new_beast = {}
            for i, text in enumerate(lower_part):
                if '：' in text or ':' in text:
                    if '：' in text:
                        attr_name, attr_value = text.split('：', 1)
                    else:
                        attr_name, attr_value = text.split(':', 1)
                    
                    attr_name = attr_name.strip()
                    attr_value = attr_value.strip()
                    
                    if attr_name == '名称':
                        new_beast['name'] = attr_value
                    elif attr_name == '类型':
                        new_beast['type'] = attr_value
                    elif attr_name == '生命':
                        new_beast['hp'] = int(attr_value.replace(',', '').replace('，', ''))
                    elif attr_name == '攻击':
                        new_beast['attack'] = int(attr_value.replace(',', '').replace('，', ''))
                    elif attr_name == '防御':
                        new_beast['defense'] = int(attr_value.replace(',', '').replace('，', ''))
                    elif attr_name == '速度':
                        new_beast['speed'] = int(attr_value.replace(',', '').replace('，', ''))
                    elif attr_name in ['暴击', '连击', '闪避', '吸血', '反击', '击晕']:
                        new_beast['special_attribute'] = attr_name
                        new_beast['special_value'] = float(attr_value.replace('%', '').replace(',', '').replace('，', ''))
            
            # 设置默认值
            for beast in [old_beast, new_beast]:
                if 'name' not in beast:
                    beast['name'] = '未知'
                if 'type' not in beast:
                    beast['type'] = '普通'
                if 'hp' not in beast:
                    beast['hp'] = 0
                if 'attack' not in beast:
                    beast['attack'] = 0
                if 'defense' not in beast:
                    beast['defense'] = 0
                if 'speed' not in beast:
                    beast['speed'] = 0
                if 'special_attribute' not in beast:
                    beast['special_attribute'] = ''
                    beast['special_value'] = 0
            
            return [old_beast, new_beast]
        except Exception as e:
            self.logger.error(f"解析异兽属性出错: {e}")
            traceback.print_exc()
            return None

    def should_capture(self, beast_list):
        """
        判断是否需要收服（主入口）
        Args:
            beast_list: 包含两个异兽属性的列表，beast_list[0]是当前异兽，beast_list[1]是新获异兽
        Returns:
            bool: 是否需要收服
        """
        if not beast_list or len(beast_list) < 2:
            self.logger.warning("异兽属性列表为空或格式不正确，无法判断")
            return False
        
        current_beast = beast_list[0]
        new_beast = beast_list[1]
        
        # 使用收服策略模块判断
        attribute_slots = self.slot_manager.get_attribute_slots()
        return self.capture_strategy.should_capture(new_beast, current_beast, self.strategy, attribute_slots)
    
    def stop(self):
        """停止程序"""
        self.running = False
        self.logger.info("收到停止信号，正在退出...")
        # 恢复电源管理
        self.power_manager.restore_sleep()
    
    def click_auto_hatch_button(self):
        """
        检查是否没有孵蛋
        """
        try:
            start_button = os.path.join(IMAGES_DIR, AUTO_EGG_IMAGE)
            result = pyautogui.locateOnScreen(start_button, confidence=0.9)
            if result:
                self.mouse_controller.click_auto_hatch_button()
                pyautogui.moveTo(1, 1)
                print("点击自动孵蛋按钮")
        except Exception as e:
            pass

    def run(self):
        """
        执行一次孵蛋任务（不循环）
        """
        self.logger.info("开始自动孵蛋任务...")
        lock = FileLock("auto_hatch.lock")
        with lock:
            try:
                relogin_button = os.path.join(IMAGES_DIR, 'relogin_button.png')
                result = pyautogui.locateOnScreen(relogin_button, confidence=0.8)
                if result:
                    self.mouse_controller.move_mouse_to_window_relative(255, 598)
                    print("点击重新登录按钮")
                    return 
            except Exception as e:
                pass
            
            self.click_auto_hatch_button()
            
            try: 
                # 检查孵蛋界面
                self.check_egg_screen()
                self.logger.info("孵蛋任务完成")
            except Exception as e:
                self.logger.error(f"运行出错: {e}")
                traceback.print_exc()


# 全局应用实例
app_instance = None
scheduler_instance = None
current_beast_cache = None  # 缓存当前异兽属性


def signal_handler(signum, frame):
    """信号处理器"""
    print("\n收到中断信号，正在停止程序...")
    global app_instance, scheduler_instance
    
    if app_instance:
        app_instance.stop()
    
    if scheduler_instance:
        scheduler_instance.shutdown()
        print("调度器已停止")
    
    sys.exit(0)


def job():
    """
    定时任务函数
    """
    global app_instance, current_beast_cache
    
    # 如果是第一次运行，创建新实例并获取基础属性
    if app_instance is None:
        app_instance = ShanHaiJing(skip_initial_ocr=True)
        current_beast_cache = app_instance.current_beast
        app_instance.logger.info("首次启动，已缓存当前异兽属性")
        # 启用防锁屏
        app_instance.power_manager.prevent_sleep()
    else:
        # 复用缓存的属性，避免重复OCR识别
        app_instance = ShanHaiJing(skip_initial_ocr=True)
        app_instance.current_beast = current_beast_cache
        app_instance.logger.info(f"使用缓存的当前异兽属性: {current_beast_cache}")
    
    app_instance.run()
    
    # 执行完成后，更新缓存（可能在收服过程中更新了）
    current_beast_cache = app_instance.current_beast


if __name__ == "__main__":
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 使用后台调度器
    scheduler_instance = BackgroundScheduler()
    
    # 每300秒执行一次
    scheduler_instance.add_job(job, 'interval', seconds=SCHEDULER_INTERVAL)
    
    try:
        scheduler_instance.start()
        print("调度器已启动，按Ctrl+C退出")
        while True:
            time.sleep(MAIN_LOOP_WAIT_TIME)
    except (KeyboardInterrupt, SystemExit):
        scheduler_instance.shutdown()
        print("调度器已停止")