# Plugin Upload Specification

## ADDED Requirements

### Requirement: System SHALL validate ZIP file structure

The system MUST validate that uploaded ZIP files conform to the plugin standard before extraction.

#### Scenario: Valid ZIP structure
- **WHEN** user uploads ZIP containing `manifest.json` and `strategy.py`
- **THEN** system accepts the file for further validation
- **AND** extracts to temporary directory for inspection

#### Scenario: Missing required files
- **WHEN** user uploads ZIP without `manifest.json`
- **THEN** system returns HTTP 400 error
- **AND** error message indicates "Missing manifest.json"

#### Scenario: Maximum file size exceeded
- **WHEN** user uploads ZIP larger than 5MB
- **THEN** system returns HTTP 413 error
- **AND** error message indicates "File size exceeds 5MB limit"

#### Scenario: Invalid file extension
- **WHEN** user uploads file without .zip extension
- **THEN** system returns HTTP 400 error
- **AND** error message indicates "Only .zip files are accepted"

#### Scenario: Path traversal attempt
- **WHEN** ZIP contains files with `../` in path
- **THEN** system returns HTTP 400 error
- **AND** error message indicates "Invalid file path detected"
- **AND** operation is logged as security event

### Requirement: System SHALL validate manifest.json schema

The system MUST validate manifest.json against the defined schema.

#### Scenario: Valid manifest
- **WHEN** manifest.json contains all required fields (name, version, display_name, strategy_class)
- **THEN** system proceeds to code validation

#### Scenario: Missing required field
- **WHEN** manifest.json is missing "name" field
- **THEN** system returns HTTP 400 error
- **AND** error message indicates "Missing required field: name"

#### Scenario: Invalid version format
- **WHEN** version is not in semver format (e.g., "1.0" instead of "1.0.0")
- **THEN** system returns HTTP 400 error
- **AND** error message indicates "Invalid version format, must be X.Y.Z"

#### Scenario: Invalid parameter definition
- **WHEN** parameter type is not one of (integer, float, string, boolean)
- **THEN** system returns HTTP 400 error
- **AND** error message indicates "Invalid parameter type: <type>"

### Requirement: System SHALL perform AST code analysis

The system MUST analyze strategy.py for security violations using AST parsing.

#### Scenario: Clean code
- **WHEN** strategy.py imports only allowed modules (pandas, numpy, app.backtest.strategies.base)
- **THEN** system proceeds to class validation

#### Scenario: Forbidden import detected
- **WHEN** strategy.py imports "os" module
- **THEN** system returns HTTP 400 error
- **AND** error message indicates "Forbidden import: os"
- **AND** operation is logged as security event

#### Scenario: Dynamic code execution
- **WHEN** strategy.py contains "eval()" or "exec()" call
- **THEN** system returns HTTP 400 error
- **AND** error message indicates "Dynamic code execution is forbidden"

#### Scenario: Missing BaseStrategy inheritance
- **WHEN** strategy class does not inherit from BaseStrategy
- **THEN** system returns HTTP 400 error
- **AND** error message indicates "Strategy class must inherit from BaseStrategy"

#### Scenario: Missing required methods
- **WHEN** strategy class is missing generate_signals() method
- **THEN** system returns HTTP 400 error
- **AND** error message indicates "Missing required method: generate_signals"

### Requirement: System SHALL enforce version rules

The system MUST validate version against existing plugins with same name.

#### Scenario: New plugin name
- **WHEN** no existing plugin with same name
- **THEN** system creates directory: `plugins/{name}/`
- **AND** saves metadata to MongoDB with status "active"

#### Scenario: New version of existing plugin
- **WHEN** existing plugin has version 1.0.0 and uploaded version is 1.1.0
- **THEN** system creates directory: `plugins/{name}_1.1.0/`
- **AND** saves metadata with status "inactive"
- **AND** returns message "Uploaded as new version, activate to use"

#### Scenario: Same version already exists
- **WHEN** existing plugin has version 1.0.0 and uploaded version is 1.0.0
- **THEN** system returns HTTP 409 conflict
- **AND** error message indicates "Version 1.0.0 already exists"

#### Scenario: Lower version than existing
- **WHEN** existing plugin has version 1.1.0 and uploaded version is 1.0.0
- **THEN** system returns HTTP 409 conflict
- **AND** error message indicates "Higher version 1.1.0 already exists"

### Requirement: System SHALL require upload permission

The system MUST check user permission before accepting plugin upload.

#### Scenario: User with upload permission
- **WHEN** user has "plugin:upload" permission
- **THEN** system processes the upload request

#### Scenario: User without upload permission
- **WHEN** user does not have "plugin:upload" permission
- **THEN** system returns HTTP 403 forbidden
- **AND** error message indicates "Missing permission: plugin:upload"

### Requirement: System SHALL store plugin metadata

The system MUST save plugin information to MongoDB for management.

#### Scenario: Successful upload
- **WHEN** all validations pass
- **THEN** system saves to strategy_plugins collection: {name, version, path, manifest, status, created_at}
- **AND** returns plugin_id and success message
