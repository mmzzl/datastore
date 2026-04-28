import sys, os
sys.path.insert(0, 'apps/api')
os.environ['PYTHONPATH'] = 'apps/api'
from app.storage.mongo_client import MongoStorage
from app.core.config import settings

storage = MongoStorage(host=settings.mongodb_host, port=settings.mongodb_port, db_name=settings.mongodb_database, username=settings.mongodb_username, password=settings.mongodb_password)
storage.connect()
col = storage.kline_collection

# CSI300 前几个代码
from app.qlib.config import CSI_300_STOCKS
print("CSI300 first 5:", CSI_300_STOCKS[:5])

# MongoDB 中 code 的格式
docs = list(col.find({"frequency": 0}, {"code": 1, "_id": 0}).limit(10))
print("MongoDB code samples:", [d["code"] for d in docs])

# 用 CSI300 的代码查一下
test_codes = CSI_300_STOCKS[:5]
for c in test_codes:
    cnt = col.count_documents({"code": c, "frequency": 0})
    print(f"  code={c!r}: {cnt} docs")
    # 也试试带 SH/SZ 前缀
    for prefix in ['SH', 'SZ']:
        pc = prefix + c
        cnt2 = col.count_documents({"code": pc, "frequency": 0})
        if cnt2 > 0:
            print(f"  code={pc!r}: {cnt2} docs")

storage.close()
