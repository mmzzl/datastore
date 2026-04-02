#!/usr/bin/env python3
"""
Check holdings data in MongoDB

This script checks if there are any holdings data for the admin user.
"""

import asyncio
import logging

from app.storage.mongo_client import MongoStorage
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Check holdings data in MongoDB."""
    logger.info("Checking holdings data in MongoDB...")
    
    storage = MongoStorage(
        host=settings.mongodb_host,
        port=settings.mongodb_port,
        db_name=settings.mongodb_database,
        username=settings.mongodb_username,
        password=settings.mongodb_password,
    )
    
    try:
        # Connect to MongoDB
        storage.connect()
        logger.info("Connected to MongoDB successfully")
        
        # Check if holdings collection exists
        collections = storage.db.list_collection_names()
        logger.info(f"Available collections: {collections}")
        
        if "holdings" in collections:
            # Check holdings for admin user
            holdings_collection = storage.db.get_collection("holdings")
            
            # Get all documents
            all_holdings = list(holdings_collection.find())
            logger.info(f"Total holdings documents: {len(all_holdings)}")
            
            if all_holdings:
                logger.info("Holdings documents:")
                for doc in all_holdings:
                    logger.info(f"  ID: {doc.get('_id')}, User: {doc.get('user_id')}, Code: {doc.get('code')}, Quantity: {doc.get('quantity', 0)}")
            else:
                logger.warning("No holdings documents found")
            
            # Check specifically for admin user
            admin_holdings = list(holdings_collection.find({"user_id": "admin"}))
            logger.info(f"Admin holdings: {len(admin_holdings)}")
            
            if admin_holdings:
                logger.info("Admin holdings details:")
                for doc in admin_holdings:
                    logger.info(f"  Code: {doc.get('code')}, Name: {doc.get('name')}, Quantity: {doc.get('quantity', 0)}, Cost: {doc.get('average_cost', 0)}")
            else:
                logger.warning("No holdings found for admin user")
        else:
            logger.warning("Holdings collection does not exist")
            
    except Exception as e:
        logger.error(f"Error checking holdings data: {e}")
        raise
    finally:
        # Close connection
        storage.close()
        logger.info("MongoDB connection closed")

if __name__ == "__main__":
    asyncio.run(main())