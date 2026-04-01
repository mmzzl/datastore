"""
MongoDB Rollback Script

Restores collections from backup with safety checks.

Usage:
    py -3.12 scripts/rollback.py --backup-dir ./backups/backup_20240101_120000
                                 [--collections qlib_models,backtest_results]
                                 [--dry-run]
                                 [--force]
"""

import argparse
import gzip
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from apps.api.app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class MongoDBRollback:
    """MongoDB rollback manager with safety checks."""

    def __init__(
        self,
        backup_path: Path,
        host: str = "localhost",
        port: int = 27017,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "news_db",
    ):
        self.backup_path = Path(backup_path)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database

    def validate_backup(self) -> Dict[str, Any]:
        """
        Validate backup before rollback.

        Returns:
            Validation results
        """
        results = {
            "valid": True,
            "manifest": None,
            "collections": [],
            "errors": [],
        }

        if not self.backup_path.exists():
            results["valid"] = False
            results["errors"].append(f"Backup path does not exist: {self.backup_path}")
            return results

        manifest_path = self.backup_path / "manifest.json"
        if not manifest_path.exists():
            results["valid"] = False
            results["errors"].append("Manifest file not found")
            return results

        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
            results["manifest"] = manifest

            backup_date = datetime.strptime(manifest["timestamp"], "%Y%m%d_%H%M%S")
            results["backup_date"] = backup_date.isoformat()

            for collection, info in manifest.get("collections", {}).items():
                if info.get("status") != "success":
                    continue

                file_path = Path(info["file"])
                if not file_path.exists():
                    results["valid"] = False
                    results["errors"].append(f"Missing backup file: {file_path}")
                else:
                    results["collections"].append(collection)

            if not results["collections"]:
                results["valid"] = False
                results["errors"].append("No valid collection backups found")

        except Exception as e:
            results["valid"] = False
            results["errors"].append(f"Validation error: {str(e)}")

        return results

    def get_current_counts(self, collections: List[str]) -> Dict[str, int]:
        """Get current document counts for collections."""
        from pymongo import MongoClient
        from urllib.parse import quote_plus

        counts = {}

        if self.username and self.password:
            encoded_password = quote_plus(self.password)
            uri = f"mongodb://{self.username}:{encoded_password}@{self.host}:{self.port}"
        else:
            uri = f"mongodb://{self.host}:{self.port}"

        client = MongoClient(uri)
        db = client[self.database]

        for collection in collections:
            try:
                if collection in db.list_collection_names():
                    counts[collection] = db[collection].count_documents({})
                else:
                    counts[collection] = 0
            except Exception as e:
                logger.warning(f"Could not count {collection}: {e}")
                counts[collection] = -1

        client.close()
        return counts

    def restore_collection(
        self,
        collection: str,
        backup_file: Path,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Restore a single collection from backup.

        Args:
            collection: Collection name
            backup_file: Backup file path
            dry_run: If True, don't make actual changes

        Returns:
            Restore results
        """
        results = {
            "collection": collection,
            "status": "pending",
            "documents_restored": 0,
            "error": None,
        }

        try:
            with gzip.open(backup_file, "rt", encoding="utf-8") as f:
                docs = json.load(f)

            results["documents_in_backup"] = len(docs)

            if dry_run:
                results["status"] = "dry_run"
                results["documents_restored"] = len(docs)
                return results

            from pymongo import MongoClient
            from urllib.parse import quote_plus
            from datetime import datetime as dt

            if self.username and self.password:
                encoded_password = quote_plus(self.password)
                uri = f"mongodb://{self.username}:{encoded_password}@{self.host}:{self.port}"
            else:
                uri = f"mongodb://{self.host}:{self.port}"

            client = MongoClient(uri)
            db = client[self.database]

            db[collection].drop()

            if docs:
                for doc in docs:
                    if "created_at" in doc and isinstance(doc["created_at"], str):
                        try:
                            doc["created_at"] = dt.fromisoformat(doc["created_at"])
                        except ValueError:
                            pass

                db[collection].insert_many(docs)

            results["status"] = "success"
            results["documents_restored"] = len(docs)

            client.close()

        except Exception as e:
            results["status"] = "error"
            results["error"] = str(e)
            logger.error(f"Failed to restore {collection}: {e}")

        return results

    def rollback(
        self,
        collections: Optional[List[str]] = None,
        dry_run: bool = False,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Perform rollback from backup.

        Args:
            collections: List of collections to restore (None = all)
            dry_run: If True, don't make actual changes
            force: Skip confirmation prompt

        Returns:
            Rollback results
        """
        validation = self.validate_backup()
        if not validation["valid"]:
            return {
                "status": "error",
                "errors": validation["errors"],
            }

        available_collections = validation["collections"]

        if collections:
            invalid = set(collections) - set(available_collections)
            if invalid:
                return {
                    "status": "error",
                    "errors": [f"Collections not in backup: {invalid}"],
                }
            target_collections = [c for c in collections if c in available_collections]
        else:
            target_collections = available_collections

        if not target_collections:
            return {
                "status": "error",
                "errors": ["No collections to restore"],
            }

        logger.info("\n" + "=" * 60)
        logger.info("ROLLBACK PLAN")
        logger.info("=" * 60)
        logger.info(f"Backup: {self.backup_path}")
        logger.info(f"Backup date: {validation.get('backup_date', 'unknown')}")
        logger.info(f"Collections to restore: {target_collections}")

        current_counts = self.get_current_counts(target_collections)
        logger.info("\nCurrent document counts:")
        for coll, count in current_counts.items():
            logger.info(f"  {coll}: {count}")

        if not dry_run and not force:
            print("\n" + "=" * 60)
            print("WARNING: This will DROP and REPLACE the listed collections!")
            print("=" * 60)
            confirm = input("Continue? (yes/no): ")
            if confirm.lower() != "yes":
                return {
                    "status": "cancelled",
                    "message": "Rollback cancelled by user",
                }

        results = {
            "status": "success",
            "backup_path": str(self.backup_path),
            "backup_date": validation.get("backup_date"),
            "dry_run": dry_run,
            "collections": {},
        }

        manifest = validation["manifest"]
        for collection in target_collections:
            backup_file = Path(manifest["collections"][collection]["file"])
            logger.info(f"\nRestoring {collection}...")
            restore_result = self.restore_collection(collection, backup_file, dry_run)
            results["collections"][collection] = restore_result

            if restore_result["status"] == "error":
                results["status"] = "partial_error"

        return results


def main():
    parser = argparse.ArgumentParser(description="MongoDB Rollback Script")
    parser.add_argument(
        "backup_dir",
        help="Backup directory to restore from",
    )
    parser.add_argument(
        "--collections",
        help="Comma-separated list of collections to restore (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate rollback without making changes",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt",
    )

    args = parser.parse_args()

    collections = None
    if args.collections:
        collections = [c.strip() for c in args.collections.split(",")]

    rollback = MongoDBRollback(
        backup_path=Path(args.backup_dir),
        host=settings.mongodb_host,
        port=settings.mongodb_port,
        username=settings.mongodb_username,
        password=settings.mongodb_password,
        database=settings.mongodb_database,
    )

    logger.info("=" * 60)
    logger.info("MongoDB Rollback Script")
    logger.info("=" * 60)

    results = rollback.rollback(
        collections=collections,
        dry_run=args.dry_run,
        force=args.force,
    )

    print("\n" + "=" * 60)
    print("ROLLBACK RESULTS")
    print("=" * 60)

    if results["status"] == "cancelled":
        print(results["message"])
        return

    if results.get("dry_run"):
        print("*** DRY RUN - No changes were made ***\n")

    print(f"Status: {results['status']}")

    for collection, info in results.get("collections", {}).items():
        status = info.get("status", "unknown")
        docs = info.get("documents_restored", 0)
        print(f"  {collection}: {status} ({docs} documents)")

        if info.get("error"):
            print(f"    Error: {info['error']}")

    print("=" * 60)

    if results["status"] in ["error", "partial_error"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
