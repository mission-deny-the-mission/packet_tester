# Capability: Network Monitoring

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
