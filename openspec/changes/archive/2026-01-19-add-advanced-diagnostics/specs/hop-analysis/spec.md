## ADDED Requirements

### Requirement: Hop Enrichment (ISP/Geo)
The system SHALL identify the owner (ISP) and approximate geographic location for each identified hop in the path.

#### Scenario: Identifying external bottlenecks
- **WHEN** a hop IP is discovered
- **THEN** the system SHALL asynchronously fetch and display the ISP name (e.g., "Level3", "Comcast") and location
