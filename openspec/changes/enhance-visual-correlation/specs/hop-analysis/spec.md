## MODIFIED Requirements

### Requirement: Visual Path Diagnostics
The system SHALL display a table of all hops with real-time stats and visual timelines to assist in identifying where network bottlenecks begin.

#### Scenario: Correlating spikes across hops
- **WHEN** Hop 4 experiences a latency spike
- **THEN** its sparkline SHALL show the spike
- **AND** the destination sparkline SHALL show a corresponding spike at the same vertical alignment
