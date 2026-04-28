from pymongo import MongoClient
from urllib.parse import quote_plus

conn_str = f'mongodb://admin:{quote_plus("aa123aaqqA!")}@121.37.47.63:27017'
client = MongoClient(conn_str, serverSelectionTimeoutMS=5000)
db = client['eastmoney_news']
col = db['stock_kline']

freqs = col.distinct('frequency')
print(f"distinct_frequencies: {freqs}")

for freq in freqs:
    cnt = col.count_documents({'frequency': freq})
    print(f"count_freq_{freq}: {cnt}")
    latest = col.find_one({'frequency': freq}, {'date': 1, 'code': 1}, sort=[('date', -1)])
    print(f"latest_freq_{freq}: {latest}")

# Also check some samples for 4/17/2026
sample1 = col.find_one({'date': '2026-04-17 15:00'})
print(f"\nsample_2026-04-17: {sample1}")

client.close()
