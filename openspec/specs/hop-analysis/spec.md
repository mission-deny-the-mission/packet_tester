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
The system SHALL highlight hops experiencing packet loss to assist in identifying network bottlenecks.

#### Scenario: Highlighting lossy hops
- **WHEN** a hop has a packet loss greater than 0%
- **THEN** that hop's row in the table SHALL be highlighted in red
