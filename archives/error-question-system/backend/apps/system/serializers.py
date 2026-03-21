from rest_framework import serializers
from .models import SystemConfig, SystemNotification, UserNotification, Feedback, OperationLog
import structlog

logger = structlog.get_logger(__name__)


class SystemConfigSerializer(serializers.ModelSerializer):
    """系统配置序列化器"""
    
    class Meta:
        model = SystemConfig
        fields = ('id', 'key', 'value', 'description', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class SystemNotificationSerializer(serializers.ModelSerializer):
    """系统通知序列化器"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = SystemNotification
        fields = (
            'id', 'title', 'content', 'type', 'type_display', 'is_active',
            'start_time', 'end_time', 'is_valid', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'is_valid', 'created_at', 'updated_at')


class UserNotificationSerializer(serializers.ModelSerializer):
    """用户通知序列化器"""
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = UserNotification
        fields = (
            'id', 'user', 'title', 'content', 'type', 'type_display', 'is_read',
            'related_object_type', 'related_object_id', 'created_at', 'read_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'read_at')


class FeedbackSerializer(serializers.ModelSerializer):
    """用户反馈序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Feedback
        fields = (
            'id', 'user', 'username', 'type', 'type_display', 'title', 'content',
            'status', 'status_display', 'admin_reply', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'username', 'status', 'admin_reply', 'created_at', 'updated_at')


class FeedbackCreateSerializer(serializers.ModelSerializer):
    """用户反馈创建序列化器"""
    
    class Meta:
        model = Feedback
        fields = ('type', 'title', 'content')
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        
        feedback = Feedback.objects.create(**validated_data)
        
        logger.info("创建用户反馈成功", feedback_id=feedback.id, user_id=user.id)
        return feedback


class OperationLogSerializer(serializers.ModelSerializer):
    """操作日志序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = OperationLog
        fields = (
            'id', 'user', 'username', 'action', 'resource_type', 'resource_id',
            'description', 'ip_address', 'user_agent', 'extra_data', 'created_at'
        )
        read_only_fields = ('id', 'user', 'username', 'ip_address', 'user_agent', 'created_at')