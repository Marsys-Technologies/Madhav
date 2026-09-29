---
artifact: CLOSURE_PACKET_DESIGN_SPECS
canonical_id: CLOSURE_PACKET_DESIGN_SPECS
version: "1.2"
status: PARKED_AWAITING_THIRD_ROUND
date: 2026-09-30
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
purpose: >
  Closure map for the narrow third review round (steward's standing authority: Codex only —
  closure of its round-2 blockers, plus Kimi NK-1/NK-2). Each blocker is listed with exactly
  where v1.2/v2.1 closes it. Reviewer is asked to verify closure, not to re-review the corpus.
reviewed_files: "GOCHARA_DESIGN_SPECS_v1_2.md (sha256 5bfe1553d404be59f9b0246fcf410fe5a09be6946b5d97da6d733ecede45b039), GOCHARA_TEST_ORACLES_v1_2.json (c11a9d7e5ccf3a6c4a53569da5383ea7531ce840e48cfa6f7e0b8e2310143a43), EVALUATION_PROTOCOL_v2_1.md (21de59943b335abb3df393810155c2a0d07315c5b1ae7fee5d54e93e7f5c7f1d), EVENT_REGISTRY_v2_1.md (ec738020dd2fbbe492317089a8ac5723169756740de932cea408aeb5cde7f34c), BASELINE_3_0_v2_1.md (b4c46222fe23fbd51b5028004d11a11cfafb422de124c23c4f4867bfb8a4ce60)"
map_of_record: "design/RECONCILIATION_DESIGN_SPECS_v1_1.md — full dispositions and all hashes"
---

# Closure packet — third round (narrow)

## A. Codex round-2 blockers → closure locations

| blocker | closed at |
|---|---|
| R2-S01 typed contract (contact_id, generation, FKs, tagged nulls, signature-house) | specs v1.2 §1.1 (new columns + null rules; object_role += signature_house) |
| R2-S02 episode identity vs object identity | specs v1.2 §6.1 contact_id + occurrence_ordinal; oracle O-RX-1 |
| R2-S03 score algebra; O-RP-2/P4 contradiction | specs v1.2 §2.1 (within-path product + null propagation); O-RP-2 rewritten, scoped to the father target set |
| R2-S04 AV comparator, P5 matrix, O-BP-5 band, G-10 payload | specs v1.2 §2.2 P5 availability matrix + §8.1; extracts v1_0/v1_1; O-BP-5 (24 vs 28), O-BP-1 competing values |
| R2-S05 O-RP-5 fixture split | O-RP-5a (scored 8th, Saturn 172.00° Virgo) / O-RP-5b (testimony 12th, zero effect) |
| R2-S06 placeholder fixtures; O-AD-4 | O-AD-4 Cancer; fixture_kind labels on all 57; literals per NK-7; O-SM-3/O-AO-2 positive controls |
| R2-M01 registry (SPR.D, grains, vertigo, count) | EVENT_REGISTRY_v2_1 (47 = 30 + 17; 57 = 3+47+7) |
| R2-M02 T-FP estimand | protocol v2.1 §6.4 — single all-observed-time estimand, one denominator; scorer v2.1 |
| R2-M03 degeneracy before rank; peak-diversity | protocol v2.1 §8 + §6.3; scorer: 0/30 → rank-unproven |
| R2-M04 interval N, signed intensity, aggregation | protocol v2.1 §4.3/§6.3/§9.5; scorer v2.1 |
| R2-M05 controls (61 d, off-by-one) | random_controls_v1_1.json (seed 482012; 645/940 = 68.6 %) |
| R2-M06 coverage manifest, polarity table, annotation guard | protocol v2.1 §6.5 (T-honesty UNVERIFIABLE; manifest = build requirement), §2, §7 (guard disclosed manual for the pinned re-run) |
| R2-M07 baseline narrative | BASELINE_3_0_v2_1 (no-observed-separation; 22/5/0; 15/16; NK-5 dedup table) |

## B. Kimi round-2 blockers → closure locations

| blocker | closed at |
|---|---|
| NK-1 registry omission + arithmetic | EVENT_REGISTRY_v2_1 §3 row 41; header 57 = 3+47+7; BASELINE_3_0_v2_1 (32/47; floor 16) |
| NK-2 occurrence identity | specs v1.2 §6.1; O-RX-1 (three crossings, ordinals 1/2/3, one object) |

## C. Items the third round is explicitly asked to judge

1. Whether each closure in §A/§B actually closes the blocker as written (not a paraphrase).
2. **B38-F1 (self-found, deferred):** O-PP-1's expected MD/AD values (Mercury/Ketu at
   2013-12-11; Mercury/Moon at 2018-11-28; Mercury/Rāhu at 2022-01-03) contradict L1
   `chart_dashas` (vimshottari: Mercury/Sun, Mercury/Rahu, Mercury/Saturn respectively).
   Judge: defect in O-PP-1's `then` values, or a dasha-source discrepancy the spec must name.
3. Whether the G-10 caveats are carried honestly: tier `single_pass` verbatim; build
   aa9602ce vs 1c092ffb answered by recompute only; `pinda_sarva` per-subject split flagged
   not recompute-covered; P5c disabled as rebuild-pending (#2731), not sourceless.
4. Whether oracles v1.2's `given` fields are now literal enough to build a fixture from
   without asking a question — and whether the `fixture_kind` labels are truthful.

*Stream B does not dispatch reviewers. The packet is ready; B3.8 is parked with this path.*
