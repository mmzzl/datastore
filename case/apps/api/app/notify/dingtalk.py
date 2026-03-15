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
            logger.warning("AkshareClient is None, cannot initialize without target_date")
            logger.warning("Please ensure AkshareClient is passed to DingTalkNotifier constructor")
            self.akshare_client = None
        else:
            logger.debug("Using provided AkshareClient")

    def send(self, msg: str, max_retries: int = 10) -> bool:
        if not self.webhook_url:
            logger.warning("DingTalk webhook_url is empty, skip sending")
            return False

        for attempt in range(max_retries):
            timestamp = int(datetime.now().timestamp() * 1000) 
            params = {"timestamp": timestamp, "sign": self._sign(timestamp)} if self.secret else {}
            date = datetime.now().strftime("%Y-%m-%d")
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"📊 盘后信息 {date}",
                    "text": msg
                }
            }
            try:
                resp = requests.post(self.webhook_url, json=payload, params=params, timeout=10)
                if resp.status_code == 200:
                    result = resp.json()
                    if result.get("errcode") == 0:
                        logger.info(f"DingTalk notification sent successfully for {date}")
                        return True
                    else:
                        logger.error(f"DingTalk API error: {result}")
                        if attempt < max_retries - 1:
                            logger.warning(f"重试发送钉钉消息 ({attempt + 1}/{max_retries})...")
                            import time
                            time.sleep(2)
                else:
                    logger.error(f"DingTalk HTTP error: {resp.status_code}")
                    if attempt < max_retries - 1:
                        logger.warning(f"重试发送钉钉消息 ({attempt + 1}/{max_retries})...")
                        import time
                        time.sleep(2)
            except requests.RequestException as e:
                logger.error(f"DingTalk request failed: {e}")
                if attempt < max_retries - 1:
                    logger.warning(f"重试发送钉钉消息 ({attempt + 1}/{max_retries})...")
                    import time
                    time.sleep(2)
        
        logger.error(f"DingTalk notification failed after {max_retries} attempts")
        return False
