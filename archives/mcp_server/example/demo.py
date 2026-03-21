#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF转Markdown工具演示脚本

使用方法：
    python demo.py <pdf文件路径>

示例：
    python demo.py "../芯片手册/C31151_模数转换芯片ADC_AD9288BSTZ-100_规格书_WJ126841.PDF"
"""
import os
import sys
import subprocess
from pdftomd import pdftomd

def find_default_paths():
    """尝试查找默认安装路径"""
    # 常见的Tesseract安装路径
    tesseract_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
    ]
    
    # 常见的Poppler安装路径
    poppler_paths = [
        r"C:\poppler\bin",
        r"C:\Program Files\poppler\bin",
        r"C:\Program Files (x86)\poppler\bin"
    ]
    
    # 查找存在的Tesseract路径
    tesseract_cmd = None
    for path in tesseract_paths:
        if os.path.exists(path):
            tesseract_cmd = path
            break
    
    # 查找存在的Poppler路径
    poppler_path = None
    for path in poppler_paths:
        if os.path.exists(path):
            poppler_path = path
            break
    
    return tesseract_cmd, poppler_path

def get_user_input_paths():
    """获取用户输入的路径"""
    # 先尝试查找默认路径
    tesseract_cmd, poppler_path = find_default_paths()
    
    # 获取用户输入的Tesseract路径
    print("\n配置外部工具路径（可选）：")
    print("如果工具已在PATH环境变量中，可直接按回车跳过")
    
    # Tesseract路径输入
    user_input = input(f"Tesseract OCR路径 [默认: {tesseract_cmd or '未找到'}]: ").strip()
    if user_input:
        tesseract_cmd = user_input
    elif tesseract_cmd:
        print(f"✓ 使用默认Tesseract路径: {tesseract_cmd}")
    else:
        print("⚠ Tesseract路径未指定，将尝试使用系统PATH中的默认路径")
    
    # Poppler路径输入
    user_input = input(f"Poppler bin目录路径 [默认: {poppler_path or '未找到'}]: ").strip()
    if user_input:
        poppler_path = user_input
    elif poppler_path:
        print(f"✓ 使用默认Poppler路径: {poppler_path}")
    else:
        print("⚠ Poppler路径未指定，将尝试使用系统PATH中的默认路径")
    
    return tesseract_cmd, poppler_path

def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) != 2:
        print("使用方法：python demo.py <pdf文件路径>")
        print("\n示例：")
        print("    python demo.py \"../芯片手册/C31151_模数转换芯片ADC_AD9288BSTZ-100_规格书_WJ126841.PDF\"")
        # 尝试使用默认的PDF文件进行演示
        default_pdf = "../芯片手册/C31151_模数转换芯片ADC_AD9288BSTZ-100_规格书_WJ126841.PDF"
        if os.path.exists(default_pdf):
            print(f"\n检测到默认PDF文件，将使用：{default_pdf}")
            pdf_path = default_pdf
        else:
            print("\n未找到默认PDF文件，请指定PDF文件路径")
            return 1
    else:
        pdf_path = sys.argv[1]
    
    print("="*60)
    print("PDF转Markdown工具演示")
    print("="*60)
    
    # 检查依赖
    check_dependencies()
    
    # 获取用户输入的路径配置
    tesseract_cmd, poppler_path = get_user_input_paths()
    
    print(f"\n开始转换PDF文件：{pdf_path}")
    
    # 调用转换函数，传入路径参数
    try:
        result = pdftomd(pdf_path, tesseract_cmd=tesseract_cmd, poppler_path=poppler_path)
        print("\n转换结果：")
        print("-"*60)
        print(result)
        print("-"*60)
        
        # 检查生成的markdown文件
        md_filename = os.path.splitext(os.path.basename(pdf_path))[0] + ".md"
        if os.path.exists(md_filename):
            md_size = os.path.getsize(md_filename) / 1024  # KB
            print(f"\n生成的Markdown文件：{md_filename} ({md_size:.2f} KB)")
            print(f"可以使用文本编辑器打开查看内容")
        
        return 0
    except Exception as e:
        print(f"转换失败：{str(e)}")
        return 1

def check_dependencies():
    """检查依赖项"""
    print("检查依赖项...")
    
    # 检查tesseract
    try:
        # 尝试调用tesseract命令
        subprocess.run(["tesseract", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        print("✓ Tesseract OCR 已安装并在PATH中")
    except (subprocess.SubprocessError, FileNotFoundError):
        print("⚠ Tesseract OCR 未安装或未在PATH中")
        print("  请从 https://github.com/UB-Mannheim/tesseract/wiki 下载并安装")
        print("  安装时请选择中文语言包")
        print("  或在后续步骤中手动指定Tesseract路径")
    
    # 检查poppler (pdf2image的依赖)
    try:
        from pdf2image import convert_from_path
        print("✓ pdf2image 库已安装")
        # 简单检查是否能找到poppler
        try:
            # 尝试使用convert_from_path，但不实际转换文件
            # 这里只是简单测试，不会真正执行转换
            import inspect
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                f.write(b'%PDF-1.5\n1 0 obj<<>>stream\nx\nendstream\nendobj\nxref\n0 1\n0000000000 65535 f\ntrailer<<\n  /Size 1\n>>\nstartxref\n15\n%%EOF')
                temp_pdf = f.name
            
            # 尝试转换，可能会失败但我们只关心能否找到poppler
            try:
                convert_from_path(temp_pdf, poppler_path=None, dpi=72, first_page=1, last_page=1, timeout=1)
                print("✓ Poppler 已安装并在PATH中")
            except (FileNotFoundError, ValueError) as e:
                if "poppler" in str(e).lower() or "pdfinfo" in str(e).lower():
                    print("⚠ Poppler 未安装或未在PATH中")
                    print("  请从 https://github.com/oschwartz10612/poppler-windows/releases/ 下载")
                    print("  或在后续步骤中手动指定Poppler路径")
                else:
                    # 其他错误不影响，因为我们只是测试poppler
                    pass
            finally:
                # 清理临时文件
                if os.path.exists(temp_pdf):
                    try:
                        os.unlink(temp_pdf)
                    except:
                        pass
        except:
            # 如果测试失败，不影响程序继续
            pass
    except ImportError:
        print("⚠ pdf2image 库未安装")
    
    # 检查其他Python库
    required_libs = ["cv2", "numpy", "PIL"]
    for lib in required_libs:
        try:
            __import__(lib)
            print(f"✓ {lib} 库已安装")
        except ImportError:
            print(f"⚠ {lib} 库未安装")
            print(f"  请使用: pip install {lib}")

if __name__ == "__main__":
    sys.exit(main())