# -*- coding: utf-8 -*-
"""
Trae AI MCP服务启动脚本

此脚本启动一个兼容Trae AI的MCP服务器，提供PDF转Markdown功能。
服务器将监听HTTP请求，接受Trae AI的工具调用格式。
"""

import os
import sys
import json
import logging
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入Trae AI适配器
from trae_adapter import execute_tool, health_check, get_tool_definition

# 确保日志目录存在
log_dir = os.path.join(os.path.dirname(__file__), 'log')
os.makedirs(log_dir, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - traer-server - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(log_dir, 'traer_server.log'))
    ]
)
logger = logging.getLogger('traer-server')

class TraerRequestHandler(BaseHTTPRequestHandler):
    """
    处理Trae AI格式的HTTP请求
    """
    
    def do_GET(self):
        """处理GET请求（健康检查、工具定义）"""
        if self.path == '/health':
            self._handle_health_check()
        elif self.path == '/tool-definition':
            self._handle_tool_definition()
        elif self.path == '/':
            self._handle_root()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """处理POST请求（工具执行）"""
        if self.path == '/execute':
            self._handle_execute()
        else:
            self.send_error(404, "Not Found")
    
    def _handle_health_check(self):
        """处理健康检查请求"""
        try:
            result = health_check()
            self._send_json_response(200, result)
        except Exception as e:
            logger.error(f"健康检查失败: {str(e)}")
            self._send_json_response(500, {
                "status": "error",
                "message": "健康检查失败"
            })
    
    def _handle_tool_definition(self):
        """处理工具定义请求"""
        try:
            definition = get_tool_definition()
            self._send_json_response(200, definition)
        except Exception as e:
            logger.error(f"获取工具定义失败: {str(e)}")
            self._send_json_response(500, {
                "status": "error",
                "message": "获取工具定义失败"
            })
    
    def _handle_execute(self):
        """处理工具执行请求"""
        try:
            # 读取请求体
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # 解析JSON请求
            params = json.loads(post_data)
            logger.info(f"收到执行请求: {params}")
            
            # 执行工具
            result = execute_tool(params)
            
            # 返回结果
            status_code = 200 if result.get('status') == 'success' else 400
            self._send_json_response(status_code, result)
            
        except json.JSONDecodeError:
            logger.error("无效的JSON格式")
            self._send_json_response(400, {
                "status": "error",
                "message": "无效的JSON格式"
            })
        except Exception as e:
            logger.error(f"执行请求处理失败: {str(e)}")
            self._send_json_response(500, {
                "status": "error",
                "message": f"服务器内部错误: {str(e)}"
            })
    
    def _handle_root(self):
        """处理根路径请求，返回服务信息"""
        info = {
            "service": "PDF转Markdown Trae AI服务",
            "version": "1.0.0",
            "endpoints": {
                "GET /": "服务信息",
                "GET /health": "健康检查",
                "GET /tool-definition": "获取工具定义",
                "POST /execute": "执行转换工具"
            },
            "status": "running"
        }
        
        html_response = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PDF转Markdown Trae AI服务</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #333366; }}
                .endpoint {{ margin: 10px 0; padding: 10px; background-color: #f0f0f0; border-radius: 5px; }}
                .version {{ color: #666; }}
                .status {{ display: inline-block; padding: 5px 10px; background-color: #4CAF50; color: white; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <h1>PDF转Markdown Trae AI服务</h1>
            <div class="version">版本: {info['version']}</div>
            <div class="status">状态: {info['status']}</div>
            
            <h2>可用接口</h2>
            {''.join([f'<div class="endpoint"><strong>{info["endpoints"][k]}:</strong> {k}</div>' 
                     for k in info['endpoints'].keys()])}
            
            <h2>使用说明</h2>
            <p>此服务提供PDF转Markdown功能，可通过HTTP API进行调用。</p>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html_response.encode('utf-8'))
    
    def _send_json_response(self, status_code, data):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')  # 允许跨域请求
        self.end_headers()
        
        response_json = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.wfile.write(response_json)
    
    def log_message(self, format, *args):
        """覆盖日志方法，使用自定义日志"""
        logger.info(f"{self.client_address[0]} - {format % args}")

def run_server(host, port):
    """
    启动HTTP服务器
    
    Args:
        host: 主机地址
        port: 端口号
    """
    server_address = (host, port)
    httpd = HTTPServer(server_address, TraerRequestHandler)
    
    logger.info(f"Trae AI MCP服务器启动成功")
    logger.info(f"监听地址: http://{host}:{port}")
    logger.info(f"健康检查: http://{host}:{port}/health")
    logger.info(f"工具定义: http://{host}:{port}/tool-definition")
    logger.info(f"执行接口: http://{host}:{port}/execute (POST)")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在关闭服务器...")
    finally:
        httpd.server_close()
        logger.info("服务器已关闭")

def main():
    """
    主函数，解析命令行参数并启动服务器
    """
    parser = argparse.ArgumentParser(description='PDF转Markdown Trae AI服务')
    parser.add_argument('--host', type=str, default='127.0.0.1',
                        help='服务器主机地址')
    parser.add_argument('--port', type=int, default=8081,
                        help='服务器端口号')
    
    args = parser.parse_args()
    
    # 确保输出目录存在
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    temp_dir = os.path.join(os.path.dirname(__file__), 'temp')
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)
    
    logger.info(f"输出目录: {os.path.abspath(output_dir)}")
    logger.info(f"临时目录: {os.path.abspath(temp_dir)}")
    
    # 启动服务器
    run_server(args.host, args.port)

if __name__ == '__main__':
    main()