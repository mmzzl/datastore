# System Initialization Specification

## ADDED Requirements

### Requirement: System SHALL initialize default admin on first startup

The system MUST create default administrator when no users exist.

#### Scenario: Fresh installation
- **WHEN** system starts and users collection is empty
- **THEN** system reads default credentials from config
- **AND** creates superuser role with "*" permission
- **AND** creates admin, trader, viewer roles
- **AND** creates default admin user with superuser role

#### Scenario: Existing users
- **WHEN** system starts and users collection has documents
- **THEN** initialization is skipped
- **AND** log message indicates "Users exist, skipping initialization"

### Requirement: System SHALL read default admin from config

The system MUST support configuration-based default admin credentials.

#### Scenario: Config defined
- **WHEN** config.yaml contains auth.default_admin.username and auth.default_admin.password
- **THEN** system uses these credentials for initial admin

#### Scenario: Config missing
- **WHEN** config does not define default_admin
- **THEN** system uses fallback: username="admin", password="admin"
- **AND** logs warning "Using default credentials, please change immediately"

### Requirement: System SHALL create system roles

The system MUST pre-define essential roles during initialization.

#### Scenario: Role creation
- **WHEN** system initializes
- **THEN** creates roles:
  - role_superuser: name="超级管理员", permissions=["*"], is_system=true
  - role_admin: name="管理员", permissions=[user:*, role:*, plugin:*, system:*], is_system=true
  - role_trader: name="交易员", permissions=[backtest:*, selection:*, holdings:*, risk:view], is_system=true
  - role_viewer: name="观察者", permissions=[*:view], is_system=true

#### Scenario: Roles already exist
- **WHEN** roles collection already has documents
- **THEN** role creation is skipped

### Requirement: System SHALL hash initial password

The system MUST hash the default admin password before storage.

#### Scenario: Password hashing
- **WHEN** creating default admin
- **THEN** password is hashed with bcrypt (rounds=12)
- **AND** only password_hash is stored

### Requirement: System SHALL log initialization events

The system MUST log all initialization actions.

#### Scenario: Successful initialization
- **WHEN** initialization completes
- **THEN** logs "System initialized: created roles X, Y, Z and default admin"
- **AND** logs "Default admin username: admin"

#### Scenario: Initialization skipped
- **WHEN** initialization is skipped
- **THEN** logs "System already initialized, skipping"

### Requirement: System SHALL create MongoDB indexes

The system MUST create necessary indexes during initialization.

#### Scenario: Index creation
- **WHEN** system initializes
- **THEN** creates indexes:
  - users: username (unique), email (sparse unique), role_id, status
  - roles: role_id (unique)
  - strategy_plugins: name (with version), status
  - action_logs: user_id, command, created_at

### Requirement: System SHALL run initialization before accepting requests

The system MUST complete initialization before API becomes available.

#### Scenario: Startup order
- **WHEN** FastAPI startup event fires
- **THEN** initialization runs
- **AND** API endpoints become available after initialization completes

#### Scenario: Initialization failure
- **WHEN** initialization fails (e.g., database connection error)
- **THEN** system logs error
- **AND** continues startup (manual intervention required)
