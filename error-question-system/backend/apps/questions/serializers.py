from rest_framework import serializers
from .models import Subject, KnowledgePoint, Question, QuestionImage, QuestionNote, QuestionReview, QuestionTag, QuestionStatistics
import structlog

logger = structlog.get_logger(__name__)


class SubjectSerializer(serializers.ModelSerializer):
    """学科序列化器"""
    class Meta:
        model = Subject
        fields = ('id', 'name', 'icon', 'description', 'color', 'is_active', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class KnowledgePointSerializer(serializers.ModelSerializer):
    """知识点序列化器"""
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = KnowledgePoint
        fields = ('id', 'subject', 'subject_name', 'name', 'parent', 'level', 'description', 'is_active', 'created_at', 'updated_at', 'children')
        read_only_fields = ('id', 'level', 'created_at', 'updated_at')
    
    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return KnowledgePointSerializer(children, many=True).data


class QuestionImageSerializer(serializers.ModelSerializer):
    """题目图片序列化器"""
    image_url = serializers.ImageField(source='image', read_only=True)
    
    class Meta:
        model = QuestionImage
        fields = ('id', 'image', 'image_url', 'description', 'is_main', 'created_at')
        read_only_fields = ('id', 'created_at')


class QuestionNoteSerializer(serializers.ModelSerializer):
    """错题笔记序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = QuestionNote
        fields = ('id', 'question', 'user', 'username', 'content', 'is_public', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'username', 'created_at', 'updated_at')


class QuestionReviewSerializer(serializers.ModelSerializer):
    """错题复习记录序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = QuestionReview
        fields = ('id', 'question', 'user', 'username', 'is_correct', 'review_time', 'notes', 'created_at')
        read_only_fields = ('id', 'user', 'username', 'created_at')


class QuestionTagSerializer(serializers.ModelSerializer):
    """题目标签序列化器"""
    
    class Meta:
        model = QuestionTag
        fields = ('id', 'name', 'color', 'created_at')
        read_only_fields = ('id', 'created_at')


class QuestionStatisticsSerializer(serializers.ModelSerializer):
    """题目统计序列化器"""
    
    class Meta:
        model = QuestionStatistics
        fields = ('id', 'question', 'view_count', 'review_count', 'last_reviewed_at', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class QuestionSerializer(serializers.ModelSerializer):
    """错题序列化器"""
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    knowledge_points_str = serializers.CharField(source='get_knowledge_points_str', read_only=True)
    tags_str = serializers.CharField(source='get_tags_str', read_only=True)
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    
    class Meta:
        model = Question
        fields = (
            'id', 'user', 'subject', 'subject_name', 'title', 'question_type', 'question_type_display',
            'difficulty', 'difficulty_display', 'source', 'source_display', 'tags', 'tags_str',
            'knowledge_points_str', 'is_solved', 'is_marked', 'view_count', 'created_at',
            'last_reviewed_at', 'review_count'
        )
        read_only_fields = ('id', 'user', 'view_count', 'created_at', 'last_reviewed_at', 'review_count')


class QuestionListSerializer(serializers.ModelSerializer):
    """错题列表序列化器"""
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    knowledge_points_str = serializers.CharField(source='get_knowledge_points_str', read_only=True)
    tags_str = serializers.CharField(source='get_tags_str', read_only=True)
    question_type_display = serializers.CharField(source='get_question_type_display', read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    
    class Meta:
        model = Question
        fields = (
            'id', 'user', 'subject', 'subject_name', 'title', 'question_type', 'question_type_display',
            'difficulty', 'difficulty_display', 'source', 'source_display', 'tags', 'tags_str',
            'knowledge_points_str', 'is_solved', 'is_marked', 'view_count', 'created_at',
            'last_reviewed_at', 'review_count'
        )
        read_only_fields = ('id', 'user', 'view_count', 'created_at', 'last_reviewed_at', 'review_count')


class QuestionDetailSerializer(QuestionListSerializer):
    """错题详情序列化器"""
    knowledge_points = serializers.SerializerMethodField()
    images = QuestionImageSerializer(many=True, read_only=True)
    notes = QuestionNoteSerializer(many=True, read_only=True)
    reviews = QuestionReviewSerializer(many=True, read_only=True)
    
    class Meta(QuestionListSerializer.Meta):
        fields = QuestionListSerializer.Meta.fields + (
            'content', 'options', 'correct_answer', 'user_answer', 'analysis',
            'source_detail', 'images', 'knowledge_points', 'notes', 'reviews'
        )
        read_only_fields = QuestionListSerializer.Meta.read_only_fields
    
    def get_knowledge_points(self, obj):
        return [{'id': kp.id, 'name': kp.name} for kp in obj.knowledge_points.all()]


class QuestionCreateSerializer(serializers.ModelSerializer):
    """错题创建序列化器"""
    images = serializers.ListField(child=serializers.ImageField(), required=False, write_only=True)
    
    class Meta:
        model = Question
        fields = (
            'subject', 'knowledge_points', 'title', 'content', 'question_type',
            'options', 'correct_answer', 'user_answer', 'analysis', 'difficulty',
            'source', 'source_detail', 'tags', 'images'
        )
    
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        knowledge_points = validated_data.pop('knowledge_points', [])
        
        question = Question.objects.create(**validated_data)
        
        # 添加知识点关联
        if knowledge_points:
            question.knowledge_points.set(knowledge_points)
        
        # 添加图片
        for i, image_data in enumerate(images_data):
            QuestionImage.objects.create(
                question=question,
                image=image_data,
                is_main=(i == 0)  # 第一张图为主图
            )
        
        logger.info("创建错题成功", question_id=question.id, user_id=question.user.id)
        return question


class QuestionUpdateSerializer(serializers.ModelSerializer):
    """错题更新序列化器"""
    knowledge_points = serializers.PrimaryKeyRelatedField(
        queryset=KnowledgePoint.objects.all(),
        many=True,
        required=False
    )
    
    class Meta:
        model = Question
        fields = (
            'subject', 'knowledge_points', 'title', 'content', 'question_type',
            'options', 'correct_answer', 'user_answer', 'analysis', 'difficulty',
            'source', 'source_detail', 'tags', 'is_solved', 'is_marked'
        )
    
    def update(self, instance, validated_data):
        knowledge_points = validated_data.pop('knowledge_points', None)
        
        # 更新知识点关联
        if knowledge_points is not None:
            instance.knowledge_points.set(knowledge_points)
        
        # 更新其他字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # 如果标记为已解决，调用相应方法
        if validated_data.get('is_solved', False) and not instance.is_solved:
            instance.mark_as_solved()
        
        logger.info("更新错题成功", question_id=instance.id, user_id=instance.user.id)
        return instance


class QuestionNoteCreateSerializer(serializers.ModelSerializer):
    """错题笔记创建序列化器"""
    
    class Meta:
        model = QuestionNote
        fields = ('question', 'content', 'is_public')
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        note = QuestionNote.objects.create(**validated_data)
        logger.info("创建错题笔记成功", note_id=note.id, question_id=note.question.id, user_id=user.id)
        return note


class QuestionReviewCreateSerializer(serializers.ModelSerializer):
    """错题复习记录创建序列化器"""
    
    class Meta:
        model = QuestionReview
        fields = ('question', 'is_correct', 'review_time', 'notes')
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        review = QuestionReview.objects.create(**validated_data)
        
        # 更新错题的复习信息
        question = review.question
        question.last_reviewed_at = review.created_at
        question.review_count += 1
        question.save(update_fields=['last_reviewed_at', 'review_count'])
        
        logger.info("创建错题复习记录成功", review_id=review.id, question_id=question.id, user_id=user.id)
        return review


class QuestionBatchCreateSerializer(serializers.Serializer):
    """批量创建错题序列化器"""
    questions = QuestionCreateSerializer(many=True)
    
    def create(self, validated_data):
        user = self.context['request'].user
        questions_data = validated_data.get('questions', [])
        created_questions = []
        
        for question_data in questions_data:
            images_data = question_data.pop('images', [])
            knowledge_points = question_data.pop('knowledge_points', [])
            
            question = Question.objects.create(user=user, **question_data)
            
            # 添加知识点关联
            if knowledge_points:
                question.knowledge_points.set(knowledge_points)
            
            # 添加图片
            for i, image_data in enumerate(images_data):
                QuestionImage.objects.create(
                    question=question,
                    image=image_data,
                    is_main=(i == 0)  # 第一张图为主图
                )
            
            created_questions.append(question)
        
        logger.info("批量创建错题成功", count=len(created_questions), user_id=user.id)
        return created_questions


class QuestionBatchUpdateSerializer(serializers.Serializer):
    """批量更新错题序列化器"""
    ids = serializers.ListField(child=serializers.IntegerField())
    data = QuestionUpdateSerializer()
    
    def update(self, instance, validated_data):
        ids = validated_data.get('ids', [])
        data = validated_data.get('data', {})
        
        questions = Question.objects.filter(id__in=ids)
        updated_questions = []
        
        for question in questions:
            knowledge_points = data.get('knowledge_points', None)
            
            # 更新知识点关联
            if knowledge_points is not None:
                question.knowledge_points.set(knowledge_points)
            
            # 更新其他字段
            for attr, value in data.items():
                if attr != 'knowledge_points':
                    setattr(question, attr, value)
            
            question.save()
            
            # 如果标记为已解决，调用相应方法
            if data.get('is_solved', False) and not question.is_solved:
                question.mark_as_solved()
            
            updated_questions.append(question)
        
        logger.info("批量更新错题成功", count=len(updated_questions))
        return updated_questions