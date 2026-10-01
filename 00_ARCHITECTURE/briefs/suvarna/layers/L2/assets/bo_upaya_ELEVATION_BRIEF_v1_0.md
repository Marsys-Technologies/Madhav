---
asset_id: bo_upaya
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
nirmana_freeze: "t1, 2026-09-10"
ledger_gap_ids: [bo_upaya-Idem.pattern, bo_upaya-Build.completion, bo_upaya-Earn.build_record, bo_upaya-Cost.baseline, bo_upaya-Dens.served, bo_upaya-Build.history, bo_upaya-Build.dep_liveness, bo_upaya-Carr.detector]
---
# bo_upaya — Remediation Map (RM): resonances, remedy prescriptions and four ancillary tables

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

Reads `bodha_msr_signals`, L1 `chart_facts` (shadbala, bhava bala, combustion/debility/dignity rollups) and `brahma_remedy_corpus` and writes six tables: `bodha_rm_resonances` (one per graha per ayanamsha: weakness and remedy priority, `resonance_score_v1`), `bodha_rm_remedy_prescriptions` (1-3 per resonance, grounded to the G27 corpus, `resonance_match_score_v1`) and `bodha_rm_chart_summary`, `bodha_rm_dosha_remedy_bundles`, `bodha_rm_pattern_remedies` (`bo_upaya.py` docstring, INSERTs `:58-158`). `@register("bo_upaya")` at `bo_upaya.py:1898`; chart deletes of the three ancillary tables at `:1934-1936`, then per ayanamsha `replace_prior_rm_dasha_windowed`, `replace_prior_rm_prescriptions`, `replace_prior_rm_resonances` (`:1952-1954`). **R244 on main:** the writer once deleted the prescriptions parent without first deleting the legacy `bodha_rm_dasha_windowed_prescriptions` child (NO ACTION foreign key), so every rebuild would fail; the fix (PR #2773, merged 2026-09-30T15:55Z, commit 9fecaecda) restores the legacy delete in front of the prescriptions delete and ships `tests/l2/test_bo_upaya_source_order.py`. The saved census (20:30 IST = 15:00Z that day) and the layer instance (which records #2773 as open) PREDATE that merge. Live rows 180 = 45 resonances + 135 prescriptions; build record 240. Daśā-window prescriptions are no longer produced at L2 (`UNAVAILABLE_AT_L2`, DP-SD-015). Direct dependents `bo_pramana_mapa`, `bo_samvada`, `ka_kshetra`, `ph_pratikara`. Frozen under the t1 definition (2026-09-10).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1807` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_upaya.py:1898`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_rm_resonances`; count_sql tables: `bodha_rm_resonances`, `bodha_rm_remedy_prescriptions` | census CEN-R |
| live rows / floor | 180 / 180 (chart 482012f1, count_sql scope) — count_sql names resonances + prescriptions (180 = 45 + 135); the writer also writes three more tables | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bo_laksana`, `bo_sangati`, `ga_structural`, `ga_dashas`, `bo_cgm_motifs` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 4 / transitive 17; seed-derived closure (post-1210): direct 4 / transitive 17; direct dependents: `bo_pramana_mapa`, `bo_samvada`, `ka_kshetra`, `ph_pratikara` | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_rm_resonances`: 16 non-test py/ts/tsx files reference it (12 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `cr_status.ts`, `assetClearSpec.ts`, `query_rm_resonances.ts`, `query_rm_dosha_remedy_bundles.ts`, `query_rm_chart_summary.ts`, `query_rm_pattern_remedies.ts` +6 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | 2 capability module(s): `L2_bodha/query_remedies.ts`, `L2_bodha/query_rm_resonances.ts`; `density_contract` declared on 0 (saved rev-1 reading) | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t1, 2026-09-10; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run fcdcd284 complete/build (2026-09-09) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): bodha_rm_resonances (bodha_writers/_idempotency.py:430 via bo_upaya.py → bodha_writers/_idempotency.py:replace_prior_rm_resonances), bodha_rm_resonances (bodha_writers/_idempotency.py:435 via bo_upaya.py → bodha_writers/_idempotency.py:replace_prior_rm_resonances), bodha_rm_remedy_prescriptions (bodha_writers/_idempotency.py:445 via bo_upaya.py → bodha_writer… |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served† | FAIL | 2 module(s): query_remedies.ts, query_rm_resonances.ts; declaring density_contract: 0 |
| Build | Build.completion | FAIL | build record rows_written=240 disagrees with live=180 (count_sql total over 2 table(s): bodha_rm_resonances, bodha_rm_remedy_prescriptions; chart 482012f1); target_table bodha_rm_resonances alone: 135 row(s), whole table — context, not the compared figure |
| Build | Build.history | PARTIAL | latest run complete, but 27 error(s) and 11 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-10): BLOCKED: upstream dependency(ies) bo_cgm_motifs did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | PARTIAL | 4/5 declared dependencies lit at chart 482012f1 (or global); stale: ['bo_cgm_motifs (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run fcdcd284 complete/build (2026-09-09) |
| Complete (information) | Complete.depth | PARTIAL | 135 rows, 24 cols; fully populated 18; NEVER populated ['is_chara_karaka_role', 'associated_motifs_array'] |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width 17/22 built column(s) (77.3%) selected by 2 capability module(s); dark: ['build_id', 'chart_id', 'ephemeris_audit_jsonb', 'resonance_score_formula_version', 'snapshot_type']; depth 100.0% (a … |

**PASS cells (compact):** Ldgr.source_presence (citation_ref populated on 135/135 rows); Vocab.identity (declared key (chart_id, ayanamsha_id, build_id, snapshot_type, graha): 0 duplicate(s)); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.exercised (47 executed run(s) of 123 build_run_assets row(s), scope(s): asset_set, global, layer, last executed 2026-09-0…); Count.floor (count_sql total=180, floor=180, delta=+0).

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build FAIL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **NO_DETECTOR** — 1 serving-root file(s) naming bodha_rm_resonances lose the string scanner's sync (an unbalanced quote, a nested template literal, or a regex literal holding a quote desynced it): platform-mcp/src/tools/registry_bridge.ts; its served select and density_contract cannot be read — never FA; Idem.pattern rev 2 reads **PASS**.

**Build.dag rev 2 (E6 g+h; recompute over the saved registry BEFORE migration 1210, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`, reads-match clause):** FAIL — missing edge `bo_upaya → bo_bimba` (reads `bodha_cgm_nodes` at `bo_upaya.py:575`; reachable transitively via `bo_cgm_motifs`, `bo_sangati`, so ordering holds but the edge is undeclared). **Migration 1210 deliberately did NOT add it** (`TrackI/edges_evidence.md:91`), so this FAIL remains. The saved census cell Build.dag PASS † above is the rev-1 reading.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| R244 / `bo_upaya-Idem.pattern` (saved cell PASS, ledger row stale) | Idem | stale + real-in-live (live rebuild unproven) | code on main now matches the ruling (`bo_upaya.py:1952-1954`, offline rev-2 scan PASS, source-order test present): the saved census predates #2773, so the layer instance's "PASS withheld, unmerged live head" is out of date for CODE. What remains is the live proof: the live rebuild (B.U, its own wave; the R246 detector E1.6 follows) has not run, so the PASS is earned in code and unproven in production, and the register's "5 referencing rows on the canonical chart" was never re-measured (unreadable table). The annotation procedure for emits (withhold until B.U) is for SS to lift. |
| `bo_upaya-Build.completion` | Build (completion) | real (attribution; cause read in code, not measured) | build record 240 vs live 180 (60 short). The writer returns resonances + prescriptions + summary + bundles + patterns (`:1987`) and `count_sql` names the first two, so the 60 is consistent with the three ancillary tables (the chart summary 5 rows plus bundles and patterns; the tables are unreadable to the census login, MF-L2-002; NOT verified). CF-02. |
| `bo_upaya` Build.dag rev 2 (E6gh recompute; `TrackI/edges_evidence.md:91`) | Build (dag) | real (missing edge) | reads `bodha_cgm_nodes` at `bo_upaya.py:575` (the motif-to-node join behind `cgm_motifs_weakest_node`) with no declared `bo_upaya → bo_bimba` edge; the producer is reachable only transitively via `bo_cgm_motifs`, `bo_sangati`. Migration 1210 left it out deliberately ("a later, separately ruled migration"), so the rev-2 FAIL remains. FD-2; CF-15. |
| `bo_upaya-Dens.served` / census cell Dens.served † | Dens | detector (rev 1 FAIL; rev 4 NO_DETECTOR) | saved rev-1 FAIL (2 modules `query_remedies.ts`, `query_rm_resonances.ts`; 0 contracts); offline rev-4 unreadable (scanner desync in `registry_bridge.ts`). 17 of 22 built columns served. CF-04. |
| `bo_upaya-Build.dep_liveness` | Build (dep_liveness) | history/ordering | 4 of 5 declared dependencies lit; `bo_cgm_motifs` stale (built, upstream moved since). CF-10 / §7. |
| census: Null/Narr | Null, Narr | detector | `prose_fields` = [`prescription_detail_jsonb.$.maraka_contraindication_verdict.reason`, `citation_human`]: the maraka verdict reason is composed by f-string in both branches (`bo_upaya.py:1008`; the fact-missing branch `:989` is constant). CF-14. |
| census cell Complete.depth (information) | Complete (information) | information | 135 rows table-wide, 24 columns, 18 fully populated; NEVER populated `is_chara_karaka_role`, `associated_motifs_array` (the motif linkage the declared `bo_cgm_motifs` edge exists to feed). CF-17. |
| `bo_upaya-Build.history` | Build (history) | history | latest run complete; 27 errors and 11 aborts on record (latest error 2026-08-10, `BLOCKED: upstream bo_cgm_motifs did not complete`). CF-10. |
| `bo_upaya-Earn.build_record`, `-Cost.baseline`, `-Carr.detector` | Earn, Carr | detector | instrument absent / no D1-D3 detector; CF-05, CF-07. |

## 3 · Disposition

**keep (P)** — the code defect that blocked its rebuild (R244) is fixed on main; what remains is live proof (a production rebuild, SS REVIEW), an attribution mismatch and a density declaration. The asset is Track E's lane for the rebuild (E4.2, recorded not redesigned); the corpus-grounded prescriptions are the preserved kernel.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Re-measure Idem on main and plan the live proof

- **Answers:** R244 / the Idem cell; plan items E4.2, E1.6, B.U (recorded, not redesigned)
- **Change:** no code change in this lane: re-run the census Idem and Build checks for this asset on main (the fix is in), then schedule B.U (the live `bo_upaya` rebuild) as its own wave with the read-only pre-check that the legacy `bodha_rm_dasha_windowed_prescriptions` child rows and the FK referencing rows are measured before the delete; lift the withheld-PASS annotation only after B.U
- **Files / declaration / migration:** none (evidence and wave planning)
- **Failing-first test and mutation:** after B.U: the rebuild completes, `bodha_rm_remedy_prescriptions` is replaced and the legacy child table is empty; mutation: re-order the two deletes → `test_bo_upaya_source_order.py` fails (exists)
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 4: `bo_pramana_mapa`, `bo_samvada`, `ka_kshetra`, `ph_pratikara`; transitive 17); the touched surface is none (evidence and wave planning)
- **Rebuild:** needs production rebuild of `bo_upaya` (B.U, its own wave): REVIEW item for SS; its four direct dependents (`bo_pramana_mapa`, `bo_samvada`, `ka_kshetra`, `ph_pratikara`) re-run after
- **Gate it moves:** Idem, Build
- **Fix class:** detector/tooling + rebuild proof; **buildable before J1:** tier-independent

### FD-2 · Declare the `bo_upaya → bo_bimba` edge

- **Answers:** Build.dag rev-2 FAIL (missing edge); CF-15
- **Change:** append `bo_bimba` to `bo_upaya.depends_on` (append-only, idempotent, guarded, the shape of migration 1210); `bo_bimba` was previewed lit and fresh as the producer of 1210's `bo_laksana_rerank`/`bo_yantra_mechanism` edges and `bo_upaya` already follows it transitively, so the edge is acyclic and adds no wait
- **Files / declaration / migration:** one surgical migration (number = max+1 across origin heads at execution time) and the seed literal `asset_registry_seed.ts:1807-1830`
- **Failing-first test and mutation:** failing-first: the rev-2 Build.dag reads-match reads PASS for `bo_upaya`; mutation: remove the edge → FAIL
- **Output change:** none
- **Blast radius:** `bo_bimba`'s direct radius +1; `compute_upstream_hash` for `bo_upaya` changes once; the frozen t1 manifest fails the identity check; no change to the R244 rebuild order
- **Rebuild:** none for the migration; the next dispatch sees a changed upstream set
- **Gate it moves:** Build (dag)
- **Fix class:** registry/declaration only; **buildable before J1:** tier-independent in content; a DAG change 1210 deferred: needs its own ruling
- **Question for SS:** May the deferred `bo_upaya → bo_bimba` edge be added?

### FD-3 · Narr golden-value test for the declared prose columns

- **Answers:** Narr gate (NO_DETECTOR); CF-14; Track A §5 (per-asset Narr golden tests)
- **Change:** golden fixture: a gemstone remedy for a graha with a known L1 maraka status → `maraka_contraindication_verdict.reason` (`:1008`) states exactly the L1 maraka lord/house facts it cites in both branches; the fact-missing constant (`:989`) stays constant
- **Files / declaration / migration:** a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can find it; no asset or registry change
- **Failing-first test and mutation:** failing-first: the test fails on a writer whose narrated value differs from the cited fact; mutation: change one composed value (a house number, a count) in the writer → the test fails
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 4: `bo_pramana_mapa`, `bo_samvada`, `ka_kshetra`, `ph_pratikara`; transitive 17); the touched surface is a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can f
- **Rebuild:** none
- **Gate it moves:** Narr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent (SS ruling 2026-10-01 defines narration; declarations 1.6.0 exists)

### FD-4 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D1 for the prescriptions (resolve each prescription's `brahma_remedy_corpus` row and test that the remedy, planet and source citation match; the corpus is L0 `bg_remedies`, whose source ids resolve imperfectly) and D3 for the resonance score (recompute `resonance_score_v1` from the cited L1 shadbala and combustion facts).
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 4: `bo_pramana_mapa`, `bo_samvada`, `ka_kshetra`, `ph_pratikara`; transitive 17); the touched surface is a new check in the Nikaṣa inspector tooling (Track E) registered for this asset
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-02** — Producer attribution: multi-table writers, rider rows and shared tables (count scope). *This asset:* 240 written vs 180 counted: three ancillary tables
- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* Dens FAIL (rev 1); scanner-desync NO_DETECTOR at rev 4
- **CF-14** — Narr fidelity (golden-value) tests per L2 narration writer. *This asset:* declared prose
- **CF-17** — Complete.depth: never-populated columns (declare, populate or drop). *This asset:* never-populated columns
- **CF-15** — depends_on audit: declared edges versus what each writer reads. *This asset:* FD-2: rev-2 FAIL, a missing `bo_bimba` edge 1210 deferred
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage D1/D3 (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL and stale upstream
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural keys: resonances `(chart_id, ayanamsha_id, snapshot_type, graha)`, prescriptions per resonance and corpus remedy, and the three ancillary tables' own keys (`ON CONFLICT DO NOTHING` on bundles/patterns, `:115`, `:154`). Fingerprint: `resonance_score`, `weakest_rank_in_chart`, `remedy_priority_class`, prescription remedy ids (resolved to `brahma_remedy_corpus` natural keys), `resonance_match_score`, `prescription_detail_jsonb` including the maraka verdict, `citation_ref`/`citation_human`. **Volatile:** row ids, `build_id`, `computed_at`, `ephemeris_audit_jsonb` timestamps. Expected 45 resonances and 135 prescriptions on the chart.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** corpus-grounded prescriptions per graha, the resonance score and ranking, the maraka contraindication verdict, the ancillary bundles.
- **Carriage check chosen (T4 §4.1; one only):** D1 for the prescriptions (resolve each prescription's `brahma_remedy_corpus` row and test that the remedy, planet and source citation match; the corpus is L0 `bg_remedies`, whose source ids resolve imperfectly) and D3 for the resonance score (recompute `resonance_score_v1` from the cited L1 shadbala and combustion facts). (design in FD-4)
- **Opportunities (never blocking):** `dasha_windowed` remedies are intentionally absent at L2; the `associated_motifs_array` carrier the motif edge feeds is empty.

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t1 on 2026-09-10 (NIRMANA_SUPERSESSION_RECORD §2.3). Migration 1210 added no edge to this row. Manifest staleness has two severities (`src/lib/nirmana-elevation/definitions.ts:379-396`, `monitor.ts:374-393`): a `depends_on`, layer or membership change makes `assertManifestMatchesRegistryIdentity` throw (the monitor reports `plan_adaptation_required`; `dispatch_nirmana_campaign_wave.py` refuses the wave); a change to `count_sql`, `natural_key_partition`, `catalog_status`, `target_table` or `integrity_check_sql` only trips `assertManifestMatchesRegistry` (`evidence_refresh_required`: accepted evidence must be refreshed). The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3), so the staleness has no running consumer, but the frozen-definition DB row still reads `frozen`. **A production rebuild (SS REVIEW):** its direct dependents (`bo_pramana_mapa`, `bo_samvada`, `ka_kshetra`, `ph_pratikara`) re-run after it in DAG order; seed-derived transitive closure 17 assets. R244: the code fix is on main; the production rebuild has never run since it. Do not rebuild before B.U's pre-check; after it, its four direct dependents re-run: `bo_pramana_mapa`, `bo_samvada` (L2) and `ka_kshetra` (L3), `ph_pratikara` (L4).

## 8 · Questions for Strategic Suvarṇa

1. Lift the "PASS withheld" annotation for emits now that the fix is on main, or only after B.U proves it live?
2. CF-02: confirm the 60-row gap is the ancillary tables (read-only counts on a login that can select them).
