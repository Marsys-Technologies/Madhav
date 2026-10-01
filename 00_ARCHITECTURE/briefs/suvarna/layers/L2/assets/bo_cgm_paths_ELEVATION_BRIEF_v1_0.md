---
asset_id: bo_cgm_paths
layer: L2 Bodha (bo_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L2 (briefs, dispositions, designs)
census_revision_used: "after-grant census `00_ARCHITECTURE/briefs/suvarna/layers/census/after_reader_grant/census_L2.json` (generated 2026-09-30T20:30:56+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). It differs from the first run (`census/census_L2.json`, 20:23:30) in exactly six cells (bo_anveshana, bo_sangati, bo_upaya: Build.completion and Count.floor, ERRORED then). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L2/L2_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)"
base_commit: "main 3311b0a06"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
nirmana_freeze: "t1, 2026-09-09"
ledger_gap_ids: [bo_cgm_paths-Earn.build_record, bo_cgm_paths-Cost.baseline, bo_cgm_paths-Dens.served, bo_cgm_paths-Build.history, bo_cgm_paths-Carr.detector]
---
# bo_cgm_paths — CGM dispositor-chain paths

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

For each graha node per ayanamsha, follows the dispositor chain (graha → sign lord → its lord …) over the CGM edges until a self-ruling graha, a cycle or depth 9, emitting one `bodha_cgm_paths` row per distinct chain (`bo_cgm_paths.py` docstring). CONTRACT-3: `ph_nimitta._load_cgm_meta` reads `path_id`, `path_label_human`, `path_length`, `is_final_dispositor`, which therefore must be populated here. `@register("bo_cgm_paths")` at `bo_cgm_paths.py:360`, delete at `:384`, INSERT `_PATH_INSERT` (`:353`). 45 chart rows (floor 9 live; the seed says 5), 135 table-wide. `path_label_human` is composed (`:181`, `"{graha chain} (self-ruling / final dispositor)"`). Direct dependents `bo_chart_gestalt`, `bo_yantra_mechanism`, `ph_nimitta`. Frozen under the t1 definition (2026-09-09).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1789` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_cgm_paths.py:360`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_cgm_paths`; count_sql tables: `bodha_cgm_paths` | census CEN-R |
| live rows / floor | 45 / 9 (chart 482012f1, count_sql scope) | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bo_bimba`, `bo_karanajala` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 3 / transitive 20; seed-derived closure (post-1210): direct 3 / transitive 20; direct dependents: `bo_chart_gestalt`, `bo_yantra_mechanism`, `ph_nimitta` | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_cgm_paths`: 12 non-test py/ts/tsx files reference it (7 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `ph_nimitta.py`, `engine.py`, `instrument.ts`, `types.ts`, `query_cgm_paths.ts`, `tool_name_bridge.ts` +1 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | 1 capability module(s): `L2_bodha/query_cgm_paths.ts`; `density_contract` declared on 0 (saved rev-1 reading) | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t1, 2026-09-09; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 1a7889d2 complete/build (2026-09-09) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): bodha_cgm_paths (bo_cgm_paths.py:384) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served† | FAIL | 1 module(s): query_cgm_paths.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 17 error(s) and 7 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-07-16): BLOCKED: upstream dependency(ies) bo_bimba, bo_karanajala did not complete in this run; skipped to avoid building on incomplete data |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 1a7889d2 complete/build (2026-09-09) |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width 16/20 built column(s) (80.0%) selected by 1 capability module(s); dark: ['build_id', 'centrality_formula_version', 'chart_id', 'computed_at']; depth 100.0% (a capability query reads it with n… |

**PASS cells (compact):** Ldgr.source_presence (citation_ref populated on 135/135 rows); Vocab.identity (declared key (chart_id, ayanamsha_id, build_id, snapshot_type, path_type, from_node_id, to_node_id): 0 duplica…); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.completion (rows_written=45 = live=45 (count_sql over the target table; chart 482012f1)); Build.exercised (44 executed run(s) of 76 build_run_assets row(s), scope(s): asset_set, global, layer, last executed 2026-09-09); Build.dep_liveness; Count.floor (live=45, floor=9, delta=+36); Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **FAIL** — 1 module(s) reach it by code: L2_bodha/query_cgm_paths.ts; 2 served select(s) of its table; no referencing capability that serves it declares density_contract; a tier column is selected without a contract in: L2_bodha/query_cgm_paths.ts; Idem.pattern rev 2 reads **PASS**.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| `bo_cgm_paths-Dens.served` / census cell Dens.served † | Dens | real (rev 1 and offline rev 4) | 1 module `query_cgm_paths.ts`, 2 served selects, no `density_contract`; the offline rev-4 scan reads FAIL (a tier column is selected without a contract). The handler paginates by `limit` only (`:61`). FD-1; CF-04. |
| declarations `prose_fields: null` | Null, Narr | detector (declaration) | `path_label_human` is composed by f-string from the chain's graha names plus the stated property "self-ruling / final dispositor" (`bo_cgm_paths.py:181`); `citation_human` is a constant (`:350`). Whether the label counts as narration is the SS rule (structural member labels do not; the stated property is a computed one). Proposal: declare `["path_label_human"]` with the `:181` evidence, or `[]` if SS reads it as a structural label. CF-06. |
| registry seed text `asset_registry_seed.ts:1795-1798` | Complete (information) | stale | the seed's volume note ("only self-ruling zero-hop paths emit — bo_karanajala does not yet write dispositor-class edges") predates the live 40 `dispositor` edges (layer instance §2.2); live paths are 45 (9 per ayanamsha, one chain per graha). Whether multi-hop chains now emit is not measured here. CF-03 (description). |
| `bo_cgm_paths-Build.history` | Build (history) | history | latest run complete; 17 errors and 7 aborts on record (latest error 2026-07-16, `BLOCKED: upstream bo_bimba, bo_karanajala did not complete`). CF-10. |
| `bo_cgm_paths-Earn.build_record`, `-Cost.baseline`, `-Carr.detector` | Earn, Carr | detector | instrument absent / no D1-D3 detector; CF-05, CF-07. |

## 3 · Disposition

**keep (P)** — complete on the census (completion equals live, all 20 columns populated); the open items are the density declaration and a label declaration.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Declare the density contract on `query_cgm_paths.ts`

- **Answers:** Dens.served FAIL; CF-04
- **Change:** as for `bo_cgm_motifs` FD-1: `paginated: false` (limit only), `facets: ['ayanamsha_id','path_type','final_only']`, `empty_reason` only if backed by the handler
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L2_bodha/query_cgm_paths.ts`
- **Failing-first test and mutation:** response-shape test for the empty page and the truncated page; mutation: drop the declaration → Dens FAIL
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents); the change is local to this asset’s record or declaration unless the output change says otherwise
- **Rebuild:** none
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-dependent: TGH-T3-26 and N-22 applicability

### FD-2 · Narr golden-value test for the declared prose columns

- **Answers:** Narr gate (NO_DETECTOR); CF-14; Track A §5 (per-asset Narr golden tests)
- **Change:** golden fixture: a dispositor chain A → B → C (C self-ruling) → `path_label_human` states the same chain and the same self-ruling flag as `is_final_dispositor`; a looped chain must not be labelled final
- **Files / declaration / migration:** a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can find it; no asset or registry change
- **Failing-first test and mutation:** failing-first: the test fails on a writer whose narrated value differs from the cited fact; mutation: change one composed value (a house number, a count) in the writer → the test fails
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents); the change is local to this asset’s record or declaration unless the output change says otherwise
- **Rebuild:** none
- **Gate it moves:** Narr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent (SS ruling 2026-10-01 defines narration; declarations 1.6.0 exists)

### FD-3 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (re-derivation): recompute each graha's dispositor chain from the canonical sign-lord table and the graha signs in L1 `graha_position`, compare to `bodha_cgm_paths` (chain, length, finality); the traversal is closed-form so the check can be exact.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** as the §0 row (declared dependents); the change is local to this asset’s record or declaration unless the output change says otherwise
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* FD-1
- **CF-06** — prose_fields declarations for the L2 assets that have none (Null and Narr gates). *This asset:* `prose_fields` declaration (`path_label_human`)
- **CF-14** — Narr fidelity (golden-value) tests per L2 narration writer. *This asset:* fidelity test once declared
- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* seed description stale
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage D3 (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id, snapshot_type, path_type, from_node_id, to_node_id)` (registry partition). Fingerprint over endpoints resolved to node natural keys, `path_length`, `is_final_dispositor`, `path_strength` (product of constituent edge strengths, JL-013), `path_label_human`, `citation_ref`. **Volatile:** `path_id`, `build_id`, `computed_at`; the raw node-id endpoints. Expected 45 rows on the chart.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the dispositor-chain traversal with the stop rules (self-ruling, cycle, depth 9) and the product-not-average path strength.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation) (design in FD-3)
- **Opportunities (never blocking):** confirm whether multi-hop chains now emit; expose `centrality_formula_version` (dark).

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t1 on 2026-09-09 (NIRMANA_SUPERSESSION_RECORD §2.3). Migration 1210 added no edge to this row; any registry edit proposed in §4 (`count_sql`, `natural_key_partition`, `catalog_status`, `depends_on`, `integrity_check_sql`) enters `registryContractFingerprintInput` and would stale the manifest. The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3), so the staleness has no running consumer, but the frozen-definition DB row still reads `frozen`. **A production rebuild (SS REVIEW):** its direct dependents (`bo_chart_gestalt`, `bo_yantra_mechanism`, `ph_nimitta`) re-run after it in DAG order; seed-derived transitive closure 20 assets. Idempotent per-chart delete-then-insert; `ph_nimitta` (L4) reads these rows.

## 8 · Questions for Strategic Suvarṇa

1. CF-06: is a path label that states "self-ruling / final dispositor" narration (declare `path_label_human`) or a structural label (declare `[]`)?
