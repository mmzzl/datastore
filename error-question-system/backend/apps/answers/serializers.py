from rest_framework import serializers
from .models import Answer, AnswerImage, AnswerComment, AnswerLike, CommentLike
import structlog

logger = structlog.get_logger(__name__)


class AnswerImageSerializer(serializers.ModelSerializer):
    """答案图片序列化器"""
    image_url = serializers.ImageField(source='image', read_only=True)
    
    class Meta:
        model = AnswerImage
        fields = ('id', 'image', 'image_url', 'description', 'created_at')
        read_only_fields = ('id', 'created_at')


class CommentLikeSerializer(serializers.ModelSerializer):
    """评论点赞序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = CommentLike
        fields = ('id', 'comment', 'user', 'username', 'created_at')
        read_only_fields = ('id', 'user', 'username', 'created_at')


class AnswerCommentSerializer(serializers.ModelSerializer):
    """答案评论序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True)
    replies = serializers.SerializerMethodField()
    likes_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = AnswerComment
        fields = (
            'id', 'answer', 'user', 'username', 'user_avatar', 'parent', 'content',
            'is_deleted', 'likes_count', 'is_liked', 'created_at', 'updated_at', 'replies'
        )
        read_only_fields = ('id', 'user', 'username', 'user_avatar', 'likes_count', 'created_at', 'updated_at')
    
    def get_replies(self, obj):
        if not obj.replies.exists():
            return []
        replies = obj.replies.filter(is_deleted=False)
        return AnswerCommentSerializer(replies, many=True, context=self.context).data
    
    def get_is_liked(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return CommentLike.objects.filter(comment=obj, user=user).exists()


class AnswerLikeSerializer(serializers.ModelSerializer):
    """答案点赞序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AnswerLike
        fields = ('id', 'answer', 'user', 'username', 'created_at')
        read_only_fields = ('id', 'user', 'username', 'created_at')


class AnswerSerializer(serializers.ModelSerializer):
    """答案列表序列化器"""
    username = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.ImageField(source='user.avatar', read_only=True)
    question_title = serializers.CharField(source='question.title', read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    views_count = serializers.IntegerField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Answer
        fields = (
            'id', 'question', 'question_title', 'user', 'username', 'user_avatar',
            'content', 'is_verified', 'is_public', 'likes_count', 'views_count',
            'is_liked', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'username', 'user_avatar', 'likes_count', 'views_count', 'created_at', 'updated_at')
    
    def get_is_liked(self, obj):
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return AnswerLike.objects.filter(answer=obj, user=user).exists()


class AnswerDetailSerializer(AnswerSerializer):
    """答案详情序列化器"""
    images = AnswerImageSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()
    
    class Meta(AnswerSerializer.Meta):
        fields = AnswerSerializer.Meta.fields + (
            'explanation', 'steps', 'images', 'source', 'comments'
        )
    
    def get_comments(self, obj):
        comments = obj.comments.filter(parent=None, is_deleted=False)
        return AnswerCommentSerializer(comments, many=True, context=self.context).data


class AnswerCreateSerializer(serializers.ModelSerializer):
    """答案创建序列化器"""
    images = serializers.ListField(child=serializers.ImageField(), required=False, write_only=True)
    
    class Meta:
        model = Answer
        fields = (
            'question', 'content', 'explanation', 'steps', 'images',
            'source', 'is_verified', 'is_public'
        )
    
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        user = self.context['request'].user
        validated_data['user'] = user
        
        answer = Answer.objects.create(**validated_data)
        
        # 添加图片
        for image_data in images_data:
            AnswerImage.objects.create(answer=answer, image=image_data)
        
        logger.info("创建答案成功", answer_id=answer.id, question_id=answer.question.id, user_id=user.id)
        return answer


class AnswerUpdateSerializer(serializers.ModelSerializer):
    """答案更新序列化器"""
    
    class Meta:
        model = Answer
        fields = (
            'content', 'explanation', 'steps', 'source', 'is_verified', 'is_public'
        )
    
    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        logger.info("更新答案成功", answer_id=instance.id, question_id=instance.question.id, user_id=instance.user.id)
        return instance


class AnswerCommentCreateSerializer(serializers.ModelSerializer):
    """答案评论创建序列化器"""
    
    class Meta:
        model = AnswerComment
        fields = ('answer', 'parent', 'content')
    
    def create(self, validated_data):
        user = self.context['request'].user
        validated_data['user'] = user
        comment = AnswerComment.objects.create(**validated_data)
        
        logger.info("创建答案评论成功", comment_id=comment.id, answer_id=comment.answer.id, user_id=user.id)
        return comment