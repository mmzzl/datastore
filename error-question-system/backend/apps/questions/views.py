from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Avg
from django.utils import timezone
from django.core.files.storage import default_storage
from django.conf import settings
import os
import uuid
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import structlog

from .models import Subject, KnowledgePoint, Question, QuestionImage, QuestionStatistics, QuestionTag
from .serializers import (
    SubjectSerializer, KnowledgePointSerializer, QuestionImageSerializer,
    QuestionSerializer, QuestionDetailSerializer, QuestionCreateSerializer,
    QuestionUpdateSerializer, QuestionStatisticsSerializer, QuestionTagSerializer,
    QuestionBatchCreateSerializer, QuestionBatchUpdateSerializer
)

logger = structlog.get_logger(__name__)


class SubjectViewSet(viewsets.ModelViewSet):
    """科目视图集"""
    queryset = Subject.objects.filter(is_active=True)
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @extend_schema(
        summary="获取科目统计信息",
        description="获取指定科目的题目统计信息",
        responses={200: {'type': 'object'}}
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取科目统计信息"""
        subject = self.get_object()
        
        # 计算科目下的题目统计
        question_stats = Question.objects.filter(
            subject=subject
        ).aggregate(
            total=Count('id'),
            solved=Count('id', filter=Q(is_solved=True)),
            marked=Count('id', filter=Q(is_marked=True)),
            avg_difficulty=Avg('difficulty')
        )
        
        # 按难度统计
        difficulty_stats = Question.objects.filter(
            subject=subject
        ).values('difficulty').annotate(
            count=Count('id')
        ).order_by('difficulty')
        
        # 按类型统计
        type_stats = Question.objects.filter(
            subject=subject
        ).values('question_type').annotate(
            count=Count('id')
        ).order_by('question_type')
        
        data = {
            'subject': SubjectSerializer(subject).data,
            'total_questions': question_stats['total'],
            'solved_questions': question_stats['solved'],
            'marked_questions': question_stats['marked'],
            'avg_difficulty': question_stats['avg_difficulty'],
            'difficulty_distribution': list(difficulty_stats),
            'type_distribution': list(type_stats)
        }
        return Response(data)


@extend_schema(
    summary="上传文件",
    description="上传图片或PDF文件",
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'file': {
                    'type': 'string',
                    'format': 'binary'
                }
            }
        }
    },
    responses={
        200: {
            'type': 'object',
            'properties': {
                'url': {'type': 'string'},
                'name': {'type': 'string'},
                'type': {'type': 'string'}
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser])
def upload_file(request):
    """上传文件接口"""
    file_obj = request.FILES.get('file')
    if not file_obj:
        return Response({'error': '没有提供文件'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate unique filename
    ext = os.path.splitext(file_obj.name)[1].lower()
    filename = f"{uuid.uuid4()}{ext}"
    
    # Determine subdirectory based on extension
    subdir = 'others'
    if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        subdir = 'images'
    elif ext in ['.pdf']:
        subdir = 'documents'
        
    # Save file
    save_path = os.path.join('uploads', subdir, filename)
    name = default_storage.save(save_path, file_obj)
    
    # Generate URL
    url = request.build_absolute_uri(settings.MEDIA_URL + name)
    
    return Response({
        'url': url,
        'name': file_obj.name,
        'type': subdir
    })

class KnowledgePointViewSet(viewsets.ModelViewSet):
    """知识点视图集"""
    serializer_class = KnowledgePointSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subject', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    queryset = KnowledgePoint.objects.all()
    
    def get_queryset(self):
        """根据科目过滤知识点"""
        queryset = KnowledgePoint.objects.filter(is_active=True)
        subject_id = self.request.query_params.get('subject_id')
        if subject_id:
            queryset = queryset.filter(subject_id=subject_id)
        return queryset
    
    @extend_schema(
        summary="获取知识点统计信息",
        description="获取指定知识点的题目统计信息",
        responses={200: {'type': 'object'}}
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取知识点统计信息"""
        knowledge_point = self.get_object()
        
        # 计算知识点下的题目统计
        question_stats = Question.objects.filter(
            knowledge_points=knowledge_point
        ).aggregate(
            total=Count('id'),
            solved=Count('id', filter=Q(is_solved=True)),
            marked=Count('id', filter=Q(is_marked=True)),
            avg_difficulty=Avg('difficulty')
        )
        
        data = {
            'knowledge_point': KnowledgePointSerializer(knowledge_point).data,
            'total_questions': question_stats['total'],
            'solved_questions': question_stats['solved'],
            'marked_questions': question_stats['marked'],
            'avg_difficulty': question_stats['avg_difficulty']
        }
        
        return Response(data)


class QuestionViewSet(viewsets.ModelViewSet):
    """题目视图集"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['subject', 'difficulty', 'question_type', 'is_solved', 'is_marked']
    search_fields = ['title', 'content', 'answer', 'analysis']
    ordering_fields = ['created_at', 'updated_at', 'view_count', 'review_count', 'title']
    ordering = ['-created_at']
    queryset = Question.objects.all()
    
    def get_queryset(self):
        """获取当前用户的题目列表"""
        user = self.request.user
        queryset = Question.objects.filter(user=user)
        
        # 按知识点过滤
        knowledge_point_ids = self.request.query_params.get('knowledge_points')
        if knowledge_point_ids:
            ids = [int(id) for id in knowledge_point_ids.split(',')]
            queryset = queryset.filter(knowledge_points__id__in=ids).distinct()
        
        # 按标签过滤
        tags = self.request.query_params.get('tags')
        if tags:
            tag_list = tags.split(',')
            queryset = queryset.filter(tags__name__in=tag_list).distinct()
        
        # 按日期范围过滤
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset
    
    def get_serializer_class(self):
        """根据操作类型选择序列化器"""
        if self.action == 'create':
            return QuestionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return QuestionUpdateSerializer
        elif self.action == 'retrieve':
            return QuestionDetailSerializer
        return QuestionSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """获取题目详情，增加查看次数"""
        instance = self.get_object()
        
        # 增加查看次数
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        
        # 更新或创建统计信息
        statistics, created = QuestionStatistics.objects.get_or_create(
            question=instance,
            defaults={'view_count': 1}
        )
        if not created:
            statistics.view_count += 1
            statistics.save(update_fields=['view_count'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @extend_schema(
        summary="标记题目为已解决",
        description="将指定题目标记为已解决或未解决",
        request=None,
        responses={200: QuestionSerializer}
    )
    @action(detail=True, methods=['post'])
    def mark_solved(self, request, pk=None):
        """标记题目为已解决"""
        question = self.get_object()
        is_solved = not question.is_solved
        question.is_solved = is_solved
        question.save(update_fields=['is_solved'])
        
        # 记录用户活动
        from apps.authentication.models import UserActivityLog
        UserActivityLog.objects.create(
            user=request.user,
            action='mark_solved' if is_solved else 'mark_unsolved',
            object_type='question',
            object_id=question.id,
            object_repr=question.title[:100],
            details={"ip_address": request.META.get('REMOTE_ADDR')},
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("题目解决状态更新", question_id=question.id, is_solved=is_solved)
        
        serializer = self.get_serializer(question)
        return Response(serializer.data)
    
    @extend_schema(
        summary="标记题目为收藏",
        description="将指定题目标记为收藏或取消收藏",
        request=None,
        responses={200: QuestionSerializer}
    )
    @action(detail=True, methods=['post'])
    def mark(self, request, pk=None):
        """标记题目为收藏"""
        question = self.get_object()
        is_marked = not question.is_marked
        question.is_marked = is_marked
        question.save(update_fields=['is_marked'])
        
        # 记录用户活动
        from apps.authentication.models import UserActivityLog
        UserActivityLog.objects.create(
            user=request.user,
            action='mark' if is_marked else 'unmark',
            object_type='question',
            object_id=question.id,
            object_repr=question.title[:100],
            details={"ip_address": request.META.get('REMOTE_ADDR')},
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("题目收藏状态更新", question_id=question.id, is_marked=is_marked)
        
        serializer = self.get_serializer(question)
        return Response(serializer.data)
    
    @extend_schema(
        summary="复习题目",
        description="标记题目为已复习，增加复习次数",
        request=None,
        responses={200: QuestionSerializer}
    )
    @action(detail=True, methods=['post'])
    def review(self, request, pk=None):
        """复习题目"""
        question = self.get_object()
        question.review_count += 1
        question.last_reviewed_at = timezone.now()
        question.save(update_fields=['review_count', 'last_reviewed_at'])
        
        # 更新统计信息
        statistics, created = QuestionStatistics.objects.get_or_create(
            question=question,
            defaults={'review_count': 1}
        )
        if not created:
            statistics.review_count += 1
            statistics.last_reviewed_at = timezone.now()
            statistics.save(update_fields=['review_count', 'last_reviewed_at'])
        
        # 记录用户活动
        from apps.authentication.models import UserActivityLog
        UserActivityLog.objects.create(
            user=request.user,
            action='review',
            object_type='question',
            object_id=question.id,
            object_repr=question.title[:100],
            details={"ip_address": request.META.get('REMOTE_ADDR')},
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("题目复习", question_id=question.id)
        
        serializer = self.get_serializer(question)
        return Response(serializer.data)
    
    @extend_schema(
        summary="批量创建题目",
        description="批量创建多个题目",
        request=QuestionBatchCreateSerializer,
        responses={201: QuestionSerializer(many=True)}
    )
    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        """批量创建题目"""
        serializer = QuestionBatchCreateSerializer(data=request.data)
        if serializer.is_valid():
            questions = serializer.save(user=request.user)
            
            # 记录用户活动
            from apps.authentication.models import UserActivityLog
            UserActivityLog.objects.create(
                user=request.user,
                action='batch_create',
                object_type='question',
                object_repr=f"批量创建{len(questions)}个题目",
                details={"ip_address": request.META.get('REMOTE_ADDR')},
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            logger.info("批量创建题目成功", count=len(questions))
            
            response_serializer = QuestionSerializer(questions, many=True)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        logger.warning("批量创建题目验证失败", errors=serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="批量更新题目",
        description="批量更新多个题目",
        request=QuestionBatchUpdateSerializer,
        responses={200: QuestionSerializer(many=True)}
    )
    @action(detail=False, methods=['put'])
    def batch_update(self, request):
        """批量更新题目"""
        serializer = QuestionBatchUpdateSerializer(data=request.data)
        if serializer.is_valid():
            questions = serializer.save()
            
            # 记录用户活动
            from apps.authentication.models import UserActivityLog
            UserActivityLog.objects.create(
                user=request.user,
                action='batch_update',
                object_type='question',
                object_repr=f"批量更新{len(questions)}个题目",
                details={"ip_address": request.META.get('REMOTE_ADDR')},
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            logger.info("批量更新题目成功", count=len(questions))
            
            response_serializer = QuestionSerializer(questions, many=True)
            return Response(response_serializer.data)
        
        logger.warning("批量更新题目验证失败", errors=serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="获取题目统计",
        description="获取当前用户的题目统计信息",
        responses={200: {'type': 'object'}}
    )
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取题目统计信息"""
        user = request.user
        
        # 基本统计
        total = Question.objects.filter(user=user).count()
        solved = Question.objects.filter(user=user, is_solved=True).count()
        marked = Question.objects.filter(user=user, is_marked=True).count()
        reviewed = Question.objects.filter(user=user, last_reviewed_at__isnull=False).count()
        
        # 按科目统计
        subject_stats = Question.objects.filter(user=user).values(
            'subject__name'
        ).annotate(
            count=Count('id'),
            solved=Count('id', filter=Q(is_solved=True))
        ).order_by('-count')
        
        # 按难度统计
        difficulty_stats = Question.objects.filter(user=user).values(
            'difficulty'
        ).annotate(
            count=Count('id')
        ).order_by('difficulty')
        
        # 按类型统计
        type_stats = Question.objects.filter(user=user).values(
            'question_type'
        ).annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 最近7天创建统计
        seven_days_ago = timezone.now() - timezone.timedelta(days=7)
        recent_stats = Question.objects.filter(
            user=user,
            created_at__gte=seven_days_ago
        ).count()
        
        data = {
            'total_questions': total,
            'solved_questions': solved,
            'marked_questions': marked,
            'reviewed_questions': reviewed,
            'solved_rate': round(solved / total * 100, 2) if total > 0 else 0,
            'marked_rate': round(marked / total * 100, 2) if total > 0 else 0,
            'reviewed_rate': round(reviewed / total * 100, 2) if total > 0 else 0,
            'recent_created': recent_stats,
            'subject_distribution': list(subject_stats),
            'difficulty_distribution': list(difficulty_stats),
            'type_distribution': list(type_stats)
        }
        
        return Response(data)

    @extend_schema(
        summary="获取最近错题",
        description="获取当前用户最近创建的错题",
        responses={200: QuestionSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """获取最近错题"""
        user = request.user
        limit = int(request.query_params.get('limit', 10))
        
        # 获取最近创建的错题
        recent_questions = Question.objects.filter(
            user=user
        ).order_by('-created_at')[:limit]
        
        serializer = self.get_serializer(recent_questions, many=True)
        
        # 返回统一格式的响应
        return Response({
            'code': 200,
            'message': '获取成功',
            'data': serializer.data
        })


class QuestionTagViewSet(viewsets.ModelViewSet):
    """题目标签视图集"""
    serializer_class = QuestionTagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    queryset = QuestionTag.objects.none()  # 添加一个空的queryset以满足路由器要求
    
    def get_queryset(self):
        """获取当前用户的标签列表"""
        return QuestionTag.objects.filter(user=self.request.user)
    
    @extend_schema(
        summary="获取热门标签",
        description="获取当前用户使用频率最高的标签",
        responses={200: QuestionTagSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """获取热门标签"""
        limit = int(request.query_params.get('limit', 20))
        
        # 获取使用频率最高的标签
        popular_tags = QuestionTag.objects.filter(
            user=request.user
        ).annotate(
            question_count=Count('questions')
        ).filter(
            question_count__gt=0
        ).order_by('-question_count')[:limit]
        
        serializer = self.get_serializer(popular_tags, many=True)
        return Response(serializer.data)


from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@extend_schema(
    summary="获取用户统计数据",
    description="获取当前用户的错题统计信息",
    responses={200: {'type': 'object'}}
)
def user_stats(request):
    """获取用户统计数据"""
    user = request.user
    
    # 基本统计
    total_questions = Question.objects.filter(user=user).count()
    solved_questions = Question.objects.filter(user=user, is_solved=True).count()
    categories = Subject.objects.filter(questions__user=user).distinct().count()
    
    data = {
        'code': 200,
        'message': '获取成功',
        'data': {
            'totalQuestions': total_questions,
            'solvedQuestions': solved_questions,
            'categories': categories
        }
    }
    
    return Response(data)