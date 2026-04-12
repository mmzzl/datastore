# Plugin Management Specification

## ADDED Requirements

### Requirement: System SHALL list all plugins

The system MUST provide an endpoint to retrieve all uploaded plugins with their versions.

#### Scenario: List plugins
- **WHEN** GET /api/plugins is called
- **THEN** system returns array of plugins with: {id, name, version, display_name, description, status, created_at}
- **AND** each plugin includes all available versions

#### Scenario: List with pagination
- **WHEN** GET /api/plugins?page=2&page_size=10 is called
- **THEN** system returns 10 plugins starting from 11th
- **AND** includes total count and page info

#### Scenario: Filter by status
- **WHEN** GET /api/plugins?status=active is called
- **THEN** system returns only plugins with status "active"

### Requirement: System SHALL provide plugin details

The system MUST return detailed information about a specific plugin.

#### Scenario: Get plugin detail
- **WHEN** GET /api/plugins/{id} is called
- **THEN** system returns full plugin info: {id, name, version, manifest, path, parameters, author, tags}
- **AND** includes available versions list

#### Scenario: Plugin not found
- **WHEN** GET /api/plugins/nonexistent_id is called
- **THEN** system returns HTTP 404
- **AND** error message indicates "Plugin not found"

### Requirement: System SHALL allow plugin deletion

The system MUST allow users with plugin:delete permission to remove plugins.

#### Scenario: Delete plugin
- **WHEN** DELETE /api/plugins/{id} is called with plugin:delete permission
- **THEN** system removes plugin directory from filesystem
- **AND** removes all versions from MongoDB
- **AND** returns success message

#### Scenario: Delete without permission
- **WHEN** user without plugin:delete permission attempts deletion
- **THEN** system returns HTTP 403
- **AND** error message indicates "Missing permission: plugin:delete"

#### Scenario: Delete in-use plugin
- **WHEN** attempting to delete plugin that is being used in a running backtest
- **THEN** system returns HTTP 409 conflict
- **AND** error message indicates "Cannot delete plugin in use"

### Requirement: System SHALL allow version switching

The system MUST allow users to activate different versions of the same plugin.

#### Scenario: Activate different version
- **WHEN** POST /api/plugins/{id}/activate with {version: "1.1.0"} is called
- **THEN** system sets version 1.1.0 as active
- **AND** previous active version becomes inactive
- **AND** returns success message

#### Scenario: Activate non-existent version
- **WHEN** attempting to activate version that doesn't exist
- **THEN** system returns HTTP 404
- **AND** error message indicates "Version not found"

#### Scenario: Activate without permission
- **WHEN** user without plugin:manage permission attempts activation
- **THEN** system returns HTTP 403
- **AND** error message indicates "Missing permission: plugin:manage"

### Requirement: System SHALL require view permission

The system MUST check permission for plugin listing and details.

#### Scenario: User with view permission
- **WHEN** user has "plugin:view" permission
- **THEN** system returns plugin list/details

#### Scenario: User without view permission
- **WHEN** user does not have "plugin:view" permission
- **THEN** system returns HTTP 403
- **AND** error message indicates "Missing permission: plugin:view"
