import sys, os, time
sys.path.insert(0, 'apps/api')
os.environ['PYTHONPATH'] = 'apps/api'

from app.qlib.bin_converter import QlibBinConverter

c = QlibBinConverter()

t0 = time.time()
calendar = c._build_calendar()
t1 = time.time()

n = c._write_calendar(calendar)
t2 = time.time()

with open('d:/datastore/qlib_cal_result.txt', 'w') as f:
    f.write(f"build_elapsed={t1-t0:.1f}s\n")
    f.write(f"write_new_dates={n}\n")
    f.write(f"write_elapsed={t2-t1:.1f}s\n")
    f.write(f"total_dates={len(calendar)}\n")
    if calendar:
        f.write(f"last_date={calendar[-1]}\n")

# Verify day.txt
with open('d:/datastore/apps/api/qlib_data/cn_data/calendars/day.txt', 'r') as f2:
    lines = f2.readlines()
    with open('d:/datastore/qlib_cal_result.txt', 'a') as f:
        f.write(f"day.txt_lines={len(lines)}\n")
        if lines:
            f.write(f"day.txt_last={lines[-1].strip()}\n")
