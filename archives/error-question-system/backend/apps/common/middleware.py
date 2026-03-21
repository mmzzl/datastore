import logging
import time
import structlog
from django.utils.deprecation import MiddlewareMixin

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    请求日志中间件，记录所有API请求的详细信息
    """
    
    def process_request(self, request):
        """处理请求开始"""
        request.start_time = time.time()
        
        # 记录请求信息
        request_data = {
            'method': request.method,
            'path': request.path,
            'user_id': request.user.id if hasattr(request, 'user') and request.user.is_authenticated else None,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
        
        # 记录请求参数（仅限GET和POST）
        if request.method == 'GET':
            request_data['params'] = dict(request.GET)
        elif request.method == 'POST':
            try:
                request_data['body'] = request.body.decode('utf-8')[:500]  # 限制长度
            except UnicodeDecodeError:
                request_data['body'] = '[Binary Data]'
        
        # 存储请求数据，以便在process_response中使用
        request._logging_data = request_data
        
        logger.info("API请求开始", **request_data)
        return None
    
    def process_response(self, request, response):
        """处理请求结束"""
        if hasattr(request, 'start_time') and hasattr(request, '_logging_data'):
            # 计算请求处理时间
            duration = time.time() - request.start_time
            
            # 记录响应信息
            response_data = {
                **request._logging_data,
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2),
            }
            
            # 根据状态码确定日志级别
            if response.status_code >= 500:
                logger.error("API请求完成(服务器错误)", **response_data)
            elif response.status_code >= 400:
                logger.warning("API请求完成(客户端错误)", **response_data)
            else:
                logger.info("API请求完成", **response_data)
        
        return response
    
    def _get_client_ip(self, request):
        """获取客户端IP地址"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip