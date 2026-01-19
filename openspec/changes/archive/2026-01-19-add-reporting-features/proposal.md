# Change: Add Reporting Features

## Why
Users frequently need to share diagnostic data with ISPs or IT support. Providing an easy way to export and share snapshots of network issues makes the tool significantly more useful for troubleshooting.

## What Changes
- **Snapshot Export**: Ability to download a specific monitor card (including charts and tables) as a PNG image.
- **Report Generation**: A "Generate Report" button that produces a consolidated view of current network health.

## Impact
- Affected specs: `network-monitoring`
- Affected code: `templates/index.html`, `static/js/dashboard.js`
