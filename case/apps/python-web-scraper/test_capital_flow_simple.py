#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试资金流向爬虫"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from internal.scheduler.scheduler import run_capital_flow_spider


def test_capital_flow_spider():
    """测试资金流向爬虫"""
    print("开始测试资金流向爬虫...")
    
    try:
        run_capital_flow_spider()
        print("资金流向爬虫执行完成")
        return True
    except Exception as e:
        print(f"测试资金流向爬虫失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_capital_flow_spider()
    sys.exit(0 if success else 1)
