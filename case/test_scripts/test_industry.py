import baostock as bs

lg = bs.login()
print(f'Login result: {lg.error_code} - {lg.error_msg}')

if lg.error_code == '0':
    # 获取行业分类
    rs = bs.query_stock_industry()
    print(f'\nQuery stock industry result: {rs.error_code} - {rs.error_msg}')
    print(f'Fields: {rs.fields}')
    print(f'Data rows: {len(rs.data)}')
    
    if len(rs.data) > 0:
        print('\nSample data (first 10 rows):')
        for i, row in enumerate(rs.data[:10]):
            print(f'  {row}')
    
    # 获取申万一级行业分类
    rs_sw = bs.query_stock_industry(date="2024-01-05")
    print(f'\nQuery SW industry result: {rs_sw.error_code} - {rs_sw.error_msg}')
    print(f'Fields: {rs_sw.fields}')
    print(f'Data rows: {len(rs_sw.data)}')
    
    if len(rs_sw.data) > 0:
        print('\nSample data (first 10 rows):')
        for i, row in enumerate(rs_sw.data[:10]):
            print(f'  {row}')

bs.logout()
