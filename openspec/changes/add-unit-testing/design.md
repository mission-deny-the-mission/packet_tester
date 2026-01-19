## Context
The project currently lacks automated tests. We need a way to verify that core functions work correctly without requiring manual execution of the entire application.

## Goals / Non-Goals
- Goals:
    - Establish a standard for unit testing.
    - Provide high coverage for critical parsing and calculation logic.
    - Mock external dependencies (subprocess, database) to ensure tests are fast and isolated.
- Non-Goals:
    - Full End-to-End (E2E) testing involving real network utilities.
    - Testing third-party libraries (Flask, SocketIO) themselves.

## Decisions
- **Decision**: Use `pytest` as the testing framework.
    - Rationale: `pytest` is the industry standard for Python, offers powerful fixtures, and has great plugin support (like `pytest-mock`).
- **Decision**: Use `unittest.mock` (via `pytest-mock`) for isolating units.
    - Rationale: Avoids the need for real network calls or a running database during unit tests.
- **Decision**: Separate test database.
    - Rationale: Ensure tests don't pollute the production `network_data.db`.

## Risks / Trade-offs
- [Risk] Mocking too much might hide integration issues. → Mitigation: Keep mocks focused on external I/O and verify integration manually or with targeted integration tests later.

## Migration Plan
1. Add dependencies.
2. Create `tests/` directory.
3. Implement first set of tests for utility functions.
4. Add test execution to `CLAUDE.md` or `README.md`.

## Open Questions
- Should we use a separate SQLite file for database tests or an in-memory database?
    - Decision: Use in-memory SQLite for speed and isolation.
