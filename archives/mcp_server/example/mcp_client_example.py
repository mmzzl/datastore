# -*- coding: utf-8 -*-
"""
PDF转Markdown MCP服务客户端示例

此脚本展示如何远程调用PDF转Markdown MCP服务的API接口。
提供了同步和异步两种调用方式。
"""

import os
import json
import time
import logging
import requests
from typing import Dict, Any, Optional, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mcp-client')

class MCPRemoteClient:
    """
    MCP服务远程客户端
    提供与远程MCP服务交互的方法
    """
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        """
        初始化客户端
        
        Args:
            base_url: MCP服务基础URL，例如: http://localhost:8080
            api_key: API密钥（如果服务需要认证）
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        # 设置默认请求头
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        # 如果提供了API密钥，设置认证头
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}'
            })
    
    def _make_request(self, endpoint: str, method: str = 'GET', 
                     data: Optional[Dict[str, Any]] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        发送HTTP请求到MCP服务
        
        Args:
            endpoint: API端点
            method: HTTP方法
            data: 请求数据
        
        Returns:
            Tuple[bool, Dict]: (是否成功, 响应数据)
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.upper() == 'GET':
                response = self.session.get(url, timeout=30)
            elif method.upper() == 'POST':
                response = self.session.post(
                    url, 
                    json=data, 
                    timeout=30
                )
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            # 检查响应状态
            response.raise_for_status()
            
            # 尝试解析JSON响应
            response_data = response.json()
            return True, response_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {str(e)}")
            return False, {
                'status': 'error',
                'message': f'请求失败: {str(e)}'
            }
        except json.JSONDecodeError:
            logger.error("无法解析响应为JSON格式")
            return False, {
                'status': 'error',
                'message': '无法解析响应为JSON格式'
            }
    
    def health_check(self) -> Tuple[bool, Dict[str, Any]]:
        """
        检查服务健康状态
        
        Returns:
            Tuple[bool, Dict]: (是否健康, 健康状态信息)
        """
        success, data = self._make_request('/health')
        if success:
            is_healthy = data.get('status') == 'healthy'
            return is_healthy, data
        return False, data
    
    def get_service_info(self) -> Tuple[bool, Dict[str, Any]]:
        """
        获取服务信息
        
        Returns:
            Tuple[bool, Dict]: (是否成功, 服务信息)
        """
        return self._make_request('/info')
    
    def invoke_service(self, method: str, params: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        调用MCP服务方法
        
        Args:
            method: 要调用的方法名
            params: 方法参数
        
        Returns:
            Tuple[bool, Dict]: (是否成功, 调用结果)
        """
        request_data = {
            'method': method,
            'params': params
        }
        
        logger.info(f"调用服务方法: {method}")
        start_time = time.time()
        
        success, data = self._make_request(
            '/api/invoke',
            method='POST',
            data=request_data
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"服务调用完成，耗时: {elapsed_time:.2f}秒")
        
        return success, data
    
    def convert_pdf_to_md(self, file_path: str, 
                         tesseract_cmd: Optional[str] = None,
                         poppler_path: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
        """
        转换PDF文件为Markdown
        
        Args:
            file_path: PDF文件路径
            tesseract_cmd: Tesseract OCR路径（可选）
            poppler_path: Poppler路径（可选）
        
        Returns:
            Tuple[bool, Dict]: (是否成功, 转换结果)
        """
        params = {
            'file_path': file_path
        }
        
        if tesseract_cmd:
            params['tesseract_cmd'] = tesseract_cmd
        if poppler_path:
            params['poppler_path'] = poppler_path
        
        return self.invoke_service('convert_pdf_to_md', params)
    
    def update_service_config(self, config: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        更新服务配置
        
        Args:
            config: 配置参数
        
        Returns:
            Tuple[bool, Dict]: (是否成功, 更新结果)
        """
        return self.invoke_service('update_config', config)

def sync_client_example():
    """
    同步客户端调用示例
    """
    print("\n=== 同步客户端调用示例 ===")
    
    # 创建客户端实例
    # 注意: 替换为实际的服务地址和API密钥
    client = MCPRemoteClient(
        base_url="http://localhost:8080",
        api_key="your-api-key-if-required"
    )
    
    # 1. 健康检查
    print("\n1. 执行健康检查...")
    success, data = client.health_check()
    print(f"健康检查结果: {'成功' if success else '失败'}")
    print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    # 2. 获取服务信息
    print("\n2. 获取服务信息...")
    success, data = client.get_service_info()
    print(f"获取服务信息: {'成功' if success else '失败'}")
    if success:
        print(f"服务名称: {data.get('service_info', {}).get('name')}")
        print(f"服务版本: {data.get('service_info', {}).get('version')}")
    
    # 3. 转换PDF文件（示例）
    print("\n3. 转换PDF文件示例...")
    # 注意: 替换为实际的PDF文件路径
    test_pdf_path = "/path/to/your/document.pdf"
    
    # 检查文件是否存在（仅在本地运行时有效）
    if os.path.exists(test_pdf_path):
        success, data = client.convert_pdf_to_md(test_pdf_path)
        print(f"转换PDF: {'成功' if success else '失败'}")
        if success:
            print(f"输出文件: {data.get('data', {}).get('output_file')}")
            print(f"内容预览: {data.get('data', {}).get('content_preview')}")
        else:
            print(f"错误信息: {data.get('message')}")
    else:
        print(f"注意: 测试PDF文件不存在 - {test_pdf_path}")
        print("请在实际使用时替换为有效的PDF文件路径")

def async_client_example():
    """
    异步客户端调用示例（使用线程模拟）
    
    注: 如需真正的异步支持，可以使用Python的asyncio和aiohttp库
    """
    print("\n=== 异步客户端调用示例（使用线程）===")
    
    def async_convert_task(pdf_path: str, client: MCPRemoteClient):
        """异步转换任务"""
        print(f"开始转换: {pdf_path}")
        success, data = client.convert_pdf_to_md(pdf_path)
        print(f"转换完成: {pdf_path}, 成功: {success}")
        if success:
            print(f"  输出文件: {data.get('data', {}).get('output_file')}")
    
    # 创建客户端
    client = MCPRemoteClient(
        base_url="http://localhost:8080"
    )
    
    # 创建并启动多个转换任务
    # 注意: 替换为实际的PDF文件路径列表
    test_pdfs = [
        "/path/to/pdf1.pdf",
        "/path/to/pdf2.pdf",
        "/path/to/pdf3.pdf"
    ]
    
    threads = []
    for pdf_path in test_pdfs:
        if os.path.exists(pdf_path) or "path/to" in pdf_path:  # 允许示例路径
            thread = threading.Thread(
                target=async_convert_task,
                args=(pdf_path, client)
            )
            threads.append(thread)
            thread.start()
    
    # 等待所有任务完成
    for thread in threads:
        thread.join()
    
    print("\n所有异步任务已完成")

def command_line_example():
    """
    命令行调用示例
    """
    print("\n=== 命令行调用示例 ===")
    print("\n使用curl调用服务:")
    print("# 健康检查")
    print("curl http://localhost:8080/health")
    
    print("\n# 转换PDF文件")
    print("curl -X POST \\\n" \
          "  -H 'Content-Type: application/json' \\\n" \
          "  -H 'Authorization: Bearer your-api-key-if-required' \\\n" \
          "  -d '{\"method\":\"convert_pdf_to_md\",\"params\":{\"file_path\":\"/path/to/document.pdf\"}}' \\\n" \
          "  http://localhost:8080/api/invoke")
    
    print("\n使用Python requests库:")
    print("""
import requests
import json

url = "http://localhost:8080/api/invoke"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your-api-key-if-required"
}
data = {
    "method": "convert_pdf_to_md",
    "params": {
        "file_path": "/path/to/document.pdf"
    }
}

response = requests.post(url, headers=headers, json=data)
result = response.json()
print(json.dumps(result, indent=2))
""")

# 添加线程导入，用于异步示例
import threading

def main():
    """
    主函数 - 运行所有示例
    """
    print("PDF转Markdown MCP服务客户端示例")
    print("================================")
    
    # 运行同步示例
    sync_client_example()
    
    # 运行命令行示例
    command_line_example()
    
    # 注释掉异步示例，需要实际的PDF文件路径才能运行
    # async_client_example()
    
    print("\n================================")
    print("使用说明:")
    print("1. 确保MCP服务已在指定地址运行")
    print("2. 在代码中替换正确的服务地址和API密钥")
    print("3. 提供有效的PDF文件路径")
    print("4. 检查服务返回的错误信息以排查问题")

if __name__ == "__main__":
    main()