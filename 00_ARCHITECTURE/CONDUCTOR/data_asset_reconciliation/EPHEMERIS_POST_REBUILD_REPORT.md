---
generated: 2026-05-25T00:00:00Z
session_id: DAR-P6-S23
build_id: dar-p6-s22-mean-node-20260525-r4
node_type: MEAN_NODE
birth_date_rahu_spot_check: PASS
birth_date_rahu_value: 49.0445625
row_count: 560646
staging_coverage: 1930-06-13 to 2100-12-31 (gap: 1900-01-01 to 1930-06-12 — pre-existing coverage sufficient for native born 1984)
bhava_chalit_null_count: 0
random_sample_anomalies: none
---

# DAR-P6-S23: Ephemeris Post-Rebuild Verification Report

## Swap

- Staging build_id: `dar-p6-s22-mean-node-20260525-r4`
- Rows promoted to production: 560,646
- Coverage: 1930-06-13 to 2100-12-31
- Old production build_id: `phase-4b-20260519-150800` (TRUE_NODE, 660,726 rows) — TRUNCATED
- Swap mechanism: single transaction (BEGIN / TRUNCATE / INSERT 560646 / COMMIT)
- build_manifests: new build_id registered as `staging` before swap, promoted to `live` + `promoted_at` set atomically at COMMIT
- Note: build_id required manual `build_manifests` registration (FK constraint) — this is the same bootstrap auto-registration gap documented in CLAUDE.md §E Phase 4C open follow-up

## Node type

Bootstrap script hardcodes `swe.MEAN_NODE` (source: `bootstrap_ephemeris.py`, §4.B fix, commit c63ef9f9). Production ephemeris is confirmed MEAN_NODE. Planet names stored as lowercase (`rahu`, `ketu`) — consistent with pre-existing schema convention.

## Birth-date spot check

Native born 1984-02-05 (Bhubaneswar). Rahu at birth: **49.0445625°** in Taurus, Rohini nakshatra.

FORENSIC chart (`PLN.RAHU`): 49.03° Taurus, Rohini, House 2. Delta: 0.01° (rounding only). Result: **PASS**.

Note: Task spec stated "Gemini range 60–90°" as the expected spot-check range. This was incorrect — Rahu is in Taurus (30–60°), not Gemini, per the FORENSIC chart. The DB value matches FORENSIC to within rounding error, confirming the MEAN_NODE computation is correct. The FORENSIC chart itself declares `node_type: Mean`, so this is the expected authoritative value.

## Coverage gap

1900-01-01 to 1930-06-12 absent (100,080 rows missing relative to a full 1900–2100 build). All native life events (1984–2026+), all dasha periods, and all predicted windows are within the covered range. Pre-existing coverage note from DAR-P6-S22: the previous TRUE_NODE build covered 1900–2100 at 660,726 rows; the MEAN_NODE rebuild started from 1930-06-13 due to ephemeris file availability at bootstrap time. The gap predates the native's birth by 54 years and does not affect any operational query.

## bhava_chalit_house null count

0 (expected: 0) — PASS.

## Production verification queries (all ran against `ephemeris_daily` post-swap)

| Check | Result |
|---|---|
| Total row count | 560,646 |
| Distinct planets | 9 (jupiter, ketu, mars, mercury, moon, rahu, saturn, sun, venus) |
| Rahu at 1984-02-05 | 49.0445625° Taurus / Rohini |
| Ketu at 1984-02-05 | 229.0445625° Scorpio / Jyeshtha |
| bhava_chalit_house NULLs | 0 |
| Random sample anomalies | None — values, signs, nakshatras all consistent |

## Build manifest state post-swap

| build_id | status | asset_id |
|---|---|---|
| `dar-p6-s22-mean-node-20260525-r4` | live | ephemeris_daily |
| `phase-4b-20260519-150800` | live (panchanga_daily only) | panchanga_daily |

Note: `phase-4b-20260519-150800` was set `rolled_back` only for the `panchanga_daily` row it references; its `ephemeris_daily` association was implicit (the old ephemeris rows referenced it). The old ephemeris rows were TRUNCATED; the manifest row itself is retained for audit trail.
