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
    username = serializers.CharField(read_only=True)
    email = serializers.EmailField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    phone = serializers.CharField(read_only=True)
    avatar = serializers.ImageField(read_only=True)
    subjects = serializers.SerializerMethodField()
    difficulty_preferences = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    solved_questions = serializers.SerializerMethodField()
    study_days = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'phone', 'avatar',
            'nickname', 'bio', 'grade', 'school', 'subjects', 'difficulty_preferences',
            'total_questions', 'solved_questions', 'study_days', 'created_at'
        )
        read_only_fields = ('id', 'created_at')
    
    def get_subjects(self, obj):
        if hasattr(obj, 'profile') and obj.profile:
            return [{'id': subject.id, 'name': subject.name} for subject in obj.profile.study_subjects.all()]
        return []
    
    def get_difficulty_preferences(self, obj):
        if hasattr(obj, 'profile') and obj.profile:
            return [{'id': obj.profile.difficulty_preference, 
                    'name': dict(obj.profile._meta.get_field('difficulty_preference').choices).get(obj.profile.difficulty_preference, '')}]
        return []
    
    def get_total_questions(self, obj):
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.total_questions
        return 0
    
    def get_solved_questions(self, obj):
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.solved_questions
        return 0
    
    def get_study_days(self, obj):
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.study_days
        return 0


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """用户档案更新序列化器"""
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    avatar = serializers.ImageField(required=False)
    bio = serializers.CharField(required=False)
    grade = serializers.CharField(required=False)
    school = serializers.CharField(required=False)
    
    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'phone', 'avatar',
            'nickname', 'bio', 'grade', 'school'
        )


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
        fields = ('id', 'username', 'ip_address', 'device', 'browser', 'os', 'location', 'login_time', 'logout_time')
        read_only_fields = ('id', 'username', 'ip_address', 'device', 'browser', 'os', 'location', 'login_time', 'logout_time')


class UserActivityLogSerializer(serializers.ModelSerializer):
    """用户活动日志序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        from .models import UserActivityLog
        model = UserActivityLog
        fields = ('id', 'username', 'action', 'object_type', 'object_id', 'object_repr', 'details', 'ip_address', 'timestamp')
        read_only_fields = ('id', 'username', 'action', 'object_type', 'object_id', 'object_repr', 'details', 'ip_address', 'timestamp')