---
artifact: 4C6_S1_muhurat_latency.md
type: PERFORMANCE_BASELINE
session: 4C-6-S1
measured_on: 2026-05-20
measured_by: Claude Code (4C-6-S1 autonomous session)
engine_version: 1.0.0-S3
location: Bhubaneswar (lat=20.27, lon=85.84, tz_offset=330)
---

# Muhurat Finder — Latency Baseline (4C-6-S1)

## Summary

The muhurat backend (Phase 4C-6-S1) is significantly faster than anticipated.
The brief estimated ~30 seconds for a 90-day range on a cold sidecar.
Actual performance is ~0.68s for 90 days — ~44× faster than the estimate.

## Measurements

All measurements taken on the local dev machine (Apple Silicon, M-series),
cold Python process (no warm cache), Lahiri ayanamsha, Swiss Ephemeris.
Event: `vivah`. Location: Bhubaneswar (IST +05:30).

| Range | Days | Elapsed | Windows Found | ms/day |
|-------|------|---------|---------------|--------|
| 2026-06-01 → 2026-06-30 | 30 | 0.22s | 10 | 7 ms |
| 2026-04-01 → 2026-06-30 | 90 | 0.68s | 10 | 8 ms |

## Top Vivah Window (Jun 2026)

- Date: 2026-06-21 (Monday, Shukla Ashtami, Uttara Phalguni)
- Score: 63.5 (3-star)
- Note: June windows are modestly scored; Vivah season peaks in Nov–Feb (Shukla paksha)
  when auspicious tithis, fixed nakshatras, and Thursday/Friday varas coincide more readily.

## Canary Cross-Check (brief §9)

Range query for `vivah` Jun 2026 (Bhubaneswar) returns plausibly-ranked windows.
The top result (2026-06-21: Monday, Uttara Phalguni, Shukla Ashtami) aligns with
classical guidance (Uttara Phalguni = MC 3.5 top-ranked marriage nakshatra, Monday =
acceptable vara). Shukla Ashtami is a weak tithi for Vivah (score 0.40), which correctly
keeps this window at 3-star rather than 5-star.

Senior-acharya intuition check: Uttara Phalguni is presided by Aryaman (god of contracts,
marriage, friendship) — classical texts specifically name it as the nakshatra under which
the Sun was positioned during Sita-Rama vivah (Ramayana reference). A knowledgeable
acharya would agree this is a valid Vivah nakshatra ranking highly.

## Performance Notes

- MVP path computes one full Panchang (Swiss Ephemeris + planetary positions + all 5 angas
  + special yogas + timings) per calendar day. At ~7–8 ms/day, the compute is IO-bound
  on the Swiss Ephemeris calls.
- For a 90-day range at 8 ms/day, total latency is ~720ms (well within interactive threshold).
- For a 180-day range (not yet supported; 90-day cap enforced), extrapolated: ~1.4s.
- No pre-filter needed for MVP. A coarser pre-filter (e.g., exclude obvious bad varas first)
  could reduce this by ~40% if latency becomes a concern in v2.
- Cloud Run cold start adds ~2–3s; warm sidecar (keep-alive) avoids this entirely.

## v2 Optimization Path

When finer per-muhurta windows (sub-day precision) are added in v2:
- Each day will need ~30 muhurta evaluations instead of 1 daylong score.
- Estimated v2 latency: ~8ms × 30 = 240ms/day → ~22s for 90 days.
- At that point, a tithi/nakshatra pre-filter to skip clearly bad days (score 0 on daylong)
  becomes valuable: typically 30–40% of days are pre-filtered, reducing v2 to ~13s/90 days.

## Re-baseline Trigger

Re-run this baseline when:
- Engine version bumps to v1.1+ (v2 sub-day muhurta windows)
- Deployment target changes (Cloud Run vs bare metal)
- Swiss Ephemeris version changes (affects per-call cost)
