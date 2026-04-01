# Qlib Integration Architecture

This document describes the architecture for integrating Qlib (Quantitative Investment Library) with the trading system.

## Overview

Qlib is Microsoft's AI-oriented quantitative investment framework. The integration enables:
- ML-based stock selection
- Model training with custom data
- Prediction scoring for stocks

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Vue 3)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Stock Select │  │ Model Manage │  │ Training Dashboard   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼─────────────────┼─────────────────────┼──────────────┘
          │                 │                     │
          ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ /qlib/select │  │ /qlib/models │  │ /qlib/train          │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                     │              │
│         ▼                 ▼                     ▼              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Qlib Service Layer                     │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │  │
│  │  │ QlibPredictor│  │ ModelManager │  │ QlibTrainer    │  │  │
│  │  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘  │  │
│  └─────────┼─────────────────┼──────────────────┼───────────┘  │
└────────────┼─────────────────┼──────────────────┼─────────────┘
             │                 │                  │
             ▼                 ▼                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ MongoDataProvider │  │ Model Storage    │  │ MongoDB       │ │
│  │ (K-line Data)     │  │ (./models/)      │  │ qlib_models   │ │
│  └─────────┬────────┘  └──────────────────┘  └───────────────┘ │
│            │                                                     │
│            ▼                                                     │
│  ┌──────────────────┐                                           │
│  │ DataSourceManager│                                           │
│  │ (Baostock/Akshare)│                                          │
│  └──────────────────┘                                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## MongoDataProvider Design

The `MongoDataProvider` bridges MongoDB K-line data with Qlib's data interface.

### Class Definition

```python
class MongoDataProvider:
    """
    Provides K-line data from MongoDB to Qlib.
    
    Bridges existing MongoDB K-line storage with Qlib's data interface,
    enabling ML model training without data duplication.
    """
    
    def __init__(
        self,
        data_manager: DataSourceManager,
        mongo_adapter: Optional[MongoAdapter] = None,
    ):
        self.data_manager = data_manager
        self.mongo_adapter = mongo_adapter
        self._cache: Dict[str, pd.DataFrame] = {}
```

### Key Methods

#### `load_data()`

Loads K-line data for specified instruments:

```python
def load_data(
    self,
    instruments: List[str],
    start_time: str,
    end_time: str,
    frequency: str = "day",
    adjust_flag: str = "3",
) -> pd.DataFrame:
    """
    Load K-line data from MongoDB.
    
    Args:
        instruments: Stock codes ["SH600000", "SH600519"]
        start_time: "2020-01-01"
        end_time: "2024-01-01"
        frequency: "day", "week", "month"
        adjust_flag: "3" for forward adjusted
    
    Returns:
        DataFrame with MultiIndex (datetime, instrument)
        Columns: open, high, low, close, volume, amount
    """
```

**Output Format**:
```
                              open    high     low   close    volume       amount
datetime   instrument                                                     
2020-01-02 SH600000      10.50   10.80   10.40   10.70  5000000  53000000.0
           SH600519     180.50  182.00  179.00  181.50   500000  90000000.0
```

#### `prepare_for_qlib()`

Creates Qlib Dataset configuration:

```python
def prepare_for_qlib(
    self,
    instruments: List[str],
    start_time: str,
    end_time: str,
    factor_config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Prepare Qlib Dataset configuration.
    
    Returns configuration for DatasetH with Alpha158/Alpha360 handler.
    """
```

### Data Flow

```
1. Request → MongoDataProvider.load_data()
2. _get_klines_for_instrument() for each stock
3. DataSourceManager.get_kline(provider="mongodb")
4. MongoDB Adapter queries collection
5. Returns List[StockKLine]
6. Convert to DataFrame with MultiIndex
7. Return to Qlib Dataset
```

---

## Model Lifecycle

### States

| State | Description |
|-------|-------------|
| `pending` | Training completed, awaiting review |
| `approved` | Approved for production use |
| `rejected` | Rejected after review |
| `deleted` | Soft deleted |

### Lifecycle Diagram

```
┌─────────────┐
│   Train     │
│   Model     │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│   pending   │────▶│  approved   │
└──────┬──────┘     └──────┬──────┘
       │                   │
       │                   ▼
       │            ┌─────────────┐
       │            │ Production  │
       │            │   Use       │
       │            └─────────────┘
       │
       ▼
┌─────────────┐
│  rejected   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  deleted    │
└─────────────┘
```

### Model Metadata

```python
{
    "model_id": "model_20240101_123000",
    "version": 1,
    "created_at": datetime,
    "status": "approved",
    "metrics": {
        "sharpe_ratio": 2.15,
        "ic": 0.05,
        "num_predictions": 5000
    },
    "config": {
        "model_type": "lgbm",
        "factor_type": "alpha158",
        "instruments": ["SH600000", ...],
        "start_time": "2015-01-01",
        "end_time": "2024-01-01"
    }
}
```

---

## Training Pipeline

### Training Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     Training Pipeline                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Configuration                                           │
│     ├── instruments: Stock codes                            │
│     ├── start_time / end_time: Date range                   │
│     ├── model_type: lgbm / mlp                              │
│     └── factor_type: alpha158 / alpha360                    │
│                                                             │
│  2. Data Loading                                            │
│     ├── MongoDataProvider.load_data()                       │
│     ├── Create DatasetH                                     │
│     └── Split: train (60%) / valid (20%) / test (20%)       │
│                                                             │
│  3. Feature Engineering                                     │
│     ├── Alpha158: 158 factors                               │
│     │   └── Technical indicators, price patterns            │
│     └── Alpha360: 360 factors                               │
│         └── Extended feature set                            │
│                                                             │
│  4. Model Training                                          │
│     ├── LGBModel (LightGBM)                                 │
│     │   └── Gradient boosting, MSE loss                    │
│     └── MLPModel (Neural Network)                           │
│         └── Multi-layer perceptron                          │
│                                                             │
│  5. Evaluation                                              │
│     ├── Sharpe Ratio estimation                             │
│     ├── Information Coefficient (IC)                        │
│     └── Prediction count                                    │
│                                                             │
│  6. Model Storage                                           │
│     ├── Save to ./models/{model_id}.pkl                     │
│     └── Store metadata in MongoDB                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### QlibTrainer Implementation

```python
class QlibTrainer:
    def start_training(self, config: Dict[str, Any]) -> str:
        """
        Start async training task.
        
        Returns task_id for progress tracking.
        """
        task_id = self._generate_task_id(config)
        
        # Store task status
        self._training_tasks[task_id] = {
            "config": config,
            "status": "pending",
            "progress": 0,
            "started_at": datetime.now(),
        }
        
        # Run in background thread
        thread = threading.Thread(
            target=self._run_training,
            args=(task_id, config),
            daemon=True,
        )
        thread.start()
        
        return task_id
    
    def _run_training(self, task_id: str, config: Dict[str, Any]):
        """Execute training in background."""
        try:
            # 1. Initialize Qlib
            self._ensure_qlib_initialized()
            
            # 2. Create dataset
            dataset = self._create_dataset(config)
            
            # 3. Create model
            model = self._create_model(config)
            
            # 4. Prepare data
            train_data = dataset.prepare("train")
            valid_data = dataset.prepare("valid")
            
            # 5. Train model
            model.fit(train_data, valid_data)
            
            # 6. Evaluate
            test_data = dataset.prepare("test")
            predictions = model.predict(test_data)
            metrics = self._calculate_metrics(predictions, test_data)
            
            # 7. Save model
            model_id = self._save_model(model, config, metrics)
            
            self._update_status(task_id, "completed", 
                model_id=model_id, metrics=metrics)
                
        except Exception as e:
            self._update_status(task_id, "failed", error=str(e))
```

### Progress Tracking

```python
# Poll training status
GET /api/qlib/train/{task_id}

# Response during training
{
    "status": "running",
    "progress": 40,
    "progress_message": "Training model"
}

# Response on completion
{
    "status": "completed",
    "progress": 100,
    "model_id": "model_20240101_123000",
    "metrics": {
        "sharpe_ratio": 2.15,
        "ic": 0.05
    }
}
```

---

## Stock Selection

### Prediction Flow

```
1. User selects model and date
2. QlibPredictor.predict() called
3. Load model from disk
4. Load data for date range
5. Generate features (Alpha158)
6. Run model prediction
7. Rank stocks by score
8. Return top-k results
```

### QlibPredictor

```python
class QlibPredictor:
    def predict(
        self,
        model_id: str,
        topk: int = 50,
        date: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Run stock selection.
        
        Args:
            model_id: Trained model ID
            topk: Number of stocks to return
            date: Prediction date (latest if None)
        
        Returns:
            List of {code, name, score} dicts
        """
```

### Usage Example

```python
# API call
POST /api/qlib/select
{
    "model_id": "model_20240101_123000",
    "date": "2024-01-15",
    "topk": 50
}

# Response
{
    "model_id": "model_20240101_123000",
    "date": "2024-01-15",
    "results": [
        {"rank": 1, "code": "SH600000", "name": "浦发银行", "score": 0.8521},
        {"rank": 2, "code": "SH600519", "name": "贵州茅台", "score": 0.8234},
        ...
    ]
}
```

---

## Configuration

### Model Types

| Type | Description | Parameters |
|------|-------------|------------|
| `lgbm` | LightGBM Gradient Boosting | `n_estimators`, `learning_rate`, `num_leaves` |
| `mlp` | Multi-Layer Perceptron | `hidden_sizes`, `dropout_rate` |

### Factor Types

| Type | Features | Use Case |
|------|----------|----------|
| `alpha158` | 158 technical factors | General stock selection |
| `alpha360` | 360 extended factors | Advanced strategies |

### CSI 300 Configuration

```python
# app/qlib/config.py
CSI_300_STOCKS = [
    "SH600000",  # 浦发银行
    "SH600519",  # 贵州茅台
    # ... 300 stocks total
]

def get_csi300_instruments() -> List[str]:
    return CSI_300_STOCKS.copy()
```

---

## Integration Points

### 1. Data Source

```python
# DataSourceManager provides unified data access
data_manager = DataSourceManager()

# Get K-line data
klines = data_manager.get_kline(
    code="600000",
    start_date="2020-01-01",
    end_date="2024-01-01",
    provider="mongodb"  # or "baostock", "akshare"
)
```

### 2. Model Storage

```python
# Models stored in two places:
# 1. Disk: ./models/{model_id}.pkl (pickled model object)
# 2. MongoDB: qlib_models collection (metadata)

# ModelManager handles both
manager = ModelManager()
model_id = manager.save_model(model, config, metrics)
metadata = manager.get_model_metadata(model_id)
```

### 3. Scheduler Integration

```python
# Scheduled training via scheduler
job_config = {
    "model_type": "lgbm",
    "instruments": "csi300",
    "factor_type": "alpha158",
}

# Cron: Every Sunday at 2 AM
# "0 2 * * 0"
```

---

## Best Practices

1. **Data Quality**: Ensure K-line data is complete and adjusted correctly
2. **Model Versioning**: Always version models and keep metadata
3. **Evaluation**: Use out-of-sample data for testing
4. **Approval Process**: Review metrics before approving models
5. **Monitoring**: Track model performance over time
6. **Retraining**: Schedule periodic retraining for market changes
