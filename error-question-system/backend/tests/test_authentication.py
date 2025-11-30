import json
from django.test import TestCase, Client
from django.urls import reverse
from apps.authentication.models import User


class AuthenticationTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
    
    def test_user_registration(self):
        """测试用户注册功能"""
        url = reverse('authentication:register')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpassword123',
            'password_confirm': 'newpassword123'
        }
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 201)
        # 验证用户是否被创建
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_user_login(self):
        """测试用户登录功能"""
        url = reverse('authentication:login')
        data = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('username', response_data)
        self.assertIn('email', response_data)
    
    def test_user_profile(self):
        """测试获取用户信息功能"""
        # 使用Django测试客户端的login方法登录
        self.client.login(username='testuser', password='testpassword123')
        
        # 获取用户信息
        profile_url = reverse('authentication:profile')
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, 200)
        profile_data = response.json()
        self.assertEqual(profile_data['username'], 'testuser')
        self.assertEqual(profile_data['email'], 'test@example.com')
    
    def test_logout(self):
        """测试用户登出功能"""
        # 使用Django测试客户端的login方法登录
        self.client.login(username='testuser', password='testpassword123')
        
        # 登出
        logout_url = reverse('authentication:logout')
        response = self.client.post(logout_url, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('message', response.json())