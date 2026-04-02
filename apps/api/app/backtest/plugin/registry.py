"""Plugin Registry

Manages plugin registration and lifecycle in MongoDB.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing strategy plugins.

    Handles registration, unregistration, listing, and activation
    of plugins stored in MongoDB.
    """

    COLLECTION_NAME = "strategy_plugins"
    VERSIONS_COLLECTION_NAME = "plugin_versions"

    def __init__(self, storage):
        """Initialize plugin registry.

        Args:
            storage: MongoStorage instance
        """
        self.storage = storage
        self._ensure_collections()

    def _ensure_collections(self) -> None:
        """Ensure required collections exist with proper indexes."""
        try:
            db = self.storage.db

            if self.COLLECTION_NAME not in db.list_collection_names():
                db.create_collection(self.COLLECTION_NAME)

            if self.VERSIONS_COLLECTION_NAME not in db.list_collection_names():
                db.create_collection(self.VERSIONS_COLLECTION_NAME)

            collection = db[self.COLLECTION_NAME]
            collection.create_index("name", unique=True)
            collection.create_index("status")
            collection.create_index("created_at")

            versions_collection = db[self.VERSIONS_COLLECTION_NAME]
            versions_collection.create_index([("plugin_id", 1), ("version", 1)])
            versions_collection.create_index("is_active")

            logger.info("Plugin collections and indexes ensured")

        except Exception as e:
            logger.error(f"Failed to ensure collections: {e}")

    def register(
        self,
        name: str,
        version: str,
        path: str,
        manifest: Dict[str, Any],
    ) -> str:
        """Register a new plugin.

        Args:
            name: Plugin name
            version: Plugin version
            path: Path to plugin directory
            manifest: Plugin manifest data

        Returns:
            Plugin ID

        Raises:
            ValueError: If plugin with same name and version exists
        """
        db = self.storage.db
        collection = db[self.COLLECTION_NAME]

        existing = collection.find_one({"name": name})
        if existing:
            existing_versions = self._get_existing_versions(existing["_id"])
            for v in existing_versions:
                if v == version:
                    raise ValueError(f"Plugin {name} version {version} already exists")

        now = datetime.now()

        plugin_doc = {
            "name": name,
            "version": version,
            "path": path,
            "manifest": manifest,
            "status": "inactive",
            "created_at": now,
            "updated_at": now,
        }

        result = collection.insert_one(plugin_doc)
        plugin_id = result.inserted_id

        version_doc = {
            "plugin_id": plugin_id,
            "version": version,
            "path": path,
            "is_active": False,
            "created_at": now,
        }
        db[self.VERSIONS_COLLECTION_NAME].insert_one(version_doc)

        logger.info(f"Registered plugin: {name} v{version} (ID: {plugin_id})")
        return str(plugin_id)

    def unregister(self, plugin_id: str) -> bool:
        """Unregister a plugin.

        Args:
            plugin_id: Plugin ID

        Returns:
            True if unregistered, False if not found
        """
        db = self.storage.db
        collection = db[self.COLLECTION_NAME]

        result = collection.delete_one({"_id": ObjectId(plugin_id)})

        if result.deleted_count > 0:
            db[self.VERSIONS_COLLECTION_NAME].delete_many(
                {"plugin_id": ObjectId(plugin_id)}
            )
            logger.info(f"Unregistered plugin: {plugin_id}")
            return True

        logger.warning(f"Plugin not found for unregistration: {plugin_id}")
        return False

    def get(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get a plugin by ID.

        Args:
            plugin_id: Plugin ID

        Returns:
            Plugin document or None
        """
        db = self.storage.db
        collection = db[self.COLLECTION_NAME]

        try:
            plugin = collection.find_one({"_id": ObjectId(plugin_id)})
            if plugin:
                plugin["_id"] = str(plugin["_id"])
            return plugin
        except Exception:
            return None

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin document or None
        """
        db = self.storage.db
        collection = db[self.COLLECTION_NAME]

        plugin = collection.find_one({"name": name}, sort=[("created_at", -1)])
        if plugin:
            plugin["_id"] = str(plugin["_id"])
        return plugin

    def list(
        self,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """List plugins with optional filtering.

        Args:
            status: Filter by status (active/inactive)
            skip: Number of documents to skip
            limit: Maximum number of documents

        Returns:
            List of plugin documents
        """
        db = self.storage.db
        collection = db[self.COLLECTION_NAME]

        query = {}
        if status:
            query["status"] = status

        cursor = collection.find(query).sort("created_at", -1).skip(skip).limit(limit)

        plugins = []
        for plugin in cursor:
            plugin["_id"] = str(plugin["_id"])
            plugins.append(plugin)

        return plugins

    def count(self, status: Optional[str] = None) -> int:
        """Count plugins.

        Args:
            status: Filter by status

        Returns:
            Number of plugins
        """
        db = self.storage.db
        collection = db[self.COLLECTION_NAME]

        query = {}
        if status:
            query["status"] = status

        return collection.count_documents(query)

    def activate(self, plugin_id: str) -> bool:
        """Activate a plugin.

        Args:
            plugin_id: Plugin ID

        Returns:
            True if activated, False if not found
        """
        db = self.storage.db
        collection = db[self.COLLECTION_NAME]
        versions_collection = db[self.VERSIONS_COLLECTION_NAME]

        plugin = collection.find_one({"_id": ObjectId(plugin_id)})
        if not plugin:
            return False

        versions_collection.update_many(
            {"plugin_id": ObjectId(plugin_id)},
            {"$set": {"is_active": False}},
        )

        versions_collection.update_one(
            {"plugin_id": ObjectId(plugin_id), "version": plugin["version"]},
            {"$set": {"is_active": True}},
        )

        collection.update_one(
            {"_id": ObjectId(plugin_id)},
            {"$set": {"status": "active", "updated_at": datetime.now()}},
        )

        logger.info(f"Activated plugin: {plugin_id}")
        return True

    def deactivate(self, plugin_id: str) -> bool:
        """Deactivate a plugin.

        Args:
            plugin_id: Plugin ID

        Returns:
            True if deactivated, False if not found
        """
        db = self.storage.db
        collection = db[self.COLLECTION_NAME]
        versions_collection = db[self.VERSIONS_COLLECTION_NAME]

        result = collection.update_one(
            {"_id": ObjectId(plugin_id)},
            {"$set": {"status": "inactive", "updated_at": datetime.now()}},
        )

        if result.modified_count > 0:
            versions_collection.update_many(
                {"plugin_id": ObjectId(plugin_id)},
                {"$set": {"is_active": False}},
            )
            logger.info(f"Deactivated plugin: {plugin_id}")
            return True

        return False

    def update(
        self,
        plugin_id: str,
        updates: Dict[str, Any],
    ) -> bool:
        """Update plugin metadata.

        Args:
            plugin_id: Plugin ID
            updates: Fields to update

        Returns:
            True if updated, False if not found
        """
        db = self.storage.db
        collection = db[self.COLLECTION_NAME]

        updates["updated_at"] = datetime.now()

        result = collection.update_one(
            {"_id": ObjectId(plugin_id)},
            {"$set": updates},
        )

        if result.modified_count > 0:
            logger.info(f"Updated plugin {plugin_id}")
            return True

        return False

    def add_version(
        self,
        plugin_id: str,
        version: str,
        path: str,
    ) -> str:
        """Add a new version to an existing plugin.

        Args:
            plugin_id: Plugin ID
            version: New version string
            path: Path to the version

        Returns:
            Version document ID

        Raises:
            ValueError: If version already exists
        """
        db = self.storage.db
        versions_collection = db[self.VERSIONS_COLLECTION_NAME]

        existing = versions_collection.find_one(
            {"plugin_id": ObjectId(plugin_id), "version": version}
        )
        if existing:
            raise ValueError(f"Version {version} already exists")

        now = datetime.now()
        version_doc = {
            "plugin_id": ObjectId(plugin_id),
            "version": version,
            "path": path,
            "is_active": False,
            "created_at": now,
        }

        result = versions_collection.insert_one(version_doc)

        db[self.COLLECTION_NAME].update_one(
            {"_id": ObjectId(plugin_id)},
            {
                "$set": {
                    "version": version,
                    "path": path,
                    "updated_at": now,
                }
            },
        )

        logger.info(f"Added version {version} to plugin {plugin_id}")
        return str(result.inserted_id)

    def get_versions(self, plugin_id: str) -> List[Dict[str, Any]]:
        """Get all versions of a plugin.

        Args:
            plugin_id: Plugin ID

        Returns:
            List of version documents
        """
        db = self.storage.db
        versions_collection = db[self.VERSIONS_COLLECTION_NAME]

        versions = []
        for v in versions_collection.find({"plugin_id": ObjectId(plugin_id)}).sort(
            "created_at", -1
        ):
            v["_id"] = str(v["_id"])
            v["plugin_id"] = str(v["plugin_id"])
            versions.append(v)

        return versions

    def get_active_version(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """Get the active version of a plugin.

        Args:
            plugin_id: Plugin ID

        Returns:
            Active version document or None
        """
        db = self.storage.db
        versions_collection = db[self.VERSIONS_COLLECTION_NAME]

        version = versions_collection.find_one(
            {"plugin_id": ObjectId(plugin_id), "is_active": True}
        )

        if version:
            version["_id"] = str(version["_id"])
            version["plugin_id"] = str(version["plugin_id"])

        return version

    def get_existing_versions(self, plugin_id: str) -> List[str]:
        """Get existing version strings for a plugin.

        Args:
            plugin_id: Plugin ID string

        Returns:
            List of version strings
        """
        db = self.storage.db
        versions_collection = db[self.VERSIONS_COLLECTION_NAME]

        versions = []
        for v in versions_collection.find({"plugin_id": ObjectId(plugin_id)}):
            versions.append(v["version"])

        return versions

    def _get_existing_versions(self, plugin_id: ObjectId) -> List[str]:
        """Get existing version strings for a plugin (internal).

        Args:
            plugin_id: Plugin ObjectId

        Returns:
            List of version strings
        """
        db = self.storage.db
        versions_collection = db[self.VERSIONS_COLLECTION_NAME]

        versions = []
        for v in versions_collection.find({"plugin_id": plugin_id}):
            versions.append(v["version"])

        return versions
