from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
import structlog

from .models import UserProfile, UserLoginLog, UserActivityLog
from .serializers import (
    UserRegistrationSerializer, UserProfileSerializer, UserProfileUpdateSerializer,
    PasswordChangeSerializer, UserLoginLogSerializer, UserActivityLogSerializer
)

logger = structlog.get_logger(__name__)


@extend_schema(
    summary="用户注册",
    description="创建新用户账户",
    request=UserRegistrationSerializer,
    responses={201: UserProfileSerializer}
)
@api_view(['POST'])
@permission_classes([])
def register(request):
    """用户注册"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        try:
            user = serializer.save()
            
            # 记录用户活动
            UserActivityLog.objects.create(
                user=user,
                action='register',
                resource_type='user',
                resource_id=user.id,
                description='用户注册',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            logger.info("用户注册成功", user_id=user.id, username=user.username)
            
            # 返回用户信息
            user_serializer = UserProfileSerializer(user)
            return Response(user_serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error("用户注册失败", error=str(e))
            return Response(
                {'error': '注册失败，请稍后再试'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    logger.warning("用户注册验证失败", errors=serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="用户登录",
    description="用户登录获取认证令牌",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string'},
                'password': {'type': 'string'}
            },
            'required': ['username', 'password']
        }
    },
    responses={200: UserProfileSerializer}
)
@api_view(['POST'])
@permission_classes([])
def login_view(request):
    """用户登录"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': '用户名和密码不能为空'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    if user:
        login(request, user)
        
        # 更新最后登录时间
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # 记录登录日志
        UserLoginLog.objects.create(
            user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # 记录用户活动
        UserActivityLog.objects.create(
            user=user,
            action='login',
            resource_type='user',
            resource_id=user.id,
            description='用户登录',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("用户登录成功", user_id=user.id, username=user.username)
        
        # 返回用户信息
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)
    else:
        logger.warning("用户登录失败", username=username)
        return Response(
            {'error': '用户名或密码错误'},
            status=status.HTTP_401_UNAUTHORIZED
        )


@extend_schema(
    summary="用户登出",
    description="用户登出，清除会话",
    responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """用户登出"""
    user = request.user
    
    # 记录用户活动
    UserActivityLog.objects.create(
        user=user,
        action='logout',
        resource_type='user',
        resource_id=user.id,
        description='用户登出',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    logout(request)
    logger.info("用户登出成功", user_id=user.id, username=user.username)
    
    return Response({'message': '登出成功'})


@extend_schema(
    summary="获取用户信息",
    description="获取当前登录用户的详细信息",
    responses={200: UserProfileSerializer}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """获取用户信息"""
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


@extend_schema(
    summary="更新用户信息",
    description="更新当前登录用户的个人信息",
    request=UserProfileUpdateSerializer,
    responses={200: UserProfileSerializer}
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """更新用户信息"""
    user = request.user
    serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        
        # 记录用户活动
        UserActivityLog.objects.create(
            user=user,
            action='update_profile',
            resource_type='user',
            resource_id=user.id,
            description='更新个人信息',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("用户信息更新成功", user_id=user.id)
        
        # 返回更新后的用户信息
        response_serializer = UserProfileSerializer(user)
        return Response(response_serializer.data)
    
    logger.warning("用户信息更新验证失败", user_id=user.id, errors=serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="修改密码",
    description="修改当前登录用户的密码",
    request=PasswordChangeSerializer,
    responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """修改密码"""
    serializer = PasswordChangeSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        serializer.save()
        
        # 记录用户活动
        UserActivityLog.objects.create(
            user=request.user,
            action='change_password',
            resource_type='user',
            resource_id=request.user.id,
            description='修改密码',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        logger.info("用户密码修改成功", user_id=request.user.id)
        
        return Response({'message': '密码修改成功'})
    
    logger.warning("用户密码修改验证失败", user_id=request.user.id, errors=serializer.errors)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary="获取登录历史",
    description="获取当前用户的登录历史记录",
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
    responses={200: UserLoginLogSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def login_history(request):
    """获取登录历史"""
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    
    logs = UserLoginLog.objects.filter(user=request.user).order_by('-login_time')
    
    # 简单分页
    start = (page - 1) * page_size
    end = start + page_size
    page_logs = logs[start:end]
    
    serializer = UserLoginLogSerializer(page_logs, many=True)
    
    return Response({
        'count': logs.count(),
        'results': serializer.data,
        'page': page,
        'page_size': page_size,
        'total_pages': (logs.count() + page_size - 1) // page_size
    })


@extend_schema(
    summary="获取活动日志",
    description="获取当前用户的活动日志记录",
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
    responses={200: UserActivityLogSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def activity_logs(request):
    """获取活动日志"""
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    
    logs = UserActivityLog.objects.filter(user=request.user).order_by('-created_at')
    
    # 简单分页
    start = (page - 1) * page_size
    end = start + page_size
    page_logs = logs[start:end]
    
    serializer = UserActivityLogSerializer(page_logs, many=True)
    
    return Response({
        'count': logs.count(),
        'results': serializer.data,
        'page': page,
        'page_size': page_size,
        'total_pages': (logs.count() + page_size - 1) // page_size
    })