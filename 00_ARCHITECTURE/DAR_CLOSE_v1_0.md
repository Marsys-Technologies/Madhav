---
canonical_id: DAR_CLOSE
version: 1.0
status: COMPLETE
closed: 2026-05-25T00:00:00Z
workstream: data-asset-reconciliation
branch_merged: feature/data-asset-reconciliation
sessions_completed: 26
artifact: DAR_CLOSE_v1_0
---

# Data Asset Reconciliation — Workstream Close

## Summary

All 26 DAR sessions (Run 1: P1-S1 through P4-S14; Run 2: P5-S15 through P7-S26) completed successfully. Every canonical data asset is now:

- **MSR v5.1**: 573 signals fully B.3 derivation-ledger grounded, loaded to DB (573 rows in `msr_signals`)
- **chart_facts**: 767 rows across 36 categories (ashtakavarga, sthira_karaka, narayana_dasha, etc.) in DB
- **ephemeris_daily**: Rebuilt with MEAN_NODE Rahu/Ketu; 560,646 rows (1930-06-13 → 2100-12-31); Rahu at 1984-02-05 = 49.04° Taurus/Rohini (FORENSIC-verified delta 0.01°)
- **rag_chunks**: 6,990 total (573 MSR signal chunks + 5,743 classical text chunks)
- **school_signal_coverage**: 4,011 rows; school_convergence_index: 573 rows
- **ICR confirm + MCP asset route**: Both reference MSR_v5_0.md (correct canonical path)
- **CGM/UCN/CDLM**: Cross-reference integrity verified; all MSR signal IDs resolve in DB
- **Mirror pairs MP.1/MP.2**: In scope for DAR; governance files updated

## Phase gate summary

| Phase | Sessions | Gate passage |
|---|---|---|
| P1: Code fixes + governance | S1–S4 | 4/4 PASS |
| P2: DB baseline | S5–S6 | 2/2 PASS |
| P3: MSR DB reload + RAG rebuild | S7–S10 | 4/4 PASS |
| P4: chart_facts expansion | S11–S14 | 4/4 PASS |
| P5: B.3 derivation-ledger grounding | S15–S20 | 6/6 PASS |
| P6: Ephemeris MEAN_NODE rebuild | S21–S23 | 3/3 PASS |
| P7: Integration testing + close | S23–S26 | 4/4 PASS |

## Residuals (deferred, non-blocking)

1. **Ephemeris coverage gap**: 1900-01-01 → 1930-06-12 (100,080 rows) absent from production. Native born 1984 — all relevant periods covered. Backfill deferred to V1.3 queue.
2. **bootstrap build_manifests auto-registration**: Both ephemeris and panchanga bootstraps require manual `build_manifests` row insertion before swap (FK constraint). Documented at V1_3_AUDIT_QUEUE CF.V13.x.
3. **lel_events DB table absent**: LEL lives as canonical markdown (57 events). DB table not created in this workstream scope.
