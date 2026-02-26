import requests
import hmac
import hashlib
import base64
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DingTalkNotifier:
    def __init__(self, webhook_url: str, secret: str = ""):
        self.webhook_url = webhook_url
        self.secret = secret

    def _sign(self, timestamp: int) -> str:
        if not self.secret:
            return ""
        
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return sign

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
        
        msg_parts = [f"## 📊 盘后信息 {date}\n"]
        
        market = data.get('market_overview', {})
        indices = market.get('indices', [])
        if indices:
            msg_parts.append("### 🔹 大盘指数\n")
            for idx in indices:
                name = idx.get('name', '')
                close = idx.get('close', 0)
                pct_chg = idx.get('pct_chg', 0)
                trend_emoji = "📈" if pct_chg > 0 else "📉" if pct_chg < 0 else "➡️"
                msg_parts.append(f"- {name}: {close:.2f} ({trend_emoji} {pct_chg:+.2f}%)\n")
        
        stats = market.get('stats', {})
        if stats:
            msg_parts.append("\n### 🔹 市场统计\n")
            msg_parts.append(f"- 上涨: {stats.get('up_count', 0)} 家\n")
            msg_parts.append(f"- 下跌: {stats.get('down_count', 0)} 家\n")
            msg_parts.append(f"- 涨停: {stats.get('limit_up', 0)} 家\n")
            msg_parts.append(f"- 跌停: {stats.get('limit_down', 0)} 家\n")
        
        sectors = data.get('sectors', [])
        if sectors:
            msg_parts.append("\n### 🔹 板块热点 (Top 5)\n")
            for sector in sectors[:5]:
                name = sector.get('name', '')
                pct_chg = sector.get('pct_chg', 0)
                msg_parts.append(f"- {name}: {pct_chg:+.2f}%\n")
        
        news = data.get('news', [])
        if news:
            msg_parts.append(f"\n### 🔹 今日新闻 ({len(news)}条)\n")
            for item in news[:3]:
                title = item.get('title', '')[:50]
                if len(title) >= 50:
                    title += "..."
                msg_parts.append(f"- {title}\n")
        
        rec = data.get('recommendations', {})
        if rec:
            msg_parts.append("\n### 🔹 明日操作建议\n")
            market_rec = rec.get('market', {})
            msg_parts.append(f"- **趋势**: {market_rec.get('trend', '震荡')}\n")
            msg_parts.append(f"- **仓位**: {market_rec.get('position', '5成')}\n")
            msg_parts.append(f"- **风险**: {market_rec.get('risk', '无')}\n")
        
        msg_parts.append(f"\n---\n*发布时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        
        return "".join(msg_parts)
