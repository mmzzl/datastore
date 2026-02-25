# -*- coding: utf-8 -*-
"""爬虫服务启动脚本"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from internal.service.spider_service import main

if __name__ == "__main__":
    main()
