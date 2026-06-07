# SUPPORTS Edge Reconciler — Batch B4_supports_batch1

**Session:** Madhav_M2A_Exec_7  
**Date:** 2026-04-26  
**Raw response:** `2026-04-26_B4_supports_batch1_raw.md`  
**Reconciler:** `cgm_supports_reconciler.py`  

---

## §1 — Result Summary

| Metric | Count |
|--------|-------|
| Proposed | 11 |
| Accepted | 8 |
| Rejected (total) | 3 |
| → Rejected P1 (L3 report validity) | 0 |
| → Rejected P2 (UCN section validity / l1_basis) | 0 |
| → Rejected P5 (signal_id resolution) | 0 |
| → Rejected L3 chain | 3 |

---

## §2 — Per-Edge Verdict Table

| # | source_signal_id | target_ucn_section_id | l3_evidence_report | verdict | P1 | P2 | P5 | L3 chain | notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SIG.MSR.413 | UCN.SEC.IV.3 | REPORT_CAREER_DHARMA_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 2 | SIG.MSR.396 | UCN.SEC.VII.4 | REPORT_CAREER_DHARMA_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 3 | SIG.MSR.391 | UCN.SEC.I.1 | REPORT_CAREER_DHARMA_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.391' found in L3 at lines [15, 239]... but UCN ref '§I |
| 4 | SIG.MSR.131 | UCN.SEC.VII.3 | REPORT_CAREER_DHARMA_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.131' found in L3 at lines [819]... but UCN ref '§VII.3 |
| 5 | SIG.MSR.397 | UCN.SEC.IV.4 | REPORT_CAREER_DHARMA_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 6 | SIG.MSR.404 | UCN.SEC.VIII.2 | REPORT_CAREER_DHARMA_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 7 | SIG.MSR.228 | UCN.SEC.IX.2 | REPORT_CAREER_DHARMA_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 8 | SIG.MSR.354 | UCN.SEC.X.2 | REPORT_CAREER_DHARMA_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.354' found in L3 at lines [800, 871]... but UCN ref '§ |
| 9 | SIG.MSR.216 | UCN.SEC.IV.5 | REPORT_CAREER_DHARMA_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ | L3_CHAIN: signal not found by ID in L3 (implicit reference — LOW confidence) |
| 10 | SIG.MSR.348 | UCN.SEC.II.2 | REPORT_CAREER_DHARMA_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ | L3_CHAIN: signal not found by ID in L3 (implicit reference — LOW confidence) |
| 11 | SIG.MSR.194 | UCN.SEC.VIII.4 | REPORT_CAREER_DHARMA_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ | L3_CHAIN: signal not found by ID in L3 (implicit reference — LOW confidence) |
