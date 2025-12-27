# -*- coding: utf-8 -*-
"""
日志模块 - 配置和管理日志系统
"""

import logging
import logging.handlers
import datetime
import os
from config import LOG_DIR, LOG_FILENAME_FORMAT, LOG_BACKUP_COUNT, LOG_FORMAT, TARGET_ATTRIBUTES


class BeastLogger:
    """异兽自动化日志管理器"""
    
    def __init__(self, log_dir=None):
        """
        初始化日志管理器
        Args:
            log_dir: 日志目录路径，如果为None则使用配置文件中的路径
        """
        self.log_dir = log_dir or LOG_DIR
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 创建logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # 清除已有的处理器
        self.logger.handlers.clear()
        
        # 配置日志
        self._setup_logging()
    
    def _setup_logging(self):
        """配置日志系统"""
        # 创建日志文件名（按日期）
        log_filename = datetime.datetime.now().strftime(LOG_FILENAME_FORMAT)
        log_filepath = os.path.join(self.log_dir, log_filename)
        
        # 日志格式
        formatter = logging.Formatter(LOG_FORMAT)
        
        # 1. 文件处理器 - 使用TimedRotatingFileHandler按天分割日志
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_filepath,
            when='midnight',
            interval=1,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y%m%d.log"
        
        # 2. 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # 添加处理器
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # 记录启动信息
        self.logger.info("=" * 80)
        self.logger.info(f"山海北荒卷自动化脚本启动 - 目标属性: {', '.join(TARGET_ATTRIBUTES)}")
        self.logger.info(f"日志文件: {log_filepath}")
        self.logger.info("=" * 80)
    
    def get_logger(self):
        """获取logger实例"""
        return self.logger


def setup_logger(log_dir=None):
    """
    设置并返回logger实例
    Args:
        log_dir: 日志目录路径
    Returns:
        logger: 日志实例
    """
    logger_manager = BeastLogger(log_dir)
    return logger_manager.get_logger()
