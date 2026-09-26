# L2 Bodha — LAYER INSTANCE SKELETON

**TEST ARTEFACT — NOT AN INSTANCE.** Derived 2026-09-26 by a fresh reader from tiers 1–3 plus the
inspector census only (`nikasha_test/census/L2_prod_20260926.json`, production, generated
2026-09-26T17:18:41+05:30; `L2_sandbox_20260926.json`, sandbox, 2026-09-26T21:07:57+05:30 — sandbox run,
structurally identical: same 23 assets, same targets). Every place the documents did not provide the
content is marked `INVENTED — <what>, clause that should have provided it: <quote>` and listed in
`L2_INVENTIONS.md`. Census readings that are themselves register-known-defective are flagged
`CENSUS CAVEAT` and not treated as ground truth.

Template: `LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md` (tier 3, SEALED). Only the sections the
campaign brief requires are filled: Part 0, §1.1, §2.1–§2.7, §4.4.

---

## Part 0 · VALUE — the origin

### 0.1 · What cannot be answered without this layer

```
inherits:    Product §2 (P01-P24), Data plane §2 (V01-V13)
measured_by: none — definitional
traces_to:   —
```

| P / V | the distinction that disappears without this layer |
|---|---|
| **INVENTED** — the necessity rows themselves. Neither parent assigns P-needs or V-journeys to layers; the sets are enumerated (P01–P24, V01–V13) but "necessary to L2" is nowhere stated. Clause that should have provided it: "List the P-needs and V-journeys for which this layer is **necessary** — not "involved in", not "contributes to", but *cannot be answered without*." (template §0.1). | Any specific P/V entry written here (e.g. "V0x whole-chart reading") would be invented. Proposed text in `L2_INVENTIONS.md` I-01. |

Only derivable statement: by tier-2 §3.1, L2 owns the question "What does the chart's connected
structure permit us to interpret?", so every P/V row whose answer requires whole-chart structure,
configurations, signed relationships, contradictions, alternate routes or candidate mechanisms is a
candidate row — but *which* of P01–P24 / V01–V13 those are is not stated in any readable tier.

### 0.2 · The layer's objective

```
inherits:    Product §1 (the join), §11 (this layer's row), Data plane §3.1 (this layer's row)
measured_by: none — definitional
traces_to:   0.1
```

Derivable without invention, quoted from the parents:

- **Owned question** (tier-2 §3.1): "What does the chart's connected structure permit us to interpret?"
- **Contribution handed onward** (tier-2 §3.1): "Whole-chart context, qualified structural propositions,
  signed relationships, configurations, contradictions, alternate routes and candidate mechanisms."
- **Must not claim** (tier-2 §3.1): "Graph centrality as causation, catalog matches as confirmed
  formation, temporal hooks as independent clock evidence."
- **Proof obligations scored on** (tier-1 §11, the ten-not-eleven set): **Concept and relationship
  completeness + Interpretive fidelity.**
- **Layer-distinctive fill** (template, adapting-per-layer table): "shared roots visible (several assets
  from one placement are not independent confirmations); 1.3 is where whole-chart reading lives or fails."
- **One-line identity** (tier-2 §6 closing): "Bodha makes it intelligible."

What it computes that existing software does not / what it hands the reasoning layer: **INVENTED** if
written in this layer's own words — the template asks for "the distinctions this layer makes earnable"
as a paragraph; the parents supply the table rows above but no L2 narrative beyond tier-2 §6.3's asset
families, which were not provided to this reader in full (summary level only). Recorded as I-02.

### 0.3 · Its place in the wheel

```
inherits:    Data plane §3.2 (five edge types), §7 (DP contracts)
measured_by: registry depends_on reconciled across seed, migration pin AND live asset_registry — state all three and any disagreement
traces_to:   0.2
```

- **Receives from** (tier-2 §7.1, derivable): DP02 (L0 rule qualification), DP03 (L1 chart facts),
  DP04 (L1 condition decomposition), DP05 (configuration, L0+L1 → L2). Edge types: computational.
- **Hands onward to** (derivable): DP06 structural relationship (L2 → L3 and inquiry); DP05 relayed
  onward (L2 → L3, "hydrate actual configuration before timing"); feeds DP08 (L2 + qualified clocks →
  L3 consumers).
- **What the join needs from it** (tier-1 §1 "the join"): the computed depth the reasoning layer reads
  across — whole-chart structure as above. Derivable at this generality only.
- **The three sources of the dependency graph, stated separately:** **CANNOT FILL — INVENTED if
  attempted.** The census reports per-asset edge *counts* ("6 edge(s), all resolvable") and names some
  dependencies only inside `Build.history` error text; it does not carry per-asset `depends_on` edge
  lists, and it reads the live registry only — no seed, no migration pin. Clause: "measured_by:
  registry depends_on reconciled across seed, migration pin AND live asset_registry — state all three
  and any disagreement" (template §0.3). I-03.

### 0.4 · The alignment test

Noted, not run (skeleton). Every section below names `traces_to:`.

---

## Part 1 · VALUE DECOMPOSITION

### 1.1 · Inventory, measured

```
inherits:    Data plane §13.3 item 2
measured_by: asset_registry (live, read-only) · the registry seed · the migration-governed pin · asset_throughput · the production probe — AS RUN: the L2 production census 2026-09-26 only (population: the 23 registered L2 assets)
traces_to:   0.3
```

**What the census provides (23 assets, all `has_writer`, all registered, 0 phantom, 0
never-exercised-with-writer, `local_map_candidates: -1` i.e. not measured):**

| asset | target table | rows (per Complete.depth) | Idem | Dens.served | Earn/Cost | Carr |
|---|---|---|---|---|---|---|
| bo_anveshana | bodha_discoveries | 3,695 (28/30 cols) | PASS | PASS (3 mod, 1 dc) | FAIL/FAIL (stale) | NO_DETECTOR |
| bo_arudha | **bodha_msr_signals** | 150,724 (40/85) | PARTIAL (ON CONFLICT) | PASS (9 mod, 3 dc) | FAIL/FAIL | NO_DETECTOR |
| bo_bimba | bodha_cgm_nodes | 1,101 (20/45) | PARTIAL (delegates) | FAIL (2 mod, 0 dc) | FAIL/FAIL | NO_DETECTOR |
| bo_cdlm_summary | bodha_cdlm_chart_summary | 15 (19/23) | PASS | PASS (1/1) | FAIL/FAIL (stale) | NO_DETECTOR |
| bo_cgm_motifs | bodha_cgm_motifs | 1,811 (16/16) | PASS | FAIL (1/0) | FAIL/FAIL (stale) | NO_DETECTOR |
| bo_cgm_paths | bodha_cgm_paths | 135 (20/20) | PASS | FAIL (1/0) | FAIL/FAIL | NO_DETECTOR |
| bo_chart_gestalt | bodha_chart_gestalt | 15 (19/20) | PASS | PASS (1/1) | FAIL/FAIL (stale) | NO_DETECTOR |
| bo_drishti | bodha_question_lenses | 180 (15/15) | PASS | PASS (2 mod, 1 dc) | FAIL/FAIL | NO_DETECTOR |
| bo_grounding (catalog DRAFT) | bodha_grounding_matches | 50,731 (10/13) | PARTIAL (ON CONFLICT) | N/A (0 mod) | FAIL/FAIL | NO_DETECTOR |
| bo_karanajala | bodha_cgm_edges | 2,517 (34/43) | PARTIAL (ON CONFLICT) | FAIL (2/0) | FAIL/FAIL | NO_DETECTOR |
| bo_laksana | **bodha_msr_signals** | 150,724 (40/85) | PARTIAL (ON CONFLICT) | PASS (9/3) | FAIL/FAIL | NO_DETECTOR |
| bo_laksana_rerank | **bodha_msr_signals** (writer file shared with bo_laksana) | 150,724 | PARTIAL | PASS | FAIL/FAIL | NO_DETECTOR |
| bo_nakshatra_semantic | **bodha_msr_signals** | 150,724 | PARTIAL | PASS | FAIL/FAIL | NO_DETECTOR |
| bo_pramana_mapa | synthesis_quality_scorecard | 3 (30/34) | PARTIAL (delegates) | FAIL (1/0) | FAIL/FAIL (stale) | NO_DETECTOR |
| bo_pratijna | bodha_pratijna | 405 (10/16) | PASS | PASS (1/1) | FAIL/FAIL (stale) | NO_DETECTOR |
| bo_samskara | bodha_signal_embeddings | 150,724 (10/10) | PARTIAL (ON CONFLICT) | PASS (2/1) | FAIL/FAIL | NO_DETECTOR |
| bo_samvada | **vw_chart_digest (a VIEW)** | 15 per Complete.depth; `live_rows=0`, `rows_written=1, live=0` | PARTIAL (delegates) | FAIL (1/0) | FAIL/FAIL (stale) | NO_DETECTOR |
| bo_sangati | bodha_cdlm_cells | 430 (30/59) | PASS | FAIL (3/0) | FAIL/FAIL | NO_DETECTOR |
| bo_special_lagna | **bodha_msr_signals** | 150,724 | PARTIAL | PASS | FAIL/FAIL | NO_DETECTOR |
| bo_sudarshana | **bodha_msr_signals** | 150,724 | PARTIAL | PASS | FAIL/FAIL | NO_DETECTOR |
| bo_upaya | bodha_rm_resonances | 135 (18/24) | PASS | FAIL (6/0) | FAIL/FAIL | NO_DETECTOR |
| bo_vargottama_dhana | **bodha_msr_signals** | 150,724 | PARTIAL | PASS | FAIL/FAIL | NO_DETECTOR |
| bo_yantra_mechanism | bodha_mechanisms | 1,868 (18/24) | PASS | PASS (2/1) | FAIL/FAIL (stale) | NO_DETECTOR |

Layer aggregates (all from the census): Build.registered/contract/target/dag/count_integrity/exercised/
dep_liveness PASS 23/23 · Build.history PARTIAL 23/23 (dominant text: "BLOCKED: upstream dependency(ies)
… did not complete in this run") · Build.completion N/A 22, PASS 1 · Earn.build_record FAIL 23/23
(`rows_per_second=NULL`) · Cost.baseline FAIL 23/23 · Carr.detector NO_DETECTOR 23/23 · Complete.width
NOT_GENERIC 23/23 ("no declared universe") · Reach.fields NOT_GENERIC 23/23 · Vocab.identity PASS 22/23
· Idem.pattern PASS 10, PARTIAL 13 (10× "ON CONFLICT where the layer convention is delete-then-insert",
3× "no idempotency pattern … likely delegates") · Dens.served PASS 14, FAIL 8, N/A 1.

**C-10 / R06 / R10 — CONFIRMED for L2, and worse than L0.** `bodha_msr_signals` has **seven**
registered producers (bo_arudha, bo_laksana, bo_laksana_rerank, bo_nakshatra_semantic,
bo_special_lagna, bo_sudarshana, bo_vargottama_dhana); the census credits each with the table's full
150,724 rows and 85 columns, and two of the seven (bo_laksana, bo_laksana_rerank) share one writer
file `bo_laksana.py`. §1.1's shape — one asset, a set of target tables, "row counts in production" —
cannot express seven producers sharing one table with per-producer row scopes. INVENTED if expressed
per asset without a producer-scope rule. Clause: "For each: target table(s) — a **set**, not one
pointer, for multi-table assets — row counts in production, columns, contract fields live, last build"
(template §1.1). I-04.

**"whether current code on any live head differs from what is deployed"** (template §1.1): **CANNOT
FILL.** The census reads registry + live tables + writer files at one head; it has no
deployed-vs-current-code comparison. INVENTED if written. I-05.

**Registry vs seed vs pin reconciliation** (template §1.1: "Three sources are reconciled, not one
read"): **CANNOT FILL** — the census reads the live registry only. I-03 (same gap as §0.3).

**CENSUS CAVEAT (register-known inspector defects, not ground truth):** R45 — `Build.dep_liveness`
reads PASS 23/23 while several assets' own build state is `stale`; R44 — Earn/Cost quote non-latest
`asset_throughput` rows; R46 — bo_samvada's `live_rows=0` is a stub `count_sql` (`SELECT 0`) while the
view returns 15 rows; R42 — `Build.completion` N/A "no count_sql" contradicts `count_integrity` PASS.

### 1.2–1.5 (not required by the campaign brief; recorded for the delta chain)

- **1.2 individual term:** L2 is a chart-product layer (`scoring: contribution` in the census), so the
  measure is ablation. No ablation harness exists; per the template's own escape each asset is
  "unmeasurable — not reached" where unserved, and unmeasured-where-served otherwise. Not an invention
  — the template prescribes the honest null.
- **1.3 synergistic term:** **DERIVATION BLOCKER.** The adapting-per-layer table makes this L2's
  defining term ("1.3 is where whole-chart reading lives or fails"), §1.3 inherits "the layer's synergy
  binding if one exists" — none exists for L2 — and §1.5 forbids inventing the fraction ("Record the
  synergistic term as a fraction of the total **only where an ablation harness exists to produce it** …
  Do not invent a fraction to fill the field."). Result: L2's elevation delta (1.5's shortfall) is
  unmeasurable exactly at the term that defines the layer. Absent instrument recorded. I-06.
- **1.4 cross-layer term:** DP06 (→ L3, inquiry) and DP05 relay. Census provides the `served` evidence
  state per asset (Dens.served module lists) but nothing "verified at the consumer"; the
  consumed/transformed states are unmeasured. Partial fill; consumer-verified states CANNOT FILL. I-07.

---

## Part 2 · CONDITIONS UNDER WHICH THE VALUE IS REAL

### 2.1 · Correctness rules

```
inherits:    Product §8.1 (this layer's row), §13; Data plane §9.2 (the switch and the storage separation)
measured_by: a detector per rule, named here, that can report the rule violated
traces_to:   0.2
```

Derivable:
- Product §8.1 L2 row (per tier-1 summary): L2 "must not make biography-dependent support appear
  event-free." (Correctness rule, verbatim-level from summary.)
- Tier-2 §3.1 must-not-claim row (0.2 above).
- Product §13: "No invented computation, source, detector, confidence, empirical score, or claim of
  exhaustive coverage."

**INVENTED — the life-event switch behaviour for L2** (what L2 may do when ON, what it emits when OFF,
and the storage separation that makes OFF a selection rather than a rebuild). The parents define the
switch and its storage separation *generally* (one switch, two states, state recorded in the forecast
emission record); nothing states L2's per-layer ON/OFF semantics. Clause that should have provided it:
"inherits: Product §8.1 (this layer's row), §13; Data plane §9.2 (the switch and the storage
separation)" (template §2.1) — the inherits list names the switch but no tier assigns its per-layer
behaviour. I-08.

**Detector per rule:** none exists in any provided source. Recorded **NO DETECTOR** per rule — the
template's own honest null ("A rule with no detector is a wish."). Not an invention; a measured gap.

### 2.2 · Presentation obligation

```
inherits:    Product §2 (two modes, one depth); Data plane §3.4 (the field → contract mapping)
measured_by: presentation-parity test (Data plane §12.2) — never run for L2
traces_to:   0.1
```

Partially derivable: tier-2 §3.4 maps acharya fields to DP contracts, and the rows whose carriage
contract L2 produces follow mechanically: **competing readings → DP06+DP02** and **typed chains →
DP06** are L2-carried. **INVENTED — the rest of the assignment boundary**: whether L2 also carries
method/school (DP02 relay), conventions (DP01/DP03 relay), intermediate quantities (DP03/DP04 relay)
is judgment; tier-2 §13.3 item 6 requires the layer plan to state "which §3.4 presentation rows this
layer carries and which fields it hands onward for them" but no tier states it for L2. I-09.

`[TRANSFERS]` note: the §12.2 test this section is measured by — **Presentation parity** — is itself
marked [TRANSFERS] in tier 2. A layer plan reading §2.2's `measured_by` cannot tell from the template
whether running that test is its own work. See I-20.

### 2.3 · Contracts produced and consumed

```
inherits:    Data plane §7 (DP01-DP17), §7.1 (common envelope)
measured_by: for each contract, the fields and grain actually present in the producer's table and actually read by the consumer — verified both ends
traces_to:   0.3
```

| direction | contract | producer → consumer | derivable content |
|---|---|---|---|
| produces | DP06 structural relationship | L2 → L3 and inquiry | actor/relation/target, signed support/opposition, ledgers, variants, ancestry (tier-2 §7.1 verbatim) |
| produces | DP05 relay (configuration, hydrated) | L0+L1 → L2 → L3 | "hydrate actual configuration before timing" |
| produces (feeds) | DP08 temporal mechanism input | L2 + qualified clocks → L3 consumers | mechanism/configuration ID, engaged participants, alternate routes |
| consumes | DP02 rule qualification | L0 → L2 | rule clauses, prerequisites/exceptions, witness variants |
| consumes | DP03 chart facts | L1 → L2 | fact_id, grain/value/unit, conventions; no re-derivation |
| consumes | DP04 condition decomposition | L1 → L2 | conditions/bala/roles; zeros as zeros |
| consumes | DP05 configuration | L0+L1 → L2 | every clause tested with its result |

**CANNOT FILL per asset:** which asset produces/consumes which contract, with declared use. The census
carries `depends_on` only as resolvable counts, no asset→DP-contract mapping. "A citation with no
declared use is not a contract" — and no declared-use field exists in the census. INVENTED if written
per asset. I-10.

### 2.4 · Jyotish coverage owned

```
inherits:    Product §3 (substance), Data plane §5 (domain obligations)
measured_by: per obligation: applied / inapplicable-with-reason / unavailable / unqualified / unresolved — the five states, never a blank
traces_to:   0.1
```

**INVENTED — which coverage obligations L2 owns.** Product §3 names instruments in substance (yoga/
doṣa/bhaṅga, sambandha chains, Bhāvat Bhāvam, varga, ārūḍha/special lagnas, nakshatra/KP …) and tier-2
§5 is referenced, but no tier assigns coverage obligations to L2 specifically. Clause: "Which of the
product's coverage obligations this layer owns, with prerequisites, variants, exceptions, negative
cases and uncertainty." (template §2.4). Census corroborates from the other side: `Complete.width`
NOT_GENERIC 23/23 — "no declared universe for this asset — declaring one is the first width gap".
I-11.

### 2.6 · Vocabulary conformance

```
inherits:    Data plane §4.1 (the controlled vocabulary — six rules with detectors)
measured_by: alias-set coverage per entity class · independent-map census per class · interface-parameter census · parity tests for code-side snapshots
traces_to:   0.2
```

**INVENTED — which of the sixteen entity classes L2 emits or accepts.** Derivable only by guessing
from table/column names (signals carry graha/yoga/doṣa/domain references). Nothing in tiers 1–2 or the
census assigns classes per layer; the census header reads `local_map_candidates: -1` (not measured)
and per-asset `Vocab.identity` PASS 22/23 covers rule-1 uniqueness only. Clause: "Which of the sixteen
entity classes this layer emits or accepts; for each, whether every name resolves through the
controlled set … how many independent maps the layer's code carries (permitted: one)" (template §2.6).
I-12.

### 2.7 · Source carriage and reproduction

```
inherits:    Product §11; Data plane §12.2 (Source carriage and reproduction), §4.3, §5
measured_by: the three checks (a source correspondence, b witness carriage, c independent re-derivation), each named per obligation this layer owns
traces_to:   0.1
```

**C-9 / R09 — CONFIRMED for L2 (fifth confirmation, first outside L0).** The template assigns the
checks at layer scope: "For each obligation the layer owns (§2.4), state which of a–c applies, the
detector, and its current result" (template §2.7) — and since §2.4's per-layer coverage ownership is
itself underivable (I-11), even the layer-scope assignment has nothing to attach to. The census reads
`Carr.detector` NO_DETECTOR for **23/23** L2 assets with the literal text "which check applies is
per-asset semantics" — i.e. the inspector itself declares the assignment per-asset while the template
provides no per-asset assignment surface. The §4.4 row-13 inheritance is therefore unfillable for
every L2 asset. I-13.

Layer-scope statement that IS derivable: L2 assets restate classical configurations (→ D1), carry
school-variant signals (→ D2), and compute graph/structural quantities (→ D3); all three menu items
apply somewhere in the layer — which is exactly why a layer-scope assignment cannot discharge row 13.

### 2.5 · Edges and order

```
inherits:    Data plane §3.2; the registry DAG
measured_by: topological sort of the reconciled depends_on from 0.3; cycle check; cross-layer gates via egate.sql scoped to the CURRENT frozen definition revision
traces_to:   0.3
```

**CANNOT FILL in full.** Census: Build.dag PASS 23/23 ("N edge(s), all resolvable", no cycles
reported) — but edge *lists* are not emitted, so no topological sort is derivable, and 0.3's reconciled
DAG does not exist (I-03). The "CURRENT frozen definition revision" the gate evaluation must be scoped
to is nowhere readable from the provided sources. INVENTED if an order or a revision id were written.
I-14. (Template defect noted by L0 as C-7/R08 — §2.5 is ordered after §2.7 — is inherited here
unchanged; the skeleton preserves the template's own order.)

---

## Part 4 · STRATEGY

### 4.4 · What each asset brief inherits

```
inherits:    Product §16; Data plane §13.3 (asset brief sentence)
measured_by: derivability — a brief author must be able to fill these from this instance alone
traces_to:   0.1
```

The thirteen rows, marked by whether this skeleton could supply them to a tier-4 brief:

| # | row (template §4.4) | state for L2 |
|---|---|---|
| 1 | P-needs and V-journeys the asset serves (0.1, narrowed) | **INVENTED** — 0.1 has no rows (I-01); narrowing nothing yields nothing. I-15 |
| 2 | the ten obligations it is scored on (0.2) | **PROVIDED** — concept/relationship completeness + interpretive fidelity (tier-1 §11); layer-level, not per-asset weighting |
| 3 | correctness rules and switch behaviour (2.1) | rules **PROVIDED** (§8.1 row, §3.1 must-not-claims, §13); switch behaviour **INVENTED** (I-08) |
| 4 | presentation fields (2.2) | **PARTIAL** — competing readings + typed chains derivable via DP06; the rest INVENTED (I-09) |
| 5 | contracts produced and consumed, with declared use (2.3) | layer-level **PROVIDED**; per-asset **INVENTED** (I-10) |
| 6 | coverage obligations and current states (2.4) | **INVENTED** (I-11); census confirms no declared universes (NOT_GENERIC 23/23) |
| 7 | position in the order + three-way baseline (2.5, 4.1) | **PARTIAL** — DAG resolvability PASS per asset; full order underivable (I-14); **deployed vs current-code delta absent from census** (I-05); the risk number (current code − deployed) is uncomputable |
| 8 | disposition and must-add list (3.2, 3.3) | **INVENTED** — dispositions require Part 1 measurements; 1.2 unmeasured and 1.3 unmeasurable (I-06), so any P/I/E/Q/C/H/R/U letter is supplied, not derived. I-16 |
| 9 | individual term, measured (1.2) | **ABSENT INSTRUMENT** — ablation never run; template-prescribed honest null, not an invention |
| 10 | synergistic term, which seam (1.3) | seam nameable from census module overlaps; measured term **ABSENT INSTRUMENT** (I-06) |
| 11 | cross-layer term, which contract at which evidence state (1.4) | contract **PROVIDED** (DP06); evidence state **PARTIAL** — census gives `served`; consumed/transformed "verified at the consumer" absent. I-07 |
| 12 | the preserved kernel (3.2) | **INVENTED** per asset — nothing in tiers or census defines it; §4.4 sources it "(from 3.2)" which is itself underivable (row 8). I-17 |
| 13 | the Jyotish concepts it touches, each with the carriage check (2.7, 5.2's menu) | **INVENTED — C-9/R09 confirmed for L2** (I-13); census: Carr NO_DETECTOR 23/23 |

**Score: 2 of 13 rows fully provided (2; and 3-half), 4 partial, 6 invented, 1 honest absent
instrument.** Under the template's own rule — "A brief that has to invent any of these has found a
defect in this instance, not in the brief" — an L2 instance derived from tiers 1–3 + census alone
cannot pass §5.4 test 1.

---

## [TRANSFERS] — can an L2 plan tell what is its own work?

Test per campaign brief. Tier-2 §1 defines the convention: "A [TRANSFERS] obligation is not a
data-plane layer's to build alone, and a layer plan does not inherit it as its own work." The marked
set is: all of tier-2 §8, plus the §12.2 rows Presentation parity and Delivery sentinel, plus (in the
tier-4 template §1.2/§9) the retrieval-reachability requirement.

**Finding: the marking is followable only if the reader already knows where it lives.** The
obligations a layer plan is told to discharge (tier-2 §13.3 items 1–8; template §2.2's `measured_by`)
do not carry the mark: §13.3 item 6 demands §3.4 presentation-row carriage while the test that scores
it (Presentation parity) is [TRANSFERS]; item 1's DP-contract inheritance includes DP10/DP11 whose
home (§8) is wholly [TRANSFERS]; the tier-4 template adds a *third* [TRANSFERS] location (§1.2) that
neither tier 2 nor tier 3 points to. An L2 plan cannot, from §13.3 + the layer template alone,
separate its own work from transferred work. INVENTED — the separation itself, if this skeleton
claimed one. Clause: "A [TRANSFERS] obligation is not a data-plane layer's to build alone, and a
layer plan does not inherit it as its own work." (tier-2 §1). I-20.

## Reference-layer vs chart-product layer — L2 applicability check

L2 is chart-product (`scoring: contribution`): the §1.2/§5.1 reference-layer clauses correctly do not
apply — no template defect there. The reverse asymmetry found: the template's escape hatches are
calibrated to a reference layer (fidelity is always measurable by inspection), while the
chart-product measures it mandates for L2 (ablation in 1.2, synergy in 1.3) have no prescribed
instrument at all — so a chart-product layer's *defining* terms are the unmeasurable ones (I-06).
Nothing in the template fails *only* for a reference layer from what L2 can see; the L0 instance's
C-8 (rule-1 detector) is already corrected at the tier-2 level L2 inherits.
