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

from apps.categories.models import Category, QuestionCategory
from apps.categories.views import CategoryViewSet
from apps.questions.models import Question, Subject, KnowledgePoint

User = get_user_model()


class CategoryModelTests(TestCase):
    """分类模型测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.parent_category = Category.objects.create(
            name='数学',
            description='数学相关错题',
            color='#FF5722',
            icon='math',
            sort_order=1,
            is_active=True
        )
        self.child_category = Category.objects.create(
            name='代数',
            description='代数相关错题',
            parent=self.parent_category,
            color='#2196F3',
            icon='algebra',
            sort_order=1,
            is_active=True
        )
    
    def test_category_creation(self):
        """测试分类创建"""
        self.assertEqual(self.parent_category.name, '数学')
        self.assertEqual(self.parent_category.description, '数学相关错题')
        self.assertEqual(self.parent_category.color, '#FF5722')
        self.assertEqual(self.parent_category.icon, 'math')
        self.assertEqual(self.parent_category.sort_order, 1)
        self.assertTrue(self.parent_category.is_active)
        self.assertIsNone(self.parent_category.parent)
    
    def test_child_category_creation(self):
        """测试子分类创建"""
        self.assertEqual(self.child_category.name, '代数')
        self.assertEqual(self.child_category.description, '代数相关错题')
        self.assertEqual(self.child_category.color, '#2196F3')
        self.assertEqual(self.child_category.icon, 'algebra')
        self.assertEqual(self.child_category.sort_order, 1)
        self.assertTrue(self.child_category.is_active)
        self.assertEqual(self.child_category.parent, self.parent_category)
    
    def test_category_str_representation(self):
        """测试分类字符串表示"""
        self.assertEqual(str(self.parent_category), '数学')
        self.assertEqual(str(self.child_category), '数学 - 代数')
    
    def test_category_level_property(self):
        """测试分类级别属性"""
        self.assertEqual(self.parent_category.level, 1)
        self.assertEqual(self.child_category.level, 2)
    
    def test_category_has_children_property(self):
        """测试分类是否有子分类属性"""
        self.assertTrue(self.parent_category.has_children)
        self.assertFalse(self.child_category.has_children)
    
    def test_category_question_count_property(self):
        """测试分类题目数量属性"""
        self.assertEqual(self.parent_category.question_count, 0)
        self.assertEqual(self.child_category.question_count, 0)
        
        # 创建题目并关联到子分类
        subject = Subject.objects.create(
            name='数学',
            description='数学学科',
            sort_order=1,
            is_active=True
        )
        knowledge_point = KnowledgePoint.objects.create(
            subject=subject,
            name='代数',
            description='代数知识点',
            level=1,
            sort_order=1,
            is_active=True
        )
        question = Question.objects.create(
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
        QuestionCategory.objects.create(
            question=question,
            category=self.child_category
        )
        
        # 重新获取分类以触发属性计算
        parent_category = Category.objects.get(id=self.parent_category.id)
        child_category = Category.objects.get(id=self.child_category.id)
        
        self.assertEqual(parent_category.question_count, 1)
        self.assertEqual(child_category.question_count, 1)
    
    def test_category_get_children(self):
        """测试获取子分类"""
        children = self.parent_category.get_children()
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0], self.child_category)
    
    def test_category_get_siblings(self):
        """测试获取同级分类"""
        # 创建另一个同级分类
        sibling_category = Category.objects.create(
            name='几何',
            description='几何相关错题',
            parent=self.parent_category,
            color='#4CAF50',
            icon='geometry',
            sort_order=2,
            is_active=True
        )
        
        siblings = self.child_category.get_siblings()
        self.assertEqual(len(siblings), 1)
        self.assertEqual(siblings[0], sibling_category)
    
    def test_category_get_all_children(self):
        """测试获取所有子分类（包括子分类的子分类）"""
        # 创建三级分类
        grandchild_category = Category.objects.create(
            name='一元一次方程',
            description='一元一次方程错题',
            parent=self.child_category,
            color='#9C27B0',
            icon='linear_equation',
            sort_order=1,
            is_active=True
        )
        
        all_children = self.parent_category.get_all_children()
        self.assertEqual(len(all_children), 2)
        self.assertIn(self.child_category, all_children)
        self.assertIn(grandchild_category, all_children)
    
    def test_category_get_root(self):
        """测试获取根分类"""
        root = self.child_category.get_root()
        self.assertEqual(root, self.parent_category)
        root_same = self.parent_category.get_root()
        self.assertEqual(root_same, self.parent_category)
    
    def test_category_get_path(self):
        """测试获取分类路径"""
        path = self.child_category.get_path()
        self.assertEqual(len(path), 2)
        self.assertEqual(path[0], self.parent_category)
        self.assertEqual(path[1], self.child_category)
    
    def test_category_is_descendant_of(self):
        """测试是否为某个分类的后代"""
        self.assertTrue(self.child_category.is_descendant_of(self.parent_category))
        self.assertFalse(self.parent_category.is_descendant_of(self.child_category))
        self.assertFalse(self.parent_category.is_descendant_of(self.parent_category))
    
    def test_category_is_ancestor_of(self):
        """测试是否为某个分类的祖先"""
        self.assertTrue(self.parent_category.is_ancestor_of(self.child_category))
        self.assertFalse(self.child_category.is_ancestor_of(self.parent_category))
        self.assertFalse(self.parent_category.is_ancestor_of(self.parent_category))


class QuestionCategoryModelTests(TestCase):
    """题目分类关联模型测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.category = Category.objects.create(
            name='数学',
            description='数学相关错题',
            color='#FF5722',
            icon='math',
            sort_order=1,
            is_active=True
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
        self.question_category = QuestionCategory.objects.create(
            question=self.question,
            category=self.category
        )
    
    def test_question_category_creation(self):
        """测试题目分类关联创建"""
        self.assertEqual(self.question_category.question, self.question)
        self.assertEqual(self.question_category.category, self.category)
    
    def test_question_category_str_representation(self):
        """测试题目分类关联字符串表示"""
        expected_str = f"{self.question.title} - {self.category.name}"
        self.assertEqual(str(self.question_category), expected_str)
    
    def test_question_category_unique_constraint(self):
        """测试题目分类关联唯一约束"""
        # 尝试创建相同的关联记录
        with self.assertRaises(Exception):  # 应该抛出IntegrityError或类似异常
            QuestionCategory.objects.create(
                question=self.question,
                category=self.category
            )


class CategoryViewTests(APITestCase):
    """分类视图测试"""
    
    def setUp(self):
        """测试数据初始化"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.parent_category = Category.objects.create(
            name='数学',
            description='数学相关错题',
            color='#FF5722',
            icon='math',
            sort_order=1,
            is_active=True
        )
        self.child_category = Category.objects.create(
            name='代数',
            description='代数相关错题',
            parent=self.parent_category,
            color='#2196F3',
            icon='algebra',
            sort_order=1,
            is_active=True
        )
        
        # 认证用户
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_get_categories_list(self):
        """测试获取分类列表"""
        url = reverse('categories:category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        # 验证返回的分类数据
        names = [category['name'] for category in response.data['results']]
        self.assertIn('数学', names)
        self.assertIn('代数', names)
    
    def test_get_categories_list_filtered_by_parent(self):
        """测试按父分类过滤分类列表"""
        url = reverse('categories:category-list')
        response = self.client.get(url, {'parent': self.parent_category.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], '代数')
    
    def test_get_categories_list_filtered_by_level(self):
        """测试按级别过滤分类列表"""
        url = reverse('categories:category-list')
        response = self.client.get(url, {'level': 1})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], '数学')
    
    def test_get_categories_list_filtered_by_is_active(self):
        """测试按激活状态过滤分类列表"""
        # 创建一个非激活分类
        inactive_category = Category.objects.create(
            name='非激活分类',
            description='非激活分类描述',
            color='#9E9E9E',
            icon='inactive',
            sort_order=2,
            is_active=False
        )
        
        url = reverse('categories:category-list')
        response = self.client.get(url, {'is_active': True})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
        
        names = [category['name'] for category in response.data['results']]
        self.assertIn('数学', names)
        self.assertIn('代数', names)
        self.assertNotIn('非激活分类', names)
    
    def test_get_category_detail(self):
        """测试获取分类详情"""
        url = reverse('categories:category-detail', kwargs={'pk': self.parent_category.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], '数学')
        self.assertEqual(response.data['description'], '数学相关错题')
        self.assertEqual(response.data['color'], '#FF5722')
        self.assertEqual(response.data['icon'], 'math')
        self.assertEqual(response.data['sort_order'], 1)
        self.assertTrue(response.data['is_active'])
        self.assertIsNone(response.data['parent'])
        self.assertEqual(response.data['level'], 1)
        self.assertTrue(response.data['has_children'])
        self.assertEqual(response.data['question_count'], 0)
    
    def test_get_category_detail_not_found(self):
        """测试获取不存在的分类详情"""
        url = reverse('categories:category-detail', kwargs={'pk': 999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_category(self):
        """测试创建分类"""
        url = reverse('categories:category-list')
        data = {
            'name': '物理',
            'description': '物理相关错题',
            'color '#4CAF50',
            'icon': 'physics',
            'sort_order': 2,
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 3)
        
        new_category = Category.objects.latest('created_at')
        self.assertEqual(new_category.name, '物理')
        self.assertEqual(new_category.description, '物理相关错题')
        self.assertEqual(new_category.color, '#4CAF50')
        self.assertEqual(new_category.icon, 'physics')
        self.assertEqual(new_category.sort_order, 2)
        self.assertTrue(new_category.is_active)
        self.assertIsNone(new_category.parent)
    
    def test_create_child_category(self):
        """测试创建子分类"""
        url = reverse('categories:category-list')
        data = {
            'name': '几何',
            'description': '几何相关错题',
            'color': '#9C27B0',
            'icon': 'geometry',
            'sort_order': 2,
            'is_active': True,
            'parent': self.parent_category.id
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Category.objects.count(), 3)
        
        new_category = Category.objects.latest('created_at')
        self.assertEqual(new_category.name, '几何')
        self.assertEqual(new_category.parent, self.parent_category)
        self.assertEqual(new_category.level, 2)
    
    def test_create_category_without_authentication(self):
        """测试未认证创建分类"""
        self.client.credentials()  # 清除认证
        url = reverse('categories:category-list')
        data = {
            'name': '物理',
            'description': '物理相关错题',
            'color': '#4CAF50',
            'icon': 'physics',
            'sort_order': 2,
            'is_active': True
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Category.objects.count(), 2)
    
    def test_update_category(self):
        """测试更新分类"""
        url = reverse('categories:category-detail', kwargs={'pk': self.parent_category.id})
        data = {
            'name': '数学（更新）',
            'description': '数学相关错题（更新）',
            'color': '#FF9800',
            'icon': 'math_updated',
            'sort_order': 3,
            'is_active': False
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.parent_category.refresh_from_db()
        self.assertEqual(self.parent_category.name, '数学（更新）')
        self.assertEqual(self.parent_category.description, '数学相关错题（更新）')
        self.assertEqual(self.parent_category.color, '#FF9800')
        self.assertEqual(self.parent_category.icon, 'math_updated')
        self.assertEqual(self.parent_category.sort_order, 3)
        self.assertFalse(self.parent_category.is_active)
    
    def test_update_category_parent(self):
        """测试更新分类父分类"""
        # 创建另一个父分类
        other_parent = Category.objects.create(
            name='物理',
            description='物理相关错题',
            color='#4CAF50',
            icon='physics',
            sort_order=2,
            is_active=True
        )
        
        url = reverse('categories:category-detail', kwargs={'pk': self.child_category.id})
        data = {
            'name': '代数',
            'description': '代数相关错题',
            'color': '#2196F3',
            'icon': 'algebra',
            'sort_order': 1,
            'is_active': True,
            'parent': other_parent.id
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.child_category.refresh_from_db()
        self.assertEqual(self.child_category.parent, other_parent)
        self.assertEqual(self.child_category.level, 2)
    
    def test_update_category_parent_to_itself(self):
        """测试将分类的父分类设置为自己"""
        url = reverse('categories:category-detail', kwargs={'pk': self.parent_category.id})
        data = {
            'name': '数学',
            'description': '数学相关错题',
            'color': '#FF5722',
            'icon': 'math',
            'sort_order': 1,
            'is_active': True,
            'parent': self.parent_category.id
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.parent_category.refresh_from_db()
        self.assertIsNone(self.parent_category.parent)
    
    def test_update_category_parent_to_descendant(self):
        """测试将分类的父分类设置为自己的后代"""
        url = reverse('categories:category-detail', kwargs={'pk': self.parent_category.id})
        data = {
            'name': '数学',
            'description': '数学相关错题',
            'color': '#FF5722',
            'icon': 'math',
            'sort_order': 1,
            'is_active': True,
            'parent': self.child_category.id
        }
        response = self.client.put(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.parent_category.refresh_from_db()
        self.assertIsNone(self.parent_category.parent)
    
    def test_delete_category_without_children(self):
        """测试删除没有子分类的分类"""
        url = reverse('categories:category-detail', kwargs={'pk': self.child_category.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Category.objects.count(), 1)
        self.assertFalse(Category.objects.filter(id=self.child_category.id).exists())
    
    def test_delete_category_with_children(self):
        """测试删除有子分类的分类"""
        url = reverse('categories:category-detail', kwargs={'pk': self.parent_category.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Category.objects.count(), 2)
        self.assertTrue(Category.objects.filter(id=self.parent_category.id).exists())
    
    def test_get_category_tree(self):
        """测试获取分类树"""
        url = reverse('categories:category-tree')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        
        # 验证树结构
        root = response.data[0]
        self.assertEqual(root['id'], self.parent_category.id)
        self.assertEqual(root['name'], '数学')
        self.assertEqual(len(root['children']), 1)
        
        child = root['children'][0]
        self.assertEqual(child['id'], self.child_category.id)
        self.assertEqual(child['name'], '代数')
        self.assertEqual(len(child['children']), 0)
    
    def test_get_category_tree_filtered_by_is_active(self):
        """测试按激活状态过滤获取分类树"""
        # 创建一个非激活分类
        inactive_category = Category.objects.create(
            name='非激活分类',
            description='非激活分类描述',
            color='#9E9E9E',
            icon='inactive',
            sort_order=2,
            is_active=False
        )
        
        url = reverse('categories:category-tree')
        response = self.client.get(url, {'is_active': True})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.parent_category.id)
        
        # 验证非激活分类不在树中
        category_ids = []
        def collect_ids(nodes):
            for node in nodes:
                category_ids.append(node['id'])
                collect_ids(node['children'])
        
        collect_ids(response.data)
        self.assertNotIn(inactive_category.id, category_ids)
    
    def test_get_category_statistics(self):
        """测试获取分类统计信息"""
        # 创建题目并关联到分类
        subject = Subject.objects.create(
            name='数学',
            description='数学学科',
            sort_order=1,
            is_active=True
        )
        knowledge_point = KnowledgePoint.objects.create(
            subject=subject,
            name='代数',
            description='代数知识点',
            level=1,
            sort_order=1,
            is_active=True
        )
        question = Question.objects.create(
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
        QuestionCategory.objects.create(
            question=question,
            category=self.child_category
        )
        
        url = reverse('categories:category-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # 验证统计信息
        parent_stats = next(stat for stat in response.data if stat['id'] == self.parent_category.id)
        child_stats = next(stat for stat in response.data if stat['id'] == self.child_category.id)
        
        self.assertEqual(parent_stats['question_count'], 1)
        self.assertEqual(child_stats['question_count'], 1)
        self.assertEqual(parent_stats['children_count'], 1)
        self.assertEqual(child_stats['children_count'], 0)
    
    def test_get_category_questions(self):
        """测试获取分类下的题目"""
        # 创建题目并关联到分类
        subject = Subject.objects.create(
            name='数学',
            description='数学学科',
            sort_order=1,
            is_active=True
        )
        knowledge_point = KnowledgePoint.objects.create(
            subject=subject,
            name='代数',
            description='代数知识点',
            level=1,
            sort_order=1,
            is_active=True
        )
        question = Question.objects.create(
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
        QuestionCategory.objects.create(
            question=question,
            category=self.child_category
        )
        
        url = reverse('categories:category-questions', kwargs={'pk': self.parent_category.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], question.id)
    
    def test_get_category_questions_include_children(self):
        """测试获取分类下的题目（包括子分类）"""
        # 创建题目并关联到子分类
        subject = Subject.objects.create(
            name='数学',
            description='数学学科',
            sort_order=1,
            is_active=True
        )
        knowledge_point = KnowledgePoint.objects.create(
            subject=subject,
            name='代数',
            description='代数知识点',
            level=1,
            sort_order=1,
            is_active=True
        )
        question = Question.objects.create(
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
        QuestionCategory.objects.create(
            question=question,
            category=self.child_category
        )
        
        url = reverse('categories:category-questions', kwargs={'pk': self.parent_category.id})
        response = self.client.get(url, {'include_children': True})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], question.id)
    
    def test_add_question_to_category(self):
        """测试将题目添加到分类"""
        # 创建题目
        subject = Subject.objects.create(
            name='数学',
            description='数学学科',
            sort_order=1,
            is_active=True
        )
        knowledge_point = KnowledgePoint.objects.create(
            subject=subject,
            name='代数',
            description='代数知识点',
            level=1,
            sort_order=1,
            is_active=True
        )
        question = Question.objects.create(
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
        
        url = reverse('categories:category-add-question', kwargs={'pk': self.parent_category.id})
        data = {
            'question': question.id
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(QuestionCategory.objects.filter(
            question=question,
            category=self.parent_category
        ).exists())
    
    def test_remove_question_from_category(self):
        """测试将题目从分类中移除"""
        # 创建题目并关联到分类
        subject = Subject.objects.create(
            name='数学',
            description='数学学科',
            sort_order=1,
            is_active=True
        )
        knowledge_point = KnowledgePoint.objects.create(
            subject=subject,
            name='代数',
            description='代数知识点',
            level=1,
            sort_order=1,
            is_active=True
        )
        question = Question.objects.create(
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
        question_category = QuestionCategory.objects.create(
            question=question,
            category=self.parent_category
        )
        
        url = reverse('categories:category-remove-question', kwargs={'pk': self.parent_category.id})
        data = {
            'question': question.id
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(QuestionCategory.objects.filter(
            question=question,
            category=self.parent_category
        ).exists())