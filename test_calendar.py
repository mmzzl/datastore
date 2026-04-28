import sys, os, time
sys.path.insert(0, 'apps/api')
os.environ['PYTHONPATH'] = 'apps/api'

from pymongo import MongoClient
from urllib.parse import quote_plus
from app.core.config import settings

conn_str = f'mongodb://{settings.mongodb_username}:{quote_plus(settings.mongodb_password)}@{settings.mongodb_host}:{settings.mongodb_port}'
client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
db = client[settings.mongodb_database]
col = db['stock_kline']

# Test $group aggregation for daily data
t0 = time.time()
dates = set()
for doc in col.aggregate([
    {"$match": {"frequency": 9}},
    {"$group": {"_id": "$date"}},
]):
    d = doc.get("_id")
    if d:
        dates.add(d.split(" ")[0] if " " in d else d)
t1 = time.time()

with open('d:/datastore/qlib_debug5.txt', 'w') as f:
    f.write(f"daily_group_elapsed={t1-t0:.1f}s\n")
    f.write(f"daily_dates_count={len(dates)}\n")
    sorted_dates = sorted(dates)
    if sorted_dates:
        f.write(f"daily_last={sorted_dates[-1]}\n")

# Test $group aggregation for 5min data
t2 = time.time()
dates_5min = set()
for doc in col.aggregate([
    {"$match": {"frequency": 0}},
    {"$group": {"_id": "$date"}},
]):
    d = doc.get("_id")
    if d:
        dates_5min.add(d.split(" ")[0] if " " in d else d)
t3 = time.time()

with open('d:/datastore/qlib_debug5.txt', 'a') as f:
    f.write(f"5min_group_elapsed={t3-t2:.1f}s\n")
    f.write(f"5min_dates_count={len(dates_5min)}\n")
    sorted_5min = sorted(dates_5min)
    if sorted_5min:
        f.write(f"5min_last={sorted_5min[-1]}\n")

client.close()
