from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import structlog

from .models import Category, QuestionCategory
from .serializers import (
    CategorySerializer, CategoryTreeSerializer, QuestionCategorySerializer,
    CategoryCreateSerializer, CategoryUpdateSerializer, CategoryBatchCreateSerializer
)

logger = structlog.get_logger(__name__)


class CategoryViewSet(viewsets.ModelViewSet):
    """分类视图集"""
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    queryset = Category.objects.none()  # 添加一个空的queryset以满足路由器要求
    
    def get_queryset(self):
        """获取当前用户的分类列表"""
        return Category.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """根据操作类型选择序列化器"""
        if self.action == 'create':
            return CategoryCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return CategoryUpdateSerializer
        return CategorySerializer
    
    def perform_create(self, serializer):
        """创建分类时设置用户"""
        serializer.save(user=self.request.user)
        
        # 记录用户活动
        from apps.authentication.models import UserActivityLog
        UserActivityLog.objects.create(
            user=self.request.user,
            action='create_category',
            object_type='category',
            object_id=serializer.instance.id,
            object_repr=serializer.instance.name[:100],
            details={"ip_address": self.request.META.get('REMOTE_ADDR')},
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("创建分类成功", category_id=serializer.instance.id, user_id=self.request.user.id)
    
    def perform_update(self, serializer):
        """更新分类时记录活动"""
        serializer.save()
        
        # 记录用户活动
        from apps.authentication.models import UserActivityLog
        UserActivityLog.objects.create(
            user=self.request.user,
            action='update_category',
            object_type='category',
            object_id=serializer.instance.id,
            object_repr=serializer.instance.name[:100],
            details={"ip_address": self.request.META.get('REMOTE_ADDR')},
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("更新分类成功", category_id=serializer.instance.id, user_id=self.request.user.id)
    
    def destroy(self, request, *args, **kwargs):
        """删除分类前检查是否有子分类和关联的题目"""
        instance = self.get_object()
        
        # 检查是否有子分类
        has_children = Category.objects.filter(parent=instance).exists()
        if has_children:
            return Response(
                {'error': '无法删除包含子分类的分类，请先删除或移动子分类'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查是否有关联的题目
        has_questions = QuestionCategory.objects.filter(category=instance).exists()
        if has_questions:
            return Response(
                {'error': '无法删除包含题目的分类，请先移除分类中的题目'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 记录用户活动
        from apps.authentication.models import UserActivityLog
        UserActivityLog.objects.create(
            user=request.user,
            action='delete_category',
            object_type='category',
            object_id=instance.id,
            object_repr=instance.name[:100],
            details={"ip_address": request.META.get('REMOTE_ADDR')},
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("删除分类成功", category_id=instance.id, user_id=request.user.id)
        
        return super().destroy(request, *args, **kwargs)
    
    @extend_schema(
        summary="获取分类树",
        description="获取当前用户的分类树结构",
        responses={200: CategoryTreeSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """获取分类树"""
        categories = Category.objects.filter(
            user=request.user,
            parent=None,
            is_active=True
        ).prefetch_related('children')
        
        serializer = CategoryTreeSerializer(categories, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="获取分类统计",
        description="获取指定分类的题目统计信息",
        responses={200: {'type': 'object'}}
    )
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取分类统计信息"""
        category = self.get_object()
        
        # 获取分类下的所有题目ID（包括子分类）
        category_ids = [category.id]
        self._get_all_children_ids(category, category_ids)
        
        # 计算题目统计
        from apps.questions.models import Question
        question_stats = Question.objects.filter(
            id__in=QuestionCategory.objects.filter(
                category_id__in=category_ids
            ).values_list('question_id', flat=True)
        ).aggregate(
            total=Count('id'),
            solved=Count('id', filter=Q(is_solved=True)),
            marked=Count('id', filter=Q(is_marked=True))
        )
        
        # 按难度统计
        difficulty_stats = Question.objects.filter(
            id__in=QuestionCategory.objects.filter(
                category_id__in=category_ids
            ).values_list('question_id', flat=True)
        ).values('difficulty').annotate(
            count=Count('id')
        ).order_by('difficulty')
        
        # 按类型统计
        type_stats = Question.objects.filter(
            id__in=QuestionCategory.objects.filter(
                category_id__in=category_ids
            ).values_list('question_id', flat=True)
        ).values('question_type').annotate(
            count=Count('id')
        ).order_by('question_type')
        
        # 子分类统计
        children_stats = Category.objects.filter(
            parent=category
        ).annotate(
            question_count=Count('questioncategory')
        ).order_by('-question_count')
        
        data = {
            'category': CategorySerializer(category).data,
            'total_questions': question_stats['total'],
            'solved_questions': question_stats['solved'],
            'marked_questions': question_stats['marked'],
            'difficulty_distribution': list(difficulty_stats),
            'type_distribution': list(type_stats),
            'children_stats': CategorySerializer(children_stats, many=True).data
        }
        
        return Response(data)
    
    def _get_all_children_ids(self, category, ids):
        """递归获取所有子分类ID"""
        children = Category.objects.filter(parent=category)
        for child in children:
            ids.append(child.id)
            self._get_all_children_ids(child, ids)
    
    @extend_schema(
        summary="批量创建分类",
        description="批量创建多个分类",
        request=CategoryBatchCreateSerializer,
        responses={201: CategorySerializer(many=True)}
    )
    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        """批量创建分类"""
        serializer = CategoryBatchCreateSerializer(data=request.data)
        if serializer.is_valid():
            categories = serializer.save(user=request.user)
            
            # 记录用户活动
            from apps.authentication.models import UserActivityLog
            UserActivityLog.objects.create(
                user=request.user,
                action='batch_create_category',
                object_type='category',
                object_repr=f"批量创建{len(categories)}个分类",
                details={"ip_address": request.META.get('REMOTE_ADDR')},
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            logger.info("批量创建分类成功", count=len(categories))
            
            response_serializer = CategorySerializer(categories, many=True)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        logger.warning("批量创建分类验证失败", errors=serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="移动分类",
        description="将分类移动到新的父分类下",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'parent_id': {'type': 'integer', 'nullable': True}
                },
                'required': ['parent_id']
            }
        },
        responses={200: CategorySerializer}
    )
    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """移动分类"""
        category = self.get_object()
        parent_id = request.data.get('parent_id')
        
        # 检查是否移动到自己的子分类下（防止循环）
        if parent_id:
            try:
                parent = Category.objects.get(id=parent_id, user=request.user)
                if self._is_child_category(parent, category):
                    return Response(
                        {'error': '不能将分类移动到自己的子分类下'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            except Category.DoesNotExist:
                return Response(
                    {'error': '目标父分类不存在'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # 更新父分类
        category.parent_id = parent_id
        category.save(update_fields=['parent'])
        
        # 记录用户活动
        from apps.authentication.models import UserActivityLog
        UserActivityLog.objects.create(
            user=request.user,
            action='move_category',
            object_type='category',
            object_id=category.id,
            object_repr=category.name[:100],
            details={"ip_address": request.META.get('REMOTE_ADDR'), "parent_id": parent_id},
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("移动分类成功", category_id=category.id, parent_id=parent_id)
        
        serializer = self.get_serializer(category)
        return Response(serializer.data)
    
    def _is_child_category(self, potential_child, potential_parent):
        """检查potential_child是否是potential_parent的子分类"""
        if potential_child.parent is None:
            return False
        if potential_child.parent.id == potential_parent.id:
            return True
        return self._is_child_category(potential_child.parent, potential_parent)


class QuestionCategoryViewSet(viewsets.ModelViewSet):
    """题目分类关联视图集"""
    serializer_class = QuestionCategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['question', 'category']
    queryset = QuestionCategory.objects.none()  # 添加一个空的queryset以满足路由器要求
    
    def get_queryset(self):
        """获取当前用户的题目分类关联列表"""
        user = self.request.user
        
        # 获取用户的所有题目ID和分类ID
        from apps.questions.models import Question
        user_question_ids = Question.objects.filter(user=user).values_list('id', flat=True)
        user_category_ids = Category.objects.filter(user=user).values_list('id', flat=True)
        
        return QuestionCategory.objects.filter(
            question_id__in=user_question_ids,
            category_id__in=user_category_ids
        )
    
    def perform_create(self, serializer):
        """创建题目分类关联时检查权限"""
        question = serializer.validated_data['question']
        category = serializer.validated_data['category']
        
        # 检查权限
        if question.user != self.request.user or category.user != self.request.user:
            return Response(
                {'error': '无权限关联此题目和分类'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer.save()
        
        # 记录用户活动
        from apps.authentication.models import UserActivityLog
        UserActivityLog.objects.create(
            user=self.request.user,
            action='add_question_category',
            object_type='question_category',
            object_repr=f"将题目{question.id}添加到分类{category.id}",
            details={"ip_address": self.request.META.get('REMOTE_ADDR')},
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("添加题目分类关联成功", question_id=question.id, category_id=category.id)
    
    def perform_destroy(self, instance):
        """删除题目分类关联时记录活动"""
        question_id = instance.question.id
        category_id = instance.category.id
        
        # 记录用户活动
        from apps.authentication.models import UserActivityLog
        UserActivityLog.objects.create(
            user=self.request.user,
            action='remove_question_category',
            object_type='question_category',
            object_repr=f"从分类{category_id}移除题目{question_id}",
            details={"ip_address": self.request.META.get('REMOTE_ADDR')},
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("删除题目分类关联成功", question_id=question_id, category_id=category_id)
        
        super().perform_destroy(instance)
    
    @extend_schema(
        summary="批量添加题目到分类",
        description="将多个题目添加到指定分类",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'category_id': {'type': 'integer'},
                    'question_ids': {'type': 'array', 'items': {'type': 'integer'}}
                },
                'required': ['category_id', 'question_ids']
            }
        },
        responses={201: {'type': 'object'}}
    )
    @action(detail=False, methods=['post'])
    def batch_add(self, request):
        """批量添加题目到分类"""
        category_id = request.data.get('category_id')
        question_ids = request.data.get('question_ids', [])
        
        if not category_id or not question_ids:
            return Response(
                {'error': '分类ID和题目ID列表不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查分类权限
        try:
            category = Category.objects.get(id=category_id, user=request.user)
        except Category.DoesNotExist:
            return Response(
                {'error': '分类不存在或无权限'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 检查题目权限
        from apps.questions.models import Question
        questions = Question.objects.filter(
            id__in=question_ids,
            user=request.user
        )
        
        if questions.count() != len(question_ids):
            return Response(
                {'error': '部分题目不存在或无权限'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 创建关联
        created_count = 0
        for question in questions:
            # 检查是否已存在关联
            if not QuestionCategory.objects.filter(question=question, category=category).exists():
                QuestionCategory.objects.create(question=question, category=category)
                created_count += 1
        
        # 记录用户活动
        from apps.authentication.models import UserActivityLog
        UserActivityLog.objects.create(
            user=request.user,
            action='batch_add_question_category',
            object_type='question_category',
            object_repr=f"批量添加{created_count}个题目到分类{category_id}",
            details={"ip_address": request.META.get('REMOTE_ADDR')},
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("批量添加题目到分类成功", count=created_count, category_id=category_id)
        
        return Response({
            'category_id': category_id,
            'question_count': len(question_ids),
            'created_count': created_count
        }, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        summary="批量移除题目分类",
        description="从指定分类中移除多个题目",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'category_id': {'type': 'integer'},
                    'question_ids': {'type': 'array', 'items': {'type': 'integer'}}
                },
                'required': ['category_id', 'question_ids']
            }
        },
        responses={200: {'type': 'object'}}
    )
    @action(detail=False, methods=['post'])
    def batch_remove(self, request):
        """批量移除题目分类"""
        category_id = request.data.get('category_id')
        question_ids = request.data.get('question_ids', [])
        
        if not category_id or not question_ids:
            return Response(
                {'error': '分类ID和题目ID列表不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查分类权限
        try:
            category = Category.objects.get(id=category_id, user=request.user)
        except Category.DoesNotExist:
            return Response(
                {'error': '分类不存在或无权限'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 删除关联
        deleted_count, _ = QuestionCategory.objects.filter(
            category=category,
            question_id__in=question_ids
        ).delete()
        
        # 记录用户活动
        from apps.authentication.models import UserActivityLog
        UserActivityLog.objects.create(
            user=request.user,
            action='batch_remove_question_category',
            object_type='question_category',
            object_repr=f"从分类{category_id}移除{deleted_count}个题目",
            details={"ip_address": request.META.get('REMOTE_ADDR')},
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("批量移除题目分类成功", count=deleted_count, category_id=category_id)
        
        return Response({
            'category_id': category_id,
            'question_count': len(question_ids),
            'deleted_count': deleted_count
        })