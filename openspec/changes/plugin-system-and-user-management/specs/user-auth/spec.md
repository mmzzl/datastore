# User Authentication Specification

## ADDED Requirements

### Requirement: System SHALL authenticate users from MongoDB

The system MUST verify user credentials against the users collection in MongoDB.

#### Scenario: Successful login
- **WHEN** user submits correct username and password
- **THEN** system verifies password hash using bcrypt
- **AND** generates JWT token with {sub, username, role_id, permissions, is_superuser}
- **AND** returns token with 200 status

#### Scenario: Invalid credentials
- **WHEN** user submits incorrect password
- **THEN** system returns HTTP 401
- **AND** error message indicates "Invalid credentials"
- **AND** login attempt is logged

#### Scenario: User not found
- **WHEN** username does not exist in database
- **THEN** system returns HTTP 401
- **AND** error message indicates "Invalid credentials"

#### Scenario: Disabled user
- **WHEN** user status is "disabled"
- **THEN** system returns HTTP 403
- **AND** error message indicates "Account is disabled"

#### Scenario: Locked user
- **WHEN** user status is "locked"
- **THEN** system returns HTTP 403
- **AND** error message indicates "Account is locked"

### Requirement: System SHALL store password securely

The system MUST hash passwords using bcrypt before storage.

#### Scenario: Password hashing
- **WHEN** user is created or password is changed
- **THEN** system hashes password with bcrypt (rounds=12)
- **AND** stores only the hash in password_hash field

#### Scenario: Password verification
- **WHEN** user logs in
- **THEN** system compares submitted password with stored hash using bcrypt.checkpw()
- **AND** does NOT store plaintext password

### Requirement: System SHALL allow password change

The system MUST allow authenticated users to change their own password.

#### Scenario: Change own password
- **WHEN** POST /api/auth/change-password with {old_password, new_password}
- **THEN** system verifies old_password
- **AND** hashes new_password
- **AND** updates password_hash in database
- **AND** returns success message

#### Scenario: Wrong old password
- **WHEN** old_password is incorrect
- **THEN** system returns HTTP 401
- **AND** error message indicates "Current password is incorrect"

#### Scenario: New password same as old
- **WHEN** new_password equals old_password
- **THEN** system returns HTTP 400
- **AND** error message indicates "New password must be different"

### Requirement: System SHALL allow logout

The system MUST provide logout endpoint (optional token invalidation).

#### Scenario: Logout
- **WHEN** POST /api/auth/logout is called
- **THEN** system returns success
- **AND** client clears token from storage

### Requirement: System SHALL return user info

The system MUST provide endpoint to get current user information.

#### Scenario: Get current user
- **WHEN** GET /api/auth/me is called with valid token
- **THEN** system returns {username, display_name, role, permissions, is_superuser}

#### Scenario: Invalid token
- **WHEN** token is expired or invalid
- **THEN** system returns HTTP 401
- **AND** error message indicates "Invalid or expired token"
