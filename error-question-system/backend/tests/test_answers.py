import json
from django.test import TestCase, Client
from django.urls import reverse
from apps.authentication.models import User
from apps.categories.models import Category
from apps.questions.models import Question
from apps.answers.models import Answer


class AnswerTestCase(TestCase):
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
            options='{"A": "选项A", "B": "选项B"}'
        )
        # 创建测试答案
        self.answer = Answer.objects.create(
            question=self.question,
            content='这是正确答案',
            is_correct=True,
            created_by=self.user,
            steps='["步骤1：分析问题", "步骤2：得出结论"]',
            images='["answer_image1.jpg", "answer_image2.jpg"]'
        )
        # 使用Django测试客户端的login方法登录
        self.client.login(username='testuser', password='testpassword123')
    
    def test_create_answer(self):
        """测试创建答案功能"""
        url = reverse('answers:answer-list')
        data = {
            'question': self.question.id,
            'content': '新的答案',
            'is_correct': False,
            'steps': '["新步骤1", "新步骤2"]',
            'images': '["new_answer_image.jpg"]'
        }
        response = self.client.post(
            url,
            data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Answer.objects.filter(content='新的答案').exists())
    
    def test_list_answers(self):
        """测试获取答案列表功能"""
        url = reverse('answers:answer-list')
        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 1)
    
    def test_retrieve_answer(self):
        """测试获取单个答案详情功能"""
        url = reverse('answers:answer-detail', args=[self.answer.id])
        response = self.client.get(
            url
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['content'], '这是正确答案')
    
    def test_json_field_accessors(self):
        """测试JSON字段访问器功能"""
        # 测试get/set steps
        self.assertEqual(self.answer.get_steps(), ["步骤1：分析问题", "步骤2：得出结论"])
        self.answer.set_steps(["新步骤1", "新步骤2"])
        self.assertEqual(self.answer.get_steps(), ["新步骤1", "新步骤2"])
        
        # 测试get/set images
        self.assertEqual(self.answer.get_images(), ["answer_image1.jpg", "answer_image2.jpg"])
        self.answer.set_images(["new_answer_image.jpg"])
        self.assertEqual(self.answer.get_images(), ["new_answer_image.jpg"])
    
    def test_update_answer(self):
        """测试更新答案功能"""
        url = reverse('answers:answer-detail', args=[self.answer.id])
        data = {
            'content': '更新后的答案',
            'is_correct': False,
            'steps': '["更新后的步骤1", "更新后的步骤2"]'
        }
        response = self.client.put(
            url,
            data,
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.content, '更新后的答案')
        self.assertFalse(self.answer.is_correct)
    
    def test_delete_answer(self):
        """测试删除答案功能"""
        url = reverse('answers:answer-detail', args=[self.answer.id])
        response = self.client.delete(
            url
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Answer.objects.filter(id=self.answer.id).exists())