# Change: Add Persistent Storage

## Why
Currently, all network monitoring data is volatile and lost upon browser refresh. To provide professional-grade diagnostics, the system must persist results to allow for historical analysis and long-term trend spotting.

## What Changes
- **Database Integration**: Add SQLite to store targets, ping results, and hop analysis data.
- **Historical API**: New endpoints to retrieve data for specific time ranges.
- **Frontend Persistence**: Targets will persist across sessions, and historical data will load automatically on dashboard initialization.

## Impact
- Affected specs: `network-monitoring`, `hop-analysis`
- Affected code: `app.py` (new DB logic), `dashboard.js` (loading history)
