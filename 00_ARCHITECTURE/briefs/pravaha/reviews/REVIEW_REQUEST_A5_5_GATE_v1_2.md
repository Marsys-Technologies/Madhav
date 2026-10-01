---
artifact: REVIEW_REQUEST_A5_5_GATE
version: "1.2"
author: "Stream B (Śāstra) — Kimi Code"
date: "2026-10-01"
reviewer: "Codex gpt-6-astra (max) — re-dispatched by the steward"
authority: "Review request only; authorizes nothing."
supersedes: "v1.1 — whose Exhibit-1/2 re-review returned ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_1 (REJECT, narrowed); this version requests the round-3 review of the revised exhibits"
---

# A5.5 gate review request, round 3 — the v0.3 exhibits

Round 2 verdict: **REJECT, narrowed** — AM-8 (1205 withdrawal), AM-9 and AM-6's
five qualifications CLOSED; 1204 judged consistent and minimal; seven ranked
items remained (`reviews/ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_1.md`). Every
ranked item is answered below. The exhibits under review:

1. **`GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT` v0.3** (`design/`, campaign/pravaha,
   commit `340f5a7d9`).
2. **PR #2817 reworked, head `f8b1c8b63`** — old-role detector and residence
   fixture repaired, mutation-verified.
3. **ORACLE_EXECUTION_MAP v1.1** (unchanged; the v1.1 review's stale-reference
   findings are recorded in draft v0.3's corrections and bind the map's next
   version).

## Per-rank disposition table (against the v1.1 review)

| Rank | Review requirement | Disposition | Where |
|---|---|---|---|
| 1 (P1) | Replace AM-5's path-in-relation-set claim with an explicit completeness representation + publication/serving rules; partial search can never read as complete-empty nor imply unsearched combinations | **Replaced by a versioned receipt**: `ka_gochara_path_search_receipt` (PK chart/gen/class/path/rule_version; `searched_intervals` multirange; relation and target inventories; `input_identity`; `completion_state ∈ completed / completed_unqualified / missing_inputs`). Publication: seal requires the receipt set to equal the applicable-path inventory. Serving: per-path receipt coverage decides "searched / partially searched: <paths/intervals missing> / not searched"; the three states are never collapsed. Worked example (the reviewer's own case): P1-Jan/P5-Feb → "partially searched — P1 not searched February; P5 not searched January"; the v0.2 flat reading is shown unrepresentable. **Schema impact corrected: one additive receipt-table migration** (chart-context, no live CHECK, no protected window) | draft v0.3 §AM-5 |
| 2 (P1) | Correct AM-1/AM-3 bootstrap categories; chart lock BEFORE legacy coverage writes | Two transaction categories pinned: **registry txn** (`ka_gochara_lock_global` EXCLUSIVE — predicates/factors/paths/memberships/seals; sky conventions are NOT 1154 registry rows) vs **chart-serving txn** (`ka_gochara_lock_chart` FIRST — sky convention, bridge, AV declaration, substrate/contacts, records/windows, receipts, AND every legacy `kala_gochara_coverage` mutation; the legacy table has no family trigger, so the ordering is the writer's stated obligation). Worked bootstrap sequence (txn R / txn C) with both failure directions cited: 1153:560-578, 604-607, 450-469; 1154:407-410 | draft v0.3 §AM-1/§AM-3 |
| 3 (P2) | Finish convention and identity bytes | **Convention vector byte-pinned** — one canonical string, expected digest `sha256:eac922d4c3b0deb700112f2260cd250a0388ab159f4a1c4bca9451281a48e7a3` (stream-B computed); the compound ephemeris label adopted from A5.3's implementation; the nakṣatra `13d20m` rendering named a deliberate correction of the implementation's `13.20` (new bytes → new digest → new id, landing before any row); domain authority pinned IN the vector (searched partition ≠ domain; O-RX-1 extension stays inside the fixed domain); bridge evolution: a correction mints a new sky id + a new legacy convention row, mappings never repointed. **Lowercase contradiction resolved by naming successor oracle O-RX-1a** (frozen v1.4 preserved). Numeric rendering pinned (≤6 fractional digits, trailing zeros/dot stripped — `198.520` ≡ `198.52`); sign `sign:1–12` absolute; star stored 1-based (`star_zero = star_stored − 1`); correction component named (the tuple carries no time component — a time-only correction never mints a UUID; a method change = new `convention_id`). **5 UUIDv8 vectors pinned** (stream-B recomputed; matches the reviewer's table) plus a **post-mask collision control vector** (two digests differing only in the 6 masked bits → same UUID, verified) | draft v0.3 §AM-1/§AM-2 |
| 4 (P2) | Repair the old-role detector and residence fixture; removing an old CHECK role must FAIL the test | **Detector rewritten**: every v1.0 role gets a FULL acceptance probe (seeded `mars:<role>` partition, real contact, committed writer-path record — v0.2's dangling-contact probes failed at `factsFor` before the INSERT) plus an isolated live `pg_get_constraintdef` assertion. The static detector strips full-line comments and extracts the CHECK's **own** role list by bounded regex (the rollback comment AND the selector-function tail can no longer satisfy it). **Mutation-verified live**: removing `'lord'` from the live CHECK fails the DB probe with `kgrr_object_role_ck` AND fails the static test; suites green on restore (PG 17.10 throwaway; db 8/8; unit migrations 873 passed; eslint/tsc clean). **Residence fixture rebuilt**: `object_kind='house_span'`, lagna frame, `transit_residence` grain, consuming a seeded 1157 `ka_gochara_av_polarity_declaration` row through the writer read-back gate, with O-BP-3 absent-key and wrong-category arms both refused | #2817 @f8b1c8b63 |
| 5 (P2) | P5 form identity / applicability / typed operand lineage / declaration read-back | P5a/P5b are separate `(path_id, rule_version)` identities, never merged or double counted; applicability declared per path (class + affected person); lineage pinned — the consumed declaration key (1157's PK `convention`, resolved HERE as naming the L1 AV-build convention), typed bindu operand evidence with L1 provenance, competing BAV/SAV operands both recorded, the residence contact's sky convention; **read-back rejection executable**: absent key / operand category outside `applies_to_fact_categories` / bindu figures disagreeing with the L1 AV extract are all loud (O-BP-3); missingness recorded per form via the AM-5 receipt's `missing_inputs` | draft v0.3 §AM-7 |
| 6 (P2) | AM-6 score qualification vs hard-predicate admission; null policy; evidence binding | `null_state='unqualified'` pinned on the membership; admission boundary pinned against 1155:822-832 (admission derives from necessary predicates ONLY — a soft factor's missing evidence can never set `admission_state`, its `0` never revokes an admitted interval); evidence binding pinned (typed raw rūpas + full L1 provenance: fact_id, subject, build, ayanāṃśa, tier; conversions documented, never inferred from a field name) | draft v0.3 §AM-6 |
| 7 (P2) | Post-seal query-receipt storage + coverage identity; defer parent-context/temporal-containment to before P6 | Receipt contract: the `moon_on_demand` coverage row (key `moon:interval:<start>/<end>`) is the durable coverage identity; the sealed manifest digest covers build partitions only (`moon_on_demand` excluded whether written before or after sealing); the receipt binds manifest id+digest, coverage key + `coverage_facts` snapshot, query interval, input identity, and result digest; it lives in the application answer log with ZERO ka_gochara writes; replay = result-digest equality. Parent-context/temporal-containment **deferred to before P6** and tracked with AM-8's future template migration | draft v0.3 §AM-4/§AM-8 |

Stale-statement corrections folded alongside (v1.1:269): the frame validator's
**five** kinds (v0.2 said four); the oracle map's 1205 reference corrected to
the future template migration at its next version; v0.2's fixture-debt note
superseded by the shipped rank-4 repair.

## What the round-3 reviewer must judge

- Whether rank 1's receipt representation is **representably complete**
  (path/version × intervals × relations/targets × inputs × state) and whether
  the publication/serving rules make the v0.2 failure modes unrepresentable —
  including whether hosting it in one new additive table is the right storage
  call against the existing `kala_gochara_coverage` shape (1081:225-253).
- Whether rank 2's transaction categorisation matches the applied lock
  protocol everywhere it matters (in particular the chart-lock-before-legacy-
  coverage obligation, which no trigger enforces).
- Whether the AM-1 vector/digest pins and the O-RX-1a successor decision
  close the canonical-bytes contradiction without touching the frozen oracle
  file; whether the numeric/sign/star pins and the named correction component
  leave any identity ambiguity.
- Whether the rank-4 repair's mutation evidence (both detectors red on the
  role removal, green on restore) is sufficient acceptance for #2817, and
  whether the declaration read-back arms constitute a faithful fixture-layer
  O-BP-3 given 1157's deliberate deferral of the SQL gate.
- Whether ranks 5-7 pin what they claim, with the line-level contradictions
  the previous rounds found now absent.

Verdict shape requested: PASS / PASS-WITH-AMENDMENTS / REJECT per exhibit,
with numbered findings.
