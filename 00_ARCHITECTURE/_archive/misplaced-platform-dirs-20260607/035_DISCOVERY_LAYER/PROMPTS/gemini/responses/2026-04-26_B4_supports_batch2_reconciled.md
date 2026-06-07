# SUPPORTS Edge Reconciler — Batch B4_supports_batch2

**Session:** Madhav_M2A_Exec_7  
**Date:** 2026-04-26  
**Raw response:** `2026-04-26_B4_supports_batch2_raw.md`  
**Reconciler:** `cgm_supports_reconciler.py`  

---

## §1 — Result Summary

| Metric | Count |
|--------|-------|
| Proposed | 14 |
| Accepted | 4 |
| Rejected (total) | 10 |
| → Rejected P1 (L3 report validity) | 0 |
| → Rejected P2 (UCN section validity / l1_basis) | 0 |
| → Rejected P5 (signal_id resolution) | 0 |
| → Rejected L3 chain | 10 |

---

## §2 — Per-Edge Verdict Table

| # | source_signal_id | target_ucn_section_id | l3_evidence_report | verdict | P1 | P2 | P5 | L3 chain | notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SIG.MSR.164 | UCN.SEC.V.4 | REPORT_CHILDREN_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ | L3_CHAIN: signal not found by ID in L3 (implicit reference — LOW confidence) |
| 2 | SIG.MSR.083 | UCN.SEC.V.4 | REPORT_CHILDREN_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ | L3_CHAIN: signal not found by ID in L3 (implicit reference — LOW confidence) |
| 3 | SIG.MSR.343 | UCN.SEC.V.4 | REPORT_CHILDREN_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.343' found in L3 at lines [11, 39]... but UCN ref '§V. |
| 4 | SIG.MSR.343 | UCN.SEC.V.1 | REPORT_CHILDREN_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.343' found in L3 at lines [11, 39]... but UCN ref '§V. |
| 5 | SIG.MSR.404 | UCN.SEC.V.4 | REPORT_CHILDREN_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.404' found in L3 at lines [85]... but UCN ref '§V.4' n |
| 6 | SIG.MSR.398 | UCN.SEC.V.4 | REPORT_CHILDREN_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.398' found in L3 at lines [11]... but UCN ref '§V.4' n |
| 7 | SIG.MSR.333 | UCN.SEC.V.4 | REPORT_CHILDREN_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.333' found in L3 at lines [11]... but UCN ref '§V.4' n |
| 8 | SIG.MSR.341 | UCN.SEC.V.4 | REPORT_CHILDREN_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.341' found in L3 at lines [11]... but UCN ref '§V.4' n |
| 9 | SIG.MSR.394 | UCN.SEC.V.4 | REPORT_CHILDREN_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.394' found in L3 at lines [11]... but UCN ref '§V.4' n |
| 10 | SIG.MSR.397 | UCN.SEC.V.4 | REPORT_CHILDREN_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.397' found in L3 at lines [106, 114, 173]... but UCN r |
| 11 | SIG.MSR.406 | UCN.SEC.V.4 | REPORT_CHILDREN_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.406' found in L3 at lines [11]... but UCN ref '§V.4' n |
| 12 | SIG.MSR.413 | UCN.SEC.IV.3 | REPORT_CHILDREN_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.413' found in L3 at lines [11]... but UCN ref '§IV.3'  |
| 13 | SIG.MSR.255 | UCN.SEC.VIII.2 | REPORT_CHILDREN_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ | L3_CHAIN: signal not found by ID in L3 (implicit reference — LOW confidence) |
| 14 | SIG.MSR.263 | UCN.SEC.VIII.2 | REPORT_CHILDREN_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ | L3_CHAIN: signal not found by ID in L3 (implicit reference — LOW confidence) |
