from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import structlog
import json

logger = structlog.get_logger(__name__)
User = get_user_model()


class SystemConfig(models.Model):
    """
    系统配置模型
    """
    key = models.CharField(_('配置键'), max_length=100, unique=True)
    value = models.TextField(_('配置值'))
    description = models.TextField(_('描述'), blank=True)
    is_active = models.BooleanField(_('是否启用'), default=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('系统配置')
        verbose_name_plural = _('系统配置')
        db_table = 'system_config'
        ordering = ['key']
    
    def __str__(self):
        return f"{self.key}: {self.value}"


class SystemNotification(models.Model):
    """
    系统通知模型
    """
    TYPE_CHOICES = [
        ('info', _('信息')),
        ('warning', _('警告')),
        ('error', _('错误')),
        ('success', _('成功')),
    ]
    
    title = models.CharField(_('标题'), max_length=100)
    content = models.TextField(_('内容'))
    type = models.CharField(_('类型'), max_length=10, choices=TYPE_CHOICES, default='info')
    is_active = models.BooleanField(_('是否启用'), default=True)
    start_time = models.DateTimeField(_('开始时间'), blank=True, null=True)
    end_time = models.DateTimeField(_('结束时间'), blank=True, null=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('系统通知')
        verbose_name_plural = _('系统通知')
        db_table = 'system_notification'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def is_valid(self):
        """检查通知是否有效"""
        from django.utils import timezone
        now = timezone.now()
        
        if not self.is_active:
            return False
        
        if self.start_time and now < self.start_time:
            return False
        
        if self.end_time and now > self.end_time:
            return False
        
        return True


class UserNotification(models.Model):
    """
    用户通知模型
    """
    TYPE_CHOICES = [
        ('info', _('信息')),
        ('warning', _('警告')),
        ('error', _('错误')),
        ('success', _('成功')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name=_('接收者')
    )
    title = models.CharField(_('标题'), max_length=100)
    content = models.TextField(_('内容'))
    type = models.CharField(_('类型'), max_length=10, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(_('是否已读'), default=False)
    related_object_type = models.CharField(_('关联对象类型'), max_length=50, blank=True)
    related_object_id = models.PositiveIntegerField(_('关联对象ID'), blank=True, null=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    read_at = models.DateTimeField(_('阅读时间'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('用户通知')
        verbose_name_plural = _('用户通知')
        db_table = 'user_notification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', 'created_at']),
            models.Index(fields=['related_object_type', 'related_object_id']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """标记为已读"""
        if not self.is_read:
            self.is_read = True
            from django.utils import timezone
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class Feedback(models.Model):
    """
    用户反馈模型
    """
    TYPE_CHOICES = [
        ('bug', _('Bug反馈')),
        ('feature', _('功能建议')),
        ('improvement', _('改进建议')),
        ('other', _('其他')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('待处理')),
        ('processing', _('处理中')),
        ('resolved', _('已解决')),
        ('rejected', _('已拒绝')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        verbose_name=_('反馈者')
    )
    type = models.CharField(_('反馈类型'), max_length=20, choices=TYPE_CHOICES, default='other')
    title = models.CharField(_('标题'), max_length=100)
    content = models.TextField(_('内容'))
    status = models.CharField(_('处理状态'), max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_reply = models.TextField(_('管理员回复'), blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('用户反馈')
        verbose_name_plural = _('用户反馈')
        db_table = 'feedback'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class OperationLog(models.Model):
    """
    操作日志模型
    """
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='operation_logs',
        verbose_name=_('操作者')
    )
    action = models.CharField(_('操作动作'), max_length=50)
    resource_type = models.CharField(_('资源类型'), max_length=50)
    resource_id = models.PositiveIntegerField(_('资源ID'), blank=True, null=True)
    description = models.TextField(_('描述'), blank=True)
    ip_address = models.GenericIPAddressField(_('IP地址'), blank=True, null=True)
    user_agent = models.TextField(_('用户代理'), blank=True)
    extra_data = models.TextField(_('额外数据'), default='{}', blank=True)
    
    # JSON字段访问器
    def get_extra_data(self):
        try:
            return json.loads(self.extra_data)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_extra_data(self, value):
        self.extra_data = json.dumps(value, ensure_ascii=False)
    created_at = models.DateTimeField(_('操作时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('操作日志')
        verbose_name_plural = _('操作日志')
        db_table = 'operation_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['action', 'resource_type']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else '匿名用户'
        return f"{user_str} {self.action} {self.resource_type}"


# 信号处理函数
from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender=Feedback)
def notify_admin_on_feedback(sender, instance, created, **kwargs):
    """用户反馈时通知管理员"""
    if created:
        # 这里可以添加通知管理员的逻辑
        logger.info("收到用户反馈", feedback_id=instance.id, user_id=instance.user.id)