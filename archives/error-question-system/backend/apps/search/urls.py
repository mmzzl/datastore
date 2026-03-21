from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SearchHistoryViewSet, SearchSuggestionViewSet, PopularSearchViewSet, SearchViewSet
)

app_name = 'search'

router = DefaultRouter()
router.register(r'history', SearchHistoryViewSet)
router.register(r'suggestions', SearchSuggestionViewSet)
router.register(r'popular', PopularSearchViewSet)
router.register(r'search', SearchViewSet, basename='search')

urlpatterns = [
    path('', include(router.urls)),
    # 添加额外路由以匹配测试中使用的'search-list'、'search-history'和'search-suggestions'
    path('search-list/', SearchViewSet.as_view({'get': 'questions'}), name='search-list'),
    path('search-history/', SearchViewSet.as_view({'post': 'questions'}), name='search-history'),
    path('search-suggestions/', SearchSuggestionViewSet.as_view({'get': 'suggest'}), name='search-suggestions'),
]