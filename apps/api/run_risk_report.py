#!/usr/bin/env python3
"""
Manual risk report generation script

Run this script to manually generate risk reports for users.
"""

import asyncio
import logging
from datetime import datetime

from app.scheduler.risk_report_job import risk_report_handler
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to generate risk reports."""
    logger.info("Starting manual risk report generation...")

    from app.storage.mongo_client import MongoStorage
    storage = MongoStorage(
        host=settings.mongodb_host,
        port=settings.mongodb_port,
        db_name=settings.mongodb_database,
        username=settings.mongodb_username,
        password=settings.mongodb_password,
    )
    storage.connect()
    user_ids = list(storage.db.get_collection("holdings").distinct("user_id"))
    storage.close()
    if not user_ids:
        logger.warning("No users with holdings found in database")
        return
    config = {
        "user_ids": user_ids,
        "dingtalk_webhook": settings.after_market_dingtalk_webhook,
        "dingtalk_secret": settings.after_market_dingtalk_secret,
    }
    
    try:
        start_time = datetime.now()
        logger.info(f"Starting risk report generation at {start_time}")
        
        # Execute the risk report handler
        result = await risk_report_handler(config)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"Risk report generation completed in {duration:.1f} seconds")
        logger.info(f"Results: {result}")
        
        if result.get("status") == "success":
            logger.info("✅ All risk reports generated successfully!")
        elif result.get("status") == "partial":
            logger.warning("⚠️  Some risk reports failed to generate")
        else:
            logger.error("❌ Risk report generation failed")
            
    except Exception as e:
        logger.error(f"Error generating risk reports: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())