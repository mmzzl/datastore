import sys

sys.path.insert(0, "D:/work/datastore/apps/api")

from app.storage import MongoStorage
from app.core.config import settings

storage = MongoStorage(
    host=settings.mongodb_host,
    port=settings.mongodb_port,
    db_name=settings.mongodb_database,
    username=settings.mongodb_username,
    password=settings.mongodb_password,
)
storage.connect()

collection = storage.db["stock_selections"]
count = collection.count_documents({})
print("Total in DB:", count)

docs = list(collection.find().sort("created_at", -1).limit(5))
for doc in docs:
    print(doc.get("_id"), doc.get("status"), doc.get("strategy_type"))
