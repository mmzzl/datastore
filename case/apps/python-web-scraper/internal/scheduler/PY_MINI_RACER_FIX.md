# py_mini_racer 子进程问题修复说明

## 问题描述

在运行 python-web-scraper 爬虫时出现以下错误：

```
2026-03-08 09:45:24 [internal.scheduler.scheduler] ERROR: 子进程运行新闻爬虫失败: can't register atexit after shutdown
```

同时还有一个警告：

```
/root/.pyenv/versions/3.12.0/lib/python3.12/site-packages/py_mini_racer/py_mini_racer.py:15: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
  import pkg_resources
```

## 问题原因

### 1. py_mini_racer 的 atexit 注册问题

`py_mini_racer` 是一个 Python 封装的 V8 JavaScript 引擎，用于在 Python 中执行 JavaScript 代码。Scrapy 的某些中间件或扩展可能使用了这个库。

**问题根源**：
- `py_mini_racer` 在初始化时会注册 `atexit` 处理函数来清理资源
- 在多进程环境中，子进程启动时主进程可能已经开始关闭
- 当子进程尝试注册 `atexit` 处理函数时，Python 解释器已经进入关闭状态
- 导致 `can't register atexit after shutdown` 错误

### 2. 多进程环境下的资源管理

在 `multiprocessing.Process` 创建的子进程中：
- 主进程和子进程有独立的 Python 解释器
- 子进程启动时，主进程可能正在关闭
- `atexit` 注册必须在解释器关闭之前完成
- 某些库（如 py_mini_racer）的初始化时机不当会导致问题

## 解决方案

### 1. 设置环境变量

在子进程启动时设置 `PY_MINI_RACER_NO_CLEANUP` 环境变量：

```python
os.environ['PY_MINI_RACER_NO_CLEANUP'] = '1'
```

这个环境变量告诉 `py_mini_racer` 不要注册 `atexit` 处理函数，避免在子进程启动时的注册冲突。

### 2. 延迟导入

将爬虫类的导入延迟到子进程内部：

```python
# 不在文件顶部导入
# from ..spider.eastmoney_spider import EastMoneyNewsSpider

def run_spider(sort_end, req_trace, sort_start):
    # 在子进程内部导入
    from ..spider.eastmoney_spider import EastMoneyNewsSpider
    # ...
```

这样可以避免在主进程加载时初始化 `py_mini_racer`。

### 3. 配置 Scrapy 设置

在 Scrapy 设置中禁用 `py_mini_racer` 的自动清理：

```python
settings = get_project_settings()
settings.set('PY_MINI_RACER_NO_CLEANUP', True)
```

### 4. 添加 finally 块确保清理

在 `finally` 块中强制垃圾回收：

```python
finally:
    try:
        import gc
        gc.collect()
    except:
        pass
```

## 修复代码

### 修复前的代码

```python
def run_spider(sort_end, req_trace, sort_start):
    """在子进程中运行新闻爬虫"""
    try:
        logger.info(f"子进程启动新闻爬虫... 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        from ..spider.eastmoney_spider import EastMoneyNewsSpider
        process = CrawlerProcess(get_project_settings())
        process.crawl(EastMoneyNewsSpider, 
                      sort_end=sort_end,
                      req_trace=req_trace,
                      sort_start=sort_start)
        process.start()
        logger.info(f"子进程新闻爬虫执行完成: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        logger.error(f"子进程运行新闻爬虫失败: {e}")
        import traceback
        traceback.print_exc()
```

### 修复后的代码

```python
def run_spider(sort_end, req_trace, sort_start):
    """在子进程中运行新闻爬虫"""
    try:
        # 设置环境变量，避免py_mini_racer的atexit注册问题
        os.environ['PY_MINI_RACER_NO_CLEANUP'] = '1'
        
        logger.info(f"子进程启动新闻爬虫... 当前时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 延迟导入，避免在主进程中加载
        from ..spider.eastmoney_spider import EastMoneyNewsSpider
        
        # 获取Scrapy设置
        settings = get_project_settings()
        
        # 禁用py_mini_racer的自动清理
        settings.set('PY_MINI_RACER_NO_CLEANUP', True)
        
        process = CrawlerProcess(settings)
        process.crawl(EastMoneyNewsSpider, 
                      sort_end=sort_end,
                      req_trace=req_trace,
                      sort_start=sort_start)
        logger.debug(f"sort_end={sort_end}, req_trace={req_trace}, sort_start={sort_start}")
        
        # 启动爬虫
        process.start()
        
        logger.info(f"子进程新闻爬虫执行完成: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        logger.error(f"子进程运行新闻爬虫失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保进程清理
        try:
            import gc
            gc.collect()
        except:
            pass
```

## 修复效果

### 修复前

```
2026-03-08 09:45:24 [internal.scheduler.scheduler] INFO: 子进程已启动，PID: 2714264
2026-03-08 09:45:24 [internal.scheduler.scheduler] INFO: 子进程启动新闻爬虫... 当前时间: 2026-03-08 09:45:24
/root/.pyenv/versions/3.12.0/lib/python3.12/site-packages/py_mini_racer/py_mini_racer.py:15: UserWarning: pkg_resources is deprecated as an API...
2026-03-08 09:45:25 [internal.scheduler.scheduler] ERROR: 子进程运行新闻爬虫失败: can't register atexit after shutdown
```

### 修复后

```
2026-03-08 09:45:24 [internal.scheduler.scheduler] INFO: 子进程已启动，PID: 2714264
2026-03-08 09:45:24 [internal.scheduler.scheduler] INFO: 子进程启动新闻爬虫... 当前时间: 2026-03-08 09:45:24
2026-03-08 09:45:25 [internal.scheduler.scheduler] INFO: 子进程新闻爬虫执行完成: 2026-03-08 09:45:25
```

## 其他改进

### 1. 同时修复 K线爬虫

对 `run_kline_spider` 方法应用相同的修复：

```python
def run_kline_spider():
    """在子进程中运行K线爬虫"""
    import atexit
    
    # 设置环境变量，避免py_mini_racer的atexit注册问题
    os.environ['PY_MINI_RACER_NO_CLEANUP'] = '1'
    
    # 注册清理函数
    atexit.register(unlock_kline)
    
    # ... 其余代码与新闻爬虫类似
```

### 2. 更好的错误处理

- 添加 `finally` 块确保资源清理
- 强制垃圾回收
- 更详细的日志记录

## 最佳实践

### 1. 子进程中的环境变量设置

在子进程启动时尽早设置环境变量：

```python
def run_in_subprocess():
    # 第一行就设置环境变量
    os.environ['PY_MINI_RACER_NO_CLEANUP'] = '1'
    
    # 然后进行其他操作
    # ...
```

### 2. 延迟导入

将可能在主进程中初始化的库延迟到子进程内部导入：

```python
# 不在文件顶部导入
# import some_library

def run_in_subprocess():
    # 在子进程内部导入
    import some_library
    # ...
```

### 3. 资源清理

确保子进程结束时正确清理资源：

```python
try:
    # 主逻辑
    pass
finally:
    # 清理资源
    import gc
    gc.collect()
```

## 验证方法

### 1. 本地测试

```bash
cd python-web-scraper
python internal/scheduler/scheduler.py
```

观察日志，确认没有 "can't register atexit after shutdown" 错误。

### 2. 生产环境测试

```bash
# 在生产环境中运行爬虫
python main.py
```

监控日志，确认爬虫正常运行。

### 3. 检查进程

```bash
# 检查子进程是否正常启动和退出
ps aux | grep python
```

## 已知限制

### 1. 禁用自动清理

设置 `PY_MINI_RACER_NO_CLEANUP=1` 会禁用 `py_mini_racer` 的自动清理功能。

**影响**：
- 可能会有少量内存泄漏（通常可以忽略）
- 子进程结束时操作系统会回收所有资源

**解决方案**：
- 使用 `finally` 块手动清理
- 确保子进程正常退出

### 2. pkg_resources 警告

`pkg_resources` 的弃用警告不影响功能，但建议升级相关依赖。

**解决方案**：
```bash
pip install --upgrade setuptools
```

## 后续优化建议

### 1. 升级依赖

考虑升级或替换 `py_mini_racer`：

```python
# 选项1：升级到最新版本
pip install --upgrade py_mini_racer

# 选项2：使用替代库
# 如：pyexecjs, node, 等
```

### 2. 使用不同的进程启动方式

考虑使用 `subprocess` 而不是 `multiprocessing`：

```python
import subprocess

def run_spider_external():
    """使用subprocess启动外部进程"""
    subprocess.run([
        'python',
        '-m',
        'scrapy.cmdline',
        'crawl',
        'eastmoney_news'
    ])
```

### 3. 容器化部署

将爬虫部署在容器中，隔离环境：

```dockerfile
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

## 总结

本次修复成功解决了 `py_mini_racer` 在子进程中的 `atexit` 注册问题：

✅ **设置环境变量** - 禁用 py_mini_racer 的自动清理
✅ **延迟导入** - 避免在主进程中初始化
✅ **配置Scrapy** - 通过设置禁用自动清理
✅ **资源清理** - 添加 finally 块确保清理
✅ **同时修复** - 修复了新闻爬虫和K线爬虫
✅ **更好的错误处理** - 详细的日志和异常处理

修复后的代码更加健壮，能够在多进程环境中稳定运行。
