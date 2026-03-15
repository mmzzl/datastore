#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试资金流向爬虫 - 直接在主进程中运行"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 设置环境变量，让 Scrapy 能找到项目设置
os.environ.setdefault('SCRAPY_SETTINGS_MODULE', 'python_web_scraper.settings')

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from internal.spider.eastmoney_capital_flow_spider import EastMoneyCapitalFlowSpider


def test_capital_flow_spider():
    """测试资金流向爬虫"""
    print("开始测试资金流向爬虫...")
    
    try:
        # 获取Scrapy设置
        settings = get_project_settings()
        
        # 禁用py_mini_racer的自动清理
        settings.set("PY_MINI_RACER_NO_CLEANUP", True)
        
        # 创建并启动CrawlerProcess
        process = CrawlerProcess(settings)
        process.crawl(EastMoneyCapitalFlowSpider)
        
        print("开始执行资金流向爬虫")
        process.start()
        print("资金流向爬虫执行完成")
        
    except Exception as e:
        print(f"测试资金流向爬虫失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = test_capital_flow_spider()
    sys.exit(0 if success else 1)
