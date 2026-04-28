import pandas as pd

df = pd.read_csv('apps/api/data/all_stock_industry.csv', encoding='utf-8-sig')

# Industry-level sectors (real economic sectors, not market sentiment labels)
# Keywords for filtering
industry_keywords = ['银行', '保险', '证券', '医药', '医疗', '食品', '饮料', '白酒', '汽车', 
    '地产', '房地产', '建筑', '建材', '钢铁', '煤炭', '有色', '黄金', '化工',
    '电力', '能源', '光伏', '风电', '氢能', '锂电', '电池', '新能源',
    '军工', '国防', '农业', '农林', '牧渔', '纺织', '服装', '造纸', '轻工',
    '家电', '电子', '通信', '半导体', '芯片', '软件', '计算机', '传媒', '互联网',
    '物流', '航空', '航运', '铁路', '公路', '港口', '运输', '交通',
    '环保', '公用', '消费', '白酒', '机械', '工程', '材料', '有色',
    '中药', '创新药', '疫苗', '医美', '机器人', '人工智能', '大数据', '云计算',
    '游戏', '影视', '旅游', '酒店', '餐饮', '零售', '贸易', '商业',
    '军工', '船舶', '航天', '教育', '传媒', '房地产', '建材', '建筑']

valid_sectors = set()
for ind in df.iloc[:, 0].unique():
    for kw in industry_keywords:
        if kw in ind:
            valid_sectors.add(ind)
            break

# Exclude market sentiment / timing labels
exclude_keywords = ['涨停', '跌停', '首板', '连板', '打板', '炸板', '封板', '扭亏', '预增', '预减',
    '中报', '季报', '年报', 'ST', '热股', '高振幅', '小盘', '大盘', '价值股', '红利股',
    '上证', '沪深', '中证', '上证180', '上证50', '中证500', 'HS300', 'MSCI',
    '破净', '行业龙头', 'QFII', '北上', '深股通', '沪股通',
    '昨日', '最近', '今日', '白马股', '次新股', '高送转', '低价股']

valid = set()
for s in valid_sectors:
    if not any(kw in s for kw in exclude_keywords):
        valid.add(s)

valid = sorted(valid)

with open('apps/api/industry_mapping_plan.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total original sectors: {len(df.iloc[:, 0].unique())}\n")
    f.write(f"Filtered industry-like sectors: {len(valid)}\n\n")
    for s in valid:
        # Count how many stocks in this sector
        count = len(df[df.iloc[:, 0] == s])
        f.write(f"  {s} ({count} stocks)\n")
