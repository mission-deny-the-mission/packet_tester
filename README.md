# Packet Tester

A real-time network diagnostic dashboard.

## Development

### Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Running the App
```bash
python3 app.py
```

### Running Tests
Automated tests use `pytest`.

```bash
# Run all tests
pytest

# Run tests with coverage (if pytest-cov is installed)
# pytest --cov=.
```

The test suite includes:
- Unit tests for parsing logic and database operations.
- Integration tests for Flask routes.
- Mocking for external dependencies and isolated test databases.
