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
                        msg_parts.append("\n### 🔹 新闻分析 (AI)\n")
                        
                        def format_analysis_value(value, indent="  "):
                            """递归格式化分析值"""
                            if isinstance(value, dict):
                                result = []
                                for k, v in value.items():
                                    if isinstance(v, (list, dict)):
                                        result.append(f"{indent}{k}:\n")
                                        result.append(format_analysis_value(v, indent + "  "))
                                    elif isinstance(v, str):
                                        result.append(f"{indent}{v}\n")
                                    else:
                                        result.append(f"{indent}{k}: {v}\n")
                                return "".join(result)
                            elif isinstance(value, list):
                                result = []
                                for item in value:
                                    if isinstance(item, dict):
                                        result.append(format_analysis_value(item, indent))
                                    else:
                                        result.append(f"{indent}- {item}\n")
                                return "".join(result)
                            elif isinstance(value, str):
                                lines = value.split('\n')
                                result = []
                                for line in lines:
                                    if line.strip():
                                        result.append(f"{indent}{line}\n")
                                return "".join(result)
                            else:
                                return f"{indent}{value}\n"
                        
                        msg_parts.append(format_analysis_value(news_analysis))
                        msg_parts.append(f"\n---\n*发布时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
                        return "".join(msg_parts)
                    
                    return akshare_msg
            except Exception as e:
                logger.warning(f"Failed to use AkshareClient format: {e}")
        
        # 如果 AkshareClient 失败，返回空消息
        logger.error("Failed to build message")
        return f"## 📊 每日收盘简报 {date}\n\n消息生成失败，请检查日志。"
