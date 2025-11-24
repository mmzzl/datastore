import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta

from apps.search.models import SearchHistory, SearchSuggestion, PopularSearch
from apps.search.views import SearchHistoryViewSet, SearchSuggestionViewSet, PopularSearchViewSet, SearchViewSet
from apps.questions.models import Question, Subject, KnowledgePoint

User = get_user_model()


class SearchHistoryModelTests(TestCase):
    """搜索历史模型测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.search_history = SearchHistory.objects.create(
            user=self.user,
            query='一元一次方程',
            results_count=10,
            search_time=0.5
        )
    
    def test_search_history_creation(self):
        """测试搜索历史创建"""
        self.assertEqual(self.search_history.user, self.user)
        self.assertEqual(self.search_history.query, '一元一次方程')
        self.assertEqual(self.search_history.results_count, 10)
        self.assertEqual(self.search_history.search_time, 0.5)
    
    def test_search_history_str_representation(self):
        """测试搜索历史字符串表示"""
        expected_str = f"{self.user.username} - 一元一次方程"
        self.assertEqual(str(self.search_history), expected_str)
    
    def test_search_history_ordering(self):
        """测试搜索历史排序"""
        # 创建另一个搜索历史
        search_history2 = SearchHistory.objects.create(
            user=self.user,
            query='二元一次方程',
            results_count=5,
            search_time=0.3
        )
        
        # 获取所有搜索历史，应该按创建时间倒序排列
        histories = SearchHistory.objects.all()
        self.assertEqual(histories[0], search_history2)
        self.assertEqual(histories[1], self.search_history)


class SearchSuggestionModelTests(TestCase):
    """搜索建议模型测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.search_suggestion = SearchSuggestion.objects.create(
            keyword='一元一次方程求解',
            frequency=10,
            is_active=True
        )
    
    def test_search_suggestion_creation(self):
        """测试搜索建议创建"""
        self.assertEqual(self.search_suggestion.query, '一元一次方程')
        self.assertEqual(self.search_suggestion.suggestion, '一元一次方程求解')
        self.assertEqual(self.search_suggestion.frequency, 10)
        self.assertTrue(self.search_suggestion.is_active)
    
    def test_search_suggestion_str_representation(self):
        """测试搜索建议字符串表示"""
        expected_str = f"一元一次方程 - 一元一次方程求解"
        self.assertEqual(str(self.search_suggestion), expected_str)
    
    def test_search_suggestion_ordering(self):
        """测试搜索建议排序"""
        # 创建另一个搜索建议
        search_suggestion2 = SearchSuggestion.objects.create(
            query='二元一次方程',
            suggestion='二元一次方程求解',
            frequency=5,
            is_active=True
        )
        
        # 获取所有搜索建议，应该按频率降序排列
        suggestions = SearchSuggestion.objects.all()
        self.assertEqual(suggestions[0], self.search_suggestion)
        self.assertEqual(suggestions[1], search_suggestion2)


class PopularSearchModelTests(TestCase):
    """热门搜索模型测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.popular_search = PopularSearch.objects.create(
            query='一元一次方程',
            search_count=100,
            is_active=True
        )
    
    def test_popular_search_creation(self):
        """测试热门搜索创建"""
        self.assertEqual(self.popular_search.query, '一元一次方程')
        self.assertEqual(self.popular_search.search_count, 100)
        self.assertTrue(self.popular_search.is_active)
    
    def test_popular_search_str_representation(self):
        """测试热门搜索字符串表示"""
        expected_str = f"一元一次方程 (100)"
        self.assertEqual(str(self.popular_search), expected_str)
    
    def test_popular_search_ordering(self):
        """测试热门搜索排序"""
        # 创建另一个热门搜索
        popular_search2 = PopularSearch.objects.create(
            query='二元一次方程',
            search_count=50,
            is_active=True
        )
        
        # 获取所有热门搜索，应该按搜索次数降序排列
        popular_searches = PopularSearch.objects.all()
        self.assertEqual(popular_searches[0], self.popular_search)
        self.assertEqual(popular_searches[1], popular_search2)


class SearchHistoryViewTests(APITestCase):
    """搜索历史视图测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.search_history = SearchHistory.objects.create(
            user=self.user,
            query='一元一次方程',
            results_count=10,
            search_time=0.5
        )
        
        # 认证用户
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_search_history_list(self):
        """测试获取搜索历史列表"""
        url = reverse('search:searchhistory-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['query'], '一元一次方程')
        self.assertEqual(response.data['results'][0]['results_count'], 10)
        self.assertEqual(response.data['results'][0]['search_time'], 0.5)
    
    def test_get_search_history_list_filtered_by_query(self):
        """测试按查询内容过滤搜索历史列表"""
        # 创建另一个搜索历史
        SearchHistory.objects.create(
            user=self.user,
            query='二元一次方程',
            results_count=5,
            search_time=0.3
        )
        
        url = reverse('search:searchhistory-list')
        response = self.client.get(url, {'query': '一元一次方程'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['query'], '一元一次方程')
    
    def test_get_search_history_detail(self):
        """测试获取搜索历史详情"""
        url = reverse('search:searchhistory-detail', kwargs={'pk': self.search_history.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['query'], '一元一次方程')
        self.assertEqual(response.data['results_count'], 10)
        self.assertEqual(response.data['search_time'], 0.5)
    
    def test_get_search_history_detail_not_found(self):
        """测试获取不存在的搜索历史详情"""
        url = reverse('search:searchhistory-detail', kwargs={'pk': 999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_delete_search_history(self):
        """测试删除搜索历史"""
        url = reverse('search:searchhistory-detail', kwargs={'pk': self.search_history.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SearchHistory.objects.count(), 0)
    
    def test_clear_search_history(self):
        """测试清空搜索历史"""
        # 创建另一个搜索历史
        SearchHistory.objects.create(
            user=self.user,
            query='二元一次方程',
            results_count=5,
            search_time=0.3
        )
        
        url = reverse('search:searchhistory-clear')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(SearchHistory.objects.count(), 0)
    
    def test_get_search_history_without_authentication(self):
        """测试未认证获取搜索历史"""
        self.client.credentials()  # 清除认证
        url = reverse('search:searchhistory-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class SearchSuggestionViewTests(APITestCase):
    """搜索建议视图测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.search_suggestion = SearchSuggestion.objects.create(
            keyword='一元一次方程求解',
            frequency=10,
            is_active=True
        )
        
        # 认证用户
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_search_suggestion_list(self):
        """测试获取搜索建议列表"""
        url = reverse('search:searchsuggestion-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['query'], '一元一次方程')
        self.assertEqual(response.data['results'][0]['suggestion'], '一元一次方程求解')
        self.assertEqual(response.data['results'][0]['frequency'], 10)
        self.assertTrue(response.data['results'][0]['is_active'])
    
    def test_get_search_suggestion_list_filtered_by_query(self):
        """测试按查询内容过滤搜索建议列表"""
        # 创建另一个搜索建议
        SearchSuggestion.objects.create(
            keyword='二元一次方程求解',
            frequency=5,
            is_active=True
        )
        
        url = reverse('search:searchsuggestion-list')
        response = self.client.get(url, {'query': '一元一次方程'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['query'], '一元一次方程')
    
    def test_get_search_suggestion_list_filtered_by_is_active(self):
        """测试按激活状态过滤搜索建议列表"""
        # 创建一个非激活的搜索建议
        SearchSuggestion.objects.create(
            keyword='非激活搜索建议',
            frequency=1,
            is_active=False
        )
        
        url = reverse('search:searchsuggestion-list')
        response = self.client.get(url, {'is_active': True})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['query'], '一元一次方程')
    
    def test_get_search_suggestion_detail(self):
        """测试获取搜索建议详情"""
        url = reverse('search:searchsuggestion-detail', kwargs={'pk': self.search_suggestion.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['query'], '一元一次方程')
        self.assertEqual(response.data['suggestion'], '一元一次方程求解')
        self.assertEqual(response.data['frequency'], 10)
        self.assertTrue(response.data['is_active'])
    
    def test_get_search_suggestion_detail_not_found(self):
        """测试获取不存在的搜索建议详情"""
        url = reverse('search:searchsuggestion-detail', kwargs={'pk': 999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_search_suggestion(self):
        """测试创建搜索建议"""
        url = reverse('search:searchsuggestion-list')
        data = {
            'query': '二元一次方程',
            'suggestion': '二元一次方程求解',
            'frequency': 5,
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(SearchSuggestion.objects.count(), 2)
        
        new_suggestion = SearchSuggestion.objects.latest('created_at')
        self.assertEqual(new_suggestion.query, '二元一次方程')
        self.assertEqual(new_suggestion.suggestion, '二元一次方程求解')
        self.assertEqual(new_suggestion.frequency, 5)
        self.assertTrue(new_suggestion.is_active)
    
    def test_update_search_suggestion(self):
        """测试更新搜索建议"""
        url = reverse('search:searchsuggestion-detail', kwargs={'pk': self.search_suggestion.id})
        data = {
            'query': '一元一次方程（更新）',
            'suggestion': '一元一次方程求解（更新）',
            'frequency': 15,
            'is_active': False
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.search_suggestion.refresh_from_db()
        self.assertEqual(self.search_suggestion.query, '一元一次方程（更新）')
        self.assertEqual(self.search_suggestion.suggestion, '一元一次方程求解（更新）')
        self.assertEqual(self.search_suggestion.frequency, 15)
        self.assertFalse(self.search_suggestion.is_active)
    
    def test_delete_search_suggestion(self):
        """测试删除搜索建议"""
        url = reverse('search:searchsuggestion-detail', kwargs={'pk': self.search_suggestion.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(SearchSuggestion.objects.count(), 0)
    
    def test_get_search_suggestions_by_query(self):
        """测试根据查询内容获取搜索建议"""
        # 创建另一个搜索建议
        SearchSuggestion.objects.create(
            keyword='一元一次方程应用',
            frequency=8,
            is_active=True
        )
        
        url = reverse('search:searchsuggestion-by-query')
        response = self.client.get(url, {'query': '一元一次方程'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        suggestions = [suggestion['suggestion'] for suggestion in response.data]
        self.assertIn('一元一次方程求解', suggestions)
        self.assertIn('一元一次方程应用', suggestions)
    
    def test_increment_search_suggestion_frequency(self):
        """测试增加搜索建议频率"""
        url = reverse('search:searchsuggestion-increment-frequency', kwargs={'pk': self.search_suggestion.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.search_suggestion.refresh_from_db()
        self.assertEqual(self.search_suggestion.frequency, 11)


class PopularSearchViewTests(APITestCase):
    """热门搜索视图测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.popular_search = PopularSearch.objects.create(
            query='一元一次方程',
            search_count=100,
            is_active=True
        )
        
        # 认证用户
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_popular_search_list(self):
        """测试获取热门搜索列表"""
        url = reverse('search:popularsearch-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['query'], '一元一次方程')
        self.assertEqual(response.data['results'][0]['search_count'], 100)
        self.assertTrue(response.data['results'][0]['is_active'])
    
    def test_get_popular_search_list_filtered_by_is_active(self):
        """测试按激活状态过滤热门搜索列表"""
        # 创建一个非激活的热门搜索
        PopularSearch.objects.create(
            query='非激活搜索',
            search_count=1,
            is_active=False
        )
        
        url = reverse('search:popularsearch-list')
        response = self.client.get(url, {'is_active': True})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['query'], '一元一次方程')
    
    def test_get_popular_search_detail(self):
        """测试获取热门搜索详情"""
        url = reverse('search:popularsearch-detail', kwargs={'pk': self.popular_search.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['query'], '一元一次方程')
        self.assertEqual(response.data['search_count'], 100)
        self.assertTrue(response.data['is_active'])
    
    def test_get_popular_search_detail_not_found(self):
        """测试获取不存在的热门搜索详情"""
        url = reverse('search:popularsearch-detail', kwargs={'pk': 999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_popular_search(self):
        """测试创建热门搜索"""
        url = reverse('search:popularsearch-list')
        data = {
            'query': '二元一次方程',
            'search_count': 50,
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(PopularSearch.objects.count(), 2)
        
        new_popular_search = PopularSearch.objects.latest('created_at')
        self.assertEqual(new_popular_search.query, '二元一次方程')
        self.assertEqual(new_popular_search.search_count, 50)
        self.assertTrue(new_popular_search.is_active)
    
    def test_update_popular_search(self):
        """测试更新热门搜索"""
        url = reverse('search:popularsearch-detail', kwargs={'pk': self.popular_search.id})
        data = {
            'query': '一元一次方程（更新）',
            'search_count': 150,
            'is_active': False
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.popular_search.refresh_from_db()
        self.assertEqual(self.popular_search.query, '一元一次方程（更新）')
        self.assertEqual(self.popular_search.search_count, 150)
        self.assertFalse(self.popular_search.is_active)
    
    def test_delete_popular_search(self):
        """测试删除热门搜索"""
        url = reverse('search:popularsearch-detail', kwargs={'pk': self.popular_search.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PopularSearch.objects.count(), 0)
    
    def test_increment_popular_search_count(self):
        """测试增加热门搜索次数"""
        url = reverse('search:popularsearch-increment-count', kwargs={'pk': self.popular_search.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.popular_search.refresh_from_db()
        self.assertEqual(self.popular_search.search_count, 101)
    
    def test_get_top_popular_searches(self):
        """测试获取前N个热门搜索"""
        # 创建更多热门搜索
        PopularSearch.objects.create(
            query='二元一次方程',
            search_count=80,
            is_active=True
        )
        PopularSearch.objects.create(
            query='几何',
            search_count=60,
            is_active=True
        )
        PopularSearch.objects.create(
            query='非激活搜索',
            search_count=200,
            is_active=False
        )
        
        url = reverse('search:popularsearch-top')
        response = self.client.get(url, {'limit': 2})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # 验证按搜索次数降序排列
        self.assertEqual(response.data[0]['query'], '一元一次方程')
        self.assertEqual(response.data[0]['search_count'], 100)
        self.assertEqual(response.data[1]['query'], '二元一次方程')
        self.assertEqual(response.data[1]['search_count'], 80)


class SearchViewTests(APITestCase):
    """搜索视图测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.subject = Subject.objects.create(
            name='数学',
            description='数学学科',
            sort_order=1,
            is_active=True
        )
        self.knowledge_point = KnowledgePoint.objects.create(
            subject=self.subject,
            name='代数',
            description='代数知识点',
            level=1,
            sort_order=1,
            is_active=True
        )
        self.question = Question.create_with_compatibility(
            user=self.user,
            subject=self.subject,
            title='一元一次方程求解',
            content='求解方程 2x + 5 = 15',
            answer='x = 5',
            solution='移项得 2x = 10，两边除以2得 x = 5',
            difficulty=2,
            question_type='选择题',
            source='教材',
            is_solved=False,
            is_marked=False
        )
        
        # 认证用户
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    @patch('apps.search.views.search_questions')
    def test_search_questions(self, mock_search_questions):
        """测试搜索题目"""
        mock_search_questions.return_value = {
            'results': [
                {
                    'id': self.question.id,
                    'title': '一元一次方程求解',
                    'content': '求解方程 2x + 5 = 15',
                    'answer': 'x = 5',
                    'solution': '移项得 2x = 10，两边除以2得 x = 5',
                    'difficulty': 2,
                    'question_type': '选择题',
                    'source': '教材',
                    'is_solved': False,
                    'is_marked': False,
                    'user': self.user.id,
                    'subject': self.subject.id,
                    'knowledge_points': [self.knowledge_point.id],
                    'created_at': self.question.created_at.isoformat(),
                    'updated_at': self.question.updated_at.isoformat()
                }
            ],
            'count': 1,
            'next': None,
            'previous': None
        }
        
        url = reverse('search:search-list')
        response = self.client.get(url, {'q': '一元一次方程'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], '一元一次方程求解')
        self.assertEqual(response.data['count'], 1)
        
        # 验证搜索历史被记录
        self.assertTrue(SearchHistory.objects.filter(
            user=self.user,
            query='一元一次方程',
            results_count=1
        ).exists())
        
        # 验证搜索函数被正确调用
        mock_search_questions.assert_called_once_with('一元一次方程', user=self.user)
    
    @patch('apps.search.views.search_questions')
    def test_search_questions_with_filters(self, mock_search_questions):
        """测试带过滤条件的题目搜索"""
        mock_search_questions.return_value = {
            'results': [
                {
                    'id': self.question.id,
                    'title': '一元一次方程求解',
                    'content': '求解方程 2x + 5 = 15',
                    'answer': 'x = 5',
                    'solution': '移项得 2x = 10，两边除以2得 x = 5',
                    'difficulty': 2,
                    'question_type': '选择题',
                    'source': '教材',
                    'is_solved': False,
                    'is_marked': False,
                    'user': self.user.id,
                    'subject': self.subject.id,
                    'knowledge_points': [self.knowledge_point.id],
                    'created_at': self.question.created_at.isoformat(),
                    'updated_at': self.question.updated_at.isoformat()
                }
            ],
            'count': 1,
            'next': None,
            'previous': None
        }
        
        url = reverse('search:search-list')
        response = self.client.get(url, {
            'q': '方程',
            'subject': self.subject.id,
            'difficulty': 2,
            'question_type': '选择题'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # 验证搜索函数被正确调用
        mock_search_questions.assert_called_once_with(
            '方程',
            user=self.user,
            subject=self.subject.id,
            difficulty=2,
            question_type='选择题'
        )
    
    @patch('apps.search.views.search_questions')
    def test_search_questions_empty_query(self, mock_search_questions):
        """测试空查询的题目搜索"""
        url = reverse('search:search-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # 验证搜索函数未被调用
        mock_search_questions.assert_not_called()
    
    @patch('apps.search.views.search_questions')
    def test_search_questions_with_pagination(self, mock_search_questions):
        """测试带分页的题目搜索"""
        mock_search_questions.return_value = {
            'results': [
                {
                    'id': self.question.id,
                    'title': '一元一次方程求解',
                    'content': '求解方程 2x + 5 = 15',
                    'answer': 'x = 5',
                    'solution': '移项得 2x = 10，两边除以2得 x = 5',
                    'difficulty': 2,
                    'question_type': '选择题',
                    'source': '教材',
                    'is_solved': False,
                    'is_marked': False,
                    'user': self.user.id,
                    'subject': self.subject.id,
                    'knowledge_points': [self.knowledge_point.id],
                    'created_at': self.question.created_at.isoformat(),
                    'updated_at': self.question.updated_at.isoformat()
                }
            ],
            'count': 1,
            'next': None,
            'previous': None
        }
        
        url = reverse('search:search-list')
        response = self.client.get(url, {
            'q': '一元一次方程',
            'page': 1,
            'page_size': 10
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        
        # 验证搜索函数被正确调用
        mock_search_questions.assert_called_once_with(
            '一元一次方程',
            user=self.user,
            page=1,
            page_size=10
        )
    
    @patch('apps.search.views.search_questions')
    def test_search_questions_with_error(self, mock_search_questions):
        """测试搜索题目时出错"""
        mock_search_questions.side_effect = Exception("搜索服务不可用")
        
        url = reverse('search:search-list')
        response = self.client.get(url, {'q': '一元一次方程'})
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('error', response.data)
        
        # 验证搜索历史未被记录
        self.assertFalse(SearchHistory.objects.filter(
            user=self.user,
            query='一元一次方程'
        ).exists())
    
    def test_get_search_suggestions(self):
        """测试获取搜索建议"""
        # 创建搜索建议
        SearchSuggestion.objects.create(
            keyword='一元一次方程求解',
            frequency=10,
            is_active=True
        )
        SearchSuggestion.objects.create(
            keyword='一元一次方程应用',
            frequency=8,
            is_active=True
        )
        SearchSuggestion.objects.create(
            keyword='二元一次方程求解',
            frequency=5,
            is_active=True
        )
        
        url = reverse('search:search-suggestions')
        response = self.client.get(url, {'q': '一元一次方程'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        suggestions = [suggestion['suggestion'] for suggestion in response.data]
        self.assertIn('一元一次方程求解', suggestions)
        self.assertIn('一元一次方程应用', suggestions)
        self.assertNotIn('二元一次方程求解', suggestions)
    
    def test_get_search_suggestions_empty_query(self):
        """测试空查询的搜索建议"""
        url = reverse('search:search-suggestions')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_get_popular_searches(self):
        """测试获取热门搜索"""
        # 创建热门搜索
        PopularSearch.objects.create(
            query='一元一次方程',
            search_count=100,
            is_active=True
        )
        PopularSearch.objects.create(
            query='二元一次方程',
            search_count=80,
            is_active=True
        )
        PopularSearch.objects.create(
            query='几何',
            search_count=60,
            is_active=True
        )
        PopularSearch.objects.create(
            query='非激活搜索',
            search_count=200,
            is_active=False
        )
        
        url = reverse('search:search-popular')
        response = self.client.get(url, {'limit': 5})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)
        
        # 验证按搜索次数降序排列
        self.assertEqual(response.data[0]['query'], '一元一次方程')
        self.assertEqual(response.data[0]['search_count'], 100)
        self.assertEqual(response.data[1]['query'], '二元一次方程')
        self.assertEqual(response.data[1]['search_count'], 80)
        self.assertEqual(response.data[2]['query'], '几何')
        self.assertEqual(response.data[2]['search_count'], 60)
    
    def test_record_search_history(self):
        """测试记录搜索历史"""
        url = reverse('search:search-history')
        data = {
            'query': '一元一次方程',
            'results_count': 10,
            'search_time': 0.5
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(SearchHistory.objects.filter(
            user=self.user,
            query='一元一次方程',
            results_count=10,
            search_time=0.5
        ).exists())
    
    def test_record_search_history_without_authentication(self):
        """测试未认证记录搜索历史"""
        self.client.credentials()  # 清除认证
        url = reverse('search:search-history')
        data = {
            'query': '一元一次方程',
            'results_count': 10,
            'search_time': 0.5
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(SearchHistory.objects.filter(
            query='一元一次方程'
        ).exists())