"""
SQLite JSON字段兼容性补丁
"""
import json
from django.db.backends.signals import connection_created


def register_json_valid(connection, **kwargs):
    """
    为SQLite连接注册JSON_VALID函数
    当Django创建数据库连接时会触发此函数
    """
    # 只对SQLite数据库应用此补丁
    if connection.vendor == 'sqlite':
        
        def json_valid(value):
            """检查值是否为有效的JSON格式"""
            try:
                if value is None:
                    return 0
                json.loads(value)
                return 1
            except (json.JSONDecodeError, TypeError):
                return 0
        
        # 获取底层的sqlite3连接并注册函数
        connection.connection.create_function('json_valid', 1, json_valid)

# 连接Django的connection_created信号
connection_created.connect(register_json_valid)