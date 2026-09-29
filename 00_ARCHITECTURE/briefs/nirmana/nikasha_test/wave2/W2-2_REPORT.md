---
artifact: NIKASHA_WAVE2_W2-2_REPORT
packet: W2-2 — latest row, right registration, attempt-linked timing
version: "1.1"
status: CORRECTIONS C-KSHETRA (code, 2e1c06d1b) and C1/C3 (this text) APPLIED after W2-2_REVIEW.md (9f84ecf6a, ACCEPT_WITH_CORRECTIONS)
changelog:
  - "1.1 (2026-09-27): gate corrections. C-KSHETRA (2e1c06d1b): Idem.pattern counts a DELETE only when it names the
    asset's own table and is reachable on a populated rebuild; ka_kshetra PASS->FAIL (its PASS was WRONG, not correct
    by accident), bo_upaya and ka_gochara PASS->PARTIAL. C1: §0, §4.3, §5.2, §5.3, OS-C rewritten — 33 of 34 simulated
    second-emit closures were earned; after the fix the simulation closes 33, all earned. C3: fact_category_ownership
    is created and seeded by migration 410 (418/842/845 later); OS-B is 1 read on L1, not 2; the R53-M3 claim is
    withdrawn (spec unrecorded; its natural form is an equivalent mutant). New §10."
  - "1.0 (2026-09-27): builder report."
produced_on: 2026-09-27
builder: Opus (wave-2 builder, packet W2-2 only). Rows R233…R54 were built and committed by a first builder that
  was stopped mid-R232; a second (finishing) builder verified the tree, finished and committed R232, re-ran one or
  two mutations per committed row at the final HEAD, ran the four packet proofs and wrote this report.
base: 931dbc479
head_code: "2e1c06d1b (v1.0 was 8f5e2fd29)"
rows: [R233, R44, R49, R45, D6-item-2, R43, R46, R50, R51, R53, R54, R232]
corrections: ["C-KSHETRA 2e1c06d1b", "C1/C3 this report"]
files_touched:
  - platform/scripts/governance/asset_census.py
  - platform/scripts/governance/__tests__/test_w2_2_latest_row_registration_timing.py   (new)
  - platform/scripts/governance/__tests__/test_w2_1_earned_verdicts.py
  - platform/scripts/governance/__tests__/test_b1_asset_census_blocked_dependency.py
  - platform/scripts/governance/__tests__/test_a4_gate_corrections.py
  - "platform/scripts/governance/__tests__/test_a3_fault_isolation_and_population.py (C-KSHETRA — call-site text + stub arity)"
  - 00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave2/** (this report + w2-2_evidence/)
not_touched: asset_elevation_tracker.py (no change needed), writers, orchestrator, migrations, sealed tiers,
  editorial.ts/compiler.ts, register/plan/decisions/STATE, catalog_provenance.py and its tests, provenance/**,
  00_ARCHITECTURE/control/asset_gaps.jsonl + asset_certs.jsonl (md5 30365ff2… / 514cbdfc…, 263 / 1 lines —
  unchanged at session start, after every census/emit run, and at report time)
---

# Nikaṣa wave 2 · W2-2 · builder report

## §0 — Summary

Twelve rows, twelve commits, one row per commit (`git commit -- <paths>`, only-mode; nothing pushed).

| row | commit | one line |
|---|---|---|
| R233 | `0166b096a` | `build_run_assets.error` is flattened in SQL before the line-oriented read; one attempt = one line; the strict xfail flipped. |
| R44 | `bf1ffbad0` | The build record is the latest `asset_throughput` row per (asset, chart) on a stated key; a tie reads ERRORED. |
| R49 | `0bf42192c` | `Build.history` reads attempts on a total order and quotes the latest non-cascade error, dated. |
| R45 | `1d2544f23` | `Build.dep_liveness` is measured at the canonical chart (else global); stale → PARTIAL, never PASS. |
| D6 item 2 | `ad0141bf7` | Earn/Cost linked to the latest started attempt at the record's scope; probe-green derived; still NO_DETECTOR in production (instrument absent). |
| R43 | `311a13a40` | `@register(ASSET_ID)`, package writers and shim-imported writers are recognised (13 writer-backed assets were not). |
| R46 | `9968eceaf` | A view asset is counted by its view, not by a constant `count_sql`. |
| R50 | `16a67ca41` | A line that does not parse into the 7 selected fields fails the read instead of adding a phantom run. |
| R51 | `ccec0127f` | Serving modules are attributed by code, not comments; comment-only attribution is NO_DETECTOR, never N/A. |
| R53 | `83f143be1` | `Build.target`'s FAIL is reachable; N/A only for a declared service or a writerless asset. |
| R54 | `eca58994d` | `Vocab.alias` states its measured fraction and carries `severity` (0.0–1.0). |
| R232 | `8f5e2fd29` | A module "declares" `density_contract` only with a real `density_contract:` / `density_contract?:` property in code. |
| **C-KSHETRA** (gate correction) | `2e1c06d1b` | `Idem.pattern` PASS needs a DELETE that names the asset's own table and is reachable on a populated rebuild; ka_kshetra's refused rebuild reads FAIL (§10). |

**R232 final state: finished and committed (`8f5e2fd29`).** The first builder's uncommitted diff was correct as
code. Its test was extended before commit (template-literal mention, `?:` declaration, mention + declaration, an
emit positive control). The `@LIVE` snapshot test was removed: it read no database, it failed "without the change"
only through `AttributeError`, and it asserted today's source snapshot rather than behaviour (§2, R232).

**Packet proofs.**
1. **Branch enumeration (§3):** 38 PASS/N/A-yielding branches (36 at W2-1, plus 2 new from R53). 20 genuine
   (5 of them unreachable in production while migration 1094 is absent), 12 fixed, 4 proxy, 2 contested.
   W2-2 fixed #18 (R53) and #33 (R45); #29's declaration basis is fixed (R51, R232), but its grading stays contested.
   **v1.1:** #3 (`Idem.pattern` DELETE) is fixed by C-KSHETRA for a DELETE on another table, a bare fragment, and a
   rebuild refused on a populated chart. It stays a proxy for writers that delegate (R20).
2. **Census diff (§4):** 71 verdict changes, **0 unexplained**; 500 text-only changes, each attributed to a row.
   There are **37 favourable flips** (→PASS or →N/A): 13 `Build.registered`, 13 `Build.contract` and 8 `Idem.pattern`
   (all R43), plus 3 `Build.target` (R53). **v1.1 (gate review §4): 36 of the 37 were correct. One was WRONG:
   `ka_kshetra` `Idem.pattern`.** Its writer raises `KshetraReplacementHeld` on any populated chart, and
   482012f1 holds 8,570,075 `kala_field` rows, so a rebuild holds rather than replaces. v1.0 called this verdict
   "true, but not measured by the census". That was wrong: my hand-check read the DELETE loop and missed the guard
   in front of it. C-KSHETRA (`2e1c06d1b`) fixes the detector, and ka_kshetra now reads FAIL. `ga_structural`'s
   `Build.target` verdict is correct, but its text wrongly names a lookup table as "produced" (proxy #37).
3. **Emit dry run (§5):**
   - HEAD on a copy of the production ledger: **574 OPEN, 0 CLOSED, 0 RE-OPENED**, 209 already present. Idempotent
     (the re-emit leaves the copy byte-identical).
   - Simulated second emit (base code first, then HEAD, on one copy): at `8f5e2fd29`, **34 CLOSED**, of which
     **33 were earned**. The 34th, `ka_kshetra-Idem.pattern`, would have closed on a false measurement. At
     `2e1c06d1b`: **33 CLOSED, all earned**, 14 OPEN, 0 RE-OPENED; `ka_kshetra-Idem.pattern` is not in the closed
     set. 0 `Build.dep_liveness` and 0 `Dens.served` rows close.
   - **Ruling (v1.1):** at `8f5e2fd29` a second emit was **not** safe on today's data. It would have closed
     `ka_kshetra-Idem.pattern` on a false measurement. With C-KSHETRA landed it closes only the 33 earned rows. It
     is still **not trustworthy by construction** (§5.3).
4. **Suite, fingerprint, drift, ledgers (§6):**
   - Offline suite: 227 → 291 tests (v1.0 head) → **300** (C-KSHETRA head). Base: 214 passed, 11 skipped, 2 failed.
     8f5e2fd29: 269 passed, 20 skipped, 2 failed. 2e1c06d1b: 278 passed, 20 skipped, 2 failed.
   - Live suite at HEAD: 289 passed, 2 failed.
   - The same 2 failures (`test_drift_detector_h35_h38.py`) are pre-existing at 931dbc479.
   - `manifest_fingerprint --check`: MATCH. `drift_detector`: exit 3 (1 LOW).
   - Production ledger md5s are unchanged throughout.

## §1 — Scope and safety

- **Database.** Every query ran read-only through the session scratchpad `pgenv.sh` (`SHOW
  default_transaction_read_only` = `on`, verified at session start). `dbenv.sh` and `gcloud` were not used, and no
  production write was made. Every DB/long command ran under `timeout 300`; `drift_detector` ran under `timeout 600`.
- **Ledgers.** Production `asset_gaps.jsonl` / `asset_certs.jsonl` were never written. md5
  `30365ff2238c75f5f62e622b70292da3` / `514cbdfcf3fa71b3e382f84a978bf369` was checked at session start, after the
  censuses, after both emit runs and at report time. Every census ran with `NIKASHA_CONTROL_DIR` pointed at a
  scratch copy; every emit ran on its own scratch copy.
- **Scratch.** Everything lives under `<scratchpad>/w2-2/`. The temporary base worktree (`wt_base`, 931dbc479)
  was removed after use (`git worktree remove`; `git worktree list` no longer shows it).
- **Resumption.** Before touching anything, the finishing builder confirmed that the tree's `asset_census.py` was
  byte-identical to the first builder's `mut_backup.py` (no mutation left applied). The uncommitted diff was
  exactly the R232 change.
- **No writer, orchestrator, migration, sealed tier, register/plan/decisions/STATE or Lane B file changed.**
  `git diff --stat 931dbc479 8f5e2fd29` lists only the five governance files in the frontmatter (+1443 −94).

## §2 — Per row: commit, diff, test, mutation evidence

Mutation method: `w2-2_evidence/mut.sh` copies the file, applies one surgical replacement (`sub.py`, exactly one
occurrence), runs the named tests, restores the file (byte-identical, `cmp`), then re-runs the offline suite.
`without.sh` runs the tests with `asset_census.py` at the pre-row revision.

The first builder's runs are in `mutation_runs.log`. Entries it superseded itself are annotated in place (drafts
that broke a B1 test, a mutation that survived before its fixture was strengthened, a selector that was
word-split). **Re-verification:** the finishing builder re-ran one or two mutations per row at the final HEAD
`8f5e2fd29`, and every one was killed. After each restore the offline suite read 250 passed, 20 skipped, 21
deselected. See `mutation_reverify_final_head.log` and its script `mutation_reverify_final_head.sh`.

### R233 — newline-safe error read · `0166b096a`
- **Diff.** `build_history()` selects `left(translate(a.error, E'\n\r' || chr(31), '   '),200)`. Newline, CR and
  the field separator become spaces *before* truncation, so one attempt is exactly one psql line.
- **Test.** The committed `xfail(strict)` `test_live_c4_executed_equals_the_started_at_count_over_all_rows` now
  passes as a normal test. Its sibling no longer restricts itself to parse-safe rows.
- **Mutation.**
  - First builder, R233-M1 (raw `left(a.error,200)`): the live test fails.
  - Re-verified, V-R233-raw-error-read: 2 failed (both live C4 tests).
- **Live** (`r233_live.txt`): ph_sodhana executed 41 = started 41 (was 39); 69 multi-line error rows across 32
  assets are now read intact; 0 phantom per-asset keys.
- **Limit.** The row's test is live-only. R50's offline test covers the split-line shape at the parser.

### R44 — latest `asset_throughput` row per (asset, chart) · `bf1ffbad0`
- **Diff.** `throughput()` orders by `(asset_id, chart_id, last_built_at DESC NULLS LAST, last_measured_at DESC
  NULLS LAST)` and keeps the greatest key per (asset, chart), independent of read order. It records `n_rows`, and
  a tie on the key sets `ambiguous`. `Build.completion` on an ambiguous record reads ERRORED (:1511) and is never
  compared against a row nobody chose. Two partial unique indexes, which the census never checked, enforced
  uniqueness before.
- **Tests.**
  - `test_r44_the_latest_row_wins_whatever_the_read_order[newest_first|oldest_first]`
  - `…_a_null_build_time_never_beats_a_measured_one`
  - `…_a_tie_is_ambiguous_and_completion_is_errored_closing_nothing` (ledger copy; the OPEN gap stays OPEN)
  - `test_live_r44_every_record_is_the_distinct_on_latest_row`
- **Mutation.** V-R44-last-read-row-wins → 3 failed; V-R44-tie-not-flagged → 1 failed. First builder: M1 and M2,
  plus a without-the-change run.
- **Live.** 0 (asset, chart) keys have more than one row today, so no live verdict moves. The fix closes a
  defect class.

### R49 — latest error, dated, on a total order · `0bf42192c`
- **Diff.** Attempts are read `ORDER BY a.asset_id, r.created_at, a.run_id`. `run_id` completes the primary key;
  12 same-instant run pairs exist live. The latest non-cascade error is kept with `sample_error_when`, where the
  code used to keep the *first* one. The grading text reads `latest error (<date>): …`, and `sample_error` stays
  raw (B1's contract).
- **Tests.** `test_r49_the_quoted_error_is_the_latest_not_the_first`,
  `…_attempts_of_simultaneous_runs_are_read_in_one_deterministic_order[…]`,
  `test_live_r49_every_quoted_error_is_the_latest_by_a_direct_query`.
- **Mutation.** V-R49-first-error-kept → 2 failed (including live); V-R49-partial-order-key → 1 failed. First
  builder: M1–M3, re-run after a draft broke B1.
- **Live.** ka_avadhi quotes the 2026-09-10 integrity failure, not the 2026-07-04 UndefinedColumn.

### R45 — `Build.dep_liveness` at chart scope · `1d2544f23`
- **Diff.** `_grade_dep_liveness()` (:1225) replaces the chart-agnostic `hist["lit"]` set. For each dependency:
  - the record is its row for 482012f1, else its global row;
  - `lit` → live; `stale` → PARTIAL;
  - missing, error, dormant or incomplete → FAIL;
  - an R44 tie → ERRORED.

  Dependency records come from a separate layer-wide read, cross-layer dependencies included.
- **Tests.** `test_r45_a_dependency_not_lit_on_this_chart_never_reads_pass[…]`,
  `…_positive_controls_lit_here_or_lit_globally_pass[…]`,
  `…_an_open_dep_liveness_gap_does_not_close_on_another_charts_lit`,
  `test_live_r45_dep_liveness_matches_a_direct_chart_scoped_query`.
- **Mutation.** V-R45-stale-counts-live → 3 failed; V-R45-any-chart-record → 1 failed.
- **Live** (`r45_before_after.txt`): PASS→PARTIAL 10 (exactly W2-1_REVIEW C2's ten assets), FAIL→PARTIAL 16,
  FAIL→FAIL 11, PASS→PASS 62. No change creates a PASS.

### D6 item 2 — attempt-linked Earn/Cost timing · `ad0141bf7`
- **Diff.**
  - `latest_attempts()` (:809) reads the latest **started** attempt per (asset, run chart), on the total order
    `(created_at, run_id)`. It also reads the probe receipt and the disposition era (the first
    `disposition='build'`, 2026-09-04).
  - `_attempt_timing()` (:1018) picks the attempt at the record's scope (global → any chart, else the bound chart).
  - A duration counts only for a `complete`/`build` attempt whose `ended_at` equals the record's
    `last_built_at` (the link, :1064).
  - Probe-green is **derived** (:1081): complete, no disposition, a receipt naming the run, and inside the era.
  - Anything unclassified, unlinkable, in flight or read-failed → NO_DETECTOR.
  - The instrument is detected before the build-record read, which names `duration_seconds` only when present.
  - The two offline harnesses stub the new read. W2-1's R225 call-site test moves to the wired contract.
- **Tests.** 10 offline `test_d6_2_*` plus `test_live_d6_2_every_latest_build_attempt_links_to_its_build_record_on_real_rows`.
- **Mutation.** V-D6.2-link-key-ignored → 1 failed; V-D6.2-probe-green-without-receipt → 1 failed. First builder:
  M1–M7, with M2 and without-the-change re-run after fixes (annotated in the log).
- **Live** (`d6_2_live_linkage.txt`): instrument absent, so Earn and Cost read NO_DETECTOR on 127/127 assets, now
  naming the linked attempt. Simulated with a duration injected into each real build record: 62 linked
  PASS/PASS, 31 unclassified NO_DETECTOR, and N/A only by cause (skip 25, never attempted 6, before completion 3).

### R43 — constant, package and shim registration · `311a13a40`
- **Diff.**
  - `_module_constants()`: a top-level string constant is resolved only when it is assigned exactly once.
  - `_register_id(dec, consts)` resolves `@register(ASSET_ID)` through those constants.
  - `_writer_modules()` (:287) walks `writers/*.py`, package directories, and — one level deep — the first-party
    modules they import (`_first_party_imports`).
  - `contract_scan` / `idem_scan` read the resolved path (`_writer_path`).
- **Tests.**
  - `test_r43_a_module_constant_register_is_recognised_and_a_twice_assigned_name_is_not_guessed`
  - `…_package_and_shim_imported_writers_are_recognised`
  - `…_the_resolved_writer_is_measured_not_no_detector[mi_const-L5|ph_pkg-L4|ka_svc-L3]`
  - `test_live_r43_every_writer_backed_active_asset_is_recognised`
- **Mutation.** V-R43-constants-unresolved → 3 failed; V-R43-shim-imports-unfollowed → 3 failed. First builder: M1–M4.
- **Live** (`r43_registered_before/after.txt`):
  - Registered ids: L3 11 → 22, L4 8 → 9, L5 12 → 14.
  - Every active `has_writer=true` asset in all six layers is now recognised.
  - `ka_gochara_v3_century_materialize` (`is_active=false`) is reported as registered but not in the active registry.

### R46 — views counted by the view · `9968eceaf`
- **Diff.**
  - `catalog()` reports view targets (`relkind v/m`).
  - A view target whose `count_sql` reads no table is counted by `_view_count_sql` (:114), chart-scoped when the
    view has `chart_id`.
  - `Build.completion` for a view is NO_DETECTOR, because `rows_written` counts the view object. An empty view
    FAILs (:1481).
  - `Count.floor` grades against the view count.
- **Tests.**
  - `test_r46_a_view_is_counted_by_the_view_chart_scoped`
  - `…_a_declared_floor_is_graded_against_the_view_count[3-PASS|10-FAIL]`
  - `…_an_empty_view_fails_emptiness`
  - `…_only_a_view_is_substituted_a_table_with_a_constant_stays_no_detector`
  - `test_live_r46_bo_samvada_is_counted_by_its_view`
- **Mutation.** V-R46-view-not-counted → 4 failed. First builder: M1–M3.
- **Live.** bo_samvada live 0 → 5 (vw_chart_digest for 482012f1). Its verdicts do not move: Build.completion is
  NO_DETECTOR and Count.floor is N/A (floor 0).

### R50 — tallies reconcile; malformed lines fail the read · `16a67ca41`
- **Diff.** `build_history()` raises `Unknown` when any line has ≠ 7 fields. The old
  `(x + [""] * 7)[:7]` padding could add a phantom run to a real asset. B1's fake was updated to the real
  7-column shape.
- **Tests.** `test_r50_a_line_that_is_not_one_whole_attempt_fails_the_read_instead_of_adding_a_run`;
  `test_live_r50_runs_and_executed_equal_direct_counts_on_every_layer`. The live test fails at 931dbc479 (the
  29-asset R233 undercount; first builder's without-the-change run).
- **Mutation.** V-R50-short-lines-padded-and-counted → 1 failed.
- **Limit.** The handverify's ga_dashas 108-vs-107 does not reproduce today (106 rows). The row fixes the defect
  class and does not re-create the historic figure.

### R51 — serving modules attributed by code · `ccec0127f`
- **Diff.**
  - `_ts_code()` strips `//` and `/* */` comments while respecting string and template literals.
  - `capability_scan()` matches the table or asset id in code only, and records `comment_only` modules.
  - A comment-only attribution reads NO_DETECTOR, never the closable N/A (§N.8 guard).
- **Tests.** `test_r51_a_module_that_only_mentions_the_table_in_a_comment_does_not_serve_it`,
  `test_live_r51_l4_modules_are_attributed_by_code`,
  `test_r51_stripping_comments_never_turns_a_named_asset_into_a_closable_na[…]`.
- **Mutation.** V-R51-comments-count-as-serving → 3 failed; V-R51-comment-only-reads-closable-na → 1 failed. First
  builder: M1–M4; M3 survived once and was re-run after its fixture was strengthened.
- **Live** (`r51_attribution.txt`): module lists change on 65 assets. Three verdicts move, none toward
  PASS or N/A (§4).

### R53 — `Build.target`'s FAIL is reachable · `83f143be1`
- **Diff.** N/A now applies only to a declared service or a writerless asset (:1427). A writer-backed
  data/artifact asset with no target is graded by `_grade_target_less()` (:1196), on the engine's produced-table
  rule (`dag_edge_guard._producer_tables`):
  - ≥2 `count_sql` tables → PASS;
  - 1 table that another active asset declares as its target → PASS (partition writer);
  - 1 table nobody declares → FAIL;
  - no table → FAIL;
  - an unreadable ownership map → ERRORED.
- **Tests.** `test_r53_a_writer_backed_data_asset_without_a_target_is_graded_not_waved_through[4 cases]`,
  `…_a_declared_service_and_a_writerless_asset_stay_na`, `…_an_unreadable_ownership_map_is_errored`,
  `test_live_r53_no_writer_backed_data_asset_reads_the_closable_na`.
- **Mutation.** V-R53-any-kind-waves-through → 5 failed; V-R53-unowned-single-table-passes → 1 failed.
  **v1.1 (C3c): the R53-M3 claim ("own asset counted as owner → 1 failed") is withdrawn.**
  - The first builder's log records only `ok: asset_census.py (72 -> 69 chars)`. The 72-character target is the
    line `own = [a for a in owners().get(ct[0], []) if a != r["asset_id"]]`, but the 69-character replacement was
    never recorded and cannot be recovered.
  - It killed the `owners={}` case, so it must have made the owner list non-empty when no owner exists. That is not
    the self-exclusion mutation its name describes.
  - The natural form (drop `if a != r["asset_id"]`), run by the finishing builder, **survives: 7 passed**
    (`mutation_runs_ckshetra.log` tail). It is an equivalent mutant: `_grade_target_less` runs only when the asset's
    own `target_table` is NULL, and `target_owners()` lists only assets with a non-NULL target, so the exclusion can
    never fire.
- **Live.** bg_prashna_rules, ga_strength and ga_structural move N/A → PASS. See §4.3 for the hand-check and the
  ga_structural text finding (OS-A).

### R54 — `Vocab.alias` severity · `eca58994d`
- **Diff.** The measured text states `N/M row(s) lack an alias set (x%)`, and the measurement carries
  `severity = empty / rows` (0.0–1.0). The verdict logic is unchanged.
- **Tests.** `test_r54_the_plants_worsening_is_visible_below_the_verdict` (the T1 `vocab_alias` shape, 79/741 →
  741/741); `…_a_clean_alias_census_passes_with_severity_zero`.
- **Mutation.** V-R54-severity-dropped → 2 failed; first builder's M1 (per-class max) → 1 failed.

### R232 — Dens.served reads a declared property · `8f5e2fd29`
- **Diff.** `_DENSITY_DECL = re.compile(r"\bdensity_contract\s*\??\s*:")` (:443) is searched in
  `_ts_code(txt, blank_strings=True)`: comments are stripped and string/template contents blanked. It replaces the
  raw `"density_contract" in txt`.
  - **Why:** W2-1_C1_REVIEW F-S1 (review A4). After the first emit, 59 Dens.served rows are open, and a later emit
    could close one because a comment mentions the name.
- **What the finishing builder verified and changed before commit.**
  - The code diff is correct as claimed.
  - The test was extended to seven `capability_scan()` cases:
    - four mentions must count 0: `//`, JSDoc, a quoted string, a template literal;
    - three declarations must count 1: `density_contract:`, `density_contract?:`, and a mention plus a declaration.
  - The `measure()` + `emit_gaps()` test on a ledger copy was parametrised:
    - a comment reads FAIL and the OPEN gap stays OPEN (closed 0);
    - the declared case is the positive control: PASS, closed 1.
  - The first builder's `@LIVE test_live_r232_every_declaring_module_declares_the_field` was **removed**, for three
    reasons:
    - it touched no database, yet it was skipped whenever the database was absent;
    - "without the change" it failed only by `AttributeError` (no `_DENSITY_DECL`);
    - it asserted equality with the old substring rule on today's source, so it would fail on a future harmless
      comment.

    Its measurement is kept as evidence instead (`r232_declarations.txt`, script `r232_live.py`).
- **Mutation** (finishing builder, `mutation_runs.log` tail, supersedes the first builder's R232 entries):
  - R232-M1 substring restored → **5 failed** (4 mention cases + the emit comment case);
  - M2 strings not blanked → 2 failed;
  - M3 comments not stripped → 3 failed;
  - M4 `?:` unrecognised → 1 failed.
  - Each run was reverted byte-identical; the suite afterwards read 250 passed, 20 skipped.
- **Live source:** 155 capability modules; 45 mention the name and 45 declare it. **0 modules change status**, so
  0 Dens.served verdicts move today.

## §3 — Proof 1: every branch that can yield PASS or N/A

Lines are at `8f5e2fd29`. `CLOSABLE = (PASS, NA)` is at `:1738`. The labels are W2-1's: **genuine**, **fixed**,
**proxy**, **contested**. "(W2-2)" marks a W2-2 change.

**v1.1:** C-KSHETRA inserts code at `idem_scan`, so line numbers move at `2e1c06d1b`:
- sites from `:400` to `:1176` shift by +152 (#2 → `:548`, #3 → `:553`, #4 → `:1047`, #11 → `:1307`);
- sites up to the Idem.pattern call site shift by +153 (#33 → `:1416`, #37 → `:1365`);
- later sites shift by +154 (#17 → `:1579`, #35 → `:1892`).

C-KSHETRA's new branch is a FAIL, not a PASS/N/A, so the count of 38 is unchanged.

| # | file:line | criterion — condition | label |
|---|---|---|---|
| 1 | `:386` | `Build.contract` PASS — AST scan of the registered class | **proxy** (A1). Its reach was widened by R43; the 13 new live PASSes were hand-scanned: no commit/close/rollback call and no `asset_throughput` write in any resolved file (§4.3). |
| 2 | `:402` | `Idem.pattern` PASS — `ON CONFLICT` in the writer's SQL (upsert layers) | **proxy** (A2); R20 is W2-3 |
| 3 | `:405` (v1.1: `:553`) | `Idem.pattern` PASS — v1.0: `DELETE FROM` present; **v1.1: a DELETE naming the asset's own table, not behind a populated-output refusal** | v1.0: **proxy** (A2), and live **WRONG** on ka_kshetra (PASS on a refused rebuild; review §4.1). **v1.1: fixed in `2e1c06d1b` (C-KSHETRA)** for a sibling-table or fragment DELETE and for a refused rebuild. It is **still a proxy** for delegated replacement (R20). |
| 4 | `:895` | `Build.history` PASS — cascade-blocked only, ≥1 completion | genuine (R49: text dated, total order) |
| 5 | `:905` | `Build.history` PASS — no error/abort, ≥1 completion | **fixed** (C1); tallies exact after R233/R50 (W2-2) |
| 6 | `:989` | Earn N/A — never attempted (routed from `:1061`: no started attempt on any chart) | genuine per D6; **wired by D6.2** (W2-2); unreachable in production while 1094 is absent |
| 7 | `:992` | Earn N/A — healthy non-execution (skip, *derived* probe-green `:1081`, writerless) | genuine per D6; probe-green is an inference (receipt + era), disclosed; unreachable in production |
| 8 | `:994` | Earn N/A — failed before completion | genuine per D6; unreachable in production |
| 9 | `:999` | Earn PASS — completion write, finite duration, **linked** (`:1064`) | genuine per D6 + D6.2 link; unreachable in production |
| 10 | `:1011` | Cost PASS — sanctioned baseline from a linked attempt | genuine per D6 + D6.2; unreachable in production |
| 11 | `:1155` | contract/idem N/A — no writer, registry agrees | fixed (W2-1 `61c6e637a`); R43 shrank the NO_DETECTOR twin |
| 12 | `:1286` | `Count.floor` N/A — `target_floor=0` | fixed (W2-1) |
| 13 | `:1301` | `Count.floor` PASS — live ≥ floor | fixed (W2-1); **extended by R46** to a view's count (W2-2) |
| 14 | `:1346` | `Carr.detector` adopted verdict (closed set, exit 0) | genuine |
| 15 | `:1409` | `Build.registered` PASS — one `@register`, registry agrees | genuine; recognition widened by R43. Caveat: a decorated class inside a factory function is counted without proving the factory runs; the 3 live cases (ka_dasha_kala, ka_gochara_resonance, ka_tulana) call it at module level (hand-verified). |
| 16 | `:1417` | `Build.registered` N/A — no `@register`, no writer | genuine |
| 17 | `:1425` | `Build.target` PASS — `target_table` declared | genuine (declaration) |
| 18 | `:1427` | `Build.target` N/A — declared service or writerless | **fixed in `83f143be1` (R53)**; was contested at W2-1 |
| 19 | `:1436` | `Build.dag` PASS — in-layer edges resolvable | **contested / not fixed** (OS-2, no row) |
| 20 | `:1442` | `Build.count_integrity` PASS — both SQLs present | genuine (presence) |
| 21 | `:1442` | `Build.count_integrity` N/A — no writer, no count_sql | genuine |
| 22 | `:1475` | `Build.completion` N/A — no count_sql, nothing built | fixed (W2-1) |
| 23 | `:1534` | `Build.completion` PASS — `rows_written == live`, completed record | fixed (W2-1); **R44** — latest row, a tie → ERRORED (`:1511`); **R46** — a view never PASSes (`:1481`) (W2-2) |
| 24 | `:1566` | `Complete.depth` PASS | fixed (W2-1) |
| 25 | `:1608` | `Vocab.identity` PASS | fixed (W2-1), F7 proxy caveat |
| 26 | `:1635` | `Vocab.alias` PASS | genuine; R54 adds `severity` (0.0 on PASS) |
| 27 | `:1650` | `Ldgr.source_presence` PASS | genuine |
| 28 | `:1674` | `Dens.served` N/A — scanned, no module | fixed (W2-1); **R51**: comment-only attribution → NO_DETECTOR, never N/A (W2-2) |
| 29 | `:1674` | `Dens.served` PASS — ≥1 referencing module declares | **basis fixed** (attribution by code, R51; declaration by property, R232). **Grading contested:** ≥1 of N (OS-3) — 20 of 40 live PASSes are partial. |
| 30 | `:1681` | `Build.exercised` N/A — never run, no writer | genuine |
| 31 | `:1684` | `Build.history` N/A — never run (delegation) | genuine |
| 32 | `:1698` | `Build.exercised` PASS — ≥1 started row | fixed (C1); executed count exact after R233, malformed line fail-closed by R50 (W2-2) |
| 33 | `:1263` | `Build.dep_liveness` PASS — every dependency `lit` at chart 482012f1 or global | **fixed in `1d2544f23` (R45)**. Residual: `lit` is trusted whatever set it (OS-D; 1 live dependency). |
| 34 | `:1704` | `Build.dep_liveness` N/A — no declared dependencies | genuine |
| 35 | `:1738` | `CLOSABLE` allowlist | genuine |
| 36 | `:1690` | `Build.exercised` N/A — rows but none started, no writer | genuine |
| **37** | `:1212` | **new (R53)** `Build.target` PASS — `count_sql` names ≥2 tables | **proxy.** It mirrors the engine's heuristic, which counts a JOINed lookup as "produced": ga_structural's PASS text names `fact_category_ownership`, which migrations 842/845 populate and it does not produce. An undeclared single table plus a JOIN would PASS (0 live instances). OS-A. |
| **38** | `:1217` | **new (R53)** `Build.target` PASS — its one count table is another active asset's declared target | genuine for the declaration; it does not prove the writer writes there (hand-verified for ga_strength: `ga_strength_writer.py:1630 INSERT INTO chart_facts`) |

**Tally: 38 branches.**
- **20 genuine:** #4, 6–10, 14–17, 20, 21, 26, 27, 30, 31, 34, 35, 36, 38. Of these, #6–10 cannot be reached in
  production while the instrument is absent.
- **12 fixed:** #5, 11, 12, 13, 18, 22, 23, 24, 25, 28, 32, 33. W2-2 fixed #18 and #33 and strengthened #5, 13,
  23, 28 and 32.
- **4 proxy:** #1, 2, 3, 37. v1.1: #3 is partly fixed (C-KSHETRA); it remains a proxy for delegation.
- **2 contested:** #19, and #29's grading.

Changes from W2-1's 36:
- #18 and #33 moved from contested to fixed.
- #29 is partly fixed.
- #37 and #38 are new.
- No branch was removed.

## §4 — Proof 2: six-layer census, HEAD `8f5e2fd29` vs `931dbc479`

**Method.**
- Read-only runs with `--out` to scratch and `NIKASHA_CONTROL_DIR` on a scratch copy; no `--emit-gaps`.
- The base ran in a temporary worktree under `<scratchpad>/w2-2/wt_base`, removed after use.
- Six layers ran in parallel under `timeout 300` each (`census_runs.log`):
  - HEAD: L0 165 s, L1 194 s, L2 224 s, L3 192 s, L4 52 s, L5 54 s — every run rc=2 (failures measured).
  - Base: L1, L2 and L3 hit the 300 s cap under parallel load (as in W2-1) and were re-run alone (94 s, 83 s,
    107 s; rc=2).
- Diff script: `diff_census_w2_2.py`; full output: `census_diff_931dbc479_vs_head.txt`.

### §4.1 Headline

| layer | assets | 931dbc479 PASS/N/A/FAIL/PARTIAL/NO_DET | HEAD PASS/N/A/FAIL/PARTIAL/NO_DET |
|---|---|---|---|
| L0 | 40 | 406 / 69 / 43 / 50 / 122 | 407 / 68 / 42 / 50 / 123 |
| L1 | 19 | 212 / 5 / 7 / 45 / 61 | 213 / 3 / 7 / 45 / 62 |
| L2 | 23 | 265 / 5 / 15 / 51 / 70 | 259 / 5 / 15 / 57 / 70 |
| L3 | 21 | 174 / 13 / 55 / 28 / 83 | 197 / 13 / 39 / 41 / 63 |
| L4 | 9 | 87 / 0 / 27 / 16 / 29 | 89 / 0 / 18 / 25 / 27 |
| L5 | 15 | 122 / 29 / 31 / 15 / 57 | 126 / 29 / 28 / 18 / 53 |

ERRORED 0 at both commits. NOT_GENERIC is unchanged (80/38/46/42/18/30).

### §4.2 Every verdict change, grouped by cause (71; 0 unexplained)

| cause | change | n | assets |
|---|---|---|---|
| R43 writer recognised | `Build.registered` FAIL→PASS | 13 | ka_dasha_kala, ka_gochara_resonance, ka_kota_chakra, ka_kshetra, ka_moorti_nirnaya, ka_muhurta_seva, ka_sudarshana_varsha, ka_tithi_pravesha, ka_tulana, ka_vedha_gochara, ph_rectification, mi_bhara, mi_sankalpa |
| R43 contract scan now runs | `Build.contract` NO_DET→PASS | 13 | the same 13 |
| R43 idempotency scan now runs | `Idem.pattern` NO_DET→PASS | 8 | ka_gochara_resonance, ka_kota_chakra, ka_kshetra, ka_moorti_nirnaya, ka_sudarshana_varsha, ka_tithi_pravesha, ka_vedha_gochara, ph_rectification |
| R43 idempotency scan now runs | `Idem.pattern` NO_DET→PARTIAL | 5 | ka_dasha_kala, ka_muhurta_seva, ka_tulana, mi_bhara, mi_sankalpa (no pattern in the writer's own SQL — delegates; R20) |
| R45 stale at chart scope | `Build.dep_liveness` PASS→PARTIAL | 10 | bo_anveshana, bo_chart_gestalt, bo_pramana_mapa, bo_samvada, bo_upaya, bo_yantra_mechanism, ka_avadhi, ka_kshetra, ka_sangam, ka_yojaka (= C2's ten) |
| R45 stale at chart scope | `Build.dep_liveness` FAIL→PARTIAL | 16 | ka_bhavishya_lekha, ka_jivana_parva, ka_kala_darshana, ka_kalasutra, ka_tulana, ka_vighnakara, ph_muhurta, ph_nimitta, ph_phaladesa, ph_pramana, ph_pratikara, ph_rectification, ph_sankrama, ph_sodhana, ph_suddha_sodhana, mi_bhavisya (every non-lit dependency is `stale` on 482012f1; the old rule graded "not lit on any chart" as dead) |
| R51 comment-only attribution | `Dens.served` FAIL→NO_DET | 1 | bg_dignity_reference |
| R51 comment-only attribution | `Dens.served` PASS→NO_DET | 1 | ga_strength (its only "declaring" module named it in a comment) |
| R51 attribution by code | `Dens.served` PASS→FAIL | 1 | ph_nimitta (0 of 2 code-referencing modules declare) |
| R53 target-less writer graded | `Build.target` N/A→PASS | 3 | bg_prashna_rules, ga_strength, ga_structural |

R44, R49, R46, R50, R54, D6.2, R233 and R232 move **no** verdict today:
- R44: no multi-row key exists.
- R46: bo_samvada stays NO_DET and N/A.
- R232: 0 modules change status.
- D6.2: the instrument is absent.

**Text-only changes: 500**, each attributed to a row:

| row | changes | where |
|---|---|---|
| D6.2 — the NO_DETECTOR text names the linked attempt | 254 | Earn + Cost on all 127 assets |
| R49 — latest error, dated | 79 | Build.history; leading counts identical on all 79, so no data drift |
| R45 — the text states the scope | 73 | Build.dep_liveness |
| R51 — module lists | 62 | Dens.served |
| R233 — executed count now newline-safe | 29 | Build.exercised; on all 29 the executed count rose and the raw row count was unchanged, so no build activity landed between the two runs |
| R46 — bo_samvada | 2 | Build.completion, Count.floor |
| R54 — fraction stated | 1 | Vocab.alias |

### §4.3 FAVOURABLE flips (→PASS or →N/A): 37, each with its measurement and an independent check

- **Build.registered FAIL→PASS (13) — genuine.** The census reads a real `@register` on a real class:
  - literal ids for the ten L3 service writers (`services/<x>/writer.py`), reached through the `writers/<x>.py`
    shim that imports them;
  - resolved constants for mi_bhara (`ASSET_ID = "mi_bhara"`, `@register(ASSET_ID)` :87) and mi_sankalpa (:48/:76);
  - the package `ph_rectification/__init__.py:246`.

  Hand-check: every shim exists and imports its service module. The three factory-built classes (ka_dasha_kala
  :172, ka_gochara_resonance :558, ka_tulana :135) are instantiated at module level, so the decorator fires on the
  engine's discovery import.
- **Build.contract NO_DET→PASS (13) — proxy #1, verdict hand-verified.** The census measurement is the AST scan of
  the resolved class. Hand-check (`r43_r53_favourable_flip_handcheck.out`): a text scan of every line of the 13
  resolved files finds no `.commit()`, `.close()` or `.rollback()` call and no `asset_throughput`
  INSERT/UPDATE/DELETE; the only hits are docstrings stating "NEVER calls …".
- **Idem.pattern NO_DET→PASS (8) — proxy #3. 7 correct, 1 WRONG (v1.1, corrected).**
  - **Correct (7):** these writers DELETE FROM their registry target on the rebuild path: gochara_resonance_map,
    kala_kota_chakra, kala_moorti_nirnaya, kala_sudarshana_varsha, kala_tithi_pravesha, kala_vedha_gochara,
    phala_rectification.
  - **ka_kshetra's PASS was WRONG.** v1.0 said it was "true, but the census's evidence does not measure it". That
    was false.
    - The census matched two strings: `DELETE FROM build_substep_progress` and a bare f-string fragment
      `'DELETE FROM '`.
    - My v1.0 hand-check then read the `_OWNED_TABLES` delete loop (`services/ka_kshetra/writer.py:2431–2434`) and
      stopped. It missed the guard in front of that loop.
    - `_run_prepare_replace` calls `_populated_owned_table()` and **raises `KshetraReplacementHeld`**
      (`writer.py:543–551`) when any writer-owned table already has rows for the chart. Only an output-empty chart
      reaches `_delete_prior_rows`.
    - 482012f1 holds 8,570,075 `kala_field` rows. So a rebuild of the canonical chart **holds; it does not
      replace**. §N.3's "rebuild replaces" is deliberately not met (DP-SD-017 W0).
    - That is the same proxy error twice, in the census and in my hand-check: a right-looking answer for the wrong
      reason, the §N.8 defect class.
  - **Fixed by C-KSHETRA (`2e1c06d1b`):** ka_kshetra now reads `FAIL — rebuild refused when target is populated:
    services/ka_kshetra/writer.py:545 (raise KshetraReplacementHeld after the output-existence probe
    _populated_owned_table)`.
- **Build.target N/A→PASS (3) — R53** (`r53_target_handcheck.txt`):
  - **bg_prashna_rules — genuine.** Five count tables; its writer delegates to
    `brahmagyan/l0_prashna.seed_prashna_rules`, which INSERTs into all five.
  - **ga_strength — genuine (#38).** It counts its share of `chart_facts`, the declared target of 7 active assets
    (ga_ayurdaya, ga_nakshatra, ga_panchanga, ga_positions, ga_sade_sati, ga_sensitive, ga_sensitive_degree).
    Writer: `ga_strength_writer.py:1630 INSERT INTO chart_facts`.
  - **ga_structural — verdict supported, stated measurement wrong (#37, OS-A).** It PASSes through the "≥2 tables"
    branch, "chart_facts, fact_category_ownership … tables it produces". Its `count_sql` JOINs
    `fact_category_ownership`, which only migrations populate (842, 845); no sidecar writer INSERTs into it. The
    PASS is independently earned through #38's rule (a chart_facts partition writer), but the text the census
    writes is false.

**v1.1 tally: 36 of the 37 favourable flips were correct; ka_kshetra's `Idem.pattern` was wrong.** No other flip is favourable. The 26 dep_liveness changes all land on PARTIAL (non-closable). Each of the 3
Dens.served changes moves away from PASS/N/A.

## §5 — Proof 3: `--emit-gaps` dry runs on ledger copies

### §5.1 HEAD CLI emit on a copy of the production ledger (`emit_dry_run_head.log`)

The copy started as the 263-line production ledger (md5 `30365ff2…`). The six layers ran sequentially:
```
NIKASHA_CONTROL_DIR=<scratch>/w2-2/ctrl_emit_head \
  timeout 300 python3 platform/scripts/governance/asset_census.py --layer <L> --emit-gaps --out <scratch>/…
L0  ledger:   6 row(s) appended, 209 already present, 0 closed by measurement, 0 re-opened
L1  ledger: 114 row(s) appended,   0 already present, 0 closed by measurement, 0 re-opened
L2  ledger: 142 row(s) appended,   0 already present, 0 closed by measurement, 0 re-opened
L3  ledger: 143 row(s) appended,   0 already present, 0 closed by measurement, 0 re-opened
L4  ledger:  70 row(s) appended,   0 already present, 0 closed by measurement, 0 re-opened
L5  ledger:  99 row(s) appended,   0 already present, 0 closed by measurement, 0 re-opened
```

**Transitions by type:**
- **OPEN (new): 574.** By criterion (`emit_closure_check_head.out`): Build.completion 38, Build.count_integrity 4,
  Build.dep_liveness 37, Build.history 83, Carr.detector 87, Complete.depth 51, Cost.baseline 87, Count.floor 16,
  Dens.served 37, Earn.build_record 87, Idem.pattern 40, Vocab.identity 7.
- **CLOSED 0. RE-OPENED 0.** 209 were already present (L0).

Reconciliation with W2-1's first emit (596): +12 newly failing (1 ga_strength Dens.served, 10 dep_liveness,
1 ph_nimitta Dens.served) − 34 now passing (R43) = 574. Build.contract 13 → 0, Build.registered 13 → 0,
Idem 48 → 40, dep_liveness 27 → 37, Dens.served 35 → 37.

**Closure check.**
- "CLOSED rows lacking a genuine PASS / justified N/A: none" is vacuous, because nothing closed.
- The non-vacuous check covers every closable verdict the census emitted, on all 127 assets: **0 N/A verdicts
  fall outside the justified set** (W2-1: 3, the contested R53 `Build.target`). N/A distribution:
  - Build.completion 6, Build.contract 5, Build.registered 5, Idem 5;
  - count_integrity 2, dep_liveness 28, exercised 5, history 6;
  - Build.target 7 (6 service + 1 writerless data, `lel_events`);
  - Count.floor 23 (floor 0), Dens.served 26.

**Idempotency.** Re-emitting the same six census documents gives `(0, N, 0, 0)` per layer
(215/114/142/143/70/99 present), and the copy is byte-identical afterwards (`cmp`). The emit-run census and the
§4 HEAD census agree on 2 446 / 2 446 verdicts.

### §5.2 The second emit, simulated (`emit_seq.py`, `emit_second_emit_simulation.log`, `second_emit_transitions.txt`)

On one fresh copy, the stored §4 base censuses were emitted first with **the base module's own `emit_gaps`** (the
code the R222 gate cleared for the first production emit). The stored §4 HEAD censuses were then emitted with
HEAD's. `emit_gaps` is unchanged between the two commits.
```
base L0..L5 appended/present/closed/reopened = (6,209,0,0) (113,0,0,0) (136,0,0,0) (166,0,0,0) (72,0,0,0) (103,0,0,0)
head L0..L5 appended/present/closed/reopened = (0,215,0,0) (1,113,0,0) (6,136,0,0) (4,139,27,0) (1,69,3,0) (0,99,4,0)
```
The first step reproduces W2-1's 596 appended / 0 closed exactly.

**Second-emit transitions:**
- **CLOSED 34:**
  - Build.registered 13, Build.contract 13 — the §4.3 R43 assets;
  - Idem.pattern 8 — ka_gochara_resonance, ka_kota_chakra, ka_kshetra, ka_moorti_nirnaya, ka_sudarshana_varsha,
    ka_tithi_pravesha, ka_vedha_gochara, ph_rectification.
- **OPEN 12:** dep_liveness 10 (C2's ten, now PARTIAL); Dens.served 2 (ga_strength NO_DETECTOR, ph_nimitta FAIL).
- **RE-OPENED 0.**

Each CLOSED row names its measurement (`CLOSED by measurement: @register in …; registry agrees`, `…: conformant`,
`…: DELETE FROM present (delete-then-insert)`). **0 dep_liveness and 0 Dens.served rows close.**

**v1.1 correction.** v1.0 said all 34 closures were hand-verified correct. They were not: **33 of 34 were earned.**
`ka_kshetra-Idem.pattern` would have closed on "DELETE FROM present (delete-then-insert)" for a writer that
refuses to rebuild a populated chart (§4.3).

**Re-run at `2e1c06d1b`** (`emit_second_emit_simulation_ck.log`, `second_emit_transitions_ck.txt`): the base
module's first emit is the same (596 appended, 0 closed). The second emit gives:
```
ck L0..L5 appended/present/closed/reopened = (0,215,0,0) (1,113,0,0) (7,136,0,0) (5,140,26,0) (1,69,3,0) (0,99,4,0)
```
- **CLOSED 33:** Build.contract 13, Build.registered 13, Idem.pattern 7. `ka_kshetra-Idem.pattern` is **absent**,
  and the other 33 ids are exactly the v1.0 set (0 added).
- **OPEN 14:** the v1.0 12, plus `bo_upaya-Idem.pattern` and `ka_gochara-Idem.pattern`, which now read PARTIAL (§10).
- **RE-OPENED 0.**
- ka_kshetra's Idem.pattern gap, opened by the first emit, stays OPEN (FAIL).

### §5.3 Ruling — does R45 + R232 landing make a SECOND production emit's closures trustworthy?

**v1.1 (corrected, as W2-2_REVIEW's ruling):** at `8f5e2fd29` a second emit was **NOT** safe on today's data. It
would have closed `ka_kshetra-Idem.pattern` on a false measurement; 33 of its 34 closures were earned. At
`2e1c06d1b` (C-KSHETRA) the simulated second emit closes exactly those 33, all earned, and not ka_kshetra. The
review's C2 hand-withholding of that row is no longer needed for this code, but it applies to any emit run on
`8f5e2fd29`. v1.0's text follows, with its "each correct" claim struck by the correction above.

**For the two blockers the W2-1 gates named: yes.**
- **C2 (dep_liveness "lit on any chart") is closed by R45.** The ten assets it named now read PARTIAL and would open
  gaps. No dep_liveness gap can close on another chart's state, as proven by the mutation V-R45-any-chart-record
  and by `test_r45_an_open_dep_liveness_gap_does_not_close_on_another_charts_lit`.
- **F-S1 (Dens.served declaration read from a comment) is closed by R232**, proven by
  `test_r232_an_open_dens_served_gap_does_not_close_on_a_comment`; 0 live instances either way.
- ~~On today's data, the 34 closures a second emit would make are each correct by independent hand-check.~~
  **v1.1:** 33 of 34 were correct; ka_kshetra's was not. Since `2e1c06d1b`: 33 closures, all correct.

**Not trustworthy by construction.** Four things keep it from being so (v1.1 adds the fourth, from the review):
1. `Build.contract` and `Idem.pattern` close on **proxy detectors** (#1, #2, #3).
   - ka_kshetra is a live case: the census's evidence names a table other than the one it claims about. The
     verdict is right, but only by coincidence of the proxy.
   - A future writer whose DELETE hits only a sibling table would close its gap the same way.
2. **R45 residual (OS-D):** a dependency counts as live when `asset_throughput.state='lit'`, whatever set it.
   - `bg_sarvatobhadra_grid` is `lit` (global, rows_written 0, no started orchestrator attempt ever, empty table).
     `ka_vedha_gochara`'s dep_liveness reads PASS partly on it, at both commits.
   - A dep_liveness gap opened today could close later on such a row.
3. **Dens.served grading (OS-3):** a PASS needs only one declaring module out of N (20 of 40 live PASSes are
   partial). A later emit could close a Dens.served gap on one of N.
4. **Hand-verification itself can be a proxy (v1.1).** My v1.0 hand-check confirmed a DELETE and missed the
   refusal guard in front of it. A hand-verify of a CLOSED `Idem.pattern` row must read the **rebuild path on a
   populated chart**, not only whether a DELETE exists. C-KSHETRA now detects one refusal shape structurally.
   Others (a refusal inside a probe the census cannot see, or delegated replacement) remain for R20.

**Recommendation for the executor/native (not a builder decision):** the second production emit can run with C2
and F-S1 discharged. Keep W2-1_C1_REVIEW's "hand-verify every CLOSED row" discipline for `Build.contract`,
`Idem.pattern`, `Dens.served`, `Build.dep_liveness` and `Build.target` (#37) until R20 (W2-3), OS-3 and OS-D are
decided. v1.1: on today's data, at `2e1c06d1b`, that is the 33 rows in `second_emit_transitions_ck.txt`.

## §6 — Proof 4: suite, fingerprint, drift, ledgers

| run | result |
|---|---|
| offline, `931dbc479` (temporary worktree) | 214 passed · 11 skipped · **2 failed** (227) — `suite_base_offline.txt` |
| offline, HEAD `8f5e2fd29` | 269 passed · 20 skipped · **2 failed** (291; +64, all in `test_w2_2_latest_row_registration_timing.py`) — `suite_head_offline.txt` |
| live, HEAD, 3 invocations under the 300 s cap | 287 passed + 2 failed (292.5 s); `test_live_e2e_one_simulated_query_timeout_degrades_not_aborts` 1 passed (67.2 s); `test_live_e2e_depth_census_failure_does_not_blind_identity_for_the_same_asset` 1 passed (211.5 s) → **289 passed, 2 failed, 0 skipped** |

**Pre-existing failures.** The same two tests fail in the clean `931dbc479` worktree before any W2-2 change:
- `test_drift_detector_h35_h38.py::test_f163_current_row_flagged_predecessor_row_is_not`
- `test_drift_detector_h35_h38.py::test_h35_critical_when_canonical_artifacts_missing`

They are outside the Lane A files and are W2-1's same pair.

**Other checks.**
- **Fingerprint.** `python3 platform/scripts/governance/manifest_fingerprint.py --check` →
  `entries: 141 (declared 141) / fingerprint declared: 0c723f4a1b6a6ea5 / fingerprint observed:
  0c723f4a1b6a6ea5 / MATCH`. None of the five touched files appears in `CAPABILITY_MANIFEST.json` (0 mentions each).
- **Drift.** `timeout 600 python3 platform/scripts/governance/drift_detector.py` (pgenv sourced) → **exit 3**.
  It reports 1 finding, LOW `a3_category_not_yet_populated`: "73 CHART_FACTS_SCHEMA.json categories not yet in DB
  (pending writers)" — identical to W2-1. The report went to the gitignored `00_ARCHITECTURE/drift_reports/`
  (`.gitignore:32`).
- **Ledgers.** `asset_gaps.jsonl` `30365ff2238c75f5f62e622b70292da3` (263 lines) and `asset_certs.jsonl`
  `514cbdfcf3fa71b3e382f84a978bf369` (1 line) are unchanged at session start, after §4, after §5.1/§5.2 and at
  report time.

## §7 — Honest limits

1. **Two builders.** R233–R54 were built by the first builder. For those rows the finishing builder did **not**
   re-run every mutation or without-the-change run; those are cited from `mutation_runs.log`. It re-ran one or
   two mutations per row at the final HEAD (§2), and all were killed.
2. **R232's detector is syntactic.**
   - It over-counts any code token `density_contract:` / `?:`: a type annotation, a function parameter, the
     else-branch of a ternary, `density_contract: null`.
   - It under-counts (fail-safe) a quoted key `'density_contract': …` and shorthand `{ density_contract }`.
   - `_ts_code` does not recognise regex literals or nested template literals inside `${…}`; a quote in a regex
     literal could flip string/code parsing.
   - 0 live instances: all 45 declaring modules use `density_contract: {`.
3. **R232 does not touch the ≥1-of-N grading (OS-3).**
4. **D6.2 is proven offline and by simulation only.** Migration 1094 is absent in production, so Earn/Cost read
   NO_DETECTOR on 127/127; branches #6–10 have no live instance.
5. **R44's tie → ERRORED is proven offline.** No live (asset, chart) key has more than one row.
6. **R43** follows first-party imports one level deep and counts a decorated class inside a factory without proving
   the factory runs; the 3 live cases do run. **R53** #37 is the engine's heuristic (OS-A). #38 checks the
   declaration, not the write.
7. **R45** measures one chart (482012f1, else global) and trusts `lit` provenance (OS-D).
8. **R50** does not reproduce the historic 108-vs-107 figure (not reproducible today); it removes the class.
9. **R233's own test is live-only.**
10. **Census runtime.** Three base layers exceeded 300 s in parallel and were re-run alone; the HEAD L2 run took
    224 s under parallel load.
11. **§4.3 hand-checks** are static reads of the writer source plus read-only queries. They show what the code does,
    not that a particular past build ran it.

## §8 — Out-of-scope findings (listed, not fixed)

- **OS-A (R53, #37).** `_grade_target_less`'s "≥2 count tables" branch treats a JOINed lookup table as produced.
  - ga_structural's PASS text names `fact_category_ownership`, which it does not produce. **v1.1 (C3a):** the table
    is created and seeded by **migration 410** (`410_ga_structural_category_ownership.sql`, 58 ga_structural rows),
    realigned by 418, and backfilled by 842/845 (v1.0 named only 842/845). Live: 67 rows, 64 owned by
    ga_structural.
  - A writer with one undeclared produced table plus a JOIN would PASS where R53 intends FAIL. 0 live instances.
  - The R53 commit message says ga_structural PASSes as a chart_facts partition; the live census PASSes it through
    the ≥2 branch.
- **OS-B (R53, cosmetic).** `owners.setdefault("map", target_owners())` (:1430) evaluates `target_owners()` on
  every call, although the comment at the `owners` declaration says "at most once per layer". **v1.1 (C3b): that is
  1 read on L1 today, not 2** — only ga_strength reaches the one-table branch; ga_structural takes the ≥2-table
  branch. There is no correctness effect.
- **OS-C (#3) — v1.1: mis-scoped in v1.0, now FIXED in-packet (C-KSHETRA, `2e1c06d1b`).**
  - v1.0 said "the verdict is true via `_OWNED_TABLES`". It was **false**: the writer refuses any populated
    rebuild (`KshetraReplacementHeld`, `writer.py:543–551`), so the PASS was wrong.
  - The detector now requires a DELETE naming the asset's own table, reachable on a populated rebuild. ka_kshetra
    reads FAIL.
  - **For R20's W2-3 acceptance (the executor registers this; not written to the register here):** Idem.pattern
    must grade ka_kshetra's guarded/refused-rebuild shape correctly — a held or refused replacement is never
    closable idempotency. A counted DELETE must name the asset's target and be reachable on a populated rebuild.
    Delegated replacement (bo_upaya → `bodha_writers/_idempotency.py:425–450`) must be followed, not guessed.
- **OS-D (C2 residual, R45).** `Build.dep_liveness` trusts `state='lit'` regardless of who set it:
  bg_sarvatobhadra_grid is lit (global, rows_written 0, no started attempt, empty table) under ka_vedha_gochara's
  PASS. `r45_lit_without_run.txt` has the query.
- **OS-E (OS-3 carried).** `Dens.served` PASSes on ≥1 of N declaring modules: 20 of 40 live PASSes are partial
  (W2-1: 29 of 42 before R51's attribution fix).
- **OS-F (info).** R43 surfaces `ka_gochara_v3_century_materialize` (`is_active=false`) as registered but outside
  the active registry.
- **OS-G (process, as W2-1 OS-12).** `drift_detector` writes an ad-hoc report into the gitignored
  `00_ARCHITECTURE/drift_reports/`.
- **OS-H (evidence hygiene).** The first builder's `mutation_runs.log` holds superseded entries: R49 drafts, D6.2 M2
  and without-the-change, R51-M3, and an unfinished R232-M2 (its after-revert line was lost when the builder was
  stopped). Each is annotated in place; the finishing builder's entries at the end supersede them.

## §9 — Evidence index (`nikasha_test/wave2/w2-2_evidence/`)

- **Mutations:**
  - `mutation_runs.log` — first builder, plus the finishing builder's R232 runs at the tail;
  - `mutation_reverify_final_head.log` / `.sh` — the re-verification;
  - `mut.sh`, `without.sh`, `sub.py`.
- **Per-row live evidence:** `r233_live.txt`, `r43_registered_before.txt`, `r43_registered_after.txt`,
  `r45_before_after.txt`, `r51_attribution.txt`, `d6_2_live_linkage.txt`, `r232_declarations.txt` + `r232_live.py`.
- **Proof 2:** `census_diff_931dbc479_vs_head.txt`, `diff_census_w2_2.py`, `rawdiff.py`, `census_runs.log`,
  `census_summaries.log`.
- **Favourable-flip hand-checks:** `r43_r53_favourable_flip_handcheck.py` / `.out`, `r53_target_handcheck.txt`,
  `r45_lit_without_run.txt`.
- **Proof 3:** `emit_dry_run_head.log`, `emit_closure_check_head.out`, `check_emit_head.py`, `emit_seq.py`,
  `emit_second_emit_simulation.log`, `second_emit_transitions.txt`.
- **Proof 4:** `suite_base_offline.txt`, `suite_head_offline.txt`, `suite_head_live_part1..3.txt`, `drift.out`.
- **v1.1 (C-KSHETRA):**
  - `mutation_runs_ckshetra.log` — CK-M1…M5, plus the R53-M3 natural-form run;
  - `census_diff_8f5e2fd29_vs_ckshetra.txt`, `census_runs_ckshetra.log`, `idem_compare.py`;
  - `emit_second_emit_simulation_ck.log`, `second_emit_transitions_ck.txt`, `emit_first_emit_ck.log`;
  - `suite_ck_live_touched.txt`.

## §10 — Corrections after gate review (v1.1; `W2-2_REVIEW.md`, 9f84ecf6a, ACCEPT_WITH_CORRECTIONS)

| item | what | commit | test | mutation evidence |
|---|---|---|---|---|
| **C-KSHETRA** | `Idem.pattern`: (a) a counted DELETE must name one of the asset's own tables (target_table ∪ count_sql tables), literally or through a resolved module constant or `for`-loop sequence; a bare fragment names nothing; (b) a rebuild that raises on the populated polarity of an output-existence probe before its delete path reads **FAIL** with the raise's location, never PASS | `2e1c06d1b` | `test_ckshetra_a_rebuild_refused_on_a_populated_chart_never_passes[guard / no-guard control / empty-polarity control]`; `test_ckshetra_a_counted_delete_must_name_the_assets_own_table[sibling / fragment / literal-own / no-target]`; `test_ckshetra_an_open_idem_gap_does_not_close_on_a_refused_rebuild` (measure() + emit_gaps on a ledger copy, closed 0); `test_ckshetra_the_real_ka_kshetra_does_not_pass_and_a_real_replacing_writer_does` (real source: ka_kshetra FAIL naming `services/ka_kshetra/writer.py`, ka_kota_chakra PASS) | **CK-M1 guard reverted → 3 failed**: guarded fixture, emit gap closes, and the **real ka_kshetra PASSes again**. CK-M2 any delete counts → 3. CK-M3 old rule restored → 8 of 9. CK-M4 guard polarity ignored → 1. CK-M5 loop tables unresolved → 2. All reverted byte-identical; the suite afterwards read 259 passed, 20 skipped, 21 deselected. |
| **C1** | §0, §4.3, §5.2, §5.3 and OS-C rewritten: ka_kshetra's PASS was **wrong**, not "correct by accident"; 33 of 34 simulated second-emit closures were earned at `8f5e2fd29`; 33 of 33 at `2e1c06d1b` | this report commit | — (text) | — |
| **C3a** | `fact_category_ownership`: created and seeded by migration **410**, then 418/842/845 (OS-A) | this report commit | — | — |
| **C3b** | OS-B: **1** `target_owners()` read on L1, not 2 | this report commit | — | — |
| **C3c** | The R53-M3 claim is withdrawn: its spec was not recorded, and its natural form is an equivalent mutant (§2 R53) | this report commit | — | `mutation_runs_ckshetra.log` tail: natural form **7 passed (survives)** |

**C-KSHETRA — what moved (six-layer census, read-only, `2e1c06d1b` vs `8f5e2fd29`,
`census_diff_8f5e2fd29_vs_ckshetra.txt`).** 3 verdict changes, all `Idem.pattern`, none toward PASS or N/A:

| asset | change | measured | why honest |
|---|---|---|---|
| **ka_kshetra** | PASS → **FAIL** | `rebuild refused when target is populated: services/ka_kshetra/writer.py:545 (raise KshetraReplacementHeld after the output-existence probe _populated_owned_table)` | The flip the review required. |
| **bo_upaya** | PASS → PARTIAL | its literal DELETEs hit `bodha_rm_chart_summary`, `_dosha_remedy_bundles` and `_pattern_remedies`, none of its counted tables (`bodha_rm_resonances`, `bodha_rm_remedy_prescriptions`) | The old PASS was the sibling-table proxy W2-1 review A2 already named ("correct by coincidence"). The writer does replace its counted tables, through `replace_prior_rm_*` in `bodha_writers/_idempotency.py:425–450`, a delegation the scan does not follow (R20). So PARTIAL under-claims a true PASS: non-closable, the safe direction. |
| **ka_gochara** | PASS → PARTIAL | it deletes `{TABLE}` = `kala_gochara_windows_v2`; the registry declares `kala_gochara_windows` | The old PASS matched a bare fragment. The declared table is not the one it replaces: W2-1 F8's registry-data mismatch, for the owner. |

- **Not "exactly one flip".** The coordinator expected ka_kshetra alone to move. Requirement (a), applied as
  specified, also moves bo_upaya and ka_gochara. Both are cases the earlier gates had already called unearned
  evidence.
- **One case does not move:** mi_adhilepa deletes all five targets through a loop over a literal list, which (a)
  resolves, so it stays PASS.
- **Text-only changes: 43,** all `Idem.pattern` PASS texts that now name the table deleted and its line. No other
  criterion changed on any asset.
- **Guard false-positive check:** across all 127 assets, the refusal guard fires only on ka_kshetra
  (`idem_compare.py`).
- **The ka_kshetra FAIL (not PARTIAL):** it follows the coordinator's instruction (NO_DETECTOR or FAIL). The review
  suggested PARTIAL. Either is non-closable, and FAIL states a measured refusal. R20 may re-grade it.

**Emit dry runs at `2e1c06d1b`, all on ledger copies.**
- **First emit** (`emit_first_emit_ck.log`): 577 appended (= 574 + the 3 Idem.pattern rows now failing),
  0 CLOSED. The re-emit is byte-identical.
- **Simulated second emit:** 33 CLOSED, and `ka_kshetra-Idem.pattern` is absent from the closed set (§5.2).

**Test count.**
- Offline: 291 → **300** (278 passed, 20 skipped, 2 failed); the 2 failures are the same pre-existing
  `test_drift_detector_h35_h38.py` pair.
- Live, the two touched test files (`test_w2_2_…` + `test_a3_…`): **86 passed**.
- Three existing tests were adapted to the new `idem_scan(…, targets)` signature:
  - `test_a3`'s call-site text assertion and its `_boom` arity;
  - the R43 fixture now declares the `t_x` its writer deletes.

**Ledgers.** Production `asset_gaps.jsonl` / `asset_certs.jsonl` md5 `30365ff2…` / `514cbdfc…`, unchanged
throughout the corrections. The temporary base worktree was re-created for the base first emit and removed after.

**For R20's W2-3 acceptance (reported here; the executor folds it into the register):** Idem.pattern must handle
ka_kshetra's guarded/refused-rebuild shape correctly — a guarded or refused rebuild is not closable idempotency.
It must also follow delegated replacement (bo_upaya), and grade a registry target that differs from the table
replaced (ka_gochara, F8) as the registry-data finding it is.
