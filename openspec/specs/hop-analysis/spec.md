# Capability: Hop Analysis

## Purpose
To discover and analyze the network path to a destination, identifying specific routers and monitoring their individual performance to isolate bottlenecks.
## Requirements
### Requirement: Path Discovery
The system SHALL identify all intermediate hops (routers) between the local host and the destination target using ICMP TTL expiration.

#### Scenario: Successful path discovery
- **WHEN** a new target is added
- **THEN** the system SHALL list all responding intermediate IP addresses in order

### Requirement: Continuous Hop Probing
The system SHALL probe each identified hop at regular intervals to determine its specific latency and packet loss.

#### Scenario: Per-hop metrics
- **WHEN** Hop 3 is probed
- **THEN** its current average latency and packet loss percentage SHALL be updated in the path analysis table

### Requirement: Visual Path Diagnostics
The system SHALL display a table of all hops with real-time stats and visual timelines to assist in identifying where network bottlenecks begin.

#### Scenario: Correlating spikes across hops
- **WHEN** Hop 4 experiences a latency spike
- **THEN** its sparkline SHALL show the spike
- **AND** the destination sparkline SHALL show a corresponding spike at the same vertical alignment

### Requirement: Hop Enrichment (ISP/Geo)
The system SHALL identify the owner (ISP) and approximate geographic location for each identified hop in the path.

#### Scenario: Identifying external bottlenecks
- **WHEN** a hop IP is discovered
- **THEN** the system SHALL asynchronously fetch and display the ISP name (e.g., "Level3", "Comcast") and location

