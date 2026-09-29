---
artifact: RECONCILIATION_DESIGN_SPECS
canonical_id: RECONCILIATION_DESIGN_SPECS
version: "1.3"
date: 2026-09-30
author: "Stream B (Śāstra) — Kimi Code session, campaign/pravaha"
decision: "decisions/D-SPECS_DECISION_v1_0.md (FREEZE_WITH_CONDITIONS, Fable 5.1 as the native's delegate)"
scope: "condition → changed line ranges, and nothing else (per the decision's C10). Wording in « » was adopted as written; typography adapted to file style only."
files:
  old_specs: "design/GOCHARA_DESIGN_SPECS_v1_3.md — sha256 727d174a01060226e05e78cc6b3c264e241069bae652f5c2727c1a4d8988af2d (unedited; verified post-rework)"
  new_specs: "design/GOCHARA_DESIGN_SPECS_v1_4.md (918 lines)"
  old_oracles: "design/GOCHARA_TEST_ORACLES_v1_3.json — sha256 5a7258ad14f1f167530a12e122c392e4b3a6ce2595cd0c5973ff64f6d11fb981 (unedited; verified post-rework)"
  new_oracles: "design/GOCHARA_TEST_ORACLES_v1_4.json (valid JSON; 57 oracles; 21 literal / 36 executable_at_A5.5 recounted)"
supersedes: "design/RECONCILIATION_DESIGN_SPECS_v1_2.md (round-3; retained as history)"
---

# Reconciliation v1.3 — D-SPECS conditions C1–C10 landed as specs v1.4 + oracles v1.4

Every changed line in v1.4 falls inside one of the ranges named below; `diff` v1.3 → v1.4
(both files) shows no other hunk. Ranges are v1.4 line numbers, with the v1.3 source range in
parentheses where the hunk is a replacement.

## C1 — Target inventory and class set (R4-S02, Am. 2c/2d)

- **DS v1.4 lines 214–230** (replaces v1.3 192–196): exhaustive sets rewritten verbatim per
  C1 Edit 1 — agent set incl. running MD/AD/PD lords; class set = the 27 classes by reference
  to EVALUATION_PROTOCOL_v2_2 §2; target inventory through the `object_role` enum; kārakas as
  B5.1 registry content with `computed_empty`; qualification-driven enumeration; "no other
  exclusion".
- **DS v1.4 lines 298–311** (inserted after v1.3 248): row membership by protocol class name
  verbatim per C1 Edit 2 — 18 row-mapped classes + `birth_anchor` excluded + 8 classes with
  H = unknown (P3/P4 `unqualified`, never `false`, until a cited `rule_path` row supplies H).
- Verify greps pass: "karakas per the §2.2 truth table" and "a path contact outside these sets
  is not enumerated" appear 0 times in v1.4.

## C2 — Scoring algebra closure (R4-S01, Am. 2a)

- **DS v1.4 lines 193–206** (replaces v1.3 180–184): evidence accumulation rewritten verbatim
  per C2 Edit 1 — `root_id` (contact_id on transit rows, object_id on natal-fact rows),
  per-channel per-root `max` then `Σ` over roots; order-independent; no other reduction
  permitted. "deduplicated by `contact_id`" appears 0 times in v1.4.
- **DS v1.4 lines 166–177** (v1.3 164, factor contract): codomain ⊆ [0, 1] + new field
  `calibration_status ∈ {uncalibrated_default, calibrated}` inserted verbatim per C2 Edit 2.
- **JSON v1.4 line 170** (v1.3 168): O-RP-7 `then` appended verbatim per C2 Edit 3.

## C3 — Father truth-table row and O-RP-2 reconciled (Am. 2f / R3-S02 residual)

- **DS v1.4 lines 323–334** (replaces the tail of v1.3 260–263): O-RP-2 prose rewritten
  verbatim per C3 Edit 1 — H = {Sagittarius, Capricorn, Gemini, Cancer}; māraka column =
  lords of 2nd/7th from the 9th as testimony annotations; the ONE rule evaluated twice
  ((i) restricted H′/L′ → FALSE, the D-P4 withdrawal; (ii) full H → P4_admit TRUE). DS:242
  (the truth-table row) is unchanged; "which also names 2/7/8 from the 9th as the māraka
  testimony set" appears 0 times.
- **JSON v1.4 lines 125–129** (replaces v1.3 123–127): O-RP-2 rewritten verbatim per C3
  Edit 2 — `given` gains full H + restricted H′/L′ + the 9th-aspect arithmetic; `then`
  carries both (i) and (ii); `mutation_that_must_fail` per the condition; `defects` gains
  "R4-Q2". §11.2's index still reads 9 RP oracles (unchanged, line 751 region untouched).

## C4 — P5 contradiction removed (Am. 4a, F4)

- **DS v1.4 lines 743–747** (replaces v1.3 643–644): §8.2 invariant 4 rewritten verbatim per
  C4 Edit 1 — each operand gates exactly its own form; whole build absent ⇒ all forms.
- **JSON v1.4 line 324** (v1.3 322): O-BP-2 case A now "ALL P5 forms unqualified (operand
  named: AV build)" verbatim per C4 Edit 2.
- Verify greps pass: "missing BAV ⇒ P5a/P5b" and "P5a/P5b unqualified" appear 0 times in
  either v1.4 file.

## C5 — Permission composition and O-PP-2 scope (Am. 3c/3d, F1)

- **DS v1.4 lines 529–538** (replaces v1.3 446–448): §4.1 signature rewritten verbatim per
  C5 Edit 1 — per-level `{lord, row_id, licence, relation}`, `licence ∈ {scored, testimony,
  none}`, union-over-levels composition, levels never collapsed, per-level fields the
  assertable surface. (The condition's « » text includes its own "Computed per instant …
  read per §4.0" sentence; v1.3's parallel sentence is subsumed by it.)
- **DS v1.4 lines 247–261** (inserted after v1.3 211): P1 relation-kind table verbatim per
  C5 Edit 2, closed with the corpus-read verdict — **dispositorship (non-node): no clause
  found: `testimony`; association: no clause found: `testimony`**. Corpus read (this stream,
  2026-09-30, read-only prod): PG249:C1 (śl.34–36) and PG250:C1 (śl.37–39) read verbatim;
  dispositor predicate → 0 of the 11 Adh. XX chunks PG245–255; association hits are
  Rāhu-specific (śl.39, testimony under D-PADMIT), a cross-reference (PG245:C1), or a natal
  yoga (PG253:C1 śl.47) — none is a non-node transit-permission clause.
- **JSON v1.4 lines 210–213** (replaces v1.3 208–211): O-PP-2 rewritten verbatim per C5
  Edit 3 — interior instants t₁ = 2019-08-01T00:00:00Z and t₂ = 2021-01-01T00:00:00Z named;
  L1 PD rows printed by this stream (read per the §4.0 pin: chart 482012f1, ayanamsha
  lahiri_chitrapaksha, system vimshottari, build 1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb, tier
  two_pass_verified; duplicate check over all level-2/3 rows of the pin → 0 conflicts): PD
  Saturn `a4cf46db-fcb5-479c-8aab-ca87bcb551ff` (2019-06-21T00:55:52Z → 2019-08-17T09:18:53Z)
  and PD Saturn `73eea5c0-631f-4b48-8c8f-483c910c6fde` (2020-11-04T09:13:29Z →
  2021-03-31T20:29:50Z). `then` asserts per-level licences on the AD level only; the class
  level is identical at t₁/t₂; "does NOT licence the class" appears 0 times. `fixture_kind`
  stays `literal` per the decision (Q8: O-PP-2 becomes literal with C5's named instants).

## C6 — Daśā read contract completions (Am. 3a/3b; O-PP-1 hygiene)

- **DS v1.4 lines 504–513** (v1.3 430–433 region): identical-duplicate rule and instant rule
  inserted verbatim per C6 Edit 1 (the instant rule cites EVALUATION_PROTOCOL_v2_2 §3; the
  three worked events as 18:30:00Z instants).
- **DS v1.4 lines 517–525** (replaces v1.3 437–442): reference rows — every row id printed in
  full, full timestamps (AD Ketu `133b4500-ad36-4fff-8814-c6b0b253ca05`; PD Mercury
  `6b843ad2-0759-4e7f-af7d-d39eac8b0325`; AD Moon `14f20359-c30e-425d-b50f-45b017568ace`;
  PD Venus `203406df-ddc3-44b8-a174-e48c5546d009`; PD Venus
  `5c07a7c9-0848-4e54-9f0b-2a9652101cef` — all read [L] under the §4.0 pin, tier
  two_pass_verified).
- **JSON v1.4 line 203** (v1.3 201): O-PP-1 `given` — same full ids and timestamps.
- Verify grep passes: `133b4500…` (ellipsised id) appears 0 times in either v1.4 file.

## C7 — Identity completions (Am. 1a–1c)

- **DS v1.4 line 101** (v1.3 100): §1.1 `prerequisites` cell — composite
  `(predicate_id, rule_version)` references; bare id rejected at write time.
- **DS v1.4 lines 153–157** (replaces v1.3 152–155): `rule_path` registry row —
  `prerequisites: [(predicate_id, rule_version)]`, `soft_factors: [(factor_id, rule_version)]`
  + the composite-reference sentence, verbatim per C7 Edit 1.
- **DS v1.4 lines 633–639** (inserted after v1.3 542): forward-time partitions; truncated
  contact published with `coverage.truncated = true` and ordinal = assigned + 1 ordered by
  `t_in`; enrichment in place when the centre is solved — verbatim per C7 Edit 2.
- **DS v1.4 lines 642–645** (v1.3 545): enrichment-vs-correction rule inserted verbatim per
  C7 Edit 3 (in-place update fills NULL/truncated only; any published non-NULL change = new
  id + supersedes edge). O-RX-1 unchanged.

## C8 — Honest labels, tolerances and lineage notes (Q8; F3)

- **JSON v1.4 lines 132–133, 153–154, 321–322**: O-RP-3, O-RP-5b, O-BP-2 `fixture_kind` →
  `executable_at_A5.5`, each `given` gaining its verbatim append per C8 Edit 1.
- **JSON v1.4 line 291** (v1.3 289): O-SM-1 `tolerance` → "|activity − expected| ≤ 1e-6 at
  each of the five printed samples; the discriminating sample d = 0 differs by 0.6" verbatim
  per C8 Edit 2.
- **JSON v1.4 lines 9–10**: header gains `fixture_kind_split: "21 literal / 36
  executable_at_A5.5"` and `v1_4_changes` naming C1–C10's oracle edits; `oracle_count` stays
  57 (recounted: 21 literal / 36 executable = 57).
- **DS v1.4 lines 843–845** (v1.3 740): §11.1 states the same 21/36 split.
- **DS v1.4 lines 883–885** (v1.3 778): the "v1.3 note" gains the v1.4 sentence (count
  unchanged at 57; three relabels; O-RP-2, O-RP-7, O-PP-1, O-PP-2, O-BP-2, O-SM-1 edited in
  place).
- **DS v1.4 lines 889–893** (replaces v1.3 782–783) and **JSON v1.4 line 24** (v1.3 22): the
  Venus sentence replaced verbatim per C8 Edit 4 (two [L] reads disagree — 259.1882 vs
  259.1727; carried as 259.19 pending a fact_id-pinned read; no printed arithmetic depends on
  it). "v1.0's 259.17 was an error/wrong" appears 0 times.

## C9 — `affected_person` enum closed (F2)

- **DS v1.4 line 92** (v1.3 91): enum closed verbatim per C9 — `native | father | mother |
  spouse | child | sibling`, extension requires a migration and a `rule_version` bump; the
  "…" is removed (0 occurrences in §1.1 enum cells).

## C10 — Versioning and verification discipline

- **DS v1.4 lines 4, 8–9, 11, 16** (v1.3 4, 8, 10, 15): frontmatter `version: "1.4"`,
  `decision:` naming D-SPECS_DECISION_v1_0, `supersedes:` v1.3 with full sha256
  727d174a01060226e05e78cc6b3c264e241069bae652f5c2727c1a4d8988af2d, `reconciliation:` → this
  file, `oracle_file:` → v1_4.json. `status:` stays "REWORKED_PENDING_NATIVE — NOT FROZEN".
- **DS v1.4 line 21** (v1.3 20): document title re-versioned.
- **DS v1.4 lines 912–914, 917–918** (v1.3 802, 805–806): footer gains the B3.8d rework
  sentence; the closing sentence now names the steward's diff before B3.9.
- **JSON v1.4 lines 3, 6–7** (v1.3 3, 6–7): `version: "1.4"`, `spec:` → v1_4.md,
  `supersedes:` → v1_3 sha256 5a7258ad14f1f167530a12e122c392e4b3a6ce2595cd0c5973ff64f6d11fb981.
- v1.3 hashes verified unchanged after the rework (recomputed: specs 727d174a…, oracles
  5a7258ad…). The steward's `diff` of v1.4 vs v1.3 shows changes only inside the ranges
  above; then, and only then, B3.9 marks FROZEN.
