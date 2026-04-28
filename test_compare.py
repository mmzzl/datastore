import sys, os
sys.path.insert(0, 'apps/api')
os.environ['PYTHONPATH'] = 'apps/api'

from app.qlib.bin_converter import QlibBinConverter

c = QlibBinConverter()
calendar = c._build_calendar()

# Read existing
cal_file = c.target_dir / "calendars" / "day.txt"
existing = set(cal_file.read_text(encoding="utf-8").strip().splitlines())

# Find dates in calendar but not in existing
new_dates = [d for d in calendar if d not in existing]

with open('d:/datastore/qlib_compare.txt', 'w') as f:
    f.write(f"calendar_len={len(calendar)}\n")
    f.write(f"existing_len={len(existing)}\n")
    f.write(f"new_dates_len={len(new_dates)}\n")
    if new_dates:
        f.write(f"new_dates_first5={new_dates[:5]}\n")
        f.write(f"new_dates_last5={new_dates[-5:]}\n")
    # Check if some dates from calendar are in existing
    overlap = [d for d in calendar[-10:] if d in existing]
    f.write(f"overlap_in_last10={len(overlap)}\n")
    # Check last 10 dates in calendar
    f.write(f"calendar_last10={calendar[-10:]}\n")
    # Check last 10 dates in existing
    sorted_existing = sorted(existing)
    f.write(f"existing_last10={sorted_existing[-10:]}\n")
