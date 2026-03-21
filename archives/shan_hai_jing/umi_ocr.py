# -*- coding: utf-8 -*-
import mailbox
import requests 
import base64
# 使用umi-ocr-api
UMI_OCR_API_URL = "http://localhost:1224/api/ocr"

def read_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def send_request(image_path):
    try:
        payload = {"base64": read_image(image_path)}
        response = requests.post(UMI_OCR_API_URL, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return None

def parse_data(result):
    """
    解析ocr结果，提取文本列表
    Args:
        result: umi-ocr API返回的结果
    Returns:
        list: 提取的文本列表，按行排序，每行内按x坐标排序
    """
    if result and result.get('code') == 100:
        data = result.get('data', [])
        if not data:
            return None
        
        # 先按y坐标排序
        data_sorted_by_y = sorted(data, key=lambda item: item['box'][0][1])
        
        # 按行分组（同一行的文本y坐标相近）
        lines = []
        current_line = [data_sorted_by_y[0]]
        current_y = data_sorted_by_y[0]['box'][0][1]
        
        for item in data_sorted_by_y[1:]:
            y = item['box'][0][1]
            # 如果y坐标差异小于10像素，认为是同一行
            if abs(y - current_y) < 10:
                current_line.append(item)
            else:
                # 当前行结束，按x坐标排序后添加到lines
                current_line_sorted = sorted(current_line, key=lambda item: item['box'][0][0])
                lines.extend(current_line_sorted)
                # 开始新行
                current_line = [item]
                current_y = y
        
        # 添加最后一行
        if current_line:
            current_line_sorted = sorted(current_line, key=lambda item: item['box'][0][0])
            lines.extend(current_line_sorted)
        
        # 提取文本列表并清理特殊符号
        text_list = []
        for item in lines:
            text = item['text']
            # 移除末尾的特殊符号（+、- 等）
            text = text.rstrip('+-↑t')
            text_list.append(text)
        
        print(f"提取到 {len(text_list)} 个文本片段")
        return text_list
    
    return None

def get_ocr_text(image_path):
    """
    获取图片的OCR文本列表
    Args:
        image_path: 图片路径
    Returns:
        list: 提取的文本列表，按y坐标排序
    """
    result = send_request(image_path)
    if result:
        return parse_data(result)
    return None


if __name__ == '__main__':
    image_path = 'beast_20251226_101128.png'
    result = send_request(image_path)
    if result:
        text_list = parse_data(result)
        print(text_list)
        # 示例：将文本列表传递给 shan_hai_jing.py 的解析方法
        # from shan_hai_jing import ShanHaiJing
        # shj = ShanHaiJing()
        # beasts = shj.parse_capture_screen_attributes(text_list)
        # if beasts:
        #     print(f"当前异兽: {beasts[0]}")
        #     print(f"新获异兽: {beasts[1]}")