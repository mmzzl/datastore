# Role Management Specification

## ADDED Requirements

### Requirement: System SHALL list roles

The system MUST provide role listing for users with role:view permission.

#### Scenario: List roles
- **WHEN** GET /api/roles is called with role:view permission
- **THEN** system returns array of roles: {id, role_id, name, description, permissions, is_system, user_count}

#### Scenario: Include user count
- **WHEN** listing roles
- **THEN** each role includes count of users assigned to it

### Requirement: System SHALL create roles

The system MUST allow role:manage permission to create new roles.

#### Scenario: Create role
- **WHEN** POST /api/roles with {name, description, permissions}
- **THEN** system generates unique role_id
- **AND** creates role document in MongoDB
- **AND** sets is_system=false
- **AND** returns role_id

#### Scenario: Invalid permission
- **WHEN** permissions array contains invalid permission string
- **THEN** system returns HTTP 400
- **AND** error message lists valid permissions

#### Scenario: Duplicate role name
- **WHEN** role name already exists
- **THEN** system returns HTTP 409
- **AND** error message indicates "Role name already exists"

### Requirement: System SHALL update roles

The system MUST allow role:edit permission to update role information.

#### Scenario: Update role
- **WHEN** PUT /api/roles/{role_id} with {name, description, permissions}
- **THEN** system updates role document
- **AND** returns success

#### Scenario: Update system role
- **WHEN** attempting to modify system role (is_system=true)
- **THEN** only description can be changed
- **AND** permissions change returns HTTP 403
- **AND** error message indicates "Cannot modify system role permissions"

#### Scenario: Update role in use
- **WHEN** role has assigned users
- **THEN** update still proceeds
- **AND** users need to re-login for changes to take effect

### Requirement: System SHALL delete roles

The system MUST allow role:delete permission to delete non-system roles.

#### Scenario: Delete role
- **WHEN** DELETE /api/roles/{role_id} on non-system role
- **THEN** system removes role from MongoDB
- **AND** returns success

#### Scenario: Delete system role
- **WHEN** attempting to delete system role (is_system=true)
- **THEN** system returns HTTP 403
- **AND** error message indicates "Cannot delete system role"

#### Scenario: Delete role with users
- **WHEN** role has assigned users
- **THEN** system returns HTTP 409
- **AND** error message indicates "Cannot delete role with assigned users"
- **AND** suggests reassigning users first

### Requirement: System SHALL define system roles

The system MUST pre-define system roles during initialization.

#### Scenario: System roles created
- **WHEN** system initializes
- **THEN** following roles are created:
  - role_superuser: "超级管理员" - all permissions (*)
  - role_admin: "管理员" - user:*, role:*, plugin:*, system:*
  - role_trader: "交易员" - backtest:*, selection:*, holdings:*, risk:view
  - role_viewer: "观察者" - *:view permissions only

### Requirement: System SHALL provide permission list

The system MUST provide endpoint to list all valid permissions.

#### Scenario: List permissions
- **WHEN** GET /api/roles/permissions
- **THEN** system returns list of valid permissions grouped by resource:
  ```json
  {
    "user": ["view", "edit", "delete", "manage"],
    "role": ["view", "edit", "delete", "manage"],
    "plugin": ["view", "upload", "delete", "manage"],
    ...
  }
  ```
