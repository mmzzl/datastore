"""
MongoDB Backup Script

Creates backups of MongoDB collections with retention policy.

Usage:
    py -3.12 scripts/backup_mongodb.py [--collections qlib_models,backtest_results]
                                       [--retention-days 30]
                                       [--backup-dir ./backups]
                                       [--verify]
"""

import argparse
import gzip
import hashlib
import json
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

sys.path.insert(0, str(Path(__file__).parent.parent))
from apps.api.app.core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


BACKUP_COLLECTIONS = [
    "qlib_models",
    "backtest_results",
    "risk_reports",
    "scheduler_jobs",
    "job_executions",
    "dingtalk_configs",
    "holdings",
    "settings",
]

DEFAULT_RETENTION_DAYS = 30
DEFAULT_BACKUP_DIR = Path("./backups")


class MongoDBBackup:
    """MongoDB backup manager with retention policy."""

    def __init__(
        self,
        backup_dir: Path,
        retention_days: int = DEFAULT_RETENTION_DAYS,
        host: str = "localhost",
        port: int = 27017,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: str = "news_db",
    ):
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    def get_backup_path(self) -> Path:
        """Get backup directory path for current run."""
        return self.backup_dir / f"backup_{self.timestamp}"

    def get_mongo_uri(self) -> str:
        """Get MongoDB connection URI."""
        if self.username and self.password:
            from urllib.parse import quote_plus
            encoded_password = quote_plus(self.password)
            return f"mongodb://{self.username}:{encoded_password}@{self.host}:{self.port}/{self.database}"
        return f"mongodb://{self.host}:{self.port}/{self.database}"

    def create_backup(self, collections: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create backup of specified collections.

        Args:
            collections: List of collection names to backup (None = all)

        Returns:
            Dictionary with backup results
        """
        collections = collections or BACKUP_COLLECTIONS
        backup_path = self.get_backup_path()
        backup_path.mkdir(parents=True, exist_ok=True)

        results = {
            "backup_path": str(backup_path),
            "timestamp": self.timestamp,
            "collections": {},
            "total_size": 0,
            "errors": [],
        }

        logger.info(f"Starting backup to: {backup_path}")

        for collection in collections:
            try:
                logger.info(f"Backing up collection: {collection}")
                collection_path = backup_path / f"{collection}.json.gz"

                success = self._dump_collection(collection, collection_path)

                if success:
                    size = collection_path.stat().st_size
                    results["collections"][collection] = {
                        "status": "success",
                        "file": str(collection_path),
                        "size": size,
                    }
                    results["total_size"] += size
                    logger.info(f"  Backed up: {collection} ({size} bytes)")
                else:
                    results["collections"][collection] = {"status": "skipped"}
                    logger.warning(f"  Skipped: {collection}")

            except Exception as e:
                logger.error(f"  Error backing up {collection}: {e}")
                results["collections"][collection] = {
                    "status": "error",
                    "error": str(e),
                }
                results["errors"].append(f"{collection}: {str(e)}")

        manifest = self._create_manifest(results)
        manifest_path = backup_path / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        logger.info(f"Backup completed: {backup_path}")
        logger.info(f"Total size: {results['total_size']} bytes")

        return results

    def _dump_collection(self, collection: str, output_path: Path) -> bool:
        """
        Dump a single collection to compressed JSON.

        Args:
            collection: Collection name
            output_path: Output file path

        Returns:
            True if successful
        """
        try:
            from pymongo import MongoClient
            from urllib.parse import quote_plus

            if self.username and self.password:
                encoded_password = quote_plus(self.password)
                uri = f"mongodb://{self.username}:{encoded_password}@{self.host}:{self.port}"
            else:
                uri = f"mongodb://{self.host}:{self.port}"

            client = MongoClient(uri)
            db = client[self.database]

            if collection not in db.list_collection_names():
                logger.warning(f"Collection {collection} does not exist")
                client.close()
                return False

            docs = list(db[collection].find())
            for doc in docs:
                doc["_id"] = str(doc["_id"])
                if "created_at" in doc and hasattr(doc["created_at"], "isoformat"):
                    doc["created_at"] = doc["created_at"].isoformat()

            client.close()

            with gzip.open(output_path, "wt", encoding="utf-8") as f:
                json.dump(docs, f, ensure_ascii=False)

            return True

        except Exception as e:
            logger.error(f"Failed to dump {collection}: {e}")
            return False

    def _create_manifest(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create backup manifest."""
        return {
            "version": "1.0",
            "timestamp": self.timestamp,
            "database": self.database,
            "host": self.host,
            "port": self.port,
            "collections": results["collections"],
            "total_size": results["total_size"],
            "created_at": datetime.now().isoformat(),
        }

    def cleanup_old_backups(self) -> List[str]:
        """
        Remove backups older than retention period.

        Returns:
            List of removed backup paths
        """
        cutoff = datetime.now() - timedelta(days=self.retention_days)
        removed = []

        if not self.backup_dir.exists():
            return removed

        for backup_folder in self.backup_dir.iterdir():
            if not backup_folder.is_dir():
                continue

            if not backup_folder.name.startswith("backup_"):
                continue

            try:
                folder_date_str = backup_folder.name.replace("backup_", "")[:15]
                folder_date = datetime.strptime(folder_date_str, "%Y%m%d_%H%M%S")

                if folder_date < cutoff:
                    shutil.rmtree(backup_folder)
                    removed.append(str(backup_folder))
                    logger.info(f"Removed old backup: {backup_folder}")

            except (ValueError, OSError) as e:
                logger.warning(f"Could not process backup folder {backup_folder}: {e}")

        return removed

    def verify_backup(self, backup_path: Path) -> Dict[str, Any]:
        """
        Verify backup integrity.

        Args:
            backup_path: Path to backup directory

        Returns:
            Verification results
        """
        results = {
            "valid": True,
            "manifest": None,
            "files": {},
            "errors": [],
        }

        manifest_path = backup_path / "manifest.json"
        if not manifest_path.exists():
            results["valid"] = False
            results["errors"].append("Manifest file not found")
            return results

        try:
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
            results["manifest"] = manifest

            for collection, info in manifest.get("collections", {}).items():
                if info.get("status") != "success":
                    continue

                file_path = Path(info["file"])
                if not file_path.exists():
                    results["valid"] = False
                    results["errors"].append(f"Missing file: {file_path}")
                    continue

                actual_size = file_path.stat().st_size
                expected_size = info.get("size", 0)

                if actual_size != expected_size:
                    results["valid"] = False
                    results["errors"].append(
                        f"Size mismatch for {collection}: expected {expected_size}, got {actual_size}"
                    )
                else:
                    results["files"][collection] = {
                        "size": actual_size,
                        "valid": True,
                    }

        except Exception as e:
            results["valid"] = False
            results["errors"].append(f"Verification error: {str(e)}")

        return results


def main():
    parser = argparse.ArgumentParser(description="MongoDB Backup Script")
    parser.add_argument(
        "--collections",
        help="Comma-separated list of collections to backup (default: all)",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=DEFAULT_RETENTION_DAYS,
        help=f"Backup retention in days (default: {DEFAULT_RETENTION_DAYS})",
    )
    parser.add_argument(
        "--backup-dir",
        default=str(DEFAULT_BACKUP_DIR),
        help=f"Backup directory (default: {DEFAULT_BACKUP_DIR})",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify backup after creation",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Cleanup old backups after creation",
    )

    args = parser.parse_args()

    collections = None
    if args.collections:
        collections = [c.strip() for c in args.collections.split(",")]

    backup = MongoDBBackup(
        backup_dir=Path(args.backup_dir),
        retention_days=args.retention_days,
        host=settings.mongodb_host,
        port=settings.mongodb_port,
        username=settings.mongodb_username,
        password=settings.mongodb_password,
        database=settings.mongodb_database,
    )

    logger.info("=" * 60)
    logger.info("MongoDB Backup Script")
    logger.info("=" * 60)
    logger.info(f"Host: {settings.mongodb_host}:{settings.mongodb_port}")
    logger.info(f"Database: {settings.mongodb_database}")
    logger.info(f"Backup directory: {args.backup_dir}")
    logger.info(f"Retention: {args.retention_days} days")

    results = backup.create_backup(collections)

    if args.verify:
        logger.info("\nVerifying backup...")
        backup_path = Path(results["backup_path"])
        verification = backup.verify_backup(backup_path)

        if verification["valid"]:
            logger.info("Backup verification: PASSED")
        else:
            logger.error("Backup verification: FAILED")
            for error in verification["errors"]:
                logger.error(f"  - {error}")
            sys.exit(1)

    if args.cleanup:
        logger.info("\nCleaning up old backups...")
        removed = backup.cleanup_old_backups()
        logger.info(f"Removed {len(removed)} old backup(s)")

    logger.info("\nBackup completed successfully")


if __name__ == "__main__":
    main()
