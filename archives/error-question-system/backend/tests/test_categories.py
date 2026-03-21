import json
from django.test import TestCase, Client
from django.urls import reverse
from apps.authentication.models import User
from apps.categories.models import Category


class CategoryTestCase(TestCase):
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
        # 登录获取token
        login_url = reverse('authentication:login')
        login_data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        login_response = self.client.post(login_url, login_data, content_type='application/json')
        self.token = login_response.json()['access']
    
    def test_create_category(self):
        """测试创建分类功能"""
        url = reverse('categories:category-list')
        data = {
            'name': '新分类',
            'description': '新创建的分类'
        }
        response = self.client.post(
            url,
            data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Category.objects.filter(name='新分类').exists())
    
    def test_list_categories(self):
        """测试获取分类列表功能"""
        url = reverse('categories:category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 1)
    
    def test_retrieve_category(self):
        """测试获取单个分类详情功能"""
        url = reverse('categories:category-detail', args=[self.category.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['name'], '测试分类')
        self.assertEqual(data['description'], '这是一个测试分类')
    
    def test_update_category(self):
        """测试更新分类功能"""
        url = reverse('categories:category-detail', args=[self.category.id])
        data = {
            'name': '更新后的分类',
            'description': '更新后的描述'
        }
        response = self.client.put(
            url,
            data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.category.refresh_from_db()
        self.assertEqual(self.category.name, '更新后的分类')
    
    def test_delete_category(self):
        """测试删除分类功能"""
        url = reverse('categories:category-detail', args=[self.category.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Category.objects.filter(id=self.category.id).exists())