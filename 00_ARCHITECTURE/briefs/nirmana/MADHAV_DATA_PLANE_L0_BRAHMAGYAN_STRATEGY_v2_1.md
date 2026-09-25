---
artifact: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY
canonical_id: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY
tier: 3
kind: instance
chain: ELEVATION_DERIVATION_CHAIN_v1_0.md
produces: ["40 bg_* asset instances — via §4.4, which ASSET_ELEVATION_TEMPLATE §0.1 receives row for row"]
version: "2.1"
status: ACCEPT_WITH_CORRECTIONS
review_record: 00_ARCHITECTURE/briefs/reviews/REVIEW_L0_STRATEGY_v2_0.md  # verdict REJECT on v2.0; 2 BLOCKER + 12 MAJOR + 7 MINOR, all folded into v2.1
verdict_basis: >
  Under the template's three-verdict scale, the review's findings split in two. The DOCUMENT-level
  findings — nine figures that did not reproduce, three obligation sets where there should be one,
  fourteen assets untraced in Part 0, six checklist criteria with no feeding section — are defects in
  this instance and are FIXED here, not deferred: a wrong number does not become right by being built
  on. The LAYER-level findings this document correctly records — 11 duplicate canonical ids, 79 doṣas
  without aliases, 3,002 rules without executable scope — are not defects in the instance at all;
  they are the instance doing its job, and each is a packet with a detector. Corrections outstanding
  and their gates are listed in §7.
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
vocabulary_measured_on: 2026-09-25  # §2.6 added after the data plane's controlled-vocabulary principle was elevated in place
not_measured: "consumer-perturbation deltas (the cross-layer harness, W-L0-7, does not exist — ablation is NOT L0's individual measure, see §1.2); presentation-parity test (not run); whether any bg_* table carries a subject/chart column (not checked); whether brahma_remedy_corpus.source_canonical_id values resolve to a texts registry (not checked)"
---

# L0 Brahmagyan — definition, strategy and evaluation (template instance 1)

**v2.1 folds every finding of the independent review of v2.0.** Nine figures in v2.0 did not reproduce
when re-run at source; all nine are corrected below and the corrections are visible, not silent. Two
blockers — a seed-vs-registry disagreement that was an extraction artefact, and eleven duplicate
canonical ids that v2.0 printed in its own join counts and did not see — are closed. Where a finding
was about the *layer* rather than about this document, it is recorded as a packet rather than repaired
in prose.

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
| P22 · V08 "Let me read the texts themselves" | There is no text. `bg_texts` (10,651 chunks, 15 distinct `text_id`s), `bg_compendium_index`, `bg_text_index` are the whole corpus. |
| P15 · V08 "What supports this, where do schools disagree?" | No source witness, no attribution, no school. `bg_concordance`, `classical_attributions`, the `school` column on the yoga/doṣa/daśā catalogs. |
| P16 · V09 "Give me this exact fact" | The `ref_*` surface — 46 capability files — is L0's direct answer to a reference question. Without it a lookup becomes an interpretation. |
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
| the Kāla method substrates — `bg_transit_engine`, `bg_vedha_malefic_scale`, `bg_phaladeepika_latta`, `bg_kota_chakra_rings`, `bg_sarvatobhadra_grid` | P09, P10, P24 — every L3 clock reads a reference scale or a geometry | 6 `ka_*` registered consumers |
| nakshatra geometry — `bg_nakshatra`, `bg_kp_sublord_division` | P09, P21, and every KP reading | `ga_nakshatra` registered; 8 + 6 writer files |
| the investigation floors — `bg_vidhi_primitives`, `bg_vidhi_floors` | P17, P18 — the omission check and the question compass (DP11) | 1 writer + 3 serving files each |
| horary method — `bg_prashna_rules` | P20 method selection, and the Praśna horizon (product §15) | `ga_prashna` registered |
| research capital, served to no P directly — `bg_class_priors`, `bg_class_lifetime_counts`, `bg_cohort` | engineering baselines for `ka_kshetra` and `mi_kula`; **H** by design | 3 registered consumers |
| citation resolution and spatial doctrine — `bg_gochara_citation_resolution` (P15), `bg_vastu_directions` (P08, as testimony) | — | 4 / 5 serving files |

**All 40 assets are traced.** A brief author narrowing §4.4 for any asset finds its P-needs in one of
these rows or in the directly-served table above; an asset appearing in neither would have no reason
to exist in this layer, which is the alignment test applied to assets rather than to sections.

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
- **Scored on — the definitive list for this layer; §3.1, §5.1 and §5.3 use exactly these four and
  no others:**

  | obligation | why L0 is scored on it | scope |
  |---|---|---|
  | **Source and domain fidelity** (primary; product §11 L0 row) | canonical identity, source fidelity, method boundaries | all 40 |
  | **Computational correctness** | the astronomical substrate is computed, not transcribed | `bg_ephemeris`, `bg_ephemeris_engine`, `bg_gochara_arcs`, `bg_sky_calendar`, `bg_muhurta_lattice` |
  | **Delivery fidelity** | L0 has a directly-served surface (§0.1) | the 46 L0 capabilities |
  | **Operational honesty** | the registry, the descriptions and the declared counts are L0's own claims about itself | all 40 |

  Not scored: concept and relationship completeness, interpretive fidelity, distinctive understanding,
  consumer understanding, temporal integrity, predictive performance — these are scored at the layers
  that interpret, time and predict. L0 supplies the vocabulary they are expressed in.

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

- **Registry vs actual reads.** 21 of 40 L0 assets have **zero registered downstream consumers
  outside L0**; **40 of 40 are read by code**. `brahma_ontology` — the identity authority — has four
  declared consumers, all inside L0, and 18 reading files spanning every layer. The declared dependency graph is a small fraction of the real one.
  Consequence, stated precisely: `bg_ontology` **is** declared by four intra-L0 consumers —
  `bg_reference`, `bg_yogas`, `bg_doshas`, `bg_dasha_systems` — and `bg_texts` by eight. What no
  asset declares is a **cross-layer** dependency on them: no `ga_*`, `bo_*`, `ka_*`, `ph_*` or `mi_*`
  asset declares `bg_ontology`, while 18 files read it. So an ontology change propagates within L0 and
  stops at the layer boundary. That is the DP01 risk in its exact mechanical form, and the "21 of 40
  with zero registered consumers" figure above is measured over **cross-layer** consumers only —
  the population, stated, because the unqualified version of this sentence was wrong.
- **Seed vs registry: they agree.** A v2.0 draft of this section claimed five disagreements; every
  one was an artefact of the extraction regex, which matched `upstream_asset_id:` in the neighbouring
  volume-coefficient block rather than the asset's own `target_table`. Re-measured at
  `85bf8f14e:platform/scripts/seed/asset_registry_seed.ts`, parsing each asset's own object: the seed
  matches live on `target_table` and `depends_on` for every named asset. The claim is withdrawn.
  `bg_prashna_rules` remains a genuine registry defect on its own terms (see below): it is a
  five-table asset carrying `target_table: NULL`, in both sources.
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
| `bg_vidhi_floors` | vidhi_intent_floors + vidhi_floor_items | 14 + 409 | — | **none, on either** | ✓ | **0** | 1 / 3 |

**Registry defects, measured:** `bg_prashna_rules.target_table` NULL while `storage_type =
postgres_table` (it is five tables); `bg_vidhi_floors` is `DRAFT` — the only non-CURRENT of 40, while
its dependency is CURRENT; `sort_order` collides at 68 (`bg_formula_constants`, `bg_vidhi_primitives`)
and 69 (`bg_sky_calendar`, `bg_vidhi_floors`) — recorded as an observation, not a defect: no Part 0
item and no obligation depends on `sort_order`, which the orchestrator does not use for ordering; the legacy `reference_nakshatras` table (closure §7 deferred drop, three steps) is **still
present** in production. Two shared-table pairs are partitions, not duplicates: `bg_class_priors` /
`bg_class_lifetime_counts` partition `brahma_class_priors` by `prior_version`; `bg_texts` /
`bg_text_index` share `classical_text_chunks`, the second being an enrichment (embedding + topic_tag)
of the first's rows.

**One built L0 artifact the registry does not know about.** v1.0's first producer slice was built and
is on disk — `brahmagyan/l0_resource_config_slice_v1.json`, `l0_resource_config_slice.py`,
`tests/test_l0_resource_config_slice.py` — and it is registered nowhere, absent from this inventory
until now, and absent from §2.6's release inventory although it is a **second release-shaped artifact
beside `l0_semantic_release_v1.json`**. Two release-shaped files, one registry that knows of neither,
is the same defect class as seam 6 one level down. Disposition and registration: **W-L0-1**.

**Current code vs deployed:** for L0 they coincide. The L0 repair (PR #2727, migrations 1075–1079)
is on `origin/main` and applied to production; no L0 migration is pending on any live head. This is
the only layer for which that is true today.

### 1.2 · Individual contribution — measured as fidelity, not ablation

```
inherits:    Product §11 L0 row (source and domain fidelity); template §1.2 reference-layer clause
measured_by: provenance-column probe (§1.1) · integrity_check_sql presence · identity joins (§1.3 seam 1) · row-count vs registry declaration · evidence-ledger sub-states
traces_to:   0.1
```

L0 is a reference layer. Its assets are the tradition, not products of a chart, so an asset's
individual term is **whether the knowledge is faithful** — identity correct, source present and
qualified, method boundary stated, provenance carried — and not what removing it does to a reading.
An unread doṣa definition is not worth zero; it is the corpus. This section therefore scores fidelity.
Ablation appears for L0 only in §1.4, aimed at consumers, and never as grounds to disposition an asset.

Fidelity per asset, from the measurements already in §1.1 and §1.3:

| fidelity dimension | passes | fails / partial | evidence |
|---|---|---|---|
| **Identity correct** — canonical id resolves in the ontology | yoga, doṣa, daśā catalogs; parihāra → doṣa | `bg_remedies` (`source_canonical_id` is a source-work name, not an entity id) | §1.3 seam 1 / seam 3 |
| **Source present and qualified** — a witness column, populated | catalogs (`classical_citations`, `source_chunk_ids`, `school`); texts; attributions; `bg_dignity_reference`; `bg_parihara_rules`; `bg_kp_sublord_division`; `bg_sarvatobhadra_grid` (schema only) | `sutravali_rules` (text, no school); `bg_transit_rules` (per-row citation, no school; provenance not table-wide per 1079); `vidhi_floor_items` (**no provenance column**); `vidhi_primitives` (version only) | provenance probe, §1.1 |
| **Method boundary stated** — the asset says what it may and may not qualify | `bg_gochara_citation_resolution` ("resolution does not qualify a rule"); `bg_transit_engine` (mean motion, distinct from precise observation); `bg_cohort` (synthetic, labelled) | `bg_rules` — 3,002 extractions with `confidence` but no executable-scope statement per rule (v1.0 L0-C04's "executable status" is not a column) | §2.4 |
| **Integrity detector present** | 37 of 40 | services (probes instead), `bg_sarvatobhadra_grid` (empty) — all three honest | registry |
| **Declared count truthful** | `bg_class_priors` — registry `count_sql` (`WHERE prior_version='1.0'`) = **171**, seed floor 171, live 171: the registry is right | two stale *comments* in the writer (165, 164) | exact count over the asset's own partition |
| **Alias set present** (the vocabulary half of identity) | 662 of 741 entities | all 79 doṣas | §2.6 |

**Per-asset verdicts.** The dimensions above are scored per asset, not by example. Assets not named
below pass all six dimensions on the §1.1 measurement (provenance column present, integrity detector
present, identity resolving, count truthful, alias set present where the class has one):

| asset | dimension | verdict | evidence |
|---|---|---|---|
| `bg_ontology` | identity correct | **FAIL** | 741 rows, 730 distinct ids — 11 duplicates across entity classes (§1.3 seam 1). The identity owner does not satisfy its own rule 1. |
| `bg_ontology` | alias set present | **PARTIAL** | 662 of 741; all 79 doṣas empty |
| `bg_ontology` | source, method boundary, integrity, count | PASS | |
| `bg_rules` | method boundary | **FAIL** | 3,002 extractions carry `confidence` but no executable-scope state; DP §4.3's five rule states are absent (finding 10) |
| `bg_rules` | source present | **PARTIAL** | `text_id` on all 3,002; no `school` |
| `bg_remedies` | identity correct | **PARTIAL** | 289 of 341 `source_canonical_id` values fail on spelling (§1.3 seam 3) |
| `bg_transit_rules` | source present | **PARTIAL** | per-row `classical_citation`, no `school`; provenance is not table-wide (migration 1079) |
| `bg_parihara_rules` | source present | **PARTIAL** | source text and chapter, no `school` |
| `bg_vidhi_floors` | source present | **FAIL** | no provenance column on either of its two tables |
| `bg_vidhi_primitives` | source present | **FAIL** | `version` only |
| `bg_sarvatobhadra_grid` | source present | **UNRESOLVED** | schema carries `school_tag`; 0 rows pending the school ruling |

**What this term says:** L0's knowledge is largely faithful where it is *catalogued* — the yoga /
doṣa / daśā / text core is identified, sourced and schooled — and thin where it is *extracted or
derived*: the rule corpus has passages but no school and no executable scope, two vidhi tables carry
almost no provenance, and one remedy column reuses the identity vocabulary for a different space.
None of this is grounds to remove anything. All of it is grounds to complete it.

**Reachability, recorded as context and not as a score:** every one of the 40 is read by something
(§1.1). Two have no served path — `bg_reference` (a genuine gap: the graha reference table is not
exposed through any `ref_*` capability, candidate **I**) and `bg_cohort` (engineering capital by
design, **H**). One has no writer path and only a served one — `bg_gochara_citation_resolution`,
static by disposition. These are integration facts, not worth judgements.

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
| join | left rows | joined rows | orphans | reading |
|---|---|---|---|---|
| `brahma_yoga_catalog.canonical_id` → `brahma_ontology` | 233 | **237** | 0 | +4 — right key not unique |
| `brahma_dosha_catalog.canonical_id` → `brahma_ontology` | 79 | **84** | 0 | +5 |
| `brahma_dasha_systems.canonical_id` → `brahma_ontology` | 20 | **22** | 0 | +2 |
| `bg_parihara_rules.dosha_canonical_id` → `brahma_dosha_catalog` | 60 | 60 | 0 | clean |

**Every catalog resolves — and three of the four joins return more rows than they started with.** A
join that grows has a non-unique key on the right. Measured directly:
`count(*) = 741`, `count(DISTINCT canonical_id) = 730` — **`brahma_ontology` holds 11 duplicate
canonical ids**, each the same identifier in two entity classes:

```
ashtakavarga [concept+school]      kemadruma [dosha+yoga]        sade_sati [concept+dosha]
balarishta [concept+dosha]         kp [dasha_system+school]      sthira_dasha [concept+dasha_system]
daridra [dosha+yoga]               phaladeepika [school+text]    vyatipata [upagraha+yoga]
dhaiya [concept+dosha]             neecha_bhanga_raja_yoga [concept+yoga]
```

This is **data plane §4.1 rule 1 — one canonical id per thing — failing inside the asset that owns
the rule**, and it is a fidelity FAIL for `bg_ontology` on "identity correct" (§1.2). A consumer
resolving `kemadruma` gets two rows and must pick; nothing in the schema tells it which. Whether the
correct repair is a class-qualified key, a merge, or a declared legitimate polysemy is a design
question, not a cleanup — packet **W-L0-9**.

So the seam reads: **membership is complete — no catalog entry is unknown to the ontology — but
identity is not unique.** The first half was real synergy and remains so; the second half this
document printed and did not see for one draft, which is why the template now requires that a join be
key-checked before it is reported.

**Seam 2 — rules → concepts: NOT LINKED.** `sutravali_rules` has 3,002 rules, **3,002** with a
`text_id` (source-linked, 14 distinct texts) and **17** with a `yoga_canonical_id` (concept-linked).
The rule corpus is anchored to *passages*, not to the *concepts* the catalogs define. Data plane §4.3
asks for "a usable rule graph, not just more text"; measured, it is text. A reasoning layer can cite
a rule's passage but cannot, from the rule row, reach the yoga it qualifies — the link exists for
0.6 % of rules.

**Seam 3 — remedies → identity: ONE SPACE, SPELLING DRIFT.** `brahma_remedy_corpus.source_canonical_id`
is non-null on all **341** rows; **289 do not resolve to `brahma_ontology`**. A v2.0 draft read this
as two identity spaces — entity ids in one column, source-work names in another. It is not. The 52
that *do* resolve are also source-work names — `brihat_samhita` 17, `bphs` 7, `hora_sara` 6,
`muhurta_chintamani` 5 — and they resolve because **`text` and `school` are themselves ontology
classes**. The column has one meaning throughout: the work a remedy comes from. The 289 fail on
**spelling**, not on space: `BPHS` (193) against the ontology's `bphs`, `Phaladeepika` (11) against
`phaladeepika`, plus `classical_tradition` (80), which names no work at all.

That is a controlled-vocabulary violation of the ordinary kind — an unlisted spelling accepted rather
than raised (§4.1 rule 2) — fixed by normalization plus an alias entry, not by a redesign. It is also
the exact failure the native named: a thing missed because it was written differently.

**Seam 4 — declared dependency: LARGELY UNDECLARED.** 19 of 40 assets have ≥1 registered downstream
consumer; 40 of 40 are read. The orchestrator's staleness propagation runs on the declared graph.

**Seam 5 — served surface contract: ABSENT.** 46 capability files (non-test, excluding `index.ts`) under
`platform/src/lib/retrieval/registry/layers/L0_brahmagyan`; **0** declare a `density_contract`
(§N.6). The one served-surface defect this document previously carried here — the `bg_muhurta_lattice`
`FACTOR_FAMILIES` allowlist at 4 of 9 families — **was closed on 2026-09-04 (#1705)**: at
`85bf8f14e` the allowlist lists all nine, and production holds exactly those nine families across
**173,219** rows (exact count; §1.1's `~172,330` estimate is superseded by it). W2 MUST-1 is
discharged, not open.

**Seam 6 — the vocabulary itself: THREE AUTHORITIES.** The DB ontology (741 entities, `synonyms
text[]`), the Python writer-side release `l0.semantic.2026-09-13.1` (12 entities, graha only), and the
domain vocabulary (`domain_vocabulary.py` ↔ `.ts`, 13 members). They disagree where they overlap:
Venus has **7** aliases in the DB and **10** in the release (`venus`, `VE`, `śukra` are release-only);
the `domain` class has **45** entities in the DB, **13** in the domain module, **1** in the release.
No test joins the release to the DB. Full measurement in §2.6.

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

- **Individual (fidelity):** faithful at the catalogued core; thin where extracted or derived — rules
  without school or executable scope, two vidhi tables without provenance, one remedy column in the
  wrong identity space, 79 doṣas without aliases. Nothing fails fidelity outright.
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

**Retirement is not decided by contribution in a reference layer.** The only **R** in this instance
is the legacy `reference_nakshatras` table, retired for *superseded authority* (its successor is
`reference_nakshatra`; closure §7). **I candidates:** `bg_reference` (unserved), `bg_rules`
(unlinked). **H confirmed:** `bg_cohort`, `bg_vastu_directions`, the `bg_medical_mappings` family
(research or testimony capital, served as attributed testimony only). **C candidates:** none — the two
shared-table pairs are partition patterns, verified by their `count_sql`.

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
| Sambandha (typed relations) | rule vocabulary in `bg_rules` | **unqualified → decided here:** the *relation type vocabulary* (aspect, conjunction, exchange, dispositor, nakshatra-link, argalā, virodha) is **L0 data**, because DP §4.2 puts "role vocabulary" and DP §4.1 puts every named thing in the controlled set, and a relation type is a named thing L2 and L3 both cite. The *detection* of a relation in a chart stays L2 code. Packet: add the class to `bg_ontology` under W-L0-9. |
| Bhāvat Bhāvam | no L0 owner | **unavailable → decided here:** the *scope object* — which derived frames are qualified, under which method, with which prerequisites and exceptions — is **L0 data**, for the same reason: it is a qualified rule, and DP02 makes rule qualification L0's. Its *application* to a chart is L2. Packet: W-L0-5, beside the other rule-qualification work. |
| Varga and reference perspectives | `bg_formula_constants` (construction), `bg_kp_sublord_division` | applied for KP; **decided here:** varga *construction conventions* are a calculation convention, which DP §4.2 assigns to L0 explicitly ("varga construction" is named in its Calculation-convention row) — so they are **L0 data** and currently live in L1 code. This is a real relocation, not a new asset; packet W-L0-5, and it is the one decision here with a migration cost, so it is flagged to the native as a *consequence*, not a question. |
| Yoga/doṣa/bhaṅga | `bg_yogas`, `bg_doshas`, `bg_rules` | applied for catalogs; **unqualified** for rules (seam 2) |
| Nakshatra/KP | `bg_nakshatra`, `bg_kp_sublord_division` | applied |
| Kāla methods | `bg_dasha_systems`, `bg_transit_rules`, `bg_vedha_malefic_scale`, `bg_phaladeepika_latta`, `bg_kota_chakra_rings`, `bg_sarvatobhadra_grid` | applied except `bg_sarvatobhadra_grid` — **unresolved** (ADJUDICATION-11 school ruling) |
| Praśna/Muhūrta/calendar | `bg_prashna_rules`, `bg_muhurta_lattice`, `bg_panchanga`, `bg_sky_calendar` | applied as data; Praśna *facility* dormant — native decision open |
| Āyurdāya and constitution | `bg_dasha_systems`, `bg_formula_constants` (method); medical mappings (constitution testimony) | applied as method; computation is L1 |
| Practices and wider tradition | `bg_remedies`, `bg_parihara_rules` | applied; source spellings unnormalized (seam 3) |
| Present interval (P24) | no L0 half | **inapplicable with reason** — the row's data is L3's interval set and L4's expression; L0 supplies only the clock vocabulary, already covered under Kāla |

### 2.6 · Vocabulary conformance — inverted: L0 owns the controlled vocabulary

```
inherits:    Data plane §4.1 (controlled vocabulary, six rules); template §2.6 (L0 inverts: owner, not conformer)
measured_by: brahma_ontology alias-set coverage by class (exact count) · l0_semantic_release_v1.json contents · CANONICAL_DOMAINS member count · test_graha_vocabulary_census.py scope · literal-count grep (non-test .py/.ts) · interface-parameter census (z.enum vs z.string over planet/graha params)
traces_to:   0.2 — "one identity per entity" IS L0's objective; this section measures whether it holds
```

L0 does not conform to the plane's vocabulary. It **is** the vocabulary, and the six rules of data
plane §4.1 are scored against L0 as owner. Measured 2026-09-25:

| rule | state | evidence |
|---|---|---|
| 1 · one id, one closed alias set, per thing | **PARTIAL** | `brahma_ontology`: 741 entities, 16 classes, `synonyms text[]`; **662 populated, 79 empty — and all 79 are the entire `dosha` class.** Venus = `{shukra, sukra, Venus, Bhargava, usana, VEN, VENUS}`. |
| 2 · the set is the only permitted surface; unlisted names are raised | **PARTIAL** | A fail-closed adapter exists — `UnknownGrahaIdentity`, `AmbiguousGrahaIdentity` in `l0_semantic_release.py` — **for graha, in Python**. The serving resolver `resolve_entity.ts` reads DB `synonyms` + names live. Meanwhile **130 Python files and 42 TypeScript files** carry Venus-variant string literals (`"Venus"` ×952, `'Venus'` ×38, `"VENUS"` ×5, `"Shukra"` ×4 …); the top carriers are L1 writers (`ga_structural_writer` 44, `ga_sensitive_writer` 29) and one L0 writer (`bg_dignity_reference` 21). |
| 3 · deterministic, one-directional, normalization declared, ambiguity explicit | **YES for graha; two normalizations overall** | The release declares `unicode_nfc_trim_casefold` and an `ambiguous_aliases` list. The DB resolver uses `$1 = ANY(synonyms) OR lower(name)` — a *different* normalization (no NFC, no diacritic fold). `śukra` resolves in Python and not in the TS resolver unless spelled as stored. |
| 4 · code-side snapshots generated, pinned, parity-tested | **PARTIAL, and it is the central defect** | Release `l0.semantic.2026-09-13.1` carries `content_sha256`, `generation_id`, `supersedes_release_id` and names `bg_ontology` as `identity_owner` — the *shape* is right. But **no test joins the release to `brahma_ontology`**; its `release_status` is `PRODUCER_READY_CANDIDATE`, `admission_status` **`LOCAL_EXECUTION_ONLY`**; it covers **12 entities** (graha) with six near-empty catalogues (concepts 3, roles 2, domains 1, outcomes 2, methods 1, operator_scopes 1). `graha_labels.ts` **is** generated from the release: it imports `l0_semantic_release_v1.json` and builds `RELEASED_IDENTITY_BY_ID` from `semanticRelease.entities` under the release's own `NFC` normalization. Rule 4 holds here. The gap is one level up — the release itself has no parity test against `brahma_ontology`, so a correctly-generated snapshot can still be generated from a stale authority. The **domain** vocabulary is the one place rule 4 fully holds: `domain_vocabulary.py` ↔ `domain_vocabulary.ts` with a member-for-member test — but it holds between two *code* files, and neither derives from the DB's 45 `domain` entities. |
| 5 · external inputs typed to the set | **NO** | Across the retrieval registry and MCP: **2 enum-typed** planet/graha parameters, **32 free-string**. Whether each free-string parameter is resolver-validated before comparison is unverified per tool; `gochara_intensity/enrichment.py`'s own docstring records the failure mode — `fact_subject = 'Venus'` compared raw, mismatching — which it has partly fixed by importing the SSoT — a literal graha set remains at `enrichment.py:93`. |
| 6 · independent maps censused, one per class | **graha only** | `test_graha_vocabulary_census.py` (ADHIṢṬHĀNA A2) reduced 46 independent graha maps to 1 and fails above it — a real detector. It censuses *maps*; two name *tuples* escape it (`panchang_engine/planets.py`, `brahmagyan/ganita/l1_positions.py`, 0 imports of the SSoT). **Fifteen of sixteen entity classes have no census at all.** |

**Where the plane actually stands:** the controlled vocabulary exists end-to-end for **eleven planets on
the Python writer side**, with a serving-side resolver over the full DB set that normalizes
differently, and a cross-language domain vocabulary that agrees with itself and not with the DB. It
is *three* authorities that overlap on a few classes and disagree where they do. The user's example —
a Venus missed because it was called something else — is measured: 32 unconstrained interface
parameters, ~1,000 raw literals, and a diacritic form (`śukra`) that resolves in one language and not
the other.

A correction to §1.1's reader table: `parity_check.ts` appears there as a reader of
`brahma_ontology`, but it is the MCP↔chat *registry* parity gate, not a vocabulary parity check. No
vocabulary parity test exists on the TypeScript side.

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
| **Source and domain fidelity** (primary) | Catalog identity complete. Rules text-anchored, 0.6 % concept-linked. Remedy identity space mismatched. `bg_transit_rules` provenance per-row, registry description corrected (1079) but no standing detector. `bg_sarvatobhadra_grid` empty pending ruling. **The controlled vocabulary is three authorities: DB 741 / release 12 / domains 13, disagreeing on Venus (7 vs 10) and on domains (45 / 13 / 1); the `dosha` class has no alias set at all; 32 of 34 external planet parameters are free strings; and the identity owner itself holds 11 duplicate canonical ids.** | Rule→concept linkage (W-L0-3); identity-space separation (W-L0-3); **one vocabulary authority with parity to every snapshot, all 16 classes, typed interfaces (W-L0-8)**; a description-vs-table detector (W-L0-5); the school ruling (W-L0-6). |
| **Computational correctness** (substrate) | Node frame and epoch declared on `ephemeris_daily` (1076); engine probe degree-anchored (1075); `.se1` file-presence finding from another session not re-verified. | Re-verify the ephemeris file resolver in production (W-L0-1); nothing else measured as wrong. |
| **Concept and relationship completeness** | No L0 object for sambandha typing or Bhāvat Bhāvam scope; varga construction conventions live in L1 code, not L0 data. | Decide whether these are L0 data or remain L1/L2 code — a native/strategy call, recorded in §4.2 as W-L0-6, not assumed. |
| **Delivery fidelity** (served surface) | 46 capability files, 0 `density_contract`; `bg_muhurta_lattice` allowlist 4/9 families; `bg_reference` unserved. | `density_contract` on all 49; allowlist 9/9; a `ref_` capability for graha reference (W-L0-4). |
| **Operational honesty** | `bg_prashna_rules` carries `target_table: NULL` while being a five-table asset; the legacy `reference_nakshatras` table was never dropped (closure §7); `l0_resource_config_slice_v1.json` is built and registered nowhere; two stale count comments in the `bg_class_priors` writer (165, 164) against a correct registry figure of 171; `sort_order` collides at 68 and 69 (observation — nothing orders by it). **Withdrawn after re-measurement:** the seed-vs-registry disagreement (extraction artefact) and the duplicate `@register` decorations (both were docstrings; `register()` raises on a real conflict). | Registry truth pass (W-L0-1). |

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
| `bg_class_priors` / `bg_class_lifetime_counts` | **P** | v1.0 stands. The v2.0 count finding is **withdrawn**: the registry `count_sql` (`WHERE prior_version='1.0'`) returns 171, which is the asset's own partition and matches registry, seed and snapshot; 177 is the shared `brahma_class_priors` table including `bg_class_lifetime_counts`' `ne_v01` rows — the partition this document describes two sections earlier. Two stale writer comments (165, 164) go to W-L0-1. |
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

- `bg_ontology`: declared consumers; a decision on the second identity space; **alias sets for the 79
  doṣas; a DB↔release parity test; one normalization rule shared with the serving resolver; census
  extended from graha to all sixteen classes.**
- `bg_reference`: a served capability; declared consumers.
- `bg_rules`: a concept link (`yoga_canonical_id` / `dasha_system_id` / a doṣa key) on every rule
  that qualifies a catalogued concept, or an explicit `unlinked_reason`; a `school` column; and **a
  qualification state per rule** — DP §4.3 requires rules distinguished as supported /
  readable-but-not-executable / disputed / unsupported / method-inapplicable, and v1.0 carried this
  vocabulary (`READABLE_NOT_EXECUTABLE`, `QUALIFIED_EXECUTABLE`, `UNQUALIFIED_SOURCE`,
  `UNSUPPORTED_SCOPE`, `METHOD_INAPPLICABLE`). It is a parent obligation, it exists in code, and it
  was dropped from this document's must-add list; restored here.
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
| **W-L0-1 Registry truth** | 3.1 operational honesty: `bg_prashna_rules` target made honest (five tables, or a declared multi-table set); the two stale writer comments corrected to 171; `l0_resource_config_slice_v1.json` dispositioned and registered or deleted (C-5); legacy `reference_nakshatras` dropped; `bg_vidhi_floors` status re-verified against the writer source (C-2); the "no subject column on any `bg_*` table" check run; the `.se1` resolver re-verified in production | a registry-parity test for L0 (the L3 parity test extended to `bg_*`); `to_regclass('reference_nakshatras') IS NULL` |
| **W-L0-2 Declared dependencies and declared use** | seam 4; 2.3 both halves | every code read of a `bg_*` table is either a registered `depends_on` edge or a documented serve-time read with a declared use type; detector: the reader grep in §1.1 re-run yields no undeclared writer-side reads |
| **W-L0-3 One identity, linked rules** | seam 2, seam 3; 3.2 for `bg_ontology`, `bg_rules`, `bg_remedies` | `source_canonical_id` no longer joined against `brahma_ontology` by name (renamed or re-keyed); rule→concept coverage reported as a number with an `unlinked_reason` on the remainder — the 0.6 % becomes a measured figure with a stated ceiling, not a target |
| **W-L0-4 Served-surface contract** | seam 5; 3.1 delivery fidelity | every exported `CapabilityDescriptor` in the L0 registry declares one (the proof counts descriptors, not files); lattice allowlist 9/9 with a test that fails on 8; `ref_graha_reference_get` (or equivalent) exists and is exercised |
| **W-L0-5 Provenance completion and truthfulness** | 2.2 partial/absent rows; 2.1 description-vs-table gap | `school` on `sutravali_rules`, `bg_transit_rules`, `bg_parihara_rules`; provenance columns on `vidhi_floor_items`; a standing check that a registry `english_description` provenance claim is supported by the table (the 1079 defect class, generalised) |
| **W-L0-6 Native rulings — two, not five** | `bg_sarvatobhadra_grid`'s school (ADJUDICATION-11: a doctrinal choice with no in-repo answer); `bg_prashna_rules`' facility (a product-scope and disclosure decision). **Withdrawn as native rulings:** `bg_vidhi_floors`' status — the live registry description already answers it ("catalog_status=DRAFT is intentional, not stale: 12/14 intent floors are writer-tagged [MANDATORY] … re-verify against the writer source before flipping"), so this is a verification task, not a ruling; the remedy identity question — it dissolved when the column turned out to be one space with spelling drift (§1.3 seam 3); and whether sambandha typing / Bhāvat Bhāvam scope / varga construction become L0 data — **data plane §4.1–4.2 assigns that decision to this document**, and pushing it up was this author avoiding a call that was his. It is taken in §2.4 below. | rulings recorded in `KALA_DELEGATED_DECISIONS` or its L0 equivalent; each packet above that depends on one names it |
| **W-L0-9 Identity uniqueness and the missing classes** | §1.3 seam 1 (11 duplicate canonical ids); §2.4's two decisions (relation-type vocabulary, Bhāvat Bhāvam scope as L0 data) | `SELECT count(*) - count(DISTINCT canonical_id) FROM brahma_ontology` = 0, by whichever repair the design review chooses — class-qualified key, merge, or a declared and *enforced* polysemy rule that tells a consumer which row to take. Plus: the relation-type class exists in the ontology and `bg_rules`/L2 cite it rather than typing relations locally. Must precede W-L0-8, since a vocabulary cannot be controlled while its identity owner has ambiguous keys. |
| **W-L0-8 Controlled vocabulary, end to end** | §2.6 rules 1–6; seam 6; seam 3 (the remedy column is a vocabulary violation instance) | (1) `SELECT count(*) FROM brahma_ontology WHERE cardinality(synonyms)=0` = 0; (2) a parity test joins `l0_semantic_release_v1.json` to `brahma_ontology` and fails on any alias-set difference — Venus 10 ≟ 7 is the first failure it must report; (3) the `domain` class has one authority, with DB↔Python↔TypeScript parity, and the count is one number, not 45/13/1; (4) the serving resolver and the release share one declared normalization (`śukra` resolves in both); (5) the graha census is generalised to a per-class census over all sixteen classes, permitted count one, and the two escaping name-tuple modules import the SSoT; (6) the interface-parameter census reports 0 free-string planet/graha parameters (enum or resolver-validated); (7) the release's `admission_status` leaves `LOCAL_EXECUTION_ONLY` by a recorded native decision, not by drift. Depends on W-L0-1 (a registry it can trust) and pairs with W-L0-3 (the identity-space decision). |
| **W-L0-7 The consumer-perturbation harness** | 1.4 "traceably transformed" and "value evaluated" — for L0's *consumers* | a shared instrument, not an L0 judgement: on a disposable snapshot, perturb a named L0 fact (a rule row, an alias, a constant) and run a fixed set of L1–L3 readings; the detector is that the consuming reading **moves**, and moves in the way the fact predicts. A consumer that does not move has not consumed. Findings land in L1–L5's plans. Detector for the packet itself: the harness exists, runs in CI, and shows at least one L2 reading moving when `bg_yogas` is perturbed. |

W-L0-7 is the packet without which §1.4 stays at "consumed" and never reaches "value evaluated" — for
L0's consumers, not for L0. It is named last because it depends
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

### 5.1 · The score — fidelity for the assets, ablation only for their consumers

```
inherits:    Product §14, §14.1; Data plane §12.2 (reference-layer carve-out); template §5.1
measured_by: fidelity dimensions of §1.2 (measurable today); consumer-perturbation harness W-L0-7 (does not exist)
traces_to:   0.2
```

L0 scores on **source and domain fidelity** (all 40), **computational correctness** (the five substrate
assets), **delivery fidelity** (the served surface) and **operational honesty** (registry and
description truthfulness). The individual flavour of ablation is **replaced by the fidelity score** of
§1.2 — an L0 asset is never scored, and never dispositioned, by what its removal does to a reading.

Ablation runs against L0 in exactly one flavour, **cross-layer**, and answers exactly one question:
*does the consumer use this knowledge correctly?* Perturb a `bg_transit_rules` row and confirm the L3
reading moves; sever the ontology joins and confirm L2 resolution fails loudly rather than silently.
A consumer that does not move has not consumed. That is a finding about L1–L5, recorded in their
plans; it is never a finding against the L0 asset.

### 5.2 · The per-asset checklist

```
inherits:    kala_brief_tracker.py TIERS; template §5.2
measured_by: the tracker — which today lists only the 22 L3 assets; extending its ASSETS table to bg_* is part of W-L0-1
traces_to:   4.4
```

The 32 criteria apply unchanged. Two are structurally different for L0 and the template should say
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

## §7 · Corrections outstanding, and the gate each blocks

Required by the template's first middle-tier guard: a correction with no named gate defaults to
blocking the next gate. None of these is a document defect — all were fixed above. These are the
verification and design items this instance leaves open.

| # | correction | gate it blocks |
|---|---|---|
| C-1 | The per-asset fidelity verdicts in §1.2 are scored from §1.1's measurements; the five **PARTIAL/FAIL** rows have not been re-verified by a second party | L0 layer certification (§5.3), not the asset briefs |
| C-2 | `bg_vidhi_floors`' DRAFT status: the registry description says re-verify against the writer source before flipping. Not done here | the `bg_vidhi_floors` asset brief |
| C-3 | The varga-construction relocation (§2.4) has a migration cost that is stated but not sized | the first L1 instance — it moves a convention out of L1 code |
| C-4 | §5.2's 32 criteria are not yet mapped to §4.4's inheritance list; the review found six with no feeding section | the first `bg_*` asset brief |
| C-5 | `l0_resource_config_slice_v1.json` is on disk, registered nowhere, and undispositioned | W-L0-1, and the registry-parity detector it builds |
| C-6 | Presentation parity (§2.2) has not been run for any L0 capability | the first served-surface packet, W-L0-4 |

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
6. **Ablation was the wrong individual measure for a reference layer**, and the template applied it
   uniformly. Raised by the native: perennial knowledge judged by today's readers would be retired one
   unread chunk at a time. Repaired 2026-09-25 in the template (§1.2 reference-layer clause, §1.5
   exemption, §5.1) and in the data plane (§12.2 carve-out). This instance's §1.2 was rewritten from a
   reachability proxy to a fidelity score, and W-L0-7 re-aimed from judging L0 assets to verifying
   their consumers. The second finding that propagated upward.
8. **`measured_by:` named an instrument but never a population**, and three of this instance's nine
   wrong figures came from exactly that gap — a regex whose scope was unstated, a count over a shared
   table compared against one partition's registry figure, and a join reported without checking its
   right-hand key was unique. Repaired 2026-09-25: `measured_by:` must name the population, with the
   corollary that a join is not measured until its keys are.
9. **§5.2's 32 criteria were never mapped to §4.4's inheritance list**, so a brief author could reach
   a criterion no section feeds — the review found six. Repaired: the map is now required before an
   instance is called ready.
10. **The verdict scale was binary**, which forces REJECT on an instance whose direction is sound and
   whose corrections are real. Repaired with a three-verdict scale and the document/layer distinction
   that keeps the middle tier from rotting (template §5.4).
7. **Vocabulary conformance was missing from the template entirely** until this instance's
   measurement surfaced three disagreeing authorities. Repaired 2026-09-25 in the template (§2.6, T4
   `Vocab`) and in the data plane (§4.1 raised to a governing principle) — the first defect this
   instance found that propagated *upward* rather than down.
