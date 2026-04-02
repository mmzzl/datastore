"""Plugin Loader

Loads and instantiates strategy plugins dynamically.
"""

import importlib
import importlib.util
import logging
import os
import sys
from typing import Any, Dict, Optional, Type

from app.backtest.strategies.base import BaseStrategy

logger = logging.getLogger(__name__)


def load_plugin_module(
    module_path: str,
    module_name: str,
) -> Optional[Any]:
    """Load a plugin module dynamically.

    Args:
        module_path: Path to the plugin module directory
        module_name: Name of the module to load

    Returns:
        Loaded module or None on failure

    Raises:
        ImportError: If module cannot be loaded
        ValueError: If path is invalid
    """
    if not os.path.isdir(module_path):
        raise ValueError(f"Module path does not exist: {module_path}")

    strategy_file = os.path.join(module_path, "strategy.py")
    if not os.path.isfile(strategy_file):
        raise ValueError(f"Strategy file not found: {strategy_file}")

    init_file = os.path.join(module_path, "__init__.py")
    if not os.path.isfile(init_file):
        logger.warning(f"No __init__.py in {module_path}, creating one")
        with open(init_file, "w") as f:
            f.write(f'"""Plugin module: {module_name}"""\n')

    full_module_name = f"app.backtest.strategies.plugins.{module_name}"

    try:
        if full_module_name in sys.modules:
            del sys.modules[full_module_name]

        spec = importlib.util.spec_from_file_location(
            full_module_name,
            strategy_file,
            submodule_search_locations=[module_path],
        )

        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot create spec for module: {module_name}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[full_module_name] = module

        spec.loader.exec_module(module)

        logger.info(f"Successfully loaded plugin module: {module_name}")
        return module

    except Exception as e:
        if full_module_name in sys.modules:
            del sys.modules[full_module_name]
        logger.error(f"Failed to load plugin module {module_name}: {e}")
        raise ImportError(f"Failed to load plugin module {module_name}: {str(e)}")


def create_strategy_instance(
    module: Any,
    strategy_class_name: str,
    **params: Any,
) -> BaseStrategy:
    """Create a strategy instance from a loaded module.

    Args:
        module: Loaded plugin module
        strategy_class_name: Name of the strategy class
        **params: Parameters to pass to strategy constructor

    Returns:
        Instantiated strategy object

    Raises:
        AttributeError: If strategy class not found
        TypeError: If class doesn't inherit from BaseStrategy
    """
    if not hasattr(module, strategy_class_name):
        raise AttributeError(f"Strategy class '{strategy_class_name}' not found in module")

    strategy_class = getattr(module, strategy_class_name)

    if not issubclass(strategy_class, BaseStrategy):
        raise TypeError(
            f"Strategy class '{strategy_class_name}' does not inherit from BaseStrategy"
        )

    try:
        instance = strategy_class(**params)
        logger.info(
            f"Created strategy instance: {strategy_class_name} with params: {params}"
        )
        return instance
    except Exception as e:
        logger.error(f"Failed to instantiate strategy {strategy_class_name}: {e}")
        raise


class PluginLoader:
    """Plugin loader that manages module loading and strategy instantiation."""

    def __init__(self, plugins_base_path: str = None):
        """Initialize plugin loader.

        Args:
            plugins_base_path: Base path for plugins directory.
                               Defaults to app/backtest/strategies/plugins
        """
        if plugins_base_path is None:
            current_dir = os.path.dirname(__file__)
            self.plugins_base_path = os.path.normpath(
                os.path.join(current_dir, "..", "strategies", "plugins")
            )
        else:
            self.plugins_base_path = plugins_base_path

        self._loaded_modules: Dict[str, Any] = {}

    def load(self, plugin_name: str, plugin_path: str = None) -> Any:
        """Load a plugin by name.

        Args:
            plugin_name: Name of the plugin
            plugin_path: Optional custom path to plugin directory

        Returns:
            Loaded module

        Raises:
            ValueError: If plugin not found
            ImportError: If plugin cannot be loaded
        """
        if plugin_path is None:
            plugin_path = os.path.join(self.plugins_base_path, plugin_name)

        cache_key = plugin_name
        if cache_key in self._loaded_modules:
            logger.debug(f"Returning cached module for {plugin_name}")
            return self._loaded_modules[cache_key]

        module = load_plugin_module(plugin_path, plugin_name)
        self._loaded_modules[cache_key] = module
        return module

    def create_strategy(
        self,
        plugin_name: str,
        strategy_class: str,
        **params: Any,
    ) -> BaseStrategy:
        """Load and instantiate a strategy from a plugin.

        Args:
            plugin_name: Name of the plugin
            strategy_class: Name of the strategy class
            **params: Parameters for strategy constructor

        Returns:
            Instantiated strategy
        """
        module = self.load(plugin_name)
        return create_strategy_instance(module, strategy_class, **params)

    def unload(self, plugin_name: str) -> bool:
        """Unload a plugin module.

        Args:
            plugin_name: Name of the plugin to unload

        Returns:
            True if module was unloaded, False if not loaded
        """
        cache_key = plugin_name
        if cache_key in self._loaded_modules:
            del self._loaded_modules[cache_key]

            full_module_name = f"app.backtest.strategies.plugins.{plugin_name}"
            if full_module_name in sys.modules:
                del sys.modules[full_module_name]

            logger.info(f"Unloaded plugin: {plugin_name}")
            return True

        return False

    def is_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is loaded.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if loaded, False otherwise
        """
        return plugin_name in self._loaded_modules

    def get_loaded_plugins(self) -> Dict[str, Any]:
        """Get all loaded plugins.

        Returns:
            Dictionary of plugin name to module
        """
        return self._loaded_modules.copy()

    def reload(self, plugin_name: str, plugin_path: str = None) -> Any:
        """Reload a plugin module.

        Args:
            plugin_name: Name of the plugin
            plugin_path: Optional custom path to plugin

        Returns:
            Reloaded module
        """
        self.unload(plugin_name)
        return self.load(plugin_name, plugin_path)
