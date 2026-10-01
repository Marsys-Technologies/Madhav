---
asset_id: bo_pramana_mapa
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
decisions_applied: "SS decision N-59 (2026-10-01) on DECISION_SHEET_L2_v1_0.md (PR #2841); items marked (R) provisional until J1; section 8 lists the rulings for this asset"
track_i_items: [TI-L2-36, TI-L2-03, TI-L2-13, TI-L2-14, TI-L2-24]
ledger_gap_ids: [bo_pramana_mapa-Idem.pattern, bo_pramana_mapa-Earn.build_record, bo_pramana_mapa-Cost.baseline, bo_pramana_mapa-Dens.served, bo_pramana_mapa-Build.history, bo_pramana_mapa-Build.dep_liveness, bo_pramana_mapa-Carr.detector]
---
# bo_pramana_mapa — Synthesis quality scorecard (terminal Bodha writer)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

The last Bodha writer: it reads every `bodha_*` table for the chart and writes one `synthesis_quality_scorecard` row per chart: per-asset row counts, verified-versus-approximation percentages, formula versions, the Trap-1 authority-inversion check, and the §N.8 earned-signal detectors (LEL leak, pillar reachability, no-threshold-drop, trap-2 narration leak, verification divergence), each with "a reachable false/non-zero branch — none is a proxy, a tautology or a literal"; it also refreshes the materialized views of the A10/A11 specs (`bo_pramana_mapa.py` docstring). `@register("bo_pramana_mapa")` at `bo_pramana_mapa.py:650`, `replace_prior_scorecard` at `:908` (`_idempotency.py:523`, which deletes every prior row for the chart). 1 chart row (floor 1), 3 table-wide (3 charts), 34 columns with 30 fully populated; NEVER populated: `centrality_formula_version`, `no_pre_answer_pass`, `ledger_independence_pass`, `discovery_not_fabricated_pass` (flags with no detector stay NULL rather than green: the intended reading of CLAUDE.md §N.8). Declared dependencies (8) include `bo_upaya`, `bo_drishti`, `bo_anveshana` (stale at the census); its one dependent is `bo_samvada`. Frozen under the t2 definition (2026-09-10).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1871` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_pramana_mapa.py:650`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `synthesis_quality_scorecard`; count_sql tables: `synthesis_quality_scorecard` | census CEN-R |
| live rows / floor | 1 / 1 (chart 482012f1, count_sql scope) | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bo_upaya`, `bo_drishti`, `bo_anveshana`, `bo_laksana`, `bo_sangati`, `bo_bimba`, `bo_karanajala`, `bo_samskara` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 1 / transitive 1; seed-derived closure (post-1210): direct 1 / transitive 1; direct dependents: `bo_samvada` | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `synthesis_quality_scorecard`: 7 non-test py/ts/tsx files reference it (4 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `trace_assembler.ts`, `coverage_matrix.ts`, `query_quality_scorecard.ts`, `source_query_availability.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | 1 capability module(s): `L2_bodha/query_quality_scorecard.ts`; `density_contract` declared on 0 (saved rev-1 reading) | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t2, 2026-09-10; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 2938fefd complete/build (2026-09-10) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): synthesis_quality_scorecard (bodha_writers/_idempotency.py:523 via bo_pramana_mapa.py → bodha_writers/_idempotency.py:replace_prior_scorecard) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served† | FAIL | 1 module(s): query_quality_scorecard.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 26 error(s) and 12 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-10): post-write integrity check failed: integrity_check_sql error: there is no parameter $1 LINE 7:     WHERE s.chart_id = $1                                ^ |
| Build | Build.dep_liveness | PARTIAL | 5/8 declared dependencies lit at chart 482012f1 (or global); stale: ['bo_upaya (stale, chart 482012f1)', 'bo_drishti (stale, chart 482012f1)', 'bo_anveshana (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 2938fefd complete/build (2026-09-10) |
| Complete (information) | Complete.depth | PARTIAL | 3 rows, 34 cols; fully populated 30; NEVER populated ['centrality_formula_version', 'no_pre_answer_pass', 'ledger_independence_pass', 'discovery_not_fabricated_pass'] |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width 14/30 built column(s) (46.7%) selected by 1 capability module(s); dark: ['contradiction_count', 'convergence_count', 'convergence_formula_version', 'divergent_flagged_count', 'embedding_count… |

Census emits **no cell** (absent, not N/A) for: Ldgr.source_presence (MF-L2-003, register R128).

**PASS cells (compact):** Vocab.identity (declared key (scorecard_id): 0 duplicate(s)); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.completion (rows_written=1 = live=1 (count_sql over the target table; chart 482012f1)); Build.exercised (40 executed run(s) of 96 build_run_assets row(s), scope(s): asset, asset_set, global, layer, last executed 202…); Count.floor (live=1, floor=1, delta=+0).

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **FAIL** — 2 module(s) reach it by code: L1_ganita/coverage_matrix.ts, L2_bodha/query_quality_scorecard.ts; 1 served select(s) of its table; no referencing capability that serves it declares density_contract; also a served select outside the scanned serving roots (not graded): platform/src/lib/admi; Idem.pattern rev 2 reads **PASS**.

**Build.dag rev 2 (E6 g+h; recompute over the saved registry BEFORE migration 1210, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`, reads-match clause):** PARTIAL — 10 resolved reads are covered, but the parse is incomplete: a table is named dynamically at `bo_pramana_mapa.py:100` and `execute()` is given SQL not traced to a literal at `:79`. Unchanged by 1210 (it adds no edge here); a detector-limit PARTIAL, not a missing edge. The saved census cell Build.dag PASS † above is the rev-1 reading.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| `bo_pramana_mapa-Dens.served` / census cell Dens.served † | Dens | real (rev 1 and offline rev 4) | 1 module `query_quality_scorecard.ts` (plus an admin read outside the serving roots, not graded) and no `density_contract`; the offline rev-4 scan reads FAIL. 14 of 30 built columns served; the detector flags (`lel_zero_leak_pass`, `pillars_meet_reachability_pass`, `msr_no_threshold_drop_flag`, `notes`) are dark by default. FD-1; CF-04. |
| `bo_pramana_mapa` Build.dag rev 2 (E6gh recompute) | Build (dag) | detector | PARTIAL: the reads-match parse is incomplete (a dynamically named table at `bo_pramana_mapa.py:100`, `execute()` given untraced SQL at `:79`); the 10 resolved reads are covered. A detector limit, not a missing edge; unchanged by 1210. |
| `bo_pramana_mapa-Build.dep_liveness` | Build (dep_liveness) | history/ordering | 5 of 8 declared dependencies lit; `bo_upaya`, `bo_drishti`, `bo_anveshana` stale (built, upstream moved since). CF-10 / §7. |
| `bo_pramana_mapa-Build.history` | Build (history) | history | latest run complete; 26 errors and 12 aborts on record (latest error 2026-09-10, `post-write integrity check failed: integrity_check_sql error: there is no parameter $1`, an integrity-SQL defect in a past run; the latest run completed). CF-10. |
| census: no `Ldgr.source_presence` cell (MF-L2-003) | Ldgr | detector | the scorecard carries counts and flags, not citations; the carrying columns (`notes`, per-asset counts) need a declaration. CF-08. |
| declarations `prose_fields: null` (undeclared) | Null, Narr | detector (declaration) | the writer's f-strings are queries and error messages (`:100`, `:369-407`, `:676-795`), not stored text; the `notes` jsonb holds detector terms. Proposal: declare `[]` after reading the `notes` builder for composed sentences. CF-06. |
| census cell Complete.depth (information) | Complete (information) | information | NEVER populated: `no_pre_answer_pass`, `ledger_independence_pass`, `discovery_not_fabricated_pass` (no detector: NULL is the honest value) and `centrality_formula_version`. Keep NULL until a detector exists (CLAUDE.md §N.8). CF-17. |
| `bo_pramana_mapa-Earn.build_record`, `-Cost.baseline`, `-Carr.detector` | Earn, Carr | detector | instrument absent / no D1-D3 detector (the scorecard is itself a detector asset: its flags are the Earn-gate claims it makes about the layer); CF-05, CF-07. |

## 3 · Disposition

**keep (P)** — complete on the census; the one measured shortfall is the density declaration on its served surface. The asset is an instrument whose own earned-signal discipline (detectors that can read false, NULL when none exists) is the kernel to preserve.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Declare the density contract and surface the detector flags

- **Answers:** Dens.served FAIL; CF-04
- **Change:** declare `density_contract` on `query_quality_scorecard.ts` (single-row-per-chart response: `paginated: false`, `facets: ['chart_id']`, backed `empty_reason`) and select the tier/verification column plus the detector flags (`lel_zero_leak_pass`, `pillars_meet_reachability_pass`, `msr_no_threshold_drop_flag`) in the default projection so a caller can read which flags are earned and which are NULL
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L2_bodha/query_quality_scorecard.ts`
- **Failing-first test and mutation:** response-shape test: an empty chart returns the declared `empty_reason`; a NULL flag is returned as NULL (not false); mutation: drop the declaration → FAIL
- **Output change:** none
- **Blast radius:** consumers of the `query_quality_scorecard` tool: `registry/mcp_capability_bridge.ts`, the fan-out umbrella `register_d5_fanout.ts`, `platform-mcp/src/tools/registry_bridge.ts` and knowledge metadata; selecting the flags adds response fields (NULL stays NULL); no value changes
- **Rebuild:** none
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-dependent: TGH-T3-26 and N-22

### FD-2 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (re-derivation): recompute each stored count and detector term with its own SQL on the same chart and compare; a seeded corruption (a leaked `lel_origin` row) must flip the corresponding flag, which is the existing test discipline (`test_n8_earned_signal_detectors.py`).
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 1: `bo_samvada`; transitive 1); the touched surface is a new check in the Nikaṣa inspector tooling (Track E) registered for this asset
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* FD-1
- **CF-08** — Ldgr: assets with no recognised citation column (no census cell). *This asset:* no Ldgr reading
- **CF-06** — prose_fields declarations for the L2 assets that have none (Null and Narr gates). *This asset:* declare `[]` after reading `notes`
- **CF-17** — Complete.depth: never-populated columns (declare, populate or drop). *This asset:* honest NULL flags
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage D3 (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL and stale upstream
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id)` per scorecard (the table is keyed `(chart_id, build_id)`; the writer keeps one row per chart). Fingerprint: the per-asset counts, formula versions, the detector terms and flags (NULL preserved), the verification percentages. **Volatile:** `scored_at`, `build_id`, `notes` timestamps. The counts depend on every upstream table, so the scorecard fingerprint is only comparable after a full-layer rebuild.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** detectors that can read false (each with a reachable non-zero branch) and NULL, never green, where no detector exists.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation) (design in FD-2)
- **Opportunities (never blocking):** the three NULL pass-flags are the layer's open detector backlog: no-pre-answer, ledger-independence, discovery-not-fabricated.

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t2 on 2026-09-10 (NIRMANA_SUPERSESSION_RECORD §2.3). Migration 1210 added no edge to this row. Manifest staleness has two severities (`src/lib/nirmana-elevation/definitions.ts:379-396`, `monitor.ts:374-393`): a `depends_on`, layer or membership change makes `assertManifestMatchesRegistryIdentity` throw (the monitor reports `plan_adaptation_required`; `dispatch_nirmana_campaign_wave.py` refuses the wave); a change to `count_sql`, `natural_key_partition`, `catalog_status`, `target_table` or `integrity_check_sql` only trips `assertManifestMatchesRegistry` (`evidence_refresh_required`: accepted evidence must be refreshed). The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3), so the staleness has no running consumer, but the frozen-definition DB row still reads `frozen`. **A production rebuild (SS REVIEW):** its direct dependents (`bo_samvada`) re-run after it in DAG order; seed-derived transitive closure 1 assets. It reads all other Bodha tables, so it is the last to run after any L2 rebuild; its row is single-per-chart and deleted by `replace_prior_scorecard`.

## 8 · Questions for Strategic Suvarṇa

1. Is the open detector backlog (`no_pre_answer_pass`, `ledger_independence_pass`, `discovery_not_fabricated_pass`) in scope for the first L2 wave, or do the flags stay NULL?

**SS rulings (N-59, 2026-10-01; decision sheet `DECISION_SHEET_L2_v1_0.md` (PR #2841); (R) = provisional until the J1 review). The questions above are kept for the record.**

- **Q-L2-02 - accepted.** The module's `density_contract` is declared as what the handler does (`paginated: false`, the true `empty_reason`; precedent `query_cdlm_summary.ts:144`, `query_chart_gestalt.ts:64`). No rebuild. TI-L2-03.
- **Q-L2-20 - accepted.** The three pass-flags (`no_pre_answer_pass`, `ledger_independence_pass`, `discovery_not_fabricated_pass`) already have detector code (`bo_pramana_mapa.py:511-620`, #2607); they are read after the one rebuild (`bo_sangati` before `bo_pramana_mapa` inside it). TI-L2-24.
- **Layer-wide (Q-L2-18, Q-L2-19, sequencing).** Build.history counts only runs since the last writer or registry change (L0 Q11 carried; TI-L2-13) and Carr uses a D3 stratified sample with the section N.5 resolver, PASS only if every sampled row re-derives (L0 Q13 grading; TI-L2-14); both are read after the one coherent L2 rebuild on main's code, in which no asset is rebuilt twice.
- **TI-L2-36 (SS, 2026-10-02) - added to the batch.** `_VERIFICATION_TIER_RANKS` (`bo_pramana_mapa.py:430-438`) is aligned with the L1 respelling (`single_pass` = 2 against `single` = 1 is one alias with two ranks); this asset's writer therefore changes. Tier respelling: L1 writers now emit `single`, never `single_pass` (PR #2854); the F-10 tier-inversion count is not read between S-L1 and S-L2 (INDEX 12.4). One rebuild, no asset rebuilt twice.
