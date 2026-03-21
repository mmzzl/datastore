#!/usr/bin/env python
"""
简化的测试运行脚本，直接使用pytest运行测试
"""
import os
import sys
import subprocess

def main():
    # 设置环境变量
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.test_settings'
    
    # 运行pytest
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '--disable-warnings'
    ]
    
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())