from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import structlog

logger = structlog.get_logger(__name__)
User = get_user_model()


class Category(models.Model):
    """
    错题分类模型
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='categories',
        verbose_name=_('创建者')
    )
    name = models.CharField(_('分类名称'), max_length=50)
    description = models.TextField(_('描述'), blank=True)
    color = models.CharField(_('颜色'), max_length=7, default='#1890ff')
    icon = models.CharField(_('图标'), max_length=50, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='children',
        verbose_name=_('父分类')
    )
    level = models.IntegerField(_('层级'), default=1)
    sort_order = models.IntegerField(_('排序'), default=0)
    is_system = models.BooleanField(_('系统分类'), default=False)
    is_active = models.BooleanField(_('是否启用'), default=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('错题分类')
        verbose_name_plural = _('错题分类')
        db_table = 'category'
        ordering = ['user', 'sort_order', 'id']
        unique_together = ['user', 'name', 'parent']
        indexes = [
            models.Index(fields=['user', 'parent', 'is_active']),
            models.Index(fields=['is_system', 'is_active']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} - {self.name}"
        return self.name
    
    def get_full_name(self):
        """获取完整分类路径"""
        if self.parent:
            return f"{self.parent.get_full_name()} > {self.name}"
        return self.name
    
    def get_children_count(self):
        """获取子分类数量"""
        return self.children.filter(is_active=True).count()
    
    def get_questions_count(self):
        """获取该分类下的错题数量"""
        # 通过QuestionCategory关联获取题目数量
        from apps.questions.models import Question
        return Question.objects.filter(question_categories__category=self).count()
    
    # 添加属性以满足测试需求
    @property
    def has_children(self):
        """是否有子分类"""
        return self.children.exists()
    
    @property
    def question_count(self):
        """该分类下的错题数量（包括子分类的题目）"""
        count = self.get_questions_count()
        # 加上所有子分类的题目数量
        for child in self.children.all():
            count += child.question_count
        return count
    
    # 添加方法以满足测试需求
    def get_children(self):
        """获取子分类"""
        return self.children.all()
    
    def get_siblings(self):
        """获取同级分类"""
        if self.parent:
            return self.parent.children.exclude(id=self.id)
        return Category.objects.filter(parent=None, user=self.user).exclude(id=self.id)
    
    def get_all_children(self):
        """获取所有子分类（包括子分类的子分类）"""
        all_children = []
        for child in self.children.all():
            all_children.append(child)
            all_children.extend(child.get_all_children())
        return all_children
    
    def get_root(self):
        """获取根分类"""
        if self.parent:
            return self.parent.get_root()
        return self
    
    def get_path(self):
        """获取分类路径"""
        if self.parent:
            path = self.parent.get_path()
            path.append(self)
            return path
        return [self]
    
    def is_descendant_of(self, category):
        """是否为某个分类的后代"""
        if self.parent == category:
            return True
        if self.parent:
            return self.parent.is_descendant_of(category)
        return False
    
    def is_ancestor_of(self, category):
        """是否为某个分类的祖先"""
        return category.is_descendant_of(self)
    
    def save(self, *args, **kwargs):
        """保存时自动设置层级"""
        if self.parent:
            self.level = self.parent.level + 1
        else:
            self.level = 1
        super().save(*args, **kwargs)


class QuestionCategory(models.Model):
    """
    错题与分类关联模型
    """
    question = models.ForeignKey(
        'questions.Question',
        on_delete=models.CASCADE,
        related_name='question_categories',
        verbose_name=_('错题')
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='question_categories',
        verbose_name=_('分类')
    )
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('错题分类关联')
        verbose_name_plural = _('错题分类关联')
        db_table = 'question_category'
        unique_together = ['question', 'category']
        indexes = [
            models.Index(fields=['question', 'category']),
            models.Index(fields=['category', 'question']),
        ]
    
    def __str__(self):
        return f"{self.question.title} - {self.category.name}"


# 信号处理函数
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender=Category)
def create_default_categories(sender, instance, created, **kwargs):
    """创建用户时创建默认分类"""
    if created and not instance.is_system:
        # 这里可以添加创建默认分类的逻辑
        logger.info("创建新分类", category_id=instance.id, user_id=instance.user.id)