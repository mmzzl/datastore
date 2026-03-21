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

from apps.questions.models import Question, Subject, KnowledgePoint
from apps.answers.models import Answer, AnswerImage, AnswerComment, AnswerLike, CommentLike
from apps.answers.views import AnswerViewSet

User = get_user_model()


class AnswerModelTests(TestCase):
    """答案模型测试"""
    
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
        self.answer = Answer.objects.create(
            question=self.question,
            user=self.user,
            content='这是我的解答过程：移项得 2x = 10，两边除以2得 x = 5',
            is_ai_generated=False,
            is_correct=True,
            is_public=True
        )
    
    def test_answer_creation(self):
        """测试答案创建"""
        self.assertEqual(self.answer.question, self.question)
        self.assertEqual(self.answer.user, self.user)
        self.assertEqual(
            self.answer.content,
            '这是我的解答过程：移项得 2x = 10，两边除以2得 x = 5'
        )
        self.assertFalse(self.answer.is_ai_generated)
        self.assertTrue(self.answer.is_correct)
        self.assertTrue(self.answer.is_public)
    
    def test_answer_str_representation(self):
        """测试答案字符串表示"""
        expected_str = f"{self.user.username} - {self.question.title}"
        self.assertEqual(str(self.answer), expected_str)
    
    def test_answer_like_count(self):
        """测试答案点赞数"""
        self.assertEqual(self.answer.like_count, 0)
        
        # 添加点赞
        AnswerLike.objects.create(
            user=self.other_user,
            answer=self.answer
        )
        
        # 重新获取答案以触发属性计算
        answer = Answer.objects.get(id=self.answer.id)
        self.assertEqual(answer.like_count, 1)
    
    def test_answer_comment_count(self):
        """测试答案评论数"""
        self.assertEqual(self.answer.comment_count, 0)
        
        # 添加评论
        AnswerComment.objects.create(
            user=self.other_user,
            answer=self.answer,
            content='很好的解答！'
        )
        
        # 重新获取答案以触发属性计算
        answer = Answer.objects.get(id=self.answer.id)
        self.assertEqual(answer.comment_count, 1)


class AnswerImageModelTests(TestCase):
    """答案图片模型测试"""
    
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
        self.answer = Answer.objects.create(
            question=self.question,
            user=self.user,
            content='这是我的解答过程',
            is_ai_generated=False,
            is_correct=True,
            is_public=True
        )
        self.answer_image = AnswerImage.objects.create(
            answer=self.answer,
            image='answers/images/test_image.jpg',
            description='解答图片',
            sort_order=1
        )
    
    def test_answer_image_creation(self):
        """测试答案图片创建"""
        self.assertEqual(self.answer_image.answer, self.answer)
        self.assertEqual(self.answer_image.image, 'answers/images/test_image.jpg')
        self.assertEqual(self.answer_image.description, '解答图片')
        self.assertEqual(self.answer_image.sort_order, 1)
    
    def test_answer_image_str_representation(self):
        """测试答案图片字符串表示"""
        expected_str = f"{self.user.username} - {self.question.title} - 解答图片"
        self.assertEqual(str(self.answer_image), expected_str)


class AnswerCommentModelTests(TestCase):
    """答案评论模型测试"""
    
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
        self.answer = Answer.objects.create(
            question=self.question,
            user=self.user,
            content='这是我的解答过程',
            is_ai_generated=False,
            is_correct=True,
            is_public=True
        )
        self.comment = AnswerComment.objects.create(
            user=self.other_user,
            answer=self.answer,
            content='很好的解答！'
        )
    
    def test_answer_comment_creation(self):
        """测试答案评论创建"""
        self.assertEqual(self.comment.user, self.other_user)
        self.assertEqual(self.comment.answer, self.answer)
        self.assertEqual(self.comment.content, '很好的解答！')
    
    def test_answer_comment_str_representation(self):
        """测试答案评论字符串表示"""
        expected_str = f"{self.other_user.username} - {self.question.title}"
        self.assertEqual(str(self.comment), expected_str)
    
    def test_answer_comment_like_count(self):
        """测试答案评论点赞数"""
        self.assertEqual(self.comment.like_count, 0)
        
        # 添加点赞
        CommentLike.objects.create(
            user=self.user,
            comment=self.comment
        )
        
        # 重新获取评论以触发属性计算
        comment = AnswerComment.objects.get(id=self.comment.id)
        self.assertEqual(comment.like_count, 1)


class AnswerLikeModelTests(TestCase):
    """答案点赞模型测试"""
    
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
        self.answer = Answer.objects.create(
            question=self.question,
            user=self.user,
            content='这是我的解答过程',
            is_ai_generated=False,
            is_correct=True,
            is_public=True
        )
        self.answer_like = AnswerLike.objects.create(
            user=self.other_user,
            answer=self.answer
        )
    
    def test_answer_like_creation(self):
        """测试答案点赞创建"""
        self.assertEqual(self.answer_like.user, self.other_user)
        self.assertEqual(self.answer_like.answer, self.answer)
    
    def test_answer_like_str_representation(self):
        """测试答案点赞字符串表示"""
        expected_str = f"{self.other_user.username} - {self.question.title}"
        self.assertEqual(str(self.answer_like), expected_str)
    
    def test_answer_like_unique_constraint(self):
        """测试答案点赞唯一约束"""
        # 尝试创建相同的点赞记录
        with self.assertRaises(Exception):  # 应该抛出IntegrityError或类似异常
            AnswerLike.objects.create(
                user=self.other_user,
                answer=self.answer
            )


class CommentLikeModelTests(TestCase):
    """评论点赞模型测试"""
    
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
        self.answer = Answer.objects.create(
            question=self.question,
            user=self.user,
            content='这是我的解答过程',
            is_ai_generated=False,
            is_correct=True,
            is_public=True
        )
        self.comment = AnswerComment.objects.create(
            user=self.other_user,
            answer=self.answer,
            content='很好的解答！'
        )
        self.comment_like = CommentLike.objects.create(
            user=self.user,
            comment=self.comment
        )
    
    def test_comment_like_creation(self):
        """测试评论点赞创建"""
        self.assertEqual(self.comment_like.user, self.user)
        self.assertEqual(self.comment_like.comment, self.comment)
    
    def test_comment_like_str_representation(self):
        """测试评论点赞字符串表示"""
        expected_str = f"{self.user.username} - {self.question.title}"
        self.assertEqual(str(self.comment_like), expected_str)
    
    def test_comment_like_unique_constraint(self):
        """测试评论点赞唯一约束"""
        # 尝试创建相同的点赞记录
        with self.assertRaises(Exception):  # 应该抛出IntegrityError或类似异常
            CommentLike.objects.create(
                user=self.user,
                comment=self.comment
            )


class AnswerViewTests(APITestCase):
    """答案视图测试"""
    
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
        self.answer = Answer.objects.create(
            question=self.question,
            user=self.user,
            content='这是我的解答过程：移项得 2x = 10，两边除以2得 x = 5',
            is_ai_generated=False,
            is_correct=True,
            is_public=True
        )
        
        # 认证用户
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_answers_list(self):
        """测试获取答案列表"""
        url = reverse('answers:answer-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(
            response.data['results'][0]['content'],
            '这是我的解答过程：移项得 2x = 10，两边除以2得 x = 5'
        )
    
    def test_get_answers_list_filtered_by_question(self):
        """测试按题目过滤答案列表"""
        # 创建另一个题目和答案
        question2 = Question.objects.create(
            user=self.user,
            title='二元一次方程求解',
            content='求解方程组',
            answer='x=1, y=2',
            solution='代入法求解',
            difficulty=2,
            question_type='解答题'
        )
        answer2 = Answer.objects.create(
            question=question2,
            user=self.user,
            content='这是我的解答过程',
            is_ai_generated=False,
            is_correct=True,
            is_public=True
        )
        
        url = reverse('answers:answer-list')
        response = self.client.get(url, {'question': self.question.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.answer.id)
    
    def test_get_answer_detail(self):
        """测试获取答案详情"""
        url = reverse('answers:answer-detail', kwargs={'pk': self.answer.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['content'],
            '这是我的解答过程：移项得 2x = 10，两边除以2得 x = 5'
        )
        self.assertFalse(response.data['is_ai_generated'])
        self.assertTrue(response.data['is_correct'])
        self.assertTrue(response.data['is_public'])
    
    def test_get_answer_detail_not_found(self):
        """测试获取不存在的答案详情"""
        url = reverse('answers:answer-detail', kwargs={'pk': 999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_answer(self):
        """测试创建答案"""
        url = reverse('answers:answer-list')
        data = {
            'question': self.question.id,
            'content': '新的解答过程',
            'is_ai_generated': False,
            'is_correct': True,
            'is_public': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Answer.objects.count(), 2)
        
        new_answer = Answer.objects.latest('created_at')
        self.assertEqual(new_answer.question, self.question)
        self.assertEqual(new_answer.user, self.user)
        self.assertEqual(new_answer.content, '新的解答过程')
        self.assertFalse(new_answer.is_ai_generated)
        self.assertTrue(new_answer.is_correct)
        self.assertTrue(new_answer.is_public)
    
    def test_create_answer_without_authentication(self):
        """测试未认证创建答案"""
        self.client.credentials()  # 清除认证
        url = reverse('answers:answer-list')
        data = {
            'question': self.question.id,
            'content': '新的解答过程',
            'is_ai_generated': False,
            'is_correct': True,
            'is_public': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Answer.objects.count(), 1)
    
    def test_update_answer(self):
        """测试更新答案"""
        url = reverse('answers:answer-detail', kwargs={'pk': self.answer.id})
        data = {
            'content': '更新后的解答过程',
            'is_ai_generated': True,
            'is_correct': False,
            'is_public': False
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.answer.refresh_from_db()
        self.assertEqual(self.answer.content, '更新后的解答过程')
        self.assertTrue(self.answer.is_ai_generated)
        self.assertFalse(self.answer.is_correct)
        self.assertFalse(self.answer.is_public)
    
    def test_update_answer_of_other_user(self):
        """测试更新其他用户的答案"""
        # 创建其他用户的答案
        other_answer = Answer.objects.create(
            question=self.question,
            user=self.other_user,
            content='其他用户的解答',
            is_ai_generated=False,
            is_correct=True,
            is_public=True
        )
        
        url = reverse('answers:answer-detail', kwargs={'pk': other_answer.id})
        data = {
            'content': '更新后的解答过程',
            'is_ai_generated': True,
            'is_correct': False,
            'is_public': False
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        other_answer.refresh_from_db()
        self.assertEqual(other_answer.content, '其他用户的解答')
    
    def test_delete_answer(self):
        """测试删除答案"""
        url = reverse('answers:answer-detail', kwargs={'pk': self.answer.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Answer.objects.count(), 0)
    
    def test_delete_answer_of_other_user(self):
        """测试删除其他用户的答案"""
        # 创建其他用户的答案
        other_answer = Answer.objects.create(
            question=self.question,
            user=self.other_user,
            content='其他用户的解答',
            is_ai_generated=False,
            is_correct=True,
            is_public=True
        )
        
        url = reverse('answers:answer-detail', kwargs={'pk': other_answer.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Answer.objects.count(), 2)
    
    def test_like_answer(self):
        """测试点赞答案"""
        # 使用其他用户登录
        refresh = RefreshToken.for_user(self.other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('answers:answer-like', kwargs={'pk': self.answer.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(AnswerLike.objects.filter(
            user=self.other_user,
            answer=self.answer
        ).exists())
    
    def test_like_own_answer(self):
        """测试点赞自己的答案"""
        url = reverse('answers:answer-like', kwargs={'pk': self.answer.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(AnswerLike.objects.filter(
            user=self.user,
            answer=self.answer
        ).exists())
    
    def test_unlike_answer(self):
        """测试取消点赞答案"""
        # 先点赞
        AnswerLike.objects.create(
            user=self.other_user,
            answer=self.answer
        )
        
        # 使用其他用户登录
        refresh = RefreshToken.for_user(self.other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        url = reverse('answers:answer-unlike', kwargs={'pk': self.answer.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(AnswerLike.objects.filter(
            user=self.other_user,
            answer=self.answer
        ).exists())
    
    def test_mark_answer_as_correct(self):
        """测试标记答案为正确"""
        # 创建一个错误的答案
        wrong_answer = Answer.objects.create(
            question=self.question,
            user=self.other_user,
            content='错误的解答',
            is_ai_generated=False,
            is_correct=False,
            is_public=True
        )
        
        url = reverse('answers:answer-mark-correct', kwargs={'pk': wrong_answer.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        wrong_answer.refresh_from_db()
        self.assertTrue(wrong_answer.is_correct)
    
    def test_mark_other_user_answer_as_correct(self):
        """测试标记其他用户答案为正确"""
        # 创建其他用户的题目
        other_question = Question.objects.create(
            user=self.other_user,
            title='其他用户的题目',
            content='其他内容',
            answer='其他答案',
            solution='其他解答',
            difficulty=1,
            question_type='填空题'
        )
        
        # 创建该题目的答案
        other_answer = Answer.objects.create(
            question=other_question,
            user=self.other_user,
            content='其他用户的解答',
            is_ai_generated=False,
            is_correct=False,
            is_public=True
        )
        
        url = reverse('answers:answer-mark-correct', kwargs={'pk': other_answer.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        other_answer.refresh_from_db()
        self.assertFalse(other_answer.is_correct)
    
    @patch('apps.answers.views.generate_ai_answer')
    def test_request_ai_answer(self, mock_generate_ai_answer):
        """测试请求AI解答"""
        mock_generate_ai_answer.return_value = {
            'content': 'AI生成的解答过程',
            'confidence': 0.95
        }
        
        url = reverse('answers:answer-ai-answer')
        data = {
            'question': self.question.id
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Answer.objects.count(), 2)
        
        ai_answer = Answer.objects.latest('created_at')
        self.assertEqual(ai_answer.question, self.question)
        self.assertEqual(ai_answer.user, self.user)
        self.assertEqual(ai_answer.content, 'AI生成的解答过程')
        self.assertTrue(ai_answer.is_ai_generated)
        mock_generate_ai_answer.assert_called_once_with(self.question.content)
    
    @patch('apps.answers.views.generate_ai_answer')
    def test_request_ai_answer_with_error(self, mock_generate_ai_answer):
        """测试请求AI解答时出错"""
        mock_generate_ai_answer.side_effect = Exception("AI服务不可用")
        
        url = reverse('answers:answer-ai-answer')
        data = {
            'question': self.question.id
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(Answer.objects.count(), 1)
    
    def test_get_question_answers(self):
        """测试获取题目答案列表"""
        # 创建更多答案
        answer2 = Answer.objects.create(
            question=self.question,
            user=self.other_user,
            content='其他用户的解答',
            is_ai_generated=False,
            is_correct=True,
            is_public=True
        )
        
        url = reverse('answers:answer-question-answers', kwargs={'question_id': self.question.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # 验证答案按创建时间倒序排列
        self.assertEqual(response.data[0]['id'], answer2.id)
        self.assertEqual(response.data[1]['id'], self.answer.id)
    
    def test_get_question_answers_not_found(self):
        """测试获取不存在题目的答案列表"""
        url = reverse('answers:answer-question-answers', kwargs={'question_id': 999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_upload_answer_image(self):
        """测试上传答案图片"""
        # 创建测试图片
        image = Image.new('RGB', (100, 100), 'blue')
        image_file = io.BytesIO()
        image.save(image_file, 'jpeg')
        image_file.seek(0)
        
        url = reverse('answers:answer-upload-image', kwargs={'pk': self.answer.id})
        data = {
            'image': image_file,
            'description': '解答图片',
            'sort_order': 1
        }
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AnswerImage.objects.count(), 1)
        
        answer_image = AnswerImage.objects.first()
        self.assertEqual(answer_image.answer, self.answer)
        self.assertEqual(answer_image.description, '解答图片')
        self.assertEqual(answer_image.sort_order, 1)
    
    def test_create_answer_comment(self):
        """测试创建答案评论"""
        url = reverse('answers:answer-add-comment', kwargs={'pk': self.answer.id})
        data = {
            'content': '很好的解答！'
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AnswerComment.objects.count(), 1)
        
        comment = AnswerComment.objects.first()
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.answer, self.answer)
        self.assertEqual(comment.content, '很好的解答！')
    
    def test_get_answer_comments(self):
        """测试获取答案评论列表"""
        # 创建评论
        comment = AnswerComment.objects.create(
            user=self.other_user,
            answer=self.answer,
            content='很好的解答！'
        )
        
        url = reverse('answers:answer-comments', kwargs={'pk': self.answer.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], comment.id)
        self.assertEqual(response.data[0]['content'], '很好的解答！')
    
    def test_like_answer_comment(self):
        """测试点赞答案评论"""
        # 创建评论
        comment = AnswerComment.objects.create(
            user=self.other_user,
            answer=self.answer,
            content='很好的解答！'
        )
        
        url = reverse('answers:answer-like-comment', kwargs={'pk': self.answer.id, 'comment_id': comment.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(CommentLike.objects.filter(
            user=self.user,
            comment=comment
        ).exists())
    
    def test_unlike_answer_comment(self):
        """测试取消点赞答案评论"""
        # 创建评论
        comment = AnswerComment.objects.create(
            user=self.other_user,
            answer=self.answer,
            content='很好的解答！'
        )
        
        # 先点赞
        CommentLike.objects.create(
            user=self.user,
            comment=comment
        )
        
        url = reverse('answers:answer-unlike-comment', kwargs={'pk': self.answer.id, 'comment_id': comment.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CommentLike.objects.filter(
            user=self.user,
            comment=comment
        ).exists())