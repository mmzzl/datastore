"""
API运行日志配置模块
日志包含：时间、日志级别、文件名、函数名、行号、消息
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

# 日志文件保存路径
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 日志文件名（按日期）
LOG_FILE = os.path.join(LOG_DIR, f"api_{datetime.now().strftime('%Y%m%d')}.log")

# 日志格式：时间 | 日志级别 | 文件名 | 函数名 | 行号 | 消息
LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(filename)s:%(funcName)s:%(lineno)d | %(message)s'

# 日期格式
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def setup_logger(name: str = 'api_logger', level: int = logging.INFO) -> logging.Logger:
    """
    配置并返回日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器
    if logger.handlers:
        return logger
    
    # 创建格式化器
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # 文件处理器 - 按大小轮转（最大10MB，保留5个备份）
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 创建默认日志记录器
logger = setup_logger()


# 装饰器：自动记录函数调用和异常
def log_api_call(func):
    """
    API调用日志装饰器
    自动记录函数调用入口、参数、返回值和异常
    """
    def wrapper(*args, **kwargs):
        func_name = func.__name__
        module_name = func.__module__
        
        # 记录函数调用
        logger.info(f"[API CALL] {module_name}.{func_name} - 开始调用")
        
        try:
            # 执行函数
            result = func(*args, **kwargs)
            
            # 记录成功返回
            logger.info(f"[API SUCCESS] {module_name}.{func_name} - 调用成功")
            return result
            
        except Exception as e:
            # 记录异常
            logger.error(f"[API ERROR] {module_name}.{func_name} - 异常: {str(e)}", exc_info=True)
            raise
    
    return wrapper
