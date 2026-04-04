"""Tests for plugin registry"""

import pytest
from unittest.mock import MagicMock
from bson import ObjectId

from app.backtest.plugin.registry import PluginRegistry


class TestPluginRegistry:
    @pytest.fixture
    def mock_collections(self):
        """Create mock collections that will be reused."""
        plugins_collection = MagicMock()
        versions_collection = MagicMock()
        return plugins_collection, versions_collection

    @pytest.fixture
    def mock_storage(self, mock_collections):
        plugins_collection, versions_collection = mock_collections
        storage = MagicMock()

        # Create mock database
        mock_db = MagicMock()
        mock_db.list_collection_names.return_value = ["strategy_plugins", "plugin_versions"]
        mock_db.create_collection = MagicMock()

        # Make db["strategy_plugins"] return plugins_collection
        # and db["plugin_versions"] return versions_collection
        def getitem(_self, key):
            if key == "strategy_plugins":
                return plugins_collection
            elif key == "plugin_versions":
                return versions_collection
            return MagicMock()

        type(mock_db).__getitem__ = getitem
        storage.db = mock_db
        return storage

    @pytest.fixture
    def registry(self, mock_storage, mock_collections):
        """Create registry with mocked storage."""
        return PluginRegistry(mock_storage)

    def test_register_new_plugin(self, registry, mock_collections):
        plugins_collection, versions_collection = mock_collections
        plugins_collection.find_one.return_value = None
        plugins_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())
        versions_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        plugin_id = registry.register(
            name="test_plugin",
            version="1.0.0",
            path="/plugins/test_plugin",
            manifest={"name": "test_plugin", "version": "1.0.0"},
        )

        assert plugin_id is not None
        plugins_collection.insert_one.assert_called_once()

    def test_register_duplicate_version(self, registry, mock_collections):
        existing_id = ObjectId()
        plugins_collection, versions_collection = mock_collections
        plugins_collection.find_one.return_value = {"_id": existing_id, "name": "test_plugin"}
        versions_collection.find.return_value = [{"version": "1.0.0"}]

        with pytest.raises(ValueError) as exc_info:
            registry.register(
                name="test_plugin",
                version="1.0.0",
                path="/plugins/test_plugin",
                manifest={"name": "test_plugin"},
            )

        assert "already exists" in str(exc_info.value)

    def test_unregister(self, registry, mock_collections):
        plugins_collection, versions_collection = mock_collections
        plugin_id = str(ObjectId())
        plugins_collection.delete_one.return_value = MagicMock(deleted_count=1)

        result = registry.unregister(plugin_id)

        assert result is True
        plugins_collection.delete_one.assert_called_once()
        versions_collection.delete_many.assert_called_once()

    def test_unregister_not_found(self, registry, mock_collections):
        plugins_collection, _ = mock_collections
        plugin_id = str(ObjectId())
        plugins_collection.delete_one.return_value = MagicMock(deleted_count=0)

        result = registry.unregister(plugin_id)

        assert result is False

    def test_get_plugin(self, registry, mock_collections):
        plugins_collection, _ = mock_collections
        plugin_id = str(ObjectId())
        plugins_collection.find_one.return_value = {
            "_id": ObjectId(plugin_id),
            "name": "test_plugin",
            "version": "1.0.0",
        }

        plugin = registry.get(plugin_id)

        assert plugin is not None
        assert plugin["name"] == "test_plugin"

    def test_get_plugin_not_found(self, registry, mock_collections):
        plugins_collection, _ = mock_collections
        plugin_id = str(ObjectId())
        plugins_collection.find_one.return_value = None

        plugin = registry.get(plugin_id)

        assert plugin is None

    def test_get_by_name(self, registry, mock_collections):
        plugins_collection, _ = mock_collections
        plugins_collection.find_one.return_value = {
            "_id": ObjectId(),
            "name": "test_plugin",
            "version": "1.0.0",
        }

        plugin = registry.get_by_name("test_plugin")

        assert plugin is not None
        assert plugin["name"] == "test_plugin"

    def test_list_plugins(self, registry, mock_collections):
        plugins_collection, _ = mock_collections
        plugins_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = [
            {"_id": ObjectId(), "name": "plugin1", "version": "1.0.0"},
            {"_id": ObjectId(), "name": "plugin2", "version": "2.0.0"},
        ]

        plugins = registry.list()

        assert len(plugins) == 2

    def test_list_plugins_with_status_filter(self, registry, mock_collections):
        plugins_collection, _ = mock_collections
        plugins_collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = [
            {"_id": ObjectId(), "name": "plugin1", "status": "active"},
        ]

        plugins = registry.list(status="active")

        assert len(plugins) == 1
        assert plugins[0]["status"] == "active"

    def test_count_plugins(self, registry, mock_collections):
        plugins_collection, _ = mock_collections
        plugins_collection.count_documents.return_value = 5

        count = registry.count()

        assert count == 5

    def test_count_plugins_with_filter(self, registry, mock_collections):
        plugins_collection, _ = mock_collections
        plugins_collection.count_documents.return_value = 3

        count = registry.count(status="active")

        assert count == 3
        plugins_collection.count_documents.assert_called_with({"status": "active"})

    def test_activate(self, registry, mock_collections):
        plugins_collection, versions_collection = mock_collections
        plugin_id = str(ObjectId())
        plugins_collection.find_one.return_value = {
            "_id": ObjectId(plugin_id),
            "name": "test_plugin",
            "version": "1.0.0",
        }
        plugins_collection.update_one.return_value = MagicMock(modified_count=1)

        result = registry.activate(plugin_id)

        assert result is True
        versions_collection.update_many.assert_called()
        versions_collection.update_one.assert_called()

    def test_activate_not_found(self, registry, mock_collections):
        plugins_collection, _ = mock_collections
        plugin_id = str(ObjectId())
        plugins_collection.find_one.return_value = None

        result = registry.activate(plugin_id)

        assert result is False

    def test_deactivate(self, registry, mock_collections):
        plugins_collection, versions_collection = mock_collections
        plugin_id = str(ObjectId())
        plugins_collection.update_one.return_value = MagicMock(modified_count=1)

        result = registry.deactivate(plugin_id)

        assert result is True
        plugins_collection.update_one.assert_called()
        versions_collection.update_many.assert_called()

    def test_update(self, registry, mock_collections):
        plugins_collection, _ = mock_collections
        plugin_id = str(ObjectId())
        plugins_collection.update_one.return_value = MagicMock(modified_count=1)

        result = registry.update(plugin_id, {"description": "Updated description"})

        assert result is True

    def test_add_version(self, registry, mock_collections):
        plugins_collection, versions_collection = mock_collections
        plugin_id = str(ObjectId())
        versions_collection.find_one.return_value = None
        versions_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId())

        version_id = registry.add_version(plugin_id, "1.1.0", "/plugins/test/1.1.0")

        assert version_id is not None
        versions_collection.insert_one.assert_called()
        plugins_collection.update_one.assert_called()

    def test_add_version_duplicate(self, registry, mock_collections):
        _, versions_collection = mock_collections
        plugin_id = str(ObjectId())
        versions_collection.find_one.return_value = {
            "version": "1.0.0",
            "plugin_id": ObjectId(plugin_id),
        }

        with pytest.raises(ValueError) as exc_info:
            registry.add_version(plugin_id, "1.0.0", "/plugins/test/1.0.0")

        assert "already exists" in str(exc_info.value)

    def test_get_versions(self, registry, mock_collections):
        _, versions_collection = mock_collections
        plugin_id = str(ObjectId())
        versions_collection.find.return_value.sort.return_value = [
            {"_id": ObjectId(), "version": "1.0.0", "plugin_id": ObjectId(plugin_id)},
            {"_id": ObjectId(), "version": "1.1.0", "plugin_id": ObjectId(plugin_id)},
        ]

        versions = registry.get_versions(plugin_id)

        assert len(versions) == 2
        for v in versions:
            assert "plugin_id" in v
            assert isinstance(v["plugin_id"], str)

    def test_get_active_version(self, registry, mock_collections):
        _, versions_collection = mock_collections
        plugin_id = str(ObjectId())
        versions_collection.find_one.return_value = {
            "_id": ObjectId(),
            "version": "1.0.0",
            "plugin_id": ObjectId(plugin_id),
            "is_active": True,
        }

        version = registry.get_active_version(plugin_id)

        assert version is not None
        assert version["is_active"] is True

    def test_get_active_version_none(self, registry, mock_collections):
        _, versions_collection = mock_collections
        plugin_id = str(ObjectId())
        versions_collection.find_one.return_value = None

        version = registry.get_active_version(plugin_id)

        assert version is None

    def test_get_existing_versions(self, registry, mock_collections):
        _, versions_collection = mock_collections
        plugin_id = str(ObjectId())
        versions_collection.find.return_value = [
            {"version": "1.0.0"},
            {"version": "1.1.0"},
        ]

        versions = registry.get_existing_versions(plugin_id)

        assert versions == ["1.0.0", "1.1.0"]
