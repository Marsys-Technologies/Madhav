---
asset_id: bo_drishti
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
track_i_items: [TI-L2-13, TI-L2-14]
ledger_gap_ids: [bo_drishti-Earn.build_record, bo_drishti-Cost.baseline, bo_drishti-Build.history, bo_drishti-Carr.detector]
---
# bo_drishti — Question lenses (pointer-only lens table, one row per question type × ayanamsha)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

Pre-computes deterministic classical question lenses: a question type maps to the chart-specific structural elements that bear on it, as signal ids (`template_element_ids_jsonb`), a mandatory wildcard graph sweep over `bodha_cgm_edges` so no high-salience far-from-template signal is lost (`wildcard_element_ids_jsonb`) and the ranked union (`all_relevant_ranked_jsonb`, total sort key F-114: salience, template-first, `signal_id`). Two absolute guards in the docstring: a lens POINTS, never pre-answers (`points_only_assertion = True`, `bo_drishti.py:268`) and is ADDITIVE, never subtractive. `@register("bo_drishti")` at `bo_drishti.py:288`, chart-wide delete at `:311`; 60 chart rows (floor 60, delta 0), 180 table-wide, all 15 columns populated; `lens_id` is `stable_semantic_uuid` (deterministic). Served by `query_question_lenses.ts` (declares a contract and selects `verification_pass_status`) and `query_domain_reading.ts`. Dependents `bo_anveshana`, `bo_pramana_mapa`. Frozen under the t1 definition (2026-09-09).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1890` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_drishti.py:288`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_question_lenses`; count_sql tables: `bodha_question_lenses` | census CEN-R |
| live rows / floor | 60 / 60 (chart 482012f1, count_sql scope) | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bo_laksana`, `bo_sangati`, `bo_karanajala` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 2 / transitive 22; seed-derived closure (post-1210): direct 2 / transitive 22; direct dependents: `bo_anveshana`, `bo_pramana_mapa` | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_question_lenses`: 7 non-test py/ts/tsx files reference it (5 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `register_d8_assess_domain.ts`, `query_domain_reading.ts`, `query_question_lenses.ts`, `tool_name_bridge.ts`, `source_query_availability.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | 2 capability module(s): `L2_bodha/query_domain_reading.ts`, `L2_bodha/query_question_lenses.ts`; `density_contract` declared on 1 (saved rev-1 reading) | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t1, 2026-09-09; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run a5b0eef1 complete/build (2026-09-09) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): bodha_question_lenses (bo_drishti.py:311) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Build | Build.history | PARTIAL | latest run complete, but 17 error(s) and 8 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-07-16): BLOCKED: upstream dependency(ies) bo_karanajala, bo_laksana, bo_sangati did not complete in this run; skipped to avoid building on incomplete data |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run a5b0eef1 complete/build (2026-09-09) |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width 12/15 built column(s) (80.0%) selected by 2 capability module(s); dark: ['build_id', 'chart_id', 'engine_version']; depth 100.0% (a capability query reads it with no literal row pin (upper bo… |

**PASS cells (compact):** Ldgr.source_presence (citation_ref populated on 180/180 rows); Vocab.identity (declared key (chart_id, ayanamsha_id, question_type): 0 duplicate(s)); Dens.served† (2 module(s): query_domain_reading.ts, query_question_lenses.ts; declaring density_contract: 1); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.completion (rows_written=60 = live=60 (count_sql over the target table; chart 482012f1)); Build.exercised (42 executed run(s) of 76 build_run_assets row(s), scope(s): asset_set, global, layer, last executed 2026-09-09); Build.dep_liveness; Count.floor (live=60, floor=60, delta=+0); Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **PASS** — 3 module(s) reach it by code: L2_bodha/query_domain_reading.ts, L2_bodha/query_question_lenses.ts, register_d8_assess_domain.ts; 1 capability(ies) declare density_contract AND select a tier column from it (verification_pass_status) in: L2_bodha/query_question_lenses.ts; Idem.pattern rev 2 reads **PASS**.

**Build.dag rev 2 (E6 g+h; recompute over the saved registry BEFORE migration 1210, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`, reads-match clause):** PASS (not in the recompute's L2 gate-diff list; no change from the saved rev-1 PASS) The saved census cell Build.dag PASS † above is the rev-1 reading.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| declarations `prose_fields: null` (undeclared) | Null, Narr | detector (declaration) | the writer binds ids, floats, flags, a constant `verification_pass_status = 'documented_approximation'` and an identifier `citation_ref = f"bo_drishti/{question_type}/{aya}"` (`bo_drishti.py:254-272`) and composes no sentence; proposal: declare `[]` with that `file:line` evidence (an identifier string is not narration, per the declarations rule). CF-06. |
| `bo_drishti-Build.history` | Build (history) | history | latest run complete; 17 errors and 8 aborts on record (latest error 2026-07-16, `BLOCKED: upstream bo_karanajala, bo_laksana, bo_sangati did not complete`). CF-10. |
| `bo_drishti-Earn.build_record`, `-Cost.baseline`, `-Carr.detector` | Earn, Carr | detector | instrument absent / no D1-D3 detector; CF-05, CF-07. |
| census Dens.served † | Dens | information | rev-1 PASS and the offline rev-4 scan reads PASS (`query_question_lenses.ts` declares a contract and selects `verification_pass_status`); no gap. |

## 3 · Disposition

**keep (P)** — clean on every measured cell; the only open items are an undeclared prose field, absent detectors and recorded history. The preserved kernel is the pointer-only, additive, total-ordered lens.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Declare `prose_fields = []` with writer evidence

- **Answers:** Null/Narr NO_DETECTOR (undeclared); CF-06
- **Change:** add `prose_fields: []` and `evidence.prose_fields` citing `bo_drishti.py:254-272` (no composed string bound to a column) to the declarations file; verify by reading the three `*_element_ids_jsonb` builders for any text key before declaring
- **Files / declaration / migration:** `platform/scripts/governance/asset_declarations.json` (Track E)
- **Failing-first test and mutation:** declarations validation test passes; mutation: add a composed text key to a lens dict → the Narr scan flags the undeclared prose
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 2: `bo_anveshana`, `bo_pramana_mapa`; transitive 22); the touched surface is `platform/scripts/governance/asset_declarations.json` (Track E)
- **Rebuild:** none
- **Gate it moves:** Null, Narr
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent (SS ruling 2026-10-01; file schema 1.6.0 exists)

### FD-2 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (re-derivation): recompute the template element set from the lens template and the ranked union from `bodha_msr_signals` salience, and check that every pointed `signal_id` resolves to a signal row; additivity (the wildcard set never removes a template signal) is a testable set property.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 2: `bo_anveshana`, `bo_pramana_mapa`; transitive 22); the touched surface is a new check in the Nikaṣa inspector tooling (Track E) registered for this asset
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-06** — prose_fields declarations for the L2 assets that have none (Null and Narr gates). *This asset:* FD-1: declare `[]`
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage D3/D2 (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id, question_type)` (registry partition; `lens_id` is a deterministic function of it plus `lens_template_version`). Fingerprint: the three `*_element_ids_jsonb` payloads with signal ids resolved to signal natural keys (sort order is part of the contract), `lens_template_version`, `lens_formula_version`, `points_only_assertion`, `verification_pass_status`, `citation_ref`. **Volatile:** `build_id`, `computed_at`, `engine_version`, raw `signal_id`s. Expected 60 rows.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the points-only guard, the mandatory wildcard sweep, the reproducible total ordering.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation) (design in FD-2)
- **Opportunities (never blocking):** declare the question-type universe (`Complete.width`).

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t1 on 2026-09-09 (NIRMANA_SUPERSESSION_RECORD §2.3). Migration 1210 added no edge to this row. Manifest staleness has two severities (`src/lib/nirmana-elevation/definitions.ts:379-396`, `monitor.ts:374-393`): a `depends_on`, layer or membership change makes `assertManifestMatchesRegistryIdentity` throw (the monitor reports `plan_adaptation_required`; `dispatch_nirmana_campaign_wave.py` refuses the wave); a change to `count_sql`, `natural_key_partition`, `catalog_status`, `target_table` or `integrity_check_sql` only trips `assertManifestMatchesRegistry` (`evidence_refresh_required`: accepted evidence must be refreshed). The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3), so the staleness has no running consumer, but the frozen-definition DB row still reads `frozen`. **A production rebuild (SS REVIEW):** its direct dependents (`bo_anveshana`, `bo_pramana_mapa`) re-run after it in DAG order; seed-derived transitive closure 22 assets. Idempotent per-chart delete-then-insert; `bo_anveshana` and `bo_pramana_mapa` re-run after it.

## 8 · Questions for Strategic Suvarṇa

1. CF-06: confirm `[]` after the read of the jsonb builders (no text key).

**SS rulings (N-59, 2026-10-01; decision sheet `DECISION_SHEET_L2_v1_0.md` (PR #2841); (R) = provisional until the J1 review). The questions above are kept for the record.**

- **Layer-wide (Q-L2-18, Q-L2-19, sequencing).** Build.history counts only runs since the last writer or registry change (L0 Q11 carried; TI-L2-13) and Carr uses a D3 stratified sample with the section N.5 resolver, PASS only if every sampled row re-derives (L0 Q13 grading; TI-L2-14); both are read after the one coherent L2 rebuild on main's code, in which no asset is rebuilt twice.
