# -*- coding: utf-8 -*-
import os
import time
import datetime
import logging
import pygetwindow as gw
import pyautogui 
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from paddleocr import PaddleOCR


class ShanHaiJing:
    def __init__(self, keyword="山海北荒卷"):
        self.keyword = keyword
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.filtered_windows = self.filter_windows_by_title(self.keyword)
        self.ocr = PaddleOCR(lang="ch", use_textline_orientation=False, cpu_threads=8, text_det_limit_side_len=640)
        self.previous_beast = None  # 记录之前的异兽属性
        self.target_attribute = '暴击'  # 目标属性，可以修改为其他属性如'吸血'、'暴击'等
        self.screenshot_dir = os.path.join(self.base_dir, "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # 配置日志
        self.log_dir = os.path.join(self.base_dir, "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.setup_logging()
        
        if not self.filtered_windows:
            print(f"未找到包含关键词: [{self.keyword}]的窗口")
            return
        self.filtered_windows[0].activate()
    
    def setup_logging(self):
        """
        配置日志系统
        """
        # 创建日志文件名（按日期）
        log_filename = datetime.datetime.now().strftime("beast_capture_%Y%m%d.log")
        log_filepath = os.path.join(self.log_dir, log_filename)
        
        # 配置日志格式
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filepath, encoding='utf-8'),
                logging.StreamHandler()  # 同时输出到控制台
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("=" * 80)
        self.logger.info(f"山海北荒卷自动化脚本启动 - 目标属性: {self.target_attribute}")
        self.logger.info("=" * 80)
    
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
        """

        file_path = os.path.join(self.base_dir, "confirm.png")
        retry_count = 5
        while retry_count:
            if self.is_image_exist(file_path):
                return True
            time.sleep(1)
            retry_count -= 1
        return False
    
    def capture_and_recognize(self):
        """
        截图并使用OCR识别文字
        Returns:
            list: 识别到的文字列表
        """
        try:
            # 获取窗口区域
            region = self.get_active_window_region()
            if not region:
                return None
            
            # 截图
            screenshot = pyautogui.screenshot(region=region)
            
            # 保存截图
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            screenshot_path = os.path.join(self.screenshot_dir, f"beast_{timestamp}.png")
            screenshot.save(screenshot_path)
            self.logger.info(f"截图已保存到: {screenshot_path}")
            
            # OCR识别
            result = self.ocr.predict(screenshot_path)
            
            # 提取文字
            if result and isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict):
                    text_list = result[0].get('rec_texts', [])
                else:
                    # 尝试直接从结果中提取文字
                    text_list = []
                    for item in result:
                        if isinstance(item, list) and len(item) > 1:
                            text_list.append(item[1][0])
                
                self.logger.debug(f"识别到{len(text_list)}个文本片段:")
                self.logger.debug(text_list)
                return text_list
            
            return None
        except Exception as e:
            self.logger.error(f"OCR识别出错: {e}")
            return None
    
    def parse_beast_attributes(self, text_list):
        """
        解析异兽属性
        Args:
            text_list: OCR识别的文字列表
        Returns:
            dict: 包含异兽属性的字典
        """
        if not text_list:
            return None
        attributes = []
        old_attribute = {
            'name': text_list[0],
            'type': text_list[1],
            'hp': int(text_list[4]),
            'attack': int(text_list[8]),
            'defense': int(text_list[11]),
            'speed': int(text_list[15]),
            'special_attribute': text_list[5],  # 特殊属性（如闪避、吸血等）
            'special_value': text_list[6]  # 特殊属性的数值
        }
        new_attribute = {
            'name': text_list[21],
            'type': text_list[22],
            'hp': int(text_list[25]),
            'attack': int(text_list[29]),
            'defense': int(text_list[32]),
            'speed': int(text_list[34]),
            'special_attribute': text_list[26],  # 特殊属性（如闪避、吸血等）
            'special_value': text_list[27]  # 特殊属性的数值
        }
        attributes.append(old_attribute)
        attributes.append(new_attribute)
        
        return attributes
    
    def should_capture(self, beast_list):
        """
        判断是否需要收服
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
        
        # 规则1: 如果旧属性和新属性的特殊属性相同
        if old_special == new_special:
            self.logger.info("【判断规则1】新旧异兽特殊属性相同")
            self.logger.info("【属性对比】")
            hp_better = new_beast.get('hp', 0) > old_beast.get('hp', 0)
            attack_better = new_beast.get('attack', 0) > old_beast.get('attack', 0)
            defense_better = new_beast.get('defense', 0) > old_beast.get('defense', 0)
            speed_better = new_beast.get('speed', 0) > old_beast.get('speed', 0)
            
            self.logger.info(f"  生命: {new_beast.get('hp')} vs {old_beast.get('hp')} - {'✓ 更好' if hp_better else '✗ 更差'}")
            self.logger.info(f"  攻击: {new_beast.get('attack')} vs {old_beast.get('attack')} - {'✓ 更好' if attack_better else '✗ 更差'}")
            self.logger.info(f"  防御: {new_beast.get('defense')} vs {old_beast.get('defense')} - {'✓ 更好' if defense_better else '✗ 更差'}")
            self.logger.info(f"  速度: {new_beast.get('speed')} vs {old_beast.get('speed')} - {'✓ 更好' if speed_better else '✗ 更差'}")
            
            if hp_better or attack_better or defense_better or speed_better:
                self.logger.info(f"✓ 判断结果: 新异兽至少有一项属性更好，需要收服")
                self.logger.info("-" * 60)
                return True
            else:
                self.logger.info(f"✗ 判断结果: 新异兽所有属性都不比旧的好，不收服")
                self.logger.info("-" * 60)
                return False
        
        # 规则2: 如果新异兽的特殊属性是目标属性，旧异兽不是目标属性
        elif new_special == self.target_attribute and old_special != self.target_attribute:
            self.logger.info("【判断规则2】新异兽是目标属性，旧异兽不是目标属性")
            
            # 检查新异兽名称是否包含"神兽"或"至尊神兽"
            if '神兽' in new_name:
                self.logger.info(f"✓ 判断结果: 新异兽名称包含'神兽'（{new_name}），收服")
                self.logger.info("-" * 60)
                return True
            elif '至尊神兽' in new_name:
                self.logger.info(f"✓ 判断结果: 新异兽名称包含'至尊神兽'（{new_name}），收服")
                self.logger.info("-" * 60)
                return True
            elif '鸿蒙祖兽' in new_name:
                self.logger.info(f"✓ 判断结果: 新异兽名称包含'鸿蒙祖兽'（{new_name}），收服")
                self.logger.info("-" * 60)
                return True
            elif '混沌源兽' in new_name:
                self.logger.info(f"✓ 判断结果: 新异兽名称包含'混沌源兽'（{new_name}），收服")
                self.logger.info("-" * 60)
                return True
            else:
                self.logger.info(f"✗ 判断结果: 新异兽名称不包含'神兽'（{new_name}），不收服")
                self.logger.info("-" * 60)
                return False
        
        # 其他情况不收服
        else:
            self.logger.info("【判断规则3】其他情况")
            if new_special != self.target_attribute:
                self.logger.info(f"✗ 判断结果: 新异兽不是目标属性（{self.target_attribute}），不收服")
            else:
                self.logger.info(f"✗ 判断结果: 旧异兽也是目标属性，不满足收服条件，不收服")
            self.logger.info("-" * 60)
            return False


    
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
            self.move_mouse_to_window_relative(272,754)
            
            # 截图并识别异兽属性
            self.logger.info("开始OCR识别异兽属性...")
            text_list = self.capture_and_recognize()
            beast_list = self.parse_beast_attributes(text_list)
            
            # 判断是否需要收服
            should_capture_beast = self.should_capture(beast_list)
            
            if should_capture_beast:
                self.logger.info("执行收服操作")
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
            self.click_auto_hatch_button()
    
    def __enter__(self):
        return self 
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.logger.info("上下文对象销毁")
        for attr in list(vars(self)):
            delattr(self, attr)
        return False

def job():
    with ShanHaiJing("山海北荒卷") as app:
        app = ShanHaiJing("山海北荒卷")
        app.run()


    
if __name__ == '__main__':
    # scheduler = BlockingScheduler()
    scheduler = BackgroundScheduler()
    scheduler.add_job(job, 'interval', seconds=180)  # 每5秒执行
    try:
        print('调度器开始运行...')
        scheduler.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.shutdown(wait=False)  # wait=False 表示不等待当前任务完成
        print('调度器已停止')