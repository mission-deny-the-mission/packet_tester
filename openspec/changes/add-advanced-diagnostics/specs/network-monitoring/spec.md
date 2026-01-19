## ADDED Requirements

### Requirement: Jitter Calculation
The system SHALL calculate the variation in latency (jitter) for each target to measure connection stability.

#### Scenario: Displaying jitter
- **WHEN** ping latencies vary significantly (e.g., 20ms, 80ms, 15ms)
- **THEN** the system SHALL display the calculated jitter in milliseconds

### Requirement: Quality Scoring (MOS)
The system SHALL provide a Mean Opinion Score (MOS) between 1.0 and 5.0 to represent the estimated quality of the connection for real-time applications.

#### Scenario: Poor connection score
- **WHEN** packet loss is high or jitter is extreme
- **THEN** the MOS SHALL drop below 3.0 to indicate a poor quality connection
