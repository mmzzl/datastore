# DingTalk Configuration Specification

## ADDED Requirements

### Requirement: System SHALL provide API for DingTalk webhook configuration

The system MUST implement REST API endpoints for managing DingTalk webhook and secret settings.

#### Scenario: Get DingTalk configuration
- **WHEN** GET /api/dingtalk/config is called for authenticated user
- **THEN** system returns DingTalk configuration: {webhook_url: string (masked), secret: string (masked), enabled: boolean, created_at, updated_at}
- **AND** sensitive fields are partially masked (e.g., "https://oapi.dingtalk.com/...***abc")

#### Scenario: Create DingTalk configuration
- **WHEN** POST /api/dingtalk/config is called with {webhook_url: "...", secret: "..."}
- **THEN** system saves configuration to MongoDB dingtalk_configs collection
- **AND** associates with authenticated user
- **AND** sets enabled: true by default
- **AND** returns success status

#### Scenario: Update DingTalk configuration
- **WHEN** PUT /api/dingtalk/config is called with updated fields
- **THEN** system updates configuration in MongoDB
- **AND** updates updated_at timestamp
- **AND** returns updated configuration (masked)

#### Scenario: Delete DingTalk configuration
- **WHEN** DELETE /api/dingtalk/config is called
- **THEN** system marks configuration as deleted (soft delete)
- **AND** disables all DingTalk notifications for user

### Requirement: System SHALL validate DingTalk webhook format

The system MUST validate webhook URL format and test connectivity.

#### Scenario: Valid webhook URL
- **WHEN** POST /api/dingtalk/config with webhook_url matching "https://oapi.dingtalk.com/robot/send?access_token=*"
- **THEN** system accepts configuration
- **AND** validates URL structure

#### Scenario: Invalid webhook URL
- **WHEN** POST /api/dingtalk/config with malformed webhook_url
- **THEN** system returns HTTP 400 error
- **AND** error message indicates invalid webhook format

### Requirement: System SHALL provide test notification endpoint

The system MUST allow users to test DingTalk configuration by sending a test message.

#### Scenario: Send test notification
- **WHEN** POST /api/dingtalk/test is called
- **THEN** system sends test message: "DingTalk configuration test - [timestamp]"
- **AND** returns success status if message sent
- **AND** returns HTTP 400 with error details if sending fails

#### Scenario: Test without configuration
- **WHEN** POST /api/dingtalk/test is called but no configuration exists
- **THEN** system returns HTTP 400 error
- **AND** error message indicates configuration not found

### Requirement: System SHALL enable/disable DingTalk notifications

The system MUST allow toggling DingTalk notifications without deleting configuration.

#### Scenario: Disable notifications
- **WHEN** PUT /api/dingtalk/config with {enabled: false}
- **THEN** system stops sending DingTalk notifications
- **AND** keeps configuration for future re-enable

#### Scenario: Re-enable notifications
- **WHEN** PUT /api/dingtalk/config with {enabled: true}
- **THEN** system resumes sending DingTalk notifications
- **AND** next scheduled notification is sent

### Requirement: System SHALL secure DingTalk credentials

The system MUST encrypt DingTalk webhook and secret in MongoDB.

#### Scenario: Encrypt on save
- **WHEN** DingTalk configuration is saved
- **THEN** webhook_url and secret are encrypted using application secret key
- **AND** only decrypted when sending notifications

#### Scenario: Mask in API response
- **WHEN** GET /api/dingtalk/config is called
- **THEN** sensitive fields are masked in response
- **AND** full webhook/secret never exposed via API

### Requirement: Frontend SHALL provide DingTalk configuration page

The frontend MUST display a dedicated page for DingTalk configuration with test functionality.

#### Scenario: Display configuration form
- **WHEN** user navigates to /dingtalk-config
- **THEN** page shows form with fields: Webhook URL, Secret, Enabled checkbox
- **AND** if configuration exists, fields are pre-filled with masked values

#### Scenario: Save configuration
- **WHEN** user fills form and clicks "Save"
- **THEN** frontend calls POST or PUT /api/dingtalk/config
- **AND** shows success message on completion

#### Scenario: Test configuration
- **WHEN** user clicks "Test Notification" button
- **THEN** frontend calls POST /api/dingtalk/test
- **AND** shows success/error message based on result

#### Scenario: Toggle notifications
- **WHEN** user toggles "Enabled" checkbox
- **THEN** frontend calls PUT /api/dingtalk/config with new enabled value
- **AND** updates UI to reflect new state

### Requirement: System SHALL send DingTalk notifications for critical events

The system MUST send DingTalk notifications for: training completion, training failure, risk threshold breach, scheduled job failure.

#### Scenario: Training completion notification
- **WHEN** Qlib model training completes successfully
- **THEN** system sends DingTalk message: "✅ Model training completed: [model_id], Sharpe: [value]"
- **AND** includes link to view model details

#### Scenario: Training failure notification
- **WHEN** Qlib model training fails
- **THEN** system sends DingTalk message: "❌ Model training failed: [error summary]"
- **AND** includes suggestion to check logs

#### Scenario: Risk threshold breach notification
- **WHEN** daily risk report shows VaR > 5%
- **THEN** system sends DingTalk message: "⚠️ Risk threshold exceeded: Portfolio VaR at [value]%"
- **AND** includes top recommendations

### Requirement: System SHALL support multiple DingTalk configurations (future)

The system SHOULD be designed to support multiple DingTalk webhooks for different notification types.

#### Scenario: Single configuration (current implementation)
- **WHEN** DingTalk configuration is saved
- **THEN** only one active configuration per user
- **AND** all notifications go to single webhook

#### Scenario: Multiple configurations (future enhancement)
- **WHEN** system is enhanced to support multiple webhooks
- **THEN** each notification type can have separate webhook
- **AND** backward compatible with existing single configuration
