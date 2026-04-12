# User Management Specification

## ADDED Requirements

### Requirement: System SHALL list users with pagination

The system MUST provide paginated user listing for users with user:view permission.

#### Scenario: List users
- **WHEN** GET /api/users is called with user:view permission
- **THEN** system returns array of users: {id, username, display_name, role_id, role_name, status, last_login}
- **AND** password_hash is NOT included in response

#### Scenario: Paginated results
- **WHEN** GET /api/users?page=2&page_size=20
- **THEN** system returns 20 users starting from 21st
- **AND** includes {items, total, page, page_size, total_pages}

#### Scenario: Filter by status
- **WHEN** GET /api/users?status=active
- **THEN** system returns only active users

#### Scenario: Filter by role
- **WHEN** GET /api/users?role_id=role_trader
- **THEN** system returns only users with that role

### Requirement: System SHALL create users

The system MUST allow users with user:manage permission to create new users.

#### Scenario: Create user
- **WHEN** POST /api/users with {username, password, display_name, role_id, status}
- **THEN** system hashes password
- **AND** creates user document in MongoDB
- **AND** returns user_id

#### Scenario: Duplicate username
- **WHEN** username already exists
- **THEN** system returns HTTP 409 conflict
- **AND** error message indicates "Username already exists"

#### Scenario: Invalid role
- **WHEN** role_id does not exist
- **THEN** system returns HTTP 400
- **AND** error message indicates "Invalid role_id"

#### Scenario: Create superuser
- **WHEN** attempting to create user with is_superuser=true
- **THEN** system rejects unless requester is superuser
- **AND** error message indicates "Only superuser can create superuser accounts"

### Requirement: System SHALL update users

The system MUST allow users with user:edit permission to update user information.

#### Scenario: Update user
- **WHEN** PUT /api/users/{id} with {display_name, role_id, status}
- **THEN** system updates user document
- **AND** updates updated_at timestamp
- **AND** returns success

#### Scenario: Update own status
- **WHEN** user attempts to change their own status
- **THEN** system returns HTTP 403
- **AND** error message indicates "Cannot modify own status"

#### Scenario: Update superuser
- **WHEN** non-superuser attempts to update superuser account
- **THEN** system returns HTTP 403
- **AND** error message indicates "Cannot modify superuser account"

### Requirement: System SHALL delete users

The system MUST allow users with user:delete permission to delete users.

#### Scenario: Delete user
- **WHEN** DELETE /api/users/{id}
- **THEN** system sets status to "deleted" (soft delete)
- **AND** returns success

#### Scenario: Delete superuser
- **WHEN** attempting to delete a superuser account
- **THEN** system returns HTTP 403
- **AND** error message indicates "Cannot delete superuser account"

#### Scenario: Delete self
- **WHEN** user attempts to delete their own account
- **THEN** system returns HTTP 403
- **AND** error message indicates "Cannot delete own account"

### Requirement: System SHALL reset passwords

The system MUST allow password reset for users with user:manage permission.

#### Scenario: Reset password
- **WHEN** POST /api/users/{id}/reset-password with {new_password}
- **THEN** system hashes new password
- **AND** updates password_hash
- **AND** returns success

#### Scenario: Reset own password forbidden
- **WHEN** user attempts to reset own password via this endpoint
- **THEN** system returns HTTP 400
- **AND** error message indicates "Use /api/auth/change-password for own password"
