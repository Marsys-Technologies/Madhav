---
asset_id: bo_chart_gestalt
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
nirmana_freeze: "t2, 2026-09-10"
ledger_gap_ids: [bo_chart_gestalt-Earn.build_record, bo_chart_gestalt-Cost.baseline, bo_chart_gestalt-Build.history, bo_chart_gestalt-Build.dep_liveness, bo_chart_gestalt-Carr.detector]
---
# bo_chart_gestalt — Chart gestalt (pointers-only synthesis of the earlier Bodha assets)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

Reads the earlier Bodha assets and writes one row per chart per ayanamsha of **pointers**: defining threads (top chart-defining and major signals), central dynamics (strongest CDLM cells), center-of-gravity node ids, a domain verdict map, a headline, a watch list, contested areas, a zoom spine and outliers from the discoveries (`bo_chart_gestalt.py` docstring). Anti-drift is absolute: no verdict and no confidence are stored (SAMĀPTI B-N8-FIX / register F-12 removed `verdict_class` and `confidence`; F-17 added a real `balance_ratio` so "contested" is not mistaken for "balanced", `:466-474`). `@register("bo_chart_gestalt")` at `bo_chart_gestalt.py:661`, chart delete at `:685`. 5 chart rows (floor 1), 15 table-wide, 20 columns with 19 fully populated (`pivot_ids` never: "placeholder for CDLM §C3 pivot factor ids (populated when available)"). Served by `query_chart_gestalt.ts` (declares a contract). No registry dependents (0/0). Declared edges include `bo_cgm_paths` and `bo_anveshana`, both stale at the census. Frozen under the t2 definition (2026-09-10).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1853` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_chart_gestalt.py:661`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_chart_gestalt`; count_sql tables: `bodha_chart_gestalt` | census CEN-R |
| live rows / floor | 5 / 1 (chart 482012f1, count_sql scope) | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bo_laksana`, `bo_sangati`, `bo_bimba`, `bo_cgm_paths`, `bo_anveshana` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 0 / transitive 0; seed-derived closure (post-1210): direct 0 / transitive 0; direct dependents: none | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_chart_gestalt`: 6 non-test py/ts/tsx files reference it (5 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `instrument.ts`, `types.ts`, `query_chart_gestalt.ts`, `tool_name_bridge.ts`, `editorial.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | 1 capability module(s): `L2_bodha/query_chart_gestalt.ts`; `density_contract` declared on 1 (saved rev-1 reading) | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t2, 2026-09-10; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 46f6d80e complete/build (2026-09-10) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): bodha_chart_gestalt (bo_chart_gestalt.py:685) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Build | Build.history | PARTIAL | latest run complete, but 23 error(s) and 11 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-12): BLOCKED: upstream dependency(ies) bo_anveshana did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | PARTIAL | 3/5 declared dependencies lit at chart 482012f1 (or global); stale: ['bo_cgm_paths (stale, chart 482012f1)', 'bo_anveshana (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 46f6d80e complete/build (2026-09-10) |
| Complete (information) | Complete.depth | PARTIAL | 15 rows, 20 cols; fully populated 19; NEVER populated ['pivot_ids'] |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width 16/19 built column(s) (84.2%) selected by 1 capability module(s); dark: ['build_id', 'chart_id', 'computed_at']; depth 100.0% (a capability query reads it with no literal row pin (upper bound… |

Census emits **no cell** (absent, not N/A) for: Ldgr.source_presence (MF-L2-003, register R128).

**PASS cells (compact):** Vocab.identity (declared key (chart_id, ayanamsha_id): 0 duplicate(s)); Dens.served† (1 module(s): query_chart_gestalt.ts; declaring density_contract: 1); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.completion (rows_written=5 = live=5 (count_sql over the target table; chart 482012f1)); Build.exercised (36 executed run(s) of 91 build_run_assets row(s), scope(s): asset, asset_set, global, layer, last executed 202…); Count.floor (live=5, floor=1, delta=+4).

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **PARTIAL** — 1 module(s) reach it by code: L2_bodha/query_chart_gestalt.ts; a referencing capability declares density_contract but L2_bodha/query_chart_gestalt.ts: no tier column in its served select; Idem.pattern rev 2 reads **PASS**.

**Build.dag rev 2 (E6 g+h; recompute over the saved registry BEFORE migration 1210, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`, reads-match clause):** PASS (not in the recompute's L2 gate-diff list; no change from the saved rev-1 PASS) The saved census cell Build.dag PASS † above is the rev-1 reading.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| census cell Complete.depth (information) | Complete (information) | real (registry/column truth) | `pivot_ids` is NEVER populated: a column promised by the spec with no producer. Either a producer exists later (declare NULL-by-design with the owner) or the column is dropped from the contract; it must not read as a measured empty list. CF-17. |
| census: no `Ldgr.source_presence` cell (MF-L2-003) | Ldgr | detector | the table has no recognised citation column; every field is a pointer (signal/cell/node ids), which is the carriage. Declare the pointer columns as the carrying columns. CF-08. |
| declarations `prose_fields: null` (undeclared) | Null, Narr | detector (declaration) | the strings in the writer are constants (`verdict_note`, `:277`) or constants with an interpolated threshold (the contested `note`, `:466-474`, which also quotes a fixed example "136 vs 632, ratio 0.215"); proposal: declare `[]` with that evidence after reading the headline/watch-list builders for composed text. CF-06. |
| census cell Dens.served † (offline rev 4 PARTIAL) | Dens | real (rev 4 PARTIAL) | the contract is declared (`query_chart_gestalt.ts:63`) but the offline rev-4 scan finds "no tier column in its served select" (16 of 19 columns served). FD-1; CF-04. |
| `bo_chart_gestalt-Build.dep_liveness` | Build (dep_liveness) | history/ordering | 3 of 5 declared dependencies lit; `bo_cgm_paths` and `bo_anveshana` stale. CF-10 / §7. |
| `bo_chart_gestalt-Build.history` | Build (history) | history | latest run complete; 23 errors and 11 aborts on record (latest error 2026-08-12, `BLOCKED: upstream bo_anveshana did not complete`). CF-10. |
| `bo_chart_gestalt-Earn.build_record`, `-Cost.baseline`, `-Carr.detector` | Earn, Carr | detector | instrument absent / no D1-D3 detector; CF-05, CF-07. |

## 3 · Disposition

**keep (P)** — pointers-only by construction, complete on its columns apart from the one placeholder; the gaps are a column that no asset produces, a missing declaration and a tier column on the served select.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Carry a tier on the served select

- **Answers:** offline rev-4 Dens PARTIAL; CF-04
- **Change:** add the tier column the table carries (`verification_pass_status` if present, otherwise declare the tier through the descriptor) to the served select of `query_chart_gestalt.ts` so the declared contract is backed by a tier read
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L2_bodha/query_chart_gestalt.ts`
- **Failing-first test and mutation:** the rev-4 scan reads PASS; mutation: remove the column → PARTIAL
- **Output change:** none
- **Blast radius:** consumers of the `query_chart_gestalt` tool: `vidhi/inquiry/compiler.ts` and its acceptance corpus `beyond_acarya_acceptance.corpus.ts`, `retrieval/synthesis/instrument.ts`, `synthesis/surface_gateway.ts`, `registry/tool_name_bridge.ts`; one more selected column, no value changes
- **Rebuild:** none
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-dependent: TGH-T3-26 and N-22

### FD-2 · Settle `pivot_ids`

- **Answers:** Complete.depth NEVER populated; CF-17
- **Change:** declare `pivot_ids` as NULL-by-design with its future owner (CDLM §C3 pivot factors) in the column comment and the declaration, or remove the column from the contract if no owner exists; do not populate it with an empty array
- **Files / declaration / migration:** a column comment (migration) or the declarations file; no writer change
- **Failing-first test and mutation:** `Complete.depth` reads PASS or the column is declared; mutation: write `[]` into `pivot_ids` → the Null test flags a neutral default
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 0: none; transitive 0); the touched surface is a column comment (migration) or the declarations file
- **Rebuild:** none
- **Gate it moves:** Complete (information), Null
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent

### FD-3 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D2/D3 (pointer resolution and re-derivation): every pointed id must resolve to a row of the asset it names, and the per-domain evidence counts and the balance ratio must equal the counts recomputed from `bodha_msr_signals` valences.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 0: none; transitive 0); the touched surface is a new check in the Nikaṣa inspector tooling (Track E) registered for this asset
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-17** — Complete.depth: never-populated columns (declare, populate or drop). *This asset:* FD-2: `pivot_ids`
- **CF-08** — Ldgr: assets with no recognised citation column (no census cell). *This asset:* no Ldgr reading (pointer columns)
- **CF-06** — prose_fields declarations for the L2 assets that have none (Null and Narr gates). *This asset:* declare `[]` after reading the builders
- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* FD-1
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage D2/D3 (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL and stale upstream
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id)` (registry partition). Fingerprint: the pointer arrays and jsonb (`defining_threads_jsonb`, `central_dynamics_ids`, `center_of_gravity_node_ids`, `domain_verdict_map_jsonb`, `headline_jsonb`, `watch_list_jsonb`, `contested_areas_jsonb`, `zoom_spine_jsonb`, `outliers_jsonb`) with every id resolved to its target's natural key and arrays sorted where order is not meaningful (defining threads are ranked, so keep order). **Volatile:** `build_id`, `computed_at`, raw ids. Expected 5 rows.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the pointers-only discipline: no verdict, no confidence, no restated value; real per-domain evidence counts and a real balance ratio.
- **Carriage check chosen (T4 §4.1; one only):** D2/D3 (pointer resolution and re-derivation) (design in FD-3)
- **Opportunities (never blocking):** serve the zoom spine to L1 `fact_id` by default; fill `pivot_ids` when the CDLM pivot factors exist.

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t2 on 2026-09-10 (NIRMANA_SUPERSESSION_RECORD §2.3). Migration 1210 added no edge to this row. Manifest staleness has two severities (`src/lib/nirmana-elevation/definitions.ts:379-396`, `monitor.ts:374-393`): a `depends_on`, layer or membership change makes `assertManifestMatchesRegistryIdentity` throw (the monitor reports `plan_adaptation_required`; `dispatch_nirmana_campaign_wave.py` refuses the wave); a change to `count_sql`, `natural_key_partition`, `catalog_status`, `target_table` or `integrity_check_sql` only trips `assertManifestMatchesRegistry` (`evidence_refresh_required`: accepted evidence must be refreshed). The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3), so the staleness has no running consumer, but the frozen-definition DB row still reads `frozen`. **A production rebuild (SS REVIEW):** its direct dependents (none) re-run after it in DAG order; seed-derived transitive closure 0 assets. Idempotent per-chart delete-then-insert; terminal asset (no dependents). It must run after `bo_anveshana` and `bo_cgm_paths`, both stale at the census.

## 8 · Questions for Strategic Suvarṇa

1. FD-2: is `pivot_ids` to be declared NULL-by-design (owner: CDLM §C3) or removed from the contract?
