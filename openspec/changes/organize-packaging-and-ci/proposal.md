# Change: Organize Packaging and CI/CD

## Why
The project lacks formal distribution mechanisms and automated verification. Providing Docker containers, Debian packages, and Pacman packages ensures easy deployment across different Linux environments. Integrating these into GitHub Actions automates quality assurance and distribution.

## What Changes
- Add `Dockerfile` and `.dockerignore` for containerization.
- Add `packaging/` directory containing configurations for `deb` and `pacman`.
- Add `packet-tester.service` systemd unit file.
- Add GitHub Actions workflows in `.github/workflows/` for:
  - Running unit tests on every push/PR.
  - Building and pushing Docker images to GitHub Packages (GHCR).
  - Building `.deb` and `.pkg.tar.zst` packages on release or manual trigger.

## Impact
- Affected specs: `packaging` (new), `ci-cd` (new).
- Affected code: New files added to project root and `packaging/` directory. No existing code logic should be broken, but `app.py` might need minor adjustments for production environment variables.
