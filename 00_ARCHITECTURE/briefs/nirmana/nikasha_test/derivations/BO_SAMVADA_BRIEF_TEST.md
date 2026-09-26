---
artifact: BO_SAMVADA_BRIEF_TEST
tier: 4
kind: instance
status: TEST ARTEFACT — NOT A BRIEF
pilot: yes
asset_id: bo_samvada
layer: L2 Bodha
measured_on: 2026-09-26
measured_against: "nikasha_test/census/L2_prod_20260926.json (production census 2026-09-26T17:18:41+05:30) only"
verdict: NONE
---

# bo_samvada — asset elevation brief (TEST ARTEFACT, pilot; EDGE KIND: view-target / delegates)

Chosen as the L2 edge kind: its `target_table` is a **view** (`vw_chart_digest`), its writer shows no
idempotency pattern of its own ("likely delegates"), and its build record is internally contradictory
(`rows_written=1, live=0` scored PASS by Build.completion while Complete.depth counts 15 rows — the
register's R46 explains: a stub `count_sql` of `SELECT 0`). L2 has no service, never-run or
multi-table asset (census: `never_exercised_with_writer: []`; every target is a single table or this
one view), so this is the nearest edge kind the layer offers.

## §0 · Identity and inheritance

```
asset_id: bo_samvada · layer: L2 Bodha · pilot: yes
kind: INVENTED — "view-backed serving digest". Tier-4 §0's closed kind list —
  "data | service (no table by design) | multi-table | rider (producer_covered) | static (migration-seeded)"
  — has no value for an asset whose target is a view over other assets' tables: it is not "data"
  (owns no rows), not "service" (a writer runs and a build record exists), not "multi-table",
  not "rider", not "static". (I-26)
scoring_mode: contribution · role: neither (INVENTED, as I-21)
measured_on: 2026-09-26 · measured_against: L2 production census
layer_instance: derivations/L2_INSTANCE_SKELETON.md (TEST ARTEFACT — pilot clause applies)
```

### 0.1 · Inherited — thirteen rows

| # | what | value | state |
|---|---|---|---|
| 1 | P/V served | — | **INVENTED** (I-01/I-15) |
| 2 | obligations scored on | concept and relationship completeness · interpretive fidelity | PROVIDED |
| 3 | correctness rules + switch | rules PROVIDED (as bo_drishti row 3); switch **INVENTED** (I-08) |
| 4 | presentation fields | — a digest view plausibly carries every §3.4 row its upstreams carry; which fields *it* must retain is unstated | **INVENTED** (I-09) |
| 5 | contracts produced/consumed, declared use | consumes from ≥5 upstream bo_* assets (history blocking text); DP mapping unknown | **INVENTED** (I-10) |
| 6 | coverage obligations + states | — | **INVENTED** (I-11); Complete.width NOT_GENERIC |
| 7 | position + three-way baseline | 5 DAG edges resolvable; deployed = **15 rows (view) but census `live_rows=0`** | PARTIAL and **contradictory at source** — R46; risk uncomputable (I-05) |
| 8 | disposition + must-add | — | **INVENTED** (I-16) |
| 9 | individual term | unmeasurable — no ablation harness | ABSENT INSTRUMENT |
| 10 | synergistic term | it *is* a join of sibling assets — the seam is the whole asset; unmeasured | PARTIAL / ABSENT INSTRUMENT (I-06) |
| 11 | cross-layer term | served via query_ucd.ts (1 module, 0 density_contracts → Dens FAIL) | PARTIAL (I-07) |
| 12 | preserved kernel | — | **INVENTED** (I-17). Proposed: the view definition (its SELECT), not any rows |
| 13 | concepts + carriage check | concepts: the whole-chart digest it assembles. Carriage check: **D3 chosen by the author** — a digest is recomputed from underlying tables; a second derivation compares | **INVENTED — C-9/R09, sixth confirmation** (I-13) |

**Derivability: 1 of 13 fully provided; 4 partial; 7 invented; 1 absent instrument.**

### 0.2 · What this asset is for

INVENTED beyond one line: it is the chart-digest view the UCD query module reads — a serving
projection over the layer's structural tables. Everything richer is supplied, not derived (I-22).

## §1 · Measured current state

```
inherits:    layer §1.1, §4.1
measured_by: L2 production census 2026-09-26 (population: registry row, view definition, writer file for bo_samvada)
traces_to:   layer §0.3
```

- **Storage:** `vw_chart_digest` — a **view**. Complete.depth counts **15 rows, 13 cols, all
  populated**; `live_rows` reads **0**; Count.floor PASS reads "live=0, floor=0, delta=+0".
  CENSUS CAVEAT R46: the floor check passes vacuously against a stub `SELECT 0` count_sql — a view's
  emptiness and a view's stub counter are indistinguishable in this surface. INVENTED if the brief
  asserted either "empty by design" or "populated": the census itself carries both (I-27).
- **Producer:** `bo_samvada.py` (@register agrees); Idem.pattern PARTIAL — "no idempotency pattern in
  the writer's own SQL — it likely delegates; verify there". CENSUS/REGISTER R20: delegation not
  followed. Whether the writer rebuilds the view or a table the view reads is **not derivable** from
  the census (I-28).
- **Consumers:** 1 module (`query_ucd.ts`), 0 density_contracts → Dens.served FAIL. Declared vs actual
  readers beyond that: not measured (I-23).
- **Three-way baseline:** deployed = 15 rows (Complete.depth) or 0 (live_rows) — contradictory;
  current code unmeasured; risk uncomputable (I-05).
- **Evidence-state position:** served ✓ (1 module); the rest not in census (I-07).
- **Build cost:** FAIL — stale, rows_written=1, rps NULL, last_built 2026-09-11.
- **Missing census checks:** this asset's measurement block carries **no `Vocab.identity` and no
  `Ldgr.source_presence` row at all** (23-asset aggregates: Vocab 22, Ldgr 16) — a view over other
  assets' rows is silently exempted from identity and citation checks rather than scored N/A with a
  reason. INVENTED if the brief assigned a verdict; the template requires "a bare N/A is a gap" to be
  explicit (tier-4 §4). I-29.

### 1.1 · Concept completeness

No declared universe (NOT_GENERIC). CANNOT FILL (I-24).

### 1.2 · Retrieval reachability

Reach.fields NOT_GENERIC. Requirement [TRANSFERS]. CANNOT FILL (R23).

## §2 · Brief shape

identity ✓ inputs/DAG ✓ correctness ✓ data sufficiency ✓ consumers ✓ value/target ✓ synergy ✓
knowledge-time ✓ change packet ✓ evidence ✓ — presence only.

## §3 · Obligations specialised

| obligation | satisfied means for bo_samvada | detector |
|---|---|---|
| Concept/relationship completeness | the digest exposes the same structure its source tables hold, at the declared digest grain | the width census — cannot run (I-24); and "same structure" needs a view-vs-source parity query no check defines (I-30) |
| Interpretive fidelity | the digest never adds a claim its sources do not carry | NO_DETECTOR — no such check exists |

## §4 · Asset conformance — the nine gates

| gate | verdict | evidence |
|---|---|---|
| Ldgr | **MISSING — no check emitted** | census carries no Ldgr.source_presence row for this asset (I-29) |
| Idem | PARTIAL | delegates; unverified (R20) |
| Earn | FAIL | rows_per_second=NULL; and rows_written=1 vs 15 live rows is the completion-honesty question the gate exists for |
| Null | **NO_DETECTOR** | no census check |
| Vocab | **MISSING — no check emitted** | no Vocab.identity row (I-29) |
| Carr | NO_DETECTOR | D3 chosen by author (row 13); no detector exists |
| Narr | N/A — emits no prose | structured digest |
| Dens | FAIL | 1 module, 0 density_contracts |
| Build | PARTIAL | statics PASS; completion "PASS" is against the stub count (R46); history PARTIAL (23 errors, 12 aborts; latest complete; upstream-blocked text); exercised 98 runs incl. global scope |

## §5 · Delta ledger rows (would register; pilot)

`G1` count_sql is a stub (`SELECT 0`) for a view — floor and completion checks vacuous (R46) ·
`G2` Idem delegation unverified (R20) · `G3` Earn uninstrumented · `G4` Ldgr/Vocab checks silently
absent for a view asset (I-29) · `G5` no declared universe (I-24) · `G6` Dens: module without
density_contract · `G7` no Carr D3 detector (I-13).

## §9 · Opportunity register

| id | dimension | entry | proof afterward |
|---|---|---|---|
| O1 | algorithm | a view needs no writer-side idempotency; declare it a view asset and drop the writer, or materialize it and take the convention seriously — one sentence of kind truth dissolves G1, G2, G4 | the census scores the asset under its real kind with no PARTIALs from category confusion |
| O2 | build cost | instrument the digest build | non-NULL rps on next run |

## §6 · Change packet — not authorised (pilot)

Preserved kernel: per row 12 (INVENTED — I-17): the view definition. Nothing else is derivable.

## §7 · Certification

None — pilot.

## §8 · Review — unsigned. Invention record (against the thirteen §0.1 rows)

| row | state | invention |
|---|---|---|
| 1 | INVENTED | P/V assignment (I-01/I-15) |
| 2 | provided | — |
| 3 | partial | switch behaviour (I-08) |
| 4 | INVENTED | which §3.4 fields a digest must retain (I-09) |
| 5 | INVENTED | contracts + declared use (I-10) |
| 6 | INVENTED | coverage ownership (I-11) |
| 7 | partial, contradictory at source | baseline (I-05; R46) |
| 8 | INVENTED | disposition + must-add (I-16) |
| 9 | absent instrument | — |
| 10 | partial | measured synergy (I-06) |
| 11 | partial | consumer-verified evidence state (I-07) |
| 12 | INVENTED | preserved kernel (I-17) |
| 13 | INVENTED | concepts + carriage check chosen by author — C-9/R09 sixth confirmation (I-13) |

Plus three asset-level inventions not in the thirteen rows: the `kind` value itself (I-26), the
empty-vs-populated assertion (I-27), and the writer's actual target (I-28).

**Derivability: 1/13 clean.** The edge kind the template's §0 kind list cannot name is also the asset
whose checks the census silently omits — category confusion at tier 4 becomes missing measurement at
the inspector.
