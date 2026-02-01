from datetime import datetime, timedelta
import baostock as bs

lg = bs.login()
print(f'Login result: {lg.error_code} - {lg.error_msg}')

if lg.error_code == '0':
    # 获取最近一个月的交易日历
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    print(f'查询交易日历: {start_date} 到 {end_date}')
    
    rs = bs.query_trade_dates(start_date=start_date, end_date=end_date)
    print(f'Query result: {rs.error_code} - {rs.error_msg}')
    print(f'Data rows: {len(rs.data)}')
    
    if rs.error_code == '0' and len(rs.data) > 0:
        print(f'\n最新交易日: {rs.data[-1][0]}')
        print(f'交易日列表（最后5个）:')
        for i, row in enumerate(rs.data[-5:], 1):
            print(f'  {i}. {row[0]}')

bs.logout()
