# -*- coding: utf-8 -*-
"""
山海北荒卷自动化脚本
功能：自动孵蛋、识别异兽属性、智能收服
"""

import os
import time
import datetime
import logging
import logging.handlers
import pygetwindow as gw
import pyautogui 
import traceback
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from paddleocr import PaddleOCR

# 初始化OCR
ocr = PaddleOCR(
    lang="ch",
    text_detection_model_name="PP-OCRv5_server_det",
    text_recognition_model_name="PP-OCRv5_server_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
)


class ShanHaiJing:
    """
    山海北荒卷自动化主类
    """
    
    # ==================== 初始化和配置 ====================
    
    def __init__(self, keyword="山海北荒卷"):
        """
        初始化山海北荒卷自动化脚本
        Args:
            keyword: 窗口标题关键词
        """
        self.keyword = keyword
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.filtered_windows = self.filter_windows_by_title(self.keyword)
        self.previous_beast = None  # 记录之前的异兽属性
        self.current_beast = None  # 记录当前异兽属性
        
        # 6种特殊属性
        self.special_attributes = ['暴击', '连击', '闪避', '反击', '击晕', '吸血']
        
        # 追踪每种属性的格子数量（实际使用）
        self.attribute_slots = {attr: 0 for attr in self.special_attributes}
        self.total_slots = 9  # 总格子数
        
        # 属性格子状态文件路径
        self.slots_file = os.path.join(self.base_dir, "attribute_slots.json")
        
        # 收服策略配置
        self.strategy = 'focused'  # 可选: 'focused'(专注), 'balanced'(平衡), 'optimal'(最优)
        self.target_attributes = ['暴击', '连击', '闪避']  # 专注策略的目标属性（支持多个）
        
        # 基础属性权重（用于计算综合评分）
        self.attribute_weights = {
            'hp': 1.0,      # 生命权重
            'attack': 1.2,  # 攻击权重（攻击通常更重要）
            'defense': 1.0,  # 防御权重
            'speed': 1.1    # 速度权重
        }
        
        # 截图目录
        self.screenshot_dir = os.path.join(self.base_dir, "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # 配置日志
        self.log_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.setup_logging()
        
        # 加载属性格子状态
        self.load_attribute_slots()

        # 激活窗口
        if not self.filtered_windows:
            print(f"未找到包含关键词: [{self.keyword}]的窗口")
            return
        self.filtered_windows[0].activate()
    
    def setup_logging(self):
        """
        配置日志系统 - 按天分割日志文件
        """
        # 创建日志文件名（按日期）
        log_filename = datetime.datetime.now().strftime("beast_capture_%Y%m%d.log")
        log_filepath = os.path.join(self.log_dir, log_filename)
        
        # 创建logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # 日志格式
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # 1. 文件处理器 - 使用TimedRotatingFileHandler按天分割日志
        # when='midnight' 表示每天午夜分割
        # interval=1 表示每天分割一次
        # backupCount=30 表示保留30天的日志
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_filepath,
            when='midnight',
            interval=1,
            backupCount=30,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y%m%d.log"  # 设置日志文件名后缀格式
        
        # 2. 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 记录启动信息
        self.logger.info("=" * 80)
        self.logger.info(f"山海北荒卷自动化脚本启动 - 目标属性: {', '.join(self.target_attributes)}")
        self.logger.info(f"日志文件: {log_filepath}")
        self.logger.info("=" * 80)
    
    # ==================== 属性格子管理 ====================
    
    def update_attribute_slots(self, old_special, new_special, captured):
        """
        更新属性格子数量
        Args:
            old_special: 旧异兽的特殊属性
            new_special: 新异兽的特殊属性
            captured: 是否收服了新异兽
        """
        if captured:
            # 收服新异兽：减少旧属性格子，增加新属性格子
            if old_special and old_special in self.attribute_slots:
                self.attribute_slots[old_special] = max(0, self.attribute_slots[old_special] - 1)
            if new_special and new_special in self.attribute_slots:
                self.attribute_slots[new_special] = min(self.total_slots, self.attribute_slots[new_special] + 1)
        else:
            # 未收服：保持不变（旧属性格子不变）
            pass
        
        # 记录当前格子状态
        self.logger.info("【当前格子状态】")
        for attr, count in self.attribute_slots.items():
            self.logger.info(f"  {attr}: {count}/{self.total_slots}")
        
        # 保存到文件
        self.save_attribute_slots()
    
    def load_attribute_slots(self):
        """
        从文件加载属性格子状态
        """
        import json
        try:
            if os.path.exists(self.slots_file):
                with open(self.slots_file, 'r', encoding='utf-8') as f:
                    loaded_slots = json.load(f)
                    # 验证加载的数据
                    if isinstance(loaded_slots, dict):
                        # 确保所有属性都存在
                        for attr in self.special_attributes:
                            if attr in loaded_slots:
                                self.attribute_slots[attr] = loaded_slots[attr]
                        self.logger.info(f"【加载格子状态】从文件加载成功: {self.attribute_slots}")
                    else:
                        self.logger.warning(f"【加载格子状态】文件格式错误，使用默认值")
            else:
                self.logger.info(f"【加载格子状态】文件不存在，使用默认值")
        except Exception as e:
            self.logger.error(f"【加载格子状态】加载失败: {e}，使用默认值")
    
    def save_attribute_slots(self):
        """
        保存属性格子状态到文件
        """
        import json
        try:
            with open(self.slots_file, 'w', encoding='utf-8') as f:
                json.dump(self.attribute_slots, f, ensure_ascii=False, indent=2)
            self.logger.debug(f"【保存格子状态】保存成功: {self.attribute_slots}")
        except Exception as e:
            self.logger.error(f"【保存格子状态】保存失败: {e}")
    
    def calculate_comprehensive_score(self, beast):
        """
        计算异兽的综合评分
        Args:
            beast: 异兽属性字典
        Returns:
            float: 综合评分
        """
        score = 0
        score += beast.get('hp', 0) * self.attribute_weights['hp']
        score += beast.get('attack', 0) * self.attribute_weights['attack']
        score += beast.get('defense', 0) * self.attribute_weights['defense']
        score += beast.get('speed', 0) * self.attribute_weights['speed']
        
        # 特殊属性加成
        special_value = beast.get('special_value', 0)
        if special_value and isinstance(special_value, str):
            try:
                special_value = int(special_value)
            except:
                special_value = 0
        score += special_value * 10  # 特殊属性值加成
        
        return score
    
    def get_optimal_target_attribute(self):
        """
        获取最优目标属性（格子数量最多的属性）
        Returns:
            str: 最优目标属性
        """
        # 找出格子数量最多的属性
        max_count = max(self.attribute_slots.values())
        candidates = [attr for attr, count in self.attribute_slots.items() if count == max_count]
        
        # 如果有多个属性格子数量相同，优先选择特殊属性价值高的
        # 这里简单返回第一个
        return candidates[0] if candidates else '暴击'
    
    # ==================== 收服策略判断 ====================
    
    def should_capture_optimal(self, old_beast, new_beast):
        """
        最优策略：最大化收益
        Args:
            old_beast: 旧异兽属性
            new_beast: 新异兽属性
        Returns:
            bool: 是否收服
        """
        old_special = old_beast.get('special_attribute')
        new_special = new_beast.get('special_attribute')
        new_name = new_beast.get('name', '')
        
        # 优先收服稀有异兽
        if any(keyword in new_name for keyword in ['神兽', '至尊神兽', '鸿蒙祖兽', '混沌源兽']):
            self.logger.info("【最优策略】新异兽为稀有异兽，优先收服")
            return True
        
        # 如果新异兽的特殊属性格子数量更多，优先收服
        old_slots = self.attribute_slots.get(old_special, 0)
        new_slots = self.attribute_slots.get(new_special, 0)
        
        if new_slots > old_slots:
            self.logger.info(f"【最优策略】新属性({new_special})格子数({new_slots}) > 旧属性({old_special})格子数({old_slots})，收服")
            return True
        
        # 如果格子数量相同，比较综合评分
        if new_slots == old_slots:
            old_score = self.calculate_comprehensive_score(old_beast)
            new_score = self.calculate_comprehensive_score(new_beast)
            if new_score > old_score:
                self.logger.info(f"【最优策略】格子数相同，新异兽评分({new_score}) > 旧异兽评分({old_score})，收服")
                return True
        
        return False
    
    def should_capture_balanced(self, old_beast, new_beast):
        """
        平衡策略：在多种属性间保持平衡
        Args:
            old_beast: 旧异兽属性
            new_beast: 新异兽属性
        Returns:
            bool: 是否收服
        """
        old_special = old_beast.get('special_attribute')
        new_special = new_beast.get('special_attribute')
        new_name = new_beast.get('name', '')
        
        # 优先收服稀有异兽
        if any(keyword in new_name for keyword in ['神兽', '至尊神兽', '鸿蒙祖兽', '混沌源兽']):
            self.logger.info("【平衡策略】新异兽为稀有异兽，优先收服")
            return True
        
        # 计算所有属性格子数量的标准差，衡量平衡度
        counts = list(self.attribute_slots.values())
        mean = sum(counts) / len(counts)
        variance = sum((x - mean) ** 2 for x in counts) / len(counts)
        std_dev = variance ** 0.5
        
        # 如果当前平衡度较好（标准差小），只收服评分更高的
        if std_dev < 2:
            old_score = self.calculate_comprehensive_score(old_beast)
            new_score = self.calculate_comprehensive_score(new_beast)
            if new_score > old_score:
                self.logger.info(f"【平衡策略】当前平衡度较好，新异兽评分({new_score}) > 旧异兽评分({old_score})，收服")
                return True
        else:
            # 如果不平衡，优先收服格子数少的属性
            old_slots = self.attribute_slots.get(old_special, 0)
            new_slots = self.attribute_slots.get(new_special, 0)
            if new_slots < old_slots:
                self.logger.info(f"【平衡策略】当前不平衡，优先收服格子少的属性({new_special}: {new_slots} < {old_special}: {old_slots})，收服")
                return True
        
        return False
    
    def should_capture_focused(self, old_beast, new_beast):
        """
        专注策略：专注于目标属性，同时快速提升基础属性
        Args:
            old_beast: 旧异兽属性
            new_beast: 新异兽属性
        Returns:
            bool: 是否收服
        """
        old_special = old_beast.get('special_attribute')
        new_special = new_beast.get('special_attribute')
        new_name = new_beast.get('name', '')
        
        # 优先收服稀有异兽
        if any(keyword in new_name for keyword in ['神兽', '至尊神兽', '鸿蒙祖兽', '混沌源兽']):
            self.logger.info("【专注策略】新异兽为稀有异兽，优先收服")
            return True
        
        # 如果新异兽是目标属性之一，收服（快速提升专一特殊属性）
        if new_special in self.target_attributes:
            self.logger.info(f"【专注策略】新异兽是目标属性({new_special})，收服")
            return True
        
        # 如果旧异兽不是目标属性，新异兽也不是目标属性，比较基础属性
        # 只要新异兽的基础属性更高就收服（快速提升基础属性）
        if old_special not in self.target_attributes and new_special not in self.target_attributes:
            # 计算基础属性总分（不包含特殊属性）
            old_basic_score = (
                old_beast.get('hp', 0) +
                old_beast.get('attack', 0) +
                old_beast.get('defense', 0) +
                old_beast.get('speed', 0)
            )
            new_basic_score = (
                new_beast.get('hp', 0) +
                new_beast.get('attack', 0) +
                new_beast.get('defense', 0) +
                new_beast.get('speed', 0)
            )
            
            if new_basic_score > old_basic_score:
                self.logger.info(f"【专注策略】新旧异兽都不是目标属性，新异兽基础属性({new_basic_score}) > 旧异兽基础属性({old_basic_score})，收服")
                return True
        
        return False
    
    def should_capture(self, beast_list):
        """
        判断是否需要收服（主入口）
        Args:
            beast_list: 包含两个异兽属性的列表，beast_list[0]是旧属性，beast_list[1]是新属性
        Returns:
            bool: 是否需要收服
        """
        if not beast_list or len(beast_list) < 2:
            self.logger.warning("异兽属性列表为空或格式不正确，无法判断")
            return False
        
        old_beast = beast_list[0]
        new_beast = beast_list[1]
        
        old_special = old_beast.get('special_attribute')
        new_special = new_beast.get('special_attribute')
        new_name = new_beast.get('name', '')
        
        # 记录旧异兽属性
        self.logger.info("-" * 60)
        self.logger.info("【旧异兽属性】")
        self.logger.info(f"  名称: {old_beast.get('name')}")
        self.logger.info(f"  类型: {old_beast.get('type')}")
        self.logger.info(f"  生命: {old_beast.get('hp')}")
        self.logger.info(f"  攻击: {old_beast.get('attack')}")
        self.logger.info(f"  防御: {old_beast.get('defense')}")
        self.logger.info(f"  速度: {old_beast.get('speed')}")
        self.logger.info(f"  特殊属性: {old_special} ({old_beast.get('special_value')}%)")
        
        # 记录新异兽属性
        self.logger.info("【新异兽属性】")
        self.logger.info(f"  名称: {new_beast.get('name')}")
        self.logger.info(f"  类型: {new_beast.get('type')}")
        self.logger.info(f"  生命: {new_beast.get('hp')}")
        self.logger.info(f"  攻击: {new_beast.get('attack')}")
        self.logger.info(f"  防御: {new_beast.get('defense')}")
        self.logger.info(f"  速度: {new_beast.get('speed')}")
        self.logger.info(f"  特殊属性: {new_special} ({new_beast.get('special_value')}%)")
        
        # 根据策略选择判断逻辑
        self.logger.info(f"【当前策略】{self.strategy}")
        
        if self.strategy == 'focused':
            # 专注策略
            captured = self.should_capture_focused(old_beast, new_beast)
        elif self.strategy == 'balanced':
            # 平衡策略
            captured = self.should_capture_balanced(old_beast, new_beast)
        elif self.strategy == 'optimal':
            # 最优策略
            captured = self.should_capture_optimal(old_beast, new_beast)
        else:
            # 默认使用最优策略
            self.logger.warning(f"未知策略 {self.strategy}，使用最优策略")
            captured = self.should_capture_optimal(old_beast, new_beast)
        
        # 更新属性格子数量
        self.update_attribute_slots(old_special, new_special, captured)
        
        self.logger.info("-" * 60)
        return captured
    
    # ==================== 窗口管理 ====================
    
    def get_active_window_region(self):
        """
        获取当前激活窗口的查找区域
        Returns:
            tuple: 窗口区域坐标 (x, y, width, height)
        """
        active_window = self.filtered_windows[0]
        try:
            active_window.activate() 
        except Exception as e:
            print(f"激活窗口时出错: {e}")
            return None
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
    
    # ==================== 鼠标操作 ====================
    
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
        self.logger.debug(f"移动鼠标：窗口内相对坐标 ({clamped_x}, {clamped_y}) → 屏幕绝对坐标 ({absolute_x}, {absolute_y})")
        
        # 移动鼠标并点击
        duration = 1 if smooth else 0
        pyautogui.moveTo(absolute_x, absolute_y, duration=duration)
        self.logger.debug("鼠标移动完成！")
        pyautogui.sleep(0.5)
        pyautogui.click()
        self.logger.debug(f"已点击窗口内坐标{clamped_x}, {clamped_y}")
    
    def click_auto_hatch_button(self):
        """
        点击自动孵蛋按钮
        """
        file_path = os.path.join(self.base_dir, "auto_egg.png")
        if self.is_image_exist(file_path):
            # 点击相关按钮执行自动孵蛋操作
            self.logger.info("点击自动孵蛋按钮")
            self.move_mouse_to_window_relative(259, 888)  # 第一个按钮位置
            self.move_mouse_to_window_relative(243, 690)  # 第二个按钮位置
    
    # ==================== 界面检查 ====================
    
    def needs_to_capture(self):
        """
        判断是否需要收服
        Returns:
            bool: 是否需要收服
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
                    self.logger.debug(f"找到图片！")
                    self.logger.debug(f"图片屏幕坐标：左上角({image_position.left}, {image_position.top}) → 中心点({center_x}, {center_y})")
                    self.logger.debug(f"图片在窗口内相对坐标：({relative_x}, {relative_y})")
                else:
                    self.logger.debug(f"找到图片！")
                    self.logger.debug(f"图片屏幕坐标：左上角({image_position.left}, {image_position.top}) → 中心点({center_x}, {center_y})")
                return image_position
            else:
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
        file_path = os.path.join(self.base_dir, "egg.png")
        retry_count = 15
        image_list = ['egg1.png', 'egg2.png', 'egg3.png', 'egg4.png']
        while retry_count:
            for image in image_list:
                file_path = os.path.join(self.base_dir, image)
                if self.is_image_exist(file_path):
                    return True
            time.sleep(1)
            retry_count -= 1
        return False
    
    def check_confim_capture(self):
        """
        检查是否有确定按钮
        Returns:
            bool: 是否有确定按钮
        """
        file_path = os.path.join(self.base_dir, "confirm.png")
        retry_count = 5
        while retry_count:
            if self.is_image_exist(file_path):
                return True
            time.sleep(1)
            retry_count -= 1
        return False
    
    # ==================== OCR和属性解析 ====================
    
    def capture_and_recognize(self):
        """
        截图并使用OCR识别文字
        Returns:
            list: 识别到的文字列表（包含坐标和文字）
        """
        try:
            # 获取窗口区域
            window_region = self.get_active_window_region()
            if not window_region:
                return None
            
            # 计算截图区域（相对于窗口的固定坐标）
            # 起点: (27, 199), 终点: (460, 783)
            screenshot_region = (
                window_region[0] + 27,      # x: 窗口左上角x + 27
                window_region[1] + 199,     # y: 窗口左上角y + 199
                460 - 27,                   # width: 433
                783 - 199                   # height: 584
            )
            
            # 截图
            screenshot = pyautogui.screenshot(region=screenshot_region)
            
            # 保存截图
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.screenshot_dir, f"beast_{timestamp}.png")
            screenshot.save(screenshot_path)
            self.logger.info(f"截图已保存到: {screenshot_path}")
            
            # OCR识别
            result = ocr.predict(screenshot_path)
            
            # 提取文字和坐标信息
            if result and isinstance(result, list) and len(result) > 0:
                    if isinstance(result[0], dict):
                        text_list = result[0].get('rec_texts', [])
                    else:
                        # 尝试直接从结果中提取文字
                        text_list = []
                        for item in result:
                            if isinstance(item, list) and len(item) > 1:
                                if item:
                                    text_list.append(item[1][0])
                    return text_list
            return []
        except Exception as e:
            self.logger.error(f"OCR识别出错: {e}")
            return []
    
    def parse_beast_attributes(self, text_list):
        """
        解析异兽属性
        Args:
            text_list: OCR识别的文字列表
        Returns:
            dict: 包含异兽属性的字典
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
                        # 查找关键词后面的数值
                        for j in range(i+1, min(i+5, len(text_list))):
                            try:
                                # 尝试转换为数字
                                value = text_list[j].replace(',', '').replace('，', '')
                                if value.isdigit():
                                    return int(value)
                            except:
                                continue
                return None
            
            # 辅助函数：根据Y坐标将文本分为上下两部分（旧异兽和新异兽）
            def split_by_y_coordinate(text_list):
                """根据Y坐标将OCR结果分为上下两部分"""
                if not text_list:
                    return [], []
                count = len(text_list) // 2
                return text_list[:count], text_list[count:]
            
            # 将OCR结果分为上下两部分
            upper_part, lower_part = split_by_y_coordinate(text_list)
            
            print(f"上半部分（旧异兽）有{len(upper_part)}个文本片段")
            print(f"下半部分（新异兽）有{len(lower_part)}个文本片段")
            
            # 解析旧异兽属性
            old_attribute = {}
            if upper_part:
                # 名称通常是第一个文本
                old_attribute['name'] = upper_part[0] if upper_part else ''
                # 类型通常是第二个文本
                old_attribute['type'] = upper_part[1] if len(upper_part) > 1 else ''
                
                # 使用关键词查找属性值
                old_attribute['hp'] = find_value_by_keyword(upper_part, '生命') or 0
                old_attribute['attack'] = find_value_by_keyword(upper_part, '攻击') or 0
                old_attribute['defense'] = find_value_by_keyword(upper_part, '防御') or 0
                old_attribute['speed'] = find_value_by_keyword(upper_part, '速度') or 0
                
                # 特殊属性和数值
                special_keywords = ['闪避', '吸血', '暴击', '反击', '坚韧', '穿透', '命中', '格挡']
                for keyword in special_keywords:
                    if find_value_by_keyword(upper_part, keyword):
                        old_attribute['special_attribute'] = keyword
                        old_attribute['special_value'] = find_value_by_keyword(upper_part, keyword)
                        break
                
                if 'special_attribute' not in old_attribute:
                    old_attribute['special_attribute'] = ''
                    old_attribute['special_value'] = '0'
            
            # 解析新异兽属性
            new_attribute = {}
            if lower_part:
                # 名称通常是第一个文本
                new_attribute['name'] = lower_part[0] if lower_part else ''
                # 类型通常是第二个文本
                new_attribute['type'] = lower_part[1] if len(lower_part) > 1 else ''
                
                # 使用关键词查找属性值
                new_attribute['hp'] = find_value_by_keyword(lower_part, '生命') or 0
                new_attribute['attack'] = find_value_by_keyword(lower_part, '攻击') or 0
                new_attribute['defense'] = find_value_by_keyword(lower_part, '防御') or 0
                new_attribute['speed'] = find_value_by_keyword(lower_part, '速度') or 0
                
                # 特殊属性和数值
                special_keywords = ['闪避', '吸血', '暴击', '反击', '连击', '击晕']
                for keyword in special_keywords:
                    if find_value_by_keyword(lower_part, keyword):
                        new_attribute['special_attribute'] = keyword
                        new_attribute['special_value'] = find_value_by_keyword(lower_part, keyword)
                        break
                
                if 'special_attribute' not in new_attribute:
                    new_attribute['special_attribute'] = ''
                    new_attribute['special_value'] = '0'
            
            attributes = [old_attribute, new_attribute]
            
            self.logger.info("解析结果:")
            self.logger.info(f"  旧异兽: {old_attribute}")
            self.logger.info(f"  新异兽: {new_attribute}")
            
            return attributes
            
        except Exception as e:
            self.logger.info(f"解析异兽属性出错: {e}")
            import traceback
            self.logger.info(traceback.format_exc())
            return None
    
    # ==================== 主要业务逻辑 ====================
    
    def check_egg_screen(self):
        """
        检查当前窗口是否在蛋界面并执行相应操作
        """
        # 检查是否在孵蛋界面
        if self.is_on_hatching_screen():
            self.logger.info("当前在孵蛋界面")
        else:
            # 先点击自动孵蛋按钮
            self.logger.info("自动孵蛋停止")
            self.move_mouse_to_window_relative(272, 754)
            time.sleep(1)
            # 截图并识别异兽属性
            self.logger.info("开始OCR识别异兽属性...")
            text_list = self.capture_and_recognize()
            beast_list = self.parse_beast_attributes(text_list)
            
            # 判断是否需要收服
            should_capture_beast = self.should_capture(beast_list)
            
            if should_capture_beast:
                self.logger.info("执行收服操作")
                # 记录新异兽属性作为当前异兽属性
                if beast_list and len(beast_list) >= 2:
                    self.current_beast = beast_list[1].copy()
                    self.logger.info(f"已更新当前异兽属性: {self.current_beast.get('name')} ({self.current_beast.get('special_attribute')})")
                
                self.move_mouse_to_window_relative(350, 748)  # 收服按钮位置
                # 再点击出售按钮
                self.move_mouse_to_window_relative(168, 748)  # 出售按钮位置
                time.sleep(1)
                # 判断是否出现确定按钮
                if self.check_confim_capture():
                    self.logger.info("点击确定按钮")
                    self.move_mouse_to_window_relative(354, 599)
            else:
                self.logger.info("不收服，直接出售")
                # 直接点击出售按钮
                self.move_mouse_to_window_relative(168, 748)  # 出售按钮位置
                if self.check_confim_capture():
                    self.logger.info("点击确定按钮")
                    self.move_mouse_to_window_relative(354, 599)
    
    def run(self):
        """
        主循环 - 持续执行自动孵蛋和检查蛋界面的操作
        """
        try:
            self.logger.info("开始运行山海北荒卷自动化脚本...")
            time.sleep(2)
            # while True:
            if self.check_confim_capture():
                self.logger.info("点击确认按钮")
                self.move_mouse_to_window_relative(231, 608)  # 确认按钮位置
                time.sleep(1)  # 循环间隔
                
            self.click_auto_hatch_button()
            self.check_egg_screen()
            time.sleep(1)  # 循环间隔
        except KeyboardInterrupt:
            self.logger.warning("程序被用户中断")
        except Exception as error:
            self.logger.error(f"程序运行出错：{error}")
            # 出错后尝试重新点击自动孵蛋按钮
            print(traceback.format_exc())
            self.click_auto_hatch_button()
    
    # ==================== 上下文管理 ====================
    
    def __enter__(self):
        return self 
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.logger.info("上下文对象销毁")
        for attr in list(vars(self)):
            delattr(self, attr)
        return False

def job():
    """
    定时任务函数
    """ 
    with ShanHaiJing("山海北荒卷") as app:
        app.run()


# ==================== 主程序入口 ====================

if __name__ == '__main__':
    # scheduler = BlockingScheduler()
    scheduler = BackgroundScheduler()
    
    # 配置调度器默认参数
    job_defaults = {
        'coalesce': True,  # 合并错过的任务
        'max_instances': 1,  # 最多同时运行1个实例
        'misfire_grace_time': 300  # 允许5分钟的延迟执行
    }
    scheduler.configure(job_defaults=job_defaults)
    
    scheduler.add_job(job, 'interval', seconds=300)  # 每300秒执行一次
    try:
        print('调度器开始运行...')
        scheduler.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown(wait=False)  # wait=False 表示不等待当前任务完成
        print('调度器已停止')