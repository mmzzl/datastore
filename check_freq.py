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

with open('d:/datastore/check_freq.txt', 'w') as f:
    f.write(f"distinct_frequencies={freqs}\n")

    # Check some sample data for each frequency
    for freq in freqs:
        sample = col.find_one({'frequency': freq})
        f.write(f"\nsample_freq_{freq}:\n")
        f.write(f"  code={sample.get('code')}\n")
        f.write(f"  date={sample.get('date')}\n")
        f.write(f"  frequency={sample.get('frequency')}\n")
        f.write(f"  close={sample.get('close')}\n")

    # Check data count for each frequency
    for freq in freqs:
        cnt = col.count_documents({'frequency': freq})
        f.write(f"\ncount_freq_{freq}={cnt}\n")

    # Check the latest date for each frequency
    for freq in freqs:
        doc = col.find_one({'frequency': freq}, {'date': 1}, sort=[('date', -1)])
        f.write(f"\nlatest_freq_{freq}={doc.get('date')}\n")

client.close()
