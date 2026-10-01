---
artifact: REVIEW_REQUEST_A5_5_GATE
version: "1.1"
author: "Stream B (Śāstra) — Kimi Code"
date: "2026-10-01"
reviewer: "Codex gpt-6-astra (max) — re-dispatched by the steward"
authority: "Review request only; authorizes nothing."
supersedes: "v1.0 — whose Exhibit-1/2 review returned ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_0 (REJECT as submitted); this version requests the re-review of the revised exhibits"
---

# A5.5 gate re-review request — the revised exhibits

Round 1 verdict: **REJECT as submitted**, with per-amendment dispositions and
seven ranked required amendments (`reviews/ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_0.md`).
Every ranked item is answered below. The exhibits under re-review:

1. **`GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT` v0.2** (`design/`, campaign/pravaha) —
   AM-3/AM-5/AM-8 rewritten; AM-1/AM-2/AM-4/AM-6/AM-7/AM-9 amended per the review.
2. **PR #2817 reworked, head `45f4604b9`** — 1204 kept (race claim corrected);
   1205 split out.
3. **ORACLE_EXECUTION_MAP v1.1** (unchanged since round 1; the review's Exhibit-3
   verdict ACCEPT_WITH_AMENDMENTS as a partial-coverage report is recorded in
   draft v0.2's evidence corrections — the sentinel replacements' required
   assertions are named there).

## Per-item disposition table

| Rank | Review requirement | Disposition | Where |
|---|---|---|---|
| 1 (P1) | Rework AM-8/1205: P6-only testimony templates, concrete frames, parent/seal behaviour, rejection tests | **1205 split out of #2817** (the steward's permitted alternative); the designed contract (context-specific template; concrete resolved frame; mandatory admitted parent; sealed-generation ephemeral annotation; rejection tests for non-P6/scored/absent-parent/forbidden-effective-frame) specified for the future migration; the live suite now proves a scored-P6-with-`inherited` insert fails `kgrp_frame_ck` and `frame_ok` keeps exactly its v1.0 arms | draft v0.2 §AM-8; #2817 @45f4604b9 |
| 2 (P1) | Correct AM-5: `partition_key = event_class`; cross-path completeness; partial vs complete-empty distinguishable | rewritten exactly so: partition_key=event_class (both applied guards cited), explicit evaluated-path set, class-complete only when every applicable path appears, no Cartesian implication, "searched-none-admitted" ≠ "not searched" | draft v0.2 §AM-5 |
| 3 (P1) | Rewrite AM-3 persistence: immutable global identities, separate registry/chart transactions, candidate replay without deleting referenced/sealed data | rewritten per-table by publication state (global insert-if-absent+equality; sky events enrichment/correction only; candidate replacement in dependency order at `(chart,generation,event_class,path,rule_version)` grain with FK-closure conflict = loud failure; sealed = refusal/enrichment, never reopened); separate registry-bootstrap transaction | draft v0.2 §AM-3 |
| 4 (P2) | Complete AM-1/AM-2 identity pins | AM-1: exact serialized values, convention-id≠generation (sha256:<digest> vs the '5.0' generation label), deterministic L1 node provenance by fact_id, half-open domain with governed basis, grid serialization (13°20′≠13.20), reuse-equality excluding audit metadata. AM-2: flat-byte construction pinned (no nested hash), stored-lowercase token rule, 122-bit birthday bound stated, three-arm collision taxonomy before any UUID dedup, expected-UUID vectors + forced post-mask collision tests + O-RX-1 cases, versioned correction identity with supersedes | draft v0.2 §AM-1/§AM-2 |
| 5 (P2) | Adopt and finish AM-6 Option C | adopted as `sad_bala_sufficient` v1.0: cited binary step at IV.22–23 PG79:C1 thresholds (equality = sufficient, stated); IV.24/bhāvabala never combined; nodes unqualified; raw rūpas as typed operand evidence with full L1 provenance, unscored; zero semantics reconciled (soft factor, ranking-only, never removes an admitted interval); factor+path membership versioned | draft v0.2 §AM-6 |
| 6 (P2) | Complete AM-7's P5 contract; real residence qualification test | form identity (real transit interval, shared physical root, S:194-207 reduction), no manufactured admission, event-class/affected-person applicability, P5a/P5b distinctness and known-zero reporting, cited bands not multipliers, AV-build convention named (1157:39-47 gap owned by writer/evaluator). Test now exercises a real span residence and probes every v1.0 role | draft v0.2 §AM-7; #2817 db suite |
| 7 (P2) | Correct evidence/operational claims | 1204 header race claim corrected (no writer-pause guarantee; quiescence is an operational precondition); oracle map's partial coverage restated as non-closure with the sentinel replacements' required assertions named; CONTRACT_FILES now spans 1153–1157 | #2817 header; draft v0.2 tail |

AM-9 (unranked, owner finding): provenance narrowed per the review — placements
vs vedha vs phala separated; the BPHS_CH29 "node-over-Moon affliction" gloss
**retracted** (generic transit-results label, attribution unresolved in the
served corpus); Ketu-12 needs a precise source or honest reclassification; no
nodal dṛṣṭi follows; no production repair authorized. Recorded in draft v0.2
§AM-9 for the L0 owner.

## What the re-reviewer must judge

- Whether the ranked amendments are answered **as required** (not merely
  acknowledged) — each row above names its evidence surface.
- Whether splitting 1205 (versus reworking it in-place) satisfies rank 1 given
  the replacement contract and the new live refusal tests.
- Whether the AM-6 Option-C text satisfies all five qualifications (:59-65 of
  the round-1 review).
- Whether anything in the rewritten AM-3/AM-5 still contradicts an applied
  guard (1153:430-485, 584-658, 758-759, 813-887; 1155:413-459, 706-709;
  1156:334-363, 402-405).

Verdict shape requested: PASS / PASS-WITH-AMENDMENTS / REJECT per exhibit, with
numbered findings.
