from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SubjectViewSet, KnowledgePointViewSet, QuestionViewSet, QuestionTagViewSet
)

router = DefaultRouter()
router.register(r'subjects', SubjectViewSet)
router.register(r'knowledge-points', KnowledgePointViewSet)
router.register(r'questions', QuestionViewSet)
router.register(r'tags', QuestionTagViewSet)

urlpatterns = [
    path('', include(router.urls)),
]