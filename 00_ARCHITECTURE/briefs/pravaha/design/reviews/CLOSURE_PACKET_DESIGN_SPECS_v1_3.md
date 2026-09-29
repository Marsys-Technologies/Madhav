---
artifact: CLOSURE_PACKET_DESIGN_SPECS
canonical_id: CLOSURE_PACKET_DESIGN_SPECS
version: "1.3"
status: READY_FOR_REVIEW — contract items only (B3.8b); protocol items are the B4.5/D-PROTO track, out of scope here
date: 2026-09-30
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
scope: "Contract (D-SPECS) closure of the round-3 review, for the steward-dispatched Codex round (B3.8c). Protocol (D-PROTO) findings are dispositioned in RECONCILIATION_DESIGN_SPECS_v1_2.md §2/§6 and land as v2.2 artifacts under B4.5 — please do not re-review them here."
reviewed_artifacts: "design/GOCHARA_DESIGN_SPECS_v1_3.md (sha256 727d174a01060226e05e78cc6b3c264e241069bae652f5c2727c1a4d8988af2d) · design/GOCHARA_TEST_ORACLES_v1_3.json (sha256 5a7258ad14f1f167530a12e122c392e4b3a6ce2595cd0c5973ff64f6d11fb981) · design/RECONCILIATION_DESIGN_SPECS_v1_2.md"
ground_rules: "Read-only. Cite file:line. Judge closure against the round-3 requested changes, not against new scope. A reviewed file is never edited — findings go against v1.3 as it stands."
---

# Closure packet — design specs v1.3 (contract items only, B3.8b)

One question per round-3 contract blocker: **is it closed, and is the closure evidence sound?**
The reconciliation (RECONCILIATION_DESIGN_SPECS_v1_2.md) is the map; the artifacts are the
evidence. Line references below are to the v1.3 files.

## Q1 — R3-S01 (O-PP-2 controls)

v1.3 O-PP-2 (oracles JSON): positive control Mercury/Mars AD row
`b1e4d515-6a94-4054-89ff-1ed2487f66ae` (2019-02-17T06:50:23Z → 2020-02-14T11:47:23Z), Mars
natal 198.52° Libra = 7th-house occupant (scored occupancy); negative control Mercury/Rahu
AD row `25a4b815-39bb-4b4a-b922-84a71778bb4f`, with the Venus-dispositor chain named and
marked testimony-only (D-PADMIT); boundary 2020-02-14T11:47:23Z under the half-open
convention; 2018-11-28 stated as Mercury/Moon. Spec §4.3 carries the same text.
**Judge:** are these controls sound under the pinned Lahiri build, and is the negative case's
lack of a *scored* path proven rather than asserted?

## Q2 — R3-S02 (one P4 rule)

v1.3 spec §2.2 P4: `infl(g) := (∃h∈H: contact(g,h)) ∨ (∃ℓ∈L(H): contact(g,ℓ))`;
`P4_admit := infl(Jupiter) ∧ infl(Saturn)`. O-RP-2 (father): infl(Jupiter) = FALSE with the
transit-to-natal arithmetic printed (Δ = 29.48°; aspect signs Pisces/Taurus/Cancer);
restricted-negative-test label. O-RP-3 (childbirth): same rule, both agents TRUE.
**Judge:** do both fixtures obey the one rule, and is the father case's geometry correct?

## Q3 — R3-S03 (synthetic AV provenance)

v1.3 O-BP-1: synthetic rows labelled `fixture=true` with explicit keys; real extract rows
cited for contrast (constants.av_extracts prints the real SARVA vector and the real Mars BAV
minimum 1); a provenance mutation added. O-BP-5: real Aquarius SARVA = 23, fact_id
`36b81039eeb707a7`, against config 28. Extracts untouched.
**Judge:** can any reader still mistake the synthetic rows for extract data?

## Q4 — D-SPECS amendment 1 (typed identity)

v1.3 §1.1 (record key includes generation + contact_id; tagged `temporal_support`;
unknown-admission; `source_fact_ids`), §2.1 (version-qualified composite PKs/FKs), §6.1
(ordinal domain pinned in `convention_id`; appends-only partition extension; publication
immutability; canonical serialization). O-RX-1 carries the identity bytes and the extension
case. **Judge:** does anything in the round-3 R2-S01/S02 residuals remain open?

## Q5 — D-SPECS amendment 2 (scoring algebra + sets)

v1.3 §2.1: factor `function`/`range`/`units` fields; evidence = sum over records deduped by
`contact_id` per path; exhaustive agent/class/target sets. **Judge:** is the shared-root
aggregation rule implementable as written?

## Q6 — D-SPECS amendment 3 (daśā read contract)

v1.3 §4.0: full pin (chart, ayanamsha, system, build `1f89fd4c-…`, tier), half-open
convention, parent linkage, duplicate-row rule, reference rows with PD lords **Mercury,
Venus, Venus** printed. O-PP-1 asserts those PD values; O-RR-2 pins the MD/AD rows.
Reconciliation §4 C.2 records the corrected ayanamsha conclusion (the v1_1 "no variant
explains" claim is withdrawn as wrong — O-PP-1 was right). **Judge:** is the contract
sufficient that no future read can repeat B38-F1?

## Q7 — D-SPECS amendment 4 (P5 semantics)

v1.3 §2.2 P5 missing-input matrix (each operand gates exactly its own form); P5a nonzero
comparator explicitly `unresolved`, scored output = known-zero detection only; O-BP-2 case C
(SAV missing ⇒ P5b alone). **Judge:** is the BAV/SAV contradiction gone and the unresolved
state honest?

## Q8 — D-SPECS amendment 5 (fixture contract)

v1.3 §11.1 fixture-kind policy; labels now **24 literal / 33 executable_at_A5.5** (count
57 = 57, header = index = array). The four named defects fixed: O-VI-2 (half-open convention;
2025-03-01 in the clean interval), O-SM-1 (clean parabola λ = 305.5° − 0.0005°·d² with
per-sample expected values printed; time-triangle discriminating sample d=0: 1.0 vs 0.4),
O-RX-1 (identity bytes + extension case), O-RP-5a (named class `illness_acute`).
**Judge:** are the labels truthful now — is every remaining `literal` fixture actually
buildable from its `given` without asking a question?

## Out of scope for this round (B4.5 / D-PROTO track)

R2-M01, R2-M03, R2-M04, R2-M05, R2-M06, R2-M07, R3-P01 — dispositioned in the
reconciliation §2/§6; artifacts land as EVENT_REGISTRY v2.2 (+ machine-readable JSON),
EVALUATION_PROTOCOL v2.2, scorer v2.2 re-run, BASELINE_3_0 v2.2. No candidate scoring occurs
before the native closes D-PROTO.
