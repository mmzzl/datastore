from django.test import TestCase, Client
from django.urls import reverse
from apps.authentication.models import User
from apps.categories.models import Category
from apps.questions.models import Question
from apps.answers.models import Answer
from apps.search.models import SearchHistory


class SearchTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        # 创建测试分类
        self.category = Category.objects.create(
            name='测试分类',
            description='这是一个测试分类',
            created_by=self.user
        )
        # 创建测试问题
        self.question1 = Question.objects.create(
            title='Python测试问题',
            content='这是关于Python的测试问题',
            category=self.category,
            created_by=self.user,
            tags='["Python", "编程"]'
        )
        self.question2 = Question.objects.create(
            title='Django测试问题',
            content='这是关于Django的测试问题',
            category=self.category,
            created_by=self.user,
            tags='["Django", "Web开发"]'
        )
        # 创建搜索历史
        self.search_history = SearchHistory.objects.create(
            user=self.user,
            keyword='Python',
            filters='{"category": null, "tags": ["Python"]}',
            results_count=1
        )
        # 使用Django测试客户端的login方法登录
        self.client.login(username='testuser', password='testpassword123')
    
    def test_search_questions(self):
        """测试搜索问题功能"""
        url = reverse('search:search-questions')
        params = {
            'keyword': 'Python'
        }
        response = self.client.get(
            url,
            params
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data['results']), 1)
    
    def test_search_with_filters(self):
        """测试带过滤器的搜索功能"""
        url = reverse('search:search-questions')
        params = {
            'keyword': '测试',
            'category': self.category.id,
            'tags': 'Python'
        }
        response = self.client.get(
            url,
            params
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsNotNone(data['results'])
    
    def test_search_history_json_accessor(self):
        """测试搜索历史的JSON字段访问器"""
        # 测试get/set filters
        expected_filters = {"category": None, "tags": ["Python"]}
        self.assertEqual(self.search_history.get_filters(), expected_filters)
        
        new_filters = {"category": self.category.id, "tags": ["Django"]}
        self.search_history.set_filters(new_filters)
        self.assertEqual(self.search_history.get_filters(), new_filters)
    
    def test_get_search_history(self):
        """测试获取搜索历史功能"""
        url = reverse('search:search-history')
        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 1)
    
    def test_clear_search_history(self):
        """测试清除搜索历史功能"""
        url = reverse('search:clear-history')
        response = self.client.delete(
            url
        )
        self.assertEqual(response.status_code, 204)
        self.assertEqual(SearchHistory.objects.filter(user=self.user).count(), 0)