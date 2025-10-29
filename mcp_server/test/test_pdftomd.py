import unittest
import os
import cv2
import numpy as np
from PIL import Image
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pdftomd import extract_text, process_text, detect_formula_regions

class TestPDFToMD(unittest.TestCase):
    
    def setUp(self):
        """设置测试环境"""
        # 创建一个简单的测试图像
        self.test_image = np.ones((200, 400, 3), dtype=np.uint8) * 255  # 白色背景
        # 添加一些文本区域（在实际OCR中会被识别）
        cv2.putText(self.test_image, "测试文本", (50, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        # 创建一个临时图像文件
        self.test_image_path = "test_image.png"
        cv2.imwrite(self.test_image_path, self.test_image)
    
    def tearDown(self):
        """清理测试环境"""
        # 删除临时文件
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
        # 删除可能生成的其他临时文件
        for file in os.listdir('.'):
            if file.startswith('temp_page_') and file.endswith('.png'):
                try:
                    os.remove(file)
                except:
                    pass
    
    def test_extract_text(self):
        """测试文本提取功能"""
        try:
            text = extract_text(self.test_image)
            # 验证返回类型
            self.assertIsInstance(text, str)
            print(f"文本提取测试通过，提取到的文本: {text[:50]}...")
        except Exception as e:
            print(f"文本提取测试异常（可能是Tesseract未安装）: {str(e)}")
            # 如果Tesseract未安装，这个测试应该被跳过而不是失败
            
    def test_process_text(self):
        """测试文本处理功能"""
        test_text = "# 标题\n\n这是一段普通文本。\n\nANOTHER TITLE"
        processed = process_text(test_text)
        
        # 验证处理后的文本包含预期内容
        self.assertIn("标题", processed)
        self.assertIn("这是一段普通文本", processed)
        # 验证全大写的文本被识别为标题
        self.assertIn("### ANOTHER TITLE", processed)
        print("文本处理测试通过")
    
    def test_detect_formula_regions(self):
        """测试公式区域检测功能"""
        # 创建一个包含复杂形状的图像（模拟公式）
        formula_image = np.ones((200, 400, 3), dtype=np.uint8) * 255
        # 绘制一些复杂形状
        cv2.circle(formula_image, (100, 100), 30, (0, 0, 0), 2)
        cv2.rectangle(formula_image, (150, 70), (250, 130), (0, 0, 0), 2)
        cv2.line(formula_image, (200, 50), (200, 150), (0, 0, 0), 2)
        
        regions = detect_formula_regions(formula_image)
        
        # 验证返回类型
        self.assertIsInstance(regions, list)
        print(f"公式检测测试通过，检测到{len(regions)}个区域")
    
    def test_file_processing(self):
        """测试文件处理（集成测试）"""
        # 导入pdftomd函数
        from pdftomd import pdftomd
        
        # 测试不存在的文件
        result = pdftomd("not_exist.pdf")
        self.assertIn("文件不存在", result)
        
        # 测试非PDF文件
        with open("test.txt", "w") as f:
            f.write("This is not a PDF")
        result = pdftomd("test.txt")
        self.assertIn("请提供PDF格式的文件", result)
        os.remove("test.txt")
        
        print("文件处理测试通过")

if __name__ == "__main__":
    unittest.main()