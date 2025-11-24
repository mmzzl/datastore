"""
自定义字段，用于兼容SQLite的JSONField
"""
import json
from django.db import models
from django.core.exceptions import ValidationError


class SQLiteJSONField(models.TextField):
    """
    SQLite兼容的JSON字段，使用TextField存储JSON数据
    """
    
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
        super().validate(value, model_instance)
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