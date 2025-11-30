from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SystemConfigViewSet, SystemNotificationViewSet, UserNotificationViewSet,
    FeedbackViewSet, OperationLogViewSet
)

app_name = 'system'

router = DefaultRouter()
router.register(r'configs', SystemConfigViewSet)
router.register(r'system-notifications', SystemNotificationViewSet)
router.register(r'user-notifications', UserNotificationViewSet)
router.register(r'feedback', FeedbackViewSet)
router.register(r'operation-logs', OperationLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
]