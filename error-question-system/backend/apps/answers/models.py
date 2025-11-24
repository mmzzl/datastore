from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.conf import settings
import structlog

# 导入通用JSONField
try:
    from apps.common.fields import get_json_field
    JSONField = get_json_field()
except ImportError:
    from django.db.models import JSONField

logger = structlog.get_logger(__name__)
User = get_user_model()


class Answer(models.Model):
    """
    答案模型
    """
    question = models.OneToOneField(
        'questions.Question',
        on_delete=models.CASCADE,
        related_name='answer',
        verbose_name=_('关联错题')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('创建者')
    )
    content = models.TextField(_('答案内容'))
    explanation = models.TextField(_('解释'), blank=True)
    steps = models.JSONField(_('解题步骤'), default=list, blank=True)
    images = models.JSONField(_('图片'), default=list, blank=True)
    source = models.CharField(_('来源'), max_length=50, blank=True)
    is_verified = models.BooleanField(_('是否已验证'), default=False)
    is_public = models.BooleanField(_('是否公开'), default=True)
    likes_count = models.IntegerField(_('点赞数'), default=0)
    views_count = models.IntegerField(_('查看次数'), default=0)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('答案')
        verbose_name_plural = _('答案')
        db_table = 'answer'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['question', 'is_verified']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.question.title}的答案"
    
    def get_images_list(self):
        """获取图片列表"""
        return self.images if isinstance(self.images, list) else []
    
    def increment_view_count(self):
        """增加查看次数"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def increment_likes_count(self):
        """增加点赞数"""
        self.likes_count += 1
        self.save(update_fields=['likes_count'])
    
    def decrement_likes_count(self):
        """减少点赞数"""
        self.likes_count = max(0, self.likes_count - 1)
        self.save(update_fields=['likes_count'])


class AnswerImage(models.Model):
    """
    答案图片模型
    """
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='answer_images',
        verbose_name=_('所属答案')
    )
    image = models.ImageField(_('图片'), upload_to='answer_images/')
    description = models.CharField(_('描述'), max_length=200, blank=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('答案图片')
        verbose_name_plural = _('答案图片')
        db_table = 'answer_image'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.answer.question.title}的答案图片"


class AnswerComment(models.Model):
    """
    答案评论模型
    """
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name=_('所属答案')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='answer_comments',
        verbose_name=_('评论者')
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='replies',
        verbose_name=_('父评论')
    )
    content = models.TextField(_('评论内容'))
    is_deleted = models.BooleanField(_('是否已删除'), default=False)
    likes_count = models.IntegerField(_('点赞数'), default=0)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('答案评论')
        verbose_name_plural = _('答案评论')
        db_table = 'answer_comment'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['answer', 'parent', 'is_deleted']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username}对{self.answer.question.title}的评论"
    
    def increment_likes_count(self):
        """增加点赞数"""
        self.likes_count += 1
        self.save(update_fields=['likes_count'])
    
    def decrement_likes_count(self):
        """减少点赞数"""
        self.likes_count = max(0, self.likes_count - 1)
        self.save(update_fields=['likes_count'])


class AnswerLike(models.Model):
    """
    答案点赞模型
    """
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_('所属答案')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='answer_likes',
        verbose_name=_('点赞者')
    )
    created_at = models.DateTimeField(_('点赞时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('答案点赞')
        verbose_name_plural = _('答案点赞')
        db_table = 'answer_like'
        unique_together = ['answer', 'user']
        indexes = [
            models.Index(fields=['answer', 'user']),
        ]
    
    def __str__(self):
        return f"{self.user.username}点赞了{self.answer.question.title}的答案"


class CommentLike(models.Model):
    """
    评论点赞模型
    """
    comment = models.ForeignKey(
        AnswerComment,
        on_delete=models.CASCADE,
        related_name='likes',
        verbose_name=_('所属评论')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comment_likes',
        verbose_name=_('点赞者')
    )
    created_at = models.DateTimeField(_('点赞时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('评论点赞')
        verbose_name_plural = _('评论点赞')
        db_table = 'comment_like'
        unique_together = ['comment', 'user']
        indexes = [
            models.Index(fields=['comment', 'user']),
        ]
    
    def __str__(self):
        return f"{self.user.username}点赞了评论"


# 信号处理函数
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender=AnswerLike)
def update_answer_likes_on_save(sender, instance, created, **kwargs):
    """创建点赞时增加答案点赞数"""
    if created:
        instance.answer.increment_likes_count()
        logger.info("答案被点赞", answer_id=instance.answer.id, user_id=instance.user.id)


@receiver(post_delete, sender=AnswerLike)
def update_answer_likes_on_delete(sender, instance, **kwargs):
    """删除点赞时减少答案点赞数"""
    instance.answer.decrement_likes_count()
    logger.info("取消答案点赞", answer_id=instance.answer.id, user_id=instance.user.id)


@receiver(post_save, sender=CommentLike)
def update_comment_likes_on_save(sender, instance, created, **kwargs):
    """创建点赞时增加评论点赞数"""
    if created:
        instance.comment.increment_likes_count()
        logger.info("评论被点赞", comment_id=instance.comment.id, user_id=instance.user.id)


@receiver(post_delete, sender=CommentLike)
def update_comment_likes_on_delete(sender, instance, **kwargs):
    """删除点赞时减少评论点赞数"""
    instance.comment.decrement_likes_count()
    logger.info("取消评论点赞", comment_id=instance.comment.id, user_id=instance.user.id)