# Permission Check Specification

## ADDED Requirements

### Requirement: System SHALL enforce permissions on all protected endpoints

The system MUST check user permissions before allowing access to protected API endpoints.

#### Scenario: Access granted
- **WHEN** user has required permission for endpoint
- **THEN** request proceeds normally

#### Scenario: Access denied
- **WHEN** user lacks required permission
- **THEN** system returns HTTP 403
- **AND** error message indicates "Missing permission: <permission>"

#### Scenario: Superuser bypass
- **WHEN** user is superuser (is_superuser=true)
- **THEN** all permission checks pass
- **AND** request proceeds without restriction

### Requirement: System SHALL support permission hierarchy

The system MUST recognize wildcard permissions.

#### Scenario: Wildcard permission
- **WHEN** user has "backtest:*" permission
- **THEN** user can access backtest:view, backtest:run, backtest:edit

#### Scenario: Global wildcard
- **WHEN** user has "*" permission
- **THEN** user can access all endpoints

### Requirement: System SHALL cache permissions in JWT

The system MUST include permissions in JWT payload for performance.

#### Scenario: Token validation
- **WHEN** API receives request with JWT
- **THEN** system extracts permissions from token
- **AND** does NOT query database for permissions

#### Scenario: Permission change
- **WHEN** user's role permissions are updated
- **THEN** user must re-login to get new token with updated permissions

### Requirement: System SHALL provide permission decorator

The system MUST provide reusable dependency for permission checking.

#### Scenario: Use require_permission
- **WHEN** endpoint uses `Depends(require_permission("plugin:upload"))`
- **THEN** system checks permission before executing endpoint

### Requirement: System SHALL map endpoints to permissions

The system MUST define required permissions for each endpoint.

| Endpoint | Required Permission |
|----------|---------------------|
| POST /api/plugins/upload | plugin:upload |
| GET /api/plugins | plugin:view |
| DELETE /api/plugins/{id} | plugin:delete |
| POST /api/plugins/{id}/activate | plugin:manage |
| GET /api/users | user:view |
| POST /api/users | user:manage |
| PUT /api/users/{id} | user:edit |
| DELETE /api/users/{id} | user:delete |
| GET /api/roles | role:view |
| POST /api/roles | role:manage |
| PUT /api/roles/{id} | role:edit |
| DELETE /api/roles/{id} | role:delete |
| POST /api/backtest/run | backtest:run |
| GET /api/backtest/results | backtest:view |
| POST /api/qlib/select | selection:run |
| GET /api/qlib/models | selection:view |
| GET /api/holdings/{user_id} | holdings:view |
| POST /api/holdings/{user_id} | holdings:edit |
| GET /api/risk/reports | risk:view |
| GET /api/scheduler/jobs | scheduler:view |
| POST /api/scheduler/jobs | scheduler:manage |

### Requirement: System SHALL allow public endpoints

The system MUST NOT require authentication for public endpoints.

#### Scenario: Public access
- **WHEN** accessing public endpoints (login, health, docs)
- **THEN** no authentication is required

#### Scenario: Public endpoints list
- **THEN** following endpoints are public:
  - POST /api/auth/token
  - GET /api/health
  - GET /api/docs
  - GET /api/openapi.json
