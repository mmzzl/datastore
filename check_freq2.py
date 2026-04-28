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

# Check distinct values of frequency
freqs = col.distinct('frequency')
print(f"distinct_frequencies={freqs}")

# Check some sample data for each frequency
for freq in freqs:
    sample = col.find_one({'frequency': freq})
    print(f"\nsample_freq_{freq}:")
    print(f"  code={sample.get('code')}")
    print(f"  date={sample.get('date')}")
    print(f"  frequency={sample.get('frequency')}")
    print(f"  close={sample.get('close')}")

# Check data count for each frequency
for freq in freqs:
    cnt = col.count_documents({'frequency': freq})
    print(f"\ncount_freq_{freq}={cnt}")

# Check the latest date for each frequency
for freq in freqs:
    doc = col.find_one({'frequency': freq}, {'date': 1}, sort=[('date', -1)])
    print(f"\nlatest_freq_{freq}={doc.get('date')}")

client.close()
