---
artifact: SUVARNA_L1_LAYER_INSTANCE
canonical_id: SUVARNA_L1_LAYER_INSTANCE
tier: 3
kind: instance
version: "1.0-rev1"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
verdict: "NONE. First draft by the analyst of lane A.L1i; no independent review has happened (template §5.4 test 6), so nothing may inherit from it as accepted."
produced_on: 2026-09-30
produced_in: "Exec Suvarṇa"
plan_item: "A.L1i step 2 (layer-instance draft)"
layer: "L1 Gaṇita — 19 active assets, ga_*"
template: "00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md (tier 3, FINAL / SEALED), read at /Users/Dev/suvarna-census, detached at 2a78ec64d"
parents:
  - "00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md (tier 1)"
  - "00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md (tier 2)"
census_run:
  output: /Users/Dev/suvarna-evidence/census/census_L1.json   # + census_L1.log, SUMMARY.md
  exit_code: 2            # FAIL cells present = MEASURED (arch §12.14)
  inspector_commit: 2a78ec64d88e59438bd6527b4c99826432102c57
  generated: "2026-09-30T20:22:28+05:30"
  chart_scope: 482012f1-710e-4a25-994a-93821f5871aa
  runtime_seconds: 66     # SUMMARY.md
census_rerun:             # gate-review corrections (rev1): the ga_prashna cells are read from this second run
  output: /Users/Dev/suvarna-evidence/census2/census_L1.json   # + census_L1.log beside it
  exit_code: "not recorded beside the file; the log reports FAIL 7 (FAIL cells present = MEASURED)"
  generated: "2026-09-30T20:30:02+05:30"
  differences_from_census1: "field-by-field script comparison: every difference is on ga_prashna (Build.completion ERRORED -> PARTIAL, its text, live_rows null -> 0, live_rows_basis) plus the generated stamp"
tier_gaps: "00_ARCHITECTURE/briefs/suvarna/layers/L1/L1_TIER_GAPS_v1_0.md (TG-L1-001 … 024; LG-L1-001/002; MF-L1-001 … 012)"
code_read_at: "origin/main e2352f881751deced2dc089451ef676db0aac5d5, platform/python-sidecar and platform/supabase/migrations"
db_reads: "suvarna_reader via proxy 127.0.0.1:5433, read-only, chart 482012f1 only, 2026-09-30 (cited by table and predicate where used)"
inputs_checked_not_trusted: ["nikasha_test/derivations/L1_INSTANCE_SKELETON.md", "nikasha_test/derivations/L1_INVENTIONS.md"]
changelog:
  - "1.0-rev1 (2026-09-30): gate review corrections applied (independent Opus review 2026-09-30): 6 defects. ga_prashna cells re-read from census2 (Build.completion PARTIAL, live_rows 0; ERRORED cleared; layer tally PARTIAL 28, ERRORED 0; sections 1.1, 3.1, 3.2, 4.2 P6, 5.2, Part 6); ga_prashna is no longer described as having no capability module (census reach lists one MCP reader; 1.2, 1.5); T3 §2.3 citation for 'a citation with no declared use is not a contract' corrected (was attributed to T2 §7.1); V12 serves P07 and P23; units gap recorded as TG-L1-024; Ldgr.source_presence forms corrected (citation_ref, classical_citation, source_citation)."
  - "1.0 (2026-09-30): first draft of the L1 instance from tiers 1–2, the template, the census run above, the live registry and code read at the stated head. Every clause the tiers do not supply is marked 'TIER GAP: TG-L1-nnn' and left unfilled. No figure is typed from memory: each is read from census_L1.json, a named query, or a named file:line."
---

# L1 Gaṇita — Layer Definition and Strategy (draft 1.0-rev1)

**Reading conventions.** Every section carries the template's three lines. A section or cell marked **TIER GAP:
TG-L1-nnn** is one the tiers do not supply; the reason and evidence are in `L1_TIER_GAPS_v1_0.md`, and nothing is
invented in its place. A figure marked "not measured" carries its reason. "Census" means `census_L1.json`, field path
`L1.assets[*].measurements["<criterion>"]`, except the `ga_prashna` cells, which are read from the rerun `census2/census_L1.json` (differences: frontmatter `census_rerun`); "registry" means `asset_registry` read on 2026-09-30; "the chart" means
`482012f1-710e-4a25-994a-93821f5871aa`. The verdict vocabulary is the closed set `PASS · FAIL · PARTIAL · NO_DETECTOR ·
N/A` plus `ERRORED` (plan §2.1). Nothing here certifies anything.

---

## Part 0 · VALUE — the origin

### 0.1 · What cannot be answered without this layer

```
inherits:    Product §2 (P01-P24), Data plane §2 (V01-V13)
measured_by: none for the tier text; the two counts below are measured over asset_registry.depends_on (all is_active assets, read 2026-09-30) and census blocking_radius
traces_to:   —  (this IS the origin)
```

**TIER GAP: TG-L1-001.** No tier maps a P-need or V-journey to a layer by necessity (searched T1 §2, §11; T2 §2, §3.1, §5,
§7.1), so the table this section asks for cannot be filled without inventing it. What the tiers *do* say explicitly about
L1 is listed below, and only that:

| P / V | the tier text that names L1 for it | the distinction that disappears without L1 (as the tier states it) |
|---|---|---|
| V12 / P07, P23 (lifespan and constitution) | T2 §2 V12 (line 128, which serves P07 and P23) and §5 "Ayurdaya and constitution" (line 338): "L0 method/source -> L1 ayurdaya computed under each applicable school -> L2 …" | āyurdāya computed under each applicable school, with its inputs, cancellations, inter-authority disagreement and uncertainty, not a bare figure |
| no P/V id stated | T2 §5 "Graha contextual roles" (line 327): "L0 meaning → L1 computed roles/placements → L2 mechanism …" | natural/functional role, lordship, kāraka, placement, condition and relations kept separate |
| no P/V id stated | T2 §12.1 (line 582), the financial-promise story: "L1 supplies actual positions, conditions, divisions, formation and clocks" | the computed positions, conditions, divisions, formation and clocks that the later layers construct on |
| no P/V id stated (switch ON only) | T2 §9.2 (line 500): "L1 separate event-time context"; T1 §8.1 (line 423) "Event-time astronomical calculation from supplied dates" | event-time calculation kept apart from natal truth |

Every other P and V row: L1's necessity for it is **not established here**. A build-graph measure, offered as information
and not as a necessity statement: 25 active non-L1 assets (L2 9 · L3 14 · L4 1 · L5 1) declare a direct `depends_on` edge to
at least one `ga_*` asset (46 edges); 13 of the 19 L1 assets have downstream dependents in census `blocking_radius`, and 6 have
0/0 (`ga_ayurdaya`, `ga_medical`, `ga_prashna`, `ga_sensitive_degree`, `ga_transit_anchors`, `ga_vastu`). Register R221/R85 re-scope this
section to a catalog-provenance and necessity-closure reading; the sealed template text is unchanged.

### 0.2 · The layer's objective

```
inherits:    Product §1 (the join), §11 (this layer's row), Data plane §3.1 (this layer's row)
measured_by: none — definitional
traces_to:   0.1
```

The distinctions L1 makes earnable, in the tiers' own words. Product §1 (lines 51–56): conventional software "computes each
element on demand and presents it — a varga when asked for it, a daśā table when asked for it"; Madhav computes "the whole
estate and … the relationships between its parts: every graha in every relevant condition, across every applicable varga,
relationship chain, clock and window, held together." Data plane §6.2 (lines 353–359): L1's deliverable "is a qualified fact
package, including what was not computed or is too sensitive to uncertain birth inputs"; dimensions are joined "by canonical
fact/configuration identity", a downstream consumer "must not select whichever row first matches a category or substitute
zero/neutral for missing computation."

- **The owned question** (T2 §3.1, line 140): "What is actually calculated for this subject and context?"
- **The contribution handed onward** (T2 §3.1): "Reproducible facts, configuration membership, conditions, divisions, clocks and uncertainty, with fact identities and conventions."
- **What it must not claim** (T2 §3.1): "A newly invented downstream value or interpretation disguised as computation."
- **The proof that matters** (T1 §11, line 501): "Computational correctness (§14): fact identity, values, units, precision, provenance. Downstream consumers refer to L1 facts; they do not recompute them."
- **Layer ownership is not epistemic type** (T2 §3.3, line 176): L1 includes judged structure (`ga_vichara`), specialized rule applications and temporal products; "Being in L1 does not make every field an equally verified numerical fact." Typing each output is TIER GAP: TG-L1-020.
- **"What it computes that existing software does not":** TIER GAP: TG-L1-002 for any L1-specific claim beyond the product-level quotation above; no baseline or instrument exists in the tiers and T1 §13 forbids an invented claim.

### 0.3 · Its place in the wheel

```
inherits:    Data plane §3.2 (five edge types), §7 (DP contracts)
measured_by: live asset_registry.depends_on (all 19 ga_* rows and every active asset whose depends_on names a ga_* asset, read 2026-09-30); writer-class depends_on in platform/python-sidecar/pipeline/orchestrator/writers/ga_*.py (origin/main e2352f88); seed and migration pin NOT measured (TG-L1-003)
traces_to:   0.2
```

**The three sources, stated separately (T3 §0.3).**
- *Live registry:* 45 edges among the 19 assets: 40 inside L1 and 5 to L0 (`ga_nakshatra` → `bg_nakshatra`, `bg_kp_sublord_division`; `ga_panchanga` → `bg_panchanga`; `ga_prashna` → `bg_prashna_rules`; `ga_sensitive` → `bg_reference`). Census `Build.dag` reads PASS for 19 of 19 (every edge resolves).
- *Writer code:* declared in 2 of 19 classes only. `ga_vichara.py:46` `['ga_structural','ga_strength','ga_dashas','ga_yoga']` agrees with the registry; `ga_structural.py:21` `['ga_nakshatra']` differs from the registry's seven edges (the file's comment at line 19 defers to the registry).
- *Seed and migration pin:* **TIER GAP: TG-L1-003 — not measured.** One migration-history fact is visible: 416 added `ga_structural → ga_condition` and 419 removed it; the live registry has no such edge, so that pair is consistent.

**Receives from** (T2 §7.1): DP01 identity/release and DP02 rule qualification, both L0 → writers (edge types: definition and computational). The five live L0 edges above are the declared receipts. Code reads more: MF-L1-006 finds `ga_condition` (`bg_dignity_reference`, `ga_condition_writer.py:615`), `ga_medical` (`bg_medical_mappings`, `ga_medical_writer.py:172`), `ga_yoga` (`brahma_yoga_catalog`, `ga_yoga_writer.py:166`) and `ga_sensitive_degree` (`reference_nakshatra`, `ga_sensitive_degree_writer.py:415`) querying L0 tables their `depends_on` does not declare; the declared-versus-actual comparison for the rest was not made.

**Hands onward to** (T2 §7.1): DP03 chart facts (→ L2–L4/services); DP04 condition decomposition (→ L2/L3/L4); a share of DP05 configuration (L0+L1 → L2 → L3) and of DP07 precise clocks (L0/L1/L3 primitives); DP14 takes L1 context into comparison. In the live registry, 25 non-L1 assets (L2 9, L3 14, L4 1, L5 1) declare 46 direct edges to L1 (census `blocking_radius` and the column "direct dependents outside L1" in §1.1). L1 assets as sources: `ga_positions` 16 edges (L2 6, L3 8, L4 1, L5 1); `ga_dashas` 8 (L2 1, L3 7); `ga_structural` 4 (L2 4); `ga_panchanga` 3; `ga_condition`, `ga_nakshatra`, `ga_sensitive`, `ga_strength`, `ga_vargas`, `ga_yoga` 2 each; `ga_sade_sati`, `ga_tajaka`, `ga_vichara` 1 each; the other six none.

**What the join needs from it** (T2 §7.1 DP03 field list): `fact_id`, grain/value/unit, chart/build, ayanāṃśa/frame/varga, input precision and verification, with no downstream re-derivation. The field-level check that a consumer actually reads those fields is not measured (TG-L1-009).

### 0.4 · The alignment test

```
inherits:    Template §0.4
measured_by: author's own pass over this draft
traces_to:   0.1–0.3
```

Author's run: every section from Part 1 names its `traces_to`. Nothing was struck. Two sections (1.2, 1.3) record an **absent
instrument** rather than a term, and are kept because the template's accounting (1.5) requires them and T1 §1.3 / T2 §3.5 say an
absent instrument is recorded, never a number. The reviewer runs the test again (template §5.4 test 2); that has not happened.

---

## Part 1 · VALUE DECOMPOSITION

### 1.1 · Inventory, measured

```
inherits:    Data plane §13.3 item 2
measured_by: census_L1.json (asset population: the 19 active rows of asset_registry for layer ganita, population_registry_total 19, none excluded, registered_ids 19, registry_has_writer 19, phantom_registered [], never_exercised_with_writer []); asset_registry columns read 2026-09-30; asset_throughput for chart 482012f1 read 2026-09-30; live_rows = the asset's own count_sql at chart 482012f1, per census
traces_to:   0.3
```

All 19 assets are `asset_kind = data`, `scope = per_chart`, `catalog_status = CURRENT`, writer-backed; the census reports `global_runs` 61 and `global_runs_touching_layer` 519 (a figure larger than the run count; the inspector does not state its unit, and SUMMARY.md prints it "as printed by the inspector").

| asset | registry target_table | census live rows (chart) | registry target_floor | asset_throughput (chart): state / rows_written | deps (registry) | blocking radius direct / transitive | direct dependents outside L1 |
|---|---|---|---|---|---|---|---|
| `ga_ayurdaya` | chart_facts | 130 | 130 | lit / 130 | 1 | 0 / 0 | none |
| `ga_condition` | ga_condition_composite | 2,970 | 2,880 | lit / 45 | 3 | 4 / 51 | L2 1, L4 1 |
| `ga_dashas` | chart_dashas | 483,870 | 471,767 | lit / 483,870 | 1 | 14 / 61 | L2 1, L3 7 |
| `ga_medical` | ga_medical | 45 | 45 | lit / 45 | 2 | 0 / 0 | none |
| `ga_nakshatra` | chart_facts | 2,847 | 1,813 | lit / 2,847 | 3 | 4 / 56 | L2 2 |
| `ga_panchanga` | chart_facts | 437 | 437 | lit / 437 | 2 | 5 / 56 | L2 1, L3 1, L4 1 |
| `ga_positions` | chart_facts | 1,205 | 1,205 | lit / 1,205 | 0 | 31 / 79 | L2 6, L3 8, L4 1, L5 1 |
| `ga_prashna` | ga_prashna_judgment | 0 (census2; null in census1, see MF-L1-001) | 0 | lit / 0 | 2 | 0 / 0 | none |
| `ga_sade_sati` | chart_facts | 6,287 | 6,120 | lit / 6,287 | 7 | 1 / 49 | L2 1 |
| `ga_sensitive` | chart_facts | 8,775 | 8,775 | lit / 8,775 | 2 | 4 / 58 | L2 2 |
| `ga_sensitive_degree` | chart_facts | 335 | 335 | lit / 335 | 1 | 0 / 0 | none |
| `ga_strength` | NULL (count_sql over chart_facts) | 14,141 | 13,621 | lit / 13,715 | 2 | 5 / 56 | L2 1, L3 1 |
| `ga_structural` | NULL (count_sql over chart_facts + fact_category_ownership) | 102,037 | 98,446 | lit / 106,707 | 7 | 7 / 55 | L2 4 |
| `ga_tajaka` | l1_tajik_varsha_year_lords | 240 | 240 | lit / 240 | 3 | 1 / 26 | L3 1 |
| `ga_transit_anchors` | ga_transit_anchors | 45 | 45 | lit / 45 | 1 | 0 / 0 | none |
| `ga_vargas` | chart_divisionals | **0** | 22,092 | lit / **24,400** | 1 | 6 / 61 | L2 2 |
| `ga_vastu` | ga_vastu_planet_direction_map | 40 | 40 | lit / 40 | 1 | 0 / 0 | none |
| `ga_vichara` | chart_vichara | 8,524 | 8,249 | lit / 8,524 | 4 | 1 / 49 | L2 1 |
| `ga_yoga` | ga_yoga_firings | 53 | 63 | lit / 53 | 2 | 3 / 51 | L2 1, L3 1 |

`ga_condition`'s census figure is a `count_sql` total over two tables (45 composite rows + 2,925 `chart_facts` rows); `ga_strength` and `ga_structural` declare no single target and are counted by predicate over `chart_facts` (`ga_structural` also over `fact_category_ownership`). For the chart, `chart_facts` holds 143,299 rows (query `count(*) … WHERE chart_id`), `chart_dashas` 483,870, `chart_divisionals` 0. `ga_prashna`'s census2 `live_rows` is 0 (a `count_sql` total over `ga_prashna_lagna` and `ga_prashna_judgment` for the chart; census1 had null because of a permission error, MF-L1-001). `asset_throughput.rows_per_second` is NULL on 19 of 19 rows.

**Build record per asset** (census `Build.exercised`, `Build.history`; population: `build_run_assets` ⋈ `build_runs` for all charts, as the inspector reads them):

| asset | writer file | Build.exercised (executed runs of build_run_assets rows) | Build.history | latest recorded error (per census) |
|---|---|---|---|---|
| `ga_ayurdaya` | `ga_ayurdaya.py` | 14 of 23 | PARTIAL (0 err / 4 abort) | none recorded |
| `ga_condition` | `ga_condition.py` | 42 of 90 | PARTIAL (14 err / 8 abort) | 2026-09-07: post-write integrity check failed: integrity_check_sql → False |
| `ga_dashas` | `ga_dashas.py` | 65 of 104 | PARTIAL (18 err / 6 abort) | 2026-08-05: orphaned_by_crash: prior orchestrator terminated while asset was in-flight |
| `ga_medical` | `ga_medical.py` | 40 of 60 | PARTIAL (9 err / 7 abort) | 2026-07-16: BLOCKED: upstream dependency ga_condition did not complete |
| `ga_nakshatra` | `ga_nakshatra.py` | 41 of 51 | PARTIAL (1 err / 5 abort) | 2026-09-07: provenance receipt: output digest spec where_in values must be unique and sorted |
| `ga_panchanga` | `ga_panchanga.py` | 38 of 48 | PARTIAL (0 err / 5 abort) | none recorded |
| `ga_positions` | `ga_positions.py` | 44 of 53 | **FAIL** (1 err / 5 abort; most recent run aborted 2026-09-19) | 2026-09-05: provenance: Object of type UUID is not JSON serializable |
| `ga_prashna` | `ga_prashna.py` | 37 of 48 | PARTIAL (0 err / 6 abort) | none recorded |
| `ga_sade_sati` | `ga_sade_sati.py` | 46 of 106 | PARTIAL (21 err / 9 abort) | 2026-08-05: BLOCKED: upstream ga_dashas, ga_structural did not complete |
| `ga_sensitive` | `ga_sensitive.py` | 40 of 50 | PARTIAL (3 err / 7 abort) | 2026-08-08: orphaned_by_crash |
| `ga_sensitive_degree` | `ga_sensitive_degree.py` | 16 of 26 | PARTIAL (0 err / 4 abort) | none recorded |
| `ga_strength` | `ga_strength.py` | 41 of 57 | PARTIAL (7 err / 9 abort) | 2026-07-14: BLOCKED: upstream ga_vargas did not complete |
| `ga_structural` | `ga_structural.py` | 49 of 115 | PARTIAL (23 err / 10 abort) | 2026-09-07: post-write integrity check failed: integrity_check_sql → False |
| `ga_tajaka` | `ga_tajaka.py` | 43 of 63 | PARTIAL (7 err / 7 abort) | 2026-07-16: swisseph.calc_ut: jd -0.001010 outside Moshier planet range |
| `ga_transit_anchors` | `ga_transit_anchors.py` | 37 of 48 | PARTIAL (0 err / 6 abort) | none recorded |
| `ga_vargas` | `ga_vargas.py` | 43 of 52 | PARTIAL (5 err / 6 abort) | 2026-09-07: post-write integrity check failed: integrity_check_sql → False |
| `ga_vastu` | `ga_vastu.py` | 39 of 59 | PARTIAL (10 err / 7 abort) | 2026-09-08: post-write integrity check failed: integrity_check_sql → False |
| `ga_vichara` | `ga_vichara.py` | 24 of 71 | PARTIAL (14 err / 3 abort) | 2026-08-05: BLOCKED: upstream ga_dashas, ga_structural, ga_yoga did not complete |
| `ga_yoga` | `ga_yoga.py` | 44 of 105 | PARTIAL (15 err / 9 abort) | 2026-08-05: BLOCKED: upstream ga_dashas, ga_structural did not complete |

**The shared table.** `chart_facts` is the declared target of seven assets and is also written by `ga_strength`, `ga_structural` and
`ga_condition`. **TIER GAP: TG-L1-005** (ownership and counting rule). Measured, not concluded: each of the seven has a `natural_key_partition`
in the registry and a partition-scoped `count_sql` (sum of the seven live figures 20,016); `fact_category_ownership` (67 category rows)
names three owners only and, joined to the chart's 143,299 rows, owns 102,037 (`ga_structural`) + 130 (`ga_ayurdaya`) + 90 (`ga_condition`), leaving 41,042
rows with no owner row; the `ga_strength` predicate matches 420 rows the ownership table gives `ga_structural`; whether the partitions are disjoint and
complete over the 143,299 rows is not measured. Census cells `Complete.depth`, `Ldgr.source_presence`, `Vocab.identity`, `Reach.fields` and
`Dens.served` are still whole-table and attributed alike to each producer (MF-L1-002).

**Three-way baseline** (deployed / current code / target). *Deployed:* the production figures above (structure read from `information_schema`, never
the migration ledger). *Current code:* origin/main e2352f88 only; another head carries the engine's timing commit (`8edba0533` on `campaign/nirmana-engine`, not on main),
so the code side differs by head. **TIER GAP: TG-L1-004** — per-asset deployed-versus-code comparison not measured. *Target:* the asset briefs (A.L1).

### 1.2 · Individual contribution — ablate one

```
inherits:    Product §14.1 (ablation), Data plane §12.2
measured_by: none available — no ablation harness is named in the tiers, the census or the repository; the columns below are read-only reach measurements from the census, offered as information
traces_to:   0.1 (which rows this asset serves)
```

The template's individual term (with-versus-without, scored against the product's ten obligations) is **not measured for any of the 19
assets: absent instrument.** It is recorded as an absent instrument, never as a number (T1 §1.3; T2 §3.5). L1 is `scoring: contribution`
(census), not a reference layer, so the reference-layer fidelity clause does not apply. The measurements the census does hold, which
are reach and not contribution:

| asset | Dens.served | capability modules serving it | of which declare density_contract | Reach.fields width | depth |
|---|---|---|---|---|---|
| `ga_ayurdaya` | PASS | 34 | 19 | 54.2% | 100.0% |
| `ga_condition` | PASS | 1 | 1 | 88.9% | 100.0% |
| `ga_dashas` | PASS | 3 | 1 | 30.9% | 100.0% |
| `ga_medical` | PASS | 1 | 1 | 86.7% | 100.0% |
| `ga_nakshatra` | PASS | 34 | 19 | 54.2% | 100.0% |
| `ga_panchanga` | PASS | 34 | 19 | 54.2% | 100.0% |
| `ga_positions` | PASS | 34 | 19 | 54.2% | 100.0% |
| `ga_prashna` | N/A (0 registry modules; census `reach.modules` lists one MCP reader, `register_p1_synthesis.ts`) | 0 | 0 | 5.9% (1 of 17 columns) | 100.0% |
| `ga_sade_sati` | PASS | 34 | 19 | 54.2% | 100.0% |
| `ga_sensitive` | PASS | 34 | 19 | 54.2% | 100.0% |
| `ga_sensitive_degree` | PASS | 34 | 19 | 54.2% | 100.0% |
| `ga_strength` | NO_DETECTOR | not attributable by code | — | n/a | n/a |
| `ga_structural` | PASS | 2 | 1 | n/a (no target_table) | n/a |
| `ga_tajaka` | PASS | 2 | 1 | 100.0% | 100.0% |
| `ga_transit_anchors` | PASS | 1 | 1 | 88.9% | 100.0% |
| `ga_vargas` | PASS | 4 | 1 | 100.0% | 100.0% |
| `ga_vastu` | PASS | 1 | 1 | 81.8% | 100.0% |
| `ga_vichara` | PASS | 2 | 2 | 80.0% | 100.0% |
| `ga_yoga` | PASS | 2 | 2 | 0.0% (a lower bound; the module selects a run-time column set) | 100.0% |

The seven `chart_facts` producers show one identical figure because the census attributes by table (MF-L1-002, MF-L1-009). A reader must not
take "34 modules" as a per-asset contribution. `ga_prashna` is the only zero-radius asset for which `Dens.served` counts 0 registry modules (with 0/0 radius and 0 chart rows), but it is not consumer-less: the census's `reach.modules` lists one MCP reader (`platform-mcp/src/tools/register_p1_synthesis.ts`) selecting 1 of its 17 columns (5.9%, `chart_id`). The other five zero-radius assets each show at least one module in `Dens.served` (two of them, `ga_ayurdaya` and `ga_sensitive_degree`, only through the table-level attribution).

### 1.3 · Synergistic contribution — ablate the group

```
inherits:    Data plane §3.4 (presentation contract), §7 (DP contracts), §3.5 (four seams)
measured_by: no ablation harness exists; the seam-by-seam measurements below are read-only (registry, code at e2352f88, chart queries)
traces_to:   0.2
```

The synergistic term is an **absent instrument**; no fraction is recorded (T3 §1.5: "Do not invent a fraction to fill the field").
The seam-by-seam measurements are the value recorded, over T2 §3.5's four seams:

- **Vocabulary seam.** `brahmagyan/verification_vocab.py` is one controlled vocabulary for one field (`verification_pass_status`, 13 members; `single_pass` a deprecated alias of `single`); every value stored on the chart's 143,299 `chart_facts` rows is a member. Census `local_map_candidates = -1`, so the T2 §4.1 independent-map count is a non-result for every other class (TG-L1-014).
- **Contract seam.** All 19 writers carry `@l1_producer_contract` (`ga_writers/data_plane_runtime.py`, `CONTRACTED_L1_ASSETS` = the same 19), which opens a generation partition per build (migration 1035). The generation tables exist in production and are unreadable to the reader login (MF-L1-012); consumer-side field reads are not measured (TG-L1-009).
- **Edge-ordering seam.** The live DAG is acyclic with six levels (§2.5). One historical collision shows the seam: two writers (`ga_condition`, `ga_structural`) deleted and re-inserted the same two `chart_facts` categories, and only serial execution kept them from blocking each other under the wave scheduler (migration 416's comment, then edge removed by 419). Current state of that pair: no edge between them in the registry; both count rows through predicates that overlap (MF-L1-005).
- **Presentation seam.** Which §3.4 rows L1 carries is a join of two tier tables (§2.2); the parity test is [TRANSFERS]-pending (TG-L1-011).

This term is the department test (T3 §1.3). Its current size is **not measured**; what the seams show is that the shared-table seam (five census cells attributed table-wide) is where
attribution is weakest.

### 1.4 · Cross-layer handoff — what it produces for downstream

```
inherits:    Data plane §11 (six evidence states), §7 (DP contracts this layer PRODUCES)
measured_by: per contract, the six-state position; states 1 and 2 from the census and registry (producer side), state 5 from census Dens.served, states 3, 4 and 6 not measured at any consumer (TG-L1-009)
traces_to:   0.3 (hands onward)
```

No tier assigns an L1 asset to a DP contract (TG-L1-009); the mapping below is by asset name and table and is labelled as such. Evidence
states: (1) source-present, (2) method-qualified, (3) consumed by the intended component, (4) traceably transformed, (5) served, (6) value
evaluated. States 3, 4 and 6 are "verified at the consumer" and no consumer-side probe exists in the census; registry edges are declared consumption, not verified.

| contract (T2 §7.1) | L1 producer assets, by name/table | (1) present at the chart | (3) declared consumers outside L1 (registry direct edges) | (5) served (census) | (2), (4), (6) |
|---|---|---|---|---|---|
| DP03 chart facts | `ga_positions`, `ga_ayurdaya`, `ga_nakshatra`, `ga_panchanga`, `ga_sensitive`, `ga_sensitive_degree`, `ga_sade_sati` (+ `ga_strength`, `ga_structural`, `ga_condition` rows) in `chart_facts`; `ga_dashas` in `chart_dashas`; `ga_vargas` in `chart_divisionals` | `chart_facts` 143,299 · `chart_dashas` 483,870 · `chart_divisionals` **0** | see §1.1 last column (L2 to L5 edges: `ga_positions` 16, `ga_dashas` 8, `ga_structural` 4 …) | `chart_facts` 34 modules (table-level), `chart_dashas` 3, `chart_divisionals` 4 | (2) L0 release id/digest carried in code (`L0_SEMANTIC_RELEASE_ID`), verified against nothing measured here; (4), (6) not measured |
| DP04 condition decomposition | `ga_condition` (composite + `chart_facts`), `ga_strength` | 2,970 · 14,141 | L2 1 + L4 1 · L2 1 + L3 1 | 1 module · not attributable | (2), (4), (6) not measured |
| DP05 share (clause results) | `ga_yoga` (`ga_yoga_firings`) | 53 (floor 63) | L2 1, L3 1 (+ `ga_vichara` in L1) | 2 modules | `partial_formation_pct` and `activation_dasha_periods` never populated (census, whole-table 202 rows); (2), (4), (6) not measured |
| DP07 primitives (clocks) | `ga_dashas`, `ga_tajaka`, `ga_transit_anchors`, `ga_sade_sati` | 483,870 · 240 · 45 · 6,287 | L2 1 + L3 7 · L3 1 · none · L2 1 | 3 · 2 · 1 · 34 (table-level) | (2), (4), (6) not measured |
| no contract named in T2 §7.1 | `ga_vichara` (judged structure, T2 §3.3), `ga_ayurdaya`, `ga_medical`, `ga_vastu`, `ga_prashna` | 8,524 · 130 · 45 · 40 · 0 | L2 1 · none · none · none · none | 2 · 34 (table-level) · 1 · 1 · 0 (`Dens.served`; census `reach.modules` lists one MCP reader) | not measured |

An asset can contribute nothing to L1's served value and be essential because a downstream layer reads it; the six zero-radius assets have no declared consumer, so for them the cross-layer term rests on the served surface alone.

### 1.5 · The accounting

```
inherits:    —
measured_by: 1.2 + 1.3 + 1.4 against 0.2
traces_to:   0.2
```

layer value = Σ individual + Σ synergistic + Σ cross-layer handoff. **None of the three terms has an instrument that produces a number, so no sum and
no fraction is recorded, and the shortfall against 0.2 is itemised in Part 3 from measured gate results and open tier gaps, not from a value figure.**
Candidates under T3's rule ("a candidate, not a verdict; lack of a caller in a bounded search is not redundancy"): the only asset with no rows for the chart, no
dependents and no registry-counted capability module (`Dens.served` 0) is `ga_prashna` (registry `data_disposition = RETAINED_AS_CAPITAL`), though census `reach.modules` lists one MCP reader for it, so it is not without a consumer. An asset with a large individual reach and no synergistic
seam of its own is not identifiable without the harness. This is a candidate list of one, not a disposition.

---

## Part 2 · CONDITIONS UNDER WHICH THE VALUE IS REAL

### 2.1 · Correctness rules

```
inherits:    Product §8.1 (this layer's row), §13; Data plane §9.2 (the switch and the storage separation)
measured_by: a detector per rule — named where one exists; where none exists the cell says NO DETECTOR (census; code read at e2352f88)
traces_to:   0.2 — the value is real only if these hold
```

**The product's "what must not happen" row for L1** (T1 §8.1, line 423), verbatim: "Altering birth facts or chart calculations to fit biography."

**The life-event switch, as T2 §9.2 (lines 493–517) states it.** ON: "L1 separate event-time context." OFF: "Nothing derived from life events, anywhere. Every reading emits only what the chart, sources and methods produce on their own." Storage separation: "event-conditioned overlays are kept separate from event-free structural and temporal products. Turning the switch OFF deselects the overlays; it never requires recomputing the event-free products." Event-time calculation, where authorized, "use[s] separate context identities and do[es] not overwrite natal truth" (T2 §6.2, line 359). What is not supplied: an identity form for an event-time context and a detector (TIER GAP: TG-L1-010). None of the 19 registry assets is declared as an event-time asset; whether any writes event-conditioned rows is not measured.

| rule | source | detector | current result |
|---|---|---|---|
| biography must not alter a birth fact or chart calculation | T1 §8.1 L1 row | none in the census; FORENSIC anchor gates exist in five writers plus `forensic_gate_vargas` (test that birth anchors reproduce, a different claim) | **NO DETECTOR** for this rule (TG-L1-010) |
| no invented computation, source, detector, confidence or score | T1 §13 | none as a per-rule detector; nearest cells are `Build.contract` and `Carr.detector` | `Build.contract` PASS 19/19 (contract shape only); `Carr.detector` NO_DETECTOR 19/19 |
| consumers refer to L1 facts, they do not recompute them | T1 §11 (line 501); T2 §6.2 | none in the census; the `check_fact_category_pinning.py` CI guard at `platform/scripts/governance/` addresses category-only selection by consumers (per CLAUDE.md §N.7 item 2; file present, not run here) | NO DETECTOR in the census for the rule as stated |
| zero stays zero, unavailable stays unavailable; missing computation is a named gap, never a neutral default | T1 §3.3; T2 DP04 (line 423) | none: plan §2.1 says no `Null.*` criterion exists; the L1 census has none | **NO DETECTOR**; the code has `MissingnessState` (`data_plane_contracts.py:37–46`) and a `floored` status |
| no downstream selection "whichever row first matches a category" | T2 §6.2 (line 357) | as row three | as row three |
| the sentence that grades a number is verified separately from the arithmetic | T1 §3.3; T2 §12.2 (line 612) | none; L1's only narration check found is `run_no_narration_linter` (`ga_writers/gates.py:42`), wired only through the legacy `build_runner` (MF-L1-008) | **NO DETECTOR** on the orchestrated path by this reading |

A rule with no detector is a wish (T3 §2.1). Register R117 records the same for L2 and asks for a detector registry per layer rule; TG-L1-010 cites it.

### 2.2 · Presentation obligation

```
inherits:    Product §2 (two modes, one depth); Data plane §3.4 (the field → contract mapping)
measured_by: the join of T2 §3.4 with §7.1 (a reading of two tier tables, not a stated assignment: TG-L1-012); census Reach.fields (columns exposed by capability modules); presentation-parity test NOT run
traces_to:   0.1 — the acharya rows are unservable if these fields are not carried
```

| T2 §3.4 row (acharya rendering) | contract(s) that carry it | producer layer per T2 §7.1 | L1's share, by the join |
|---|---|---|---|
| method and school, where authorities disagree | DP02 | L0 | none — except that āyurdāya's schools are to be carried (T2 §5, line 338) |
| prerequisites tested, exceptions checked, including passed clauses | DP02 (clause set), DP05 (each clause's result) | L0; L0+L1 → L2 | partial: `ga_yoga` clause results. The L1 fields inside DP05 are not delineated (TG-L1-012) |
| conventions in force — ayanāṃśa, node, house system, varga construction | DP01, DP03 | L0; L1 | yes in storage — `ayanamsha_id` is served; `engine_version` is stored but dark; `fact_subject`/`fact_key` bind frame and varga by name only (unverified) |
| intermediate quantities, not only the graded result | DP03, DP04 | L1 | yes |
| dignity, strength and condition components separately, with units and disagreements | DP04 | L1 | yes — `ga_strength`, `ga_condition` |
| competing readings and their authorities | DP06, DP02 | L2; L0 | none |
| the chain of influence with typed relations | DP06 | L2 | none |
| clock geometry, activation rule, nearest-vs-better-supported criterion, bridge or falsifier | DP07, DP08, DP09 | L0/L1/L3; L2+ → L3; L3+ → L4 | DP07 primitives only |

The columns that DP03's "input precision and verification" would naturally live in are present in `chart_facts` (`verification_pass_status`, `tolerance_arcsec`, `near_sign_boundary_flag`,
`near_nakshatra_boundary_flag`, `cross_ayanamsha_divergence_arcsec`); the census lists as **dark** (built, selected by no capability module) for the `chart_facts` producers: `build_id`, `chart_id`, `citation_human`, `computed_at`,
`cross_ayanamsha_divergence_arcsec`, `engine_version`, `near_nakshatra_boundary_flag`, `near_sign_boundary_flag`, `source_calculation`, `tolerance_arcsec`, `vargottama_flag_at_point` (11 of 24 built columns; `Reach.fields` reads NOT_GENERIC, "reported, not graded").
Binding a DP03 field to a column is left to the briefs (T2 §7: "Names not present in source are target semantic fields, to bind in layer/asset briefs"). Whether both renderings can be produced from the consumed package without recomputation (T2 §3.4, last paragraph) is the parity test: **TIER GAP: TG-L1-011** ([TRANSFERS]-pending; never a pass, never a block).

### 2.3 · Contracts produced and consumed

```
inherits:    Data plane §7 (DP01-DP17), §7.1 (common envelope)
measured_by: T2 §7.1 field lists (definitional); producer-side presence from census and registry; consumer-side reads NOT measured
traces_to:   0.3
```

**Produced** (T2 §7.1; asset mapping by name, TG-L1-009): DP03 chart facts, DP04 condition decomposition, DP05 (the L1 share), DP07 (the L1 primitives); §1.4 gives fields, grain and state per contract group. The grain per table, as the writers' code keys it: `chart_facts` (chart_id, ayanamsha_id, fact_category, fact_subject, fact_key) with `build_id` in the unique key (`ga_writers/_idempotency.py` lines 3–6); `chart_dashas` (chart_id, ayanamsha_id, system_id, level_n, start_iso); `chart_divisionals` scoped (chart_id, ayanamsha_id, varga). The other tables' keys: not stated in any tier and not read here.

**Consumed:** DP01 (canonical entities, aliases, units, released definitions) and DP02 (rule clauses, prerequisites and exceptions to test). The declared receipts are the five L0 edges (§0.3), and the code carries `L0_SEMANTIC_RELEASE_ID = "l0.semantic.2026-09-13.1"` and a digest (`ga_writers/data_plane_contracts.py`) recorded per generation. **Declared use** per consumed input (calculation, applicability, counter-evidence, uncertainty, interpretation, exclusion, navigation, evaluation) is not on record as data anywhere (TIER GAP: TG-L1-009, R109); "A citation with no declared use is not a contract" (T3 §2.3, line 299; T2 §7.1, line 416, words it "does not prove utilization"), so the five edges are declared dependencies, not yet contracts in the template's sense. The load-bearing rule (T1 §11) is restated in 2.1.

### 2.4 · Jyotish coverage owned

```
inherits:    Product §3 (substance), Data plane §5 (domain obligations)
measured_by: per obligation the five states — NOT ASSIGNABLE from the tiers; census Complete.width NOT_GENERIC 19/19, Complete.depth over whole tables (MF-L1-002)
traces_to:   0.1
```

**TIER GAP: TG-L1-013.** T1 §3 names the substance; T2 §5 assigns L1 in two rows only; no tier lists the obligations L1 owns or declares a universe for any of them. The five-state result
(applied / inapplicable-with-reason / unavailable / unqualified / unresolved) is therefore **not assigned to any obligation**: assigning one would be an invented result. What is measured, by
asset name only (the mapping is not stated by any tier):

| T1 §3 substance | L1 asset(s) whose name matches | measured presence (chart) | measured depth (census, whole-table population) | state |
|---|---|---|---|---|
| 3.1 graha roles and placement | `ga_positions` | 1,205 | `chart_facts` 421,096 rows, 25 cols, 17 fully populated, `salience_formula_ver` never populated | not assigned |
| 3.3 condition, dignity, bala, avasthā | `ga_condition`, `ga_strength` | 2,970 · 14,141 | `ga_condition_composite` 135 rows / 31 cols, never populated: `avastha_lajjitaadi`, `avastha_sayanadi`, `speed_degrees_per_day`, `graha_yuddha_result` | not assigned |
| 3.4 sambandha (aspects, dispositors, argalā) | within `ga_structural` (argala, yoga, dosha, varga row counts appear in its build log) | 102,037 | no depth cell (no target table) | not assigned |
| 3.6 varga with sensitivity | `ga_vargas` | **0** | NO_DETECTOR (table empty) | not assigned |
| 3.7 yoga, doṣa, cancellation | `ga_yoga`, part of `ga_structural` | 53 (floor 63) | `ga_yoga_firings` 24 cols, 15 fully populated; `partial_formation_pct`, `activation_dasha_periods` never populated | not assigned |
| 3.8 nakshatra, pada, KP | `ga_nakshatra`, `ga_sensitive_degree` | 2,847 · 335 | `chart_facts` (as above) | not assigned |
| 3.9 ārūḍha, special lagnas | within `ga_sensitive` | 8,775 | `chart_facts` (as above) | not assigned |
| 3.10 daśā, Tājaka, tithi-praveśa, Sudarśana (clock foundations) | `ga_dashas`, `ga_tajaka`, `ga_transit_anchors`, `ga_sade_sati` | 483,870 · 240 · 45 · 6,287 | `chart_dashas` 42 cols, 22 fully populated, none never-populated; `l1_tajik_varsha_year_lords` 18/18 | not assigned |
| 3.11 pañcāṅga, praśna | `ga_panchanga`, `ga_prashna` | 437 · 0 | as above · NO_DETECTOR (empty) | not assigned |
| āyurdāya (T1 P23; T2 §5, V12) | `ga_ayurdaya` | 130 | `chart_facts` (as above) | not assigned |
| medical and vāstu applications | `ga_medical`, `ga_vastu` | 45 · 40 | 15 cols, 14 fully populated, none never-populated · 11 cols, all populated | not assigned |
| judged structure (T2 §3.3) | `ga_vichara` | 8,524 | 20 cols, 13 fully populated | not assigned |

The declared universe per asset (T4 §1.1) does not exist as data; the width cell for all 19 reads "no declared universe for this asset — declaring one is the first width gap". The sub-list of asset-specific universes such as the varṣaphala year-lord set for `ga_tajaka` (register R98) stays open.

### 2.6 · Vocabulary conformance

```
inherits:    Data plane §4.1 (the controlled vocabulary — six rules with detectors)
measured_by: census Vocab.identity (declared-key duplicate count, rule 1(i) only); census local_map_candidates; code read of brahmagyan/verification_vocab.py; chart query of chart_facts.verification_pass_status
traces_to:   0.2 — the value is real only if the layer speaks the plane's one language
```

L1 conforms; L0 owns the set (T3 §2.6). **TIER GAP: TG-L1-014** for which of T2 §4.1's sixteen classes (planets, signs, houses, nakshatras, vargas, karakas, aspect types, upagrahas, yogas, doṣas, daśā systems, domains, concepts, remedy types, texts, schools) L1 emits or accepts.
- *Rule 1(i), identity:* `Vocab.identity` PASS 15, NO_DETECTOR 2 (`ga_prashna`, `ga_vargas`: empty tables, uniqueness vacuous), no cell for `ga_strength` and `ga_structural`. The census tests the duplicate count of each table's own declared row key (`fact_id` for the `chart_facts` producers, `dasha_row_id`, `(chart_id, ayanamsha_id, graha)`, `(chart_id, ayanamsha_id, yoga_canonical_id)`, `(id)` …), 0 duplicates on each populated table. That is **row identity**; T2 §4.1 rule 1(i) states its detector for the authority's key (L0) and rules 2 and 5 for resolution and interface parameters, so **no census cell tests that an L1 name resolves through the controlled set**.
- *Rule 1(ii), aliases:* no L1 cell; not measured.
- *Rule 4, parity tests:* the one L1-visible snapshot is the `verification_pass_status` table, whose build-side copy in `verification_vocab.py` is documented as guarded by `tests/test_verification_vocab.py` against the serve-side copy in `envelope.ts` (per the module docstring; the test was not run here).
- *Rules 2, 3, 5, 6:* census `local_map_candidates = -1` (non-result); interface-parameter census not in the census.
- *Stored values of the one measured field*, chart 482012f1, `chart_facts`: `single` 115,807; `single_pass` 10,836 (a deprecated alias of `single`); `two_pass_verified` 9,320; `computed_extension` 3,855; `floored` 2,365; `documented_approximation` 1,020; `pending_w3_verification` 50; `not_defined_for_nodes` 32; `classical_match` 14 (sum 143,299; all are members of the 13-entry vocabulary, one of them a deprecated spelling still stored).

### 2.7 · Source carriage and reproduction

```
inherits:    Product §11 (L1 computational correctness); Data plane §12.2 (Source carriage and reproduction), §4.3, §5
measured_by: census Carr.detector (19 cells); chart query of verification_pass_status; code read of the independent verifier module
traces_to:   0.1 — a layer that corrupts what it carries serves no P-need, however well it is engineered
```

This section asks whether what L1 restates matches its source, whether what it computes reproduces a second way, and whether witness disagreement is carried (T3 §2.7 a–c). It does not ask whether the astrology is right (ruling 11).

- **The layer-level hint** (T4 "Adapting per layer", line 505): "`Carr` D3 dominates." The hint does not cover every asset: āyurdāya (T2 §5 line 338, "the disagreement between authorities") is a D2 case; classical-rule applications (T2 §3.3 line 176) invite D1. **TIER GAP: TG-L1-015** for the per-asset (concept, check) pairs; none is assigned here.
- **Measured.** `Carr.detector` = NO_DETECTOR for 19 of 19 ("no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics"). `NO DETECTOR` is a gap, never a pass.
- **What exists in code but not in the census.** `ga_writers/_vimshottari_independent_verifier.py` (1,483 lines) re-derives Vimshottari levels 1–4 independently and compares boundary by boundary; its docstring says levels 2–4, which nothing else examined, are honestly stamped `single`. Whether it runs on the orchestrated path was not traced.
- **The verification field as stored** (chart 482012f1): `chart_facts` `two_pass_verified` 9,320 of 143,299 rows (6.5%), `single` + `single_pass` 126,643 (88.4%); `chart_dashas` `two_pass_verified` 46,009 of 483,870 (9.5%), `single` 437,474 (90.4%), `classical_match` 386, `scope_cap_sentinel` 1. The vocabulary's own rule: only `two_pass_verified` "counts as grounding". Which outputs *require* an independent derivation is not settled by any tier (TIER GAP: TG-L1-022).
- **Sensitivity data present:** `near_sign_boundary_flag` true on 725 rows, `near_nakshatra_boundary_flag` true on 657; `cross_ayanamsha_divergence_arcsec` non-null on all 143,299; `tolerance_arcsec` non-null on 8,775 (6.1%).

### 2.5 · Edges and order

```
inherits:    Data plane §3.2; the registry DAG
measured_by: topological levelling and cycle check computed over the live asset_registry.depends_on of the 19 ga_* rows (read 2026-09-30); census Build.dag (edges resolvable) and Build.dep_liveness (declared dependencies lit at the chart); egate.sql NOT run (TG-L1-016)
traces_to:   0.3
```

| level | asset | registry depends_on (live) | census Build.dag edges |
|---|---|---|---|
| 0 | `ga_positions` | (none) | 0 |
| 1 | `ga_ayurdaya` | `ga_positions` | 1 |
| 1 | `ga_dashas` | `ga_positions` | 1 |
| 1 | `ga_nakshatra` | `bg_nakshatra`, `ga_positions`, `bg_kp_sublord_division` | 3 |
| 1 | `ga_panchanga` | `ga_positions`, `bg_panchanga` | 2 |
| 1 | `ga_prashna` | `ga_positions`, `bg_prashna_rules` | 2 |
| 1 | `ga_sensitive` | `ga_positions`, `bg_reference` | 2 |
| 1 | `ga_sensitive_degree` | `ga_positions` | 1 |
| 1 | `ga_transit_anchors` | `ga_positions` | 1 |
| 1 | `ga_vargas` | `ga_positions` | 1 |
| 2 | `ga_condition` | `ga_positions`, `ga_vargas`, `ga_dashas` | 3 |
| 2 | `ga_strength` | `ga_positions`, `ga_vargas` | 2 |
| 2 | `ga_tajaka` | `ga_positions`, `ga_dashas`, `ga_sensitive` | 3 |
| 3 | `ga_medical` | `ga_condition`, `ga_positions` | 2 |
| 3 | `ga_structural` | `ga_dashas`, `ga_nakshatra`, `ga_panchanga`, `ga_positions`, `ga_sensitive`, `ga_strength`, `ga_vargas` | 7 |
| 3 | `ga_vastu` | `ga_condition` | 1 |
| 4 | `ga_sade_sati` | `ga_positions`, `ga_strength`, `ga_panchanga`, `ga_vargas`, `ga_dashas`, `ga_structural`, `ga_nakshatra` | 7 |
| 4 | `ga_yoga` | `ga_structural`, `ga_dashas` | 2 |
| 5 | `ga_vichara` | `ga_structural`, `ga_strength`, `ga_dashas`, `ga_yoga` | 4 |

No cycle; six levels (0–5); 45 edges. `ga_positions` is the layer root and the largest fan-out (31 direct, 79 transitive dependents in census). `Build.dep_liveness`: PASS 18, N/A 1 (`ga_positions`, no dependencies). Edge type: the registry carries no `edge_type`
(register R133 for L3); every edge here is read as a computational (build) edge, and the five L0 edges also as definition edges (T2 §3.2), **the per-edge type is not recorded anywhere**. The census reports edges resolvable, not that declared edges equal actual reads (MF-L1-006).
**TIER GAP: TG-L1-016** — the "frozen definition revision" the template asks the cross-layer gate to be scoped to belongs to the Nirmāṇa campaign's `egate.sql`; the Suvarṇa plan carries no such concept, and no cross-layer gate was evaluated.
Blocking radius (census, "active assets depending on it, transitively, every layer") is the severity weight for each failure: `ga_positions` 79, `ga_vargas` 61, `ga_dashas` 61, `ga_sensitive` 58, `ga_nakshatra` 56, `ga_panchanga` 56, `ga_strength` 56, `ga_structural` 55, `ga_condition` 51, `ga_yoga` 51, `ga_sade_sati` 49, `ga_vichara` 49, `ga_tajaka` 26; six assets 0.

---

## Part 3 · THE DELTA

```
inherits:    —
measured_by: the shortfall itemised from census gate results, registry and code reads; no value figure exists (1.5)
traces_to:   0.2
```

### 3.1 · Per obligation

L1 is scored on **one** of the product's ten proof obligations: **Computational correctness** (T1 §11, line 501; ten, not eleven, ruling 11). T1 §14 (line 588) states its evidence as five parts. Where the layer stands, measured:

| part of the obligation (T1 §14) | measured state at the chart | what closes the gap |
|---|---|---|
| authoritative inputs | `Build.contract` PASS 19/19 (birth params and chart id taken from `ctx.config`, per T4 §4.2 check 2); the L0 references read are declared for 4 assets and found undeclared for 5 (MF-L1-006) | edges reconciled (TG-L1-003, TG-L1-016) |
| reproducible calculations | `Idem.pattern` PASS 19/19 (static); `Build.completion` PASS 14, FAIL 4, PARTIAL 1 (census2); rebuild-twice reproduction (semantic fingerprint) not measured; `ga_vargas` 0 rows | packets in 4.2 (P1–P4); fingerprint proof is a brief item (Track A brief §5) |
| units and conventions | `chart_facts.unit` non-empty on 82,611 of 143,299 rows (57.6%); `ayanamsha_id`, `engine_version` present | which rows owe a unit is not stated by any tier (TIER GAP: TG-L1-024; the 57.6% is not gradable without it) |
| sensitivity | boundary flags and divergence columns present (2.7), dark in serving (2.2); no rule for what sensitivity is owed | TG-L1-022 |
| independent verification where required | 6.5% (`chart_facts`) and 9.5% (`chart_dashas`) `two_pass_verified`; `Carr.detector` NO_DETECTOR 19/19 | TG-L1-022, TG-L1-015 |

### 3.2 · Per asset — disposition

The disposition letter for each asset is the output of the A.L1 dispositions file (Track A brief §5), not drafted here: no tier gives an evidence→letter rule (TIER GAP: TG-L1-017), T2 §10.1 says "no quota", and a letter assigned from the census alone would be a verdict the template forbids without Part 1's value terms. The evidence Part 1 does hold, per asset, with no letter:

| asset | measured evidence toward a disposition (open cells only; every other census cell reads PASS) |
|---|---|
| `ga_positions` | `Build.history` FAIL (most recent run aborted); blocking radius 79 |
| `ga_ayurdaya` | `Complete.depth` PARTIAL (table-level); no dependents; 34 modules (table-level) |
| `ga_condition` | `Build.completion` FAIL (basis mismatch, R42: 45 vs 2,970); `Complete.depth` PARTIAL (4 never-populated columns) |
| `ga_dashas` | `Build.history` PARTIAL (18 error / 6 abort); `Reach.fields` 30.9% (13 of 42 columns) |
| `ga_medical` | none beyond gate-level PARTIALs; 0/0 radius; 1 module |
| `ga_nakshatra` | `Build.history` PARTIAL; shares table-level cells |
| `ga_panchanga` | as `ga_nakshatra` |
| `ga_prashna` | `Build.completion` PARTIAL (census2: rows_written 0 = live 0, writer-backed, emptiness not declared by design; ERRORED in census1, MF-L1-001); 0 chart rows; 0 registry modules (one MCP reader in census `reach.modules`); 0/0 radius; `data_disposition = RETAINED_AS_CAPITAL`; `Count.floor` N/A (`target_floor` 0) |
| `ga_sade_sati` | `Build.history` PARTIAL (21 error / 9 abort); depends on 7 assets |
| `ga_sensitive` | table-level cells; `tolerance_arcsec` populated (8,775 rows) |
| `ga_sensitive_degree` | 0/0 radius; table-level cells |
| `ga_strength` | `Build.completion` FAIL (13,715 vs 14,141); `Dens.served` NO_DETECTOR (not attributable); no `Ldgr`/`Depth`/`Vocab` cell; 420 rows also owned by `ga_structural` per `fact_category_ownership` |
| `ga_structural` | `Build.completion` FAIL (106,707 vs 102,037); `Build.history` PARTIAL (23 error / 10 abort); no `Ldgr`/`Depth`/`Vocab` cell |
| `ga_tajaka` | all depth cells PASS; `Build.history` PARTIAL (7 error / 7 abort) |
| `ga_transit_anchors` | 0/0 radius; no `Ldgr` cell |
| `ga_vargas` | `Build.completion` FAIL, `Count.floor` FAIL (0 vs 22,092), state `lit` with 24,400 (LG-L1-002); blocking radius 61 |
| `ga_vastu` | 0/0 radius; `Build.history` PARTIAL (10 error / 7 abort, latest an integrity-check failure) |
| `ga_vichara` | `Build.history` PARTIAL (14 error / 3 abort); judged structure (T2 §3.3) |
| `ga_yoga` | `Count.floor` FAIL (53 vs 63); `Complete.depth` PARTIAL (`partial_formation_pct`, `activation_dasha_periods` never populated) |

### 3.3 · Per asset — what it must add

The contract fields (2.3), presentation fields (2.2) and coverage states (2.4) each asset must add are **not derivable from the tiers**: each depends on a clause that is a tier gap
(declared use, TG-L1-009; row assignment, TG-L1-012; owned obligations and universes, TG-L1-013). What this instance can state is the layer-wide additions the census and registry already show:
(a) a verdict basis for every gate cell, with the population named (MF-L1-002, MF-L1-003); (b) an earned status for the `lit` build record where the record and the live count disagree (`ga_vargas`, and the three FAILs in `Build.completion`); (c) the instruments the census lacks
for Earn/Cost, Null, Narr and Carr (MF-L1-007, plan §2.1); (d) a declared universe per asset (TG-L1-013). Asset-specific must-adds are the A.L1 briefs' inheritance from these rows, and a brief that must invent one has found a defect here, as T3 §4.4 says.

### 3.4 · Intra-layer interplay

The input/output/use matrix between the layer's own assets is the edge table in §2.5 (which asset reads which). **On which fields** each edge reads is not measured: the registry records assets, not fields, and the census has no field-level edge (TG-L1-009).
Boundary with adjacent layers: upstream L0, five declared edges and at least five undeclared reads (MF-L1-006); downstream, 46 declared edges from 25 assets (§0.3). The synergistic term this matrix is where the template says to build or find missing (T3 §3.4) is unmeasured (1.3); the observed weak points are the shared-table attribution (TG-L1-005, TG-L1-006), the overlapping `count_sql` predicates (MF-L1-005) and the historical two-writers-one-category collision (1.3).

---

## Part 4 · STRATEGY

### 4.1 · Order

```
inherits:    2.5
measured_by: the DAG in 2.5; the three-way baseline per asset (TG-L1-004)
traces_to:   0.2
```

Upstream before downstream, by the level in §2.5: level 0 `ga_positions`; level 1 nine assets; level 2 three; level 3 three; level 4 two; level 5 `ga_vichara`. Within a level nothing in the tiers constrains the choice
between assets, and T3 says to choose "for learning value, not alphabet"; **no learning-value measure exists**, so no within-level order is proposed here. Two orderings are forced by measured facts, not preference: `ga_vargas` (0 rows, radius 61) sits under `ga_condition`, `ga_strength`, `ga_structural`, `ga_sade_sati`; `ga_positions`'s failing run history sits under everything.
**The three-way baseline:** *deployed* = §1.1 and the build-record table; *current code* = origin/main e2352f88 (other heads not read, TG-L1-004); *target* = the A.L1 briefs. Delta = target − current code; risk = current code − deployed. Neither number is computed per asset here.

### 4.2 · Work packets

```
inherits:    Data plane §13.1, §13.3 item 8
measured_by: each packet's proof — a detector that fails when the packet has not landed
traces_to:   3.x — every packet closes a named delta item
```

Candidate packets that close a measured delta item. They are proposals for the A.L1 briefs and Track I; none has started, none is approved, and a packet the tiers can change is marked tier-dependent.

| packet | closes | proof (a detector that fails until it lands) | tier-dependent? |
|---|---|---|---|
| P1 restore and re-earn `ga_vargas` for the chart | LG-L1-002; `Build.completion` FAIL, `Count.floor` FAIL; `Idem` claim vs 0 rows | `chart_divisionals` chart count ≥ `target_floor` **and** build record = live count (the `Build.completion` cell) | no (cause of the empty table first) |
| P2 completion-honesty basis for `ga_condition`, `ga_strength`, `ga_structural` | MF-L1-005 (`Build.completion` FAIL ×3) | `rows_written` equals the compared count on a stated basis, or the basis is declared per asset | partly: TG-L1-005 decides ownership |
| P3 `ga_positions` run history | `Build.history` FAIL; latest error "Object of type UUID is not JSON serializable" (2026-09-05) | latest run complete and the error class absent from a new run | no |
| P4 the eight `_telemetry` call sites | LG-L1-001 (R34 residual) | grep finds no call to `update_asset_throughput(` from a `ga_writers` module, or each is declared CLI-only; `asset_throughput.rows_per_second` non-NULL after an orchestrated run (needs the engine timing landed, Track E) | design open: remove or keep as CLI |
| P5 `ga_yoga` floor | `Count.floor` FAIL 53 < 63 | chart count ≥ floor, or the floor re-declared with reason (floors are information under D3) | no |
| P6 grants for unmeasured cells | MF-L1-012 (MF-L1-001 first half already closed: census2 reads `ga_prashna` `Build.completion` PARTIAL, not ERRORED) | the generation tables readable by the reader login | outside L1 (access, Track E) |
| P7 declare universes, carriage pairs, classes, roles | TG-L1-013, -014, -015, -018 | `Complete.width` no longer NOT_GENERIC; `Carr.detector` no longer NO_DETECTOR | **yes — waits on the tier rows named** |
| P8 per-asset Idem behavioural check | MF-L1-004 | a rebuild-twice test on the chart leaves the semantic fingerprint unchanged (E5.5) | no |

### 4.3 · Generation, invalidation, rollback

```
inherits:    Data plane §11, §4.4, DP16
measured_by: code read (data_plane_runtime.py, _idempotency.py, migration 1035); production pg_class; access to the generation tables NOT available to the reader login
traces_to:   2.1 — a rebuild that resets chronology is a hindsight leak
```

What exists: every L1 writer is wrapped by `l1_producer_contract`, which opens a generation partition (`l1_data_plane_generations`, `…_generation_partitions`, `…_generation_heads`, `…_fact_snapshots`, `…_dasha_snapshots`, etc.; migration 1035, and 1033 per the runtime module's docstring) and completes it after a successful writer run, with an append-only immutable store beside the replace-in-place active tables (migration 1035's header). `chart_facts` deletes are gated by an owner receipt (`authorize_chart_fact_delete`, `_idempotency.py` lines 44–55). The consumed release is recorded: `L0_SEMANTIC_RELEASE_ID` and its digest are written into each generation.
What cannot be stated: **the generation pins each consumer records** (T3 §4.3) and **whether the invalidation path is exercised**, because `suvarna_reader` gets "permission denied" on `l1_data_plane_generations` and `…_generation_heads` (MF-L1-012); no rollback was exercised. The chronology-reset hazard of DP15a is an L4/L5 issuance concern (T2 §7.1), not an L1 one; L1's own hindsight-leak risk is the §8.1 rule (2.1), which has no detector.

### 4.4 · What each asset brief inherits

```
inherits:    Product §16; Data plane §13.3 (asset brief sentence)
measured_by: derivability — a brief author must be able to fill these from this instance alone
traces_to:   0.1
```

The thirteen inherited rows (T4 §0.1, lines 88–102) and whether this instance supplies them. **Each "TIER GAP" row is one a brief author would have to invent; per T4 §0.1 the brief raises it here and stops.**

| # | item | supplied by this instance? | source |
|---|---|---|---|
| 1 | P-needs and V-journeys the asset serves | **TIER GAP: TG-L1-001** (only V12/P23 for `ga_ayurdaya` and the four tier-named L1 texts in 0.1) | §0.1 |
| 2 | obligations scored on | **yes** — Computational correctness (T1 §11) for every L1 asset | §0.2, §3.1 |
| 3 | correctness rules and switch behaviour | partly — the T1/T2 rules in 2.1 are supplied; the detector per rule and the event-context identity are **TIER GAP: TG-L1-010** | §2.1 |
| 4 | presentation fields it must carry | partly — by the T2 §3.4 × §7.1 join (2.2); DP05/DP07 shares **TIER GAP: TG-L1-012**; parity **TG-L1-011** | §2.2 |
| 5 | contracts produced and consumed, with declared use | partly — contracts by asset name (1.4); declared use **TIER GAP: TG-L1-009** | §2.3 |
| 6 | coverage obligations and their state | **TIER GAP: TG-L1-013** (no obligation list, no universe, no state assigned) | §2.4 |
| 7 | position in the order and three-way baseline | partly — level, edges and deployed figures supplied; code-head comparison **TIER GAP: TG-L1-004**; seed/pin **TG-L1-003** | §2.5, §4.1 |
| 8 | disposition and must-add list | evidence supplied (3.2); letter and must-add **TIER GAP: TG-L1-017** | §3.2, §3.3 |
| 9 | individual term | **absent instrument** (1.2); reach information only | §1.2 |
| 10 | synergistic term (which seam it sits on) | **absent instrument**; seam measurements (1.3); the shared-table seam for 10 assets (7 declared + 3) | §1.3 |
| 11 | cross-layer term (contract, evidence state) | partly — states 1 and 5 by contract group (1.4); 3, 4, 6 not measured | §1.4 |
| 12 | the preserved kernel | **TIER GAP: TG-L1-017**; grain and delete-scope facts supplied in 2.3 and TG-L1-006 as inputs, not as a declared kernel | §3.2 |
| 13 | the Jyotish concepts touched, each with its carriage check | **TIER GAP: TG-L1-015** (T4's "D3 dominates" hint only) | §2.7 |
| — | the asset's temporal or manifestation role (T3 §4.4 line 476) | four named in T2 §6.2; the rest **TIER GAP: TG-L1-018** | §0.3 |
| — | the epistemic type of each output (T2 §3.3) | **TIER GAP: TG-L1-020** | §0.2 |

---

## Part 5 · EVALUATION AND CERTIFICATION

### 5.1 · The score is ablation, in three flavours

```
inherits:    Product §14, §14.1; Data plane §12.2
measured_by: ablation deltas — none exist (absent instrument)
traces_to:   0.2
```

L1's 0.2 row names one obligation, Computational correctness. Individual, synergistic and cross-layer ablation are each **an absent instrument** for L1 (1.2–1.4). The reference-layer variant does not apply.

### 5.2 · What is certified, and what is merely checked

```
inherits:    Product §14; CLAUDE.md §N.6-N.8; the t3 lesson
measured_by: census_L1.json, 20 criteria per asset (370 cells over 19 assets); certification ledger asset_certs.jsonl — NOT written by this draft
traces_to:   4.4 — the gates are what an asset brief is certified against
```

This draft certifies nothing (status PROVISIONAL; "may register gaps, may not certify"). **Census cells for the layer** (count of assets per verdict per criterion; source: `census_L1.json` tallied by this run, with the one changed cell (`ga_prashna` `Build.completion`) taken from `census2/census_L1.json`; census2's log reads "FAIL 7 · PARTIAL/NO_DETECTOR 90 · ERRORED 0" (= PARTIAL 28 + NO_DETECTOR 62), whereas census1's `SUMMARY.md` read PARTIAL 27 · ERRORED 1: L1 FAIL 7 · PARTIAL 28 · NO_DETECTOR 62 · ERRORED 0 · PASS 232 · N/A 3 · NOT_GENERIC 38):

| criterion | cells | PASS | FAIL | PARTIAL | NO_DETECTOR | ERRORED | N/A | NOT_GENERIC |
|---|---|---|---|---|---|---|---|---|
| Build.registered | 19 | 19 | 0 | 0 | 0 | 0 | 0 | 0 |
| Build.contract | 19 | 19 | 0 | 0 | 0 | 0 | 0 | 0 |
| Idem.pattern | 19 | 19 | 0 | 0 | 0 | 0 | 0 | 0 |
| Build.target | 19 | 19 | 0 | 0 | 0 | 0 | 0 | 0 |
| Build.dag | 19 | 19 | 0 | 0 | 0 | 0 | 0 | 0 |
| Build.count_integrity | 19 | 19 | 0 | 0 | 0 | 0 | 0 | 0 |
| Build.completion | 19 | 14 | 4 | 1 | 0 | 0 | 0 | 0 |
| Build.exercised | 19 | 19 | 0 | 0 | 0 | 0 | 0 | 0 |
| Build.history | 19 | 0 | 1 | 18 | 0 | 0 | 0 | 0 |
| Build.dep_liveness | 19 | 18 | 0 | 0 | 0 | 0 | 1 | 0 |
| Earn.build_record | 19 | 0 | 0 | 0 | 19 | 0 | 0 | 0 |
| Cost.baseline | 19 | 0 | 0 | 0 | 19 | 0 | 0 | 0 |
| Count.floor | 19 | 16 | 2 | 0 | 0 | 0 | 1 | 0 |
| Complete.depth | 17 | 6 | 0 | 9 | 2 | 0 | 0 | 0 |
| Complete.width | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 19 |
| Vocab.identity | 17 | 15 | 0 | 0 | 2 | 0 | 0 | 0 |
| Reach.fields | 19 | 0 | 0 | 0 | 0 | 0 | 0 | 19 |
| Ldgr.source_presence | 13 | 13 | 0 | 0 | 0 | 0 | 0 | 0 |
| Dens.served | 19 | 17 | 0 | 0 | 1 | 0 | 1 | 0 |
| Carr.detector | 19 | 0 | 0 | 0 | 19 | 0 | 0 | 0 |

The four criteria families the plan calls information and never blocks (Cost, Count, Complete, Reach; D3) are listed above as measured; only the gate-bearing cells (Build, Idem, Ldgr, Vocab, Carr, Dens, Earn) count toward ELEVATED. **No `Null.*` or `Narr.*` cell exists in the census** (plan §2.1, "Today's gap"). Selected per-asset matrix:

| asset | Build.completion | Build.history | Count.floor | Complete.depth | Dens.served | Idem.pattern | Carr.detector | Complete.width |
|---|---|---|---|---|---|---|---|---|
| `ga_ayurdaya` | PASS | PARTIAL | PASS | PARTIAL | PASS | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_condition` | FAIL | PARTIAL | PASS | PARTIAL | PASS | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_dashas` | PASS | PARTIAL | PASS | PASS | PASS | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_medical` | PASS | PARTIAL | PASS | PASS | PASS | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_nakshatra` | PASS | PARTIAL | PASS | PARTIAL | PASS | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_panchanga` | PASS | PARTIAL | PASS | PARTIAL | PASS | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_positions` | PASS | FAIL | PASS | PARTIAL | PASS | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_prashna` | PARTIAL | PARTIAL | N/A | NO_DETECTOR | N/A | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_sade_sati` | PASS | PARTIAL | PASS | PARTIAL | PASS | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_sensitive` | PASS | PARTIAL | PASS | PARTIAL | PASS | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_sensitive_degree` | PASS | PARTIAL | PASS | PARTIAL | PASS | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_strength` | FAIL | PARTIAL | PASS | (no cell) | NO_DETECTOR | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_structural` | FAIL | PARTIAL | PASS | (no cell) | PASS | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_tajaka` | PASS | PARTIAL | PASS | PASS | PASS | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_transit_anchors` | PASS | PARTIAL | PASS | PASS | PASS | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_vargas` | FAIL | PARTIAL | FAIL | NO_DETECTOR | PASS | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_vastu` | PASS | PARTIAL | PASS | PASS | PASS | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_vichara` | PASS | PARTIAL | PASS | PASS | PASS | PASS | NO_DETECTOR | NOT_GENERIC |
| `ga_yoga` | PASS | PARTIAL | FAIL | PARTIAL | PASS | PASS | NO_DETECTOR | NOT_GENERIC |

**The gate map** (template §5.2, "fixed here, not re-derived"; nine rows, not eight: TG-L1-023). The right-hand column is the instance's fill. **TIER GAP: TG-L1-019** on granularity: each row asks for per-asset content, and this layer instance fills the layer-level facts and the cells the census, registry and code supply, leaving the rest to the A.L1 briefs.

| gate | section a brief author reads | what this instance supplies |
|---|---|---|
| **Ldgr** | §2.3 | the upstream `fact_id` sources per asset: **not supplied** — no `chart_facts` column holds upstream fact identifiers, `ga_positions` has no upstream fact edge, and the census's only Ldgr cell (`Ldgr.source_presence`, a provenance column populated: `citation_ref`, or `classical_citation` for `ga_medical` and `ga_vastu`, or `source_citation` for `ga_vichara`) is the reference-layer form: PASS 13, absent for 6 (**TIER GAP: TG-L1-021**, MF-L1-003) |
| **Idem** | §2.5, §4.1 | natural keys: `chart_facts`, `chart_dashas`, `chart_divisionals` as in 2.3 (from `_idempotency.py`), the seven `natural_key_partition` scopes in the registry for the `chart_facts` producers; the other assets' keys and each writer's delete scope on the shared table: **TIER GAP: TG-L1-006**. Census: PASS 19/19, a static pattern reading (MF-L1-004) |
| **Earn** | §2.4, §1.4 | emitted statuses that are claims: `verification_pass_status` (`chart_facts`, `chart_dashas`, `chart_divisionals`) with the vocabulary's own falsifiability rule (only `two_pass_verified` is grounding), and `asset_throughput.state` (`lit`); what would falsify `lit`: a live count that disagrees (`ga_vargas` is the observed case, LG-L1-002). Census `Earn.build_record` NO_DETECTOR 19/19 measures rate instrumentation, a different claim (MF-L1-007) |
| **Null** | §2.4 (state vocabulary); §1.4 | the tier rule (T1 §3.3, T2 DP04) and the code's `MissingnessState` and `floored` status; the per-asset convention for an underivable value is **not stated** (no `Null.*` criterion exists) |
| **Vocab** | §2.6 | the classes the asset owns or consumes: **TIER GAP: TG-L1-014**; the authority for the one measured field is `brahmagyan/verification_vocab.py` (L0) |
| **Carr** | §2.7; §4.4 row 13 | the (concept, check) pair per asset: **TIER GAP: TG-L1-015**; layer hint D3; NO_DETECTOR 19/19 |
| **Narr** | §2.2 | whether the asset emits prose: **not measured**; L1's design intent is prose-free (`gates.py` no-narration linter with forbidden patterns, wired only through `build_runner`, MF-L1-008); no `Narr.*` census criterion |
| **Dens** | §2.2; §3.4 served boundary | which served surface: per asset by census `Dens.served` (1.2), PASS 17, N/A 1, NO_DETECTOR 1; the seven `chart_facts` producers share one table-level attribution (MF-L1-002) |
| **Build** | §2.5; §1.1; §4.3 | writer file and registered id (build table in 1.1; `Build.registered` PASS 19/19), target (`Build.target` PASS 19/19, two by rule not by declaration), edges (2.5), build record (1.1); `Build.contract` PASS 19/19; `Build.completion` PASS 14 / FAIL 4 / PARTIAL 1; the runtime `dry_run` proof is not among the 20 census criteria |

### 5.3 · Certification is per criterion, not per definition revision

```
inherits:    the t3 lesson; asset_certs.jsonl's _schema line
measured_by: the certification record itself
traces_to:   —
```

No certification record is written by this draft. When the layer instance is accepted (A.L1a, N-10.L1.i), each certification is one record
`asset · criterion · criterion_version · detector · evidence · verdict · verified_by · verified_on` with the verdict in the closed set. Nothing here presumes it.

### 5.4 · Acceptance of the instance itself

```
inherits:    Template §5.4
measured_by: the six tests below, stated honestly
traces_to:   —
```

| test | status |
|---|---|
| 1 Derivability (a fresh-context reader derives one asset brief) | **not run**; §4.4 marks the rows that would force an invention |
| 2 Alignment (every section names `traces_to`) | author's pass done (0.4); a reviewer's pass not run |
| 3 Measured, not inherited (every figure names `measured_by`) | author's pass: each section carries the line; figures re-runnable from `census_L1.json`, the named queries and file:line; a reviewer's re-run not done |
| 4 Presentation parity | **[TRANSFERS]-pending** (TIER GAP: TG-L1-011): neither a pass nor a block |
| 5 The gate map exists | yes — nine rows in 5.2; its per-asset fill is partial by TG-L1-019 |
| 6 Independent review, fresh context | **not done**; **the instance carries no verdict**, and nothing may inherit from it until one is recorded |

---

## Part 6 · Corrections with gates

T3 §5.2 says "report unfillable rows in §7 as corrections with gates"; T3 has no §7 (R08), so this closing section carries them, as the L0 v3.0 draft did. Every entry names the gate it blocks; a correction with no named gate would default to blocking the next gate. Each is a **tier gap or a layer finding, not a defect of this document**, per T3 §5.4's distinction (a finding about the layer that the document correctly records is a work packet, not a document defect).

| id | what is unfillable | blocks |
|---|---|---|
| TG-L1-001 | P/V necessity | first asset brief, §0.1 row 1 |
| TG-L1-002 | L1-specific "computes what existing software does not" | none of the gates; the objective paragraph stands on T1/T2 quotation |
| TG-L1-003, -004 | seed/pin and code-head baseline | first asset brief, §0.1 row 7; the layer's certification of `Build.dag`'s completeness claim |
| TG-L1-005, -006, -007, -008 | shared-table ownership, natural key, kind, empty asset | first asset briefs for the ten `chart_facts` writers and `ga_prashna`; the `Idem` and `Build` gates |
| TG-L1-009, -011, -012 | declared use, consumer verification, parity, row assignment | first asset brief §0.1 rows 4–5; layer certification of §1.4 |
| TG-L1-010 | detector per correctness rule | first asset brief §0.1 row 3; `Ldgr`/switch claims |
| TG-L1-013, -014, -018, -020 | owned obligations, classes, role, epistemic type | first asset brief §0.1 rows 6 and the role row; `Vocab` gate |
| TG-L1-015, -022 | carriage pair per asset; where verification is required | the `Carr` gate; first asset brief §0.1 row 13 |
| TG-L1-016 | frozen definition revision, egate | the next instance revalidation (A.L1r) |
| TG-L1-017 | disposition rule, preserved kernel | A.L1 dispositions file; first asset brief rows 8 and 12 |
| TG-L1-019, -021, -023 | gate-map granularity, the L1 form of `Ldgr`, template references | the `Ldgr` gate; the instance's own acceptance test 5 |
| TG-L1-024 | which rows owe a unit | the units part of the correctness obligation (3.1); first asset brief §0.1 row 3 |
| LG-L1-001, -002 | `_telemetry` sites; `ga_vargas` empty with `lit` | the first build (`Build` and `Idem` gates) for `ga_vargas`; the layer's certification for the telemetry residual |
| MF-L1-012 (MF-L1-001 resolved by census2; its residual is TG-L1-008) | unmeasured generation tables (permission) | layer certification (an unmeasured cell is not PASS) |

No packet in 4.2 closes a delta item this draft cannot name, and no packet was struck; P7 is tier-dependent and waits on the tier rows it names.
