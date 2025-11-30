import json
from django.test import TestCase, Client
from django.urls import reverse
from apps.authentication.models import User
from apps.system.models import OperationLog


class SystemTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        # 创建测试操作日志
        self.log = OperationLog.objects.create(
            user=self.user,
            action='CREATE',
            resource_type='QUESTION',
            resource_id=1,
            extra_data='{"title": "测试问题", "action": "创建成功"}'
        )
        # 使用Django测试客户端的login方法登录
        self.client.login(username='testuser', password='testpassword123')
    
    def test_operation_log_json_accessor(self):
        """测试操作日志的JSON字段访问器"""
        # 测试get/set extra_data
        expected_extra_data = {"title": "测试问题", "action": "创建成功"}
        self.assertEqual(self.log.get_extra_data(), expected_extra_data)
        
        new_extra_data = {"title": "更新后的问题", "action": "更新成功"}
        self.log.set_extra_data(new_extra_data)
        self.assertEqual(self.log.get_extra_data(), new_extra_data)
    
    def test_get_operation_logs(self):
        """测试获取操作日志功能"""
        url = reverse('system:operation-logs')
        response = self.client.get(
            url,

        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 1)
    
    def test_filter_operation_logs(self):
        """测试按类型过滤操作日志功能"""
        url = reverse('system:operation-logs')
        params = {
            'action': 'CREATE',
            'resource_type': 'QUESTION'
        }
        response = self.client.get(
            url,
            params,

        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # 确保至少有一条匹配的日志
        self.assertGreaterEqual(len(data), 1)
        # 验证过滤结果
        for log in data:
            self.assertEqual(log['action'], 'CREATE')
            self.assertEqual(log['resource_type'], 'QUESTION')