#!/usr/bin/env python
"""
简单的测试运行脚本，用于运行错题本系统的单元测试
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ['DJANGO_SETTINGS_MODULE'] = 'config.test_settings'
    django.setup()
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["tests"])
    
    if failures:
        sys.exit(1)