# Implementation Tasks

## 1. Backend - User Model and Storage

- [ ] 1.1 Create `app/user/__init__.py`
- [ ] 1.2 Create `app/user/models.py` with User dataclass
- [ ] 1.3 Add password hashing utilities using bcrypt
- [ ] 1.4 Add MongoDB users collection handling in MongoStorage
- [ ] 1.5 Add MongoDB roles collection handling in MongoStorage
- [ ] 1.6 Create MongoDB indexes for users and roles collections
- [ ] 1.7 Write unit tests for User model and password hashing

## 2. Backend - Role Model and Permissions

- [ ] 2.1 Create `app/role/__init__.py`
- [ ] 2.2 Create `app/role/models.py` with Role dataclass
- [ ] 2.3 Define permission constants in `app/core/permissions.py`
- [ ] 2.4 Create `require_permission()` dependency function
- [ ] 2.5 Create `get_current_user()` dependency function
- [ ] 2.6 Write unit tests for Role model and permission checking

## 3. Backend - System Initialization

- [ ] 3.1 Add default_admin config to Settings class
- [ ] 3.2 Create `app/core/init_db.py` for database initialization
- [ ] 3.3 Implement create_default_roles() function
- [ ] 3.4 Implement create_default_admin() function
- [ ] 3.5 Add initialization to FastAPI startup event
- [ ] 3.6 Write integration tests for system initialization

## 4. Backend - Authentication API

- [ ] 4.1 Update `app/api/endpoints/auth.py` for MongoDB authentication
- [ ] 4.2 Implement POST /api/auth/token endpoint
- [ ] 4.3 Implement POST /api/auth/logout endpoint
- [ ] 4.4 Implement POST /api/auth/change-password endpoint
- [ ] 4.5 Implement GET /api/auth/me endpoint
- [ ] 4.6 Update JWT payload to include role_id and permissions
- [ ] 4.7 Update auth middleware to support new user model
- [ ] 4.8 Write API tests for authentication endpoints

## 5. Backend - User Management API

- [ ] 5.1 Create `app/api/endpoints/users.py`
- [ ] 5.2 Implement GET /api/users with pagination
- [ ] 5.3 Implement POST /api/users
- [ ] 5.4 Implement PUT /api/users/{id}
- [ ] 5.5 Implement DELETE /api/users/{id}
- [ ] 5.6 Implement POST /api/users/{id}/reset-password
- [ ] 5.7 Add permission checks to all user endpoints
- [ ] 5.8 Write API tests for user management endpoints

## 6. Backend - Role Management API

- [ ] 6.1 Create `app/api/endpoints/roles.py`
- [ ] 6.2 Implement GET /api/roles
- [ ] 6.3 Implement GET /api/roles/permissions
- [ ] 6.4 Implement POST /api/roles
- [ ] 6.5 Implement PUT /api/roles/{id}
- [ ] 6.6 Implement DELETE /api/roles/{id}
- [ ] 6.7 Add permission checks to all role endpoints
- [ ] 6.8 Write API tests for role management endpoints

## 7. Backend - Plugin Validator

- [ ] 7.1 Create `app/backtest/plugin/__init__.py`
- [ ] 7.2 Create `app/backtest/plugin/validator.py`
- [ ] 7.3 Implement validate_zip_structure() function
- [ ] 7.4 Implement validate_manifest_schema() function
- [ ] 7.5 Implement validate_code_ast() function (forbidden imports check)
- [ ] 7.6 Implement validate_strategy_class() function
- [ ] 7.7 Implement check_version_rules() function
- [ ] 7.8 Write unit tests for plugin validator

## 8. Backend - Plugin Loader and Registry

- [ ] 8.1 Create `app/backtest/plugin/loader.py`
- [ ] 8.2 Implement load_plugin_module() function
- [ ] 8.3 Implement create_strategy_instance() function
- [ ] 8.4 Create `app/backtest/plugin/registry.py`
- [ ] 8.5 Implement PluginRegistry class with register/unregister/list methods
- [ ] 8.6 Add strategy_plugins and plugin_versions collection handling
- [ ] 8.7 Write unit tests for plugin loader and registry

## 9. Backend - Plugin Management API

- [ ] 9.1 Create `app/api/endpoints/plugins.py`
- [ ] 9.2 Implement POST /api/plugins/upload
- [ ] 9.3 Implement GET /api/plugins with pagination
- [ ] 9.4 Implement GET /api/plugins/{id}
- [ ] 9.5 Implement DELETE /api/plugins/{id}
- [ ] 9.6 Implement POST /api/plugins/{id}/activate
- [ ] 9.7 Add permission checks to all plugin endpoints
- [ ] 9.8 Write API tests for plugin management endpoints

## 10. Backend - Unified Action Runner

- [ ] 10.1 Create `app/action/__init__.py`
- [ ] 10.2 Create `app/action/runner.py` with ActionRunner class
- [ ] 10.3 Implement run_action() method
- [ ] 10.4 Implement _run_backtest() handler
- [ ] 10.5 Implement _run_selection() handler
- [ ] 10.6 Implement _validate_plugin() handler
- [ ] 10.7 Add action_logs collection handling
- [ ] 10.8 Create POST /api/action/run endpoint
- [ ] 10.9 Write unit tests for ActionRunner

## 11. Backend - Update Existing APIs

- [ ] 11.1 Add permission checks to backtest endpoints
- [ ] 11.2 Add plugin strategy support to backtest
- [ ] 11.3 Add permission checks to qlib/select endpoint
- [ ] 11.4 Add plugin strategy support to stock selection
- [ ] 11.5 Add permission checks to holdings endpoints
- [ ] 11.6 Add permission checks to risk report endpoints
- [ ] 11.7 Add permission checks to scheduler endpoints
- [ ] 11.8 Add permission checks to dingtalk endpoints
- [ ] 11.9 Update API tests for permission changes

## 12. Frontend - API Services

- [ ] 12.1 Create `src/services/api_auth.ts`
- [ ] 12.2 Create `src/services/api_users.ts`
- [ ] 12.3 Create `src/services/api_roles.ts`
- [ ] 12.4 Create `src/services/api_plugins.ts`
- [ ] 12.5 Create `src/services/api_action.ts`
- [ ] 12.6 Update existing API services for permission handling

## 13. Frontend - Auth Store

- [ ] 13.1 Create `src/stores/auth.ts` with user/role/permission state
- [ ] 13.2 Implement login/logout actions
- [ ] 13.3 Implement permission checking helpers (hasPermission, hasAnyPermission)
- [ ] 13.4 Update LoginView to use new auth store
- [ ] 13.5 Add router navigation guards for permission checking

## 14. Frontend - User Management Page

- [ ] 14.1 Create `src/views/UserManagementView.vue`
- [ ] 14.2 Implement user list table with pagination
- [ ] 14.3 Implement create user modal form
- [ ] 14.4 Implement edit user modal
- [ ] 14.5 Implement delete confirmation dialog
- [ ] 14.6 Implement reset password functionality
- [ ] 14.7 Add permission checks (only show if user:view)
- [ ] 14.8 Add route: /admin/users

## 15. Frontend - Role Management Page

- [ ] 15.1 Create `src/views/RoleManagementView.vue`
- [ ] 15.2 Implement role list table
- [ ] 15.3 Implement permission checkbox panel (grouped by resource)
- [ ] 15.4 Implement create role modal
- [ ] 15.5 Implement edit role modal
- [ ] 15.6 Implement delete confirmation (with user count check)
- [ ] 15.7 Add permission checks (only show if role:view)
- [ ] 15.8 Add route: /admin/roles

## 16. Frontend - Plugin Management Page

- [ ] 16.1 Create `src/views/PluginManagementView.vue`
- [ ] 16.2 Implement plugin list table with version info
- [ ] 16.3 Implement ZIP file upload component
- [ ] 16.4 Implement upload progress indicator
- [ ] 16.5 Implement plugin detail modal
- [ ] 16.6 Implement version switching dropdown
- [ ] 16.7 Implement delete plugin functionality
- [ ] 16.8 Add permission checks (only show if plugin:view)
- [ ] 16.9 Add route: /plugins

## 17. Frontend - Update Backtest Page

- [ ] 17.1 Update BacktestView to load plugin list
- [ ] 17.2 Add "Plugin" strategy option to dropdown
- [ ] 17.3 Implement plugin selector dropdown (when plugin chosen)
- [ ] 17.4 Implement dynamic parameter form from plugin manifest
- [ ] 17.5 Update api_backtest.ts to support plugin strategy

## 18. Frontend - Update Stock Selection Page

- [ ] 18.1 Update QlibSelectView to support plugin strategies
- [ ] 18.2 Add plugin strategy option
- [ ] 18.3 Implement plugin parameter configuration
- [ ] 18.4 Update api_qlib.ts for plugin support

## 19. Frontend - Navigation Updates

- [ ] 19.1 Update sidebar navigation to show admin menu (if permission)
- [ ] 19.2 Add Users menu item (if user:view)
- [ ] 19.3 Add Roles menu item (if role:view)
- [ ] 19.4 Add Plugins menu item (if plugin:view)
- [ ] 19.5 Hide unauthorized menu items

## 20. Integration Testing

- [ ] 20.1 Test: System initialization creates default admin
- [ ] 20.2 Test: Login with default admin
- [ ] 20.3 Test: Create new user with role
- [ ] 20.4 Test: Login with new user and verify permissions
- [ ] 20.5 Test: Upload plugin with validation
- [ ] 20.6 Test: Run backtest with plugin strategy
- [ ] 20.7 Test: Permission denied for unauthorized access
- [ ] 20.8 Test: Version management (upload same plugin different versions)
- [ ] 20.9 Test: Unified action runner execution

## 21. Documentation

- [ ] 21.1 Update API documentation for new endpoints
- [ ] 21.2 Document plugin standard (manifest.json schema)
- [ ] 21.3 Document permission system
- [ ] 21.4 Write user guide for plugin upload
- [ ] 21.5 Write admin guide for user/role management
- [ ] 21.6 Update setup guide with initialization steps

## 22. Deployment

- [ ] 22.1 Add bcrypt to requirements.txt
- [ ] 22.2 Add python-multipart to requirements.txt (if not present)
- [ ] 22.3 Create database migration script (for existing installations)
- [ ] 22.4 Update AGENTS.md with new build/test commands
- [ ] 22.5 Create rollback script
