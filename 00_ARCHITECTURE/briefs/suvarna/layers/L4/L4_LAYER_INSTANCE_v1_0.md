---
artifact: SUVARNA_L4_LAYER_INSTANCE
canonical_id: SUVARNA_L4_LAYER_INSTANCE
tier: 3
kind: instance          # of LAYER_DEFINITION_AND_STRATEGY_TEMPLATE (SEALED); first draft
layer: "L4 Phala (asset prefix ph_, 9 assets)"
version: "1.1"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_on: 2026-09-30
produced_in: "Exec Suvarṇa"
lane: "A.L4i (analysis), branch suvarna/land/A.L4i-analysis-001"
census_run:
  output: /Users/Dev/suvarna-evidence/census/census_L4.json      # + census_L4.log, SUMMARY.md, same folder
  exit_code: 2                                                     # 2 = FAIL rows present = MEASURED (census SUMMARY.md); 4/5 would be unmeasured
  inspector_commit: 2a78ec64d88e59438bd6527b4c99826432102c57       # /Users/Dev/suvarna-census, detached at origin/campaign/nikasha-test
  chart_scope: 482012f1-710e-4a25-994a-93821f5871aa
  generated: "2026-09-30T20:23:50+05:30"
  runtime_seconds: 19
  assets_measured: 9          # = registry active population for layer phala (census_L4.json › L4.population_active)
inherits:
  - {tier: 1, path: 00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_FINAL.md, last_commit: 62b9c34ce}
  - {tier: 2, path: 00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_VALUE_ARCHITECTURE_FINAL.md, last_commit: 090bd9aaa}
  - {tier: 3 template, path: 00_ARCHITECTURE/briefs/nirmana/LAYER_DEFINITION_AND_STRATEGY_TEMPLATE_v1_0.md, last_commit: 090bd9aaa}
  - {tier: 4 template (context), path: 00_ARCHITECTURE/briefs/nirmana/ASSET_ELEVATION_TEMPLATE_v2_0.md, last_commit: 2289778be}
  - {register (cited, not restated), path: 00_ARCHITECTURE/briefs/nirmana/NIKASHA_CHANGE_REGISTER_v2_0.md, last_commit: 2a78ec64d}
tier_gaps: 00_ARCHITECTURE/briefs/suvarna/layers/L4/L4_TIER_GAPS_v1_0.md      # TG-L4-001 … TG-L4-025
inputs_not_authority: "nikasha_test/derivations/L4_INSTANCE_SKELETON.md and L4_INVENTIONS.md (2026-09-26) were read as inputs; every claim taken from them was re-checked against the tiers, the registry or the census (Appendix C)."
changelog:
  - "1.1 (2026-09-30): gate review corrections applied (independent Opus review 2026-09-30): 7 defects. Role column set to TG-L4-024 for all nine assets (T2 l.388 names all nine the Phala asset family; l.390 is an overlap-investigation list); T2 l.155 -> l.151; ph_pratikara DRAFT moved from must-add to an observation under TG-L4-006; the floor item moved from work packets to information/opportunity; the unsourced ph_pramana P12/V06 tie dropped. Tier-gap counts unchanged (25: T1 0 · T2 9 · T3 15 · T4 1)."
  - "1.0 (2026-09-30): first draft from the tiers and the census only. Sections the tiers do not supply are marked TIER GAP with the gap id; no content was invented to fill them. Every figure names its instrument and population. No certification is written (banner)."
---

# L4 Phala — layer instance (first draft)

> **PROVISIONAL — until J1; may register gaps, may not certify.** This instance is not accepted (T3 §5.4). Any
> asset brief derived from it is a pilot (T4 §0 pilot clause). Where a section reads **TIER GAP: TG-L4-nnn**, the tiers
> do not supply the clause; the row is in `L4_TIER_GAPS_v1_0.md` and nothing has been written in its place.

**Conventions used throughout.**
- *Population.* "the canonical chart" = 482012f1-710e-4a25-994a-93821f5871aa; "registry" = the live `asset_registry` read
  read-only as `suvarna_reader` on 2026-09-30 (layer `phala`, 9 active rows, none `dead_flag`); "census" =
  `census_L4.json`, generated 2026-09-30T20:23:50+05:30 by the inspector at 2a78ec64d; `asset_throughput` is read at the canonical
  chart; `information_schema` and `pg_constraint` are metadata reads; "code" = `platform/python-sidecar/**` at 2a78ec64d
  (the nine `ph_*` writer paths are byte-identical at origin/main e2352f881: `git diff --stat` empty).
- *Citations.* T1/T2/T3/T4/REG/T2c as in the tier-gaps file; census fields as `census › <asset> › <check>`.
- *Figures not read from a source are written "not measured", with the reason.*

---

## Part 0 · VALUE — the origin

### 0.1 · What cannot be answered without this layer

```
inherits:    Product §2 (P01-P24), Data plane §2 (V01-V13)
measured_by: none — definitional; every P/V cited was checked to exist under the parents' current numbering (T1 l.154–179; T2 l.115–129)
traces_to:   —  (this IS the origin)
```

**TIER GAP: TG-L4-001.** No tier assigns P-needs or V-journeys to a layer (T2 §2 maps V→P only). The register has re-scoped this section
(R221: "the catalog units this layer's assets produce or part-produce, and the layer's place in the necessity closure") but T3 is
unchanged in the checkout. The instance therefore lists (a) the rows where a tier clause itself ties the need to L4, and (b) rows tied only
by a concept name, with no necessity claim made.

**(a) Rows a tier clause ties to L4**

| P / V | the distinction that disappears without this layer | tier clause |
|---|---|---|
| P24 / V13 (the present interval) | What each active mechanism *means* in a stated life domain, as opposed to which mechanisms are active: "L3 owns the interval set and its boundaries; L4 owns the expression; neither may infer the other's half" | T2 §5 l.335; T2 §6.4 l.377–380 |
| P03–P04 / V02 (resources, business) | Receipts vs retained surplus; title vs authority vs workload vs pay: "The manifestation consumer then distinguishes nearer receipts from durable relief. If that distinction lacks a qualified rule, return a named gap—not a synthetic promise" | T2 §7.2 l.445; T2 §12.1 l.582; T1 §7.1 l.371–377 |

**(b) Rows tied to L4 assets by concept name only (T2 §6.5 l.392: "Electional/remedial/rectification assets keep their separate method and authority gates")** — no necessity claim:
P11 / V05 (timing context, attributed practices: T1 §3.11–§3.12) ↔ `ph_muhurta`, `ph_pratikara`; P13 / V07 (rectification as an explicit hypothesis
process, T1 P13 and §13) ↔ `ph_rectification`; No tie is drawn for `ph_pramana` (P12 / V06): the T2 l.392 quote covers only the electional, remedial and rectification assets, and the companion register (T2c) row for `ph_pramana` names no P or V.

Measured substitute for necessity, a DAG reading and not a P/V answer: `blocking_radius.transitive` per L4 asset = 11 (`ph_muhurta`), 17 (`ph_nimitta`),
9 (`ph_phaladesa`), 10 (`ph_pramana`), 11 (`ph_pratikara`), 0 (`ph_rectification`), 11 (`ph_sankrama`), 12 (`ph_sodhana`), 11 (`ph_suddha_sodhana`) — census › `blocking_radius`, "active assets depending on it, transitively, every layer".

### 0.2 · The layer's objective

```
inherits:    Product §1 (the join), §11 (this layer's row), Data plane §3.1 (this layer's row)
measured_by: none — definitional
traces_to:   0.1
```

**Owned question** (T2 §3.1 l.143): "What could that structure-in-time mean in the person's stated life domain?"
**Contribution handed onward** (same row): "Qualified manifestation alternatives, earned outcome propositions, falsifiers and action constraints."
**Must not claim** (same row): "Automatic certainty or calibration; a generic domain score as a specific outcome."
**Product responsibility and proof** (T1 §11 l.504): "Qualified manifestation and earned outcome interpretation"; proof "**Interpretive fidelity + Distinctive understanding** (§14): the explicit bridge from configuration and timing to named life distinctions; no unqualified composite score."
**The chain L4 completes** (T1 §7 l.362–369): formation and condition → eligible structural mechanism → applicable temporal activation → **qualified manifestation alternatives → earned external-outcome forecast**; "The chain may stop before the last link; say precisely where."
**How L4 behaves at the end of that chain** (T2 §6.5 l.388–392): distinguish named life expressions, competing manifestations, qualified support, falsifiers and permissible action; "the bridge requires a qualified operator and its limitations"; "L4 does not calibrate itself. If an affirmative, specific forecast is earned, emit it with the exact outcome and temporal scope. If not, retain the useful interpretation/activation and explain the absent bridge."
**One-way rule** (T2 §3.2 l.166): a chart-specific L4 conclusion "must not feed back into the L3 computation as independent evidence".

*What L4 computes that existing software does not:* **TIER GAP: TG-L4-002.** The product-wide differentiator (T1 §1 l.44–64: the whole estate and the relationships between its parts, then AI reading across it) is not restated here as an L4 claim.

### 0.3 · Its place in the wheel

```
inherits:    Data plane §3.2 (five edge types), §7 (DP contracts)
measured_by: registry depends_on reconciled across seed, migration pin AND live asset_registry — live registry measured (below); seed and migration pin NOT MEASURED (TG-L4-004: no tier defines them; the census reads the live registry only)
traces_to:   0.2
```

**Live registry, layer `phala`** — 41 declared `depends_on` edges: 19 intra-L4 and 22 inbound edges from 16 distinct assets (11 `bo_`, 8 `ka_`, 3 `ga_` edges); **0 edges to `bg_*`** although T2 §3.2 l.151 describes direct qualified L0 reference use by L4 (definition edges are not recorded in `depends_on`; TG-L4-003). Census `Build.dag` PASS ×9 with the same per-asset counts. All registry edges are computational edges (T2 §3.2 l.161: they follow the governed DAG); the other four edge types have no registry expression.

**Receives from (inbound, registry).**

| upstream asset (layer) | read by | note |
|---|---|---|
| `ka_sangam` (L3) | `ph_nimitta`, `ph_muhurta`, `ph_pratikara` | Saṅgam is a family asset (TRACK_A_BRIEF §6: campaign rule, not a tier) — briefs of these three record the family input and the D2 wait |
| `ka_gochara` (L3) | `ph_muhurta` | family asset |
| `ka_bhavishya_lekha`, `ka_kalasutra`, `ka_vighnakara` (L3) | `ph_nimitta` · `ph_muhurta` · `ph_muhurta`, `ph_pratikara` | |
| `bo_laksana` (L2) | `ph_nimitta`, `ph_sodhana`, `ph_phaladesa` | |
| `bo_sangati` (L2) | `ph_nimitta`, `ph_sankrama` | |
| `bo_anveshana`, `bo_bimba`, `bo_cgm_paths`, `bo_karanajala`, `bo_samskara` (L2) | `ph_nimitta` | |
| `bo_upaya` (L2) | `ph_pratikara` | |
| `ga_condition`, `ga_panchanga`, `ga_positions` (L1) | `ph_muhurta` | |

**Hands onward to (registry, active dependents of `ph_*`).** `mi_bhavisya` (L5) reads `ph_nimitta`, `ph_pramana`, `ph_phaladesa`; `mi_adhilepa` (L5) reads `ph_nimitta`; every other dependent is inside L4. **No L1, L2 or L3 asset depends on any L4 asset** (the one-way rule of T2 §3.2 l.166 holds at the edge level; it is not proof that no semantic feedback exists).

**DP contracts.** Tier text names L4 as consumer of DP01 (l.420, "all adapters and writers"), DP03 (l.422, "L2–L4/services"), DP04 (l.423, "L2/L3/L4") and DP09 (l.428, "→ L4"); as a producer, T2 §8 l.457 assigns every producer its DP10 duty (capability metadata about itself). Which contracts L4 *produces* to a downstream consumer, and the edge type of each: **TIER GAP: TG-L4-003** (DP09's own producer→consumer cell reads L3 → L4, while its fields describe L4's output). Declared use per consumed contract: **TIER GAP: TG-L4-013**.

**What the join needs from L4** (T2 §3.4 l.197, T2 §6.5): the manifestation bridge or its falsifier, carried, plus outcome subtype, competing expressions, constraints and temporal scope (DP09, l.428). The fields exist (§2.2); their reach is measured there.

### 0.4 · The alignment test

```
inherits:    (template)
measured_by: author self-run on this draft
traces_to:   0.1 / 0.2 / 0.3
```

Run by the author on this draft: every section from Part 1 carries a `traces_to` line and names a 0.1–0.3 item. Nothing was struck, because no section was added beyond
the template's; sections that cannot be filled are kept as marked gaps, not struck, so the hole stays visible. The reviewer runs it again (T3 §0.4).

---

## Part 1 · VALUE DECOMPOSITION

### 1.1 · Inventory, measured

```
inherits:    Data plane §13.3 item 2
measured_by: asset_registry (live, read-only, layer phala) · asset_throughput at the canonical chart · census_L4.json (inspector 2a78ec64d) · code at 2a78ec64d. Registry SEED and migration PIN: not measured (TG-L4-004). Production probe asset_elevation_tracker.py: not run (the census is the probe of record).
traces_to:   0.3
```

Nine assets, all writer-backed, all per-chart (`scope = per_chart`, `domain = chart`), no service asset, no shared table (C-10 verified refuted; tier-gaps §2.1). Kinds: **TIER GAP: TG-L4-006** (the registry says `asset_kind = artifact` on 9/9, `asset_type = data`; neither matches T3's or T4's kind list). `ph_pratikara` is `catalog_status = DRAFT`, the other eight `CURRENT`; no tier defines DRAFT or requires that it be resolved (observation under TG-L4-006, not a must-add).

| asset | writer (`@register` id, census `Build.registered` PASS ×9) | target table(s) | live rows, chart (`count_sql`) | registry `target_floor` | build record `rows_written` | `state` / last built (UTC) |
|---|---|---|---|---|---|---|
| `ph_nimitta` | `ph_nimitta.py` | `phala_anchors` | 4 | 139 | 139 | stale / 2026-08-13 01:16 |
| `ph_muhurta` | `ph_muhurta.py` | `phala_muhurta` | 134 | 134 | 139 | stale / 2026-08-13 01:16 |
| `ph_sodhana` | `ph_sodhana.py` | `phala_sodhana` | 0 | none | 97 | stale / 2026-08-13 01:16 |
| `ph_pratikara` | `ph_pratikara.py` | `phala_mitigation` | 536 | 536 | 536 | stale / 2026-08-13 01:16 |
| `ph_suddha_sodhana` | `ph_suddha_sodhana.py` | `phala_suddha_sodhana` | 4 | 139 | 139 | stale / 2026-08-13 01:16 |
| `ph_sankrama` | `ph_sankrama.py` | `phala_sankrama` | 155 | 2510 | 2510 | stale / 2026-08-13 01:16 |
| `ph_pramana` | `ph_pramana.py` | `phala_pramana` | 4 | none | 139 | stale / 2026-08-13 01:16 |
| `ph_phaladesa` | `ph_phaladesa.py` | `phala_phaladesa` | 13 | 13 | 13 | stale / 2026-08-13 01:16 |
| `ph_rectification` | `ph_rectification/__init__.py` (package) | `phala_rectification`, `phala_rectification_best` (a set) | 186 (185 + 1) | 186 | 186 | stale / 2026-08-13 01:16 |

Instruments: live rows = registry `count_sql` (chart-scoped) executed read-only; `rows_written`, `state`, last built = `asset_throughput` at the canonical chart; floors = `asset_registry.target_floor`. Census `Build.completion`: PASS ×3 (`ph_phaladesa`, `ph_pratikara`, `ph_rectification`), **FAIL ×6**; `Count.floor`: PASS ×4, FAIL ×3 (`ph_nimitta` −135, `ph_sankrama` −2355, `ph_suddha_sodhana` −135), no verdict on `ph_pramana` and `ph_sodhana` (no floor declared). The build record over-reports against the live table for six assets; the three assets recording **139 written against 4 present** are `ph_nimitta`, `ph_pramana`, `ph_suddha_sodhana` — detail and the foreign-key mechanism consistent with it in tier-gaps §2.3 (TG-L4-023).

**Columns and depth** (census `Complete.depth`; note its population is the whole table, not the chart — the two differ, e.g. `phala_anchors` 60 rows vs 4 at the chart):

| asset | table rows / columns | fully populated | NEVER populated |
|---|---|---|---|
| `ph_muhurta` | 183 / 24 | 21 | none |
| `ph_nimitta` | 60 / 37 | 29 | `subsystem_source`, `karmic_frame`, `karmic_note` |
| `ph_phaladesa` | 26 / 31 | 16 | `narration_requested_at`, `narration_model` |
| `ph_pramana` | 60 / 14 | 11 | `lel_entry_id`, `lel_entry_jsonb`, `linked_sodhana_id` |
| `ph_pratikara` | 1277 / 22 | 16 | `initiation_muhurta_ref`, `source_id` |
| `ph_rectification` | 370 / 13 | 11 | none |
| `ph_sankrama` | 630 / 26 | 24 | `mitigation_ref` |
| `ph_sodhana` | 41 / 14 | 13 | `leakage_class` |
| `ph_suddha_sodhana` | 60 / 16 | 10 | `revision_approved_by`, `revision_applied_at`, `magnitude_delta_if_applied` |

**Build history** (census `Build.exercised` PASS ×9; `Build.history` PARTIAL ×9 — "latest run complete, but N error(s) and M abort(s) on record"): errors/aborts `ph_muhurta` 26/9, `ph_nimitta` 27/9, `ph_phaladesa` 32/9, `ph_pramana` 29/9, `ph_pratikara` 26/9, `ph_rectification` 28/9, `ph_sankrama` 26/9, `ph_sodhana` 29/9, `ph_suddha_sodhana` 29/9. Census header: `global_runs` 61, `global_runs_touching_layer` 328 — as printed by the inspector; 328 exceeds 61 and the basis is not stated, so it is reported and not used.

**Current code vs deployed.** Partial (TG-L4-005): writers at 2a78ec64d and origin/main e2352f881 are byte-identical for the nine `ph_*` paths; other live heads, unmerged branches and the deployed writer version were not enumerated. **Contract fields live:** not measured (no `produces_contracts` columns; TG-L4-013).

**Residual code paths (not assets).** `brahmagyan/phala/rectification.py` and `brahmagyan/phala/mitigation.py` contain INSERTs into `phala_rectification` and `phala_mitigation` with column lists that do not match the live tables; the latter is reachable only from `pipeline/brahma_pipeline.py`, described in its own comment as a legacy pipeline with no live importer; `run_ka_sangam_prod.py` deletes `phala_anchors` rows by `anchor_source`. None is a live second producer (tier-gaps §2.1).

### 1.2 · Individual contribution — ablate one

```
inherits:    Product §14.1 (ablation), Data plane §12.2
measured_by: none — no ablation harness exists. "Unmeasurable — not reached" is the entry for every asset, per T3 l.181. What can be read instead: capability-module reach and DAG blocking radius (census), reported as readings not as contributions.
traces_to:   0.1 (which rows this asset serves)
```

Scoring flavour: **contribution** (chart-product layer; census `scoring: contribution`; T3 §1.2 reference-layer clause does not apply). Individual term for each of the nine: **unmeasurable — not reached**; no contribution is invented and no asset is recorded ≈ 0. Readings:

| asset | capability modules that read its table(s) (census `reach.modules`) | built / exposed / dark columns | width (exposed ÷ built) | blocking radius direct / transitive |
|---|---|---|---|---|
| `ph_nimitta` | `query_phala_calibration.ts`, `query_predictive_anchors.ts` | 34 / 25 / 9 | 0.735 | 10 / 17 |
| `ph_muhurta` | `query_phala_calibration.ts` | 24 / 13 / 11 | 0.542 | 2 / 11 |
| `ph_phaladesa` | `query_domain_result.ts` | 29 / 21 / 8 | 0.724 | 1 / 9 |
| `ph_pramana` | `query_phala_calibration.ts` | 11 / 8 / 3 | 0.727 | 2 / 10 |
| `ph_pratikara` | `query_phala_calibration.ts` | 20 / 15 / 5 | 0.750 | 2 / 11 |
| `ph_rectification` | `query_phala_calibration.ts` | 13 / 12 / 1 | 0.923 | 0 / 0 |
| `ph_sankrama` | `query_phala_calibration.ts` | 25 / 19 / 6 | 0.760 | 2 / 11 |
| `ph_sodhana` | `query_phala_calibration.ts` | 13 / 9 / 4 | 0.692 | 2 / 12 |
| `ph_suddha_sodhana` | `query_phala_calibration.ts` | 13 / 9 / 4 | 0.692 | 2 / 11 |

"Dark" = built but selected by no capability module (T4 §1.2: a reachability opportunity, recorded not blocking; the requirement itself is [TRANSFERS]). Census `Reach.fields` is NOT_GENERIC ×9 ("reported, not graded"). Two consumer maps disagree about which serving unit reads `ph_nimitta` and `ph_sankrama` (TG-L4-022): the catalog snapshot binds `ph_nimitta` to `scu.catalog.query_prashna_special_techniques` and `ph_sankrama` to `scu.catalog.query_planet_transit`.

### 1.3 · Synergistic contribution — ablate the group

```
inherits:    Data plane §3.4 (presentation contract), §7 (DP contracts), the layer's synergy binding if one exists
measured_by: none — absent instrument (no cross-layer ablation harness; T2 §3.5, T1 §1.3). Seam readings below are census/registry observations, not a synergy figure.
traces_to:   0.2
```

**Synergy term: absent instrument. No figure and no fraction is recorded** (T2 §3.5 l.235–237; T3 §1.5 l.249–251). Seam-by-seam readings, at the seams T2 §3.5 names:

- *Controlled vocabulary.* Census `Vocab.identity` PASS ×9 measures only rule 1(i) (declared-key uniqueness) and for 6 of 9 assets tests the surrogate primary key (TG-L4-025); `local_map_candidates` = −1; alias coverage, parity tests and interface-parameter census: not measured (TG-L4-016).
- *DP contracts.* Contract fields at both ends: not measured (TG-L4-013).
- *Edge ordering.* `Build.dag` PASS ×9. `Build.dep_liveness` PARTIAL ×9 ("built, but an upstream has moved since"): lit/declared = `ph_nimitta` 5/9, `ph_muhurta` 4/8, `ph_phaladesa` 1/7, `ph_pramana` 0/6, `ph_pratikara` 0/4, `ph_rectification` 0/1, `ph_sankrama` 1/2, `ph_sodhana` 1/2, `ph_suddha_sodhana` 0/2. `ph_nimitta` is itself stale against `ka_sangam`, `ka_bhavishya_lekha`, `bo_anveshana`, `bo_cgm_paths`, and every intra-L4 dependent lists `ph_nimitta` as stale.
- *Presentation contract.* The bridge/falsifier fields exist but most are dark (§2.2).

### 1.4 · Cross-layer handoff — what it produces for downstream

```
inherits:    Data plane §11 (six evidence states), §7 (DP contracts this layer PRODUCES)
measured_by: registry reverse `depends_on` (active assets) for the consumer list; the six-state position "verified at the consumer" is NOT MEASURED (TG-L4-022)
traces_to:   0.3 (hands onward)
```

| asset | direct dependents outside L4 (registry) | direct dependents inside L4 | evidence-state position |
|---|---|---|---|
| `ph_nimitta` | `mi_bhavisya`, `mi_adhilepa` | `ph_muhurta`, `ph_pratikara`, `ph_rectification`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`, `ph_pramana`, `ph_phaladesa` | not measured |
| `ph_pramana` | `mi_bhavisya` | `ph_phaladesa` | not measured |
| `ph_phaladesa` | `mi_bhavisya` | — | not measured |
| `ph_muhurta`, `ph_pratikara`, `ph_sankrama`, `ph_suddha_sodhana` | none | `ph_pramana`, `ph_phaladesa` (both read all four) | not measured |
| `ph_sodhana` | none | `ph_suddha_sodhana`, `ph_pramana` | not measured |
| `ph_rectification` | none | none | not measured |

T2 §9.1 l.491 records that `ph_nimitta` and `mi_bhavisya` "produce rebuildable candidates, not protected issuance history"; the protected issuance sits at L5 (DP15a). A pure producer is not thereby retirable (T3 §1.4 l.223); no disposition is drawn here.

### 1.5 · The accounting

```
inherits:    —
measured_by: 1.2 + 1.3 + 1.4 against 0.2 — not computable: the three terms are absent instruments
traces_to:   0.2
```

No sum can be formed: the individual term is unmeasurable (1.2), the synergy term is an absent instrument (1.3), the cross-layer term is unverified at the consumer (1.4). The elevation delta is therefore itemised in Part 3 from **measured shortfalls against the nine gates** and from the tiers' own statements, not from a value shortfall. No asset is a candidate for R or H on value grounds. The one asset with no dependent in the registry, `ph_rectification` (blocking radius 0/0), is read by a capability module and is fenced by T1 §13 l.577 ("No automatic rectification") and T2 §6.5 l.392 (separate method and authority gate); that is a note, not a candidate call. Synergy fraction: not recorded (no harness).

---

## Part 2 · CONDITIONS UNDER WHICH THE VALUE IS REAL

### 2.1 · Correctness rules

```
inherits:    Product §8.1 (this layer's row), §13; Data plane §9.2 (the switch and the storage separation)
measured_by: a detector per rule — none exists for any rule below (census Carr.detector NO_DETECTOR ×9); the structural readings noted are edge- or column-level, not detectors
traces_to:   0.2 — the value is real only if these hold
```

| # | rule (verbatim or near-verbatim) | source | detector | current reading |
|---|---|---|---|---|
| C1 | L4 must not: "Rewriting the original forecast to fit the eventual story" | T1 §8.1 l.426 | **none** — TIER GAP: TG-L4-008 (no L4 object is "the original forecast"; L4 rows are rebuildable candidates, T2 §9.1 l.491; every L4 writer is delete-then-insert per chart, census `Idem.pattern` PASS ×9) | not measured |
| C2 | "No invented computation, source, detector, confidence, empirical score, or claim of exhaustive coverage" | T1 §13 l.566–569 | none per asset (`Carr.detector` NO_DETECTOR ×9; TG-L4-017) | not measured |
| C3 | L4 "does not calibrate itself"; no "automatic certainty or calibration"; "no unqualified composite score"; "intensity is not event probability" | T2 §6.5 l.392, §3.1 l.143, DP09 l.428; T1 §11 l.504 | **none** — TIER GAP: TG-L4-019 | code gate only in `ph_pramana` (eight forbidden field names); score-bearing columns in five L4 tables; see §2.1a |
| C4 | A chart-specific L4 conclusion must not feed back into the L3 computation as independent evidence | T2 §3.2 l.166 | none (semantic); an edge-level reading exists | registry: 0 L1/L2/L3 assets depend on any `ph_*` asset (measured, edge level only) |
| C5 | "No automatic rectification, no outcome-driven personal tuning" | T1 §13 l.577–578 | none | `phala_rectification_best` carries `auto_action`, `native_adopted`, `adopted_at`, `leakage_firewall_note` (information_schema); their content is not analysed here |
| C6 | "A rebuild must not reset chronology: re-stamping emission time turns a frozen claim into a hindsight leak" | T1 §7.3 l.390–392; DP15a l.434 | none in L4 (applies at issuance, L5) | L4 rows carry `computed_at` / `scored_at` (`DEFAULT now()`), re-stamped on every per-chart rebuild (registry notes); T2 §9.1 makes them candidates, not issued claims |

**The life-event switch** (T1 §8 l.401–414; T2 §9.2 l.498–517). ON, L4 (T1 §8.1 l.426): "Refine manifestation distinctions; preserve exact forecast outcome definitions"; T2 l.500: "L4 manifestation distinctions". OFF: "Nothing derived from life events, anywhere … No life events appear in any inquiry surface"; the switch state travels "in the emission record beside the information cutoff" (T2 l.500–501). Storage separation: "event-conditioned overlays are kept separate from event-free structural and temporal products" so OFF is a selection, not a rebuild (T2 l.510–512). **TIER GAP: TG-L4-009** for which L4 tables are overlays. Observed, not a tier statement: `ph_pramana.py` and `ph_rectification/__init__.py` are the only two of the nine writer files that read `life_events`; no `phala_*` table has a switch-state or cutoff column (information_schema). Measured layer finding (not a tier gap): `ph_pramana`'s LEL read is unscoped by chart while the live `life_events.chart_id` is `NOT NULL` (tier-gaps §3 item 2).

#### 2.1a · The NO-SCORING constraint and the `ph_pramana` gate

How the tiers express it, clause by clause, is in tier-gaps §2.2: layer-level only, three strengths, no asset-level clause, no detector, no gate among the nine; "D5" is in no tier. Measured, recorded without resolving: `phala_pramana` (14 columns) carries none of the eight names its writer's D5 gate forbids; `phala_anchors.posterior` is populated on 4 of 4 chart rows and `lift_vector_jsonb`, `magnitude`, `confidence_low`/`confidence_high` are populated 4 of 4; `phala_muhurta` has `panchanga_score`, `chart_personalization_score`, `personal_adversity_penalty`, `composite_quality` (`composite_quality`, `panchanga_score` and `chart_personalization_score` are each populated on 134 of 134 chart rows; `personal_adversity_penalty` was not counted); `phala_sankrama` has `linkage_strength`, `asymmetry_score`, `spillover_confidence`; `phala_rectification` has `lel_fit_score`, `phala_rectification_best` `best_lel_fit_score`. Whether any of these is a "composite score", a "probability" or a "structural confidence" in the tiers' sense is not decidable from the tiers (T1 §5.2 l.324–326 says probability, comparative grade, timestamp and reliability statement are "different objects" but no clause types these columns). The companion register's phrase for `ph_pramana` is "retain hard no-scoring" and for `ph_nimitta` "Structural confidence not probability" (T2c, not a tier).

### 2.2 · Presentation obligation

```
inherits:    Product §2 (two modes, one depth); Data plane §3.4 (the field → contract mapping)
measured_by: producer-field presence (information_schema) and reach (census reach.exposed/dark). The presentation-parity test itself is [TRANSFERS] (T2 §1 l.83–85, §12.2 l.614) and is NOT run and NOT claimed here (TG-L4-010).
traces_to:   0.1 — the acharya rows are unservable if these fields are not carried
```

**Row carried.** T2 §3.4 l.197: "the clock geometry, the activation rule, the named nearest-versus-better-supported criterion, and the manifestation bridge or its falsifier → DP07 clocks/contacts, DP08 temporal mechanism, DP09 manifestation". L4's share is the manifestation bridge or falsifier and the competing readings (T2 §6.5). Which of the other §3.4 rows L4 carries or hands onward: **TIER GAP: TG-L4-012**. Whether the bridge/falsifier is L4's or a temporal layer's row: **TIER GAP: TG-L4-011** (T3 §2.2 l.283–286 puts it under temporal layers; T3 Adapting l.683 and T4 l.508 put it at L4). This instance follows the L4-side texts and flags the conflict.

**Fields present, and their reach** (information_schema; census `reach`):

| §3.4 content | table › column | reach |
|---|---|---|
| falsifier (text) | `phala_anchors.falsifier`; `phala_sankrama.falsifier`; `phala_pramana.falsifier_text` | exposed |
| falsifier (structured), observable criteria | `phala_anchors.structured_falsifier_jsonb` · `phala_pramana.observable_criteria_jsonb` | **dark** · exposed |
| manifestation bridge / mechanism | `phala_anchors.causal_chain_jsonb` · `phala_sankrama.bridge_path_jsonb`, `cascade_chain_jsonb`, `mechanism_text` | **dark** · **dark**, **dark**, exposed |
| competing readings, contradictions, counterfactual | `phala_anchors.contradiction_jsonb`, `counterfactual_jsonb`, `school_consensus_jsonb`, `precedent_refs_jsonb` · `phala_phaladesa.contradiction_summary_jsonb`, `precedent_refs_jsonb` | all **dark** |
| method robustness (school, ayanāṃśa, dasha consensus) | `phala_anchors.ayanamsha_robustness`, `dasha_consensus_count` | exposed |
| derivation ledger (every L4 table except `phala_rectification*`) | `derivation_ledger_jsonb` | **dark** on 8 of 8 tables that carry it |
| intermediate quantities of the election | `phala_muhurta.panchanga_snapshot_jsonb`, `tarabala_chandrabala_jsonb`, `significators_met_jsonb` | **dark** |
| prose | `phala_phaladesa.narration_jsonb` | **dark** (`narration_requested_at`, `narration_model` never populated) |

By T4 §1.2 l.172–176 dark fields are recorded as reachability opportunities and do not block until the retrieval plane has its own artefact. The presentation claim this instance can make is only "producer fields present and located"; end-to-end parity and the delivery sentinel are **[TRANSFERS]-pending** (the D3 ruling's wording, REG R71).

### 2.3 · Contracts produced and consumed

```
inherits:    Data plane §7 (DP01-DP17), §7.1 (common envelope)
measured_by: registry depends_on (edges); fields and grain at both ends NOT MEASURED (census does not read fields against contracts; TG-L4-013)
traces_to:   0.3
```

**Produced by L4.**

| contract | consumer (tier text) | fields/grain/identity/generation |
|---|---|---|
| DP10 capability metadata about itself | registry / investigator / build consumers (T2 l.429; §8 l.457) | census `Reach.fields` and `Dens.served` are the only readings; declared `density_contract` = 0 on all three serving modules |
| DP09 "Manifestation" | named as L3 → L4 in T2 l.428 | **TIER GAP: TG-L4-003** (fields are L4's output; producer→consumer cell reads the other way) |
| any other L4 → downstream contract | — | **TIER GAP: TG-L4-003**; registry shows `mi_bhavisya` and `mi_adhilepa` as readers (§1.4) with no declared use |

**Consumed by L4.**

| contract (tier text) | producer | declared use |
|---|---|---|
| DP01 identity/release | L0 → all adapters and writers (l.420) | **TIER GAP: TG-L4-013** |
| DP03 chart facts | L1 → L2–L4 (l.422); registry edges from `ga_condition`, `ga_panchanga`, `ga_positions` into `ph_muhurta` | TG-L4-013 |
| DP04 condition decomposition | L1 → L2/L3/L4 (l.423) | TG-L4-013 |
| DP09 (as consumer) | L3 + qualified structural/rule evidence (l.428); registry edges from `ka_*` (8) and `bo_*` (11) | TG-L4-013 |

The nineteen intra-L4 edges are within-layer computational edges (§3.4).

### 2.4 · Jyotish coverage owned

```
inherits:    Product §3 (substance), Data plane §5 (domain obligations)
measured_by: per obligation the five states; the only measured coverage evidence is census Complete.depth (populated columns) and Complete.width (NOT_GENERIC ×9: "no declared universe for this asset")
traces_to:   0.1
```

**TIER GAP: TG-L4-014.** T2 §5 names L4 in three of its thirteen rows and assigns no owner or state: graha roles ("→ L4 domain-specific interpretation", l.327); present interval ("expression … is L4", l.335); ayurdaya ("→ L4 expression, with the tradition's own caveats preserved at every hop", l.338). The bala row (l.329) bars "universal favourability or probability conversion" without naming a layer. Concepts whose T1 clause fits L4's manifestation work by wording — yoga/doṣa manifestation (T1 §3.7), Muhūrta (§3.11), remedies (§3.12), Kāla manifestation (§3.10) — are listed for the harvest, not claimed. No obligation is given a state here, and none is asserted **applied**: a populated column is not application (T2 l.341). Width: no declared universe for any of the nine (R22). Depth: §1.1 (never-populated columns).

### 2.6 · Vocabulary conformance

```
inherits:    Data plane §4.1 (the controlled vocabulary — six rules with detectors)
measured_by: census Vocab.identity (rule 1(i) only); local_map_candidates (−1 = not computed); alias coverage, parity test presence, interface-parameter census: NOT MEASURED
traces_to:   0.2 — the value is real only if the layer speaks the plane's one language
```

**TIER GAP: TG-L4-016** — no tier maps the sixteen entity classes (T2 l.268–270) to L4. Observation from the schema, not a tier assignment: L4 columns that name an entity class include `domain` (13-member canonical domain vocabulary, CHECK-constrained on `phala_phaladesa` per the registry note; `phala_anchors.domain`; `phala_sankrama.source_domain`/`target_domain`), graha (`afflicting_graha`, `personalization_graha`, `hora_lord`), ayanāṃśa (`ayanamsha_id`, `ayanamsha_robustness`), daśā (`dasha_consensus_count`), tradition/remedy (`tradition_options_jsonb`, `program_jsonb`). Census: `Vocab.identity` PASS ×9 on rule 1(i); 6 of 9 test the surrogate key (TG-L4-025); at the registry-declared natural keys the canonical chart has 0 duplicate groups in all nine tables (read-only counts). Rules 1(ii), 2, 3, 4, 5, 6: not measured.

### 2.7 · Source carriage and reproduction — did we transmit it faithfully?

```
inherits:    Product §11; Data plane §12.2 (Source carriage and reproduction), §4.3, §5
measured_by: the three checks (a source correspondence · b witness carriage · c independent re-derivation) — none has a detector for any L4 asset (census Carr.detector NO_DETECTOR ×9)
traces_to:   0.1 — a layer that corrupts what it carries serves no P-need
```

**TIER GAP: TG-L4-017 (C-9 confirmed for L4).** The check is assigned per obligation (T3 l.358), the brief needs it per asset (T3 §4.4 l.477–478; T4 §0.1 row 13), and nothing produces the per-asset table. The nine cells below stay open. The "concept" column names what the asset is described as carrying in T2 §6.5/T2c (companion, PROPOSED) — it is a label for the harvest, not a tier assignment:

| asset | concept named (T2 §6.5 / T2c) | carriage check ∈ {a/D1, b/D2, c/D3} | detector | result |
|---|---|---|---|---|
| `ph_nimitta` | manifestation anchors, mechanisms, contradictions, precedents, falsifiers | TG-L4-017 | none | NO_DETECTOR |
| `ph_muhurta` | electional windows (tāra/candra, lord resolution, obstruction) | TG-L4-017 | none | NO_DETECTOR |
| `ph_pratikara` | sequenced, conflict-aware mitigation programmes | TG-L4-017 | none | NO_DETECTOR |
| `ph_sankrama` | cross-domain spillover and competing effects | TG-L4-017 | none | NO_DETECTOR |
| `ph_sodhana` | detectors for inflated confidence, absent falsifiers/derivation, contamination | TG-L4-017 | none | NO_DETECTOR |
| `ph_suddha_sodhana` | usable/caveated/revision-staged anchor disposition | TG-L4-017 | none | NO_DETECTOR |
| `ph_rectification` | staged birth-time candidates and discrimination gate | TG-L4-017 | none | NO_DETECTOR |
| `ph_pramana` | observable criteria/falsifiers, window states, evidence links | TG-L4-017 | none | NO_DETECTOR |
| `ph_phaladesa` | per-domain overview of top anchor, contradictions, spillovers, action availability | TG-L4-017 | none | NO_DETECTOR |

L4's proof obligations (T1 §11: Interpretive fidelity + Distinctive understanding) have no linked carriage check in T3 §2.7's `inherits` (l.333 names L0 and L1 only); recorded in TG-L4-017.

### 2.5 · Edges and order

```
inherits:    Data plane §3.2; the registry DAG
measured_by: topological sort of the LIVE registry depends_on over the nine ph_* assets (derived here; no cycle); seed and pin readings not measured (TG-L4-004); egate and the frozen definition revision NOT AVAILABLE (TG-L4-015)
traces_to:   0.3
```

Intra-L4 build order (longest-path levels over the 19 intra-L4 edges; no cycle):

| level | assets |
|---|---|
| 0 | `ph_nimitta` |
| 1 | `ph_muhurta`, `ph_pratikara`, `ph_rectification`, `ph_sankrama`, `ph_sodhana` |
| 2 | `ph_suddha_sodhana` (needs `ph_sodhana`, `ph_nimitta`) |
| 3 | `ph_pramana` (needs `ph_nimitta`, `ph_sankrama`, `ph_muhurta`, `ph_pratikara`, `ph_sodhana`, `ph_suddha_sodhana`) |
| 4 | `ph_phaladesa` (needs `ph_nimitta`, `ph_muhurta`, `ph_pratikara`, `ph_suddha_sodhana`, `ph_sankrama`, `ph_pramana`, `bo_laksana`) |

Cross-layer gates: T3 asks for `egate.sql` scoped to "the CURRENT frozen definition revision" — **TIER GAP: TG-L4-015**, no gate evaluated. Edge type of every edge: computational (registry `depends_on`); the other four types are not recorded in the registry. Liveness of upstream at the canonical chart: §1.3 (`Build.dep_liveness` PARTIAL ×9). The census does not test T4 §4.2 check 4's last clause ("the declared edges match what the asset actually reads"): not measured.

---

## Part 3 · THE DELTA

```
inherits:    —
measured_by: 1.5's shortfall, itemised — here itemised from measured gate shortfalls (census) and tier statements, because the value terms are unmeasured
traces_to:   0.2
```

### 3.1 · Per obligation

T1 §11 l.504 scores L4 on two of the ten obligations; the other eight are not L4's row.

| obligation (T1 §14 l.590–591) | required evidence (T1) | where L4 stands, measured | what closes the gap |
|---|---|---|---|
| Interpretive fidelity | "Material rivals, qualified manifestation bridge, counter-evidence, dependence accounting, and no unsupported prose added after synthesis" | **not measured — no instrument** (TG-L4-018; T2 §12.2 l.629: tests "are planned"). Fields that would carry rivals, bridge and counter-evidence exist and are mostly dark (§2.2) | an instrument per obligation (TG-L4-018); reach of the dark fields ([TRANSFERS]) |
| Distinctive understanding | "Correct useful distinctions against competent simpler baselines, on ordinary as well as dramatic cases, with added errors counted alongside added insight" | **not measured — no ablation harness** (TG-L4-007) | the harness (T3 §1.5: "a packet") |

### 3.2 · Per asset — disposition

```
inherits:    Data plane §10.1 (P I E Q C H R U)
measured_by: TIER GAP — no evidence→disposition rule (TG-L4-007). The codes below are the companion register's provisional ones (T2c, status PROPOSED), carried with T2 §6.5, and are NOT verdicts.
traces_to:   0.2
```

| asset | provisional code (T2c) | with what T2/T2c says | census evidence that bears on it (not a rule) |
|---|---|---|---|
| `ph_nimitta` | P/E/I/Q | "proposition/event-class-specific joins instead of unordered first class per domain; include method key. Structural confidence not probability. DP09" | `Build.completion` FAIL 139 vs 4; `Count.floor` FAIL |
| `ph_muhurta` | P/I/Q/E | "preserve actual tāra/candra and lord resolution; deferred transit factor 0.5 and 400-anchor cap must be explicit. DP07/09" | `Build.completion` FAIL 139 vs 134 |
| `ph_pratikara` | P/I/Q | "L2 owns prescriptions; retain topological/conflict feasibility while binding actual obstruction/domain/window; no efficacy proof from source. DP09" | `catalog_status` DRAFT; `Build.completion` PASS |
| `ph_sankrama` | P/I/Q | "source-window fallback not independent timing; preserve uncovered-domain/missing-gradient states. DP06/08/09" | `Build.completion` FAIL 2510 vs 155; `Count.floor` FAIL |
| `ph_sodhana` | P/I/Q | "preserve build-halt checks; a clean label alone does not prove all upstream lineage. DP09/15" | `Build.completion` FAIL "empty: live=0"; 97 recorded |
| `ph_suddha_sodhana` | P/I/Q | "preserve D43 no-auto-approval; corrections bind immutable consumed revisions, no silent issued-claim repair. DP09/16" | `Build.completion` FAIL 139 vs 4; `Count.floor` FAIL |
| `ph_rectification` | P/E/Q/H | "preserve original event precision rather than fixed month-exact; exposure/history-conditioned hypotheses cannot silently drive event-free forecast. DP14/17" | reads `life_events`; `Build.completion` PASS 186 = 186 |
| `ph_pramana` | P/E/I/Q | "retain hard no-scoring; subject-scope event lookup and separate criteria from event matching. Domain history is not complete observation coverage. DP09/14/15" | `Build.completion` FAIL 139 vs 4; LEL read unscoped by chart at 2a78ec64d |
| `ph_phaladesa` | P/I/Q | "preserve overview; hydrate complete material evidence; event-informed fields require purpose-aware serving. DP09/10/12" | `Build.completion` PASS 13 = 13; `narration_jsonb` dark |

**Consolidation.** T2 §6.5 l.390: "Investigate overlaps among `ph_phaladesa`, `ph_nimitta`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana` and `ph_pramana` by exact responsibility and consumers before deciding consolidation." That is an instruction to investigate, so **C is a candidate for those six, not a disposition**; no consolidation is proposed. No asset receives R (T2 §10.1 l.541: "No asset receives unconditional R in this master").

### 3.3 · Per asset — what it must add

The list an asset brief's "exact delta" inherits, restricted to what a tier, the companion register or a measured shortfall supports:

| asset | must add (source) |
|---|---|
| all nine | a `Carr` check and a named concept (TG-L4-017); an honest-null convention and prose flag for the Null/Narr gates (TG-L4-020); `density_contract` declarations on the serving modules — ownership open (TG-L4-021, [TRANSFERS]); a declared width universe (TG-L4-014, R22); the `Earn` instrument (R55, migration 1094) |
| `ph_nimitta`, `ph_pramana`, `ph_suddha_sodhana`, `ph_muhurta`, `ph_sankrama`, `ph_sodhana` | reconcile the build record with the live table, with the cause classified (TG-L4-023) — `Build.completion` FAIL ×6 |
| `ph_nimitta` | the T2c delta above; a stated place for `posterior` and the confidence columns against C3 (TG-L4-019); the dark bridge/counter-evidence fields (§2.2) |
| `ph_pramana` | subject-scoped LEL lookup (T2c) — the measured code/schema disagreement (tier-gaps §3 item 2) |
| `ph_rectification` | a `Ldgr` reading (the gate applies always, T3 l.531): no `source_citation` column exists, so census `Ldgr.source_presence` has no row for it |

### 3.4 · Intra-layer interplay

```
inherits:    Data plane §7, §3.2
measured_by: registry depends_on (asset level); fields and use per edge NOT MEASURED (TG-L4-013)
traces_to:   0.2 (where the synergistic term is built or found missing)
```

Reads (consumer ← producers, intra-L4): `ph_muhurta` ← `ph_nimitta`; `ph_pratikara` ← `ph_nimitta`; `ph_rectification` ← `ph_nimitta`; `ph_sankrama` ← `ph_nimitta`; `ph_sodhana` ← `ph_nimitta`; `ph_suddha_sodhana` ← `ph_nimitta`, `ph_sodhana`; `ph_pramana` ← `ph_nimitta`, `ph_sankrama`, `ph_muhurta`, `ph_pratikara`, `ph_sodhana`, `ph_suddha_sodhana`; `ph_phaladesa` ← `ph_nimitta`, `ph_muhurta`, `ph_pratikara`, `ph_suddha_sodhana`, `ph_sankrama`, `ph_pramana`. This is the chain T2 §6.5 l.390 wants ("a coherent publication chain, not multiple wrappers"): `ph_nimitta` (anchors) → the five level-1 assets → `ph_suddha_sodhana` → `ph_pramana` → `ph_phaladesa`. Input/output/use per edge: TIER GAP TG-L4-013.

**A second dependence that is not in `depends_on`: foreign-key cascade.** `phala_anchors.convergence_id` → `kala_convergence` ON DELETE CASCADE; `phala_sodhana.anchor_id`, `phala_suddha_sodhana.anchor_id`, `phala_pramana.anchor_id`, `phala_sankrama.source_anchor_id` → `phala_anchors` ON DELETE CASCADE (pg_constraint). Rows of five L4 tables can therefore be removed by an L3 asset's rebuild or delete without any L4 writer running. `phala_muhurta.linked_anchor_id`, `phala_mitigation.linked_anchor_id` and `phala_anchors.bhavishya_id` are SET NULL; `phala_rectification*.chart_id` cascade from `charts`. Boundary with adjacent layers: L3 inbound (family assets `ka_sangam`, `ka_gochara` included), L5 outbound (`mi_bhavisya`, `mi_adhilepa`).

---

## Part 4 · STRATEGY

### 4.1 · Order

```
inherits:    2.5
measured_by: the DAG (2.5); the three-way baseline per asset — deployed measured, current code partly, target not yet written
traces_to:   0.2
```

Order = the levels of §2.5, upstream before downstream, cross-layer gates honoured as far as they can be stated (TG-L4-015). Within a level nothing constrains order; no learning-value ordering is asserted (no basis in the tiers).

| level | asset | deployed (canonical chart) | current code | target |
|---|---|---|---|---|
| 0 | `ph_nimitta` | 4 rows, stale, last built 2026-08-13; floor 139 | writer identical at origin/main e2352f881; other heads not enumerated (TG-L4-005) | the asset brief (A.L4, not yet written) |
| 1 | `ph_muhurta` | 134, stale | same | same |
| 1 | `ph_pratikara` | 536, stale, DRAFT | same | same |
| 1 | `ph_rectification` | 186 (185 + 1), stale | same | same |
| 1 | `ph_sankrama` | 155, stale; floor 2510 | same | same |
| 1 | `ph_sodhana` | 0, stale | same | same |
| 2 | `ph_suddha_sodhana` | 4, stale; floor 139 | same | same |
| 3 | `ph_pramana` | 4, stale | same | same |
| 4 | `ph_phaladesa` | 13, stale | same | same |

Delta = target − current code (not computable: no target); risk = current code − deployed (not measured beyond the byte-identity above). The two are different numbers and both are open.

### 4.2 · Work packets

```
inherits:    Data plane §13.1, §13.3 item 8
measured_by: each packet's proof — a detector that fails when the packet has not landed
traces_to:   3.x — every packet closes a named delta item
```

Candidates only, each tied to a measured delta item; none is authorised here, and whether each is tier-independent or tier-dependent is the A.L4 designs' work.

| packet (candidate) | closes | proof (detector that fails until it lands) |
|---|---|---|
| Reconcile build records and live rows, classifying the cause | §3.3 (`Build.completion` FAIL ×6; TG-L4-023) | census `Build.completion` PASS, with the cause classified |
| Per-asset carriage check and concept table | §2.7 (TG-L4-017) | `Carr.detector` ≠ NO_DETECTOR |
| Type the score-bearing L4 columns against C3 | §2.1a (TG-L4-019) | a detector that can report a violation |
| Natural-key authority and detector target | §2.6 (TG-L4-025) | `Vocab.identity` tests the declared natural key |
| Null and Narr gates | §5.2 (TG-L4-020) | a check row for each in the census |
| Declare width universes | §2.4 (TG-L4-014) | `Complete.width` ≠ NOT_GENERIC |
| Dens declarations on the three serving modules | §5.2 (TG-L4-021) | `Dens.served` PASS — ownership open, [TRANSFERS] |

*Information / opportunity, not a packet.* `ph_pramana` and `ph_sodhana` declare no `target_floor`, so census `Count.floor` gives no verdict for them (§1.1). Count is a non-gate criterion, information only (D3; Track A brief §5), and no tier requires a floor; whether to declare one is a choice for the asset brief, not a tier-derived delta.

### 4.3 · Generation, invalidation, rollback

```
inherits:    Data plane §11, §4.4, DP16
measured_by: generation pins each consumer records — NOT MEASURED; the invalidation path exercised — NOT EXERCISED (described here only); pg_constraint for the cascade paths
traces_to:   2.1 — a rebuild that resets chronology is a hindsight leak
```

Measured: all nine builds are `stale` at the canonical chart. Every L4 rebuild is a per-chart delete-then-insert (N.3), so `computed_at`/`scored_at` are re-stamped; T2 §9.1 makes L4 rows candidates, the protected claim is L5's. The only invalidation path that actually moves L4 rows is the foreign-key cascade in §3.4, which is not a DP16 dependency-specific stale marking. Generation pins per consumer (`mi_bhavisya`, `mi_adhilepa`): not measured. Rollback: none stated in the tiers for L4 rows. Whether DP16 covers a foreign deletion: TG-L4-023.

### 4.4 · What each asset brief inherits

```
inherits:    Product §16 (what every brief states); Data plane §13.3 (asset brief sentence)
measured_by: derivability — a brief author must be able to fill these from this instance alone
traces_to:   0.1
```

T3 §4.4 lists twelve inherited bullets and T4 §0.1 thirteen rows (the counts differ, TG-L4-024); both are filled below at layer scope. "TG" = not derivable from this instance.

| # | item | layer-scope value |
|---|---|---|
| 1 | P-needs and V-journeys | §0.1 (a) two rows; (b) concept-name ties; rest TG-L4-001 |
| 2 | obligations scored on | Interpretive fidelity + Distinctive understanding (T1 §11 l.504); ten, not eleven |
| 3 | correctness rules and switch | §2.1 C1–C6, switch as stated; detectors and overlay classification TG-L4-008, -009, -019 |
| 4 | presentation fields | §2.2; row assignment TG-L4-011, -012; parity [TRANSFERS]-pending |
| 5 | contracts produced/consumed, with declared use | §2.3; TG-L4-003, -013 |
| 6 | coverage obligations and states | §2.4; TG-L4-014 |
| 7 | position in order, three-way baseline | §2.5, §4.1; TG-L4-005, -015 |
| 8 | disposition and must-add | §3.2 (provisional), §3.3; TG-L4-007 |
| 9 | individual term | unmeasurable — not reached (§1.2) |
| 10 | synergistic term | absent instrument (§1.3) |
| 11 | cross-layer term | §1.4; evidence state not measured (TG-L4-022) |
| 12 | preserved kernel | per asset below (T2c "Preserve" column, provisional) |
| 13 | Jyotish concepts and carriage check | §2.7; TG-L4-017 |
| — | role (T3 bullet "manifestation or temporal role"; T4 header field) | below; TG-L4-024 |

**Role and preserved kernel per asset.** T4's role vocabulary is manifestation | temporal | neither (T4 §0 l.76; T3 §4.4 l.476, "its manifestation or temporal role"). No tier assigns the role value per asset: T2 §6.5 l.388 calls all nine assets "the Phala asset family"; l.390 lists six (`ph_phaladesa`, `ph_nimitta`, `ph_sankrama`, `ph_sodhana`, `ph_suddha_sodhana`, `ph_pramana`) only to be investigated for overlap (and calls `ph_sodhana` / `ph_suddha_sodhana` "purification/provenance kernels"); l.392 says electional/remedial/rectification assets (`ph_muhurta`, `ph_pratikara`, `ph_rectification`) "keep their separate method and authority gates". That list and that sentence are context, not a role assignment, so the role is **TIER GAP: TG-L4-024** for all nine assets.

| asset | role | preserved kernel (T2c "Preserve: contribution to the story", provisional, quoted) |
|---|---|---|
| `ph_nimitta` | TG-L4-024 | "Rich manifestation anchors with mechanisms, contradictions, precedent and falsifiers." |
| `ph_muhurta` | TG-L4-024 | "Personalized election windows using calendar, natal Moon/condition and obstruction." |
| `ph_pratikara` | TG-L4-024 | "Sequenced, conflict-aware mitigation programs." |
| `ph_sankrama` | TG-L4-024 | "Cross-domain spillover and competing effects via CDLM paths/windows." |
| `ph_sodhana` | TG-L4-024 | "Real detectors for inflated confidence, absent falsifiers/derivation and declared contamination." |
| `ph_suddha_sodhana` | TG-L4-024 | "Usable/caveated/revision-staged anchor disposition." |
| `ph_rectification` | TG-L4-024 | "Staged birth-time candidates and discrimination gate, no automatic chart mutation." |
| `ph_pramana` | TG-L4-024 | "Observable criteria/falsifiers, window states and historical evidence links." |
| `ph_phaladesa` | TG-L4-024 | "Per-domain overview of top anchor, contradictions, spillovers and action availability." |

---

## Part 5 · EVALUATION AND CERTIFICATION

### 5.1 · The score is ablation, in three flavours

```
inherits:    Product §14, §14.1; Data plane §12.2
measured_by: ablation deltas — none exist (absent instrument)
traces_to:   0.2
```

L4 is a chart-product layer scored on **contribution** (individual flavour: ablation of one asset; synergistic: a shared contract, vocabulary or ordering; cross-layer: L4's produced contract at the consumer). The subset of the ten obligations is two (T1 §11 l.504; §3.1 above). No flavour has an instrument; nothing is scored.

### 5.2 · What is certified, and what is merely checked

```
inherits:    Product §14; CLAUDE.md §N.6-N.8; the t3 lesson (certification is expensive to re-earn)
measured_by: the census verdicts below (a machine reading, not a certification record); no record is written to asset_certs.jsonl by this instance
traces_to:   4.4 — the gates are what an asset brief is certified against
```

**Gate map, filled** (T3 l.572–582; the middle column is what the census reads for L4; the right column is what the instance supplies, or the gap):

| gate | census reading for the nine (census_L4.json) | the instance supplies |
|---|---|---|
| **Ldgr** | `Ldgr.source_presence` PASS ×8 ("source_citation populated on N/N rows"); no row for `ph_rectification` (no `source_citation` column). `fact_id` resolution: not measured | upstream `fact_id` sources per asset: TG-L4-013. The `derivation_ledger_jsonb` column exists on 8 of 9 tables and is dark on all (§2.2) |
| **Idem** | `Idem.pattern` PASS ×9 ("DELETE FROM the asset's own table(s) (delete-then-insert)") | natural key per asset, from the registry `natural_key_partition` (table below); authority for it: TG-L4-025 |
| **Earn** | `Earn.build_record` NO_DETECTOR ×9 (instrument absent, migration 1094; `asset_throughput.duration_seconds` confirmed absent in production) | which emitted states are claims and what would falsify each: TG-L4-014 |
| **Null** | no check row | the asset's own null convention: TG-L4-020 |
| **Vocab** | `Vocab.identity` PASS ×9 (rule 1(i) only; 6 of 9 on the surrogate key) | classes owned/consumed: TG-L4-016 |
| **Carr** | `Carr.detector` NO_DETECTOR ×9 | TG-L4-017 |
| **Narr** | no check row | prose flag: TG-L4-020; `ph_phaladesa` has narration columns (`narration_jsonb`) |
| **Dens** | `Dens.served` FAIL ×9 (`density_contract` declared on 0 of the serving modules) | ownership of the fix: TG-L4-021 |
| **Build** | `Build.registered`, `Build.contract`, `Build.target`, `Build.dag`, `Build.count_integrity` PASS ×9; `Build.completion` PASS ×3 / FAIL ×6; `Build.exercised` PASS ×9; `Build.history` PARTIAL ×9; `Build.dep_liveness` PARTIAL ×9. Runtime state (`ctx.dry_run`): not measured | writer, registered id, target, edges, build record: §1.1, §2.5; cause of completion FAIL: TG-L4-023 |

**Natural keys declared in the registry** (`natural_key_partition`, chart-scoped duplicate groups measured 0 for all nine):

| asset | declared natural key | census "declared key" (`Vocab.identity`) |
|---|---|---|
| `ph_nimitta` | `anchor_id` (the table's primary key, `phala_anchor_identity()`) | `anchor_id` |
| `ph_muhurta` | `(chart_id, action_class, window_start)` | `muhurta_id` (surrogate) |
| `ph_sodhana` | `(anchor_id, anomaly_type, detected_field)` | `sodhana_id` (surrogate) |
| `ph_pratikara` | `(chart_id, obstruction_id, intensity_tier)` | `mitigation_id` (surrogate) |
| `ph_suddha_sodhana` | `(chart_id, anchor_id)` | `entry_id` (surrogate) |
| `ph_sankrama` | `(chart_id, source_anchor_id, cdlm_cell_id, target_domain, relationship_type)` | same five columns |
| `ph_pramana` | `(chart_id, anchor_id)` | `pramana_id` (surrogate) |
| `ph_phaladesa` | `(chart_id, domain)` | `phaladesa_id` (surrogate) |
| `ph_rectification` | `(chart_id, offset_minutes, ayanamsha_id)`; `phala_rectification_best (chart_id)` | `(chart_id, offset_minutes, ayanamsha_id)` |

**Census tallies for the layer** (all 177 measurement cells, `census_L4.json`): PASS 89 · FAIL 18 · PARTIAL 25 · NO_DETECTOR 27 · NOT_GENERIC 18 · ERRORED 0. Layer FAIL by check: `Build.completion` 6, `Count.floor` 3, `Dens.served` 9. These agree with the run's `SUMMARY.md` row for L4.

*(b) Brief shape and (c) ladder position* are per-asset and unchanged from T3 §5.2; not written here.

### 5.3 · Certification is per criterion, not per definition revision

```
inherits:    the t3 lesson; asset_certs.jsonl `_schema`
measured_by: the certification record itself — none written
traces_to:   —
```

**No certification record is written.** The instance is PROVISIONAL (banner); the census verdicts above are readings. Nothing in this file is to be read as PASS, ELEVATED or ACCEPT.

### 5.4 · Acceptance of the instance itself

```
inherits:    (template)
measured_by: the six tests of T3 §5.4
traces_to:   —
```

| test | status |
|---|---|
| 1 Derivability (fresh reader derives one brief; zero inventions) | **not run**. The rows the tiers do not supply are exactly the TG-L4 list |
| 2 Alignment | author self-run (§0.4); reviewer's run pending |
| 3 Measured, not inherited | every figure carries an instrument and population in its section's `measured_by` or its table note; figures not measured are marked; a reviewer should re-run the read-only queries and the JSON reads |
| 4 Presentation | [TRANSFERS]-pending; fields carried, parity not claimed (TG-L4-010) |
| 5 The gate map exists | yes, §5.2 (nine rows; T3 l.629 says "eight-row", REG R67) |
| 6 Independent review | **not done**; verdict: none. Gate ACCEPT is required before anything inherits from this file |

**Unfillable rows (T3 l.585 says report them "in §7"; T3 has no §7, REG R08).** The 25 tier gaps are those rows: TG-L4-001 to -025 in `L4_TIER_GAPS_v1_0.md`. By T3 l.663–665 a correction with no named gate blocks the next gate — here the first L4 asset brief (A.L4). None is claimed closed.

---

## Appendix A · Census reading by asset (census_L4.json, inspector 2a78ec64d; PASS P, FAIL F, PARTIAL Pt, NO_DETECTOR ND, NOT_GENERIC NG, — = no row)

| check | nimitta | muhurta | sodhana | pratikara | suddha | sankrama | pramana | phaladesa | rectification |
|---|---|---|---|---|---|---|---|---|---|
| Build.registered / contract / target / dag / count_integrity | P | P | P | P | P | P | P | P | P |
| Idem.pattern | P | P | P | P | P | P | P | P | P |
| Build.completion | F | F | F | P | F | F | F | P | P |
| Earn.build_record / Cost.baseline | ND | ND | ND | ND | ND | ND | ND | ND | ND |
| Count.floor | F | P | — | P | F | F | — | P | P |
| Complete.depth | Pt | P | Pt | Pt | Pt | Pt | Pt | Pt | P |
| Vocab.identity | P | P | P | P | P | P | P | P | P |
| Reach.fields / Complete.width | NG | NG | NG | NG | NG | NG | NG | NG | NG |
| Ldgr.source_presence | P | P | P | P | P | P | P | P | — |
| Dens.served | F | F | F | F | F | F | F | F | F |
| Build.exercised | P | P | P | P | P | P | P | P | P |
| Build.history / Build.dep_liveness | Pt | Pt | Pt | Pt | Pt | Pt | Pt | Pt | Pt |
| Carr.detector | ND | ND | ND | ND | ND | ND | ND | ND | ND |

## Appendix B · The 139-against-4 figures

See `L4_TIER_GAPS_v1_0.md` §2.3 (exact per-asset figures, instruments and the foreign-key evidence). Assets: `ph_nimitta`, `ph_pramana`, `ph_suddha_sodhana` — `rows_written` 139, live 4 each at the canonical chart.

## Appendix C · The earlier skeleton, re-checked (input, not authority)

| skeleton statement (2026-09-26) | re-check |
|---|---|
| `registered_ids` 8; `ph_rectification` `Build.registered` FAIL (inspector false positive) | now 9 and PASS (REG R43 closed; census › `registered_ids` 9) |
| every P/V row invented | still a gap (TG-L4-001); two rows now cited where a tier clause names L4 (§0.1 a) |
| no parent states L4's switch behaviour | partly wrong: T2 §9.2 and T1 §8.1 state ON/OFF; the per-asset overlay classification is missing (TG-L4-009) |
| §4.4 has no role row (R192) | inexact: T3 §4.4 l.476 has a role bullet; T4 §0.1 omits it and counts thirteen (TG-L4-024) |
| C-10 refuted for L4 | verified against tiers, registry and code (tier-gaps §2.1); the nearby real defect is the foreign-key cascade |
| C-9 confirmed for L4 | confirmed (`Carr.detector` NO_DETECTOR ×9) |
| `ph_muhurta` count_integrity PASS vs completion N/A | now consistent: `Build.completion` FAIL 139 vs 134 |
| `Build.dep_liveness` FAIL ×9; `Earn`/`Cost` FAIL | now PARTIAL ×9; NO_DETECTOR ×9 (R45; R55/D6) |
| `Dens.served` FAIL on 5 of 9 (in its [TRANSFERS] paragraph) | 9 of 9 |
