## 1. Metric Implementation
- [x] 1.1 Update `run_ping` in `app.py` to calculate Jitter (standard deviation or RFC 3550)
- [x] 1.2 Implement MOS scoring formula based on latency, loss, and jitter
- [x] 1.3 Update `ping_result` socket event to include `jitter` and `mos`

## 2. Enrichment Services
- [x] 2.1 Integrate an IP-to-ISP/Geo API (e.g., ip-api.com or similar)
- [x] 2.2 Implement caching for IP lookups to avoid rate limits
- [x] 2.3 Update `hop_update` socket event to include `isp` and `location`

## 3. UI Updates
- [x] 3.1 Add "Jitter" and "MOS" display to target cards
- [x] 3.2 Add "ISP" column to the Path Analysis table
- [x] 3.3 Add tooltips or icons for geographic location info
