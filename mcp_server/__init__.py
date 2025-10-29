# -*- coding: utf-8 -*-
"""
PDF转Markdown MCP服务模块

该模块提供了将PDF文件转换为Markdown格式的MCP远程服务功能。
支持通过MCP服务框架进行远程调用。
"""

from pdftomd import (
    pdftomd,
    convert_pdf_to_md,
    health_check,
    update_config,
    SERVICE_INFO
)

# MCP服务注册和暴露的接口
def get_service_info():
    """
    获取服务信息，用于MCP服务发现
    
    Returns:
        dict: 包含服务元数据的字典
    """
    return SERVICE_INFO

def get_service_endpoints():
    """
    获取服务端点列表
    
    Returns:
        dict: 包含所有可调用函数的字典
    """
    return {
        'convert_pdf_to_md': convert_pdf_to_md,
        'health_check': health_check,
        'update_config': update_config
    }

# 标准MCP服务接口
def invoke(method, params):
    """
    MCP服务标准调用入口
    
    Args:
        method: 要调用的方法名
        params: 方法参数
    
    Returns:
        dict: 方法调用结果
    """
    endpoints = get_service_endpoints()
    
    if method not in endpoints:
        return {
            'status': 'error',
            'message': f'未知的方法: {method}',
            'available_methods': list(endpoints.keys())
        }
    
    try:
        # 调用对应的方法
        func = endpoints[method]
        result = func(params)
        return result
    except Exception as e:
        return {
            'status': 'error',
            'message': f'调用方法时出错: {str(e)}',
            'method': method
        }

# 服务元数据
__version__ = '1.0.0'
__service_name__ = 'pdf-to-markdown-converter'
__description__ = '将PDF文件转换为Markdown格式的MCP服务'

# 导出的公共接口
__all__ = [
    'pdftomd',
    'convert_pdf_to_md',
    'health_check',
    'update_config',
    'get_service_info',
    'get_service_endpoints',
    'invoke'
]

# 当直接运行此模块时显示服务信息
if __name__ == '__main__':
    import json
    print(f"{__service_name__} v{__version__}")
    print(__description__)
    print("\n可用接口:")
    for name, endpoint in get_service_endpoints().items():
        doc = endpoint.__doc__
        doc_line = doc.split('\n')[0].strip() if doc else '无描述'
        print(f"- {name}: {doc_line}")
    print("\n完整服务信息:")
    print(json.dumps(get_service_info(), indent=2, ensure_ascii=False))