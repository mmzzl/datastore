"""Tests for plugin validator"""

import pytest
import tempfile
import zipfile
import json
from pathlib import Path

from app.backtest.plugin.validator import (
    ValidationResult,
    validate_zip_structure,
    validate_manifest_schema,
    validate_code_ast,
    validate_strategy_class,
    check_version_rules,
    PluginValidator,
    FORBIDDEN_IMPORTS,
)


class TestValidationResult:
    def test_valid_result_initialization(self):
        result = ValidationResult(valid=True)
        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_add_error_marks_invalid(self):
        result = ValidationResult(valid=True)
        result.add_error("Test error")
        assert result.valid is False
        assert "Test error" in result.errors

    def test_add_warning_keeps_valid(self):
        result = ValidationResult(valid=True)
        result.add_warning("Test warning")
        assert result.valid is True
        assert "Test warning" in result.warnings


class TestValidateZipStructure:
    def test_valid_zip_with_manifest_and_strategy(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, "w") as zf:
                zf.writestr("manifest.json", json.dumps({"name": "test"}))
                zf.writestr("strategy.py", "class TestStrategy: pass")

            result = validate_zip_structure(tmp.name)

            assert result.valid is True
            assert len(result.errors) == 0

    def test_missing_manifest(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, "w") as zf:
                zf.writestr("strategy.py", "class TestStrategy: pass")

            result = validate_zip_structure(tmp.name)

            assert result.valid is False
            assert any("manifest.json" in e for e in result.errors)

    def test_missing_strategy(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, "w") as zf:
                zf.writestr("manifest.json", json.dumps({"name": "test"}))

            result = validate_zip_structure(tmp.name)

            assert result.valid is False
            assert any("strategy.py" in e for e in result.errors)

    def test_too_many_files(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, "w") as zf:
                zf.writestr("manifest.json", "{}")
                zf.writestr("strategy.py", "pass")
                for i in range(101):
                    zf.writestr(f"file_{i}.py", "pass")

            result = validate_zip_structure(tmp.name)

            assert result.valid is False
            assert any("Too many files" in e for e in result.errors)

    def test_file_too_large(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, "w") as zf:
                zf.writestr("manifest.json", "{}")
                zf.writestr("strategy.py", "pass")
                large_content = "x" * (11 * 1024 * 1024)
                zf.writestr("large_file.txt", large_content)

            result = validate_zip_structure(tmp.name)

            assert result.valid is False
            assert any("too large" in e for e in result.errors)

    def test_invalid_zip_file(self):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            tmp.write(b"Not a valid zip file")
            tmp.flush()

            result = validate_zip_structure(tmp.name)

            assert result.valid is False
            assert any("Invalid ZIP" in e for e in result.errors)


class TestValidateManifestSchema:
    def test_valid_manifest(self):
        manifest = {
            "name": "test_plugin",
            "version": "1.0.0",
            "display_name": "Test Plugin",
            "description": "A test plugin",
            "author": "Test Author",
            "strategy_class": "TestStrategy",
            "min_data_points": 100,
        }

        result = validate_manifest_schema(manifest)

        assert result.valid is True
        assert result.manifest == manifest

    def test_missing_required_field(self):
        manifest = {
            "name": "test_plugin",
            "version": "1.0.0",
        }

        result = validate_manifest_schema(manifest)

        assert result.valid is False
        assert any("display_name" in e for e in result.errors)

    def test_invalid_version_format(self):
        manifest = {
            "name": "test_plugin",
            "version": "1.0",
            "display_name": "Test Plugin",
            "description": "A test plugin",
            "author": "Test Author",
            "strategy_class": "TestStrategy",
        }

        result = validate_manifest_schema(manifest)

        assert result.valid is False
        assert any("version" in e.lower() for e in result.errors)

    def test_invalid_plugin_name(self):
        manifest = {
            "name": "test-plugin@#$",
            "version": "1.0.0",
            "display_name": "Test Plugin",
            "description": "A test plugin",
            "author": "Test Author",
            "strategy_class": "TestStrategy",
        }

        result = validate_manifest_schema(manifest)

        assert result.valid is False
        assert any("name" in e.lower() for e in result.errors)

    def test_invalid_min_data_points(self):
        manifest = {
            "name": "test_plugin",
            "version": "1.0.0",
            "display_name": "Test Plugin",
            "description": "A test plugin",
            "author": "Test Author",
            "strategy_class": "TestStrategy",
            "min_data_points": -1,
        }

        result = validate_manifest_schema(manifest)

        assert result.valid is False
        assert any("min_data_points" in e for e in result.errors)

    def test_valid_parameters(self):
        manifest = {
            "name": "test_plugin",
            "version": "1.0.0",
            "display_name": "Test Plugin",
            "description": "A test plugin",
            "author": "Test Author",
            "strategy_class": "TestStrategy",
            "parameters": {
                "param1": {"type": "integer", "default": 10},
                "param2": {"type": "float", "default": 0.5},
            },
        }

        result = validate_manifest_schema(manifest)

        assert result.valid is True

    def test_invalid_parameter_type(self):
        manifest = {
            "name": "test_plugin",
            "version": "1.0.0",
            "display_name": "Test Plugin",
            "description": "A test plugin",
            "author": "Test Author",
            "strategy_class": "TestStrategy",
            "parameters": {
                "param1": {"type": "invalid_type"},
            },
        }

        result = validate_manifest_schema(manifest)

        assert result.valid is False


class TestValidateCodeAst:
    def test_clean_code(self):
        code = """
class TestStrategy:
    def generate_signals(self, data):
        return data
"""

        result = validate_code_ast(code)

        assert result.valid is True
        assert len(result.errors) == 0

    def test_forbidden_import_os(self):
        code = "import os"

        result = validate_code_ast(code)

        assert result.valid is False
        assert any("os" in e for e in result.errors)

    def test_forbidden_import_subprocess(self):
        code = "import subprocess"

        result = validate_code_ast(code)

        assert result.valid is False
        assert any("subprocess" in e for e in result.errors)

    def test_forbidden_function_eval(self):
        code = "eval('1 + 1')"

        result = validate_code_ast(code)

        assert result.valid is False
        assert any("eval" in e for e in result.errors)

    def test_forbidden_exec(self):
        code = "exec('print(1)')"

        result = validate_code_ast(code)

        assert result.valid is False
        assert any("exec" in e for e in result.errors)

    def test_import_from_forbidden_module(self):
        code = "from os import path"

        result = validate_code_ast(code)

        assert result.valid is False
        assert any("os" in e for e in result.errors)

    def test_dangerous_method_call(self):
        code = "os.system('ls')"

        result = validate_code_ast(code)

        assert result.valid is False or len(result.warnings) > 0

    def test_syntax_error(self):
        code = "def broken(:"

        result = validate_code_ast(code)

        assert result.valid is False
        assert any("Syntax error" in e for e in result.errors)

    def test_dunder_import(self):
        code = "__import__('os')"

        result = validate_code_ast(code)

        assert result.valid is False
        assert any("__import__" in e for e in result.errors)


class TestValidateStrategyClass:
    def test_valid_strategy_class(self):
        code = """
from app.backtest.strategies.base import BaseStrategy

class MyStrategy(BaseStrategy):
    def generate_signals(self, data):
        return data

    def get_name(self):
        return "MyStrategy"

    def get_params(self):
        return {}
"""

        result = validate_strategy_class(code, "MyStrategy")

        assert result.valid is True

    def test_missing_strategy_class(self):
        code = """
class OtherStrategy:
    pass
"""

        result = validate_strategy_class(code, "MyStrategy")

        assert result.valid is False
        assert any("not found" in e for e in result.errors)

    def test_missing_required_methods(self):
        code = """
class MyStrategy:
    def generate_signals(self, data):
        return data
"""

        result = validate_strategy_class(code, "MyStrategy")

        assert result.valid is False
        assert any("missing required methods" in e.lower() for e in result.errors)


class TestCheckVersionRules:
    def test_new_plugin_accepts_any_version(self):
        valid, msg = check_version_rules("1.0.0", [])
        assert valid is True
        assert "accepted" in msg.lower()

    def test_same_version_rejected(self):
        valid, msg = check_version_rules("1.0.0", ["1.0.0", "0.9.0"])
        assert valid is False
        assert "already exists" in msg.lower()

    def test_lower_version_rejected(self):
        valid, msg = check_version_rules("0.8.0", ["1.0.0", "0.9.0"])
        assert valid is False
        assert "lower than" in msg.lower()

    def test_higher_version_accepted(self):
        valid, msg = check_version_rules("1.1.0", ["1.0.0", "0.9.0"])
        assert valid is True


class TestPluginValidator:
    def test_validate_zip(self):
        validator = PluginValidator()
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, "w") as zf:
                zf.writestr("manifest.json", "{}")
                zf.writestr("strategy.py", "pass")

            result = validator.validate_zip(tmp.name)
            assert result.valid is True

    def test_validate_manifest(self):
        validator = PluginValidator()
        manifest = {
            "name": "test",
            "version": "1.0.0",
            "display_name": "Test",
            "description": "Test",
            "author": "Test",
            "strategy_class": "Test",
        }

        result = validator.validate_manifest(manifest)
        assert result.valid is True

    def test_validate_code(self):
        validator = PluginValidator()
        code = "class Test: pass"

        result = validator.validate_code(code)
        assert result.valid is True

    def test_validate_all(self):
        validator = PluginValidator()

        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            with zipfile.ZipFile(tmp.name, "w") as zf:
                zf.writestr("manifest.json", json.dumps({
                    "name": "test_plugin",
                    "version": "1.0.0",
                    "display_name": "Test",
                    "description": "Test",
                    "author": "Test",
                    "strategy_class": "TestStrategy",
                }))
                zf.writestr("strategy.py", """
class TestStrategy:
    def generate_signals(self, data):
        return data
    def get_name(self):
        return "TestStrategy"
    def get_params(self):
        return {}
""")

            manifest = {
                "name": "test_plugin",
                "version": "1.0.0",
                "display_name": "Test",
                "description": "Test",
                "author": "Test",
                "strategy_class": "TestStrategy",
            }
            strategy_code = """
class TestStrategy:
    def generate_signals(self, data):
        return data
    def get_name(self):
        return "TestStrategy"
    def get_params(self):
        return {}
"""
            result = validator.validate_all(tmp.name, manifest, strategy_code, [])

            assert result.valid is True
