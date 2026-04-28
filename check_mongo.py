import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))
os.environ.setdefault("PYTHONPATH", os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from app.storage.mongo_client import MongoStorage
from app.core.config import settings

storage = MongoStorage(host=settings.mongodb_host, port=settings.mongodb_port, db_name=settings.mongodb_database)
storage.connect()
coll = storage.db.get_collection("stock_info")
doc = coll.find_one()
print("stock_info doc:", doc)
cnt = coll.count_documents({})
print("stock_info count:", cnt)

# Check what industry fields exist
pipeline = [{"$group": {"_id": None, "fields": {"$addToSet": {"$objectToArray": "$$ROOT"}}}}]
sample = coll.find_one({"industry": {"$exists": True}})
if sample:
    print("\nSample with 'industry' field:", sample.get("industry"))
else:
    print("\nNo 'industry' field found")

sample2 = coll.find_one({"industryClassification": {"$exists": True}})
if sample2:
    print("\nSample with 'industryClassification' field:", sample2.get("industryClassification"))

# Check all field names in collection
pipeline = [{"$project": {"arrayofkeyvalue": {"$objectToArray": "$$ROOT"}}}, {"$unwind": "$arrayofkeyvalue"}, {"$group": {"_id": None, "allKeys": {"$addToSet": "$arrayofkeyvalue.k"}}}]
result = list(coll.aggregate(pipeline))
if result:
    print("\nAll fields in stock_info:", result[0].get("allKeys"))

storage.close()
