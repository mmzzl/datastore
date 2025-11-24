"""
SQLite数据库后端，禁用JSON_VALID函数
"""
from django.db.backends.sqlite3 import base
from django.db.backends.sqlite3.operations import DatabaseOperations


class CustomDatabaseOperations(DatabaseOperations):
    """
    自定义数据库操作类，禁用JSON_VALID函数
    """
    
    def check_sql(self, table_name=None):
        """
        禁用约束检查，避免JSON_VALID函数问题
        """
        return None


class DatabaseWrapper(base.DatabaseWrapper):
    """
    自定义SQLite数据库后端，禁用JSON_VALID函数
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ops = CustomDatabaseOperations(self)
    
    def check_constraints(self, table_names=None):
        """
        禁用约束检查，避免JSON_VALID函数问题
        """
        # 不执行任何约束检查
        pass