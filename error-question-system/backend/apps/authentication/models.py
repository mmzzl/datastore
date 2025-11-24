from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
import structlog

# 导入通用JSONField
try:
    from apps.common.fields import get_json_field
    JSONField = get_json_field()
except ImportError:
    from django.db.models import JSONField

logger = structlog.get_logger(__name__)


class UserManager(BaseUserManager):
    """
    自定义用户管理器
    """
    def create_user(self, username, email, password=None, **extra_fields):
        """创建普通用户，要求必须提供邮箱"""
        if not email:
            raise ValueError('必须提供邮箱地址')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email, password=None, **extra_fields):
        """创建超级用户"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须设置is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须设置is_superuser=True')
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    自定义用户模型，扩展Django默认用户
    """
    objects = UserManager()  # 使用自定义管理器
    email = models.EmailField(_('邮箱'), unique=True)
    phone = models.CharField(_('手机号'), max_length=11, blank=True, null=True)
    avatar = models.ImageField(_('头像'), upload_to='avatars/', blank=True, null=True)
    nickname = models.CharField(_('昵称'), max_length=50, blank=True)
    bio = models.TextField(_('个人简介'), blank=True)
    birth_date = models.DateField(_('出生日期'), blank=True, null=True)
    gender = models.CharField(
        _('性别'),
        max_length=1,
        choices=[
            ('M', _('男')),
            ('F', _('女')),
            ('O', _('其他')),
        ],
        blank=True,
        default=''
    )
    school = models.CharField(_('学校'), max_length=100, blank=True)
    grade = models.CharField(_('年级'), max_length=20, blank=True)
    is_verified = models.BooleanField(_('已验证'), default=False)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    last_login_ip = models.GenericIPAddressField(_('最后登录IP'), blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('用户')
        verbose_name_plural = _('用户')
        db_table = 'auth_user'
    
    def __str__(self):
        return self.username
    
    
    def get_full_name(self):
        """获取用户全名"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username
    
    def get_short_name(self):
        """获取用户短名称"""
        return self.first_name or self.username


class UserProfile(models.Model):
    """
    用户扩展信息
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('用户')
    )
    study_subjects = models.ManyToManyField(
        'questions.Subject',
        blank=True,
        related_name='students',
        verbose_name=_('学习科目')
    )
    difficulty_preference = models.IntegerField(
        _('难度偏好'),
        choices=[
            (1, _('简单')),
            (2, _('中等')),
            (3, _('困难')),
        ],
        default=2
    )
    daily_target = models.IntegerField(_('每日目标'), default=5)
    total_questions = models.IntegerField(_('总错题数'), default=0)
    solved_questions = models.IntegerField(_('已解决错题数'), default=0)
    study_days = models.IntegerField(_('学习天数'), default=0)
    consecutive_days = models.IntegerField(_('连续学习天数'), default=0)
    last_study_date = models.DateField(_('最后学习日期'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('用户档案')
        verbose_name_plural = _('用户档案')
        db_table = 'user_profile'
    
    def __str__(self):
        return f"{self.user.username}的档案"
    
    def get_accuracy_rate(self):
        """获取正确率"""
        if self.total_questions == 0:
            return 0
        return round(self.solved_questions / self.total_questions * 100, 2)


class UserLoginLog(models.Model):
    """
    用户登录日志
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='login_logs',
        verbose_name=_('用户')
    )
    ip_address = models.GenericIPAddressField(_('IP地址'))
    device = models.CharField(_('设备'), max_length=100, blank=True)
    browser = models.CharField(_('浏览器'), max_length=100, blank=True)
    os = models.CharField(_('操作系统'), max_length=50, blank=True)
    location = models.CharField(_('位置'), max_length=100, blank=True)
    login_time = models.DateTimeField(_('登录时间'), auto_now_add=True)
    logout_time = models.DateTimeField(_('登出时间'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('登录日志')
        verbose_name_plural = _('登录日志')
        db_table = 'user_login_log'
        ordering = ['-login_time']
    
    def __str__(self):
        return f"{self.user.username}于{self.login_time}的登录记录"


class UserActivityLog(models.Model):
    """
    用户活动日志
    """
    ACTION_CHOICES = [
        ('create_question', _('创建错题')),
        ('update_question', _('更新错题')),
        ('delete_question', _('删除错题')),
        ('create_answer', _('创建解答')),
        ('update_answer', _('更新解答')),
        ('delete_answer', _('删除解答')),
        ('create_category', _('创建分类')),
        ('update_category', _('更新分类')),
        ('delete_category', _('删除分类')),
        ('search', _('搜索')),
        ('view', _('查看')),
        ('export', _('导出')),
        ('import', _('导入')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activity_logs',
        verbose_name=_('用户')
    )
    action = models.CharField(_('操作'), max_length=50, choices=ACTION_CHOICES)
    object_type = models.CharField(_('对象类型'), max_length=50, blank=True)
    object_id = models.PositiveIntegerField(_('对象ID'), blank=True, null=True)
    object_repr = models.CharField(_('对象表示'), max_length=200, blank=True)
    details = JSONField(_('详细信息'), default=dict, blank=True)
    ip_address = models.GenericIPAddressField(_('IP地址'), blank=True, null=True)
    user_agent = models.TextField(_('用户代理'), blank=True)
    timestamp = models.DateTimeField(_('时间戳'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('活动日志')
        verbose_name_plural = _('活动日志')
        db_table = 'user_activity_log'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user.username}于{self.timestamp}进行了{self.get_action_display()}操作"


# 信号处理函数
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """创建用户时自动创建用户档案"""
    if created:
        logger.info("创建用户档案", user_id=instance.id, username=instance.username)
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """保存用户时同时保存用户档案"""
    if hasattr(instance, 'profile'):
        instance.profile.save()