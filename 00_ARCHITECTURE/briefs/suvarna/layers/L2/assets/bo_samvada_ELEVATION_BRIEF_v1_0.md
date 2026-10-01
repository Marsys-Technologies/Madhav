---
asset_id: bo_samvada
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
disposition: "qualify (Q)"
disposition_proposal_approver: "Steward (G16) for qualify; any consolidation or retirement is SS (R5)"
nirmana_freeze: "t2, 2026-09-11"
decisions_applied: "SS decision N-59 (2026-10-01) on DECISION_SHEET_L2_v1_0.md (PR #2841); items marked (R) provisional until J1; section 8 lists the rulings for this asset"
track_i_items: [TI-L2-08, TI-L2-10, TI-L2-13, TI-L2-14]
ledger_gap_ids: [bo_samvada-Idem.pattern, bo_samvada-Build.completion, bo_samvada-Earn.build_record, bo_samvada-Cost.baseline, bo_samvada-Dens.served, bo_samvada-Build.history, bo_samvada-Build.dep_liveness, bo_samvada-Carr.detector]
---
# bo_samvada — Unified Chart Digest (UCD) view: a passive compatibility boundary

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

Registered as the digest asset, but on main the writer is a passive compatibility boundary: `run()` writes nothing (`rows_inserted=0`, `rows_skipped=1`, note "legacy serving projection preserved; no per-chart DDL; versioned projection integration not authorized at L2", `bo_samvada.py:139-160`), because the `vw_chart_digest` view it once created is now "preserved, not recreated": replacing it in a writer would be an uncaptured global DDL mutation that cannot be replayed from a generation snapshot (docstring `:26-28`). The view aggregates the Bodha layer per chart per ayanamsha (signal/yoga/dosha counts, salience, contradiction count, weakest graha from L1 shadbala, top remedy priority, top convergence domains, Trap-1 count, `digest_at` at query time) and is served by `query_ucd.ts` (11 of 13 columns). Live 5 rows on the chart (counted by the census from the view). The registry `count_sql` is the constant `SELECT 0 AS count` (MF-L2-007) while the docstring says it reads `SELECT count(*) FROM vw_chart_digest …` (`:30-32`) and the seed says the same with `$1` (`asset_registry_seed.ts:1832-1850`); the declarations file records `kind: view` while the registry says `asset_kind = data`. Declared dependencies (5, `bo_laksana … bo_pramana_mapa`) make it the last Bodha asset in order. No dependents. Frozen under the t2 definition (2026-09-11).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | view | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1832` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_samvada.py:139`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `vw_chart_digest`; count_sql tables: `vw_chart_digest` | census CEN-R |
| live rows / floor | 5 / 0 (chart 482012f1, count_sql scope) — count_sql is the constant `SELECT 0 AS count` (the census counts the view itself) | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bo_laksana`, `bo_karanajala`, `bo_upaya`, `bo_sangati`, `bo_pramana_mapa` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 0 / transitive 0; seed-derived closure (post-1210): direct 0 / transitive 0; direct dependents: none | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `vw_chart_digest`: 7 non-test py/ts/tsx files reference it (6 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `cr_status.ts`, `assetClearSpec.ts`, `query_ucd.ts`, `source_query_availability.ts`, `registry_bridge.ts`, `cr_status.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | 1 capability module(s): `L2_bodha/query_ucd.ts`; `density_contract` declared on 0 (saved rev-1 reading) | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t2, 2026-09-11; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 5b06c25b complete/skip_no_delta (2026-09-11) |
| Idem | Idem.pattern† | PARTIAL | no write to the asset's own table(s) ['vw_chart_digest'] anywhere in the resolved scope — nothing to replace; not graded N/A, since a static scan cannot prove a write's absence [resolved scope: bo_samvada.py, bodha_writers/data_plane_contracts.py] |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served† | FAIL | 1 module(s): query_ucd.ts; declaring density_contract: 0 |
| Build | Build.completion | NO_DETECTOR | NO_DETECTOR — view: live=5 (counted by the census from the view vw_chart_digest (chart-scoped); the registry count_sql is a constant (SELECT 0 AS count); chart 482012f1); build record rows_written=1 counts the view object, not rows — completion consistency is not measurable for a view |
| Build | Build.history | PARTIAL | latest run complete, but 23 error(s) and 11 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-12): BLOCKED: upstream dependency(ies) bo_pramana_mapa did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | PARTIAL | 3/5 declared dependencies lit at chart 482012f1 (or global); stale: ['bo_upaya (stale, chart 482012f1)', 'bo_pramana_mapa (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 5b06c25b complete/skip_no_delta (2026-09-11) |
| Count (information) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=5) |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width 11/13 built column(s) (84.6%) selected by 1 capability module(s); dark: ['ayanamsha_id', 'chart_id']; depth 100.0% (a capability query reads it with no literal row pin (upper bound)) |

Census emits **no cell** (absent, not N/A) for: Ldgr.source_presence, Vocab.identity (MF-L2-003, register R128).

**PASS cells (compact):** Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.exercised (40 executed run(s) of 95 build_run_assets row(s), scope(s): asset, asset_set, global, layer, last executed 202…); Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr NO_DETECTOR · Idem PARTIAL · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build NO_DETECTOR.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **NO_DETECTOR** — 1 serving-root file(s) naming vw_chart_digest lose the string scanner's sync (an unbalanced quote, a nested template literal, or a regex literal holding a quote desynced it): platform-mcp/src/tools/registry_bridge.ts; its served select and density_contract cannot be read — never FAIL,; Idem.pattern rev 2 reads **PARTIAL**.

**Build.dag rev 2 (E6 g+h; recompute over the saved registry BEFORE migration 1210, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`, reads-match clause):** PASS (not in the recompute's L2 gate-diff list; no change from the saved rev-1 PASS) The saved census cell Build.dag PASS † above is the rev-1 reading.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| census cells Idem.pattern (PARTIAL), Build.completion (NO_DETECTOR); no Vocab/Ldgr cells | Idem, Build, Vocab, Ldgr | detector (applicability) | a view target: Idem reads PARTIAL ("no write to the asset's own table … nothing to replace; not graded N/A, since a static scan cannot prove a write's absence"), Build.completion NO_DETECTOR (the saved record `rows_written=1` counts the view object; the writer now returns `rows_inserted=0`), no Vocab or Ldgr cell. These are applicability facts for a view, not defects: they need N-22 rules (`NA_RULE_DECISIONS` is empty on main), not asset changes. CF-03 (declare kind). |
| census: registry `count_sql` / seed / docstring (MF-L2-007) | Earn / Build | real (registry) | three statements disagree: live `count_sql` is the constant `SELECT 0 AS count`, the seed and the docstring say a chart-scoped `count(*)` over the view. A constant count cannot read false on writer failure (the earlier B8 finding, prior campaign). CF-03. |
| declarations `kind: view` vs registry `asset_kind = data` | Build | real (registry/declaration) | the declarations file and the seed `storage_type: postgres_view` agree; the registry `asset_kind` reads `data` (declarations evidence). A kind is a fact, never a rule (declarations description), so the disagreement is listed, not resolved here. CF-03. |
| `bo_samvada-Dens.served` / census cell Dens.served † | Dens | detector (rev 1 FAIL; rev 4 NO_DETECTOR) | saved rev-1 FAIL (1 module `query_ucd.ts`, 0 contracts); the offline rev-4 scan could not read the served surface (scanner desync in `registry_bridge.ts`). CF-04. |
| `bo_samvada-Build.dep_liveness` and the five declared edges | Build (dep_liveness, dag) | history/ordering + question | 3 of 5 declared dependencies lit; `bo_upaya`, `bo_pramana_mapa` stale. The writer (a no-op) reads none of them, but the VIEW it fronts aggregates exactly those assets' tables (layer instance §3.4: `bodha_contradictions`, `bodha_convergence`, `bodha_msr_signals`, `bodha_rm_resonances`, `synthesis_quality_scorecard`), so the five edges are the lineage and freshness gating of the view's inputs, not dead weight. Removing them would drop that gating: a trade-off, not a provable over-declaration. Recommendation: keep them unless the view is consolidated into a versioned projection that owns its own dependencies. CF-15 (kept, with this caveat). |
| census: registry `natural_key_partition` | Idem | real (registry) | blank (MF-L2-009); the asset has no rows to partition. CF-03. |
| `bo_samvada-Build.history` | Build (history) | history | latest run complete; 23 errors and 11 aborts on record (latest error 2026-08-12, `BLOCKED: upstream bo_pramana_mapa did not complete`). CF-10. |
| `bo_samvada-Earn.build_record`, `-Cost.baseline`, `-Carr.detector` | Earn, Carr | detector | instrument absent / no D1-D3 detector; CF-05, CF-07. |

## 3 · Disposition

**qualify (Q)** — the asset is not a row producer: its writer is a documented no-op and its output is a legacy serving view whose DDL is outside L2 producer authority. The honest disposition is to narrow its claims (kind `view`, Build/Idem/count gates N/A by explicit rule, `count_sql` a real chart-scoped read of the view) rather than to grade it as a data asset. A later decision may consolidate the view into a versioned projection owned elsewhere (the writer's own note anticipates an "approved integration packet"); that is SS's, not decided here.

Approver under Track A brief §10: **Steward (G16) for qualify; any consolidation or retirement is SS (R5)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Make the registry state what the asset is

- **Answers:** the count_sql, kind and applicability gaps; CF-03
- **Change:** (1) replace the constant `count_sql` with the chart-scoped read of the view (`SELECT count(*) FROM vw_chart_digest WHERE chart_id = $1`), the one the seed and the docstring already state, and set `target_floor` to 5 with it (the seed already says 5; live is 0 only because the constant count could never exceed it: with a real count the achieved value on the chart is 5, §N.4); (2) align `asset_kind` with the declared `view`; (3) declare, via N-22 rules with decision ids, that Idem.pattern, Build.completion, Vocab and Ldgr are N/A for a view target
- **Files / declaration / migration:** one surgical migration + `asset_registry_seed.ts:1832-1850` literals; `asset_declarations.json` kind; `NA_RULE_DECISIONS` (Track E) for the N/A rules
- **Failing-first test and mutation:** failing-first: `count_sql` returns 5 on the canonical chart and 0 on a chart with no signal rows (so it can read false); mutation: restore the constant → the count test fails
- **Output change:** none
- **Blast radius:** `count_sql` is in the registry contract fingerprint: the frozen t2 manifest goes stale; the cockpit count for the asset changes (cosmetic); no consumer reads it
- **Rebuild:** none
- **Gate it moves:** Earn (count_sql), Build, Idem
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent for (1)(2); tier-dependent for (3): the N-22 rule wording and the kind vocabulary (TG-L2-007)
- **Question for SS:** May the three N/A rules be declared for a view target, or must Idem/Build stay graded?

### FD-2 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (re-derivation of the view's columns): recompute each aggregate (counts, averages, contradiction count, weakest graha from L1 shadbala) from the source tables for the chart and compare to the view's row; the UCN→UCD retirement (L2 handoff §1) means the view must hold no authored text.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 0: none; transitive 0); the touched surface is a new check in the Nikaṣa inspector tooling (Track E) registered for this asset
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-03** — Registry correction batch (one surgical migration + seed literals). *This asset:* FD-1
- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* Dens FAIL (rev 1)
- **CF-15** — depends_on audit: declared edges versus what each writer reads. *This asset:* the five declared edges are the view's lineage/freshness gating: keep (trade-off recorded), not an over-declaration to remove
- **CF-06** — prose_fields declarations for the L2 assets that have none (Null and Narr gates). *This asset:* declarations `prose_fields` null: a view with no composed text; declare `[]` with the view definition as evidence (DDL evidence is rejected by the validator: cite writer code, which composes nothing)
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage: not applicable to a no-op writer; the view's own definition is the check (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

No rows are produced by the asset. The view's output is fingerprinted by its definition (the SQL text, captured with the migration that owns it) and by its result on a fixed chart: `msr_signal_count`, `yoga_count`, `dosha_count`, `avg_salience`, `max_salience`, `contradiction_count`, `weakest_graha`, `top_priority_class`, `top_convergence_domains`, `trap1_count`. **Volatile:** `digest_at` (query-time clock). Expected 5 rows on the chart.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the served UCD digest with its documented column semantics, preserved rather than recreated.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation of the view's columns) (design in FD-2)
- **Opportunities (never blocking):** a versioned, snapshot-capturable projection owned by the serving layer (the writer's own note).

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t2 on 2026-09-11 (NIRMANA_SUPERSESSION_RECORD §2.3). Migration 1210 added no edge to this row. Manifest staleness has two severities (`src/lib/nirmana-elevation/definitions.ts:379-396`, `monitor.ts:374-393`): a `depends_on`, layer or membership change makes `assertManifestMatchesRegistryIdentity` throw (the monitor reports `plan_adaptation_required`; `dispatch_nirmana_campaign_wave.py` refuses the wave); a change to `count_sql`, `natural_key_partition`, `catalog_status`, `target_table` or `integrity_check_sql` only trips `assertManifestMatchesRegistry` (`evidence_refresh_required`: accepted evidence must be refreshed). The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3), so the staleness has no running consumer, but the frozen-definition DB row still reads `frozen`. **A production rebuild (SS REVIEW):** its direct dependents (none) re-run after it in DAG order; seed-derived transitive closure 0 assets. The writer is a no-op, so a rebuild changes nothing; the build record now reads `rows_inserted=0`. The registry edits in FD-1 stale the frozen manifest.

## 8 · Questions for Strategic Suvarṇa

1. FD-1: confirm qualify (view kind, count_sql real, N/A rules by N-22) and decide whether to consolidate the view into a versioned projection later.
2. The saved record says `rows_written=1` (the view object) and the code now returns 0: which is the intended build record for a passive boundary?

**SS rulings (N-59, 2026-10-01; decision sheet `DECISION_SHEET_L2_v1_0.md` (PR #2841); (R) = provisional until the J1 review). The questions above are kept for the record.**

- **Q-L2-09 - accepted.** Qualify confirmed: chart-scoped `count_sql` over the view (reads 5), floor 5, `natural_key_partition`, build record 0 under the changed-rows convention (L0 Q1); docstring (`bo_samvada.py:31-40`) and `cr_status.ts` comment corrected; no consolidation now. No rebuild. TI-L2-08.
- **Q-L2-07 - accepted.** The five view-lineage edges are kept.
- **Q-L2-12 - accepted.** This asset is in the CF-03 batch: the registry migration and the seed alignment (seed TO live) are pre-approved now; its floor is restated to the achieved count AFTER the one rebuild. TI-L2-10, TI-L2-24.
- **Layer-wide (Q-L2-18, Q-L2-19, sequencing).** Build.history counts only runs since the last writer or registry change (L0 Q11 carried; TI-L2-13) and Carr uses a D3 stratified sample with the section N.5 resolver, PASS only if every sampled row re-derives (L0 Q13 grading; TI-L2-14); both are read after the one coherent L2 rebuild on main's code, in which no asset is rebuilt twice.
