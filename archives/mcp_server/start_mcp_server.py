# -*- coding: utf-8 -*-
"""
PDF转Markdown MCP服务启动脚本

此脚本用于启动一个HTTP服务器，提供PDF转Markdown服务的远程访问功能。
支持通过HTTP API进行服务调用。
"""

import os
import sys
import json
import logging
import argparse
import threading
import traceback
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional, Tuple

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入MCP服务模块和配置
from mcp_service_config import MCPConfig, DEFAULT_CONFIG
from __init__ import invoke, get_service_info

# 配置日志
logging.basicConfig(
    level=getattr(logging, DEFAULT_CONFIG.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(DEFAULT_CONFIG.log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('mcp-server')

class MCPRequestHandler(BaseHTTPRequestHandler):
    """
    处理MCP服务HTTP请求的处理器
    """
    
    def __init__(self, *args, **kwargs):
        self.config = DEFAULT_CONFIG  # 使用全局配置
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """
        处理GET请求 - 主要用于健康检查和服务信息
        """
        if self.path == '/health':
            self._handle_health_check()
        elif self.path == '/info':
            self._handle_service_info()
        elif self.path == '/':
            self._handle_root()
        else:
            self._send_error(404, "路径不存在")
    
    def do_POST(self):
        """
        处理POST请求 - 主要用于服务调用
        """
        if self.path == '/api/invoke':
            # 检查认证
            if not self._check_auth():
                self._send_error(401, "未授权访问")
                return
                
            # 处理服务调用
            self._handle_invoke()
        else:
            self._send_error(404, "路径不存在")
    
    def _check_auth(self) -> bool:
        """
        检查请求的认证信息
        """
        if not self.config.require_auth:
            return True
            
        # 从请求头获取API密钥
        auth_header = self.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            api_key = auth_header[7:]  # 移除 'Bearer ' 前缀
            return api_key == self.config.api_key
        
        return False
    
    def _handle_health_check(self):
        """
        处理健康检查请求
        """
        try:
            # 调用健康检查接口
            result = invoke('health_check', {})
            self._send_json_response(200, result)
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            self._send_json_response(500, {
                'status': 'error',
                'message': f'健康检查失败: {str(e)}'
            })
    
    def _handle_service_info(self):
        """
        处理服务信息请求
        """
        try:
            service_info = get_service_info()
            # 添加运行时信息
            runtime_info = {
                'server_time': datetime.now().isoformat(),
                'python_version': sys.version,
                'config_summary': {
                    'host': self.config.host,
                    'port': self.config.port,
                    'require_auth': self.config.require_auth,
                    'log_level': self.config.log_level
                }
            }
            response = {
                'service_info': service_info,
                'runtime_info': runtime_info
            }
            self._send_json_response(200, response)
        except Exception as e:
            logger.error(f"获取服务信息失败: {str(e)}")
            self._send_json_response(500, {
                'status': 'error',
                'message': f'获取服务信息失败: {str(e)}'
            })
    
    def _handle_root(self):
        """
        处理根路径请求，返回服务信息页面
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PDF转Markdown MCP服务</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333; }}
                .info {{ background-color: #f5f5f5; padding: 20px; border-radius: 5px; }}
                .endpoint {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                code {{ background-color: #eee; padding: 2px 5px; }}
            </style>
        </head>
        <body>
            <h1>PDF转Markdown MCP服务</h1>
            <div class="info">
                <p>服务版本: {DEFAULT_CONFIG.service_version}</p>
                <p>运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>健康检查: <a href="/health">/health</a></p>
                <p>服务信息: <a href="/info">/info</a></p>
            </div>
            
            <h2>API端点</h2>
            <div class="endpoint">
                <h3>调用服务</h3>
                <p>POST <code>/api/invoke</code></p>
                <p>请求体示例:</p>
                <pre>{json.dumps({
                    "method": "convert_pdf_to_md",
                    "params": {"file_path": "/path/to/document.pdf"}
                }, indent=2)}</pre>
            </div>
        </body>
        </html>
        """
        self._send_text_response(200, html_content, 'text/html')
    
    def _handle_invoke(self):
        """
        处理服务调用请求
        """
        try:
            # 读取请求体
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                request_body = self.rfile.read(content_length).decode('utf-8')
                request_data = json.loads(request_body)
            else:
                request_data = {}
            
            # 验证请求数据
            if 'method' not in request_data:
                self._send_json_response(400, {
                    'status': 'error',
                    'message': '缺少必要参数: method'
                })
                return
            
            # 提取方法名和参数
            method = request_data['method']
            params = request_data.get('params', {})
            
            logger.info(f"收到调用请求: method={method}")
            
            # 调用服务方法
            result = invoke(method, params)
            
            # 返回结果
            self._send_json_response(200, result)
            
        except json.JSONDecodeError:
            self._send_json_response(400, {
                'status': 'error',
                'message': '无效的JSON格式'
            })
        except Exception as e:
            logger.error(f"处理服务调用时出错: {str(e)}")
            logger.error(traceback.format_exc())
            self._send_json_response(500, {
                'status': 'error',
                'message': f'处理请求时出错: {str(e)}'
            })
    
    def _send_json_response(self, status_code: int, data: Dict[str, Any]):
        """
        发送JSON格式的响应
        """
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')  # 允许跨域访问
        self.end_headers()
        
        response_json = json.dumps(data, ensure_ascii=False)
        self.wfile.write(response_json.encode('utf-8'))
    
    def _send_text_response(self, status_code: int, content: str, content_type: str = 'text/plain'):
        """
        发送文本格式的响应
        """
        self.send_response(status_code)
        self.send_header('Content-Type', f'{content_type}; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def _send_error(self, status_code: int, message: str):
        """
        发送错误响应
        """
        self._send_json_response(status_code, {
            'status': 'error',
            'message': message
        })
    
    def log_message(self, format, *args):
        """
        覆盖日志方法，使用Python的logging模块
        """
        logger.info(f"{self.client_address[0]} - {format % args}")

def run_server(config: MCPConfig = None):
    """
    运行MCP服务HTTP服务器
    
    Args:
        config: MCP配置对象
    """
    # 使用提供的配置或默认配置
    if config is not None:
        global DEFAULT_CONFIG
        DEFAULT_CONFIG = config
    
    # 创建服务器
    server_address = (DEFAULT_CONFIG.host, DEFAULT_CONFIG.port)
    httpd = HTTPServer(server_address, MCPRequestHandler)
    
    logger.info(f"PDF转Markdown MCP服务启动中...")
    logger.info(f"服务版本: {DEFAULT_CONFIG.service_version}")
    logger.info(f"监听地址: http://{DEFAULT_CONFIG.host}:{DEFAULT_CONFIG.port}")
    logger.info(f"健康检查: http://{DEFAULT_CONFIG.host}:{DEFAULT_CONFIG.port}/health")
    logger.info(f"服务信息: http://{DEFAULT_CONFIG.host}:{DEFAULT_CONFIG.port}/info")
    logger.info(f"API接口: http://{DEFAULT_CONFIG.host}:{DEFAULT_CONFIG.port}/api/invoke")
    
    if DEFAULT_CONFIG.require_auth:
        logger.warning("认证已启用，请确保在请求中提供有效的API密钥")
    else:
        logger.warning("警告: 认证未启用，服务可能存在安全风险")
    
    try:
        # 启动服务器
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"服务器运行出错: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        # 关闭服务器
        httpd.server_close()
        logger.info("服务已关闭")

def main():
    """
    主函数 - 处理命令行参数并启动服务
    """
    parser = argparse.ArgumentParser(description='PDF转Markdown MCP服务')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--host', type=str, help='服务器监听地址')
    parser.add_argument('--port', type=int, help='服务器监听端口')
    parser.add_argument('--auth', action='store_true', help='启用API认证')
    parser.add_argument('--api-key', type=str, help='API密钥')
    parser.add_argument('--log-level', type=str, help='日志级别')
    
    args = parser.parse_args()
    
    # 创建配置
    if args.config:
        config = MCPConfig(args.config)
    else:
        config = DEFAULT_CONFIG
    
    # 从命令行参数覆盖配置
    if args.host:
        config.host = args.host
    if args.port:
        config.port = args.port
    if args.auth:
        config.require_auth = True
    if args.api_key:
        config.require_auth = True
        config.api_key = args.api_key
    if args.log_level:
        config.log_level = args.log_level
        # 更新日志级别
        logger.setLevel(getattr(logging, config.log_level))
    
    # 启动服务
    run_server(config)

if __name__ == "__main__":
    main()