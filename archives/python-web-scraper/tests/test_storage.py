import unittest
import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unittest.mock import Mock, patch
from internal.storage.mongo_storage import MongoStorage

class TestMongoStorage(unittest.TestCase):
    def setUp(self):
        self.storage = MongoStorage()
    
    @patch('pymongo.MongoClient')
    def test_init_connection(self, mock_client):
        """测试初始化mongodb连接"""
        mock_db = Mock()
        mock_client.return_value.__getitem__.return_value = mock_db
        mock_collection = Mock()
        mock_db.__getitem__.return_value = mock_collection
        
        storage = MongoStorage()
        mock_client.assert_called_once()
        mock_db.__getitem__.assert_called_once_with('news')
    
    @patch('pymongo.MongoClient')
    def test_save_news(self, mock_client):
        """测试保存新闻"""
        mock_collection = Mock()
        mock_collection.insert_one.return_value = Mock(inserted_id='test_id')
        mock_db = Mock()
        mock_db.__getitem__.return_value = mock_collection
        mock_client.return_value.__getitem__.return_value = mock_db
        
        storage = MongoStorage()
        news_item = {
            'code': 'test123',
            'title': 'Test News',
            'summary': 'Test Summary',
            'showTime': '2026-02-25 10:00:00'
        }
        result = storage.save_news(news_item)
        mock_collection.insert_one.assert_called_once_with(news_item)
        self.assertEqual(result, 'test_id')
    
    @patch('pymongo.MongoClient')
    def test_check_duplicate(self, mock_client):
        """测试检查重复新闻"""
        mock_collection = Mock()
        # 模拟已存在的新闻
        mock_collection.find_one.return_value = {'code': 'test123'}
        mock_db = Mock()
        mock_db.__getitem__.return_value = mock_collection
        mock_client.return_value.__getitem__.return_value = mock_db
        
        storage = MongoStorage()
        result = storage.check_duplicate('test123')
        self.assertTrue(result)
        
        # 模拟不存在的新闻
        mock_collection.find_one.return_value = None
        result = storage.check_duplicate('test456')
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
