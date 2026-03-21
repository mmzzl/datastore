import os
import sys
import json
from django.conf import settings

# 配置Django设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.test_settings')

# 导入Django设置
import django
django.setup()

# 在测试前运行所有迁移
from django.core.management import call_command
print("Running migrations...")
call_command('migrate')
print("Migrations completed.")

# 现在可以导入和使用Django组件
from django.test import Client

# 创建测试客户端
client = Client()

# 准备注册数据
register_data = {
    'username': 'newuser',
    'email': 'new@example.com',
    'password': 'newpassword123',
    'password_confirm': 'newpassword123'
}

# 使用reverse函数获取正确的URL
from django.urls import reverse
url = reverse('authentication:register')
print(f"Using URL: {url}")

# 发送注册请求
response = client.post(
    url,
    json.dumps(register_data),
    content_type='application/json'
)

# 打印响应状态码和内容
print(f"Status Code: {response.status_code}")
print(f"Response Content: {response.content.decode('utf-8')}")
