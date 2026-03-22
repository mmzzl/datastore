from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from .base import BaseWatcher


class NewsEventWatcher(BaseWatcher):
    def __init__(self, data_manager=None, keyword_rules: Dict[str, List[str]] = None):
        super().__init__(data_manager)
        self.keyword_rules = keyword_rules or {}
        self._last_triggered: Dict[str, datetime] = {}
        self._cooldown_seconds = 300

    def collect(self) -> Optional[Dict[str, Any]]:
        try:
            import akshare as ak

            news_list = ak.stock_news_em(symbol="A股")
            if news_list is None or news_list.empty:
                return {"news": [], "timestamp": datetime.now()}
            recent = news_list.head(20)
            return {
                "news": [
                    {
                        "title": row.get("新闻标题", ""),
                        "content": row.get("新闻内容", ""),
                        "time": row.get("发布时间", ""),
                    }
                    for _, row in recent.iterrows()
                ],
                "timestamp": datetime.now(),
            }
        except Exception as e:
            self._logger.error(f"NewsEventWatcher collect error: {e}")
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

            for category, keywords in keyword_rules.items():
                for keyword in keywords:
                    if keyword in text:
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

                        if signal_action != "hold":
                            signals.append(
                                {
                                    "code": category,
                                    "name": f"新闻事件: {keyword}",
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
                            break

        return signals
