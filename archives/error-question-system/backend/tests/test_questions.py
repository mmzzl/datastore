import json
from django.test import TestCase, Client
from django.urls import reverse
from apps.authentication.models import User
from apps.categories.models import Category
from apps.questions.models import Question


class QuestionTestCase(TestCase):
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
        self.question = Question.objects.create(
            title='测试问题',
            content='这是一个测试问题的内容',
            category=self.category,
            created_by=self.user,
            options='{"A": "选项A", "B": "选项B"}',
            tags='["测试", "示例"]',
            images='["image1.jpg", "image2.jpg"]'
        )
        # 使用Django测试客户端的login方法登录
        self.client.login(username='testuser', password='testpassword123')
    
    def test_create_question(self):
        """测试创建问题功能"""
        url = reverse('questions:question-list')
        data = {
            'title': '新问题',
            'content': '新问题的内容',
            'category': self.category.id,
            'options': '{"A": "新选项A", "B": "新选项B"}',
            'tags': '["新标签1", "新标签2"]',
            'images': '["new_image.jpg"]'
        }
        response = self.client.post(
            url,
            data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Question.objects.filter(title='新问题').exists())
    
    def test_list_questions(self):
        """测试获取问题列表功能"""
        url = reverse('questions:question-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 1)
    
    def test_retrieve_question(self):
        """测试获取单个问题详情功能"""
        url = reverse('questions:question-detail', args=[self.question.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['title'], '测试问题')
    
    def test_json_field_accessors(self):
        """测试JSON字段访问器功能"""
        # 测试get/set options
        self.assertEqual(self.question.get_options(), {"A": "选项A", "B": "选项B"})
        self.question.set_options({"C": "选项C", "D": "选项D"})
        self.assertEqual(self.question.get_options(), {"C": "选项C", "D": "选项D"})
        
        # 测试get/set tags
        self.assertEqual(self.question.get_tags(), ["测试", "示例"])
        self.question.set_tags(["新标签1", "新标签2"])
        self.assertEqual(self.question.get_tags(), ["新标签1", "新标签2"])
        
        # 测试get/set images
        self.assertEqual(self.question.get_images(), ["image1.jpg", "image2.jpg"])
        self.question.set_images(["new_image.jpg"])
        self.assertEqual(self.question.get_images(), ["new_image.jpg"])
    
    def test_update_question(self):
        """测试更新问题功能"""
        url = reverse('questions:question-detail', args=[self.question.id])
        data = {
            'title': '更新后的问题',
            'content': '更新后的内容',
            'options': '{"C": "选项C", "D": "选项D"}'
        }
        response = self.client.put(
            url,
            data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.question.refresh_from_db()
        self.assertEqual(self.question.title, '更新后的问题')
    
    def test_delete_question(self):
        """测试删除问题功能"""
        url = reverse('questions:question-detail', args=[self.question.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Question.objects.filter(id=self.question.id).exists())