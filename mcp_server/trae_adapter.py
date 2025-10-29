# -*- coding: utf-8 -*-
"""
Trae AI MCP适配器

此模块将PDF转Markdown MCP服务适配为Trae AI环境可用的工具格式。
提供了符合Trae AI规范的工具注册和调用接口。
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union

# 导入MCP服务核心功能
# 导入当前目录的模块
import importlib.util
import sys
import os

# 获取当前文件所在目录
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入pdftomd模块（假设与trae_adapter.py在同一目录）
spec = importlib.util.spec_from_file_location("pdftomd", os.path.join(os.path.dirname(__file__), "pdftomd.py"))
pdftomd_module = importlib.util.module_from_spec(spec)
sys.modules["pdftomd"] = pdftomd_module
spec.loader.exec_module(pdftomd_module)

# 现在可以从pdftomd导入需要的函数
from pdftomd import (
    pdftomd,
    convert_pdf_to_md,
    health_check as mcp_health_check,
    update_config,
    SERVICE_INFO
)

# 定义MCP调用函数
def mcp_invoke(method, params):
    """模拟原有的mcp_invoke函数"""
    endpoints = {
        'convert_pdf_to_md': convert_pdf_to_md,
        'health_check': mcp_health_check,
        'update_config': update_config
    }
    
    if method not in endpoints:
        return {
            'status': 'error',
            'message': f'未知的方法: {method}',
            'available_methods': list(endpoints.keys())
        }
    
    try:
        func = endpoints[method]
        result = func(params)
        return result
    except Exception as e:
        return {
            'status': 'error',
            'message': f'调用方法时出错: {str(e)}',
            'method': method
        }

def get_service_info():
    """获取服务信息"""
    return SERVICE_INFO

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - trae-adapter - %(levelname)s - %(message)s'
)
logger = logging.getLogger('trae-adapter')

# Trae AI工具定义
def get_tool_definition():
    """
    获取Trae AI工具定义
    
    Returns:
        dict: 符合Trae AI规范的工具定义
    """
    # 从MCP服务获取信息
    mcp_info = get_service_info()
    
    return {
        "name": "pdf_to_markdown_converter",
        "description": "将PDF文件转换为Markdown格式",
        "version": "1.0.0",
        "author": "MCP Team",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "PDF文件的完整路径",
                    "required": True
                },
                "tesseract_cmd": {
                    "type": "string",
                    "description": "Tesseract OCR可执行文件路径（可选）",
                    "required": False
                },
                "poppler_path": {
                    "type": "string",
                    "description": "Poppler二进制文件目录路径（可选）",
                    "required": False
                }
            }
        },
        "returns": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "操作状态: success 或 error"
                },
                "message": {
                    "type": "string",
                    "description": "操作结果消息"
                },
                "data": {
                    "type": "object",
                    "properties": {
                        "original_file": {"type": "string"},
                        "output_file": {"type": "string"},
                        "content_preview": {"type": "string"},
                        "content_length": {"type": "integer"}
                    }
                }
            }
        }
    }

# Trae AI工具执行函数
def execute_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行PDF转Markdown转换工具
    
    Args:
        params: 包含转换参数的字典
    
    Returns:
        dict: 转换结果
    """
    try:
        logger.info(f"开始执行PDF转Markdown: {params.get('file_path')}")
        
        # 验证必要参数
        if 'file_path' not in params:
            return {
                "status": "error",
                "message": "缺少必要参数: file_path"
            }
        
        # 检查文件是否存在
        file_path = params['file_path']
        if not os.path.exists(file_path):
            return {
                "status": "error",
                "message": f"PDF文件不存在: {file_path}"
            }
        
        # 检查文件格式
        if not file_path.lower().endswith('.pdf'):
            return {
                "status": "error",
                "message": "请提供PDF格式的文件"
            }
        
        # 通过MCP调用核心功能
        result = mcp_invoke("convert_pdf_to_md", params)
        
        logger.info(f"PDF转Markdown完成: {result.get('status')}")
        return result
        
    except Exception as e:
        logger.error(f"执行转换时出错: {str(e)}")
        return {
            "status": "error",
            "message": f"转换过程中发生错误: {str(e)}"
        }

# 健康检查接口
def health_check():
    """
    工具健康检查
    
    Returns:
        dict: 健康状态信息
    """
    try:
        result = mcp_invoke("health_check", {})
        return {
            "status": "healthy",
            "service": "pdf-to-markdown-trae-adapter",
            "mcp_service": result
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Trae AI工具注册和使用示例
def register_with_traer():
    """
    注册工具到Trae AI的示例代码
    在实际环境中，Trae AI会通过标准接口发现此工具
    """
    return {
        "tool": get_tool_definition(),
        "execute": execute_tool,
        "health": health_check
    }

# 导出Trae AI标准接口
__all__ = [
    "get_tool_definition",
    "execute_tool",
    "health_check",
    "register_with_traer"
]

# 当直接运行此模块时进行测试
if __name__ == "__main__":
    print("PDF转Markdown Trae AI适配器测试")
    print("=" * 50)
    
    # 显示工具定义
    print("工具定义:")
    print(json.dumps(get_tool_definition(), indent=2, ensure_ascii=False))
    print("\n")
    
    # 执行健康检查
    print("健康检查:")
    print(json.dumps(health_check(), indent=2, ensure_ascii=False))
    print("\n")
    
    print("适配器已准备就绪，可以接入Trae AI环境")
    print("使用方法: import trae_adapter; trae_adapter.execute_tool({...})")