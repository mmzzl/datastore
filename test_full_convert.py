import sys, os, time
sys.path.insert(0, 'apps/api')
os.environ['PYTHONPATH'] = 'apps/api'

from app.qlib.bin_converter import QlibBinConverter
from app.qlib.config import get_instruments

c = QlibBinConverter()
t0 = time.time()
r = c.full_convert(instruments=get_instruments('csi300'))
t1 = time.time()

with open('d:/datastore/qlib_result.txt', 'w') as f:
    f.write(f"result={r}\n")
    f.write(f"elapsed={t1-t0:.1f}s\n")

    # Check day.txt
    with open('d:/datastore/apps/api/qlib_data/cn_data/calendars/day.txt', 'r') as cal:
        lines = cal.readlines()
        f.write(f"day.txt_total={len(lines)}\n")
        f.write(f"day.txt_last5={lines[-5:]}\n")

    # Check csi300.txt
    with open('d:/datastore/apps/api/qlib_data/cn_data/instruments/csi300.txt', 'r') as inst:
        lines = inst.readlines()
        f.write(f"csi300.txt_total={len(lines)}\n")
        f.write(f"csi300.txt_first={lines[0]}\n")
        # Find SH600000
        for line in lines:
            if line.startswith('SH600000'):
                f.write(f"csi300.txt_600000={line}\n")
                break
