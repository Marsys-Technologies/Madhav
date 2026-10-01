---
asset_id: bo_cdlm_summary
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
decisions_applied: "SS decision N-59 (2026-10-01) on DECISION_SHEET_L2_v1_0.md (PR #2841); items marked (R) provisional until J1; section 8 lists the rulings for this asset"
track_i_items: [TI-L2-02, TI-L2-10, TI-L2-13, TI-L2-14]
ledger_gap_ids: [bo_cdlm_summary-Build.completion, bo_cdlm_summary-Earn.build_record, bo_cdlm_summary-Cost.baseline, bo_cdlm_summary-Complete.depth, bo_cdlm_summary-Build.history, bo_cdlm_summary-Carr.detector]
---
# bo_cdlm_summary — CDLM chart summary (per-chart cross-domain aggregate)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

Aggregates `bodha_cdlm_cells` (written by `bo_sangati`) into one row per chart per ayanamsha in `bodha_cdlm_chart_summary`: total linkage, dominant and weakest three domains, contradiction density, bridge and asymmetric link counts, strongest pair and a domain connectivity map; "ANTI-DRIFT: references `bodha_cdlm_cells` — never invents values" (`bo_cdlm_summary.py` docstring). It also writes `bodha_cdlm_domain_rollups` and `bodha_cdlm_pattern_clusters` (`:433-435`, `:456-458`) and returns the sum of the three tables (`:464`). `@register("bo_cdlm_summary")` at `bo_cdlm_summary.py:409`. 5 chart rows (floor 1). No registry dependents (0/0) and, by the census `Reach.fields`, no capability module reads the table by name, although `query_cdlm_summary.ts` serves it through a table map (`chart_summary: …`, `:36`; declaration `read_kind: table_map`). Frozen under the t1 definition (2026-09-09).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1753` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_cdlm_summary.py:409`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_cdlm_chart_summary`; count_sql tables: `bodha_cdlm_chart_summary` | census CEN-R |
| live rows / floor | 5 / 1 (chart 482012f1, count_sql scope) — count_sql counts `bodha_cdlm_chart_summary` (5); the writer also writes rollups and pattern clusters | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bo_sangati` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 0 / transitive 0; seed-derived closure (post-1210): direct 0 / transitive 0; direct dependents: none | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_cdlm_chart_summary`: 5 non-test py/ts/tsx files reference it (3 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `query_cdlm_summary.ts`, `tool_name_bridge.ts`, `source_query_availability.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | none by the census (`Reach.fields` 0 modules);  | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t1, 2026-09-09; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run a5b0eef1 complete/build (2026-09-09) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): bodha_cdlm_chart_summary (bo_cdlm_summary.py:433) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Build | Build.completion | FAIL | build record rows_written=70 disagrees with live=5 (count_sql over the target table; chart 482012f1) |
| Build | Build.history | PARTIAL | latest run complete, but 16 error(s) and 8 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-07-16): BLOCKED: upstream dependency(ies) bo_sangati did not complete in this run; skipped to avoid building on incomplete data |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run a5b0eef1 complete/build (2026-09-09) |
| Complete (information) | Complete.depth | PARTIAL | 15 rows, 23 cols; fully populated 19; NEVER populated ['dynamic_system_id', 'dynamic_maha_lord', 'dynamic_antar_lord', 'tradition_view_id'] |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width 0/19 built column(s) (0.0%) selected by 0 capability module(s); dark: ['asymmetric_link_count', 'ayanamsha_id', 'bridge_link_count', 'build_id', 'chart_id', 'chart_typology_class', 'citation_… |

**PASS cells (compact):** Ldgr.source_presence (citation_ref populated on 15/15 rows); Vocab.identity (declared key (chart_id, ayanamsha_id, build_id, snapshot_type, dynamic_system_id, dynamic_maha_lord, dynamic_a…); Dens.served† (1 module(s): query_cdlm_summary.ts; declaring density_contract: 1); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.exercised (41 executed run(s) of 76 build_run_assets row(s), scope(s): asset_set, global, layer, last executed 2026-09-09); Build.dep_liveness; Count.floor (live=5, floor=1, delta=+4).

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build FAIL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **NO_DETECTOR** — 1 module(s) reach it by code: L2_bodha/query_cdlm_summary.ts, but no served `SELECT ... FROM` its table was found (no served select): whether it is served cannot be told by code; Idem.pattern rev 2 reads **PASS**.

**Build.dag rev 2 (E6 g+h; recompute over the saved registry BEFORE migration 1210, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`, reads-match clause):** PASS (not in the recompute's L2 gate-diff list; no change from the saved rev-1 PASS) The saved census cell Build.dag PASS † above is the rev-1 reading.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| `bo_cdlm_summary-Build.completion` | Build (completion) | real (attribution; cause read in code, not measured) | build record 70 vs live 5. The writer returns summary + rollups + clusters (`:464`) and `count_sql` names the summary table only; 65 more is consistent with 13 domains × 5 ayanamshas of rollup rows (not verified; the two extra tables are unreadable to the census login, MF-L2-002). CF-02. |
| census cells Dens.served † (PASS) vs Reach.fields (0 modules) | Dens | detector | MF-L2-013: the saved rev-1 Dens PASS reads `query_cdlm_summary.ts` (declares a contract), while `Reach.fields` finds no module reading the table; the offline rev-4 scan reads NO_DETECTOR ("no served SELECT … FROM its table was found") because the served read goes through a table map. The two instruments disagree about whether this asset is served; the declaration (`served_surface: true`, `read_evidence query_cdlm_summary.ts:36`) is the settled statement. CF-04 (detector must read the table-map pattern). |
| census cell Complete.depth (information) | Complete (information) | information | 15 rows table-wide, 23 columns, 19 fully populated; NEVER populated `dynamic_system_id`, `dynamic_maha_lord`, `dynamic_antar_lord`, `tradition_view_id` (L3-dynamic hooks, NULL by design at L2). CF-17. |
| `bo_cdlm_summary-Build.history` | Build (history) | history | latest run complete; 16 errors and 8 aborts on record (latest error 2026-07-16). CF-10. |
| `bo_cdlm_summary-Earn.build_record`, `-Cost.baseline`, `-Carr.detector` | Earn, Carr | detector | instrument absent / no D1-D3 detector; CF-05, CF-07. |
| census: Null/Narr | Null, Narr | detector | `prose_fields = [citation_human]`: the pattern-cluster citation embeds the cell count (`:391`); the domain-rollup string is a pointer and the summary string a constant (AST census 2 composed, 1 constant). CF-14. |
| `bo_cdlm_summary-Ldgr.source_presence` | Ldgr | information | `citation_ref` populated on 15/15 rows; PASS. |

## 3 · Disposition

**keep (P)** — an aggregate over another asset's table with every column it computes populated; the shortfalls are an attribution mismatch and a detector disagreement, not content.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Record the produced-table set so completion compares like with like

- **Answers:** Build.completion FAIL; CF-02
- **Change:** declare the three produced tables (`bodha_cdlm_chart_summary`, `bodha_cdlm_domain_rollups`, `bodha_cdlm_pattern_clusters`) as this asset's produced set and have the completion check compare `rows_written` against the chart-scoped count over that set (option A of CF-02); `count_sql` is left as it is (it names the one summary table; migration 326 does not mention this asset)
- **Files / declaration / migration:** `asset_declarations.json` needs a SCHEMA EXTENSION first: version 1.6.0 has no produced-tables field (unlike `cross_asset_writes`, which exists), so a new field (for example `produced_tables`) plus its validator in `asset_census.py`/`test_e6_1_declarations.py` must land before the declaration can be made; then `asset_census.py` Build.completion reads it (Track E)
- **Failing-first test and mutation:** failing-first: `rows_written` (70) equals the count over the declared set on a fixture and differs when one rollup row is deleted; mutation: remove the declaration → FAIL
- **Output change:** none
- **Blast radius:** declarations file and detector only; no asset, registry row or consumer changes (this asset has no registry dependents: 0 direct / 0 transitive)
- **Rebuild:** none
- **Gate it moves:** Build (completion)
- **Fix class:** declarations schema + detector/tooling; **buildable before J1:** tier-dependent: needs the declarations-schema extension, T4 §4.2 check 6 wording and the produced-set vocabulary (TGH-T2-05)

### FD-2 · Narr golden-value test for the declared prose columns

- **Answers:** Narr gate (NO_DETECTOR); CF-14; Track A §5 (per-asset Narr golden tests)
- **Change:** golden fixture: a pattern cluster of n cells → `citation_human` (`:391`) states exactly n; the pointer and constant strings are unchanged
- **Files / declaration / migration:** a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can find it; no asset or registry change
- **Failing-first test and mutation:** failing-first: the test fails on a writer whose narrated value differs from the cited fact; mutation: change one composed value (a house number, a count) in the writer → the test fails
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 0: none; transitive 0); the touched surface is a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can f
- **Rebuild:** none
- **Gate it moves:** Narr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent (SS ruling 2026-10-01 defines narration; declarations 1.6.0 exists)

### FD-3 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (re-derivation): recompute totals, dominant/weakest domains and contradiction density from `bodha_cdlm_cells` and compare to the summary row; pure arithmetic over the stored cells.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 0: none; transitive 0); the touched surface is a new check in the Nikaṣa inspector tooling (Track E) registered for this asset
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-02** — Producer attribution: multi-table writers, rider rows and shared tables (count scope). *This asset:* FD-1
- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* table-map read pattern invisible to Dens/Reach detectors
- **CF-14** — Narr fidelity (golden-value) tests per L2 narration writer. *This asset:* declared `citation_human`
- **CF-17** — Complete.depth: never-populated columns (declare, populate or drop). *This asset:* never-populated L3-dynamic columns
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage D3 (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id)` (registry partition; the census `Vocab.identity` key adds `build_id, snapshot_type, dynamic_*, tradition_view_id`, volatile or NULL by design). Fingerprint: `total_chart_linkage`, `dominant_3_domains_array`, `weakest_3_domains_array`, `contradiction_density`, `bridge_link_count`, `asymmetric_link_count`, `strongest_linkage_pair_jsonb`, `domain_connectivity_jsonb`, `citation_ref`/`citation_human`. **Volatile:** `summary_id`, `build_id`, `computed_at`. Expected 5 rows on the chart.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the pure aggregation of CDLM cells, with no value of its own.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation) (design in FD-3)
- **Opportunities (never blocking):** the L3-dynamic columns are placeholders for a later layer; none proposed.

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t1 on 2026-09-09 (NIRMANA_SUPERSESSION_RECORD §2.3). Migration 1210 added no edge to this row. Manifest staleness has two severities (`src/lib/nirmana-elevation/definitions.ts:379-396`, `monitor.ts:374-393`): a `depends_on`, layer or membership change makes `assertManifestMatchesRegistryIdentity` throw (the monitor reports `plan_adaptation_required`; `dispatch_nirmana_campaign_wave.py` refuses the wave); a change to `count_sql`, `natural_key_partition`, `catalog_status`, `target_table` or `integrity_check_sql` only trips `assertManifestMatchesRegistry` (`evidence_refresh_required`: accepted evidence must be refreshed). The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3), so the staleness has no running consumer, but the frozen-definition DB row still reads `frozen`. **A production rebuild (SS REVIEW):** its direct dependents (none) re-run after it in DAG order; seed-derived transitive closure 0 assets. **F-3 invariant (this asset carries or derives from MSR signal ids):** it must be rebuilt strictly after every MSR producer and not before a later MSR regeneration in the same window (`msr_rebuild_order_guard.py`, F3 `plan_invariant.md`); I-6: an unguarded MSR replace took the `kala_*` tables from 4 rows to 0 and erased the canonical chart's five Kāla tables on 2026-09-08; charts 1c826d5a and cb73cd3d (all-v4 ids) make the guard mandatory; see INDEX §7. Idempotent per-chart delete-then-insert of three tables; no dependents.

## 8 · Questions for Strategic Suvarṇa

1. CF-02: option A (declared produced set, detector change) or widen `count_sql` to the unnamed tables (precedent: migration 661 PART 3 widened `bo_sangati`'s `count_sql` to include `bodha_triangulation`)?
2. CF-04: should the Dens/Reach detectors learn the `table_map` read pattern, or is the declaration the settled statement for this asset?

**SS rulings (N-59, 2026-10-01; decision sheet `DECISION_SHEET_L2_v1_0.md` (PR #2841); (R) = provisional until the J1 review). The questions above are kept for the record.**

- **Q-L2-01 - accepted.** The produced-table set of this asset is declared (option A) with a detector clause; `count_sql` is neither widened nor narrowed. The reader SELECT on the 10 unreadable `bodha_*` tables goes first (they are owned by `data_plane_l2_owner` and pinned in the ownership preflight, so it is a D6 plan with hash as REVIEW, not an amjis_app migration); the gap in this asset's count is confirmed from the tables before the detector is written. TI-L2-01, TI-L2-02.
- **Q-L2-12 - accepted.** This asset is in the CF-03 batch: the registry migration and the seed alignment (seed TO live) are pre-approved now; its floor is restated to the achieved count AFTER the one rebuild. TI-L2-10, TI-L2-24.
- **Layer-wide (Q-L2-18, Q-L2-19, sequencing).** Build.history counts only runs since the last writer or registry change (L0 Q11 carried; TI-L2-13) and Carr uses a D3 stratified sample with the section N.5 resolver, PASS only if every sampled row re-derives (L0 Q13 grading; TI-L2-14); both are read after the one coherent L2 rebuild on main's code, in which no asset is rebuilt twice.
