# Change: Add Unit Testing Framework

## Why
Currently, the project relies on manual verification for testing. As the codebase grows, manual testing becomes time-consuming and prone to human error. Introducing an automated unit testing framework will ensure code quality, prevent regressions, and simplify the development process.

## What Changes
- Add `pytest` and `pytest-mock` to `requirements.txt`.
- Create a `tests/` directory to house unit tests.
- Implement unit tests for core logic (e.g., `parse_ping` in `app.py`).
- Implement unit tests for database interactions in `database.py`.
- Configure a CI-friendly test command.

## Impact
- Affected specs: `automated-testing` (new capability)
- Affected code: `requirements.txt`, new `tests/` directory, `app.py` (for testability if needed), `database.py` (for testability if needed).
