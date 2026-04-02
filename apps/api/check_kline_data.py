#!/usr/bin/env python3
"""
Check K-line data format in MongoDB

This script checks the format of K-line data for the stocks in holdings.
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
    """Check K-line data format in MongoDB."""
    logger.info("Checking K-line data format in MongoDB...")
    
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
        
        # Check if stock_kline collection exists
        collections = storage.db.list_collection_names()
        logger.info(f"Available collections: {collections}")
        
        if "stock_kline" in collections:
            # Check K-line data for the stocks in holdings
            test_codes = ["SH600000", "SZ159930", "SZ159934", "SH561360"]
            
            for code in test_codes:
                try:
                    # Try with the original code format
                    klines = storage.get_kline(code, limit=5)
                    logger.info(f"K-line data for {code} (original format): {len(klines)} records")
                    
                    if klines:
                        logger.info(f"Sample K-line data for {code}:")
                        for i, kline in enumerate(klines[:2]):
                            logger.info(f"  Record {i+1}: date={kline.get('date')}, close={kline.get('close')}")
                    else:
                        # Try with different code formats
                        if code.startswith("SH"):
                            alt_code = code[2:]  # Remove "SH" prefix
                            klines = storage.get_kline(alt_code, limit=5)
                            logger.info(f"K-line data for {alt_code} (without SH prefix): {len(klines)} records")
                        elif code.startswith("SZ"):
                            alt_code = code[2:]  # Remove "SZ" prefix
                            klines = storage.get_kline(alt_code, limit=5)
                            logger.info(f"K-line data for {alt_code} (without SZ prefix): {len(klines)} records")
                            
                        # Try with .SH or .SZ suffix
                        if code.startswith("SH"):
                            alt_code = code[2:] + ".SH"
                            klines = storage.get_kline(alt_code, limit=5)
                            logger.info(f"K-line data for {alt_code} (with .SH suffix): {len(klines)} records")
                        elif code.startswith("SZ"):
                            alt_code = code[2:] + ".SZ"
                            klines = storage.get_kline(alt_code, limit=5)
                            logger.info(f"K-line data for {alt_code} (with .SZ suffix): {len(klines)} records")
                            
                except Exception as e:
                    logger.error(f"Error checking K-line data for {code}: {e}")
        else:
            logger.warning("stock_kline collection does not exist")
            
    except Exception as e:
        logger.error(f"Error checking K-line data: {e}")
        raise
    finally:
        # Close connection
        storage.close()
        logger.info("MongoDB connection closed")

if __name__ == "__main__":
    asyncio.run(main())