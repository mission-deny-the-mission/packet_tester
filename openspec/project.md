# Project Context

## Purpose
A real-time network diagnostic dashboard inspired by PingPlotter. It enables concurrent monitoring of multiple network destinations, providing live visualizations of latency, packet loss, and hop-by-hop path analysis to identify the exact source of network degradation.

## Tech Stack
- **Backend**: Python 3 (Flask, Flask-SocketIO)
- **Concurrency**: Eventlet (monkey-patching for non-blocking I/O)
- **Frontend**: HTML5, Tailwind CSS, Chart.js, Socket.io (client)
- **Utilities**: Linux system binaries (`ping`, `tracepath`)

## Project Conventions

### Code Style
- **Python**: Follows PEP 8. Uses `eventlet.spawn` for background tasks. Logging is handled via standard print statements for container/CLI visibility.
- **JavaScript**: Modern ES6. Uses dynamic DOM manipulation and HTML templates for UI scalability.
- **Naming**: 
  - Python: `snake_case` for functions and variables.
  - JavaScript: `camelCase` for variables and `kebab-case` for CSS classes.

### Architecture Patterns
- **WebSocket Streaming**: Continuous bi-directional communication for sub-second metric updates.
- **Subprocess Management**: Spawning long-lived `ping` and `tracepath` processes, tracked in a session-aware `active_tasks` dictionary.
- **State Management**: Server-side tracking of active tests indexed by session ID (`sid`) and target IP/domain.

### Testing Strategy
- **Manual Verification**: End-to-end testing by adding known stable (8.8.8.8) and unstable targets.
- **Self-Correction**: Automatic subprocess termination on client disconnect or test removal.

### Git Workflow
- **Commit Style**: Concise, action-oriented messages (e.g., "Implement per-hop loss detection").
- **Exclusions**: Managed via `.gitignore` (venv, logs, pycache).

## Domain Context
- **Path Analysis**: Utilizes ICMP TTL expiration to map the network path.
- **Packet Loss Correlation**: Distinguishes between localized hop loss (ICMP deprioritization) and cascading loss (congestion starting at a specific node).

## Important Constraints
- **Platform**: Tailored for Linux environments (relies on `ping` and `tracepath` CLI output parsing).
- **Permissions**: Requires the ability to execute network utilities.

## External Dependencies
- **CDNs**: Tailwind CSS, Chart.js, and Socket.io are loaded via CDN for simplicity.
