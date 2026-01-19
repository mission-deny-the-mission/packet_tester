# Design: Packaging and CI/CD Organization

## Context
The packet_tester application needs to be distributed as a service on various Linux distributions. It relies on `ping` and `tracepath` and runs as a Flask-SocketIO server.

## Goals
- Provide a consistent way to run the application as a systemd service.
- Automate the build process for Docker, Debian, and Pacman packages.
- Ensure all changes are verified by unit tests before packaging.

## Decisions
- **Packaging Directory**: A new `packaging/` directory will house package-specific files (control files, PKGBUILD, etc.).
- **Systemd Unit**: A shared `packet-tester.service` will be used for both Debian and Arch Linux packages.
- **Docker**: A multi-stage build or a simple lightweight Alpine/Debian-based image. Since we need `ping` and `tracepath`, a Debian-based image (like `python:3.14-slim`) is preferred for better compatibility with these tools.
- **GitHub Actions**:
  - `test.yml`: Runs `pytest`.
  - `docker-publish.yml`: Builds and pushes to GHCR.
  - `build-packages.yml`: Uses `nfpm` (for deb) and a custom action/script for `makepkg`.

## Risks / Trade-offs
- **Permissions**: The application needs `CAP_NET_RAW` or to run as root for certain ping operations. The systemd unit and Docker container must be configured to handle this safely.
- **Maintenance**: Adding multiple package formats increases maintenance overhead.

## Migration Plan
1. Create the `packaging/` structure and systemd service.
2. Implement Dockerfile.
3. Set up GitHub Actions for testing.
4. Set up GitHub Actions for packaging.
