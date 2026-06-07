# SUPPORTS Edge Reconciler — Batch B4_supports_batch3

**Session:** Madhav_M2A_Exec_7  
**Date:** 2026-04-26  
**Raw response:** `2026-04-26_B4_supports_batch3_raw.md`  
**Reconciler:** `cgm_supports_reconciler.py`  

---

## §1 — Result Summary

| Metric | Count |
|--------|-------|
| Proposed | 28 |
| Accepted | 7 |
| Rejected (total) | 21 |
| → Rejected P1 (L3 report validity) | 0 |
| → Rejected P2 (UCN section validity / l1_basis) | 0 |
| → Rejected P5 (signal_id resolution) | 0 |
| → Rejected L3 chain | 21 |

---

## §2 — Per-Edge Verdict Table

| # | source_signal_id | target_ucn_section_id | l3_evidence_report | verdict | P1 | P2 | P5 | L3 chain | notes |
|---|---|---|---|---|---|---|---|---|---|
| 1 | SIG.MSR.407 | UCN.SEC.IV.4 | REPORT_FINANCIAL_v2_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 2 | SIG.MSR.407 | UCN.SEC.V.7 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.407' found in L3 at lines [53]... but UCN ref '§V.7' n |
| 3 | SIG.MSR.407 | UCN.SEC.VIII.3 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.407' found in L3 at lines [53]... but UCN ref '§VIII.3 |
| 4 | SIG.MSR.407 | UCN.SEC.IX.2 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.407' found in L3 at lines [53]... but UCN ref '§IX.2'  |
| 5 | SIG.MSR.391 | UCN.SEC.IV.4 | REPORT_FINANCIAL_v2_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 6 | SIG.MSR.391 | UCN.SEC.V.7 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.391' found in L3 at lines [81, 175]... but UCN ref '§V |
| 7 | SIG.MSR.391 | UCN.SEC.VIII.3 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.391' found in L3 at lines [81, 175]... but UCN ref '§V |
| 8 | SIG.MSR.391 | UCN.SEC.IX.2 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.391' found in L3 at lines [81, 175]... but UCN ref '§I |
| 9 | SIG.MSR.404 | UCN.SEC.IV.4 | REPORT_FINANCIAL_v2_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 10 | SIG.MSR.404 | UCN.SEC.V.7 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.404' found in L3 at lines [28, 110, 113]... but UCN re |
| 11 | SIG.MSR.404 | UCN.SEC.VIII.3 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.404' found in L3 at lines [28, 110, 113]... but UCN re |
| 12 | SIG.MSR.404 | UCN.SEC.IX.2 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.404' found in L3 at lines [28, 110, 113]... but UCN re |
| 13 | SIG.MSR.435 | UCN.SEC.IV.4 | REPORT_FINANCIAL_v2_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 14 | SIG.MSR.435 | UCN.SEC.V.7 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.435' found in L3 at lines [131]... but UCN ref '§V.7'  |
| 15 | SIG.MSR.435 | UCN.SEC.VIII.3 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.435' found in L3 at lines [131]... but UCN ref '§VIII. |
| 16 | SIG.MSR.435 | UCN.SEC.IX.2 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.435' found in L3 at lines [131]... but UCN ref '§IX.2' |
| 17 | SIG.MSR.436 | UCN.SEC.IV.4 | REPORT_FINANCIAL_v2_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 18 | SIG.MSR.436 | UCN.SEC.V.7 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.436' found in L3 at lines [131]... but UCN ref '§V.7'  |
| 19 | SIG.MSR.436 | UCN.SEC.VIII.3 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.436' found in L3 at lines [131]... but UCN ref '§VIII. |
| 20 | SIG.MSR.436 | UCN.SEC.IX.2 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.436' found in L3 at lines [131]... but UCN ref '§IX.2' |
| 21 | SIG.MSR.438 | UCN.SEC.IV.4 | REPORT_FINANCIAL_v2_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 22 | SIG.MSR.438 | UCN.SEC.V.7 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.438' found in L3 at lines [152]... but UCN ref '§V.7'  |
| 23 | SIG.MSR.438 | UCN.SEC.VIII.3 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.438' found in L3 at lines [152]... but UCN ref '§VIII. |
| 24 | SIG.MSR.438 | UCN.SEC.IX.2 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.438' found in L3 at lines [152]... but UCN ref '§IX.2' |
| 25 | SIG.MSR.024 | UCN.SEC.IV.4 | REPORT_FINANCIAL_v2_1.md | **ACCEPT** | ✓ | ✓ | ✓ | ✓ |  |
| 26 | SIG.MSR.024 | UCN.SEC.V.7 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.024' found in L3 at lines [152]... but UCN ref '§V.7'  |
| 27 | SIG.MSR.024 | UCN.SEC.VIII.3 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.024' found in L3 at lines [152]... but UCN ref '§VIII. |
| 28 | SIG.MSR.024 | UCN.SEC.IX.2 | REPORT_FINANCIAL_v2_1.md | **REJECT** | ✓ | ✓ | ✓ | ✗ | L3_CHAIN: signal 'SIG.MSR.024' found in L3 at lines [152]... but UCN ref '§IX.2' |
