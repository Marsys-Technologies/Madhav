---
artifact: ASSET_ELEVATION_BRIEF_INDEX
layer: L1 Gaṇita (ga_*)
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L1 (briefs, dispositions, designs)
base_commit: "main 3311b0a06"
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L1.json` (generated 2026-09-30T20:22:28+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr); the `ga_prashna` cells are read from the post-grant rerun `census/after_reader_grant/census_L1.json` (generated 2026-09-30T20:30:02+05:30; every other cell identical). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L1/L1_LAYER_INSTANCE_v1_0.md (1.0-rev1, PROVISIONAL)"
briefs: 19 (one per L1 asset, `<ASSET_ID>_ELEVATION_BRIEF_v1_0.md` in this directory, per Track A brief §8)
---

# L1 asset briefs — layer index (provisional)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Every figure is from the repository or the saved census (B.10). Nothing in this directory certifies a gate or approves a disposition: dispositions are proposals under Track A brief §10, and every fix marked **needs production rebuild** (or dispatch) is a REVIEW item for Strategic Suvarṇa.

## 1 · What this index rests on, and what is stale

- **Census used:** saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L1.json` (generated 2026-09-30T20:22:28+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr); the `ga_prashna` cells are read from the post-grant rerun `census/after_reader_grant/census_L1.json` (generated 2026-09-30T20:30:02+05:30; every other cell identical). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.
- **Population:** the census lists 19 active `ga_*` assets (`population_registry_total` 19, none excluded, 19 registered ids, no phantoms). `ga_chart_service` is not a registry asset and does not appear in the census or the seed, so it has no brief; the layer instance and CLAUDE.md §E describe it as a service beside the assets.
- **Layer instance:** `L1_LAYER_INSTANCE_v1_0.md` (1.0-rev1) is the draft these briefs continue (code read at `origin/main e2352f88` there; this lane reads main `3311b0a06`). It proposes no dispositions (TG-L1-017: no evidence→letter rule); the letters below are this lane's proposals (§6).
- **Gap ids** are ledger `asset_gaps.jsonl` ids from the census checkout (`/Users/Dev/suvarna-census/00_ARCHITECTURE/control/asset_gaps.jsonl` @ 2a78ec64d: 114 L1 rows, all OPEN, of which Idem.pattern ×18 is stale against the saved census); that ledger is **not on main**. Rows tagged `brief:` in the briefs are this lane's own and have no ledger id.
- **Re-measure:** not possible in this lane (no DB). The repo's own code was run **offline over the saved measurements**, labelled so everywhere: `asset_census.py` `rollup_census` (REGISTRY_REVISION 6) and its Dens.served rev-4 scanner over this tree, and the Null/Narr graders over the declarations file plus a DDL-derived column stand-in (scripts and outputs: `/Users/Dev/suvarna-evidence/A_L1/offline_rollup_L1.py`, `offline_narr_null_L1.py`, `rollup_saved_L1.json`, `narr_null_offline_L1.json`). A real re-measure by the current inspector is expected before any verdict is read.

**Criteria whose definition changed on main since the saved run (gates affected: Build, Dens, Idem; Null and Narr did not exist):** checked by diffing `CRITERION_REGISTRY` revisions of `2a78ec64d` against main.

- `Build.dag`: rev 1 -> 2 (three clauses: any-layer unknown dep, cycle, reads-match against the writer's SQL; L0 bedrock reads exempt as `bedrock_exempt`, SS 2026-10-01, provisional pending J1; `chart_facts` satisfied by any producer in the declared transitive closure)
- `Build.target`: rev 1 -> 2 (declared service with no `target_table` reads PASS by declaration; no L1 asset is a service)
- `Idem.pattern`: rev 1 -> 2 (relative imports resolve; update-only reading; verdicts identical on the 127 saved writers; no L1 writer is update-only)
- `Dens.served`: rev 1 -> 4 (needs a `density_contract` AND a tier column in the served select; comment-only mentions no longer count)
- `Narr.agree/checkable/fidelity_test/lint` and `Null.schema_default/blank_rows` (new at REGISTRY_REVISION 5): not in the saved census; declarations 1.6.0 gives `prose_fields: ["citation_human"]` for 11 of 19 L1 assets, none `[]`, 8 `null`
- Unchanged since the saved run: `Build.completion` (rev 2, R99 already in), `Build.history`, `Build.exercised`, `Count.floor`, `Complete.*`, `Vocab.identity`, `Ldgr.source_presence`, `Carr.detector`, `Reach.fields`.
- `NA_RULE_DECISIONS` is empty on main (`asset_census.py:243`): a measured N/A reads NO_DETECTOR in the rollup, so the offline rollup is harsher than an N/A-aware reading.
- Registry moved since the census: migration 1210 (12 direct `depends_on` edges, Track I) adds direct dependents to four L1 producers (`ga_vichara` +2, `ga_dashas` +2, `ga_vargas` +1, `ga_yoga` +1) and changes no L1 consumer row; its sibling 1211 (5 edges, all non-L1 producers) is held. Live production was not re-read: counts and floors are the saved ones.

## 2 · Rollup counts

**Dispositions proposed (19):** keep 16, enrich 2 (`ga_ayurdaya`, `ga_yoga`), qualify 1 (`ga_prashna`); integrate 0, consolidate 0, historical 0, retire 0, unresolved 0.

**Gap rows across the 19 briefs (162 rows):** real 50 · SS question 14 · detector 45 · history 20 · stale 6 · information 22 · opportunity 1 · PASS-note 4.

**Saved census cells over the layer (370; `ga_prashna` from the post-grant rerun):** FAIL 7 · PARTIAL 28 · NO_DETECTOR 62 · ERRORED 0 · PASS 232 · N/A 3 · NOT_GENERIC 38. FAIL by criterion: Build.completion 4 (`ga_condition`, `ga_strength`, `ga_structural`, `ga_vargas`) · Count.floor 2 (`ga_vargas`, `ga_yoga`) · Build.history 1 (`ga_positions`). (The first run read PARTIAL 27 / ERRORED 1 because `suvarna_reader` lacked SELECT on `ga_prashna_lagna`; the grant cleared it.)

**Nine-gate cells, offline rollup of the saved measurements under main's rules (assets of 19; not a re-measure, not a certification):**

| gate | Ldgr | Idem | Earn | Null | Vocab | Carr | Narr | Dens | Build |
|---|---|---|---|---|---|---|---|---|---|
| rollup | NO_DETECTOR 6 · PASS 13 | PASS 19 | NO_DETECTOR 19 | NO_DETECTOR 19 | NO_DETECTOR 19 | NO_DETECTOR 19 | NO_DETECTOR 19 | NO_DETECTOR 2 · PASS 17 | FAIL 5 · PARTIAL 14 |

Two criteria the saved census predates, re-scanned offline with main's own code: **Dens.served rev 4** reads PASS 3 · PARTIAL 7 · NO_DETECTOR 9 (saved rev 1: PASS 17 · NO_DETECTOR 1 · N/A 1); **Null/Narr graders** over the declarations: Narr.agree NO_DETECTOR 8 PARTIAL 3 PASS 8; Narr.checkable NO_DETECTOR 19; Narr.fidelity_test NO_DETECTOR 8 PARTIAL 11; Narr.lint NO_DETECTOR 13 PARTIAL 1 PASS 5; Null.blank_rows NO_DETECTOR 19; Null.schema_default NO_DETECTOR 8 PARTIAL 11 (`Narr.checkable` and `Null.blank_rows` are INCONCLUSIVE everywhere: no row data).

## 3 · Assets × disposition × gaps × fix class × rebuild

Columns: **real** = a shortfall in rows/writer/registry/served surface; **SS q.** = real or not depends on a ruling; **detector** = NO_DETECTOR or definition-open; **other** = history + stale + information + opportunity + PASS-note; **rebuild** y = a fix needs a production rebuild of this asset, cond = only under one option, cascade = re-earned only because `ga_vargas` is restored (CF-16), n = none. **Shared fixes** are the CF ids whose brief section applies to the asset.

| asset | disposition | real | SS q. | detector | other | fix class | rebuild | shared fixes |
|---|---|---:|---:|---:|---:|---|---|---|
| [ga_positions](ga_positions_ELEVATION_BRIEF_v1_0.md) | keep (P) | 2 | 0 | 3 | 4 | detector/tooling; writer code | n | CF-02, CF-04, CF-05, CF-06, CF-07, CF-10, CF-12, CF-14, CF-15, CF-17, CF-18 |
| [ga_vargas](ga_vargas_ELEVATION_BRIEF_v1_0.md) | keep (P) | 5 | 0 | 3 | 3 | data (output change); detector/tooling; diagnosis; migration; registry/declaration; writer code | y | CF-03, CF-04, CF-05, CF-07, CF-08, CF-10, CF-12, CF-13, CF-14, CF-15, CF-16, CF-17, CF-18 |
| [ga_dashas](ga_dashas_ELEVATION_BRIEF_v1_0.md) | keep (P) | 2 | 1 | 3 | 3 | detector/tooling; registry/declaration | cascade (CF-16); cond (edge) | CF-04, CF-05, CF-06, CF-07, CF-10, CF-12, CF-13, CF-14, CF-16, CF-18 |
| [ga_ayurdaya](ga_ayurdaya_ELEVATION_BRIEF_v1_0.md) | enrich (E) | 3 | 0 | 2 | 3 | data (output change); detector/tooling; registry/declaration; writer code | y (enrichment) | CF-02, CF-04, CF-05, CF-06, CF-07, CF-10, CF-12, CF-17, CF-18 |
| [ga_nakshatra](ga_nakshatra_ELEVATION_BRIEF_v1_0.md) | keep (P) | 1 | 0 | 3 | 4 | detector/tooling | n | CF-02, CF-04, CF-05, CF-06, CF-07, CF-10, CF-12, CF-15, CF-17, CF-18 |
| [ga_panchanga](ga_panchanga_ELEVATION_BRIEF_v1_0.md) | keep (P) | 3 | 0 | 1 | 5 | data (output change); detector/tooling; registry/declaration; writer code | y (tier, spelling) | CF-02, CF-03, CF-04, CF-05, CF-07, CF-10, CF-12, CF-14, CF-15, CF-17, CF-18, CF-19 |
| [ga_sensitive](ga_sensitive_ELEVATION_BRIEF_v1_0.md) | keep (P) | 3 | 1 | 2 | 2 | data (output change); detector/tooling; writer code | y (tier) | CF-02, CF-04, CF-05, CF-06, CF-07, CF-10, CF-12, CF-14, CF-15, CF-17, CF-18, CF-19 |
| [ga_sensitive_degree](ga_sensitive_degree_ELEVATION_BRIEF_v1_0.md) | keep (P) | 1 | 3 | 1 | 3 | detector/tooling; registry/declaration | cond (Yogi authority) | CF-02, CF-04, CF-05, CF-06, CF-07, CF-10, CF-12, CF-14, CF-17, CF-18, CF-19 |
| [ga_transit_anchors](ga_transit_anchors_ELEVATION_BRIEF_v1_0.md) | keep (P) | 1 | 1 | 3 | 2 | data (output change); detector/tooling; migration; registry/declaration; writer code | cond (lineage column) | CF-04, CF-05, CF-06, CF-07, CF-08, CF-10, CF-12, CF-14 |
| [ga_prashna](ga_prashna_ELEVATION_BRIEF_v1_0.md) | qualify (Q) | 0 | 1 | 4 | 2 | detector/tooling; registry/declaration | n | CF-04, CF-05, CF-06, CF-07, CF-08, CF-10, CF-12, CF-14, CF-18 |
| [ga_condition](ga_condition_ELEVATION_BRIEF_v1_0.md) | keep (P) | 5 | 0 | 3 | 2 | data (output change); detector/tooling; writer code | cascade (CF-16); y (columns) | CF-02, CF-04, CF-05, CF-06, CF-08, CF-10, CF-12, CF-13, CF-15, CF-16, CF-17, CF-18 |
| [ga_strength](ga_strength_ELEVATION_BRIEF_v1_0.md) | keep (P) | 4 | 1 | 3 | 2 | data (output change); detector/tooling; registry/declaration; writer code | cascade (CF-16); cond (tier) | CF-02, CF-04, CF-05, CF-06, CF-08, CF-10, CF-12, CF-13, CF-14, CF-15, CF-16, CF-17, CF-18, CF-19 |
| [ga_tajaka](ga_tajaka_ELEVATION_BRIEF_v1_0.md) | keep (P) | 2 | 1 | 1 | 3 | detector/tooling; migration; writer code | cond (year column) | CF-04, CF-05, CF-06, CF-07, CF-10, CF-12, CF-14, CF-15, CF-17, CF-18 |
| [ga_medical](ga_medical_ELEVATION_BRIEF_v1_0.md) | keep (P) | 1 | 1 | 1 | 3 | detector/tooling; registry/declaration; writer code | cond (thresholds) | CF-04, CF-05, CF-06, CF-07, CF-10, CF-12, CF-13, CF-14, CF-20 |
| [ga_vastu](ga_vastu_ELEVATION_BRIEF_v1_0.md) | keep (P) | 2 | 1 | 2 | 3 | writer code | cond (NULL case) | CF-04, CF-05, CF-06, CF-07, CF-10, CF-12, CF-13, CF-14, CF-20 |
| [ga_structural](ga_structural_ELEVATION_BRIEF_v1_0.md) | keep (P) | 4 | 0 | 3 | 2 | data (output change); detector/tooling; registry/declaration; writer code | cascade (CF-16); cond (FD-1) | CF-02, CF-04, CF-05, CF-06, CF-07, CF-08, CF-10, CF-12, CF-13, CF-14, CF-15, CF-16, CF-17, CF-18 |
| [ga_sade_sati](ga_sade_sati_ELEVATION_BRIEF_v1_0.md) | keep (P) | 3 | 1 | 1 | 3 | detector/tooling; writer code | cascade (CF-16) | CF-02, CF-04, CF-05, CF-06, CF-07, CF-10, CF-12, CF-14, CF-15, CF-16, CF-18, CF-19 |
| [ga_yoga](ga_yoga_ELEVATION_BRIEF_v1_0.md) | enrich (E) | 6 | 1 | 2 | 1 | data (output change); diagnosis; registry/declaration; served surface (TS); writer code | cascade (CF-16); y (enrichment) | CF-03, CF-04, CF-05, CF-06, CF-07, CF-08, CF-10, CF-12, CF-13, CF-14, CF-15, CF-16, CF-17 |
| [ga_vichara](ga_vichara_ELEVATION_BRIEF_v1_0.md) | keep (P) | 2 | 1 | 4 | 3 | data (output change); detector/tooling; registry/declaration; writer code | cond (family); follows its upstream | CF-03, CF-04, CF-05, CF-06, CF-07, CF-10, CF-12, CF-13, CF-14, CF-16, CF-17 |

`chart_facts` is shared: seven assets declare it as `target_table` (`ga_positions`, `ga_ayurdaya`, `ga_nakshatra`, `ga_panchanga`, `ga_sade_sati`, `ga_sensitive`, `ga_sensitive_degree`; each with a `natural_key_partition`, migrations 868–874); `ga_strength`, `ga_structural` and `ga_condition` also write it. `fact_category_ownership` names three owners only (`ga_structural` 64, `ga_ayurdaya` 1, `ga_condition` 2 = 67 rows) — see CF-02. Declared `prose_fields`: `["citation_human"]` on `ga_condition`, `ga_nakshatra`, `ga_panchanga`, `ga_positions`, `ga_sade_sati`, `ga_sensitive`, `ga_strength`, `ga_structural`, `ga_tajaka`, `ga_vargas`, `ga_yoga`; undeclared (null): `ga_ayurdaya`, `ga_dashas`, `ga_medical`, `ga_prashna`, `ga_sensitive_degree`, `ga_transit_anchors`, `ga_vastu`, `ga_vichara` — see CF-06.

## 4 · Cross-asset fixes, ordered by value for J1 (Tracks I and B)

Order rule: assets served × gate movement, then tier-independence and absence of a rebuild first (Track I can start tier-independent designs before J1: Track A §10); CF-16 is first by consequence (6 direct / 61 transitive dependents) because its first step is a read-only diagnosis. CF ids CF-02 … CF-12 reuse the L0 index's numbering where the same fix applies to L1 (CF-01, CF-09, CF-11 do not apply: L1 is delete-then-insert, so no converged-rerun `rows_written = 0` convention, and L1 has no identity or classical-tradition token); CF-13 … CF-20 are new in L1.

### 1. CF-16 — `ga_vargas` restore and downstream re-earn: `chart_divisionals` empty for the canonical chart under a `lit` record

- **Why this rank:** highest consequence in the layer: `chart_divisionals` is empty for the canonical chart under a `lit` record, and six assets (and `bo_pratijna`) read it; the diagnosis is read-only and tier-independent; the rebuild is a production REVIEW item.
- **Gate:** Build (completion, dep_liveness), Count (information), Earn (a `lit` that can read false); **assets:** 8 — `ga_vargas`, `ga_dashas`, `ga_condition`, `ga_strength`, `ga_structural`, `ga_sade_sati`, `ga_yoga`, `ga_vichara`
- **Evidence:** Census: `ga_vargas` `Build.completion` FAIL (live 0, floor 22,092, build record 24,400), `Count.floor` FAIL; layer instance LG-L1-002 (newest run touching the asset 2026-09-07 11:02 `complete`; the run before it errored `post-write integrity check failed`); migration 654's integrity conjunct (c) is red by design until the F-A1-corrected writer rebuilds; readers of `chart_divisionals` in L1 writers: `ga_dashas_writer.py:579`, `ga_condition_writer.py:769-780`, `ga_strength_writer.py:1234-1236`, `ga_structural_writer.py:960-972`, `ga_yoga_writer.py:2435-2441` (through `ga_structural`'s loader), `ga_sade_sati_writer.py` D10 prerequisite; `bo_pratijna` through `ChartReaderV4` (Track I). Other writers of the table: `ga_vargas_writer.py` only (plus the non-orchestrated `brahma/l1/ganita/divisionals_writer.py:422`).
- **Design:** (1) Read-only diagnosis (SS authorises): run history for `ga_vargas` since 2026-09-07; per-chart counts in `chart_divisionals` (loss specific to the canonical chart or table-wide); table delete statistics; generation heads for the asset (unreadable to the reader login today, MF-L1-012). (2) Restore by a single-asset dispatch of `ga_vargas` for the chart, then re-earn in DAG order: `ga_dashas`, `ga_condition`, `ga_strength`, `ga_structural`, `ga_sade_sati`, `ga_yoga` (and `ga_vichara` after its upstream). (3) Earn the `lit` state: a promotion predicate that reads false when the live count is under the floor (the `Build.completion` cell is the existing detector; Earn is the instrument that makes the status itself earned). (4) F-A2 (unique key + `fact_subject`) is a separate output change that should ride the same rebuild if SS approves.
- **Failing-first test and mutation:** failing-first: `chart_divisionals` chart count ≥ `target_floor` and build record = live count; migration 654's conjunct (c) turns true; mutation: delete one varga for one ayanamsha and Build.completion must flip back.
- **Blast radius:** 6 direct / 61 transitive dependents (`bo_laksana`, `bo_pratijna`, `ga_condition`, `ga_sade_sati`, `ga_strength`, `ga_structural` by the seed + 1210 reconstruction); about 22% of varga sign assignments differ from the pre-F-A1 rows (W2 §3, notice #1747); a rebuild of `ga_condition` BEFORE the restore would NULL `varga_dignity_composite` again (migration 658 header); a rebuild of `ga_dashas` before it leaves `lord_natal_dignity_d1` NULL.
- **Rebuild:** diagnosis: none. Restore and the six-asset cascade: **needs production rebuild** (REVIEW).
- **Fix class:** diagnosis, then data (restore) + writer code (F-A2) + migration (index); **buildable before J1:** tier-independent (diagnosis and restore)
- **Question for SS:** May SS authorise the read-only diagnosis, own the restore dispatch (single-asset, sequential), and approve F-A2 (output change) for the same rebuild?

### 2. CF-06 — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates)

- **Why this rank:** moves two gates (Null, Narr) on nine assets with a declarations-file edit only; tier-independent, no rebuild, no data risk.
- **Gate:** Null, Narr; **assets:** 9 need a declaration edit — `ga_ayurdaya`, `ga_dashas`, `ga_sensitive_degree`, `ga_transit_anchors`, `ga_prashna`, `ga_vichara`, `ga_yoga` (incomplete), and `ga_medical` / `ga_vastu` (after the grade ruling); the other 10 are already declared (`ga_condition`, `ga_nakshatra`, `ga_panchanga`, `ga_positions`, `ga_sade_sati`, `ga_sensitive`, `ga_strength`, `ga_structural`, `ga_tajaka`, `ga_vargas` carry `["citation_human"]`; listed in the briefs for reference)
- **Evidence:** Declarations file 1.6.0: 11 L1 assets declare `prose_fields: ["citation_human"]` with writer evidence (`ga_condition`, `ga_nakshatra`, `ga_panchanga`, `ga_positions`, `ga_sade_sati`, `ga_sensitive`, `ga_strength`, `ga_structural`, `ga_tajaka`, `ga_vargas`, `ga_yoga`); none declares `[]`; 8 are `null` (undeclared): `ga_ayurdaya`, `ga_dashas`, `ga_medical`, `ga_prashna`, `ga_sensitive_degree`, `ga_transit_anchors`, `ga_vastu`, `ga_vichara`, so Null and Narr read NO_DETECTOR for them. Offline graders over the declarations (not a re-measure): Narr.agree PASS 8 / PARTIAL 3 / NO_DETECTOR 8; Narr.fidelity_test PARTIAL 11 / NO_DETECTOR 8; Null.schema_default PARTIAL 11 / NO_DETECTOR 8; Null.blank_rows and Narr.checkable INCONCLUSIVE (no row data). `ga_yoga`'s declaration is incomplete: the INSERT also binds `derivation`, `strength_label`, `bhanga_na_reason` (offline Narr.agree PARTIAL names `derivation`).
- **Design:** Per asset, from the code read in the briefs: `ga_ayurdaya` candidate `["citation_human"]` (`_row`, `ga_ayurdaya_writer.py:189`); `ga_dashas` `["citation_human"]` (`_citation` at `:1156, 1500, 1685`, literal `:3424`); `ga_sensitive_degree` `["citation_human"]` (`:676-677`); `ga_prashna` `["classical_citation"]` (`:273`); `ga_transit_anchors` `[]` with evidence at the INSERT (`ga_transit_anchors.py:200-215`); `ga_medical` and `ga_vastu` wait on the grade-label ruling (a threshold grade of a score: `["indication_strength"]` / `["direction_impact"]` or `[]`); `ga_vichara` read `:437, 519` first; `ga_yoga` extend to the text columns that state or grade a value. A declared `[]` needs an `evidence.prose_fields` pointer to writer code as `path:line`.
- **Failing-first test and mutation:** `platform/scripts/governance/__tests__/test_e6_1_declarations.py` validation passes; mutation: declare `[]` for a writer that composes text and Narr.agree/lint must flag it.
- **Blast radius:** none (census inputs only).
- **Rebuild:** none (declaration only).
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01 defines narration; schema 1.6.0 exists)
- **Question for SS:** Is a fixed-vocabulary grade from a threshold (`indication_strength`, `direction_impact`, `strength_label`) narration for the Null/Narr gates?

### 3. CF-13 — Build.dag reads-match: declared `depends_on` against the tables each L1 writer reads (missing edges, two back-reads)

- **Why this rank:** Build.dag rev 2 reads-match is the gate whose definition changed most for L1; Track I already evidenced the findings and migration 1210 added only producer-side edges for L1, so three consumer-side findings and two back-reads remain.
- **Gate:** Build (dag); **assets:** 5 need a registry or code change — `ga_dashas` and `ga_yoga` (missing edges to `ga_vargas`), `ga_structural` (two back-reads), `ga_vichara` (receives the relocated family), `ga_vargas` (the producer; no change to it); `ga_condition`, `ga_strength`, `ga_medical`, `ga_vastu` carry only declared or bedrock-exempt reads
- **Evidence:** Track I `/Users/Dev/suvarna-evidence/TrackI/edges_evidence.md` §C (back-reads) and §D (assets still FAIL on the aligned detector): `ga_dashas` missing edge `ga_vargas` (table `chart_divisionals`, `ga_dashas_writer.py:579`, no covering path); `ga_yoga` missing direct edge `ga_vargas` (transitive path through `ga_structural`); `ga_structural` back-reads `chart_vichara` (`ga_structural_writer.py:2770`) and `ga_yoga_firings` (`:2806`) — "reads the PREVIOUS generation"; edge would create a cycle, so not added. Migration 1210 (applied state not verified here) adds direct dependents to L1 producers only: `ga_vichara` +2, `ga_dashas` +2, `ga_vargas` +1, `ga_yoga` +1; no L1 consumer row changes. Undeclared L0 reads (bedrock, exempt on main, SS 2026-10-01, provisional pending J1): `ga_condition` (`bg_dignity_reference`), `ga_medical` (`bg_medical_mappings`, `bg_nakshatra_medical`), `ga_yoga`/`ga_structural` (`brahma_yoga_catalog`, `brahma_dosha_catalog`), `ga_sensitive_degree` (`reference_nakshatra`), `ga_vastu` (should read `bg_vastu_directions`), `ga_vichara` (`brahma_vichara_constants`). The writer-class comment `ga_structural.py:21` lists one edge where the registry has seven.
- **Design:** (a) Declare `ga_dashas` → `ga_vargas` and `ga_yoga` → `ga_vargas` by a registry migration of the 1210 kind (append-only, guarded, acyclic check inside the migration) — AFTER the CF-16 restore: the hard dependency gate (`asset_runner.deps_unsatisfied`) requires the producer `lit` and fresh and reads state, not row counts, so today (`ga_vargas` is `lit` with 0 rows) the edge would pass the gate while meaning nothing. (b) Relocate the daridra-cancellation pass out of `ga_structural` (see `ga_structural` FD-1): evaluate it in `ga_vichara`, which already holds `ga_yoga` firings and its own wealth ratification in DAG order. (c) Keep L0 reads undeclared under the bedrock exemption, or declare them at J1; no change now.
- **Failing-first test and mutation:** failing-first: Build.dag rev 2 reads FAIL for the consumer before and PASS after; the order-independence test for (b): the cancellation outcome on a fresh build equals the outcome after a second build; mutation: remove an edge / reintroduce the back-read and the check flips.
- **Blast radius:** declaring an edge changes the consumer's upstream hash (a one-time rebuild signal) and its dispatch order; `ga_dashas` has 14 direct dependents; (b) moves rows between assets (category ownership).
- **Rebuild:** (a) needs production rebuild of `ga_dashas` if its upstream hash drives dispatch (REVIEW); (b) needs production rebuild of `ga_structural` and `ga_vichara`.
- **Fix class:** registry/declaration (a); writer code + data (b); **buildable before J1:** (a) tier-independent but needs its own review (Track I left it to a separately ruled migration); (b) tier-dependent: which asset owns a cancellation (judged structure, T2 §3.3)
- **Question for SS:** Declare the two `ga_vargas` edges after the restore? Where does the daridra-cancellation pass belong: `ga_vichara`, a declared stale read, or a new post-yoga asset?

### 4. CF-02 — Producer attribution on the shared `chart_facts` table: partition-scoped `count_sql`, `fact_category_ownership`, multi-table writers

- **Why this rank:** the shared `chart_facts` table is written by ten L1 assets; the cells that fail or cannot be attributed (Build.completion ×3, Dens, Complete, Ldgr, Vocab) come from counting by predicate and from a hand-maintained ownership table.
- **Gate:** Build (completion), Earn (count_sql scope), Dens/Complete/Ldgr/Vocab (population, see CF-18); **assets:** 10 — `ga_positions`, `ga_ayurdaya`, `ga_nakshatra`, `ga_panchanga`, `ga_sensitive`, `ga_sensitive_degree`, `ga_condition`, `ga_strength`, `ga_structural`, `ga_sade_sati`
- **Evidence:** `chart_facts` is the declared target of seven assets (`ga_positions`, `ga_ayurdaya`, `ga_nakshatra`, `ga_panchanga`, `ga_sade_sati`, `ga_sensitive`, `ga_sensitive_degree`; each with a `natural_key_partition`, migrations 868–874, and a partition-scoped `count_sql`; live partition counts 1,205 / 130 / 2,847 / 437 / 6,287 / 8,775 / 335 = 20,016) and is also written by `ga_strength`, `ga_structural` (both `target_table` NULL) and `ga_condition` (composite + `chart_facts`). `fact_category_ownership` (migration 410 + 842 + 845) holds 67 rows over three owners (`ga_structural` 64, `ga_ayurdaya` 1, `ga_condition` 2), joined to the chart's 143,299 rows it owns 102,037 + 130 + 90 and leaves **41,042 rows with no owner row**; the `ga_strength` predicate matches 420 rows the table gives `ga_structural`; `ga_condition`'s `count_sql` claims 2,925 `chart_facts` rows where the table gives it 90. Build records vs live: `ga_condition` 45 vs 2,970, `ga_strength` 13,715 vs 14,141, `ga_structural` 106,707 vs 102,037 (layer instance TG-L1-005, MF-L1-005; harvest TGH-T2-05).
- **Design:** (1) Registry/declaration (tier-independent): scope each asset's `count_sql` to the categories its own writer writes (precedent: L0 `bg_class_lifetime_counts`), or declare the table multi-producer; complete `fact_category_ownership` by the migration-842 pattern after a read-only list of unowned categories. (2) Writer code: report every row the writer writes in `WriterResult.rows_inserted` (`ga_condition`'s `_insert_per_varga_avastha_rows` returns nothing, `ga_condition_writer.py:1183-1215, 1704`). (3) A parity test between the categories each L1 writer emits (a constant per writer) and the ownership table. Never a `WriterBase` change.
- **Failing-first test and mutation:** failing-first: for each asset `rows_written` of a rerun equals the changed rows of ITS OWN count_sql scope; a seeded extra row in a sibling category must not move this asset's count; mutation: revert the scope and the count test fails.
- **Blast radius:** registry-only part: cockpit counts for the named assets (no consumer reads `count_sql`); writer part: `asset_throughput` records only.
- **Rebuild:** (1) none. (2) takes effect on the next dispatch; an idempotent rerun refreshes the record (production run, REVIEW).
- **Fix class:** registry/declaration only (1); writer code (2) + test (3); **buildable before J1:** (1) tier-independent; ownership rule tier-dependent (TG-L1-005 / TGH-T2-05)
- **Question for SS:** Which asset owns the 420 rows both `ga_strength`'s predicate and `ga_structural`'s ownership name, and do the 41,042 unowned rows get owners?

### 5. CF-19 — Earned verification tier: `two_pass_verified` stamped by default or by literal where no second derivation runs (CLAUDE.md §N.8)

- **Why this rank:** an unearned strongest tier is the layer's clearest earned-signal defect (CLAUDE.md §N.8) and every Carr detector (CF-07) is meaningless until the tier is earned; it is an output change with an L2 salience consequence, so SS decides first.
- **Gate:** Earn (the emitted tier), Carr; **assets:** 5 — `ga_panchanga`, `ga_sensitive`, `ga_sensitive_degree`, `ga_strength`, `ga_sade_sati`
- **Evidence:** `ga_sensitive_writer.py:373-374`: `_make_row` DEFAULTS `verification_pass_status=TWO_PASS_VERIFIED` with `tolerance_arcsec=0.0`, and the Yogi/Dagdha rows pass the literal `"two_pass_verified"` (`:2657-2678`) over one formula evaluation and a table lookup; `verification_vocab.two_pass_verdict` ("the ONLY sanctioned producer of `two_pass_verified`") is called nowhere in L1 writers except through `ga_nakshatra` (checked by grep of `ga_writers/*_writer.py` and `ga_nakshatra.py`); `ga_dashas` earns per row through `_apply_vimshottari_independent_verification` (`ga_dashas_writer.py:735`); `ga_panchanga` stamps `single_pass` on the four FORENSIC angas (`:150-151`); `ga_strength` (`_verify_ashtakavarga`, `:731`), `ga_sade_sati` (`two_pass_verify_cycles`, `:880-892`) and `ga_sensitive_degree` (Yogi arcsecond re-evaluation, `:506-524`) stamp `two_pass_verified` on checks that can fail but re-use the same values. Stored: `two_pass_verified` is 9,320 of 143,299 `chart_facts` rows (6.5%) and 46,009 of 483,870 `chart_dashas` rows (9.5%) on the chart (layer instance §2.7). W2 §6 warns a tier change taken ahead of the alias fix would have demoted 10,316 rows 0.85 → 0.60.
- **Design:** (1) Read-only stored-tier census by asset and `fact_category` for the chart (how many rows change). (2) SS rules the tier an invariant/bounds check earns. (3) Then: row builders default to `UNVERIFIED_DEFAULT`; each verified stamp comes from `two_pass_verdict(primary, independent)` with an independent path; relays and table lookups use `CLASSICAL_MATCH`; a CI test fails on a verified-tier default or literal outside the helper, and a grep of `two_pass_verdict` call sites with identical arguments (the vocabulary's own residual-fraud note). Do not stamp from a FORENSIC gate (it asserts a native fact, not a second derivation: `ga_dashas_writer.py:710-715` makes the same distinction).
- **Failing-first test and mutation:** failing-first: a row built without an explicit status reads `single`; a seeded wrong second derivation reads `divergent_flagged`; mutation: restore the default and the CI test fails.
- **Blast radius:** readers of the affected tiers; L2 salience weights derived from `VERIFICATION_RESCALE` (0.85 vs 1.00 per the `ga_panchanga_writer.py:147-148` comment) move for the demoted rows (not computed here).
- **Rebuild:** the stored tier changes only on **production rebuild** of the affected assets (`ga_sensitive` 8,775 rows; `ga_panchanga` 437; others per ruling): REVIEW.
- **Fix class:** writer code + output change; **buildable before J1:** the census read is tier-independent; the stored-tier change is tier-dependent (TG-L1-022 / TGH-T1-01: where independent verification is required)
- **Question for SS:** May the row-builder default and literal stamps be corrected after the census (L2 salience effect)? Does an invariant/bounds check that can fail earn `two_pass_verified`, `classical_match` or `single`? Which Yogi-point category is the authority?

### 6. CF-03 — Registry correction batch (live registry vs seed literals: floors, edges, status) in one surgical migration plus seed literals

- **Why this rank:** small, tier-independent, no rebuild; L1 needs far fewer registry corrections than L0 (the Nirmāṇa W3 migrations 650/843 already corrected the live registry).
- **Gate:** Count (information), Build.completion basis; **assets:** 4 — `ga_vargas`, `ga_panchanga`, `ga_yoga`, `ga_vichara`
- **Evidence:** Seed literals that lag the live registry (layer instance §1.1 vs `asset_registry_seed.ts`): `ga_vargas` `target_floor` 21635 vs live 22,092 (migration 439); `ga_panchanga` 221 vs live 437 (migration 843); `ga_vichara` 8240 vs live 8,249. Open decisions: `ga_yoga` floor 63 vs live 53 (re-floor with a reason or restore, after the CF-16 diagnosis); `ga_sensitive_degree` seed `count_sql` counts one category while the writer writes two (live `count_sql` not read).
- **Design:** Refresh the three seed literals (seed edits never rewrite an existing row: hygiene) and their `volume_explanation` text; for `ga_yoga` and `ga_sensitive_degree` one surgical migration per outcome (`UPDATE … WHERE asset_id AND <old value>` with an in-migration check), number = max+1 across every origin head and both migration directories at execution time; verify by production structure, never by the runner's report. Floors are information (D3) and equal the achieved count after a build (CLAUDE.md §N.4).
- **Failing-first test and mutation:** failing-first: `scripts/__tests__/asset_registry_seed_dag_parity.test.ts` and the registry parity gate stay green; for a migration: Count.floor reads PASS for the asset; mutation: restore the old floor and it fails.
- **Blast radius:** registry rows only; no consumer reads `target_floor`.
- **Rebuild:** none.
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### 7. CF-04 — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution

- **Why this rank:** Dens is the gate whose rev-4 definition moves L1 most (saved PASS 17 → offline PASS 3); applicability is a ruling first.
- **Gate:** Dens; **assets:** 19 — `ga_positions`, `ga_vargas`, `ga_dashas`, `ga_ayurdaya`, `ga_nakshatra`, `ga_panchanga`, `ga_sensitive`, `ga_sensitive_degree`, `ga_transit_anchors`, `ga_prashna`, `ga_condition`, `ga_strength`, `ga_tajaka`, `ga_medical`, `ga_vastu`, `ga_structural`, `ga_sade_sati`, `ga_yoga`, `ga_vichara`
- **Evidence:** Saved census (rev 1): PASS 17, NO_DETECTOR 1 (`ga_strength`), N/A 1 (`ga_prashna`). Offline re-scan with main's rev-4 code over this tree (no DB): PASS 3 (`ga_medical`, `ga_tajaka`, `ga_vastu`), PARTIAL 7 (`ga_condition`, `ga_dashas`, `ga_prashna`, `ga_transit_anchors`, `ga_vargas`, `ga_vichara`, `ga_yoga`: a contract is declared but a served select has no tier column or a run-time select list), NO_DETECTOR 9 (the seven declared `chart_facts` producers: shared table, cannot attribute; `ga_strength`: no served select attributable; `ga_structural`: the scanner loses sync in `platform-mcp/src/tools/register_p1_ganita.ts`). The L1 tables carry a verification tier column (`chart_facts`, `chart_dashas`, `chart_divisionals`), so a tier column in a served select is attainable (unlike L0). Served selects lacking it: `get_dasha_lord_capability.ts`, `query_mechanism_retrodiction.ts`, `get_argala.ts`, `get_condition_composite.ts`, `get_transit_anchors.ts`, `get_vichara.ts`, `get_yoga_dosha.ts`, `get_yoga_firings.ts` (run-time select), `get_prashna_lagna.ts`. E6.1 ran the same scan on tree 0b9cdd37a (`/Users/Dev/suvarna-evidence/E6.1/dens_before_after.md`); the main tree differs for `ga_structural` (FAIL there, NO_DETECTOR here).
- **Design:** Add the tier column to each listed served select (additive response field) while keeping `density_contract`; attribute shared-table serving by `fact_category` through the declarations `carriage.served_surface` + `read_evidence` (all 19 L1 assets already carry one) so Dens reads a partition, not a table (inspector change, Track E); fix or exempt the scanner desync. If SS rules Dens N/A for an asset with no served read, that is an N-22 rule with a decision id, not an asset change.
- **Failing-first test and mutation:** per module: a response-shape test that the tier field is present and `empty_reason` is emitted on an empty page; mutation: drop the declaration and the census cell reads non-PASS again.
- **Blast radius:** additive response fields on L1 retrieval tools; consumers that parse strictly would see new keys (none identified).
- **Rebuild:** none (TypeScript serving surface only).
- **Fix class:** served surface (TS) + detector/tooling + SS ruling; **buildable before J1:** tier-dependent: TGH-T3-26 (who owns a Dens FAIL) and the N-22 per-gate applicability rules
- **Question for SS:** Does Dens read per partition for shared-table producers (inspector change), or is a table-level reading with a tier column enough?

### 8. CF-15 — Narr golden tests that name the declared `citation_human` field (assertion on the sentence, not only on the builder)

- **Why this rank:** the L1 layer declares `citation_human` as narration on 11 assets; the grader can only reach structural PARTIAL, but three assets have no test that names the declared field at all.
- **Gate:** Narr; **assets:** 11 — `ga_positions`, `ga_vargas`, `ga_nakshatra`, `ga_panchanga`, `ga_sensitive`, `ga_condition`, `ga_strength`, `ga_tajaka`, `ga_structural`, `ga_sade_sati`, `ga_yoga`
- **Evidence:** Offline Narr.fidelity_test PARTIAL on all 11 declared assets; 8 have a test file that references `citation_human` in the same test function as a builder call (`ga_panchanga`, `ga_positions`, `ga_sade_sati`, `ga_sensitive`, `ga_strength`, `ga_structural`, `ga_vargas`, `ga_yoga`: "structural only … whether the assertion grades the sentence is not read, so this never reads PASS") and 3 have none that names it (`ga_condition`, `ga_nakshatra`, `ga_tajaka`). `ga_sade_sati` Narr.lint is PARTIAL on three allowlisted category-only selects (`ga_sade_sati_writer.py:1449, 1483, 1636`); `ga_writers/gates.py` `run_no_narration_linter` is wired only through the legacy `build_runner` (MF-L1-008).
- **Design:** One golden test per declared asset that builds the canonical-chart rows for one ayanamsha and asserts the exact `citation_human` sentence for rows whose value is a FORENSIC anchor (Sun Capricorn, Moon Purva Bhadrapada, Lagna Aries, the pañcāṅga four, Muntha Libra for varṣa 43) so the sentence is graded against a hand-known value, not against the builder's own output; pin the allowlisted `fact_category` selects.
- **Failing-first test and mutation:** mutation per test: change the sign/pada/lord name in the composed string and the test fails.
- **Blast radius:** none (tests only).
- **Rebuild:** none.
- **Fix class:** detector/tooling (tests) + writer code (lint pins); **buildable before J1:** tier-independent (SS Narr ruling 2026-10-01)

### 9. CF-17 — Verification-tier string literals in L1 writers (CLAUDE.md §N.4: named constants from `verification_vocab.py`)

- **Why this rank:** CLAUDE.md §N.4 (S7 ruling) says writers must emit the tier through named constants; 13 of 17 `ga_writers/*_writer.py` modules carry quoted tier strings.
- **Gate:** Earn, Vocab; **assets:** 13 modules carry quoted tier strings (`ga_strength`, `ga_vargas`, `ga_structural`, `ga_sensitive`, `ga_panchanga`, `ga_sade_sati`, `ga_dashas`, `ga_sensitive_degree`, `ga_tajaka`, `ga_condition`, `ga_yoga`, `ga_positions`, `ga_ayurdaya`); `ga_nakshatra` is the conformant model and `ga_medical`, `ga_prashna`, `ga_vastu`, `ga_vichara` carry none
- **Evidence:** Indicative regex count of quoted tier strings per writer module (emissions and comparisons not separated): `ga_strength` 26, `ga_vargas` 21, `ga_structural` 19, `ga_sensitive` 17, `ga_panchanga` 15, `ga_sade_sati` 12, `ga_dashas` 7, `ga_sensitive_degree` 7, `ga_tajaka` 7, `ga_condition` 6, `ga_yoga` 4, `ga_positions` 3, `ga_ayurdaya` 2, and 0 in `ga_medical`, `ga_prashna`, `ga_vastu`, `ga_vichara`. The vocabulary exports four named constants only (`UNVERIFIED_DEFAULT`, `TWO_PASS_VERIFIED`, `DIVERGENT_FLAGGED`, `CLASSICAL_MATCH`, `verification_vocab.py:180, 274-282`); `single_pass`, `floored`, `computed_extension`, `documented_approximation`, `pending_w3_verification`, `not_defined_for_nodes`, `scope_cap_sentinel` have none. The one guard is `tests/test_ga_dashas_f_a17_bare_tier_literals.py`. Editing the shared L0 `verification_vocab.py` shifts the source-hash closure of about 24 L1+L2 writers (`ga_dashas_writer.py:54-72` comment).
- **Design:** Extend the F-A17 guard to every L1 writer as one parametrised test (fails on a quoted tier string assigned to `verification_pass_status`/`provenance`/`verification` outside the vocabulary import; comparisons allowlisted by reason). For members with no constant, use the `entry_for()` lookup `ga_dashas` already uses (no L0 edit) or add constants to the L0 module (a shared-module edit: SS). Emit the canonical spelling where an alias is stored (`ga_panchanga`: `single_pass` → `single`).
- **Failing-first test and mutation:** failing-first: the new test fails on the current literals; mutation: reintroduce one and it fails.
- **Blast radius:** none for data (strings identical) except the `single_pass` → `single` spelling (stored rows change only on rebuild).
- **Rebuild:** none required; the `ga_panchanga` spelling needs a rebuild to change stored rows.
- **Fix class:** writer code + test; **buildable before J1:** tier-independent (an existing ruling)
- **Question for SS:** Add named constants for the other `verification_vocab` members to the shared L0 module (changes ~24 writers' source hashes), or use `entry_for()` lookups?

### 10. CF-07 — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1)

- **Why this rank:** the largest gate count (Carr 19 of 19 NO_DETECTOR) but tooling work for Track E; not a J1 input; depends on CF-19.
- **Gate:** Carr; **assets:** 17 — `ga_positions`, `ga_vargas`, `ga_dashas`, `ga_ayurdaya`, `ga_nakshatra`, `ga_panchanga`, `ga_sensitive`, `ga_sensitive_degree`, `ga_transit_anchors`, `ga_prashna`, `ga_tajaka`, `ga_medical`, `ga_vastu`, `ga_structural`, `ga_sade_sati`, `ga_yoga`, `ga_vichara`
- **Evidence:** Census `Carr.detector` NO_DETECTOR ×19. Layer hint (T4 "Adapting per layer"): D3 dominates in L1. Code that already holds a second derivation the inspector cannot read: `_vimshottari_independent_verifier.py` (`ga_dashas`), `compute_cross_ayanamsha_agreement`/`two_pass_verdict` (`ga_nakshatra`), the upagraha Swiss-Ephemeris vs BPHS comparison with `tolerance_arcsec` stored on 8,775 rows (`ga_sensitive`), `two_pass_verify_cycles` (`ga_sade_sati`), `_yogi_point_two_pass` (`ga_sensitive_degree`). Assignment per asset (briefs §6): D3 for `ga_positions`, `ga_vargas`, `ga_dashas`, `ga_nakshatra`, `ga_panchanga`, `ga_sensitive`, `ga_sensitive_degree`, `ga_transit_anchors`, `ga_condition`, `ga_strength`, `ga_tajaka`, `ga_structural`, `ga_sade_sati`, `ga_vichara`; D2 for `ga_ayurdaya`; D1 for `ga_medical`, `ga_vastu`, `ga_yoga`; none for `ga_prashna` (no prashna chart on the canonical chart, outside R-1).
- **Design:** Deterministic-first (CLAUDE.md §N.4: no JH-parity oracle): one reader per detector family that reports verified/unverified/divergent counts per asset partition and PASSES only on the verified subset (never on presence). D2 for āyurdāya: three method rows exist, none an average. D1: resolve each row's citation to the source row and test anchor terms; semantic equivalence stays a sampled human reading. Each detector ships a seeded mismatch it must catch.
- **Failing-first test and mutation:** failing-first per detector: a non-zero mismatch count on a seeded corrupted copy and zero on the real table; the proof is the seeded case.
- **Blast radius:** none for the assets (Track E tooling).
- **Rebuild:** none.
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent for the per-asset D1/D2/D3 assignment (TGH-T3-02); the detectors need no tier clause
- **Question for SS:** Is the verified subset the PASS population for D3 (never presence), and is a consistency invariant that can fail an acceptable second pass (see CF-19)?

### 11. CF-12 — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written

- **Why this rank:** the L1 Idem PASS (19 of 19) is a static reading of a DELETE before the insert; it does not test accretion or a delete scope built from the rows about to be written.
- **Gate:** Idem; **assets:** 19 — `ga_positions`, `ga_vargas`, `ga_dashas`, `ga_ayurdaya`, `ga_nakshatra`, `ga_panchanga`, `ga_sensitive`, `ga_sensitive_degree`, `ga_transit_anchors`, `ga_prashna`, `ga_condition`, `ga_strength`, `ga_tajaka`, `ga_medical`, `ga_vastu`, `ga_structural`, `ga_sade_sati`, `ga_yoga`, `ga_vichara`
- **Evidence:** Delete scopes: `replace_prior_chart_facts` (categories present in the rows), `replace_prior_chart_dashas` (systems/levels present), `replace_prior_chart_divisionals` (vargas/ayanamshas present, with the per-run `cleared` set), `replace_prior_tajik_varsha` (exact `(chart, ayanamsha, varsha_year)` triples), exact `(chart_id, ayanamsha_id)` for the own-table writers (`ga_condition` composite, `ga_vastu`, `ga_medical`, `ga_prashna`, `ga_transit_anchors`, `ga_vichara`, `ga_yoga`). A rebuild that stops emitting a category (or a shrinking `ga_tajaka` window) leaves earlier rows in place (MF-L1-004 (a)); `ga_vargas` reads PASS with 0 rows (b); the historical `ga_condition`/`ga_structural` collision on two categories (migrations 416/419).
- **Design:** A read-only orphan census per delete-then-insert writer: run the writer's produced-key computation in `ctx.dry_run` mode (supported by the frozen contract) and compare to the live natural keys of its partition (`natural_key_partition`, migrations 868–874, for the `chart_facts` producers); orphans = live − produced; PASS = 0. The behavioural proof is a rebuild-twice semantic fingerprint (E5.5, plan P8). Where orphans exist the writer gets a prune scoped to its own partition.
- **Failing-first test and mutation:** failing-first: a fixture table with one extra row not produced by the writer → census FAIL naming it; after the prune → PASS; mutation: widen the prune beyond the asset's partition and the shared-table test fails.
- **Blast radius:** detector: none; a prune changes data only where orphans exist (none known).
- **Rebuild:** none for the detector.
- **Fix class:** detector/tooling (+ writer code only if orphans are found); **buildable before J1:** tier-dependent: what Idem means when the delete scope follows the rows (TGH-T3-16, TG-L1-006)
- **Question for SS:** Is "no orphan rows under the writer's own partition" the Idem claim for L1 delete-then-insert writers?

### 12. CF-18 — Census population on shared tables: chart-scoped, partition-scoped cells for Complete / Ldgr / Vocab / Reach / Dens

- **Why this rank:** cells for shared and no-target assets are computed over a different population from the one they are attributed to (MF-L1-002/-003); a detector fix, no asset change.
- **Gate:** Complete, Ldgr, Vocab, Reach, Dens; **assets:** 14 — `ga_positions`, `ga_vargas`, `ga_dashas`, `ga_ayurdaya`, `ga_nakshatra`, `ga_panchanga`, `ga_sensitive`, `ga_sensitive_degree`, `ga_prashna`, `ga_condition`, `ga_strength`, `ga_tajaka`, `ga_structural`, `ga_sade_sati`
- **Evidence:** `Complete.depth`, `Ldgr.source_presence`, `Vocab.identity`, `Reach.fields` and `Dens.served` for the seven `chart_facts` producers are whole-table (`chart_facts` 421,096 rows over all charts) and identical across producers; `chart_dashas` 1,460,985 rows (chart-scoped live 483,870), `ga_condition_composite` 135 rows (45 for the chart), `l1_tajik_varsha_year_lords` 780 (240). `ga_strength` and `ga_structural` have no Complete/Vocab/Reach cell (no `target_table`); six assets have no Ldgr cell; `ga_prashna` and `ga_vargas` cells are NO_DETECTOR because the tables are empty for the chart.
- **Design:** The inspector scopes each cell to the chart and to the producer's partition (`natural_key_partition` or the ownership join), states the population per cell, and emits every gate row (N/A with reason included; register R128). Empty-by-design (`ga_prashna`) needs the N-22 rule.
- **Failing-first test and mutation:** failing-first: a cell for a shared-table producer changes when a sibling producer's rows change only if the asset's partition changes; mutation: add a row to a sibling partition and this asset's cell must not move.
- **Blast radius:** none for the assets.
- **Rebuild:** none.
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: T3 lines 76–86 (a count must say what it counted over)

### 13. CF-08 — Ldgr: assets with no recognised citation column (six L1 cells with no reading)

- **Why this rank:** declaration-only for most of the six assets; tier-dependent on the L1 form of the Ldgr claim (TGH-T3-22).
- **Gate:** Ldgr; **assets:** 7 — `ga_vargas`, `ga_transit_anchors`, `ga_prashna`, `ga_condition`, `ga_strength`, `ga_structural`, `ga_yoga`
- **Evidence:** No `Ldgr.source_presence` cell for `ga_condition`, `ga_prashna`, `ga_strength`, `ga_structural`, `ga_transit_anchors`, `ga_vargas` (MF-L1-003); the other 13 read PASS on `citation_ref`, `classical_citation` or `source_citation`. L1's inputs are birth parameters and L0 rows, not `fact_id`s (TG-L1-021 / TGH-T3-22). Two real lineage gaps: `ga_transit_anchors` restates `chart_facts` positions without a source `fact_id`; `ga_yoga` D9 clauses cite D1 facts because `chart_divisionals` has no `fact_id`.
- **Design:** Per asset, declare the source column (declarations `carriage`), partition-scoped for shared tables; where no column exists the gap is real: `ga_transit_anchors` `source_fact_ids` (additive migration) and a `chart_divisionals` row id for D9 lineage (`ga_yoga` FD-2).
- **Failing-first test and mutation:** Ldgr reads PASS/FAIL (not no reading) after the declaration; a row with a blank citation must read FAIL.
- **Blast radius:** none for declaration-only cases.
- **Rebuild:** none (declaration); the two lineage columns need a small production rebuild (REVIEW).
- **Fix class:** registry/declaration only (or data where no column exists); **buildable before J1:** tier-dependent: TGH-T3-22 / TGH-T3-01

### 14. CF-10 — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it

- **Why this rank:** a definition question; no edit can change a history record.
- **Gate:** Build (history); **assets:** 19 — `ga_positions`, `ga_vargas`, `ga_dashas`, `ga_ayurdaya`, `ga_nakshatra`, `ga_panchanga`, `ga_sensitive`, `ga_sensitive_degree`, `ga_transit_anchors`, `ga_prashna`, `ga_condition`, `ga_strength`, `ga_tajaka`, `ga_medical`, `ga_vastu`, `ga_structural`, `ga_sade_sati`, `ga_yoga`, `ga_vichara`
- **Evidence:** Build.history reads PARTIAL on 18 L1 assets and FAIL on `ga_positions` (most recent run aborted 2026-09-19). Latest recorded errors (layer instance §1.1): integrity-contract failure ×4 (`ga_condition`, `ga_structural`, `ga_vargas`, `ga_vastu`, 2026-09-07/08), cascade `BLOCKED` ×5 (`ga_medical`, `ga_sade_sati`, `ga_strength`, `ga_vichara`, `ga_yoga`), `orphaned_by_crash` ×2 (`ga_dashas`, `ga_sensitive`), a fixed UUID serialization error (`ga_positions`, #1861), an output-digest-spec error (`ga_nakshatra`; migration 889 adds that spec), a Moshier-range error (`ga_tajaka`), none recorded ×5. In every PARTIAL the latest run completed.
- **Design:** None for the assets. A clean run raises the count of complete runs but never removes an error from history. The definition could read only runs since the last change to the asset's writer or registry row; the `ga_positions` FAIL needs either that definition or a clean asset-set rerun (production run: REVIEW).
- **Failing-first test and mutation:** n/a (definition).
- **Blast radius:** none.
- **Rebuild:** none (a rerun of `ga_positions` would be a production run).
- **Fix class:** detector/tooling (definition); **buildable before J1:** tier-dependent: T4 §4.2 check 8 wording
- **Question for SS:** Should Build.history look only at runs since the last change to the asset's writer or registry row?

### 15. CF-14 — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual)

- **Why this rank:** a small, tier-independent hygiene item that closes a CLAUDE.md §N.2 residual (the orchestrator is the sole `asset_throughput` writer).
- **Gate:** Earn (information); **assets:** 8 — `ga_dashas`, `ga_panchanga`, `ga_positions`, `ga_sade_sati`, `ga_sensitive`, `ga_strength`, `ga_structural`, `ga_tajaka` (the other eleven L1 writers have no direct call: LG-L1-001)
- **Evidence:** Eight direct calls to `update_asset_throughput` in `ga_writers` (LG-L1-001, R34 residual): `ga_dashas_writer.py:3078`, `ga_panchanga_writer.py:1315`, `ga_positions_writer.py:693`, `ga_sade_sati_writer.py:1876`, `ga_sensitive_writer.py:3038`, `ga_strength_writer.py:1961`, `ga_structural_writer.py:8143`, `ga_tajaka_writer.py:835`; every one is under `if owns_conn` (the legacy standalone path; the orchestrated wrappers pass `conn=ctx.db_conn`), so by code reading none executes under the orchestrator; `_telemetry.update_asset_throughput` writes `state`/`rows_written` and no duration, and `asset_throughput.rows_per_second` is NULL on 19 of 19 rows because the engine timing is off `main` (TG-L1-004). `ga_vargas_writer.py:2779` is a documented no-op.
- **Design:** Either delete the eight call sites and the CLI path they serve (`scripts/run_l1_ganita_build.py` via `build_runner`) or declare them CLI-only; add a grep guard that no `ga_writers` module calls `update_asset_throughput(` outside the declared CLI.
- **Failing-first test and mutation:** failing-first: the guard fails on a new call; mutation: add a call and it fails.
- **Blast radius:** the legacy CLI loses its throughput write if removed.
- **Rebuild:** none.
- **Fix class:** writer code; **buildable before J1:** tier-independent
- **Question for SS:** Remove the eight legacy `_telemetry` sites with the CLI path, or keep them as declared CLI-only?

### 16. CF-20 — Grade labels derived from `condition_score` with writer-local thresholds (ga_vastu 0.4/0.7, ga_medical 0.4/0.6): one authority for the cut points

- **Why this rank:** two L1 assets grade the same score with different writer-local cut points; one authority is a §N.7 item 3 matter.
- **Gate:** Narr/Null; **assets:** 2 — `ga_medical`, `ga_vastu`
- **Evidence:** `ga_vastu_writer.py:52-67` (`< 0.4` weakened, `< 0.7` neutral, else strengthened; NULL → `neutral`) vs `ga_medical_writer.py` `indication_strength_from_score` (`< 0.4` strong, `≤ 0.6` moderate, else mild; NULL → `unknown`), both over `ga_condition_composite.condition_score`; the vāstu NULL case is an invented neutral (§N.7 item 6).
- **Design:** Declare one cited cut-point set at the score's owner (`ga_condition`) and read it from both writers, or record, with a source, why the medical and vāstu scales differ; return NULL/`unknown` (not `neutral`) when the score is missing.
- **Failing-first test and mutation:** both writers grade a boundary score through the one authority; mutation: change a cut point once and both move.
- **Blast radius:** none if the shared set equals today's values.
- **Rebuild:** none unless values change (REVIEW).
- **Fix class:** writer code; **buildable before J1:** tier-dependent: no tier defines the cut points
- **Question for SS:** Where do the `condition_score` cut points live, and may the vāstu and medical scales differ?

### 17. CF-05 — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094)

- **Why this rank:** Track E instrument (19 assets); nothing to change in any L1 asset.
- **Gate:** Earn (and Cost, information); **assets:** 19 — `ga_positions`, `ga_vargas`, `ga_dashas`, `ga_ayurdaya`, `ga_nakshatra`, `ga_panchanga`, `ga_sensitive`, `ga_sensitive_degree`, `ga_transit_anchors`, `ga_prashna`, `ga_condition`, `ga_strength`, `ga_tajaka`, `ga_medical`, `ga_vastu`, `ga_structural`, `ga_sade_sati`, `ga_yoga`, `ga_vichara`
- **Evidence:** Every L1 `Earn.build_record` and `Cost.baseline` reads "NO_DETECTOR — instrument absent (migration 1094)". Claims an L1 asset emits that need a detector able to read false: `asset_throughput.state = 'lit'` (observed false on `ga_vargas`), `verification_pass_status` (CF-19), `count_sql`, `integrity_check_sql` (all 19 carry a contract since the Nirmāṇa W3 migrations 653–659, 740–754; the history shows they were red where defects were known), the floor. `asset_throughput.rows_per_second` is NULL on 19 of 19.
- **Design:** Track E owns the instrument; the asset side is a declaration of which emitted statuses are claims. Nothing in any L1 asset file changes.
- **Failing-first test and mutation:** Track E's own: a seeded false status must read FAIL.
- **Blast radius:** none for L1 assets.
- **Rebuild:** none.
- **Fix class:** detector/tooling; **buildable before J1:** tier-independent

## 5 · Rebuild consequences Track B needs per asset (facts found while reading the writers)

These are not gaps; they are what a level-by-level L1 rebuild must plan for (N-29 impact statement, rebuild plan, pre/post fingerprints). DAG levels from the layer instance §2.5: 0 `ga_positions`; 1 `ga_ayurdaya`, `ga_dashas`, `ga_nakshatra`, `ga_panchanga`, `ga_prashna`, `ga_sensitive`, `ga_sensitive_degree`, `ga_transit_anchors`, `ga_vargas`; 2 `ga_condition`, `ga_strength`, `ga_tajaka`; 3 `ga_medical`, `ga_structural`, `ga_vastu`; 4 `ga_sade_sati`, `ga_yoga`; 5 `ga_vichara`. Declaring `ga_dashas` → `ga_vargas` (CF-13) moves `ga_dashas` to level 2.

- **`ga_vargas` first (CF-16):** `chart_divisionals` is empty under a `lit` record; nothing that reads it should be rebuilt before the restore (code reading, not run: `ga_condition` would write `varga_dignity_composite` NULL again; `ga_dashas` `lord_natal_dignity_d1` NULL; `ga_strength` would drop its saptavargaja components; `ga_yoga` D9 detectors would not fire). After the restore: `ga_dashas`, `ga_condition`, `ga_strength`, `ga_structural`, `ga_sade_sati`, `ga_yoga`, then `ga_vichara`.
- **`ga_positions` (level 0, layer canary):** every other asset reads its rows; the writer was sound (W2 `rebuild_only`); a rebuild is expected to change nothing for the chart; fingerprint over the five categories must be equal before and after.
- **`ga_dashas` (largest table):** 483,870 rows; rebuild cost and the one-time upstream-hash signal when the `ga_vargas` edge is declared; hierarchical UUIDs are stabilised so a rebuild keeps them.
- **`ga_tajaka`:** the window follows the build clock (`reference_year` defaults to the build year), so a rebuild in 2027 writes 245 rows, not 240; fingerprints must fix the year.
- **`ga_structural` / `ga_yoga` / `ga_vichara`:** the cancellation back-read (CF-13) makes the first build and a rebuild differ for the daridra finding; after FD-1 the order is structural → yoga → vichara with no back-read.
- **Shared-table producers:** deletes are category-scoped and owner-receipt gated (`authorize_chart_fact_delete`); two assets deleting and re-inserting the same category collided once (migrations 416/419); keep the producers' categories disjoint (CF-02, CF-12).
- **Shared L0 `verification_vocab.py`:** an edit changes the source-hash closure of ~24 L1+L2 writers (CF-17); sequence it, or use `entry_for()`.
- **`ga_prashna`:** a natal build writes 0 rows by design (R-1); do not "fix" the zero count.

## 6 · Dispositions that differ from the layer instance, and who approves

The layer instance proposes no letters (TG-L1-017: no tier gives an evidence→letter rule; T2 §10.1 says "no quota"). This index proposes keep for 16, **enrich** for `ga_ayurdaya` (cancellations absent against T2 V12 wording) and `ga_yoga` (DP05 fields and D9 lineage absent), **qualify** for `ga_prashna` (valid and measurable only for question-moment charts; dormant by native ruling R-1). Six assets with 0 declared dependents (`ga_ayurdaya`, `ga_medical`, `ga_prashna`, `ga_sensitive_degree`, `ga_transit_anchors`, `ga_vastu`) are kept: absence of a declared consumer is not a retirement reason without an ablation instrument (layer instance §1.5), and each has a served reader.

**Approval under Track A §10:** keep, qualify and enrich (with or without fix designs) go to the Steward (G16); **any output change goes to SS (R5)**: the enrich assets and the fixes named "data (output change)" (CF-16 F-A2 and the restore, CF-19 tier changes, CF-13(b), `ga_condition` NULL columns, `ga_transit_anchors` lineage column, `ga_panchanga` spelling). Provisional approval before J1 covers only tier-independent designs.

## 7 · Questions for Strategic Suvarṇa (consolidated)

Curated from the per-asset questions (the full lists stay in each brief, §4 `Question for SS` and §7). Ordered by how many assets or gates the answer unblocks.

1. **CF-16 (6 direct / 61 transitive dependents):** may SS authorise the read-only diagnosis of the empty `chart_divisionals` (run history, per-chart counts, delete statistics, generation heads), own the restore dispatch (single-asset, sequential; production REVIEW), and approve F-A2 (widen the unique key to `fact_subject`, output change) for the same rebuild?
2. **CF-13:** declare `ga_dashas` → `ga_vargas` and `ga_yoga` → `ga_vargas` (after the restore; one-time rebuild signal)? Where does the daridra-cancellation pass belong: `ga_vichara`, a declared stale read, or a new post-yoga asset?
3. **CF-19:** after a read-only stored-tier census, may the `ga_sensitive` row-builder default and literal `two_pass_verified` stamps be corrected (L2 salience effect)? Does a consistency invariant that can fail (`ga_strength` aṣṭakavarga Σ = 337, `ga_sade_sati` cycle invariants, `ga_sensitive_degree` Yogi arcsecond re-evaluation) earn `two_pass_verified`, `classical_match` or `single`? Is a second derivation from `ga_positions` longitudes accepted for the four pañcāṅga FORENSIC angas? Which Yogi-point category is the authority?
4. **CF-02:** which asset owns the 420 rows both `ga_strength`'s predicate and `ga_structural`'s ownership name, do the 41,042 unowned `chart_facts` rows get owners, and do the rows a writer puts on `chart_facts` count as its `rows_written` (`ga_condition`)?
5. **CF-06:** is a fixed-vocabulary threshold grade (`indication_strength`, `direction_impact`, `strength_label`) narration for Null/Narr? (Decides `ga_medical`, `ga_vastu`, `ga_yoga` declarations.)
6. **CF-04:** does Dens read per partition for shared-table producers (inspector change) or is a table-level reading with a tier column enough, and is Dens N/A for an asset with no served read?
7. **CF-10:** should Build.history look only at runs since the last change to the asset's writer or registry row? Is the 2026-09-19 abort on `ga_positions` an asset failure or does it need a clean asset-set rerun (production run)?
8. **CF-12:** is "no orphan rows under the writer's own partition" the Idem claim for L1 delete-then-insert writers whose delete scope follows the rows written?
9. **CF-07:** is the verified subset the PASS population for D3 (never presence); is D2 (three rows, none averaged) the carriage check for `ga_ayurdaya`?
10. **`ga_ayurdaya` (enrich):** is the harana (cancellation) enrichment in the first L1 wave, and may it read `ga_structural`/`ga_condition` facts through new `depends_on` edges?
11. **`ga_yoga` (enrich):** may SS authorise the read-only per-yoga comparison of the last two builds (63 → 53 firings)? Are `partial_formation_pct`, `activation_dasha_periods` and a D9 lineage id in scope for the first L1 wave?
12. **`ga_prashna` (qualify):** is a registry-recorded dormancy (`data_disposition = RETAINED_AS_CAPITAL` + the R-1 text, migration 650) a sufficient basis for an N-22 N/A rule on Build.completion/Complete/Vocab, and is `qualify` the right letter?
13. **`ga_transit_anchors`:** lineage by a new `source_fact_ids` column, a declaration only, or integration into `chart_facts`? (An asset with 0 declared dependents and a served tool is retained, not retired, without an ablation instrument.)
14. **`ga_tajaka`:** is the clock-dependent hybrid window acceptable (record the reference year), or must a rebuild of a recorded build reproduce its window?
15. **`ga_condition`:** populate the four NULL composite columns (`avastha_lajjitaadi`, `avastha_sayanadi`, `speed_degrees_per_day`, `graha_yuddha_result`) from L1 facts, or drop them?
16. **CF-17 / CF-14 / CF-20:** named constants for the other vocabulary members in the shared L0 module (changes ~24 writers' source hashes) or `entry_for()` lookups; remove or keep the eight legacy `_telemetry` sites; where do the `condition_score` cut points live?
17. **Dispositions:** accept keep for 16, enrich for `ga_ayurdaya` and `ga_yoga`, qualify for `ga_prashna`.

## 8 · Notes on method and path

- **Path:** per Track A brief §8: `00_ARCHITECTURE/briefs/suvarna/layers/L1/assets/<ASSET_ID>_ELEVATION_BRIEF_v1_0.md` (revalidation bumps to v1.1). Fix designs live inside each brief (§4), not in separate `designs/` files; `INDEX.md` sits beside the briefs.
- **Evidence beyond the census, all in the repository:** the Nirmāṇa W2 decisions (`00_ARCHITECTURE/briefs/nirmana/sessions/L1_W2_DECIDE_v1_0.md`, 139 findings triaged) and the registry/writer fixes that followed (migrations 650, 651, 652–659, 740–754, 842, 843, 868–895, 914–920), read against current code to tell which findings are already on main; Track I's edge evidence (`/Users/Dev/suvarna-evidence/TrackI/edges_evidence.md`, a working-location file, not in the repo); the E6.1 Dens before/after (`/Users/Dev/suvarna-evidence/E6.1/dens_before_after.md`, working location).
- **Gap classification** (real / SS question / detector / stale / history / information) is this lane's reading of the saved census, the ledger and the code; no tier supplies a rule mapping evidence to a disposition (TGH-T3-03).
- **Fixes go in the asset or the registry, never in the frozen orchestrator** (T4 §4.2): every design respects that; none needs a `WriterBase` change.
- **Facts not established offline** are marked in the briefs: the cause of the empty `chart_divisionals`; whether the 4,670-row and 426-row differences are unowned categories or losses; the stored tier distribution per asset; the live `count_sql` of `ga_sensitive_degree`; per-emitter tier earning in the 3,251-line `ga_sensitive` writer; the unread composition sites for the undeclared `prose_fields`; whether the orchestrated substep path reaches `ga_dashas`' per-row verifier; the applied state of migration 1210.
- **Staleness to watch:** the saved census predates REGISTRY_REVISION 5/6 and migration 1210; the ledger is not on main; the layer instance reads code at `e2352f88`; the Dens re-scan here (main tree) and E6.1's (tree 0b9cdd37a) differ for `ga_structural`.

## 9 · Format used (reuse for the next layers)

Each brief is `<ASSET_ID>_ELEVATION_BRIEF_v1_0.md` with the L0 frontmatter and section list: **§0 Identity** (what the asset is with file:line, then a field table) · **§1 Measured state and the nine gates** (saved-census table of non-PASS cells, compact PASS list with `†` for criteria whose definition changed, the offline rollup line, the offline Dens rev-4 and Null/Narr readings) · **§2 Gaps** (real / SS question / detector / stale / history / information) · **§3 Disposition** (closed set, with approver) · **§4 Fix designs** (one FD per real gap, then the shared CF-nn entries that apply) · **§5 Semantic fingerprint contract** · **§6 Preserved kernel, carriage check, opportunities** · **§7 Questions for Strategic Suvarṇa**. `INDEX.md` carries: what the index rests on and what is stale, rollup counts, the asset table, shared fixes ordered for J1, rebuild consequences, dispositions and approvers, curated SS questions, method notes and this section.
