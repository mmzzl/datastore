import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class NewsClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.token = self._get_token(username, password)

    def _get_token(self, username: str, password: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        payload = {"username": username, "password": password}
        
        logger.info(f"正在获取 token，URL: {self.base_url}/api/auth/token")
        logger.info(f"用户名: {username}")
        
        resp = requests.post(
            f"{self.base_url}/api/auth/token",
            json=payload,
            headers=headers,
            timeout=10,
            verify=False
        )
        
        logger.info(f"响应状态码: {resp.status_code}")
        if resp.status_code != 200:
            logger.error(f"认证失败，响应内容: {resp.text}")
        
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        headers = {"Authorization": f"Bearer {self.token}"}
        url = f"{self.base_url}{endpoint}"
        
        logger.info(f"请求 URL: {url}")
        logger.info(f"请求参数: {params}")
        
        try:
            resp = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=30,
                verify=False
            )
            
            logger.info(f"响应状态码: {resp.status_code}")
            if resp.status_code != 200:
                logger.error(f"请求失败，响应内容: {resp.text}")
            
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP 错误: {e}")
            logger.error(f"响应内容: {e.response.text if e.response else 'No response'}")
            raise
        except Exception as e:
            logger.error(f"请求异常: {e}")
            raise

    def get_daily_news(self, date: Optional[str] = None, limit: int = 10, offset: int = 0) -> Dict:
        return self._request("/api/news/daily", {"date": date, "limit": limit, "offset": offset})

    def get_weekly_news(self, date: Optional[str] = None, limit: int = 10, offset: int = 0) -> Dict:
        return self._request("/api/news/weekly", {"date": date, "limit": limit, "offset": offset})

    def get_monthly_news(self, date: Optional[str] = None, limit: int = 10, offset: int = 0) -> Dict:
        return self._request("/api/news/monthly", {"date": date, "limit": limit, "offset": offset})

    def get_all_news(self, date: Optional[str] = None, limit: int = 20) -> List[Dict]:
        all_items = []
        
        daily = self.get_daily_news(date, limit, 0)
        if daily.get("items"):
            all_items.extend(daily["items"])
        
        weekly = self.get_weekly_news(date, limit, 0)
        if weekly.get("items"):
            all_items.extend(weekly["items"])
        
        monthly = self.get_monthly_news(date, limit, 0)
        if monthly.get("items"):
            all_items.extend(monthly["items"])
        
        return all_items[:limit]
