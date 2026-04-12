# Scheduler Management Specification

## ADDED Requirements

### Requirement: System SHALL provide CRUD APIs for scheduled jobs

The system MUST implement REST API endpoints for creating, reading, updating, and deleting scheduled jobs.

#### Scenario: List all scheduled jobs
- **WHEN** GET /api/scheduler/jobs is called
- **THEN** system returns array of all configured jobs
- **AND** each job includes: {job_id, name, job_type, cron_expression, enabled, last_run, next_run, status}

#### Scenario: Create new scheduled job
- **WHEN** POST /api/scheduler/jobs is called with {name: "Weekly Qlib Training", job_type: "qlib_train", cron_expression: "0 2 * * 0", config: {...}, enabled: true}
- **THEN** system creates new job entry in MongoDB scheduler_jobs collection
- **AND** schedules job using APScheduler
- **AND** returns job_id

#### Scenario: Update scheduled job
- **WHEN** PUT /api/scheduler/jobs/{job_id} is called with updated configuration
- **THEN** system updates job in MongoDB
- **AND** reschedules job with new cron expression
- **AND** returns updated job details

#### Scenario: Delete scheduled job
- **WHEN** DELETE /api/scheduler/jobs/{job_id} is called
- **THEN** system removes job from APScheduler
- **AND** marks job as deleted in MongoDB (soft delete)
- **AND** returns success status

#### Scenario: Enable/disable job
- **WHEN** PUT /api/scheduler/jobs/{job_id} is called with {enabled: false}
- **THEN** system pauses job in APScheduler
- **AND** updates job status to "disabled"

### Requirement: System SHALL support multiple job types

The system MUST support different job types: qlib_train, backtest, risk_report, news_collect, custom.

#### Scenario: Create qlib_train job
- **WHEN** POST /api/scheduler/jobs with job_type: "qlib_train"
- **THEN** system validates qlib-specific config: {stock_pool, model_type, factors}
- **AND** schedules training job

#### Scenario: Create backtest job
- **WHEN** POST /api/scheduler/jobs with job_type: "backtest"
- **THEN** system validates backtest-specific config: {strategy, start_date, end_date, initial_capital}
- **AND** schedules backtest job

#### Scenario: Invalid job type
- **WHEN** POST /api/scheduler/jobs with unsupported job_type
- **THEN** system returns HTTP 400 error
- **AND** error message lists valid job types

### Requirement: System SHALL track job execution history

The system MUST record each job execution with start time, end time, status, and results.

#### Scenario: Record successful execution
- **WHEN** scheduled job completes successfully
- **THEN** system saves execution record to job_executions collection: {job_id, started_at, completed_at, status: "success", result: {...}}

#### Scenario: Record failed execution
- **WHEN** scheduled job fails
- **THEN** system saves execution record with status: "failed", error_message

#### Scenario: Retrieve execution history
- **WHEN** GET /api/scheduler/jobs/{job_id}/executions is called
- **THEN** system returns paginated execution history
- **AND** ordered by started_at descending

### Requirement: System SHALL allow manual job triggering

The system MUST provide endpoint to manually trigger scheduled jobs without waiting for cron schedule.

#### Scenario: Trigger job immediately
- **WHEN** POST /api/scheduler/jobs/{job_id}/trigger is called
- **THEN** system executes job immediately
- **AND** returns execution_id for tracking
- **AND** does not affect next scheduled run

#### Scenario: Trigger disabled job
- **WHEN** POST /api/scheduler/jobs/{job_id}/trigger is called for disabled job
- **THEN** system executes job once despite being disabled
- **AND** logs execution

### Requirement: System SHALL validate cron expressions

The system MUST validate cron expressions and provide human-readable descriptions.

#### Scenario: Valid cron expression
- **WHEN** POST /api/scheduler/jobs with valid cron_expression: "0 2 * * 0"
- **THEN** system accepts and schedules job
- **AND** returns human-readable description: "Every Sunday at 02:00"

#### Scenario: Invalid cron expression
- **WHEN** POST /api/scheduler/jobs with invalid cron_expression
- **THEN** system returns HTTP 400 error
- **AND** error message indicates invalid syntax

### Requirement: Frontend SHALL provide scheduler management page

The frontend MUST display scheduler jobs in a table with create/edit/delete functionality.

#### Scenario: Display job list
- **WHEN** user navigates to /scheduler
- **THEN** page shows table of all scheduled jobs
- **AND** columns: Name, Type, Schedule, Enabled, Last Run, Next Run, Status, Actions

#### Scenario: Create job form
- **WHEN** user clicks "New Job" button
- **THEN** modal opens with job creation form
- **AND** form fields: Name, Job Type (dropdown), Cron Expression, Config (JSON editor), Enabled checkbox

#### Scenario: Edit job
- **WHEN** user clicks "Edit" button on job row
- **THEN** modal opens pre-filled with job details
- **AND** user can modify and save

#### Scenario: Delete job confirmation
- **WHEN** user clicks "Delete" button
- **THEN** confirmation dialog appears
- **AND** job is deleted only after confirmation

### Requirement: System SHALL support timezone configuration

The system MUST allow specifying timezone for cron schedules.

#### Scenario: Configure job timezone
- **WHEN** creating job with timezone: "Asia/Shanghai"
- **THEN** cron schedule is interpreted in that timezone
- **AND** next_run time is shown in that timezone

### Requirement: System SHALL prevent concurrent execution of same job

The system MUST prevent multiple instances of the same job from running simultaneously.

#### Scenario: Job already running
- **WHEN** scheduled time arrives but previous execution is still running
- **THEN** system skips this execution
- **AND** logs "Job already running, skipping"
- **AND** records skipped execution
