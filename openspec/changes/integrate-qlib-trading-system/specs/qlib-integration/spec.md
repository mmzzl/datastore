# Qlib Integration Specification

## ADDED Requirements

### Requirement: System SHALL provide custom MongoDB data provider for Qlib

The system MUST implement a MongoDataProvider class that loads K-line data from MongoDB and converts it to Qlib-compatible format (MultiIndex DataFrame with datetime and instrument levels).

#### Scenario: Load CSI 300 K-line data
- **WHEN** MongoDataProvider.load_data() is called with instruments=["SH600000", "SH600519"], start_time="2020-01-01", end_time="2026-01-01"
- **THEN** system returns a DataFrame with MultiIndex (datetime, instrument) and columns [open, high, low, close, volume, amount]
- **AND** all specified instruments are included in the result

#### Scenario: Handle missing data gracefully
- **WHEN** requested stock has no data in MongoDB for the specified date range
- **THEN** system returns empty DataFrame for that instrument without raising exception
- **AND** logs a warning message

### Requirement: System SHALL train Qlib models weekly

The system MUST execute automated model training every Sunday at 02:00 using CSI 300 stock pool and Alpha158 factors.

#### Scenario: Weekly training executes successfully
- **WHEN** Sunday 02:00 arrives (cron: "0 2 * * 0")
- **THEN** system initiates model training with predefined configuration
- **AND** training uses MongoDB data from 2015-01-01 to current date minus 14 days
- **AND** validation set uses most recent 14 days

#### Scenario: Training failure triggers alert
- **WHEN** model training fails due to data unavailability or system error
- **THEN** system sends DingTalk notification with error details
- **AND** retains previous model version without changes
- **AND** logs error to MongoDB

#### Scenario: Manual training trigger
- **WHEN** POST /api/qlib/train is called with valid configuration
- **THEN** system starts training job immediately
- **AND** returns task_id for status tracking
- **AND** does not interfere with scheduled training if running

### Requirement: System SHALL evaluate model performance using Sharpe ratio

The system MUST calculate Sharpe ratio on test set and only deploy models meeting minimum threshold (Sharpe > 1.5).

#### Scenario: Model meets deployment criteria
- **WHEN** trained model achieves Sharpe ratio > 1.5 on test set
- **THEN** system marks model as "approved" status
- **AND** saves model metadata to MongoDB qlib_models collection
- **AND** saves model binary to filesystem

#### Scenario: Model fails deployment criteria
- **WHEN** trained model achieves Sharpe ratio ≤ 1.5 on test set
- **THEN** system marks model as "rejected" status
- **AND** does NOT deploy model
- **AND** sends DingTalk notification about rejection
- **AND** continues using previous approved model

### Requirement: System SHALL manage model versions

The system MUST store model metadata in MongoDB and model binaries on filesystem, with automatic version numbering.

#### Scenario: Save new model version
- **WHEN** model training completes successfully
- **THEN** system assigns version number (previous version + 1)
- **AND** saves metadata to MongoDB: {model_id, version, created_at, metrics, file_path, status}
- **AND** saves binary to ./models/{model_id}.pkl

#### Scenario: Load specific model version
- **WHEN** GET /api/qlib/models/{model_id} is called
- **THEN** system returns model metadata from MongoDB
- **AND** model binary is accessible via file_path field

#### Scenario: List all models
- **WHEN** GET /api/qlib/models is called
- **THEN** system returns paginated list of models sorted by created_at descending
- **AND** each entry includes model_id, version, created_at, metrics, status

### Requirement: System SHALL use Alpha158 factors for training

The system MUST configure Qlib Dataset with Alpha158 feature handler as the default factor set.

#### Scenario: Configure Alpha158 dataset
- **WHEN** training configuration is created
- **THEN** dataset uses "qlib.contrib.data.handler.Alpha158" as handler
- **AND** feature count equals 158 (or as per Qlib version)
- **AND** data is split into train/valid/test segments

### Requirement: System SHALL use LightGBM as default model

The system MUST configure LightGBM as the default ML model with predefined hyperparameters optimized for aggressive trading style.

#### Scenario: LightGBM configuration
- **WHEN** model is initialized for training
- **THEN** model uses "qlib.contrib.model.gbdt.LGBModel"
- **AND** hyperparameters include: learning_rate=0.01, n_estimators=1000, num_leaves=63
- **AND** early_stopping_rounds=50
