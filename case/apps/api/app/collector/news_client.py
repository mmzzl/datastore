import requests
from typing import List, Dict, Optional


class NewsClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.token = self._get_token(username, password)

    def _get_token(self, username: str, password: str) -> str:
        resp = requests.post(
            f"{self.base_url}/api/auth/token",
            json={"username": username, "password": password},
            timeout=10,
            verify=False
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        headers = {"Authorization": f"Bearer {self.token}"}
        resp = requests.get(
            f"{self.base_url}{endpoint}",
            params=params,
            headers=headers,
            timeout=30,
            verify=False
        )
        resp.raise_for_status()
        return resp.json()

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
