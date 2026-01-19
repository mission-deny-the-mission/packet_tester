# Capability: Network Monitoring

## Purpose
To provide real-time visibility into network connectivity and performance for multiple targets simultaneously.
## Requirements
### Requirement: Concurrent Target Monitoring
The system SHALL allow users to monitor multiple IP addresses or domains simultaneously from a single dashboard.

#### Scenario: Adding multiple targets
- **WHEN** the user adds "8.8.8.8" as a target
- **AND** the user adds "google.com" as a target
- **THEN** both targets SHALL be monitored in parallel with independent stats and charts

### Requirement: Real-time Latency Tracking
The system SHALL provide a live line chart for each target showing the round-trip time (RTT) in milliseconds.

#### Scenario: Visualizing latency spikes
- **WHEN** a ping response is received with 150ms latency
- **THEN** the chart SHALL immediately update with a new data point at 150ms

### Requirement: Packet Loss Calculation
The system SHALL calculate and display the percentage of packet loss for each target based on the ratio of sent to received packets.

#### Scenario: Detecting loss
- **WHEN** 10 packets are sent but only 9 are received
- **THEN** the system SHALL display "10%" packet loss for that target

### Requirement: Historical Data Retention
The system SHALL persist network metrics in a local database to allow for analysis across sessions and system restarts.

#### Scenario: Data survives restart
- **WHEN** the server is restarted
- **AND** the user reloads the dashboard
- **THEN** all previous targets and their historical charts SHALL be restored

### Requirement: Diagnostic Snapshot Export
The system SHALL allow users to export the current state of a monitor card as an image for sharing and documentation.

#### Scenario: Capturing evidence of loss
- **WHEN** the user clicks the "Snapshot" button on a target card
- **THEN** an image file (PNG) containing the charts and path analysis table SHALL be downloaded

