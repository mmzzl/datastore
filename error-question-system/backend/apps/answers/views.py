from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import structlog

from .models import Answer, AnswerImage, AnswerComment, AnswerLike, CommentLike
from .serializers import (
    AnswerImageSerializer, CommentLikeSerializer, AnswerCommentSerializer,
    AnswerLikeSerializer, AnswerSerializer, AnswerDetailSerializer,
    AnswerCreateSerializer, AnswerUpdateSerializer
)

logger = structlog.get_logger(__name__)


class AnswerViewSet(viewsets.ModelViewSet):
    """答案视图集"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['question', 'is_correct', 'is_public']
    search_fields = ['content']
    ordering_fields = ['created_at', 'updated_at', 'like_count']
    ordering = ['-created_at']
    queryset = Answer.objects.all()
    
    def get_queryset(self):
        """获取答案列表，根据用户权限过滤"""
        user = self.request.user
        queryset = Answer.objects.all()
        
        # 非管理员只能看到自己的答案和公开的答案
        if not user.is_staff:
            queryset = queryset.filter(
                Q(user=user) | Q(is_public=True)
            )
        
        # 按题目过滤
        question_id = self.request.query_params.get('question_id')
        if question_id:
            queryset = queryset.filter(question_id=question_id)
        
        # 按用户过滤
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset
    
    def get_serializer_class(self):
        """根据操作类型选择序列化器"""
        if self.action == 'create':
            return AnswerCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return AnswerUpdateSerializer
        elif self.action == 'retrieve':
            return AnswerDetailSerializer
        return AnswerSerializer
    
    def perform_create(self, serializer):
        """创建答案时设置用户"""
        serializer.save(user=self.request.user)
        
        # 记录用户活动
        from apps.system.models import UserActivityLog
        UserActivityLog.objects.create(
            user=self.request.user,
            action='create_answer',
            resource_type='answer',
            resource_id=serializer.instance.id,
            description="创建答案",
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("创建答案成功", answer_id=serializer.instance.id, user_id=self.request.user.id)
    
    def perform_update(self, serializer):
        """更新答案时记录活动"""
        serializer.save()
        
        # 记录用户活动
        from apps.system.models import UserActivityLog
        UserActivityLog.objects.create(
            user=self.request.user,
            action='update_answer',
            resource_type='answer',
            resource_id=serializer.instance.id,
            description="更新答案",
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("更新答案成功", answer_id=serializer.instance.id, user_id=self.request.user.id)
    
    @extend_schema(
        summary="点赞答案",
        description="点赞或取消点赞指定答案",
        request=None,
        responses={200: {'type': 'object'}}
    )
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """点赞答案"""
        answer = self.get_object()
        user = request.user
        
        # 检查是否已点赞
        like_exists = AnswerLike.objects.filter(answer=answer, user=user).exists()
        
        if like_exists:
            # 取消点赞
            AnswerLike.objects.filter(answer=answer, user=user).delete()
            answer.like_count = max(0, answer.like_count - 1)
            is_liked = False
            action_text = "取消点赞"
        else:
            # 点赞
            AnswerLike.objects.create(answer=answer, user=user)
            answer.like_count += 1
            is_liked = True
            action_text = "点赞"
        
        answer.save(update_fields=['like_count'])
        
        # 记录用户活动
        from apps.system.models import UserActivityLog
        UserActivityLog.objects.create(
            user=user,
            action='like_answer' if is_liked else 'unlike_answer',
            resource_type='answer',
            resource_id=answer.id,
            description=f"{action_text}答案",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("答案点赞状态更新", answer_id=answer.id, user_id=user.id, is_liked=is_liked)
        
        return Response({
            'is_liked': is_liked,
            'like_count': answer.like_count
        })
    
    @extend_schema(
        summary="标记答案为正确",
        description="将指定答案标记为正确答案",
        request=None,
        responses={200: AnswerSerializer}
    )
    @action(detail=True, methods=['post'])
    def mark_correct(self, request, pk=None):
        """标记答案为正确"""
        answer = self.get_object()
        question = answer.question
        
        # 检查权限：只有题目创建者可以标记答案为正确
        if question.user != request.user:
            return Response(
                {'error': '只有题目创建者可以标记答案为正确'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 取消该题目的其他正确答案
        Answer.objects.filter(question=question, is_correct=True).update(is_correct=False)
        
        # 标记当前答案为正确
        answer.is_correct = True
        answer.save(update_fields=['is_correct'])
        
        # 记录用户活动
        from apps.system.models import UserActivityLog
        UserActivityLog.objects.create(
            user=request.user,
            action='mark_correct',
            resource_type='answer',
            resource_id=answer.id,
            description="标记答案为正确",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("标记答案为正确", answer_id=answer.id, user_id=request.user.id)
        
        serializer = self.get_serializer(answer)
        return Response(serializer.data)
    
    @extend_schema(
        summary="获取答案评论",
        description="获取指定答案的评论列表",
        parameters=[
            OpenApiParameter(
                name='page',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='页码',
                default=1
            ),
            OpenApiParameter(
                name='page_size',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='每页数量',
                default=20
            )
        ],
        responses={200: AnswerCommentSerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def comments(self, request, pk=None):
        """获取答案评论"""
        answer = self.get_object()
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 20))
        
        comments = AnswerComment.objects.filter(answer=answer).order_by('-created_at')
        
        # 简单分页
        start = (page - 1) * page_size
        end = start + page_size
        page_comments = comments[start:end]
        
        serializer = AnswerCommentSerializer(page_comments, many=True)
        
        return Response({
            'count': comments.count(),
            'results': serializer.data,
            'page': page,
            'page_size': page_size,
            'total_pages': (comments.count() + page_size - 1) // page_size
        })
    
    @extend_schema(
        summary="添加答案评论",
        description="为指定答案添加评论",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'content': {'type': 'string'}
                },
                'required': ['content']
            }
        },
        responses={201: AnswerCommentSerializer}
    )
    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        """添加答案评论"""
        answer = self.get_object()
        content = request.data.get('content', '').strip()
        
        if not content:
            return Response(
                {'error': '评论内容不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        comment = AnswerComment.objects.create(
            answer=answer,
            user=request.user,
            content=content
        )
        
        # 更新答案评论数
        answer.comment_count = AnswerComment.objects.filter(answer=answer).count()
        answer.save(update_fields=['comment_count'])
        
        # 记录用户活动
        from apps.system.models import UserActivityLog
        UserActivityLog.objects.create(
            user=request.user,
            action='comment_answer',
            resource_type='answer',
            resource_id=answer.id,
            description="评论答案",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("添加答案评论成功", comment_id=comment.id, answer_id=answer.id, user_id=request.user.id)
        
        serializer = AnswerCommentSerializer(comment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AnswerCommentViewSet(viewsets.ModelViewSet):
    """答案评论视图集"""
    serializer_class = AnswerCommentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['answer']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    queryset = AnswerComment.objects.all()
    
    def get_queryset(self):
        """获取评论列表，根据用户权限过滤"""
        user = self.request.user
        queryset = AnswerComment.objects.all()
        
        # 非管理员只能看到自己的评论和公开答案的评论
        if not user.is_staff:
            queryset = queryset.filter(
                Q(user=user) | Q(answer__is_public=True)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """创建评论时设置用户"""
        serializer.save(user=self.request.user)
        
        # 更新答案评论数
        answer = serializer.instance.answer
        answer.comment_count = AnswerComment.objects.filter(answer=answer).count()
        answer.save(update_fields=['comment_count'])
        
        # 记录用户活动
        from apps.system.models import UserActivityLog
        UserActivityLog.objects.create(
            user=self.request.user,
            action='create_comment',
            resource_type='comment',
            resource_id=serializer.instance.id,
            description="创建评论",
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("创建评论成功", comment_id=serializer.instance.id, user_id=self.request.user.id)
    
    def perform_destroy(self, instance):
        """删除评论时更新答案评论数"""
        answer = instance.answer
        super().perform_destroy(instance)
        
        # 更新答案评论数
        answer.comment_count = AnswerComment.objects.filter(answer=answer).count()
        answer.save(update_fields=['comment_count'])
        
        # 记录用户活动
        from apps.system.models import UserActivityLog
        UserActivityLog.objects.create(
            user=self.request.user,
            action='delete_comment',
            resource_type='comment',
            resource_id=instance.id,
            description="删除评论",
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("删除评论成功", comment_id=instance.id, user_id=self.request.user.id)
    
    @extend_schema(
        summary="点赞评论",
        description="点赞或取消点赞指定评论",
        request=None,
        responses={200: {'type': 'object'}}
    )
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """点赞评论"""
        comment = self.get_object()
        user = request.user
        
        # 检查是否已点赞
        like_exists = CommentLike.objects.filter(comment=comment, user=user).exists()
        
        if like_exists:
            # 取消点赞
            CommentLike.objects.filter(comment=comment, user=user).delete()
            comment.like_count = max(0, comment.like_count - 1)
            is_liked = False
            action_text = "取消点赞"
        else:
            # 点赞
            CommentLike.objects.create(comment=comment, user=user)
            comment.like_count += 1
            is_liked = True
            action_text = "点赞"
        
        comment.save(update_fields=['like_count'])
        
        # 记录用户活动
        from apps.system.models import UserActivityLog
        UserActivityLog.objects.create(
            user=user,
            action='like_comment' if is_liked else 'unlike_comment',
            resource_type='comment',
            resource_id=comment.id,
            description=f"{action_text}评论",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("评论点赞状态更新", comment_id=comment.id, user_id=user.id, is_liked=is_liked)
        
        return Response({
            'is_liked': is_liked,
            'like_count': comment.like_count
        })