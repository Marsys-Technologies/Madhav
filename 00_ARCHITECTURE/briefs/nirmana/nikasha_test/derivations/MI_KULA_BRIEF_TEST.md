---
artifact: MI_KULA_BRIEF_TEST
tier: 4
kind: instance — TEST ARTEFACT, NOT A BRIEF
status: PILOT_DRAFT (derivability test only)
produced_on: 2026-09-26
template: 00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md
layer_instance: nikasha_test/derivations/L5_INSTANCE_SKELETON.md (TEST ARTEFACT — not ACCEPTED, therefore pilot by the §0 pilot clause)
pilot: yes
measured_on: 2026-09-26
measured_against: "census nikasha_test/census/L5_prod_20260926.json (production run); sandbox census agrees on all verdict fields"
verdict: NONE
---

# mi_kula — asset elevation brief (TEST ARTEFACT)

## §0 · Identity and inheritance

```
asset_id: mi_kula · layer: L5 Mīmāṃsā · pilot: yes
kind: data · scoring_mode: contribution · role: INVENTED (see §8)
measured_on: 2026-09-26
```

### 0.1 · Inherited — thirteen rows (from skeleton §4.4; fill status per that table)

| # | what | value | from |
|---|---|---|---|
| 1 | P/V | INVENTED — no per-layer P/V necessity exists above the instance | layer §0.1 (itself INVENTED) |
| 2 | obligations | predictive performance · operational honesty | product §11 L5 row — provided |
| 3 | correctness + switch | no outcome leakage into prospective generation (product §8.1 L5 row); switch ON/OFF emission semantics INVENTED | layer §2.1 |
| 4 | presentation fields | INVENTED — no per-layer §3.4 row assignment exists | layer §2.2 |
| 5 | contracts | produces: none identifiable (serves query_signal_families, query_calibration); consumes: 2 resolvable edges (unnamed in census) — declared uses INVENTED | layer §2.3 |
| 6 | coverage obligations + state | INVENTED — no per-layer §5 split exists | layer §2.4 |
| 7 | position + baseline | census: 43 runs (asset_set/global/layer), last 2026-09-06/07, latest complete; three-way baseline (deployed / current-code / target) PARTIAL — deployed only | census |
| 8 | disposition + must-add | INVENTED — requires Part 1 measurements the skeleton could not produce | layer §3.2/3.3 |
| 9 | individual term | absent instrument (no ablation harness) — recorded, not invented | layer §1.2 |
| 10 | synergistic term | absent instrument | layer §1.3 |
| 11 | cross-layer term | served: 2 modules (index.ts, query_signal_families.ts; 1 density_contract); not verified at consumer | census |
| 12 | preserved kernel | INVENTED — nothing defines it above the brief | layer §3.2 |
| 13 | concepts + carriage check | INVENTED — **C-9/R09 confirmed for L5**: census `Carr.detector` = NO_DETECTOR for 14/14; §2.7 assigns a/b/c at layer scope only. Chosen here by the author: **D3** if the signal-family definitions are computable a second way; D1/D2 inapplicable absent a cited classical source | layer §2.7/§4.4 |

### 0.2 · What this asset is for

INVENTED — one-paragraph purpose ("families of signals whose joint behaviour is learned from"), because no permitted document states what mi_kula computes. Clause that should have provided it: tier-4 §0.2 presumes "the layer's terms" exist — the layer instance §3.x that would name the asset's role was never derivable (skeleton rows 8–10 NO).

## §1 · Measured current state

- Storage: `mimamsa_signal_families`, 15 rows (live=15, floor=0, Δ+15), 20 cols, 16 fully populated; NEVER populated: `data_source_pin`, `apply_point`, `interaction_value`, `interaction_status` (census Complete.depth PARTIAL; Count.floor PASS).
- Producer: `mi_kula.py`, `@register` present and registry agrees (Build.registered/contract PASS); Idem PASS (delete-then-insert).
- Consumers: 2 declared edges, all resolvable (Build.dag PASS); actual code consumers NOT MEASURED (no grep in permitted inputs).
- Served: 2 capability modules, 1 with density_contract.
- Baseline: deployed = 15 rows, state lit; current code vs deployed NOT MEASURED; target = this brief.
- Build cost: **not instrumented** — Earn.build_record FAIL (`rows_per_second=NULL`), Cost.baseline FAIL (rows_written=15, rps=-).
- Evidence state: source-present…served (2 modules); value-evaluated: no.

### 1.1 · Concept completeness
Complete.width = **NOT_GENERIC** — "no declared universe for this asset — declaring one is the first width gap". Universe declaration INVENTED if attempted; recorded NOT MEASURED instead.

### 1.2 · Retrieval reachability
Reach.fields = **NOT_GENERIC** — "field-level exposure census is per-capability; not generic". Requirement [TRANSFERS] to the retrieval plane; not blocking.

## §2 · Shape
identity ✓ inputs/DAG ✓ correctness ✓ data sufficiency ✓ consumers ✓ value/target ✓ synergy ✓ knowledge-time ✓ change packet ✓ evidence ✓ (self-check only; no records).

## §3 · Obligations specialised

| obligation | satisfied means for mi_kula | detector |
|---|---|---|
| predictive performance | family definitions separate signal from noise against declared denominators | INVENTED — no detector named anywhere (NO_DETECTOR) |
| operational honesty | build record carries real figures | rows_written/rps — currently FAIL |

## §4 · Asset conformance — the nine gates (from census)

| gate | verdict | evidence (census) |
|---|---|---|
| Ldgr | NOT RUN by census for this asset (no Ldgr.source_presence row) | NO_DETECTOR |
| Idem | PASS | DELETE FROM present |
| Earn | FAIL | rows_per_second=NULL, last_built=2026-09-06 |
| Null | NOT MEASURED | — |
| Vocab | PASS (identity) | declared key (family_id): 0 duplicates — note: key is NOT chart-scoped; tier-4 §6's "L1+ delete-then-insert on chart × natural key" does not fit |
| Carr | NO_DETECTOR | census, and row 13 was invented (§0.1.13) |
| Narr | N/A — no prose column evidenced | reason: none of the 20 columns identified as prose in census |
| Dens | PASS | 2 modules, 1 density_contract |
| Build | PARTIAL overall | registered/contract/target/dag/count_integrity/completion PASS; exercised PASS (43 runs); history PARTIAL (2 aborts); dep_liveness PASS |

## §5 · Delta ledger rows (would be registered; not registered — test artefact)

- G1 Earn.build_record FAIL (detector: asset_throughput non-null rps)
- G2 4 columns never populated (detector: Complete.depth)
- G3 Carr NO_DETECTOR (detector: the D-check chosen under an R09 resolution)
- G4 width universe undeclared (detector: §1.1 census)

## §9 · Opportunity register
None recorded — the admission rule ("no measurement-after, no entry") cannot be satisfied from census data alone without inventing measurements.

## §6 · Change packet
Not authorised; not attempted.

## §7 · Certification
None — pilot (tier-4 §0 pilot clause: a pilot "may register gaps … may not write certification records").

## §8 · Review — unsigned; invention table

| row | invention | clause that should have provided it (verbatim) |
|---|---|---|
| §0 role | "manifestation \| temporal \| neither" not assigned for L5 assets | tier-4 §0: "role: manifestation \| temporal \| neither (supplies what both rest on)   # from layer §4.4" — layer §4.4's thirteen rows contain no role assignment |
| 0.1.1 | P/V rows | tier-3 §4.4: "the P-needs and V-journeys the asset serves (from 0.1, narrowed)" — 0.1 itself was invented |
| 0.1.3 | switch ON/OFF semantics | tier-3 §2.1: "what this layer may do when ON, what it emits when OFF" |
| 0.1.4 | presentation fields | tier-2 §13.3 item 6: "which §3.4 presentation rows this layer carries and which fields it hands onward for them" |
| 0.1.5 | declared uses | tier-3 §2.3: "Every consumed input declares its use" |
| 0.1.6 | coverage split | tier-3 §2.4: "Which of the product's coverage obligations this layer owns" |
| 0.1.8 | disposition/must-add | tier-3 §4.4: "its disposition and its 'must add' list (3.2, 3.3)" — 3.2/3.3 unproducible without Part 1 instruments |
| 0.1.12 | preserved kernel | tier-3 §4.4: "the preserved kernel — what of the asset must survive any rebuild unchanged (from 3.2)" |
| 0.1.13 | carriage check choice (D3) | tier-3 §4.4: "the relevant Jyotish concepts the asset touches, named, with the domain detector each invites (2.7, 5.2's menu)" — C-9/R09 confirmed |
| §3 detector | performance detector | tier-4 §3: "detector (named here, run in §4)" |

**Derivability: 2 of 13 rows filled without invention (rows 2, 7-partial counted against). Row 13 = C-9, fifth confirmation.**
