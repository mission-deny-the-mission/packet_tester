# ci-cd Specification

## Purpose
TBD - created by archiving change organize-packaging-and-ci. Update Purpose after archive.
## Requirements
### Requirement: Automated Testing Pipeline
The system SHALL execute automated tests on every push and pull request to the main branch.

#### Scenario: Test failure blocks merge
- **WHEN** a pull request contains failing tests
- **THEN** the CI status MUST be failing, indicating that it should not be merged.

### Requirement: Automated Container Publishing
The system SHALL automatically build and publish a Docker image to GitHub Container Registry (GHCR) upon successful merge to the main branch or on release.

#### Scenario: Image available in GHCR
- **WHEN** a new tag is pushed
- **THEN** a corresponding Docker image MUST be available in `ghcr.io`.

### Requirement: Automated Package Building
The system SHALL automatically build Debian and Pacman packages on release.

#### Scenario: Packages as release artifacts
- **WHEN** a GitHub release is created
- **THEN** the `.deb` and `.pkg.tar.zst` files MUST be attached to the release artifacts.

