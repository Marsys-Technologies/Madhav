---
asset_id: ga_condition
layer: L1 Gaṇita (ga_*)
artifact: ASSET_ELEVATION_BRIEF
version: "1.0-provisional"
status: "PROVISIONAL — until J1; may register gaps, may not certify"
produced_by: exec-suvarna
produced_on: 2026-10-01
plan_item: A.L1 (briefs, dispositions, designs)
census_revision_used: "saved census `00_ARCHITECTURE/briefs/suvarna/layers/census/census_L1.json` (generated 2026-09-30T20:22:28+05:30, chart 482012f1, inspector 2a78ec64d on campaign/nikasha-test, pre-REGISTRY_REVISION; criterion revisions then: Build.dag 1, Build.target 1, Idem.pattern 1, Dens.served 1, no Null/Narr), with the `ga_prashna` cells read from the post-grant rerun `census/after_reader_grant/census_L1.json` (generated 2026-09-30T20:30:02+05:30; every other cell identical). NOT re-measured: main's inspector is at REGISTRY_REVISION 6 at the base commit (7 on origin/main 066c58587: the revision note names a NA_CAUSES addition for Carr; the criterion bodies were not diffed beyond that) and the lane has no DB access."
template_revision: "ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)"
layer_instance: "00_ARCHITECTURE/briefs/suvarna/layers/L1/L1_LAYER_INSTANCE_v1_0.md (1.0-rev1, PROVISIONAL)"
base_commit: "main 3311b0a06"
disposition: "keep (P)"
disposition_proposal_approver: "Steward (G16)"
decisions_applied: "SS answers logged 2026-10-01 and applied: Build.history window (L0 Q11: yes, runs since the last writer/registry change), Dens applicability (L0 Q2: wherever a served surface is reached; mixed-authority tables need a real tier), count_sql scope (L0 Q19: primary table, multi-table declared), the argala authority answer (L1 is the authority, L2 references); I-11 diagnosis (RLS) from the independent review; dispositions proposed, not yet answered by SS; SS ruling N-62 (2026-10-02) on the L1 decision sheet: every recommendation accepted, (R) items provisional until J1, recorded at the end of this brief"
track_i_items: [I-11, I-13, I-28, I-29, I-30, I-35]
ledger_gap_ids: [ga_condition-Idem.pattern, ga_condition-Build.completion, ga_condition-Earn.build_record, ga_condition-Cost.baseline, ga_condition-Complete.depth, ga_condition-Build.history, ga_condition-Carr.detector]
---
# ga_condition — Planetary condition composite (dignity, avasthā, motion, combustion, friendship, 0–1 score) and per-varga avasthās

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

A unified per-graha, per-ayanamsha condition: dignity, avasthā (bālādi, jāgradādi, dīptādi), motion state, combustion, naisargika/tātkālika/pañcadhā friendship, graha-yuddha, and a 0–1 condition score into `ga_condition_composite` (natural key `(chart_id, ayanamsha_id, graha)`; `ga_writers/ga_condition_writer.py:1-20`), plus per-varga avasthā rows into `chart_facts` (`_insert_per_varga_avastha_rows`, `:1183`). Idempotency: `DELETE FROM ga_condition_composite WHERE chart_id, ayanamsha_id` then INSERT (`:1647`), and an owner-receipt-gated category-scoped delete for the `chart_facts` rows (`:1196`). `varga_dignity_composite` reads `chart_divisionals` (migration 658 header). A FORENSIC guard asserts the Sun in Capricorn is not exalted/own/mūlatrikoṇa.

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields declared `['citation_human']` | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1479` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_condition.py:13` (heavy: `run_substep` per ayanamsha); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `ga_condition_composite` (target; 9 grahas × 5 ayanamshas = 45 rows per chart) and `chart_facts` (`graha_avastha_%_per_varga` categories; 2 categories named for this asset in `fact_category_ownership`) | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 2,970 / 2,880 (Δ +90): count_sql total = 45 composite + 2,925 `chart_facts` per-varga rows; `asset_throughput` lit / **45**; seed floor literal 2880 (45 + 2,835, migration 310) | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_positions`, `ga_vargas`, `ga_dashas` (live and seed); the writer also reads `bg_dignity_reference` (`ga_condition_writer.py:615`, MF-L1-006; L0 reads exempt on main) | layer instance §2.5 |
| blast radius | live registry incl. migration 1210 (applied; verified live 2026-10-01 14:37Z per the independent review): direct 4; census (2026-09-30, pre-1210): direct 4 / transitive 51; seed + 1210 reconstruction names 4 direct dependent(s): `bo_laksana`, `ga_medical`, `ga_vastu`, `ph_muhurta` | census `blocking_radius`; live count from the independent review; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry) |
| code readers / served surface | `get_condition_composite.ts:91` (declarations `read_evidence`; 24 of 27 built columns selected; 1 module declaring `density_contract`) | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | DP04 condition decomposition (layer instance §1.4); 4 direct / 51 transitive dependents (`ga_medical`, `ga_vastu`, L2 1, L4 1) | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.completion | FAIL | build record rows_written=45 disagrees with live=2970 (count_sql total over 2 table(s): ga_condition_composite, chart_facts; chart 482012f1); target_table ga_condition_composite alone: 135 row(s), whole table — context, not the compared figure |
| Build | Build.history | PARTIAL | latest run complete, but 14 error(s) and 8 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-07): post-write integrity check failed: integrity_check_sql → False |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 7a6f34fb complete/build (2026-09-07) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 7a6f34fb complete/build (2026-09-07) |
| Complete | Complete.depth | PARTIAL | 135 rows, 31 cols; fully populated 19; NEVER populated ['avastha_lajjitaadi', 'avastha_sayanadi', 'speed_degrees_per_day', 'graha_yuddha_result'] |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Count.floor; Vocab.identity; Dens.served †; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — reported, not graded — width 24/27 built column(s) (88.9%) selected by 1 capability module(s); dark: ['build_id', 'chart_id', 'id']; depth 100.0% (a capability query reads it with no literal row pin (upper bound)); Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.



**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `_evidence/rollup_saved_L1.json` beside this file): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build FAIL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **PARTIAL** — STRUCTURAL: 1 module(s) reach it by code: L1_ganita/get_condition_composite.ts; a referencing capability declares density_contract but L1_ganita/get_condition_composite.ts: no tier column in its served select (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`_evidence/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree PARTIAL; checkable NO_DETECTOR*; fidelity_test PARTIAL; lint PASS; schema_default PARTIAL; blank_rows NO_DETECTOR*.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling; **artefact** = a saved census cell that reads a measurement the inspector's role could not make (pending a read by a role that can). A row naming several classes counts under its leading label.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| ga_condition-Build.completion | Build | real | FAIL: `rows_written` 45 vs live 2,970. `build_ga_condition_substep` returns only the composite `inserted` count (`:1704`) while the `chart_facts` per-varga rows go through `_insert_per_varga_avastha_rows`, which returns nothing (`:1183`), so the build record under-reports what the writer writes; register R42 already reads this as a basis mismatch. The `count_sql` claims 2,925 `chart_facts` rows while `fact_category_ownership` gives the asset 90 (MF-L1-005); CF-02 |
| ga_condition-Complete.depth | Complete | real | PARTIAL (135 rows whole table): `avastha_lajjitaadi` and `avastha_sayanadi` are hard-set to None ("require chart-level context; store None", `ga_condition_writer.py:1511-1513`) although the same writer writes `graha_avastha_sayanadi` rows to `chart_facts` (`:1289-1361`); `speed_degrees_per_day` (`speed = pos.get("speed")`, `:1477`) and `graha_yuddha_result` (`:1607`, no assignment found) are also never populated. Honest nulls, but four advertised columns of 31 carry nothing |
| brief: sequencing hazard with `ga_vargas` access | Build/Earn | real | the varga composite reads `chart_divisionals` (`:769-780`; migration 658 header: `_compute_varga_composite` looks the divisional label up, F-C8); whether the per-varga avasthā rows read it too was not traced. `varga_dignity_composite` is non-NULL on 45/45 live rows (the independent review of HEAD f9448c509 (reader queries, 2026-10-01; not in the repo)), so the rows built 2026-09-07 saw the table. If the builder role is RLS-blind now (CF-16, I-11), a rebuild of this asset before the access fix would write the column NULL again (the loader returns None when the table is unavailable or has no data, `:770`). Not verified by running |
| ga_condition-Build.history | Build | history | PARTIAL: 14 errors / 8 aborts; latest error 2026-09-07 `post-write integrity check failed: integrity_check_sql → False`; the latest run completed. Migration 658 documents a conjunct that was red by design until the F-C8 fix landed; CF-10 |
| brief: verification-tier literals | Earn | real | 6 bare tier literals (indicative regex); CF-17 |
| brief: Narr fidelity (declared `citation_human`) | Narr | real | declared; offline: Narr.agree PARTIAL (reverse leg unavailable), Narr.fidelity_test PARTIAL (7 test files call the builder; none names `citation_human`), Narr.lint PASS; CF-15 |
| brief: Dens (offline rev 4) | Dens | detector | PARTIAL: contract declared but `get_condition_composite.ts` has no tier column in its served select (the composite table has none); CF-04 |
| ga_condition (no cell) | Ldgr | detector | no `Ldgr.source_presence` cell (MF-L1-003); the composite table's source column was not found; CF-08 |
| brief: undeclared L0 read | Build.dag | information | `bg_dignity_reference` read at `:615`; exempt as L0 bedrock on main; the historical collision with `ga_structural` (both deleted/re-inserted two `chart_facts` categories; migration 416/419 removed the edge) is the CF-12 background |
| ga_condition-Earn / Cost / Carr / Idem | Earn, Cost, Carr, Idem | detector / stale | CF-05, CF-07; the Idem ledger row is stale (census PASS) |

## 3 · Disposition

**keep (P)** — load-bearing (DP04; 51 transitive dependents), with a conformant delete-then-insert pattern and a FORENSIC guard. The Build.completion FAIL is a writer-reporting defect plus an overlapping `count_sql` predicate, not missing data; the four NULL columns are honest but incomplete. Fix designs, not a different disposition.

Approver under Track A brief §10: **Steward (G16)**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Report every row the writer writes (composite + per-varga `chart_facts`)

- **Answers:** census Build.completion FAIL; MF-L1-005; CF-02
- **Change:** make `_insert_per_varga_avastha_rows` return the inserted count and add it to `inserted` in `build_ga_condition_substep` (`:1704`) so `rows_written` = rows the writer wrote on both tables, then confirm it equals the asset's own `count_sql` (composite + the per-varga categories) on a rerun. If `count_sql` is instead scoped to the primary table (SS Q19 at L0) or to the owned categories (45 composite + 90 owned `chart_facts` rows = 135), the count falls from 2,970 against a live floor of 2,880 and Count.floor would FAIL: the floor is re-declared in the same registry migration (floors equal the achieved count after a build, CLAUDE.md §N.4) Never change `WriterBase`
- **Files / declaration / migration:** `platform/python-sidecar/ga_writers/ga_condition_writer.py:1183-1215, 1688-1704`; the `count_sql` scope per CF-02 (a registry migration, only if the overlap with `ga_structural` is confirmed)
- **Failing-first test and mutation:** failing-first: a rerun's `rows_written` equals the asset-owned rows (composite 45 + per-varga rows) — today 45 vs 2,970; mutation: drop the added count and the test fails
- **Output change:** none
- **Blast radius:** `asset_throughput` records only; cockpit counts (cosmetic). No data change
- **Rebuild:** takes effect on the next dispatch; the asset-set rerun is a production run (idempotent, no data change; REVIEW) — and must follow the CF-16 access fix (see the sequencing gap)
- **Gate it moves:** Build (completion)
- **Fix class:** writer code; **buildable before J1:** tier-independent (CF-02 registry half is tier-independent; the ownership rule is TG-L1-005)

### FD-2 · Populate `avastha_sayanadi` / `avastha_lajjitaadi` from the L1 facts, or drop the columns

- **Answers:** Complete.depth never-populated columns; L1 authority (§N.5)
- **Change:** `avastha_sayanadi` is already computed and stored as `graha_avastha_sayanadi` (`:1289-1361`): reference that value (same writer, same run) instead of a hard-coded None; for `avastha_lajjitaadi`, `speed_degrees_per_day` and `graha_yuddha_result` either source them from stored L1 facts (positions speed, ga_structural yuddha) or remove the columns (a migration) — an honest null stays an honest null where no L1 fact exists. SS chooses populate vs drop
- **Files / declaration / migration:** `ga_condition_writer.py:1511-1513, 1595-1607`; possibly a migration (DROP COLUMN needs SS approval; additive populate needs none)
- **Failing-first test and mutation:** failing-first: the four columns are non-NULL where the source fact exists; mutation: break the lookup and the column reads NULL
- **Output change:** yes if populated (new values in existing columns) — SS (R5)
- **Blast radius:** readers of `get_condition_composite.ts` see values where they saw NULL
- **Rebuild:** **needs production rebuild** of the asset (45 + 2,925 rows): REVIEW
- **Gate it moves:** Complete (information), Null (the honest-null claim)
- **Fix class:** data (output change) + writer code; **buildable before J1:** tier-independent for the sayanadi reference; tier-dependent for lajjitaadi/yuddha (which L1 fact authorises them)
- **Question for SS:** Populate the four NULL composite columns from L1 facts, or drop them?

### FD-3 · Guard the `ga_vargas` ordering (design only)

- **Answers:** sequencing hazard
- **Change:** the dependency `ga_condition` → `ga_vargas` is already declared; the hazard is the CF-16 access question. Gate any rebuild on the CF-16 read confirming the builder role can see `chart_divisionals` (`Build.dep_liveness` only checks the dependency is `lit` and fresh, which holds either way); the fix is CF-16's access fix plus an earned `lit` (a non-empty integrity conjunct on `ga_vargas`)
- **Files / declaration / migration:** none for this asset
- **Failing-first test and mutation:** the CF-16 detector (build record = live count) is what makes `dep_liveness` meaningful
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Build (dep_liveness)
- **Fix class:** detector/tooling; **buildable before J1:** tier-independent

### FD-4 · Tier literals, Narr test

- **Answers:** CF-17, CF-15
- **Change:** as `ga_positions` FD-1/FD-2 for this writer (6 literals; a golden test on the avasthā sentence)
- **Files / declaration / migration:** `ga_condition_writer.py`; a test beside `test_ga_condition.py`
- **Failing-first test and mutation:** as ga_positions
- **Output change:** none
- **Blast radius:** none for data
- **Rebuild:** none
- **Gate it moves:** Earn, Narr
- **Fix class:** writer code + test; **buildable before J1:** tier-independent

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-02** — Producer attribution on the shared `chart_facts` table: partition-scoped `count_sql`, `fact_category_ownership`, multi-table writers. *This asset:* FD-1: rows_written vs overlapping `count_sql`; `fact_category_ownership` names 90 rows vs 2,925 claimed
- **CF-16** — `chart_divisionals` reads 0 rows for every login role since the migration-1035 ownership change (RLS deny-all): an access incident, data probably intact, UNVERIFIED until read as owner or builder (Track I I-11). *This asset:* FD-3: reads `chart_divisionals`; rebuild only after the CF-16 access fix
- **CF-17** — Verification-tier string literals in L1 writers (CLAUDE.md §N.4: named constants from `verification_vocab.py`). *This asset:* FD-4: 6 literals
- **CF-15** — Narr golden tests that name the declared `citation_human` field (assertion on the sentence, not only on the builder). *This asset:* FD-4: declared; Narr.agree PARTIAL offline
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* offline PARTIAL: tier column absent
- **CF-08** — Ldgr: assets with no recognised citation column (six L1 cells with no reading). *This asset:* no Ldgr cell: one of six
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 14/8: history
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: composite: `(chart_id, ayanamsha_id)` exact; `chart_facts`: categories present in rows, owner-receipt gated
- **CF-13** — Build.dag reads-match: declared `depends_on` against the tables each L1 writer reads (missing edges, two back-reads). *This asset:* edges: declared edges match its table reads (`chart_divisionals`↔`ga_vargas`, `chart_dashas`↔`ga_dashas`); L0 read exempt
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* declared: `["citation_human"]`
- **CF-18** — Census population on shared tables: chart-scoped, partition-scoped cells for Complete / Ldgr / Vocab / Reach / Dens. *This asset:* whole-table cells: `Complete.depth` over 135 rows (all charts)

## 5 · Semantic fingerprint contract (for E5.5)

composite table: natural key `(chart_id, ayanamsha_id, graha)`; volatile: surrogate `id`, `build_id`, `computed_at`; `chart_facts` per-varga rows: the shared-table key `(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key)` over the `graha_avastha_%_per_varga` categories. Both partitions must be fingerprinted; the composite alone misses 2,925 rows.

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 45-row composite with its 0–1 score, the dignity/avasthā/friendship components stored separately (DP04), the per-varga avasthā rows, and the FORENSIC guard.
- **Carriage check chosen (T4 §4.1; one only):** D3 — recompute the avasthā and dignity components from stored positions and the L0 dignity table by a second path and compare.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Do the rows the writer produces on `chart_facts` count as this asset's `rows_written` (FD-1), and does `fact_category_ownership` get the per-varga categories (TG-L1-005)?
2. Populate or drop the four NULL composite columns?

## SS rulings (2026-10-02, decision N-62) for this asset

SS ruled the L1 decision sheet (`DECISION_SHEET_L1_v1_0.md`, PR #2844). Every recommendation is ACCEPTED with the specifics below; (R) items are provisional until the J1 review. S-L1 is the canonical chart first; the other two charts are the later stage S-L1b (separate REVIEW); S-L1 never waits for an optional item.

- Q-L1-16(c) accepted (R): one band table at this asset, cut points 0.4 / 0.7, NULL score = NULL / `unknown`, never `neutral` (I-28). Mandatory before S-L1.
- X2 accepted (R): the D1 fallback is visible and an integrity clause fails a fallback on a chart that has divisionals (I-29); the two affected charts are rebuilt in S-L1b, after the canonical run.
- Q-L1-04 accepted: declared multi-table, `count_sql` on the primary table, `rows_written` counts everything it writes (I-30).
- Q-L1-15 accepted, OPTIONAL: three columns from existing L1 facts; `speed_degrees_per_day` stays NULL, null-by-design, `[EXTERNAL_COMPUTATION_REQUIRED]` until `ga_positions` stores it; the column is not dropped (I-35).
