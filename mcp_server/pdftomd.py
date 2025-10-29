# -*- coding: utf-8 -*-
"""
PDF转Markdown核心功能模块

此模块提供了将PDF文件转换为Markdown格式的核心功能，使用pytesseract、opencv-python和pdf2image实现。
支持图片、公式和文字的提取，无需输入环境变量。
"""

import os
import json
import logging
import argparse
import sys
import platform
import subprocess
from typing import Dict, Any, Optional, List
from datetime import datetime

# 导入必要的PDF处理库
try:
    from pdf2image import convert_from_path
    import cv2
    import numpy as np
    import pytesseract
    from PIL import Image
except ImportError as e:
    logger = logging.getLogger('pdftomd')
    logger.warning(f"无法导入必要的库: {str(e)}")
    logger.warning("请确保已安装: pytesseract, opencv-python, pdf2image, pillow")
# 确保日志目录存在
log_dir = os.path.join(os.path.dirname(__file__), 'log')
os.makedirs(log_dir, exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - pdftomd - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(log_dir, 'pdftomd.log'))
    ]
)
logger = logging.getLogger('pdftomd')

# 自动检测Tesseract和Poppler路径
def find_tesseract():
    """自动检测Tesseract可执行文件路径"""
    # 常见的Tesseract路径
    common_paths = []
    
    if platform.system() == 'Windows':
        # Windows常见路径
        common_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Tesseract-OCR\tesseract.exe",
            # 尝试从环境变量PATH中查找
        ]
        # 尝试从环境变量PATH中查找
        try:
            result = subprocess.run(['where', 'tesseract'], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE, 
                                    text=True)
            if result.returncode == 0:
                common_paths.append(result.stdout.strip().split('\n')[0])
        except:
            pass
    else:
        # Linux/macOS常见路径
        common_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/opt/local/bin/tesseract',
        ]
        # 尝试从环境变量PATH中查找
        try:
            result = subprocess.run(['which', 'tesseract'], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE, 
                                    text=True)
            if result.returncode == 0:
                common_paths.append(result.stdout.strip())
        except:
            pass
    
    # 检查路径是否存在
    for path in common_paths:
        if os.path.exists(path):
            logger.info(f"找到Tesseract: {path}")
            return path
    
    logger.warning("未找到Tesseract，请手动指定路径或确保已安装")
    return None

def find_poppler():
    """自动检测Poppler路径"""
    # 常见的Poppler路径
    common_paths = []
    
    if platform.system() == 'Windows':
        # Windows常见路径
        common_paths = [
            r"C:\Program Files\poppler-xx\bin",
            r"C:\Program Files (x86)\poppler-xx\bin",
            r"C:\poppler-xx\bin",
        ]
        # 尝试查找所有可能的poppler版本
        program_files = [r"C:\Program Files", r"C:\Program Files (x86)"]
        for pf in program_files:
            if os.path.exists(pf):
                for item in os.listdir(pf):
                    if item.startswith("poppler"):
                        poppler_path = os.path.join(pf, item, "bin")
                        if os.path.exists(poppler_path):
                            common_paths.append(poppler_path)
    else:
        # Linux/macOS通常在PATH中
        try:
            result = subprocess.run(['which', 'pdftoppm'], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE, 
                                    text=True)
            if result.returncode == 0:
                return os.path.dirname(result.stdout.strip())
        except:
            pass
    
    # 检查路径是否存在
    for path in common_paths:
        if os.path.exists(path):
            logger.info(f"找到Poppler: {path}")
            return path
    
    logger.warning("未找到Poppler，请手动指定路径或确保已安装")
    return None

def extract_text_from_image(image, lang='chi_sim+eng') -> str:
    """
    从图像中提取文本，包括文字和公式
    
    Args:
        image: PIL图像对象
        lang: OCR语言设置
    
    Returns:
        str: 提取的文本
    """
    try:
        # 转换PIL图像为OpenCV格式
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # 图像预处理 - 提高文字识别率
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # 降噪处理
        denoised = cv2.fastNlMeansDenoising(gray)
        
        # 锐化处理
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
        sharpened = cv2.filter2D(denoised, -1, kernel)
        
        # 应用自适应阈值以改善OCR效果
        thresh = cv2.adaptiveThreshold(
            sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        # 形态学操作 - 去除噪点
        kernel = np.ones((1,1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # 尝试不同的OCR配置
        configs = [
            # 标准文本配置
            r'--oem 3 --psm 6',
            # 稀疏文本配置
            r'--oem 3 --psm 11',
            # 单列文本配置
            r'--oem 3 --psm 4',
            # 公式识别配置
            r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+-=<>[](){}.,;:!?\'\"@#$%^&*_/\\|`~ \n\t',
        ]
        
        best_text = ""
        best_confidence = 0
        
        for config in configs:
            try:
                # 获取文本和置信度
                data = pytesseract.image_to_data(
                    processed, 
                    lang=lang, 
                    config=config, 
                    output_type=pytesseract.Output.DICT
                )
                
                # 计算平均置信度
                confidences = [int(c) for c in data['conf'] if int(c) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0
                
                # 提取文本
                text = ' '.join([word for i, word in enumerate(data['text']) if int(data['conf'][i]) > 0])
                
                # 如果置信度更高，则使用此文本
                if avg_confidence > best_confidence:
                    best_confidence = avg_confidence
                    best_text = text
                    
            except Exception as e:
                logger.debug(f"OCR配置 {config} 失败: {str(e)}")
                continue
        
        # 如果所有配置都失败，使用默认配置
        if not best_text:
            try:
                best_text = pytesseract.image_to_string(processed, lang=lang)
            except Exception as e:
                logger.error(f"默认OCR配置也失败: {str(e)}")
                # 最后尝试直接处理原始图像
                try:
                    best_text = pytesseract.image_to_string(image, lang=lang)
                except Exception as inner_e:
                    logger.error(f"所有OCR尝试都失败: {str(inner_e)}")
                    return ""
        
        # 后处理文本
        # 移除多余的空行
        lines = best_text.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip():
                cleaned_lines.append(line.strip())
        
        return '\n'.join(cleaned_lines)
        
    except Exception as e:
        logger.error(f"OCR处理失败: {str(e)}")
        # 如果OpenCV处理失败，直接使用pytesseract处理PIL图像
        try:
            return pytesseract.image_to_string(image, lang=lang)
        except Exception as inner_e:
            logger.error(f"备用OCR处理也失败: {str(inner_e)}")
            return ""

# 全局配置
CONFIG = {
    'output_dir': os.path.abspath('output'),  # 输出目录（绝对路径）
    'temp_dir': os.path.abspath('temp'),      # 临时文件目录（绝对路径）
    'tesseract_cmd': find_tesseract(),        # 自动检测Tesseract OCR路径
    'poppler_path': find_poppler()            # 自动检测Poppler路径
}

# 确保目录存在
os.makedirs(CONFIG['output_dir'], exist_ok=True)
os.makedirs(CONFIG['temp_dir'], exist_ok=True)

# 服务信息
SERVICE_INFO = {
    'name': 'pdf-to-markdown-converter',
    'version': '1.0.0',
    'description': '将PDF文件转换为Markdown格式',
    'endpoints': [
        {
            'name': 'convert_pdf_to_md',
            'description': '转换PDF文件为Markdown'
        },
        {
            'name': 'health_check',
            'description': '检查服务健康状态'
        },
        {
            'name': 'update_config',
            'description': '更新服务配置'
        }
    ],
    'dependencies': {
        'tesseract_ocr': 'required',
        'poppler': 'required'
    },
    'config': CONFIG
}

def pdftomd(file_path: str, tesseract_cmd: Optional[str] = None, poppler_path: Optional[str] = None) -> str:
    """
    PDF转Markdown主函数
    
    Args:
        file_path: PDF文件路径
        tesseract_cmd: Tesseract OCR可执行文件路径
        poppler_path: Poppler二进制文件目录路径
    
    Returns:
        str: 转换结果消息
    """
    try:
        # 准备参数
        params = {
            'file_path': file_path
        }
        if tesseract_cmd:
            params['tesseract_cmd'] = tesseract_cmd
        if poppler_path:
            params['poppler_path'] = poppler_path
        
        # 调用转换函数
        result = convert_pdf_to_md(params)
        
        if result['status'] == 'success':
            return f"转换成功！输出文件: {result['data']['output_file']}"
        else:
            return f"转换失败: {result['message']}"
            
    except Exception as e:
        logger.error(f"转换过程中发生错误: {str(e)}")
        return f"转换过程中发生错误: {str(e)}"

def process_text_for_markdown(text: str) -> str:
    """
    处理提取的文本，识别公式和表格，转换为Markdown格式
    
    Args:
        text: 原始文本
    
    Returns:
        str: 处理后的Markdown文本
    """
    lines = text.split('\n')
    processed_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            processed_lines.append('')
            continue
            
        # 检测全大写的文本，可能是标题
        if line.isupper() and len(line) > 3:
            # 将全大写的文本转换为三级标题
            processed_lines.append(f"### {line}")
        # 检测可能的公式（包含数学符号或等号）
        elif any(symbol in line for symbol in ['∑', '∫', '∂', '√', '±', '≈', '≠', '≤', '≥', '∞', 'α', 'β', 'γ', 'δ', 'π', '=']):
            # 将公式行用LaTeX格式包围
            processed_lines.append(f"$${line}$$")
        # 检测表格（包含多个制表符或连续空格）
        elif '\t' in line or '  ' in line:
            # 简单的表格处理
            cells = [cell.strip() for cell in line.split('\t') if cell.strip()]
            if len(cells) > 1:
                processed_lines.append('| ' + ' | '.join(cells) + ' |')
            else:
                processed_lines.append(line)
        else:
            processed_lines.append(line)
    
    return '\n'.join(processed_lines)

def convert_pdf_to_md(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    转换PDF文件为Markdown格式，支持文字、公式和表格提取
    
    Args:
        params: 包含转换参数的字典
            - file_path: PDF文件路径
            - tesseract_cmd: Tesseract OCR路径（可选）
            - poppler_path: Poppler路径（可选）
            - lang: OCR语言设置（可选）
    
    Returns:
        dict: 转换结果，包含状态、消息和数据
    """
    try:
        # 验证参数
        if 'file_path' not in params:
            return {
                'status': 'error',
                'message': '缺少必要参数: file_path'
            }
        
        file_path = params['file_path']
        lang = params.get('lang', 'chi_sim+eng')
        
        # 检查文件是否存在
        if not os.path.exists(file_path):
            return {
                'status': 'error',
                'message': f'PDF文件不存在: {file_path}'
            }
        
        # 检查文件格式
        if not file_path.lower().endswith('.pdf'):
            return {
                'status': 'error',
                'message': '请提供PDF格式的文件'
            }
        
        # 更新配置（如果提供）
        if 'tesseract_cmd' in params:
            CONFIG['tesseract_cmd'] = params['tesseract_cmd']
        if 'poppler_path' in params:
            CONFIG['poppler_path'] = params['poppler_path']
        
        # 设置Tesseract路径
        if CONFIG['tesseract_cmd']:
            pytesseract.pytesseract.tesseract_cmd = CONFIG['tesseract_cmd']
        
        # 生成输出文件路径
        filename = os.path.splitext(os.path.basename(file_path))[0]
        output_path = os.path.join(CONFIG['output_dir'], f"{filename}.md")
        
        logger.info(f"开始处理PDF文件: {file_path}")
        logger.info(f"输出目录: {CONFIG['output_dir']}")
        logger.info(f"临时目录: {CONFIG['temp_dir']}")
        
        # 确保图片目录存在
        images_dir = os.path.join(os.path.dirname(output_path), "images")
        os.makedirs(images_dir, exist_ok=True)
        
        # 将PDF转换为图像
        try:
            images = convert_from_path(
                file_path,
                dpi=300,
                poppler_path=CONFIG['poppler_path']
            )
            logger.info(f"成功转换PDF，共{len(images)}页")
        except Exception as e:
            logger.error(f"PDF转图像失败: {str(e)}")
            return {
                'status': 'error',
                'message': f'PDF转图像失败: {str(e)}'
            }
        
        # 处理每一页
        markdown_content = []
        markdown_content.append(f"# {filename}\n\n")
        
        # 添加目录
        markdown_content.append("## 目录\n\n")
        for i in range(1, len(images)+1):
            markdown_content.append(f"- [第 {i} 页](#第-{i}-页)\n")
        markdown_content.append("\n---\n\n")
        
        # 处理每一页
        for i, image in enumerate(images, 1):
            # 保存图像
            img_path = os.path.join(images_dir, f"page_{i}.png")
            image.save(img_path, "PNG")
            
            # 提取文本
            text = extract_text_from_image(image, lang)
            
            # 处理文本，识别公式和表格
            processed_text = process_text_for_markdown(text)
            
            # 添加到Markdown内容
            markdown_content.append(f"## 第 {i} 页\n\n")
            markdown_content.append(f"![第 {i} 页]({os.path.relpath(img_path, os.path.dirname(output_path))})\n\n")
            markdown_content.append(f"{processed_text}\n\n")
            markdown_content.append("---\n\n")
        
        # 保存Markdown文件
        final_content = ''.join(markdown_content)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(final_content)
        
        logger.info(f"PDF转换完成，输出文件: {output_path}")
        
        return {
            'status': 'success',
            'message': 'PDF转换成功',
            'data': {
                'original_file': file_path,
                'output_file': output_path,
                'pages': len(images),
                'content_length': len(final_content),
                'preview': final_content[:500] + "..." if len(final_content) > 500 else final_content
            }
        }
        
    except Exception as e:
        logger.error(f"PDF转换失败: {str(e)}")
        return {
            'status': 'error',
            'message': f'转换失败: {str(e)}'
        }

def health_check(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    检查服务健康状态
    
    Args:
        params: 可选参数（未使用）
    
    Returns:
        dict: 健康状态信息
    """
    try:
        # 检查目录是否可访问
        output_dir_accessible = os.access(CONFIG['output_dir'], os.W_OK)
        temp_dir_accessible = os.access(CONFIG['temp_dir'], os.W_OK)
        
        # 构建健康检查结果
        health_info = {
            'status': 'healthy',
            'service_name': SERVICE_INFO['name'],
            'version': SERVICE_INFO['version'],
            'dependencies': {
                'tesseract_ocr': {
                    'available': CONFIG['tesseract_cmd'] is not None,
                    'path': CONFIG['tesseract_cmd']
                },
                'poppler': {
                    'available': CONFIG['poppler_path'] is not None,
                    'path': CONFIG['poppler_path']
                }
            },
            'config': {
                'output_dir': CONFIG['output_dir'],
                'temp_dir': CONFIG['temp_dir'],
                'output_dir_accessible': output_dir_accessible,
                'temp_dir_accessible': temp_dir_accessible
            },
            'timestamp': '2024-01-01 12:00:00'  # 实际应用中应该使用当前时间
        }
        
        return health_info
        
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            'status': 'error',
            'message': f'健康检查失败: {str(e)}'
        }

def update_config(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    更新服务配置
    
    Args:
        params: 包含配置参数的字典
    
    Returns:
        dict: 更新结果
    """
    try:
        updated = []
        
        # 更新输出目录
        if 'output_dir' in params:
            output_dir = os.path.abspath(params['output_dir'])
            os.makedirs(output_dir, exist_ok=True)
            CONFIG['output_dir'] = output_dir
            updated.append('output_dir')
        
        # 更新临时目录
        if 'temp_dir' in params:
            temp_dir = os.path.abspath(params['temp_dir'])
            os.makedirs(temp_dir, exist_ok=True)
            CONFIG['temp_dir'] = temp_dir
            updated.append('temp_dir')
        
        # 更新Tesseract路径
        if 'tesseract_cmd' in params:
            CONFIG['tesseract_cmd'] = params['tesseract_cmd']
            updated.append('tesseract_cmd')
        
        # 更新Poppler路径
        if 'poppler_path' in params:
            CONFIG['poppler_path'] = params['poppler_path']
            updated.append('poppler_path')
        
        return {
            'status': 'success',
            'message': f'配置更新成功',
            'updated_fields': updated,
            'current_config': CONFIG
        }
        
    except Exception as e:
        logger.error(f"配置更新失败: {str(e)}")
        return {
            'status': 'error',
            'message': f'配置更新失败: {str(e)}'
        }

# 导出的公共接口
__all__ = [
    'pdftomd',
    'convert_pdf_to_md',
    'health_check',
    'update_config',
    'SERVICE_INFO',
    'CONFIG'
]

# 当直接运行此模块时进行简单测试
if __name__ == "__main__":
    print("PDF转Markdown模块测试")
    print(f"输出目录: {CONFIG['output_dir']}")
    print(f"临时目录: {CONFIG['temp_dir']}")
    
    # 执行健康检查
    health = health_check()
    print("\n健康检查结果:")
    print(json.dumps(health, indent=2, ensure_ascii=False))
    
    print("\n模块已准备就绪，可以通过Trae AI适配器使用")