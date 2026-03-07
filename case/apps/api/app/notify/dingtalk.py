import requests
import hmac
import hashlib
import base64
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from ..collector import AkshareClient

logger = logging.getLogger(__name__)


class DingTalkNotifier:
    def __init__(self, webhook_url: str, secret: str = "", akshare_client=None):
        self.webhook_url = webhook_url
        self.secret = secret
        self.akshare_client = akshare_client  # 接受外部传入的 AkshareClient

    def _sign(self, timestamp: int) -> str:
        if not self.secret:
            return ""
        
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign
    
    def _ensure_akshare_client(self):
        """确保 AkshareClient 已初始化"""
        if self.akshare_client is None:
            try:
                self.akshare_client = AkshareClient()
                logger.info("AkshareClient initialized for DingTalk notifications")
            except Exception as e:
                logger.error(f"Failed to initialize AkshareClient: {e}")
                self.akshare_client = None
        else:
            logger.debug("Using provided AkshareClient")

    def send(self, data: Dict[str, Any]) -> bool:
        if not self.webhook_url:
            logger.warning("DingTalk webhook_url is empty, skip sending")
            return False

        timestamp = int(datetime.now().timestamp() * 1000)
        
        msg = self._build_message(data)
        
        params = {"timestamp": timestamp, "sign": self._sign(timestamp)} if self.secret else {}
        
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": f"📊 盘后信息 {data.get('date', '')}",
                "text": msg
            }
        }
        
        try:
            resp = requests.post(self.webhook_url, json=payload, params=params, timeout=10)
            if resp.status_code == 200:
                result = resp.json()
                if result.get("errcode") == 0:
                    logger.info(f"DingTalk notification sent successfully for {data.get('date')}")
                    return True
                else:
                    logger.error(f"DingTalk API error: {result}")
                    return False
            else:
                logger.error(f"DingTalk HTTP error: {resp.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"DingTalk request failed: {e}")
            return False

    def _build_message(self, data: Dict[str, Any]) -> str:
        date = data.get('date', '')
        
        # 使用 AkshareClient 生成消息
        self._ensure_akshare_client()
        
        if self.akshare_client is not None:
            try:
                akshare_msg = self.akshare_client.format_brief_for_dingtalk(date)
                logger.info(f"AkshareClient message: {akshare_msg}")
                if akshare_msg:
                    logger.info(f"Using AkshareClient to format message for {date}")
                    
                    # 添加 deepseek 新闻分析（如果有）
                    news_analysis = data.get('news_analysis', {})
                    if news_analysis:
                        msg_parts = [akshare_msg]
                        msg_parts.append("\n### 📰 新闻分析 (AI)\n")
                        
                        # 格式化新闻分析
                        if isinstance(news_analysis, dict):
                            # 摘要 - 优先显示
                            if 'summary' in news_analysis:
                                msg_parts.append("#### 📝 市场摘要\n")
                                summary = news_analysis['summary']
                                msg_parts.append(f"{summary}\n\n")
                            
                            # 市场情绪
                            if 'sentiment' in news_analysis:
                                msg_parts.append("#### 📊 市场情绪\n")
                                sentiment = news_analysis['sentiment']
                                sentiment_emoji = {
                                    "利好": "🟢",
                                    "利空": "🔴",
                                    "中性": "⚪",
                                    "偏多": "🟢",
                                    "偏空": "🔴",
                                    "谨慎偏多": "🟡",
                                    "谨慎偏空": "🟡"
                                }
                                emoji = sentiment_emoji.get(sentiment, "⚪")
                                msg_parts.append(f"{emoji} **{sentiment}**\n\n")
                            
                            # 热门板块
                            if 'hot_sectors' in news_analysis:
                                msg_parts.append("#### 🔥 热门板块\n")
                                hot_sectors = news_analysis['hot_sectors']
                                if isinstance(hot_sectors, list):
                                    for sector in hot_sectors:
                                        msg_parts.append(f"- {sector}\n")
                                else:
                                    msg_parts.append(f"{hot_sectors}\n")
                                msg_parts.append("\n")
                            
                            # 热门股票
                            if 'hot_stocks' in news_analysis:
                                msg_parts.append("#### 📈 热门股票\n")
                                hot_stocks = news_analysis['hot_stocks']
                                if isinstance(hot_stocks, list):
                                    for stock in hot_stocks:
                                        msg_parts.append(f"- {stock}\n")
                                else:
                                    msg_parts.append(f"{hot_stocks}\n")
                                msg_parts.append("\n")
                            
                            # 明日策略
                            if 'tomorrow_strategy' in news_analysis:
                                msg_parts.append("#### 🎯 明日策略\n")
                                strategy = news_analysis['tomorrow_strategy']
                                if isinstance(strategy, dict):
                                    if 'direction' in strategy:
                                        msg_parts.append(f"**方向：** {strategy['direction']}\n")
                                    if 'attention' in strategy:
                                        msg_parts.append(f"**关注：** {strategy['attention']}\n")
                                    if 'risk' in strategy:
                                        msg_parts.append(f"**风险：** {strategy['risk']}\n")
                                    if '利好' in strategy:
                                        msg_parts.append(f"**利好板块：** {strategy['利好']}\n")
                                    if '风险' in strategy:
                                        msg_parts.append(f"**风险提示：** {strategy['风险']}\n")
                                    msg_parts.append("\n")
                                elif isinstance(strategy, str):
                                    msg_parts.append(f"{strategy}\n\n")
                            
                            # 关键事件
                            if 'key_events' in news_analysis:
                                msg_parts.append("#### ⚡ 关键事件\n")
                                key_events = news_analysis['key_events']
                                if isinstance(key_events, list):
                                    for event in key_events:
                                        msg_parts.append(f"- {event}\n")
                                else:
                                    msg_parts.append(f"{key_events}\n")
                                msg_parts.append("\n")
                            
                            # 其他字段（排除已处理的字段）
                            processed_keys = ['summary', 'sentiment', 'hot_sectors', 'hot_stocks', 'tomorrow_strategy', 'key_events']
                            for key, value in news_analysis.items():
                                if key not in processed_keys:
                                    msg_parts.append(f"#### {key}\n")
                                    if isinstance(value, list):
                                        for item in value:
                                            msg_parts.append(f"- {item}\n")
                                    elif isinstance(value, dict):
                                        for k, v in value.items():
                                            msg_parts.append(f"- {k}: {v}\n")
                                    else:
                                        msg_parts.append(f"{value}\n")
                                    msg_parts.append("\n")
                        
                        msg_parts.append(f"\n---\n*发布时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
                        return "".join(msg_parts)
                    
                    return akshare_msg
            except Exception as e:
                logger.warning(f"Failed to use AkshareClient format: {e}")
        
        # 如果 AkshareClient 失败，返回空消息
        logger.error("Failed to build message")
        return f"## 📊 每日收盘简报 {date}\n\n消息生成失败，请检查日志。"
