---
session: DAR-P3-S8
source_file: MSR_v5_0
msr_signals_count: 573
l25_msr_signals_count: 573
msr_signals_source: MSR_v5_0.md
l25_msr_signals_source: MSR_v5_0.md
build_id: dar-p3-s8-msr-v5-load-20260525
load_status: COMPLETE
date: 2026-05-25
---

# DAR-P3-S8 MSR DB Load Report

## Summary

Both MSR signal tables now contain 573 rows sourced from `MSR_v5_0.md` (573 signals, SIG.MSR.001–SIG.MSR.573).

## Table: msr_signals

**Pre-load state:** 573 rows from MSR_v5_0.md (already current — loaded by prior KARN-W2-R1 pipeline session via `ingest_msr.py`).

**Action:** No reload required. Verified via:
```sql
SELECT source_file, COUNT(*) FROM msr_signals GROUP BY source_file;
-- Result: MSR_v5_0.md | 573
```

**Schema note:** `msr_signals` uses a different schema than `l25_msr_signals` — it holds the original MSR ingestion columns (domain, planet, house, confidence, significance, claim_text, source_file, source_version) plus the 8 additional columns added by migration 028 (signal_type, temporal_activation, valence, entities_involved, supporting_rules, rpt_deep_dive, v6_ids_consumed, prior_id).

## Table: l25_msr_signals

**Pre-load state:** 514 rows (stale — sourced from an earlier build `build-865dd96e-3cad-4715-be47-fc8005ef95b5`, missing 59 signals).

**Action:** Full reload via staging→swap lifecycle using `MSRSignalsWriter`.

**Method:**
1. Registered build_manifest `dar-p3-s8-msr-v5-load-20260525` (status: staging → live after swap).
2. Extracted 573 signals via `pipeline.extractors.msr_extractor.extract_msr_signals()` from `025_HOLISTIC_SYNTHESIS/MSR_v5_0.md`.
3. Wrote 573 rows to `l25_msr_signals_staging` via `MSRSignalsWriter.write_to_staging()` — 0 errors.
4. Validated staging: 573 rows for build_id confirmed (valid=True).
5. Swapped staging → live via `MSRSignalsWriter.swap_to_live()`: promoted 573 rows atomically (DELETE live → INSERT from staging → TRUNCATE staging → update build_manifests).

**Verification:**
```sql
SELECT COUNT(*), MIN(signal_id), MAX(signal_id)
FROM l25_msr_signals WHERE build_id = 'dar-p3-s8-msr-v5-load-20260525';
-- Result: 573 | SIG.MSR.001 | SIG.MSR.573
```

## Verification Commands Run

```sql
-- msr_signals
SELECT source_file, COUNT(*) FROM msr_signals GROUP BY source_file;
-- MSR_v5_0.md | 573  ✓

-- l25_msr_signals
SELECT COUNT(*), MIN(signal_id), MAX(signal_id)
FROM l25_msr_signals WHERE build_id = 'dar-p3-s8-msr-v5-load-20260525';
-- 573 | SIG.MSR.001 | SIG.MSR.573  ✓
```

## Anomalies

None. Both tables contain exactly 573 rows from MSR_v5_0.md. The l25_msr_signals pre-load deficit of 59 rows (514 → 573) was resolved by the staging→swap reload.

## DB Connection

- Proxy: Cloud SQL Auth Proxy, port 5433
- Instance: `madhav-astrology:asia-south1:amjis-postgres`
- Database: `amjis`
