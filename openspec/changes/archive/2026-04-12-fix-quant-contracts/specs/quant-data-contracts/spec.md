## ADDED Requirements

### Requirement: Unified Pydantic Data Models
All quantitative data entities (K-lines, Indicators, Signals, Tasks) SHALL be defined using Pydantic `BaseModel` to ensure strict type validation.

#### Scenario: Validate K-line data
- **WHEN** data is loaded from MongoDB
- **THEN** the system MUST validate that `close` is a float and `timestamp` is a valid datetime, raising a validation error otherwise.

#### Scenario: Type-safe signal generation
- **WHEN** a strategy generates a signal
- **THEN** the signal MUST be an instance of `SignalModel` with a valid `SignalType` enum value.

### Requirement: Serialization Consistency
The system SHALL ensure that the model used for internal calculation is identical to the model used for API response serialization.

#### Scenario: Zero-loss serialization
- **WHEN** an engine result is returned via FastAPI
- **THEN** no `TypeError` or `ValueError` SHALL occur during JSON serialization of the Pydantic model.
