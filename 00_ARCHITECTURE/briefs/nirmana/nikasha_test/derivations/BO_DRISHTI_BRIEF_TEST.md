---
artifact: BO_DRISHTI_BRIEF_TEST
tier: 4
kind: instance
status: TEST ARTEFACT — NOT A BRIEF
pilot: yes
asset_id: bo_drishti
layer: L2 Bodha
measured_on: 2026-09-26
measured_against: "nikasha_test/census/L2_prod_20260926.json (production census 2026-09-26T17:18:41+05:30) only"
verdict: NONE
---

# bo_drishti — asset elevation brief (TEST ARTEFACT, pilot)

Derived from `L2_INSTANCE_SKELETON.md` (a test artefact, not an accepted instance) + tiers 1–4 +
the L2 production census, per the tier-4 template §0–§9. Every cell the sources could not fill is
marked INVENTED and indexed in `L2_INVENTIONS.md`.

## §0 · Identity and inheritance

```
asset_id: bo_drishti · layer: L2 Bodha · pilot: yes
kind: data (writer-backed, single table) · scoring_mode: contribution · role: neither
  — INVENTED: "role" chosen as "neither"; no tier assigns manifestation/temporal/neither per L2 asset (I-21)
measured_on: 2026-09-26 · measured_against: L2 production census
layer_instance: derivations/L2_INSTANCE_SKELETON.md (TEST ARTEFACT — pilot clause applies: may register gaps, may not certify)
```

### 0.1 · Inherited — thirteen rows

| # | what | value | state |
|---|---|---|---|
| 1 | P/V served | — | **INVENTED** if filled: skeleton 0.1 has no rows (I-01/I-15). Clause: "the P-needs and V-journeys the asset serves (from 0.1, narrowed)" (tier-3 §4.4) |
| 2 | obligations scored on | concept and relationship completeness · interpretive fidelity | PROVIDED (tier-1 §11 L2 row) |
| 3 | correctness rules + switch | rules: "must not make biography-dependent support appear event-free" (§8.1); no graph-centrality-as-causation, no catalog-match-as-formation, no temporal-hook-as-clock-evidence (§3.1). Switch behaviour: — | rules PROVIDED; switch **INVENTED** (I-08). Clause: "its correctness rules and switch behaviour (2.1)" (tier-3 §4.4) |
| 4 | presentation fields | competing readings with authorities; typed chains (via DP06) | PARTIAL — rest INVENTED (I-09) |
| 5 | contracts produced/consumed, declared use | consumes DP03/DP04/DP05 (layer-level); per-asset assignment and declared use unknown | **INVENTED** per asset (I-10). Clause: "its contracts produced and consumed, with declared use (2.3)" |
| 6 | coverage obligations + states | — | **INVENTED** (I-11); census: Complete.width NOT_GENERIC, no declared universe |
| 7 | position in order + three-way baseline | DAG: 3 edges, all resolvable (census); deployed = 180 rows; current-code-vs-deployed delta not in census | PARTIAL; risk figure **CANNOT FILL** (I-05). Clause: "its position in the order and its three-way baseline (4.1)" |
| 8 | disposition + must-add | — | **INVENTED** — needs Part 1 measurements that do not exist (I-16). Clause: "its disposition and its 'must add' list (3.2, 3.3)" |
| 9 | individual term, measured | unmeasurable — ablation never run | ABSENT INSTRUMENT (template-sanctioned null, not an invention) |
| 10 | synergistic term, which seam | seam: served jointly via query_domain_reading.ts with other bo_* signals (census module list) | PARTIAL; measured term ABSENT INSTRUMENT (I-06) |
| 11 | cross-layer term, contract + evidence state | DP06 → L3/inquiry; evidence state: served (2 modules, 1 density_contract) | PARTIAL — "verified at the consumer" absent from census (I-07) |
| 12 | preserved kernel | — | **INVENTED** (I-17). Proposed: the (chart_id, ayanamsha_id, question_type) grain; delete-then-insert scope; the 15-column lens shape |
| 13 | Jyotish concepts + carriage check | concepts: question-lens doctrine (dṛṣṭi-based question shaping) — named here by the author. Carriage check: **D1 chosen by the author** (the lenses restate cited classical question doctrine) | **INVENTED — C-9/R09, fifth confirmation** (I-13). Clause: "the relevant Jyotish concepts the asset touches, named, with the domain detector each invites (2.7, 5.2's menu)" (tier-3 §4.4) |

**Derivability: 1 of 13 fully provided; 4 partial; 7 invented; 1 absent instrument.**

### 0.2 · What this asset is for

INVENTED if written from asset semantics: the census shows a 180-row table of question lenses keyed by
(chart_id, ayanamsha_id, question_type), read by two capability modules. One line derivable: without
it, question-shaped queries have no per-chart lens structure to read (consistent with the L2 §3.1 row).
Anything richer is supplied, not derived (I-22).

## §1 · Measured current state

```
inherits:    layer §1.1, §4.1
measured_by: L2 production census 2026-09-26 (population: the registry row, live table and writer file for bo_drishti)
traces_to:   layer §0.3
```

- **Storage:** `bodha_question_lenses` — 180 rows, 15 columns, all 15 fully populated; never-populated:
  none. `count_sql`/`integrity_check_sql` present (Build.count_integrity PASS). CENSUS CAVEAT R42:
  Build.completion reads N/A "no count_sql" although count_sql exists — completion unverified.
- **Producer:** `bo_drishti.py`, `@register` agrees with registry (Build.registered PASS); WriterBase
  contract conformant. Idem: DELETE FROM present — delete-then-insert, matches the L1+ convention (PASS).
- **Consumers, declared vs actual:** declared 3 DAG edges in; actual readers per census: served by
  `query_domain_reading.ts`, `query_question_lenses.ts` (1 of 2 declares a density_contract). The
  declared-vs-actual gap is NOT MEASURED by the census (no grep population) — CANNOT FILL (I-23).
- **Served surface:** 2 modules; Dens.served PASS.
- **Three-way baseline:** deployed 180 rows · current code = unmeasured · target = this brief.
  Risk uncomputable (I-05).
- **Evidence-state position:** source-present ✓ (citation_ref 180/180) · served ✓ (census) ·
  qualified / consumed / transformed / value-evaluated — not in census. CANNOT FILL (I-07).
- **Build-cost baseline:** FAIL — `rows_per_second=NULL, last_built=2026-08-12`, rows_written=60.
  "Not instrumented" per template §1 is the legal honest value; the census scores it FAIL.
  CENSUS CAVEAT R44 (non-latest throughput row possible).

### 1.1 · Concept completeness

Universe: **not declared** — census Complete.width NOT_GENERIC ("declaring one is the first width
gap"). Width/depth fractions: unmeasurable. CANNOT FILL without inventing the universe (I-24; register
R22 — universes have nowhere to be declared).

### 1.2 · Retrieval reachability

Reach.fields NOT_GENERIC (per-capability census not run). Field-level exposure: CANNOT FILL (R23).
Requirement [TRANSFERS] to the retrieval plane per tier-4 §1.2.

## §2 · Brief shape

identity ✓ inputs/DAG ✓ correctness ✓ data sufficiency ✓ consumers ✓ value/target ✓ synergy ✓
knowledge-time ✓ change packet ✓ evidence ✓ — presence only; certifies nothing.

## §3 · Obligations specialised

| obligation | satisfied means for bo_drishti | detector |
|---|---|---|
| Concept/relationship completeness | every declared question_type has its lens rows at the declared grain | the width census — **cannot run, no declared universe** (I-24) |
| Interpretive fidelity | a served lens row traces to the structural signals it restates | citation_ref field-presence (PASS) is presence, not fidelity — a fidelity detector does not exist. NO_DETECTOR |

Specialising "interpretive fidelity" to a testable claim required inventing the claim's content —
the parents define the obligation at layer altitude only (I-25).

## §4 · Asset conformance — the nine gates

| gate | verdict | evidence (all census) |
|---|---|---|
| Ldgr | PASS (as source-presence) | citation_ref 180/180 |
| Idem | PASS | DELETE FROM present |
| Earn | FAIL | rows_per_second=NULL against last_built 2026-08-12 |
| Null | **NO_DETECTOR** | no census check reads null-handling for this asset |
| Vocab | PASS (rule 1 scope only) | declared key 0 duplicates; rules 4–6 NOT MEASURED (local_map_candidates −1) |
| Carr | NO_DETECTOR | D1 chosen by author (row 13); no detector exists |
| Narr | N/A — emits no prose | reason: table of structured lens rows |
| Dens | PASS | 2 modules, 1 density_contract |
| Build | PARTIAL | static checks PASS ×6; history PARTIAL (17 errors, 9 aborts; latest complete; blocking text: upstream bo_karanajala/bo_laksana/bo_sangati incomplete); exercised 79 runs |

## §5 · Delta ledger rows (would register; pilot — registered nowhere)

`G1` Earn build record uninstrumented · `G2` no Carr D1 detector · `G3` no declared width universe ·
`G4` Null gate has no detector · `G5` Vocab rules 4–6 unmeasured · `G6` build-history error/abort tail
(upstream-blocked) · `G7` field-level reachability unmeasured ([TRANSFERS]-adjacent, opportunity side).

## §9 · Opportunity register

| id | dimension | entry | proof afterward |
|---|---|---|---|
| O1 | build cost | instrument the writer's rows/duration into asset_throughput | a non-NULL rows_per_second on the next run |
| O2 | concept completeness | declare the question_type universe (from the ontology's domain/question classes) and re-run the width census | census emits a fraction instead of NOT_GENERIC |

(No synergy entry: the shared-root guardrail applies — bo_drishti's lenses derive from the same
bodha_msr_signals placements as seven sibling assets; a pairing would restate one root.)

## §6 · Change packet — not authorised (pilot; no acceptance of the layer skeleton)

Preserved kernel: per row 12 (INVENTED — I-17). Idempotency: delete-then-insert on
(chart_id × ayanamsha_id × question_type) — matches convention. Rollback, consumer impact, open
decisions: not derivable from the provided sources; not invented here.

## §7 · Certification

None — pilot (tier-4 §0 pilot clause: may register gaps, may not certify).

## §8 · Review — unsigned. Invention record (against the thirteen §0.1 rows)

| row | state | invention |
|---|---|---|
| 1 | INVENTED | P/V assignment (I-01/I-15) |
| 2 | provided | — |
| 3 | partial | switch behaviour (I-08) |
| 4 | partial | presentation-field boundary (I-09) |
| 5 | INVENTED | per-asset contracts + declared use (I-10) |
| 6 | INVENTED | coverage ownership (I-11) |
| 7 | partial | three-way baseline risk figure (I-05) |
| 8 | INVENTED | disposition + must-add (I-16) |
| 9 | absent instrument | — |
| 10 | partial | measured synergy (I-06) |
| 11 | partial | consumer-verified evidence state (I-07) |
| 12 | INVENTED | preserved kernel (I-17) |
| 13 | INVENTED | concepts + carriage check chosen by author — C-9/R09 fifth confirmation (I-13) |

**Derivability: 1/13 clean.** The brief exists only because its author supplied rows 1, 3, 5, 6, 8,
12, 13 — each a defect in the layer instance or the templates, recorded in `L2_INVENTIONS.md`.
