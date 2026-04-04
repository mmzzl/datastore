"""Tests for plugin loader"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch

from app.backtest.plugin.loader import (
    load_plugin_module,
    create_strategy_instance,
    PluginLoader,
)
from app.backtest.strategies.base import BaseStrategy


class TestLoadPluginModule:
    def test_load_valid_module(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            strategy_file = os.path.join(tmpdir, "strategy.py")
            with open(strategy_file, "w") as f:
                f.write("""
class TestStrategy:
    def generate_signals(self, data):
        return data
""")

            init_file = os.path.join(tmpdir, "__init__.py")
            with open(init_file, "w") as f:
                f.write('"""Test plugin"""\n')

            module = load_plugin_module(tmpdir, "test_plugin")

            assert module is not None
            assert hasattr(module, "TestStrategy")

    def test_missing_strategy_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with pytest.raises(ValueError) as exc_info:
                load_plugin_module(tmpdir, "test_plugin")

            assert "Strategy file not found" in str(exc_info.value)

    def test_invalid_path(self):
        with pytest.raises(ValueError) as exc_info:
            load_plugin_module("/nonexistent/path", "test_plugin")

        assert "does not exist" in str(exc_info.value)

    def test_creates_init_if_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            strategy_file = os.path.join(tmpdir, "strategy.py")
            with open(strategy_file, "w") as f:
                f.write("class TestStrategy: pass")

            module = load_plugin_module(tmpdir, "test_plugin")

            init_file = os.path.join(tmpdir, "__init__.py")
            assert os.path.exists(init_file)


class TestCreateStrategyInstance:
    def test_create_instance_success(self):
        class MockStrategy(BaseStrategy):
            def __init__(self, param1=10):
                self.param1 = param1

            def generate_signals(self, data):
                return data

            def get_name(self):
                return "MockStrategy"

            def get_params(self):
                return {"param1": self.param1}

        mock_module = MagicMock()
        mock_module.MockStrategy = MockStrategy

        instance = create_strategy_instance(mock_module, "MockStrategy", param1=20)

        assert isinstance(instance, BaseStrategy)
        assert instance.param1 == 20

    def test_class_not_found(self):
        mock_module = MagicMock()
        del mock_module.NonExistentStrategy

        with pytest.raises(AttributeError) as exc_info:
            create_strategy_instance(mock_module, "NonExistentStrategy")

        assert "not found" in str(exc_info.value)

    def test_not_base_strategy_subclass(self):
        class NotAStrategy:
            pass

        mock_module = MagicMock()
        mock_module.NotAStrategy = NotAStrategy

        with pytest.raises(TypeError) as exc_info:
            create_strategy_instance(mock_module, "NotAStrategy")

        assert "does not inherit from BaseStrategy" in str(exc_info.value)


class TestPluginLoader:
    def test_initialization(self):
        loader = PluginLoader("/custom/plugins/path")
        assert loader.plugins_base_path == "/custom/plugins/path"

    def test_default_plugins_path(self):
        loader = PluginLoader()
        assert "strategies" in loader.plugins_base_path.lower()

    def test_load_and_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            strategy_file = os.path.join(tmpdir, "strategy.py")
            with open(strategy_file, "w") as f:
                f.write("class TestStrategy: pass")

            init_file = os.path.join(tmpdir, "__init__.py")
            with open(init_file, "w") as f:
                f.write('"""Test"""\n')

            loader = PluginLoader()

            module1 = loader.load("test_plugin", tmpdir)
            assert loader.is_loaded("test_plugin")

            module2 = loader.load("test_plugin", tmpdir)
            assert module1 is module2

    def test_unload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            strategy_file = os.path.join(tmpdir, "strategy.py")
            with open(strategy_file, "w") as f:
                f.write("class TestStrategy: pass")

            init_file = os.path.join(tmpdir, "__init__.py")
            with open(init_file, "w") as f:
                f.write('"""Test"""\n')

            loader = PluginLoader()
            loader.load("test_plugin", tmpdir)

            result = loader.unload("test_plugin")

            assert result is True
            assert not loader.is_loaded("test_plugin")

    def test_unload_not_loaded(self):
        loader = PluginLoader()
        result = loader.unload("nonexistent_plugin")
        assert result is False

    def test_get_loaded_plugins(self):
        loader = PluginLoader()
        loaded = loader.get_loaded_plugins()
        assert isinstance(loaded, dict)

    def test_reload(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            strategy_file = os.path.join(tmpdir, "strategy.py")
            with open(strategy_file, "w") as f:
                f.write("class TestStrategy: pass")

            init_file = os.path.join(tmpdir, "__init__.py")
            with open(init_file, "w") as f:
                f.write('"""Test"""\n')

            loader = PluginLoader()
            loader.load("test_plugin", tmpdir)

            module = loader.reload("test_plugin", tmpdir)

            assert module is not None
            assert loader.is_loaded("test_plugin")


class TestPluginLoaderIntegration:
    def test_full_workflow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            strategy_content = '''
from app.backtest.strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    def __init__(self, param=10):
        self.param = param

    def generate_signals(self, data):
        return data

    def get_name(self):
        return "MyStrategy"

    def get_params(self):
        return {"param": self.param}
'''
            strategy_file = os.path.join(tmpdir, "strategy.py")
            with open(strategy_file, "w") as f:
                f.write(strategy_content)

            init_file = os.path.join(tmpdir, "__init__.py")
            with open(init_file, "w") as f:
                f.write('"""My Strategy Plugin"""\n')

            loader = PluginLoader()

            module = loader.load("my_strategy", tmpdir)
            assert module is not None

            strategy = loader.create_strategy("my_strategy", "MyStrategy", param=25)
            assert isinstance(strategy, BaseStrategy)
            assert strategy.param == 25
