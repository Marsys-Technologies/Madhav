# SUPPORTS Edge Reconciler — Batch B4_supports_batch6

**Session:** Madhav_M2A_Exec_7  
**Date:** 2026-04-26  
**Raw response:** `2026-04-26_B4_supports_batch6_raw.md`  
**Reconciler:** `cgm_supports_reconciler.py`  

---

## §1 — Result Summary

| Metric | Count |
|--------|-------|
| Proposed | 40 |
| Accepted | 2 |
| Rejected (total) | 38 |
| → Rejected P1 (L3 report validity) | 0 |
| → Rejected P2 (UCN section validity / l1_basis) | 0 |
| → Rejected P5 (signal_id resolution) | 0 |
| → Rejected L3 chain | 38 |

---

## §2 — Per-Edge Verdict Table

| # | source_signal_id | target_ucn_section_id | l3_evidence_report | verdict | P1 | P2 | P5 | L3 chain | notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SIG.MSR.190 | UCN.SEC.V.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.190' found in L3 at lines [493, 494]... but UCN ref '§ |
| 2 | SIG.MSR.190 | UCN.SEC.III.2 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.190' found in L3 at lines [493, 494]... but UCN ref '§ |
| 3 | SIG.MSR.190 | UCN.SEC.III.3 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.190' found in L3 at lines [493, 494]... but UCN ref '§ |
| 4 | SIG.MSR.190 | UCN.SEC.III.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.190' found in L3 at lines [493, 494]... but UCN ref '§ |
| 5 | SIG.MSR.253 | UCN.SEC.V.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.253' found in L3 at lines [12, 492]... but UCN ref '§V |
| 6 | SIG.MSR.253 | UCN.SEC.III.2 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.253' found in L3 at lines [12, 492]... but UCN ref '§I |
| 7 | SIG.MSR.253 | UCN.SEC.III.3 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.253' found in L3 at lines [12, 492]... but UCN ref '§I |
| 8 | SIG.MSR.253 | UCN.SEC.III.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.253' found in L3 at lines [12, 492]... but UCN ref '§I |
| 9 | SIG.MSR.348 | UCN.SEC.V.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.348' found in L3 at lines [12, 466, 489]... but UCN re |
| 10 | SIG.MSR.348 | UCN.SEC.III.2 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.348' found in L3 at lines [12, 466, 489]... but UCN re |
| 11 | SIG.MSR.348 | UCN.SEC.III.3 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.348' found in L3 at lines [12, 466, 489]... but UCN re |
| 12 | SIG.MSR.348 | UCN.SEC.III.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.348' found in L3 at lines [12, 466, 489]... but UCN re |
| 13 | SIG.MSR.354 | UCN.SEC.V.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.354' found in L3 at lines [516]... but UCN ref '§V.5'  |
| 14 | SIG.MSR.354 | UCN.SEC.III.2 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.354' found in L3 at lines [516]... but UCN ref '§III.2 |
| 15 | SIG.MSR.354 | UCN.SEC.III.3 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.354' found in L3 at lines [516]... but UCN ref '§III.3 |
| 16 | SIG.MSR.354 | UCN.SEC.III.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.354' found in L3 at lines [516]... but UCN ref '§III.5 |
| 17 | SIG.MSR.369 | UCN.SEC.V.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.369' found in L3 at lines [12, 491]... but UCN ref '§V |
| 18 | SIG.MSR.369 | UCN.SEC.III.2 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.369' found in L3 at lines [12, 491]... but UCN ref '§I |
| 19 | SIG.MSR.369 | UCN.SEC.III.3 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.369' found in L3 at lines [12, 491]... but UCN ref '§I |
| 20 | SIG.MSR.369 | UCN.SEC.III.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.369' found in L3 at lines [12, 491]... but UCN ref '§I |
| 21 | SIG.MSR.374 | UCN.SEC.V.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.374' found in L3 at lines [12, 490]... but UCN ref '§V |
| 22 | SIG.MSR.374 | UCN.SEC.III.2 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.374' found in L3 at lines [12, 490]... but UCN ref '§I |
| 23 | SIG.MSR.374 | UCN.SEC.III.3 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.374' found in L3 at lines [12, 490]... but UCN ref '§I |
| 24 | SIG.MSR.374 | UCN.SEC.III.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.374' found in L3 at lines [12, 490]... but UCN ref '§I |
| 25 | SIG.MSR.388 | UCN.SEC.V.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.388' found in L3 at lines [12, 487]... but UCN ref '§V |
| 26 | SIG.MSR.388 | UCN.SEC.III.2 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.388' found in L3 at lines [12, 487]... but UCN ref '§I |
| 27 | SIG.MSR.388 | UCN.SEC.III.3 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.388' found in L3 at lines [12, 487]... but UCN ref '§I |
| 28 | SIG.MSR.388 | UCN.SEC.III.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.388' found in L3 at lines [12, 487]... but UCN ref '§I |
| 29 | SIG.MSR.396 | UCN.SEC.V.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 30 | SIG.MSR.396 | UCN.SEC.III.2 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.396' found in L3 at lines [12, 251, 488]... but UCN re |
| 31 | SIG.MSR.396 | UCN.SEC.III.3 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.396' found in L3 at lines [12, 251, 488]... but UCN re |
| 32 | SIG.MSR.396 | UCN.SEC.III.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.396' found in L3 at lines [12, 251, 488]... but UCN re |
| 33 | SIG.MSR.406 | UCN.SEC.V.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.406' found in L3 at lines [12, 486]... but UCN ref '§V |
| 34 | SIG.MSR.406 | UCN.SEC.III.2 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.406' found in L3 at lines [12, 486]... but UCN ref '§I |
| 35 | SIG.MSR.406 | UCN.SEC.III.3 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.406' found in L3 at lines [12, 486]... but UCN ref '§I |
| 36 | SIG.MSR.406 | UCN.SEC.III.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.406' found in L3 at lines [12, 486]... but UCN ref '§I |
| 37 | SIG.MSR.413 | UCN.SEC.V.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 38 | SIG.MSR.413 | UCN.SEC.III.2 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.413' found in L3 at lines [12, 44, 169]... but UCN ref |
| 39 | SIG.MSR.413 | UCN.SEC.III.3 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.413' found in L3 at lines [12, 44, 169]... but UCN ref |
| 40 | SIG.MSR.413 | UCN.SEC.III.5 | REPORT_PSYCHOLOGY_MIND_v1_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.413' found in L3 at lines [12, 44, 169]... but UCN ref |
