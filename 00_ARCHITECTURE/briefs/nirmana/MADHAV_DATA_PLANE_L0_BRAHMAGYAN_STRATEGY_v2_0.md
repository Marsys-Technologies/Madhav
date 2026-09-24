---
artifact: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY
canonical_id: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY
version: "2.0"
status: DRAFT_FOR_INDEPENDENT_REVIEW
produced_on: 2026-09-25
decision_owner: Native
template: 00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md   # first instance; template defects found here are fixed THERE
inherits:
  - 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md                                    # tier 1
  - 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md          # tier 2
supersedes_on_acceptance: 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v1_0.md  # v1.0 (APPROVED_STRATEGY, parent product v3.0) stays authoritative until this instance passes §5.4
measured_on: 2026-09-25
measured_against:
  registry: "live asset_registry (read-only), 40 bg_* rows"
  seed: "platform/scripts/seed/asset_registry_seed.ts @ l3/kala-layer-briefs 85bf8f14e, 40 bg_* rows"
  manifest: "nirmana_evidence frozen definition t3-2026-09-11-8b884eac, 40 bg_* assets"
  production: "information_schema + pg_class.reltuples (estimates marked ~) + exact count(*) where stated"
  code_readers: "grep over platform/python-sidecar (*.py, excl. tests/migrations/scripts) and platform/src + platform-mcp/src (*.ts, excl. tests/generated) at 85bf8f14e"
  evidence_ledger: "nirmana_evidence.nirmana_elevation_campaign_events, entity_type=asset"
not_measured: "ablation deltas (no L0 ablation harness exists); presentation-parity test (not run); whether any bg_* table carries a subject/chart column (not checked); whether brahma_remedy_corpus.source_canonical_id values resolve to a texts registry (not checked)"
---

# L0 Brahmagyan — definition, strategy and evaluation (template instance 1)

This is the first instance of the layer template. Where the template proved insufficient, that is
recorded in §6 for repair in the template, not worked around here.

---

## Part 0 · VALUE — the origin

### 0.1 · What cannot be answered without this layer

```
inherits:    Product §2 (P01–P24), Data plane §2 (V01–V13)
measured_by: none — definitional; every P/V below exists in PRODUCT_DEFINITION_FINAL under current numbering
traces_to:   — (origin)
```

L0 is the only layer that is necessary to **every** P-need and yet directly serves few of them. Two
kinds of necessity, kept apart:

**Directly served — the customer reads L0 itself, through the `ref_*` / text tools:**

| P / V | the distinction that disappears without this layer |
|---|---|
| P22 · V08 "Let me read the texts themselves" | There is no text. `bg_texts` (10,651 chunks, 14 texts), `bg_compendium_index`, `bg_text_index` are the whole corpus. |
| P15 · V08 "What supports this, where do schools disagree?" | No source witness, no attribution, no school. `bg_concordance`, `classical_attributions`, the `school` column on the yoga/doṣa/daśā catalogs. |
| P16 · V09 "Give me this exact fact" | The `ref_*` surface — 49 capability files — is L0's direct answer to a reference question. Without it a lookup becomes an interpretation. |
| P21 · V05 "What does this day mean in context?" | `bg_panchanga` (service), `bg_sky_calendar`, `bg_muhurta_lattice`. General calendar context is L0's; personal relevance is L3's. |
| P11 · V05 "Which practices can I explore?" | `bg_remedies` (341), `bg_parihara_rules` (60). The attributed catalog of practices is L0. |
| P07 · V12 "What does the tradition say about wellbeing?" | `bg_medical_mappings`, `bg_nakshatra_medical`, `bg_sign_medical` — the tradition's own correspondences, served as testimony. |
| P09 · V04 "Does this yoga form?" | Formation *definitions* — `bg_yogas` (233), `bg_doshas` (79). Formation itself is L1; the catalog it is tested against is L0. |
| P13 · V07 "Does a different convention change this?" | The conventions are L0: `bg_dignity_reference` (with `variant_traditions`), `bg_formula_constants`, `bg_kp_sublord_division`, and since migration 1076 the node frame on `ephemeris_daily`. |
| P23 · V12 "What does the tradition say about lifespan?" | The *method* — `bg_dasha_systems`, `bg_formula_constants`. The computation is L1's `ga_ayurdaya`; the schools and their constants are L0's. |

**Necessary to everything — no P-need survives its absence, though none names it:**

| what L0 supplies | which P-needs fall without it | measured reach |
|---|---|---|
| one identity per entity — `bg_ontology` (741), `bg_reference` (11) | all 24; a Sun that is three Suns breaks every reading | `brahma_ontology` read by 12 writer files + 6 serving files; **registered downstream consumers: 0** |
| the sky — `bg_ephemeris` (~824,543 rows), `bg_ephemeris_engine`, `bg_gochara_arcs` (~33,933) | every timed need: P09, P10, P21, P24, and every forecast | `ephemeris_daily` read by 28 writer files + 14 serving; registered: 5 |
| the event vocabulary — `bg_ghatana` (27) | P10, P12, P24, and all of L4/L5 | `brahma_event_ontology` read by 31 writer files + 21 serving; registered: 5 |
| the rule and formation vocabulary — `bg_rules` (3,002), `bg_yogas`, `bg_doshas`, `bg_transit_rules` (76) | P09, P10, P15 and every L2 mechanism | `bg_transit_rules` read by 26 writer files + 9 serving; registered: 6 |

The second table is L0's real value, and it is almost entirely **cross-layer handoff** (§1.4). The
first is what a customer can see.

### 0.2 · The layer's objective

```
inherits:    Product §1 (the join), §11 L0 row; Data plane §3.1 L0 row, §6.1
measured_by: none — definitional
traces_to:   0.1
```

L0 is where computation gets its **meaning**. The product's differentiator is a join — depth of
computation and an AI that reads across it — and L0 is the half of that join nobody sees: without a
single identity per entity, a qualified source behind every rule and a declared convention behind
every number, the computed estate is uninterpretable and the reasoning layer has nothing qualified to
read. L0 makes the depth *legible*. It computes little itself (the astronomical substrate and the
calendar lattice are the exceptions), and what it computes it computes once, globally, for every chart.

Inherited verbatim, not restated:

- **Owned question** (DP §3.1): *What does a term, rule, method or reference quantity mean, and when is
  it applicable?*
- **Contribution handed onward:** canonical identities; source-qualified doctrine; constants;
  astronomy/calendar foundations; method/prerequisite/exception vocabulary.
- **Must not claim:** personal fate, raw private biography as global truth, source count as probability.
- **Product responsibility** (Product §11): qualified vocabulary, sources, rules, constants, reference
  systems, ephemeris and calendar foundations.
- **Scored on** (Product §11 → §14): **Source and domain fidelity** — canonical identity, source
  fidelity, method boundaries. This instance adds **computational correctness** for the astronomical
  substrate (`bg_ephemeris`, `bg_ephemeris_engine`, `bg_gochara_arcs`, `bg_sky_calendar`,
  `bg_muhurta_lattice`), which is computed, not transcribed, and **delivery fidelity** for the 49-file
  served surface. Reasoning: the product row names the obligation that dominates; the ablation in §5.1
  cannot score a computed table on source fidelity alone.

### 0.3 · Its place in the wheel

```
inherits:    Data plane §3.2 (five edge types), §7 (DP01, DP02, DP07, DP13-vocabulary)
measured_by: live asset_registry.depends_on · seed · migration pin (not separately readable for L0 — no L0 parity test pins exist; the pin instrument is L3-only today) · actual code reads (grep, §1.1)
traces_to:   0.2
```

**Receives from:** nothing inside the plane. L0 is the root. Its inputs are external — the classical
texts, the Swiss ephemeris files, the seeded reference doctrine — and the *declaration* of those
inputs is part of L0's own job (edition, rights, engine version, node frame).

**Hands onward, by contract:**

| contract | producer assets | declared consumers (registry) | actual readers (code) |
|---|---|---|---|
| DP01 identity / release | `bg_ontology`, `bg_reference`, `bg_nakshatra` | `ga_sensitive`, `ga_nakshatra` | 12 + 4 + 8 writer files; 6 + 0 + 2 serving |
| DP02 rule qualification | `bg_rules`, `bg_yogas`, `bg_doshas`, `bg_dasha_systems`, `bg_transit_rules`, `bg_parihara_rules` | `bo_laksana`, `mi_kula`; six `ka_*` on transit_rules | 10 / 8 / 7 / 5 / 26 / 3 writer files |
| DP07 clocks (sampled substrate) | `bg_ephemeris`, `bg_gochara_arcs`, `bg_sky_calendar` | five `ka_*`; `ka_gochara_v3_century_materialize` | 28 / 7 / 6 writer files |
| DP13 event vocabulary (L0 half) | `bg_ghatana` | `ka_avadhi`, `ka_taranga`, `ka_yojaka`, `mi_jivanaghatana`, `mi_pramana` | 31 writer files, 21 serving |
| constants | `bg_formula_constants` | `mi_gunanaka`, `mi_pariksha`, `mi_pramana` | 8 writer files |

**The three dependency sources disagree**, and the template's demand to state all three is what
surfaced it:

- **Registry vs actual reads.** 21 of 40 L0 assets have **zero registered downstream consumers**;
  **40 of 40 are read by code**. `brahma_ontology` — the identity authority — has 0 registered
  consumers and 18 reading files. The declared dependency graph is a small fraction of the real one.
  Consequence: a change to `bg_ontology` stales *nothing* through the orchestrator, because nothing
  declares it. This is the DP01 risk ("local representations cannot diverge in meaning") in its exact
  mechanical form.
- **Seed vs registry.** The seed gives `target_table: None` for `bg_ephemeris`, `bg_rules`,
  `bg_concordance` (live: `ephemeris_daily`, `sutravali_rules`, `classical_attributions`); gives
  `bg_ephemeris_engine` a target of `reference_nakshatra` (it is a service; live: NULL); gives
  `bg_prashna_rules` a target of `bg_vastu_directions` (live: NULL — it is a five-table asset whose
  `count_sql` sums `bg_prashna_lagna_methods`, `_tajik_yogas`, `_significators`,
  `_fructification_rules`, `_special_techniques`). Live carries edges the seed lacks: `bg_rules` (3 vs
  0), `bg_concordance` (4 vs 0).
- **Pin.** No migration-governed dependency pin exists for L0 (the parity test that pins L3 does not
  cover `bg_*`). So the "third source" the template requires is *absent*, not merely different.

**What the join needs from L0:** one identity per entity across Python and TypeScript (the Sun
problem, DP §4.1); a school/tradition and a source witness on every rule the reasoning layer might
cite; declared conventions on every number; and a served reference surface that answers "what does
this mean" without manufacturing interpretation.

### 0.4 · The alignment test

Applied to every section below. **Struck from v1.0 and not carried:** nothing substantive — v1.0's
twelve L0-Q acceptance questions are absorbed into 0.1 and 2.4, and its ten L0-C capability contracts
into 2.3, so the cleanse-cost check in review should look there. Its per-asset disposition table (§5)
is carried into 3.2 with measured updates.

---

## Part 1 · VALUE DECOMPOSITION

### 1.1 · Inventory, measured

```
inherits:    Data plane §13.3 item 2
measured_by: live asset_registry · seed · pg_class/information_schema · code-reader grep · asset_throughput · nirmana_evidence
traces_to:   0.3
```

40 assets: 36 `postgres_table`, 2 services. Of the 36, four have `has_writer=false` and each has an
honest reason on the evidence ledger — `producer_covered` (rider on another asset's multi-`@register`
writer: `bg_transit_engine` on `bg_transit_rules`; `bg_nakshatra_medical`, `bg_sign_medical` on
`bg_medical_mappings`), `static` (`bg_gochara_citation_resolution`, migration-seeded), `empty`
(`bg_sarvatobhadra_grid`, 0 rows by adjudication). All 40 are `lit` in `asset_throughput`. All 40 are
`asset_frozen` under **t0 only**; **0 under the current definition t3**.

| asset | table(s) | rows | cols | provenance columns present | integrity check | reg. downstream | code readers (writer / serving) |
|---|---|---|---|---|---|---|---|
| `bg_ontology` | brahma_ontology | 741 | 9 | canonical_id, names en/sa, source_citation | ✓ | **0** | 12 / 6 |
| `bg_reference` | reference_planets | 11 | 14 | names en/sa, source_citation | ✓ | 1 | 4 / **0** |
| `bg_nakshatra` | reference_nakshatra | 28 | 46 | classical_source, tradition_scope | ✓ | 1 | 8 / 2 |
| `bg_texts` | classical_text_chunks | ~10,651 | 26 | chunk_id, text_id, source_citation, tradition_school, translation_provenance, ocr_* | ✓ | **0** | 29 / 11 |
| `bg_text_index` | classical_text_chunks (embedding + topic_tag partition) | — | — | (same table) | ✓ | **0** | (same) |
| `bg_compendium_index` | brahma_compendium_index | ~9,571 | 13 | chunk_ids, text_id | ✓ | **0** | 1 / 4 |
| `bg_concordance` | classical_attributions | 721 | 11 | attribution_id, rule_ids, school, source_chunk_ids, source_text_ids, match_confidence | ✓ | **0** | 2 / 4 |
| `bg_rules` | sutravali_rules | 3,002 | 14 | rule_id, text_id, verse_ref, confidence, yoga_canonical_id, dasha_system_id | ✓ | 2 | 10 / 5 |
| `bg_yogas` | brahma_yoga_catalog | 233 | 19 | canonical_id, classical_citations, school, source_chunk_ids | ✓ | **0** | 8 / 5 |
| `bg_doshas` | brahma_dosha_catalog | 79 | 14 | canonical_id, classical_citations, school, source_chunk_ids | ✓ | **0** | 7 / 5 |
| `bg_dasha_systems` | brahma_dasha_systems | 20 | 14 | canonical_id, classical_citations, school, source_chunk_ids | ✓ | **0** | 5 / 5 |
| `bg_remedies` | brahma_remedy_corpus | 341 | 26 | source_canonical_id, source_citation, confidence | ✓ | **0** | 6 / 15 |
| `bg_parihara_rules` | bg_parihara_rules | 60 | 14 | dosha_canonical_id, source_text_id, source_chapter, source_citation | ✓ | **0** | 3 / 7 |
| `bg_ghatana` | brahma_event_ontology | 27 | 19 | citations, version | ✓ | 5 | 31 / 21 |
| `bg_class_priors` | brahma_class_priors (prior_version='1.0') | 177 total | 13 | citation, prior_version, signal_tradition, source_ref, source_subsystem | ✓ | 1 | 9 / 2 |
| `bg_class_lifetime_counts` | brahma_class_priors (prior_version='ne_v01', fact_kind) | (shared) | — | (same) | ✓ | 1 | (same) |
| `bg_cohort` | bg_synthetic_cohort | ~10,000 | 11 | source_citation | ✓ | 1 | 3 / **0** |
| `bg_formula_constants` | brahma_formula_constants | 17 | 9 | citation_or_ratification, version | ✓ | 3 | 8 / 3 |
| `bg_dignity_reference` | bg_dignity_reference | 9 | 13 | classical_citation, variant_traditions | ✓ | 1 | 6 / 11 |
| `bg_kp_sublord_division` | bg_kp_sublord_division | 249 | 14 | source_citation, table_version | ✓ | 1 | 6 / 2 |
| `bg_ephemeris` | ephemeris_daily | ~824,543 | 15 | source_citation (+ node_mode, epoch_convention since 1076) | ✓ | 5 | 28 / 14 |
| `bg_ephemeris_engine` | (service) | — | — | probe-verified (1075: degree-level mean-node anchor) | probe | **0** | — |
| `bg_panchanga` | (service) | — | — | probe-verified against FORENSIC anchors | probe | 1 | — |
| `bg_gochara_arcs` | bg_gochara_arcs | ~33,933 | 16 | engine_version, substrate_version | ✓ | **0** | 7 / 1 |
| `bg_sky_calendar` | bg_sky_calendar | ~31,059 | 17 | source_citation | ✓ | 1 | 6 / 3 |
| `bg_muhurta_lattice` | bg_muhurta_lattice | ~172,330 | 16 | source_citation | ✓ | **0** | 3 / 11 |
| `bg_transit_rules` | bg_transit_rules | 76 | 8 | classical_citation | ✓ (1078 reseal at 75+1) | 6 | 26 / 9 |
| `bg_transit_engine` | bg_transit_engine | 9 | 6 | classical_citation | ✓ | **0** | 4 / 4 |
| `bg_vedha_malefic_scale` | bg_vedha_malefic_scale | 5 | 7 | source_citation, table_version | ✓ (1077 reseal) | 1 | 6 / 2 |
| `bg_phaladeepika_latta` | bg_phaladeepika_latta | 8 | 9 | source_citation, table_version | ✓ | 1 | 4 / 2 |
| `bg_sarvatobhadra_grid` | bg_sarvatobhadra_grid | **0** | 10 | school_tag, source_citation, source_text_id, table_version | none (empty by adjudication) | 1 | 3 / 4 |
| `bg_kota_chakra_rings` | bg_kota_chakra_rings | 27 | 9 | citation, table_version | ✓ | 1 | 6 / 1 |
| `bg_gochara_citation_resolution` | bg_gochara_citation_resolution | 14 | 9 | chunk_id, text_id, source_citation, citation_string | ✓ | **0** | **0** / 4 |
| `bg_prashna_rules` | five `bg_prashna_*` tables | (five) | — | not probed | ✓ | 1 | not probed |
| `bg_vastu_directions` | bg_vastu_directions | 8 | 8 | classical_citation | ✓ | **0** | 3 / 5 |
| `bg_medical_mappings` | bg_medical_mappings | 21 | 8 | classical_citation | ✓ | **0** | 5 / 5 |
| `bg_nakshatra_medical` | bg_nakshatra_medical | 27 | 6 | classical_citation | ✓ | **0** | 5 / 4 |
| `bg_sign_medical` | bg_sign_medical | 12 | 7 | classical_citation | ✓ | **0** | 2 / 6 |
| `bg_vidhi_primitives` | vidhi_primitives | 60 | 11 | version | ✓ | **0** | 1 / 3 |
| `bg_vidhi_floors` | vidhi_floor_items | 409 | 7 | **none** | ✓ | **0** | 1 / 3 |

**Registry defects, measured:** `bg_prashna_rules.target_table` NULL while `storage_type =
postgres_table` (it is five tables); `bg_vidhi_floors` is `DRAFT` — the only non-CURRENT of 40, while
its dependency is CURRENT; `sort_order` collides at 68 (`bg_formula_constants`, `bg_vidhi_primitives`)
and 69 (`bg_sky_calendar`, `bg_vidhi_floors`); duplicate `@register` decorations for `bg_reference`
(in `__init__.py`) and `bg_gochara_arcs` (twice in its own file) — last-registration-wins behaviour
unverified; the legacy `reference_nakshatras` table (closure §7 deferred drop, three steps) is **still
present** in production. Two shared-table pairs are partitions, not duplicates: `bg_class_priors` /
`bg_class_lifetime_counts` partition `brahma_class_priors` by `prior_version`; `bg_texts` /
`bg_text_index` share `classical_text_chunks`, the second being an enrichment (embedding + topic_tag)
of the first's rows.

**Current code vs deployed:** for L0 they coincide. The L0 repair (PR #2727, migrations 1075–1079)
is on `origin/main` and applied to production; no L0 migration is pending on any live head. This is
the only layer for which that is true today.

### 1.2 · Individual contribution — ablate one

```
inherits:    Product §14.1; Data plane §12.2
measured_by: NOT RUN — no L0 ablation harness exists. Proxy recorded instead: reachability (served files / consuming writer files, §1.1) and the six-state position (§1.4). An asset's individual term is UNMEASURED until a served-reading ablation is run against the ref_* surface.
traces_to:   0.1
```

What the proxy says, honestly labelled as proxy:

- **Every one of the 40 is read by something.** No asset is ≈ 0 on reachability. The template's
  "≈ 0 on all three terms → R/H candidate" test yields **no candidates** from reachability alone.
- **Two assets have no served path:** `bg_reference` (`reference_planets`, 4 writer readers, 0
  serving) and `bg_cohort` (`bg_synthetic_cohort`, 3 writer readers, 0 serving). The first is a
  genuine gap — the graha reference table is not exposed through any `ref_*` capability, so P16's
  "give me this exact fact" cannot reach it; candidate **I**. The second is engineering capital by
  design (synthetic population); **H**, as v1.0 already held.
- **One asset has no writer path and only a served one:** `bg_gochara_citation_resolution` (0 writer
  readers, 4 serving). It is a resolver consumed at serve time; static by disposition. Not a defect.
- **The highest-reach assets are the invisible ones:** `brahma_event_ontology` (52 reading files),
  `classical_text_chunks` (40), `ephemeris_daily` (42), `bg_transit_rules` (35), `brahma_ontology`
  (18). Their individual term, once ablated, will be the largest in the layer — and four of the five
  have 0–6 *registered* consumers.

### 1.3 · Synergistic contribution — ablate the group

```
inherits:    Data plane §3.4, §4.1 ("one authority, many representations"), §7
measured_by: identity-join integrity across L0's own tables (exact count(*), 2026-09-25); declared-edge coverage (registry vs code reads); served-surface contract coverage (density_contract grep)
traces_to:   0.2
```

L0's synergy is the question *is the shared vocabulary actually shared?* Three seams measured:

**Seam 1 — catalog identity → ontology: SHARED.**

| join | rows | orphans |
|---|---|---|
| `brahma_yoga_catalog.canonical_id` → `brahma_ontology` | 237 | **0** |
| `brahma_dosha_catalog.canonical_id` → `brahma_ontology` | 84 | **0** |
| `brahma_dasha_systems.canonical_id` → `brahma_ontology` | 22 | **0** |
| `bg_parihara_rules.dosha_canonical_id` → `brahma_dosha_catalog` | 60 | **0** |

The yoga/doṣa/daśā/parihāra family speaks one identity. This is real synergy and it is complete.

**Seam 2 — rules → concepts: NOT LINKED.** `sutravali_rules` has 3,002 rules, **3,002** with a
`text_id` (source-linked, 14 distinct texts) and **17** with a `yoga_canonical_id` (concept-linked).
The rule corpus is anchored to *passages*, not to the *concepts* the catalogs define. Data plane §4.3
asks for "a usable rule graph, not just more text"; measured, it is text. A reasoning layer can cite
a rule's passage but cannot, from the rule row, reach the yoga it qualifies — the link exists for
0.6 % of rules.

**Seam 3 — remedies → identity: TWO MEANINGS OF ONE COLUMN.** `brahma_remedy_corpus.source_canonical_id`
has 345 non-null values of which **289 do not resolve to `brahma_ontology`**. They resolve to nothing
there because they are *source-work names* — `BPHS` (193), `classical_tradition` (80),
`Phaladeepika` (11), `Tajaka` (3) — not entity identities. The column is named as if it were the
entity vocabulary and holds the source vocabulary. Whether those names resolve to a texts registry is
**not measured**. The finding stands regardless: `canonical_id` carries two identity spaces across
L0's tables, which is the exact "local representations diverge in meaning" DP01 forbids.

**Seam 4 — declared dependency: LARGELY UNDECLARED.** 19 of 40 assets have ≥1 registered downstream
consumer; 40 of 40 are read. The orchestrator's staleness propagation runs on the declared graph.

**Seam 5 — served surface contract: ABSENT.** 49 capability files under
`platform/src/lib/retrieval/registry/layers/L0_brahmagyan`; **0** declare a `density_contract`
(§N.6). The `bg_muhurta_lattice` capability's `FACTOR_FAMILIES` allowlist covers 4 of 9 families the
writer produces — ~72,580 of ~165K rows unreachable by explicit filter (W2 MUST-1, still open).

**The synergistic term as a fraction:** not computable without ablation, and this instance will not
invent one. Recorded as measured: one seam complete (catalog identity), one mismatched (remedy
identity), one absent (rule→concept), one mostly undeclared (dependencies), one unspecified (served
contract). L0 *has* a department at its catalog core and is a collection of tables everywhere else.

### 1.4 · Cross-layer handoff — what it produces for downstream

```
inherits:    Data plane §11 (six evidence states), §7 (DP01, DP02, DP07, DP13-L0)
measured_by: code reads at the consumer (grep, §1.1) for "consumed"; capability files for "served"; NOT verified: "traceably transformed" (would require reading each consumer's transformation) and "value evaluated" (no ablation)
traces_to:   0.3
```

This is L0's dominant term. Per produced contract, its evidence-state position verified at the
consumer:

| contract | source present | qualified | consumed (at consumer) | traceably transformed | served | value evaluated |
|---|---|---|---|---|---|---|
| DP01 identity (`bg_ontology`, `bg_reference`, `bg_nakshatra`) | ✓ | ✓ for catalogs (seam 1); ✗ for remedies (seam 3) | ✓ 24 writer files | not verified | ✓ `list_entities`, `resolve_entity` | not run |
| DP02 rule qualification (rules, yogas, doṣas, daśās, transit rules, parihāra) | ✓ | **partial** — catalogs carry `school` + `source_chunk_ids`; `sutravali_rules` carries text but 0.6 % concept links; `bg_transit_rules` provenance is per-row not table-wide (migration 1079 corrected the registry description that claimed otherwise) | ✓ 59 writer files across the six | not verified | ✓ `query_yoga_catalog`, `query_dosha_catalog`, `query_dasha_systems`, `query_transit_engine`, `sutravali_tools` | not run |
| DP07 sampled clocks (`bg_ephemeris`, `bg_gochara_arcs`, `bg_sky_calendar`) | ✓ | ✓ node frame + epoch declared on the row (1076); probe degree-anchored (1075) | ✓ 41 writer files | not verified | ✓ `ephemeris_cache_*`, `query_planet_position`, `query_sky_calendar` | not run |
| DP13 event vocabulary (`bg_ghatana`) | ✓ | ✓ citations + version | ✓ 31 writer files, incl. L4/L5 | not verified | ✓ 21 serving files | not run |
| constants (`bg_formula_constants`) | ✓ | ✓ citation_or_ratification + version | ✓ 8 writer files | not verified | ✓ `query_formula_constants` | not run |

**What this term says about L0's value:** it is consumed everywhere and evaluated nowhere. Every
contract reaches "served"; none reaches "value evaluated", because no consumer's reading has ever been
ablated against an L0 change. The instrument to close that gap does not exist and is named in §4.2.

### 1.5 · The accounting

```
inherits:    —
measured_by: 1.2 (proxy) + 1.3 (seams) + 1.4 (states) against 0.2
traces_to:   0.2
```

> **L0 value = Σ individual + Σ synergistic + Σ cross-layer handoff**

- **Individual:** unmeasured (no harness). Reachability proxy: 40/40 reached; 2 without a served path.
- **Synergistic:** real at the catalog-identity core; absent at rules→concepts; mismatched at
  remedies; undeclared for dependencies; unspecified for serving.
- **Cross-layer handoff:** the dominant term — five contracts consumed by 59+ writer files across
  L1–L5, none evaluated.

**Against the objective (0.2):** L0's job is to make the depth *legible* — one identity, a qualified
source behind every rule, a declared convention behind every number. Measured: identity is one
(seam 1) except where a column reuses the word for a different space (seam 3); sources sit behind
rules at the *passage* level and not at the *concept* level (seam 2); conventions are declared on the
substrate since the repair. **The elevation delta is therefore not "build more L0." It is: link the
rules to the concepts they qualify; separate the two identity spaces; declare the dependencies that
exist; put a contract on the served surface; and build the one instrument — ablation against the
`ref_*` surface — that would let the individual term be measured at all.** Part 3 itemises it.

**R/H candidates by the accounting:** none at ≈ 0 on all terms. **I candidates:** `bg_reference`
(unserved), `bg_rules` (unlinked). **H confirmed:** `bg_cohort`, `bg_vastu_directions`,
`bg_medical_mappings` family (research/testimony capital, served as attributed testimony only).
**C candidates:** none — the two shared-table pairs are partition patterns, verified by their
`count_sql`.

---

## Part 2 · CONDITIONS UNDER WHICH THE VALUE IS REAL

### 2.1 · Correctness rules

```
inherits:    Product §8.1 L0 row, §13; Data plane §9.2
measured_by: integrity_check_sql presence (37/40) · probe events (2 services) · empty_accepted (1) · NOT checked: absence of subject/chart columns on bg_* tables
traces_to:   0.2
```

| rule | inherited from | detector | state |
|---|---|---|---|
| *Private observations must not become global doctrine or reference truth* | Product §8.1 L0 row, verbatim | should be: no `bg_*` table carries a `chart_id`/`subject_id` column and no L0 writer reads a subject table | **not measured** — named as the first check in W-L0-1 |
| L0 is switch-independent — it holds no life-event data, so ON/OFF changes nothing it emits | Data plane §9.2 | same detector as above | not measured |
| No invented computation, source, detector, confidence or score | Product §13 first boundary | `integrity_check_sql` on 37 of 40 assets; the three without are `bg_ephemeris_engine` and `bg_panchanga` (services: `probe_accepted` on the ledger) and `bg_sarvatobhadra_grid` (0 rows, `empty_accepted`) — all three honest exceptions | ✓ measured |
| A registry description must not assert a provenance the table does not have | migration 1079's finding | none standing — 1079 was a one-off correction; the description-vs-table check has no detector | **gap** |
| Source count is not probability | DP §3.1 must-not-claim | `bg_concordance` was reworked from "abundance as agreement" to passage/rule ancestry (v1.0 §5); detector: none | **gap** |

### 2.2 · Presentation obligation

```
inherits:    Product §2 (two modes, one depth); Data plane §3.4
measured_by: provenance-column probe (§1.1); presentation-parity test NOT RUN
traces_to:   0.1 — the acharya rows of P15/P09/P13 are unservable without these
```

For the acharya rendering, L0 must **carry** — not merely know — per rule and per reference row:
the **school/tradition**, the **source witness** (text, chapter, passage), the **convention in force**,
the **aliases** in script and transliteration, and the **unresolved alternatives**. Measured presence:

- **Carried fully:** `brahma_yoga_catalog`, `brahma_dosha_catalog`, `brahma_dasha_systems` (`school`,
  `classical_citations`, `source_chunk_ids`); `classical_text_chunks` (`tradition_school`,
  `translation_provenance`, edition context); `classical_attributions` (`school`, `source_text_ids`);
  `bg_dignity_reference` (`variant_traditions`); `bg_sarvatobhadra_grid` (`school_tag`, though empty).
- **Carried partially:** `sutravali_rules` (text and verse, **no school**); `bg_transit_rules`
  (`classical_citation` only, **no school**, provenance per-row); `bg_parihara_rules` (source text and
  chapter, no school); `brahma_event_ontology` (citations, version, no school — arguably not a
  school-bearing object).
- **Not carried:** `vidhi_floor_items` (**no provenance column at all**); `vidhi_primitives` (version
  only); `bg_gochara_arcs` (engine/substrate version only — computed, so a *convention* declaration is
  what is owed, and `substrate_version` partly supplies it).

Acceptance test (presentation parity, DP §12.2): not run for L0. What it would test: a `ref_yogas_get`
answer rendered for the acharya exposes school, citations and source chunks that the layperson
rendering carries but does not show.

### 2.3 · Contracts produced and consumed

```
inherits:    Data plane §7, §7.1
measured_by: §1.4 per contract; declared use — NOT recorded anywhere for L0 consumers (no consumer declares calculation/applicability/counter-evidence/…)
traces_to:   0.3
```

**Produced:** DP01, DP02, DP07 (sampled), DP13-vocabulary, constants — as §0.3 and §1.4.

**Consumed:** none from inside the plane. External inputs, which L0 must *declare* as if they were
contracts: the classical text editions and rights (`bg_texts`); the Swiss ephemeris backend and file
set (`bg_ephemeris_engine` — an earlier session found the `.se1` resolver returning None with
calculations proceeding; **not re-verified here**, carried as an open check); the seeded reference
doctrine and who ratified each constant (`citation_or_ratification`).

**Declared use:** the data plane's rule is *a citation with no declared use is not a contract*. No
L0 consumer declares its use type. Every one of the 59+ reading writer files consumes L0 without
saying whether the input is calculation, applicability, counter-evidence or navigation. This is a
consumer-side obligation, but the producer-side half — a per-contract field list and grain
(§7.1's envelope) — is also absent for L0. Both halves go to W-L0-2.

### 2.4 · Jyotish coverage owned

```
inherits:    Product §3; Data plane §5 ("L0 meaning →" column of every row)
measured_by: presence of the owning asset and its qualification state (§1.1, §1.3)
traces_to:   0.1
```

L0 owns the *meaning* half of every coverage obligation. State per obligation, using the five states:

| obligation (DP §5) | L0 owner | state |
|---|---|---|
| Graha contextual roles | `bg_ontology`, `bg_reference` | **applied** — identity complete; role vocabulary on `reference_planets` |
| Rāśi/bhāva/lord/kāraka | `bg_ontology`, `bg_reference` | applied |
| Bala/dignity/avasthā | `bg_dignity_reference` (variants), `bg_formula_constants` | applied — variants named, not unified |
| Sambandha (typed relations) | rule vocabulary in `bg_rules` | **unqualified** — relations are typed in L2 code, not in an L0 vocabulary table |
| Bhāvat Bhāvam | no L0 owner | **unavailable** — no rule scope object exists; v1.0's L0-Q05 stands unanswered |
| Varga and reference perspectives | `bg_formula_constants` (construction), `bg_kp_sublord_division` | applied for KP; varga construction conventions **not carried as data** — they live in L1 code |
| Yoga/doṣa/bhaṅga | `bg_yogas`, `bg_doshas`, `bg_rules` | applied for catalogs; **unqualified** for rules (seam 2) |
| Nakshatra/KP | `bg_nakshatra`, `bg_kp_sublord_division` | applied |
| Kāla methods | `bg_dasha_systems`, `bg_transit_rules`, `bg_vedha_malefic_scale`, `bg_phaladeepika_latta`, `bg_kota_chakra_rings`, `bg_sarvatobhadra_grid` | applied except `bg_sarvatobhadra_grid` — **unresolved** (ADJUDICATION-11 school ruling) |
| Praśna/Muhūrta/calendar | `bg_prashna_rules`, `bg_muhurta_lattice`, `bg_panchanga`, `bg_sky_calendar` | applied as data; Praśna *facility* dormant — native decision open |
| Āyurdāya and constitution | `bg_dasha_systems`, `bg_formula_constants` (method); medical mappings (constitution testimony) | applied as method; computation is L1 |
| Practices and wider tradition | `bg_remedies`, `bg_parihara_rules` | applied; identity space mismatched (seam 3) |

### 2.5 · Edges and order

```
inherits:    Data plane §3.2; live registry depends_on
measured_by: topological sort of live depends_on (acyclic, verified by inspection of the 40 rows); egate scoped to t3
traces_to:   0.3
```

**Intra-L0 order** (live `depends_on`): roots — `bg_ontology`, `bg_texts`, `bg_ephemeris`,
`bg_ephemeris_engine`, `bg_nakshatra`, `bg_ghatana`, `bg_formula_constants`, and the standalone
reference tables → `bg_reference`, `bg_yogas`, `bg_doshas`, `bg_dasha_systems` (on ontology + texts)
→ `bg_text_index`, `bg_compendium_index` (on reference + texts) → `bg_rules` (on dasha_systems,
texts, yogas) → `bg_concordance` (on reference, rules, text_index, texts) → `bg_parihara_rules` (on
doshas, texts); `bg_kp_sublord_division` (on nakshatra); `bg_gochara_arcs` (on ephemeris); `bg_cohort`
(on ephemeris_engine); `bg_class_lifetime_counts` (on ghatana); `bg_vidhi_floors` (on primitives);
`bg_gochara_citation_resolution` (on texts). No cycle.

**Cross-layer gate:** under the frozen definition **t3**, L0 is 0/40 frozen, so `egate.sql` reports
every L1–L5 asset `BLOCKED-ANCESTORS` on L0. The native ruled (S-4, 2026-09-24) that L0/L1/L2 are
*assumed* elevated for L3 gating. This instance is the beginning of converting that assumption into a
per-criterion certification (§5.3); until then, every downstream result inherits it.

---

## Part 3 · THE DELTA

```
inherits:    —
measured_by: §1.5's shortfall, itemised
traces_to:   0.2
```

### 3.1 · Per obligation

| obligation (Product §14) | where L0 stands, measured | what closes the gap |
|---|---|---|
| **Source and domain fidelity** (primary) | Catalog identity complete. Rules text-anchored, 0.6 % concept-linked. Remedy identity space mismatched. `bg_transit_rules` provenance per-row, registry description corrected (1079) but no standing detector. `bg_sarvatobhadra_grid` empty pending ruling. | Rule→concept linkage (W-L0-3); identity-space separation (W-L0-3); a description-vs-table detector (W-L0-5); the school ruling (W-L0-6). |
| **Computational correctness** (substrate) | Node frame and epoch declared on `ephemeris_daily` (1076); engine probe degree-anchored (1075); `.se1` file-presence finding from another session not re-verified. | Re-verify the ephemeris file resolver in production (W-L0-1); nothing else measured as wrong. |
| **Concept and relationship completeness** | No L0 object for sambandha typing or Bhāvat Bhāvam scope; varga construction conventions live in L1 code, not L0 data. | Decide whether these are L0 data or remain L1/L2 code — a native/strategy call, recorded in §4.2 as W-L0-6, not assumed. |
| **Delivery fidelity** (served surface) | 49 capability files, 0 `density_contract`; `bg_muhurta_lattice` allowlist 4/9 families; `bg_reference` unserved. | `density_contract` on all 49; allowlist 9/9; a `ref_` capability for graha reference (W-L0-4). |
| **Operational honesty** | Three disagreeing `bg_class_priors` counts (171/165/164 vs live 177); `bg_vidhi_floors` DRAFT; `bg_prashna_rules` NULL target; sort_order collisions; duplicate `@register`; legacy table not dropped; seed disagrees with registry in five places. | Registry truth pass (W-L0-1). |

### 3.2 · Per asset — disposition

v1.0's per-asset table is carried; where measurement changed a disposition, the change and its
evidence are shown. Unchanged rows keep v1.0's `P/I/E/Q` and are not re-argued.

| asset | disposition | measured basis for any change from v1.0 |
|---|---|---|
| `bg_ontology` | **P/I/E** | seam 1 clean; **I**: declare its 18 actual readers as dependencies; **E**: reconcile the second identity space (seam 3) *into* it or *away* from it — a decision, §4.2 |
| `bg_reference` | **P/I** | **I** added: 0 served files — expose through a `ref_` capability |
| `bg_texts` / `bg_text_index` | P/I | declare the shared-table partition explicitly; v1.0 unchanged otherwise |
| `bg_rules` | **P/E** | **E** sharpened: 17/3,002 concept links; plan the linkage, do not fabricate it |
| `bg_yogas`, `bg_doshas`, `bg_dasha_systems` | P/I/Q | seam 1 clean — v1.0 stands |
| `bg_remedies` | **P/E/Q** | **E**: `source_canonical_id` is a source-work column; rename or re-key so `canonical_id` means one thing |
| `bg_concordance`, `bg_compendium_index` | P/I/Q | v1.0 stands; 0 registered consumers, 4–6 served — declare |
| `bg_transit_rules` | **P/Q** | **Q** sharpened per 1079: provenance is per-row; the description now says so; keep it true with a detector |
| `bg_transit_engine` | P (producer_covered) | v1.0 stands |
| `bg_ghatana` | P/I | highest reach in the layer (52 files); **I**: its 5 registered consumers understate 31 |
| `bg_ephemeris`, `bg_ephemeris_engine`, `bg_gochara_arcs`, `bg_sky_calendar` | P/Q | conventions now declared (1075/1076); re-verify file resolver |
| `bg_muhurta_lattice` | **P/I** | **I**: 4/9 factor families reachable (W2 MUST-1, open) |
| `bg_class_priors` / `bg_class_lifetime_counts` | **P/E** | **E**: reconcile 171/165/164 against live 177; declare the partition |
| `bg_vidhi_floors` | **Q** | status decision (DRAFT accurate or stale) — native, W2 §3 |
| `bg_vidhi_primitives` | P/E | **E**: no provenance beyond `version` |
| `bg_sarvatobhadra_grid` | **U/H** | 0 rows by adjudication; **U** until the school ruling; consumer plumbing already wired |
| `bg_prashna_rules` | **P/Q** | data complete; facility dormant — native decision; registry target NULL must be made honest (five tables or a declared multi-table set) |
| `bg_cohort` | **H** | synthetic engineering population; 0 served; keep restricted |
| `bg_vastu_directions`, `bg_medical_mappings`, `bg_nakshatra_medical`, `bg_sign_medical` | **P/H** | attributed testimony, served as such; under FINAL these are *in scope as testimony*, no longer excluded — v1.0's "restricted" reads as "attributed" now |
| `bg_gochara_citation_resolution` | **H** (static) | v1.0 stands |
| `bg_kota_chakra_rings`, `bg_vedha_malefic_scale`, `bg_phaladeepika_latta`, `bg_kp_sublord_division`, `bg_dignity_reference`, `bg_nakshatra`, `bg_formula_constants`, `bg_panchanga`, `bg_parihara_rules` | P/I/Q | v1.0 stands; no measurement moved them |
| legacy `reference_nakshatras` | **R** | closure §7 deferred drop (three steps) never executed; table still present |

### 3.3 · Per asset — what it must add

Compact; the asset brief's "exact delta" inherits from here.

- `bg_ontology`: declared consumers; a decision on the second identity space.
- `bg_reference`: a served capability; declared consumers.
- `bg_rules`: a concept link (`yoga_canonical_id` / `dasha_system_id` / a doṣa key) on every rule
  that qualifies a catalogued concept, or an explicit `unlinked_reason`; a `school` column.
- `bg_remedies`: `source_canonical_id` renamed to what it is (`source_work_id`) or re-keyed to the
  entity space; the unresolved 289 characterised, not forced.
- `bg_transit_rules`, `bg_parihara_rules`: `school`.
- `vidhi_floor_items`: a provenance column set; `vidhi_primitives`: more than `version`.
- `bg_muhurta_lattice`: allowlist 9/9 and a truthful capability description.
- `bg_class_priors`: one count, three places agreeing.
- All 49 served capabilities: `density_contract`.
- All 40: declared use recorded by each consumer (consumer-side); per-contract field/grain envelope
  (producer-side).

### 3.4 · Intra-layer interplay

Declared vs actual, the seam that decides whether L0 is a department:

| declared edges (live registry) | actual reads (code) |
|---|---|
| 19 assets with ≥1 registered consumer; 21 with none | 40 with ≥1 reader; median 5 writer files + 4 serving files per table |
| `bg_ontology` → 0 | `brahma_ontology` ← 18 files, incl. `resolve_entity`, `list_entities`, `l0_brahmagyan`, `parity_check` |
| `bg_texts` → 0 | `classical_text_chunks` ← 40 files |
| `bg_ghatana` → 5 | `brahma_event_ontology` ← 52 files, incl. L4 intervention filing and L5 ledgers |

Within L0 itself the interplay is real where the catalogs meet the ontology (seam 1) and absent where
the rules should meet the catalogs (seam 2). The remedy corpus stands beside the ontology using the
same word for a different thing (seam 3).

---

## Part 4 · STRATEGY

### 4.1 · Order

```
inherits:    2.5
measured_by: the live DAG; three-way baseline (deployed = current code for L0, see §1.1)
traces_to:   0.2
```

Within L0, dependency order is loose — most assets are roots. So order is chosen for **learning
value and blast radius**, in this sequence:

1. **`bg_ontology`** first — it is the identity authority, everything hangs on it, it has 0 declared
   consumers and 18 real ones, and the seam-3 decision (one identity space or two) is made here. If
   the template cannot express L0's central asset honestly, that is found at asset 1.
2. **`bg_rules` with `bg_yogas`/`bg_doshas`/`bg_dasha_systems`** — the rule→concept linkage is the
   largest fidelity gap and the one the reasoning layer will feel first.
3. **`bg_remedies`** — the identity-space fix, small and decisive.
4. **The served surface as one packet** — `density_contract` × 49, the lattice allowlist, the
   `bg_reference` capability. Not per-asset; one sweep, as the L3 column-gap lesson showed.
5. **The substrate** (`bg_ephemeris`, engine, arcs, sky calendar) — verify, do not change; the repair
   already landed.
6. **Registry truth** runs *before* all of the above as W-L0-1 — it is cheap and everything else reads
   from what it fixes.

**Three-way baseline:** deployed == current code (all L0 migrations on `main` and applied). Target =
Part 3. The risk term (current code − deployed) is **zero** for L0 today — record it, because it
will not stay so.

### 4.2 · Work packets

```
inherits:    Data plane §13.1, §13.3 item 8
measured_by: each packet's proof, named
traces_to:   3.x — each closes named delta items
```

| packet | closes | proof (a detector that fails when not landed) |
|---|---|---|
| **W-L0-1 Registry truth** | 3.1 operational honesty: `bg_prashna_rules` target; sort_order 68/69; `bg_vidhi_floors` status *decision recorded*; `bg_class_priors` one count; duplicate `@register`; seed reconciled to live; legacy `reference_nakshatras` dropped; the "no subject column on any bg_ table" check run; the `.se1` resolver re-verified | a registry-parity test for L0 (the L3 parity test extended to `bg_*`); `to_regclass('reference_nakshatras') IS NULL` |
| **W-L0-2 Declared dependencies and declared use** | seam 4; 2.3 both halves | every code read of a `bg_*` table is either a registered `depends_on` edge or a documented serve-time read with a declared use type; detector: the reader grep in §1.1 re-run yields no undeclared writer-side reads |
| **W-L0-3 One identity, linked rules** | seam 2, seam 3; 3.2 for `bg_ontology`, `bg_rules`, `bg_remedies` | `source_canonical_id` no longer joined against `brahma_ontology` by name (renamed or re-keyed); rule→concept coverage reported as a number with an `unlinked_reason` on the remainder — the 0.6 % becomes a measured figure with a stated ceiling, not a target |
| **W-L0-4 Served-surface contract** | seam 5; 3.1 delivery fidelity | `density_contract` present on 49/49 (grep = 49); lattice allowlist 9/9 with a test that fails on 8; `ref_graha_reference_get` (or equivalent) exists and is exercised |
| **W-L0-5 Provenance completion and truthfulness** | 2.2 partial/absent rows; 2.1 description-vs-table gap | `school` on `sutravali_rules`, `bg_transit_rules`, `bg_parihara_rules`; provenance columns on `vidhi_floor_items`; a standing check that a registry `english_description` provenance claim is supported by the table (the 1079 defect class, generalised) |
| **W-L0-6 Native rulings** | `bg_sarvatobhadra_grid` school; `bg_prashna_rules` facility; `bg_vidhi_floors` status; whether sambandha typing / Bhāvat Bhāvam scope / varga construction become L0 data or stay L1/L2 code; whether the remedy identity space merges into the ontology or stays a separate, honestly-named source registry | rulings recorded in `KALA_DELEGATED_DECISIONS` or its L0 equivalent; each packet above that depends on one names it |
| **W-L0-7 The instrument** | 1.2, 1.4 "value evaluated" | an L0 ablation harness: run a fixed set of `ref_*` and L1–L3 readings with and without a named `bg_*` table (or with it emptied in a disposable DB), diff the readings, score against the ten obligations. Detector: the harness exists, runs in CI on a disposable snapshot, and produces a non-empty delta for at least `bg_ontology` |

W-L0-7 is the packet without which §1.2 stays a proxy forever. It is named last because it depends
on W-L0-1 (a registry it can trust) and W-L0-2 (dependencies it can follow), not because it matters
least.

### 4.3 · Generation, invalidation, rollback

```
inherits:    Data plane §4.4, §11, DP16
measured_by: the declared graph (seam 4) — which is the invalidation path; NOT exercised
traces_to:   2.1
```

L0 revisions are classified per DP §4.4 (alias correction · identity mapping · semantic rule change ·
constant/method change · provenance/rights correction · qualification change). Today the
invalidation path is the declared `depends_on` graph — and seam 4 shows it reaches a fraction of the
real consumers. **A semantic change to `bg_ontology` today stales nothing.** Until W-L0-2 lands,
L0's invalidation is by convention, not by mechanism. Rollback for the static tables is a governed
rebuild against the `integrity_check_sql` reseal pattern (1077/1078 are the worked examples); the
services roll back by engine pin (`substrate_version`, the 1075 probe).

### 4.4 · What each asset brief inherits

```
inherits:    Product §16; Data plane §13.3
measured_by: derivability — §5.4 item 1
traces_to:   0.1
```

Every `bg_*` asset brief takes from this instance, without re-deriving: its P/V rows from 0.1
(narrowed to the asset); its obligations from 0.2 (source and domain fidelity for all; computational
correctness for the substrate five; delivery fidelity if it has a served capability); its correctness
rules from 2.1; its presentation fields from 2.2 (which of school / witness / convention / alias /
alternatives it must carry); its produced contract and its actual readers from 1.1 and 1.4; its
coverage state from 2.4; its disposition and must-add list from 3.2 and 3.3; its position in 4.1;
its three-way baseline (deployed == current, for now); its measured terms from 1.2–1.4 with the honest
"NOT RUN" on ablation; and its role — L0 assets have no manifestation or temporal role of their own;
they *define* the vocabulary those roles are expressed in.

A brief that must invent any of these has found a defect in this instance.

---

## Part 5 · EVALUATION AND CERTIFICATION

### 5.1 · The score is ablation, in three flavours

```
inherits:    Product §14, §14.1; Data plane §12.2
measured_by: W-L0-7 (does not exist yet)
traces_to:   0.2
```

L0 scores on **source and domain fidelity** (all 40), **computational correctness** (the five
substrate assets), **delivery fidelity** (the served surface), **operational honesty** (registry and
description truthfulness). The three flavours for L0: *individual* — a `ref_*` reading and an L1–L3
reading with the table present vs emptied; *synergistic* — the same readings with the ontology joins
severed (seam 1 broken deliberately) to measure what shared identity is worth; *cross-layer* — an L2
mechanism reading with `bg_rules`/`bg_yogas` absent, measured at the L2 consumer. None has been run.

### 5.2 · The per-asset checklist

```
inherits:    kala_brief_tracker.py TIERS; template §5.2
measured_by: the tracker — which today lists only the 22 L3 assets; extending its ASSETS table to bg_* is part of W-L0-1
traces_to:   4.4
```

The 31 criteria apply unchanged. Two are structurally different for L0 and the template should say
so (§6): **T1-E consumers** is measured by code reads, not by served readings, for a root layer; and
**T5's campaign ladder** position is `ANALYZED` for all 40 (W1 analyses exist) with `FROZEN` only
under a superseded revision — which under §5.3 is *not frozen*.

### 5.3 · Certification is per criterion

```
inherits:    template §5.3
measured_by: the certification record — none exists yet under criterion_version
traces_to:   —
```

The 40 `asset_frozen` events under t0 are per-definition certifications and were invalidated by the
t3 re-freeze. No per-criterion record exists. The first records to write, for `bg_ontology`:
`source_and_domain_fidelity/seam1` — evidence: the four joins in §1.3, verdict PASS;
`operational_honesty/declared_consumers` — evidence: registry 0 vs code 18, verdict FAIL. A revision
to either criterion re-opens that record only.

### 5.4 · Acceptance of this instance

1. **Derivability test — pending.** A fresh-context reader is to derive the `bg_ontology` brief from
   this instance plus tiers 1–2 and report every invention.
2. **Alignment test — applied by the author.** Every section names `traces_to:`; nothing was carried
   from v1.0 that could not.
3. **Measured, not inherited — applied.** Every figure names its instrument; four things are
   explicitly NOT measured (frontmatter) rather than estimated.
4. **Presentation parity — not run.**
5. **Independent review — pending.** Status is `DRAFT_FOR_INDEPENDENT_REVIEW`; v1.0 remains the
   authoritative L0 strategy until this passes.

---

## §6 · What this instance found in the template

Recorded here for repair in `LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md`, not worked around:

1. **The "pin" source does not exist for L0.** §0.3 demands seed / registry / pin reconciliation; the
   migration-governed pin is an L3 instrument. The template should say: *state the three sources; if
   one does not exist for this layer, say so — its absence is a finding.*
2. **A root layer consumes nothing internal.** §2.3 "contracts consumed" needs a line for *external
   inputs declared as contracts* (editions, engine files, ratifications); this instance improvised it.
3. **§1.2's ablation cannot be a proxy silently.** The template allows "unmeasurable — not reached";
   it should also allow *"harness does not exist — proxy recorded, harness is a packet"*, which is
   L0's case and will be L1's.
4. **T1-E "consumers" and T5 "campaign ladder" mean something different at a root layer** (§5.2).
5. **The "synergistic term as a fraction" instruction cannot be honestly met without ablation.** The
   template should accept a seam-by-seam measurement as the recorded value until a harness exists,
   rather than invite a number.
