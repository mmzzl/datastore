"""
新闻客户端 - 重构版本
支持自动分页查询，获取所有类型的完整数据
支持缓存机制，避免重复请求
"""

import requests
from typing import List, Dict, Optional, Iterator
from dataclasses import dataclass
import logging
import hashlib
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class NewsClientConfig:
    """新闻客户端配置"""
    # 分页配置
    default_page_size: int = 20          # 默认每页数量
    max_page_size: int = 100             # 最大每页数量
    max_total_items: int = 10000         # 最大总记录数限制（防止无限循环）
    
    # 请求配置
    request_timeout: int = 30            # 请求超时时间（秒）
    auth_timeout: int = 10               # 认证超时时间（秒）
    max_retries: int = 3                 # 最大重试次数
    
    # 行为配置
    auto_retry: bool = True              # 是否自动重试
    stop_on_empty: bool = True           # 遇到空页是否停止
    log_requests: bool = True            # 是否记录请求日志
    
    # 缓存配置
    enable_cache: bool = True            # 是否启用缓存
    cache_ttl: int = 3600            # 缓存过期时间（秒），默认24小时


class NewsClient:
    """新闻客户端，支持自动分页查询和缓存"""
    
    def __init__(
        self, 
        base_url: str, 
        username: str, 
        password: str,
        config: NewsClientConfig = None
    ):
        """
        初始化新闻客户端
        
        参数:
            base_url: API基础URL
            username: 用户名
            password: 密码
            config: 客户端配置，如果为None则使用默认配置
        """
        self.base_url = base_url.rstrip('/')
        self.config = config or NewsClientConfig()
        self.token = self._get_token(username, password)
        
        # 初始化缓存
        self._cache = {}  # 格式: {cache_key: (data, timestamp)}
        
        cache_status = "启用" if self.config.enable_cache else "禁用"
        logger.info(f"新闻客户端初始化完成，配置: page_size={self.config.default_page_size}, 缓存={cache_status}")
    
    def _get_token(self, username: str, password: str) -> str:
        """
        获取认证token
        
        参数:
            username: 用户名
            password: 密码
        
        返回:
            认证token
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        payload = {"username": username, "password": password}
        
        if self.config.log_requests:
            logger.info(f"正在获取 token，URL: {self.base_url}/api/auth/token")
            logger.info(f"用户名: {username}")
        
        try:
            resp = requests.post(
                f"{self.base_url}/api/auth/token",
                json=payload,
                headers=headers,
                timeout=self.config.auth_timeout,
                verify=False
            )
            
            if self.config.log_requests:
                logger.info(f"认证响应状态码: {resp.status_code}")
            
            if resp.status_code != 200:
                logger.error(f"认证失败，响应内容: {resp.text}")
            
            resp.raise_for_status()
            token = resp.json()["access_token"]
            
            if self.config.log_requests:
                logger.info("Token获取成功")
            
            return token
            
        except Exception as e:
            logger.error(f"获取token失败: {e}")
            raise
    
    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """
        发送HTTP请求（支持重试）
        
        参数:
            endpoint: API端点
            params: 请求参数
        
        返回:
            响应数据
        """
        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{self.base_url}{endpoint}"
        
        if self.config.log_requests:
            logger.info(f"请求 URL: {url}")
            logger.info(f"请求参数: {params}")
        
        max_retries = 10
        last_error = None
        
        for attempt in range(max_retries):
            try:
                resp = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=self.config.request_timeout,
                    verify=False
                )
                
                if self.config.log_requests:
                    logger.info(f"响应状态码: {resp.status_code}")
                
                if resp.status_code != 200:
                    logger.error(f"请求失败，响应内容: {resp.text}")
                
                resp.raise_for_status()
                result = resp.json()
                
                if self.config.log_requests:
                    logger.info(f"响应数据: {len(result.get('items', []))} 条记录")
                
                return result
                
            except requests.exceptions.HTTPError as e:
                last_error = e
                logger.error(f"HTTP 错误 (第{attempt + 1}/{max_retries}次尝试): {e}")
                logger.error(f"响应内容: {e.response.text if e.response else 'No response'}")
                
                if attempt < max_retries - 1:
                    import time
                    wait_time = 2 ** attempt  # 指数退避：2, 4, 8, 16, 32...
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"已达到最大重试次数 {max_retries}，放弃请求")
                    
            except requests.exceptions.Timeout as e:
                last_error = e
                logger.error(f"请求超时 (第{attempt + 1}/{max_retries}次尝试): {e}")
                
                if attempt < max_retries - 1:
                    import time
                    wait_time = 2 ** attempt
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"已达到最大重试次数 {max_retries}，放弃请求")
                    
            except requests.exceptions.ConnectionError as e:
                last_error = e
                logger.error(f"连接错误 (第{attempt + 1}/{max_retries}次尝试): {e}")
                
                if attempt < max_retries - 1:
                    import time
                    wait_time = 2 ** attempt
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"已达到最大重试次数 {max_retries}，放弃请求")
                    
            except Exception as e:
                last_error = e
                logger.error(f"请求异常 (第{attempt + 1}/{max_retries}次尝试): {e}")
                
                if attempt < max_retries - 1:
                    import time
                    wait_time = 2 ** attempt
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"已达到最大重试次数 {max_retries}，放弃请求")
        
        # 所有重试都失败，抛出最后一个错误
        if last_error:
            raise last_error
    
    def _generate_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """
        生成缓存键
        
        参数:
            endpoint: API端点
            params: 请求参数
        
        返回:
            缓存键
        """
        # 将参数转换为字符串并排序，确保相同参数生成相同的键
        params_str = json.dumps(params, sort_keys=True) if params else ""
        key_str = f"{endpoint}:{params_str}"
        # 使用MD5哈希生成缓存键
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """
        从缓存获取数据
        
        参数:
            cache_key: 缓存键
        
        返回:
            缓存的数据，如果不存在或已过期返回None
        """
        if not self.config.enable_cache:
            return None
        
        if cache_key not in self._cache:
            return None
        
        data, timestamp = self._cache[cache_key]
        cache_age = datetime.now() - timestamp
        
        if cache_age.total_seconds() > self.config.cache_ttl:
            logger.info(f"缓存已过期（{cache_age.total_seconds():.0f}秒），删除缓存")
            del self._cache[cache_key]
            return None
        
        logger.info(f"从缓存获取数据（缓存时间: {cache_age.total_seconds():.0f}秒）")
        return data
    
    def _save_to_cache(self, cache_key: str, data: Dict) -> None:
        """
        保存数据到缓存
        
        参数:
            cache_key: 缓存键
            data: 要缓存的数据
        """
        if not self.config.enable_cache:
            return
        
        self._cache[cache_key] = (data, datetime.now())
        logger.info(f"数据已缓存，键: {cache_key[:16]}...")
    
    def clear_cache(self) -> None:
        """
        清空缓存
        """
        self._cache.clear()
        logger.info("缓存已清空")
    
    def get_daily_news(
        self, 
        date: Optional[str] = None, 
        limit: int = None, 
        offset: int = 0
    ) -> Dict:
        """
        获取每日新闻（单页）
        
        参数:
            date: 日期
            limit: 每页数量（默认使用配置值）
            offset: 偏移量
        
        返回:
            新闻数据
        """
        limit = limit or self.config.default_page_size
        params = {"date": date, "limit": limit, "offset": offset}
        
        # 检查缓存
        cache_key = self._generate_cache_key("/api/news/daily", params)
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # 缓存未命中，发送请求
        data = self._request("/api/news/daily", params)
        
        # 保存到缓存
        self._save_to_cache(cache_key, data)
        
        return data
    
    def get_weekly_news(
        self, 
        date: Optional[str] = None, 
        limit: int = None, 
        offset: int = 0
    ) -> Dict:
        """
        获取每周新闻（单页）
        
        参数:
            date: 日期
            limit: 每页数量（默认使用配置值）
            offset: 偏移量
        
        返回:
            新闻数据
        """
        limit = limit or self.config.default_page_size
        params = {"date": date, "limit": limit, "offset": offset}
        
        # 检查缓存
        cache_key = self._generate_cache_key("/api/news/weekly", params)
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # 缓存未命中，发送请求
        data = self._request("/api/news/weekly", params)
        
        # 保存到缓存
        self._save_to_cache(cache_key, data)
        
        return data
    
    def get_monthly_news(
        self, 
        date: Optional[str] = None, 
        limit: int = None, 
        offset: int = 0
    ) -> Dict:
        """
        获取每月新闻（单页）
        
        参数:
            date: 日期
            limit: 每页数量（默认使用配置值）
            offset: 偏移量
        
        返回:
            新闻数据
        """
        limit = limit or self.config.default_page_size
        params = {"date": date, "limit": limit, "offset": offset}
        
        # 检查缓存
        cache_key = self._generate_cache_key("/api/news/monthly", params)
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        # 缓存未命中，发送请求
        data = self._request("/api/news/monthly", params)
        
        # 保存到缓存
        self._save_to_cache(cache_key, data)
        
        return data
    
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
        page_size = page_size or self.config.default_page_size
        max_items = max_items or self.config.max_total_items
        
        return self._fetch_all_pages(
            endpoint="/api/news/daily",
            params={"date": date},
            page_size=page_size,
            max_items=max_items,
            news_type="daily"
        )
    
    def get_all_weekly_news(
        self, 
        date: Optional[str] = None, 
        page_size: int = None,
        max_items: int = None
    ) -> List[Dict]:
        """
        获取所有每周新闻（自动分页）
        
        参数:
            date: 日期
            page_size: 每页数量（默认使用配置值）
            max_items: 最大记录数限制（默认使用配置值）
        
        返回:
            所有每周新闻列表
        """
        page_size = page_size or self.config.default_page_size
        max_items = max_items or self.config.max_total_items
        
        return self._fetch_all_pages(
            endpoint="/api/news/weekly",
            params={"date": date},
            page_size=page_size,
            max_items=max_items,
            news_type="weekly"
        )
    
    def get_all_monthly_news(
        self, 
        date: Optional[str] = None, 
        page_size: int = None,
        max_items: int = None
    ) -> List[Dict]:
        """
        获取所有每月新闻（自动分页）
        
        参数:
            date: 日期
            page_size: 每页数量（默认使用配置值）
            max_items: 最大记录数限制（默认使用配置值）
        
        返回:
            所有每月新闻列表
        """
        page_size = page_size or self.config.default_page_size
        max_items = max_items or self.config.max_total_items
        
        return self._fetch_all_pages(
            endpoint="/api/news/monthly",
            params={"date": date},
            page_size=page_size,
            max_items=max_items,
            news_type="monthly"
        )
    
    def _fetch_all_pages(
        self,
        endpoint: str,
        params: Dict,
        page_size: int,
        max_items: int,
        news_type: str
    ) -> List[Dict]:
        """
        获取所有页面的数据（支持缓存）
        
        参数:
            endpoint: API端点
            params: 基础参数
            page_size: 每页数量
            max_items: 最大记录数限制
            news_type: 新闻类型（用于日志）
        
        返回:
            所有数据列表
        """
        # 检查缓存
        cache_key = self._generate_cache_key(endpoint, params)
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            logger.info(f"从缓存获取所有{news_type}新闻")
            return cached_data
        
        all_items = []
        offset = 0
        page_count = 0
        
        logger.info(f"开始获取所有{news_type}新闻，page_size={page_size}, max_items={max_items}")
        
        while True:
            # 检查是否达到最大记录数限制
            if len(all_items) >= max_items:
                logger.info(f"已达到最大记录数限制 {max_items}，停止获取")
                break
            
            # 请求当前页
            try:
                response = self._request(
                    endpoint,
                    {**params, "limit": page_size, "offset": offset}
                )
            except Exception as e:
                logger.error(f"获取{news_type}新闻第{page_count + 1}页失败: {e}")
                break
            
            # 提取数据
            items = response.get("items", [])
            
            if not items:
                if self.config.stop_on_empty:
                    logger.info(f"{news_type}新闻第{page_count + 1}页为空，停止获取")
                    break
                else:
                    logger.warning(f"{news_type}新闻第{page_count + 1}页为空，继续下一页")
                    offset += page_size
                    page_count += 1
                    continue
            
            # 添加数据
            remaining = max_items - len(all_items)
            items_to_add = items[:remaining]
            all_items.extend(items_to_add)
            
            page_count += 1
            logger.info(
                f"已获取{news_type}新闻第{page_count}页，"
                f"本页{len(items_to_add)}条，累计{len(all_items)}条"
            )
            
            # 如果返回的数据少于请求的数量，说明已经是最后一页
            if len(items) < page_size:
                logger.info(f"{news_type}新闻已获取完毕，共{page_count}页，{len(all_items)}条记录")
                break
            
            # 移动到下一页
            offset += page_size
        
        logger.info(f"{news_type}新闻获取完成，共{len(all_items)}条记录")
        
        # 保存到缓存
        self._save_to_cache(cache_key, all_items)
        
        return all_items
    
    def get_all_news(
        self, 
        date: Optional[str] = None, 
        limit: int = None,
        page_size: int = None
    ) -> List[Dict]:
        """
        获取所有类型的新闻（自动分页）
        
        参数:
            date: 日期
            limit: 总记录数限制（None表示不限制）
            page_size: 每页数量（默认使用配置值）
        
        返回:
            所有新闻列表
        """
        limit = limit or self.config.max_total_items
        page_size = page_size or self.config.default_page_size
        
        all_items = []
        
        # 获取每日新闻
        logger.info("开始获取每日新闻...")
        daily_items = self.get_all_daily_news(date, page_size, limit)
        all_items.extend(daily_items)
        logger.info(f"每日新闻获取完成，{len(daily_items)}条")
        
        # 检查是否达到限制
        if limit and len(all_items) >= limit:
            return all_items[:limit]
        
        # 获取每周新闻
        logger.info("开始获取每周新闻...")
        remaining = limit - len(all_items) if limit else None
        weekly_items = self.get_all_weekly_news(date, page_size, remaining)
        all_items.extend(weekly_items)
        logger.info(f"每周新闻获取完成，{len(weekly_items)}条")
        
        # 检查是否达到限制
        if limit and len(all_items) >= limit:
            return all_items[:limit]
        
        # 获取每月新闻
        logger.info("开始获取每月新闻...")
        remaining = limit - len(all_items) if limit else None
        monthly_items = self.get_all_monthly_news(date, page_size, remaining)
        all_items.extend(monthly_items)
        logger.info(f"每月新闻获取完成，{len(monthly_items)}条")
        
        # 应用限制
        if limit:
            all_items = all_items[:limit]
        
        logger.info(f"所有新闻获取完成，共{len(all_items)}条记录")
        return all_items
    
    def get_all_news_iter(
        self, 
        date: Optional[str] = None,
        page_size: int = None
    ) -> Iterator[Dict]:
        """
        获取所有类型的新闻（迭代器模式）
        
        参数:
            date: 日期
            page_size: 每页数量（默认使用配置值）
        
        返回:
            新闻迭代器
        """
        page_size = page_size or self.config.default_page_size
        
        # 获取每日新闻
        yield from self._fetch_all_pages_iter(
            endpoint="/api/news/daily",
            params={"date": date},
            page_size=page_size,
            max_items=self.config.max_total_items,
            news_type="daily"
        )
        
        # 获取每周新闻
        yield from self._fetch_all_pages_iter(
            endpoint="/api/news/weekly",
            params={"date": date},
            page_size=page_size,
            max_items=self.config.max_total_items,
            news_type="weekly"
        )
        
        # 获取每月新闻
        yield from self._fetch_all_pages_iter(
            endpoint="/api/news/monthly",
            params={"date": date},
            page_size=page_size,
            max_items=self.config.max_total_items,
            news_type="monthly"
        )
    
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
        
        参数:
            endpoint: API端点
            params: 基础参数
            page_size: 每页数量
            max_items: 最大记录数限制
            news_type: 新闻类型（用于日志）
        
        返回:
            数据迭代器
        """
        offset = 0
        total_fetched = 0
        
        logger.info(f"开始迭代获取{news_type}新闻，page_size={page_size}, max_items={max_items}")
        
        while total_fetched < max_items:
            # 请求当前页
            try:
                response = self._request(
                    endpoint,
                    {**params, "limit": page_size, "offset": offset}
                )
            except Exception as e:
                logger.error(f"获取{news_type}新闻失败: {e}")
                break
            
            # 提取数据
            items = response.get("items", [])
            
            if not items:
                if self.config.stop_on_empty:
                    logger.info(f"{news_type}新闻迭代完成，共{total_fetched}条")
                    break
                else:
                    offset += page_size
                    continue
            
            # 逐条yield
            for item in items:
                if total_fetched >= max_items:
                    logger.info(f"{news_type}新闻迭代完成，已达到最大限制{max_items}")
                    return
                yield item
                total_fetched += 1
            
            # 如果返回的数据少于请求的数量，说明已经是最后一页
            if len(items) < page_size:
                logger.info(f"{news_type}新闻迭代完成，共{total_fetched}条")
                break
            
            # 移动到下一页
            offset += page_size
