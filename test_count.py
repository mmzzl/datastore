import sys, os
sys.path.insert(0, 'apps/api')
os.environ['PYTHONPATH'] = 'apps/api'

from pymongo import MongoClient
from urllib.parse import quote_plus
from app.core.config import settings

conn_str = f'mongodb://{settings.mongodb_username}:{quote_plus(settings.mongodb_password)}@{settings.mongodb_host}:{settings.mongodb_port}'
client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
db = client[settings.mongodb_database]
col = db['stock_kline']

count_5min = col.count_documents({'frequency': 0})
count_daily = col.count_documents({'frequency': 9})

with open('d:/datastore/qlib_debug2.txt', 'w') as f:
    f.write(f"5min={count_5min}\n")
    f.write(f"daily={count_daily}\n")

client.close()
