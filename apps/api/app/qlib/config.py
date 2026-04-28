"""
Qlib Configuration Module

This module provides configuration constants and default settings
for Qlib integration with OpenClaw.
"""

import os
import csv
from typing import Dict, Any, List
from dataclasses import dataclass, field


def _load_csv_codes(csv_name: str, prefix: str = "SH") -> List[str]:
    """Load stock codes from a CSV file in the data directory, add exchange prefix."""
    csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", csv_name)
    codes = []
    try:
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get("code", "").strip()
                if code:
                    # 6xxxxx → SH, others → SZ
                    p = prefix if code.startswith("6") else "SZ"
                    codes.append(f"{p}{code}")
    except Exception:
        pass
    return codes


CSI_300_STOCKS: List[str] = _load_csv_codes("hs300_stocks.csv")
CSI_500_STOCKS: List[str] = _load_csv_codes("zz500_stocks.csv")


DEFAULT_MODEL_CONFIG: Dict[str, Any] = {
    "lgbm": {
        "class": "qlib.contrib.model.gbdt.LGBModel",
        "module_path": "qlib.contrib.model.gbdt",
        "kwargs": {
            "loss": "mse",
            "colsample_bytree": 0.8,
            "learning_rate": 0.01,
            "n_estimators": 1000,
            "num_leaves": 63,
            "subsample": 0.8,
            "early_stopping_rounds": 50,
        },
    },
    "mlp": {
        "class": "qlib.contrib.model.pytorch_mlp.PytorchMLPModel",
        "module_path": "qlib.contrib.model.pytorch_mlp",
        "kwargs": {
            "hidden_sizes": [256, 128, 64],
            "lr": 0.001,
            "batch_size": 4096,
            "epochs": 100,
        },
    },
}


DEFAULT_FACTOR_CONFIG: Dict[str, Any] = {
    "alpha158": {
        "class": "qlib.contrib.data.handler.Alpha158",
        "module_path": "qlib.contrib.data.handler",
    },
    "alpha360": {
        "class": "qlib.contrib.data.handler.Alpha360",
        "module_path": "qlib.contrib.data.handler",
    },
}


TRAINING_TIME_SEGMENTS: Dict[str, tuple] = {
    "train": ("2015-01-01", "2022-12-31"),
    "valid": ("2023-01-01", "2024-06-30"),
    "test": ("2024-07-01", "2026-01-01"),
}


CRON_SCHEDULES: Dict[str, str] = {
    "weekly_training": "0 2 * * 0",
    "daily_risk_report": "30 15 * * 1-5",
}


def get_model_config(model_type: str) -> Dict[str, Any]:
    """
    Get model configuration by type.
    
    Args:
        model_type: Model type identifier
    
    Returns:
        Model configuration dictionary
    """
    return DEFAULT_MODEL_CONFIG.get(model_type, DEFAULT_MODEL_CONFIG["lgbm"])


def get_factor_config(factor_type: str) -> Dict[str, Any]:
    """
    Get factor configuration by type.
    
    Args:
        factor_type: Factor type identifier
    
    Returns:
        Factor configuration dictionary
    """
    return DEFAULT_FACTOR_CONFIG.get(factor_type, DEFAULT_FACTOR_CONFIG["alpha158"])


def get_csi300_instruments() -> List[str]:
    """Get CSI 300 stock list.

    Returns:
        List of stock codes
    """
    return CSI_300_STOCKS.copy()


def get_csi500_instruments() -> List[str]:
    """Get CSI 500 stock list.

    Returns:
        List of stock codes
    """
    return CSI_500_STOCKS.copy()


VALID_POOLS = {"csi300", "csi500"}


def get_instruments(pool_name: str) -> List[str]:
    """Get stock list by pool name.

    Args:
        pool_name: Stock pool name, either "csi300" or "csi500"

    Returns:
        List of stock codes

    Raises:
        ValueError: If pool_name is not a valid pool name
    """
    if pool_name == "csi300":
        return get_csi300_instruments()
    elif pool_name == "csi500":
        return get_csi500_instruments()
    else:
        raise ValueError(
            f"Invalid pool name: '{pool_name}'. Valid pool names: {sorted(VALID_POOLS)}"
        )


def create_dataset_config(
    instruments: List[str],
    start_time: str,
    end_time: str,
    factor_type: str = "alpha158",
    train_ratio: float = 0.6,
    valid_ratio: float = 0.2,
) -> Dict[str, Any]:
    """
    Create Qlib Dataset configuration.
    
    Args:
        instruments: List of stock codes
        start_time: Start date
        end_time: End date
        factor_type: Factor type (alpha158, alpha360)
        train_ratio: Training data ratio
        valid_ratio: Validation data ratio
    
    Returns:
        Dataset configuration dictionary
    """
    factor_config = get_factor_config(factor_type)
    
    from datetime import datetime
    import pandas as pd
    
    start_dt = pd.to_datetime(start_time)
    end_dt = pd.to_datetime(end_time)
    total_days = (end_dt - start_dt).days
    
    train_end = start_dt + pd.Timedelta(days=int(total_days * train_ratio))
    valid_end = start_dt + pd.Timedelta(days=int(total_days * (train_ratio + valid_ratio)))
    
    return {
        "class": "qlib.data.dataset.DatasetH",
        "module_path": "qlib.data.dataset",
        "kwargs": {
            "handler": {
                **factor_config,
                "kwargs": {
                    "start_time": start_time,
                    "end_time": end_time,
                    "fit_start_time": start_time,
                    "fit_end_time": end_time,
                    "instruments": instruments,
                },
            },
            "segments": {
                "train": (start_time, train_end.strftime("%Y-%m-%d")),
                "valid": (train_end.strftime("%Y-%m-%d"), valid_end.strftime("%Y-%m-%d")),
                "test": (valid_end.strftime("%Y-%m-%d"), end_time),
            },
        },
    }
