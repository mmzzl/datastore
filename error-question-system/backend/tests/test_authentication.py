import pytest
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta

from apps.authentication.models import UserProfile, UserLoginLog, UserActivityLog
from apps.authentication.views import register, login_view, logout_view, profile, update_profile

User = get_user_model()


class UserModelTests(TestCase):
    """用户模型测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)
    
    def test_create_user(self):
        """测试创建用户"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpass123'))
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
    
    def test_create_user_without_email(self):
        """测试创建无邮箱用户"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username='noemail',
                email='',
                password='testpass123'
            )
    
    def test_create_superuser(self):
        """测试创建超级用户"""
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)
    
    def test_user_str_representation(self):
        """测试用户字符串表示"""
        self.assertEqual(str(self.user), 'testuser')
    
    def test_get_full_name(self):
        """测试获取全名"""
        self.user.first_name = 'Test'
        self.user.last_name = 'User'
        self.user.save()
        self.assertEqual(self.user.get_full_name(), 'Test User')
    
    def test_get_short_name(self):
        """测试获取短名称"""
        self.user.first_name = 'Test'
        self.user.save()
        self.assertEqual(self.user.get_short_name(), 'Test')


class UserProfileModelTests(TestCase):
    """用户档案模型测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.profile = UserProfile.objects.create(
            user=self.user,
            nickname='Test Nickname',
            bio='Test bio',
            phone='1234567890',
            avatar='avatars/test_avatar.jpg'
        )
    
    def test_profile_creation(self):
        """测试档案创建"""
        self.assertEqual(self.profile.user, self.user)
        self.assertEqual(self.profile.nickname, 'Test Nickname')
        self.assertEqual(self.profile.bio, 'Test bio')
        self.assertEqual(self.profile.phone, '1234567890')
        self.assertEqual(self.profile.avatar, 'avatars/test_avatar.jpg')
    
    def test_profile_str_representation(self):
        """测试档案字符串表示"""
        self.assertEqual(str(self.profile), 'testuser - Test Nickname')
    
    def test_profile_auto_creation(self):
        """测试用户创建时自动创建档案"""
        new_user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )
        self.assertTrue(hasattr(new_user, 'profile'))
        self.assertIsInstance(new_user.profile, UserProfile)


class UserLoginLogModelTests(TestCase):
    """用户登录日志模型测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.login_log = UserLoginLog.objects.create(
            user=self.user,
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            login_type='web'
        )
    
    def test_login_log_creation(self):
        """测试登录日志创建"""
        self.assertEqual(self.login_log.user, self.user)
        self.assertEqual(self.login_log.ip_address, '127.0.0.1')
        self.assertEqual(self.login_log.user_agent, 'Test Agent')
        self.assertEqual(self.login_log.login_type, 'web')
        self.assertIsNotNone(self.login_log.login_time)
    
    def test_login_log_str_representation(self):
        """测试登录日志字符串表示"""
        expected_str = f"{self.user.username} - {self.login_log.login_time}"
        self.assertEqual(str(self.login_log), expected_str)


class UserActivityLogModelTests(TestCase):
    """用户活动日志模型测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.activity_log = UserActivityLog.objects.create(
            user=self.user,
            action='create_question',
            resource_type='question',
            resource_id=1,
            description='创建了一道错题',
            ip_address='127.0.0.1',
            user_agent='Test Agent'
        )
    
    def test_activity_log_creation(self):
        """测试活动日志创建"""
        self.assertEqual(self.activity_log.user, self.user)
        self.assertEqual(self.activity_log.action, 'create_question')
        self.assertEqual(self.activity_log.resource_type, 'question')
        self.assertEqual(self.activity_log.resource_id, 1)
        self.assertEqual(self.activity_log.description, '创建了一道错题')
        self.assertEqual(self.activity_log.ip_address, '127.0.0.1')
        self.assertEqual(self.activity_log.user_agent, 'Test Agent')
        self.assertIsNotNone(self.activity_log.timestamp)
    
    def test_activity_log_str_representation(self):
        """测试活动日志字符串表示"""
        expected_str = f"{self.user.username} - {self.activity_log.action} - {self.activity_log.timestamp}"
        self.assertEqual(str(self.activity_log), expected_str)


class AuthenticationViewTests(APITestCase):
    """认证视图测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        self.user = User.objects.create_user(**self.user_data)
        self.login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
    
    def test_register_user(self):
        """测试用户注册"""
        new_user_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        url = reverse('authentication:register')
        response = self.client.post(url, new_user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        self.assertEqual(response.data['username'], 'newuser')
        self.assertEqual(response.data['email'], 'new@example.com')
        self.assertNotIn('password', response.data)
    
    def test_register_user_with_invalid_data(self):
        """测试使用无效数据注册用户"""
        invalid_data = {
            'username': '',  # 空用户名
            'email': 'invalid-email',  # 无效邮箱
            'password': '123',  # 密码太短
            'password_confirm': '456'  # 密码不匹配
        }
        url = reverse('authentication:register')
        response = self.client.post(url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username='').exists())
    
    def test_register_user_with_existing_username(self):
        """测试使用已存在的用户名注册"""
        existing_user_data = {
            'username': 'testuser',  # 已存在的用户名
            'email': 'another@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        url = reverse('authentication:register')
        response = self.client.post(url, existing_user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
    
    def test_login_user(self):
        """测试用户登录"""
        url = reverse('authentication:login')
        response = self.client.post(url, self.login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('username', response.data)
        self.assertEqual(response.data['username'], 'testuser')
        
        # 验证登录日志是否创建
        self.assertTrue(UserLoginLog.objects.filter(user=self.user).exists())
    
    def test_login_user_with_invalid_credentials(self):
        """测试使用无效凭据登录"""
        invalid_login_data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        url = reverse('authentication:login')
        response = self.client.post(url, invalid_login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_logout_user(self):
        """测试用户登出"""
        # 先登录
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('authentication:logout')
        response = self.client.post(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    def test_get_user_info(self):
        """测试获取用户信息"""
        # 先登录
        self.client.login(username='testuser', password='testpass123')
        
        url = reverse('authentication:profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')
    
    def test_get_user_info_without_authentication(self):
        """测试未认证获取用户信息"""
        url = reverse('authentication:profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_user_info(self):
        """测试更新用户信息"""
        # 先登录
        self.client.login(username='testuser', password='testpass123')
        
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com'
        }
        url = reverse('authentication:update_profile')
        response = self.client.put(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.email, 'updated@example.com')
    
    def test_update_user_info_without_authentication(self):
        """测试未认证更新用户信息"""
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'email': 'updated@example.com'
        }
        url = reverse('authentication:update_profile')
        response = self.client.put(url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_change_password(self):
        """测试修改密码"""
        # 先登录
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        password_data = {
            'old_password': 'testpass123',
            'new_password': 'newtestpass123'
        }
        url = reverse('authentication:change-password')
        response = self.client.post(url, password_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newtestpass123'))
    
    def test_change_password_with_wrong_old_password(self):
        """测试使用错误旧密码修改密码"""
        # 先登录
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        password_data = {
            'old_password': 'wrongpass123',
            'new_password': 'newtestpass123'
        }
        url = reverse('authentication:change-password')
        response = self.client.post(url, password_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('testpass123'))
    
    @patch('apps.authentication.views.send_password_reset_email')
    def test_reset_password(self, mock_send_email):
        """测试重置密码"""
        mock_send_email.return_value = True
        
        reset_data = {
            'email': 'test@example.com'
        }
        url = reverse('authentication:reset-password')
        response = self.client.post(url, reset_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_email.assert_called_once()
    
    def test_reset_password_with_nonexistent_email(self):
        """测试使用不存在的邮箱重置密码"""
        reset_data = {
            'email': 'nonexistent@example.com'
        }
        url = reverse('authentication:reset-password')
        response = self.client.post(url, reset_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AuthenticationIntegrationTests(APITestCase):
    """认证集成测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }
    
    def test_full_user_authentication_flow(self):
        """测试完整用户认证流程"""
        # 1. 注册用户
        register_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        register_url = reverse('authentication:register')
        register_response = self.client.post(register_url, register_data, format='json')
        
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)
        
        # 2. 登录用户
        login_data = {
            'username': 'newuser',
            'password': 'newpass123'
        }
        login_url = reverse('authentication:login')
        login_response = self.client.post(login_url, login_data, format='json')
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', login_response.data)
        self.assertIn('refresh', login_response.data)
        
        access_token = login_response.data['access']
        refresh_token = login_response.data['refresh']
        
        # 3. 获取用户信息
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        user_url = reverse('authentication:user')
        user_response = self.client.get(user_url)
        
        self.assertEqual(user_response.status_code, status.HTTP_200_OK)
        self.assertEqual(user_response.data['username'], 'newuser')
        
        # 4. 更新用户信息
        update_data = {
            'first_name': 'Test',
            'last_name': 'User'
        }
        update_response = self.client.put(user_url, update_data, format='json')
        
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        
        # 5. 修改密码
        password_data = {
            'old_password': 'newpass123',
            'new_password': 'updatedpass123'
        }
        password_url = reverse('authentication:change-password')
        password_response = self.client.post(password_url, password_data, format='json')
        
        self.assertEqual(password_response.status_code, status.HTTP_200_OK)
        
        # 6. 登出用户
        logout_url = reverse('authentication:logout')
        logout_response = self.client.post(logout_url, {'refresh': refresh_token}, format='json')
        
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
        # 7. 使用新密码重新登录
        new_login_data = {
            'username': 'newuser',
            'password': 'updatedpass123'
        }
        new_login_response = self.client.post(login_url, new_login_data, format='json')
        
        self.assertEqual(new_login_response.status_code, status.HTTP_200_OK)
    
    def test_multiple_login_sessions(self):
        """测试多登录会话"""
        # 创建用户
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # 第一次登录
        login_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        login_url = reverse('authentication:login')
        first_login_response = self.client.post(login_url, login_data, format='json')
        
        self.assertEqual(first_login_response.status_code, status.HTTP_200_OK)
        first_access_token = first_login_response.data['access']
        
        # 第二次登录（使用新的客户端实例）
        client2 = self.client_class()
        second_login_response = client2.post(login_url, login_data, format='json')
        
        self.assertEqual(second_login_response.status_code, status.HTTP_200_OK)
        second_access_token = second_login_response.data['access']
        
        # 验证两个token都有效
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {first_access_token}')
        user_url = reverse('authentication:user')
        first_user_response = self.client.get(user_url)
        
        client2.credentials(HTTP_AUTHORIZATION=f'Bearer {second_access_token}')
        second_user_response = client2.get(user_url)
        
        self.assertEqual(first_user_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_user_response.status_code, status.HTTP_200_OK)
        
        # 验证登录日志记录
        self.assertEqual(UserLoginLog.objects.filter(user=user).count(), 2)