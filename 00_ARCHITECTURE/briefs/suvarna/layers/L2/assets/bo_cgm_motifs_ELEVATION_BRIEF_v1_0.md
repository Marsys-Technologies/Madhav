---
asset_id: bo_cgm_motifs
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
ledger_gap_ids: [bo_cgm_motifs-Earn.build_record, bo_cgm_motifs-Cost.baseline, bo_cgm_motifs-Dens.served, bo_cgm_motifs-Build.history, bo_cgm_motifs-Carr.detector]
---
# bo_cgm_motifs — CGM structural motifs, sub-graphs and topology summary

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question. Dispositions are proposals under Track A brief §10; every fix marked **needs production rebuild** is a REVIEW item for Strategic Suvarṇa.

## 0 · Identity — what the asset is

Derives the CGM topology layer from `bodha_cgm_nodes` and `bodha_cgm_edges` in one deterministic pass per ayanamsha: motifs (`bodha_cgm_motifs`: mutual reception, stellium, parivartana chain, yoga cluster, mutual aspect, triangle), sub-graphs and a chart topology summary, each carrying edge lineage that resolves through `bodha_cgm_edges.constituent_fact_ids_array` to `chart_facts.fact_id` (`bo_cgm_motifs.py` docstring; the LCA-6 fix explains why the native had zero motifs before WP-2.3). `@register("bo_cgm_motifs")` at `bo_cgm_motifs.py:887`; it deletes and rewrites three tables (`:913-916`) but returns only the motif count (`:929`), which is also the registry `count_sql`. 600 chart motif rows (floor 0; table-wide 1,811, 16 of 16 columns populated). Direct dependents `bo_upaya` and `bo_yantra_mechanism`. Frozen under the t1 definition (2026-09-09).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1771` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/bo_cgm_motifs.py:887`; registry `has_writer` = True | writers dir, census `Build.registered` |
| target table(s) | `bodha_cgm_motifs`; count_sql tables: `bodha_cgm_motifs` | census CEN-R |
| live rows / floor | 600 / 0 (chart 482012f1, count_sql scope) | census `live_rows`, `Count.floor` |
| catalog_status | CURRENT | census |
| depends_on (declared, seed incl. migration 1210) | `bo_bimba`, `bo_karanajala` | seed `asset_registry_seed.ts` (live may differ by migrations 913/1084/730/676) |
| blast radius | census (saved, pre-1210): direct 2 / transitive 19; seed-derived closure (post-1210): direct 2 / transitive 19; direct dependents: `bo_upaya`, `bo_yantra_mechanism` | census `blocking_radius`; seed + migration 1210 closure (`/Users/Dev/suvarna-evidence/A_L2/closure_L2.json`) |
| code readers | `bodha_cgm_motifs`: 8 non-test py/ts/tsx files reference it (3 outside bodha_writers/, brahmagyan/ and bo_*.py writers): `query_cgm_motifs.ts`, `tool_name_bridge.ts`, `source_query_availability.ts` | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src (py/ts/tsx; paths containing `test` and `/generated/` excluded; run 2026-10-01) |
| served surface | 1 capability module(s): `L2_bodha/query_cgm_motifs.ts`; `density_contract` declared on 0 (saved rev-1 reading) | census reach |
| Nirmāṇa freeze | frozen by Nirmāṇa (t1, 2026-09-09; NIRMANA_SUPERSESSION_RECORD §2.3) | NIRMANA_SUPERSESSION_RECORD §2.3 |
| role / scoring mode | neither (supplies what manifestation and time rest on); contribution scoring (chart-product layer) | layer instance §2.5 (TG-L2-019), census `L2.scoring` |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: the after-grant saved census named in the frontmatter (inspector 2a78ec64d, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access.

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count).

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 4a821dad complete/build (2026-09-09) |
| Idem | Idem.pattern† | PASS | DELETE FROM the asset's own table(s) (delete-then-insert): bodha_cgm_motifs (bo_cgm_motifs.py:913) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Dens | Dens.served† | FAIL | 1 module(s): query_cgm_motifs.ts; declaring density_contract: 0 |
| Build | Build.history | PARTIAL | latest run complete, but 25 error(s) and 10 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-08-06): BLOCKED: upstream dependency(ies) bo_bimba, bo_karanajala did not complete in this run; skipped to avoid building on incomplete data |
| Cost (information, D3) | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 4a821dad complete/build (2026-09-09) |
| Count (information) | Count.floor | N/A | target_floor=0: the registry declares zero rows complete — there is no floor to breach (live=600) |
| Complete (information) | Complete.width | NOT_GENERIC | no declared universe for this asset — declaring one is the first width gap |
| Reach (information) | Reach.fields | NOT_GENERIC | reported, not graded — width 12/16 built column(s) (75.0%) selected by 1 capability module(s); dark: ['build_id', 'chart_id', 'computed_at', 'fingerprint_hash']; depth 100.0% (a capability query reads it with no literal … |

**PASS cells (compact):** Ldgr.source_presence (citation_ref populated on 1811/1811 rows); Vocab.identity (declared key (motif_id): 0 duplicate(s)); Build.registered; Build.contract; Build.target†; Build.dag†; Build.count_integrity; Build.completion (rows_written=600 = live=600 (count_sql over the target table; chart 482012f1)); Build.exercised (45 executed run(s) of 120 build_run_assets row(s), scope(s): asset_set, global, layer, last executed 2026-09-0…); Build.dep_liveness; Complete.depth.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; N/A reads NO_DETECTOR because `NA_RULE_DECISIONS` is empty on main; not a re-measure, not a certification): Ldgr PASS · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens FAIL · Build PARTIAL.

**Offline static re-scans on main's code** (indicative, not a census; method in `INDEX.md` §1): Dens.served rev 4 reads **FAIL** — 1 module(s) reach it by code: L2_bodha/query_cgm_motifs.ts; 2 served select(s) of its table; no referencing capability that serves it declares density_contract; a tier column is selected without a contract in: L2_bodha/query_cgm_motifs.ts; Idem.pattern rev 2 reads **PASS**.

**Build.dag rev 2 (E6 g+h; recompute over the saved registry BEFORE migration 1210, `/Users/Dev/suvarna-evidence/E6gh/recompute_result.json`, reads-match clause):** PASS (not in the recompute's L2 gate-diff list; no change from the saved rev-1 PASS) The saved census cell Build.dag PASS † above is the rev-1 reading.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset’s rows, writer, registry row, declaration or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row from the 2026-09-27 run (`asset_gaps.jsonl` @ 2a78ec64d, not on main) that the saved 2026-09-30 census no longer reads as written; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **real-or-SS-question** = read in code, not measured by the census, whose verdict needs a ruling.

| gap id (ledger or census cell) | gate | class | note |
|---|---|---|---|
| `bo_cgm_motifs-Dens.served` / census cell Dens.served † | Dens | real (measured at rev 1 and again by the offline rev-4 static scan) | 1 module `query_cgm_motifs.ts` reaches the table with 2 served selects; the offline rev-4 scan reads FAIL: "a tier column is selected without a contract in: query_cgm_motifs.ts" (it selects `verification_pass_status` but declares no `density_contract`). The handler paginates by `limit` only (`query_cgm_motifs.ts:61`, no offset or total), so the contract would honestly state that. FD-1; CF-04. |
| code: `bo_cgm_motifs.py:913-916`, `:929` | Build | information | the writer writes three tables (motifs, sub-graphs, topology) and returns the motif count only, which equals `count_sql`; the other two tables are unreadable to the census login (MF-L2-002), so their rows are not checked by any gate. CF-02. |
| `bo_cgm_motifs-Build.history` | Build (history) | history | latest run complete; 25 errors and 10 aborts on record (latest error 2026-08-06, `BLOCKED: upstream bo_bimba, bo_karanajala did not complete`). CF-10. |
| `bo_cgm_motifs-Earn.build_record`, `-Cost.baseline`, `-Carr.detector` | Earn, Carr | detector | instrument absent / no D1-D3 detector; CF-05, CF-07. |
| census: Null/Narr | Null, Narr | detector | `prose_fields` = [`citation_human`, `motif_name`] declared (`motif_name` is served, `query_cgm_motifs.ts:71`; stellium house and chain length are stated in it, `:342`, `:400`); no fidelity test measured. CF-14. |

## 3 · Disposition

**keep (P)** — the asset is complete on the census (all 16 columns populated, completion equals live) and its one measured shortfall is the missing density declaration on a served surface that already selects a tier column; that is a small served-surface fix, not a reason to change the asset.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Declare the density contract on `query_cgm_motifs.ts`

- **Answers:** Dens.served FAIL (rev 1) and the offline rev-4 FAIL; CF-04
- **Change:** add `density_contract` to the capability stating what the handler does: `paginated: false` (limit only, no offset/total) unless pagination is added, `facets: ['ayanamsha_id','motif_class']`, `empty_reason` true only if the handler sets `content.empty_reason` (the standard is the comment at `query_question_lenses.ts:55-61`: an auto-stamped `empty_reason` is an unbacked claim); optionally add `total_matching`/`more_available` so a truncated list is visible
- **Files / declaration / migration:** `platform/src/lib/retrieval/registry/layers/L2_bodha/query_cgm_motifs.ts` (types: `retrieval/registry/types.ts` `CapabilityDescriptor`)
- **Failing-first test and mutation:** response-shape test: an empty page emits the declared `empty_reason`, a limit-truncated page says so; mutation: drop the declaration → the census Dens cell reads FAIL again
- **Output change:** none
- **Blast radius:** the consumers of the `query_cgm_motifs` tool are its registration (`L2_bodha/index.ts`), the name bridge (`registry/tool_name_bridge.ts`), the knowledge/availability metadata (`knowledge/source_query_availability.ts`, `producer_editorial_review.ts`, `editorial_review.ts`) and the response-budget trimmer that reads `density_contract`; the change is additive metadata (no row or value changes); no strict parser of the response was found by grep
- **Rebuild:** none
- **Gate it moves:** Dens
- **Fix class:** served surface (TS); **buildable before J1:** tier-dependent: TGH-T3-26 (who owns a Dens FAIL; serving is [TRANSFERS]) and the N-22 per-gate applicability rules

### FD-2 · Narr golden-value test for the declared prose columns

- **Answers:** Narr gate (NO_DETECTOR); CF-14; Track A §5 (per-asset Narr golden tests)
- **Change:** golden fixture: a graph with a stellium of n nodes in house h and a parivartana chain of length k → `motif_name` and `citation_human` (`:342`, `:400`, citation sites) must state exactly h, n and k from the stored motif row
- **Files / declaration / migration:** a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can find it; no asset or registry change
- **Failing-first test and mutation:** failing-first: the test fails on a writer whose narrated value differs from the cited fact; mutation: change one composed value (a house number, a count) in the writer → the test fails
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 2: `bo_upaya`, `bo_yantra_mechanism`; transitive 19); the touched surface is a new test beside `platform/python-sidecar/tests/l2/` (one file per writer), registered in the declaration `evidence.prose_fields` so `Narr.fidelity_test` can f
- **Rebuild:** none
- **Gate it moves:** Narr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling (test); **buildable before J1:** tier-independent (SS ruling 2026-10-01 defines narration; declarations 1.6.0 exists)

### FD-3 · Carr detector

- **Answers:** Carr.detector NO_DETECTOR; CF-07
- **Change:** D3 (re-derivation): recompute stellium (≥3 mutually conjoined nodes in a house), mutual reception (2-cycle of dispositor edges) and parivartana chains from `bodha_cgm_edges` and compare to the stored motif rows; the detector definitions are in the docstring.
- **Files / declaration / migration:** a new check in the Nikaṣa inspector tooling (Track E) registered for this asset; no asset file changes
- **Failing-first test and mutation:** a seeded mismatch the check must report and a clean pass it must report as zero; mutation: corrupt one row → count ≥ 1
- **Output change:** none
- **Blast radius:** no stored value changes, so none of this asset's registry dependents is affected by it (direct 2: `bo_upaya`, `bo_yantra_mechanism`; transitive 19); the touched surface is a new check in the Nikaṣa inspector tooling (Track E) registered for this asset
- **Rebuild:** none
- **Gate it moves:** Carr (NO_DETECTOR → measured)
- **Fix class:** detector/tooling; **buildable before J1:** tier-dependent: per-asset D1/D2/D3 assignment is TGH-T3-02; the detector itself needs no tier clause

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-04** — Dens (serving density) on the L2 served modules. *This asset:* FD-1
- **CF-02** — Producer attribution: multi-table writers, rider rows and shared tables (count scope). *This asset:* three tables written, one counted
- **CF-14** — Narr fidelity (golden-value) tests per L2 narration writer. *This asset:* declared `citation_human`, `motif_name`
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset. *This asset:* carriage D3 (§6)
- **CF-10** — Build.history PARTIAL is a record of past errors; no edit changes it. *This asset:* history PARTIAL
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* Earn/Cost instrument

## 5 · Semantic fingerprint contract (for E5.5)

Natural key `(chart_id, ayanamsha_id, snapshot_type, fingerprint_hash)` (registry partition; `fingerprint_hash` is content-derived and therefore part of the key, not volatile). Fingerprint: `motif_class`, `motif_name`, member node natural keys (not ids), `involved_edge_ids_array` resolved to edge natural keys, valence, `citation_ref`/`citation_human`. **Volatile:** `motif_id`, `build_id`, `computed_at`. Expected 600 rows on the chart, unchanged by an idempotent rebuild; sub-graph and topology tables are fingerprinted separately.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** motifs detected deterministically over the real node/edge set with edge lineage to L1 `fact_id`s (§N.5).
- **Carriage check chosen (T4 §4.1; one only):** D3 (re-derivation) (design in FD-3)
- **Opportunities (never blocking):** declare the motif-class universe; expose `fingerprint_hash` and lineage columns (4 of 16 columns are dark).

## 7 · Rebuild and frozen-manifest consequences

Frozen manifest: Nirmāṇa froze this asset under definition t1 on 2026-09-09 (NIRMANA_SUPERSESSION_RECORD §2.3). Migration 1210 added no edge to this row. Manifest staleness has two severities (`src/lib/nirmana-elevation/definitions.ts:379-396`, `monitor.ts:374-393`): a `depends_on`, layer or membership change makes `assertManifestMatchesRegistryIdentity` throw (the monitor reports `plan_adaptation_required`; `dispatch_nirmana_campaign_wave.py` refuses the wave); a change to `count_sql`, `natural_key_partition`, `catalog_status`, `target_table` or `integrity_check_sql` only trips `assertManifestMatchesRegistry` (`evidence_refresh_required`: accepted evidence must be refreshed). The Nirmāṇa campaign is OFF (NIRMANA_SUPERSESSION_RECORD §1, §3), so the staleness has no running consumer, but the frozen-definition DB row still reads `frozen`. **A production rebuild (SS REVIEW):** its direct dependents (`bo_upaya`, `bo_yantra_mechanism`) re-run after it in DAG order; seed-derived transitive closure 19 assets. Idempotent per-chart delete-then-insert of three tables; `bo_yantra_mechanism` promotes these rows 1:1 and `bo_upaya` reads them, so both re-run after it.

## 8 · Questions for Strategic Suvarṇa

1. CF-04: must the contract state `paginated: false` (honest) or should the handler first gain offset/total (a served-surface change)?
