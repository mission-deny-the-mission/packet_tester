## ADDED Requirements

### Requirement: Docker Support
The system SHALL provide a `Dockerfile` that builds a containerized version of the packet_tester application.

#### Scenario: Successful Docker build
- **WHEN** the user runs `docker build -t packet_tester .`
- **THEN** a Docker image is successfully created containing all dependencies and the application code.

### Requirement: Debian Packaging
The system SHALL provide configuration for building a `.deb` package.

#### Scenario: Deb package contents
- **WHEN** the Debian package is built
- **THEN** it MUST include the application code, dependencies (via requirements), and the systemd unit file.

### Requirement: Arch Linux Packaging
The system SHALL provide a `PKGBUILD` for Arch Linux (Pacman).

#### Scenario: PKGBUILD validity
- **WHEN** `makepkg` is executed in the Arch packaging directory
- **THEN** it MUST produce a valid `.pkg.tar.zst` file.

### Requirement: Systemd Integration
The system SHALL provide a systemd unit file to manage the application as a service.

#### Scenario: Service management
- **WHEN** the service is installed
- **THEN** it SHALL be manageable via `systemctl start|stop|restart packet-tester.service`.
