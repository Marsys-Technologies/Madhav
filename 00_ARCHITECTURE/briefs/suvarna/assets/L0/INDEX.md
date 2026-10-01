---
artifact: ASSET_ELEVATION_BRIEF_INDEX
layer: L0 Brahmagyan (bg_*)
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L0 (briefs, dispositions, designs)
base_commit: "main 0250cbade"
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L0/L0_LAYER_INSTANCE_v3_1.md (3.1-rev1, PROVISIONAL)"
briefs: 40 (one per L0 asset, `<asset_id>.md` in this directory)
---

# L0 asset briefs — layer index (provisional)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Every figure is from the repository or the saved census (B.10). Nothing in this directory certifies a gate or approves a disposition: dispositions are proposals under Track A brief §10, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 1 · What this index rests on, and what is stale

- **Census used:** saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.
- **Layer instance:** `L0_LAYER_INSTANCE_v3_1.md` (3.1-rev1) is the draft these briefs continue; its §4.4 rows were filled from it, its dispositions (§3.2) re-examined (see §6).
- **Gap ids** are ledger `asset_gaps.jsonl` ids from the census checkout (`/Users/Dev/suvarna-census/00_ARCHITECTURE/control/asset_gaps.jsonl` @ 2a78ec64d: 290 L0 rows, hand-authored for five pilots, inspector-emitted for the rest); that ledger is **not on main**. Several ledger rows are older than the saved census (class **stale** in the briefs).
- **Re-measure:** not possible in this lane (no DB). The repo's own rollup code (`asset_census.py` `rollup_asset`, REGISTRY_REVISION 6) was run **offline over the saved measurements** (output `/Users/Dev/suvarna-evidence/A_L0/rollup_saved_L0.json`); that mixes old measurements with new rules and is labelled so everywhere. A real re-measure by the current inspector is expected before any verdict is read.

**Criteria whose definition changed on main since the saved run (gates affected: Build, Dens, Idem; Null and Narr did not exist):**

- `Build.dag`: rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle)
- `Build.target`: rev 1 -> 2 (declared service with no target_table reads PASS by declaration)
- `Idem.pattern`: rev 1 -> 2 (relative imports resolve; update-only reading)
- `Dens.served`: rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count)
- `Narr.agree/checkable/fidelity_test/lint` and `Null.schema_default/blank_rows` (new at rev 5): not in the saved census; the declarations file 1.6.0 gives `prose_fields` for 5 of 40 L0 assets (3 `[]`, 2 non-empty), 35 are `null` so those cells read NO_DETECTOR.
- `NA_RULE_DECISIONS` is empty on main (`asset_census.py:243`): until N-22 rules are declared, a measured N/A reads NO_DETECTOR in the rollup, so the offline rollup below is harsher than the draft's N/A-aware Appendix B.
- Registry moved since the census: migration 1210 (12 direct `depends_on` edges, Track I) deliberately excludes L0 bedrock edges; the DAG detector exempts L0 bedrock reads as `bedrock_exempt` (SS 2026-10-01, provisional pending J1). Live production was not re-read: counts and floors are the saved ones.

## 2 · Rollup counts

**Dispositions proposed (40):** enrich 5, integrate 1, keep 32, qualify 2; consolidate 0, historical 0, retire 0, unresolved 0. (Draft v3.1 §3.2: P 30, E 4, Q 2, I 2, C 2 — see §6 for the four changes.)

**Gap rows across the 40 briefs (332 rows; duplicate ledger rows folded under R81 are listed separately in the ledger and counted once per id here):** real 40 · Dens rev-1 reading with applicability open 26 · real-or-SS-question 5 · detector 147 · stale 27 · history 13 · information 55 · opportunity 18 · other 1.

**Saved census cells over the layer (777):** FAIL 42 · PARTIAL 24 · NO_DETECTOR 123 · ERRORED 0 · PASS 440 · N/A 68 · NOT_GENERIC 80. FAIL by criterion: Dens.served 23 · Build.completion 14 · Build.registered 2 · Build.exercised 1 · Count.floor 1 · Vocab.alias 1.

**Nine-gate cells, offline rollup of the saved measurements under main's rules (assets of 40; not a re-measure, not a certification):**

| gate | Ldgr | Idem | Earn | Null | Vocab | Carr | Narr | Dens | Build |
|---|---|---|---|---|---|---|---|---|---|
| rollup | NO_DETECTOR 16 · PASS 24 | NO_DETECTOR 4 · PARTIAL 1 · PASS 35 | NO_DETECTOR 40 | NO_DETECTOR 40 | FAIL 1 · NO_DETECTOR 39 | NO_DETECTOR 40 | NO_DETECTOR 40 | FAIL 23 · NO_DETECTOR 17 | FAIL 16 · NO_DETECTOR 12 · PARTIAL 10 · PASS 2 |

The draft's N/A-aware reading (layer instance Appendix B) differs only because it lets a measured N/A drop out: Vocab PASS 35 · FAIL 1 · NO_DETECTOR 1 · no reading 3; Idem PASS 35 · PARTIAL 1 · N/A 4; Dens FAIL 23 · NO_DETECTOR 1 · N/A 16; Build FAIL 16 · PARTIAL 11 · PASS 13; Ldgr PASS 24 · no reading 16.

## 3 · Assets × disposition × gaps × fix class × rebuild

Columns: **real** = a shortfall in rows/writer/registry/served surface; **Dens/SSq** = Dens rev-1 FAILs whose applicability is open (CF-04) plus items framed as an SS question; **detector** = NO_DETECTOR or definition-open; **other** = stale + history + information + opportunity; **rebuild** y = a fix needs a production rebuild/dispatch, cond = only under one option, n = none.

| asset | disposition | real | Dens/SSq | detector | other | fix class | rebuild | shared fixes |
|---|---|---:|---:|---:|---:|---|---|---|
| [bg_class_lifetime_counts](bg_class_lifetime_counts.md) | keep (P) | 0 | 1 | 4 | 3 | detector/tooling; registry/declaration; served surface (TS) | n | CF-04, CF-05, CF-06, CF-07, CF-08, CF-10, CF-12 |
| [bg_class_priors](bg_class_priors.md) | keep (P) | 0 | 1 | 4 | 2 | registry/declaration; served surface (TS) | n | CF-04, CF-05, CF-06, CF-07, CF-08, CF-12 |
| [bg_cohort](bg_cohort.md) | keep (P) | 1 | 0 | 3 | 2 | detector/tooling; registry/declaration; writer code | cond | CF-02, CF-05, CF-06, CF-07, CF-10 |
| [bg_compendium_index](bg_compendium_index.md) | keep (P) | 0 | 1 | 3 | 4 | detector/tooling; registry/declaration; served surface (TS); writer code | n | CF-04, CF-05, CF-07, CF-08, CF-10 |
| [bg_concordance](bg_concordance.md) | keep (P) | 0 | 0 | 4 | 2 | data (output change); detector/tooling; registry/declaration; writer code | n | CF-05, CF-06, CF-07, CF-08 |
| [bg_dasha_systems](bg_dasha_systems.md) | keep (P) | 0 | 1 | 3 | 3 | detector/tooling; registry/declaration; served surface (TS) | n | CF-04, CF-05, CF-06, CF-07, CF-10 |
| [bg_dignity_reference](bg_dignity_reference.md) | keep (P) | 0 | 1 | 3 | 1 | detector/tooling; registry/declaration | n | CF-04, CF-05, CF-06, CF-07, CF-12 |
| [bg_doshas](bg_doshas.md) | enrich (E) | 1 | 2 | 2 | 3 | data (output change); detector/tooling; served surface (TS); writer code | y | CF-04, CF-05, CF-07, CF-09, CF-10, CF-11 |
| [bg_ephemeris](bg_ephemeris.md) | keep (P) | 3 | 2 | 5 | 7 | detector/tooling; registry/declaration; served surface (TS); writer code | cond | CF-01, CF-04, CF-05, CF-06, CF-07, CF-08, CF-09, CF-12 |
| [bg_ephemeris_engine](bg_ephemeris_engine.md) | keep (P) | 0 | 1 | 5 | 1 | detector/tooling; registry/declaration; served surface (TS) | n | CF-03, CF-04, CF-05, CF-06, CF-07 |
| [bg_formula_constants](bg_formula_constants.md) | keep (P) | 1 | 1 | 4 | 3 | detector/tooling; registry/declaration; served surface (TS); writer code | n | CF-02, CF-04, CF-05, CF-06, CF-07, CF-08, CF-10, CF-12 |
| [bg_ghatana](bg_ghatana.md) | keep (P) | 0 | 0 | 4 | 2 | detector/tooling; registry/declaration | n | CF-05, CF-06, CF-07, CF-08, CF-12 |
| [bg_gochara_arcs](bg_gochara_arcs.md) | keep (P) | 0 | 0 | 4 | 3 | detector/tooling; registry/declaration | n | CF-05, CF-06, CF-07, CF-08, CF-10 |
| [bg_gochara_citation_resolution](bg_gochara_citation_resolution.md) | keep (P) | 1 | 0 | 3 | 1 | detector/tooling; registry/declaration; served surface (TS); writer code | cond | CF-04, CF-05, CF-06, CF-07 |
| [bg_kota_chakra_rings](bg_kota_chakra_rings.md) | keep (P) | 0 | 0 | 4 | 3 | detector/tooling; registry/declaration | n | CF-05, CF-06, CF-07, CF-08, CF-12 |
| [bg_kp_sublord_division](bg_kp_sublord_division.md) | keep (P) | 0 | 0 | 3 | 3 | detector/tooling; registry/declaration | n | CF-04, CF-05, CF-06, CF-07, CF-10 |
| [bg_medical_mappings](bg_medical_mappings.md) | keep (P) | 1 | 1 | 3 | 2 | detector/tooling; registry/declaration; served surface (TS); writer code | n | CF-02, CF-04, CF-05, CF-06, CF-07, CF-12 |
| [bg_muhurta_lattice](bg_muhurta_lattice.md) | keep (P) | 1 | 1 | 3 | 1 | detector/tooling; registry/declaration; served surface (TS); writer code | n | CF-01, CF-03, CF-04, CF-05, CF-06, CF-07, CF-12 |
| [bg_nakshatra](bg_nakshatra.md) | keep (P) | 0 | 0 | 4 | 3 | detector/tooling; registry/declaration | cond | CF-05, CF-06, CF-07, CF-08, CF-09 |
| [bg_nakshatra_medical](bg_nakshatra_medical.md) | keep (P) | 1 | 1 | 3 | 2 | detector/tooling; registry/declaration; served surface (TS) | y | CF-02, CF-03, CF-04, CF-05, CF-06, CF-07, CF-12 |
| [bg_ontology](bg_ontology.md) | enrich (E) | 9 | 2 | 4 | 9 | data (output change); detector/tooling; registry/declaration; served surface (TS); writer code | y | CF-01, CF-02, CF-04, CF-05, CF-07, CF-09 |
| [bg_panchanga](bg_panchanga.md) | keep (P) | 1 | 1 | 8 | 4 | detector/tooling; registry/declaration; served surface (TS) | n | CF-03, CF-04, CF-05, CF-06, CF-07 |
| [bg_parihara_rules](bg_parihara_rules.md) | keep (P) | 2 | 1 | 3 | 3 | detector/tooling; registry/declaration; served surface (TS); writer code | n | CF-03, CF-04, CF-05, CF-06, CF-07, CF-10, CF-12 |
| [bg_phaladeepika_latta](bg_phaladeepika_latta.md) | keep (P) | 0 | 0 | 3 | 2 | detector/tooling; registry/declaration | n | CF-05, CF-06, CF-07, CF-12 |
| [bg_prashna_rules](bg_prashna_rules.md) | keep (P) | 0 | 0 | 4 | 2 | detector/tooling; registry/declaration | n | CF-02, CF-04, CF-05, CF-06, CF-07, CF-08, CF-12 |
| [bg_reference](bg_reference.md) | keep (P) | 1 | 0 | 3 | 3 | detector/tooling; registry/declaration; writer code | n | CF-01, CF-04, CF-05, CF-06, CF-07, CF-10, CF-12 |
| [bg_remedies](bg_remedies.md) | enrich (E) | 2 | 2 | 2 | 3 | data (output change); detector/tooling; served surface (TS); writer code | y | CF-04, CF-05, CF-07, CF-09, CF-10, CF-11 |
| [bg_rules](bg_rules.md) | enrich (E) | 5 | 2 | 6 | 8 | data (output change); detector/tooling; registry/declaration; served surface (TS); writer code | y | CF-05, CF-06, CF-07, CF-08, CF-09 |
| [bg_sarvatobhadra_grid](bg_sarvatobhadra_grid.md) | qualify (Q) | 1 | 0 | 7 | 5 | detector/tooling; registry/declaration | n | CF-05, CF-06, CF-10 |
| [bg_sign_medical](bg_sign_medical.md) | keep (P) | 2 | 1 | 3 | 2 | detector/tooling; registry/declaration; served surface (TS) | y | CF-02, CF-04, CF-05, CF-06, CF-07, CF-12 |
| [bg_sky_calendar](bg_sky_calendar.md) | keep (P) | 1 | 1 | 3 | 1 | detector/tooling; registry/declaration; served surface (TS); writer code | n | CF-01, CF-03, CF-04, CF-05, CF-06, CF-07, CF-12 |
| [bg_text_index](bg_text_index.md) | integrate (I) | 1 | 1 | 4 | 2 | detector/tooling; registry/declaration; served surface (TS); writer code | n | CF-01, CF-04, CF-05, CF-06, CF-07, CF-08 |
| [bg_texts](bg_texts.md) | keep (P) | 1 | 1 | 3 | 2 | detector/tooling; registry/declaration; served surface (TS); writer code | n | CF-01, CF-04, CF-05, CF-06, CF-07 |
| [bg_transit_engine](bg_transit_engine.md) | keep (P) | 1 | 1 | 3 | 2 | detector/tooling; registry/declaration; served surface (TS) | y | CF-02, CF-03, CF-04, CF-05, CF-06, CF-07 |
| [bg_transit_rules](bg_transit_rules.md) | keep (P) | 2 | 1 | 3 | 2 | data (output change); detector/tooling; registry/declaration; served surface (TS); writer code | y | CF-02, CF-04, CF-05, CF-06, CF-07, CF-11 |
| [bg_vastu_directions](bg_vastu_directions.md) | keep (P) | 0 | 1 | 3 | 3 | detector/tooling; registry/declaration; served surface (TS) | n | CF-04, CF-05, CF-06, CF-07, CF-12 |
| [bg_vedha_malefic_scale](bg_vedha_malefic_scale.md) | keep (P) | 0 | 0 | 3 | 2 | detector/tooling; registry/declaration | n | CF-05, CF-06, CF-07, CF-12 |
| [bg_vidhi_floors](bg_vidhi_floors.md) | qualify (Q) | 0 | 0 | 5 | 2 | detector/tooling; registry/declaration | n | CF-05, CF-06, CF-07, CF-08, CF-10 |
| [bg_vidhi_primitives](bg_vidhi_primitives.md) | keep (P) | 1 | 0 | 4 | 1 | detector/tooling; registry/declaration; writer code | n | CF-01, CF-03, CF-05, CF-06, CF-07, CF-08 |
| [bg_yogas](bg_yogas.md) | enrich (E) | 0 | 2 | 2 | 5 | data (output change); detector/tooling; registry/declaration; served surface (TS) | y | CF-04, CF-05, CF-07, CF-09, CF-10, CF-11 |

**Rebuild needed (y):** 9 — bg_doshas, bg_nakshatra_medical, bg_ontology, bg_remedies, bg_rules, bg_sign_medical, bg_transit_engine, bg_transit_rules, bg_yogas. **Option-dependent (cond):** 4 — bg_cohort, bg_ephemeris, bg_gochara_citation_resolution, bg_nakshatra. All others: none.

## 4 · Cross-asset fixes, ordered by value for J1 (Tracks I and B)

Order rule: assets served × gate movement, then tier-independence and absence of a rebuild first (Track I can start tier-independent designs before J1: Track A §10). Each shared fix is designed once here; the per-asset brief states how it applies and adds the asset-specific parts.

### 1. CF-03 — Registry correction batch (one surgical migration + seed literals)

- **Why this rank:** smallest, tier-independent, no rebuild, one migration; removes the layer’s only Count FAIL and two Build.registered FAILs (expect the recorded R61 cascade).
- **Gate:** Count (information), Build.registered, Build.target/dag; **assets:** 4 certain + 3 optional — bg_parihara_rules (floor 449 → 440), bg_nakshatra_medical and bg_transit_engine (`has_writer` false → true), bg_panchanga (declare its ephemeris edge, ledger `bg_panchanga-G04`); optional floor refresh (information): bg_muhurta_lattice, bg_sky_calendar, bg_ontology
- **Evidence:** Migration 644 set the parihara floor to 449 over 61 + 329 + 59 rows; migration 703 (applied 2026-09-06) deleted 9 orphaned rows and re-pinned the integrity check but left the floor; live 60 + 329 + 51 = 440 (layer instance CH-04, Q-15). Code registers `bg_nakshatra_medical` (`bg_medical_mappings.py:25-27`) and `bg_transit_engine` (`bg_transit_rules.py:11-12`) while the registry says `has_writer = false` (census `Build.registered` FAIL ×2). Nikaṣa register R61: flipping `has_writer` to true opens a NEW measured gap (`Build.exercised`, writer never dispatched) until the id is dispatched in a run. Floors below live (+8,644 muhūrta lattice; +22 sky calendar; +4 ontology) are not failures (`Count.floor` PASS); CLAUDE.md §N.4 says a floor equals the achieved count after a build, so a refresh is cosmetic.
- **Design:** One migration, number = max+1 across every origin head and both migration directories at execution time (never trusted from this document; Suvarṇa migration range per Track E), `UPDATE asset_registry SET target_floor = 440 WHERE asset_id = 'bg_parihara_rules'` and `SET has_writer = true WHERE asset_id IN ('bg_nakshatra_medical','bg_transit_engine')`, each with an `AND <old value>` guard and an in-migration check, plus the same literals in `platform/scripts/seed/asset_registry_seed.ts`; verify by production structure, never by the runner’s report. The `bg_panchanga` edge is a `depends_on` change (DAG order and upstream hash move): Track I’s migration 1210 deliberately excluded L0 bedrock edges, so this one needs its own review.
- **Failing-first test and mutation:** Failing-first: after the migration `Count.floor` for `bg_parihara_rules` reads PASS and `Build.registered` PASS for the two ids; the cascade `Build.exercised` FAIL for the two ids is EXPECTED and recorded, not a regression. Mutation: restore the old floor → `Count.floor` FAIL again.
- **Blast radius:** Registry rows only. `has_writer = true` makes the two ids dispatchable in a layer-scope L0 plan (they ride sibling writers). No consumer reads `target_floor`.
- **Rebuild:** none for the floor and the has_writer flags. Clearing the cascade (`Build.exercised`) needs the two ids dispatched in an L0 asset-set/layer run: a production build, so a REVIEW item for SS.
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (the `bg_panchanga` edge: tier-independent but needs its own review).
- **Question for SS:** May the cascade `Build.exercised` FAIL on the two flipped ids stand until the first L0 dispatch (B.L0.x), or must the flip wait for that run?

### 2. CF-06 — prose_fields declarations for the 35 L0 assets that have none (Null and Narr gates)

- **Why this rank:** moves two gates (Null, Narr) on 35 assets with a declarations-file edit only; tier-independent, no rebuild, no risk to data.
- **Gate:** Null, Narr; **assets:** 35 null (3 declared `[]`: bg_doshas, bg_ontology, bg_yogas; 2 declared non-empty: bg_compendium_index, bg_remedies) — every L0 asset except bg_doshas, bg_ontology, bg_yogas, bg_compendium_index, bg_remedies
- **Evidence:** `platform/scripts/governance/asset_declarations.json` (version 1.6.0): `prose_fields: null` = undeclared, so Null and Narr read NO_DETECTOR (registered at REGISTRY_REVISION 5); `[]` is a positive declaration that needs an `evidence.prose_fields` pointer to writer code as `path:line`; a non-empty list names generated columns. The five declared L0 entries are the worked examples (bg_remedies composes `prescription_text` by f-string, `l0_remedy_corpus.py:247-424,2236`; bg_compendium_index composes `significance`, `bg_compendium_index.py:97,109`).
- **Design:** For each asset read the writer and its seed module for any f-string, template, join or computation that states or grades a value in a text column; declare `[]` with the `file:line` evidence if none, or the column list if some. The per-asset brief names the module to read and, where the repository already shows the answer, the proposed value. This is a declarations-file edit owned by Track E; it changes no asset.
- **Failing-first test and mutation:** `platform/scripts/governance/__tests__/test_e6_1_declarations.py` validation passes; mutation: declare `[]` for an asset whose writer composes text → `Narr.agree`/`Narr.lint` must flag it.
- **Blast radius:** none (census inputs only).
- **Rebuild:** none (declaration only).
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01 defines narration; file schema 1.6.0 exists).

### 3. CF-09 — Identity and normalisation reconciliation at the authority (bg_ontology and its consumers)

- **Why this rank:** highest consequence: bg_ontology is the identity root (4 direct / 69 transitive). Splits into rebuild-free served-surface fixes that can land first (list_entities, resolve_entity) and data changes that need the level-0/1 rebuild (B.L0.0/L0.1).
- **Gate:** Vocab, Ldgr, Build; **assets:** 6 — bg_ontology, bg_doshas, bg_remedies, bg_rules, bg_texts, bg_ephemeris
- **Evidence:** Census `Vocab.alias` FAIL: `dosha` 79 of 79 alias sets empty (`l0_doshas.py:1989-2002`: `[]  # synonyms — empty for doshas`). Ledger: `bg_ontology-G07/G08/G09`, `bg_ephemeris-G01` (body stored `Jupiter`, ontology `jupiter`), `bg_rules-G08` (2 of 14 rule `text_id`s have no ontology identity), `bg_ontology-G04` (resolve_entity returns two rows for 11 duplicated ids). Layer instance CH-05: 289 of 341 remedy source ids do not resolve exactly; 204 resolve case-insensitively; 85 do not (`classical_tradition` ×80 + 5). The `text` class holds 15 members and the corpus 15, differing by 3 in each direction (`bg_ontology-G09`).
- **Design:** (a) `brahmagyan/l0_doshas.py` seeds the 79 `dosha` ontology rows with `[]` synonyms: author the closed alias set per doṣa from the catalogue’s own names (no invented names: derive from `brahma_dosha_catalog` fields or the native/classical transliterations already in the repo; unresolvable rows stay explicit). (b) declare the normalisation rule ONCE at the authority (a `release`/normalisation declaration in the ontology; there is no release id today, TGH-T2-12) and make consumers resolve through it (`ephemeris_daily.body`, remedy `source_canonical_id`, `resolve_entity.ts`). (c) reconcile the `text` class with the corpus (derive the class from `classical_text_chunks`, ledger `bg_ontology-O5`). Order: ontology first, then the co-writers (doṣa, daśā systems, yogas), then readers.
- **Failing-first test and mutation:** `count(*) = count(DISTINCT (entity_class, canonical_id))` still holds; 79/79 doṣa alias sets non-empty; remedy unresolved 289 → the number the declared rule predicts (stated before the change); `resolve_entity` on each of the 11 duplicated ids returns one row per requested class. Mutation: blank one alias set → the alias test fails.
- **Blast radius:** Highest in L0: `bg_ontology` has 4 direct / 69 transitive dependents. An alias addition is an additive class (T2 §4.4 display/alias correction) and must not recompute a chart; a release id or a key change is not (identity-mapping change, real invalidation path).
- **Rebuild:** needs production rebuild: bg_ontology and bg_doshas (global, idempotent; B.L0.0/L0.1 in the plan), then dependents by level.
- **Fix class:** data (output change) + writer code + served surface; **buildable before J1:** tier-dependent: the release/normalisation clause (TGH-T2-12) and the Vocab rule wording; the alias sets themselves are tier-independent.
- **Question for SS:** Which authority holds the normalisation rule (the ontology table, a declared function, or the registry), and is a release id in scope for the first L0 wave?

### 4. CF-01 — Build.completion for converged reruns (rows_written = changed rows, not rows present)

- **Why this rank:** one ruling clears Build.completion on 8 assets with no rebuild (option A).
- **Gate:** Build (completion); **assets:** 8 (rows_written = 0 against a populated table) — bg_ephemeris, bg_muhurta_lattice, bg_ontology, bg_reference, bg_sky_calendar, bg_text_index, bg_texts, bg_vidhi_primitives
- **Evidence:** The L0 convention is a conditional upsert that leaves exact rows untouched, so a converged rerun legitimately reports 0 changed rows: `bg_ephemeris.py:9-12` ("Exact rows are left untouched so rowcount reports only inserted or genuinely repaired rows"); `brahmagyan/l0_ontology.py:1115-1145,1183-1190` (`ON CONFLICT … DO UPDATE … WHERE ROW(…) IS DISTINCT FROM ROW(…)`; returns `inserted = changed + deleted`, `skipped = unchanged`); `asset_runner.py:1210` (`rows_written = rows_inserted + rows_updated`; `rows_skipped` is read nowhere in the orchestrator and persisted in no migration); `asset_runner.py:1229-1247` (a global asset with 0 rows is still marked `lit`). T4 §4.2 check 6 (L277) reads `rows_written = 0` against a populated table as a gap. The cause is established for bg_ontology and stated in the writer docstring for bg_ephemeris; for bg_texts, bg_reference, bg_text_index and bg_vidhi_primitives it is the same convention by pattern, not individually verified.
- **Design:** Two options; a ruling is needed first. **A (detector/tooling, recommended):** `platform/scripts/governance/asset_census.py` Build.completion reads `rows_written = 0` as complete when the asset’s declaration states the changed-rows convention with a writer `file:line`, the latest run is `complete`, live rows are at or above the floor and the integrity SQL held; the verdict text names the convention. **B (writer code, not recommended):** make each seed return `rows_updated` = rows verified exact; this mislabels the field and inflates `rows_per_second` (`asset_runner.py:737`). A third option (persist `rows_skipped` and compare `rows_written + rows_skipped`) needs an orchestrator change, which is frozen: it would be raised to the Steward as R2, not designed around.
- **Failing-first test and mutation:** Failing-first: a fixture asset with `rows_written = 0`, live 0 and floor > 0 stays FAIL; the same with live ≥ floor and the declaration present reads PASS; without the declaration it reads FAIL. Mutation: delete the declaration → the verdict must flip back.
- **Blast radius:** No data and no consumer changes for A (census and ledger only). B would change `asset_throughput.rows_written` for 8 assets and the Cost baseline rate.
- **Rebuild:** A: none. B: needs production rebuild of the 8 assets (idempotent, no data change) so the new record is written.
- **Fix class:** detector/tooling (A) or writer code (B); **buildable before J1:** tier-dependent: T4 §4.2 check 6 wording; no harvest item states it (propose a second-round TG; nearest TGH-T3-18, TGH-T4-03).
- **Question for SS:** Is a converged-rerun `rows_written = 0` on a declared changed-rows writer a Build.completion PASS (option A), or must the writer report rows present (option B)?

### 5. CF-02 — Producer attribution: rider ids, multi-table writers and multi-producer tables

- **Why this rank:** nine assets; the registry/declaration half is tier-independent, the writer half needs small idempotent rebuilds.
- **Gate:** Build (completion, registered, exercised) and Earn (count_sql scope); **assets:** 9 — bg_medical_mappings, bg_sign_medical, bg_nakshatra_medical, bg_transit_rules, bg_transit_engine, bg_cohort, bg_formula_constants, bg_ontology, bg_class_priors/bg_class_lifetime_counts (shared table, already partition-scoped)
- **Evidence:** `bg_medical_mappings.py` registers three ids on one class (L25-27) and returns `sum(counts.values())` (L49): 60 = 21 + 27 + 12, against 21 for the asset’s own count_sql. `bg_transit_rules.py` registers two ids (L11-12) and returns `counts["total"]`; `brahmagyan/l0_transit.py:1210-1215` totals `bg_transit_engine + bg_transit_rules + bg_transit_moorti`. The module’s own volume line (`l0_transit.py:19-20`) reads 9 engine + 68 writer-owned rules + 7 migration-owned double-transit rules + 27 moorti: 9 + 68 + 27 = 104, the recorded `rows_written`, so the build record spans three tables including `bg_transit_moorti`, which no asset’s count_sql counts; live `bg_transit_rules` = 76 includes the 7 rows owned by migration 397 (`supabase/migrations/397_bg_transit_av_gates.sql`). `bg_cohort.py:525-575` tracks `rows_written` (10,000) apart from `md_rows_written` (100,000) and reports the first; the registry count_sql sums both tables (110,000). `brahmagyan/l0_formula_constants.py` upserts 10 constants; the table holds 17: `supabase/migrations/400_mimamsa_p6_schema.sql:68` and `424_ba_lel_r2_2_calibration_state_persistence.sql:30` insert further rows, so the table has more than one producer. `l0_ontology.py:1115-1135` names `CO_WRITER_ENTITY_CLASSES` written `DO NOTHING` (yoga, dosha, dasha_system seeded by their own writers; ledger `bg_ontology-G01`: 327 of 741 rows). Declarations already mark `bg_sign_medical`, `bg_nakshatra_medical`, `bg_transit_engine` as `kind: rider`.
- **Design:** (1) Registry/declaration (tier-independent): scope each asset’s `count_sql` to the rows its own producer writes (the precedent is `bg_class_lifetime_counts`, seed L580-608: `WHERE prior_version=… AND fact_kind=…`), or declare the table multi-producer in the declarations file; for `bg_transit_rules` add `bg_transit_moorti` to a declared produced-table set. (2) Writer code: report rows per registered id where the writer serves several (return the asset’s own partition in `rows_inserted`, or split the writer — never change `WriterBase`). (3) Rider handling in the gate (`Build.exercised`/`Build.registered`) is T4 `kind: rider (producer_covered)` territory.
- **Failing-first test and mutation:** Failing-first: for each asset, `rows_written` of a rerun equals the changed rows of ITS OWN count_sql scope; a seeded extra row in a sibling table must not move this asset’s count. Mutation: revert the count_sql scope → the count test fails.
- **Blast radius:** Registry-only part: cockpit counts for the named assets change (cosmetic); no consumer reads `count_sql`. Writer part: `asset_throughput` records only.
- **Rebuild:** (1) none. (2) needs production rebuild of the affected assets to refresh the record (idempotent, no data change).
- **Fix class:** registry/declaration only (1); writer code (2); **buildable before J1:** (1) tier-independent; (2) tier-dependent: TGH-T2-05 (one table, several producers) and TGH-T4-01 (`kind` vocabulary incl. rider).
- **Question for SS:** For a rider id, does `Build.exercised` count the sibling’s dispatch (T4 `producer_covered`), or must each id be dispatched itself?

### 6. CF-07 — Carr (source carriage and reproduction) detectors, one check per asset

- **Why this rank:** the largest gate count (Carr 40) but tooling work for Track E; D1/D2/D3 designs per asset are in the briefs; not a J1 input.
- **Gate:** Carr; **assets:** 40 of 40 NO_DETECTOR — D1: bg_rules, bg_yogas, bg_doshas, bg_remedies, bg_ontology, bg_dignity_reference, bg_parihara_rules, bg_vidhi_primitives and the static reference tables; D2: bg_concordance; D3: bg_ephemeris, bg_sky_calendar, bg_muhurta_lattice, bg_gochara_arcs, bg_kp_sublord_division, bg_cohort, bg_panchanga, bg_ephemeris_engine
- **Evidence:** Census `Carr.detector` NO_DETECTOR ×40; ledger rows `Carr.D1` (bg_ontology-G05, bg_rules-G03, …) and `Carr.D3` (bg_ephemeris-G02, bg_panchanga-G02). Layer instance §2.7: a (source correspondence) NO DETECTOR, b (witness carriage) PARTIAL, c (re-derivation) NO DETECTOR at L0. Anchors that already exist: `bg_texts_source_manifest_v1.json` pins 20 source objects with `md5_base64`, `generation`, `size_bytes`; `bg_ephemeris.py:44-45` fails closed on pyswisseph’s analytic fallback; `l0_kp_sublord_division.py` documents the Vimśottarī derivation (R1+R2: 243 + 6 = 249) and a star-lord cross-check.
- **Design:** Deterministic-first (CLAUDE.md §N.4: no JH-parity oracle; verification is internal consistency + classical-rule re-derivation). **D1:** resolve each row’s citation (`text_id`, `verse_ref`) to a `classical_text_chunks` row and test that the chunk contains the row’s anchor terms; report matched / unmatched / unresolvable counts; PASS only on the matched subset, PARTIAL otherwise (never PASS on a presence reading). Semantic equivalence of prerequisites and exceptions stays a sampled human reading, recorded as such. **D2:** for `classical_attributions` rows that share a claim, assert the disagreement is carried as two rows, not collapsed. **D3:** re-derive a stratified sample a second way and compare within a declared tolerance (ephemeris: a second pyswisseph call with different flags, or the stored daily-motion continuity; sky calendar: re-find a sampled event by root-finding on the stored ephemeris; KP: recompute the 249 divisions from Vimśottarī proportions). Each detector ships a seeded mismatch it must catch.
- **Failing-first test and mutation:** Failing-first per detector: report a non-zero mismatch count on a seeded corrupted copy and zero on the real table. The proof is the seeded case, not the real-data pass.
- **Blast radius:** none for the asset; the detector is Track E tooling.
- **Rebuild:** none.
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent for the assignment of D1/D2/D3 per asset (TGH-T3-02: T3 assigns carriage at layer scope only); the detectors themselves need no tier clause.
- **Question for SS:** Is a D1 anchor-term match acceptable as the L0 carriage detector (PASS on the matched subset), with semantic equivalence a sampled reading?

### 7. CF-04 — Dens (serving density) on the L0 served modules

- **Why this rank:** applicability ruling first (23 assets); no rebuild; re-measure at rev 4 is needed before the count means anything.
- **Gate:** Dens; **assets:** 23 FAIL + 1 NO_DETECTOR in the saved census — bg_class_lifetime_counts, bg_class_priors, bg_compendium_index, bg_dasha_systems, bg_doshas, bg_ephemeris, bg_ephemeris_engine, bg_formula_constants, bg_medical_mappings, bg_muhurta_lattice, bg_nakshatra_medical, bg_ontology, bg_panchanga, bg_parihara_rules, bg_remedies, bg_sign_medical, bg_sky_calendar, bg_text_index, bg_texts, bg_transit_engine, bg_transit_rules, bg_vastu_directions, bg_yogas (NO_DETECTOR: bg_dignity_reference)
- **Evidence:** 0 of 46 L0 capability modules declare a `density_contract` (layer instance §1.4). The saved `Dens.served` is criterion revision 1 (file-level "modules reference the table; declaring density_contract: 0"). Main’s revision 4 (`asset_census.py`, REGISTRY_REVISION 4) passes only when ONE capability entry declares `density_contract` AND its own served read selects a tier column (`DENS_TIER_COLUMN`, `asset_census.py:2638`: `tier | *_tier | verification_pass_status`). Among the populated columns the saved census recorded for the 40 L0 target tables, the only tier-like name is `cost_tier` on `brahma_remedy_corpus` (a cost tier, not a verification tier). So under revision 4 no L0 asset can reach PASS by declaring a contract alone, and some of the 23 may read N/A (no served read) rather than FAIL; the saved figure is a rev-1 reading and a re-measure is expected.
- **Design:** First the applicability question (below). If Dens applies: add `density_contract` (`platform/src/lib/retrieval/registry/types.ts` `CapabilityDescriptor`) to each L0 module that paginates or facets (`paginated`, `facets`, `empty_reason`), additive to the response; where a catalogue carries a catalog-only/confirmed distinction (the yoga and doṣa catalogues are the CLAUDE.md §N.6 case: `catalog_only_rows_in_page`, `judgment_flags`), serve it through the existing flag fields. If it does not apply to reference vocabularies, it is an N-22 applicability rule with a decision id in `NA_RULE_DECISIONS` (empty on main), not an asset change.
- **Failing-first test and mutation:** Per module: a response-shape test that the declared `empty_reason` is emitted on an empty page and that a trim keeps the dense layer (the `response_budget.ts` `hardFloor` pattern). Mutation: drop the declaration → the census Dens cell reads FAIL again.
- **Blast radius:** Additive response fields on the L0 retrieval tools; consumers that parse strictly would see new keys (none identified). No data change.
- **Rebuild:** none (TypeScript serving surface only).
- **Fix class:** served surface (TS) + SS ruling; **buildable before J1:** tier-dependent: TGH-T3-26 (who owns a Dens FAIL; serving is [TRANSFERS]) and the N-22 per-gate applicability rules.
- **Question for SS:** Does Dens apply to L0 reference vocabularies that carry no verification tier, and if so what is the L0 tier column (add one, or accept `density_contract` facets only)?

### 8. CF-12 — Idem: an orphan census for upsert-only writers (the Idem PASS does not test accretion)

- **Why this rank:** detector for 18 assets; protects against a repeat of migration 703; tier-dependent on the Idem meaning for upsert writers.
- **Gate:** Idem; **assets:** 18 by a static scan (indicative) — bg_class_lifetime_counts, bg_class_priors, bg_dignity_reference, bg_ephemeris, bg_formula_constants, bg_ghatana, bg_kota_chakra_rings, bg_medical_mappings, bg_muhurta_lattice, bg_nakshatra_medical, bg_parihara_rules, bg_phaladeepika_latta, bg_prashna_rules, bg_reference, bg_sign_medical, bg_sky_calendar, bg_vastu_directions, bg_vedha_malefic_scale
- **Evidence:** Saved `Idem.pattern` reads PASS for upsert writers ("INSERT … ON CONFLICT … into the asset's own table(s)"). Layer instance §5.2: a PASS does not test accretion. The documented instance: migration 703 (applied 2026-09-06) deleted 9 orphaned rows (1 from `bg_parihara_rules`, 8 from `bg_muhurta_factor_census`) after the upsert-only writer failed to remove them (layer instance CH-04). A static scan of each upsert asset's writer and delegated seed module (2026-10-01) found no `DELETE FROM` in these 18 (the other upsert assets delete or prune: `bg_ontology` `l0_ontology.py:1160-1173`, `bg_rules` `l0_rules.py:1559`, `bg_texts` `bg_texts.py:435`, …). The scan is a presence test of the text `DELETE FROM`, not proof that a table cannot hold orphans: it only selects where to look. Some of the 18 are append-only or horizon-driven by ruling (bg_class_lifetime_counts "APPEND-ONLY", `l0_class_lifetime_counts.py` header; bg_muhurta_lattice and bg_sky_calendar rolling horizons; bg_ephemeris fixed grid).
- **Design:** Add a read-only **orphan census** per upsert writer: run the writer’s produced-key computation in `ctx.dry_run` mode (supported by the frozen contract) and compare to the live natural keys; orphans = live − produced. Report per asset; PASS = 0 orphans, FAIL names them. This is the measurable form of "a rebuild replaces its own rows, never accretes" for upsert writers (the question TGH-T3-18 leaves open). Where the census finds orphans, the writer gets a prune scoped to its own natural-key partition (never a table-wide delete). Append-only-by-ruling assets declare it instead of pruning.
- **Failing-first test and mutation:** Failing-first: a fixture table with one extra row not produced by the writer → census FAIL naming it; after the prune → PASS. Mutation: widen the prune beyond the asset’s partition → the shared-table test (bg_class_priors/lifetime) fails.
- **Blast radius:** Detector: none. A prune changes data only when orphans exist (none known after migration 703).
- **Rebuild:** none for the detector; a prune is exercised by the next rebuild (no separate rebuild).
- **Fix class:** detector/tooling + writer code (prune, only if orphans are found); **buildable before J1:** tier-dependent: TGH-T3-18 (what Idem means for upsert writers); T4 §6 names L0 upsert as the convention.
- **Question for SS:** Is "no orphan rows under the writer’s own partition" the Idem claim for L0 upsert writers?

### 9. CF-08 — Ldgr: assets with no recognised citation column (16 "no reading")

- **Why this rank:** declaration-only for most of 16 assets; tier-dependent on the Ldgr source definition.
- **Gate:** Ldgr; **assets:** 16 — bg_class_lifetime_counts, bg_class_priors, bg_compendium_index, bg_concordance, bg_ephemeris_engine, bg_formula_constants, bg_ghatana, bg_gochara_arcs, bg_kota_chakra_rings, bg_nakshatra, bg_panchanga, bg_prashna_rules, bg_rules, bg_sarvatobhadra_grid, bg_vidhi_floors, bg_vidhi_primitives
- **Evidence:** Saved `Ldgr.source_presence` reads PASS on 24 and has no reading on 16 because the target table has no column in `CITATION_COLUMNS` (`asset_census.py`). The offline rollup therefore reads NO_DETECTOR for these. Some carry a source under another column name (bg_rules: `verse_ref`; bg_formula_constants: `citation_or_ratification`; bg_class_priors: `citation`).
- **Design:** Per asset: name the column that carries the source (declaration, e.g. `carriage` fact) so the inspector can read it; where a table carries none, the gap is real (a source must be added) and is an output change. The brief says which case applies.
- **Failing-first test and mutation:** Inspector: `Ldgr.source_presence` reads PASS/FAIL (not no reading) after the declaration; a row with a blank citation must read FAIL.
- **Blast radius:** none for declaration-only cases.
- **Rebuild:** none (declaration); data change would need a rebuild.
- **Fix class:** registry/declaration only (or data where no column exists); **buildable before J1:** tier-dependent: TGH-T3-01 (the gate map’s Ldgr source is undefined).

### 10. CF-05 — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094)

- **Why this rank:** Track E instrument (40 assets); nothing to change in any L0 asset.
- **Gate:** Earn (and Cost, information); **assets:** 40 of 40 NO_DETECTOR — all 40
- **Evidence:** Every L0 `Earn.build_record` and `Cost.baseline` reads "NO_DETECTOR — instrument absent (migration 1094)". The claims an L0 asset emits that need a detector able to read false: `asset_throughput.state = 'lit'` (4 L0 assets are `lit` with no `build_run_assets` row: bg_sign_medical, bg_nakshatra_medical, bg_transit_engine, bg_sarvatobhadra_grid; bg_gochara_citation_resolution has no throughput row — layer instance §1.1 finding 5), `count_sql`, `integrity_check_sql` (37 of 40 carry one; they have been observed to fail: 7 identical `post-write integrity check failed` errors), the floor.
- **Design:** Track E (the Nikaṣa engine) owns the instrument; the asset side is a declaration of which emitted statuses are claims (above). Nothing in any L0 asset file changes.
- **Failing-first test and mutation:** Track E’s own: a seeded false status must read FAIL.
- **Blast radius:** none for L0 assets.
- **Rebuild:** none.
- **Fix class:** detector/tooling; **buildable before J1:** tier-independent (no tier clause is needed to build the instrument).

### 11. CF-11 — `classical_tradition` provenance made an explicit queryable state (no invented citations)

- **Why this rank:** output change on four assets (explicit attribution state); needs SS’s answer on `classical_tradition` first; rebuild of four small assets after a migration.
- **Gate:** Ldgr (qualification), Carr; **assets:** 4 (doṣa 53, yoga 1, remedy 80 rows; transit rules 19 refuted + 6 unsourced) — bg_doshas, bg_yogas, bg_remedies, bg_transit_rules
- **Evidence:** `brahmagyan/l0_doshas.py:18-21`: "Citation policy (native decision per brief §3a): ~40 entries cite 'classical_tradition' (honest provenance for tradition-rooted doshas where no single BPHS verse names them … These are NOT fabricated citations.)". The census `Ldgr.source_presence` reads PASS because the column is populated (presence, not qualification; layer instance §1.2). 53 of 79 doṣa, 1 of 233 yoga (`l0_yogas.py:946`) and 80 remedy rows (`l0_remedy_corpus.py:263,507,526…`) carry the token.
- **Design:** Do NOT replace the token with a verse (B.10: no invented citation). Add an explicit attribution state (`attribution_state` ∈ `verse_cited | tradition_rooted | unattributed`, derived by the writer from the token) so a reader and the Ldgr gate can tell a tradition-rooted row from a verse-cited one; any replacement of a token by a real verse is a domain decision made row by row from the corpus, not by this design.
- **Failing-first test and mutation:** Failing-first: the count of `tradition_rooted` rows equals the count of rows carrying the token today (53 / 1 / 80); no row changes its citation; mutation: change a token to a verse → the state flips to `verse_cited`.
- **Blast radius:** Additive column; readers of the three catalogues see a new field.
- **Rebuild:** needs production rebuild: bg_doshas, bg_yogas, bg_remedies (idempotent; column add by migration first).
- **Fix class:** data (output change); **buildable before J1:** tier-independent for the state; tier-dependent for any claim that replaces the layer instance’s "placeholder" reading (the code says the token is a native decision).
- **Question for SS:** Is `classical_tradition` an accepted provenance value (the code cites a native decision) so the fix is an explicit state, or does SS want the 53 + 1 + 80 rows re-sourced from the corpus?

### 12. CF-10 — Build.history PARTIAL is a record of past errors; no edit changes it

- **Why this rank:** a definition question; no edit can change a history record.
- **Gate:** Build (history); **assets:** 13 — bg_class_lifetime_counts, bg_cohort, bg_compendium_index, bg_dasha_systems, bg_doshas, bg_formula_constants, bg_gochara_arcs, bg_kp_sublord_division, bg_parihara_rules, bg_reference, bg_remedies, bg_vidhi_floors, bg_yogas
- **Evidence:** Each reads "latest run complete, but N error(s) and M abort(s) on record" (T4 §4.2 check 8: PARTIAL if it has errored before and the latest run completed). Seven carry the identical error `post-write integrity check failed: integrity_check_sql → False` (2026-09-04 … 2026-09-06). The latest runs completed; no repair of the asset can remove the old rows.
- **Design:** None for the assets. A clean run raises the count of complete runs but never removes an error from history, so this cell stays PARTIAL until the definition says otherwise (a window, or "since the last registry/writer change").
- **Failing-first test and mutation:** n/a (definition).
- **Blast radius:** none.
- **Rebuild:** none.
- **Fix class:** detector/tooling (definition); **buildable before J1:** tier-dependent: T4 §4.2 check 8 wording.
- **Question for SS:** Should Build.history look only at runs since the last change to the asset’s writer or registry row, so that a repaired error stops counting?

## 5 · Rebuild consequences Track B needs per asset (facts found while reading the writers)

These are not gaps; they are what a level-by-level L0 rebuild (B.L0.0-B.L0.3, global request) must plan for (N-29 impact statement, rebuild plan, pre/post fingerprints). DAG depth from the layer instance §2.5: depth 0 (24 assets), 1 (11), 2 (4: bg_compendium_index, bg_parihara_rules, bg_rules, bg_text_index), 3 (1: bg_concordance).

- **`bg_texts` (depth 0, retained capital):** only `additive` and `metadata_only` rebuild modes exist; no mode deletes chunks (`bg_texts.py:388-396`); the corpus is recoverable only while the GCS bucket survives (non-regenerable inventory). A rebuild is expected to change nothing; fingerprint per text must be equal before and after.
- **`bg_formula_constants` (depth 0, retained capital):** the upsert overwrites `value_jsonb`/`bounds` of the 10 seeded constants, 8 of them `calibratable`; 7 more rows are migration-seeded and not produced by the writer. Record the live values before any rebuild; the guard in its FD-2 should land first.
- **`bg_ephemeris` and its dependents:** any change to stored values reaches `bg_gochara_arcs` (R9) and five Kāla assets; the table is TRUE-node while the engine/panchang standard is MEAN_NODE (a convention split, not a defect to fix in a wave). Rename of `body` values is NOT recommended (46 readers).
- **`bg_muhurta_lattice`, `bg_sky_calendar`:** rolling horizons computed from `today` at run time; fingerprints must use a fixed as-of window; `bg_sky_calendar` is `DO NOTHING`, so a corrected computation does not repair existing rows.
- **`bg_transit_rules`:** SERIAL `id` is FK-referenced by `gochara_resonance_map` (migration 459); retirement is ownership-scoped (`_owned_row_filter`); 7 rows are migration-owned; 19 rows carry a refuted citation pending re-verification.
- **`bg_rules`:** `ON CONFLICT (rule_id) DO NOTHING` — new columns need `DO UPDATE` or a backfill migration to reach existing rows.
- **`bg_ontology` and the co-writers:** identity-mapping changes (the `text` class) have a real invalidation path; additive alias sets do not. Order: `bg_ontology` (level 0) → `bg_doshas`, `bg_dasha_systems`, `bg_yogas`, `bg_reference`, `bg_remedies` (level 1) → `bg_rules` (2) → `bg_concordance` (3).
- **R9 assets (`bg_gochara_arcs`, `bg_gochara_citation_resolution`):** analysed here; any rebuild waits for SS after notifying Pravāha. Anything that changes `bg_ephemeris` or `bg_texts` reaches them.
- **Services (`bg_ephemeris_engine`, `bg_panchanga`):** no table, no rebuild; their status is a `lit` row no probe can read false.

## 6 · Dispositions that differ from the layer instance (v3.1 §3.2), and who approves

| asset | layer instance | this index | reason |
|---|---|---|---|
| bg_class_lifetime_counts, bg_class_priors | C (consolidation candidate) | keep | different governing rulings (ADJUDICATION-2 source tiers vs the judgment seed package); count_sql already partition-scopes each; T2 §10.1 C needs a proven shared authority |
| bg_prashna_rules | I (declare its table set) | keep | census now reads Build.target PASS for the multi-table asset; no discovery/projection/join repair identified |
| bg_yogas | P (with a must-add left to this lane) | enrich | 1 tradition-rooted citation + 4 unpopulated DP05 formation columns |
| bg_doshas | E | enrich (narrowed) | alias sets stay; the citation half becomes an explicit attribution state because the code cites a native decision for the token |
| bg_text_index | I | integrate (narrowed) | declare the grain/unit once; SS routes it |

**Approval under Track A §10:** keep and qualify and enrich (with or without fix designs) go to the Steward (G16); integrate (bg_text_index) goes to SS; **any output change goes to SS (R5)**: the enrich assets (bg_ontology, bg_doshas, bg_remedies, bg_rules, bg_yogas) and the fixes named "data (output change)" (CF-09, CF-11, bg_transit_rules citation state, bg_concordance chunk pointers). Provisional approval before J1 covers only tier-independent designs.

## 7 · Questions for Strategic Suvarṇa (consolidated)

Curated from the per-asset questions (the full per-asset lists stay in each brief, §4 `Question for SS` and §7). Ordered by how many assets or gates the answer unblocks.

1. **CF-01 (8 assets, Build):** is a converged-rerun `rows_written = 0` on a writer that declares the changed-rows convention a Build.completion PASS (option A), or must writers report rows present (option B)? Option C needs an orchestrator change and is R2.
2. **CF-04 (23 assets, Dens):** does Dens apply to L0 reference vocabularies that carry no verification tier? If yes, what is the L0 tier column (add one, or accept `density_contract` facets only); if no, an N-22 applicability rule with a decision id. Re-measure at registry rev 4 first.
3. **CF-11 (bg_doshas 53 rows, bg_yogas 1, bg_remedies 80, bg_transit_rules 19 refuted + 6 unsourced):** is `classical_tradition` an accepted provenance value (the code cites a native decision, `l0_doshas.py:18-21`), so the fix is an explicit attribution state, or does SS want re-sourcing? Who re-verifies the 19 refuted "BPHS Ch.29" transit citations?
4. **CF-09 (bg_ontology and 5 consumers):** where does the normalisation rule live and is a vocabulary release id in the first wave (TGH-T2-12)? Which identity option for the 11 two-class ids (ledger O1 a/b/c)? The three ontology-only text ids (bhrigu_samhita, jaimini_sutram, lal_kitab_text): keep or remove? Abhijit (28th nakshatra in the reference table, absent from the 27-id ontology class): identity or declared exception?
5. **bg_ephemeris / R9:** the table holds TRUE node while the engine and panchang standard is MEAN_NODE: intended and declared, or must SS rule a convention (a domain decision)? Body-name normalisation by authority-side declaration (recommended, no stored-value change) or rewrite? Which route notifies Pravāha before any wave touches `bg_ephemeris` or `bg_texts` (inputs of the R9 pair)?
6. **CF-02 / CF-03 (riders):** does a sibling’s dispatch count for a rider id (T4 `producer_covered`) or must each id run? May the recorded R61 cascade (`Build.exercised` FAIL after `has_writer` flips to true on bg_nakshatra_medical and bg_transit_engine) stand until the first L0 dispatch?
7. **Static migration-seeded assets (bg_gochara_citation_resolution; also bg_sarvatobhadra_grid):** Build gate N/A by an N-22 rule, or a dispatchable writer?
8. **bg_formula_constants:** where do calibrated values live once L5 tunes them (the upsert would revert them on rebuild)? Scope count_sql to the ten writer rows, or declare two producers?
9. **bg_rules:** backfill concept ids by migration or change `DO NOTHING` to `DO UPDATE`; drop/rename `confidence` or build a discriminating score; populate or remove `dasha_system_id`.
10. **Dispositions:** accept keep (not C) for bg_class_priors and bg_class_lifetime_counts; keep (not I) for bg_prashna_rules; integrate (declare the unit) for bg_text_index; enrich for bg_yogas.
11. **CF-10 (13 assets):** should Build.history count only runs since the last change to the asset’s writer or registry row?
12. **CF-12 (18 upsert writers):** is "no orphan rows under the writer’s own partition" the Idem claim for L0 upsert writers (TGH-T3-18)?
13. **CF-07:** is a D1 anchor-term match acceptable as the L0 carriage detector (PASS on the matched subset, semantic equivalence a sampled reading)? For ratified judgment seeds (bg_class_priors, bg_formula_constants non-classical rows) is Carr N/A with a decision id?
14. **bg_vidhi_floors:** what does `catalog_status = DRAFT` block for certification (TGH-T3-21), and who ratifies `education_deepdive` and `progeny_deepdive`?
15. **Duplicate authority:** combustion orbs are held in `bg_combustion_orbs` and `brahma_formula_constants`: intended redundancy or a consolidation question?
16. **bg_panchanga edge:** declare `bg_ephemeris_engine` (the code calls swisseph) or `bg_ephemeris` (the ledger)?
17. **bg_concordance:** chunk-level pointers on `classical_attributions` in scope for L0 (an output change) or is text-level carriage the contract?
18. **bg_vastu_directions:** admit Mayamata to the corpus so D1 can run, or record its rows as outside the corpus?
19. **bg_cohort:** report both tables in `rows_written` or scope count_sql to the primary table?
20. **bg_yogas:** are the four unpopulated DP05 formation columns in scope for the first L0 wave, and by what source-grounded extraction?


## 8 · Notes on method and path

- **Path:** the lane instruction placed briefs at `00_ARCHITECTURE/briefs/suvarna/assets/L0/<asset_id>.md`; Track A brief §8 names `layers/<Lx>/assets/<ASSET_ID>_ELEVATION_BRIEF_v1_0.md` and `designs/<ASSET_ID>_FIX_DESIGN_v1_0.md`. Here each brief carries its fix designs in §4; if SS wants the §8 layout the files move by name only.
- **Gap classification** (real / detector / stale / history / information) is this lane’s reading of the saved census and ledger; no tier supplies a rule mapping evidence to a disposition (TGH-T3-03).
- **Fixes go in the asset or the registry, never in the frozen orchestrator** (T4 §4.2): every design above respects that; the one option that would need an orchestrator change (persisting `rows_skipped`, CF-01) is flagged R2 and not designed.
- **Facts not established offline** are marked as such in the briefs (for example the unnamed third dependent of `bg_rules`, the cause of 7 extra `bg_transit_rules` rows beyond the writer’s own plus migration 397’s, live column lists for the multi-table assets).
