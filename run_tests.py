#!/usr/bin/env python
"""TDD 测试运行器"""

import subprocess
import sys


def run_tests(test_path, description):
    print(f"\n{'=' * 60}")
    print(f"测试: {description}")
    print(f"{'=' * 60}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"],
            capture_output=True,
            text=True,
            cwd="apps/api",
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode
    except Exception as e:
        print(f"运行测试失败: {e}")
        return 1


# 运行现有测试
run_tests("tests/test_auth.py", "认证模块测试")

# 运行持仓管理测试（如果有）
run_tests("tests/data_source/test_unified_interface.py", "数据源统一接口测试")
