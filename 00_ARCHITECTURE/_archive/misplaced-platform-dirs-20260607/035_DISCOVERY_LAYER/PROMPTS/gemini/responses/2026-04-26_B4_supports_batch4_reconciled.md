# SUPPORTS Edge Reconciler — Batch B4_supports_batch4

**Session:** Madhav_M2A_Exec_7  
**Date:** 2026-04-26  
**Raw response:** `2026-04-26_B4_supports_batch4_raw.md`  
**Reconciler:** `cgm_supports_reconciler.py`  

---

## §1 — Result Summary

| Metric | Count |
|--------|-------|
| Proposed | 3 |
| Accepted | 0 |
| Rejected (total) | 3 |
| → Rejected P1 (L3 report validity) | 0 |
| → Rejected P2 (UCN section validity / l1_basis) | 0 |
| → Rejected P5 (signal_id resolution) | 0 |
| → Rejected L3 chain | 3 |

---

## §2 — Per-Edge Verdict Table

| # | source_signal_id | target_ucn_section_id | l3_evidence_report | verdict | P1 | P2 | P5 | L3 chain | notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SIG.MSR.391 | UCN.SEC.III.4 | REPORT_HEALTH_LONGEVITY_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.391' found in L3 at lines [36, 338]... but UCN ref '§I |
| 2 | SIG.MSR.391 | UCN.SEC.IX.2 | REPORT_HEALTH_LONGEVITY_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.391' found in L3 at lines [36, 338]... but UCN ref '§I |
| 3 | SIG.MSR.391 | UCN.SEC.V.7 | REPORT_HEALTH_LONGEVITY_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.391' found in L3 at lines [36, 338]... but UCN ref '§V |
