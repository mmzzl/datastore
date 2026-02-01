import baostock as bs

lg = bs.login()
print(f'Login result: {lg.error_code} - {lg.error_msg}')

if lg.error_code == '0':
    # Test with 2023 data
    rs = bs.query_history_k_data_plus(
        "sh.600000",
        "date,code,open,high,low,close,volume,amount,adjustflag",
        start_date='2023-12-01',
        end_date='2023-12-31',
        frequency="d",
        adjustflag="3"
    )
    print(f'\nQuery result for 2023-12: {rs.error_code} - {rs.error_msg}')
    if rs.error_code == '0':
        print(f'Data rows: {len(rs.data)}')
        if len(rs.data) > 0:
            print('Sample data:')
            for i, row in enumerate(rs.data[:3]):
                print(f'  {row}')
    
    # Test with 2024 data
    rs = bs.query_history_k_data_plus(
        "sh.600000",
        "date,code,open,high,low,close,volume,amount,adjustflag",
        start_date='2024-01-01',
        end_date='2024-01-05',
        frequency="d",
        adjustflag="3"
    )
    print(f'\nQuery result for 2024-01: {rs.error_code} - {rs.error_msg}')
    if rs.error_code == '0':
        print(f'Data rows: {len(rs.data)}')
        if len(rs.data) > 0:
            print('Sample data:')
            for i, row in enumerate(rs.data[:3]):
                print(f'  {row}')

bs.logout()
