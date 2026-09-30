---
artifact: L3_LAYER_INSTANCE
canonical_id: SUVARNA_L3_LAYER_INSTANCE
version: "1.0"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_on: 2026-09-30
produced_in: "Exec Suvarṇa"
plan_item: "A.L3i (step 2: layer-instance draft)"
layer: L3 (Kāla)
template: 00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md   # tier 3, SEALED; numbering and section order below are the template's own
inherits:
  T1: 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md
  T2: 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md
  tier_files_read_at: "/Users/Dev/suvarna-census, commit 2a78ec64d (line numbers are that checkout's)"
census_run:
  path: /Users/Dev/suvarna-evidence/census/census_L3.json (+ census_L3.log, SUMMARY.md)
  exit_code: 2   # FAIL rows present = MEASURED (TRACK_A_BRIEF §3); 21 of 21 active assets measured, 0 ERRORED
  inspector_commit: 2a78ec64d88e59438bd6527b4c99826432102c57
  chart_scope: 482012f1-710e-4a25-994a-93821f5871aa
  generated: "2026-09-30T20:25:37+05:30"
  runtime: "84 s (SUMMARY.md)"
tier_gaps: 00_ARCHITECTURE/briefs/suvarna/layers/L3/L3_TIER_GAPS_v1_0.md   # TG-L3-001 … 027
inputs_not_authority: "nikasha_test/derivations/L3_INSTANCE_SKELETON.md and L3_INVENTIONS.md (2026-09-26, sandbox census, 23 assets). Every lead was re-checked against the tier text and the 2026-09-30 census; where they disagree the disagreement is reported (§B)."
changelog:
  - "1.0 (2026-09-30): first draft. Filled from tiers 1-2 and the L3 census only; every clause the tiers do not supply is marked TIER GAP with its TG-L3 id and is left unfilled. No disposition, no synergy fraction and no certification is written (the status line forbids the last). The five family assets are MEASURED AND RECORDED, never decided (Pravāha and the family sessions own them; TRACK_A_BRIEF §6)."
---

# L3 Kāla — layer instance (draft 1.0, PROVISIONAL)

**Reading rules for this draft.**
- **Measured, not typed.** Every figure carries its source in the `measured_by` line of its section. Source tags: **CEN** = `census_L3.json` (key path `L3.assets[<id>].measurements[<criterion>]` or a layer-level field); **REG** = `asset_registry` read as `suvarna_reader` on 2026-09-30 (population stated); **GRP** = grep/find over `/Users/Dev/suvarna-census` at 2a78ec64d, population stated; **SEED** = block-scoped parse of `platform/scripts/seed/asset_registry_seed.ts` at 2a78ec64d; **T1/T2/T3** = a tier clause, cited by section and line.
- **Unfilled is honest.** "TIER GAP: TG-L3-nnn" = the tiers do not supply the clause (see the gaps file). "NOT MEASURED" = the tier specifies the measure but no instrument produced it in this pass (the reason is given).
- **Family assets are out of bounds for any decision.** `ka_gochara`, `ka_gochara_resonance`, `ka_vedha_gochara`, `ka_sangam`, `ka_kshetra` (and their tables) belong to the Pravāha campaign and the family sessions. This document records what was measured about them and what reads them. It states no disposition, target or fix for them.
- **Population.** 21 active L3 assets (CEN `L3.population_active`), of 23 registry rows (`L3.population_registry_total`); the two excluded are inactive (`ka_gochara_sweep`, RETIRED; `ka_gochara_v3_century_materialize`, CURRENT but `is_active = f`; CEN `L3.population_excluded_inactive`). Of the 21: 17 have a table and a chart-scoped `count_sql`; 4 are services with no table (`ka_dasha_kala`, `ka_graha_sancara`, `ka_muhurta_seva`, `ka_tulana`; REG `asset_kind = 'service'`).

---

## Part 0 · VALUE — the origin

### 0.1 · What cannot be answered without this layer

```
inherits:    Product §2 (P01-P24), Data plane §2 (V01-V13)
measured_by: none — definitional; every P/V cited was checked to exist in the parent under its current numbering (T1 lines 154-179; T2 lines 115-129)
traces_to:   —  (this IS the origin)
```

**TIER GAP: TG-L3-001.** Neither sealed parent assigns P-needs or V-journeys to layers (T1 §2 and T2 §2 are not keyed to layers; the only layer keying is T1 §11 and T2 §3.1). Only one row is anchored to L3 by the tiers themselves. The other rows below are the P/V rows whose own wording asks *when* or *which period*; that is a reading of their text, not a tier assignment, and whether L3 is *necessary* (rather than *involved*) to each is not decided by any tier. They are listed so the brief authors have the candidates and no more.

| P / V | anchoring | the distinction that disappears without this layer (quoted from the parent's own text) |
|---|---|---|
| **P24 / V13** | **tier-anchored** (T1 line 178; T2 lines 129, 335, 427) | "which mechanisms are active now, what they are doing, and how the current interval differs from the one before it" — T2 §5 (line 335): "L3 owns the interval set and its boundaries" |
| P09 | wording (T1 line 164) | "multiple activation routes, nearest versus better-supported window" |
| P10 | wording (T1 line 165) | "Enduring structure versus temporal expression, recurrence with differences" |
| P03, P04 | wording (T1 lines 158-159) | "When will I make substantial money…", "When will my business succeed…" — timing questions |
| P11 | wording (T1 line 166) | "When might I initiate something" — timing context |
| V04 | wording (T2 line 120) | "multiple qualified temporal routes, recurrence, inhibition and horizon coverage. Nearest contact is not automatically full manifestation" |
| V02 | wording (T2 line 117) | "Structural routes and timing must retain these distinctions" |
| V05 | wording, partial (T2 line 121; T2 §5 line 337: "Preserve existing services") | Praśna/Muhūrta operators and calendar context; only the service `ka_muhurta_seva` is named in this layer's registry population |

The prediction chain of T1 §7 (lines 362-365) places L3 at one link: "eligible structural mechanism → **applicable temporal activation** → qualified manifestation alternatives". T1 §11 (line 503) gives the layer's product responsibility: "Which structures are engaged by which clocks, when, under what conditions and with which alternatives".

### 0.2 · The layer's objective

```
inherits:    Product §1 (the join), §11 (this layer's row), Data plane §3.1 (this layer's row)
measured_by: none — definitional
traces_to:   0.1
```

**Owned question** (T2 §3.1, line 142): "Which of those structures are engaged, how, when and under what conditions?"
**Contribution handed onward** (same row): "Structure–time mechanisms, background/enablement/contact/inhibition intervals, recurrence, comparisons and coverage-qualified windows."
**What it must not claim** (same row): "Activity/intensity as event probability; precise geometry as equally precise life timing."
**Scored on** (T1 §11 line 503; §14 line 593): **Temporal integrity** — "Correct boundaries, zones, hierarchy, horizons, nearest versus better-supported separation, and absence-versus-unavailable semantics." T1 §11 adds "honest 'none found' semantics" and T1 §7.1 (line 376) states the "none found" duty: "state the searched horizon, resolution and method coverage".
**What L3 is told to preserve** (T2 §6.4, lines 369-384): "the expensive useful capital in transit engines/sweeps, precise daśā timelines, annual and return methods, temporal joins and materializations"; the distinction of "raw celestial motion, chart-relative contacts, eligible activation, convergence/comparison, scenario publication and consumer projection"; "Similar names may represent different stages of this chain rather than redundant assets."

**TIER GAP: TG-L3-002.** T3 §0.2 also asks for "what it computes that existing software does not". The tiers state the plane-level answer (T1 lines 51-59; T2 lines 60-67) and no L3-specific comparison; none is written here.

### 0.3 · Its place in the wheel

```
inherits:    Data plane §3.2 (five edge types), §7 (DP contracts)
measured_by: REG (all 129 asset_registry rows read; depends_on of the 21 active kala rows and the readers of each, 2026-09-30) · SEED (23 ka_* blocks) · migration pin: NOT MEASURED (see below)
traces_to:   0.2
```

**Receives from (by DP contract, T2 §7.1 lines 420-427).** DP01 identity/release (L0 → all writers); DP02 rule qualification (L0 → calculation, interpretation); DP03 chart facts (L1 → L2–L4/services); DP04 condition decomposition (L1 → L2/L3/L4); DP05 configuration (L0+L1 → L2 → L3); DP06 structural relationship (L2 → L3 and inquiry); DP07 precise clocks/contacts ("L0/L1/L3 primitives → temporal integrators").
**Hands onward (by DP contract).** DP08 temporal mechanism and DP09 manifestation (T2 lines 427-428: "L3+qualified structural/rule evidence → L4"). **TIER GAP: TG-L3-003** — the DP08 row's producer column reads "L2+qualified clocks → L3 consumers" and does not name L3 as producer; T2 §3.1 ("hands onward: structure–time mechanisms") and §5 (line 335) are the basis for reading L3 as its producer. This draft follows that reading and flags it.
**What the join needs from it** (T2 §3.4 line 197): "The clock geometry, the activation rule, the named nearest-versus-better-supported criterion, and the manifestation bridge or its falsifier" — see 2.2.

**The dependency graph, measured (REG).** 21 active L3 assets; 83 `depends_on` edges among them and their upstreams: **31 intra-L3 edges and 52 cross-layer edges** (cross-layer upstream assets: L1 `ga_*` 6, L2 `bo_*` 5, L0 `bg_*` 10). No edge from an active asset points to an inactive or unregistered asset, and the active graph has no cycle (REG, all 129 rows; DFS). Per-asset upstreams and readers are in §3.4. **TIER GAP: TG-L3-005** — T3 asks for edges "by edge type"; every registry edge reads as a *computational* edge (T2 §3.2 item 2, line 161: "It follows the actual governed DAG"); the other four edge types have no registry representation.

**Three sources (T3 line 135).** **TIER GAP: TG-L3-004** — the tiers define neither "seed" nor "migration-governed pin".
- **live REG**: as above.
- **SEED** (`platform/scripts/seed/asset_registry_seed.ts` at 2a78ec64d, 23 `ka_*` blocks parsed block by block): **18 of 23 `depends_on` arrays identical to live; 5 differ.** ka_gochara — seed `[bg_gochara_arcs, ka_gochara_resonance]`; live adds `bg_ephemeris, bg_transit_rules, ga_dashas, ga_positions, ga_yoga, ka_moorti_nirnaya, ka_vedha_gochara` and drops `bg_gochara_arcs`. ka_kshetra — live adds `ka_vedha_gochara`. ka_sangam — live adds `ka_vedha_gochara`. ka_muhurta_seva — seed `[ka_graha_sancara]`, live empty. ka_vighnakara — seed has `ka_gochara`; live has `bg_dignity_reference` and `ka_yojaka` instead. (Three of the five are family assets: recorded, not judged.)
- **migration-governed pin**: **NOT MEASURED.** No tier defines it and CEN carries no pin read (register R132/R86 propose the instrument).

### 0.4 · The alignment test

Every section below carries a `traces_to:` line naming a 0.1 row or a 0.2/0.3 item. Run on this draft: no section was struck. Sections 1.2, 1.3, 3.2, 3.3, 4.2 are kept because the template requires them, and each states plainly what the tiers or the instruments do not let it say.

---

## Part 1 · VALUE DECOMPOSITION

### 1.1 · Inventory, measured

```
inherits:    Data plane §13.3 item 2
measured_by: CEN (`L3.assets[*]`: live_rows via each asset's own count_sql at chart 482012f1, Build.* cells, reach) · REG (asset_registry rows for layer 'kala', 2026-09-30: target_table, target_floor, asset_kind, scope, has_substeps, catalog_status) · population: 21 active assets, 4 of them services
traces_to:   0.3
```

`live` = CEN `live_rows` (row count of the asset's own `count_sql` for the canonical chart); `floor (REG)` = REG `target_floor`. Cell letters: **P** PASS · **F** FAIL · **p** PARTIAL · **-** N/A · **·** criterion not emitted for that asset. Columns: `compl` = Build.completion, `count.floor` = Count.floor verdict, `hist` = Build.history, `dep` = Build.dep_liveness, `idem` = Idem.pattern, `dens` = Dens.served.

| asset | kind | target table | live | floor (REG) | writer file (CEN) | compl | count.floor | hist | dep | idem | dens |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ka_avadhi | data | kala_avadhi | 1,169 | 1,169 | ka_avadhi.py | F | P | F | p | P | F |
| ka_bhavishya_lekha | artifact | kala_bhavishya | 0 | 100 | ka_bhavishya_lekha.py | F | F | p | p | P | F |
| ka_dasha_kala | service | — | (service) | 0 | services/ka_dasha_kala/writer.py | - | - | p | P | p | F |
| ka_gochara | data | kala_gochara_windows | 0 | 83 | ka_gochara.py | F | F | p | P | p | F |
| ka_gochara_resonance | data | gochara_resonance_map | 765 | 762 | services/ka_gochara_resonance/writer.py | P | P | p | P | P | - |
| ka_graha_sancara | service | — | (service) | — | ka_graha_sancara.py | - | · | P | P | p | F |
| ka_jivana_parva | artifact | kala_jivana_parva | 100 | 100 | ka_jivana_parva.py | P | P | p | p | P | F |
| ka_kala_darshana | artifact | kala_darshana | 0 | 750 | ka_kala_darshana.py | F | F | p | p | P | F |
| ka_kalasutra | artifact | kala_activation | 0 | 335,403 | ka_kalasutra.py | F | F | p | p | P | F |
| ka_kota_chakra | data | kala_kota_chakra | 585 | 588 | services/ka_kota_chakra/writer.py | P | F | p | P | P | F |
| ka_kshetra | data | kala_field | 8,570,075 | 8,599,775 | services/ka_kshetra/writer.py | F | F | F | p | F | - |
| ka_moorti_nirnaya | data | kala_moorti_nirnaya | 74 | 72 | services/ka_moorti_nirnaya/writer.py | F | P | p | P | P | F |
| ka_muhurta_seva | service | — | (service) | — | services/ka_muhurta_seva/writer.py | - | · | P | - | p | F |
| ka_sangam | artifact | kala_convergence | 0 | 14,868 | ka_sangam.py | F | F | p | p | P | F |
| ka_sudarshana_varsha | data | kala_sudarshana_varsha | 120 | 120 | services/ka_sudarshana_varsha/writer.py | P | P | p | P | P | F |
| ka_taranga | data | kala_taranga | 92,412 | 92,412 | ka_taranga.py | P | P | p | F | P | F |
| ka_tithi_pravesha | data | kala_tithi_pravesha | 120 | 120 | services/ka_tithi_pravesha/writer.py | P | P | p | P | P | F |
| ka_tulana | service | — | (service) | 0 | services/ka_tulana/writer.py | - | - | p | p | p | F |
| ka_vedha_gochara | data | kala_vedha_gochara | 171 | 176 | services/ka_vedha_gochara/writer.py | F | F | p | P | P | F |
| ka_vighnakara | artifact | kala_obstruction | 0 | 536 | ka_vighnakara.py | F | F | p | p | P | F |
| ka_yojaka | artifact | kala_activation_predicates | 50,678 | 50,104 | ka_yojaka.py | P | P | p | p | P | F |

**Family assets in the table:** ka_gochara, ka_gochara_resonance, ka_vedha_gochara, ka_sangam, ka_kshetra (and ka_yojaka, flagged as a claimed prerequisite in Appendix A).

**Inactive registry rows (not in the 21).** `ka_gochara_sweep`: RETIRED, target `kala_gochara_windows`, `target_floor` 16,297, `data_disposition` RETAINED_AS_CAPITAL, `superseded_by` ka_gochara. `ka_gochara_v3_century_materialize`: `is_active = f`, catalog_status CURRENT, target `kala_gochara_windows_v2`, `target_floor` 914; it has a registered writer (CEN `L3.phantom_registered`).

**Registered writers against the registry** (CEN `L3.registered_ids` = 22; `L3.registry_has_writer` = 21; `L3.phantom_registered` = ['ka_gochara_v3_century_materialize']). This is the registry anomaly the task asked to be recorded, **no action**: 22 registered writer ids against 21 active assets. The Nirmāṇa W0 field-contract register counts 22 *active* identities including the century writer; the live registry counts 21 active (see §B).

**Multi-table and shared-table facts** (TIER GAP: TG-L3-024; the model is the template's, the facts are measured):
- `ka_kshetra` writes 15 tables (GRP: INSERT/DELETE/UPDATE targets over `platform/python-sidecar/services/ka_kshetra/**/*.py`, tests excluded, at 2a78ec64d: kala_field, kala_field_null, kala_field_windows, kala_field_provenance, kala_field_salience, kala_field_kinematics, kala_field_primitives, kala_field_promise_nodes, kala_field_promise_edges, kala_field_routes, kala_field_clocks, kala_field_boundaries, kala_field_snapshots, kala_insights, kala_timeline_spec); the registry's structured fields name one (`target_table` kala_field, `count_sql` over kala_field only, `clear_tables` empty; CEN `count_sql_tables` = ['kala_field']). `natural_key_partition` (free text) lists 13 of them with keys.
- `kala_insights` has two inserting writers in two layers (`services/ka_kshetra/writer.py:1387`, `services/mi_bhara/db.py:380`; GRP over `platform/python-sidecar/**/*.py` excluding tests).
- `kala_gochara_windows` (REG count by generation, canonical chart): generation '3.0' 914 rows, generation 'v1' 16,297 rows; `kala_gochara_windows_v2`: 1,001 rows. ka_gochara's registry `count_sql` is `… WHERE chart_id=$1 AND generation='4.0'` and its `target_floor` is 83. The census therefore reads live = 0 against floor 83 (CEN Count.floor FAIL, Build.completion FAIL "empty: live=0"), while 17,211 rows (914 + 16,297) sit in the table under other generation labels. The Idem cell reads PARTIAL for the recorded reason: the registry declares `kala_gochara_windows`, the writer replaces `kala_gochara_windows_v2` (CEN ka_gochara Idem.pattern). Recorded, not judged (family asset).

**Rows the census could not credit as built (cascade-shaped zeros).** Six active assets read live = 0 on the canonical chart: ka_bhavishya_lekha, ka_gochara, ka_kala_darshana, ka_kalasutra, ka_sangam, ka_vighnakara. Five of these (all but ka_gochara, whose zero is the generation pin above) target the five L3 tables that are the referencing side of `ON DELETE CASCADE` foreign keys into `bodha_msr_signals` (REG `pg_constraint` where `confrelid = bodha_msr_signals`: eight cascade keys from seven tables, five of them L3: kala_activation, kala_bhavishya, kala_convergence, kala_darshana, kala_obstruction). The build records still say rows were written (rows_written = 100, 750, 335,403, 14,868, 536; CEN Build.completion text). The cause is **inferred** from the keys, not measured; TIER GAP: TG-L3-027.

**Latest build record and executed-run counts (CEN `Earn.build_record`, `Build.exercised`).**

| asset | latest attempt at chart 482012f1 (run, state/disposition, date) | executed runs of build_run_assets rows |
|---|---|---|
| ka_avadhi | 474811e3 error/no disposition 2026-09-10 | 49 of 98 |
| ka_bhavishya_lekha | cbd6ea44 complete/no disposition 2026-08-13 | 41 of 111 |
| ka_dasha_kala | 8e00f2cd complete/build 2026-09-10 | 43 of 100 |
| ka_gochara | a96ba6b9 complete/build 2026-09-10 | 35 of 59 |
| ka_gochara_resonance | 8d74930c complete/skip_no_delta 2026-09-07 | 22 of 27 |
| ka_graha_sancara | fef77aaf complete/no disposition 2026-07-26 | 29 of 51 |
| ka_jivana_parva | cbd6ea44 complete/no disposition 2026-08-13 | 40 of 109 |
| ka_kala_darshana | cbd6ea44 complete/no disposition 2026-08-13 | 40 of 109 |
| ka_kalasutra | cbd6ea44 complete/no disposition 2026-08-13 | 49 of 110 |
| ka_kota_chakra | 8d74930c complete/skip_no_delta 2026-09-07 | 10 of 15 |
| ka_kshetra | 6e47cae4 error/no disposition 2026-09-11 | 98 of 158 |
| ka_moorti_nirnaya | 8d74930c complete/skip_no_delta 2026-09-07 | 11 of 16 |
| ka_muhurta_seva | fef77aaf complete/no disposition 2026-07-26 | 29 of 51 |
| ka_sangam | cbd6ea44 complete/no disposition 2026-08-13 | 55 of 103 |
| ka_sudarshana_varsha | 8d74930c complete/skip_no_delta 2026-09-07 | 7 of 10 |
| ka_taranga | cbd6ea44 complete/no disposition 2026-08-13 | 46 of 109 |
| ka_tithi_pravesha | 8d74930c complete/skip_no_delta 2026-09-07 | 11 of 16 |
| ka_tulana | cbd6ea44 complete/no disposition 2026-08-13 | 38 of 106 |
| ka_vedha_gochara | 5369367f complete/skip_no_delta 2026-09-07 | 8 of 17 |
| ka_vighnakara | cbd6ea44 complete/no disposition 2026-08-13 | 43 of 104 |
| ka_yojaka | a085a8b7 complete/build 2026-09-10 | 49 of 97 |

Columns, contract fields live and "whether current code on any live head differs from what is deployed": column counts are in CEN `Complete.depth` and `reach.columns_built`; **contract fields live: NOT MEASURED (TG-L3-011)**; **deployed-versus-current-code: NOT MEASURED for the layer** (R87). One fact is known: PR #2731 (commit 285bff17c) changed `platform/python-sidecar/services/ka_kshetra/` and is an ancestor of origin/main but **not** of the inspector commit 2a78ec64d (git merge-base --is-ancestor, both checked), so the writer code CEN read for ka_kshetra predates it.

### 1.2 · Individual contribution — ablate one

```
inherits:    Product §14.1 (ablation), Data plane §12.2
measured_by: NOT MEASURED — no ablation harness exists (T2 §12.2 line 627 for the synergy case; none is defined for a single asset's reading). What CEN does measure is the reach of each asset (below).
traces_to:   0.1 (which rows this asset serves)
```

T3 §1.2 permits "unmeasurable — not reached" where no served path exists. No individual term is written. What is measured, from CEN and REG, is how far each asset is read:

| asset | serving modules that select it (CEN `reach.modules`, file names) | modules counted by Dens.served | direct dependents (all layers) | transitive dependents (CEN `blocking_radius`, active assets, every layer) |
|---|---|---|---|---|
| ka_avadhi | query_dasha_dossier.ts | 1 | 1 | 1 |
| ka_bhavishya_lekha | query_projections.ts, query_temporal_activation.ts | 2 | 1 | 18 |
| ka_dasha_kala | — | 1 | 3 | 29 |
| ka_gochara | reading_checklist.ts, register_gochara_windows.ts | 1 | 2 | 26 |
| ka_gochara_resonance | register_gochara_windows.ts | 0 | 2 | 30 |
| ka_graha_sancara | — | 1 | 0 | 0 |
| ka_jivana_parva | query_life_arc.ts | 1 | 0 | 0 |
| ka_kala_darshana | query_temporal_view.ts | 1 | 3 | 21 |
| ka_kalasutra | call_service_wrappers.ts, query_temporal_activation.ts, register_d8_assess_domain.ts | 2 | 2 | 22 |
| ka_kota_chakra | query_kota_chakra.ts | 1 | 0 | 0 |
| ka_kshetra | — | 0 | 2 | 2 |
| ka_moorti_nirnaya | query_moorti_nirnaya.ts | 1 | 1 | 27 |
| ka_muhurta_seva | — | 1 | 2 | 26 |
| ka_sangam | query_convergence_windows.ts | 2 | 11 | 25 |
| ka_sudarshana_varsha | query_sudarshana_varsha.ts | 1 | 0 | 0 |
| ka_taranga | query_activation_waveform.ts | 1 | 0 | 0 |
| ka_tithi_pravesha | query_tithi_pravesha.ts | 1 | 0 | 0 |
| ka_tulana | — | 1 | 0 | 0 |
| ka_vedha_gochara | query_vedha_gochara.ts | 1 | 3 | 30 |
| ka_vighnakara | query_obstruction_periods.ts | 1 | 5 | 22 |
| ka_yojaka | query_temporal_activation.ts | 1 | 4 | 26 |

CEN's two module counts differ for 8 assets (`reach.modules` vs the count in `Dens.served`); both are the inspector's own populations and are shown as emitted. Four assets have no serving-module row in `reach` (the four services); their `Dens.served` cell names `call_service_wrappers.ts`. `ka_kshetra` has zero serving modules and two registry dependents (mi_bhara, mi_sankalpa, both L5).
**TIER GAP: TG-L3-022** (T3) and **TG-L3-023** (T4) — what "ablate one", "rows", "kernel" and a service descriptor mean for the four services.

### 1.3 · Synergistic contribution — ablate the group

```
inherits:    Data plane §3.4 (presentation contract), §7 (DP contracts), the layer's synergy binding if one exists
measured_by: NOT MEASURED — absent instrument (T2 §3.5 lines 235-237: "where the term cannot yet be measured, that is recorded as an absent instrument, never as a number")
traces_to:   0.2
```

**TIER GAP: TG-L3-006** — T2 §3.5 binds four PLANE-level seams; no tier gives a layer-level seam list, so "the layer's synergy binding" does not exist for L3. Seam-by-seam facts that can be stated without a harness, each with its instrument:

| seam (T2 §3.5 lines 223-228) | what CEN/REG can say about L3 | state |
|---|---|---|
| edge ordering | 31 intra-L3 edges, six topological levels (0–5, §2.5), no cycle (REG) | measured (ordering only; whether ordering "lets one asset's output be another's input" at consumers is not) |
| DP contracts | which L3 asset produces which contract, which columns carry it | NOT MEASURED — TG-L3-011 |
| controlled vocabulary | independent-map census per class | NOT MEASURED — CEN `L3.local_map_candidates` = -1 (no detector); TG-L3-015 |
| presentation contract | which §3.4 rows L3 carries and hands onward | NOT MEASURED — TG-L3-009 |

No fraction of the total is recorded (T3 lines 249-251).

### 1.4 · Cross-layer handoff — what it produces for downstream

```
inherits:    Data plane §11 (six evidence states), §7 (DP contracts this layer PRODUCES)
measured_by: REG `depends_on` readers (declared edges only) · CEN `reach.modules` (serving modules) · verification at the consumer: NOT MEASURED (no consumer-side probe exists; R157/R106)
traces_to:   0.3 (hands onward)
```

Declared L3 → L4/L5 readers (REG, 2026-09-30):
- **L4** `ph_muhurta` (reads ka_gochara, ka_kalasutra, ka_sangam, ka_vighnakara), `ph_nimitta` (ka_bhavishya_lekha, ka_sangam), `ph_pratikara` (ka_sangam, ka_vighnakara; catalog_status DRAFT).
- **L5** `mi_adhilepa` (ka_sangam), `mi_bhara` (ka_kshetra), `mi_sankalpa` (ka_kshetra).
- L3 assets read by no active asset in any layer: ka_graha_sancara, ka_jivana_parva, ka_kota_chakra, ka_sudarshana_varsha, ka_taranga, ka_tithi_pravesha, ka_tulana (zero dependents in `blocking_radius`); they are read, if at all, through serving modules (§1.2 table).

For each declared reader the position on T2 §11's ladder (source present → qualified → consumed → traceably transformed → served → value evaluated) is: **declared edge only.** "Consumed" is not established by `depends_on` (T2 §7.1 line 416: "A citation with no declared use does not prove utilization"), and a consumer-side verification is not measured (TIER GAP: TG-L3-012 for declared use). The full reader set of the family assets is in Appendix A.

### 1.5 · The accounting

```
inherits:    —
measured_by: 1.2 + 1.3 + 1.4 against 0.2
traces_to:   0.2
```

**Not computed.** 1.2 has no harness, 1.3 is an absent instrument, 1.4 is declared-edge only. The elevation delta (the shortfall against 0.2) is therefore not stated as a number, and no asset is marked ≈ 0 on all three terms (T3 line 245 requires a candidate to be evidenced, and T3 lines 249-251 forbid inventing a fraction). What can be said is the measured state of the layer's gates: CEN cell tallies over the 21 assets are FAIL 42, PARTIAL 42, NO_DETECTOR 63, PASS 195, N/A 13, NOT_GENERIC 42, ERRORED 0 (equal to SUMMARY.md); the FAIL cells are Dens.served 19, Build.completion 10, Count.floor 9, Build.history 2, Idem.pattern 1 and Build.dep_liveness 1. These are gate and floor measurements, not a measure of the layer's value.

---

## Part 2 · CONDITIONS UNDER WHICH THE VALUE IS REAL

### 2.1 · Correctness rules

```
inherits:    Product §8.1 (this layer's row), §13; Data plane §9.2 (the switch and the storage separation)
measured_by: a detector per rule — NONE FOUND in CEN (19 criteria; none concerns the switch or circularity). Test files matched by name only: GRP `find platform/python-sidecar -iname '*circularity*'` at 2a78ec64d returns tests/l3/ka_kshetra/test_circularity_guard.py, tests/l3/test_ka_jivana_parva_circularity_guard.py, tests/l5/test_mi_bhara_circularity_guard_w2.py (contents not verified in this pass)
traces_to:   0.2 — the value is real only if these hold
```

**The rule, verbatim** (T1 §8.1 line 425; T2 §9.2 lines 516-517): "**Using the observed event to choose the supposedly prior trigger.**" Violating it "makes the output wrong, not merely inappropriate." The plane-wide rules that hold whatever the switch state (T2 lines 514-517): "biography must never alter a chart fact; a biography-dependent support must never be presented as event-free chart structure".
**Also binding on L3** (T1 §13 line 566; T2 §3.2 line 166): no invented computation, source, detector, confidence or score; "A chart-specific L4 conclusion must not feed back into the L3 computation as independent evidence."

**The switch at layer grain** (T2 §9.2). ON: "L3 alignment of reported intervals against independently established mechanisms, and inspection of unmatched windows" (line 500). OFF: "Nothing derived from life events, anywhere. Every reading emits only what the chart, sources and methods produce on their own" (line 501). Storage separation (lines 510-512): "event-conditioned overlays are kept separate from event-free structural and temporal products. Turning the switch OFF deselects the overlays; it never requires recomputing the event-free products." The emission record carries the switch state beside the information cutoff (line 500; T1 §7.2 line 382).
**TIER GAP: TG-L3-007** — which L3 assets or tables are event-conditioned overlays and which are event-free products is not stated by any tier, so "OFF is a selection" cannot be checked per asset. **TIER GAP: TG-L3-008** — no tier names a detector for the rule, and none is written here. Recorded fact only: the Kṣetra writer's own docstring states "Nothing here reads the life-event log" and points to `tests/l3/ka_kshetra/test_circularity_guard.py` "(static census + dynamic hash invariance)" (GRP, `services/ka_kshetra/writer.py`); that is a statement in code about a family asset, not a measurement made in this pass.

### 2.2 · Presentation obligation

```
inherits:    Product §2 (two modes, one depth); Data plane §3.4 (the field → contract mapping)
measured_by: presentation-parity test (T2 §12.2 line 614): NOT MEASURED, and its ownership is contested between the tiers (TG-L3-010)
traces_to:   0.1 — the acharya rows are unservable if these fields are not carried
```

**The temporal row** (T2 §3.4 line 197; T3 lines 284-286), which L3 must "retain and hand onward, not merely use internally": the clock geometry, the activation rule, "the named nearest-versus-better-supported criterion", and the manifestation bridge or its falsifier, carried by DP07 (clocks/contacts), DP08 (temporal mechanism), DP09 (manifestation). T2 line 199-202: "A component may present less; it may not *compute* less or *hand onward* less."
**TIER GAP: TG-L3-009** — the other §3.4 rows (method/school; prerequisites tested and exceptions checked; conventions in force; intermediate quantities; dignity components; competing readings; chain of influence) are mapped to DP contracts, not to layers; which of them L3 carries for its own findings is unassigned. **TIER GAP: TG-L3-010** — T2 §1/§12.2 mark presentation parity **[TRANSFERS]** ("a layer plan does not inherit it as its own work"), T3 §5.4 test 4 makes it an acceptance test of this instance. **TIER GAP: TG-L3-018** — the "named criterion" the temporal row must carry is not named or bounded by any tier.

### 2.3 · Contracts produced and consumed

```
inherits:    Data plane §7 (DP01-DP17), §7.1 (common envelope)
measured_by: NOT MEASURED — no instrument verifies fields and grain at both ends (TG-L3-011); the rows below are the contracts the tier text assigns, quoted, with the assignment to L3 assets left open
traces_to:   0.3
```

**Produced by L3** (T2 §7.1; identity and generation per the common envelope, lines 412-416). TIER GAP: TG-L3-003 (producer of DP08), TG-L3-011 (asset, fields, grain).

| contract | consumer | what the tier says it carries (quoted) | asset(s) and columns |
|---|---|---|---|
| DP07 precise clocks/contacts (L3 supplies primitives; also an integrator) | temporal integrators | "Parent/child clocks, actual interval boundaries, geometry, reference frame, coverage and uncertainty; retain exact data until final presentation." (line 426) | TIER GAP: TG-L3-011 |
| DP08 temporal mechanism | L3 consumers, L4 | "Same mechanism/configuration ID, engaged participants, qualified necessary/optional conditions, enablement/inhibition, alternate routes, horizon, and **for the present-tense need (P24) the interval now active and the one immediately preceding it**, each with its engaged participants. No topology-only gating." (line 427) | TIER GAP: TG-L3-011 |
| DP09 manifestation (L3 evidence in; L4 produces) | L4 | "Outcome subtype, competing expressions, required bridge, falsifier, constraints and temporal scope; intensity is not event probability." (line 428) | L3 supplies inputs only |

**Consumed by L3** (T2 §7.1; each consumed input must "declare its use — calculation, applicability, counter-evidence, uncertainty, interpretation, exclusion, navigation, evaluation", T3 lines 294-299; TIER GAP: TG-L3-012 — no declaration exists in the registry or anywhere else).

| contract | producer | what the tier says it carries (quoted) |
|---|---|---|
| DP01 identity/release | L0 | "Canonical entities, qualified aliases, units and released definitions" (line 420) |
| DP02 rule qualification | L0 | "Exact rule clauses, method, school/tradition, the prerequisites and exceptions that must be tested … invocation is not application" (line 421) |
| DP03 chart facts | L1 | "`fact_id`, grain/value/unit, chart/build, ayanāṃśa/frame/varga, input precision and verification; no downstream re-derivation" (line 422) |
| DP04 condition decomposition | L1 | "Retain zeros as zeros and unavailable as unavailable" (line 423) |
| DP05 configuration | L0+L1 → L2 | "Formation, participants, every clause tested with its result — passed, partial, failed — and cancellation; hydrate actual configuration before timing" (line 424) |
| DP06 structural relationship | L2 | "Actor/relation/target, all relevant domains, constituent facts/signals, signed support/opposition, condition/occurrence ledgers, variants and ancestry" (line 425) |
| DP07 (as consumer) | L0/L1 primitives | line 426 |

The measured upstream assets per L3 asset, by layer, are in §3.4 (52 cross-layer edges). The T1 §3 / L1 rule binds here: "Downstream consumers refer to L1 facts; they do not recompute them" (T1 line 501; CLAUDE.md §N.5 is not a tier and is not cited as one).

### 2.4 · Jyotish coverage owned

```
inherits:    Product §3 (substance), Data plane §5 (domain obligations)
measured_by: per obligation the five states — NOT MEASURED for any obligation: CEN has no coverage-state criterion; `Complete.width` = NOT_GENERIC on 21 of 21 ("no declared universe for this asset — declaring one is the first width gap")
traces_to:   0.1
```

**TIER GAP: TG-L3-013** (no per-layer enumeration of owned obligations) and **TIER GAP: TG-L3-014** (three tiers give three state vocabularies: T3 line 305 five states; T1 §5.1 lines 317-319 six states incl. "contradictory" and "still unexplored"; T2 line 341 "applied, … inapplicable, … unavailable/unqualified/unresolved").

The obligations the tier text itself names for the Kāla layer, with the state left honestly blank:

| source | obligation (quoted) | state |
|---|---|---|
| T1 §3.10 (lines 259-269) | "Daśā systems and nested periods, gochara, transit conditions with their aṣṭakavarga and vedha qualifications, annual and return methods, Tājaka, tithi-praveśa and Sudarśana"; boundaries, calendars, location and time-zone conventions, hierarchy and reference frames; "a background period, an enabling interval, a specific contact, an inhibiting condition, recurrence and inferred manifestation"; nearest versus better-supported "under a **named criterion**" | NOT MEASURED |
| T2 §5 line 335 | Present interval (P24): "The active clock set at `as_of`, each active clock's participants and what it is doing, and the immediately preceding interval retained for contrast. Activation is L3; expression of what it is doing is L4." | NOT MEASURED |
| T2 §5 line 336 | Kāla: "Daśā hierarchy, contact geometry, reference sign/house, transit conditions, applicable AV/vedha, annual/return conventions and precise coverage" — "Background period, enablement, trigger, inhibition and recurrence are distinct contributors to the same structural mechanism" | NOT MEASURED |
| T2 §5 line 327, 337, 338 | L3 named inside three other rows: "L3 participating roles" (graha roles); "Preserve existing services" (Praśna/Muhūrta/calendar); "L3 applicable intervals" (Ayurdaya) | NOT MEASURED |
| T2 §6.4 lines 375-382 | retain "the structural/configuration IDs and actual activated participants"; "Do not make shared graph nodes necessary timing gates without a qualified rule"; rank closest and better-supported later windows separately "using declared criteria and shared-dependence accounting"; return "the search horizon, covered methods, temporal precision and missing inputs with no-window results" | NOT MEASURED |

Asset names that match a T1 §3.10 instrument (reading of the *names* only, not verified in code): ka_dasha_kala, ka_avadhi (daśā); ka_gochara, ka_gochara_resonance, ka_vedha_gochara, ka_moorti_nirnaya (gochara/vedha); ka_tithi_pravesha, ka_sudarshana_varsha (annual/return, Sudarśana). No L3 asset name matches Tājaka (the registry has `ga_tajaka` in L1). The family names are recorded as found.

### 2.6 · Vocabulary conformance

```
inherits:    Data plane §4.1 (the controlled vocabulary — six rules with detectors)
measured_by: NOT MEASURED — CEN layer field `L3.local_map_candidates` = -1 (the independent-map detector did not run for this layer); no alias-set criterion in CEN
traces_to:   0.2 — the value is real only if the layer speaks the plane's one language
```

**TIER GAP: TG-L3-015** — T2 §4.1 (lines 268-271) lists the sixteen entity classes plane-wide; no tier assigns classes to layers, so which classes L3 emits or accepts is not stated. What CEN does measure: `Vocab.identity` PASS on all 17 table-backed assets (declared identity key with 0 duplicates), which is a different check from the §4.1 rules (identity of rows, not of names). No conformance finding is recorded either way.

### 2.7 · Source carriage and reproduction

```
inherits:    Product §11; Data plane §12.2 (Source carriage and reproduction), §4.3, §5
measured_by: CEN `Carr.detector` — NO_DETECTOR on 21 of 21 ("no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics")
traces_to:   0.1
```

**TIER GAP: TG-L3-016.** T3 §2.7 (line 358) assigns checks a/b/c "per obligation this layer owns"; §4.4 (line 478) and §5.2 (lines 545-556) ask for one carriage detector and the relevant Jyotish concepts **per asset**. Nothing in the tiers chooses among D1 (source correspondence), D2 (witness carriage) and D3 (independent re-derivation) for any L3 asset, and none is chosen here. All 21 read NO_DETECTOR, which T3 line 359 calls "a gap, never a pass". Ledger presence (`Ldgr.source_presence`, CEN) is measured on 8 assets only: PASS on 7 (source_citation or classical_citation populated on every row counted), PARTIAL on ka_gochara_resonance (`classical_citation` populated on 539 of 1,595 rows). That is presence of a citation column, not carriage.

### 2.5 · Edges and order

```
inherits:    Data plane §3.2; the registry DAG
measured_by: REG `depends_on` (21 active kala rows, 2026-09-30): topological levelling by longest path over intra-L3 edges; DFS cycle check over the 129-row active graph · cross-layer gates via egate.sql: NOT MEASURED (the script exists at platform/scripts/nirmana/egate.sql in the census checkout and is not run by the census) · CEN `Build.dag` (all resolvable) and `Build.dep_liveness`
traces_to:   0.3
```

**Order within L3 (longest path over the 31 intra-L3 edges; no cycle):**
- level 0: ka_avadhi, ka_dasha_kala, ka_gochara_resonance, ka_graha_sancara, ka_kota_chakra, ka_moorti_nirnaya, ka_muhurta_seva, ka_sudarshana_varsha, ka_tithi_pravesha, ka_vedha_gochara, ka_yojaka
- level 1: ka_gochara, ka_kshetra
- level 2: ka_sangam
- level 3: ka_kalasutra, ka_taranga, ka_vighnakara
- level 4: ka_kala_darshana
- level 5: ka_bhavishya_lekha, ka_jivana_parva, ka_tulana

The same levels appear as a column in §3.4. **Edge types:** TIER GAP: TG-L3-005. **Frozen definition revision:** TIER GAP: TG-L3-017 — T3 (lines 369, 374-375) requires gates "scoped to the CURRENT frozen definition revision"; no tier defines that revision and none exists for L3.
**Build-liveness of the edges (CEN `Build.dep_liveness`):** 9 PASS, 10 PARTIAL (a declared upstream is stale: an upstream "has moved since"), 1 FAIL (ka_taranga: `ka_avadhi (error)`), 1 N/A (ka_muhurta_seva has no declared dependencies). `Build.dag` PASS on 21 of 21 (every edge resolves).

---

## Part 3 · THE DELTA

```
inherits:    —
measured_by: 1.5's shortfall, itemised — 1.5 is not computed, so the delta is itemised below as measured gate cells only, never as a number of the elevation gap
traces_to:   0.2
```

### 3.1 · Per obligation

The layer is scored on one obligation, **Temporal integrity** (T1 §11 line 503). **NOT MEASURED, and no measurement exists to cite** — TIER GAP: TG-L3-019: T2 §12.2's "Temporal boundary" row (line 622) is a planned test shape (T2 line 629: "All tests listed here are planned"), and none of the 19 census criteria concerns boundaries, zones, hierarchy, horizons, nearest-versus-better-supported separation or absence-versus-unavailable semantics. The nine certified gates measure something else (buildability, idempotency, carriage, density, …). The measured cells are therefore given in 3.3 as gate cells, not as a score on this obligation. T3's "ten, not eleven" note (line 392) is respected: Domain correctness is not scored here.

### 3.2 · Per asset — disposition

**Not written.** TIER GAP: TG-L3-020 — no tier maps evidence to one of the eight dispositions, and the dispositions are the A.L3 dispositions file (out of this pass). The family assets are not dispositioned by Track A (charter R8/P11). The only tier text about L3 assets at family grain is T2 §6.4 (line 373): "`ka_kshetra` should contribute its useful search/temporal-integration engineering as a mechanism-qualified candidate substrate, not become a universal authority that all questions accept without reconstructing its inputs", and T2 §10.1 (lines 531-544) for the eight-letter hierarchy and "smallest sufficient change".

### 3.3 · Per asset — what it must add

**Only the measured part.** The "must add" list is every FAIL or PARTIAL gate cell plus inherited must-adds (T3 lines 408-411); the inherited part needs 3.2, which is not written (TG-L3-020, TG-L3-021). The measured part (CEN, 2026-09-30):

| asset | FAIL cells | PARTIAL cells |
|---|---|---|
| ka_avadhi | Build.completion, Dens.served, Build.history | Build.dep_liveness |
| ka_bhavishya_lekha | Build.completion, Count.floor, Dens.served | Complete.depth, Build.history, Build.dep_liveness |
| ka_dasha_kala | Dens.served | Idem.pattern, Build.count_integrity, Build.history |
| ka_gochara | Build.completion, Count.floor, Dens.served | Idem.pattern, Complete.depth, Build.history |
| ka_gochara_resonance | — | Complete.depth, Build.history, Ldgr.source_presence |
| ka_graha_sancara | Dens.served | Idem.pattern, Build.count_integrity |
| ka_jivana_parva | Dens.served | Build.history, Build.dep_liveness |
| ka_kala_darshana | Build.completion, Count.floor, Dens.served | Build.history, Build.dep_liveness |
| ka_kalasutra | Build.completion, Count.floor, Dens.served | Build.history, Build.dep_liveness |
| ka_kota_chakra | Count.floor, Dens.served | Build.history |
| ka_kshetra | Idem.pattern, Build.completion, Count.floor, Build.history | Complete.depth, Build.dep_liveness |
| ka_moorti_nirnaya | Build.completion, Dens.served | Build.history |
| ka_muhurta_seva | Dens.served | Idem.pattern, Build.count_integrity |
| ka_sangam | Build.completion, Count.floor, Dens.served | Build.history, Build.dep_liveness |
| ka_sudarshana_varsha | Dens.served | Build.history |
| ka_taranga | Dens.served, Build.dep_liveness | Build.history |
| ka_tithi_pravesha | Dens.served | Build.history |
| ka_tulana | Dens.served | Idem.pattern, Build.count_integrity, Build.history, Build.dep_liveness |
| ka_vedha_gochara | Build.completion, Count.floor, Dens.served | Complete.depth, Build.history |
| ka_vighnakara | Build.completion, Count.floor, Dens.served | Build.history, Build.dep_liveness |
| ka_yojaka | Dens.served | Build.history, Build.dep_liveness |

Common to all 21 (not repeated per row): `Earn.build_record` and `Cost.baseline` NO_DETECTOR ("instrument absent (migration 1094)"), `Carr.detector` NO_DETECTOR, `Reach.fields` and `Complete.width` NOT_GENERIC ("reported, not graded"). Cell tallies over the layer:

| criterion | assets with the cell | PASS | FAIL | PARTIAL | NO_DETECTOR | NOT_GENERIC | N/A |
|---|---|---|---|---|---|---|---|
| Build.registered | 21 | 21 | 0 | 0 | 0 | 0 | 0 |
| Build.contract | 21 | 21 | 0 | 0 | 0 | 0 | 0 |
| Idem.pattern | 21 | 15 | 1 | 5 | 0 | 0 | 0 |
| Build.target | 21 | 17 | 0 | 0 | 0 | 0 | 4 |
| Build.dag | 21 | 21 | 0 | 0 | 0 | 0 | 0 |
| Build.count_integrity | 21 | 17 | 0 | 4 | 0 | 0 | 0 |
| Build.completion | 21 | 7 | 10 | 0 | 0 | 0 | 4 |
| Earn.build_record | 21 | 0 | 0 | 0 | 21 | 0 | 0 |
| Cost.baseline | 21 | 0 | 0 | 0 | 21 | 0 | 0 |
| Count.floor | 19 | 8 | 9 | 0 | 0 | 0 | 2 |
| Complete.depth | 17 | 12 | 0 | 5 | 0 | 0 | 0 |
| Vocab.identity | 17 | 17 | 0 | 0 | 0 | 0 | 0 |
| Reach.fields | 21 | 0 | 0 | 0 | 0 | 21 | 0 |
| Dens.served | 21 | 0 | 19 | 0 | 0 | 0 | 2 |
| Build.exercised | 21 | 21 | 0 | 0 | 0 | 0 | 0 |
| Build.history | 21 | 2 | 2 | 17 | 0 | 0 | 0 |
| Build.dep_liveness | 21 | 9 | 1 | 10 | 0 | 0 | 1 |
| Complete.width | 21 | 0 | 0 | 0 | 0 | 21 | 0 |
| Carr.detector | 21 | 0 | 0 | 0 | 21 | 0 | 0 |
| Ldgr.source_presence | 8 | 7 | 0 | 1 | 0 | 0 | 0 |

### 3.4 · Intra-layer interplay

```
inherits:    —
measured_by: REG `depends_on` for the 21 active kala rows and the readers of each (2026-09-30); level = longest path over intra-L3 edges. Fields and declared use: NOT MEASURED (TG-L3-011, TG-L3-012)
traces_to:   3.x (this is where the synergistic term is built or found missing)
```

`direct / transitive` = CEN `blocking_radius` (active assets depending on it, directly / transitively, every layer).

| asset | level | reads (L3) | reads (L0/L1/L2) | read by (L3) | read by (L4) | read by (L5) | direct / transitive |
|---|---|---|---|---|---|---|---|
| ka_avadhi | 0 | — | ga_dashas, bo_pratijna, bg_ghatana | ka_taranga | — | — | 1 / 1 |
| ka_bhavishya_lekha | 5 | ka_kala_darshana, ka_vighnakara, ka_sangam | bo_laksana | — | ph_nimitta | — | 1 / 18 |
| ka_dasha_kala | 0 | — | ga_dashas | ka_jivana_parva, ka_kshetra, ka_sangam | — | — | 3 / 29 |
| ka_gochara | 1 | ka_gochara_resonance, ka_vedha_gochara, ka_moorti_nirnaya | bg_ephemeris, bg_transit_rules, ga_positions, ga_dashas, ga_yoga | ka_sangam | ph_muhurta | — | 2 / 26 |
| ka_gochara_resonance | 0 | — | bg_transit_rules | ka_gochara, ka_kshetra | — | — | 2 / 30 |
| ka_graha_sancara | 0 | — | bg_ephemeris | — | — | — | 0 / 0 |
| ka_jivana_parva | 5 | ka_kala_darshana, ka_dasha_kala, ka_sangam, ka_yojaka | ga_dashas | — | — | — | 0 / 0 |
| ka_kala_darshana | 4 | ka_sangam, ka_vighnakara, ka_kalasutra | — | ka_bhavishya_lekha, ka_jivana_parva, ka_tulana | — | — | 3 / 21 |
| ka_kalasutra | 3 | ka_yojaka, ka_sangam | bo_laksana | ka_kala_darshana | ph_muhurta | — | 2 / 22 |
| ka_kota_chakra | 0 | — | ga_positions, bg_ephemeris, bg_kota_chakra_rings | — | — | — | 0 / 0 |
| ka_kshetra | 1 | ka_dasha_kala, ka_gochara_resonance, ka_vedha_gochara | ga_panchanga, bo_pratijna, bo_sangati, bo_upaya, bg_cohort, bg_class_lifetime_counts | — | — | mi_bhara, mi_sankalpa | 2 / 2 |
| ka_moorti_nirnaya | 0 | — | ga_positions, bg_ephemeris, bg_transit_rules | ka_gochara | — | — | 1 / 27 |
| ka_muhurta_seva | 0 | — | — | ka_sangam, ka_vighnakara | — | — | 2 / 26 |
| ka_sangam | 2 | ka_yojaka, ka_dasha_kala, ka_gochara, ka_muhurta_seva, ka_vedha_gochara | bo_laksana, ga_dashas, ga_strength, ga_positions, ga_tajaka, bg_transit_rules | ka_bhavishya_lekha, ka_jivana_parva, ka_kala_darshana, ka_kalasutra, ka_taranga, ka_tulana, ka_vighnakara | ph_muhurta, ph_nimitta, ph_pratikara | mi_adhilepa | 11 / 25 |
| ka_sudarshana_varsha | 0 | — | ga_positions | — | — | — | 0 / 0 |
| ka_taranga | 3 | ka_avadhi, ka_sangam | bo_pratijna, ga_dashas, bg_ghatana | — | — | — | 0 / 0 |
| ka_tithi_pravesha | 0 | — | ga_positions | — | — | — | 0 / 0 |
| ka_tulana | 5 | ka_sangam, ka_vighnakara, ka_kala_darshana | — | — | — | — | 0 / 0 |
| ka_vedha_gochara | 0 | — | ga_positions, bg_ephemeris, bg_transit_rules, bg_sarvatobhadra_grid, bg_vedha_malefic_scale, bg_phaladeepika_latta | ka_gochara, ka_kshetra, ka_sangam | — | — | 3 / 30 |
| ka_vighnakara | 3 | ka_sangam, ka_muhurta_seva, ka_yojaka | ga_positions, bg_dignity_reference | ka_bhavishya_lekha, ka_kala_darshana, ka_tulana | ph_muhurta, ph_pratikara | — | 5 / 22 |
| ka_yojaka | 0 | — | bo_laksana, bg_transit_rules, ga_dashas, bo_bimba, bo_sangati, bo_pratijna, bg_ghatana | ka_jivana_parva, ka_kalasutra, ka_sangam, ka_vighnakara | — | — | 4 / 26 |

The matrix lists which asset reads which, not on which fields or for what use; the template's "input/output/use matrix" is unfilled for the last two (TIER GAPs above). Boundary with adjacent layers: upward reads from L3 into L4 exist in code but not in the registry (Appendix A, `ka_kshetra` → `phala_rectification`).

---

## Part 4 · STRATEGY

### 4.1 · Order

```
inherits:    2.5
measured_by: the DAG (§2.5); three-way baseline: deployed = CEN rows and states, current code = NOT MEASURED (R87; one fact in 1.1), target = the asset briefs (not this pass)
traces_to:   0.2
```

Order: upstream before downstream, by the levels in §2.5, with the cross-layer upstreams (L0 `bg_*` 10 assets, L1 `ga_*` 6, L2 `bo_*` 5 — REG) ahead of level 0. "Within a depth level … chosen for learning value" (T3 lines 431-433) is a strategy choice this draft does not make. **Deployed** (CEN): the row and gate state of §1.1; the build records show 2026-09-07/10/11 attempts for family assets and 2026-08-13 attempts for the six zero-row assets. **Current code:** NOT MEASURED except the ka_kshetra fact in §1.1. **Target:** not written.

### 4.2 · Work packets

```
inherits:    Data plane §13.1, §13.3 item 8
measured_by: each packet's proof — none defined
traces_to:   3.x — every packet closes a named delta item
```

The one packet the tiers supply for L3 is **W05** (T2 §13.1 line 641): "Reconcile the Kāla layer's existing temporal plan and its recorded gap assertions against accepted upstream outputs, re-validating each assertion against its actual producer; one structure–time route with proper clocks, counterconditions and alternative windows." Dependency: "Real producer dependency pins; broader campaign layer gates remain binding." **TIER GAP: TG-L3-026** — the "existing temporal plan" is named by description only. T2 §14 (lines 690-693) adds that earlier Kāla cross-layer contracts and view groupings are "reusable kernels and hypotheses … revalidate each against its actual producer before reusing an old gap assertion." No further packet is written: a packet that closes no named delta item is struck (T3 line 446), and the delta is not itemised as a gap (1.5).

### 4.3 · Generation, invalidation, rollback

```
inherits:    Data plane §11, §4.4, DP16
measured_by: the generation pins each consumer records; the invalidation path exercised, not described — NOT MEASURED (no consumer-side pin read exists)
traces_to:   2.1 — a rebuild that resets chronology is a hindsight leak
```

Measured facts only. (i) Generation labels are in use in `kala_gochara_windows` ('3.0', 'v1') and are pinned inside a registry `count_sql` ('4.0') that matches neither (§1.1; family asset, recorded). (ii) Eight foreign keys with `ON DELETE CASCADE` into `bodha_msr_signals` from seven tables, five in L3 (§1.1), mean a rebuild of the L2 signal table can remove L3 rows by deletion rather than by staleness marking; **TIER GAP: TG-L3-027** — no tier speaks to deletion coupling, only to "dependency-specific stale marking" (DP16, T2 line 436). (iii) `ka_kshetra`'s rebuild of a populated chart is refused by design (CEN Idem.pattern FAIL, `KshetraReplacementHeld` at `services/ka_kshetra/writer.py:545`); recorded, not judged.

### 4.4 · What each asset brief inherits

```
inherits:    Product §16 (what every brief states); Data plane §13.3 (asset brief sentence)
measured_by: derivability — can a brief author fill each row from this instance alone? (answered below; the test is a fresh-context reader's, T3 §5.4 test 1, and has NOT been run)
traces_to:   0.1
```

| # | row (T3 lines 466-478) | derivable from this instance? |
|---|---|---|
| 1 | P-needs / V-journeys served | PARTIAL — P24/V13 tier-anchored, others wording candidates (0.1; TG-L3-001) |
| 2 | the obligations it is scored on | YES — Temporal integrity (0.2) |
| 3 | correctness rules and switch behaviour | PARTIAL — rule and layer-grain switch quoted (2.1); per-asset behaviour and detectors TG-L3-007, TG-L3-008 |
| 4 | presentation fields | PARTIAL — temporal row only (2.2; TG-L3-009, TG-L3-018) |
| 5 | contracts produced and consumed, with declared use | PARTIAL — contract text quoted; asset assignment, fields, grain, declared use open (2.3; TG-L3-003, 011, 012) |
| 6 | coverage obligations and their current states | PARTIAL — obligation text quoted; states NOT MEASURED (2.4; TG-L3-013, 014) |
| 7 | position in the order and three-way baseline | PARTIAL — level and edges measured (2.5, 3.4); current-code half NOT MEASURED |
| 8 | disposition and "must add" list | NO — TG-L3-020; measured must-add cells only (3.3) |
| 9 | individual contribution | NOT MEASURED (1.2) |
| 10 | synergistic contribution | NOT MEASURED (1.3; TG-L3-006) |
| 11 | cross-layer contribution | PARTIAL — declared readers measured (1.4, Appendix A); consumer verification NOT MEASURED |
| 12 | preserved kernel | NO — TG-L3-021 |
| 13 | Jyotish concepts and the carriage check | NO — TG-L3-016 |

---

## Part 5 · EVALUATION AND CERTIFICATION

### 5.1 · The score is ablation, in three flavours

```
inherits:    Product §14, §14.1; Data plane §12.2
measured_by: ablation deltas — NONE measured (no harness for any flavour)
traces_to:   0.2
```

L3 is `scoring: contribution` (CEN `L3.scoring`), not a reference layer, so the individual flavour applies (and the reference-layer carve-out of T3 lines 192-196 does not). Individual, synergistic and cross-layer flavours: NOT MEASURED (§1.2–§1.4). The one obligation L3 is scored on is Temporal integrity (T1 §11).

### 5.2 · What is certified, and what is merely checked

```
inherits:    Product §14; CLAUDE.md §N.6-N.8; the t3 lesson
measured_by: CEN gate cells for the nine gates; no certification record is written by this document (status: may not certify)
traces_to:   4.4 — the gates are what an asset brief is certified against
```

**The gate map (T3 lines 567-585; the left two columns are fixed by the template).** The right-hand column is what this instance supplies; a hole is reported, not filled (TIER GAP: TG-L3-025; T3 lines 584-585 send holes to "§7", which the template does not contain).

| gate | section a brief author reads | what this instance supplies (measured, layer grain) | per-asset content the instance cannot supply |
|---|---|---|---|
| **Ldgr** | 2.3 | `Ldgr.source_presence` exists on 8 assets (7 PASS, 1 PARTIAL); consumed-input use undeclared (TG-L3-012) | the upstream `fact_id` sources per asset |
| **Idem** | 2.5; 4.1 | `Idem.pattern`: 15 PASS, 5 PARTIAL (4 services + ka_gochara), 1 FAIL (ka_kshetra: refused rebuild); natural key from CEN `Vocab.identity` for 17 assets (8 declare only a surrogate: id ×7, convergence_id ×1) and from REG `natural_key_partition` for 4 (which disagrees with CEN for ka_sangam, ka_bhavishya_lekha, ka_kala_darshana) | one agreed natural key per table-backed asset; the service convention (TG-L3-022) |
| **Earn** | 2.4 | `Earn.build_record` NO_DETECTOR on 21 ("instrument absent (migration 1094)") | which emitted states are claims, and what would falsify each |
| **Null** | 2.4; 1.4 | no census criterion for Null | the asset's null convention |
| **Vocab** | 2.6 | `Vocab.identity` PASS 17 (row identity); §4.1 class conformance NOT MEASURED (TG-L3-015) | the classes and authority per asset |
| **Carr** | 2.7; 4.4 row 13 | `Carr.detector` NO_DETECTOR on 21 | concept and menu item per asset (TG-L3-016) |
| **Narr** | 2.2 | no census criterion for Narr | whether the asset emits prose |
| **Dens** | 2.2; 3.4 | `Dens.served`: 19 FAIL (serving modules found, `density_contract` declared by none), 2 N/A (ka_gochara_resonance, ka_kshetra: `Dens.served` counts 0 modules) | which surface each asset reaches (partly in §1.2) |
| **Build** | 2.5; 1.1; 4.3 | the six static checks and the runtime state, layer tallies in §3.3: registered 21 P, contract 21 P, target 17 P/4 N/A, dag 21 P, count_integrity 17 P/4 p, completion 7 P/10 F/4 N/A; plus exercised 21 P, history 2 P/17 p/2 F, dep_liveness 9 P/10 p/1 F/1 N/A | — (the asset's writer, target, edges and record are in §1.1, §2.5 and the runs table) |

**The full verdict matrix** (CEN, all criteria emitted for L3; letters as above, **n** NO_DETECTOR, **g** NOT_GENERIC):

| asset | Build.registered | Build.contract | Idem.pattern | Build.target | Build.dag | Build.count_integrity | Build.completion | Earn.build_record | Cost.baseline | Count.floor | Complete.depth | Vocab.identity | Reach.fields | Dens.served | Build.exercised | Build.history | Build.dep_liveness | Complete.width | Carr.detector | Ldgr.source_presence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ka_avadhi | P | P | P | P | P | P | F | n | n | P | P | P | g | F | P | F | p | g | n | · |
| ka_bhavishya_lekha | P | P | P | P | P | P | F | n | n | F | p | P | g | F | P | p | p | g | n | P |
| ka_dasha_kala | P | P | p | - | P | p | - | n | n | - | · | · | g | F | P | p | P | g | n | · |
| ka_gochara | P | P | p | P | P | P | F | n | n | F | p | P | g | F | P | p | P | g | n | · |
| ka_gochara_resonance | P | P | P | P | P | P | P | n | n | P | p | P | g | - | P | p | P | g | n | p |
| ka_graha_sancara | P | P | p | - | P | p | - | n | n | · | · | · | g | F | P | P | P | g | n | · |
| ka_jivana_parva | P | P | P | P | P | P | P | n | n | P | P | P | g | F | P | p | p | g | n | P |
| ka_kala_darshana | P | P | P | P | P | P | F | n | n | F | P | P | g | F | P | p | p | g | n | P |
| ka_kalasutra | P | P | P | P | P | P | F | n | n | F | P | P | g | F | P | p | p | g | n | P |
| ka_kota_chakra | P | P | P | P | P | P | P | n | n | F | P | P | g | F | P | p | P | g | n | · |
| ka_kshetra | P | P | F | P | P | P | F | n | n | F | p | P | g | - | P | F | p | g | n | · |
| ka_moorti_nirnaya | P | P | P | P | P | P | F | n | n | P | P | P | g | F | P | p | P | g | n | · |
| ka_muhurta_seva | P | P | p | - | P | p | - | n | n | · | · | · | g | F | P | P | - | g | n | · |
| ka_sangam | P | P | P | P | P | P | F | n | n | F | P | P | g | F | P | p | p | g | n | P |
| ka_sudarshana_varsha | P | P | P | P | P | P | P | n | n | P | P | P | g | F | P | p | P | g | n | · |
| ka_taranga | P | P | P | P | P | P | P | n | n | P | P | P | g | F | P | p | F | g | n | · |
| ka_tithi_pravesha | P | P | P | P | P | P | P | n | n | P | P | P | g | F | P | p | P | g | n | · |
| ka_tulana | P | P | p | - | P | p | - | n | n | - | · | · | g | F | P | p | p | g | n | · |
| ka_vedha_gochara | P | P | P | P | P | P | F | n | n | F | p | P | g | F | P | p | P | g | n | P |
| ka_vighnakara | P | P | P | P | P | P | F | n | n | F | P | P | g | F | P | p | p | g | n | P |
| ka_yojaka | P | P | P | P | P | P | P | n | n | P | P | P | g | F | P | p | p | g | n | · |

### 5.3 · Certification is per criterion, not per definition revision

No certification record is written by this document. The status line ("may register gaps, may not certify") applies; certification is the later A.Lxr census (gate-reviewed) and the Scribe's ledger.

### 5.4 · Acceptance of the instance itself

Not run. (1) The derivability test (a fresh-context reader deriving one brief) has not been performed; §4.4 is this draft's own reading. (2) Alignment: run on the draft (0.4). (3) Measured-not-inherited: every figure names its source tag; the SEED parse and the GRP populations are ad-hoc reads, not census outputs, and are labelled as such. (4) Presentation parity: NOT MEASURED (TG-L3-010). (5) The gate map exists (5.2) with its holes reported. (6) Independent review: none has been done. **Verdict: none.** Per T3 (lines 634-636) an instance with no review behind it is unreviewed whatever it says, and nothing may inherit from it.

---

## Appendix A · The family set and its readers (input to `FAMILY_ASSETS.json`, Track E lane E6.3)

```
measured_by: REG (asset_registry, 129 rows, 2026-09-30; direct readers by `depends_on`, transitive closure over active assets) · CEN (`blocking_radius`, `Build.*`) · GRP (services/ka_kshetra populations named in each line)
```

**Recorded, never decided.** These assets belong to the Pravāha campaign and the family sessions (TRACK_A_BRIEF §6; charter R8, P11). Nothing below proposes a change to any of them.

### A.1 · The family set as found

| asset | registry state | target table(s) | role in the set |
|---|---|---|---|
| `ka_gochara` | active, CURRENT, per_chart, has_substeps | kala_gochara_windows (writer replaces `_v2`) | family (Gochara) |
| `ka_gochara_resonance` | active, CURRENT | gochara_resonance_map | family (Gochara) |
| `ka_vedha_gochara` | active, CURRENT | kala_vedha_gochara | family (Gochara) |
| `ka_sangam` | active, CURRENT, has_substeps | kala_convergence | family (Saṅgam) |
| `ka_kshetra` | active, CURRENT, has_substeps | kala_field + 14 further tables (§1.1) | family (Kṣetra) |
| `ka_yojaka` | active, CURRENT | kala_activation_predicates | **claimed prerequisite, flagged, not adjudicated**: ka_sangam declares it (REG) and `SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` §2.3 item 6 states Saṅgam's rebuild needs it rebuilt first; TRACK_A_BRIEF §6: if a family brief claims it, it moves from the 16 briefs to evaluation |
| `ka_gochara_sweep` | inactive, RETIRED | kala_gochara_windows | registered, excluded from the 21 |
| `ka_gochara_v3_century_materialize` | inactive, CURRENT | kala_gochara_windows_v2 | registered writer, absent from the active population (the 22-vs-21 anomaly) |

Other L3 assets that the family assets declare as prerequisites (REG `depends_on`): ka_gochara ← ka_moorti_nirnaya; ka_sangam ← ka_dasha_kala, ka_muhurta_seva; ka_kshetra ← ka_dasha_kala. Not claimed as family; listed because a level map moves with them.

### A.2 · Readers of the family assets (REG `depends_on`, active assets)

| family asset | direct readers | transitive readers (count; by layer) |
|---|---|---|
| ka_gochara | ka_sangam (L3), ph_muhurta (L4) | 26: L3 8, L4 9, L5 9 |
| ka_gochara_resonance | ka_gochara, ka_kshetra (L3) | 30: L3 10, L4 9, L5 11 |
| ka_vedha_gochara | ka_gochara, ka_kshetra, ka_sangam (L3) | 30: L3 10, L4 9, L5 11 |
| ka_sangam | ka_bhavishya_lekha, ka_jivana_parva, ka_kala_darshana, ka_kalasutra, ka_taranga, ka_tulana, ka_vighnakara (L3); ph_muhurta, ph_nimitta, ph_pratikara (L4); mi_adhilepa (L5) | 25: L3 7, L4 9, L5 9 |
| ka_kshetra | mi_bhara, mi_sankalpa (L5) | 2: L5 2 |
| ka_yojaka (flagged) | ka_jivana_parva, ka_kalasutra, ka_sangam, ka_vighnakara (L3) | 26: L3 8, L4 9, L5 9 |

The transitive counts agree with CEN `blocking_radius.transitive` for each of the six (26, 30, 30, 25, 2, 26) and the direct counts with `blocking_radius.direct` (2, 2, 3, 11, 2, 4).

**Readers outside the family set, direct, all layers (13):** L3 ka_bhavishya_lekha, ka_jivana_parva, ka_kala_darshana, ka_kalasutra, ka_taranga, ka_tulana, ka_vighnakara; L4 ph_muhurta, ph_nimitta, ph_pratikara; L5 mi_adhilepa, mi_bhara, mi_sankalpa. With the three family assets that themselves read family assets (ka_gochara, ka_sangam, ka_kshetra) this is the 16 readers `SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` §7 lists; the registry-derived set matches it. Union of transitive readers of the five family assets (without ka_yojaka): 30 active assets (L3 10, L4 9, L5 11): ka_bhavishya_lekha, ka_gochara, ka_jivana_parva, ka_kala_darshana, ka_kalasutra, ka_kshetra, ka_sangam, ka_taranga, ka_tulana, ka_vighnakara; mi_abhilekha, mi_adhilepa, mi_bhara, mi_bhavisya, mi_darshana, mi_gunanaka, mi_pariksha, mi_pramana, mi_sambandha, mi_sankalpa, mi_seva; ph_muhurta, ph_nimitta, ph_phaladesa, ph_pramana, ph_pratikara, ph_rectification, ph_sankrama, ph_sodhana, ph_suddha_sodhana.
Readers that read the family through code but not through `depends_on` are not in this list (the registry graph is what was asked for); CEN `reach.modules` names the serving modules (§1.2).

```json
{
  "source": "asset_registry depends_on, read 2026-09-30 as suvarna_reader; census 2a78ec64d; chart 482012f1",
  "family_as_found": ["ka_gochara", "ka_gochara_resonance", "ka_vedha_gochara", "ka_sangam", "ka_kshetra"],
  "claimed_prerequisite_flagged": ["ka_yojaka"],
  "registered_not_active": ["ka_gochara_sweep", "ka_gochara_v3_century_materialize"],
  "readers_direct_outside_family": {
    "L3": ["ka_bhavishya_lekha", "ka_jivana_parva", "ka_kala_darshana", "ka_kalasutra", "ka_taranga", "ka_tulana", "ka_vighnakara"],
    "L4": ["ph_muhurta", "ph_nimitta", "ph_pratikara"],
    "L5": ["mi_adhilepa", "mi_bhara", "mi_sankalpa"]
  },
  "family_assets_that_read_family_assets": ["ka_gochara", "ka_sangam", "ka_kshetra"]
}
```

### A.3 · `ka_kshetra`'s edges, declared against read

`measured_by`: declared = REG `depends_on` of ka_kshetra; read = GRP over `platform/python-sidecar/services/ka_kshetra/**/*.py`, tests excluded, at both 2a78ec64d and origin/main e2352f881 (FROM/JOIN table identifiers; the same set at both commits); table-to-asset mapping = REG `target_table`.

Declared (9): `ka_dasha_kala`, `ka_gochara_resonance`, `ga_panchanga`, `bo_pratijna`, `bo_sangati`, `bo_upaya`, `bg_cohort`, `bg_class_lifetime_counts`, `ka_vedha_gochara`.

| declared edge | read in code? |
|---|---|
| ka_gochara_resonance | yes — `gochara_resonance_map` |
| bo_pratijna | yes — `bodha_pratijna` |
| bg_cohort | yes — `bg_synthetic_cohort` (its target table) |
| bg_class_lifetime_counts | yes, through a shared table — `brahma_class_priors` is the target of both this asset and `bg_class_priors` (REG); the code comment names `bg_class_priors` |
| ga_panchanga | reads `chart_facts`, which is the target of seven `ga_*` assets (ga_ayurdaya, ga_nakshatra, ga_panchanga, ga_positions, ga_sade_sati, ga_sensitive, ga_sensitive_degree); the edge is consistent with the read but does not identify the asset |
| **bo_upaya** | **no** — target `bodha_rm_resonances`; no `bodha_rm_` identifier in the population |
| **bo_sangati** | **no** — target `bodha_cdlm_cells`; no `bodha_cdlm_` identifier in the population |
| **ka_dasha_kala** | **no** — the service is not referenced by name (only in comments); the code reads `chart_dashas` directly |
| **ka_vedha_gochara** | **no** — `kala_vedha_gochara` does not appear in the population at either commit (the edge is in live REG; SEED lacks it, §0.3) |

Read but not declared (table → owning asset by REG `target_table`): `kala_gochara_windows` → ka_gochara; `chart_dashas` → ga_dashas; `bodha_msr_signals` → bo_laksana; `bodha_cgm_edges` → bo_karanajala, `bodha_cgm_nodes` → bo_bimba; `phala_rectification` → ph_rectification (**an L4 asset: an upward read from L3**); `ephemeris_daily` → bg_ephemeris; `bg_transit_rules` → bg_transit_rules; `bg_kp_sublord_division` → bg_kp_sublord_division; `brahma_event_ontology` → bg_ghatana; and tables no registry asset lists as a `target_table` (`kala_gochara_authority`, `kala_field_weights`, `kala_field_weight_versions`, `ka_kshetra_tier_basis`, `bg_synthetic_cohort_md`, `public.charts`; REG `target_table` search). So the declared set holds **4 edges with no read (bo_upaya, bo_sangati, ka_dasha_kala, ka_vedha_gochara)** and the population reads **10 owning assets it does not declare** (ka_gochara, ga_dashas, bo_laksana, bo_karanajala, bo_bimba, ph_rectification, bg_ephemeris, bg_transit_rules, bg_kp_sublord_division, bg_ghatana). The undeclared reads reach into L2 (`bodha_msr_signals`, `bodha_cgm_*`) and L4 (`phala_rectification`). Live REG also shows `bo_pratijna` and `bo_upaya` stale at the canonical chart (CEN `Build.dep_liveness` 7/9 lit); an orchestrated build through the declared `bo_upaya` edge is the "phantom edge" exposure the focus document describes (`SUVARNA_L3_FOCUS_FAMILIES_v1_0.md` §3.3 item 3), cited as corroboration, not re-measured beyond the read-versus-declared comparison above.

---

## Appendix B · Findings that disagree with an earlier document (both sides cited)

| topic | earlier document says | this census / read says |
|---|---|---|
| Active L3 assets and registered writers | `nikasha_test/derivations/L3_INSTANCE_SKELETON.md` §1.1: 23 assets, `registered_ids` 11 vs `registry_has_writer` 23, `Build.registered` FAIL on 12 assets | CEN `L3.n_assets` 21; `registered_ids` 22 vs `registry_has_writer` 21; `Build.registered` PASS on 21 of 21 |
| Same, W0 register | `MADHAV_DATA_PLANE_L3_W0_FIELD_CONTRACT_REGISTER_v1_0.md` ("Census invariant"): "22/22 active identities represented" incl. ka_gochara_v3_century_materialize | REG: 21 active; the century writer `is_active = f` |
| `live_rows` | Skeleton §1.1(a) and R134: `live_rows` null on all 23 assets | CEN: `live_rows` present for 17 of 21 (the 4 services are null by design) |
| `kala_field` rows | Skeleton table: 549,797 (sandbox `Complete.depth`); TRACK_A_BRIEF §3: "`kala_field` ≈ 11 M rows" | CEN `live_rows` (chart-scoped count_sql) 8,570,075; CEN `Complete.depth` (table-wide, all charts) 10,982,957; registry floor 8,599,775 |
| ka_gochara windows | R240: 17,211 rows vs 1,001 in the canonical chart's tables | REG: `kala_gochara_windows` 914 ('3.0') + 16,297 ('v1') = 17,211; `_v2` 1,001 — the figures agree; the new finding is that ka_gochara's `count_sql` pins generation '4.0', so CEN reads 0 (§1.1) |
| Registry `natural_key_partition` | Not mentioned in T1-T4 or the register (0 hits) | populated on 67 of 129 registry rows, 4 of 21 active L3 assets; differs from CEN's declared key on 3 (TG-L3-025) |
| Switch row for L3 | R138: "L3's row absent from the tier summary" | T2 §9.2 line 500 names L3 in the ON row (TG-L3-007 keeps the per-asset part open) |
| Zero-row Kāla tables | R237: "six Kāla tables empty" | CEN: six active assets at live = 0 (ka_bhavishya_lekha, ka_gochara, ka_kala_darshana, ka_kalasutra, ka_sangam, ka_vighnakara); five are cascade-key tables, one is the generation pin |

## Appendix C · Register rows observed and not tier gaps

R134 and R135 (now supplied by CEN), R146/R87 (needs a code-head read), R157/R106 (consumer probe), R160/R122 (reader grep), R237 (data finding, see B), R240 (closed, see §1.1). These are instrument or data items; the tier clause that specifies each measure is adequate.

## Appendix D · Measurement sources and populations

- **CEN** — `/Users/Dev/suvarna-evidence/census/census_L3.json`, exit 2, inspector 2a78ec64d, `generated` 2026-09-30T20:25:37+05:30; 21 assets, 19 criteria (20 with `Ldgr.source_presence`), tallies re-derived from the JSON and equal to `SUMMARY.md` (FAIL 42, PARTIAL 42, NO_DETECTOR 63, PASS 195, N/A 13, NOT_GENERIC 42, ERRORED 0).
- **REG** — `psql -X` as `suvarna_reader` through the proxy, 2026-09-30: `select … from asset_registry` (129 rows; 23 `layer='kala'`); `select generation, count(*) from kala_gochara_windows where chart_id='482012f1-…' group by 1`; `select count(*) from kala_gochara_windows_v2 where chart_id='482012f1-…'`; `select conrelid::regclass, conname, confdeltype … from pg_constraint where confrelid='bodha_msr_signals'::regclass and contype='f'`; `select count(*) from information_schema.columns where table_name='asset_registry'` (42). Chart 482012f1 only; no session `SET`.
- **SEED** — `platform/scripts/seed/asset_registry_seed.ts` at 2a78ec64d, blocks delimited by line-anchored `asset_id:` entries, `depends_on: [...]` per block; 129 blocks, 23 `ka_*`, no duplicate ids.
- **GRP** — over `/Users/Dev/suvarna-census` at 2a78ec64d: `platform/python-sidecar/services/ka_kshetra/**/*.py` (tests excluded) for table identifiers and INSERT/DELETE/UPDATE targets; `platform/python-sidecar/**/*.py` (tests excluded) for `INSERT INTO kala_insights`; `find platform/python-sidecar -iname '*circularity*'`; tier files T1-T4 and the register for the keyword searches named in the gaps file. Where origin/main e2352f881 was also read (ka_kshetra tables), the result is stated.
