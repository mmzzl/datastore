from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
import structlog
import json

logger = structlog.get_logger(__name__)
User = get_user_model()


class Subject(models.Model):
    """
    学科模型
    """
    name = models.CharField(_('学科名称'), max_length=50)
    icon = models.CharField(_('图标'), max_length=50, blank=True)
    description = models.TextField(_('描述'), blank=True)
    color = models.CharField(_('颜色'), max_length=7, default='#1890ff')
    is_active = models.BooleanField(_('是否启用'), default=True)
    sort_order = models.IntegerField(_('排序'), default=0)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('学科')
        verbose_name_plural = _('学科')
        db_table = 'subject'
        ordering = ['id']
    
    def __str__(self):
        return self.name


class KnowledgePoint(models.Model):
    """
    知识点模型
    """
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='knowledge_points',
        verbose_name=_('所属学科')
    )
    name = models.CharField(_('知识点名称'), max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='children',
        verbose_name=_('父知识点')
    )
    level = models.IntegerField(_('层级'), default=1)
    description = models.TextField(_('描述'), blank=True)
    is_active = models.BooleanField(_('是否启用'), default=True)
    sort_order = models.IntegerField(_('排序'), default=0)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('知识点')
        verbose_name_plural = _('知识点')
        db_table = 'knowledge_point'
        ordering = ['subject', 'level', 'id']
    
    def __str__(self):
        prefix = '  ' * (self.level - 1)
        return f"{self.subject.name} - {prefix}{self.name}"


class Question(models.Model):
    """
    错题模型
    """
    DIFFICULTY_CHOICES = [
        (1, _('简单')),
        (2, _('中等')),
        (3, _('困难')),
    ]
    
    QUESTION_TYPE_CHOICES = [
        ('single_choice', _('单选题')),
        ('multiple_choice', _('多选题')),
        ('true_false', _('判断题')),
        ('fill_blank', _('填空题')),
        ('short_answer', _('简答题')),
        ('essay', _('论述题')),
        ('calculation', _('计算题')),
        ('other', _('其他')),
    ]
    
    SOURCE_CHOICES = [
        ('exam', _('考试')),
        ('homework', _('作业')),
        ('exercise', _('练习')),
        ('textbook', _('教材')),
        ('mock_exam', _('模拟考')),
        ('other', _('其他')),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('创建者')
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('学科')
    )
    knowledge_points = models.ManyToManyField(
        KnowledgePoint,
        blank=True,
        related_name='questions',
        verbose_name=_('知识点')
    )
    categories = models.ManyToManyField(
        'categories.Category',
        blank=True,
        related_name='questions',
        verbose_name=_('分类')
    )
    title = models.CharField(_('题目标题'), max_length=200)
    content = models.TextField(_('题目内容'))
    question_type = models.CharField(
        _('题目类型'),
        max_length=20,
        choices=QUESTION_TYPE_CHOICES,
        default='other'
    )
    options = models.TextField(_('选项'), default='{}', blank=True)
    correct_answer = models.TextField(_('正确答案'), blank=True)
    user_answer = models.TextField(_('用户答案'), blank=True)
    analysis = models.TextField(_('解析'), blank=True)
    difficulty = models.IntegerField(
        _('难度'),
        choices=DIFFICULTY_CHOICES,
        default=2
    )
    source = models.CharField(
        _('来源'),
        max_length=20,
        choices=SOURCE_CHOICES,
        default='other'
    )
    source_detail = models.CharField(_('来源详情'), max_length=100, blank=True)
    tags = models.TextField(_('标签'), default='[]', blank=True)
    images = models.TextField(_('图片'), default='[]', blank=True)
    
    # JSON字段访问器
    def get_options(self):
        try:
            return json.loads(self.options)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_options(self, value):
        self.options = json.dumps(value, ensure_ascii=False)
    
    def get_tags(self):
        try:
            return json.loads(self.tags)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_tags(self, value):
        self.tags = json.dumps(value, ensure_ascii=False)
    
    def get_images(self):
        try:
            return json.loads(self.images)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_images(self, value):
        self.images = json.dumps(value, ensure_ascii=False)
    is_solved = models.BooleanField(_('是否已解决'), default=False)
    is_marked = models.BooleanField(_('是否标记'), default=False)
    view_count = models.IntegerField(_('查看次数'), default=0)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    last_reviewed_at = models.DateTimeField(_('最后复习时间'), blank=True, null=True)
    review_count = models.IntegerField(_('复习次数'), default=0)
    
    class Meta:
        verbose_name = _('错题')
        verbose_name_plural = _('错题')
        db_table = 'question'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['subject', 'difficulty']),
            models.Index(fields=['is_solved', 'is_marked']),
        ]
    
    def __str__(self):
        return self.title
    
    @classmethod
    def create_with_compatibility(cls, **kwargs):
        """创建方法，兼容测试代码中的answer和solution字段"""
        answer_content = kwargs.pop('answer', None)
        solution_content = kwargs.pop('solution', None)
        
        # 如果没有提供subject，创建一个默认的学科
        if 'subject' not in kwargs:
            subject, _ = Subject.objects.get_or_create(
                name='默认学科',
                defaults={
                    'description': '默认学科',
                    'color': '#1890ff',
                    'sort_order': 1,
                    'is_active': True
                }
            )
            kwargs['subject'] = subject
        
        # 创建Question实例
        question = cls.objects.create(**kwargs)
        
        # 如果提供了answer或solution，创建相应的Answer实例
        if answer_content is not None:
            from apps.answers.models import Answer
            Answer.objects.create(
                question=question,
                user=question.user,
                content=answer_content,
                explanation=solution_content or '',
                is_verified=False,
                is_public=True
            )
        
        return question
    
    def get_knowledge_points_str(self):
        """获取知识点字符串"""
        return ', '.join([kp.name for kp in self.knowledge_points.all()])
    
    def get_tags_str(self):
        """获取标签字符串"""
        return ', '.join(self.tags) if self.tags else ''
    
    def get_images_list(self):
        """获取图片列表"""
        return self.images if isinstance(self.images, list) else []
    
    def increment_view_count(self):
        """增加查看次数"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def mark_as_solved(self):
        """标记为已解决"""
        if not self.is_solved:
            self.is_solved = True
            self.save(update_fields=['is_solved'])
            # 更新用户统计
            profile = self.user.profile
            profile.solved_questions += 1
            profile.save(update_fields=['solved_questions'])
            logger.info("错题已解决", question_id=self.id, user_id=self.user.id)


class QuestionImage(models.Model):
    """
    题目图片模型
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='question_images',
        verbose_name=_('所属错题')
    )
    image = models.ImageField(_('图片'), upload_to='question_images/')
    description = models.CharField(_('描述'), max_length=200, blank=True)
    is_main = models.BooleanField(_('是否主图'), default=False)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('题目图片')
        verbose_name_plural = _('题目图片')
        db_table = 'question_image'
        ordering = ['-is_main', 'created_at']
    
    def __str__(self):
        return f"{self.question.title}的图片"


class QuestionNote(models.Model):
    """
    错题笔记模型
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='notes',
        verbose_name=_('所属错题')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='question_notes',
        verbose_name=_('创建者')
    )
    content = models.TextField(_('笔记内容'))
    is_public = models.BooleanField(_('是否公开'), default=False)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('错题笔记')
        verbose_name_plural = _('错题笔记')
        db_table = 'question_note'
        ordering = ['-created_at']
        unique_together = ['question', 'user']
    
    def __str__(self):
        return f"{self.user.username}对{self.question.title}的笔记"


class QuestionReview(models.Model):
    """
    错题复习记录模型
    """
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('所属错题')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='question_reviews',
        verbose_name=_('复习者')
    )
    is_correct = models.BooleanField(_('是否答对'), default=False)
    review_time = models.IntegerField(_('复习用时(秒)'), default=0)
    notes = models.TextField(_('复习笔记'), blank=True)
    created_at = models.DateTimeField(_('复习时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('错题复习记录')
        verbose_name_plural = _('错题复习记录')
        db_table = 'question_review'
        ordering = ['-created_at']
    
    def __str__(self):
        status = "答对" if self.is_correct else "答错"
        return f"{self.user.username}复习{self.question.title}({status})"


class QuestionTag(models.Model):
    """
    题目标签模型
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='question_tags',
        verbose_name=_('创建者')
    )
    name = models.CharField(_('标签名称'), max_length=50)
    color = models.CharField(_('颜色'), max_length=7, default='#1890ff')
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('题目标签')
        verbose_name_plural = _('题目标签')
        db_table = 'question_tag'
        unique_together = ['user', 'name']
        ordering = ['name']
    
    def __str__(self):
        return self.name


class QuestionStatistics(models.Model):
    """
    题目统计模型
    """
    question = models.OneToOneField(
        Question,
        on_delete=models.CASCADE,
        related_name='statistics',
        verbose_name=_('题目')
    )
    view_count = models.IntegerField(_('查看次数'), default=0)
    review_count = models.IntegerField(_('复习次数'), default=0)
    last_reviewed_at = models.DateTimeField(_('最后复习时间'), blank=True, null=True)
    created_at = models.DateTimeField(_('创建时间'), auto_now_add=True)
    updated_at = models.DateTimeField(_('更新时间'), auto_now=True)
    
    class Meta:
        verbose_name = _('题目统计')
        verbose_name_plural = _('题目统计')
        db_table = 'question_statistics'
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.question.title}的统计"


# 信号处理函数
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender=Question)
def update_user_question_stats(sender, instance, created, **kwargs):
    """更新用户错题统计"""
    if created:
        profile = instance.user.profile
        profile.total_questions += 1
        profile.save(update_fields=['total_questions'])
        logger.info("新增错题", question_id=instance.id, user_id=instance.user.id)


@receiver(post_delete, sender=Question)
def update_user_question_stats_on_delete(sender, instance, **kwargs):
    """删除错题时更新用户统计"""
    if instance.is_solved:
        profile = instance.user.profile
        profile.solved_questions = max(0, profile.solved_questions - 1)
        profile.save(update_fields=['solved_questions'])
    
    profile = instance.user.profile
    profile.total_questions = max(0, profile.total_questions - 1)
    profile.save(update_fields=['total_questions'])
    logger.info("删除错题", question_id=instance.id, user_id=instance.user.id)