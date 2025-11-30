from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AnswerViewSet, AnswerCommentViewSet

app_name = 'answers'

router = DefaultRouter()
router.register(r'answers', AnswerViewSet, basename='answer')
router.register(r'comments', AnswerCommentViewSet, basename='answer-comment')

urlpatterns = [
    path('', include(router.urls)),
]