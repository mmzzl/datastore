import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))
os.environ.setdefault("PYTHONPATH", os.path.join(os.path.dirname(__file__), 'apps', 'api'))
sys.argv = ['', '--config', os.path.join(os.path.dirname(__file__), 'apps', 'api', 'config', 'config.yaml')]

from app.storage.mongo_client import MongoStorage
from app.core.config import settings

print("MongoDB config:", settings.mongodb_host, settings.mongodb_port, settings.mongodb_database, settings.mongodb_username)

storage = MongoStorage(
    host=settings.mongodb_host,
    port=settings.mongodb_port,
    db_name=settings.mongodb_database,
    username=settings.mongodb_username,
    password=settings.mongodb_password,
)
storage.connect()
coll = storage.db.get_collection("stock_info")
doc = coll.find_one()
print("stock_info doc:", doc)
if not doc:
    print("stock_info is empty")
else:
    print("Keys:", list(doc.keys()))
    if "industry" in doc:
        print("industry field:", doc.get("industry"))
    if "industryClassification" in doc:
        print("industryClassification:", doc.get("industryClassification"))

cnt = coll.count_documents({})
print("stock_info count:", cnt)

storage.close()
