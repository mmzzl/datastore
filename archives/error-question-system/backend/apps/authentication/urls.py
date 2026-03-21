from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    register, login_view, logout_view, profile, update_profile,
    change_password, login_history, activity_logs
)

app_name = 'authentication'

router = DefaultRouter()
# 认证模块没有需要注册的视图集

urlpatterns = [
    # JWT认证
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # 用户注册和登录
    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    
    # 用户资料
    path('profile/', profile, name='profile'),
    path('profile/update/', update_profile, name='update_profile'),
    path('change-password/', change_password, name='change_password'),
    
    # 用户活动
    path('login-history/', login_history, name='login_history'),
    path('activity-logs/', activity_logs, name='activity_logs'),
]