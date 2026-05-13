---
artifact: LEL_HELD_OUT_PARTITION_v1_0.md
version: "1.0"
canonical_id: LEL_HELD_OUT_PARTITION
layer: L1
status: CURRENT
authored_session: M5-A-S1
authored_date: 2026-05-13
sacrosanct_until: M5-D (DBN fitting phase)
source_manifest: 06_LEARNING_LAYER/OBSERVATIONS/lel_event_match_records.json §held_out_manifest
---

# LEL Held-Out Partition — Formal Declaration

## §1 — Purpose

This document formally declares the held-out partition of the LEL corpus for M5 purposes. These 9 events are **sacrosanct**: they must not be seen by any learning mechanism before M5-D (DBN fitting). No prediction may be conditioned on their outcomes during retroactive PPL construction (Item 8, M5-A). No LL.2/LL.7/LL.1 computation may use them as training signal.

This declaration closes AC.M5A.11 (formal written declaration in L1 that the held-out set is locked).

## §2 — Selection Methodology

Decade-stratified per AC.M4A.4 (≈20% of 46 events = 9). Preference: EXACT or month-exact dates (higher-confidence test cases); spread of categories; later dates within decade. Source: `lel_event_match_records.json §held_out_manifest` (produced M4-A-INTEGRATION-PASS-R3, 2026-05-02).

## §3 — The 9 Held-Out Events

| Event ID | Date | Category | Description (brief) |
|---|---|---|---|
| `EVT.2008.06.09.01` | 2008-06-09 | career | Exited Cognizant after 1 year; returned to Bhubaneswar for IIT re-attempt |
| `EVT.2009.06.XX.01` | 2009-06 | loss | Paternal grandfather passed (academic mentor — major emotional setback) |
| `EVT.2017.03.XX.01` | 2017-03 | career | Mahindra Retail → Tech Mahindra switch; leads to US deputation 2019 |
| `EVT.2018.11.28.01` | 2018-11-28 | loss | Father passed away (28 Nov 2018; culminating 18-year kidney disease journey) |
| `EVT.2019.05.XX.01` | 2019-05 | residential+travel | US work deputation begins (Tech Mahindra; 4-year stint to May 2023) |
| `EVT.2022.01.03.01` | 2022-01-03 | family | Twin daughters born (native's only children) |
| `EVT.2024.02.16.01` | 2024-02-16 | career | Launched Kotadwara sand-mining operation at Bhanti (Marsys Group) |
| `EVT.2025.05.XX.01` | 2025-05 | loss | Major deception/fraud event |
| `EVT.2026.01.XX.01` | 2026-01 | other | Sustained psychological shift — long-standing distractions replaced by one-pointed business focus |

## §4 — Sacrosanctity Rules

1. **No training use until M5-D.** These 9 events must not be inputs to LL.1, LL.2, LL.5, LL.6, LL.7, or any other learning mechanism update prior to M5-D fitting.
2. **PPL retroactive blind protocol.** When constructing retroactive predictions (Item 8, M5-A) for the held-out events, predictions must be formulated using only training-partition chart signals + already-computed PPL predictions. The held-out event's *outcome* must not be read until after the retroactive prediction is written and recorded.
3. **No override without native approval.** Reclassifying a held-out event to training requires a NAP decision recorded in SESSION_LOG.

## §5 — Decade Distribution

| Decade | Count | Event IDs |
|---|---|---|
| 2000–2009 | 2 | EVT.2008.06.09.01, EVT.2009.06.XX.01 |
| 2010–2019 | 3 | EVT.2017.03.XX.01, EVT.2018.11.28.01, EVT.2019.05.XX.01 |
| 2020–2026 | 4 | EVT.2022.01.03.01, EVT.2024.02.16.01, EVT.2025.05.XX.01, EVT.2026.01.XX.01 |

## §6 — Cross-References

- Source manifest: `06_LEARNING_LAYER/OBSERVATIONS/lel_event_match_records.json §held_out_manifest`
- Phase plan gate: `PHASE_M5_PLAN_v1_0.md §3 Item 11`
- PPL retroactive protocol: `01_FACTS_LAYER/PPL_RETROACTIVE_PROTOCOL_v1_0.md` (to be created at Item 8)
- M5-D unlock: PHASE_M5_PLAN_v1_0.md §3 M5-D scope

---

*Authored M5-A-S1 (2026-05-13). Partition locked until M5-D.*
