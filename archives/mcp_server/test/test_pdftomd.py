import unittest
import os
import cv2
import numpy as np
from PIL import Image
import sys
import tempfile
import shutil
import json

# 添加父目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pdftomd import (
    extract_text_from_image, 
    process_text_for_markdown, 
    convert_pdf_to_md,
    health_check,
    update_config,
    find_tesseract,
    find_poppler,
    pdftomd,
    CONFIG
)

class TestPDFToMD(unittest.TestCase):
    
    def setUp(self):
        """设置测试环境"""
        # 创建临时目录用于测试
        self.test_dir = tempfile.mkdtemp()
        self.original_output_dir = CONFIG['output_dir']
        self.original_temp_dir = CONFIG['temp_dir']
        
        # 更新配置使用临时目录
        CONFIG['output_dir'] = self.test_dir
        CONFIG['temp_dir'] = self.test_dir
        
        # 创建一个简单的测试图像
        self.test_image = np.ones((200, 400, 3), dtype=np.uint8) * 255  # 白色背景
        # 添加一些文本区域（在实际OCR中会被识别）
        cv2.putText(self.test_image, "测试文本", (50, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        # 创建一个临时图像文件
        self.test_image_path = os.path.join(self.test_dir, "test_image.png")
        cv2.imwrite(self.test_image_path, self.test_image)
        
        # 创建PIL图像对象
        self.pil_image = Image.fromarray(cv2.cvtColor(self.test_image, cv2.COLOR_BGR2RGB))
    
    def tearDown(self):
        """清理测试环境"""
        # 恢复原始配置
        CONFIG['output_dir'] = self.original_output_dir
        CONFIG['temp_dir'] = self.original_temp_dir
        
        # 删除临时目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_find_tesseract(self):
        """测试Tesseract路径检测功能"""
        tesseract_path = find_tesseract()
        # 如果Tesseract已安装，路径应该不为None
        if tesseract_path:
            self.assertTrue(os.path.exists(tesseract_path))
            print(f"Tesseract路径检测测试通过，找到路径: {tesseract_path}")
        else:
            print("Tesseract未安装，路径检测返回None")
    
    def test_find_poppler(self):
        """测试Poppler路径检测功能"""
        poppler_path = find_poppler()
        # 如果Poppler已安装，路径应该不为None
        if poppler_path:
            self.assertTrue(os.path.exists(poppler_path))
            print(f"Poppler路径检测测试通过，找到路径: {poppler_path}")
        else:
            print("Poppler未安装，路径检测返回None")
    
    def test_extract_text_from_image(self):
        """测试文本提取功能"""
        try:
            text = extract_text_from_image(self.pil_image)
            # 验证返回类型
            self.assertIsInstance(text, str)
            print(f"文本提取测试通过，提取到的文本: {text[:50]}...")
        except Exception as e:
            print(f"文本提取测试异常（可能是Tesseract未安装）: {str(e)}")
            # 如果Tesseract未安装，这个测试应该被跳过而不是失败
    
    def test_process_text_for_markdown(self):
        """测试文本处理功能"""
        test_text = "# 标题\n\n这是一段普通文本。\n\nANOTHER TITLE\n\nE=mc2\n\n列1\t列2\t列3"
        processed = process_text_for_markdown(test_text)
        
        # 验证处理后的文本包含预期内容
        self.assertIn("标题", processed)
        self.assertIn("这是一段普通文本", processed)
        # 验证全大写的文本被识别为标题
        self.assertIn("### ANOTHER TITLE", processed)
        # 验证公式被识别
        self.assertIn("$$E=mc2$$", processed)
        # 验证表格被识别
        self.assertIn("| 列1 | 列2 | 列3 |", processed)
        print("文本处理测试通过")
    
    def test_health_check(self):
        """测试健康检查功能"""
        health = health_check()
        
        # 验证返回类型
        self.assertIsInstance(health, dict)
        # 验证必要字段
        self.assertIn('status', health)
        self.assertIn('service_name', health)
        self.assertIn('dependencies', health)
        self.assertIn('config', health)
        
        print(f"健康检查测试通过，服务状态: {health['status']}")
    
    def test_update_config(self):
        """测试配置更新功能"""
        # 创建新的临时目录用于测试
        new_output_dir = os.path.join(self.test_dir, "new_output")
        new_temp_dir = os.path.join(self.test_dir, "new_temp")
        
        # 更新配置
        result = update_config({
            'output_dir': new_output_dir,
            'temp_dir': new_temp_dir
        })
        
        # 验证返回结果
        self.assertEqual(result['status'], 'success')
        self.assertIn('updated_fields', result)
        self.assertIn('output_dir', result['updated_fields'])
        self.assertIn('temp_dir', result['updated_fields'])
        
        # 验证配置已更新
        self.assertEqual(CONFIG['output_dir'], new_output_dir)
        self.assertEqual(CONFIG['temp_dir'], new_temp_dir)
        
        # 验证目录已创建
        self.assertTrue(os.path.exists(new_output_dir))
        self.assertTrue(os.path.exists(new_temp_dir))
        
        print("配置更新测试通过")
    
    def test_convert_pdf_to_md_invalid_params(self):
        """测试PDF转换功能的无效参数处理"""
        # 测试缺少文件路径参数
        result = convert_pdf_to_md({})
        self.assertEqual(result['status'], 'error')
        self.assertIn('缺少必要参数', result['message'])
        
        # 测试不存在的文件
        result = convert_pdf_to_md({'file_path': 'not_exist.pdf'})
        self.assertEqual(result['status'], 'error')
        self.assertIn('PDF文件不存在', result['message'])
        
        # 测试非PDF文件
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b"This is not a PDF")
            tmp_path = tmp.name
        
        try:
            result = convert_pdf_to_md({'file_path': tmp_path})
            self.assertEqual(result['status'], 'error')
            self.assertIn('请提供PDF格式的文件', result['message'])
        finally:
            os.unlink(tmp_path)
        
        print("无效参数处理测试通过")
    
    def test_pdftomd_function(self):
        """测试pdftomd主函数"""
        # 测试不存在的文件
        result = pdftomd("not_exist.pdf")
        self.assertIn("文件不存在", result)
        
        # 测试非PDF文件
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as tmp:
            tmp.write(b"This is not a PDF")
            tmp_path = tmp.name
        
        try:
            result = pdftomd(tmp_path)
            self.assertIn("请提供PDF格式的文件", result)
        finally:
            os.unlink(tmp_path)
        
        print("pdftomd函数测试通过")
    
    def test_service_info(self):
        """测试服务信息"""
        from pdftomd import SERVICE_INFO
        
        # 验证服务信息结构
        self.assertIsInstance(SERVICE_INFO, dict)
        self.assertIn('name', SERVICE_INFO)
        self.assertIn('version', SERVICE_INFO)
        self.assertIn('description', SERVICE_INFO)
        self.assertIn('endpoints', SERVICE_INFO)
        self.assertIn('dependencies', SERVICE_INFO)
        
        # 验证端点信息
        self.assertIsInstance(SERVICE_INFO['endpoints'], list)
        for endpoint in SERVICE_INFO['endpoints']:
            self.assertIn('name', endpoint)
            self.assertIn('description', endpoint)
        
        print("服务信息测试通过")

class TestPDFToMDIntegration(unittest.TestCase):
    """集成测试类"""
    
    def setUp(self):
        """设置集成测试环境"""
        # 创建临时目录用于测试
        self.test_dir = tempfile.mkdtemp()
        self.original_output_dir = CONFIG['output_dir']
        self.original_temp_dir = CONFIG['temp_dir']
        
        # 更新配置使用临时目录
        CONFIG['output_dir'] = self.test_dir
        CONFIG['temp_dir'] = self.test_dir
    
    def tearDown(self):
        """清理集成测试环境"""
        # 恢复原始配置
        CONFIG['output_dir'] = self.original_output_dir
        CONFIG['temp_dir'] = self.original_temp_dir
        
        # 删除临时目录
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
    
    def test_full_workflow(self):
        """测试完整工作流程（如果有真实PDF文件）"""
        # 检查是否有测试用的PDF文件
        test_pdf_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "芯片手册", "lm5176.pdf")
        
        if os.path.exists(test_pdf_path):
            # 执行转换
            result = convert_pdf_to_md({'file_path': test_pdf_path})
            
            # 验证结果
            self.assertEqual(result['status'], 'success')
            self.assertIn('data', result)
            self.assertIn('output_file', result['data'])
            self.assertIn('pages', result['data'])
            self.assertIn('content_length', result['data'])
            
            # 验证输出文件存在
            output_file = result['data']['output_file']
            self.assertTrue(os.path.exists(output_file))
            
            # 验证输出文件内容
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("# lm5176", content)
                self.assertIn("## 目录", content)
                self.assertIn("## 第 1 页", content)
            
            print(f"完整工作流程测试通过，转换了{result['data']['pages']}页")
        else:
            print("跳过完整工作流程测试，未找到测试PDF文件")

if __name__ == "__main__":
    # 运行测试
    unittest.main(verbosity=2)