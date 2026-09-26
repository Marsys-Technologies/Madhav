---
artifact: L4_INSTANCE_SKELETON
canonical_id: NIKASHA_TEST_L4_INSTANCE_SKELETON
version: "0.1-test"
status: TEST ARTEFACT — NOT AN INSTANCE
layer: L4 Phala
derived_by: "fresh reader, Phase 4, campaign nikasha-test"
derived_on: 2026-09-26
sources_used:
  - tier1/tier2 structured summary (derivations/_tier1_tier2_summary.md)
  - LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md (tier 3, SEALED)
  - census: nikasha_test/census/L4_prod_20260926.json (production, read-only; generated 2026-09-26T17:23:36+05:30)
  - census cross-check: nikasha_test/census/L4_sandbox_20260926.json (sandbox; verdicts identical for L4)
---

# L4 Phala — layer-instance skeleton (TEST ARTEFACT — NOT AN INSTANCE)

TEST ARTEFACT — NOT AN INSTANCE. Derived mechanically for Phase 4 of campaign nikasha-test.
`INVENTED —` markers record every place the tiers + census did not supply the content.

## Part 0 · VALUE

### 0.1 · What cannot be answered without this layer

```
inherits:    Product §2 (P01-P24), Data plane §2 (V01-V13)
measured_by: none — definitional
traces_to:   —
```

| P / V | the distinction that disappears without this layer |
|---|---|
| INVENTED — the specific P-need and V-journey rows for L4. No parent document maps P01–P24 or V01–V13 to layers. Clause that should have provided it: template 0.1 `inherits: Product §2 (P01-P24), Data plane §2 (V01-V13)` — neither section contains a per-layer assignment; tier-1 §11 assigns *proof obligations* per layer, not P/V rows. Proposed fill (invented): P-needs in the "outcome/manifestation" family (e.g. P-rows on what a structure means in a stated life domain) and the V-journeys those serve | INVENTED — the loss-distinction per row |

### 0.2 · The layer's objective

```
inherits:    Product §1 (the join), §11 (this layer's row), Data plane §3.1 (this layer's row)
measured_by: none — definitional
traces_to:   0.1
```

DERIVED (tier 2 §3.1 row L4, verbatim): the question it owns — "What could that
structure-in-time mean in the person's stated life domain?"; contribution handed onward —
"Qualified manifestation alternatives, earned outcome propositions, falsifiers and action
constraints."; must not claim — "Automatic certainty or calibration; a generic domain score
as a specific outcome."
DERIVED (tier 1 §11 row L4): product responsibility "Qualified manifestation and earned
outcome interpretation"; proof "Interpretive fidelity + Distinctive understanding (§14) ...
no unqualified composite score."
DERIVED (tier 3 "Adapting the template per layer", L4 row): "the manifestation bridge and
its falsifier; no unqualified composite score; earned outcome interpretation".
INVENTED — the paragraph "what it computes that existing software does not, and what it
hands the reasoning layer to read across". No parent states L4's novel-computation claim.
Clause that should have provided it: template 0.2 "Name what it computes that existing
software does not, and what it hands the reasoning layer to read across." — the tiers name
responsibilities, not the distinct-from-existing-software claim.

### 0.3 · Its place in the wheel

```
inherits:    Data plane §3.2 (five edge types), §7 (DP contracts)
measured_by: registry depends_on reconciled across seed, migration pin AND live asset_registry — state all three and any disagreement
traces_to:   0.2
```

DERIVED (tier 2 §7.1, by the producer→consumer columns): L4 **consumes** DP03 (chart facts),
DP04 (condition decomposition), DP05 (configuration, via L2→L3 chain), DP08 (temporal
mechanism), DP09 (Manifestation — "L3+qualified structural/rule evidence → L4").
PARTIALLY INVENTED — which contracts L4 **produces**. Tier 2 §7.1's table gives
producer→consumer pairs, from which consumption is readable, but no clause states a per-layer
production rollup for L4 (DP14 names "independent L1/L2/L3/L4 context" as comparison input;
DP15a "Completed reading → protected claim authority" — whether L4 is that producer is
inference, not text). Clause that should have provided it: template 0.3 "Receives from:
upstream layers, by edge type, by DP contract. Hands onward to: downstream layers, by edge
type, by DP contract." — the data plane does not tabulate this per layer.
INVENTED — edge types per edge (definition/computational/serving-context/evaluation/
next-generation). §3.2 defines the five types but assigns none to L4's edges.
NOT MEASURED from census — the census does not reconcile "registry depends_on across seed,
migration pin AND live asset_registry"; it reads the live registry only. The three-source
reconciliation the `measured_by` line demands has no instrument in the census.
Census-provided edges (production, L4_prod_20260926.json): ph_muhurta 8 resolvable edges;
ph_nimitta 9; ph_rectification 1; others resolvable. `Build.dep_liveness` FAIL on all 9
assets: declared dependencies not lit — ph_muhurta: [ph_nimitta, ka_kalasutra,
ka_vighnakara, ka_sangam]; ph_nimitta: [ka_sangam, ka_bhavishya_lekha]; (each asset's own
list in census). Cross-layer receive edges into L4 are therefore from L3 (ka_*) — consistent
with DP07/DP08/DP09 consumption.

### 0.4 · The alignment test

DERIVED (template): every section below carries `traces_to:`. N/A to fill at skeleton level.

## Part 1 · VALUE DECOMPOSITION

### 1.1 · Inventory, measured

```
inherits:    Data plane §13.3 item 2
measured_by: asset_census.py --layer L4 against production read-only proxy (PGPORT=5433), 2026-09-26; asset_census.py against sandbox (L4_sandbox_20260926.json) — identical verdicts
traces_to:   0.3
```

Census-provided (production): 9 assets, `scoring: contribution`, registered_ids 8,
registry_has_writer 9, phantom_registered 0, never_exercised_with_writer 0.

| asset | target_table | has_writer | writer file | catalog | rows (Complete.depth) | non-PASS census readings |
|---|---|---|---|---|---|---|
| ph_muhurta | phala_muhurta | true | ph_muhurta.py | CURRENT | 183 rows, 24 cols, 21 fully populated | Earn.build_record FAIL; Cost.baseline FAIL; Dens.served FAIL (3 modules, 0 density_contract); Build.history PARTIAL (29 err / 10 abort); Build.dep_liveness FAIL; Complete.width NOT_GENERIC; Carr.detector NO_DETECTOR; Reach.fields NOT_GENERIC |
| ph_nimitta | phala_anchors | true | ph_nimitta.py | CURRENT | 60 rows, 37 cols; NEVER populated: subsystem_source, karmic_frame, karmic_note | Earn FAIL; Cost FAIL; Complete.depth PARTIAL; Build.history PARTIAL (30 err / 10 abort); dep_liveness FAIL; width NOT_GENERIC; Carr NO_DETECTOR; Reach NOT_GENERIC |
| ph_phaladesa | phala_phaladesa | true | ph_phaladesa.py | CURRENT | PARTIAL depth | Earn FAIL; Cost FAIL; depth PARTIAL; Dens FAIL; history PARTIAL; dep_liveness FAIL; width NOT_GENERIC; Carr NO_DETECTOR; Reach NOT_GENERIC |
| ph_pramana | phala_pramana | true | ph_pramana.py | CURRENT | PARTIAL depth | same profile as ph_phaladesa |
| ph_pratikara | phala_mitigation | true | ph_pratikara.py | DRAFT | PARTIAL depth | same profile |
| ph_rectification | phala_rectification | true | **census: none found** | CURRENT | depth PASS-level not stated | **Build.registered FAIL** ("registry says has_writer=true and no @register found"); contract N/A; Idem N/A; plus the common profile |
| ph_sankrama | phala_sankrama | true | ph_sankrama.py | CURRENT | PARTIAL depth | common profile |
| ph_sodhana | phala_sodhana | true | ph_sodhana.py | CURRENT | PARTIAL depth | common profile |
| ph_suddha_sodhana | phala_suddha_sodhana | true | ph_suddha_sodhana.py | CURRENT | PARTIAL depth | common profile |

Three-source disagreements found while filling this section (findings, not inventions):
- **ph_rectification:** census `Build.registered` = FAIL, but
  `platform/python-sidecar/pipeline/orchestrator/writers/ph_rectification/__init__.py:246`
  contains `@register("ph_rectification")` (grep over
  `platform/python-sidecar/pipeline/orchestrator/writers/**` at this branch head). Code and
  registry agree; the inspector's registered check does not find `@register` inside a writer
  **package** (`__init__.py`). Inspector false positive.
- **ph_muhurta internal contradiction:** `Build.count_integrity` PASS ("count_sql=yes") while
  `Build.completion` reads N/A with "no count_sql; build state='stale'". Two checks read the
  same field differently.
- **Shared-table check (C-10/R06/R10) — REFUTED for L4:** every L4 `target_table` is
  distinct, and `grep -l "INSERT INTO phala_"` over the writers tree matches only the owning
  ph_* writer each (mi_bhavisya.py and ka_bhavishya_lekha.py mention phala_* names but do not
  insert). No multi-producer table in L4.

INVENTED — "whether current code on any live head differs from what is deployed" per asset.
Clause that should have provided it: template 1.1 "For each: ... and whether current code on
any live head differs from what is deployed." — no instrument named for the deployed-vs-code
diff; the census does not produce it.
INVENTED — the residual / shared / historical-capital split. Clause: template 1.1 "Every
asset and service the layer owns: registered, writer-backed, service (no table by design),
residual, shared, historical." — no parent classifies L4's 9 assets into these kinds; the
census carries no such field. (All 9 look writer-backed data; no service asset is visible.)

## Part 2 · CONDITIONS

### 2.1 · Correctness rules

```
inherits:    Product §8.1 (this layer's row), §13; Data plane §9.2
measured_by: a detector per rule, named here
traces_to:   0.2
```

DERIVED (tier 1 §8.1, L4 row): L4 "must not rewrite the original forecast."
DERIVED (tier 1 §13): "No invented computation, source, detector, confidence, empirical
score, or claim of exhaustive coverage."
DERIVED (tier 3 adaptation row, L4): "no self-calibration; a forecast is emitted only when
earned; the bridge or its falsifier is a carried field" (tier-4 template's L4 row).
INVENTED — a named detector per rule. Clause: template 2.1 "**For each rule, the detector.**
A rule with no detector is a wish." — no tier names any L4 detector (e.g. a detector for
"forecast not rewritten" = DP15a's emission-time freeze check). Census confirms:
`Carr.detector` NO_DETECTOR on all 9 assets.

### 2.2 · Presentation obligation

```
inherits:    Product §2; Data plane §3.4
measured_by: presentation-parity test — NOT RUN here (§3.4 parity is [TRANSFERS] per data plane §1)
traces_to:   0.1
```

DERIVED (tier 2 §3.4 mapping, generically): method/school → DP02; passed clauses → DP05;
conventions → DP01/DP03; intermediate quantities → DP03/DP04; dignity components → DP04;
competing readings → DP06+DP02; clock geometry/activation/manifestation bridge →
DP07/DP08/DP09.
INVENTED — **which** of these rows L4 carries. Clause that should have provided it: tier 2
§13.3 item 6 "including which §3.4 presentation rows this layer carries and which fields it
hands onward for them" — the *requirement to state it* exists; the *assignment* does not. A
fresh reader must guess that L4 carries the "manifestation bridge / falsifier" half of the
DP09 row and hands the rest onward.
[TRANSFERS] note: the presentation-parity *test row* itself is marked [TRANSFERS] (data
plane §1: "A [TRANSFERS] obligation is not a data-plane layer's to build alone, and a layer
plan does not inherit it as its own work."), so this section can state carried fields but the
L4 plan cannot claim the parity test as its own work. **The template does not say so** —
clause: template 2.2 `measured_by: presentation-parity test (Data plane §12.2)` names the
test without its [TRANSFERS] marking.

### 2.3 · Contracts produced and consumed

```
inherits:    Data plane §7 (DP01-DP17), §7.1
measured_by: field/grain verification at both ends — NOT MEASURED (census does not read fields against contracts)
traces_to:   0.3
```

DERIVED at layer scope: consumed DP03, DP04, DP05 (via chain), DP08, DP09 (see 0.3).
INVENTED — produced contracts (see 0.3) and every "declared use" per consumed contract.
Clause: template 2.3 "Every consumed input declares its use — calculation, applicability,
counter-evidence, uncertainty, interpretation, exclusion, navigation, evaluation. **A
citation with no declared use is not a contract.**" — no parent declares uses per layer per
contract.

### 2.4 · Jyotish coverage owned

```
inherits:    Product §3 (substance), Data plane §5
measured_by: the five states per obligation
traces_to:   0.1
```

INVENTED — which of the product's coverage obligations L4 owns. Clause: template 2.4 "Which
of the product's coverage obligations this layer owns, with prerequisites, variants,
exceptions, negative cases and uncertainty." — no per-layer coverage assignment exists in
tier 1 §3 or tier 2 §5 as readable here. Census side-evidence: `Complete.width`
NOT_GENERIC on all 9 assets ("no declared universe for this asset") — so even the census has
no universe to measure against; the layer instance is where universes would have to be
declared, and the template does not say that (register R22 territory).

### 2.5 · Edges and order

```
inherits:    Data plane §3.2; the registry DAG
measured_by: census Build.dag + Build.dep_liveness (production, 2026-09-26)
traces_to:   0.3
```

DERIVED (census): every asset's declared edges resolvable (Build.dag PASS × 9).
DERIVED (census): Build.dep_liveness FAIL × 9 — declared L3 dependencies not lit
(ka_kalasutra, ka_vighnakara, ka_sangam, ka_bhavishya_lekha recur). Intra-layer order:
ph_nimitta precedes ph_muhurta (ph_muhurta depends on ph_nimitta).
INVENTED — a topological order beyond those two facts, and the "frozen definition revision"
for the egate. Clause: template 2.5 `measured_by: topological sort of the reconciled
depends_on from 0.3; cycle check; cross-layer gates via egate.sql scoped to the CURRENT
frozen definition revision` — the three-way reconciled DAG does not exist (0.3 NOT MEASURED),
so the sort cannot be derived.

### 2.6 · Vocabulary conformance

```
inherits:    Data plane §4.1 (six rules)
measured_by: census Vocab.identity (declared-key duplicate counts)
traces_to:   0.2
```

DERIVED (census): Vocab.identity PASS on the writer-backed assets measured (e.g.
ph_muhurta key (muhurta_id): 0 duplicates; ph_nimitta key (anchor_id): 0 duplicates).
INVENTED — which of the sixteen entity classes L4 emits or accepts, and the per-class
independent-map census. Clause: template 2.6 "Which of the sixteen entity classes this layer
emits or accepts; for each, whether every name resolves through the controlled set ... how
many independent maps the layer's code carries (permitted: one)" — no parent maps entity
classes to layers. Census field `local_map_candidates: -1` (i.e. not computed) confirms the
instrument gap.

### 2.7 · Source carriage and reproduction

```
inherits:    Product §11; Data plane §12.2 (Source carriage and reproduction), §4.3, §5
measured_by: the three checks (a/b/c) per obligation
traces_to:   0.1
```

DERIVED (shape): the three-check table (a source correspondence, b witness carriage,
c independent re-derivation) and the NO-DETECTOR-is-never-a-pass rule.
**C-9 / R09 CONFIRMED for L4** — the carriage check is assigned at layer scope only:
clause, template §2.7 "For each obligation the layer owns (§2.4), state which of a–c
applies, the detector, and its current result". Nothing assigns a/b/c **per asset**, so
§4.4 row 13 cannot be filled from this section. Census confirms operationally:
`Carr.detector` = NO_DETECTOR on all 9 L4 assets, with the inspector's own note "which check
applies is per-asset semantics".
Chart-product note: §2.7's narrative ("A reference layer is where this matters most") is
reference-layer-flavoured; for L4 the applicable check is mostly (a) source correspondence
on rule restatements and (c) re-derivation on computed phala quantities — but that selection
is INVENTED here, per the C-9 defect.

## §4.4 · What each asset brief inherits (the thirteen rows, layer-scope fill)

```
inherits:    Product §16; Data plane §13.3
measured_by: derivability
traces_to:   0.1
```

| # | row | L4-scope value derivable from tiers + census? |
|---|---|---|
| 1 | P-needs and V-journeys | **NO — INVENTED** (0.1; no per-layer P/V map) |
| 2 | ten-obligation subset | **YES** — Interpretive fidelity + Distinctive understanding (tier 1 §11 L4 row; "ten, not eleven", ruling 11) |
| 3 | correctness rules + switch behaviour | **PARTIAL** — "must not rewrite the original forecast" (tier 1 §8.1); the *switch behaviour* ("what this layer may do when ON, what it emits when OFF") is INVENTED — no parent states L4's switch behaviour |
| 4 | presentation fields | **INVENTED** (2.2; row assignment absent) |
| 5 | contracts produced/consumed with declared use | **PARTIAL/INVENTED** (0.3, 2.3) |
| 6 | coverage obligations + current states | **INVENTED** (2.4); census adds: width NOT_GENERIC on all 9 |
| 7 | position in order + three-way baseline | **PARTIAL** — census gives edges, build states (stale/error), run counts; the "current code on any live head" leg of the baseline has no instrument (template §4.1 "newest on any live head, including unmerged") |
| 8 | disposition + must-add list | **INVENTED** — dispositions require Part 1 measurements (1.2–1.4) that require an ablation harness that does not exist; template 1.5 permits recording "harness absent", but no row-by-row disposition follows |
| 9 | individual term, measured | **NO — blocked, not invented** — ablation harness absent; template 1.2 "Do not invent a contribution; record ≈ 0" applies only where ablation ran and found no reader |
| 10 | synergistic term | **NO — blocked** — template 1.3/1.5: record seam-by-seam and name the harness a packet |
| 11 | cross-layer term | **PARTIAL** — census gives evidence-state-adjacent data (Dens.served modules per asset) but not the six-state position "verified at the consumer" (template 1.4 measured_by) |
| 12 | preserved kernel | **INVENTED** — no parent states per-asset kernels for L4; template §4.4 says "(from 3.2)", and 3.2's dispositions are themselves invention-blocked |
| 13 | Jyotish concepts + carriage check each invites | **INVENTED — C-9/R09 confirmed** — clause: template §2.7 "For each obligation the layer owns (§2.4), state which of a–c applies" (layer scope only); also template §4.4 row: "the relevant Jyotish concepts the asset touches, named, with the domain detector each invites (2.7, 5.2's menu)" — demands per-asset content 2.7 does not produce |

[TRANSFERS] test result for L4 (campaign question: can the layer plan tell what is its own
work?): **NO for the served-surface rows.** Census marks `Dens.served` FAIL on 5 of 9 assets
because serving modules (`index.ts`, `query_phala_calibration.ts`, `salience_order.ts`, ...)
lack `density_contract` declarations. Those modules are retrieval-plane surface; tier 2 §1
says a [TRANSFERS] obligation "is not a data-plane layer's to build alone, and a layer plan
does not inherit it as its own work" — but the tier-3 gate table lists `Dens` as a gate the
L4 plan must close ("conditional on: the asset reaches a served surface"), and nothing in
the template tells the L4 author that fixing serving modules is not L4's work. The plan
cannot tell. Confirmed ambiguity.
