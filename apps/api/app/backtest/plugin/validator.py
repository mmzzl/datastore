"""Plugin Validator

Validates uploaded plugin packages for security and correctness.
"""

import ast
import json
import logging
import os
import zipfile
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

FORBIDDEN_IMPORTS: Set[str] = {
    "os",
    "subprocess",
    "sys",
    "socket",
    "requests",
    "importlib",
    "eval",
    "exec",
    "compile",
    "__import__",
    "pickle",
    "marshal",
    "ctypes",
}

MAX_FILE_COUNT = 100
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {".py", ".json", ".txt", ".md"}


@dataclass
class ValidationResult:
    """Result of plugin validation."""

    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    manifest: Optional[Dict[str, Any]] = None
    strategy_files: List[str] = field(default_factory=list)

    def add_error(self, error: str) -> None:
        self.errors.append(error)
        self.valid = False

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)


def validate_zip_structure(zip_path: str) -> ValidationResult:
    """Validate ZIP file structure.

    Checks:
    - File count limit
    - File size limit
    - Allowed extensions

    Args:
        zip_path: Path to ZIP file

    Returns:
        ValidationResult with validation outcome
    """
    result = ValidationResult(valid=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            file_list = zf.namelist()

            if len(file_list) > MAX_FILE_COUNT:
                result.add_error(f"Too many files: {len(file_list)} > {MAX_FILE_COUNT}")

            has_manifest = False
            has_strategy = False

            for info in zf.infolist():
                if info.file_size > MAX_FILE_SIZE:
                    result.add_error(f"File too large: {info.filename} ({info.file_size} bytes)")

                ext = os.path.splitext(info.filename)[1].lower()
                if ext and ext not in ALLOWED_EXTENSIONS:
                    result.add_warning(f"Unusual file extension: {info.filename}")

                if info.filename.endswith("manifest.json"):
                    has_manifest = True
                if info.filename.endswith("strategy.py"):
                    has_strategy = True
                    result.strategy_files.append(info.filename)

            if not has_manifest:
                result.add_error("Missing required manifest.json file")
            if not has_strategy:
                result.add_error("Missing required strategy.py file")

    except zipfile.BadZipFile as e:
        result.add_error(f"Invalid ZIP file: {str(e)}")
    except Exception as e:
        result.add_error(f"Failed to read ZIP file: {str(e)}")

    logger.info(f"ZIP structure validation: valid={result.valid}, errors={len(result.errors)}")
    return result


def validate_manifest_schema(manifest: Dict[str, Any]) -> ValidationResult:
    """Validate manifest.json schema.

    Required fields:
    - name: Plugin name (alphanumeric + underscore)
    - version: Semantic version (x.y.z)
    - display_name: Display name
    - description: Description
    - author: Author name
    - strategy_class: Strategy class name
    - min_data_points: Minimum data points required

    Optional fields:
    - tags: List of tags
    - parameters: Parameter definitions

    Args:
        manifest: Parsed manifest dictionary

    Returns:
        ValidationResult with validation outcome
    """
    result = ValidationResult(valid=True)

    required_fields = {
        "name": str,
        "version": str,
        "display_name": str,
        "description": str,
        "author": str,
        "strategy_class": str,
    }

    for field_name, field_type in required_fields.items():
        if field_name not in manifest:
            result.add_error(f"Missing required field: {field_name}")
        elif not isinstance(manifest[field_name], field_type):
            result.add_error(f"Invalid type for {field_name}: expected {field_type.__name__}")

    if "name" in manifest:
        name = manifest["name"]
        if not name.replace("_", "").replace("-", "").isalnum():
            result.add_error(f"Invalid plugin name: {name} (must be alphanumeric)")

    if "version" in manifest:
        version = manifest["version"]
        parts = version.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            result.add_error(f"Invalid version format: {version} (expected x.y.z)")

    if "min_data_points" in manifest:
        min_points = manifest["min_data_points"]
        if not isinstance(min_points, int) or min_points < 1:
            result.add_error("min_data_points must be a positive integer")

    if "tags" in manifest:
        tags = manifest["tags"]
        if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
            result.add_error("tags must be a list of strings")

    if "parameters" in manifest:
        params = manifest["parameters"]
        if not isinstance(params, dict):
            result.add_error("parameters must be a dictionary")
        else:
            for param_name, param_def in params.items():
                if not isinstance(param_def, dict):
                    result.add_error(f"Invalid parameter definition for: {param_name}")
                    continue

                if "type" not in param_def:
                    result.add_error(f"Missing type for parameter: {param_name}")

                if "default" not in param_def:
                    result.add_warning(f"Missing default for parameter: {param_name}")

                valid_types = {"integer", "float", "string", "boolean", "enum"}
                if param_def.get("type") not in valid_types:
                    result.add_error(
                        f"Invalid parameter type for {param_name}: {param_def.get('type')}"
                    )

    result.manifest = manifest
    logger.info(f"Manifest schema validation: valid={result.valid}, errors={len(result.errors)}")
    return result


def validate_code_ast(code: str, filename: str = "strategy.py") -> ValidationResult:
    """Validate code using AST for forbidden imports.

    Checks for:
    - Forbidden imports (os, subprocess, sys, socket, etc.)
    - Forbidden function calls (eval, exec, compile, etc.)
    - Dynamic imports and code execution

    Args:
        code: Python source code
        filename: Filename for error reporting

    Returns:
        ValidationResult with validation outcome
    """
    result = ValidationResult(valid=True)

    try:
        tree = ast.parse(code, filename=filename)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]
                    if module_name in FORBIDDEN_IMPORTS:
                        result.add_error(f"Forbidden import: {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split(".")[0]
                    if module_name in FORBIDDEN_IMPORTS:
                        result.add_error(f"Forbidden import from: {node.module}")

            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in FORBIDDEN_IMPORTS:
                        result.add_error(f"Forbidden function call: {func_name}")

                elif isinstance(node.func, ast.Attribute):
                    attr_name = node.func.attr
                    if attr_name in {"system", "popen", "spawn", "call", "run"}:
                        result.add_warning(f"Potentially dangerous method call: {attr_name}")

            elif isinstance(node, ast.Attribute):
                if node.attr == "__import__":
                    result.add_error("Forbidden use of __import__")

    except SyntaxError as e:
        result.add_error(f"Syntax error in {filename}: {str(e)}")
    except Exception as e:
        result.add_error(f"Failed to parse {filename}: {str(e)}")

    logger.info(f"AST validation for {filename}: valid={result.valid}, errors={len(result.errors)}")
    return result


def validate_strategy_class(
    code: str,
    expected_class: str,
    base_strategy_module: str = "app.backtest.strategies.base",
) -> ValidationResult:
    """Validate that strategy class inherits from BaseStrategy.

    Args:
        code: Python source code
        expected_class: Expected strategy class name
        base_strategy_module: Module path for BaseStrategy

    Returns:
        ValidationResult with validation outcome
    """
    result = ValidationResult(valid=True)

    try:
        tree = ast.parse(code)

        class_found = False
        inherits_from_base = False

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if node.name == expected_class:
                    class_found = True

                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "BaseStrategy":
                        inherits_from_base = True
                        elif isinstance(base, ast.Attribute):
                            if base.attr == "BaseStrategy":
                                inherits_from_base = True

                    required_methods = {"generate_signals", "get_name", "get_params"}
                    method_names = set()
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            method_names.add(item.name)

                    missing_methods = required_methods - method_names
                    if missing_methods:
                        result.add_error(
                            f"Strategy class missing required methods: {missing_methods}"
                        )

        if not class_found:
            result.add_error(f"Strategy class '{expected_class}' not found in code")

    except SyntaxError as e:
        result.add_error(f"Syntax error: {str(e)}")
    except Exception as e:
        result.add_error(f"Failed to validate strategy class: {str(e)}")

    logger.info(
        f"Strategy class validation: valid={result.valid}, class_found={class_found}"
    )
    return result


def check_version_rules(
    new_version: str,
    existing_versions: List[str],
) -> Tuple[bool, str]:
    """Check version comparison rules.

    Rules:
    - New plugin: accept any version
    - Same version: reject (409 Conflict)
    - Lower version: reject (409 Conflict)

    Args:
        new_version: Version being uploaded (x.y.z)
        existing_versions: List of existing version strings

    Returns:
        Tuple of (valid, message)
    """

    def parse_version(v: str) -> Tuple[int, int, int]:
        parts = v.split(".")
        return (int(parts[0]), int(parts[1]), int(parts[2]))

    if not existing_versions:
        return True, "New plugin accepted"

    new_ver = parse_version(new_version)

    for existing in existing_versions:
        existing_ver = parse_version(existing)

        if new_version == existing:
            return False, f"Version {new_version} already exists"

        if new_ver < existing_ver:
            return False, f"Version {new_version} is lower than existing {existing}"

    return True, f"Version {new_version} accepted"


class PluginValidator:
    """Comprehensive plugin validator combining all validation checks."""

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir

    def validate_zip(self, zip_path: str) -> ValidationResult:
        """Validate ZIP file structure."""
        return validate_zip_structure(zip_path)

    def validate_manifest(self, manifest: Dict[str, Any]) -> ValidationResult:
        """Validate manifest schema."""
        return validate_manifest_schema(manifest)

    def validate_code(self, code: str, filename: str = "strategy.py") -> ValidationResult:
        """Validate code using AST."""
        return validate_code_ast(code, filename)

    def validate_strategy(
        self, code: str, strategy_class: str
    ) -> ValidationResult:
        """Validate strategy class inheritance."""
        return validate_strategy_class(code, strategy_class)

    def validate_version(
        self, name: str, version: str, existing_versions: List[str]
    ) -> Tuple[bool, str]:
        """Validate version rules."""
        return check_version_rules(version, existing_versions)

    def validate_all(
        self,
        zip_path: str,
        manifest: Dict[str, Any],
        strategy_code: str,
        existing_versions: List[str],
    ) -> ValidationResult:
        """Run all validations and combine results.

        Args:
            zip_path: Path to ZIP file
            manifest: Parsed manifest
            strategy_code: Strategy source code
            existing_versions: Existing plugin versions

        Returns:
            Combined ValidationResult
        """
        combined = ValidationResult(valid=True)

        zip_result = self.validate_zip(zip_path)
        for error in zip_result.errors:
            combined.add_error(error)
        for warning in zip_result.warnings:
            combined.add_warning(warning)

        manifest_result = self.validate_manifest(manifest)
        for error in manifest_result.errors:
            combined.add_error(error)
        for warning in manifest_result.warnings:
            combined.add_warning(warning)

        if manifest_result.manifest:
            combined.manifest = manifest_result.manifest

        code_result = self.validate_code(strategy_code)
        for error in code_result.errors:
            combined.add_error(error)
        for warning in code_result.warnings:
            combined.add_warning(warning)

        strategy_class = manifest.get("strategy_class", "")
        if strategy_class:
            strategy_result = self.validate_strategy(strategy_code, strategy_class)
            for error in strategy_result.errors:
                combined.add_error(error)
            for warning in strategy_result.warnings:
                combined.add_warning(warning)

        version = manifest.get("version", "")
        if version:
            version_valid, version_msg = self.validate_version(
                manifest.get("name", ""), version, existing_versions
            )
            if not version_valid:
                combined.add_error(version_msg)

        logger.info(
            f"Full validation: valid={combined.valid}, "
            f"errors={len(combined.errors)}, warnings={len(combined.warnings)}"
        )
        return combined
