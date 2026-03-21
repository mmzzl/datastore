import unittest
import json
import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from unittest.mock import Mock, patch
from scrapy.http import HtmlResponse
from internal.spider.eastmoney_spider import EastMoneyNewsSpider

class TestEastMoneyNewsSpider(unittest.TestCase):
    def setUp(self):
        self.spider = EastMoneyNewsSpider()
    
    def test_parse_jsonp_response(self):
        """测试解析JSONP格式的响应"""
        jsonp_response = 'jQuery123({"code":"1","data":{"fastNewsList":[],"total":0},"message":"success"})'
        expected = {"code":"1","data":{"fastNewsList":[],"total":0},"message":"success"}
        result = self.spider._parse_jsonp(jsonp_response)
        self.assertEqual(result, expected)
    
    def test_extract_news_items(self):
        """测试从响应中提取新闻项"""
        mock_response = Mock()
        mock_response.text = 'jQuery123({"code":"1","data":{"fastNewsList":[{"code":"test123","title":"Test News","summary":"Test Summary","showTime":"2026-02-25 10:00:00","stockList":[],"image":[],"pinglun_Num":0,"share":0,"realSort":"123456789","titleColor":3}],"total":1},"message":"success"})'
        
        items = list(self.spider.parse(mock_response))
        self.assertEqual(len(items), 1)
        item = items[0]
        self.assertEqual(item['code'], 'test123')
        self.assertEqual(item['title'], 'Test News')
        self.assertEqual(item['summary'], 'Test Summary')
        self.assertEqual(item['showTime'], '2026-02-25 10:00:00')
    
    def test_parse_count_response(self):
        """测试解析新闻计数响应"""
        mock_response = Mock()
        mock_response.text = 'jQuery123({"code":"1","data":{"count":5},"message":"success"})'
        
        count = self.spider._parse_count_response(mock_response)
        self.assertEqual(count, 5)

if __name__ == '__main__':
    unittest.main()
