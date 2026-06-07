---
artifact: PPL_RETROACTIVE_PROTOCOL_v1_0.md
version: "1.0"
status: CURRENT
layer: L1 (governance)
authored_session: M5-A-S1
authored_date: 2026-05-13
purpose: "Blind retroactive prediction protocol for PPL held-out event coverage"
---

# PPL Retroactive Protocol v1.0

## §1 — Purpose

This document specifies the retroactive blind prediction protocol for building held-out PPL coverage prior to M5-D fitting. The M6 gate requires ≥20 verified retroactive predictions (from ≥20 unique held-out events or event clusters). As of M5-A-S1, the ledger has 16 entries — all prospective (future windows). This protocol governs how retroactive predictions against held-out LEL events are constructed, blinded, and recorded.

## §2 — The Blind Protocol

A retroactive prediction is only valid for calibration if it follows this sequence:

1. **Read the chart state only** — dasha (Vimshottari MD/AD), Chara dasha, Sade Sati phase, relevant natal signals from training partition. Do NOT read the event outcome in the LEL.
2. **State the prediction** — claim_text, domain, confidence level, falsifier, outcome condition. Record to ledger.
3. **Lock the record** — mark `retroactive: true`, `outcome_blinded_at` = timestamp.
4. **Read the outcome** — now read the event in LEL and record `outcome` and `outcome_verdict` (CONFIRMED / CONTRADICTED / PARTIAL).
5. **Record accuracy** — update the ledger entry with outcome fields.

**Sacrosanctity rule:** The 9 held-out events (declared in `LEL_HELD_OUT_PARTITION_v1_0.md`) are the target corpus. No retroactive prediction may be formulated against a training-partition event (those were used in LL.2/LL.7 computation and would be circular).

## §3 — Step 2 Discipline (How to Formulate the Prediction)

When reading only the chart state (dasha + natal signals) for a held-out event, the prediction must:

- Cite specific signal IDs (MSR.*) or dasha constructs from training partition
- Name a domain and a direction (positive/negative/transformative)
- Be specific enough to be falsifiable — "something will happen" is not acceptable
- Acknowledge uncertainty where the chart is ambiguous

The formulator **cannot** use knowledge of the outcome to post-hoc rationalize the prediction. In a fully live system this is enforced by temporal ordering. In M5-A retroactive mode, the discipline is self-enforced and must be declared in the ledger entry.

## §4 — Volume Target

| Milestone | Threshold |
|---|---|
| M5-A close | ≥20 total predictions (16 existing + ≥4 retroactive) |
| M5-C | ≥25 total (at least 9 of 9 held-out events covered) |
| M6 gate | ≥20 verified retroactive entries with outcome_verdict recorded |

## §5 — NAP.M5.0 — Cadence Proposal

**Proposed decision for native approval:**

> "PPL ongoing cadence: (a) Every prediction-relevant session emits ≥1 new PPL entry before close. (b) Retroactive held-out predictions: one per Cowork session until all 9 held-out events are covered (target: M5-C). (c) Outcome-recording cadence: when a held-out event's verification window passes, the outcome is recorded within the next session. (d) Gate review: at every macro-phase close, the native reviews and spot-verifies ≥2 PPL outcomes against lived experience."

**NAP.M5.0 status:** PROPOSED — pending native approval at Cowork-M5-S3 or equivalent.

## §6 — M5-A-S1 Retroactive Batch

Four retroactive predictions constructed at M5-A-S1 (2026-05-13):

| PRED ID | Event | Verdict |
|---|---|---|
| PRED.015 | EVT.2008.06.09.01 | CONFIRMED |
| PRED.016 | EVT.2018.11.28.01 | CONFIRMED |
| PRED.017 | EVT.2022.01.03.01 | CONFIRMED |
| PRED.018 | EVT.2017.03.XX.01 | CONFIRMED |

All 4 confirmed — calibration note: all 4 were high-confidence dasha-matching predictions. This represents the easy end of the held-out corpus. Remaining 5 events (EVT.2009.06.XX.01, EVT.2019.05.XX.01, EVT.2024.02.16.01, EVT.2025.05.XX.01, EVT.2026.01.XX.01) should be covered before M5-C.

---

*Authored M5-A-S1 (2026-05-13).*
