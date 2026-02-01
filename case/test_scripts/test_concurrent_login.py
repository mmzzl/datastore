import baostock as bs
import time

# Test multiple consecutive login/logout
print("Testing consecutive login/logout...")
for i in range(5):
    lg = bs.login()
    print(f"Attempt {i+1}: login - {lg.error_code} ({lg.error_msg})")
    
    if lg.error_code == '0':
        rs = bs.query_history_k_data_plus(
            "sh.600033",
            "date,code,open,high,low,close,volume,amount,adjustflag",
            start_date='2024-01-01',
            end_date='2024-01-05',
            frequency="d",
            adjustflag="3"
        )
        print(f"  Query: {rs.error_code} ({rs.error_msg}), Data rows: {len(rs.data)}")
        
        lo = bs.logout()
        print(f"  logout - {lo.error_code} ({lo.error_msg})")
    
    time.sleep(0.5)

print("\nTesting stocks that might be suspended...")
# Test a few stocks that showed empty
test_stocks = ["sh.600033", "sh.600020", "sh.600026", "sh.600032"]

for stock in test_stocks:
    lg = bs.login()
    if lg.error_code == '0':
        rs = bs.query_history_k_data_plus(
            stock,
            "date,code,open,high,low,close,volume,amount,adjustflag",
            start_date='2024-01-01',
            end_date='2024-01-05',
            frequency="d",
            adjustflag="3"
        )
        print(f"{stock}: {rs.error_code}, Data rows: {len(rs.data)}")
        bs.logout()
