import time
import json
from paddleocr import PaddleOCR
import os

from pyautogui import screenshot

# 跳过模型源检查，关闭所有额外功能
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'
start_time = time.time()
ocr = PaddleOCR(
    lang="ch",
    text_detection_model_name="PP-OCRv5_server_det",
    text_recognition_model_name="PP-OCRv5_server_rec",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    device="gpu"
)

print("OCR初始化完成，可以开始识别了！")

# # 开始计时
# start_time = time.time()

# # 使用新方法predict替代已弃用的ocr
# result = ocr.predict("snipaste_01.png")

# # 结束计时并计算耗时
# end_time = time.time()
# elapsed_time = end_time - start_time

# # 调试结果结构
# print("结果类型:", type(result))
# print("结果长度:", len(result))
# print(f"识别耗时: {elapsed_time:.2f}秒")

# # 打印详细结果以便了解结构
# # print("详细结果:", result)  # 可以注释掉以减少输出

# # 根据实际结构提取文字
# if result:
#     # 检查第一级结构
#     if isinstance(result[0], dict):
#         # 获取识别的文本列表
#         text_list = result[0].get('rec_texts', [])
#         print(f"识别到{len(text_list)}个文本片段:")
#         print(text_list)
#     else:
#         print(f"结果结构不符合预期: {type(result[0])}")

# import easyocr

# reader = easyocr.Reader(["ch_sim", "en"])
# results = reader.readtext(
#     "snipaste_01.png", text_threshold=0.4, low_text=0.4, contrast_ths=0.2
# )
# data = []
# for result in results:
#     data.append(result[1])
# print(data)

def capture_and_recognize():
        """
        截图并使用OCR识别文字
        Returns:
            list: 识别到的文字列表
        """
        try:
           
            # OCR识别
            screenshot_path = "snipaste_attr.png"
            result = ocr.predict(screenshot_path)
            # 提取文字
             # 提取文字和坐标信息
            if result and isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict):
                    text_list = result[0].get('rec_texts', [])
                else:
                    # 尝试直接从结果中提取文字
                    text_list = []
                    for item in result:
                        if isinstance(item, list) and len(item) > 1:
                            if item:
                                text_list.append(item[1][0])
                return text_list
            
            return None
        except Exception as e:
            print(f"OCR识别出错: {e}")
            return None
    
def parse_beast_attributes(text_list):
    """
    解析异兽属性
    Args:
        text_list: OCR识别的文字列表
    Returns:
        dict: 包含异兽属性的字典
    """
    
    if not text_list or len(text_list) < 10:
        print(f"OCR识别结果太少，无法解析（只有{len(text_list) if text_list else 0}个文本片段）")
        return None
    try:
        # 辅助函数：根据关键词查找对应的数值
        def find_value_by_keyword(text_list, keyword, search_start=0, search_end=None):
            """在指定范围内查找关键词后的数值"""
            for i in range(search_start, len(text_list) if search_end is None else search_end):
                if keyword in text_list[i]:
                    # 查找关键词后面的数值
                    for j in range(i+1, min(i+5, len(text_list))):
                        try:
                            # 尝试转换为数字
                            value = text_list[j].replace(',', '').replace('，', '')
                            if value.isdigit():
                                return int(value)
                        except:
                            continue
            return None
        
        # 辅助函数：根据Y坐标将文本分为上下两部分（旧异兽和新异兽）
        def split_by_y_coordinate(text_list):
            """根据Y坐标将OCR结果分为上下两部分"""
            if not text_list:
                return [], []
            count = len(text_list) // 2
            return text_list[:count], text_list[count:]
            # 计算所有文本的Y坐标中心点
            
        
        # 将OCR结果分为上下两部分
        upper_part, lower_part = split_by_y_coordinate(text_list)
        
        print(f"上半部分（旧异兽）有{len(upper_part)}个文本片段")
        print(f"下半部分（新异兽）有{len(lower_part)}个文本片段")
        
        # 解析旧异兽属性
        old_attribute = {}
        if upper_part:
            # 名称通常是第一个文本
            old_attribute['name'] = upper_part[0] if upper_part else ''
            # 类型通常是第二个文本
            old_attribute['type'] = upper_part[1] if len(upper_part) > 1 else ''
            
            # 使用关键词查找属性值
            old_attribute['hp'] = find_value_by_keyword(upper_part, '生命') or 0
            old_attribute['attack'] = find_value_by_keyword(upper_part, '攻击') or 0
            old_attribute['defense'] = find_value_by_keyword(upper_part, '防御') or 0
            old_attribute['speed'] = find_value_by_keyword(upper_part, '速度') or 0
            
            # 特殊属性和数值
            special_keywords = ['闪避', '吸血', '暴击', '反击', '坚韧', '穿透', '命中', '格挡']
            for keyword in special_keywords:
                if find_value_by_keyword(upper_part, keyword):
                    old_attribute['special_attribute'] = keyword
                    old_attribute['special_value'] = find_value_by_keyword(upper_part, keyword)
                    break
            
            if 'special_attribute' not in old_attribute:
                old_attribute['special_attribute'] = ''
                old_attribute['special_value'] = '0'
        
        # 解析新异兽属性
        new_attribute = {}
        if lower_part:
            # 名称通常是第一个文本
            new_attribute['name'] = lower_part[0] if lower_part else ''
            # 类型通常是第二个文本
            new_attribute['type'] = lower_part[1] if len(lower_part) > 1 else ''
            
            # 使用关键词查找属性值
            new_attribute['hp'] = find_value_by_keyword(lower_part, '生命') or 0
            new_attribute['attack'] = find_value_by_keyword(lower_part, '攻击') or 0
            new_attribute['defense'] = find_value_by_keyword(lower_part, '防御') or 0
            new_attribute['speed'] = find_value_by_keyword(lower_part, '速度') or 0
            
            # 特殊属性和数值
            special_keywords = ['闪避', '吸血', '暴击', '反击', '连击', '击晕']
            for keyword in special_keywords:
                if find_value_by_keyword(lower_part, keyword):
                    new_attribute['special_attribute'] = keyword
                    new_attribute['special_value'] = find_value_by_keyword(lower_part, keyword)
                    break
            
            if 'special_attribute' not in new_attribute:
                new_attribute['special_attribute'] = ''
                new_attribute['special_value'] = '0'
        
        attributes = [old_attribute, new_attribute]
        
        print("解析结果:")
        print(f"  旧异兽: {old_attribute}")
        print(f"  新异兽: {new_attribute}")
        
        return attributes
        
    except Exception as e:
        print(f"解析异兽属性出错: {e}")
        import traceback
        print(traceback.format_exc())
        return None


if __name__ == "__main__":
    start_time = time.time()
    text_list = capture_and_recognize()
    print(text_list)
    # if text_list:
    #     attributes = parse_beast_attributes(text_list)
    #     print(attributes)
    #     # if attributes:
    #     #     print("解析到的异兽属性:")
    #     #     for key, value in attributes.items():
    #     #         print(f"{key}: {value}")
    #     # else:
    #     #     print("未能解析出异兽属性")
    # else:
    #     print("OCR识别失败")
    end_time = time.time()
    print(f"OCR识别耗时: {end_time - start_time:.2f}秒")