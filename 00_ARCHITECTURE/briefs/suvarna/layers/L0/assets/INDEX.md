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

> **PROVISIONAL — until J1; may register gaps, may not certify.** SS answered section 7 on 2026-10-01 (recorded below; items marked (R) are PROVISIONAL until the J1 review). Every figure is from the repository or the saved census (B.10). Nothing in this directory certifies a gate: dispositions were ACCEPTED as proposed by SS on 2026-10-01 (Q10), and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 1 · What this index rests on, and what is stale

- **Census used:** saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L0.json` (generated 2026-09-30T20:21:19+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.
- **Layer instance:** `L0_LAYER_INSTANCE_v3_1.md` (3.1-rev1) is the draft these briefs continue; its §4.4 rows were filled from it, its dispositions (§3.2) re-examined (see §6).
- **Gap ids** are ledger `asset_gaps.jsonl` ids from the census checkout (`/Users/Dev/suvarna-census/00_ARCHITECTURE/control/asset_gaps.jsonl` @ 2a78ec64d: 290 L0 rows, hand-authored for five pilots, inspector-emitted for the rest); that ledger is **not on main**. Several ledger rows are older than the saved census (class **stale** in the briefs).
- **Re-measure:** not possible in this lane (no DB). The repo's own rollup code (`asset_census.py` `rollup_asset`, REGISTRY_REVISION 6) was run **offline over the saved measurements** (output `/Users/Dev/suvarna-evidence/A_L0/rollup_saved_L0.json`); that mixes old measurements with new rules and is labelled so everywhere. A real re-measure by the current inspector is expected before any verdict is read. **Main is now at REGISTRY_REVISION 7** (E6 item (f), #2820: adds the `Carr.D1/D2/D3:no-carriage` N/A cause candidate; the registry is otherwise unchanged and the commit states no census cell changes), so no L0 verdict changes between 6 and 7. **Evidence outside the repo:** the saved census JSONs are in the repo (`layers/census/`); the offline rollup JSON (`/Users/Dev/suvarna-evidence/A_L0/rollup_saved_L0.json`), the Dens re-measure output and the gap ledger (`/Users/Dev/suvarna-census/00_ARCHITECTURE/control/asset_gaps.jsonl`) live outside it. The Dens re-measure script and its output are committed beside this index in `_evidence/` (`dens_remeasure.py`, `dens_remeasure_output.json`) so section 9.1 is reproducible; run `python3 dens_remeasure.py <repo-root>`.

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

**Gap rows across the 40 briefs (332 rows; duplicate ledger rows folded under R81 are listed separately in the ledger and counted once per id here):** real 45 · Dens rev-1 reading (Dens applies per SS Q2) 26 · real-with-SS-decision 0 · detector 146 · stale 27 · history 13 · information 56 · opportunity 18 · other 1.

**Saved census cells over the layer (777):** FAIL 42 · PARTIAL 24 · NO_DETECTOR 123 · ERRORED 0 · PASS 440 · N/A 68 · NOT_GENERIC 80. FAIL by criterion: Dens.served 23 · Build.completion 14 · Build.registered 2 · Build.exercised 1 · Count.floor 1 · Vocab.alias 1.

**Nine-gate cells, offline rollup of the saved measurements under main's rules (assets of 40; not a re-measure, not a certification):**

| gate | Ldgr | Idem | Earn | Null | Vocab | Carr | Narr | Dens | Build |
|---|---|---|---|---|---|---|---|---|---|
| rollup | NO_DETECTOR 16 · PASS 24 | NO_DETECTOR 4 · PARTIAL 1 · PASS 35 | NO_DETECTOR 40 | NO_DETECTOR 40 | FAIL 1 · NO_DETECTOR 39 | NO_DETECTOR 40 | NO_DETECTOR 40 | FAIL 23 · NO_DETECTOR 17 | FAIL 16 · NO_DETECTOR 12 · PARTIAL 10 · PASS 2 |

The draft's N/A-aware reading (layer instance Appendix B) differs only because it lets a measured N/A drop out: Vocab PASS 35 · FAIL 1 · NO_DETECTOR 1 · no reading 3; Idem PASS 35 · PARTIAL 1 · N/A 4; Dens FAIL 23 · NO_DETECTOR 1 · N/A 16; Build FAIL 16 · PARTIAL 11 · PASS 13; Ldgr PASS 24 · no reading 16.

## 3 · Assets × disposition × gaps × fix class × rebuild

Columns: **real** = a shortfall in rows/writer/registry/served surface; **Dens/SSq** = Dens rev-1 FAILs (Dens applies where a served surface is reached: SS Q2; offline re-measure in section 9.1) plus items that were SS questions and are now decided; **detector** = NO_DETECTOR or definition-open; **other** = stale + history + information + opportunity; **rebuild** y = a fix needs a production rebuild/dispatch, cond = only under one option, n = none.

| asset | disposition | real | Dens/SSq | detector | other | fix class | rebuild | shared fixes |
|---|---|---:|---:|---:|---:|---|---|---|
| [bg_class_lifetime_counts](bg_class_lifetime_counts_ELEVATION_BRIEF_v1_0.md) | keep (P) | 0 | 1 | 4 | 3 | detector/tooling; registry/declaration; served surface (TS) | n | CF-04, CF-05, CF-06, CF-07, CF-08, CF-10, CF-12 |
| [bg_class_priors](bg_class_priors_ELEVATION_BRIEF_v1_0.md) | keep (P) | 0 | 1 | 4 | 2 | registry/declaration; served surface (TS) | n | CF-04, CF-05, CF-06, CF-07, CF-08, CF-12 |
| [bg_cohort](bg_cohort_ELEVATION_BRIEF_v1_0.md) | keep (P) | 1 | 0 | 3 | 2 | detector/tooling; registry/declaration; writer code | n | CF-02, CF-05, CF-06, CF-07, CF-10 |
| [bg_compendium_index](bg_compendium_index_ELEVATION_BRIEF_v1_0.md) | keep (P) | 0 | 1 | 3 | 4 | detector/tooling; registry/declaration; served surface (TS); writer code | n | CF-04, CF-05, CF-07, CF-08, CF-10 |
| [bg_concordance](bg_concordance_ELEVATION_BRIEF_v1_0.md) | keep (P) | 0 | 0 | 4 | 2 | data (output change); detector/tooling; registry/declaration; writer code | n | CF-05, CF-06, CF-07, CF-08 |
| [bg_dasha_systems](bg_dasha_systems_ELEVATION_BRIEF_v1_0.md) | keep (P) | 0 | 1 | 3 | 3 | detector/tooling; registry/declaration; served surface (TS) | n | CF-04, CF-05, CF-06, CF-07, CF-10 |
| [bg_dignity_reference](bg_dignity_reference_ELEVATION_BRIEF_v1_0.md) | keep (P) | 0 | 1 | 3 | 1 | detector/tooling; registry/declaration | y | CF-04, CF-05, CF-06, CF-07, CF-12 |
| [bg_doshas](bg_doshas_ELEVATION_BRIEF_v1_0.md) | enrich (E) | 2 | 1 | 2 | 3 | data (output change); detector/tooling; served surface (TS); writer code | y | CF-04, CF-05, CF-07, CF-09, CF-10, CF-11 |
| [bg_ephemeris](bg_ephemeris_ELEVATION_BRIEF_v1_0.md) | keep (P) | 3 | 2 | 5 | 7 | detector/tooling; registry/declaration; served surface (TS) | n | CF-01, CF-04, CF-05, CF-06, CF-07, CF-08, CF-09, CF-12 |
| [bg_ephemeris_engine](bg_ephemeris_engine_ELEVATION_BRIEF_v1_0.md) | keep (P) | 0 | 1 | 5 | 1 | detector/tooling; registry/declaration; served surface (TS) | n | CF-03, CF-04, CF-05, CF-06, CF-07 |
| [bg_formula_constants](bg_formula_constants_ELEVATION_BRIEF_v1_0.md) | keep (P) | 1 | 1 | 4 | 3 | detector/tooling; registry/declaration; served surface (TS); writer code | y | CF-02, CF-04, CF-05, CF-06, CF-07, CF-08, CF-10, CF-12 |
| [bg_ghatana](bg_ghatana_ELEVATION_BRIEF_v1_0.md) | keep (P) | 0 | 0 | 4 | 2 | detector/tooling; registry/declaration | n | CF-05, CF-06, CF-07, CF-08, CF-12 |
| [bg_gochara_arcs](bg_gochara_arcs_ELEVATION_BRIEF_v1_0.md) | keep (P) | 0 | 0 | 4 | 3 | detector/tooling; registry/declaration | n | CF-05, CF-06, CF-07, CF-08, CF-10 |
| [bg_gochara_citation_resolution](bg_gochara_citation_resolution_ELEVATION_BRIEF_v1_0.md) | keep (P) | 1 | 0 | 3 | 1 | detector/tooling; registry/declaration; served surface (TS); writer code | y | CF-04, CF-05, CF-06, CF-07 |
| [bg_kota_chakra_rings](bg_kota_chakra_rings_ELEVATION_BRIEF_v1_0.md) | keep (P) | 0 | 0 | 4 | 3 | detector/tooling; registry/declaration | n | CF-05, CF-06, CF-07, CF-08, CF-12 |
| [bg_kp_sublord_division](bg_kp_sublord_division_ELEVATION_BRIEF_v1_0.md) | keep (P) | 0 | 0 | 3 | 3 | detector/tooling; registry/declaration | n | CF-04, CF-05, CF-06, CF-07, CF-10 |
| [bg_medical_mappings](bg_medical_mappings_ELEVATION_BRIEF_v1_0.md) | keep (P) | 1 | 1 | 3 | 2 | detector/tooling; registry/declaration; served surface (TS); writer code | y | CF-02, CF-04, CF-05, CF-06, CF-07, CF-12 |
| [bg_muhurta_lattice](bg_muhurta_lattice_ELEVATION_BRIEF_v1_0.md) | keep (P) | 1 | 1 | 3 | 1 | detector/tooling; registry/declaration; served surface (TS) | n | CF-01, CF-03, CF-04, CF-05, CF-06, CF-07, CF-12 |
| [bg_nakshatra](bg_nakshatra_ELEVATION_BRIEF_v1_0.md) | keep (P) | 0 | 0 | 4 | 3 | detector/tooling; registry/declaration | n | CF-05, CF-06, CF-07, CF-08, CF-09 |
| [bg_nakshatra_medical](bg_nakshatra_medical_ELEVATION_BRIEF_v1_0.md) | keep (P) | 1 | 1 | 3 | 2 | detector/tooling; registry/declaration; served surface (TS) | n | CF-02, CF-03, CF-04, CF-05, CF-06, CF-07, CF-12 |
| [bg_ontology](bg_ontology_ELEVATION_BRIEF_v1_0.md) | enrich (E) | 9 | 2 | 4 | 9 | data (output change); detector/tooling; registry/declaration; served surface (TS); writer code | y | CF-01, CF-02, CF-04, CF-05, CF-07, CF-09 |
| [bg_panchanga](bg_panchanga_ELEVATION_BRIEF_v1_0.md) | keep (P) | 1 | 1 | 8 | 4 | detector/tooling; registry/declaration; served surface (TS) | n | CF-03, CF-04, CF-05, CF-06, CF-07 |
| [bg_parihara_rules](bg_parihara_rules_ELEVATION_BRIEF_v1_0.md) | keep (P) | 2 | 1 | 3 | 3 | detector/tooling; registry/declaration; served surface (TS); writer code | n | CF-03, CF-04, CF-05, CF-06, CF-07, CF-10, CF-12 |
| [bg_phaladeepika_latta](bg_phaladeepika_latta_ELEVATION_BRIEF_v1_0.md) | keep (P) | 0 | 0 | 3 | 2 | detector/tooling; registry/declaration | n | CF-05, CF-06, CF-07, CF-12 |
| [bg_prashna_rules](bg_prashna_rules_ELEVATION_BRIEF_v1_0.md) | keep (P) | 0 | 0 | 4 | 2 | detector/tooling; registry/declaration | n | CF-02, CF-04, CF-05, CF-06, CF-07, CF-08, CF-12 |
| [bg_reference](bg_reference_ELEVATION_BRIEF_v1_0.md) | keep (P) | 1 | 0 | 3 | 3 | detector/tooling; registry/declaration; writer code | n | CF-01, CF-04, CF-05, CF-06, CF-07, CF-10, CF-12 |
| [bg_remedies](bg_remedies_ELEVATION_BRIEF_v1_0.md) | enrich (E) | 3 | 1 | 2 | 3 | data (output change); detector/tooling; served surface (TS); writer code | y | CF-04, CF-05, CF-07, CF-09, CF-10, CF-11 |
| [bg_rules](bg_rules_ELEVATION_BRIEF_v1_0.md) | enrich (E) | 7 | 0 | 6 | 8 | data (output change); detector/tooling; registry/declaration; served surface (TS); writer code | y | CF-05, CF-06, CF-07, CF-08, CF-09 |
| [bg_sarvatobhadra_grid](bg_sarvatobhadra_grid_ELEVATION_BRIEF_v1_0.md) | qualify (Q) | 1 | 0 | 7 | 5 | registry/declaration; writer code | cond | CF-05, CF-06, CF-10 |
| [bg_sign_medical](bg_sign_medical_ELEVATION_BRIEF_v1_0.md) | keep (P) | 2 | 1 | 3 | 2 | detector/tooling; registry/declaration; served surface (TS) | n | CF-02, CF-04, CF-05, CF-06, CF-07, CF-12 |
| [bg_sky_calendar](bg_sky_calendar_ELEVATION_BRIEF_v1_0.md) | keep (P) | 1 | 1 | 3 | 1 | detector/tooling; registry/declaration; served surface (TS) | n | CF-01, CF-03, CF-04, CF-05, CF-06, CF-07, CF-12 |
| [bg_text_index](bg_text_index_ELEVATION_BRIEF_v1_0.md) | integrate (I) | 1 | 1 | 4 | 2 | detector/tooling; registry/declaration; served surface (TS); writer code | n | CF-01, CF-04, CF-05, CF-06, CF-07, CF-08 |
| [bg_texts](bg_texts_ELEVATION_BRIEF_v1_0.md) | keep (P) | 1 | 1 | 3 | 2 | detector/tooling; registry/declaration; served surface (TS) | n | CF-01, CF-04, CF-05, CF-06, CF-07 |
| [bg_transit_engine](bg_transit_engine_ELEVATION_BRIEF_v1_0.md) | keep (P) | 1 | 1 | 3 | 2 | detector/tooling; registry/declaration; served surface (TS) | n | CF-02, CF-03, CF-04, CF-05, CF-06, CF-07 |
| [bg_transit_rules](bg_transit_rules_ELEVATION_BRIEF_v1_0.md) | keep (P) | 2 | 1 | 3 | 2 | data (output change); detector/tooling; registry/declaration; served surface (TS); writer code | y | CF-02, CF-04, CF-05, CF-06, CF-07, CF-11 |
| [bg_vastu_directions](bg_vastu_directions_ELEVATION_BRIEF_v1_0.md) | keep (P) | 0 | 1 | 3 | 3 | detector/tooling; registry/declaration; served surface (TS) | n | CF-04, CF-05, CF-06, CF-07, CF-12 |
| [bg_vedha_malefic_scale](bg_vedha_malefic_scale_ELEVATION_BRIEF_v1_0.md) | keep (P) | 0 | 0 | 3 | 2 | detector/tooling; registry/declaration | n | CF-05, CF-06, CF-07, CF-12 |
| [bg_vidhi_floors](bg_vidhi_floors_ELEVATION_BRIEF_v1_0.md) | qualify (Q) | 0 | 0 | 4 | 3 | detector/tooling; registry/declaration | n | CF-05, CF-06, CF-07, CF-08, CF-10 |
| [bg_vidhi_primitives](bg_vidhi_primitives_ELEVATION_BRIEF_v1_0.md) | keep (P) | 1 | 0 | 4 | 1 | detector/tooling; registry/declaration | n | CF-01, CF-03, CF-05, CF-06, CF-07, CF-08 |
| [bg_yogas](bg_yogas_ELEVATION_BRIEF_v1_0.md) | enrich (narrowed after Q20; pending) | 1 | 1 | 2 | 5 | data (output change); detector/tooling; registry/declaration; served surface (TS) | y | CF-04, CF-05, CF-07, CF-09, CF-10, CF-11 |

**Rebuild needed (y):** 10 — bg_dignity_reference, bg_doshas, bg_formula_constants, bg_gochara_citation_resolution, bg_medical_mappings, bg_ontology, bg_remedies, bg_rules, bg_transit_rules, bg_yogas. **Option-dependent (cond):** 1 — bg_sarvatobhadra_grid. All others: none.

## 4 · Cross-asset fixes, ordered by value for J1 (Tracks I and B)

Order rule: assets served × gate movement, then tier-independence and absence of a rebuild first (Track I can start tier-independent designs before J1: Track A §10). Each shared fix is designed once here; the per-asset brief states how it applies and adds the asset-specific parts.

### 1. CF-03 — Registry correction batch (one surgical migration + seed literals)

- **Why this rank:** smallest, tier-independent, no rebuild, one migration; removes the layer’s only Count FAIL and two Build.registered FAILs (expect the recorded R61 cascade).
- **Gate:** Count (information), Build.registered, Build.target/dag; **assets:** 4 certain + 3 optional — bg_parihara_rules (floor 449 → 440), bg_nakshatra_medical and bg_transit_engine (`has_writer` false → true), bg_panchanga (declare its `bg_ephemeris_engine` edge per SS Q16; the ledger’s `bg_ephemeris` edge is not taken); optional floor refresh (information): bg_muhurta_lattice, bg_sky_calendar, bg_ontology
- **Evidence:** Migration 644 set the parihara floor to 449 over 61 + 329 + 59 rows; migration 703 (applied 2026-09-06) deleted 9 orphaned rows and re-pinned the integrity check but left the floor; live 60 + 329 + 51 = 440 (layer instance CH-04, Q-15). Code registers `bg_nakshatra_medical` (`bg_medical_mappings.py:25-27`) and `bg_transit_engine` (`bg_transit_rules.py:11-12`) while the registry says `has_writer = false` (census `Build.registered` FAIL ×2). Nikaṣa register R61: flipping `has_writer` to true opens a NEW measured gap (`Build.exercised`, writer never dispatched) until the id is dispatched in a run. Floors below live (+8,644 muhūrta lattice; +22 sky calendar; +4 ontology) are not failures (`Count.floor` PASS); CLAUDE.md §N.4 says a floor equals the achieved count after a build, so a refresh is cosmetic.
- **Design:** One migration, number = max+1 across every origin head and both migration directories at execution time (never trusted from this document; Suvarṇa migration range per Track E), `UPDATE asset_registry SET target_floor = 440 WHERE asset_id = 'bg_parihara_rules'` and `SET has_writer = true WHERE asset_id IN ('bg_nakshatra_medical','bg_transit_engine')`, each with an `AND <old value>` guard and an in-migration check, plus the same literals in `platform/scripts/seed/asset_registry_seed.ts`; verify by production structure, never by the runner’s report. The `bg_panchanga` edge is a `depends_on` change (DAG order and upstream hash move): Track I’s migration 1210 deliberately excluded L0 bedrock edges, so this one needs its own review.
- **Failing-first test and mutation:** Failing-first: after the migration `Count.floor` for `bg_parihara_rules` reads PASS and `Build.registered` PASS for the two ids; the cascade `Build.exercised` FAIL for the two ids is EXPECTED and recorded, not a regression. Mutation: restore the old floor → `Count.floor` FAIL again.
- **Blast radius:** Registry rows only. `has_writer = true` makes the two ids dispatchable in a layer-scope L0 plan (they ride sibling writers). No consumer reads `target_floor`.
- **Rebuild:** none for the floor and the has_writer flags. Clearing the cascade (`Build.exercised`) needs the two ids dispatched in an L0 asset-set/layer run: a production build, so a REVIEW item for SS.
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (the `bg_panchanga` edge: tier-independent but needs its own review).
- **Decision:** ANSWERED by SS 2026-10-01 (Q6): a sibling's dispatch counts (`producer_covered`) when the registry declares the rider relation; the R61 cascade may stand until the first L0 dispatch.

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
- **Evidence:** Census `Vocab.alias` FAIL: `dosha` 79 of 79 alias sets empty (`l0_doshas.py:1989-2002`: `[]  # synonyms — empty for doshas`). Ledger: `bg_ontology-G07/G08/G09`, `bg_ephemeris-G01` (body stored `Jupiter`, ontology `jupiter`), `bg_rules-G08` (2 of 14 rule `text_id`s have no ontology identity), `bg_ontology-G04` (resolve_entity silently picks one of two rows for 11 duplicated ids: `LIMIT 1`, `resolve_entity.ts:68-71`; the ledger text says two rows). Layer instance CH-05: 289 of 341 remedy source ids do not resolve exactly; 204 resolve case-insensitively; 85 do not (`classical_tradition` ×80 + 5). The `text` class holds 15 members and the corpus 15, differing by 3 in each direction (`bg_ontology-G09`).
- **Design:** **Decided (SS 2026-10-01, Q4/Q5):** (a) dosha alias sets: `brahmagyan/l0_doshas.py:2002` seeds `[]`; author a closed alias set per doṣa from names the module's own entries carry (convention read from the 15 complete classes; no invented aliases). (b) the normalisation rule lives in the `bg_ontology` writer, the one authority; consumers resolve through it; `ephemeris_daily.body` is declared the same way with NO stored-value change; a vocabulary release id goes in the first wave if cheap. (c) the `text` class is derived from the corpus: add the 3 corpus-only ids, keep an ontology-only id only if it has a consumer (referrer census first), remove the rest. Order: ontology first, then co-writers, then readers.
- **Failing-first test and mutation:** `count(*) = count(DISTINCT (entity_class, canonical_id))` still holds; 79/79 doṣa alias sets non-empty; remedy unresolved 289 → the number the declared rule predicts (stated before the change); `resolve_entity` on each of the 11 duplicated ids returns one row per requested class. Mutation: blank one alias set → the alias test fails.
- **Blast radius:** Highest in L0: `bg_ontology` has 4 direct / 69 transitive dependents. An alias addition is an additive class (T2 §4.4 display/alias correction) and must not recompute a chart; a release id or a key change is not (identity-mapping change, real invalidation path).
- **Rebuild:** needs production rebuild: bg_ontology and bg_doshas (global, idempotent; B.L0.0/L0.1 in the plan), then dependents by level.
- **Fix class:** data (output change) + writer code + served surface; **buildable before J1:** tier-dependent: the release/normalisation clause (TGH-T2-12) and the Vocab rule wording; the alias sets themselves are tier-independent.
- **Decision:** ANSWERED by SS 2026-10-01 (Q4): the normalisation rule lives in the `bg_ontology` writer, the one authority; the vocabulary release id goes in the first wave if it is cheap; for the 11 two-class ids take the recommended option (a, class-aware resolvers) unless it changes served ids (then REVIEW to SS); of bhrigu_samhita, jaimini_sutram, lal_kitab_text keep any with a consumer and remove the rest; Abhijit is a declared exception (classically intercalary) and the 27-id class stays canonical. ANSWERED by SS 2026-10-01 (Q5): authority-side declaration with NO stored-value change: `bg_ephemeris` declares `node: TRUE`; consumers needing MEAN must not read node values from it (a check, Track I item); body-name normalisation is declared the same way. BEFORE any wave touches `bg_ephemeris` or `bg_texts`, SS notifies Pravāha (Exec sends SS an ASK first).

### 4. CF-01 — Build.completion for converged reruns (rows_written = changed rows): option A decided (R)

- **Why this rank:** one ruling clears Build.completion on 8 assets with no rebuild (option A).
- **Gate:** Build (completion); **assets:** 8 (rows_written = 0 against a populated table) — bg_ephemeris, bg_muhurta_lattice, bg_ontology, bg_reference, bg_sky_calendar, bg_text_index, bg_texts, bg_vidhi_primitives
- **Evidence:** The L0 convention is a conditional upsert that leaves exact rows untouched, so a converged rerun legitimately reports 0 changed rows: `bg_ephemeris.py:9-12` ("Exact rows are left untouched so rowcount reports only inserted or genuinely repaired rows"); `brahmagyan/l0_ontology.py:1115-1145,1183-1190` (`ON CONFLICT … DO UPDATE … WHERE ROW(…) IS DISTINCT FROM ROW(…)`; returns `inserted = changed + deleted`, `skipped = unchanged`); `asset_runner.py:1210` (`rows_written = rows_inserted + rows_updated`; `rows_skipped` is read nowhere in the orchestrator and persisted in no migration); `asset_runner.py:1229-1247` (a global asset with 0 rows is still marked `lit`). T4 §4.2 check 6 (L277) reads `rows_written = 0` against a populated table as a gap. The cause is established for bg_ontology and stated in the writer docstring for bg_ephemeris; for bg_texts, bg_reference, bg_text_index and bg_vidhi_primitives it is the same convention by pattern, not individually verified.
- **Design:** **Decided (SS 2026-10-01, Q1, R, PROVISIONAL until the J1 review): option A.** `platform/scripts/governance/asset_census.py` Build.completion reads `rows_written = 0` as complete ONLY IF the asset's declaration states the changed-rows convention with a writer `file:line` AND `Build.count_integrity` PASSes on populated rows (live at or above the floor, integrity SQL held); the verdict text names the convention. Completion is proven by the count, not by `rows_written`. Options B (writer mislabels `rows_updated`) and C (persist `rows_skipped`: an orchestrator change, R2) are not taken.
- **Failing-first test and mutation:** Failing-first: a fixture asset with `rows_written = 0`, live 0 and floor > 0 stays FAIL; the same with live ≥ floor and the declaration present reads PASS; without the declaration it reads FAIL. Mutation: delete the declaration → the verdict must flip back.
- **Blast radius:** No data and no consumer changes for A (census and ledger only). B would change `asset_throughput.rows_written` for 8 assets and the Cost baseline rate.
- **Rebuild:** A: none. B: needs production rebuild of the 8 assets (idempotent, no data change) so the new record is written.
- **Fix class:** detector/tooling (A) or writer code (B); **buildable before J1:** tier-dependent: T4 §4.2 check 6 wording; no harvest item states it (propose a second-round TG; nearest TGH-T3-18, TGH-T4-03).
- **Tension named by the review:** Option A makes `count_integrity` the proof of completion. That is a rows-present proxy (live rows at or above the floor and the integrity SQL held), the same kind of signal CLAUDE.md N.8 instance 4 criticises (the orchestrator promoted `lit` on row presence without checking that the substep plan finished). It is accepted by SS as provisional (R) until the J1 review; its honest limit is that it proves the table is populated and internally consistent, not that this run produced it.
- **Decision:** ANSWERED by SS 2026-10-01 (Q1): CF-01 option A (R, PROVISIONAL until the J1 review): a converged rerun with `rows_written = 0` reads Build.completion PASS ONLY IF the writer declares the changed-rows convention AND count_integrity PASSes on populated rows; completion is proven by the count, not by `rows_written`.

### 5. CF-02 — Producer attribution: rider ids, multi-table writers and multi-producer tables

- **Why this rank:** nine assets; the registry/declaration half is tier-independent, the writer half needs small idempotent rebuilds.
- **Gate:** Build (completion, registered, exercised) and Earn (count_sql scope); **assets:** 9 — bg_medical_mappings, bg_sign_medical, bg_nakshatra_medical, bg_transit_rules, bg_transit_engine, bg_cohort, bg_formula_constants, bg_ontology, bg_class_priors/bg_class_lifetime_counts (shared table, already partition-scoped)
- **Evidence:** `bg_medical_mappings.py` registers three ids on one class (L25-27) and returns `sum(counts.values())` (L49): 60 = 21 + 27 + 12, against 21 for the asset’s own count_sql. `bg_transit_rules.py` registers two ids (L11-12) and returns `counts["total"]`; `brahmagyan/l0_transit.py:1210-1215` totals `bg_transit_engine + bg_transit_rules + bg_transit_moorti`. The module’s docstring volume line (`l0_transit.py:19-20`) reads 9 engine + 68 writer-owned rules + 7 migration-owned double-transit rules + 27 moorti: 9 + 68 + 27 = 104, the recorded `rows_written` (the imported rule list holds 69 rules, which would give 105; the one-row difference is not established), so the build record spans three tables including `bg_transit_moorti`, which no asset’s count_sql counts; live `bg_transit_rules` = 76 includes the 7 rows owned by migration 397 (`supabase/migrations/397_bg_transit_av_gates.sql`). `bg_cohort.py:525-575` tracks `rows_written` (10,000) apart from `md_rows_written` (100,000) and reports the first; the registry count_sql sums both tables (110,000). `brahmagyan/l0_formula_constants.py` upserts 10 constants; the table holds 17: `supabase/migrations/400_mimamsa_p6_schema.sql:68` and `424_ba_lel_r2_2_calibration_state_persistence.sql:30` insert further rows, so the table has more than one producer. `l0_ontology.py:1115-1135` names `CO_WRITER_ENTITY_CLASSES` written `DO NOTHING` (yoga, dosha, dasha_system seeded by their own writers; ledger `bg_ontology-G01` says 327 of 741 rows; the class counts 233 + 79 + 20 give 332). Declarations already mark `bg_sign_medical`, `bg_nakshatra_medical`, `bg_transit_engine` as `kind: rider`.
- **Design:** (1) Registry/declaration (tier-independent): scope each asset’s `count_sql` to the rows its own producer writes (the precedent is `bg_class_lifetime_counts`, seed L580-608: `WHERE prior_version=… AND fact_kind=…`), or declare the table multi-producer in the declarations file; for `bg_transit_rules` add `bg_transit_moorti` to a declared produced-table set. (2) Writer code: report rows per registered id where the writer serves several (return the asset’s own partition in `rows_inserted`, or split the writer — never change `WriterBase`). (3) Rider handling in the gate (`Build.exercised`/`Build.registered`) is T4 `kind: rider (producer_covered)` territory.
- **Failing-first test and mutation:** Failing-first: for each asset, `rows_written` of a rerun equals the changed rows of ITS OWN count_sql scope; a seeded extra row in a sibling table must not move this asset’s count. Mutation: revert the count_sql scope → the count test fails.
- **Blast radius:** Registry-only part: cockpit counts for the named assets change (cosmetic); no consumer reads `count_sql`. Writer part: `asset_throughput` records only.
- **Rebuild:** (1) none. (2) needs production rebuild of the affected assets to refresh the record (idempotent, no data change).
- **Fix class:** registry/declaration only (1); writer code (2); **buildable before J1:** (1) tier-independent; (2) tier-dependent: TGH-T2-05 (one table, several producers) and TGH-T4-01 (`kind` vocabulary incl. rider).
- **Decision:** ANSWERED by SS 2026-10-01 (Q6): a sibling's dispatch counts (`producer_covered`) when the registry declares the rider relation; the R61 cascade may stand until the first L0 dispatch. ANSWERED by SS 2026-10-01 (Q19): scope `count_sql` to the primary table and declare the asset multi-table.

### 6. CF-07 — Carr (source carriage and reproduction) detectors, one check per asset

- **Why this rank:** the largest gate count (Carr 40) but tooling work for Track E; D1/D2/D3 designs per asset are in the briefs; not a J1 input.
- **Gate:** Carr; **assets:** 40 of 40 NO_DETECTOR — D1: bg_rules, bg_yogas, bg_doshas, bg_remedies, bg_ontology, bg_dignity_reference, bg_parihara_rules, bg_vidhi_primitives and the static reference tables; D2: bg_concordance; D3: bg_ephemeris, bg_sky_calendar, bg_muhurta_lattice, bg_gochara_arcs, bg_kp_sublord_division, bg_cohort, bg_panchanga, bg_ephemeris_engine
- **Evidence:** Census `Carr.detector` NO_DETECTOR ×40; ledger rows `Carr.D1` (bg_ontology-G05, bg_rules-G03, …) and `Carr.D3` (bg_ephemeris-G02, bg_panchanga-G02). Layer instance §2.7: a (source correspondence) NO DETECTOR, b (witness carriage) PARTIAL, c (re-derivation) NO DETECTOR at L0. Anchors that already exist: `bg_texts_source_manifest_v1.json` pins 20 source objects with `md5_base64`, `generation`, `size_bytes`; `bg_ephemeris.py:44-45` fails closed on pyswisseph’s analytic fallback; `l0_kp_sublord_division.py` documents the Vimśottarī derivation (R1+R2: 243 + 6 = 249) and a star-lord cross-check.
- **Design:** Deterministic-first (CLAUDE.md §N.4: no JH-parity oracle; verification is internal consistency + classical-rule re-derivation). **D1:** resolve each row’s citation (`text_id`, `verse_ref`) to a `classical_text_chunks` row and test that the chunk contains the row’s anchor terms; report matched / unmatched / unresolvable counts; PASS only on the matched subset, PARTIAL otherwise (never PASS on a presence reading). Semantic equivalence of prerequisites and exceptions stays a sampled human reading, recorded as such. **D2:** for `classical_attributions` rows that share a claim, assert the disagreement is carried as two rows, not collapsed. **D3:** re-derive a stratified sample a second way and compare within a declared tolerance (ephemeris: a second pyswisseph call with different flags, or the stored daily-motion continuity; sky calendar: re-find a sampled event by root-finding on the stored ephemeris; KP: recompute the 249 divisions from Vimśottarī proportions). Each detector ships a seeded mismatch it must catch. **Decided (SS 2026-10-01, Q13):** the cell reads PASS ONLY if every row matches, else PARTIAL (so a catalogue with any unverifiable row is PARTIAL by construction); semantic equivalence stays sampled. (R, PROVISIONAL) Ratified judgment seeds (e.g. `bg_class_priors`, the non-classical `bg_formula_constants` rows) get check-level Carr N/A by cause `ratified_judgment` from a declared fact; it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
- **Failing-first test and mutation:** Failing-first per detector: report a non-zero mismatch count on a seeded corrupted copy and zero on the real table. The proof is the seeded case, not the real-data pass.
- **Blast radius:** none for the asset; the detector is Track E tooling.
- **Rebuild:** none.
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent for the assignment of D1/D2/D3 per asset (TGH-T3-02: T3 assigns carriage at layer scope only); the detectors themselves need no tier clause.
- **Decision:** ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.

### 7. CF-04 — Dens (serving density) on the L0 served modules: applies wherever a served surface is reached; `uniform_authority` (R)

- **Why this rank:** applicability ruling first (23 assets); no rebuild; re-measure at rev 4 is needed before the count means anything.
- **Gate:** Dens; **assets:** 23 FAIL + 1 NO_DETECTOR in the saved census — bg_class_lifetime_counts, bg_class_priors, bg_compendium_index, bg_dasha_systems, bg_doshas, bg_ephemeris, bg_ephemeris_engine, bg_formula_constants, bg_medical_mappings, bg_muhurta_lattice, bg_nakshatra_medical, bg_ontology, bg_panchanga, bg_parihara_rules, bg_remedies, bg_sign_medical, bg_sky_calendar, bg_text_index, bg_texts, bg_transit_engine, bg_transit_rules, bg_vastu_directions, bg_yogas (NO_DETECTOR: bg_dignity_reference)
- **Evidence:** 0 of 46 L0 capability modules declare a `density_contract` (layer instance §1.4). The saved `Dens.served` is criterion revision 1 (file-level "modules reference the table; declaring density_contract: 0"). Main’s revision 4 (`asset_census.py`, REGISTRY_REVISION 4) passes only when ONE capability entry declares `density_contract` AND its own served read selects a tier column (`DENS_TIER_COLUMN`, `asset_census.py:2638`: `tier | *_tier | verification_pass_status`). Among the populated columns the saved census recorded for the 40 L0 target tables, the only tier-like name is `cost_tier` on `brahma_remedy_corpus` (a cost tier, not a verification tier). So under revision 4 no L0 asset can reach PASS by declaring a contract alone, and some of the 23 may read N/A (no served read) rather than FAIL; the saved figure is a rev-1 reading and a re-measure is expected.
- **Design:** **Decided (SS 2026-10-01, Q2):** Dens applies wherever an asset reaches a served surface. (R, PROVISIONAL) A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (a Track I detector item); mixed-authority tables need a real tier column. Per module: add `density_contract` (`platform/src/lib/retrieval/registry/types.ts` `CapabilityDescriptor`: `paginated`, `facets`, `empty_reason`) where the module paginates or facets; where a catalogue carries a catalog-only/confirmed distinction (yoga, doṣa: CLAUDE.md N.6) serve it through the existing flag fields. Table by table, decide uniform vs mixed authority at declaration time.
- **Failing-first test and mutation:** Per module: a response-shape test that the declared `empty_reason` is emitted on an empty page and that a trim keeps the dense layer (the `response_budget.ts` `hardFloor` pattern). Mutation: drop the declaration → the census Dens cell reads FAIL again.
- **Blast radius:** Additive response fields on the L0 retrieval tools; consumers that parse strictly would see new keys (none identified). No data change.
- **Rebuild:** none (TypeScript serving surface only).
- **Fix class:** served surface (TS) + SS ruling; **buildable before J1:** tier-dependent: TGH-T3-26 (who owns a Dens FAIL; serving is [TRANSFERS]) and the N-22 per-gate applicability rules.
- **Decision:** ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).

### 8. CF-12 — Idem: an orphan census for upsert-only writers (the Idem PASS does not test accretion)

- **Why this rank:** detector for 18 assets; protects against a repeat of migration 703; tier-dependent on the Idem meaning for upsert writers.
- **Gate:** Idem; **assets:** 18 by a static scan (indicative) — bg_class_lifetime_counts, bg_class_priors, bg_dignity_reference, bg_ephemeris, bg_formula_constants, bg_ghatana, bg_kota_chakra_rings, bg_medical_mappings, bg_muhurta_lattice, bg_nakshatra_medical, bg_parihara_rules, bg_phaladeepika_latta, bg_prashna_rules, bg_reference, bg_sign_medical, bg_sky_calendar, bg_vastu_directions, bg_vedha_malefic_scale
- **Evidence:** Saved `Idem.pattern` reads PASS for upsert writers ("INSERT … ON CONFLICT … into the asset's own table(s)"). Layer instance §5.2: a PASS does not test accretion. The documented instance: migration 703 (applied 2026-09-06) deleted 9 orphaned rows (1 from `bg_parihara_rules`, 8 from `bg_muhurta_factor_census`) after the upsert-only writer failed to remove them (layer instance CH-04). A static scan of each upsert asset's writer and delegated seed module (2026-10-01) found no `DELETE FROM` in these 18 (the other upsert assets delete or prune: `bg_ontology` `l0_ontology.py:1160-1173`, `bg_rules` `l0_rules.py:1559`, `bg_texts` `bg_texts.py:435`, …). The scan is a presence test of the text `DELETE FROM`, not proof that a table cannot hold orphans: it only selects where to look. Some of the 18 are append-only or horizon-driven by ruling (bg_class_lifetime_counts "APPEND-ONLY", `l0_class_lifetime_counts.py` header; bg_muhurta_lattice and bg_sky_calendar rolling horizons; bg_ephemeris fixed grid).
- **Design:** Add a read-only **orphan census** per upsert writer: run the writer’s produced-key computation in `ctx.dry_run` mode (supported by the frozen contract) and compare to the live natural keys; orphans = live − produced. Report per asset; PASS = 0 orphans, FAIL names them. This is the measurable form of "a rebuild replaces its own rows, never accretes" for upsert writers (the question TGH-T3-18 leaves open). Where the census finds orphans, the writer gets a prune scoped to its own natural-key partition (never a table-wide delete). Append-only-by-ruling assets declare it instead of pruning.
- **Failing-first test and mutation:** Failing-first: a fixture table with one extra row not produced by the writer → census FAIL naming it; after the prune → PASS. Mutation: widen the prune beyond the asset’s partition → the shared-table test (bg_class_priors/lifetime) fails.
- **Blast radius:** Detector: none. A prune changes data only when orphans exist (none known after migration 703).
- **Rebuild:** none for the detector; a prune is exercised by the next rebuild (no separate rebuild).
- **Fix class:** detector/tooling + writer code (prune, only if orphans are found); **buildable before J1:** tier-dependent: TGH-T3-18 (what Idem means for upsert writers); T4 §6 names L0 upsert as the convention.
- **Decision:** ANSWERED by SS 2026-10-01 (Q12): yes: 'no orphan rows under the writer's own partition' is the Idem claim for L0 upsert writers.

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

### 11. CF-11 — `classical_tradition` is not provenance: explicit attribution state `sourced | unsourced | refuted` (no invented citations)

- **Why this rank:** output change on four assets (explicit attribution state); needs SS’s answer on `classical_tradition` first; rebuild of four small assets after a migration.
- **Gate:** Ldgr (qualification), Carr; **assets:** 4 (doṣa 53, yoga 1, remedy 80 rows; transit rules 19 refuted + 6 unsourced) — bg_doshas, bg_yogas, bg_remedies, bg_transit_rules
- **Evidence:** `brahmagyan/l0_doshas.py:18-21`: "Citation policy (native decision per brief §3a): ~40 entries cite 'classical_tradition' (honest provenance for tradition-rooted doshas where no single BPHS verse names them … These are NOT fabricated citations.)". The census `Ldgr.source_presence` reads PASS because the column is populated (presence, not qualification; layer instance §1.2). 53 of 79 doṣa, 1 of 233 yoga (`l0_yogas.py:946`) and 80 remedy rows (`l0_remedy_corpus.py:263,507,526…`) carry the token.
- **Design:** **Decided (SS 2026-10-01, Q3):** B.3 forbids a claim resting on 'per tradition' without a source, so the token is NOT accepted. Add `attribution_state` ∈ `sourced | unsourced | refuted`, derived by the writer: rows citing a verse = `sourced`; `classical_tradition` rows and the Mayamata rows = `unsourced`; the 19 'BPHS Ch.29' transit rows = `refuted`. Neither `unsourced` nor `refuted` is a PASS of Ldgr/Carr. No citation is replaced by this change (B.10); re-sourcing the 19 refuted rows from the `bg_texts` corpus is a Track I research item spot-checked at the milestone review.
- **Failing-first test and mutation:** Failing-first: counts by state equal the counts the tokens give today (doṣa 53 unsourced, yoga 1, remedy 80, transit 19 refuted + 6 unsourced) and no citation changes; mutation: change a token to a verse → the state flips to `sourced`.
- **Blast radius:** Additive column; readers of the three catalogues see a new field.
- **Rebuild:** needs production rebuild: bg_doshas, bg_yogas, bg_remedies (idempotent; column add by migration first).
- **Fix class:** data (output change); **buildable before J1:** tier-independent for the state (SS decided); the Ldgr/Carr reading of `unsourced` follows the Carr rule of CF-07.
- **Decision:** ANSWERED by SS 2026-10-01 (Q3): `classical_tradition` is NOT accepted as provenance (B.3: no claim rests on 'per tradition' without a source). Give it an explicit attribution state `sourced | unsourced | refuted`; neither `unsourced` nor `refuted` is a PASS. The 19 refuted 'BPHS Ch.29' transit citations are marked `refuted`; re-sourcing them from the `bg_texts` corpus is a Track I research item, spot-checked at the milestone review.

### 12. CF-10 — Build.history PARTIAL is a record of past errors; no edit changes it

- **Why this rank:** a definition question; no edit can change a history record.
- **Gate:** Build (history); **assets:** 13 — bg_class_lifetime_counts, bg_cohort, bg_compendium_index, bg_dasha_systems, bg_doshas, bg_formula_constants, bg_gochara_arcs, bg_kp_sublord_division, bg_parihara_rules, bg_reference, bg_remedies, bg_vidhi_floors, bg_yogas
- **Evidence:** Each reads "latest run complete, but N error(s) and M abort(s) on record" (T4 §4.2 check 8: PARTIAL if it has errored before and the latest run completed). Seven carry the identical error `post-write integrity check failed: integrity_check_sql → False` (2026-09-04 … 2026-09-06). The latest runs completed; no repair of the asset can remove the old rows.
- **Design:** Decided (SS 2026-10-01, Q11): Build.history counts only runs since the last change to the asset's writer or registry row (a Track I detector item); a repaired error then stops counting. No asset edit.
- **Failing-first test and mutation:** n/a (definition).
- **Blast radius:** none.
- **Rebuild:** none.
- **Fix class:** detector/tooling (definition); **buildable before J1:** tier-dependent: T4 §4.2 check 8 wording.
- **Decision:** ANSWERED by SS 2026-10-01 (Q11): yes: Build.history counts only runs since the last change to the writer or the registry row.

## 5 · Rebuild consequences Track B needs per asset (facts found while reading the writers)

These are not gaps; they are what a level-by-level L0 rebuild (B.L0.0-B.L0.3, global request) must plan for (N-29 impact statement, rebuild plan, pre/post fingerprints). DAG depth from the layer instance §2.5: depth 0 (24 assets), 1 (11), 2 (4: bg_compendium_index, bg_parihara_rules, bg_rules, bg_text_index), 3 (1: bg_concordance).

- **`bg_texts` (depth 0, retained capital):** only `additive` and `metadata_only` rebuild modes exist; no mode deletes chunks (`bg_texts.py:388-396`); the corpus is recoverable only while the GCS bucket survives (non-regenerable inventory). A rebuild is expected to change nothing; fingerprint per text must be equal before and after.
- **`bg_formula_constants` (depth 0, retained capital):** the upsert overwrites `value_jsonb`/`bounds` of the 10 seeded constants, 8 of them `calibratable`; 7 more rows are migration-seeded and not produced by the writer. Record the live values before any rebuild; the guard in its FD-2 should land first.
- **`bg_ephemeris` and its dependents:** any change to stored values reaches `bg_gochara_arcs` (R9) and five Kāla assets; the table is TRUE-node while the engine/panchang standard is MEAN_NODE (a convention split, not a defect to fix in a wave). Rename of `body` values is NOT recommended (46 readers).
- **`bg_muhurta_lattice`, `bg_sky_calendar`:** rolling horizons computed from `today` at run time; fingerprints must use a fixed as-of window; `bg_sky_calendar` is `DO NOTHING`, so a corrected computation does not repair existing rows.
- **`bg_transit_rules`:** SERIAL `id` is FK-referenced by `gochara_resonance_map` (migration 459); retirement is ownership-scoped (`_owned_row_filter`); 7 rows are migration-owned; 19 rows carry a refuted citation pending re-verification.
- **`bg_rules`:** the writer deletes all `python_regex_v2` rows before every re-seed (`l0_rules.py:1558-1560`) and then inserts with `ON CONFLICT (rule_id) DO NOTHING`, which never conflicts: a rebuild already reproduces every row and no backfill is needed (the premise of SS Q9 'change to DO UPDATE' is corrected; Q22 asks whether `DO UPDATE` is still wanted defensively). `rule_id` is content-based, so concept columns do not change ids; readers include L2 `bo_grounding.py` and `bo_laksana.py`.
- **`bg_ontology` and the co-writers:** identity-mapping changes (the `text` class) have a real invalidation path; additive alias sets do not. Order: `bg_ontology` (level 0) → `bg_doshas`, `bg_dasha_systems`, `bg_yogas`, `bg_reference`, `bg_remedies` (level 1) → `bg_rules` (2) → `bg_concordance` (3).
- **R9 assets (`bg_gochara_arcs`, `bg_gochara_citation_resolution`):** analysed here; any rebuild waits for SS after notifying Pravāha. Anything that changes `bg_ephemeris` or `bg_texts` reaches them.
- **Services (`bg_ephemeris_engine`, `bg_panchanga`):** no table, no rebuild; their status is a `lit` row no probe can read false.

## 6 · Dispositions that differ from the layer instance (v3.1 §3.2), and who approves

| asset | layer instance | this index | reason |
|---|---|---|---|
| bg_class_lifetime_counts, bg_class_priors | C (consolidation candidate) | keep | different governing rulings (ADJUDICATION-2 source tiers vs the judgment seed package); count_sql already partition-scopes each; T2 §10.1 C needs a proven shared authority |
| bg_prashna_rules | I (declare its table set) | keep | census now reads Build.target PASS for the multi-table asset; no discovery/projection/join repair identified |
| bg_yogas | P (with a must-add left to this lane) | enrich, narrowed after Q20 (pending) | the four DP05 columns were deferred by SS (Q20), so what remains is an explicit `attribution_state` on the 233 catalogue rows (one `unsourced`) and declared null reasons for the four empty columns; if SS reads that as too thin for E the alternative is keep with the same fixes |
| bg_doshas | E | enrich (narrowed) | alias sets stay; the citation half becomes an explicit attribution state because the code cites a native decision for the token |
| bg_text_index | I | integrate (narrowed) | declare the grain/unit once; SS routes it |

**Accepted:** SS accepted all dispositions as proposed (2026-10-01, Q10), including the four changes above. Approval of the fixes follows Track A §10: keep/qualify/enrich to the Steward, any output change to SS (R5); the answers in section 7 and the Track I items in section 8 record which output changes SS has already decided.

## 7 · Questions for Strategic Suvarṇa: ANSWERED 2026-10-01

All 20 questions were ANSWERED by SS on 2026-10-01; two new questions (21, 22) are open. The open question is replaced by the answer; (R) marks an answer that changes a verdict or criterion definition and is PROVISIONAL until the J1 review.

1. *CF-01: is a converged-rerun `rows_written = 0` a Build.completion PASS (8 assets)?* ANSWERED by SS 2026-10-01 (Q1): CF-01 option A (R, PROVISIONAL until the J1 review): a converged rerun with `rows_written = 0` reads Build.completion PASS ONLY IF the writer declares the changed-rows convention AND count_integrity PASSes on populated rows; completion is proven by the count, not by `rows_written`.
2. *CF-04: does Dens apply to L0 reference vocabularies without a verification tier (23 assets)?* ANSWERED by SS 2026-10-01 (Q2): Dens applies wherever an asset reaches a served surface. A reference vocabulary of uniform authority declares `uniform_authority: true` in the declarations file and Dens then PASSes on `density_contract` facets without a tier column (R, PROVISIONAL until the J1 review); mixed-authority tables need a real tier. Re-measure first with the current inspector (done offline here, see INDEX section 9).
3. *CF-11: is `classical_tradition` accepted provenance (doṣa 53, yoga 1, remedy 80, transit 19 refuted + 6 unsourced)? who re-verifies the 19 refuted citations?* ANSWERED by SS 2026-10-01 (Q3): `classical_tradition` is NOT accepted as provenance (B.3: no claim rests on 'per tradition' without a source). Give it an explicit attribution state `sourced | unsourced | refuted`; neither `unsourced` nor `refuted` is a PASS. The 19 refuted 'BPHS Ch.29' transit citations are marked `refuted`; re-sourcing them from the `bg_texts` corpus is a Track I research item, spot-checked at the milestone review.
4. *CF-09: where does the normalisation rule live; release id in the first wave; identity option for the 11 two-class ids; the three ontology-only text ids; Abhijit?* ANSWERED by SS 2026-10-01 (Q4): the normalisation rule lives in the `bg_ontology` writer, the one authority; the vocabulary release id goes in the first wave if it is cheap; for the 11 two-class ids take the recommended option (a, class-aware resolvers) unless it changes served ids (then REVIEW to SS); of bhrigu_samhita, jaimini_sutram, lal_kitab_text keep any with a consumer and remove the rest; Abhijit is a declared exception (classically intercalary) and the 27-id class stays canonical.
5. *bg_ephemeris: TRUE vs MEAN node; body-name normalisation; the notify-Pravāha route before any wave touches bg_ephemeris/bg_texts (R9)?* ANSWERED by SS 2026-10-01 (Q5): authority-side declaration with NO stored-value change: `bg_ephemeris` declares `node: TRUE`; consumers needing MEAN must not read node values from it (a check, Track I item); body-name normalisation is declared the same way. BEFORE any wave touches `bg_ephemeris` or `bg_texts`, SS notifies Pravāha (Exec sends SS an ASK first).
6. *CF-02/CF-03 riders: does a sibling’s dispatch count; may the R61 cascade stand until the first L0 dispatch?* ANSWERED by SS 2026-10-01 (Q6): a sibling's dispatch counts (`producer_covered`) when the registry declares the rider relation; the R61 cascade may stand until the first L0 dispatch.
7. *Static migration-seeded assets: N/A by rule or a dispatchable writer?* ANSWERED by SS 2026-10-01 (Q7): static migration-seeded assets get a DISPATCHABLE writer that re-seeds from the git source (delete-then-insert), which makes Build measurable and ELEVATED reachable (Track I item; R9 assets wait for SS after notifying Pravāha). (The case of `bg_sarvatobhadra_grid`, empty by ruling, was not covered: see open question Q21.)
8. *bg_formula_constants: where do calibrated values live; scope of count_sql?* ANSWERED by SS 2026-10-01 (Q8): L0 holds seeds only; calibrated values belong to L5 storage later and the L0 upsert must never overwrite them; scope `count_sql` to the ten writer rows.
9. *bg_rules: concept backfill vs `DO UPDATE`; `confidence`; `dasha_system_id`?* ANSWERED by SS 2026-10-01 (Q9): change the writer to `DO UPDATE` so a rebuild reproduces the concept ids and do NOT backfill; `confidence`: no fake score (CLAUDE.md N.7): if it does not discriminate the writer sets it NULL and documents why (dropping the column later is a REVIEW); `dasha_system_id`: populate if a source exists, otherwise NULL (removal later is a REVIEW). **PREMISE CORRECTED by the review pass: see open question Q22.**
10. *Dispositions (keep for the two class-prior assets and prashna_rules; integrate for text_index; enrich for yogas)?* ANSWERED by SS 2026-10-01 (Q10): all dispositions accepted as proposed.
11. *CF-10: Build.history window?* ANSWERED by SS 2026-10-01 (Q11): yes: Build.history counts only runs since the last change to the writer or the registry row.
12. *CF-12: the Idem claim for L0 upsert writers?* ANSWERED by SS 2026-10-01 (Q12): yes: 'no orphan rows under the writer's own partition' is the Idem claim for L0 upsert writers.
13. *CF-07: is D1 anchor-term matching an acceptable L0 carriage detector; Carr for ratified judgment seeds?* ANSWERED by SS 2026-10-01 (Q13): D1 anchor-term matching is accepted as the L0 carriage detector, but the cell reads PASS ONLY if every row matches, else PARTIAL; semantic equivalence is sampled. Ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (R, PROVISIONAL until the J1 review); it becomes a rule in `NA_RULE_DECISIONS` only via SS approval.
14. *bg_vidhi_floors: what does DRAFT block; who ratifies the two CANDIDATE floors?* ANSWERED by SS 2026-10-01 (Q14): `catalog_status = DRAFT` blocks certification while DRAFT; SS ratifies the deep-dive floors after the milestone independent review.
15. *Duplicate authority: combustion orbs in `bg_combustion_orbs` and `brahma_formula_constants`?* ANSWERED by SS 2026-10-01 (Q15): one authority: `bg_combustion_orbs` holds the values and `brahma_formula_constants` references it rather than duplicating it (Track I consolidation item).
16. *bg_panchanga edge target?* ANSWERED by SS 2026-10-01 (Q16): declare `bg_ephemeris_engine` (what the code actually calls).
17. *bg_concordance: chunk-level pointers in scope?* ANSWERED by SS 2026-10-01 (Q17): text-level carriage is the contract for now; chunk-level pointers are an opportunity, deferred.
18. *bg_vastu_directions: Mayamata admitted to the corpus or recorded as outside it?* ANSWERED by SS 2026-10-01 (Q18): record the Mayamata rows as outside the corpus (explicitly `unsourced`) for now; admitting the text is an opportunity.
19. *bg_cohort: report both tables or scope count_sql?* ANSWERED by SS 2026-10-01 (Q19): scope `count_sql` to the primary table and declare the asset multi-table.
20. *bg_yogas: the four DP05 columns in the first wave?* ANSWERED by SS 2026-10-01 (Q20): the four DP05 columns are out of the first wave unless a source-grounded extraction already exists; an opportunity otherwise.

**Open after the SS answers (raised by the independent review of this index):**

21. OPEN (raised by the review pass; not covered by Q7): `bg_sarvatobhadra_grid` is empty BY RULING (ADJUDICATION-11), not a migration-seeded static table with rows. Q7 decided that static migration-seeded assets get a dispatchable re-seeding writer; does that apply to an asset whose correct content is zero rows (the writer would assert 0 rows by delete-then-insert of nothing)? Until SS answers, TI-L0-20 builds the writer only for `bg_gochara_citation_resolution`.

22. OPEN (premise corrected): SS Q9 said 'change the writer to DO UPDATE so a rebuild reproduces the concept ids'. The premise does not hold: `l0_rules.py:1558-1560` runs `DELETE FROM sutravali_rules WHERE extracted_by = 'python_regex_v2'` before every re-seed, so `ON CONFLICT (rule_id) DO NOTHING` (`:1622`) never conflicts and a rebuild already reproduces every concept id. Is `DO UPDATE` still wanted as a defensive change (it would matter only if the delete were ever removed)? Default if unanswered: leave the clause, no backfill.


## 8 · Track I items arising (from the SS answers and the shared fixes)

Id, asset(s), fix, class, rebuild needed, source decision. Class set: registry / declaration / writer code / detector / research. `y` items are REVIEW items for SS at their level (production rebuild or dispatch). Items marked (R) change a verdict or criterion definition and are PROVISIONAL until the J1 review. Fix designs remain in the per-asset briefs (§4) and in section 4 here.

| id | asset(s) | fix | class | rebuild | from |
|---|---|---|---|---|---|
| TI-L0-01 | bg_ephemeris, bg_muhurta_lattice, bg_ontology, bg_reference, bg_sky_calendar, bg_text_index, bg_texts, bg_vidhi_primitives | declare the changed-rows convention (writer `file:line` evidence) in the declarations file | declaration | n | Q1 (R) |
| TI-L0-02 | inspector (all layers) | Build.completion rule: `rows_written = 0` is PASS only if the convention is declared AND count_integrity PASSes on populated rows | detector | n | Q1 (R) |
| TI-L0-03 | every L0 asset that reaches a served surface (offline Dens list, INDEX section 9) | `uniform_authority: true` declaration for uniform-authority vocabularies; decide table by table which are mixed-authority and need a real tier | declaration | n | Q2 (R) |
| TI-L0-04 | inspector | Dens: PASS on `density_contract` facets without a tier column when `uniform_authority: true` | detector | n | Q2 (R) |
| TI-L0-05 | the 23 offline FAIL or PARTIAL Dens assets (INDEX section 9.1) | `density_contract` facets on the L0 capability modules that paginate or facet | writer code (served TS) | n | Q2 |
| TI-L0-06 | 35 assets with `prose_fields: null` | prose_fields declarations with writer `file:line` evidence (CF-06) | declaration | n | CF-06 |
| TI-L0-07 | bg_parihara_rules, bg_nakshatra_medical, bg_transit_engine | one surgical registry migration: parihara floor 449→440, `has_writer` true for the two riders (R61 cascade may stand) | registry | n | Q6 |
| TI-L0-08 | bg_sign_medical, bg_nakshatra_medical, bg_transit_engine | declare the rider relation (`producer_covered`) in the registry so a sibling’s dispatch counts | registry | n | Q6 |
| TI-L0-09 | bg_doshas, bg_yogas, bg_remedies, bg_transit_rules | explicit attribution state `sourced \| unsourced \| refuted` (additive column + writers); `classical_tradition` rows read `unsourced` and the 19 refuted transit rows `refuted`; no state other than `sourced` is a PASS (bg_vastu_directions: declaration only, TI-L0-33) | writer code | y | Q3 |
| TI-L0-10 | bg_transit_rules (+ the corpus `bg_texts`) | mark the 19 refuted "BPHS Ch.29" citations `refuted` (in TI-L0-09) and re-source them from the `bg_texts` corpus, row by row with the verified predicate; spot-checked at the milestone review | research | y (after re-sourcing) | Q3 |
| TI-L0-11 | bg_ontology | normalisation rule in the `bg_ontology` writer (one authority); vocabulary release id in the first wave if cheap | writer code | y | Q4 |
| TI-L0-12 | bg_doshas, bg_ontology | closed alias sets for the 79 doṣa ontology rows (convention read from the 15 complete classes) | writer code | y | CF-09 |
| TI-L0-13 | bg_ontology (+ bg_remedies, bg_rules beneficiaries) | reconcile the `text` class with the corpus: derive from the corpus, add the 3 corpus-only ids, keep ontology-only ids that have a consumer (referrer census first) and remove the rest | writer code | y | Q4 |
| TI-L0-14 | bg_ontology consumers (`resolve_entity.ts`) | class-aware resolution for the 11 two-class ids (option a); REVIEW to SS if it changes served ids | writer code (served TS) | n | Q4 |
| TI-L0-15 | bg_ontology (`list_entities.ts`) | make `yoga` and `dosha` listable; delete the false UNBACKED branch; update the honesty test | writer code (served TS) | n | CF-09 |
| TI-L0-16 | bg_nakshatra | declare Abhijit an exception (classically intercalary); the 27-id class stays canonical; no ontology row added | declaration | n | Q4 |
| TI-L0-17 | bg_ephemeris | declare `node: TRUE` and the body-name normalisation at the authority; no stored-value change | declaration | n | Q5 |
| TI-L0-18 | consumers of `ephemeris_daily` node columns | check that a consumer needing MEAN node does not read node values from bg_ephemeris | detector | n | Q5 |
| TI-L0-19 | process: any wave touching bg_ephemeris or bg_texts | Exec sends SS an ASK first; SS notifies Pravāha before the wave | research (process REVIEW) | n | Q5 |
| TI-L0-20 | bg_gochara_citation_resolution (R9), bg_sarvatobhadra_grid (confirm: empty by ruling) | dispatchable writer re-seeding from the git source (delete-then-insert) so Build is measurable; R9: waits for SS after notifying Pravāha. bg_sarvatobhadra_grid is NOT covered by Q7 (empty by ruling): OPEN Q21 | writer code | y | Q7 |
| TI-L0-21 | bg_formula_constants | scope `count_sql` to the ten writer rows; seed-once guard so an L0 upsert never overwrites a calibrated value | registry + writer code | n | Q8 |
| TI-L0-22 | bg_formula_constants, bg_dignity_reference | combustion orbs: `bg_combustion_orbs` is the sole authority; replace or remove the duplicate `combustion_orbs` constant and correct its `consumer_assets` (traced: `ga_condition_writer.py:657-663` and `ka_vighnakara.py:295-302` already read the orbs table; `ph_sodhana.py` has no reference; no reader of the constant by id found; nothing to repoint) | writer code | y | Q15 |
| TI-L0-23 | bg_rules | concept ids populated by the families; NO backfill; `confidence` NULL with documentation; `dasha_system_id` from a source else NULL; the `DO UPDATE` change is OPEN as Q22 (premise corrected: the writer already deletes `python_regex_v2` rows before re-seeding, `l0_rules.py:1558-1560`) | writer code | y | Q9 |
| TI-L0-24 | inspector | Build.history counts only runs since the last change to the writer or registry row | detector | n | Q11 |
| TI-L0-25 | 18 upsert writers (CF-12), bg_parihara_rules first | orphan census (dry-run produced keys vs live keys) and a partition-scoped prune where orphans exist | detector | n | Q12 |
| TI-L0-26 | inspector | Carr D1 anchor-term detector: PASS only if every row matches, else PARTIAL; semantic equivalence sampled | detector | n | Q13 |
| TI-L0-27 | bg_class_priors, bg_formula_constants (non-classical rows) | declared fact for ratified judgment seeds → check-level Carr N/A by cause `ratified_judgment` (rule in `NA_RULE_DECISIONS` only via SS approval) | declaration | n | Q13 (R) |
| TI-L0-28 | bg_vidhi_floors, bg_vidhi_primitives | declare that DRAFT blocks certification; register the existing CI parity gate as the Carr detector | declaration + detector | n | Q14 |
| TI-L0-29 | bg_panchanga | declare the edge `bg_panchanga → bg_ephemeris_engine` (own review: upstream hash) | registry | n | Q16 |
| TI-L0-30 | bg_cohort | scope `count_sql` to `bg_synthetic_cohort` and declare the asset multi-table | registry | n | Q19 |
| TI-L0-31 | bg_yogas | declared null reasons for the four DP05 columns; extraction deferred (opportunity) | declaration | n | Q20 |
| TI-L0-32 | bg_medical_mappings, bg_transit_rules | writer reports its own partition in `rows_written` (CF-02; the medical riders share the writer), including `bg_transit_moorti` as a declared produced table; record-only: the rebuild writes a new build record, no row changes | writer code | y | CF-02 |
| TI-L0-33 | bg_vastu_directions | declare the Mayamata rows explicitly `unsourced` (source outside the corpus); no row, column or rebuild | declaration | n | Q18 |

**33 items.** By class: declaration 9, detector 6, registry 5, research 2, writer 11. Rebuild y: TI-L0-09, TI-L0-10, TI-L0-11, TI-L0-12, TI-L0-13, TI-L0-20, TI-L0-22, TI-L0-23, TI-L0-32.

## 9 · Decisions applied (one page)

SS accepted every disposition as proposed (Q10), so the disposition counts stand: enrich 5, integrate 1, keep 32, qualify 2. The answers that change a **verdict or a criterion definition** are the three marked (R), PROVISIONAL until the J1 review; route these to the E6 detector work:

| Q | decision | what changes in the inspector | where it lands |
|---|---|---|---|
| 1 (R) | CF-01 option A: a converged rerun with `rows_written = 0` reads Build.completion PASS only if the writer declares the changed-rows convention AND count_integrity PASSes on populated rows | Build.completion verdict rule; a new declared fact (changed-rows convention + writer `file:line`) | TI-L0-01, TI-L0-02 |
| 2 (R) | Dens applies wherever a served surface is reached; `uniform_authority: true` lets a uniform-authority vocabulary PASS on `density_contract` facets without a tier column; mixed-authority tables need a real tier | Dens.served (PASS rule without a tier column when `uniform_authority`); a new declared fact; the N/A reading of "no served surface" is unchanged | TI-L0-03, TI-L0-04, TI-L0-05 |
| 13 (R) | Carr D1 anchor-term matching is the L0 carriage detector; PASS only if every row matches, else PARTIAL; ratified judgment seeds get check-level Carr N/A by cause `ratified_judgment` from a declared fact (a rule in `NA_RULE_DECISIONS` only via SS approval) | Carr D1 grading rule (every row); a new N/A cause `ratified_judgment` | TI-L0-26, TI-L0-27 |

Other answers that change a **detector input or the build/registry, not a criterion definition**: Q11 (Build.history window: TI-L0-24; this does change what the cell counts, so route it with the three above), Q12 (CF-12 orphan census as the Idem claim: TI-L0-25), Q3 (attribution state: Ldgr/Carr read `unsourced`/`refuted` as not PASS: TI-L0-09), Q5 (node declaration and check: TI-L0-17, TI-L0-18). All others are registry, declaration or writer work with no criterion change.

### 9.1 Dens re-measured offline with the current scanner (Q2 asked for a re-measure first)

Method: main's `capability_scan` and `_grade_dens` (`asset_census.py`, REGISTRY_REVISION 6 at the time; main is now at 7 with no L0 verdict change) were run over the 40 L0 assets with the saved census's populated-column lists standing in for the database column catalog and the saved count-sql tables for the shared-table set. This re-measures the **served-surface attribution** exactly as the current scanner does it; the tier-column part uses the saved populated columns, not information_schema. Output: `/Users/Dev/suvarna-evidence/A_L0/dens_offline_rev6.json`. Not a certifying measurement.

Result: FAIL 18, N/A 3, NO_DETECTOR 14, PARTIAL 5 (the saved rev-1 run read FAIL 23 · NO_DETECTOR 1 · N/A 16). The scanner now also attributes modules in L1, L3, L4 and L5 directories and platform-mcp that read an L0 table, which is why N/A fell from 16 to 3. `PARTIAL` means a referencing capability declares a `density_contract` but its tier carriage is not established (for example `L1_ganita/get_yoga_firings.ts` for `bg_yogas`). NO_DETECTOR means the table is named only outside the scanned serving roots or no served `SELECT … FROM` was found.

| verdict | assets |
|---|---|
| FAIL | bg_class_lifetime_counts, bg_compendium_index, bg_dasha_systems, bg_doshas, bg_ephemeris, bg_formula_constants, bg_gochara_citation_resolution, bg_medical_mappings, bg_muhurta_lattice, bg_nakshatra, bg_nakshatra_medical, bg_parihara_rules, bg_prashna_rules, bg_rules, bg_sign_medical, bg_sky_calendar, bg_transit_engine, bg_transit_rules |
| PARTIAL | bg_dignity_reference, bg_ghatana, bg_remedies, bg_vastu_directions, bg_yogas |
| NO_DETECTOR | bg_class_priors, bg_cohort, bg_concordance, bg_ephemeris_engine, bg_ontology, bg_panchanga, bg_phaladeepika_latta, bg_reference, bg_sarvatobhadra_grid, bg_text_index, bg_texts, bg_vedha_malefic_scale, bg_vidhi_floors, bg_vidhi_primitives |
| N/A | bg_gochara_arcs, bg_kota_chakra_rings, bg_kp_sublord_division |

Under Q2 the FAIL and PARTIAL assets are the ones that must declare `density_contract` facets (and `uniform_authority: true` where the table is a uniform vocabulary); NO_DETECTOR assets need a `carriage` declaration with `read_evidence` so the scanner can attribute their served surface; N/A assets stay N/A.

## 10 · Notes on method and path

- **Path:** per Track A brief §8: `00_ARCHITECTURE/briefs/suvarna/layers/<Lx>/assets/<ASSET_ID>_ELEVATION_BRIEF_v1_0.md` (revalidation bumps to v1.1). **Fix designs live inside each brief (§4)**, not in separate `designs/` files; `INDEX.md` sits beside the briefs.
- **Quoted census text keeps its original `file:line`** (the saved run read older code than main: for example `l0_rules.py:1608` in the saved Idem text is `:1622` today); line numbers in the briefs’ own prose were re-read on 2026-10-01.
- **Gap classification** (real / detector / stale / history / information / opportunity) is this lane's reading of the saved census and ledger; no tier supplies a rule mapping evidence to a disposition (TGH-T3-03).
- **Fixes go in the asset or the registry, never in the frozen orchestrator** (T4 §4.2): every design respects that; the one option that would need an orchestrator change (persisting `rows_skipped`, CF-01 option C) was not taken.
- **Facts not established offline** are marked in the briefs (the unnamed third dependent of `bg_rules`, live column lists for the multi-table assets).
- **Answers applied 2026-10-01:** each brief §7 lists the decisions that apply to it. Two questions are open (Q21 in `bg_sarvatobhadra_grid`, Q22 in `bg_rules`); no other brief carries one.
- **Variance from Track A §5/§8 (pending SS acknowledgement; SS may approve the variance or ask for the template form):** (1) the briefs use their own section numbering (§0–§7) rather than the T4 template’s §0–§9; (2) there is no separate "obligations specialised" section (T4 §3): obligations are carried by the layer instance and the per-asset §6/§4; (3) there is no explicit thirteen-row inherited table (T4 §0.1): the rows are covered piecemeal in §0, §1, §5 and §6, and rows 1, 3, 4, 5, 6, 8–13 are not stated one by one; (4) there is no `L0_DISPOSITIONS_v1_0.md` (Track A §8): dispositions are in each brief §3 and in this INDEX §2, §3 and §6; (5) fix designs live inside each brief (§4) instead of `designs/<ASSET_ID>_FIX_DESIGN_v1_0.md`; (6) the gate table is per criterion with a rollup line, not the nine-row T4 §4 table with a detector column. No restructuring of the 40 briefs has been done.

## 11 · Format used (reuse for the next layers)

Each brief is `<ASSET_ID>_ELEVATION_BRIEF_v1_0.md` with this frontmatter and section list:

- **Frontmatter:** asset_id, layer, artifact, version, status (PROVISIONAL banner), produced_by, produced_on, plan_item, census_revision_used, template_revision, layer_instance, base_commit, disposition, disposition_proposal_approver, decisions_applied, track_i_items, ledger_gap_ids.
- **§0 Identity:** what the asset is (cited file:line), then a field table (kind, seed row, writer/`@register`, target tables, live rows/floor, catalog_status, intra-layer depends_on, blast radius, code readers declared-vs-actual, served surface, role/scoring mode).
- **§1 Measured state and the nine gates:** saved-census per-criterion table (non-PASS in full, PASS compact, `†` for criteria whose definition changed), plus the offline rollup line.
- **§2 Gaps:** table of gap id, gate, class (real / detector / stale / history / information / opportunity), note.
- **§3 Disposition:** value, reasoning, approver under Track A §10, SS decision.
- **§4 Fix designs:** one FD per real gap (answers, change, files/migration, failing-first test and mutation, output change, blast radius, rebuild, gate moved, fix class, buildable before J1, decision), then the shared fixes (CF-nn) that apply. **Fix designs live inside each brief (§4).**
- **§5 Semantic fingerprint contract** (natural key, volatile columns, rebuild expectation).
- **§6 Preserved kernel, carriage check chosen (one of D1/D2/D3), opportunities.**
- **§7 Decisions applied** (SS answers that bear on the asset; (R) items provisional) and the Track I items arising.

`INDEX.md` carries: what the index rests on and what is stale, rollup counts, the asset table, shared fixes ordered for J1 with their decisions, rebuild consequences, dispositions that differ from the layer instance, the SS questions with their answers, the Track I items table, decisions applied, the offline Dens re-measure, method notes, and this section.

