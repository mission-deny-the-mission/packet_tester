## ADDED Requirements

### Requirement: Historical Data Retention
The system SHALL persist network metrics in a local database to allow for analysis across sessions and system restarts.

#### Scenario: Data survives restart
- **WHEN** the server is restarted
- **AND** the user reloads the dashboard
- **THEN** all previous targets and their historical charts SHALL be restored
