## 1. Backend Persistence
- [x] 1.1 Implement SQLite schema in `database.py` (tables: `targets`, `pings`, `hops`)
- [x] 1.2 Integrate DB writes into `run_ping` and `run_hop_analysis` in `app.py`
- [x] 1.3 Create `/api/history/<target>` endpoint to fetch past 24h of data

## 2. Frontend Integration
- [x] 2.1 Update `dashboard.js` to fetch and render historical data on target creation
- [x] 2.2 Implement "Clear History" button per target card
- [x] 2.3 Ensure active targets are restored on page reload
