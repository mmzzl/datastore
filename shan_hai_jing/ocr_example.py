import time
from paddleocr import PaddleOCR
import os

# 跳过模型源检查，关闭所有额外功能
os.environ['DISABLE_MODEL_SOURCE_CHECK'] = 'True'

ocr = PaddleOCR(
    lang='ch'
)

print("OCR初始化完成，可以开始识别了！")

# 开始计时
start_time = time.time()

# 使用新方法predict替代已弃用的ocr
result = ocr.predict("snipaste_01.png")

# 结束计时并计算耗时
end_time = time.time()
elapsed_time = end_time - start_time

# 调试结果结构
print("结果类型:", type(result))
print("结果长度:", len(result))
print(f"识别耗时: {elapsed_time:.2f}秒")

# 打印详细结果以便了解结构
# print("详细结果:", result)  # 可以注释掉以减少输出

# 根据实际结构提取文字
if result:
    # 检查第一级结构
    if isinstance(result[0], dict):
        # 获取识别的文本列表
        text_list = result[0].get('rec_texts', [])
        print(f"识别到{len(text_list)}个文本片段:")
        print(text_list)
    else:
        print(f"结果结构不符合预期: {type(result[0])}")

# import easyocr

# reader = easyocr.Reader(["ch_sim", "en"])
# results = reader.readtext(
#     "snipaste_01.png", text_threshold=0.4, low_text=0.4, contrast_ths=0.2
# )
# data = []
# for result in results:
#     data.append(result[1])
# print(data)
