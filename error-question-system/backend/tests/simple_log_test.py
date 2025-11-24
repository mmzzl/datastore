"""简单的日志功能测试脚本，不依赖Django的测试框架"""
import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置Django设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

# 导入后立即mock logging配置以避免配置错误
import logging
original_logging_config = logging.config.dictConfig
def mock_dict_config(*args, **kwargs):
    pass
logging.config.dictConfig = mock_dict_config

# 模拟Django环境
class MockRequest:
    def __init__(self, meta=None, user=None):
        self.META = meta or {}
        self.user = user or MagicMock(is_authenticated=False)

class MockUser:
    def __init__(self, id=1, username='testuser'):
        self.id = id
        self.username = username
        self.is_authenticated = True

# 导入我们要测试的函数
def test_get_trace_id():
    """测试get_trace_id函数"""
    print("测试get_trace_id函数...")
    from apps.search.views import get_trace_id
    
    # 测试从请求头获取trace_id
    request = MockRequest(meta={'HTTP_X_TRACE_ID': 'test-trace-id-123'})
    trace_id = get_trace_id(request)
    print(f"从请求头获取trace_id: {trace_id}")
    assert trace_id == 'test-trace-id-123', f"Expected 'test-trace-id-123', got {trace_id}"
    
    # 测试生成新的trace_id
    request = MockRequest(meta={})
    trace_id = get_trace_id(request)
    print(f"生成新的trace_id: {trace_id}")
    assert trace_id is not None and len(trace_id) > 0
    print("✓ get_trace_id测试通过")


def test_get_user_info():
    """测试get_user_info函数"""
    print("测试get_user_info函数...")
    from apps.search.views import get_user_info
    
    # 测试获取已认证用户信息
    user = MockUser(id=1, username='testuser')
    request = MockRequest(user=user)
    user_info = get_user_info(request)
    print(f"已认证用户信息: {user_info}")
    assert user_info['user_id'] == 1
    assert user_info['username'] == 'testuser'
    
    # 测试获取未认证用户信息
    request = MockRequest()
    user_info = get_user_info(request)
    print(f"未认证用户信息: {user_info}")
    assert user_info['user_id'] is None
    print("✓ get_user_info测试通过")


def test_log_search_operation():
    """测试log_search_operation函数"""
    print("测试log_search_operation函数...")
    from apps.search.views import log_search_operation
    
    # Mock logger
    with patch('apps.search.views.logger') as mock_logger:
        # 测试成功日志
        user = MockUser()
        request = MockRequest(
            meta={'REMOTE_ADDR': '127.0.0.1', 'HTTP_USER_AGENT': 'Test Agent'},
            user=user
        )
        
        log_search_operation(
            action="test_action",
            status="success",
            request=request,
            data={'key': 'value'},
            execution_time=100
        )
        
        # 验证logger.info被调用
        assert mock_logger.info.called, "logger.info应该被调用"
        call_args = mock_logger.info.call_args[1]
        print(f"成功日志参数: action={call_args['action']}, status={call_args['status']}")
        assert call_args['action'] == "test_action"
        assert call_args['status'] == "success"
        
        # 测试失败日志
        mock_logger.reset_mock()
        request = MockRequest(meta={'REMOTE_ADDR': '127.0.0.1'})
        
        log_search_operation(
            action="test_action",
            status="failed",
            request=request,
            error={'code': 'TEST_ERROR', 'detail': 'Test error'}
        )
        
        # 验证logger.error被调用
        assert mock_logger.error.called, "logger.error应该被调用"
        call_args = mock_logger.error.call_args[1]
        print(f"失败日志参数: action={call_args['action']}, status={call_args['status']}")
        assert call_args['action'] == "test_action"
        assert call_args['status'] == "failed"
    
    print("✓ log_search_operation测试通过")


def test_search_questions_logging():
    """测试search_questions函数的日志功能"""
    print("测试search_questions函数日志...")
    
    # Mock Question模型和logger
    with patch('apps.search.views.Question'), patch('apps.search.views.logger') as mock_logger:
        from apps.search.views import search_questions
        
        # 执行搜索
        result = search_questions(query='test')
        
        # 验证日志调用
        assert mock_logger.debug.called, "logger.debug应该被调用"
        assert mock_logger.info.called or mock_logger.error.called, "应该调用info或error日志"
        
        debug_args = mock_logger.debug.call_args[1]
        print(f"search_questions开始日志: action={debug_args['action']}, query={debug_args['query']}")
        assert debug_args['action'] == "search_questions"
        assert debug_args['query'] == "test"
    
    print("✓ search_questions日志测试通过")


if __name__ == '__main__':
    print("开始日志功能测试...\n")
    
    try:
        test_get_trace_id()
        print()
        test_get_user_info()
        print()
        test_log_search_operation()
        print()
        test_search_questions_logging()
        print()
        print("🎉 所有日志功能测试通过！")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
