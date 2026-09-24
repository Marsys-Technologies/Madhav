# ESCALATIONS — Gochara WP0–WP7 autonomous run

Run: branch `l3/gochara-autonomous-wp0-7`, worktree `/Users/Dev/madhav-l3/gochara-wp0-7`.
Executing `KIMI_AUTONOMOUS_EXECUTION_PROMPT_GOCHARA_v1_0.md` against
`GOCHARA_FAMILY_ELEVATION_PLAN_v2_1.md` (NATIVE_RATIFIED_PLAN) + `GOCHARA_RULING_SHEET_v1_0.md`.

Each entry: what was hit, why it is out of scope / a stop condition, evidence gathered,
what a human needs to decide.

---

## E-001 — KALA_COST_PROFILE_v1_0.md / KALA_BASELINE_v1_0.md unreachable from this branch (WP1 exit-gate item)

- **What:** Plan §13 and WP1's exit gate require `KALA_COST_PROFILE_v1_0.md` and
  `KALA_BASELINE_v1_0.md` to be reachable from the executing checkout (or their §10 rows
  formally withdrawn). Neither file exists on `main` or on this branch. They exist only on
  the setup worktree branch `l3/kala-setup-phase01` (commits `bb7857b07`, `de2a7f269` —
  `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/`).
- **Why not fixed here:** Landing those files on `main` is another session's delivery
  decision; pulling another branch's artifacts into this run would import unreviewed state.
- **Evidence:** `git log --all -- '**/KALA_COST_PROFILE*' '**/KALA_BASELINE*'` returns only
  the two setup-branch commits above; `ls` of the l3_autonomous directory on this branch
  shows neither file.
- **Decision needed:** Whether the setup session lands those artifacts on `main`, or the
  §10 "Value" row's NOT_RUN-until-present test is formally accepted as the standing state.
- **Effect on this run (per the execution brief's explicit instruction):** WP4 cost
  measurement proceeds using this run's own freshly-produced numbers, on the declared
  synthetic workload, baselined against the family's historically-measured best completed
  run (58.2 min) only as a recorded external figure, never as an assumed content of the
  missing files.

## E-002 — Branch is ahead of the plan's pinned source_revision (drift record, not a blocker)

- **What:** Plan frontmatter pins `source_revision: origin/main c58e86662…`. This worktree's
  HEAD is `fd13ec0a6` (three docs-only commits beyond the pin: 75f0f6a47, b997ee0bd,
  fd13ec0a6 — blueprint/elevation-plan documents). The pin is an ancestor of HEAD
  (`git merge-base --is-ancestor` PASS), and the extra commits touch no source, migration,
  or test file, so every file:line citation in the plan remains valid.
- **Decision needed:** None. Recorded so no future reader mistakes the branch point for a
  content drift.

## E-003 — H-1b out of scope for this run (explicit in the execution brief)

- **What:** H-1b (kakṣyā crossing with no resolvable bindu contributes no activity,
  `completeness_state='unqualified'`) changes served λ values and is gated on N-13/M-7 +
  G-10 (L1 has no per-contributor BAV matrix). The execution brief §5 makes it out of scope:
  design only, do not ship.
- **Decision needed:** Native ruling on N-13's numeric implementation and L1's G-10 closure.
- **Effect on this run:** H-1a ships (provenance only, with the honest no-saturation-change
  statement). H-1b is designed in the WP5 design note and escalated here.

## E-004 — Consumers of the gochara tables/service that plan §6.1 does not name (WP0 re-enumeration)

- **What:** The fresh WP0 consumer re-enumeration (WP0_FINDINGS.md) found ten caller/reference
  edges the plan's §6.1 inventory does not name. The load-bearing ones: the MCP read-only
  proxy whitelist at `platform/src/app/api/mcp/db/query/route.ts:64,71,84` (the serving
  tools' SQL transits it — P-1's provenance/coverage change touches it); two admin SQL UPDATE
  writers on `kala_gochara_windows_v2` (`scripts/kala_admission/w45_post_fit_rebuild.py:262`,
  `restamp_dishonest_staging_calibration.py`); the MR20/23/47 gates and w2g_validations
  reading v1/`'3.0'`/`_v2`; the `gochara_resonance_map` read-side mesh; the still-registered
  v1 sweep writer; docstring-level couplings in `lel/prospective_ledger.ts` and
  `pariprashna/confidence/engine_tier.ts`; registry-seed prose surfaces.
- **Why not fixed here:** the execution brief is explicit — a new undeclared consumer is an
  escalation, not a WP0 fix. None of these are touched by WP0–WP7's in-scope code (they are
  readers or staging-writers outside `may_touch`), but WP7's reader inventory and the P-1
  design packet must account for them, and the cutover runbook (WP10) must extend its
  blast-radius reasoning to items 1–2 in particular.
- **Evidence:** full grep hit lists in WP0_FINDINGS.md (consumer re-enumeration section).
- **Decision needed:** at WP10 authorization time, extend the reader inventory formally and
  decide whether the W41–W45 admission scripts' `_v2` UPDATEs need a staging guard before
  `'4.0'` becomes the registry-pinned target.

## E-005 — N-14 (w30 nodal dṛṣṭi removal) is designed but NOT implemented in this run

- **What:** The native's N-14 ruling removes `w30_nodal_drishti` from the λ product
  (`engine.py:175` enabled; `:700` the executing product; `:725/:736/:845/:846` stored) and retires
  nodal dṛṣṭi (85 Rāhu + 87 Ketu served records), with three adopted conditions:
  same-generation regeneration inside a new candidate (never a patch over live rows),
  the absence declared as `completeness_state`, and the removed term kept one generation
  as a labelled non-scoring annotation.
- **Why out of scope here:** every one of those conditions is a served-data action: it
  changes every stored λ and belongs to the candidate-generation build that WP10 alone is
  authorized to run (plan §4.7, §9 step 6; the engine's own comment at `engine.py:199-200`
  demands regeneration, not patching). The execution brief's WP5 list contains exactly
  H-1a/H-2..H-6 — N-14 is not in it; the brief's §5 out-of-scope list covers WP10 in
  full. Removing the factor now, on the served path, without the candidate-generation
  machinery would be precisely the "patch over live rows" the ruling forbids.
- **Evidence:** F-28/F-29 measurements (plan §3); WP3b classification A-9 (w30 enabled
  with corpus-refuted citation); WP0 nutation/corpus records.
- **Decision needed:** at WP10, sequence the w30 removal as part of the first `'4.0'`
  candidate build with its three conditions; until then `w30_modifier` stays as-is
  (enabled, documented) and the scoring_signature fingerprint detector remains the guard.
- **Effect on this run:** WP3b's baseline documents w30's current live semantics
  (labelled A-9); the kernel emits no nodal dṛṣṭi (WP1 §7 orb table; WP2 case 6);
  WP4 classifies any λ delta attributable to w30 against this record.

## E-006 — RESOLVED 2026-09-23 (commit 59bebe7dc) — WP5 honesty fixes H-1a, H-2, H-3, H-4, H-6 now implemented

- **What:** This entry originally recorded that WP5's honesty fixes could not be completed
  in this run because they intersected with the frozen kakshya primitive and with
  writer/serving receiver contracts outside `may_touch`.
- **What actually resolved it:** the intersection concerns were real for a naive
  implementation, but each had a narrower fix that stayed inside this branch's scope:
  - **H-1a**: rather than threading a `conn` through the frozen `kakshya_cell_crossing`
    primitive, boundaries are now pre-fetched once per chart into `ClassContext`
    (`_fetch_kakshya_boundaries`) and a new engine-side function,
    `_kakshya_cell_crossing_from_context`, mirrors the primitive's logic against that
    pre-fetched data. The frozen primitive in `gochara_grammar/primitives.py` is
    untouched.
  - **H-2**: a new `EvaluationFailure` exception replaces the silent `except Exception
    -> return 0.0/None` pattern in `_eval_single`/`_eval_single_full`.
    `find_threshold_crossings` and `score_chain_milestones` catch it and attach
    `completeness_state`/`failure_detail` fields directly on the existing
    `IntervalBoundary`/`MilestoneScore` dataclasses — no writer/serving schema change
    was needed because these are internal computation types, not the served row shape;
    propagating the fields further downstream (into the actually-served
    `kala_gochara_windows` row) remains P-1/P-2's task, unchanged from before.
  - **H-3**: `HierarchyResult` gained `requested_start_jd`/`requested_end_jd` (always
    populated) and `completed_start_jd`/`completed_end_jd` (`None` on an honest empty
    result) — an additive dataclass change, no receiver contract needed.
  - **H-4/H-6**: implemented via a `_sentence_identity` adapter that calls the pinned
    `services.gochara_kernel.ids.contact_id`/`independence_group` functions (built in
    WP3a on this same branch) rather than reimplementing identity locally, and a
    collapse-by-`independence_group` pass in `_gather_sentences_no_db`.
  - **H-5 remains NOT implemented** and NOT escalated as resolved: removing the stored
    peak cap genuinely does require serving/trimming coordination in P-1/P-2 — that part
    of the original analysis was correct and stays as an open item for WP9/P-1 design.
- **Provenance note:** the implementation above was first drafted during an interactive
  session that had been pointed at the wrong checkout (the main `Vibe-Coding/Apps/Madhav`
  working copy on `campaign/nirmana-autonomous`, not this worktree/branch) and sat there
  uncommitted. During reconciliation onto this branch, the draft's H-4/H-6 wiring was
  found to call a second, non-canonical `contact_id(sentence)`/`independence_group(sentence)`
  pair with a different signature than the pinned kernel contract — corrected before
  committing; see commit `59bebe7dc` message for the full account.
- **Evidence:** commit `59bebe7dc`; `tests/l3/gochara/test_wp5_honesty.py` (9 new tests,
  including one that reproduces `_sentence_identity`'s output against a direct call to
  the pinned kernel functions to prove agreement); full suite `tests/l3/gochara/` 86/86
  passing after the change.
- **Decision needed:** none for H-1a/H-2/H-3/H-4/H-6 — implemented and tested. H-5 still
  needs the P-1/P-2 serving-side design this file's other entries already describe.

## E-006-ORIGINAL (superseded above; kept for the record) — WP5 honesty fixes (H-1a, H-2..H-6) not completed in this run

- **What:** WP5 is in-scope per the execution brief, but its implementation
  requires changes that intersect with contracts/files outside this run's
  `may_touch` boundary, or with the FROZEN orchestrator/writer contract, in
  ways that cannot be safely completed without a dedicated, focused session.
  Specifically:
  - **H-1a:** reading kakṣyā boundaries from L1 (`chart_facts.fact_category =
    'ashtakavarga_kakshya_boundary'`) instead of the equal-eighths fixture
    requires either (a) adding a `conn` parameter through `_compute_activity_v3`
    → `evaluate_lambda_vector` → `_gather_sentences_no_db`, which re-opens the
    no-DB contract of the v3 activity path, or (b) pre-fetching boundaries in
    `ClassContext` and threading them into the frozen primitive
    `gochara_grammar/primitives.py::kakshya_cell_crossing`. That primitive is
    frozen; the change therefore needs a new primitive or a contract amendment
    that is out of scope for an autonomous run.
  - **H-2:** preventing solver exceptions from becoming `0.0` scores requires
    the failed row to carry `completeness_state='unqualified'` and
    `failure_detail` through `_compute_activity_v3` / `interval_solver.py` /
    `resolution_hierarchy.py` and into the writer/result schema. The writer
    layer (`platform/src/lib/retrieval/registry/layers/reading_checklist.ts`,
    `GocharaTransitService`, and downstream `kala_gochara_windows_v2` staging)
    is outside `may_touch`; adding the field without a receiver creates an
    orphaned schema change.
  - **H-3:** honest requested-vs-completed horizon reporting is localized to
    `interval_solver.py`/`resolution_hierarchy.py`, but the existing test suite
    (`test_w32_interval_solver.py`, `test_w33_resolution_hierarchy.py`) encodes
    the current truncation behavior; a safe fix needs a design packet for the
    P-1/P-2 serving owners because the UI currently expects one window per
    requested horizon.
  - **H-4:** already implemented via the w26_real_eclipses mechanism
    (`services/gochara_v3/mechanisms/w26_real_eclipses.py` and its tests pass);
    no further work required.
  - **H-5:** removing the stored-peak cap requires the cap to move to serve
    time only. `resolution_hierarchy.py::retain_candidates_pooled` currently
    caps at `MAX_PEAKS_PER_ERA_WINDOW`; storing all admitted peaks changes the
    natural key cardinality of `kala_gochara_windows` and must be coordinated
    with the serving/trimming logic in P-1/P-2, which is outside `may_touch`.
  - **H-6:** physical-contribution identity is already implemented in
    `services/gochara_kernel/ids.py::independence_group` and used by the WP6
    ledger; wiring it into the v3 engine/scoring path requires the same
    writer/schema receiver changes as H-2.
- **Why not fixed here:** the dispatch subagent for WP5 (agent-19) reported
  completion but produced no verifiable code changes — only `ESCALATIONS.md`
  was touched. Manual implementation of the remaining items would require
  touching frozen primitives or writer/serving code outside `may_touch`,
  violating §3 constraints. The honest path is to record the partial state
  (H-4/H-6 kernel-side done, H-1a/H-2/H-3/H-5 blocked on receiver contracts)
  and continue with WP4, which does not depend on WP5 for its core
  geometry-vs-legacy comparison.
- **Evidence:** `git status` after the WP5 subagent shows only
  `ESCALATIONS.md` modified; no `test_wp5_honesty.py` or code changes were
  produced. Grep of `resolution_hierarchy.py` shows `MAX_PEAKS_PER_ERA_WINDOW`
  still governs retention; `engine.py::_gather_sentences_no_db` still swallows
  exceptions with a debug log; the kakṣyā primitive in `primitives.py` is
  frozen and still falls back to equal-eighths when `conn is None`.
- **Decision needed:** A focused follow-up session should (1) amend or replace
  the kakṣyā primitive to accept L1-fetched boundaries, (2) add the
  `completeness_state`/`failure_detail` receiver fields in the writer/serving
  layers, and (3) move the peak cap to serve-time trimming. H-1b remains out
  of scope per E-003 / the execution brief §5.
- **Effect on this run:** WP4 proceeds using the WP3b legacy baseline and WP3a
  kernel geometry; any WP5-related λ deltas are classified as
  "honesty-fix pending" in the WP4 report rather than treated as passing
  behavior.

## E-007 — Migration number reservation and WP10 frontmatter flags at run start

- **What:** At the start of the remainder execution run (`GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md`),
  every `origin/*` head was scanned across both `platform/migrations/` and
  `platform/supabase/migrations/`. The highest numeric migration prefix found on
  any remote head is **1074**. This branch already holds the renumbered
  `1075_*` and `1076_*` migrations (WP6 ledger + resonance target state). The
  **next free migration number is therefore 1077** and is reserved here before
  any new migration is written.
- **Frontmatter flags:** `PRODUCTION_TRANCHE_1_AUTHORIZED: false`,
  `PRODUCTION_TRANCHE_2_AUTHORIZED: false`. Every WP10 step that touches a
  shared/production database, the live registry, the authority table, a
  deployment, or a real chart's served rows is therefore **stopped** at the flag
  boundary; only preparation and rehearsal on a disposable database are
  performed.
- **Decision needed:** None for the migration number. WP10 tranches require the
  native to edit the brief's frontmatter flags and re-run this agent.
- **Evidence:** `git fetch --all` completed; remote scan command returned
  `1074` as the maximum prefix; local branch files
  `platform/migrations/1075_*` and `platform/migrations/1076_*` exist and are
  already committed.

- **Addendum 2026-09-24 (native session, not the executor):** the scan above was correct at 23:49 IST on 2026-09-23 and is now stale. `origin/l0/vedha-and-frame-repair` (PR #2727, the L0 vedha-and-frame repair) has since pushed `platform/supabase/migrations/1075_nirmana_l0_ephemeris_probe_degree_anchor.sql`, `1076_nirmana_l0_ephemeris_daily_node_epoch_declaration.sql`, `1077_nirmana_l0_vedha_malefic_scale_integrity_reseal.sql`, `1078_nirmana_l0_transit_rules_integrity_reseal.sql` and `1079_nirmana_l0_transit_rules_description_truthfulness.sql`; per the L3 strategic session's read-only query, all five of that branch's files are APPLIED to production (`_migrations_applied`, filename-regex query, 2026-09-23 21:07–22:03 UTC; that session first reported two, then corrected itself to five after re-querying). The runner orders both directories as one sequence, numeric then lexical, so the duplicates would have ordered deterministically (`l0_` before `l3_`) — never a tracker collision — but two 1075s and two 1076s, one pair already applied, would let A-2's step "migrations 1075/1076 applied and verified" read as already done. This branch's two migrations were therefore renumbered **1075→1080** and **1076→1081** in this commit — the lowest free numbers across every `origin/*` head, every local head and all 228 local worktrees at 03:50 IST 2026-09-24 — with every reference rewritten and the suite re-run (183 passed before and after). Neither file had been applied outside a disposable DB, so the never-renumber-after-apply rule is not engaged. **The reservation above is superseded: the next free number for this run is 1082** — re-scan before writing any migration, as brief §3 already requires.

## E-008 — Yamakaṇṭaka honesty in M-6 derived target rows; provisional weights

- **What:** While implementing the M-6 derived target-contract rows (WP1
  CONTRACTS §2.2 items 9–11: `gulika_mandi_distance`, `yamakantaka_difference`,
  `bhava_arudha`), it was verified that `ga_sensitive_writer` persists
  Yamakaṇṭaka's sign **native-only** in
  `sensitive_point_gulika_mandi[YAMAKANTAKA].sign`. There is no day-table
  fallback anywhere in the pipeline. Charts lacking the native value therefore
  emit all four `yamakantaka_difference` rows as `unavailable`; an
  approximation is never substituted. This matches the honest-state convention
  (R-4) and is recorded here so the decision is visible rather than buried in
  writer code.
- **Also recorded:** (a) Derived M-6 rows are emitted only for the
  `bereavement` and `illness_acute` event classes, are classically cited
  (`uncited_extension=False`, ref `mandi_sign_distance_from_8L`, citation
  `PG220:C1 śl.26`), and carry **provisional weight 0.5** — final factor
  values are owned by WP8. (b) Navāṃśa refinement and trikona positions are
  named in the contract but deliberately **not emitted** (declared-coarser,
  sign-grain only). (c) `bhava_arudha` rows are uncited extensions
  (weight 0.6) and resolve state only when the `arudha_pada` sign fact for
  `ARUDHA_A{h}` names a valid sign. (d) `FORMULA_VERSION` bumped
  `ka_gochara_resonance_v2.0 → v2.1`.
- **Decision needed:** None for the Yamakaṇṭaka honesty stance. WP8 owns the
  final factor weights for all three new target types.
- **Evidence:** `platform/python-sidecar/ga_writers/ga_sensitive_writer.py`
  (Yamakaṇṭaka branch writes only when a native value exists);
  `services/gochara_grammar/derived_points.py`; enrichment unavailable-state
  tests in `tests/l3/gochara/test_m6_derived_target_rows.py` (4 `neg_m6_*`
  fixture cases, all passing).

## E-009 — Migration number reservation for §8.4/§8.5 (G-9 repair, G-10 BAV contributor)

- **What:** Per brief §11 step 4 and the E-007 addendum's supersession, every
  `origin/*` head and every local head was re-scanned across both
  `platform/migrations/` and `platform/supabase/migrations/` on 2026-09-24
  (after pushing `l3/gochara-autonomous-wp0-7`). The maximum numeric prefix
  found anywhere is **1084** (`1084_wp7_k1_v1_registry_edges.sql`, this
  branch). **1085 is reserved for the G-9 Kṣetra L0 vedha repair migration
  (§8.4) and 1086 for the G-10 per-contributor BAV `chart_facts` migration
  (§8.5).**
- **Also noted:** an earlier scan draft under-counted because its filename
  regex excluded digits after the numeric prefix (`*_l0_*`); the scan was
  re-run with a corrected pattern and 1075–1079 on
  `origin/l0/vedha-and-frame-repair` are accounted for.
- **Decision needed:** None.
- **Evidence:** `git ls-tree -r --name-only <each ref> -- platform/migrations
  platform/supabase/migrations` over all `refs/remotes/origin/*` and
  `refs/heads/*`, max prefix 1084.

## E-010 — Migration 1085 retired; step 4 apply set corrected; 1086 renamed to its layer (L3 session, 2026-09-24 13:40)

- **What:** `1085_nirmana_l0_bg_transit_rules_vedha_repair.sql` and `tests/l3/gochara/test_g9_vedha_row_repair.py`
  are **removed**. Step 4 of the cutover kit no longer applies 1085 or 1086, and refuses to (a `REFUSED` set,
  checked by `assert_no_refused_migrations()`, exits 3). `1086_nirmana_l0_…` is renamed
  `1086_nirmana_l1_gochara_g10_ga_strength_contributor_digest_spec.sql` (it is an L1 change).
- **Why:** 1085 aborts against production (19 rows still cite the struck source) and its repair is already
  applied by the L0 session. Applying 1086 is an L1 governed-digest revision that sheet A-2 does not authorise
  for tranche 1. Full reasoning: `gochara_wp0_7/G9_DISPOSITION_v1_0.md`.
- **Decision needed from the native:** none for the removals. **One scope question is open and is the native's:**
  sheet A-2's literal step 4 names exactly the two Gochara migrations (now 1080/1081). Step 4's apply set also
  contains 1082, 1083 and 1084, which the executor added: 1082 is additive stamp columns on this family's own
  L3 tables; 1083 is a nullable `contact_id` on two L5 tables (packet P-3); 1084 is registry edges (packet
  K-1/V-1). They are benign and additive, but they exceed A-2's literal text and were not separately ruled.
  Until the native confirms, tranche 1 step 4 should be treated as authorised for 1080/1081 and the other three
  applied through the normal deploy pipeline with their own verification.

## E-011 — Migration number reservation for §12.3 (4.13a–d additive migration)

- **What:** §12.3's one additive migration takes number **1087**
  (`1087_nirmana_l3_gochara_contacts_inclusivity_completeness_tier_basis.sql`, platform/migrations/).
- **How the number was derived (predicate, not just the figure):** fresh scan 2026-09-24 of every
  `refs/remotes/origin/*` head (`git ls-tree -r --name-only` over both `platform/migrations/` and
  `platform/supabase/migrations/`, `_archive/` excluded) plus the local head and worktree: claimed
  numbers in the 10xx range are 1080–1084, 1086 (this family) and 1088–1090 (Saṅgam); **1085 was
  retired** (E-010) and stays unused; **1087 is the lowest free number** and 1091+ are free.
  MIG-1 (`cd platform && npm run guard:migration-numbers`) run after the scan: **PASS — no new
  migration-number collision** (the three `header-mismatch` advisories on 549/554/555 are
  pre-existing and not this family's).
- **Application scope:** the disposable WP6 Postgres only (`gochara-wp6-disposable`, port 55433),
  applied by the test harness after 1081. Never applied to a shared database; production application
  is WP10-gated.
- **Decision needed from the native:** none.

## E-012 — The '4.0' windows projection has NO WRITER: tranche 2 cannot produce a servable candidate (L3 session, 2026-09-24 14:05) — **native decision needed**

- **What:** Plan §2.2 says that after elevation `ka_gochara` writes the contact ledger, the coverage manifest, **and the
  windows projection into `kala_gochara_windows` under generation `'4.0'`**, and stops writing `'2.0'`. Only the first two
  exist. Verified at source: `pipeline/orchestrator/writers/ka_gochara.py` still writes `GENERATION_V2` (`'2.0'`) into
  `kala_gochara_windows_v2`; `scripts/kala_gochara_cutover/step06_candidate_build.py` drives only
  `register_convention → publish_candidate → write_contacts → write_coverage` from an externally supplied episode list; and
  the only other code that INSERTs into `kala_gochara_windows` is the retired sweep (generation `'v1'`). No code path
  produces a `'4.0'` window row.
- **Why it matters (tranche 2 is authorised):** step 8 flips `kala_gochara_authority` to `'4.0'`, and serving reads
  `kala_gochara_windows` at the authoritative generation. Flipping onto a generation with zero rows **empties the served
  forecast for that chart**. The four step-7 flip gates read only the ledger, coverage manifest, TS-side disclosure and a
  scratch rollback, so none could see it. The rehearsal itself recorded the symptom without flagging it: it flipped with no
  windows, watched registry conjunct (k) go red, then inserted a window by hand.
- **Done here (a guard, not a fix):** step 7 gains gate `windows_present`; step 8 refuses (exit 8) when
  `kala_gochara_windows` has no rows for `(chart, generation)`. Two negative tests prove each can go red, and two rehearsal
  tests now seed a **synthetic stand-in window and say so**, so the rehearsal no longer implies the pipeline produced one.
  Result: tranche 2 will now STOP at step 7 on the real chart rather than flip onto an empty generation.
- **NOT done, and it is the actual work:** the projection writer — extending `ka_gochara` to project λ over the ledger for
  `'4.0'` under the ratified flags (M-1 shape at 5.0°, M-3, N-14, N-15, N-17, N-22, M-8) into `kala_gochara_windows`, with
  the factor-level delta report against `'3.0'`. That is a work package of its own (plan §4.5), not a runbook step.
- **Decision needed from the native:** who builds the projection writer, and whether tranche 2 stays authorised in the
  meantime. Recommendation: leave the flags as they are — the new gates make a premature run harmless — and name the owner.

## E-013 — Two hard DAG-guard violations are in OUR asset, `ka_gochara_resonance`, and pre-date this work (L3 session, 2026-09-24)

- **What:** the strategic session ran `pipeline.orchestrator.dag_edge_guard` live, read-only, against the production registry
  (130 writer assets). Six hard violations; two are ours: `ka_gochara_resonance` reads `chart_dashas` (produced by
  `ga_dashas`) and `ga_yoga_firings` (produced by `ga_yoga`), and neither producer is in its `depends_on` closure. A soft
  finding also notes it reads `chart_facts` with no producer in the closure. The other four are not ours
  (`bo_laksana`, `ka_bhavishya_lekha`, `ka_kshetra`, `ka_sangam`).
- **Why it is real, not a false positive:** WP3c's target resolution genuinely reads the dasha portfolio and yoga firings, so
  those are true build-order dependencies — a resonance build run before `ga_dashas` or `ga_yoga` is lit would resolve
  against nothing. Nothing in CI catches it: the guard runs `--self-test` only, and the live test skips without
  `DATABASE_URL`.
- **Not done, deliberately:** adding the two edges. `depends_on` is a hard build gate (a dependency must be `lit` for the
  chart), so adding an edge changes what can build, in production, and needs the same check Kṣetra's edge got. It also
  extends WP10 step 5 beyond sheet A-2's literal "registry re-pin + `EXPLICIT_CLEAR_OPS`".
- **Decision needed from the native:** whether step 5's re-pin should also declare `ga_dashas` and `ga_yoga` on
  `ka_gochara_resonance`. Recommendation: yes, as its own reviewed change, after confirming both producers are `lit` on the
  canonical chart so the new gate does not block the next resonance build.
- **Also recorded from the same run (not ours):** `ka_bhavishya_lekha` reads `phala_anchors`, produced by `ph_nimitta` —
  L3 reading L4, a layer inversion and an architectural question for the native, not an edge to add.
