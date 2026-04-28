import sys, os
sys.path.insert(0, 'apps/api')
os.environ['PYTHONPATH'] = 'apps/api'

from app.qlib.bin_converter import QlibBinConverter

c = QlibBinConverter()

# 测试 _build_calendar
print("测试 _build_calendar...")
calendar = c._build_calendar()
print(f"日历共有 {len(calendar)} 个日期")
print(f"最新 10 个日期: {calendar[-10:]}")

# 测试 _build_instruments (CSI300)
print("\n测试 _build_instruments (CSI300)...")
from app.qlib.config import get_instruments
instr_list = c._build_instruments(get_instruments('csi300'))
print(f"共有 {len(instr_list)} 个股票")
print(f"第一个: {instr_list[0]}")
print(f"最后一个: {instr_list[-1]}")
