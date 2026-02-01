import baostock as bs
from datetime import datetime, timedelta

lg = bs.login()
print(f'Login result: {lg.error_code} - {lg.error_msg}')

if lg.error_code == '0':
    # 获取交易日历
    rs = bs.query_trade_dates(start_date="2024-01-01", end_date="2024-01-31")
    print(f'\nQuery trade dates result: {rs.error_code} - {rs.error_msg}')
    print(f'Data rows: {len(rs.data)}')
    
    if len(rs.data) > 0:
        print('\n交易日列表（最后10个）:')
        for i, row in enumerate(rs.data[-10:], 1):
            print(f'  {i}. {row[0]}')
        
        print(f'\n最新交易日: {rs.data[-1][0]}')

bs.logout()
