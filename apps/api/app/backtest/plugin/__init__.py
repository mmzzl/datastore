"""Plugin System for Strategy Upload and Management.

This module provides a comprehensive plugin system for uploading,
validating, loading, and managing trading strategy plugins.
"""

from .validator import (
    PluginValidator,
    ValidationResult,
    validate_zip_structure,
    validate_manifest_schema,
    validate_code_ast,
    validate_strategy_class,
    check_version_rules,
)
from .loader import PluginLoader, load_plugin_module, create_strategy_instance
from .registry import PluginRegistry

__all__ = [
    "PluginValidator",
    "ValidationResult",
    "validate_zip_structure",
    "validate_manifest_schema",
    "validate_code_ast",
    "validate_strategy_class",
    "check_version_rules",
    "PluginLoader",
    "load_plugin_module",
    "create_strategy_instance",
    "PluginRegistry",
]
