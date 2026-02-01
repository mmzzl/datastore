# -*- coding: utf-8 -*-
# 配置文件
import os
from pathlib import Path

class Config:
    """配置管理"""
    
    # 数据目录
    DATA_DIR = Path(os.path.expanduser("~/.qlib/stock_data/source/all_1d_original"))
    
    # 钉钉机器人配置（从环境变量读取）
    DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK", "")
    DINGTALK_SECRET = os.getenv("DINGTALK_SECRET", "")
    
    @classmethod
    def get_dingtalk_config(cls):
        """获取钉钉机器人配置"""
        webhook = cls.DINGTALK_WEBHOOK
        secret = cls.DINGTALK_SECRET
        
        # 如果环境变量为空，尝试从配置文件读取
        if not webhook:
            config_file = Path(__file__).parent.joinpath("dingtalk_config.txt")
            print(config_file)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.strip()
                        if line.startswith("webhook="):
                            webhook = line.split("=", 1)[1].strip()
                        elif line.startswith("secret="):
                            secret = line.split("=", 1)[1].strip()
        
        return webhook, secret
    
    @classmethod
    def save_dingtalk_config(cls, webhook: str, secret: str):
        """保存钉钉机器人配置"""
        config_file = Path(__file__).parent.joinpath("dingtalk_config.txt")
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(f"webhook={webhook}\n")
            f.write(f"secret={secret}\n")
        print(f"钉钉机器人配置已保存到: {config_file}")
