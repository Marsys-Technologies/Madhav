# SUPPORTS Edge Reconciler — Batch B4_supports_batch7

**Session:** Madhav_M2A_Exec_7  
**Date:** 2026-04-26  
**Raw response:** `2026-04-26_B4_supports_batch7_raw.md`  
**Reconciler:** `cgm_supports_reconciler.py`  

---

## §1 — Result Summary

| Metric | Count |
|--------|-------|
| Proposed | 15 |
| Accepted | 0 |
| Rejected (total) | 15 |
| → Rejected P1 (L3 report validity) | 0 |
| → Rejected P2 (UCN section validity / l1_basis) | 0 |
| → Rejected P5 (signal_id resolution) | 0 |
| → Rejected L3 chain | 15 |

---

## §2 — Per-Edge Verdict Table

| # | source_signal_id | target_ucn_section_id | l3_evidence_report | verdict | P1 | P2 | P5 | L3 chain | notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SIG.MSR.343 | UCN.SEC.V.1 | REPORT_RELATIONSHIPS_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.343' found in L3 at lines [10]... but UCN ref '§V.1' n |
| 2 | SIG.MSR.343 | UCN.SEC.V.2 | REPORT_RELATIONSHIPS_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.343' found in L3 at lines [10]... but UCN ref '§V.2' n |
| 3 | SIG.MSR.343 | UCN.SEC.V.7 | REPORT_RELATIONSHIPS_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.343' found in L3 at lines [10]... but UCN ref '§V.7' n |
| 4 | SIG.MSR.391 | UCN.SEC.V.1 | REPORT_RELATIONSHIPS_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.391' found in L3 at lines [10, 15, 46]... but UCN ref  |
| 5 | SIG.MSR.391 | UCN.SEC.V.2 | REPORT_RELATIONSHIPS_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.391' found in L3 at lines [10, 15, 46]... but UCN ref  |
| 6 | SIG.MSR.391 | UCN.SEC.V.7 | REPORT_RELATIONSHIPS_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.391' found in L3 at lines [10, 15, 46]... but UCN ref  |
| 7 | SIG.MSR.396 | UCN.SEC.V.1 | REPORT_RELATIONSHIPS_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.396' found in L3 at lines [10]... but UCN ref '§V.1' n |
| 8 | SIG.MSR.396 | UCN.SEC.V.2 | REPORT_RELATIONSHIPS_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.396' found in L3 at lines [10]... but UCN ref '§V.2' n |
| 9 | SIG.MSR.396 | UCN.SEC.V.7 | REPORT_RELATIONSHIPS_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.396' found in L3 at lines [10]... but UCN ref '§V.7' n |
| 10 | SIG.MSR.404 | UCN.SEC.V.1 | REPORT_RELATIONSHIPS_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.404' found in L3 at lines [10, 140]... but UCN ref '§V |
| 11 | SIG.MSR.404 | UCN.SEC.V.2 | REPORT_RELATIONSHIPS_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.404' found in L3 at lines [10, 140]... but UCN ref '§V |
| 12 | SIG.MSR.404 | UCN.SEC.V.7 | REPORT_RELATIONSHIPS_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.404' found in L3 at lines [10, 140]... but UCN ref '§V |
| 13 | SIG.MSR.443 | UCN.SEC.V.1 | REPORT_RELATIONSHIPS_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.443' found in L3 at lines [10]... but UCN ref '§V.1' n |
| 14 | SIG.MSR.443 | UCN.SEC.V.2 | REPORT_RELATIONSHIPS_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.443' found in L3 at lines [10]... but UCN ref '§V.2' n |
| 15 | SIG.MSR.443 | UCN.SEC.V.7 | REPORT_RELATIONSHIPS_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.443' found in L3 at lines [10]... but UCN ref '§V.7' n |
