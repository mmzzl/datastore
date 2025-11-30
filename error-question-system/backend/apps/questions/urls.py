from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'subjects', views.SubjectViewSet)
router.register(r'knowledge-points', views.KnowledgePointViewSet)
router.register(r'questions', views.QuestionViewSet)
router.register(r'tags', views.QuestionTagViewSet)

app_name = 'questions'

urlpatterns = [
    path('', include(router.urls)),
    path('upload/', views.upload_file, name='upload-file'),
    path('stats/user_stats/', views.user_stats, name='user-stats'),
]