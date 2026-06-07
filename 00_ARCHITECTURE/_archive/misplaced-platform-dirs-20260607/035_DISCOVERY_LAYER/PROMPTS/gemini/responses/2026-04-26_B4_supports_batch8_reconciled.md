# SUPPORTS Edge Reconciler — Batch B4_supports_batch8

**Session:** Madhav_M2A_Exec_7  
**Date:** 2026-04-26  
**Raw response:** `2026-04-26_B4_supports_batch8_raw.md`  
**Reconciler:** `cgm_supports_reconciler.py`  

---

## §1 — Result Summary

| Metric | Count |
|--------|-------|
| Proposed | 32 |
| Accepted | 8 |
| Rejected (total) | 24 |
| → Rejected P1 (L3 report validity) | 0 |
| → Rejected P2 (UCN section validity / l1_basis) | 0 |
| → Rejected P5 (signal_id resolution) | 0 |
| → Rejected L3 chain | 24 |

---

## §2 — Per-Edge Verdict Table

| # | source_signal_id | target_ucn_section_id | l3_evidence_report | verdict | P1 | P2 | P5 | L3 chain | notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SIG.MSR.374 | UCN.SEC.II.1 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.374' found in L3 at lines [10]... but UCN ref '§II.1'  |
| 2 | SIG.MSR.374 | UCN.SEC.II.5 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.374' found in L3 at lines [10]... but UCN ref '§II.5'  |
| 3 | SIG.MSR.374 | UCN.SEC.VI.1 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.374' found in L3 at lines [10]... but UCN ref '§VI.1'  |
| 4 | SIG.MSR.374 | UCN.SEC.VI.4 | REPORT_SPIRITUAL_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 5 | SIG.MSR.397 | UCN.SEC.II.1 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.397' found in L3 at lines [10]... but UCN ref '§II.1'  |
| 6 | SIG.MSR.397 | UCN.SEC.II.5 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.397' found in L3 at lines [10]... but UCN ref '§II.5'  |
| 7 | SIG.MSR.397 | UCN.SEC.VI.1 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.397' found in L3 at lines [10]... but UCN ref '§VI.1'  |
| 8 | SIG.MSR.397 | UCN.SEC.VI.4 | REPORT_SPIRITUAL_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 9 | SIG.MSR.402 | UCN.SEC.II.1 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.402' found in L3 at lines [151]... but UCN ref '§II.1' |
| 10 | SIG.MSR.402 | UCN.SEC.II.5 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.402' found in L3 at lines [151]... but UCN ref '§II.5' |
| 11 | SIG.MSR.402 | UCN.SEC.VI.1 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.402' found in L3 at lines [151]... but UCN ref '§VI.1' |
| 12 | SIG.MSR.402 | UCN.SEC.VI.4 | REPORT_SPIRITUAL_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 13 | SIG.MSR.406 | UCN.SEC.II.1 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.406' found in L3 at lines [10]... but UCN ref '§II.1'  |
| 14 | SIG.MSR.406 | UCN.SEC.II.5 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.406' found in L3 at lines [10]... but UCN ref '§II.5'  |
| 15 | SIG.MSR.406 | UCN.SEC.VI.1 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.406' found in L3 at lines [10]... but UCN ref '§VI.1'  |
| 16 | SIG.MSR.406 | UCN.SEC.VI.4 | REPORT_SPIRITUAL_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 17 | SIG.MSR.407 | UCN.SEC.II.1 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.407' found in L3 at lines [10, 18, 75]... but UCN ref  |
| 18 | SIG.MSR.407 | UCN.SEC.II.5 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.407' found in L3 at lines [10, 18, 75]... but UCN ref  |
| 19 | SIG.MSR.407 | UCN.SEC.VI.1 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.407' found in L3 at lines [10, 18, 75]... but UCN ref  |
| 20 | SIG.MSR.407 | UCN.SEC.VI.4 | REPORT_SPIRITUAL_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 21 | SIG.MSR.408 | UCN.SEC.II.1 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.408' found in L3 at lines [10, 122]... but UCN ref '§I |
| 22 | SIG.MSR.408 | UCN.SEC.II.5 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.408' found in L3 at lines [10, 122]... but UCN ref '§I |
| 23 | SIG.MSR.408 | UCN.SEC.VI.1 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.408' found in L3 at lines [10, 122]... but UCN ref '§V |
| 24 | SIG.MSR.408 | UCN.SEC.VI.4 | REPORT_SPIRITUAL_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 25 | SIG.MSR.433 | UCN.SEC.II.1 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.433' found in L3 at lines [10]... but UCN ref '§II.1'  |
| 26 | SIG.MSR.433 | UCN.SEC.II.5 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.433' found in L3 at lines [10]... but UCN ref '§II.5'  |
| 27 | SIG.MSR.433 | UCN.SEC.VI.1 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.433' found in L3 at lines [10]... but UCN ref '§VI.1'  |
| 28 | SIG.MSR.433 | UCN.SEC.VI.4 | REPORT_SPIRITUAL_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 29 | SIG.MSR.437 | UCN.SEC.II.1 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.437' found in L3 at lines [10]... but UCN ref '§II.1'  |
| 30 | SIG.MSR.437 | UCN.SEC.II.5 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.437' found in L3 at lines [10]... but UCN ref '§II.5'  |
| 31 | SIG.MSR.437 | UCN.SEC.VI.1 | REPORT_SPIRITUAL_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.437' found in L3 at lines [10]... but UCN ref '§VI.1'  |
| 32 | SIG.MSR.437 | UCN.SEC.VI.4 | REPORT_SPIRITUAL_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
