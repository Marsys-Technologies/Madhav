NOTE: 362f9f17-… is a dead phantom; canonical is 482012f1-710e-4a25-994a-93821f5871aa
---
phase: B.6
title: GCS Drift Audit
status: COMPLETE
executed_at: 2026-04-28
executor: Claude Code (Sonnet 4.6)
verdict: AMBER — GCS chart documents are stale snapshots; not a runtime failure but a deployment risk
---

# B.6 — GCS Drift Audit

## GCS Bucket Inventory

### madhav-astrology-chat-attachments
Status: **Empty** (0 objects). Expected — users haven't uploaded chart attachments yet. No action needed.

### madhav-astrology-chart-documents
Status: **19 objects** under `charts/362f9f17-95a5-490b-a5a7-027d3e0efda0/`

| GCS Path | Size | GCS Version | Current Local Version |
|---|---|---|---|
| L1/forensic_data_v1.0.md | 87 KB | v1.0 | **v8.0** ← STALE |
| L1/event_chart_states_v1.0.md | 57 KB | v1.0 | moved to SOURCES/ |
| L1/external_computation_spec_v1.0.md | 34 KB | v1.0 | v2.0 |
| L1/life_event_log_v1.0.md | 103 KB | v1.0 | v1.2 |
| L1/sade_sati_cycles_v1.0.md | 6.9 KB | v1.0 | current |
| L1/cgp_audit_v1.0.md | 22 KB | v1.0 | current |
| L2.5/cdlm_v1.0.md | 80 KB | v1.0 | v1.1 |
| L2.5/cgm_v1.0.md | 33 KB | v1.0 | v9.0 ← MAJOR STALE |
| L2.5/msr_v1.0.md | 774 KB | v1.0 | v3.0 ← STALE |
| L2.5/rm_v1.0.md | 96 KB | v1.0 | v2.0 |
| L2.5/ucn_v1.0.md | 135 KB | v1.0 | v4.0 ← STALE |
| L2/deep_analysis_v1.0.md | 436 KB | v1.0 | current |
| L2/matrix_*.md (5 files) | 30–48 KB each | v1.0 | current |
| L3/report_financial_v1.0.md | 215 KB | v1.0 | current |

## Assessment

GCS chart-documents bucket contains a **full snapshot** of an earlier build (all v1.0 dated). This is the build-state GCS output used for the deployed production app. The bundle composer reads from GCS via the `BUILD_STATE_GCS_BASE` path when resolving floor assets in production.

**Staleness risk:** FORENSIC v8.0 (local) vs `forensic_data_v1.0.md` (GCS, 87KB) — GCS version is missing all FORENSIC v2–v8 enrichments. MSR v3.0 (499 signals local) vs `msr_v1.0.md` (GCS, likely fewer signals). CGM v9.0 vs `cgm_v1.0.md`.

**Runtime impact:** The bundle composer first tries the GCS path (`BUILD_STATE_GCS_BASE`). If GCS assets are stale, synthesized answers in **production** use old document versions. Dev is unaffected (reads from local filesystem).

## Recommended Action
Re-run the build pipeline to upload current artifact versions to GCS:
1. `npm run manifest:build` (to refresh fingerprints)
2. Upload current L1/L2/L2.5 artifacts to the `charts/362f9f17.../` GCS path

This should be part of the standard deployment workflow after any canonical artifact update. Likely deferred from the Cloud SQL migration (Phase 11 cutover).

**Priority: MEDIUM** — production users may be getting answers synthesized from v1.0 artifacts.
