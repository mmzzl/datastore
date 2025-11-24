# 错题本系统 日志设计文档

## 1. 日志系统架构概述

### 1.1 日志框架选择
- 后端：使用Python标准库`logging`结合`structlog`实现结构化日志
- 前端：使用uni-app内置日志机制结合自定义日志封装

### 1.2 日志级别规划
| 级别 | 使用场景 | 示例 |
| ----- | ---------------- | ------------- |
| ERROR | 系统错误、业务异常 | 数据库连接失败、OCR识别失败 |
| WARN  | 预期内的异常 | 参数校验失败、文件格式不支持 |
| INFO  | 业务关键流程 | 用户登录成功、错题上传成功 |
| DEBUG | 调试信息 | 方法入参出参、API请求响应 |
| TRACE | 详细执行轨迹 | 循环内部状态、算法中间步骤 |

### 1.3 日志分类策略
- **业务日志**：用户操作、业务流程
- **系统日志**：系统启动、服务调用、资源使用
- **安全日志**：登录认证、权限验证、敏感操作
- **性能日志**：接口响应时间、资源消耗、瓶颈分析

## 2. 日志配置规范

### 2.1 后端日志配置
```python
# 日志配置要求
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/error_question.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'json'
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/error_question_error.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 5,
            'formatter': 'json'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'error_question': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}
```

### 2.2 前端日志配置
```javascript
// 前端日志配置
const logConfig = {
  level: process.env.NODE_ENV === 'production' ? 'info' : 'debug',
  output: {
    console: true,
    file: false, // 前端不写文件，发送到后端
    remote: true // 发送到后端日志收集接口
  },
  format: {
    timestamp: true,
    json: true,
    includeUserInfo: true
  }
}
```

## 3. 日志内容规范

### 3.1 必须记录的关键节点
- 系统启动/关闭
- 用户认证和授权
- 外部接口调用（请求/响应）
- 业务关键操作（错题录入、解答、分类、检索）
- 异常错误发生
- 性能关键路径
- 安全相关事件

### 3.2 日志内容标准
- **入口日志**：方法名 + 输入参数（脱敏后）
- **出口日志**：方法名 + 执行结果 + 耗时
- **异常日志**：错误堆栈 + 上下文信息
- **业务日志**：操作类型 + 业务ID + 操作结果

### 3.3 结构化日志字段
```json
{
  "timestamp": "2025-11-22T10:30:45.123Z",
  "level": "INFO",
  "logger": "error_question.views.upload",
  "message": "错题上传成功",
  "traceId": "abc123def456",
  "userId": "user_001",
  "sessionId": "session_789",
  "requestId": "req_456",
  "module": "错题录入",
  "action": "upload",
  "duration": 1250,
  "status": "success",
  "metadata": {
    "questionId": "q_12345",
    "subject": "数学",
    "fileSize": "2.3MB"
  }
}
```

## 4. 日志使用示例

### 4.1 业务操作日志
```python
import logging
import structlog
import time
import uuid

logger = structlog.get_logger('error_question.upload')

def upload_question(request):
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    
    logger.info(
        "错题上传开始",
        trace_id=trace_id,
        user_id=request.user.id,
        file_name=request.FILES['file'].name,
        file_size=request.FILES['file'].size
    )
    
    try:
        # 处理文件上传
        question_id = process_upload(request.FILES['file'])
        
        duration = int((time.time() - start_time) * 1000)
        logger.info(
            "错题上传成功",
            trace_id=trace_id,
            user_id=request.user.id,
            question_id=question_id,
            duration=duration
        )
        
        return JsonResponse({"status": "success", "question_id": question_id})
        
    except Exception as e:
        duration = int((time.time() - start_time) * 1000)
        logger.error(
            "错题上传失败",
            trace_id=trace_id,
            user_id=request.user.id,
            error=str(e),
            duration=duration,
            exc_info=True
        )
        
        return JsonResponse({"status": "error", "message": "上传失败"}, status=500)
```

### 4.2 前端日志示例
```javascript
// 前端日志封装
class Logger {
  constructor(config) {
    this.config = config;
    this.traceId = this.generateTraceId();
  }
  
  generateTraceId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }
  
  log(level, message, metadata = {}) {
    const logEntry = {
      timestamp: new Date().toISOString(),
      level: level.toUpperCase(),
      logger: 'error_question.uniapp',
      message: message,
      traceId: this.traceId,
      userId: this.getUserId(),
      ...metadata
    };
    
    // 控制台输出
    if (this.config.output.console) {
      console[level](logEntry);
    }
    
    // 发送到后端
    if (this.config.output.remote) {
      this.sendToServer(logEntry);
    }
  }
  
  info(message, metadata) {
    this.log('info', message, metadata);
  }
  
  error(message, metadata) {
    this.log('error', message, metadata);
  }
  
  // 其他方法...
}

// 使用示例
const logger = new Logger(logConfig);

function uploadQuestion(file) {
  logger.info('开始上传错题', {
    module: '错题录入',
    action: 'upload',
    fileName: file.name,
    fileSize: file.size
  });
  
  // 上传逻辑...
  
  .then(response => {
    logger.info('错题上传成功', {
      questionId: response.data.question_id,
      status: 'success'
    });
  })
  .catch(error => {
    logger.error('错题上传失败', {
      error: error.message,
      status: 'error'
    });
  });
}
```

## 5. 敏感信息处理

### 5.1 敏感信息识别
- 用户密码
- 身份证号
- 手机号码
- 银行卡号
- Token和密钥

### 5.2 脱敏处理规则
```python
import re

def mask_sensitive_data(data):
    """脱敏处理敏感信息"""
    if isinstance(data, str):
        # 手机号脱敏
        data = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', data)
        # 身份证号脱敏
        data = re.sub(r'(\d{6})\d{8}(\d{4})', r'\1********\2', data)
        # 银行卡号脱敏
        data = re.sub(r'(\d{4})\d+(\d{4})', r'\1****\2', data)
    return data
```

## 6. 日志性能优化

### 6.1 异步日志
```python
import logging
from logging.handlers import QueueHandler, QueueListener
import queue

# 创建队列
log_queue = queue.Queue(-1)

# 创建队列处理器
queue_handler = QueueHandler(log_queue)

# 创建文件处理器
file_handler = logging.handlers.RotatingFileHandler(
    'logs/error_question.log',
    maxBytes=1024*1024*10,  # 10MB
    backupCount=5
)

# 创建监听器
listener = QueueListener(log_queue, file_handler)
listener.start()

# 配置日志器使用队列处理器
logger = logging.getLogger('error_question')
logger.addHandler(queue_handler)
```

### 6.2 日志缓冲
```python
# 批量写入日志
class BufferedFileHandler(logging.handlers.RotatingFileHandler):
    def __init__(self, filename, buffer_size=100, **kwargs):
        super().__init__(filename, **kwargs)
        self.buffer = []
        self.buffer_size = buffer_size
        
    def emit(self, record):
        self.buffer.append(self.format(record))
        if len(self.buffer) >= self.buffer_size:
            self.flush_buffer()
            
    def flush_buffer(self):
        if self.buffer:
            with open(self.baseFilename, 'a') as f:
                f.write('\n'.join(self.buffer) + '\n')
            self.buffer = []
```

## 7. 日志监控与告警

### 7.1 错误日志监控
```python
import logging.handlers

class ErrorMonitoringHandler(logging.handlers.SMTPHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_count = 0
        self.last_error_time = None
        
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            self.error_count += 1
            current_time = time.time()
            
            # 如果5分钟内错误超过10次，发送告警
            if (self.last_error_time and 
                current_time - self.last_error_time < 300 and 
                self.error_count >= 10):
                super().emit(record)
                self.error_count = 0
                
            self.last_error_time = current_time
```

## 8. 日志测试验证

### 8.1 单元测试
```python
import unittest
import logging
from io import StringIO

class TestLogging(unittest.TestCase):
    def setUp(self):
        self.log_stream = StringIO()
        self.handler = logging.StreamHandler(self.log_stream)
        self.logger = logging.getLogger('test_logger')
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.INFO)
        
    def test_log_format(self):
        self.logger.info("Test message", extra={'user_id': '123'})
        log_output = self.log_stream.getvalue()
        self.assertIn('user_id', log_output)
        
    def test_sensitive_data_masking(self):
        from error_question.utils.logging import mask_sensitive_data
        masked = mask_sensitive_data("手机号:13812345678")
        self.assertEqual(masked, "手机号:138****5678")
```

### 8.2 集成测试
```python
def test_trace_id_propagation():
    """测试traceId在调用链中的传递"""
    trace_id = str(uuid.uuid4())
    
    # 模拟API调用
    response = client.post('/api/questions/upload', 
                          data={'file': test_file},
                          headers={'X-Trace-Id': trace_id})
    
    # 验证日志中包含正确的traceId
    log_entries = get_log_entries()
    upload_logs = [log for log in log_entries if 'upload' in log['message']]
    
    for log in upload_logs:
        assert log['traceId'] == trace_id
```

## 9. 日志分析与应用

### 9.1 业务指标提取
- 用户活跃度：通过登录日志分析
- 功能使用率：通过功能操作日志统计
- 错误率：通过错误日志计算
- 性能指标：通过耗时日志分析

### 9.2 故障排查支持
- 提供完整的调用链追踪
- 记录关键业务流程状态
- 保留异常上下文信息
- 支持日志全文检索和过滤

## 10. 日志合规与安全

### 10.1 数据保护
- 遵循GDPR等隐私保护法规
- 实施数据最小化原则
- 提供数据删除和修改机制
- 定期审计日志访问记录

### 10.2 日志保留策略
- 业务日志：保留1年
- 安全日志：保留3年
- 系统日志：保留6个月
- 错误日志：保留2年

---

**文档版本**: v1.0.0  
**创建日期**: 2025-11-22  
**最后更新**: 2025-11-22  
**作者**: 日志系统设计师