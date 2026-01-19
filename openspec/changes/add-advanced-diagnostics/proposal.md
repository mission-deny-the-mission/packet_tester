# Change: Add Advanced Diagnostics

## Why
Standard latency and packet loss provide a baseline, but high-quality diagnostics (especially for VoIP, gaming, and video conferencing) require understanding Jitter and connection quality (MOS). Additionally, identifying the ISP and location of intermediate hops helps users hold the correct entity accountable.

## What Changes
- **Jitter Calculation**: The backend will calculate the variation in latency between consecutive pings.
- **MOS Scoring**: Implementation of a Mean Opinion Score (MOS) algorithm to provide a 1-5 quality rating.
- **ISP & Geo Lookup**: Asynchronous lookup of IP ownership and approximate geographic location for all hops.
- **UI Enhancements**: New metrics displayed in the monitor cards and extra columns in the path analysis table.

## Impact
- Affected specs: `network-monitoring`, `hop-analysis`
- Affected code: `app.py` (calculations/lookups), `dashboard.js` (UI display)
