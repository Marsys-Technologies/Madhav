---
asset_id: bo_sangati
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
nirmana_freeze: "t3, 2026-09-11"
decisions_applied: "SS decision N-59 (2026-10-01) on DECISION_SHEET_L2_v1_0.md (PR #2841); items marked (R) provisional until J1; section 8 lists the rulings for this asset"
track_i_items: [TI-L2-02, TI-L2-03, TI-L2-10, TI-L2-13, TI-L2-14, TI-L2-31]
ledger_gap_ids: [bo_sangati-Build.completion, bo_sangati-Earn.build_record, bo_sangati-Cost.baseline, bo_sangati-Dens.served, bo_sangati-Build.history, bo_sangati-Carr.detector]
---
# bo_sangati — Cross-Domain Linkage Matrix (CDLM): cells, convergence and triangulation

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

Computes the cross-domain linkage matrix over `bodha_msr_signals`: one `bodha_cdlm_cells` row per domain pair that shares at least one signal, `bodha_convergence` rows per domain (convergence count and score from `convergence_formula_v1`, cross-tradition count) and `bodha_triangulation` rows (multi-tradition concordance, BA-P3B) (`bo_sangati.py` docstring, `:56`, `:101`, `:122`). `@register("bo_sangati")` at `bo_sangati.py:457`; it replaces its prior rows through `replace_prior_cdlm_cells`, `replace_prior_convergence` and a `DELETE FROM bodha_triangulation` (`:494-504`) and returns the sum of the three tables (`:511`). Live count_sql counts cells and triangulation (475 on the chart); the seed says cells + convergence + contradictions (`asset_registry_seed.ts:1735-1740`), so the live registry differs from the seed: migration 661 PART 3 changed it to cells + triangulation because triangulation was "a whole table counted by nobody" (a cockpit-truth defect) and left `bodha_convergence` uncounted. It reads the shared MSR table without a class filter, so the registry orders it after every MSR producer and the rerank (seed comment `:1723-1727`). Census direct 12 / transitive 39 (13 direct in the seed-derived post-1210 closure: `mi_darshana` added). Frozen under the t3 definition (2026-09-11).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1723` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_sangati.py:457`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_cdlm_cells`; count_sql tables: `bodha_cdlm_cells`, `bodha_triangulation` | census CEN-R |
| live rows / floor | 475 / 70 (chart 482012f1, count_sql scope) — count_sql names `bodha_cdlm_cells` + `bodha_triangulation`; the writer also writes `bodha_convergence` | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bo_laksana`, `bo_karanajala`, `bo_sudarshana`, `bo_nakshatra_semantic`, `bo_arudha`, `bo_special_lagna`, `bo_vargottama_dhana`, `bo_laksana_rerank` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 12 / transitive 39; seed-derived closure (post-1210): direct 13 / transitive 39; direct dependents: `bo_anveshana`, `bo_cdlm_summary`, `bo_chart_gestalt`, `bo_drishti`, `bo_pramana_mapa`, `bo_pratijna`, `bo_samvada`, `bo_upaya`, `ka_kshetra`, `ka_yojaka`, `mi_darshana`, `ph_nimitta`, `ph_sankrama` | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_cdlm_cells`: 17 non-test py/ts/tsx files reference it (11 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `ka_yojaka.py`, `ph_phaladesa.py`, `ph_sankrama.py`, `engine.py`, `assetClearSpec.ts`, `instrument.ts` +5 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | 2 capability module(s): `L2_bodha/query_domain_reading.ts`, `L2_bodha/query_remedies.ts`; `density_contract` declared on 0 (saved rev-1 reading) | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t3, 2026-09-11; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 8dd3fe42 complete/build (2026-09-11) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): bodha_triangulation (bo_sangati.py:504), bodha_cdlm_cells (bodha_writers/_idempotency.py:248 via bo_sangati.py → bodha_writers/_idempotency.py:replace_prior_cdlm_cells), bodha_cdlm_cells (bodha_writers/_idempotency.py:253 via bo_sangati.py → bodha_writers/_idempotency.py:replace_prior_cdlm_cells) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served† | FAIL | 2 module(s): query_domain_reading.ts, query_remedies.ts; declaring density_contract: 0 |
| Build | Build.completion | FAIL | build record rows_written=535 disagrees with live=475 (count_sql total over 2 table(s): bodha_cdlm_cells, bodha_triangulation; chart 482012f1); target_table bodha_cdlm_cells alone: 430 row(s), whole table — context, not the compared figure |
| Build | Build.history | PARTIAL | latest run complete, but 25 error(s) and 8 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-06): BLOCKED: upstream dependency(ies) bo_karanajala, bo_laksana did not complete in this run; skipped to avoid building on incomplete data |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 8dd3fe42 complete/build (2026-09-11) |
| Complete (information) | Complete.depth | PARTIAL | 430 rows, 59 cols; fully populated 30; NEVER populated ['dynamic_system_id', 'dynamic_maha_lord', 'dynamic_antar_lord', 'dynamic_window_start_iso', 'dynamic_window_end_iso', 'tradition_view_id', 'subdomain_row', 'subdomain_col', 'contradicting_signal_pairs_jsonb', 'shared_factor_keys_jsonb', 'shared_signals_high_convergence_count', 'recurring_pattern_markers_array', 'cross_ayanamsha_cell_stability_score', 'asymmetry_… |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width 8/30 built column(s) (26.7%) selected by 2 capability module(s); dark: ['asymmetric_linkage_flag', 'ayanamsha_id', 'build_id', 'chart_id', 'citation_human', 'citation_ref', 'contradicting_sig… |

**PASS cells (compact):** Ldgr.source_presence (citation_ref populated on 430/430 rows); Vocab.identity (declared key (chart_id, ayanamsha_id, build_id, snapshot_type, dynamic_system_id, dynamic_maha_lord, dynamic_a…); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.exercised (47 executed run(s) of 119 build_run_assets row(s), scope(s): asset_set, global, layer, last executed 2026-09-1…); Build.dep_liveness; Count.floor (count_sql total=475, floor=70, delta=+405).

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **FAIL** — 4 module(s) reach it by code: L2_bodha/query_domain_reading.ts, L2_bodha/query_remedies.ts, L2_bodha/query_triangulation.ts, register_d8_assess_domain.ts; 6 served select(s) of its table; no referencing capability that serves it declares density_contract; Idem.pattern rev 2 reads **PASS**.

**Build.dag rev 2 (E6 g+h; recompute over the saved registry BEFORE migration 1210, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`, reads-match clause):** PASS (not in the recompute's L2 gate-diff list; no change from the saved rev-1 PASS) The saved census cell Build.dag PASS † above is the rev-1 reading.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| `bo_sangati-Build.completion` | Build (completion) | real (attribution; cause read in code, not measured) | build record 535 vs live 475 (60 short). The writer returns `total_cells + total_conv + total_triang` (`:511`) and the live `count_sql` names cells and triangulation only, so the 60 is consistent with the `bodha_convergence` rows (one per domain per ayanamsha with signals, 12 × 5 would be 60; the table is unreadable to the census login, MF-L2-002, so the equality is NOT verified). A read-only `SELECT count(*) FROM bodha_convergence WHERE chart_id = '482012f1…'` on a login that can read it settles it. CF-02. |
| `bo_sangati-Dens.served` / census cell Dens.served † | Dens | real (rev 1 and offline rev 4) | the saved rev-1 FAIL reads 2 modules and 0 contracts; the offline rev-4 static scan reads FAIL on main's code: 4 modules reach the table by code (`query_domain_reading.ts`, `query_remedies.ts`, `query_triangulation.ts`, `register_d8_assess_domain.ts`) with 6 served selects and none declares `density_contract`. Served columns are 8 of 30 (26.7%); `citation_ref`, `citation_human`, `verification_pass_status`, `shared_factor_count` and the contribution columns are dark (Reach, information). FD-1; CF-04. |
| census cell Complete.depth (information) | Complete (information) | information | 430 rows table-wide, 59 columns, 30 fully populated; NEVER populated include `shared_factor_keys_jsonb` and `shared_signals_high_convergence_count` (the CDLM-side carriers of T1 §3.4 "shared roots visible"), `contradicting_signal_pairs_jsonb`, `subdomain_row/col` and the L3 hooks `dynamic_*`/`tradition_view_id`. CF-16 (tier-dependent: the counting rule is TG-L2-021), CF-17. |
| `bo_sangati-Build.history` | Build (history) | history | latest run complete; 25 errors and 8 aborts on record (latest error 2026-08-06, `BLOCKED: upstream bo_karanajala, bo_laksana did not complete`). CF-10. |
| `bo_sangati-Earn.build_record`, `-Cost.baseline`, `-Carr.detector` | Earn, Carr | detector | instrument absent / no D1-D3 detector; CF-05, CF-07. |
| census: Null/Narr | Null, Narr | detector | `prose_fields = [citation_human]` declared: the string embeds the shared-signal count and the signal count (`bo_sangati.py:365`, `:440`; AST census 2 composed sites). CF-14. |
| `bo_sangati-Ldgr.source_presence` (cell present) | Ldgr | information | `citation_ref` populated on 430/430 rows; PASS. |

## 3 · Disposition

**keep (P)** — the matrix is built and complete on its columns (every cell present, citations populated); the open items are the completion attribution (a code-readable cause) and a density contract on four served modules, plus the carriers of the layer's defining "shared roots" rule, which are empty and tier-dependent. None changes what the asset is.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Declare density contracts on the CDLM-serving modules

- **Answers:** Dens.served FAIL (rev 1) and the offline rev-4 FAIL; CF-04
- **Change:** declare `density_contract` on `query_domain_reading.ts` and `query_triangulation.ts` (and on `query_remedies.ts` where it serves `bodha_cdlm_cells`) stating the handler's actual pagination, facets (`ayanamsha_id`, domain pair) and backed `empty_reason`; `register_d8_assess_domain.ts` is the umbrella assessor: declare there only what that handler does. Add `verification_pass_status` to the CDLM select where it is served so the tier is carried
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L2_bodha/query_domain_reading.ts`, `query_triangulation.ts`, `query_remedies.ts`, `platform/src/lib/retrieval/registry/layers/register_d8_assess_domain.ts`
- **Failing-first test and mutation:** response-shape tests (empty page, truncated page, tier present); mutation: drop one declaration → the census Dens cell reads FAIL again
- **Output change:** none
- **Blast radius:** consumers of the three tools: `query_domain_reading` is named by `vidhi/inquiry/compiler.ts`, `retrieval/synthesis/instrument.ts` and `surface_gateway.ts`, `registry/mcp_capability_bridge.ts` and the umbrella registrations `register_d5_fanout.ts`, `register_d6_synergy.ts`, `register_d8_assess_domain.ts`; `query_remedies` by `pipeline/compiled_floor_adapter.ts`, `contract/tool_metadata.ts` and `lel/prospective_ledger.ts`; `query_triangulation` only by its registration and knowledge metadata. Additive metadata and one extra selected column; no row or value changes
- **Rebuild:** none (TypeScript only)
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-dependent: TGH-T3-26 and N-22 applicability

### FD-2 · Narr golden-value test for the declared prose columns

- **Answers:** Narr gate (NO_DETECTOR); CF-14; Track A §5 (per-asset Narr golden tests)
- **Change:** golden fixture: two domains sharing n signals out of m → `citation_human` (`:365`, `:440`) states exactly n and m from `shared_signal_count` and the row's signal count
- **Files / declaration / migration:** a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can find it; no asset or registry change
- **Failing-first test and mutation:** failing-first: the test fails on a writer whose narrated value differs from the cited fact; mutation: change one composed value (a house number, a count) in the writer → the test fails
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 13: `bo_anveshana`, `bo_cdlm_summary`, `bo_chart_gestalt`, `bo_drishti`, `bo_pramana_mapa`, `bo_pratijna`, `bo_samvada`, `bo_upaya`, `ka_kshetra`, `ka_yojaka`, `mi_darshana`, `ph_nimitta`, `ph_sankrama`; transitive 39); the touched surface is a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can f
- **Rebuild:** none
- **Gate it moves:** Narr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent (SS ruling 2026-10-01 defines narration; declarations 1.6.0 exists)

### FD-3 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (re-derivation): recompute each cell's shared-signal set from `bodha_msr_signals.domains_affected_array` (signals whose domains contain both A and B) and the convergence counts per domain, compare to the stored rows; deterministic set arithmetic.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 13: `bo_anveshana`, `bo_cdlm_summary`, `bo_chart_gestalt`, `bo_drishti`, `bo_pramana_mapa`, `bo_pratijna`, `bo_samvada`, `bo_upaya`, `ka_kshetra`, `ka_yojaka`, `mi_darshana`, `ph_nimitta`, `ph_sankrama`; transitive 39); the touched surface is a new check in the Nikaṣa inspector tooling (Track E) registered for this asset
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-02** — Producer attribution: multi-table writers, rider rows and shared tables (count scope). *This asset:* 535 written vs 475 counted: convergence rows
- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* FD-1
- **CF-14** — Narr fidelity (golden-value) tests per L2 narration writer. *This asset:* declared `citation_human`
- **CF-16** — Shared-root carriers (T1 3.4): the empty columns and their counting rule. *This asset:* `shared_factor_keys_jsonb`, `shared_signals_high_convergence_count` NEVER populated
- **CF-17** — Complete.depth: never-populated columns (declare, populate or drop). *This asset:* never-populated columns
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage D3 (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id, snapshot_type, domain_row, domain_col)` for cells; `(chart_id, ayanamsha_id, snapshot_type, domain)` for convergence; `(chart_id, ayanamsha_id, question_class, tradition)` for triangulation (registry partition and the `ON CONFLICT` at `:133`). Fingerprint: the linkage strengths, shared-signal counts, `convergence_score`, `cross_tradition_count`, concordance values, `citation_ref`/`citation_human`; shared signal ids resolved to signal natural keys. **Volatile:** row ids, `build_id`, `computed_at`, `engine_version`. Expected 475 chart rows in the two counted tables plus the convergence rows.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the pairwise shared-signal matrix, the convergence score and the triangulation, all referencing signal ids and never restating values.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation) (design in FD-3)
- **Opportunities (never blocking):** populate the shared-root carriers once the counting rule exists; serve the citation columns.

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t3 on 2026-09-11 (NIRMANA_SUPERSESSION_RECORD §2.3). Migration 1210 added no edge to this row. Manifest staleness has two severities (`src/lib/nirmana-elevation/definitions.ts:379-396`, `monitor.ts:374-393`): a `depends_on`, layer or membership change makes `assertManifestMatchesRegistryIdentity` throw (the monitor reports `plan_adaptation_required`; `dispatch_nirmana_campaign_wave.py` refuses the wave); a change to `count_sql`, `natural_key_partition`, `catalog_status`, `target_table` or `integrity_check_sql` only trips `assertManifestMatchesRegistry` (`evidence_refresh_required`: accepted evidence must be refreshed). The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3), so the staleness has no running consumer, but the frozen-definition DB row still reads `frozen`. **A production rebuild (SS REVIEW):** its direct dependents (`bo_anveshana`, `bo_cdlm_summary`, `bo_chart_gestalt`, `bo_drishti`, `bo_pramana_mapa`, `bo_pratijna`, `bo_samvada`, `bo_upaya`, `ka_kshetra`, `ka_yojaka`, `mi_darshana`, `ph_nimitta`, `ph_sankrama`) re-run after it in DAG order; seed-derived transitive closure 39 assets. **F-3 invariant (this asset carries or derives from MSR signal ids):** it must be rebuilt strictly after every MSR producer and not before a later MSR regeneration in the same window (`msr_rebuild_order_guard.py`, F3 `plan_invariant.md`); I-6: an unguarded MSR replace took the `kala_*` tables from 4 rows to 0 and erased the canonical chart's five Kāla tables on 2026-09-08; charts 1c826d5a and cb73cd3d (all-v4 ids) make the guard mandatory; see INDEX §7. Idempotent per-chart delete-then-insert of three tables; thirteen direct dependents (including `bo_pratijna`'s declared edge and `mi_darshana`) follow, 39 transitively. It must run after `bo_laksana_rerank` (seed ordering).

## 8 · Questions for Strategic Suvarṇa

1. CF-02: confirm the 60-row gap is the convergence table (a read of `bodha_convergence` on a login that can select it), then choose the count scope (CF-02).
2. CF-16: what is the counting rule for "independent support" so the empty shared-root columns can be filled or retired (TG-L2-021)?

**SS rulings (N-59, 2026-10-01; decision sheet `DECISION_SHEET_L2_v1_0.md` (PR #2841); (R) = provisional until the J1 review). The questions above are kept for the record.**

- **Q-L2-01 - accepted.** The produced-table set of this asset is declared (option A) with a detector clause; `count_sql` is neither widened nor narrowed. The reader SELECT on the 10 unreadable `bodha_*` tables goes first (they are owned by `data_plane_l2_owner` and pinned in the ownership preflight, so it is a D6 plan with hash as REVIEW, not an amjis_app migration); the gap in this asset's count is confirmed from the tables before the detector is written. TI-L2-01, TI-L2-02.
- **Q-L2-02 - accepted.** The module's `density_contract` is declared as what the handler does (`paginated: false`, the true `empty_reason`; precedent `query_cdlm_summary.ts:144`, `query_chart_gestalt.ts:64`). No rebuild. TI-L2-03.
- **Q-L2-14 (R) - accepted.** One independence rule: root = fact subject (plus varga where the subject is a varga sign), replacing sangati's fact-id fallback; `shared_factor_keys_jsonb` and `shared_factor_count` are written from it. The unit is on the J1 reviewers' list BY NAME. Batched. TI-L2-22, TI-L2-31.
- **Q-L2-12 - accepted.** This asset is in the CF-03 batch: the registry migration and the seed alignment (seed TO live) are pre-approved now; its floor is restated to the achieved count AFTER the one rebuild. TI-L2-10, TI-L2-24.
- **Layer-wide (Q-L2-18, Q-L2-19, sequencing).** Build.history counts only runs since the last writer or registry change (L0 Q11 carried; TI-L2-13) and Carr uses a D3 stratified sample with the section N.5 resolver, PASS only if every sampled row re-derives (L0 Q13 grading; TI-L2-14); both are read after the one coherent L2 rebuild on main's code, in which no asset is rebuilt twice.
