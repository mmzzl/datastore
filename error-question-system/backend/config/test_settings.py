"""
测试环境设置
继承自主设置文件，并针对测试环境进行优化
"""
from .settings import *
import os
# 导入SQLite JSON_VALID函数补丁，会自动通过信号机制生效
from . import sqlite_patch

# 测试数据库配置 - 使用SQLite进行测试
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# 禁用系统检查
SILENCED_SYSTEM_CHECKS = [
    'fields.E180',  # SQLite does not support JSONFields
]

# 测试时禁用日志
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# 测试配置
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# 禁用迁移，提高测试速度
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# 测试时简化密码验证
AUTH_PASSWORD_VALIDATORS = []

# 测试时禁用中间件，提高测试速度
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'corsheaders.middleware.CorsMiddleware',
]

# 测试时允许所有主机
ALLOWED_HOSTS = ['*']

# 测试时简化媒体文件处理
MEDIA_ROOT = os.path.join(BASE_DIR, 'test_media')

# 测试时简化静态文件处理
STATIC_ROOT = os.path.join(BASE_DIR, 'test_static')

# 测试时简化CORS设置
CORS_ALLOW_ALL_ORIGINS = True

# 测试时简化限流设置
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}