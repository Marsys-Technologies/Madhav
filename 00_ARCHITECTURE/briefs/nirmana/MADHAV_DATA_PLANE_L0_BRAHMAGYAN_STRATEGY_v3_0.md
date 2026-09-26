---
artifact: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY
canonical_id: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY
tier: 3
kind: instance
version: "3.0"
status: DRAFT_PENDING_ACCEPTANCE
produced_on: 2026-09-26
template: 00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md  # FINAL, SEALED bb88bee1e024b349470b74301159114aaedd6880a0e35f76e86ba74819e0ae42
parents:
  - 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md                              # FINAL, SEALED b9c098cd390dd3b1d1ab99738f342ca95e01f3609ffcaca70a37e3f7979a52f5
  - 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md     # FINAL, SEALED 68b991f349edae92519935d5845b6a90f78624f631866c1cbd87a99ca874ec86
supersedes: "MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md — NOT edited into this file. Built fresh from the sealed template by native instruction (2026-09-26): every figure re-measured, none inherited. v2.1 is retained as the historical instance; its nine non-reproducing figures are not carried forward."
authority: "Native instruction 2026-09-26: rebuild L0 from the sealed FINAL template, disregarding the earlier instance."
measured_at: "Production read-only, 2026-09-26, via each asset's own count_sql + asset_elevation_tracker.py --layer L0; repository at l3/kala-layer-briefs @ 96347eddb (pre-commit working tree)."
verdict: "NONE. This instance carries no verdict: its acceptance tests (§5.4) are not all met, and the template is explicit that an instance stamped by its own author with tests pending is unreviewed whatever the verdict says. §5.4 states which tests are met and which are not."
---

# L0 Brahmagyan — Layer Definition and Strategy (v3.0, rebuilt)

Built fresh against the sealed template. Every number here was measured on 2026-09-26 by the instrument
named in its section's `measured_by:` line; nothing is inherited from v2.1.

---

## Part 0 · VALUE — the origin

### 0.1 · What cannot be answered without this layer

```
inherits:    Product §2 (P01-P24), Data plane §2 (V01-V13)
measured_by: none — definitional; every P/V cited checked to exist in the parent under FINAL numbering
traces_to:   —  (this IS the origin)
```

L0 is **necessary to almost everything and directly served to little**. The rows below are only those
where removing L0 removes the distinction itself, not those where it removes convenience.

| P / V | the distinction that disappears without this layer |
|---|---|
| P15 "what supports this in the tradition, where do schools disagree" | There is no source testimony and no school record at all — the question has no substrate. |
| P22 "let me read the texts themselves" | The corpus *is* this layer: 15 texts, 10,651 chunks. Nothing to read. |
| P20 "which form of Jyotish suits my question" | Method identity, scope and applicability are L0 declarations; without them method selection is a guess. |
| P07 / P23 "what does the tradition say about wellbeing / lifespan" | The method, its school and its cancellations are doctrine held here; without them a figure would be served bare, which the parent forbids. |
| P09 "does this yoga form" | The catalogue definition and its prerequisites are the thing formation is tested *against* — 233 yoga and 79 doṣa definitions. |
| P11 "when might I initiate something, which practices" | The muhūrta lattice (173,219 rows) and the attributed practice corpus (341 rows) are L0. |
| P13 "does a different convention change this" | The conventions themselves — ayanāṃśa, node, house system, varga construction — are L0 declarations; without them there is nothing to vary. |
| P16 / P17 exact fact · what have I not asked | The concept map an omission check expands against is the ontology (741 rows, 16 classes). |
| V08 source learning and scholarly depth | Entirely L0: passage, edition, witness, rule qualification. |
| V05 calendar, action and method selection | Calendar substrate (31,081 sky-calendar rows) plus method eligibility vocabulary. |
| V12 lifespan and constitution | The applicable method and school identity, without which the computation cannot be qualified. |
| V01 connected self-understanding | The role vocabulary — natural significator, functional role, lordship, kāraka — that keeps four different things from collapsing into one word. |

**Everything else inherits L0 indirectly**, through L1's conventions and L2's concept ids. That indirect
necessity is real but it is measured in 1.4 (cross-layer handoff), not claimed here.

### 0.2 · The layer's objective

```
inherits:    Product §1 (the join), §11 (L0 row), Data plane §3.1 (L0 row)
measured_by: none — definitional
traces_to:   0.1
```

L0 makes every later distinction **attributable**. Conventional software hard-codes a term's meaning in
the routine that uses it; this layer holds meaning as data — one canonical identity per thing, the rule
that qualifies it, the passage it rests on, the convention it assumes and the boundary beyond which it
does not apply — so that a reasoning layer can read *why* a computation was legitimate, not only what it
produced. That is what it hands the join: not answers, but the vocabulary and the warrant that make
answers checkable.

- **Owned question** (data plane §3.1): what does a term, rule, method or reference quantity mean, and
  when is it applicable?
- **Handed onward**: canonical identities; source-qualified doctrine; constants; astronomy and calendar
  foundations; method, prerequisite and exception vocabulary.
- **Must not claim**: personal fate; raw private biography as global truth; source count as probability.

**Obligations this layer is scored on — stated once, here, and nowhere else in this document.** Product
§11's L0 row names one; three more are added with their reason, because this layer's own artefacts make
them applicable:

| obligation | why it applies to L0 |
|---|---|
| **Source and domain fidelity** | the product §11 row for this layer — its primary score, over all 40 assets |
| **Computational correctness** | five assets are computed substrate, not testimony (`bg_ephemeris` 825,084 · `bg_muhurta_lattice` 173,219 · `bg_gochara_arcs` 33,933 · `bg_sky_calendar` 31,081 · `bg_cohort` 110,000). A computed table cannot be scored on source fidelity alone. |
| **Delivery fidelity** | L0 is rendered through 46 served capability modules; the parent's §14 row names both presentation modes |
| **Operational honesty** | L0 is the registry's root — a registry description asserting a provenance its table lacks is an L0 defect |

**Not scored on**: concept and relationship completeness (L2's row) · temporal integrity (L3's) ·
interpretive fidelity, distinctive understanding, consumer understanding (formed above this plane) ·
predictive performance (L5's). **Domain correctness is excluded by native ruling 11** — whether the
astrology is *right* is formed above the data plane; L0's half is carriage, measured in §2.7.

### 0.3 · Its place in the wheel

```
inherits:    Data plane §3.2 (five edge types), §7 (DP contracts)
measured_by: three sources reconciled — asset_registry (live, read-only, 2026-09-26) · the registry seed (platform/scripts/seed/asset_registry_seed.ts, block-scoped parse of all 40 bg_* entries) · the migration-governed pin
traces_to:   0.2
```

- **Receives from:** no layer. All 40 assets have zero non-`bg_*` dependencies (measured). L0's inputs
  are external: the text corpus, the Swiss ephemeris, and the conventions the native has ruled on.
- **Hands onward to:** L1–L5 and the serving surface, by **edge 1 (definition)** — shared identity, unit,
  method or rule meaning — and **edge 3 (serving-context)** — hydration and source drill, including the
  query that revisits L0 after L3 reveals an exception. Contracts: **DP01 identity/release** and **DP02
  rule qualification**, plus L0's half of **DP05 configuration** (the catalogue definition against which
  L1 tests formation).
- **What the join needs from it:** the closed alias set that lets one identity render as *Śukra* for the
  acharya and *Venus* for the layperson; the school or tradition behind a rule and the fact that
  authorities disagree; the convention in force; and the method boundary that says where a rule stops.

**Three-source reconciliation, stated separately as the template requires:**

| source | state |
|---|---|
| live `asset_registry` | 40 `bg_*` assets |
| registry seed | 40 `bg_*` entries |
| migration-governed pin | **does not exist for L0.** No migration asserts L0 registry rows. This is an honest absence, not a disagreement — and it means the seed/live agreement below is a two-source check, not three. |

**Disagreements between seed and live: zero** — `target_table` and `depends_on` agree for all 40,
measured by a block-scoped parse (each entry read from its own `asset_id:` to the next, so a neighbouring
block cannot bleed in). Recorded explicitly because the previous instance reported five disagreements
here; all five were an artefact of a regex that read past its block, and none of them exists.

### 0.4 · The alignment test

Every section from Part 1 on carries `traces_to:`. Run on this draft: no section was struck, and two
candidates were — a "governance cadence" subsection and an L0-owned glossary of layer names, neither of
which served a 0.1 row.

---

## Part 1 · VALUE DECOMPOSITION

### 1.1 · Inventory, measured

```
inherits:    Data plane §13.3 item 2
measured_by: asset_registry (live) for identity/floor/writer/integrity/catalog_status · each asset's OWN count_sql executed against production 2026-09-26 (the cockpit instrument, not a table count) · asset_elevation_tracker.py --layer L0 for brief and gate state
traces_to:   0.3
```

**40 assets.** 34 writer-backed, 6 not. 38 carry a `count_sql`; 2 are services with no table by design.
1 is `catalog_status = DRAFT` (`bg_vidhi_floors`); the other 39 are CURRENT. Tracker state:
**NO_BRIEF = 40/40, ELEVATED 0/40, gates certified 0/320.**

| asset | target table(s) | live (own count_sql) | floor | Δ | writer | integrity |
|---|---|---|---|---|---|---|
| bg_ontology | brahma_ontology | 741 | 737 | +4 | y | y |
| bg_reference | reference_planets + 2 | 1,242 | 1,242 | 0 | y | y |
| bg_formula_constants | brahma_formula_constants | 17 | 17 | 0 | y | y |
| bg_dignity_reference | bg_dignity_reference + 1 | 151 | 151 | 0 | y | y |
| bg_nakshatra | reference_nakshatra + 1 | 2,857 | 2,857 | 0 | y | y |
| bg_texts | classical_text_chunks | 10,651 | 10,651 | 0 | y | y |
| bg_text_index | classical_text_chunks (distinct topic_tag) | 361 | 361 | 0 | y | y |
| bg_concordance | classical_attributions | 721 | 721 | 0 | y | y |
| bg_compendium_index | brahma_compendium_index | 9,571 | 9,571 | 0 | y | y |
| bg_rules | sutravali_rules | 3,002 | 3,002 | 0 | y | y |
| bg_yogas | brahma_yoga_catalog + 1 | 784 | 784 | 0 | y | y |
| bg_doshas | brahma_dosha_catalog + 1 | 237 | 237 | 0 | y | y |
| bg_dasha_systems | brahma_dasha_systems + 1 | 60 | 60 | 0 | y | y |
| bg_remedies | brahma_remedy_corpus | 341 | 341 | 0 | y | y |
| bg_parihara_rules | bg_parihara_rules + bg_muhurta_activity_rules + bg_muhurta_factor_census | **440** | **449** | **−9** | y | y |
| bg_muhurta_lattice | bg_muhurta_lattice | 173,219 | 164,575 | +8,644 | y | y |
| bg_ephemeris | ephemeris_daily | 825,084 | 825,084 | 0 | y | y |
| bg_sky_calendar | bg_sky_calendar | 31,081 | 31,059 | +22 | y | y |
| bg_gochara_arcs | bg_gochara_arcs | 33,933 | 33,933 | 0 | y | y |
| bg_transit_rules | bg_transit_rules | 76 | 76 | 0 | y | y |
| bg_transit_engine | bg_transit_engine | 9 | 9 | 0 | **n** | y |
| bg_cohort | bg_synthetic_cohort + 1 | 110,000 | 110,000 | 0 | y | y |
| bg_class_priors | brahma_class_priors (partition) | 171 | 171 | 0 | y | y |
| bg_class_lifetime_counts | brahma_class_priors (partition) | 6 | 6 | 0 | y | y |
| bg_ghatana | brahma_event_ontology + 1 | 39 | 39 | 0 | y | y |
| bg_vidhi_primitives | vidhi_primitives | 60 | 60 | 0 | y | y |
| bg_vidhi_floors | vidhi_intent_floors + vidhi_floor_items | 423 | 423 | 0 | y | y (DRAFT) |
| bg_kp_sublord_division | bg_kp_sublord_division | 249 | 249 | 0 | y | y |
| bg_kota_chakra_rings | bg_kota_chakra_rings | 27 | 27 | 0 | y | y |
| bg_vedha_malefic_scale | bg_vedha_malefic_scale | 5 | 5 | 0 | y | y |
| bg_phaladeepika_latta | bg_phaladeepika_latta | 8 | 8 | 0 | y | y |
| bg_gochara_citation_resolution | bg_gochara_citation_resolution | 14 | 14 | 0 | **n** | y |
| bg_vastu_directions | bg_vastu_directions + 1 | 32 | 32 | 0 | y | y |
| bg_medical_mappings | bg_medical_mappings | 21 | 21 | 0 | y | y |
| bg_sign_medical | bg_sign_medical | 12 | 12 | 0 | y | y |
| bg_nakshatra_medical | bg_nakshatra_medical | 27 | 27 | 0 | **n** | y |
| bg_prashna_rules | bg_prashna_lagna_methods + … (**target_table NULL**) | 41 | 41 | 0 | y | y |
| bg_sarvatobhadra_grid | bg_sarvatobhadra_grid | 0 | 0 | 0 | **n** | n |
| bg_ephemeris_engine | — (service) | n/a | — | — | **n** | n |
| bg_panchanga | — (service) | n/a | — | — | **n** | n |

**Three findings the inventory itself produces:**

1. **`bg_parihara_rules` is 9 rows below its floor** — components measured 60 + 329 + 51 = 440 against a
   floor of 449. Floors are aspirational and set to the achieved count after a build (§N.4), so a
   sub-floor reading means rows were lost after the floor was stamped, or the floor was stamped over a
   population the `count_sql` no longer sums. **Cause not established**; one query against build history
   settles it. Packet W-L0-6.
2. **`bg_prashna_rules` has `target_table` NULL while having a writer and summing three tables.** The
   template requires target tables as a *set*; the registry has no field for one, so a multi-table asset
   either names one table arbitrarily or names none. This asset names none.
3. **The sum of the 38 `count_sql` outputs is 1,205,713, and that is a cockpit sum, not a row total.**
   Two pairs measure the same table: `bg_class_priors` and `bg_class_lifetime_counts` are two partitions
   of `brahma_class_priors`; `bg_texts` counts rows of `classical_text_chunks` while `bg_text_index`
   counts distinct `topic_tag` over the same table. Reporting 1.2M as "L0 rows" would double-count and
   mix two units — exactly the population error the template's `measured_by` rule exists to prevent.

### 1.2 · Individual contribution — fidelity, not ablation

```
inherits:    Product §14.1, Data plane §12.2 (reference-layer carve-out), template §1.2 reference-layer clause
measured_by: per asset, four fidelity dimensions — identity correct · source present and qualified · method boundary stated · provenance carried — each by a named query at 2026-09-26; NOT MEASURED where no query was run in this pass
traces_to:   0.1
```

L0 is a knowledge authority, so the individual term is **fidelity**: an unread piece of authentic
knowledge is not worth zero, and ablation is not its measure. Six assets were measured this pass; the
remaining 34 are marked honestly.

| asset | fidelity | measured result |
|---|---|---|
| bg_ontology | **CORRECTED 2026-09-26 by pilot 1 — not an identity FAIL** | This row previously read FAIL: 741 rows, 730 distinct `canonical_id`, 11 ids in two classes each. Re-measured against the table's **declared key** — `UNIQUE (entity_class, canonical_id)`, a live database constraint, and the seeder's own `ON CONFLICT` target — production holds **741 rows, 741 distinct composites, 0 duplicates**. The authority is internally consistent and the 11 ids (`ashtakavarga` concept+school, `phaladeepika` school+text, `kemadruma` doṣa+yoga, …) are a school and a concept being two things, which the composite key permits by design. **The defect is elsewhere and is two defects:** (i) the detector this document and the sealed data plane §4.1 rule 1 specify — `count(DISTINCT canonical_id)` *across* classes — is the wrong detector for a composite-key authority and reports FAIL on conformant data (reopen request C-8); (ii) consumers that resolve on `canonical_id` alone, chiefly `resolve_entity.ts`, which returns two rows and applies a hard-coded class preference (`bg_ontology-G04`). |
| bg_ontology | **FAIL (one class)** | alias sets: 15 of 16 classes complete; **`dosha` 79 rows of 79 with an empty alias set** — the class a doṣa name lookup must resolve through. |
| bg_rules | **PASS (source present)** / **WEAK (linkage)** | 3,002 rules, **all** carrying `verse_ref`, across 14 texts. But only **17 of 3,002** carry a `yoga_canonical_id` — the rule→concept link is 0.6% populated. |
| bg_doshas | **PARTIAL (qualification)** | 79 rows, all with a citation field populated, but **53 cite the placeholder `classical_tradition`** rather than a text — a populated field that names no source. |
| bg_remedies | **PARTIAL (provenance)** | 341 of 341 rows carry `source_canonical_id`; **289 do not resolve** to `brahma_ontology`. One identity space with normalisation drift, not two spaces. |
| bg_sarvatobhadra_grid | **PASS by abstention** | 0 rows, deliberately (ADJUDICATION-11). An empty school-keyed table honestly states that grid variants exist and none is held; the alternative would have been a transcribed guess. |
| the other 34 | **NOT MEASURED** | no fidelity query was run against them in this pass. Not a pass, not a fail — a gap, and packet W-L0-1 closes it. |

### 1.3 · Synergistic contribution — ablate the group

```
inherits:    Data plane §3.4, §7, §3.5 (the plane's synergy term and its four seams)
measured_by: seam by seam — the join each seam depends on, with its key uniqueness checked first; no ablation harness exists, so no fraction is computed
traces_to:   0.2
```

L0's synergy is one question: **is the shared vocabulary actually shared?** Three seams carry it.

| seam | measured | state |
|---|---|---|
| **A · catalogue → identity** — every yoga, doṣa and daśā-system id resolves to one ontology row | 233 yoga + 79 doṣa + 20 daśā-system rows against 741 ontology rows keyed `UNIQUE (entity_class, canonical_id)` — **unique under the declared key**, 730 distinct on `canonical_id` alone | **REAL, and UNDECLARED.** Corrected 2026-09-26: the key is not broken; the seam is not *declared*. The three catalogues each seed identity rows into the ontology (pilot 1 §1) and none references it by a declared contract, so the seam cannot be broken to be measured. A consumer joining on `canonical_id` alone over-counts for 11 ids — a consumer defect, not an authority one. |
| **B · rules → concepts** | 17 of 3,002 rules linked to a concept id | **EFFECTIVELY ABSENT.** 3,002 qualified rules and almost no machine path from a rule to the concept it qualifies. |
| **C · remedies → source identity** | 52 of 341 resolve; 289 fail on spelling | **UNNORMALISED.** The seam is declared and populated but does not join. |

**Synergistic fraction: absent instrument.** No ablation harness exists for L0, so no fraction is
recorded — the template forbids inventing one. The seam-by-seam state above *is* the value of this term,
and building the harness is packet W-L0-7.

### 1.4 · Cross-layer handoff — what it produces downstream

```
inherits:    Data plane §11 (six evidence states), §7 (DP01, DP02 produced)
measured_by: registry depends_on for declared edges · file-reference counts over platform/python-sidecar, platform/src, platform-mcp/src for actual reads · the L0 served surface by directory listing and grep
traces_to:   0.3
```

This term dominates L0's value, and the instrument matters: **the registry understates it badly.**

- **Declared:** only **19 of 40** `bg_*` assets have any downstream consumer in `depends_on`; 21 have
  none. Consuming layers: Kāla (most), Gaṇita (5 edges only), Mīmāṃsā, Bodha.
- **Actual:** the same tables are read in dozens of files each — `ephemeris_daily` 71, `bg_transit_rules`
  68, `classical_text_chunks` 59, `brahma_remedy_corpus` 48, `brahma_dosha_catalog` 32, `brahma_ontology`
  30, `bg_muhurta_lattice` 30, `sutravali_rules` 29, `brahma_yoga_catalog` 27.
- **The disagreement is the finding:** consumption is real and heavy, and the registry DAG is not the
  instrument that measures it. An asset with "no consumer" in the registry may be read in twenty files.
  This is why no L0 asset may be dispositioned **R** on registry evidence alone.
- **Served state:** 46 non-test capability modules under `L0_brahmagyan/`, 39 declared
  `CapabilityDescriptor`s — and **0 of 46 declare a `density_contract`**, so the plane's density
  discipline (§N.6) is undeclared across the whole L0 surface.

Evidence states reached, per the six-state scale: `source-present` and `method-qualified` for all 40;
`consumed` demonstrable for at least the nine tables above; `traceably transformed` and `served`
demonstrable through the 46 modules; **`value evaluated` reached by none** — no ablation has been run.

### 1.5 · The accounting

```
inherits:    —
measured_by: 1.2 + 1.3 + 1.4 against 0.2
traces_to:   0.2
```

> **L0 value = Σ fidelity + Σ synergistic + Σ cross-layer handoff**

- **Fidelity:** measured for 6 assets — 2 FAIL (both in `bg_ontology`, the identity owner), 3 PARTIAL/WEAK,
  1 PASS-by-abstention; **34 unmeasured.**
- **Synergistic:** one seam real but keyed on a non-unique id, two seams effectively absent. No fraction —
  absent instrument.
- **Cross-layer:** real and dominant, unquantified. Nothing has reached `value evaluated`.
- **Shortfall against 0.2:** the objective is that every later distinction be *attributable*. Today a
  claim can be traced to an L0 row, but that row's id may resolve to two things (seam A), its rule may
  have no concept link (seam B), and its citation may name a placeholder (53 doṣa rows) or fail to
  resolve (289 remedy rows). **The delta is attribution that breaks at the join**, not missing content.

Per the reference-layer rule, no asset is a candidate for **R** on a zero score here: retirement requires
failed fidelity, never a missing reader.

---

## Part 2 · CONDITIONS UNDER WHICH THE VALUE IS REAL

Section order follows the template as written (2.1, 2.2, 2.3, 2.4, 2.6, 2.7, 2.5). The template's own
numbering places 2.5 last; kept rather than silently reordered, and logged in Part 6.

### 2.1 · Correctness rules

```
inherits:    Product §8.1 (L0 row), §13; Data plane §9.2 (the switch and the storage separation)
measured_by: a detector per rule, named below, each able to report the rule violated
traces_to:   0.2
```

| rule | detector | state 2026-09-26 |
|---|---|---|
| **Private observations must never become global doctrine or reference truth** (product §8.1, L0 row, verbatim) | any L0 target table carrying `chart_id` or `subject_id` | **PASS — 0 of 40.** L0 holds no per-subject column anywhere, so the rule is satisfied structurally rather than by policy. |
| **Switch ON** — L0 may supply shared event vocabulary, precision and provenance definitions | `brahma_event_ontology` is a vocabulary, not an event store: row count (39) vs any per-subject column (none) | PASS |
| **Switch OFF** — nothing derived from life events, anywhere | same detector as above: with no subject column, there is nothing to deselect | **PASS, and storage separation is trivial here** — OFF is a selection because L0 has no event-conditioned overlay to rebuild |
| **No invented computation, source, detector, confidence or score** (product §13) | (a) the 529 abstention — an empty school-keyed table where geometry is not held; (b) `assert_legal()` on the verification vocabulary; (c) citation fields naming a real text | **PARTIAL.** (a) and (b) hold. (c) fails for 53 doṣa rows citing `classical_tradition` — a populated citation naming no source. |
| **A status is earned or null** (§N.8) | `count_sql` present and chart-scoped per asset; `integrity_check_sql` present | 38/40 count_sql, 37/40 integrity; the 3 without are the two services and the abstaining grid — correct absences |

### 2.2 · Presentation obligation

```
inherits:    Product §2 (two modes, one depth); Data plane §3.4 (field → contract mapping)
measured_by: presentation-parity test (Data plane §12.2) — NOT RUN: no harness exists
traces_to:   0.1
```

Of the eight §3.4 rows, L0 must carry and hand onward **three**:

| §3.4 row | L0's part | carried? |
|---|---|---|
| method and school a finding rests on, and where authorities disagree | DP02: school/tradition, unresolved alternatives, the witness behind each variant | **PARTIAL** — `classical_attributions` holds 721 attributions; no detector proves a disagreement is carried rather than flattened |
| conventions in force — ayanāṃśa, node, house system, varga construction | DP01: the released convention set | carried (declared as data) |
| one identity rendering two ways (*Śukra* / Venus) | the closed alias set per §4.1 | **PARTIAL** — 15 of 16 classes; doṣa has no alias set, so a doṣa cannot render in two vocabularies |

Parity test state: **NOT RUN.** Recorded as an unmet acceptance test in §5.4, not as a pass.

### 2.3 · Contracts produced and consumed

```
inherits:    Data plane §7 (DP01-DP17), §7.1 (common envelope)
measured_by: fields present in the producer table and read at the consumer, both ends
traces_to:   0.3
```

**Produced:**

| contract | consumer | fields | grain | state |
|---|---|---|---|---|
| **DP01 identity/release** | every layer, adapter and writer | canonical id, alias set, entity class, unit, release | one row per thing | live; **key not unique** (1.2) |
| **DP02 rule qualification** | L1 formation, L2 interpretation, L3 activation, investigator | rule clauses, method, school, prerequisites and exceptions *to be* tested, unresolved alternatives, executable scope | one row per rule | live for clauses and verse; school/disagreement PARTIAL; **executable scope not a column** |
| **DP05 (L0's half)** | L2 via L1 | the catalogue definition formation is tested against | one row per configuration definition | live (233 yoga, 79 doṣa) |

**Consumed:** none from any layer — 0 of 40 assets declare a non-`bg_*` dependency. L0's inputs are
external (corpus, ephemeris, native rulings), which is why it is the only layer whose Part 2 has no
consumed-contract table with declared uses.

### 2.4 · Jyotish coverage owned

```
inherits:    Product §3, Data plane §5 (domain obligations)
measured_by: per obligation, one of the five states — applied / inapplicable-with-reason / unavailable / unqualified / unresolved; never a blank
traces_to:   0.1
```

L0 owns the **meaning half** of each row, never the chart half.

| data plane §5 obligation | L0's half | state |
|---|---|---|
| Graha contextual roles | role vocabulary: natural, functional, lordship, kāraka kept distinct | **applied** (77 kāraka + 11 planet rows) |
| Rāśi / bhāva / lord / kāraka | reference frames and significator vocabulary | **applied** (12 sign + 12 house rows) |
| Bala / dignity / avasthā | dignity reference and its units | **applied** (151 rows) |
| Sambandha | typed relation vocabulary, aspect school and orb | **applied** (13 aspect-type rows) |
| Bhāvat Bhāvam | the derived-house doctrine and its limits | **unqualified** — the concept resolves in the ontology; no L0 rule row states its prerequisites or exceptions |
| Varga and reference perspectives | varga method identity and domain | **applied** (30 varga rows) |
| Yoga / doṣa / bhaṅga | catalogue definitions, participants, cancellation conditions | **applied**, with an **unqualified subset**: 53 of 79 doṣa rows cite a placeholder |
| Nakshatra / KP | pada relationships, sub-lord division | **applied** (2,857 nakshatra + 249 KP rows) |
| Present interval (P24) | no L0 half | **inapplicable with reason** — the interval set is L3's and its expression L4's; L0 supplies only the clock vocabulary already counted under Kāla |
| Kāla | transit rule vocabulary, arcs, calendar substrate | **applied** (76 + 33,933 + 31,081) |
| Praśna / Muhūrta / calendar | method eligibility and constraint vocabulary | **applied** (lattice 173,219; praśna methods 41) |
| Āyurdāya and constitution | method and school identity, required inputs, cancellations | **unresolved** — **1** ontology concept exists and **0** rules qualify a method. V12 and P23 depend on this and it is the thinnest coverage L0 has. |
| Voluntary practice and wider tradition | attributed practice, scope, burden, evidence class | **applied** (341 rows), provenance PARTIAL (289 unresolved ids) |

### 2.6 · Vocabulary conformance — **L0 owns the set**

```
inherits:    Data plane §4.1 (six rules, each with a detector)
measured_by: per rule — uniqueness and alias census over brahma_ontology · independent-map candidates by grep over platform/python-sidecar/brahmagyan · parity-test presence by test-file listing · interface-parameter census NOT RUN
traces_to:   0.2
```

This section **inverts** for L0: it does not conform to the vocabulary, it *is* the vocabulary.

| §4.1 rule | state | measured |
|---|---|---|
| 1 · one canonical id, one closed alias set per thing | **FAIL on the alias half only** (corrected 2026-09-26) | identity half: **PASSES under the authority's declared key** — 741 rows, 741 distinct `(entity_class, canonical_id)`, 0 duplicates, constraint `brahma_ontology_canonical_unique`. The across-classes detector this document inherited from data plane §4.1 is wrong for a composite-key authority (C-8). Alias half: **FAIL** — `dosha` 79/79 with no alias set |
| 2 · the set is the only permitted surface; an unlisted name is raised | **PARTIAL** | `resolve_entity` exists and resolves by name and synonym; for the 11 duplicated ids it returns two rows, which is a resolution that has not resolved |
| 3 · resolution one-directional, normalisation declared once | **FAIL** | the 289 unresolved remedy ids differ from resolving ones only by case (`BPHS` vs `bphs`, `Phaladeepika` vs `phaladeepika`) — normalisation is not declared at the authority |
| 4 · code-side snapshots generated, pinned, parity-tested | **PARTIAL** | parity-style tests exist (10 vocabulary/parity test files, including `test_event_classes_parity.py`, `test_domain_vocabulary.py`); whether *every* snapshot has one is **NOT MEASURED** |
| 5 · external inputs typed to the set | **NOT MEASURED** this pass | the census the rule demands (per interface parameter: enum / resolver-validated / free string) was not run; the previous instance's figure is deliberately not carried forward |
| 6 · independent maps counted, permitted count one per class | **NO DETECTOR** | 6 candidate sites in `brahmagyan/` alone carry a literal graha name set; the census detector rule 6 requires does not exist |

**Sixteen classes confirmed** and they are exactly the sixteen §4.1 names: planet 11 · sign 12 · house 12 ·
nakshatra 27 · varga 30 · karaka 77 · aspect_type 13 · upagraha 11 · yoga 233 · dosha 79 · dasha_system 20 ·
domain 45 · concept 136 · remedy_type 12 · text 15 · school 8.

### 2.7 · Source carriage and reproduction

```
inherits:    Product §11 (L0 source-and-domain fidelity), Data plane §12.2 (Source carriage and reproduction)
measured_by: the three checks below, per owned obligation; PASS / FAIL / PARTIAL / NO DETECTOR
traces_to:   0.1
```

Carriage is L0's half of the question; the doctrinal verdict is formed above the plane (ruling 11).

| check | applies to | state |
|---|---|---|
| **a · source correspondence** — the encoded restatement against the passage it cites | bg_rules (3,002), bg_yogas (233), bg_doshas (79), bg_remedies (341) | **NO DETECTOR.** Nothing compares an encoding to its cited passage. The 53 placeholder citations are what a detector would surface first. This is L0's single largest gap, because a corrupted copy here is invisible at every later layer. |
| **b · witness carriage** — two witnesses agree, or the disagreement is carried unresolved | bg_concordance (721 attributions), bg_rules | **PARTIAL.** Attributions are stored; no detector proves a disagreement is carried rather than silently settled. |
| **c · independent re-derivation** — a classical quantity computed a second way | bg_ephemeris, bg_sky_calendar, bg_muhurta_lattice, bg_gochara_arcs | **NO DETECTOR at L0.** The two-pass verification that exists lives on L1 `chart_facts`, not on L0's computed substrate. |

`NO DETECTOR` is never a pass. Three of three checks are gaps; packets W-L0-3 and W-L0-4 close a and c.

### 2.5 · Edges and order

```
inherits:    Data plane §3.2; the registry DAG
measured_by: topological read of live depends_on over the 40 bg_* rows; cycle check; cross-layer gate state
traces_to:   0.3
```

- **24 roots** (no dependencies), **16 with intra-L0 edges**, **0 with edges outside L0**. The layer is a
  closed root: it is depended upon, and depends on nothing in the plane.
- **No cycles** — a DAG two levels deep at most.
- **Edge type:** every outbound edge is edge 1 (definition) or edge 3 (serving-context). L0 has no
  computational edge inbound, which is what makes it rebuildable without any chart.
- **Cross-layer gate state:** 0 of 40 frozen; no L0 asset has been certified, so no gate has been
  evaluated under any definition revision. Nothing to carry or invalidate.

---

## Part 3 · THE DELTA

```
inherits:    —
measured_by: 1.5's shortfall, itemised
traces_to:   0.2
```

### 3.1 · Per obligation

Ten obligations exist; L0 is scored on the four its 0.2 names. Domain correctness is excluded by ruling
11 — do not correct this count upward.

| obligation | where L0 stands, measured | what closes the gap |
|---|---|---|
| **Source and domain fidelity** | 3,002 rules all carry a verse reference across 14 texts; 721 attributions stored. Against that: 53 doṣa rows cite a placeholder, 289 remedy source ids do not resolve, and **no detector compares any encoding to its cited passage**. | W-L0-3 (source-correspondence detector) · W-L0-5 (placeholder and normalisation repair) |
| **Computational correctness** | 5 computed assets, 1,173,317 rows between them, all at or above floor except none; **no independent re-derivation detector at L0** | W-L0-4 (re-derivation check on ephemeris and calendar) |
| **Delivery fidelity** | 46 capability modules, 39 declared descriptors, **0 declaring a density contract**; presentation parity **never run** | W-L0-8 (density declaration + parity run) |
| **Operational honesty** | 38/40 count_sql, 37/40 integrity checks, 1 DRAFT, tracker reports 0/320 gates and 40/40 NO_BRIEF — the status surface is honest about being empty | W-L0-2 (first briefs) closes it by making the zeros non-zero |

### 3.2 · Per asset — disposition

Eight dispositions available. **No asset receives R**: the reference-layer rule forbids retiring for lack
of a reader, and no asset has failed fidelity outright.

| disposition | assets | evidence |
|---|---|---|
| **P** preserve | 29 assets — the reference, calendar, ephemeris, medical, vastu, KP, kota, latta, vidhi, cohort, prior, transit, arc and text assets | at or above floor, integrity present, no fidelity failure measured |
| **E** enrich/correct | **bg_ontology** (unique key + doṣa alias sets), **bg_remedies** (normalise 289 ids), **bg_doshas** (replace 53 placeholder citations), **bg_rules** (concept linkage beyond 17/3,002) | 1.2 and 1.3 measurements |
| **Q** qualify/limit authority | **bg_sarvatobhadra_grid** — keep the abstention and keep it visible; **bg_vidhi_floors** — DRAFT status is the honest authority limit until it is promoted | ADJUDICATION-11; catalog_status |
| **I** integrate | **bg_prashna_rules** (declare its table set), **bg_text_index** (its 361 is a distinct-tag measure sharing a table with bg_texts — the pair needs one declared grain) | 1.1 findings 2 and 3 |
| **U** unresolved use | the 21 assets with no declared downstream consumer | 1.4: the registry understates consumption, so "no consumer" is an unmeasured state, not a verdict |
| **C** consolidation candidate | **bg_class_priors / bg_class_lifetime_counts** — two assets, one table, two partitions | 1.1 finding 3; trace callers before any successor is chosen |
| **H** historical/restricted | none | — |
| **R** retire | **none** | forbidden here without failed fidelity |

### 3.3 · Per asset — what it must add

| asset | must add |
|---|---|
| bg_ontology | a unique canonical id (or a declared class-qualified key); an alias set for all 79 doṣa rows; the normalisation rule declared at the authority, not at consumers |
| bg_rules | `yoga_canonical_id` (or an equivalent concept link) beyond 17 rows; an executable-scope field, which DP02 requires and no column carries |
| bg_doshas | a real citation for the 53 placeholder rows, or an explicit `unattributed` state that does not read as a citation |
| bg_remedies | normalised `source_canonical_id`s; the two missing texts added to the `text` class; `classical_tradition` made an explicit unattributed state |
| bg_prashna_rules | a declared target-table set |
| bg_concordance | a detector that a recorded disagreement is carried, not flattened |
| the 5 computed assets | a second-derivation check with a declared tolerance |
| all 46 served modules | a `density_contract` declaration |
| all 40 | a tier-4 brief (none exists) and the 8-gate map filled |

### 3.4 · Intra-layer interplay

The matrix is thin by design — 24 of 40 assets are roots — and its value sits in three joins, all named
in 1.3: **catalogue → identity** (real, keyed on a non-unique id), **rules → concepts** (17/3,002), and
**remedies → source identity** (52/341). The boundary with L1 is the DP01/DP02 handoff, where the
registry declares 5 Gaṇita edges while code reads L0 tables in dozens of files. **This is where L0's
synergistic term is found missing**, and it is the same three joins that Part 4 sequences first.

---

## Part 4 · STRATEGY

### 4.1 · Order

```
inherits:    2.5
measured_by: the DAG; the three-way baseline per asset (deployed / current code / target)
traces_to:   0.2
```

Identity first, because every other seam resolves through it:

1. **bg_ontology** — the unique key and the doṣa alias sets. Nothing else in L0 is worth measuring while
   its identity authority can return two rows for one id.
2. **The three seams** — catalogue→identity (verify after 1), rules→concepts, remedies→source identity.
3. **The carriage detectors** — source correspondence first (it protects every later layer), then
   independent re-derivation on the computed five.
4. **The served surface** — density declarations and the first parity run.
5. **Briefs and gates** — 40 briefs, 320 gates, in dependency order within each depth level.

**Three-way baseline:** `deployed` = the production figures in 1.1, read 2026-09-26. `current code` =
identical for L0 — no unmerged branch carries an L0 writer change (the L0 writers are untouched on every
live head checked). `target` = Part 3. So for L0 today, **delta = target − current code**, and
**risk = current code − deployed = 0**. That zero is worth stating: L0 is the one layer where nothing is
in flight, which is why it is the right layer to close first.

### 4.2 · Work packets

```
inherits:    Data plane §13.1, §13.3 item 8
measured_by: each packet's proof — a detector that fails when the packet has not landed
traces_to:   3.x
```

| packet | closes | proof (fails if not landed) |
|---|---|---|
| **W-L0-1** fidelity census for the 34 unmeasured assets | 1.2 | a per-asset fidelity record exists for 40/40, each naming its query |
| **W-L0-2** first tier-4 briefs | 3.1 operational honesty | tracker NO_BRIEF drops below 40; the 8-gate map is filled per brief |
| **W-L0-3** source-correspondence detector | 2.7a, 3.1 | the detector runs over bg_rules/bg_yogas/bg_doshas/bg_remedies and reports a non-zero mismatch count it can also report as zero |
| **W-L0-4** independent re-derivation on the computed five | 2.7c, 3.1 | a second derivation with a declared tolerance, and a seeded mismatch that the check catches |
| **W-L0-5** identity and normalisation repair | 1.2, 1.3, 2.6 rules 1 and 3 | `count(*) = count(DISTINCT canonical_id)` on brahma_ontology; 79/79 doṣa alias sets; remedy unresolved count 289 → 0 |
| **W-L0-6** the parihara −9 | 1.1 finding 1 | the cause is named and either the rows or the floor is corrected; `live ≥ floor` for all 40 |
| **W-L0-7** L0 ablation harness (cross-layer flavour only) | 1.3, 1.5 | a seam can be broken and the served reading measured; the synergy term stops being an absent instrument |
| **W-L0-8** density declarations and first parity run | 2.2, 3.1 delivery | `density_contract` on every module that paginates or facets; one parity run recorded |
| **W-L0-9** rule 5 and rule 6 censuses | 2.6 | per-parameter typing census and per-class independent-map census exist and can fail |

### 4.3 · Generation, invalidation, rollback

```
inherits:    Data plane §11, §4.4, DP16
measured_by: the generation pins each consumer records; the invalidation path exercised, not described
traces_to:   2.1
```

- L0 revisions classify per §4.4: display/alias correction · identity mapping · semantic rule change ·
  constant/method change · provenance correction · evaluation qualification change.
- **An alias addition must not recompute a chart.** The doṣa alias work (W-L0-5) is therefore an
  alias-class change — additive, no downstream rebuild. **Adding a unique key is not**: it may split one
  id into two, which is an identity-mapping change with a real invalidation path.
- **Invalidation path: described, not exercised.** No L0 change has been pushed through consumer
  invalidation and measured at the consumer. Recorded as an unmet acceptance test, not as a working path.
- Rollback for the 24 root assets is a re-seed; for the 16 with intra-layer edges it is a re-seed in
  topological order. No chart is involved either way.

### 4.4 · What each asset brief inherits from this instance

```
inherits:    Product §16; Data plane §13.3 (asset brief sentence)
measured_by: derivability — a brief author fills these from this instance alone
traces_to:   0.1
```

Every tier-4 L0 brief receives, without inventing any of it: its P-needs and V-journeys (0.1, narrowed) ·
the four obligations it is scored on (0.2) · its correctness rules and switch behaviour (2.1 — for L0,
structurally satisfied) · its presentation fields (2.2) · its produced contract and declared use (2.3) ·
its coverage obligations and states (2.4) · its position in the order and its three-way baseline (4.1) ·
its disposition and must-add list (3.2, 3.3) · its fidelity, synergistic and cross-layer terms (1.2–1.4) ·
its role (L0 has no manifestation or temporal role — it supplies the vocabulary both rest on) · **its
preserved kernel** — for most L0 assets the seeded rows and their citations · **the Jyotish concepts it
touches with the carriage check each invites** (2.7's a/b/c menu).

A brief that must invent any of these has found a defect in this instance.

---

## Part 5 · EVALUATION AND CERTIFICATION

### 5.1 · The score

```
inherits:    Product §14, §14.1; Data plane §12.2
measured_by: fidelity per asset; cross-layer ablation at the consumer
traces_to:   0.2
```

For L0 the individual flavour is **fidelity** (1.2) and the **cross-layer** flavour is the only ablation
that runs — to verify consumers use the knowledge correctly, never to judge whether an asset earns its
place. The synergistic flavour is defined but has no harness (W-L0-7). No ablation of any flavour has
been run against L0 to date.

### 5.2 · What is certified, and what is merely checked

```
inherits:    Product §14; CLAUDE.md §N.6-N.8
measured_by: asset_certs.jsonl for gates (read 2026-09-26: 1 line, the _schema line; 0 certification records) · the tracker's marker scan for shape
traces_to:   4.4
```

**Eight gates × 40 assets = 320. Certified: 0.** The ledger holds its schema line and nothing else,
which agrees with the tracker's `gates certified 0/320`.

| gate | this layer's reading |
|---|---|
| **Ldgr** derivation ledger | L0 is the root: its rows cite *sources*, not upstream `fact_id`s. The gate reads as citation-presence here, and 53 doṣa rows fail it. |
| **Idem** idempotency | L0 is the one layer permitted `ON CONFLICT` upsert (§N.3); re-seed must replace, not accrete |
| **Earn** earned signal | every count_sql and integrity_check_sql must be able to fail; 37/40 carry one |
| **Null** honest null | the abstaining grid and the DRAFT floor asset are the model cases |
| **Vocab** vocabulary conformance | **inverts for L0** — it owns the set; §2.6 is its evidence, and rules 1 and 3 currently FAIL |
| **Carr** source carriage | §2.7's a/b/c; all three are NO DETECTOR or PARTIAL today |
| **Narr** narration fidelity | conditional — applies to the assets whose rows carry prose (`formation_text`, `effects_text`) |
| **Dens** serving density | conditional on reaching a served surface: 46 modules do, and 0 declare a density contract |

### 5.3 · Certification is per criterion, not per definition revision

```
inherits:    the t3 lesson — 90 assets' freezes evaporated when a campaign definition re-froze
measured_by: the certification record itself
traces_to:   —
```

One record per (asset, criterion), in the shape `asset_certs.jsonl`'s `_schema` line already uses:
`asset · criterion · criterion_version · detector · evidence · verdict · verified_by · verified_on`.
A scale revision then costs one re-test of the changed criterion, not a re-freeze of the layer. L0 has
nothing to lose to this yet — 0 certified — which makes it the cheapest layer on which to get the
discipline right first.

### 5.4 · Acceptance of this instance

```
inherits:    template §5.4
measured_by: the six acceptance tests, each stated met or unmet
traces_to:   —
```

| test | state |
|---|---|
| 1 · Derivability — a fresh reader derives one asset brief with zero inventions | **UNMET / untested.** No brief has been attempted against this instance. |
| 2 · Alignment — every section names its `traces_to:` | **MET.** Two candidate sections were struck (0.4). |
| 3 · Measured, not inherited — every figure names a re-runnable `measured_by:` | **MET**, with the honest exception of the fields marked NOT MEASURED (2.6 rules 4-5, 34 assets in 1.2), which claim nothing. |
| 4 · Presentation parity holds for the served surface | **UNMET** — never run (2.2). |
| 5 · The 8-gate map exists | **MET at layer level** (5.2); **UNMET per asset** — no brief exists to carry it. |
| 6 · Independent review, fresh context, findings folded | **UNMET.** |

**No verdict is stamped here.** Under the template, an instance carrying a verdict its own author
assigned with acceptance tests pending is unreviewed whatever the verdict says. Ruling 9 permits the
native, a reviewer or a session to sign — *after* a review has happened. This instance is
`DRAFT_PENDING_ACCEPTANCE` until then.

---

## Part 6 · Corrections with gates

The template's §5.2 tells an instance to "report unfillable rows in §7", but the template defines no §6
or §7. Recorded here rather than silently renumbered.

| # | correction | about the DOCUMENT or the LAYER | gate it blocks |
|---|---|---|---|
| C-1 | 34 assets have no fidelity measurement | document (this instance must carry it) | the first asset brief |
| C-2 | 2.6 rules 4 and 5 not measured | document | layer certification |
| C-3 | `bg_ontology` key not unique; doṣa alias sets empty | **layer** — correctly recorded here | W-L0-5, and every Vocab gate |
| C-4 | no source-correspondence detector | **layer** | every Carr gate |
| C-5 | parihara −9 cause not established | **layer** | W-L0-6 |
| C-6 | parity never run; invalidation path never exercised | **layer** | Dens and the first consumer cutover |
| C-7 | template defines no §6/§7 though §5.2 cites §7; §2.5 is ordered after §2.7 | **template** (tier 3 is sealed — this is a reopen request, not an edit) | the L1 instance, which would inherit both |

| C-8 | data plane §4.1 rule 1's detector (`count(DISTINCT canonical_id)` across classes) reports FAIL on data that satisfies its own `UNIQUE (entity_class, canonical_id)` constraint; this document inherited the error into 1.2, 1.3 and 2.6 | **sealed data plane** (tier 2) — the three rows here are corrected; the parent's detector is not mine to edit | every `Vocab` gate on every layer, and the L1 instance |
| C-9 | row 13 of the asset-brief inheritance (the concepts an asset touches, each with the carriage check it invites) **cannot be filled from this instance** — §2.7 names the three checks at layer scope and assigns none per asset. Pilot 1 had to choose D1 itself | document (this instance) | the next asset brief |
| C-10 | §1.1 models one `target_table` per asset and cannot express a **shared table with several producers**. `brahma_ontology` has four (`l0_ontology.py` 414 rows / 14 classes, plus `l0_yogas.py`, `l0_doshas.py`, `l0_dasha_systems.py` supplying 327 more), and `bg_ontology`'s `count_sql` credits it with all 741 | document (this instance) + layer | the first asset certification |

Per the template's rule, a finding about the document is fixed in the document and never deferred: C-1
and C-2 are the two that make this instance incomplete, and both are measurement passes, not decisions.
C-8's three inherited rows are corrected above; the parent's detector is a reopen request, recorded.

## Pilot findings — 5 of 5 complete

`bg_ontology` (`l0_assets/BG_ONTOLOGY_ELEVATION_BRIEF_v1_0.md`), against asset template v2.0:

- **Derivability: 12 of 13 inheritance rows filled without invention.** The thirteenth is C-9.
- **The pilot corrected a finding in this document rather than inheriting it** — which is what a pilot is
  for. The identity FAIL was a wrong detector, not wrong data.
- **10 gap rows and 6 opportunity rows registered** in `asset_gaps.jsonl`; tracker reads
  `GAPS_REGISTERED=1 · open gaps 10 · open opportunities 6`, and the opportunities correctly do not
  withhold elevation.
- **The new §1.1 width census earned its place immediately:** the `text` class and the corpus both hold 15
  members and differ by **3 in each direction**. A row count reads 15 = 15 and sees nothing.
- **The new §1.2 reachability census earned its place immediately:** of 741 built rows, **233 are
  unreachable** through `list_entities`, which explains the emptiness with a statement measurably untrue
  (`entity_class='yoga'` "has no dedicated top-level class"), and 79 more are reachable but undeclared.
  58% reachable-and-declared.
- **The §9 opportunity register found the asset's real architectural question**, which no gate would have
  asked: the key contract (composite vs simple) is a native decision worth taking once, and it dissolves
  three registered gaps.

### Pilots 2–5, and what the five together establish

| pilot | asset | kind it tested | derivability | headline finding |
|---|---|---|---|---|
| 2 | `bg_rules` | rule corpus | 12/13 | **the extractor's yield varies 29×** across texts — saravali 2.34 rules/chunk, BPHS 0.08, tājaka-nīlakaṇṭhī 0.00 from 290 chunks. At saravali's rate BPHS alone would yield ~3,400 rules, more than the whole corpus holds. Also: `confidence` has **3 distinct values** and **equals `quality_score` on 3,002/3,002 rows** — two columns, one signal, 92% of it the value 1.000 |
| 3 | `bg_ephemeris` | computed substrate | 12/13 | **the grid is provably complete and the vocabulary provably wrong**: 91,676 days × 9 bodies = 825,084 rows exactly (251 years, 61 leap days — no missing cell), while `body` is stored `'Jupiter'` against the ontology's `jupiter`, and the asset's own integrity check **pins the capitalised form** |
| 4 | `bg_panchanga` | service, no table | 12/13 | **the template disposes of a table-less asset without inventing a row** — four registry absences and six gate N/As, each with a reason. And `rows_written = 0` reads identically for a healthy service and a writer that produced nothing: the build-state surface cannot tell them apart |
| 5 | `bg_sarvatobhadra_grid` | empty by design | **13/13** | **abstention is expressible as fidelity.** Every status surface tells the same true story (floor 0, rows 0, consumer discloses its fallback). The only brief needing no invention — and the case that proves `N/A — inapplicable` and `NO_DETECTOR` are different verdicts |

**Template results (v2.0 held; four refinements, none structural):**

1. **C-9 confirmed four times.** Row 13's carriage check had to be chosen by the author in pilots 1–4. The
   instance must assign a/b/c per asset, or the template must say the author chooses and records why.
2. **§1's storage bullets assume a table.** A service filled them with four honest N/As, which worked, but
   the template should say so rather than leaving each author to decide.
3. **`N/A — inapplicable` vs `NO_DETECTOR` is load-bearing** and the template already separates them; pilot
   5 is the case that shows why (no claim vs an unverified claim).
4. **The §9 admission rule held**: every one of the 18 opportunities carries a measurement-after. Three
   asked the architectural question no gate would have asked — the key contract, the ephemeris grain, and
   a service's health signal.

**Ledger after five pilots:** 30 gap rows, 18 opportunity rows, 5 assets at `GAPS_REGISTERED`, 35 at
`NO_BRIEF`, 0/320 gates certified. The opportunities correctly do not withhold elevation.

**Three findings are layer-scope, not asset-scope, and belong to packets rather than briefs:** D1 source
correspondence (absent, and pilot 2 is where it matters most), the undeclared normalisation at the
authority (pilots 1, 2 and 3 all hit it), and the build-cost instrument (`rows_written = 0` on three of
five assets measured).
