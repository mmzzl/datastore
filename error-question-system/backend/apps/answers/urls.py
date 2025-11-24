from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    AnswerViewSet, AnswerCommentViewSet
)

router = DefaultRouter()
router.register(r'answers', AnswerViewSet)
router.register(r'comments', AnswerCommentViewSet)

urlpatterns = [
    path('', include(router.urls)),
]