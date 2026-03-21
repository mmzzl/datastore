from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet, QuestionCategoryViewSet
)

app_name = 'categories'

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'question-categories', QuestionCategoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]