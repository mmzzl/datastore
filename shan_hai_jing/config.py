# -*- coding: utf-8 -*-
"""
配置文件 - 包含所有常量和配置项
"""

import os

# ==================== 基础配置 ====================

# 窗口标题关键词
WINDOW_KEYWORD = "山海北荒卷"

# 基础目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据目录（存放中间文件、截图等）
DATA_DIR = os.path.join(BASE_DIR, "data")

# 截图目录
SCREENSHOT_DIR = os.path.join(DATA_DIR, "screenshots")

# 图片目录
IMAGES_DIR = os.path.join(BASE_DIR, "images")

# 日志目录
LOG_DIR = os.path.join(BASE_DIR, "logs")

# 属性格子状态文件路径
SLOTS_FILE = os.path.join(DATA_DIR, "attribute_slots.json")

# ==================== 异兽属性配置 ====================

# 6种特殊属性
SPECIAL_ATTRIBUTES = ['暴击', '连击', '闪避', '反击', '击晕', '吸血']

# 总格子数
TOTAL_SLOTS = 9

# 基础属性权重（用于计算综合评分）
ATTRIBUTE_WEIGHTS = {
    'hp': 1.0,      # 生命权重
    'attack': 1.2,  # 攻击权重（攻击通常更重要）
    'defense': 1.0,  # 防御权重
    'speed': 1.1    # 速度权重
}

# ==================== 收服策略配置 ====================

# 收服策略（可选: 'focused'(专注), 'balanced'(平衡), 'optimal'(最优)）
STRATEGY = 'focused'

# 专注策略的目标属性（支持多个）
TARGET_ATTRIBUTES = ['暴击']

# 稀有异兽关键词
RARE_BEAST_KEYWORDS = ['神兽', '至尊神兽', '鸿蒙祖兽', '混沌源兽']

# ==================== OCR配置 ====================

# OCR语言
OCR_LANG = "ch"

# OCR模型配置
OCR_DETECTION_MODEL = "PP-OCRv5_server_det"
OCR_RECOGNITION_MODEL = "PP-OCRv5_server_rec"

# OCR类型选择（可选: 'paddle', 'umi'）
OCR_TYPE = "umi"

# UMI-OCR API配置
UMI_OCR_API_URL = "http://localhost:1224/api/ocr"

# ==================== 截图区域配置 ====================

# 当前异兽属性截图区域（相对于窗口）
CURRENT_BEAST_REGION = {
    'x': 34,
    'y': 237,
    'width': 425,
    'height': 499
}

# 异兽对比截图区域（相对于窗口）
BEAST_COMPARE_REGION = {
    'x': 27,
    'y': 199,
    'width': 433,
    'height': 584
}

# ==================== 鼠标操作配置 ====================

# 自动孵蛋按钮位置
AUTO_HATCH_BUTTONS = [
    {'x': 259, 'y': 888},  # 第一个按钮
    {'x': 243, 'y': 690}   # 第二个按钮
]

# 重新登录按钮位置
RELOGIN_BUTTON = {'x': 255, 'y': 598}

# 收服按钮位置
CAPTURE_BUTTON = {'x': 350, 'y': 748}

# 出售按钮位置
SELL_BUTTON = {'x': 168, 'y': 748}

# 确认按钮位置
CONFIRM_BUTTON = {'x': 354, 'y': 599}

# 自动孵蛋停止按钮位置
STOP_AUTO_HATCH_BUTTON = {'x': 272, 'y': 754}

# 人物按钮位置（用于加载属性格子）
CHARACTER_BUTTON = {'x': 443, 'y': 326}

# 返回按钮位置（用于返回主界面）
BACK_BUTTON = {'x': 449, 'y': 256}

# 出售按钮备选位置（用于直接出售）
SELL_BUTTON_ALT = {'x': 166, 'y': 742}

# ==================== 界面检查配置 ====================

# 孵蛋界面图片列表
EGG_IMAGES = ['egg1.png', 'egg2.png', 'egg3.png', 'egg4.png']

# 确定按钮图片
CONFIRM_IMAGE = 'confirm.png'

# 移动按钮图片
MOVE_UP_IMAGE = 'move_up.png'

# 自动孵蛋按钮图片
AUTO_EGG_IMAGE = 'auto_egg.png'

# ==================== 日志配置 ====================

# 日志文件名格式
LOG_FILENAME_FORMAT = "beast_capture_%Y%m%d.log"

# 日志保留天数
LOG_BACKUP_COUNT = 30

# 日志格式
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

# ==================== 调度器配置 ====================

# 任务执行间隔（秒）
SCHEDULER_INTERVAL = 30

# 调度器配置
SCHEDULER_JOB_DEFAULTS = {
    'coalesce': False,              # 合并错过的任务
    'max_instances': 1,            # 最多同时运行1个实例
    'misfire_grace_time': 300      # 允许5分钟的延迟执行
}

# ==================== 时间配置 ====================

# 点击操作后的等待时间（秒）
CLICK_WAIT_TIME = 0.5

# UI检查后的等待时间（秒）
UI_CHECK_WAIT_TIME = 1

# 主循环等待时间（秒）
MAIN_LOOP_WAIT_TIME = 3

# 窗口操作后的等待时间（秒）
WINDOW_OPERATION_WAIT_TIME = 0.3