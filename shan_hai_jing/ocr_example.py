import time
import json
from paddleocr import PaddleOCR
import os

from pyautogui import screenshot

# 跳过模型源检查，关闭所有额外功能
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

ocr = PaddleOCR(
    lang='ch'
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
            screenshot_path = "snipaste_01.png"
            result = ocr.predict(screenshot_path)
            
            # 提取文字
            if result and isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict):
                    text_list = result[0].get('rec_texts', [])
                else:
                    # 尝试直接从结果中提取文字
                    text_list = []
                    for item in result:
                        if isinstance(item, list) and len(item) > 1:
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
    if not text_list:
        return None
    print(text_list)
    attributes = []
    old_attribute = {
        'name': text_list[0],
        'type': text_list[1],
        'hp': int(text_list[4]),
        'attack': int(text_list[8]),
        'defense': int(text_list[11]),
        'speed': int(text_list[15]),
        'special_attribute': text_list[5],  # 特殊属性（如闪避、吸血等）
        'special_value': text_list[6]  # 特殊属性的数值
    }
    new_attribute = {
        'name': text_list[21],
        'type': text_list[22],
        'hp': int(text_list[25]),
        'attack': int(text_list[29]),
        'defense': int(text_list[32]),
        'speed': int(text_list[34]),
        'special_attribute': text_list[26],  # 特殊属性（如闪避、吸血等）
        'special_value': text_list[27]  # 特殊属性的数值
    }
    attributes.append(old_attribute)
    attributes.append(new_attribute)
    
    return attributes

if __name__ == "__main__":
    text_list = capture_and_recognize()
    if text_list:
        attributes = parse_beast_attributes(text_list)
        print(attributes)
        # if attributes:
        #     print("解析到的异兽属性:")
        #     for key, value in attributes.items():
        #         print(f"{key}: {value}")
        # else:
        #     print("未能解析出异兽属性")
    else:
        print("OCR识别失败")