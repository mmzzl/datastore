"""
Tests for Qlib configuration module.

This module tests:
- QlibConfig dataclass
- Model configuration functions
- Factor configuration functions
- CSI 300 instruments
- Dataset configuration creation
- Training time segments
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from app.qlib.config import (
    QlibConfig,
    CSI_300_STOCKS,
    DEFAULT_MODEL_CONFIG,
    DEFAULT_FACTOR_CONFIG,
    TRAINING_TIME_SEGMENTS,
    get_model_config,
    get_factor_config,
    get_csi300_instruments,
    create_dataset_config,
)


class TestQlibConfig:
    """Tests for QlibConfig dataclass."""

    def test_default_config(self):
        """Test that default configuration values are correct."""
        config = QlibConfig()

        assert config.provider_uri == "~/.qlib/qlib_data/cn_data"
        assert config.region == "CN"
        assert config.model_dir == "./models"
        assert config.default_model_type == "lgbm"
        assert config.default_factor_type == "alpha158"
        assert config.default_instruments == "csi300"
        assert config.min_sharpe_ratio == 1.5

    def test_custom_config(self):
        """Test that custom configuration values can be set."""
        config = QlibConfig(
            provider_uri="/custom/qlib/data",
            region="US",
            model_dir="/custom/models",
            default_model_type="mlp",
            min_sharpe_ratio=2.0,
        )

        assert config.provider_uri == "/custom/qlib/data"
        assert config.region == "US"
        assert config.model_dir == "/custom/models"
        assert config.default_model_type == "mlp"
        assert config.min_sharpe_ratio == 2.0

    def test_training_config_default(self):
        """Test that training_config has expected default values."""
        config = QlibConfig()

        assert "model_type" in config.training_config
        assert config.training_config["model_type"] == "lgbm"
        assert config.training_config["factor_type"] == "alpha158"
        assert config.training_config["start_time"] == "2015-01-01"
        assert config.training_config["end_time"] == "2026-01-01"

    def test_prediction_config_default(self):
        """Test that prediction_config has expected default values."""
        config = QlibConfig()

        assert "topk" in config.prediction_config
        assert config.prediction_config["topk"] == 50
        assert config.prediction_config["n_drop"] == 0


class TestGetModelConfig:
    """Tests for get_model_config function."""

    def test_get_lgbm_config(self):
        """Test getting LightGBM model configuration."""
        config = get_model_config("lgbm")

        assert config["class"] == "qlib.contrib.model.gbdt.LGBModel"
        assert config["module_path"] == "qlib.contrib.model.gbdt"
        assert "kwargs" in config
        assert config["kwargs"]["loss"] == "mse"
        assert config["kwargs"]["learning_rate"] == 0.01

    def test_get_mlp_config(self):
        """Test getting MLP model configuration."""
        config = get_model_config("mlp")

        assert config["class"] == "qlib.contrib.model.pytorch_mlp.PytorchMLPModel"
        assert config["module_path"] == "qlib.contrib.model.pytorch_mlp"
        assert "kwargs" in config
        assert config["kwargs"]["hidden_sizes"] == [256, 128, 64]
        assert config["kwargs"]["lr"] == 0.001

    def test_get_unknown_config_returns_default(self):
        """Test that unknown model type returns default (lgbm) config."""
        config = get_model_config("unknown_model")

        # Should return lgbm config as default
        assert config["class"] == "qlib.contrib.model.gbdt.LGBModel"


class TestGetFactorConfig:
    """Tests for get_factor_config function."""

    def test_get_alpha158_config(self):
        """Test getting Alpha158 factor configuration."""
        config = get_factor_config("alpha158")

        assert config["class"] == "qlib.contrib.data.handler.Alpha158"
        assert config["module_path"] == "qlib.contrib.data.handler"

    def test_get_alpha360_config(self):
        """Test getting Alpha360 factor configuration."""
        config = get_factor_config("alpha360")

        assert config["class"] == "qlib.contrib.data.handler.Alpha360"
        assert config["module_path"] == "qlib.contrib.data.handler"

    def test_get_unknown_factor_returns_default(self):
        """Test that unknown factor type returns default (alpha158) config."""
        config = get_factor_config("unknown_factor")

        # Should return alpha158 config as default
        assert config["class"] == "qlib.contrib.data.handler.Alpha158"


class TestCSI300Instruments:
    """Tests for CSI 300 instruments functions."""

    def test_get_csi300_instruments(self):
        """Test getting CSI 300 stock list."""
        instruments = get_csi300_instruments()

        assert isinstance(instruments, list)
        assert len(instruments) > 0
        assert "SH600000" in instruments

    def test_csi300_is_copy(self):
        """Test that get_csi300_instruments returns a copy."""
        instruments1 = get_csi300_instruments()
        instruments2 = get_csi300_instruments()

        # Modifying one should not affect the other
        instruments1.append("TEST_STOCK")
        assert "TEST_STOCK" not in instruments2

    def test_csi300_constant_format(self):
        """Test that CSI 300 stocks have correct format."""
        for stock in CSI_300_STOCKS[:10]:  # Check first 10
            assert stock.startswith("SH") or stock.startswith("SZ")


class TestCreateDatasetConfig:
    """Tests for create_dataset_config function."""

    def test_create_dataset_config_basic(self):
        """Test basic dataset configuration creation."""
        config = create_dataset_config(
            instruments=["SH600000", "SH600519"],
            start_time="2020-01-01",
            end_time="2021-01-01",
        )

        assert config["class"] == "qlib.data.dataset.DatasetH"
        assert config["module_path"] == "qlib.data.dataset"
        assert "kwargs" in config
        assert "handler" in config["kwargs"]
        assert "segments" in config["kwargs"]

    def test_create_dataset_config_with_custom_ratios(self):
        """Test dataset configuration with custom train/valid ratios."""
        config = create_dataset_config(
            instruments=["SH600000"],
            start_time="2020-01-01",
            end_time="2021-01-01",
            train_ratio=0.7,
            valid_ratio=0.15,
        )

        segments = config["kwargs"]["segments"]
        assert "train" in segments
        assert "valid" in segments
        assert "test" in segments

    def test_create_dataset_config_with_alpha360(self):
        """Test dataset configuration with alpha360 factor."""
        config = create_dataset_config(
            instruments=["SH600000"],
            start_time="2020-01-01",
            end_time="2021-01-01",
            factor_type="alpha360",
        )

        handler = config["kwargs"]["handler"]
        assert "Alpha360" in handler["class"]


class TestTrainingTimeSegments:
    """Tests for training time segments."""

    def test_time_segments_structure(self):
        """Test that training time segments have correct structure."""
        assert "train" in TRAINING_TIME_SEGMENTS
        assert "valid" in TRAINING_TIME_SEGMENTS
        assert "test" in TRAINING_TIME_SEGMENTS

        for segment_name, segment in TRAINING_TIME_SEGMENTS.items():
            assert isinstance(segment, tuple)
            assert len(segment) == 2
            # Each element should be a date string
            assert isinstance(segment[0], str)
            assert isinstance(segment[1], str)

    def test_time_segments_order(self):
        """Test that training time segments are in chronological order."""
        train_start, train_end = TRAINING_TIME_SEGMENTS["train"]
        valid_start, valid_end = TRAINING_TIME_SEGMENTS["valid"]
        test_start, test_end = TRAINING_TIME_SEGMENTS["test"]

        # Train should end before valid starts
        assert train_end < valid_start
        # Valid should end before test starts
        assert valid_end < test_start
        # All should be in order
        assert train_start < train_end < valid_start < valid_end < test_start < test_end
