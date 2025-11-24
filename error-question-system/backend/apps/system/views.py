from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import structlog

from .models import SystemConfig, SystemNotification, UserNotification, Feedback, OperationLog
from .serializers import (
    SystemConfigSerializer, SystemNotificationSerializer, UserNotificationSerializer,
    FeedbackSerializer, FeedbackCreateSerializer, OperationLogSerializer
)

logger = structlog.get_logger(__name__)


class SystemConfigViewSet(viewsets.ModelViewSet):
    """系统配置视图集"""
    queryset = SystemConfig.objects.all()
    serializer_class = SystemConfigSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['key', 'is_active']
    search_fields = ['key', 'description']
    ordering_fields = ['key', 'created_at', 'updated_at']
    ordering = ['key']
    
    @extend_schema(
        summary="获取配置值",
        description="根据键名获取配置值",
        parameters=[
            OpenApiParameter(
                name='key',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.PATH,
                description='配置键名'
            )
        ],
        responses={200: {'type': 'object', 'properties': {'value': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['get'])
    def value(self, request, pk=None):
        """获取配置值"""
        config = self.get_object()
        return Response({'value': config.value})
    
    @extend_schema(
        summary="更新配置值",
        description="更新配置值",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'value': {'type': 'string'}
                }
            }
        },
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['patch'])
    def update_value(self, request, pk=None):
        """更新配置值"""
        config = self.get_object()
        value = request.data.get('value')
        
        if value is None:
            return Response({'error': '缺少value参数'}, status=status.HTTP_400_BAD_REQUEST)
        
        config.value = value
        config.save(update_fields=['value', 'updated_at'])
        
        # 记录操作日志
        OperationLog.objects.create(
            user=request.user,
            action='update_config',
            resource_type='system_config',
            resource_id=config.id,
            description=f"更新系统配置: {config.key} = {value}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("更新系统配置", key=config.key, value=value, user_id=request.user.id)
        
        return Response({'message': '配置更新成功'})


class SystemNotificationViewSet(viewsets.ModelViewSet):
    """系统通知视图集"""
    queryset = SystemNotification.objects.all()
    serializer_class = SystemNotificationSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'is_active']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at', 'start_time', 'end_time']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        """创建系统通知"""
        notification = serializer.save()
        
        # 记录操作日志
        OperationLog.objects.create(
            user=self.request.user,
            action='create_notification',
            resource_type='system_notification',
            resource_id=notification.id,
            description=f"创建系统通知: {notification.title}",
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("创建系统通知", title=notification.title, user_id=self.request.user.id)
    
    def perform_update(self, serializer):
        """更新系统通知"""
        old_notification = self.get_object()
        notification = serializer.save()
        
        # 记录操作日志
        OperationLog.objects.create(
            user=self.request.user,
            action='update_notification',
            resource_type='system_notification',
            resource_id=notification.id,
            description=f"更新系统通知: {notification.title}",
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("更新系统通知", title=notification.title, user_id=self.request.user.id)
    
    @extend_schema(
        summary="发布通知",
        description="发布系统通知给所有用户",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='通知ID'
            )
        ],
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        """发布通知"""
        notification = self.get_object()
        
        if not notification.is_active:
            return Response({'error': '通知未激活'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取所有用户
        from apps.authentication.models import User
        users = User.objects.filter(is_active=True)
        
        # 为所有用户创建用户通知
        user_notifications = []
        for user in users:
            user_notifications.append(UserNotification(
                user=user,
                system_notification=notification,
                title=notification.title,
                content=notification.content,
                type=notification.type
            ))
        
        UserNotification.objects.bulk_create(user_notifications)
        
        # 更新通知状态
        notification.is_published = True
        notification.published_at = timezone.now()
        notification.save(update_fields=['is_published', 'published_at'])
        
        # 记录操作日志
        OperationLog.objects.create(
            user=request.user,
            action='publish_notification',
            resource_type='system_notification',
            resource_id=notification.id,
            description=f"发布系统通知: {notification.title}，发送给{users.count()}个用户",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("发布系统通知", title=notification.title, user_count=users.count(), user_id=request.user.id)
        
        return Response({'message': f'通知已发布给{users.count()}个用户'})


class UserNotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """用户通知视图集"""
    serializer_class = UserNotificationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'is_read']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    queryset = UserNotification.objects.all()
    
    def get_queryset(self):
        """获取当前用户的通知列表"""
        return UserNotification.objects.filter(user=self.request.user)
    
    @extend_schema(
        summary="标记通知为已读",
        description="标记通知为已读",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='通知ID'
            )
        ],
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """标记通知为已读"""
        notification = self.get_object()
        
        if notification.is_read:
            return Response({'message': '通知已标记为已读'})
        
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=['is_read', 'read_at'])
        
        # 记录用户活动
        from apps.system.models import UserActivityLog
        UserActivityLog.objects.create(
            user=request.user,
            action='read_notification',
            resource_type='user_notification',
            resource_id=notification.id,
            description=f"阅读通知: {notification.title}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("标记通知为已读", notification_id=notification.id, user_id=request.user.id)
        
        return Response({'message': '通知已标记为已读'})
    
    @extend_schema(
        summary="标记所有通知为已读",
        description="标记当前用户的所有通知为已读",
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """标记所有通知为已读"""
        count = UserNotification.objects.filter(
            user=request.user,
            is_read=False
        ).update(
            is_read=True,
            read_at=timezone.now()
        )
        
        # 记录用户活动
        from apps.system.models import UserActivityLog
        UserActivityLog.objects.create(
            user=request.user,
            action='read_all_notifications',
            resource_type='user_notification',
            description=f"标记{count}条通知为已读",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("标记所有通知为已读", count=count, user_id=request.user.id)
        
        return Response({'message': f'已标记{count}条通知为已读'})
    
    @extend_schema(
        summary="删除通知",
        description="删除通知",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='通知ID'
            )
        ],
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['delete'])
    def delete_notification(self, request, pk=None):
        """删除通知"""
        notification = self.get_object()
        title = notification.title
        notification.delete()
        
        # 记录用户活动
        from apps.system.models import UserActivityLog
        UserActivityLog.objects.create(
            user=request.user,
            action='delete_notification',
            resource_type='user_notification',
            description=f"删除通知: {title}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("删除通知", title=title, user_id=request.user.id)
        
        return Response({'message': '通知已删除'})


class FeedbackViewSet(viewsets.ModelViewSet):
    """用户反馈视图集"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'status']
    search_fields = ['title', 'content']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    queryset = Feedback.objects.all()
    
    def get_queryset(self):
        """根据用户角色获取反馈列表"""
        user = self.request.user
        
        # 管理员可以看到所有反馈
        if user.is_staff:
            return Feedback.objects.all()
        
        # 普通用户只能看到自己的反馈
        return Feedback.objects.filter(user=user)
    
    def get_serializer_class(self):
        """根据操作类型返回不同的序列化器"""
        if self.action == 'create':
            return FeedbackCreateSerializer
        return FeedbackSerializer
    
    def perform_create(self, serializer):
        """创建反馈"""
        feedback = serializer.save(user=self.request.user)
        
        # 记录用户活动
        from apps.system.models import UserActivityLog
        UserActivityLog.objects.create(
            user=self.request.user,
            action='create_feedback',
            resource_type='feedback',
            resource_id=feedback.id,
            description=f"提交反馈: {feedback.title}",
            ip_address=self.request.META.get('REMOTE_ADDR'),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("提交反馈", title=feedback.title, user_id=self.request.user.id)
    
    @extend_schema(
        summary="回复反馈",
        description="管理员回复用户反馈",
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'reply': {'type': 'string'}
                }
            }
        },
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        """回复反馈"""
        if not request.user.is_staff:
            return Response({'error': '权限不足'}, status=status.HTTP_403_FORBIDDEN)
        
        feedback = self.get_object()
        reply = request.data.get('reply', '').strip()
        
        if not reply:
            return Response({'error': '回复内容不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        feedback.reply = reply
        feedback.replied_by = request.user
        feedback.replied_at = timezone.now()
        feedback.status = 'replied'
        feedback.save(update_fields=['reply', 'replied_by', 'replied_at', 'status'])
        
        # 记录操作日志
        OperationLog.objects.create(
            user=request.user,
            action='reply_feedback',
            resource_type='feedback',
            resource_id=feedback.id,
            description=f"回复反馈: {feedback.title}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("回复反馈", title=feedback.title, user_id=request.user.id)
        
        return Response({'message': '回复成功'})
    
    @extend_schema(
        summary="处理反馈",
        description="管理员标记反馈为已处理",
        parameters=[
            OpenApiParameter(
                name='id',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.PATH,
                description='反馈ID'
            )
        ],
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """处理反馈"""
        if not request.user.is_staff:
            return Response({'error': '权限不足'}, status=status.HTTP_403_FORBIDDEN)
        
        feedback = self.get_object()
        
        feedback.status = 'resolved'
        feedback.resolved_by = request.user
        feedback.resolved_at = timezone.now()
        feedback.save(update_fields=['status', 'resolved_by', 'resolved_at'])
        
        # 记录操作日志
        OperationLog.objects.create(
            user=request.user,
            action='resolve_feedback',
            resource_type='feedback',
            resource_id=feedback.id,
            description=f"处理反馈: {feedback.title}",
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("处理反馈", title=feedback.title, user_id=request.user.id)
        
        return Response({'message': '反馈已标记为已处理'})


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    """操作日志视图集"""
    serializer_class = OperationLogSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'action', 'resource_type']
    search_fields = ['description', 'ip_address']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    queryset = OperationLog.objects.all()
    
    def get_queryset(self):
        """获取操作日志列表"""
        queryset = OperationLog.objects.all()
        
        # 按日期范围过滤
        date_from = self.request.query_params.get('date_from')
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        date_to = self.request.query_params.get('date_to')
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        return queryset
    
    @extend_schema(
        summary="统计操作日志",
        description="统计操作日志数据",
        parameters=[
            OpenApiParameter(
                name='days',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='统计天数',
                default=7
            )
        ],
        responses={200: {'type': 'object'}}
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """统计操作日志"""
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timezone.timedelta(days=days)
        
        # 按操作类型统计
        action_stats = OperationLog.objects.filter(
            created_at__gte=start_date
        ).values('action').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # 按用户统计
        user_stats = OperationLog.objects.filter(
            created_at__gte=start_date
        ).values('user__username').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # 按日期统计
        date_stats = []
        for i in range(days):
            date = (timezone.now() - timezone.timedelta(days=i)).date()
            count = OperationLog.objects.filter(
                created_at__date=date
            ).count()
            date_stats.append({
                'date': date.isoformat(),
                'count': count
            })
        
        return Response({
            'action_stats': list(action_stats),
            'user_stats': list(user_stats),
            'date_stats': date_stats
        })