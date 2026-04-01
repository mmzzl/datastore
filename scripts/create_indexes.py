"""
MongoDB Index Creation Script

Creates indexes for collections used by Qlib, scheduler, backtest, and notification modules.
Run this script after deployment to optimize query performance.

Usage:
    py -3.12 scripts/create_indexes.py [--dry-run]
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from pymongo import MongoClient, ASCENDING, DESCENDING, TEXT
from pymongo.errors import PyMongoError
from urllib.parse import quote_plus

sys.path.insert(0, str(Path(__file__).parent.parent))
from apps.api.app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


INDEX_DEFINITIONS: Dict[str, List[Dict[str, Any]]] = {
    "qlib_models": [
        {"keys": [("model_id", ASCENDING)], "unique": True, "name": "idx_model_id"},
        {"keys": [("status", ASCENDING)], "name": "idx_status"},
        {"keys": [("created_at", DESCENDING)], "name": "idx_created_at"},
        {"keys": [("model_type", ASCENDING), ("created_at", DESCENDING)], "name": "idx_type_created"},
        {"keys": [("approved", ASCENDING), ("sharpe_ratio", DESCENDING)], "name": "idx_approved_sharpe"},
    ],
    "backtest_results": [
        {"keys": [("model_id", ASCENDING)], "name": "idx_model_id"},
        {"keys": [("created_at", DESCENDING)], "name": "idx_created_at"},
        {"keys": [("model_id", ASCENDING), ("created_at", DESCENDING)], "name": "idx_model_created"},
        {"keys": [("sharpe_ratio", DESCENDING)], "name": "idx_sharpe"},
        {"keys": [("annual_return", DESCENDING)], "name": "idx_return"},
    ],
    "risk_reports": [
        {"keys": [("report_id", ASCENDING)], "unique": True, "name": "idx_report_id"},
        {"keys": [("created_at", DESCENDING)], "name": "idx_created_at"},
        {"keys": [("report_type", ASCENDING), ("created_at", DESCENDING)], "name": "idx_type_created"},
        {"keys": [("status", ASCENDING)], "name": "idx_status"},
    ],
    "scheduler_jobs": [
        {"keys": [("job_id", ASCENDING)], "unique": True, "name": "idx_job_id"},
        {"keys": [("job_type", ASCENDING)], "name": "idx_job_type"},
        {"keys": [("enabled", ASCENDING)], "name": "idx_enabled"},
        {"keys": [("next_run_time", ASCENDING)], "name": "idx_next_run"},
        {"keys": [("job_type", ASCENDING), ("enabled", ASCENDING)], "name": "idx_type_enabled"},
    ],
    "job_executions": [
        {"keys": [("execution_id", ASCENDING)], "unique": True, "name": "idx_execution_id"},
        {"keys": [("job_id", ASCENDING)], "name": "idx_job_id"},
        {"keys": [("status", ASCENDING)], "name": "idx_status"},
        {"keys": [("started_at", DESCENDING)], "name": "idx_started_at"},
        {"keys": [("job_id", ASCENDING), ("started_at", DESCENDING)], "name": "idx_job_started"},
        {"keys": [("status", ASCENDING), ("started_at", DESCENDING)], "name": "idx_status_started"},
    ],
    "dingtalk_configs": [
        {"keys": [("user_id", ASCENDING)], "name": "idx_user_id"},
        {"keys": [("user_id", ASCENDING), ("is_active", ASCENDING)], "name": "idx_user_active"},
        {"keys": [("is_active", ASCENDING)], "name": "idx_active"},
        {"keys": [("created_at", DESCENDING)], "name": "idx_created_at"},
    ],
}


def create_mongo_client() -> MongoClient:
    """Create MongoDB client using settings."""
    if settings.mongodb_username and settings.mongodb_password:
        encoded_password = quote_plus(settings.mongodb_password)
        connection_string = f"mongodb://{settings.mongodb_username}:{encoded_password}@{settings.mongodb_host}:{settings.mongodb_port}"
        client = MongoClient(connection_string)
    else:
        client = MongoClient(settings.mongodb_host, settings.mongodb_port)
    return client


def get_existing_indexes(db, collection_name: str) -> set:
    """Get existing index names for a collection."""
    try:
        if collection_name not in db.list_collection_names():
            return set()
        indexes = db[collection_name].list_indexes()
        return {idx["name"] for idx in indexes}
    except PyMongoError as e:
        logger.warning(f"Could not list indexes for {collection_name}: {e}")
        return set()


def create_indexes(db, dry_run: bool = False) -> Dict[str, Any]:
    """
    Create indexes for all collections.

    Args:
        db: MongoDB database object
        dry_run: If True, only show what would be done

    Returns:
        Dictionary with results
    """
    results = {
        "created": [],
        "skipped": [],
        "errors": [],
        "dry_run": dry_run,
    }

    for collection_name, indexes in INDEX_DEFINITIONS.items():
        logger.info(f"\nProcessing collection: {collection_name}")

        existing = get_existing_indexes(db, collection_name)

        for index_def in indexes:
            index_name = index_def.get("name")
            keys = index_def.get("keys", [])
            unique = index_def.get("unique", False)

            if index_name in existing:
                logger.info(f"  [SKIP] Index '{index_name}' already exists")
                results["skipped"].append(f"{collection_name}.{index_name}")
                continue

            if dry_run:
                logger.info(f"  [DRY-RUN] Would create index '{index_name}' on {keys}")
                results["created"].append(f"{collection_name}.{index_name}")
                continue

            try:
                collection = db[collection_name]
                collection.create_index(
                    keys,
                    name=index_name,
                    unique=unique,
                    background=True,
                )
                logger.info(f"  [OK] Created index '{index_name}'")
                results["created"].append(f"{collection_name}.{index_name}")
            except PyMongoError as e:
                logger.error(f"  [ERROR] Failed to create index '{index_name}': {e}")
                results["errors"].append(f"{collection_name}.{index_name}: {str(e)}")

    return results


def print_summary(results: Dict[str, Any]):
    """Print summary of index creation."""
    print("\n" + "=" * 60)
    print("Index Creation Summary")
    print("=" * 60)

    if results["dry_run"]:
        print("*** DRY RUN MODE - No changes were made ***\n")

    print(f"Created: {len(results['created'])}")
    print(f"Skipped (existing): {len(results['skipped'])}")
    print(f"Errors: {len(results['errors'])}")

    if results["errors"]:
        print("\nErrors:")
        for error in results["errors"]:
            print(f"  - {error}")

    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Create MongoDB indexes")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    args = parser.parse_args()

    logger.info("Connecting to MongoDB...")
    client = create_mongo_client()

    try:
        client.admin.command("ping")
        logger.info(f"Connected to MongoDB at {settings.mongodb_host}:{settings.mongodb_port}")

        db = client[settings.mongodb_database]

        logger.info(f"Database: {settings.mongodb_database}")
        logger.info(f"Dry run: {args.dry_run}")

        results = create_indexes(db, dry_run=args.dry_run)
        print_summary(results)

        if results["errors"] and not args.dry_run:
            sys.exit(1)

    except PyMongoError as e:
        logger.error(f"MongoDB error: {e}")
        sys.exit(1)
    finally:
        client.close()
        logger.info("MongoDB connection closed")


if __name__ == "__main__":
    main()
