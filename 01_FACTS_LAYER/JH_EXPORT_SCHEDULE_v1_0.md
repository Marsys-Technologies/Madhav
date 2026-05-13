---
artifact: JH_EXPORT_SCHEDULE_v1_0.md
version: "1.0"
status: PROPOSED (pending native confirmation)
layer: L1
authored_session: M5-A-S1
authored_date: 2026-05-13
execution_owner: Native (Abhisek Mohanty)
execution_tool: Jagannatha Hora (installed)
---

# JH Export Schedule — M5 Requirements

## §1 — Purpose

This document records the three Jagannatha Hora export items required for M5 work. These exports are not blocking M5-A or M5-B but are prerequisites for M5-C (DBN topology finalization) and M5-D (DBN fitting).

## §2 — Three Export Items

### (a) Sthana + Drik Strength Export

**What:** Export Sthana Bala (positional/residential strength) and Drik Bala (aspectual strength) for all 9 natal planets.

**JHora menu:** Shadbala → Shadbala calculation → export/screenshot all 6 components including Sthana Bala and Drik Bala rows.

**Why M5 needs it:** The DBN edge topology uses signal strength scores. Current MSR strength_scores use the existing FORENSIC v8.0 values. Sthana+Drik at higher precision will allow edge weight calibration in M5-C.

**Integration target:** FORENSIC v8.0 §4 Shadbala table patch + MSR `strength_score` field updates where discrepancy > 0.05.

**Estimated native effort:** 15 minutes JH export + Claude integration session 1 hour.

---

### (b) ECR for Sthana/Drik Discrepancies vs FORENSIC v8.0

**What:** After export (a), compare JH values against the Shadbala values in FORENSIC v8.0 §4. Flag any discrepancy where the JH value differs from the recorded value by more than the stated precision threshold.

**Integration target:** FORENSIC v8.0 §4 patch; flagged discrepancies → `EXTERNAL_COMPUTATION_SPEC_v2_0.md §2` ECR (External Computation Record) entries.

**Note:** This is a derived step after (a). Claude can perform the comparison once the JH export is provided.

---

### (c) Narayana Dasha Verification

**What:** Verify the Narayana Dasha sequence for the native's chart against the Chara Dasha values in FORENSIC v8.0 §5.3.

**JHora menu:** Dasha → Narayana Dasha → compute for Aries Lagna, DOB 1984-02-05, 10:43 IST, Bhubaneswar.

**Why M5 needs it:** Chara Dasha is used in M5 DBN temporal slicing. If the JH Narayana sequence differs from the recorded Chara sequence, it needs to be resolved before temporal-node binning in M5-B.

**Integration target:** FORENSIC v8.0 §5.3 cross-check; discrepancies flagged as ECR items.

**Estimated native effort:** 10 minutes export + verification.

---

## §3 — Proposed Window

| Phase | Export Item | Proposed By | Status |
|---|---|---|---|
| Before M5-C open | (a) Sthana+Drik | M5-A-S1 | PROPOSED |
| Concurrent with (a) | (b) ECR comparison | Claude (derived from a) | PROPOSED |
| Before M5-B close | (c) Narayana Dasha verification | M5-A-S1 | PROPOSED |

**Target:** All three items complete before M5-C (DBN topology finalization). This is not blocking M5-A or M5-B.

## §4 — Native Action

At the next Cowork session, native confirms or adjusts the window. Once confirmed, this document's status changes from PROPOSED → SCHEDULED.

---

*Authored M5-A-S1 (2026-05-13). Pending native confirmation.*
