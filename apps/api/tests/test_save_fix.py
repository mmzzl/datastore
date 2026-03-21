from app.storage.mongo_client import MongoStorage
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

print("Testing MongoStorage save functionality with string input...")
try:
    # Create a MongoStorage instance
    storage = MongoStorage(
        host=settings.mongodb_host,
        port=settings.mongodb_port,
        db_name=settings.mongodb_database,
        username=settings.mongodb_username,
        password=settings.mongodb_password
    )
    
    # Connect to MongoDB
    storage.connect()
    print("Connected to MongoDB")
    
    # Test saving a string (this was causing the error)
    test_string = "This is a test string"
    result = storage.save(test_string)
    print(f"Saved string successfully: {result}")
    
    # Test saving a dictionary (should still work)
    test_dict = {"key": "value", "number": 123}
    result = storage.save(test_dict)
    print(f"Saved dictionary successfully: {result}")
    
    # Close the connection
    storage.close()
    print("Connection closed")
    
    print("All tests passed!")
except Exception as e:
    print(f"Test failed: {e}")
    import traceback
    traceback.print_exc()
