import pandas as pd
import os

df = pd.read_csv('apps/api/data/all_stock_industry.csv', encoding='utf-8-sig')

# Build mapping: code -> first matching industry name
# Codes are stored as numbers (600726), we need to handle sh./sz. prefix
code_to_industry = {}
for _, row in df.iterrows():
    code = str(row['代码'])
    industry = row['板块名称']
    if code not in code_to_industry:
        code_to_industry[code] = industry

# Also build code -> name mapping
code_to_name = {}
df_stock = pd.read_csv('apps/api/data/all_stock.csv', encoding='utf-8')
for _, row in df_stock.iterrows():
    code = row['code']
    name = row['code_name']
    code_to_name[code] = name

# Print samples
print(f"Industry mappings: {len(code_to_industry)}")
print(f"Name mappings: {len(code_to_name)}")

# Sample codes that might be in holdings
sample_codes = ['600519', '600036', '601318', '000858', '002415']
for c in sample_codes:
    ind = code_to_industry.get(c, 'NOT FOUND')
    name = code_to_name.get(f"sh.{c}", code_to_name.get(f"sz.{c}", 'NOT FOUND'))
    print(f"  {c}: {name} -> {ind}")

# Check how many stocks have industry vs not
with open('apps/api/industry_from_csv.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total industry mappings: {len(code_to_industry)}\n\n")
    for c in list(code_to_industry.keys())[:50]:
        f.write(f"  {c}: {code_to_industry[c]}\n")
