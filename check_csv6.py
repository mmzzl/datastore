import pandas as pd

df = pd.read_csv('apps/api/data/all_stock_industry.csv', encoding='utf-8-sig')
cols = df.columns.tolist()

with open('apps/api/csv_analysis.txt', 'w', encoding='utf-8') as f:
    f.write(f'Columns: {cols}\n')
    f.write(f'Rows: {len(df)}\n\n')
    
    # Check how many unique stock codes
    codes = df['代码'].unique()
    f.write(f'Unique stock codes: {len(codes)}\n')
    
    # Check each stock appears in how many sectors
    code_counts = df['代码'].value_counts()
    f.write(f'Avg sectors per stock: {code_counts.mean():.1f}\n')
    f.write(f'Max sectors per stock: {code_counts.max()}\n')
    
    # Sample a stock to see all its sectors
    sample_code = codes[0]
    stock_rows = df[df['代码'] == sample_code]
    f.write(f'\nStock {sample_code} sectors:\n')
    for _, r in stock_rows.iterrows():
        f.write(f'  {r.iloc[0]} ({r.iloc[1]})\n')
    
    # Try to find Shenwan / 申万 sectors
    sw = df[df.iloc[:, 0].str.contains('申万', na=False)]
    f.write(f'\nSectors containing "申万": {len(sw)}\n')
    if len(sw) > 0:
        for x in sw.iloc[:, 0].unique():
            f.write(f'  {x}\n')
    
    # Check for industry-level sectors (not concept boards)
    # Concept boards usually contain 概念、板块
    concepts = df[df.iloc[:, 0].str.contains('概念|板块', na=False)]
    f.write(f'\nSectors with 概念/板块: {len(concepts)}\n')
    
    # Try to find 行业 classification
    hy = df[df.iloc[:, 0].str.contains('行业', na=False)]
    f.write(f'Sectors with 行业: {len(hy)}\n')
    for x in hy.iloc[:, 0].unique():
        f.write(f'  {x}\n')
    
    # Show all unique industries - check if there are proper industry names
    all_inds = df.iloc[:, 0].unique()
    f.write(f'\nTotal sectors: {len(all_inds)}\n')
    f.write(f'First 100 sectors:\n')
    for x in sorted(all_inds)[:100]:
        f.write(f'  {x}\n')
    
    # Check specific codes 
    test_codes = ['600519', '600036', '601318', '000858', '002415', '300750', '000001', '600000', '600900']
    f.write(f'\n\nTest stocks:\n')
    for code in test_codes:
        rows = df[df['代码'] == int(code)] if code.isdigit() else df[df['代码'] == code]
        f.write(f'{code}: {len(rows)} sectors\n')
        for _, r in rows.head(3).iterrows():
            f.write(f'  {r.iloc[0]}\n')
