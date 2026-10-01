---
asset_id: ga_structural
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
disposition_proposal_approver: "Steward (G16); moving the daridra-cancellation pass (FD-1) is an output change for SS"
decisions_applied: "SS answers logged 2026-10-01 and applied: Build.history window (L0 Q11: yes, runs since the last writer/registry change), Dens applicability (L0 Q2: wherever a served surface is reached; mixed-authority tables need a real tier), count_sql scope (L0 Q19: primary table, multi-table declared), the argala authority answer (L1 is the authority, L2 references); I-11 diagnosis (RLS) from the independent review; dispositions proposed, not yet answered by SS; SS ruling N-61 (2026-10-02) on the argala block AR-1..AR-6 of the L1 decision sheet (all recommendations accepted; (R) items provisional until J1), recorded in section 4 FD-5 and section 8"
track_i_items: [I-11, I-13, I-14, I-15, I-16, I-17, I-18, I-20]
ledger_gap_ids: [ga_structural-Idem.pattern, ga_structural-Build.completion, ga_structural-Earn.build_record, ga_structural-Cost.baseline, ga_structural-Build.history, ga_structural-Carr.detector]
---
# ga_structural — Structural enumeration (64 categories: aspects, conjunctions, dignity per varga, avasthā, yoga/doṣa labelling, argala, dispositors)

> **PROVISIONAL — until J1; may register gaps, may not certify.** Facts come from the repository and the saved census only (B.10); no figure here was invented. Where a fix depends on a Strategic Suvarṇa ruling it is stated as a question.

## 0 · Identity — what the asset is

Structural enumeration v2.0 (`ga_writers/ga_structural_writer.py:1-50`, 8,144 lines): multi-varga enumeration across 16 ṣoḍaśa vargas (dignity, aspects, conjunctions, parivartana, dispositor chains, vargottama), DB-catalog-driven yoga/doṣa labelling with real constituent `fact_id` lookups, 144-row argala matrices and a cancellation pass, one substep per ayanamsha. It adds categories GA3 does not emit (it deliberately never duplicates GA3's ṣaḍbala/aṣṭakavarga rows, `:30-40`). Idempotency: category-scoped delete-then-insert on `chart_facts` through the owner-receipt gate (`authorize_chart_fact_delete`, `_idempotency.py:44-55`).

| field | value | source |
|---|---|---|
| kind (declarations 1.6.0) | data; prose_fields declared `['citation_human']` | `platform/scripts/governance/asset_declarations.json` |
| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:1382` | seed (live may differ by migration) |
| writer / `@register` | `platform/python-sidecar/pipeline/orchestrator/writers/ga_structural.py:12` (heavy: `build_ga_structural_substep` per ayanamsha); registry `has_writer` = True | writers dir; census `Build.registered` |
| target table(s) | `chart_facts` (no registry `target_table`; `count_sql` joins `fact_category_ownership`, which names 64 categories for this asset) and `fact_category_ownership` itself in the count | census CEN-R (`target_table`, `count_sql_tables`) |
| live rows / floor | 102,037 / 98,446 (Δ +3,591); `asset_throughput` lit / **106,707** (4,670 more than the census count); seed floor literal 98446 | census `live_rows`; floor and throughput from the layer instance §1.1 (live registry read 2026-09-30) |
| catalog_status | CURRENT | census |
| depends_on (live, 2026-09-30) | `ga_dashas`, `ga_nakshatra`, `ga_panchanga`, `ga_positions`, `ga_sensitive`, `ga_strength`, `ga_vargas` (live and seed; the writer-class comment `ga_structural.py:21` lists only `ga_nakshatra` and defers to the registry, `:19`); the writer also reads two L0 catalogues (`brahma_dosha_catalog`, `brahma_yoga_catalog`, MF-L1-006; exempt) | layer instance §2.5 |
| blast radius | live registry incl. migration 1210 (applied; verified live 2026-10-01 14:37Z per the independent review): direct 7; census (2026-09-30, pre-1210): direct 7 / transitive 55; seed + 1210 reconstruction names 6 direct dependent(s): `bo_arudha`, `bo_laksana`, `bo_upaya`, `ga_sade_sati`, `ga_vichara`, `ga_yoga` (1 further live edge(s) unnamed: set by other migrations) | census `blocking_radius`; live count from the independent review; names reconstructed from `asset_registry_seed.ts` + `platform/migrations/1210_asset_registry_direct_edges.sql` (other migrations also edit `depends_on`, so the reconstruction can differ from the live registry) |
| code readers / served surface | `get_structural_signals.ts:138` (declarations `read_evidence`), `get_vichara.ts`, `reading_checklist.ts` (+59 modules reach `chart_facts` by table); census: 2 modules attributed, 1 declaring `density_contract` | census `reach.modules`; layer instance §1.2 |
| role / scoring mode | the structural spine: relations, conditions, divisions and firings L2 constructs on; 7 direct / 55 transitive dependents (census) | layer instance §0.2, §4.4 (contribution layer; Computational correctness, T1 §11) |

## 1 · Measured state and the nine gates (saved census, per criterion)

Census used: as the frontmatter `census_revision_used` (not repeated here).

`†` marks a criterion whose definition changed on main since the saved run (a later re-measure is expected for it): Build.dag rev 1 -> 2 (reads-match clause, any-layer unknown dep, cycle); Build.target rev 1 -> 2 (declared service with no target_table reads PASS by declaration); Idem.pattern rev 1 -> 2 (relative imports resolve; update-only reading); Dens.served rev 1 -> 4 (needs a density_contract AND a tier column in the served select; comment-only mentions no longer count). `Null.*` and `Narr.*` did not exist in the saved census.

| gate | criterion | saved verdict | measured (saved census text) |
|---|---|---|---|
| Build | Build.completion | FAIL | build record rows_written=106707 disagrees with live=102037 (count_sql total over 2 table(s): chart_facts, fact_category_ownership; chart 482012f1) |
| Build | Build.history | PARTIAL | latest run complete, but 23 error(s) and 10 abort(s) on record (0 additional blocked_dependency row(s) excluded as cascade-only). latest error (2026-09-07): post-write integrity check failed: integrity_check_sql → False |
| Earn | Earn.build_record | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 48448049 complete/skip_no_delta (2026-09-08) |
| Cost | Cost.baseline | NO_DETECTOR | NO_DETECTOR — instrument absent (migration 1094), scoped to this run; latest attempt at chart 482012f1: run 48448049 complete/skip_no_delta (2026-09-08) |
| Carr | Carr.detector | NO_DETECTOR | no D1/D2/D3 detector exists for this asset; which check applies is per-asset semantics |
| Null / Narr | not in saved census | NO_DETECTOR (registered at rev 5) | see the offline reading below |

**PASS cells (compact):** Build.registered; Build.contract; Idem.pattern †; Build.target †; Build.dag †; Build.count_integrity; Count.floor; Dens.served †; Build.exercised; Build.dep_liveness.

Information (never blockers, D3): Reach.fields NOT_GENERIC — no target_table declared: no table to census at field level; Complete.width NOT_GENERIC — no declared universe for this asset — declaring one is the first width gap.



**Offline rollup** (main's `rollup_asset` rules, registry rev 6, applied to the SAVED measurements; `NA_RULE_DECISIONS` is empty on main, so a measured N/A reads NO_DETECTOR; mixes old measurements with new rules; not a re-measure and not a certification; `_evidence/rollup_saved_L1.json` beside this file): Ldgr NO_DETECTOR · Idem PASS · Earn NO_DETECTOR · Null NO_DETECTOR · Vocab NO_DETECTOR · Carr NO_DETECTOR · Narr NO_DETECTOR · Dens PASS · Build FAIL.

**Offline re-scan of two criteria the saved census predates** (main's own code over this tree and the saved record, no database; indicative): Dens.served rev 4 reads **NO_DETECTOR** — NO_DETECTOR — 1 serving-root file(s) naming ga_structural lose the string scanner's sync (an unbalanced quote, a nested template literal, or a regex literal holding a quote desynced it): platform-mcp/src/tools/register_p1_ganita.ts; its served select and density_contract cannot be read — never FAIL… (the saved rev-1 reading was PASS); Null/Narr graders over the declarations file 1.6.0 plus DDL-derived columns (`_evidence/narr_null_offline_L1.json`; `*` = INCONCLUSIVE because no row data was read): agree PASS; checkable NO_DETECTOR*; fidelity_test PARTIAL; lint PASS; schema_default PARTIAL; blank_rows NO_DETECTOR*.

## 2 · Gaps — which are real, which are detector gaps

Class vocabulary: **real** = a shortfall in the asset's rows, writer, registry row or served surface; **detector** = the instrument for the claim is absent or its definition is the open point; **stale** = a ledger row written by an earlier inspector run that the saved census now reads PASS/N/A; **history** = a recorded past run outcome that no edit can change; **information** = Cost/Count/Complete/Reach, never a blocker (D3); **SS question** = real or not depends on a ruling; **artefact** = a saved census cell that reads a measurement the inspector's role could not make (pending a read by a role that can). A row naming several classes counts under its leading label.

| gap id (ledger `asset_gaps.jsonl` @ 2a78ec64d, or census cell, or this brief) | gate | class | note |
|---|---|---|---|
| brief: two back-reads — ga_structural reads outputs of assets that run AFTER it (Track I evidence §C) | Build.dag | real | `_load_wealth_ratification` reads `chart_vichara` (ga_vichara, `ga_structural_writer.py:2761-2770`) and `_dhana_yoga_fires_for` reads `ga_yoga_firings` (ga_yoga, `:2800-2806`); both feed the daridra-cancellation pass (`:2860,2868`, `_cancel_daridra`). `ga_vichara` and `ga_yoga` depend on `ga_structural`, so a declared edge back would be a cycle (Track I did not add it). On a fresh chart the reads return nothing ("an honest gap", `:2770-2790`); on a rebuild they read the PREVIOUS generation. The cancellation outcome therefore depends on build order and history, not only on the chart; CF-13 |
| ga_structural-Build.completion | Build | real | FAIL: `rows_written` 106,707 vs live 102,037 (−4,670; the writer reports more than the asset's `count_sql` counts). `count_sql` joins `fact_category_ownership` (migration 410: 58 categories seeded; 842 added 7 `bhava_bala_*`; the table holds 67 rows over three owners) which "names three owners only and leaves 41,042 chart rows with no owner row" (TG-L1-005). Whether the 4,670 are unowned categories or lost rows is not determined offline (MF-L1-005); the ownership table is hand-maintained and drifted twice before migration 410 (migrations 364, 368) and needed a backfill again at 842; CF-02 |
| ga_structural (no cell) | Complete, Vocab, Reach, Ldgr | detector | no `target_table`, so Complete.depth, Vocab.identity and Reach read no cell (MF-L1-003); CF-18, CF-08 |
| brief: Dens (offline rev 4) | Dens | detector | NO_DETECTOR: the inspector's string scanner loses sync in `platform-mcp/src/tools/register_p1_ganita.ts` (an unbalanced quote, nested template literal or regex literal), so the served select and `density_contract` cannot be read — a scanner limitation, not an asset gap; CF-04 |
| ga_structural-Build.history | Build | history | PARTIAL: 23 errors / 10 aborts; latest error 2026-09-07 `post-write integrity check failed: integrity_check_sql → False` (some of the ~40 per-family integrity contracts, migrations 745–840, were written to be red where a defect was known); CF-10 |
| brief: one bare tier literal; tier discipline | Earn | real | 19 quoted tier strings (indicative) and 1 bare `verification_pass_status` literal; the module imports the vocabulary (5 references); CF-17 |
| brief: Narr fidelity (declared `citation_human`; 127 mentions) | Narr | real | declared; offline: agree PASS, lint PASS (16 writer files clean), fidelity PARTIAL (11 test files reference the declared field in the same test function as a builder call; whether the assertion grades the sentence is not read); CF-15 |
| brief: writer-class `depends_on` comment out of date | Build.dag | information | `ga_structural.py:21` names one edge while the registry carries seven; the file defers to the registry (`:19`); no behavioural effect; CF-13 |
| ga_structural-Earn / Cost / Carr / Idem | Earn, Cost, Carr, Idem | detector / stale | CF-05, CF-07 (D3: recompute a sample of aspects/conjunctions/dispositors from stored positions); the Idem ledger row is stale (census PASS) |

## 3 · Disposition

**keep (P)** — the structural spine, large and well tested (W2 route `rebuild_only`: "writer sound; owns the argala corpus; the defects are ownership-registry and downstream consumption"); its real defects are a registry/ownership basis, an order-dependent cancellation pass, and detector gaps. Fix designs, not a different disposition.

Approver under Track A brief §10: **Steward (G16); moving the daridra-cancellation pass (FD-1) is an output change for SS**.

## 4 · Fix designs (one per real gap; `needs production rebuild` is a REVIEW item for Strategic Suvarṇa)

### FD-1 · Take the daridra-cancellation pass out of the back-read position

- **Answers:** brief gap "two back-reads"; Track I §C; CF-13
- **Change:** keep the daridra finding in `ga_structural` and mark it "cancellation evaluated downstream"; evaluate the cancellation in `ga_vichara`, which already holds both operands in DAG order (it depends on `ga_structural`, `ga_strength`, `ga_dashas` and `ga_yoga` and computes the wealth `varga_ratification`), as a new `chart_vichara` family. Alternatives: (b) accept the previous-generation read and declare it (rejected by §N.3 reproducibility); (c) split a post-yoga asset (a new asset: a bigger change). The choice and the category ownership move are SS's
- **Files / declaration / migration:** `ga_writers/ga_structural_writer.py:2761-2870` (remove the two reads, keep the finding); `ga_writers/ga_vichara_writer.py` (new family and test); `fact_category_ownership`/registry text for the moved rows
- **Failing-first test and mutation:** failing-first: on a freshly built chart (no prior generation) the cancellation outcome equals the outcome after a second build (today it can differ); mutation: reintroduce the back-read and the order-independence test fails
- **Output change:** yes: the cancelled/uncancelled state of the daridra finding is emitted by a different asset and may change on a fresh build (it can only differ where the previous-generation read returned nothing); SS (R5)
- **Blast radius:** 7 direct / 55 transitive dependents read `ga_structural` rows; `ga_vichara` gains a family (its readers `bo_laksana`, `bo_karanajala`, `bo_laksana_rerank`); moving the family changes the row counts of both assets, so their floors (`ga_structural` 98,446, `ga_vichara` 8,249) are re-declared from the next build (floors equal the achieved count after a build)
- **Rebuild:** **needs production rebuild** of `ga_structural` (106,707 rows) and `ga_vichara` after the code lands, in DAG order: a REVIEW item for SS
- **Gate it moves:** Build (dag), Idem (reproducible rebuild), Earn
- **Fix class:** writer code + data (output change); **buildable before J1:** tier-dependent: which asset owns a cancellation (TGH-T2 §3.3 judged structure)
- **Question for SS:** Move the daridra-cancellation evaluation to `ga_vichara`, accept the stale read and declare it, or split a new post-yoga asset?

### FD-2 · Reconcile the 4,670 rows and complete `fact_category_ownership`

- **Answers:** census Build.completion FAIL; CF-02
- **Change:** read-only first: list the categories the last build wrote (by `fact_category`, for the build_id of the last complete run) and join to `fact_category_ownership` to see which are unowned; then add the missing rows by the migration-842 pattern (idempotent `ON CONFLICT DO NOTHING`) or scope the writer's reported count to owned categories. Longer term: a CI parity test between the categories each L1 writer emits (a constant per writer) and the ownership table. Completing ownership raises the counted rows toward the written 106,707; scoping `count_sql` to the primary table (SS Q19) would lower it; either way the floor 98,446 is re-declared from the next build
- **Files / declaration / migration:** a registry migration (number = max+1 at execution time); optionally a per-writer category constant and a parity test
- **Failing-first test and mutation:** failing-first: `rows_written` of a rerun equals the asset-owned count on a stated basis (today 106,707 vs 102,037); mutation: delete one owned category row and the parity test fails
- **Output change:** none
- **Blast radius:** cockpit counts for `ga_structural` and the producers sharing its categories (cosmetic); no consumer reads `count_sql`
- **Rebuild:** none for the ownership rows
- **Gate it moves:** Build (completion)
- **Fix class:** registry/declaration only (+ test); **buildable before J1:** tier-dependent: TG-L1-005 (who owns the count)

### FD-3 · Fix the Dens scanner desync (inspector, not the asset)

- **Answers:** Dens NO_DETECTOR; CF-04
- **Change:** make the inspector's TypeScript scanner survive `register_p1_ganita.ts` (a nested template literal/regex literal) or exclude it with a stated reason; the asset has nothing to change
- **Files / declaration / migration:** `platform/scripts/governance/asset_census.py` (Track E)
- **Failing-first test and mutation:** the scanner reads the file and Dens returns a verdict for the asset
- **Output change:** none
- **Blast radius:** none
- **Rebuild:** none
- **Gate it moves:** Dens
- **Fix class:** detector/tooling; **buildable before J1:** tier-independent

### FD-4 · Narr golden test, tier literal

- **Answers:** CF-15, CF-17
- **Change:** as `ga_positions` FD-1/FD-2 for this writer (one literal; a golden sentence test for the dispositor/yoga citation)
- **Files / declaration / migration:** `ga_structural_writer.py`; a test beside the writer tests
- **Failing-first test and mutation:** as ga_positions
- **Output change:** none
- **Blast radius:** none for data
- **Rebuild:** none
- **Gate it moves:** Earn, Narr
- **Fix class:** writer code + test; **buildable before J1:** tier-independent

### FD-5 · Argala: pairing, obstruction outcome, node reversal, empty cells, citation, graha-level family (SS-ruled, decision N-61; provisional until J1)

- **Answers:** decision sheet `DECISION_SHEET_L1_v1_0.md` group B-0, AR-1 to AR-6 (the six argala items; L1 is the authority, L2 references)
- **Change (as ruled):** (1) L1 owns the pairing 2-12, 4-10, 11-3, 5-9 as a named, cited rule; the paired offset is stored on every `argala_natal_matrix` / `virodha_argala_natal_matrix` row (additive `fact_value_jsonb` key, same 144-cell structure, the `ga_structural_writer.py:4771-4781` count assertions untouched). Obstruction applies to benefic AND malefic argala. The outcome is by count only: argala count > obstructor count = `argala_prevails`, fewer = `obstructed`, equal = `undetermined`; "stronger" stays null (no sourced strength basis). `virodha` means the obstruction in every layer. (2) A new graha-level family in `ga_structural` (working name `argala_graha_natal`; D1 only): per (target graha, source graha) at an argala offset the offset, `count_direction` (`forward` or `reverse`), the paired obstruction offset, the obstructing grahas, the argala and obstructor counts and the outcome. Rahu and Ketu are counted in reverse when the node is the REFERENCE (BOTH nodes; Ketu-only is a named stricter variant); a node as the causer counts normally; the sign-level matrix stays forward-only and its description says so. (3) An empty source sign stores `fact_value_num = NULL` with `fact_value_text = 'no_occupant'`; the 1.0 base and the 0.25 malefic penalty stay as a project convention labelled `unsourced`; the BPHS count grading (limited, medium, excellent) is post-J1. (4) The tier stays `single`; `source_calculation` is corrected from `pyjhora_adapter.argala` / `pyjhora_adapter.virodha_argala` (no such module) to the real writer function. (5) The citation block (BPHS Santhanam Ch. 31: `bphs_pg0310_c01`, `bphs_pg0311_c01`, `bphs_pg0311_c02`, `bphs_pg0312_c01`; Jaimini Su. 5-10: `bphs_jaimini_pg0023_c01`, `bphs_jaimini_pg0028_c01`, `bphs_jaimini_pg0028_c02`, `bphs_jaimini_pg0029_c01`), state `sourced_ocr_unverified`, goes in `formula_provenance_text`. (6) Canonical offsets stay L1's {2, 4, 5, 11} / {12, 10, 9, 3}; {2, 4, 11} is a named filter (exclude offset 5 and its 9th obstruction), never a second definition. Recorded, not built: the vipareeta / 3rd-house evil argala (`bphs_pg0311_c01`; Su. 6).
- **Files / declaration / migration:** `ga_writers/ga_structural_writer.py` (`:614-616`, `:4670-4781`, new family); migration 1219 (allocated by SS): the `fact_category_ownership` row for the new category and the `count_sql` / floor touch (floors follow the achieved count); `platform/src/lib/retrieval/registry/layers/L1_ganita/get_argala.ts:62-65` description (fixed now, pre-approved: the obstruction offsets read 12th/10th/9th/3rd, not "3rd/12th/10th/3rd"); one cited benefic/malefic definition in the L0 graha vocabulary (Sun, Saturn, Mars; nodes stated separately) read by both layers, if a label is needed.
- **Failing-first test and mutation:** failing-first: the BPHS worked example (`bphs_pg0312_c01`: Mars in the 4th countered by Saturn in the 10th, Sun and Mercury in the 2nd by Venus in the 12th, Jupiter in the 11th by Moon and Rahu in the 3rd) gives the recorded pairs and, by count, `argala_prevails` for the Sun-Mercury argala, `obstructed` for Jupiter's, `undetermined` for Mars's; a node-reference fixture counts in reverse and a forward count would fail it; an empty source sign stores NULL / `no_occupant`; `source_calculation` names the writer function. Mutation: restore the old pairing, the forward-only node count, the 1.0 empty cell or the `pyjhora_adapter.argala` string and the matching test fails.
- **Output change:** yes (R, provisional until J1): the argala and virodha rows gain the paired-offset key; 3,444 of 7,200 argala-offset cells per canonical chart change from 1.0 to NULL; the new D1 graha-level rows (at most 360 per chart); the label text on 43,200 rows.
- **Blast radius:** `get_argala.ts` (the empty cells; the `all_zero` flag); `bo_karanajala` (L2) builds its edges from the new rows (L2 side tracked in the L2 set); 55 declared dependents of `ga_structural` (3 L1, 20 L2, 12 L3, 9 L4, 11 L5) execute rather than delta-skip.
- **Rebuild (binding sequence, SS):** ONE `ga_structural` rebuild carrying the argala change AND the ephemeris fix, after G-EPH and G-FLIP, as part of S-L1; then `bo_karanajala` inside the single S-L2 batch. No argala-only L1 rebuild.
- **Gate it moves:** Ldgr (a classical reference on the rows), Earn (an honest provenance label), Count (floor refresh through 1219)
- **Fix class:** data (output change) + writer code + registry (1219) + served description (TS); **buildable before J1:** the `get_argala.ts` description only; the rest waits for the rebuild gates
- **Judgment for J1 (by name):** the pairing and the node reversal are on the J1 reviewers' list by name.

### Shared fixes that apply to this asset (full design in `INDEX.md`)

- **CF-13** — Build.dag reads-match: declared `depends_on` against the tables each L1 writer reads (missing edges, two back-reads). *This asset:* FD-1: two back-reads; writer-class comment
- **CF-02** — Producer attribution on the shared `chart_facts` table: partition-scoped `count_sql`, `fact_category_ownership`, multi-table writers. *This asset:* FD-2: `count_sql` joins `fact_category_ownership`; 106,707 vs 102,037
- **CF-04** — Dens (serving density) on the L1 served modules: applicability, tier column, shared-table attribution. *This asset:* FD-3: scanner desync
- **CF-15** — Narr golden tests that name the declared `citation_human` field (assertion on the sentence, not only on the builder). *This asset:* FD-4: declared
- **CF-17** — Verification-tier string literals in L1 writers (CLAUDE.md §N.4: named constants from `verification_vocab.py`). *This asset:* FD-4: 1 bare literal
- **CF-18** — Census population on shared tables: chart-scoped, partition-scoped cells for Complete / Ldgr / Vocab / Reach / Dens. *This asset:* no Complete/Vocab/Reach cells: no `target_table`
- **CF-08** — Ldgr: assets with no recognised citation column (six L1 cells with no reading). *This asset:* no Ldgr cell: one of six
- **CF-10** — Build.history PARTIAL/FAIL is a record of past errors and aborts; no edit changes it. *This asset:* PARTIAL 23/10: history
- **CF-12** — Idem: an orphan census for delete-then-insert writers whose delete scope is built from the rows about to be written. *This asset:* delete scope: categories present in rows (owner-receipt gated); the historical collision with `ga_condition` on two categories (migrations 416/419) is the case a category-scoped delete cannot see
- **CF-14** — Legacy `ga_writers/_telemetry.py` `update_asset_throughput` call sites (eight L1 writers, R34 residual). *This asset:* one of eight: `:8143` under `owns_conn` (`:6895`)
- **CF-07** — Carr (source carriage and reproduction) detectors, one check per asset (D3 dominates in L1). *This asset:* D3: recompute a sample of relations
- **CF-16** — `chart_divisionals` reads 0 rows for every login role since the migration-1035 ownership change (RLS deny-all): an access incident, data probably intact, UNVERIFIED until read as owner or builder (Track I I-11). *This asset:* reads `chart_divisionals`: rebuild only after the CF-16 access fix (`_load_varga_positions`, `:960-972`)
- **CF-05** — Earn.build_record and Cost.baseline: the instrument is absent (migration 1094). *This asset:* instrument absent: no change
- **CF-06** — `prose_fields` declarations for the L1 assets that have none or an incomplete one (Null and Narr gates). *This asset:* declared: `["citation_human"]`

## 5 · Semantic fingerprint contract (for E5.5)

natural key `(chart_id, ayanamsha_id, fact_category, fact_subject, fact_key)` (the table's unique key also includes `build_id`: `ga_writers/_idempotency.py:3-6`), restricted to this asset's `fact_category` partition over the 64 owned categories (and the unowned categories until FD-2 lands: the fingerprint must list categories explicitly, not by the ownership join). `id`/`build_id`/`build_id_uuid`/`computed_at` are volatile and excluded; `fact_id` is a semantic hash that excludes `build_id` where the writer builds it that way (checked for `ga_ayurdaya`, `_fact_id` at `ga_ayurdaya_writer.py:183-186`; not read for every writer).

## 6 · Preserved kernel, carriage check, opportunities

- **Preserved kernel:** the 64-category structural catalogue, the constituent `fact_id` references to real `chart_facts` rows (L1 authority), the catalog-driven yoga/doṣa labelling and the 144-row argala matrices.; L1 is the authority for argala: by CLAUDE.md §N.5 and the SS argala answer logged in Track I items, L2 (`bo_karanajala`) REFERENCES L1's computed argala ({2,4,5,11}, Jaimini) and never recomputes it; a BPHS {2,4,11} variant would be a separately named, cited convention, never a silent second definition
- **Carriage check chosen (T4 §4.1; one only):** D3 — recompute a stratified sample of aspects, conjunctions and dispositor chains from stored positions by an independent routine and compare; D1 for catalog-driven yoga/doṣa labels is the L0 catalogue's own check.
- **Opportunities (never blocking):** none registered beyond the ledger rows listed in §2

## 7 · Questions for Strategic Suvarṇa

1. Where does the daridra-cancellation pass belong (FD-1)?
2. Who owns the 4,670 difference between `rows_written` and `count_sql` (TG-L1-005), and is a writer-category/ownership parity test wanted?

## 8 · SS rulings (2026-10-02, decision N-61) for this asset

SS ruled the argala block of the L1 decision sheet (`DECISION_SHEET_L1_v1_0.md`, group B-0). All six recommendations are ACCEPTED; (R) items are provisional until the J1 independent review, and the pairing and the node reversal are on the J1 reviewers' list BY NAME. The ruling lines are in FD-5 above; in short:

- **AR-1 (R)** (a): L1 owns the pairing 2-12, 4-10, 11-3, 5-9; obstruction applies to benefic and malefic argala; outcome by count only (argala count > obstructor count = `argala_prevails`; fewer = `obstructed`; equal = `undetermined`); "stronger" stays null (unsourced); `virodha` means the obstruction in every layer; L2's "argala by a malefic" gets a different name (the L2 design note proposes it). Track I: I-14, I-17.
- **AR-2 (R)** (a): reverse for BOTH nodes when the node is the reference, in the L1 graha-level rows (`count_direction`); Ketu-only is a named stricter variant; the sign matrix stays forward-only and says so. Track I: I-14.
- **AR-3 (R)** (a): empty source sign = NULL with `no_occupant`; the 1.0 / 0.25 formula stays as a project convention (`unsourced`); the BPHS count grading is post-J1. Track I: I-15.
- **AR-4** (a): keep `single`; correct the provenance string to the real writer function. Track I: I-16.
- **AR-5**: accepted as written (citation chunk ids, `sourced_ocr_unverified`; rides the rebuild). Track I: I-16.
- **AR-6 (R)** (a): L1 {2, 4, 5, 11} / {12, 10, 9, 3} canonical, {2, 4, 11} a named filter; L1 adds the graha-level family (D1 only); L2 builds edges from those rows, cites their `fact_id`s and deletes its offset constants, its pairing and its own malefic set; if an edge needs a benefic/malefic label, ONE cited definition in the L0 graha vocabulary (Sun, Saturn, Mars; nodes stated separately) read by both layers; vipareeta / 3rd-house evil argala recorded, not built. Track I: I-14, I-18, I-19.
- **Sequence (binding):** one `ga_structural` rebuild carrying the argala change AND the ephemeris fix, after G-EPH and G-FLIP, as part of S-L1; then `bo_karanajala` inside the single S-L2 batch; no argala-only L1 rebuild. Migration 1219 is allocated for the `fact_category_ownership` row (and the `count_sql` / floor touch). Track I: I-20.
