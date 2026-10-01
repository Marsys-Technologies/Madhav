---
asset_id: ga_vargas
layer: L1 Gaṇita (ga_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L1 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L1.json` (generated 2026-09-30T20:22:28+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr), with the `ga_prashna` cells read from the post-grant rerun `census/after_reader_grant/census_L1.json` (generated 2026-09-30T20:30:02+05:30; every other cell identical). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L1/L1_LAYER_INSTANCE_v1_0.md (1.0-rev1, PROVISIONAL)"
base_commit: "main 3311b0a06"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16); the restore and any rebuild are SS REVIEW items (production rebuild, output change F-A2)"
ledger_gap_ids: [ga_vargas-Idem.pattern, ga_vargas-Build.completion, ga_vargas-Earn.build_record, ga_vargas-Cost.baseline, ga_vargas-Count.floor, ga_vargas-Complete.depth, ga_vargas-Vocab.identity, ga_vargas-Build.history, ga_vargas-Carr.detector]
---
# ga_vargas — Divisional charts D1–D60 per ayanamsha (empty for the canonical chart under a `lit` record)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

D1–D60 divisional chart positions per ayanamsha written to `chart_divisionals` (`ga_writers/ga_vargas_writer.py`, 3,186 lines): the main varga loop, the D30-lords pass, cross-varga harmonics and two scope-cap sentinels, each batch written by `_write_rows_batch` with a per-run `cleared` set so that the delete grain (chart, ayanamsha, varga) and the insert grain do not delete each other's rows (`:2672-2740`, Nirmāṇa F-A3 fix, PR #1766); the graha longitudes are converted to UT by `jd_utc = jd_ut - tz / 24.0` (`:852`, F-A1 fix). The orchestrated writer runs one substep per ayanamsha (`ga_vargas.py:21-29`).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields declared `['citation_human']` | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1108` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_vargas.py:14` (heavy: `plan_substeps` per ayanamsha, `run_substep`); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `chart_divisionals` (count_sql `SELECT count(*) FROM chart_divisionals WHERE chart_id = $1`) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | **0** / 22,092 (Δ −22,092); `asset_throughput` **lit / 24,400** (last built 2026-09-07, layer instance LG-L1-002); seed floor literal 21635 (migration 439 re-set the live floor to 22092) | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_positions` | layer instance §2.5 |
| blast radius | census (pre-1210): direct 6 / transitive 61; seed + migration 1210 reconstruction names 6 direct dependent(s): `bo_laksana`, `bo_pratijna`, `ga_condition`, `ga_sade_sati`, `ga_strength`, `ga_structural` | census `blocking_radius`; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry in either direction) |
| code readers / served surface | `get_divisionals.ts:90` (declarations `read_evidence`); `coverage_matrix.ts`, `get_argala.ts`, `get_chart_snapshot.ts` and others (census modules: 4 in `Dens.served`, 1 declaring `density_contract`); read by `ga_dashas_writer.py:579` (`chart_divisionals`, D1 dignity) and by `bo_pratijna` through `ChartReaderV4` (Track I evidence) | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | divisional-chart foundation for dignity, strength, condition and yoga (layer instance §2.4 row 3.6); six direct / 61 transitive dependents | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.completion | FAIL | empty: live=0 (count_sql over the target table; chart 482012f1) and the registry does not declare zero rows complete (target_floor=22092); build record rows_written=24400 |
| Build | Build.history | PARTIAL | latest run complete, but 5 error(s) and 6 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-07): post-write integrity check failed: integrity_check_sql → False |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 0663e31b complete/build (2026-09-07) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 0663e31b complete/build (2026-09-07) |
| Count | Count.floor | FAIL | live=0, floor=22092, delta=-22092 |
| Complete | Complete.depth | NO_DETECTOR | NO_DETECTOR — table empty (0 rows, 31 cols): column population cannot be measured on no rows |
| Vocab | Vocab.identity | NO_DETECTOR | NO_DETECTOR — table empty: uniqueness under (id) is vacuous on 0 rows |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Dens.served †; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width 31/31 built column(s) (100.0%) selected by 4 capability module(s); dark: []; depth 100.0% (a capability query reads it with no literal row pin (upper bound)); Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.

**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `/Users/Dev/suvarna-evidence/A_L1/rollup_saved_L1.json`): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build FAIL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **PARTIAL** — STRUCTURAL: 7 module(s) reach it by code: L1_ganita/coverage_matrix.ts, L1_ganita/get_argala.ts, L1_ganita/get_chart_snapshot.ts, L1_ganita/get_divisionals.ts, L2_bodha/query_mechanisms.ts, register_d7_channel.ts (+1 more); a referencing capability declares density_contract but L1_ganita/get_argala… (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`/Users/Dev/suvarna-evidence/A_L1/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree PASS; checkable NO_DETECTOR*; fidelity_test PARTIAL; lint NO_DETECTOR; schema_default PARTIAL; blank_rows NO_DETECTOR*.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| ga_vargas-Build.completion / ga_vargas-Count.floor | Build, Count | real | FAIL: `chart_divisionals` has 0 rows for chart 482012f1 while the registry floor is 22,092 and the build record says `lit` with rows_written 24,400 (newest run touching the asset 2026-09-07 11:02, `complete`; the run before it, 10:57, errored `post-write integrity check failed`; layer instance LG-L1-002). The cause is NOT determined offline; see FD-1 |
| brief: unique index omits `fact_subject` (Nirmāṇa F-A2, still open) | Idem/Vocab | real | the conflict target is `(chart_id, graha, ayanamsha_id, varga, fact_category, fact_key)` with `ON CONFLICT … DO NOTHING` (`ga_vargas_writer.py:2606-2640`); rows that differ only in `fact_subject` (D30 lord chains: W2 recorded 60 → 10) are silently dropped; migration 654's comment keeps it "a KNOWN, separately-tracked defect"; no migration on main widens the index (grep of `platform/migrations` + `supabase/migrations`) |
| ga_vargas-Complete.depth / ga_vargas-Vocab.identity | Complete, Vocab | detector | NO_DETECTOR because the table is empty (0 rows): a consequence of the first gap, not a separate shortfall |
| brief: integrity contract conjunct (c) is red by design | Build | history | migration 654's D1-sign cross-check against `chart_facts.graha_position` returns false today, deliberately, until the corrected writer rebuilds (Moon reads Pisces here vs Aquarius in `chart_facts` on `raman`: the F-A1 offset); it should read true after FD-1's rebuild |
| ga_vargas-Build.history | Build | history | PARTIAL: 5 errors / 6 aborts; latest error 2026-09-07 `post-write integrity check failed` (the conjunct above); CF-10 |
| brief: verification tier literals | Earn | real | 5 bare tier literals in the emit path and 21 quoted tier strings in the module (indicative regex count, comparisons included); `chart_divisionals` carries a narrower CHECK vocabulary (`verification_vocab.RESTRICTED_TABLE_VOCAB`, migrations 206/210); CF-17 |
| brief: Narr (declared `citation_human`) | Narr | real | declared; offline fidelity PARTIAL (tests call the builder, none names the declared field); CF-15 |
| brief: Dens (offline rev 4) | Dens | detector | PARTIAL: contract declared but `get_argala.ts` has no tier column in its served select; the table is empty so no served read is exercised on this chart; CF-04 |
| brief: `ga_dashas` reads this table without a declared edge | Build.dag | real | Track I evidence §D: `ga_dashas` → `ga_vargas` missing edge (read at `ga_dashas_writer.py:579`); `ga_yoga` → `ga_vargas` direct edge missing (transitive path through `ga_structural` exists); CF-13 |
| ga_vargas-Earn / Cost / Carr | Earn, Cost, Carr | detector | CF-05; CF-07. The empty table shows that a `lit` status has no detector able to read false (CLAUDE.md §N.8): that is the Earn-class claim for this asset |

## 3 · Disposition

**keep (P)** — the asset is sound as designed (the W2 `changed` route's writer fixes F-A1 and F-A3 are on main, `ga_vargas_writer.py:852, 2672-2740`) and it is load-bearing (6 direct / 61 transitive dependents), so it is kept. It is the layer's only asset whose table is empty under a `lit` record; the open work is a read-only diagnosis first and then a restore — not a disposition other than keep. F-A2 (index grain) is a separate real output change.

Approver under Track A brief §10: **Steward (G16); the restore and any rebuild are SS REVIEW items (production rebuild, output change F-A2)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Diagnose, restore and re-earn `chart_divisionals` for the canonical chart (CF-16 anchor)

- **Answers:** census Build.completion FAIL and Count.floor FAIL; layer instance P1 / LG-L1-002
- **Change:** **Step 0, read-only (SS authorises the reads; the lane has no DB):** (a) `build_run_assets` ⋈ `build_runs` for `ga_vargas` on chart 482012f1 since 2026-09-07 (state, disposition, rows_written, error text); (b) per-chart counts in `chart_divisionals` (is the loss chart-specific or table-wide? migration 654's header reads `chart_divisionals` rows for chart 1c826d5a, so other charts held rows when 654 was written); (c) `pg_stat_user_tables.n_tup_del` / last autovacuum for `chart_divisionals`; (d) whether the `l1_data_plane_generation*` heads for `ga_vargas` point at a completed generation (unreadable to `suvarna_reader`, MF-L1-012). Only code writers of `chart_divisionals` found: `ga_vargas_writer.py` (insert `:2610,2639`; deletes `_idempotency.py:106`, `:2896` INVARIANT sentinels scoped to the chart) and the non-orchestrated legacy `brahma/l1/ganita/divisionals_writer.py:422`. **Step 1:** once the cause is known, rebuild `ga_vargas` for the chart (asset-set) with sequential single-asset dispatch, then re-earn the dependents that read it (FD-4 and CF-13).
- **Files / declaration / migration:** no file change for Step 0; Step 1 is a production run through the orchestrator (no `WriterBase` change)
- **Failing-first test and mutation:** failing-first: `chart_divisionals` chart count ≥ `target_floor` AND build record = live count (the `Build.completion` cell); migration 654's conjunct (c) turns true; mutation: delete a varga's rows for one ayanamsha and Build.completion must flip back
- **Output change:** yes after the F-A1 timing fix: about 22% of varga sign assignments differ from the pre-fix rows (W2 §3, cross-layer notice #1747) — any consumer that cached old varga signs sees changes
- **Blast radius:** 6 direct / 61 transitive dependents: `ga_condition`, `ga_strength`, `ga_structural`, `ga_sade_sati` read it (layer instance §2.5) and `bo_pratijna` (Track I); after the restore each must be re-earned, in DAG order
- **Rebuild:** **needs production rebuild** of `ga_vargas`, then `ga_condition`, `ga_strength`, `ga_dashas` (its `lord_natal_dignity_d1` reads this table, `ga_dashas_writer.py:664`), `ga_structural`, `ga_sade_sati`, `ga_yoga`: a REVIEW item for SS (production build)
- **Gate it moves:** Build (completion), Count (information); Earn (a `lit` status that can read false)
- **Fix class:** data (restore) + diagnosis; **buildable before J1:** tier-independent for the diagnosis and the restore
- **Question for SS:** Does SS authorise the read-only diagnosis queries in Step 0, and may the restore run as a single-asset dispatch (the W2 plan's "sequential single-asset dispatch" mitigation for the `ga_dashas`/`ga_vargas` ordering race, F-A13)?

### FD-2 · Widen the unique key to include `fact_subject` (F-A2)

- **Answers:** brief gap F-A2 (D30 lord chains collapse); Nirmāṇa W2 MUST
- **Change:** add `fact_subject` to `chart_divisionals_unique_idx` (new migration) and to the `ON CONFLICT` target in both upsert statements; then the D30-lords rows no longer collapse
- **Files / declaration / migration:** a new migration (number = max+1 across every origin head and both migration directories at execution time, Suvarṇa range per Track E); `ga_vargas_writer.py:2606-2640` (both `_UPSERT_*` statements); `registry` `target_floor` re-measured after the build
- **Failing-first test and mutation:** failing-first: two rows differing only in `fact_subject` both survive; mutation: restore the narrow conflict target and one row is dropped
- **Output change:** yes: more rows per D30 lord chain (W2: 60 → 10 collapsed); the floor 22,092 will rise; an output change goes to SS (R5)
- **Blast radius:** every reader of `chart_divisionals` (6 direct dependents) sees additional rows; `mv_chart_vargas_summary` pivots on the old grain (`210_ga6_chart_divisionals_extension.sql:100`, not re-read for the new grain)
- **Rebuild:** **needs production rebuild** (the same one as FD-1 if sequenced together)
- **Gate it moves:** Idem/Vocab (the key the Idem claim names), Count (floor refresh)
- **Fix class:** data (output change) + writer code + migration; **buildable before J1:** tier-independent
- **Question for SS:** Sequence F-A2 with the restore (one rebuild) or after it?

### FD-3 · Tier literals and Narr test

- **Answers:** brief gaps (tier literals; Narr)
- **Change:** as `ga_positions` FD-1 and FD-2 for this writer; note the table CHECK vocabulary (only `two_pass_verified`, `classical_match`, `divergent_flagged`, `single` are legal here)
- **Files / declaration / migration:** `ga_vargas_writer.py` emit path (5 literals); a test beside the writer tests
- **Failing-first test and mutation:** as ga_positions FD-1/FD-2
- **Output change:** none
- **Blast radius:** none for data
- **Rebuild:** none
- **Gate it moves:** Earn, Narr
- **Fix class:** writer code + test; **buildable before J1:** tier-independent

### FD-4 · Declare the `ga_dashas` / `ga_yoga` edges to this asset (design only; the migration is Track I's to rule)

- **Answers:** Build.dag reads-match (Track I evidence §D); CF-13
- **Change:** no change to this asset; the edges are on the consumers (`ga_dashas` depends_on += `ga_vargas`; `ga_yoga` += `ga_vargas`)
- **Files / declaration / migration:** registry `depends_on` (consumer rows); no file in this asset
- **Failing-first test and mutation:** Build.dag for the consumers reads PASS
- **Output change:** none
- **Blast radius:** declaring `ga_dashas` → `ga_vargas` changes the upstream hash and the dispatch order (a one-time rebuild signal per the 1210 header), and `ga_dashas`' 483,870 rows are rebuilt on the next dispatch if the hash drives it
- **Rebuild:** needs production rebuild of `ga_dashas` if its hash changes (REVIEW)
- **Gate it moves:** Build (dag)
- **Fix class:** registry/declaration; **buildable before J1:** tier-independent but needs its own review (Track I left it for "a later, separately ruled migration")

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-16** — `ga_vargas` restore and downstream re-earn: `chart_divisionals` empty for the canonical chart under a `lit` record. *This asset:* the anchor of the cascade: FD-1/FD-2
- **CF-13** — Build.dag reads-match: declared `depends_on` against the tables each L1 writer reads (missing edges, two back-reads). *This asset:* FD-4: missing edges on its consumers
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL: 5 errors / 6 aborts: the 2026-09-07 integrity error is conjunct (c) red by design
- **CF-17** — Verification-tier string literals in L1 writers (CLAUDE.md §N.4: named constants from `verification_vocab.py`). *This asset:* FD-3: 5 literals
- **CF-15** — Narr golden tests that name the declared `citation_human` field (assertion on the sentence, not only on the builder). *This asset:* FD-3: declared `citation_human`
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* offline PARTIAL: tier column absent in `get_argala.ts`
- **CF-08** — Ldgr: assets with no recognised citation column (six L1 cells with no reading). *This asset:* no Ldgr cell: one of six L1 assets with no `Ldgr.source_presence` reading (the table is empty; `chart_divisionals` has `citation_ref`)
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: scoped by `(chart_id, varga[, ayanamsha_id])` present in the rows (`_idempotency.py:94-109`) plus the per-run `cleared` set (F-A3 fix)
- **CF-14** — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual). *This asset:* documented no-op: `ga_vargas_writer.py:2779` `_update_asset_throughput` is a no-op and does not import `_telemetry` (LG-L1-001 (e)): not one of the eight
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* D3: re-derive a varga sign from the D1 longitude by the classical varga rule and compare; migration 654 conjunct (c) already compares D1 signs to `chart_facts`
- **CF-18** — Census population on shared tables: chart-scoped, partition-scoped cells for Complete / Ldgr / Vocab / Reach / Dens. *This asset:* whole-table cells: information

## 5 · Semantic fingerprint contract (for E5.5)

natural key as the (to-be-widened) unique index: `(chart_id, graha, ayanamsha_id, varga, fact_category, fact_key[, fact_subject])`; volatile: `id`, `build_id`, `build_id_uuid`, `computed_at`; the fingerprint must be taken over a rebuild AFTER FD-1/FD-2, never over the pre-fix rows (the F-A1 fix changes values, so an equality against the 2026-09-07 rows is not expected).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the D1–D60 position set with its vargottama and dignity categories; the FORENSIC gate for vargas (`forensic_gate_vargas`); the per-run `cleared` scope discipline (F-A3).
- **Carriage check chosen (T4 §4.1; one only):** D3 — re-derive a stratified sample of varga signs from the stored D1 longitude by the varga rule and compare (migration 654's conjunct (c) is an existing partial check against `chart_facts`).
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. May the read-only diagnosis of the empty `chart_divisionals` (Step 0) be authorised, and who owns the restore dispatch (production run, REVIEW)?
2. Is F-A2 (widen the unique key to `fact_subject`) in scope for the same rebuild (output change, R5)?
3. Should `ga_dashas` and `ga_yoga` declare a direct edge to `ga_vargas` (Track I left it open), given the declaration changes dispatch order and the dashas' upstream hash?
