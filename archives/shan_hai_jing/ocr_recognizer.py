# -*- coding: utf-8 -*-
"""
OCR识别模块 - 处理文字识别
"""

import os
import datetime
import pyautogui
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from config import (
    SCREENSHOT_DIR,
    OCR_LANG,
    OCR_DETECTION_MODEL,
    OCR_RECOGNITION_MODEL,
    CURRENT_BEAST_REGION,
    BEAST_COMPARE_REGION,
    OCR_TYPE,
)
from umi_ocr import get_ocr_text

# 初始化OCR（全局单例）


class OCRRecognizer:
    """OCR识别器"""

    def __init__(self, window_manager, logger=None):
        """
        初始化OCR识别器
        Args:
            window_manager: 窗口管理器实例
            logger: 日志实例
        """
        self.window_manager = window_manager
        self.logger = logger
        self.ocr_type = OCR_TYPE

        # 初始化 PaddleOCR（如果需要）
        if self.ocr_type == "paddle":
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(
                lang=OCR_LANG,
                text_detection_model_name=OCR_DETECTION_MODEL,
                text_recognition_model_name=OCR_RECOGNITION_MODEL,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
            self.ocr = ocr
        else:
            self.ocr = None

    def preprocess_image(self, image):
        """
        图像预处理：转换为黑白（二值化）以提高OCR识别准确率
        Args:
            image: PIL Image对象
        Returns:
            PIL Image: 处理后的黑白图像
        """
        try:
            # 1. 转换为灰度图
            gray_image = image.convert("L")

            # 2. 增强对比度（可选，提高文字清晰度）
            enhancer = ImageEnhance.Contrast(gray_image)
            gray_image = enhancer.enhance(2.0)  # 对比度增强2倍

            # 3. 轻微锐化（可选，提高文字边缘清晰度）
            gray_image = gray_image.filter(ImageFilter.SHARPEN)

            # 4. 二值化处理（阈值化）
            # 使用自适应阈值或固定阈值
            # 方法1：固定阈值（简单快速）
            threshold = 128
            binary_image = gray_image.point(lambda x: 0 if x < threshold else 255, "1")

            # 方法2：使用numpy进行更精细的二值化（如果需要）
            # gray_array = np.array(gray_image)
            # binary_array = np.where(gray_array > threshold, 255, 0).astype(np.uint8)
            # binary_image = Image.fromarray(binary_array, mode='L')

            return binary_image
        except Exception as e:
            if self.logger:
                self.logger.warning(f"图像预处理失败，使用原图: {e}")
            return image

    def capture_and_recognize(self, region=None, save_screenshot=True, preprocess=True):
        """
        截图并使用OCR识别文字
        Args:
            region: 截图区域 (x, y, width, height)，如果为None则使用默认区域
            save_screenshot: 是否保存截图
            preprocess: 是否进行图像预处理（黑白二值化）
        Returns:
            list: 识别到的文字列表
        """
        try:
            # 获取窗口区域
            window_region = self.window_manager.get_active_window_region()
            if not window_region:
                return None

            # 如果没有指定区域，使用默认的异兽对比区域
            if region is None:
                region = (
                    window_region[0] + BEAST_COMPARE_REGION["x"],  # x: 窗口左上角x + 27
                    window_region[1]
                    + BEAST_COMPARE_REGION["y"],  # y: 窗口左上角y + 199
                    BEAST_COMPARE_REGION["width"],  # width
                    BEAST_COMPARE_REGION["height"],  # height
                )
            else:
                # 如果指定了区域，计算相对于窗口的绝对坐标
                region = (
                    window_region[0] + region[0],
                    window_region[1] + region[1],
                    region[2],
                    region[3],
                )

            # 截图
            screenshot = pyautogui.screenshot(region=region)

            # 保存截图
            if save_screenshot:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = os.path.join(SCREENSHOT_DIR, f"beast_{timestamp}.png")
                screenshot.save(screenshot_path)
                if self.logger:
                    self.logger.info(f"截图已保存到: {screenshot_path}")

            # 根据OCR类型选择识别方式
            if self.ocr_type == "umi":
                # 使用UMI-OCR API识别
                if not save_screenshot:
                    # 如果没有保存截图，需要临时保存
                    screenshot_path = os.path.join(
                        SCREENSHOT_DIR,
                        f"temp_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    )
                    screenshot.save(screenshot_path)
                # 直接调用 umi_ocr 的 get_ocr_text 方法
                text_list = get_ocr_text(screenshot_path)
                if self.logger:
                    self.logger.info(
                        f"UMI-OCR识别到 {len(text_list) if text_list else 0} 个文本片段"
                    )
                return text_list
            else:
                # 使用PaddleOCR识别
                # 图像预处理（转换为黑白）
                if preprocess:
                    screenshot = self.preprocess_image(screenshot)
                    if self.logger:
                        self.logger.info("✅ 图像已预处理为黑白（二值化）")

                # 如果没有保存截图，需要临时保存
                if not save_screenshot:
                    screenshot_path = os.path.join(
                        SCREENSHOT_DIR,
                        f"temp_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                    )
                    screenshot.save(screenshot_path)

                # OCR识别
                result = self.ocr.predict(screenshot_path)

            # 提取文字
            if result and isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict):
                    text_list = result[0].get("rec_texts", [])
                else:
                    # 尝试直接从结果中提取文字
                    text_list = []
                    for item in result:
                        if isinstance(item, list) and len(item) > 1:
                            if item:
                                text_list.append(item[1][0])
                return text_list

            return []
        except Exception as e:
            if self.logger:
                self.logger.error(f"OCR识别出错: {e}")
            return []

    def recognize_current_beast(self, save_screenshot=True, preprocess=True):
        """
        识别当前异兽属性
        Args:
            save_screenshot: 是否保存截图
            preprocess: 是否进行图像预处理（黑白二值化）
        Returns:
            list: 识别到的文字列表
        """
        # 当前异兽属性截图区域（相对于窗口）
        region = (
            CURRENT_BEAST_REGION["x"],
            CURRENT_BEAST_REGION["y"],
            CURRENT_BEAST_REGION["width"],
            CURRENT_BEAST_REGION["height"],
        )
        return self.capture_and_recognize(region, save_screenshot, preprocess)
