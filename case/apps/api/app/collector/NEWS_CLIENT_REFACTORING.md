# news_client.py 重构说明

## 重构概述

本次重构主要解决 `news_client.py` 在获取 daily、weekly、monthly 新闻时只查询第一页的问题，实现了自动分页查询功能，确保能够获取所有数据。

## 主要问题分析

### 原有代码存在的问题

#### 1. 只获取第一页数据
```python
# 重构前
def get_all_news(self, date: Optional[str] = None, limit: int = 20) -> List[Dict]:
    all_items = []
    
    daily = self.get_daily_news(date, limit, 0)  # 只获取第一页
    if daily.get("items"):
        all_items.extend(daily["items"])
    
    weekly = self.get_weekly_news(date, limit, 0)  # 只获取第一页
    if weekly.get("items"):
        all_items.extend(weekly["items"])
    
    monthly = self.get_monthly_news(date, limit, 0)  # 只获取第一页
    if monthly.get("items"):
        all_items.extend(monthly["items"])
    
    return all_items[:limit]
```

**问题**：
- `offset=0` 固定为第一页
- 没有循环获取后续页面
- 可能丢失大量数据

#### 2. 缺少配置管理
- 没有统一的配置管理
- 硬编码的参数值
- 难以调整行为

#### 3. 缺少错误处理
- 没有重试机制
- 错误处理简单
- 缺少详细的日志

#### 4. 没有数据量限制
- 可能获取无限多的数据
- 没有保护机制
- 可能导致内存溢出

## 重构解决方案

### 1. 新增配置管理

#### NewsClientConfig 配置类
```python
@dataclass
class NewsClientConfig:
    """新闻客户端配置"""
    # 分页配置
    default_page_size: int = 20          # 默认每页数量
    max_page_size: int = 100             # 最大每页数量
    max_total_items: int = 10000         # 最大总记录数限制
    
    # 请求配置
    request_timeout: int = 30            # 请求超时时间（秒）
    auth_timeout: int = 10               # 认证超时时间（秒）
    max_retries: int = 3                 # 最大重试次数
    
    # 行为配置
    auto_retry: bool = True              # 是否自动重试
    stop_on_empty: bool = True           # 遇到空页是否停止
    log_requests: bool = True            # 是否记录请求日志
```

### 2. 新增自动分页方法

#### get_all_daily_news
```python
def get_all_daily_news(
    self, 
    date: Optional[str] = None, 
    page_size: int = None,
    max_items: int = None
) -> List[Dict]:
    """
    获取所有每日新闻（自动分页）
    
    参数:
        date: 日期
        page_size: 每页数量（默认使用配置值）
        max_items: 最大记录数限制（默认使用配置值）
    
    返回:
        所有每日新闻列表
    """
```

#### get_all_weekly_news
```python
def get_all_weekly_news(
    self, 
    date: Optional[str] = None, 
    page_size: int = None,
    max_items: int = None
) -> List[Dict]:
    """
    获取所有每周新闻（自动分页）
    """
```

#### get_all_monthly_news
```python
def get_all_monthly_news(
    self, 
    date: Optional[str] = None, 
    page_size: int = None,
    max_items: int = None
) -> List[Dict]:
    """
    获取所有每月新闻（自动分页）
    """
```

### 3. 核心分页逻辑

#### _fetch_all_pages 方法
```python
def _fetch_all_pages(
    self,
    endpoint: str,
    params: Dict,
    page_size: int,
    max_items: int,
    news_type: str
) -> List[Dict]:
    """
    获取所有页面的数据
    
    特性:
    - 自动循环获取所有页面
    - 支持最大记录数限制
    - 遇到空页自动停止
    - 详细的进度日志
    - 完善的错误处理
    """
    all_items = []
    offset = 0
    page_count = 0
    
    while True:
        # 检查是否达到最大记录数限制
        if len(all_items) >= max_items:
            logger.info(f"已达到最大记录数限制 {max_items}，停止获取")
            break
        
        # 请求当前页
        response = self._request(
            endpoint,
            {**params, "limit": page_size, "offset": offset}
        )
        
        # 提取数据
        items = response.get("items", [])
        
        if not items:
            if self.config.stop_on_empty:
                logger.info(f"{news_type}新闻第{page_count + 1}页为空，停止获取")
                break
        
        # 添加数据
        all_items.extend(items)
        page_count += 1
        
        # 如果返回的数据少于请求的数量，说明已经是最后一页
        if len(items) < page_size:
            break
        
        # 移动到下一页
        offset += page_size
    
    return all_items
```

### 4. 重构 get_all_news 方法

```python
def get_all_news(
    self, 
    date: Optional[str] = None, 
    limit: int = None,
    page_size: int = None
) -> List[Dict]:
    """
    获取所有类型的新闻（自动分页）
    
    改进:
    - 使用自动分页方法
    - 支持总记录数限制
    - 详细的进度日志
    - 按顺序获取：daily -> weekly -> monthly
    """
    limit = limit or self.config.max_total_items
    page_size = page_size or self.config.default_page_size
    
    all_items = []
    
    # 获取每日新闻
    daily_items = self.get_all_daily_news(date, page_size, limit)
    all_items.extend(daily_items)
    
    # 检查是否达到限制
    if limit and len(all_items) >= limit:
        return all_items[:limit]
    
    # 获取每周新闻
    remaining = limit - len(all_items) if limit else None
    weekly_items = self.get_all_weekly_news(date, page_size, remaining)
    all_items.extend(weekly_items)
    
    # 检查是否达到限制
    if limit and len(all_items) >= limit:
        return all_items[:limit]
    
    # 获取每月新闻
    remaining = limit - len(all_items) if limit else None
    monthly_items = self.get_all_monthly_news(date, page_size, remaining)
    all_items.extend(monthly_items)
    
    # 应用限制
    if limit:
        all_items = all_items[:limit]
    
    return all_items
```

### 5. 新增迭代器模式

#### get_all_news_iter 方法
```python
def get_all_news_iter(
    self, 
    date: Optional[str] = None,
    page_size: int = None
) -> Iterator[Dict]:
    """
    获取所有类型的新闻（迭代器模式）
    
    优势:
    - 内存效率高，逐条处理
    - 适合大数据量场景
    - 支持流式处理
    """
```

#### _fetch_all_pages_iter 方法
```python
def _fetch_all_pages_iter(
    self,
    endpoint: str,
    params: Dict,
    page_size: int,
    max_items: int,
    news_type: str
) -> Iterator[Dict]:
    """
    获取所有页面的数据（迭代器模式）
    
    特性:
    - 逐条yield，不占用大量内存
    - 支持中断和恢复
    - 适合流式处理
    """
```

## 使用方法

### 1. 基本使用（默认配置）

```python
from app.collector.news_client import NewsClient

# 使用默认配置
client = NewsClient(
    base_url="https://api.example.com",
    username="user",
    password="pass"
)

# 获取所有每日新闻
daily_news = client.get_all_daily_news(date="2024-01-15")
print(f"获取到 {len(daily_news)} 条每日新闻")

# 获取所有每周新闻
weekly_news = client.get_all_weekly_news(date="2024-01-15")
print(f"获取到 {len(weekly_news)} 条每周新闻")

# 获取所有每月新闻
monthly_news = client.get_all_monthly_news(date="2024-01-15")
print(f"获取到 {len(monthly_news)} 条每月新闻")

# 获取所有类型的新闻
all_news = client.get_all_news(date="2024-01-15")
print(f"获取到 {len(all_news)} 条新闻")
```

### 2. 自定义配置

```python
from app.collector.news_client import NewsClient, NewsClientConfig

# 创建自定义配置
config = NewsClientConfig(
    default_page_size=50,      # 每页50条
    max_total_items=5000,      # 最多5000条
    request_timeout=60,        # 超时60秒
    log_requests=True          # 记录日志
)

client = NewsClient(
    base_url="https://api.example.com",
    username="user",
    password="pass",
    config=config
)

# 使用自定义配置获取数据
news = client.get_all_daily_news(date="2024-01-15")
```

### 3. 控制记录数

```python
# 限制最多100条记录
news = client.get_all_daily_news(
    date="2024-01-15",
    max_items=100
)

# 限制每页大小和总记录数
news = client.get_all_daily_news(
    date="2024-01-15",
    page_size=20,      # 每页20条
    max_items=100      # 最多100条
)
```

### 4. 使用迭代器模式（适合大数据量）

```python
# 使用迭代器逐条处理
for news_item in client.get_all_news_iter(date="2024-01-15"):
    # 处理每条新闻
    print(f"处理新闻: {news_item.get('title')}")
    
    # 可以随时中断
    if some_condition:
        break
```

### 5. 组合使用

```python
# 先获取每日新闻的前100条
daily_news = client.get_all_daily_news(
    date="2024-01-15",
    max_items=100
)

# 再获取每周新闻的前50条
weekly_news = client.get_all_weekly_news(
    date="2024-01-15",
    max_items=50
)

# 合并结果
all_news = daily_news + weekly_news
print(f"总共 {len(all_news)} 条新闻")
```

## 功能对比

### 重构前 vs 重构后

| 功能 | 重构前 | 重构后 | 改进 |
|------|--------|--------|------|
| 获取daily新闻 | 只获取第一页 | 自动获取所有页 | ✅ 完整数据 |
| 获取weekly新闻 | 只获取第一页 | 自动获取所有页 | ✅ 完整数据 |
| 获取monthly新闻 | 只获取第一页 | 自动获取所有页 | ✅ 完整数据 |
| 配置管理 | 无 | 完整配置系统 | ✅ 灵活配置 |
| 数据量限制 | 无 | 可配置限制 | ✅ 防止溢出 |
| 错误处理 | 基础 | 完善的错误处理 | ✅ 更稳定 |
| 日志记录 | 简单 | 详细的进度日志 | ✅ 便于调试 |
| 内存优化 | 全部加载到内存 | 支持迭代器模式 | ✅ 更高效 |
| 向后兼容 | N/A | 保留原有接口 | ✅ 无缝升级 |

## 性能优化

### 1. 内存优化

**列表模式**：
```python
# 适合小数据量
news = client.get_all_daily_news(date="2024-01-15")
# 所有数据加载到内存
```

**迭代器模式**：
```python
# 适合大数据量
for news_item in client.get_all_news_iter(date="2024-01-15"):
    # 逐条处理，内存占用低
    process_news(news_item)
```

### 2. 网络优化

- 自动分页减少请求次数
- 可配置的页面大小
- 超时控制
- 错误重试

### 3. 数据量控制

```python
# 设置合理的限制
config = NewsClientConfig(
    max_total_items=10000  # 最多10000条
)
```

## 错误处理

### 1. 认证错误
```python
try:
    client = NewsClient(
        base_url="https://api.example.com",
        username="user",
        password="wrong_password"
    )
except Exception as e:
    logger.error(f"认证失败: {e}")
```

### 2. 网络错误
```python
try:
    news = client.get_all_daily_news(date="2024-01-15")
except requests.exceptions.Timeout:
    logger.error("请求超时")
except requests.exceptions.ConnectionError:
    logger.error("连接错误")
except Exception as e:
    logger.error(f"获取新闻失败: {e}")
```

### 3. 空数据处理
```python
news = client.get_all_daily_news(date="2024-01-15")

if not news:
    logger.warning("没有获取到新闻数据")
else:
    logger.info(f"成功获取 {len(news)} 条新闻")
```

## 日志输出示例

```
新闻客户端初始化完成，配置: page_size=20
正在获取 token，URL: https://api.example.com/api/auth/token
用户名: user
认证响应状态码: 200
Token获取成功
开始获取所有daily新闻，page_size=20, max_items=10000
请求 URL: https://api.example.com/api/news/daily
请求参数: {'date': '2024-01-15', 'limit': 20, 'offset': 0}
响应状态码: 200
响应数据: 20 条记录
已获取daily新闻第1页，本页20条，累计20条
请求 URL: https://api.example.com/api/news/daily
请求参数: {'date': '2024-01-15', 'limit': 20, 'offset': 20}
响应状态码: 200
响应数据: 20 条记录
已获取daily新闻第2页，本页20条，累计40条
...
daily新闻已获取完毕，共5页，100条记录
daily新闻获取完成，共100条记录
```

## 最佳实践

### 1. 选择合适的方法
- **小数据量**：使用 `get_all_*_news()` 方法
- **大数据量**：使用 `get_all_news_iter()` 迭代器
- **需要限制**：设置 `max_items` 参数

### 2. 配置优化
```python
config = NewsClientConfig(
    default_page_size=50,      # 根据API性能调整
    max_total_items=5000,      # 根据内存情况调整
    request_timeout=60,        # 根据网络情况调整
    log_requests=True          # 生产环境建议开启
)
```

### 3. 错误处理
```python
try:
    news = client.get_all_daily_news(date="2024-01-15")
except Exception as e:
    logger.error(f"获取新闻失败: {e}")
    # 降级处理
    news = []
```

### 4. 性能监控
```python
import time

start = time.time()
news = client.get_all_daily_news(date="2024-01-15")
elapsed = time.time() - start

logger.info(f"获取 {len(news)} 条新闻，耗时 {elapsed:.2f} 秒")
```

## 后续优化建议

### 1. 并发请求
```python
# 使用多线程并发获取不同类型的新闻
import concurrent.futures

def fetch_all_concurrent(client, date):
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = {
            executor.submit(client.get_all_daily_news, date): 'daily',
            executor.submit(client.get_all_weekly_news, date): 'weekly',
            executor.submit(client.get_all_monthly_news, date): 'monthly'
        }
        
        results = {}
        for future in concurrent.futures.as_completed(futures):
            news_type = futures[future]
            results[news_type] = future.result()
        
        return results
```

### 2. 缓存机制
```python
# 添加缓存，避免重复请求
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_news(self, date: str, news_type: str) -> List[Dict]:
    """带缓存的新闻获取"""
    if news_type == 'daily':
        return self.get_all_daily_news(date)
    elif news_type == 'weekly':
        return self.get_all_weekly_news(date)
    elif news_type == 'monthly':
        return self.get_all_monthly_news(date)
```

### 3. 断点续传
```python
# 支持从上次中断的位置继续
def get_all_news_with_resume(
    self,
    date: Optional[str] = None,
    resume_offset: int = 0
) -> List[Dict]:
    """支持断点续传"""
    # 从指定的offset开始获取
    pass
```

### 4. 数据去重
```python
def get_all_news_deduplicated(
    self,
    date: Optional[str] = None
) -> List[Dict]:
    """获取去重后的新闻"""
    all_news = self.get_all_news(date)
    
    # 根据某个字段去重
    seen = set()
    unique_news = []
    
    for news in all_news:
        key = news.get('id') or news.get('title')
        if key not in seen:
            seen.add(key)
            unique_news.append(news)
    
    return unique_news
```

## 总结

本次重构显著提升了新闻客户端的功能和性能：

✅ **解决分页问题** - 自动获取所有页面的数据
✅ **配置管理** - 灵活的配置系统
✅ **错误处理** - 完善的异常处理和重试机制
✅ **内存优化** - 支持迭代器模式，降低内存占用
✅ **日志完善** - 详细的进度日志，便于调试
✅ **向后兼容** - 保留原有接口，无缝升级
✅ **性能优化** - 可配置的页面大小和超时时间

重构后的代码更加健壮、高效、易用，能够很好地处理各种新闻获取场景。
