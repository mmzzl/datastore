"""
自定义字段，用于兼容SQLite的JSONField
"""
import json
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class SQLiteJSONField(models.TextField):
    """
    SQLite兼容的JSON字段，使用TextField存储JSON数据
    完全表现为TextField，避免Django使用SQLite不支持的JSON_VALID函数
    """
    
    def __init__(self, *args, **kwargs):
        # 直接调用父类初始化，不添加任何可能导致Django认为这是JSONField的逻辑
        super().__init__(*args, **kwargs)
    
    def db_type(self, connection):
        # 明确指定为TEXT类型
        return 'TEXT'
    
    # 仅添加必要的JSON序列化/反序列化逻辑，不添加任何可能触发Django JSON验证的方法

    
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    
    def to_python(self, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return value
    
    def get_prep_value(self, value):
        if value is None:
            return value
        return json.dumps(value, ensure_ascii=False)
    
    def validate(self, value, model_instance):
        # 重写验证方法，不调用super.validate()以避免Django的JSON验证
        if value is None and not self.null:
            raise ValidationError(self.error_messages['null'])
        # 简单的JSON验证，但不在数据库层面验证
        try:
            json.dumps(value)
        except (TypeError, ValueError):
            raise ValidationError(_("Enter valid JSON."))
    
    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        return self.get_prep_value(value)


# 根据数据库类型选择合适的JSONField
def get_json_field():
    """
    根据数据库类型返回合适的JSONField
    在SQLite环境下使用SQLiteJSONField，否则使用默认的JSONField
    """
    from django.db import connection
    from django.conf import settings
    
    # 如果是SQLite数据库，使用自定义的SQLiteJSONField
    if 'sqlite' in connection.vendor:
        return SQLiteJSONField
    
    # 否则使用Django默认的JSONField
    return models.JSONField