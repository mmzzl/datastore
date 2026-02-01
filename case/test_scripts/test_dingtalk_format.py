# -*- coding: utf-8 -*-
# 测试钉钉格式化
from scripts.daily_brief_analyzer import DailyBriefAnalyzer

csv_dir = r'C:\Users\life8\.qlib\stock_data\source\all_1d_original'

analyzer = DailyBriefAnalyzer(csv_dir)

# 生成 Markdown 格式的简报
markdown_text = analyzer.format_brief_for_dingtalk("2026-01-29")

# 输出 Markdown 文本
print("=" * 80)
print("Markdown 格式预览：")
print("=" * 80)
print(markdown_text)
print("=" * 80)

# 保存到文件
with open("dingtalk_preview.md", "w", encoding="utf-8") as f:
    f.write(markdown_text)
print("\nMarkdown 已保存到: dingtalk_preview.md")
