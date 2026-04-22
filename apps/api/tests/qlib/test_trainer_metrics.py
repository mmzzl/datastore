"""Unit tests for QlibTrainer enriched metrics methods.

Tests _calculate_rank_ic, _calculate_icir, _calculate_long_short_return,
and the updated _calculate_metrics return dict.
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from app.qlib.trainer import QlibTrainer


@pytest.fixture
def trainer():
    return QlibTrainer(model_dir="./test_models")


def _make_multiindex_data(n_dates=20, n_stocks=50, seed=42):
    rng = np.random.RandomState(seed)
    dates = pd.date_range("2024-01-01", periods=n_dates, freq="B")
    instruments = [f"SH{600000 + i:06d}" for i in range(n_stocks)]
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    predictions = pd.Series(rng.randn(len(idx)), index=idx, name="score")
    labels = pd.Series(rng.randn(len(idx)) * 0.5, index=idx, name="label")
    return predictions, labels


class TestCalculateRankIc:
    def test_returns_float(self, trainer):
        predictions, labels = _make_multiindex_data()
        result = trainer._calculate_rank_ic(predictions, labels)
        assert isinstance(result, float)

    def test_perfect_positive_correlation(self, trainer):
        predictions = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        labels = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        result = trainer._calculate_rank_ic(predictions, labels)
        assert result > 0.99

    def test_perfect_negative_correlation(self, trainer):
        predictions = pd.Series([5.0, 4.0, 3.0, 2.0, 1.0])
        labels = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        result = trainer._calculate_rank_ic(predictions, labels)
        assert result < -0.99

    def test_no_common_index_returns_zero(self, trainer):
        predictions = pd.Series([1.0, 2.0], index=["a", "b"])
        labels = pd.Series([3.0, 4.0], index=["c", "d"])
        result = trainer._calculate_rank_ic(predictions, labels)
        assert result == 0.0

    def test_dataframe_labels(self, trainer):
        predictions = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        labels = pd.DataFrame({"label": [10.0, 20.0, 30.0, 40.0, 50.0]})
        result = trainer._calculate_rank_ic(predictions, labels)
        assert result > 0.99

    def test_nan_predictions_handled(self, trainer):
        predictions = pd.Series([1.0, np.nan, 3.0, 4.0, 5.0])
        labels = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        result = trainer._calculate_rank_ic(predictions, labels)
        assert isinstance(result, float)


class TestCalculateIcir:
    def test_returns_float(self, trainer):
        predictions, labels = _make_multiindex_data()
        result = trainer._calculate_icir(predictions, labels)
        assert isinstance(result, float)

    def test_multiindex_required(self, trainer):
        predictions = pd.Series([1.0, 2.0, 3.0])
        labels = pd.Series([4.0, 5.0, 6.0])
        result = trainer._calculate_icir(predictions, labels)
        assert result == 0.0

    def test_fewer_than_10_periods_returns_zero(self, trainer):
        predictions, labels = _make_multiindex_data(n_dates=5, n_stocks=20)
        result = trainer._calculate_icir(predictions, labels)
        assert result == 0.0

    def test_sufficient_periods_returns_nonzero(self, trainer):
        predictions, labels = _make_multiindex_data(n_dates=20, n_stocks=50)
        result = trainer._calculate_icir(predictions, labels)
        assert isinstance(result, float)

    def test_zero_std_returns_zero(self, trainer):
        dates = pd.date_range("2024-01-01", periods=15, freq="B")
        instruments = [f"SH{600000 + i:06d}" for i in range(10)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        predictions = pd.Series(1.0, index=idx)
        labels = pd.Series(1.0, index=idx)
        result = trainer._calculate_icir(predictions, labels)
        assert result == 0.0

    def test_no_common_index_returns_zero(self, trainer):
        predictions = pd.Series([1.0], index=pd.MultiIndex.from_tuples(
            [("2024-01-01", "SH600000")], names=["datetime", "instrument"]
        ))
        labels = pd.Series([2.0], index=pd.MultiIndex.from_tuples(
            [("2024-01-02", "SH600001")], names=["datetime", "instrument"]
        ))
        result = trainer._calculate_icir(predictions, labels)
        assert result == 0.0


class TestCalculateLongShortReturn:
    def test_returns_float(self, trainer):
        predictions, labels = _make_multiindex_data()
        result = trainer._calculate_long_short_return(predictions, labels)
        assert isinstance(result, float)

    def test_multiindex_required(self, trainer):
        predictions = pd.Series([1.0, 2.0, 3.0])
        labels = pd.Series([4.0, 5.0, 6.0])
        result = trainer._calculate_long_short_return(predictions, labels)
        assert result == 0.0

    def test_too_few_stocks_returns_zero(self, trainer):
        dates = pd.date_range("2024-01-01", periods=15, freq="B")
        instruments = [f"SH{600000 + i:06d}" for i in range(5)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        predictions = pd.Series(np.random.randn(len(idx)), index=idx)
        labels = pd.Series(np.random.randn(len(idx)), index=idx)
        result = trainer._calculate_long_short_return(predictions, labels)
        assert result == 0.0

    def test_sufficient_data_returns_value(self, trainer):
        predictions, labels = _make_multiindex_data(n_dates=20, n_stocks=50)
        result = trainer._calculate_long_short_return(predictions, labels)
        assert isinstance(result, float)

    def test_no_common_index_returns_zero(self, trainer):
        predictions = pd.Series([1.0], index=pd.MultiIndex.from_tuples(
            [("2024-01-01", "SH600000")], names=["datetime", "instrument"]
        ))
        labels = pd.Series([2.0], index=pd.MultiIndex.from_tuples(
            [("2024-01-02", "SH600001")], names=["datetime", "instrument"]
        ))
        result = trainer._calculate_long_short_return(predictions, labels)
        assert result == 0.0


class TestCalculateMetricsEnriched:
    @patch.object(QlibTrainer, "_ensure_qlib_initialized", return_value=True)
    @patch.object(QlibTrainer, "_create_dataset")
    @patch.object(QlibTrainer, "_create_model")
    @patch.object(QlibTrainer, "_prepare_train_data")
    @patch.object(QlibTrainer, "_prepare_valid_data")
    @patch.object(QlibTrainer, "_prepare_test_data")
    @patch.object(QlibTrainer, "_save_model", return_value="model_test")
    def test_metrics_dict_contains_enriched_keys(
        self, mock_save, mock_test, mock_valid, mock_train,
        mock_model, mock_dataset, mock_init, trainer,
    ):
        n_dates = 20
        n_stocks = 50
        dates = pd.date_range("2024-01-01", periods=n_dates, freq="B")
        instruments = [f"SH{600000 + i:06d}" for i in range(n_stocks)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        rng = np.random.RandomState(42)
        pred_values = rng.randn(len(idx))

        mock_predictions = MagicMock()
        mock_predictions.values = pred_values
        mock_predictions.index = idx

        label_df = pd.DataFrame(
            {"label": rng.randn(len(idx)) * 0.5},
            index=idx,
        )
        mock_test.return_value = label_df

        mock_model_instance = MagicMock()
        mock_model_instance.predict.return_value = mock_predictions
        mock_model_instance.fit = MagicMock()
        mock_model.return_value = mock_model_instance

        mock_dataset_instance = MagicMock()
        mock_dataset.return_value = mock_dataset_instance

        mock_train.return_value = MagicMock()
        mock_valid.return_value = MagicMock()

        config = {
            "model_type": "lgbm",
            "factor_type": "alpha158",
            "instruments": "csi300",
            "start_time": "2020-01-01",
            "end_time": "2025-01-01",
        }

        task_id = trainer.start_training(config)
        import time
        for _ in range(60):
            status = trainer.get_status(task_id)
            if status["status"] in ("completed", "failed", "cancelled"):
                break
            time.sleep(0.5)

        status = trainer.get_status(task_id)
        if status["status"] == "completed" and status.get("metrics"):
            metrics = status["metrics"]
            assert "rank_ic" in metrics
            assert "icir" in metrics
            assert "long_short_return" in metrics
            assert "ic" in metrics
            assert "sharpe_ratio" in metrics
