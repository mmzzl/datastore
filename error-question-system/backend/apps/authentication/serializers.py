from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import structlog

logger = structlog.get_logger(__name__)
User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'phone', 'first_name', 'last_name')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("密码不匹配")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        logger.info("用户注册成功", user_id=user.id, username=user.username)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """用户档案序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    avatar = serializers.ImageField(source='user.avatar', read_only=True)
    subjects = serializers.SerializerMethodField()
    difficulty_preferences = serializers.SerializerMethodField()
    
    class Meta:
        from .models import UserProfile
        model = UserProfile
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'phone', 'avatar',
            'bio', 'grade', 'school', 'subjects', 'difficulty_preferences',
            'total_questions', 'solved_questions', 'study_days', 'created_at'
        )
        read_only_fields = ('total_questions', 'solved_questions', 'study_days', 'created_at')
    
    def get_subjects(self, obj):
        return [{'id': subject.id, 'name': subject.name} for subject in obj.subjects.all()]
    
    def get_difficulty_preferences(self, obj):
        return [{'id': choice[0], 'name': choice[1]} for choice in obj.difficulty_preferences]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """用户档案更新序列化器"""
    username = serializers.CharField(source='user.username', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    phone = serializers.CharField(source='user.phone', required=False)
    avatar = serializers.ImageField(source='user.avatar', required=False)
    
    class Meta:
        from .models import UserProfile
        model = UserProfile
        fields = (
            'bio', 'grade', 'school', 'subjects', 'difficulty_preferences',
            'username', 'email', 'first_name', 'last_name', 'phone', 'avatar'
        )
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        
        # 更新用户信息
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        
        # 更新档案信息
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        logger.info("用户档案更新成功", user_id=instance.user.id)
        return instance


class PasswordChangeSerializer(serializers.Serializer):
    """密码修改序列化器"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("新密码不匹配")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("旧密码不正确")
        return value
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        logger.info("用户密码修改成功", user_id=user.id)
        return user


class UserLoginLogSerializer(serializers.ModelSerializer):
    """用户登录日志序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        from .models import UserLoginLog
        model = UserLoginLog
        fields = ('id', 'username', 'ip_address', 'device_info', 'login_time')
        read_only_fields = ('id', 'username', 'ip_address', 'device_info', 'login_time')


class UserActivityLogSerializer(serializers.ModelSerializer):
    """用户活动日志序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        from .models import UserActivityLog
        model = UserActivityLog
        fields = ('id', 'username', 'action', 'resource_type', 'resource_id', 'description', 'ip_address', 'created_at')
        read_only_fields = ('id', 'username', 'action', 'resource_type', 'resource_id', 'description', 'ip_address', 'created_at')