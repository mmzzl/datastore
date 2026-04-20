import os
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from .base import BaseWatcher


class NewsEventWatcher(BaseWatcher):
    _name_to_code: Optional[Dict[str, Tuple[str, str]]] = None
    _code_to_name: Optional[Dict[str, str]] = None
    _name_max_len: int = 0

    def __init__(self, data_manager=None, keyword_rules: Dict[str, List[str]] = None):
        super().__init__(data_manager)
        self.keyword_rules = keyword_rules or {}
        self._last_triggered: Dict[str, datetime] = {}
        self._cooldown_seconds = 300
        self._ensure_name_map()

    @classmethod
    def _ensure_name_map(cls):
        if cls._name_to_code is not None:
            return
        import pandas as pd

        name_map: Dict[str, Tuple[str, str]] = {}
        csv_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "data", "all_stock.csv"
        )
        try:
            df = pd.read_csv(csv_path, encoding="utf-8")
            for _, row in df.iterrows():
                raw_code = str(row.get("code", "")).strip()
                name = str(row.get("code_name", "")).strip()
                if not raw_code or not name:
                    continue
                if not re.match(r"^[sz][hz]\.\d{6}$", raw_code):
                    continue
                prefix = raw_code[:2].upper()
                digits = raw_code[3:]
                normalized = f"{prefix}{digits}"
                name_map[name] = (normalized, name)
            cls._name_to_code = name_map
            cls._code_to_name = {c: n for _, (c, n) in name_map.items()}
            cls._name_max_len = max((len(n) for n in name_map), default=0)
        except Exception:
            cls._name_to_code = {}
            cls._code_to_name = {}
            cls._name_max_len = 0

    @classmethod
    def _parse_stock_list(cls, stock_list: List[str]) -> List[Dict[str, str]]:
        results: List[Dict[str, str]] = []
        seen: Set[str] = set()
        for item in stock_list:
            if not item or not isinstance(item, str):
                continue
            if item.startswith("90.BK"):
                continue
            parts = item.split(".")
            if len(parts) != 2:
                continue
            market_prefix, digits = parts
            if not digits or not digits.isdigit():
                continue
            if len(digits) == 6 and digits.isdigit():
                if market_prefix.startswith("1"):
                    code = f"SH{digits}"
                elif market_prefix.startswith("0"):
                    code = f"SZ{digits}"
                elif market_prefix.startswith("2"):
                    code = f"SZ{digits}"
                else:
                    code = digits
                if code not in seen:
                    name = cls._lookup_name(code)
                    results.append({"code": code, "name": name})
                    seen.add(code)
        return results

    @classmethod
    def _lookup_name(cls, code: str) -> str:
        if cls._code_to_name and code in cls._code_to_name:
            return cls._code_to_name[code]
        return code

    @classmethod
    def _extract_stock_codes_from_text(cls, text: str) -> List[Dict[str, str]]:
        if not cls._name_to_code or not text:
            return []
        results = []
        seen: Set[str] = set()
        for length in range(cls._name_max_len, 1, -1):
            for i in range(len(text) - length + 1):
                segment = text[i : i + length]
                if segment in cls._name_to_code and segment not in seen:
                    code, name = cls._name_to_code[segment]
                    results.append({"code": code, "name": name})
                    seen.add(segment)
        code_pattern = re.findall(r"(?<![A-Za-z])(\d{6})(?![A-Za-z\d])", text)
        if code_pattern and cls._code_to_name:
            for digits in code_pattern:
                for prefix in ("SH", "SZ"):
                    candidate = f"{prefix}{digits}"
                    if candidate not in seen and candidate in cls._code_to_name:
                        results.append({"code": candidate, "name": cls._code_to_name[candidate]})
                        seen.add(candidate)
        return results

    def _get_mongo_collection(self):
        try:
            from app.core.config import settings
            from app.storage.mongo_client import MongoStorage

            storage = MongoStorage(
                host=settings.mongodb_host,
                port=settings.mongodb_port,
                db_name=settings.mongodb_database,
                username=settings.mongodb_username,
                password=settings.mongodb_password,
            )
            storage.connect()
            return storage, storage.db.get_collection("news")
        except Exception as e:
            self._logger.error(f"NewsEventWatcher MongoDB connect error: {e}")
            return None, None

    def collect(self) -> Optional[Dict[str, Any]]:
        storage = None
        try:
            storage, coll = self._get_mongo_collection()
            if coll is not None:
                since = datetime.now() - timedelta(hours=6)
                cursor = coll.find(
                    {"crawlTime": {"$gte": since}},
                    {
                        "title": 1,
                        "summary": 1,
                        "showTime": 1,
                        "stockList": 1,
                    },
                ).sort("crawlTime", -1).limit(50)
                news_items = []
                for doc in cursor:
                    stock_codes = self._parse_stock_list(doc.get("stockList", []))
                    news_items.append(
                        {
                            "title": doc.get("title", ""),
                            "content": doc.get("summary", ""),
                            "time": str(doc.get("showTime", "")),
                            "stock_codes": stock_codes,
                        }
                    )
                if news_items:
                    return {"news": news_items, "timestamp": datetime.now()}
                self._logger.info("No recent news in MongoDB, falling back to akshare")
        except Exception as e:
            self._logger.error(f"NewsEventWatcher collect from MongoDB error: {e}")
        finally:
            if storage:
                try:
                    storage.close()
                except Exception:
                    pass

        try:
            import akshare as ak

            news_list = ak.stock_news_em(symbol="A股")
            if news_list is None or news_list.empty:
                return {"news": [], "timestamp": datetime.now()}
            recent = news_list.head(20)
            return {
                "news": [
                    {
                        "title": str(row.get("新闻标题", "")),
                        "content": str(row.get("新闻内容", "")),
                        "time": str(row.get("发布时间", "")),
                        "stock_codes": [],
                    }
                    for _, row in recent.iterrows()
                ],
                "timestamp": datetime.now(),
            }
        except Exception as e:
            self._logger.error(f"NewsEventWatcher collect from akshare error: {e}")
            return {"news": [], "timestamp": datetime.now()}

    def evaluate(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        signals = []
        news_list = data.get("news", [])
        keyword_rules = self.keyword_rules

        now = datetime.now()

        for news in news_list:
            title = news.get("title", "")
            content = news.get("content", "")
            text = title + content
            stock_codes = news.get("stock_codes", [])

            for category, keywords in keyword_rules.items():
                for keyword in keywords:
                    if keyword not in text:
                        continue

                    key = f"{category}:{keyword}"

                    if key in self._last_triggered:
                        last = self._last_triggered[key]
                        if (now - last).total_seconds() < self._cooldown_seconds:
                            continue

                    self._last_triggered[key] = now

                    signal_map = {
                        "政策": ("buy", "medium"),
                        "利好": ("buy", "high"),
                        "利空": ("sell", "high"),
                        "业绩": ("buy", "medium"),
                        "黑天鹅": ("sell", "critical"),
                    }
                    signal_action, priority = signal_map.get(
                        category, ("hold", "low")
                    )

                    if signal_action == "hold":
                        break

                    mentioned_stocks = stock_codes if stock_codes else self._extract_stock_codes_from_text(text)

                    if mentioned_stocks:
                        for stock in mentioned_stocks[:5]:
                            signals.append(
                                {
                                    "code": stock["code"],
                                    "name": stock["name"],
                                    "signal": signal_action,
                                    "confidence": 0.75
                                    if priority != "critical"
                                    else 0.95,
                                    "priority": priority,
                                    "reasons": [
                                        f"新闻命中关键词「{keyword}」: {title[:50]}"
                                    ],
                                    "alert_type": "news",
                                    "strategy_type": "event",
                                    "price": 0.0,
                                    "volume_ratio": 0.0,
                                }
                            )
                    else:
                        signals.append(
                            {
                                "code": "MARKET",
                                "name": f"大盘新闻: {keyword}",
                                "signal": signal_action,
                                "confidence": 0.6
                                if priority != "critical"
                                else 0.85,
                                "priority": priority,
                                "reasons": [
                                    f"新闻命中关键词「{keyword}」(未关联个股): {title[:50]}"
                                ],
                                "alert_type": "news",
                                "strategy_type": "event",
                                "price": 0.0,
                                "volume_ratio": 0.0,
                            }
                        )
                    break

        return signals
