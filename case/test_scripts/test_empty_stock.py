import baostock as bs

lg = bs.login()
print(f'Login result: {lg.error_code} - {lg.error_msg}')

if lg.error_code == '0':
    # Test with sh.600033
    rs = bs.query_history_k_data_plus(
        "sh.600033",
        "date,code,open,high,low,close,volume,amount,adjustflag",
        start_date='2024-01-01',
        end_date='2024-01-05',
        frequency="d",
        adjustflag="3"
    )
    print(f'\nQuery result for sh.600033 (2024-01-01 to 2024-01-05):')
    print(f'Error code: {rs.error_code}')
    print(f'Error msg: {rs.error_msg}')
    print(f'Data rows: {len(rs.data)}')
    if len(rs.data) > 0:
        print('Sample data:')
        for i, row in enumerate(rs.data[:3]):
            print(f'  {row}')
    else:
        print('No data available for this date range')
    
    # Test with a wider date range
    rs = bs.query_history_k_data_plus(
        "sh.600033",
        "date,code,open,high,low,close,volume,amount,adjustflag",
        start_date='2023-01-01',
        end_date='2024-01-05',
        frequency="d",
        adjustflag="3"
    )
    print(f'\nQuery result for sh.600033 (2023-01-01 to 2024-01-05):')
    print(f'Error code: {rs.error_code}')
    print(f'Data rows: {len(rs.data)}')
    if len(rs.data) > 0:
        print('Sample data:')
        for i, row in enumerate(rs.data[:3]):
            print(f'  {row}')

bs.logout()
