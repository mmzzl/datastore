import pandas as pd

df = pd.read_csv('apps/api/data/all_stock_industry.csv', encoding='utf-8-sig')

# Build a mapping from stock code to its "best" industry sector
# Preference: real industry sectors (not market sentiment)
exclude_phrases = ['涨停', '跌停', '首板', '连板', '打板', '扭亏', '预增', '预减',
    '中报', '季报', '年报', 'ST', '热股', '高振幅', '小盘', '大盘', 
    '上证', '沪深', '中证', 'MSCI', 'HS300', 'QFII', '北上', '深股通', '沪股通',
    '破净', '昨日', '最近', '今日', '次新股', '高送转', '低价股', 
    '板块', '东方财富', 'AB股', 'AH股', 'B股', 'GDR', 'IPO受益',
    '价值股', '红利股', '茅指数', '央视', '长江三角']

# Priority industry sectors (more specific = better)
priority_sectors = [
    '银行', '证券', '保险', '白酒', '军工', '船舶制造', '航天航空',
    '汽车整车', '新能源车', '光伏概念', '风电', '氢能源', '锂电池',
    '中药概念', '创新药', '医疗器械', '生物疫苗', '医美',
    '半导体', '芯片', '国产芯片', '人工智能', '机器人',
    '云计算', '大数据', '国产软件', '互联网', '通信',
    '食品', '白酒', '农业', '化工', '钢铁', '煤炭', '有色',
    '房地产', '建筑', '建材', '工程', '电力', '环保',
    '传媒', '游戏', '影视', '旅游', '零售', '物流', '航空',
    '造纸', '纺织', '黄金', '材料', '机械', '家电', '汽车',
    '新能源', '氢能', '储能', '节能', '消费',
]

def get_best_industry(code):
    """Get best industry sector for a stock code from the CSV."""
    rows = df[df['代码'] == code]
    if len(rows) == 0:
        return None
    
    sectors = rows.iloc[:, 0].tolist()
    
    # Exclude market sentiment sectors
    real = [s for s in sectors if not any(kw in s for kw in exclude_phrases)]
    if not real:
        return None
    
    # Return the first one (already sorted by relevance in original data)
    return real[0]

# Build code -> industry mapping
code_to_industry = {}
codes = df['代码'].unique()
for c in codes:
    ind = get_best_industry(c)
    if ind:
        code_to_industry[str(c)] = ind

with open('apps/api/csv_industry_mapping.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total codes mapped: {len(code_to_industry)} out of {len(codes)}\n\n")
    
    # Sample stocks
    test = ['600519', '600036', '601318', '000858', '002415', '300750', '000001', '600000', '600900', '600276', '300059']
    for c in test:
        ind = code_to_industry.get(c, 'NOT FOUND')
        rows = df[df['代码'] == int(c)]
        f.write(f"\n{c}:\n")
        for _, r in rows.head(5).iterrows():
            f.write(f"  {r.iloc[0]}\n")
        f.write(f"  => Selected: {ind}\n")

# Write the mapping as a CSV
output = []
for code, industry in code_to_industry.items():
    output.append({'code': code, 'industry': industry})
out_df = pd.DataFrame(output)
out_df.to_csv('apps/api/data/code_to_industry.csv', index=False, encoding='utf-8')
print(f"Saved {len(out_df)} mappings to code_to_industry.csv")
print(f"Coverage: {len(code_to_industry)}/{len(codes)} = {len(code_to_industry)/len(codes)*100:.1f}%")
