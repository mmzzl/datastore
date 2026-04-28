import sys, os
sys.path.insert(0, 'apps/api')
os.environ['PYTHONPATH'] = 'apps/api'
from app.storage.mongo_client import MongoStorage
from app.core.config import settings

storage = MongoStorage(host=settings.mongodb_host, port=settings.mongodb_port, db_name=settings.mongodb_database, username=settings.mongodb_username, password=settings.mongodb_password)
storage.connect()
col = storage.kline_collection

# 1. 检查 frequency=0 的最新日期
latest = col.find_one({"frequency": 0}, sort=[("date", -1)])
print(f"Latest date (freq=0): {latest.get('date') if latest else 'NONE'}")

# 2. 查 distinct dates count
dates = col.distinct("date", {"frequency": 0})
print(f"Total distinct dates: {len(dates)}")
print(f"Latest 5: {sorted(dates)[-5:] if dates else 'NONE'}")

# 3. 用 600000 查数据
for raw_code in ["600000", "000001", "600519"]:
    cnt = col.count_documents({"code": raw_code, "frequency": 0})
    print(f"  code={raw_code!r} (freq=0): {cnt} docs")
    if cnt > 0:
        doc = col.find_one({"code": raw_code, "frequency": 0}, sort=[("date", -1)])
        print(f"    latest: {doc.get('date') if doc else 'NONE'}")

storage.close()
