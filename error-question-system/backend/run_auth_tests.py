"""
测试运行器，处理SQLite JSON_VALID函数问题
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner


def setup_test_environment():
    """
    设置测试环境，处理SQLite JSON_VALID函数问题
    """
    # 确保Django已设置
    if not settings.configured:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.test_settings')
        django.setup()
    
    # 获取数据库连接
    from django.db import connection
    
    # 如果是SQLite数据库，注册JSON_VALID函数
    if connection.vendor == 'sqlite':
        def json_valid(value):
            """模拟JSON_VALID函数，总是返回True"""
            return 1  # SQLite中TRUE的表示
        
        # 注册模拟函数
        with connection.cursor() as cursor:
            cursor.connection.create_function("JSON_VALID", 1, json_valid)


def run_tests():
    """
    运行测试
    """
    # 设置测试环境
    setup_test_environment()
    
    # 获取测试运行器
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    
    # 运行指定的测试
    failures = test_runner.run_tests(["tests.test_authentication"])
    
    # 返回测试结果
    return failures


if __name__ == "__main__":
    # 运行测试并退出
    failures = run_tests()
    sys.exit(bool(failures))