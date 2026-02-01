# -*- coding: utf-8 -*-
# 钉钉机器人发送模块
import requests
import json
import hmac
import hashlib
import base64
import time
from typing import Optional


class DingTalkBot:
    """钉钉机器人发送工具"""
    
    def __init__(self, webhook_url: str, secret: Optional[str] = None):
        """
        初始化钉钉机器人
        
        Args:
            webhook_url: 钉钉机器人 Webhook URL
            secret: 钉钉机器人加签密钥（可选）
        """
        self.webhook_url = webhook_url
        self.secret = secret
    
    def _generate_sign(self, timestamp: int) -> str:
        """生成钉钉机器人签名"""
        if not self.secret:
            return ""
        
        string_to_sign = f"{timestamp}\n{self.secret}"
        hmac_code = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign
    
    def send_text(self, text: str, at_mobiles: Optional[list] = None, at_all: bool = False):
        """
        发送文本消息
        
        Args:
            text: 文本内容
            at_mobiles: @的手机号列表
            at_all: 是否@所有人
            
        Returns:
            bool: 是否发送成功
        """
        timestamp = int(time.time() * 1000)
        sign = self._generate_sign(timestamp)
        
        url = self.webhook_url
        if sign:
            url += f"&timestamp={timestamp}&sign={sign}"
        
        data = {
            "msgtype": "text",
            "text": {
                "content": text
            },
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": at_all
            }
        }
        
        return self._send_request(url, data)
    
    def send_markdown(self, text: str, title: Optional[str] = None, at_mobiles: Optional[list] = None, at_all: bool = False):
        """
        发送 Markdown 消息
        
        Args:
            text: Markdown 内容
            title: 消息标题（仅支持部分消息类型）
            at_mobiles: @的手机号列表
            at_all: 是否@所有人
            
        Returns:
            bool: 是否发送成功
        """
        timestamp = int(time.time() * 1000)
        sign = self._generate_sign(timestamp)
        
        url = self.webhook_url
        if sign:
            url += f"&timestamp={timestamp}&sign={sign}"
        
        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title or "每日简报",
                "text": text
            },
            "at": {
                "atMobiles": at_mobiles or [],
                "isAtAll": at_all
            }
        }
        
        return self._send_request(url, data)
    
    def _send_request(self, url: str, data: dict) -> bool:
        """
        发送 HTTP 请求
        
        Args:
            url: 请求 URL
            data: 请求数据
            
        Returns:
            bool: 是否发送成功
        """
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                url,
                headers=headers,
                data=json.dumps(data),
                timeout=10
            )
            
            result = response.json()
            
            if result.get('errcode') == 0:
                return True
            else:
                print(f"钉钉发送失败: {result.get('errmsg', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"钉钉发送异常: {e}")
            return False
