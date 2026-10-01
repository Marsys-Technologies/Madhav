---
asset_id: bo_yantra_mechanism
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
ledger_gap_ids: [bo_yantra_mechanism-Earn.build_record, bo_yantra_mechanism-Cost.baseline, bo_yantra_mechanism-Build.history, bo_yantra_mechanism-Build.dep_liveness, bo_yantra_mechanism-Carr.detector]
---
# bo_yantra_mechanism — Mechanism object: named, valenced CGM subgraphs (Yantra)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

Promotes already-detected structure into first-class `bodha_mechanisms` rows (CR-24/CR-25/CR-86): every `bodha_cgm_motifs` row 1:1, plus chain/circuit mechanisms from a cycle detector over the sign-dispositor graph and the house-to-house "lord sits in" graph, each with a valence derived from its member edges' `valence`, an edge-strength summary aggregated from `bo_karanajala`'s DR-7 values (never a new formula) and a centrality summary (`bo_yantra_mechanism.py` docstring). `@register("bo_yantra_mechanism")` at `bo_yantra_mechanism.py:590`, delete at `:608`, INSERT `ON CONFLICT … DO NOTHING` (`:78-95`) after the delete. 615 chart rows (600 motifs + 15 other is consistent with the 1:1 promotion, not verified), 1,868 table-wide, all rows `verification_pass_status = 'single'` (`query_mechanisms.ts:27`, an honest tier). Zero registry dependents but wide serving: `query_mechanisms.ts`, `reading_checklist.ts`, `register_d9_judgment.ts`. Migration 1210 added its `bo_bimba` edge (it reads `bodha_cgm_nodes`). Frozen under the t1 definition (2026-09-09).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1968`; seed `catalog_status` DRAFT, live CURRENT | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_yantra_mechanism.py:590`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_mechanisms`; count_sql tables: `bodha_mechanisms` | census CEN-R |
| live rows / floor | 615 / 1 (chart 482012f1, count_sql scope) | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bo_karanajala`, `bo_cgm_motifs`, `bo_cgm_paths`, `bo_bimba` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 0 / transitive 0; seed-derived closure (post-1210): direct 0 / transitive 0; direct dependents: none | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_mechanisms`: 12 non-test py/ts/tsx files reference it (11 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `taranga.py`, `taranga_service.py`, `envelope.ts`, `register_d9_judgment.ts`, `reading_checklist.ts`, `query_mechanisms.ts` +5 | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | 3 capability module(s): `L2_bodha/query_mechanisms.ts`, `reading_checklist.ts`, `register_d9_judgment.ts`; `density_contract` declared on 1 (saved rev-1 reading) | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t1, 2026-09-09; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 322b9f70 complete/build (2026-09-09) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): bodha_mechanisms (bo_yantra_mechanism.py:608) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Build | Build.history | PARTIAL | latest run complete, but 1 error(s) and 3 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-07-16): BLOCKED: upstream dependency(ies) bo_cgm_motifs, bo_cgm_paths, bo_karanajala did not complete in this run; skipped to avoid building on incomplete data |
| Build | Build.dep_liveness | PARTIAL | 1/3 declared dependencies lit at chart 482012f1 (or global); stale: ['bo_cgm_motifs (stale, chart 482012f1)', 'bo_cgm_paths (stale, chart 482012f1)'] — built, but an upstream has moved since |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 322b9f70 complete/build (2026-09-09) |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width ≥ 8/24 built column(s) (33.3%), a lower bound: L2_bodha/query_mechanisms.ts select(s) a run-time column list selected by 3 capability module(s); dark: ['ayanamsha_id', 'build_id', 'centrality… |

**PASS cells (compact):** Ldgr.source_presence (citation_ref populated on 1868/1868 rows); Vocab.identity (declared key (chart_id, ayanamsha_id, build_id, mechanism_class, fingerprint_hash): 0 duplicate(s)); Dens.served† (1 module(s): query_mechanisms.ts; declaring density_contract: 1); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.completion (rows_written=615 = live=615 (count_sql over the target table; chart 482012f1)); Build.exercised (16 executed run(s) of 23 build_run_assets row(s), scope(s): asset_set, global, layer, last executed 2026-09-09); Count.floor (live=615, floor=1, delta=+614); Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build PARTIAL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **PARTIAL** — 4 module(s) reach it by code: L2_bodha/query_mechanisms.ts, reading_checklist.ts, register_d9_judgment.ts, platform-mcp/src/tools/register_p1_aliases.ts; a referencing capability declares density_contract but L2_bodha/query_mechanisms.ts: tier carriage not established (a run-time select; Idem.pattern rev 2 reads **PASS**.

**Build.dag rev 2 (E6 g+h; recompute over the saved registry BEFORE migration 1210, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`, reads-match clause):** FAIL — missing edge `bo_yantra_mechanism → bo_bimba` (reads `bodha_cgm_nodes` at `bo_yantra_mechanism.py:309`). **Migration 1210 added it; PASS afterwards (1210 header).** The saved census cell Build.dag PASS † above is the rev-1 reading.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| census cell Dens.served † | Dens | detector (rev 4 PARTIAL) | saved rev-1 PASS (1 module declaring a contract); the offline rev-4 scan reads PARTIAL: `query_mechanisms.ts` declares `density_contract` (`:295`) but "tier carriage not established (a run-time select)" because the select column list is built at run time. A static select (or a declared tier column) would let the detector read PASS. FD-1; CF-04. |
| `bo_yantra_mechanism` Build.dag rev 2 (E6gh recompute) | Build (dag) | information | the pre-1210 recompute read FAIL for the missing edge `bo_yantra_mechanism → bo_bimba` (`bodha_cgm_nodes` read at `bo_yantra_mechanism.py:309`); migration 1210 added it and the rev-2 detector reads PASS afterwards (1210 header). Resolved by 1210; kept here so the frozen-manifest consequence is visible (§7). |
| `bo_yantra_mechanism-Build.dep_liveness` | Build (dep_liveness) | history/ordering | 1 of 3 declared dependencies lit at the census; `bo_cgm_motifs` and `bo_cgm_paths` stale (built, upstream moved since). After 1210 it declares four (`bo_bimba` added). An ordering fact for the next L2 rebuild, not an asset defect. CF-10 / §7. |
| `bo_yantra_mechanism-Build.history` | Build (history) | history | latest run complete; 1 error and 3 aborts on record (latest error 2026-07-16, `BLOCKED: upstream bo_cgm_motifs, bo_cgm_paths, bo_karanajala did not complete`). CF-10. |
| `bo_yantra_mechanism-Earn.build_record`, `-Cost.baseline`, `-Carr.detector` | Earn, Carr | detector | instrument absent / no D1-D3 detector; CF-05, CF-07. |
| census: Null/Narr | Null, Narr | detector | `prose_fields` = [`citation_human`, `mechanism_name`] declared: `citation_human` embeds the converging-graha count (`:397`) and valence, net/natural score and dignity modifier (`:571`); `mechanism_name` embeds the valence (`:565`); member-label strings (`:344 :352 :388 :472 :480`) are not declared. CF-14. |
| `bo_yantra_mechanism-Idem.pattern` (R-note) | Idem | information | the writer deletes the whole chart (`:608`) then inserts `ON CONFLICT DO NOTHING`; the delete is chart-wide, not scoped to a partition, which is correct while it is the sole writer of `bodha_mechanisms`. |

## 3 · Disposition

**keep (P)** — every census cell is clean except history, ordering and a detector limit; the asset is sound and widely served. The preserved kernel is the 1:1 motif promotion with honest `single` tier and aggregated, not invented, edge strengths.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Let Dens read the tier carriage

- **Answers:** offline rev-4 Dens PARTIAL (run-time select); CF-04
- **Change:** select a fixed column list including `verification_pass_status` in the served query of `query_mechanisms.ts` (or declare the tier column through the descriptor) so the detector can establish tier carriage statically
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L2_bodha/query_mechanisms.ts`
- **Failing-first test and mutation:** the rev-4 Dens scan reads PASS for the asset; mutation: remove the column from the select → PARTIAL
- **Output change:** none
- **Blast radius:** consumers of the `query_mechanisms` tool: `retrieval/registry/layers/reading_checklist.ts`, `register_d9_judgment.ts` (the judgment tool), `pipeline/compiled_floor_adapter.ts`, `platform-mcp/src/server.ts` and `platform-mcp/src/tools/registry_bridge.ts`; selecting one more column adds a response field; the judgment path reads mechanisms, so its output gains the tier value only
- **Rebuild:** none
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-dependent: Dens rule (T3 §26) and N-22

### FD-2 · Narr golden-value test for the declared prose columns

- **Answers:** Narr gate (NO_DETECTOR); CF-14; Track A §5 (per-asset Narr golden tests)
- **Change:** golden fixture: a mechanism with k converging grahas, valence v, net/natural score s and dignity modifier m → `citation_human` (`:397`, `:571`) and `mechanism_name` (`:565`) state exactly k, v, s, m from the row; the forwarded motif name equals the source motif's
- **Files / declaration / migration:** a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can find it; no asset or registry change
- **Failing-first test and mutation:** failing-first: the test fails on a writer whose narrated value differs from the cited fact; mutation: change one composed value (a house number, a count) in the writer → the test fails
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 0: none; transitive 0); the touched surface is a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can f
- **Rebuild:** none
- **Gate it moves:** Narr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent (SS ruling 2026-10-01 defines narration; declarations 1.6.0 exists)

### FD-3 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (re-derivation): recompute each mechanism's valence and strength summary from its member edges' stored `valence`/`computed_strength` and re-run the cycle detector on `dispositor` and `lordship`+`occupancy` edges; compare.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 0: none; transitive 0); the touched surface is a new check in the Nikaṣa inspector tooling (Track E) registered for this asset
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* FD-1
- **CF-14** — Narr fidelity (golden-value) tests per L2 narration writer. *This asset:* declared prose columns
- **CF-15** — depends_on audit: declared edges versus what each writer reads. *This asset:* 1210 added `bo_bimba`; re-audit declared edges against reads
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage D3 (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL and stale-upstream ordering
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id, mechanism_class, fingerprint_hash)` (registry partition; the content hash is part of the key). Fingerprint: `mechanism_class`, `mechanism_name`, `valence`, `edge_strength_min/max`, `centrality_summary_jsonb`, `source_motif_id` resolved to the motif natural key, `member_edge_ids_array` resolved to edge natural keys, `citation_ref`/`citation_human`. **Volatile:** `mechanism_id`, raw edge/motif ids, `build_id`, `computed_at`, `engine_version`. Expected 615 rows on the chart.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** 1:1 promotion of motifs, deterministic cycle detection, valence and strength aggregated from stored edge values.
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation) (design in FD-3)
- **Opportunities (never blocking):** the dark columns (`edge_strength_*`, `centrality_summary_jsonb`, `member_edge_ids_array`, 16 of 24) are the mechanism's own evidence and not served by default.

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t1 on 2026-09-09 (NIRMANA_SUPERSESSION_RECORD §2.3). Migration 1210 (applied; verified live 2026-10-01 14:37Z per the coordinator) added this row's direct edge(s) `bo_bimba`, so its frozen manifest is stale against the registry fingerprint (1210 header, CONSEQUENCES 1: the identity check throws on any `depends_on` change, so the monitor reads `plan_adaptation_required`). Manifest staleness has two severities (`src/lib/nirmana-elevation/definitions.ts:379-396`, `monitor.ts:374-393`): a `depends_on`, layer or membership change makes `assertManifestMatchesRegistryIdentity` throw (the monitor reports `plan_adaptation_required`; `dispatch_nirmana_campaign_wave.py` refuses the wave); a change to `count_sql`, `natural_key_partition`, `catalog_status`, `target_table` or `integrity_check_sql` only trips `assertManifestMatchesRegistry` (`evidence_refresh_required`: accepted evidence must be refreshed). The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3), so the staleness has no running consumer, but the frozen-definition DB row still reads `frozen`. **A production rebuild (SS REVIEW):** its direct dependents (none) re-run after it in DAG order; seed-derived transitive closure 0 assets. It has no dependents of its own, so a rebuild is local, but it must run after `bo_cgm_motifs` and `bo_cgm_paths` (both stale upstream at the census).

## 8 · Questions for Strategic Suvarṇa

1. CF-04: is a declared tier column in the descriptor an acceptable way to give the Dens detector a static tier read, or must the select be static?
