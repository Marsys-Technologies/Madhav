# TEST ARTEFACT — NOT AN INSTANCE

L1 Gaṇita — layer-instance skeleton, derived by a fresh reader (Nikaṣa Phase 4, layer L1) from
tier 1 (`MADHAV_PRODUCT_DEFINITION_FINAL.md`), tier 2 (`MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md`),
tier 3 (`LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md`, SEALED) and the inspector's census
`nikasha_test/census/L1_prod_20260926.json` (production; generated 2026-09-26T17:17:20+05:30;
19 assets, all writer-backed; `never_exercised_with_writer: []`; `phantom_registered: []`;
`local_map_candidates: -1`). Sandbox census `L1_sandbox_20260926.json` exists and agrees on the
asset list; production is used throughout.

Notation: `INVENTED — <what>, clause that should have provided it: "<verbatim quote>" (<source>)`.
Inventions are numbered INV-L1-nn and collected in `L1_INVENTIONS.md`.

---

## Part 0 · VALUE — the origin

### 0.1 · What cannot be answered without this layer

```
inherits:    Product §2 (P01-P24), Data plane §2 (V01-V13)
measured_by: none — definitional; but every P/V cited must exist in the parent under current numbering
traces_to:   —  (this IS the origin)
```

Neither tier 1 nor tier 2 maps P-needs or V-journeys to layers by **necessity**. Tier 1 §11 gives
L1's product responsibility ("Reproducible subject calculations under declared inputs and
conventions") and tier 2 §3.1 the owned question, but no clause enumerates which P/V rows *cannot
be answered without* L1.

**INVENTED — the per-layer necessity set over P01–P24 / V01–V13, clause that should have provided
it: "List the P-needs and V-journeys for which this layer is **necessary** — not "involved in", not
"contributes to", but *cannot be answered without*." (tier 3 §0.1)** — INV-L1-01.

Filled here as INVENTED, mechanical reading of Product §11 ("Downstream consumers refer to L1
facts; they do not recompute them") — any P/V whose reading consumes a chart fact is necessary:

| P / V | the distinction that disappears without this layer |
|---|---|
| INVENTED: all P/V rows whose evidence is a computed chart fact (positions, daśās, vargas, strengths, conditions, configurations-membership) | the reproducible fact itself: identity, value, unit, convention, provenance — downstream layers would have to recompute, and Product §11 forbids that |

### 0.2 · The layer's objective

```
inherits:    Product §1 (the join), §11 (this layer's row), Data plane §3.1 (this layer's row)
measured_by: none — definitional
traces_to:   0.1
```

Provided verbatim by tiers 1–2, no invention:

- **Owned question** (tier 2 §3.1): "What is actually calculated for this subject and context?"
- **Contribution handed onward** (tier 2 §3.1): "Reproducible facts, configuration membership,
  conditions, divisions, clocks and uncertainty, with fact identities and conventions."
- **Must not claim** (tier 2 §3.1): "A newly invented downstream value or interpretation disguised
  as computation."
- **Proof that matters** (tier 1 §11): "Computational correctness (§14): fact identity, values,
  units, precision, provenance. Downstream consumers refer to L1 facts; they do not recompute them."
- Layer one-line identity (tier 2 §6.x closing): "Gaṇita makes the chart reproducible."
- Scored on (tier 1 §11 assignment): **Computational correctness** — the layer's subset of the
  product's ten proof obligations is this one row (ten, not eleven; ruling 11).
- Tier 3 adaptation row: "computational correctness dominates 5.1; 'downstream consumers refer to
  L1 facts, they do not recompute them' is the load-bearing 2.3 rule; L1 holds judged structure too
  — 'layer ownership is not epistemic type'" (the census confirms: `ga_vichara` is an L1 asset).

### 0.3 · Its place in the wheel

```
inherits:    Data plane §3.2 (five edge types), §7 (DP contracts)
measured_by: registry depends_on reconciled across seed, migration pin AND live asset_registry — state all three and any disagreement
traces_to:   0.2
```

- **Receives from** (tier 2 §7.1): DP01 Identity/release (L0 → all adapters and writers);
  DP02 Rule qualification (L0 → calculation, interpretation and investigator). Edge type:
  computational (build) and definition.
- **Hands onward to** (tier 2 §7.1): DP03 Chart facts (L1 → L2–L4/services); DP04 Condition
  decomposition (L1 → L2/L3/L4); contributes to DP05 Configuration (L0+L1 → L2 → L3) and DP07
  Precise clocks/contacts (L0/L1/L3 primitives → temporal integrators). DP14 names "independent
  L1/L2/L3/L4 context" into comparison.
- **What the join needs from it:** the computed depth every downstream layer reads without
  recomputing (Product §11), exposed with `fact_id`, grain/value/unit, chart/build,
  ayanāṃśa/frame/varga, input precision and verification (DP03 field list).
- **Three sources:** the template's `measured_by` demands seed, migration pin AND live registry,
  reconciled. The census provides the **live registry** view only (per-asset `Build.dag` edge
  counts, all PASS: 19/19 resolvable, no cycles reported).

**INVENTED — the seed and migration-pin readings of the DAG and their reconciliation against the
live registry, clause that should have provided it: "measured_by: registry depends_on reconciled
across seed, migration pin AND live asset_registry — state all three and any disagreement" (tier 3
§0.3). The census instrument does not emit the seed/pin readings, so a fresh reader cannot perform
the mandated three-way reconciliation.** — INV-L1-02.

### 0.4 · The alignment test

Provided by tier 3 §0.4 verbatim; no invention.

---

## Part 1 · VALUE DECOMPOSITION

### 1.1 · Inventory, measured

```
inherits:    Data plane §13.3 item 2
measured_by: census L1_prod_20260926.json (live registry + build_runs + count_sql where declared; population: the 19 L1-registered assets, production, 2026-09-26)
traces_to:   0.3
```

19 assets, all `has_writer: true`, all `catalog_status: CURRENT`. Per census:

| asset | target_table | rows (count_sql) | notes from census |
|---|---|---|---|
| ga_ayurdaya | chart_facts | 421,096 (shared) | Earn.build_record FAIL; Complete.depth PARTIAL (`salience_formula_ver` never populated) |
| ga_condition | ga_condition_composite | 135 | Build.history PARTIAL (14 err / 9 abort; blocked on ga_dashas) |
| ga_dashas | chart_dashas | 1,460,985 | Build.history PARTIAL (18 err / 7 abort) |
| ga_medical | ga_medical | 135 | history PARTIAL |
| ga_nakshatra | chart_facts | 421,096 (shared) | **Idem PARTIAL: "ON CONFLICT where the layer convention is delete-then-insert"** |
| ga_panchanga | chart_facts | 421,096 (shared) | — |
| ga_positions | chart_facts | 421,096 (shared) | **Build.history FAIL: most recent run aborted 2026-09-19; "Object of type UUID is not JSON serializable"** |
| ga_prashna | ga_prashna_judgment | **0 — "table empty"** | Dens N/A (0 modules); rows_written=0 vs state=lit |
| ga_sade_sati | chart_facts | 421,096 (shared) | 7 DAG edges |
| ga_sensitive | chart_facts | 421,096 (shared) | — |
| ga_sensitive_degree | chart_facts | 421,096 (shared) | — |
| ga_strength | **null** | not countable via target | Build.target N/A: "no target_table; asset_kind='data', has_writer=True" |
| ga_structural | **null** | not countable via target | same as ga_strength; 7 edges; 23 err / 11 abort |
| ga_tajaka | l1_tajik_varsha_year_lords | 780 | depth PASS (18/18 cols) |
| ga_transit_anchors | ga_transit_anchors | 135 | **Idem PASS** (delete-then-insert present) |
| ga_vargas | chart_divisionals | **0 — "table empty"** | history: "orphaned_by_crash" |
| ga_vastu | ga_vastu_planet_direction_map | 120 | — |
| ga_vichara | chart_vichara | 25,011 | judged structure held in L1 (tier 3 adaptation: "layer ownership is not epistemic type") |
| ga_yoga | ga_yoga_firings | 202 | depth PARTIAL (`partial_formation_pct`, `activation_dasha_periods` never populated) |

**Shared table (C-10 probe):** `chart_facts` is the declared `target_table` of **7 assets**
(ga_ayurdaya, ga_nakshatra, ga_panchanga, ga_positions, ga_sade_sati, ga_sensitive,
ga_sensitive_degree); the census reports the same 421,096-row / 25-column figure under each. The
template's inventory clause is asset-scoped ("target table(s) — a **set**, not one pointer, for
multi-table assets") and has no rule for the inverse case — several producers, one table: who owns
`count_sql`, which writer's `Idem` pattern governs the shared rows, and which asset's Build check 6
(completion honesty) answers for the table.

**INVENTED — the ownership/counting/idempotency rule for a table with several producers, clause
that should have provided it: "For each: target table(s) — a **set**, not one pointer, for
multi-table assets — row counts in production, columns, contract fields live, last build, and
whether current code on any live head differs from what is deployed." (tier 3 §1.1). The clause
covers one asset → many tables, not many assets → one table.** — INV-L1-12.

**Multi-table / undeclared-target probe:** `ga_strength` and `ga_structural` have
`target_table: null` with `asset_kind='data'`, `has_writer=True`; the census reads Build check 3 as
`N/A`. Tier 4's kind vocabulary is `data | service (no table by design) | multi-table | rider |
static` — a data asset with a writer and no declared target fits none of them cleanly.

**INVENTED — the kind assignment for a writer-backed data asset with no declared `target_table`,
clause that should have provided it: "kind: data | service (no table by design) | multi-table |
rider (producer_covered) | static (migration-seeded)" (tier 4 §0). "multi-table" presumes the set
is declared; nothing covers "declares no target at all".** — INV-L1-14.

**Three-way baseline gap:** the template requires "whether current code on any live head differs
from what is deployed" per asset. The census carries build-run history and registry state but no
deployed-vs-current-code comparison.

**INVENTED — the deployed vs current-code half of the three-way baseline, per asset, clause that
should have provided it: "whether current code on any live head differs from what is deployed"
(tier 3 §1.1). The census does not measure it.** — INV-L1-03.

Layer-wide census observations (recorded, not invented): `Earn.build_record` FAIL on all 19
(`rows_per_second=NULL`); `Cost.baseline` FAIL on all 19 (`rps=-`); `Complete.width` NOT_GENERIC on
all 19 ("no declared universe for this asset — declaring one is the first width gap");
`Carr.detector` NO_DETECTOR on all 19 ("no D1/D2/D3 detector exists for this asset; which check
applies is per-asset semantics"); `Reach.fields` NOT_GENERIC on all 19;
`local_map_candidates: -1` (the independent-map measurement failed or was not run).

### 1.2–1.5 (scaffold, not in the required minimum — noted)

Tier 3's reference-layer clause (1.2) does **not** apply to L1 (chart-product layer;
`scoring: contribution` per census and tier 4's L1 row). Ablation figures per asset: **not
measurable from census** — no served-reading ablation harness is named in tiers or census; per
tier 3 §1.5, record the harness as a packet, do not invent a fraction. No invention made here;
recorded as an absent instrument per tier 1 §1.3 ("where it cannot yet be measured, that is
recorded as an absent instrument, never as a number").

---

## Part 2 · CONDITIONS UNDER WHICH THE VALUE IS REAL

### 2.1 · Correctness rules

```
inherits:    Product §8.1 (this layer's row), §13; Data plane §9.2 (the switch and the storage separation)
measured_by: a detector per rule, named here, that can report the rule violated
traces_to:   0.2
```

Provided: L1's §8.1 row — **"L1 must not alter birth facts to fit biography"** (a correctness rule:
violating it makes the output wrong, not merely inappropriate). Product §13: "**No invented
computation, source, detector, confidence, empirical score, or claim of exhaustive coverage.**"

Not provided: the life-event switch semantics **for this layer**. Tier 1 §8 defines one switch,
two states, no third, and tier 3 §2.1 demands "what this layer may do when ON, what it emits when
OFF, and the storage separation that makes OFF a selection rather than a rebuild". Neither tier
states what a *computation* layer emits differently under the switch — L1 computes facts, and the
switch governs biography-dependent use of them.

**INVENTED — L1's switch behaviour (ON/OFF emission and storage separation), clause that should
have provided it: "The life-event switch: what this layer may do when ON, what it emits when OFF,
and the storage separation that makes OFF a selection rather than a rebuild." (tier 3 §2.1). Tier 2
§9.2 is named in the inherits line but its content was not available to the fresh reader in either
summary or census.** — INV-L1-04.

Filled here as INVENTED: L1 computes identically under both switch states; the switch binds
consumers (L2+), not the fact layer. Detector per rule: "birth facts immutable per (chart_id,
input revision)" — no such detector exists in tiers or census → `NO DETECTOR`.

### 2.2 · Presentation obligation

```
inherits:    Product §2 (two modes, one depth); Data plane §3.4 (the field → contract mapping)
measured_by: presentation-parity test (Data plane §12.2) — NOTE: §12.2's Presentation parity row is marked [TRANSFERS]
traces_to:   0.1
```

Tier 2 §3.4 maps acharya-rendering fields to DP contracts; the rows whose contracts L1 produces
are assignable mechanically: conventions in force → DP01/DP03; intermediate quantities →
DP03/DP04; dignity/strength components separately → DP04. Method/school → DP02 and passed clauses
→ DP05 are L0/L2-carried; the clock-geometry rows → DP07/DP08/DP09 are L3-carried.

**INVENTED — the authoritative assignment of §3.4 presentation rows to L1, clause that should have
provided it: "including which §3.4 presentation rows this layer carries and which fields it hands
onward for them" (tier 2 §13.3 item 6). Tier 2 maps fields to contracts, not rows to layers; the
per-layer row assignment above is derived by the reader through the contract mapping, not
stated.** — INV-L1-05.

**[TRANSFERS] probe:** §2.2's own `measured_by` names the §12.2 presentation-parity test, and
tier 3 §5.4 test 4 requires "Presentation parity holds for the layer's served surface" before the
instance is accepted — yet tier 2 marks that §12.2 row **[TRANSFERS]**, and states "A [TRANSFERS]
obligation is not a data-plane layer's to build alone, and a layer plan does not inherit it as its
own work." A layer plan cannot tell, from the documents, whether §5.4 test 4 is its own gate or a
borrowed one.

**INVENTED — the resolution of [TRANSFERS] rows against tier-3 acceptance tests, clause that
should have provided it: "A [TRANSFERS] obligation is not a data-plane layer's to build alone, and
a layer plan does not inherit it as its own work." (tier 2 §1) read against "4. **Presentation
parity** holds for the layer's served surface." (tier 3 §5.4).** — INV-L1-11.

### 2.3 · Contracts produced and consumed

```
inherits:    Data plane §7 (DP01-DP17), §7.1 (common envelope)
measured_by: tier 2 §7.1 field lists (definitional) + census (per-table presence); field-level verification NOT_MEASURED
traces_to:   0.3
```

**Produces** (from tier 2 §7.1, no invention):

| contract | consumer | fields (as stated) | grain |
|---|---|---|---|
| DP03 Chart facts | L2–L4/services | `fact_id`, grain/value/unit, chart/build, ayanāṃśa/frame/varga, input precision and verification | per census keys: `chart_facts.fact_id`; `chart_dashas.dasha_row_id`; `(chart_id, ayanamsha_id, …)` variants |
| DP04 Condition decomposition | L2/L3/L4 | separate condition/bala/benefit/functional role, constituents and reasons; zeros as zeros, unavailable as unavailable | `ga_condition_composite` (chart_id, ayanamsha_id, graha) |
| DP05 (with L0) | L2 → L3 | every clause tested with its result — passed, partial, failed | `ga_yoga_firings` — census: `partial_formation_pct`, `activation_dasha_periods` never populated |
| DP07 (with L0/L3) | temporal integrators | parent/child clocks, actual interval boundaries, geometry, frame, coverage, uncertainty | `chart_dashas`, `l1_tajik_varsha_year_lords`, `ga_transit_anchors` |

**Consumes** (from tier 2 §7.1): DP01 (canonical entities, aliases, units, released definitions —
declared use: calculation identity); DP02 (rule clauses with prerequisites/exceptions — declared
use: applicability). The load-bearing L1 rule (tier 3 adaptation): consumers refer to L1 facts,
they do not recompute them. Field-and-grain verification *at the consumer* ("verified both ends")
is NOT_MEASURED — the census measures producer-side presence and capability modules, not consumer
reads per field. Recorded, not invented.

### 2.4 · Jyotish coverage owned

```
inherits:    Product §3 (substance), Data plane §5 (domain obligations)
measured_by: per obligation: applied / inapplicable-with-reason / unavailable / unqualified / unresolved
traces_to:   0.1
```

Product §3 names the L1-shaped substance: graha positions, varga, nakshatra/KP, ārūḍha/special
lagnas, daśā computation, aṣṭakavarga, Tājaka, tithi-praveśa, pañcāṅga, āyurdāya. The **obligation
list** this layer owns, as obligations with five states, is not enumerated per layer in tier 2 §5
as available to the reader, and the census reports `Complete.width: NOT_GENERIC` for all 19 assets
("no declared universe for this asset").

**INVENTED — the enumerated list of L1's owned coverage obligations with per-obligation state,
clause that should have provided it: "Which of the product's coverage obligations this layer owns,
with prerequisites, variants, exceptions, negative cases and uncertainty. Each ends in one of the
five states." (tier 3 §2.4). Product §3 names substance, not owned obligations; no tier enumerates
the L1 obligation set.** — INV-L1-06.

Per-asset fallback recorded: every L1 asset's width state is **unqualified** (no declared
universe) per census — that half is measured, not invented.

### 2.6 · Vocabulary conformance

```
inherits:    Data plane §4.1 (six rules)
measured_by: census Vocab.identity (declared-key duplicate counts — all 19 PASS, 0 duplicates) · alias coverage NOT_MEASURED · independent-map census: local_map_candidates = -1
traces_to:   0.2
```

L1 **conforms** (tier 3 §2.6; the inversion is L0-only). Which of the sixteen entity classes L1
emits or accepts is not enumerated anywhere per layer. Measured half: declared-key uniqueness
PASS on all 19 (keys as tabulated in 1.1). Not measured: alias-set coverage per class;
interface-parameter census; code-side snapshot parity tests; independent maps per class
(`local_map_candidates: -1` — the instrument returned no value).

**INVENTED — the list of entity classes L1 emits/accepts and the per-class independent-map census,
clause that should have provided it: "Which of the sixteen entity classes this layer emits or
accepts; for each, whether every name resolves through the controlled set … how many independent
maps the layer's code carries (permitted: one)" (tier 3 §2.6). The census's single
`local_map_candidates` figure is `-1`, a non-result.** — INV-L1-07.

### 2.7 · Source carriage and reproduction

```
inherits:    Product §11 (L1 computational correctness); Data plane §12.2 (Source carriage and reproduction), §4.3, §5
measured_by: census Carr.detector — NO_DETECTOR on 19/19
traces_to:   0.1
```

Tier 4's L1 adaptation row assigns the menu item at layer level: "`Carr` D3 dominates" (L1
computes; independent re-derivation is the fitting check). Measured: **no D1/D2/D3 detector exists
for any L1 asset** (census, 19/19 NO_DETECTOR — "which check applies is per-asset semantics").
`NO DETECTOR` is never a pass (tier 3 §2.7). For the obligations of §2.4, the a/b/c assignment
per obligation cannot be completed because §2.4's obligation list is itself INV-L1-06.

**C-9 confirmation (row 13):** the per-asset *named Jyotish concepts* each with the carriage check
it invites are not derivable from tiers 1–3 or the census. The census's own instrument declares
the per-asset assignment non-generic. **C-9 CONFIRMED for L1.** — see INV-L1-08.

### 2.5 · Edges and order

```
inherits:    Data plane §3.2; the registry DAG
measured_by: census Build.dag (all 19 PASS, edges resolvable, no cycles reported) — topological sort and egate.sql evaluation NOT in census
traces_to:   0.3
```

Edge counts per census (resolvable): ga_positions 0; ga_ayurdaya/ga_dashas/ga_sensitive_degree/
ga_transit_anchors/ga_vargas/ga_vastu 1; ga_medical/ga_panchanga/ga_prashna/ga_sensitive/
ga_strength/ga_yoga 2; ga_condition/ga_nakshatra/ga_tajaka 3; ga_vichara 4; ga_sade_sati/
ga_structural 7. ga_positions is the layer root (0 edges). Intra-layer blocking chains observed in
run history: ga_dashas → ga_condition/ga_sade_sati/ga_structural/ga_tajaka/ga_yoga; ga_condition →
ga_medical/ga_vastu; ga_strength+ga_structural → ga_vichara. The frozen definition revision the
gate ordering was evaluated against is **not stated by the census** — recorded, per tier 3 §2.5's
requirement ("State the frozen definition revision the gate was evaluated against").

---

## §4.4 · What each asset brief inherits — filled for L1

Per tier 3 §4.4 ("A brief that has to invent any of these has found a defect in this instance").
Rows 9–11 (the three value terms) are per-asset measurements no tier or census provides; row 12
(preserved kernel) is defined nowhere per asset; row 13 is C-9.

| # | item | L1-fillable from tiers + census? |
|---|---|---|
| 1 | P-needs / V-journeys the asset serves | **NO** — layer-level necessity set is itself INV-L1-01; per-asset narrowing doubly underivable |
| 2 | obligations scored on | **YES** — Computational correctness (tier 1 §11, L1 row), one row of the ten |
| 3 | correctness rules + switch | **PARTIAL** — §8.1 L1 row verbatim; switch behaviour INV-L1-04 |
| 4 | presentation fields | **PARTIAL** — via §3.4→DP mapping (INV-L1-05) |
| 5 | contracts produced/consumed with declared use | **YES at contract level** (DP01–DP05, DP07, field lists verbatim); per-asset field mapping from census keys; consumer-side verification NOT_MEASURED |
| 6 | coverage obligations + states | **NO** — obligation list INV-L1-06; states all "unqualified" per census width NOT_GENERIC |
| 7 | position in order + three-way baseline | **PARTIAL** — DAG edge counts give order; baseline's deployed-vs-code half INV-L1-03 |
| 8 | disposition + must-add | **NO** — tier 3 §3.2 requires Part 1 evidence per asset; census gives gate-level evidence but no rule mapping evidence → disposition (P/I/E/Q/C/H/R/U) per asset — INVENTED (folded into INV-L1-10) |
| 9 | individual term (contribution, measured) | **NO** — no ablation harness; absent instrument (not a number) |
| 10 | synergistic term | **NO** — no harness; tier 3 §1.5 forbids inventing a fraction |
| 11 | cross-layer term (produced contract, evidence state) | **PARTIAL** — produced contracts known (DP03/DP04/DP05/DP07); evidence state per contract at the consumer NOT_MEASURED |
| 12 | preserved kernel | **NO** — defined nowhere per asset; "what must survive any rebuild unchanged" is not stated in any tier for any L1 asset — INVENTED (INV-L1-10) |
| 13 | Jyotish concepts + carriage check | **NO** — **C-9 CONFIRMED for L1**; tier 4's L1 row gives only "Carr D3 dominates" at layer level; census: NO_DETECTOR ×19, "which check applies is per-asset semantics" — INVENTED (INV-L1-08) |

Gate-map (tier 3 §5.2) right-hand column: fillable for Ldgr (census keys), Idem (shared-table
natural key blocked by INV-L1-13), Build (census supplies), Carr (blocked by INV-L1-08); the map
exists in the template and is filled where the census reaches.

**INVENTED — the shared-table natural key for L1's Idem convention, clause that should have
provided it: "`Idem` is delete-then-insert on chart × natural key" (tier 4, Adapting per layer, L1
row). For `chart_facts`, written by 7 writers keyed on `fact_id`, "its own rows" per writer is
undefined — ga_nakshatra already carries ON CONFLICT against the convention (census Idem
PARTIAL).** — INV-L1-13.
