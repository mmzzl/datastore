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
from PIL import Image
import io
import os

from apps.questions.models import Subject, KnowledgePoint, Question, QuestionImage
from apps.questions.views import SubjectViewSet, KnowledgePointViewSet, QuestionViewSet

User = get_user_model()


class SubjectModelTests(TestCase):
    """学科模型测试"""
    
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
            icon='math_icon.png',
            color='#FF5722',
            sort_order=1,
            is_active=True
        )
    
    def test_subject_creation(self):
        """测试学科创建"""
        self.assertEqual(self.subject.name, '数学')
        self.assertEqual(self.subject.description, '数学学科')
        self.assertEqual(self.subject.icon, 'math_icon.png')
        self.assertEqual(self.subject.color, '#FF5722')
        self.assertEqual(self.subject.sort_order, 1)
        self.assertTrue(self.subject.is_active)
    
    def test_subject_str_representation(self):
        """测试学科字符串表示"""
        self.assertEqual(str(self.subject), '数学')
    
    def test_subject_ordering(self):
        """测试学科排序"""
        subject2 = Subject.objects.create(
            name='英语',
            description='英语学科',
            sort_order=2,
            is_active=True
        )
        
        subjects = list(Subject.objects.all())
        self.assertEqual(subjects[0], self.subject)
        self.assertEqual(subjects[1], subject2)
    
    def test_subject_active_filter(self):
        """测试学科活跃状态过滤"""
        inactive_subject = Subject.objects.create(
            name='物理',
            description='物理学科',
            sort_order=3,
            is_active=False
        )
        
        active_subjects = Subject.objects.filter(is_active=True)
        self.assertIn(self.subject, active_subjects)
        self.assertNotIn(inactive_subject, active_subjects)


class KnowledgePointModelTests(TestCase):
    """知识点模型测试"""
    
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
            parent=None,
            level=1,
            sort_order=1,
            is_active=True
        )
    
    def test_knowledge_point_creation(self):
        """测试知识点创建"""
        self.assertEqual(self.knowledge_point.subject, self.subject)
        self.assertEqual(self.knowledge_point.name, '代数')
        self.assertEqual(self.knowledge_point.description, '代数知识点')
        self.assertIsNone(self.knowledge_point.parent)
        self.assertEqual(self.knowledge_point.level, 1)
        self.assertEqual(self.knowledge_point.sort_order, 1)
        self.assertTrue(self.knowledge_point.is_active)
    
    def test_knowledge_point_str_representation(self):
        """测试知识点字符串表示"""
        self.assertEqual(str(self.knowledge_point), '数学 - 代数')
    
    def test_knowledge_point_hierarchy(self):
        """测试知识点层级关系"""
        child_point = KnowledgePoint.objects.create(
            subject=self.subject,
            name='一元一次方程',
            description='一元一次方程知识点',
            parent=self.knowledge_point,
            level=2,
            sort_order=1,
            is_active=True
        )
        
        self.assertEqual(child_point.parent, self.knowledge_point)
        self.assertEqual(child_point.level, 2)
        self.assertIn(child_point, self.knowledge_point.children.all())
    
    def test_knowledge_point_full_name(self):
        """测试知识点完整名称"""
        child_point = KnowledgePoint.objects.create(
            subject=self.subject,
            name='一元一次方程',
            description='一元一次方程知识点',
            parent=self.knowledge_point,
            level=2,
            sort_order=1,
            is_active=True
        )
        
        self.assertEqual(child_point.get_full_name(), '数学 - 代数 > 一元一次方程')


class QuestionModelTests(TestCase):
    """错题模型测试"""
    
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
        self.question = Question.objects.create(
            user=self.user,
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
        self.question.subjects.add(self.subject)
        self.question.knowledge_points.add(self.knowledge_point)
    
    def test_question_creation(self):
        """测试错题创建"""
        self.assertEqual(self.question.user, self.user)
        self.assertEqual(self.question.title, '一元一次方程求解')
        self.assertEqual(self.question.content, '求解方程 2x + 5 = 15')
        self.assertEqual(self.question.answer, 'x = 5')
        self.assertEqual(self.question.solution, '移项得 2x = 10，两边除以2得 x = 5')
        self.assertEqual(self.question.difficulty, 2)
        self.assertEqual(self.question.question_type, '选择题')
        self.assertEqual(self.question.source, '教材')
        self.assertFalse(self.question.is_solved)
        self.assertFalse(self.question.is_marked)
        self.assertIn(self.subject, self.question.subjects.all())
        self.assertIn(self.knowledge_point, self.question.knowledge_points.all())
    
    def test_question_str_representation(self):
        """测试错题字符串表示"""
        self.assertEqual(str(self.question), 'testuser - 一元一次方程求解')
    
    def test_question_mark_as_solved(self):
        """测试标记错题为已解决"""
        self.assertFalse(self.question.is_solved)
        self.question.mark_as_solved()
        self.assertTrue(self.question.is_solved)
    
    def test_question_toggle_marked(self):
        """测试切换错题标记状态"""
        self.assertFalse(self.question.is_marked)
        self.question.toggle_marked()
        self.assertTrue(self.question.is_marked)
        self.question.toggle_marked()
        self.assertFalse(self.question.is_marked)
    
    def test_question_get_difficulty_display(self):
        """测试获取难度显示文本"""
        self.assertEqual(self.question.get_difficulty_display(), '中等')
        
        self.question.difficulty = 1
        self.assertEqual(self.question.get_difficulty_display(), '简单')
        
        self.question.difficulty = 3
        self.assertEqual(self.question.get_difficulty_display(), '困难')
    
    def test_question_get_type_display(self):
        """测试获取类型显示文本"""
        self.assertEqual(self.question.get_question_type_display(), '选择题')
        
        self.question.question_type = '填空题'
        self.assertEqual(self.question.get_question_type_display(), '填空题')
        
        self.question.question_type = '解答题'
        self.assertEqual(self.question.get_question_type_display(), '解答题')


class QuestionImageModelTests(TestCase):
    """错题图片模型测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.question = Question.objects.create(
            user=self.user,
            title='测试题目',
            content='测试内容',
            answer='测试答案',
            solution='测试解答',
            difficulty=1,
            question_type='选择题'
        )
        self.question_image = QuestionImage.objects.create(
            question=self.question,
            image='questions/images/test_image.jpg',
            description='测试图片',
            sort_order=1
        )
    
    def test_question_image_creation(self):
        """测试错题图片创建"""
        self.assertEqual(self.question_image.question, self.question)
        self.assertEqual(self.question_image.image, 'questions/images/test_image.jpg')
        self.assertEqual(self.question_image.description, '测试图片')
        self.assertEqual(self.question_image.sort_order, 1)
    
    def test_question_image_str_representation(self):
        """测试错题图片字符串表示"""
        self.assertEqual(str(self.question_image), 'testuser - 测试题目 - 测试图片')
    
    def test_question_image_ordering(self):
        """测试错题图片排序"""
        image2 = QuestionImage.objects.create(
            question=self.question,
            image='questions/images/test_image2.jpg',
            description='测试图片2',
            sort_order=2
        )
        
        images = list(QuestionImage.objects.all())
        self.assertEqual(images[0], self.question_image)
        self.assertEqual(images[1], image2)


class QuestionViewTests(APITestCase):
    """错题视图测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
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
        self.question = Question.objects.create(
            user=self.user,
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
        self.question.subjects.add(self.subject)
        self.question.knowledge_points.add(self.knowledge_point)
        
        # 认证用户
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_questions_list(self):
        """测试获取错题列表"""
        url = reverse('questions:question-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], '一元一次方程求解')
    
    def test_get_questions_list_filtered_by_user(self):
        """测试按用户过滤错题列表"""
        # 创建其他用户的错题
        other_question = Question.objects.create(
            user=self.other_user,
            title='其他用户的错题',
            content='其他内容',
            answer='其他答案',
            solution='其他解答',
            difficulty=1,
            question_type='填空题'
        )
        
        url = reverse('questions:question-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], '一元一次方程求解')
    
    def test_get_question_detail(self):
        """测试获取错题详情"""
        url = reverse('questions:question-detail', kwargs={'pk': self.question.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], '一元一次方程求解')
        self.assertEqual(response.data['content'], '求解方程 2x + 5 = 15')
        self.assertEqual(response.data['answer'], 'x = 5')
        self.assertEqual(response.data['solution'], '移项得 2x = 10，两边除以2得 x = 5')
    
    def test_get_question_detail_not_found(self):
        """测试获取不存在的错题详情"""
        url = reverse('questions:question-detail', kwargs={'pk': 999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_question_detail_of_other_user(self):
        """测试获取其他用户的错题详情"""
        # 创建其他用户的错题
        other_question = Question.objects.create(
            user=self.other_user,
            title='其他用户的错题',
            content='其他内容',
            answer='其他答案',
            solution='其他解答',
            difficulty=1,
            question_type='填空题'
        )
        
        url = reverse('questions:question-detail', kwargs={'pk': other_question.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_question(self):
        """测试创建错题"""
        url = reverse('questions:question-list')
        data = {
            'title': '新错题',
            'content': '新错题内容',
            'answer': '新错题答案',
            'solution': '新错题解答',
            'difficulty': 1,
            'question_type': '填空题',
            'source': '练习册',
            'subjects': [self.subject.id],
            'knowledge_points': [self.knowledge_point.id]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Question.objects.count(), 2)
        
        new_question = Question.objects.latest('created_at')
        self.assertEqual(new_question.title, '新错题')
        self.assertEqual(new_question.user, self.user)
        self.assertIn(self.subject, new_question.subjects.all())
        self.assertIn(self.knowledge_point, new_question.knowledge_points.all())
    
    def test_create_question_without_authentication(self):
        """测试未认证创建错题"""
        self.client.credentials()  # 清除认证
        url = reverse('questions:question-list')
        data = {
            'title': '新错题',
            'content': '新错题内容',
            'answer': '新错题答案',
            'solution': '新错题解答',
            'difficulty': 1,
            'question_type': '填空题',
            'source': '练习册'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Question.objects.count(), 1)
    
    def test_update_question(self):
        """测试更新错题"""
        url = reverse('questions:question-detail', kwargs={'pk': self.question.id})
        data = {
            'title': '更新后的错题',
            'content': '更新后的内容',
            'answer': '更新后的答案',
            'solution': '更新后的解答',
            'difficulty': 3,
            'question_type': '解答题',
            'source': '试卷'
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.question.refresh_from_db()
        self.assertEqual(self.question.title, '更新后的错题')
        self.assertEqual(self.question.content, '更新后的内容')
        self.assertEqual(self.question.answer, '更新后的答案')
        self.assertEqual(self.question.solution, '更新后的解答')
        self.assertEqual(self.question.difficulty, 3)
        self.assertEqual(self.question.question_type, '解答题')
        self.assertEqual(self.question.source, '试卷')
    
    def test_update_question_of_other_user(self):
        """测试更新其他用户的错题"""
        # 创建其他用户的错题
        other_question = Question.objects.create(
            user=self.other_user,
            title='其他用户的错题',
            content='其他内容',
            answer='其他答案',
            solution='其他解答',
            difficulty=1,
            question_type='填空题'
        )
        
        url = reverse('questions:question-detail', kwargs={'pk': other_question.id})
        data = {
            'title': '更新后的错题',
            'content': '更新后的内容',
            'answer': '更新后的答案',
            'solution': '更新后的解答',
            'difficulty': 3,
            'question_type': '解答题',
            'source': '试卷'
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        other_question.refresh_from_db()
        self.assertEqual(other_question.title, '其他用户的错题')
    
    def test_delete_question(self):
        """测试删除错题"""
        url = reverse('questions:question-detail', kwargs={'pk': self.question.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Question.objects.count(), 0)
    
    def test_delete_question_of_other_user(self):
        """测试删除其他用户的错题"""
        # 创建其他用户的错题
        other_question = Question.objects.create(
            user=self.other_user,
            title='其他用户的错题',
            content='其他内容',
            answer='其他答案',
            solution='其他解答',
            difficulty=1,
            question_type='填空题'
        )
        
        url = reverse('questions:question-detail', kwargs={'pk': other_question.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Question.objects.count(), 2)
    
    def test_mark_question_as_solved(self):
        """测试标记错题为已解决"""
        url = reverse('questions:question-mark-solved', kwargs={'pk': self.question.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.question.refresh_from_db()
        self.assertTrue(self.question.is_solved)
    
    def test_toggle_question_marked(self):
        """测试切换错题标记状态"""
        url = reverse('questions:question-toggle-marked', kwargs={'pk': self.question.id})
        
        # 标记为已标记
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.question.refresh_from_db()
        self.assertTrue(self.question.is_marked)
        
        # 取消标记
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.question.refresh_from_db()
        self.assertFalse(self.question.is_marked)
    
    def test_batch_delete_questions(self):
        """测试批量删除错题"""
        # 创建更多错题
        question2 = Question.objects.create(
            user=self.user,
            title='错题2',
            content='内容2',
            answer='答案2',
            solution='解答2',
            difficulty=1,
            question_type='填空题'
        )
        question3 = Question.objects.create(
            user=self.user,
            title='错题3',
            content='内容3',
            answer='答案3',
            solution='解答3',
            difficulty=2,
            question_type='选择题'
        )
        
        url = reverse('questions:question-batch-delete')
        data = {
            'question_ids': [self.question.id, question2.id]
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Question.objects.count(), 1)
        self.assertTrue(Question.objects.filter(id=question3.id).exists())
    
    def test_upload_question_image(self):
        """测试上传错题图片"""
        # 创建测试图片
        image = Image.new('RGB', (100, 100), 'red')
        image_file = io.BytesIO()
        image.save(image_file, 'jpeg')
        image_file.seek(0)
        
        url = reverse('questions:question-upload-image', kwargs={'pk': self.question.id})
        data = {
            'image': image_file,
            'description': '测试图片',
            'sort_order': 1
        }
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(QuestionImage.objects.count(), 1)
        
        question_image = QuestionImage.objects.first()
        self.assertEqual(question_image.question, self.question)
        self.assertEqual(question_image.description, '测试图片')
        self.assertEqual(question_image.sort_order, 1)
    
    def test_get_question_statistics(self):
        """测试获取错题统计"""
        # 创建更多错题用于统计
        Question.objects.create(
            user=self.user,
            title='错题2',
            content='内容2',
            answer='答案2',
            solution='解答2',
            difficulty=1,
            question_type='填空题',
            is_solved=True
        )
        Question.objects.create(
            user=self.user,
            title='错题3',
            content='内容3',
            answer='答案3',
            solution='解答3',
            difficulty=2,
            question_type='选择题',
            is_marked=True
        )
        
        url = reverse('questions:question-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_questions'], 3)
        self.assertEqual(response.data['solved_questions'], 1)
        self.assertEqual(response.data['marked_questions'], 1)
        self.assertIn('difficulty_distribution', response.data)
        self.assertIn('type_distribution', response.data)


class SubjectViewTests(APITestCase):
    """学科视图测试"""
    
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
            icon='math_icon.png',
            color='#FF5722',
            sort_order=1,
            is_active=True
        )
        
        # 认证用户
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_subjects_list(self):
        """测试获取学科列表"""
        url = reverse('questions:subject-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], '数学')
    
    def test_get_subject_detail(self):
        """测试获取学科详情"""
        url = reverse('questions:subject-detail', kwargs={'pk': self.subject.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], '数学')
        self.assertEqual(response.data['description'], '数学学科')
        self.assertEqual(response.data['icon'], 'math_icon.png')
        self.assertEqual(response.data['color'], '#FF5722')
        self.assertEqual(response.data['sort_order'], 1)
        self.assertTrue(response.data['is_active'])


class KnowledgePointViewTests(APITestCase):
    """知识点视图测试"""
    
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
        
        # 认证用户
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_knowledge_points_list(self):
        """测试获取知识点列表"""
        url = reverse('questions:knowledgepoint-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], '代数')
    
    def test_get_knowledge_point_detail(self):
        """测试获取知识点详情"""
        url = reverse('questions:knowledgepoint-detail', kwargs={'pk': self.knowledge_point.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], '代数')
        self.assertEqual(response.data['description'], '代数知识点')
        self.assertEqual(response.data['level'], 1)
        self.assertEqual(response.data['sort_order'], 1)
        self.assertTrue(response.data['is_active'])
    
    def test_get_knowledge_points_by_subject(self):
        """测试按学科获取知识点"""
        url = reverse('questions:knowledgepoint-list')
        response = self.client.get(url, {'subject': self.subject.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], '代数')