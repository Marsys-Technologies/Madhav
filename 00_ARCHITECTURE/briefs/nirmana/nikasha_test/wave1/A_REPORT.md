---
artifact: NIKASHA_WAVE1_LANE_A_REPORT
canonical_id: NIKASHA_WAVE1_LANE_A_REPORT
version: "1.1"
status: CORRECTIONS COMPLETE — awaiting the reviewer re-gate (§5 of the execution prompt); v1.0 was REJECTED (narrow) at A_REVIEW.md
review: 00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave1/A_REVIEW.md (8a57a3320)
lane: A
commits:
  - e2819e625e152427a98876865d8cf733a8f2b457   # A-1: R216 rebase
  - 432ed07dae3511596a20a057e49f8b68570eff77   # A-2: P3 closure loop
  - 7ed8707757195e680fc972fc42dc82f1ebc1d50b   # A-3: P4 precursors
corrections:   # after the gate review — §10 maps each finding to its commit, test and mutation
  - a77d50005   # F1 unwired D6 attempt path reads NO_DETECTOR, not N/A
  - 065e620b2   # F2 errored count_sql grades ERRORED, never N/A
  - cf955e3a3   # F3 behavioural replacements for tests that could not fail
  - 3a9c66cf9   # F4 WITHDRAWN terminal
  - cbc8b6724   # F5 superseded_by permanent across history
  - 6574d729b   # F6 tracker scoped to the active population
  - 0c16969a3   # F7 zero-active population is UNKNOWN (+ 64af00534 test stub follow-up)
  - e4505eafc   # F8 detector exit code + verdict vocabulary checked
  - 705d20058   # F9 Vocab.identity duplicate figure restored
  - 8ef861e0b   # F11 D6 classifier tested against the engine at 8edba0533 (read-only)
  - afa1d4146   # F12 R41 scope limit + ledger merge-order limit disclosed
changelog:
  - "1.1 (2026-09-27): corrections after the gate review (A_REVIEW.md F1–F12). Corrected in place: the
    'no further code change' claim (§3); D6 item 5 is PARTLY, not yes (§3); R41/R220 test coverage as it
    stands after F3 (§3); Build.exercised flips inversely, not in lockstep (§5); the tracker figures are
    now verified (§5); kala_field recounted, depth_census cost measured (§3, §7); §9's 'no proof was
    found to be false' withdrawn. New: §4 re-run, §10 corrections map, §11 L0 verdict diff vs
    7ed870775, §12 T3 re-run, §13 manifest/drift at close. Sections 0–2 are unchanged from v1.0."
  - "1.0 (2026-09-27): written from committed evidence by a report writer."
written_by: report writer from committed evidence — the builder was interrupted (machine sleep) before it could write this report; every claim below is reconstructed from the three commits, their diffs, their test files, the committed proof ledger, and independent re-runs performed by this report writer
written_on: 2026-09-27
authority: 00_ARCHITECTURE/briefs/nirmana/NIKASHA_WAVE1_EXECUTION_PROMPT_v1_0.md §2, §3, §5
---

# Nikaṣa wave 1 — Lane A packet report

## 0 — How this report was produced

The builder committed all three Lane A steps (A-1, A-2, A-3) and stopped before writing
`A_REPORT.md`. This report was written after the fact by re-reading the three commits in full
(`git show --stat` then `git show`), the two test files each commit added, the committed proof
ledger `a2_t3_proof/asset_gaps.jsonl`, and the D4/D6 rulings in `DECISIONS_RECOMMENDATIONS_v2_0.md`,
then independently re-running every proof this environment could re-run. Nothing below is
paraphrased from a builder narrative that no longer exists — it is either a direct diff/test
result or is explicitly labelled "from the commit message, not independently re-verified."

## 1 — A-1 · R216 rebase (`e2819e625`)

**Diff by file:**

- `platform/scripts/governance/asset_census.py` (+75/−10). `build_history()` now tallies rows with
  `disposition='blocked_dependency'` (migration 1095) into a new `blocked` counter, separate from
  the plain `error` tally, and records `last_disposition` alongside `last_state`. Grading logic that
  used to be inline in `measure()` is extracted into a pure `_grade_build_history(h)` function.
  Reason (stated in the diff's own comments and commit message): a cascade-blocked row — a writer
  that never ran because an upstream dependency failed in the *same run* — is a consequence of
  someone else's failure, not the asset's own defect, and was previously counted as an ordinary
  `error`, so a healthy downstream asset could grade FAIL/PARTIAL purely from upstream noise.
  `_grade_build_history` now: FAILs only when the *most recent* run failed and was not
  blocked-only; PARTIALs on any genuine (non-blocked) error/abort, or on an all-cascade history with
  **zero** completions (the "C-4 guard" — a chart that has never once actually completed a build
  must not grade PASS merely because none of its failures were "genuinely" its own); PASSes when
  there is at least one real completion and no genuine error. The blocked count is always surfaced
  in the `measured` text, never hidden (cited by the diff as the §N.6 "count it, don't hide it"
  discipline).
- `platform/scripts/governance/__tests__/test_b1_asset_census_blocked_dependency.py` (new, 185
  lines, 8 cases). Brought over unchanged from `madhav-engine 17e5a1257` per the commit message —
  reason for the file's presence is explicit: "ported verbatim... 8/8 green against the rebased
  production script."

**Proof command and actual output (re-run by this report, not just cited):**

```
$ python3 -m pytest platform/scripts/governance/__tests__/test_b1_asset_census_blocked_dependency.py -q
........                                                                 [100%]
8 passed in 0.03s
```
All 8 pass. Re-run again with the live production DB env sourced (`pgenv.sh`, read-only,
`PGPORT=5433`, confirmed `SHOW default_transaction_read_only` = `on`) as part of the combined
41-test run in §4 below — same result, unaffected by DB presence (this suite is pure-function,
no DB calls).

**Conformance:** this step ports an already-ruled, already-tested engine fix; there is no D4/D6
ruling against A-1 specifically to check. The commit's own claim ("175 diff lines, applied cleanly,
8/8 green") is independently confirmed by both stat (`75 insertions(+), 10 deletions(-)` in
`asset_census.py`, `185` new lines in the test file — the "175" in the commit message refers to the
engine-side patch line count, not this repo's diff stat, which is larger because the test file is
included) and by re-running the tests.

**Honest limits:** no production write; this step touches no database state at all (pure grading
logic). It does not itself change anything about the closure loop (that is A-2) or fault isolation
(A-3).

## 2 — A-2 · P3 closure loop (`432ed07da`)

**Diff by file:**

- `platform/scripts/governance/asset_census.py` (+135/−22, cumulative with A-1). Three changes,
  each with its stated reason:
  1. `CTRL` is now `Path(os.environ.get("NIKASHA_CONTROL_DIR", <default>))` instead of a hardcoded
     path. Reason (comment + commit message, item c): so a sandbox `--emit-gaps` run never touches
     the production ledgers.
  2. `Carr.detector` now looks for `<CTRL>/detectors/<asset>_D<1|2|3>.py` and, if found, runs it and
     adopts its verdict instead of always returning the blanket `NO_DETECTOR`. Reason (item d): a
     registered per-asset detector *is* the detector; a detector that exists but fails to run grades
     `NO_DETECTOR` with the exception text, never a pass.
  3. `emit_gaps()` is rewritten around two explicit allowlists, `CLOSABLE = (PASS, NA)` and
     `FAILING = (FAIL, PARTIAL, NO_DET)`. Reason (stated directly in the new docstring and in D4
     finding #6): the old function closed on "anything not in the failing tuple" — an implicit
     allowlist that would have closed on `NOT_GENERIC` too. The new function: opens on a first
     failing measurement; treats `IN_PROGRESS` as live alongside `OPEN`; re-opens (never
     silently re-adds) a `CLOSED` row whose check now fails again; never touches a row carrying
     `superseded_by`; and carries `change`/`owner`/`gate` forward from the prior row onto every
     `CLOSED`/`RE-OPENED` transition, falling back to census defaults only for a gap_id's very
     first `OPEN` row (there is no prior annotation to carry yet). The function's return signature
     changed from `(added, skipped)` to `(added, skipped, closed, reopened)` and `main()`'s print
     line was updated to match.
- `00_ARCHITECTURE/control/asset_elevation_tracker.py` (+14/−2). `CTRL` gains the same
  `NIKASHA_CONTROL_DIR` override (same reason as above). `scan()` now collapses `asset_gaps.jsonl`
  to one row per `gap_id` (last-wins) before counting opens, leaving gap-id-less hand rows
  untouched. Reason (comment + commit message, item b): without this collapse an appended `CLOSED`
  row is *additive* — the earlier `OPEN` row for the same identity still counts as open and the
  tracker's `ELEVATED` figure never moves.
- `platform/scripts/governance/__tests__/test_a2_emit_gaps_closure.py` (new, 284 lines, 15 cases).
  Header docstring states its own thesis directly: the sandbox port
  (`harness/asset_census_closing.py:649-679`) is not adopted unchanged because it fails four of six
  D4 acceptance cases; each test here is one of those cases run against the *fixed* production
  `emit_gaps()`, plus a `_naive_port_emit_gaps` transcription of the sandbox port's own logic used
  to independently demonstrate the four failures without depending on any file outside this repo.
- `nikasha_test/wave1/a2_t3_proof/asset_gaps.jsonl` (new, 218 lines) — the evidence ledger from the
  real T3 run; see §5 below.

**Proof commands and actual output (re-run by this report):**

```
$ python3 -m pytest platform/scripts/governance/__tests__/test_a2_emit_gaps_closure.py -q
...............                                                          [100%]
15 passed in 0.04s
```
Re-confirmed with the live DB env sourced as part of the 41-test combined run (§4) — identical
result (this suite too is pure-function against a temp-directory ledger, no DB calls).

**D4 acceptance-case conformance — each of the six cases, and whether a test covers it:**

| # | D4 acceptance case (execution prompt §3 / ruling text) | test(s) | result |
|---|---|---|---|
| 1 | CLOSED only on `PASS` or a justified `N/A` — never on `NOT_GENERIC`, `UNKNOWN`, an errored check, or an unmeasured criterion | `test_case1_not_generic_never_closes_an_open_gap`, `test_case1_not_generic_never_opens_a_gap_either` | PASS |
| 2 | `IN_PROGRESS` → CLOSED on PASS | `test_case2_in_progress_closes_on_pass` | PASS |
| 3 | a closed row re-opens on regression | `test_case3_regression_reopens_a_closed_row` | PASS |
| 4 | a superseded id is never resurrected | `test_case4_superseded_id_never_resurrected` | PASS |
| 5 | hand `change`/`owner`/`gate` carried onto every transition row | `test_case5_hand_metadata_carried_onto_closed_row`, `test_case5_hand_metadata_carried_onto_reopened_row`, `test_case5_first_open_row_uses_census_defaults` | PASS |
| 6 | `emit_gaps` twice on an unchanged target appends nothing | `test_case6_rerun_unchanged_failing_target_appends_nothing`, `test_case6_rerun_unchanged_passing_target_appends_nothing` | PASS |

Two additional tests in the same file corroborate the fix was necessary, not cosmetic:
`test_full_loop_open_closed_reopened_closed` (an in-process OPEN→CLOSED→RE-OPENED→CLOSED replay —
the same shape as the committed T3 evidence in §5) and four `test_naive_port_fails_case{1,2,4,5}_*`
tests that run `_naive_port_emit_gaps` (the sandbox port's actual logic) against the identical
scenarios and assert it produces the *wrong* result — independently confirming the commit message's
claim that "the sandbox port itself fails 4 of 6 acceptance cases." Re-run, all four still fail
under the naive port and pass under the fixed one, matching the commit's characterization exactly.

**Honest limits (stated by the commit itself, verified against the diff — nothing extra found):**
"Deliberately NOT ported (out of A-2's named scope, register R57's 'three changes'): idem_scan's
seeder-following enhancement and the data/writer-run fixes (F1/F3/F4/F5/F6 in the original T3
campaign)." Confirmed: neither `idem_scan` nor any F1–F6 logic appears in the diff. The commit
states this has "a consequence... for the tracker's ELEVATED figure" but does not spell the
consequence out inline in the diff; no further detail was found in the commit, the proof ledger, or
STATE.md, so this report can only carry the limitation forward as stated, not quantify it.

## 3 — A-3 · P4 precursors (`7ed870775`)

**Diff by file:**

- `platform/scripts/governance/asset_census.py` (+233/−35, cumulative). Four independent changes:
  1. **R41 fault isolation.** A new `ERRORED` verdict. Every per-asset check that previously ran
     unguarded inside `measure()` (`contract_scan`, `idem_scan`, the four target-table checks:
     `depth_census`, the `Vocab.identity` duplicate probe, `alias_census`, `Ldgr.source_presence`)
     is now individually wrapped in `try/except Unknown`, degrading only that criterion to
     `ERRORED` — placed in neither `FAILING` nor `CLOSABLE`, so a broken detector can neither open
     nor close a gap. Reason (comment + commit message): a single slow/failing query used to
     propagate an `Unknown` out of `measure()` and abort the entire layer census (exit 4).
  2. **R40 timeout + scale.** `PSQL_TIMEOUT_SECONDS` is now
     `int(os.environ.get("NIKASHA_CENSUS_TIMEOUT_SECONDS", "180"))` instead of a bare `180`. The
     `Vocab.identity` duplicate check is rewritten from `count(*) - count(DISTINCT (cols))` (a full
     sort/hash materializing both counts) to `SELECT EXISTS(SELECT 1 FROM {tbl} GROUP BY {kd} HAVING
     count(*) > 1)` (can stop at the first violation). Reason: the old form does not scale to the
     estate's largest table.
  3. **R220 population.** New `registry()` return shape `tuple[dict[str, dict], dict]` — the second
     element is a `population` dict (`registry_total`, `active`, `excluded_inactive`). The active
     filter changes from `is_active AND NOT dead_flag` to `is_active AND NOT coalesce(dead_flag,
     false)`. Reason (comment, verified independently below): `dead_flag` is NULL, not false, on
     every row, so the un-coalesced form is a SQL NULL trap that matches zero rows, not the intended
     127. `measure()`'s output and `main()`'s print both now state `population_active` /
     `population_registry_total` / `population_excluded_inactive` explicitly.
  4. **D6 rate grading.** New `duration_instrument_present()` (feature-detects
     `asset_throughput.duration_seconds` via `information_schema.columns`, returning `None` —
     distinct from `False` — if the check itself can't run) and a new pure `_grade_earn_cost(attempt,
     instrument_present, baseline)` replacing the old inline "rows_per_second populated ⇒ PASS"
     check. `measure()` calls it once per layer run with `instrument_present` from the feature
     detector and `attempt=None, baseline=None` (see honest limits below).
- `platform/scripts/governance/__tests__/test_a3_earn_cost_grading.py` (new, 11 cases).
- `platform/scripts/governance/__tests__/test_a3_fault_isolation_and_population.py` (new, includes
  a `pytest.mark.skipif(not _db_reachable(), ...)`-guarded live end-to-end test).

**Proof commands and actual output — re-run independently by this report, not merely cited:**

```
$ python3 -m pytest platform/scripts/governance/__tests__/test_a3_earn_cost_grading.py \
    platform/scripts/governance/__tests__/test_a3_fault_isolation_and_population.py -q
.............s....                                                       [100%]
17 passed, 1 skipped in 0.06s
```
Without a live DB, one test is skipped
(`test_live_e2e_one_simulated_query_timeout_degrades_not_aborts`, `skipif(not _db_reachable())`).
Re-run **with** `pgenv.sh` sourced (read-only production, `PGPORT=5433`, verified
`default_transaction_read_only = on`):

```
$ python3 -m pytest platform/scripts/governance/__tests__/test_b1_asset_census_blocked_dependency.py \
    platform/scripts/governance/__tests__/test_a2_emit_gaps_closure.py \
    platform/scripts/governance/__tests__/test_a3_earn_cost_grading.py \
    platform/scripts/governance/__tests__/test_a3_fault_isolation_and_population.py -v
...
======================== 41 passed in 63.91s (0:01:03) =========================
```
All 41 tests across all four Lane A test files pass, **including** the live e2e test against
production this time (`test_live_e2e_one_simulated_query_timeout_degrades_not_aborts` — PASSED).

**Independent live re-runs beyond the test suite (this report's own DB queries, all read-only):**

1. `SHOW default_transaction_read_only` → `on` (confirmed before any other query).
2. Re-ran the fixed R40 duplicate-check form directly against production `kala_field`:
   ```
   $ time psql -tAc "SELECT EXISTS(SELECT 1 FROM kala_field GROUP BY chart_id,event_class,segment_index HAVING count(*) > 1)"
   f
   real 0m8.468s
   ```
   Matches the commit's claimed "8.2s / 0 duplicates" (this report measured 8.468s; same order,
   same result).
3. Re-ran the **old**, pre-fix form for comparison:
   ```
   $ time psql -tAc "SELECT (count(*) - count(DISTINCT (chart_id,event_class,segment_index)))::text FROM kala_field"
   0
   real 0m46.755s
   ```
   Matches the commit's claimed "46.3s / 0 duplicates" almost exactly (46.755s measured here). Both
   forms agree on the answer (0 duplicates); only the cost differs — independently confirms the
   ~5.6x speedup the commit claims.
4. Re-ran a full `--layer L3` census against production (read-only, no `--emit-gaps`):
   ```
   $ time python3 platform/scripts/governance/asset_census.py --layer L3 --out <scratch>.json
   L3 Kala (contribution): 21 assets · 11 registered ids vs 21 has_writer=true
     population: 21 active of 23 registry rows for this layer — excluded (inactive/dead): ka_gochara_sweep, ka_gochara_v3_century_materialize
     ...
     FAIL 38 · PARTIAL/NO_DETECTOR 91 · ERRORED 0 · assets measured 21
   real 1m38.955s
   ```
   Independently confirms, live: **21/23 active population with the exact two excluded ids named in
   the commit** (`ka_gochara_sweep`, `ka_gochara_v3_century_materialize` — R220), **0 ERRORED**
   criteria (R41 — no layer-abort, no silent detector failure), and a completion time of ~99s. This
   is somewhat longer than the commit's claimed 89s (different moment, different cache/load state on
   the shared production DB — not a discrepancy this report can resolve further), but both are two
   orders of magnitude below the commit's stated pre-fix failure mode (28m52s before the connection
   dropped, census never completing, exit 4/UNKNOWN).

**D6 items 1–5 conformance — each item, and whether the code and a test cover it:**

| item | D6 ruling text | code | test(s) | covered? |
|---|---|---|---|---|
| 1 | Feature-detects the instrument; absent/unreachable → `NO_DETECTOR`, scoped, never `PARTIAL` | `duration_instrument_present()`; `_grade_earn_cost`'s `reason` branch | `test_case_absent_column_grades_no_detector_never_partial`, `test_case_instrument_unreachable_is_a_distinct_reason` | yes |
| 2 | Attributes timing to an attempt — measurement identity is `(asset, chart scope, latest build_run_assets attempt)`, not `duration + last_built_at` alone | `_grade_earn_cost(attempt, ...)`'s parameter shape and docstring specify the identity | **not wired (v1.1 correction).** `measure()` passes `attempt=None` unconditionally. v1.0 repeated the A-3 commit's claim that grading would begin "with migration 1094, with no further code change" — **that was false** (A_REVIEW F1): once the column exists, `attempt=None` graded `N/A "never attempted"`, which is closable, and would have closed all 40 open L0 `Earn.build_record` gaps. Since `a77d50005` the call site passes `attempt_linkage_wired=False` and reads `NO_DETECTOR — attempt linkage not wired`. Real grading needs the attempt query (R42–R56, a separate lane) as well as migration 1094. No census code reads a real `build_run_assets` attempt today. |
| 3 | Grades `Earn.build_record` by cause (finite duration incl. zero-row → PASS; healthy non-execution/no-writer service → N/A; legacy `_telemetry` completion-no-duration → FAIL; failed/aborted before completion → N/A; unclassified NULL → NO_DETECTOR, never PASS) | `_grade_earn_cost`'s five-branch cause classifier | `test_case_zero_rows_with_finite_duration_grades_pass_with_rate_zero`, `test_case_skip_no_delta_grades_na_and_preserves_prior_baseline`, `test_case_probe_green_grades_na`, `test_case_legacy_health_probe_service_no_writer_grades_na`, `test_case_legacy_telemetry_path_grades_fail`, `test_case_failure_before_completion_grades_earn_na_cost_by_prior_baseline`, `test_case_unclassified_null_grades_no_detector_never_pass`, `test_case_never_attempted_grades_na` | yes, all five named branches covered |
| 4 | Grades `Cost.baseline` against the most recent sanctioned (measured) completion, independent of the latest attempt's outcome; no measured completion ever → `FAIL — no sanctioned baseline build` | `_grade_earn_cost`'s `cost = ...` branch | `test_case_failure_does_not_erase_a_prior_cost_baseline` (plus the cost side of several of the item-3 tests, which assert `Cost.baseline` alongside `Earn.build_record`) | yes |
| 5 | Tested before adoption against the engine implementation: failure, zero rows, skip after a prior timing, probe-green, the legacy `ga_*` path, the absent column, an unknown NULL (seven named scenarios) | n/a (a testing obligation, not a code branch) | 11 tests total in `test_a3_earn_cost_grading.py`; the seven named scenarios each have a directly-named test (absent column → `test_case_absent_column_grades_no_detector_never_partial`; zero rows → `test_case_zero_rows_with_finite_duration_grades_pass_with_rate_zero`; skip-after-prior-timing → `test_case_skip_no_delta_grades_na_and_preserves_prior_baseline`; probe-green → `test_case_probe_green_grades_na`; unknown NULL → `test_case_unclassified_null_grades_no_detector_never_pass`; failure → `test_case_failure_before_completion_grades_earn_na_cost_by_prior_baseline`); plus two tests beyond the seven (`test_case_instrument_unreachable_is_a_distinct_reason`, `test_case_never_attempted_grades_na`), matching the commit's own count ("11 tests cover the seven named scenarios... plus instrument-unreachable and never-attempted"). One honest caveat: the ruling's phrase "the legacy `ga_*` path" does not map unambiguously onto a single test name — this report identifies `test_case_legacy_health_probe_service_no_writer_grades_na` and `test_case_legacy_telemetry_path_grades_fail` as the two candidates (a no-writer health-probe service and the pre-1094 `_telemetry` completion-with-no-duration path, respectively) but the commit does not state which one the ruling's exact wording refers to, so this report does not force a single mapping it cannot verify | **PARTLY (v1.1 correction; v1.0 said "yes").** The 11 tests above use hand-built dicts only, which does not meet "against the engine implementation" (A_REVIEW F11). Since `8ef861e0b`, `test_a4_d6_engine_conformance.py` reads the engine at `8edba0533` read-only and covers all seven scenarios: it pins what each engine path writes and grades the attempt that path produces, with the engine's `_compute_duration_and_rate` executed from its own source. It passes 13/13 at `8edba0533` and at engine HEAD `e5dd65b8f`. It found one census defect: the census column probe was not schema-qualified and the engine's is. That is fixed. It also found one adapter obligation: the engine never writes a `probe_green` disposition. **Not met:** running the engine's write paths against a database that carries migration 1094 and grading the real rows. That needs a migration applied and builds run, both outside this wave, and a census attempt query, which is R42–R56 and unwired. See §10 F11. |

R41/R220 test coverage. **v1.1 correction:** v1.0 listed seven tests as coverage and said "All
PASS". Four of the seven could not fail: they grepped source text, or tested helpers defined inside
the test file (A_REVIEW F3; mutations M8 and M9 survived them). This is the coverage after
`cf955e3a3` (F3) and this pass:

- **R41 `Build.contract` / `Idem.pattern`.** Behavioural.
  `test_contract_scan_exception_degrades_to_errored_not_layer_abort` and
  `test_idem_scan_exception_degrades_to_errored_not_layer_abort` call the extracted
  `_measure_contract` / `_measure_idem` with the scan raising, and assert that the result is ERRORED.
  M8 (the guard re-raises) now fails them offline.
- **R41 per-asset target-table checks.** Behavioural, live only.
  - `test_live_e2e_depth_census_failure_does_not_blind_identity_for_the_same_asset` runs
    `measure("L0")` twice.
  - `test_live_e2e_one_simulated_query_timeout_degrades_not_aborts` runs `measure("L1")`.
  - `test_errored_never_closes_a_gap_and_never_opens_one` is behavioural and offline.
- **Structural backstops, which cannot fail on behaviour and are not claimed as proof.**
  `test_measure_calls_the_extracted_guarded_helpers` and
  `test_depth_census_timeout_does_not_block_vocab_or_ldgr_checks_from_running` both grep `measure()`.
- **R220 census population.**
  - `test_live_registry_l3_excludes_the_two_retired_rows` is behavioural and live: it runs the real
    `registry("L3")` and expects 21 of 23 with the two ids named.
  - **M9, which reverts the census filter to `is_active AND NOT dead_flag`, still survives the whole
    offline suite** (re-run this pass: 71 passed, 4 skipped under M9). No offline test executes the
    census's `registry()` SQL.
  - Live, M9 fails that test. Since F7 it also makes the census exit 4 with "zero active bg_* rows
    in asset_registry (40 registry row(s) for this prefix)", where before it exited 0 on nothing.
  - `test_population_filter_null_trap_illustration` is illustrative only and relabelled as such.
  - `test_registry_returns_population_tuple_shape` and
    `test_measure_states_the_population_never_silently_drops_it` are structural (source text).
- **R220 tracker population (F6).** `test_f6_tracker_counts_only_the_active_population_and_states_it`
  runs the tracker's real SQL on SQLite and catches the NULL trap offline.

**Honest limits:**

- D6 item 2 (attempt-linked provenance) is specified in the function signature and docstring but
  not wired: `measure()` passes `attempt=None` unconditionally. **v1.1 correction:** v1.0 repeated
  the commit's "lands... with no further code change" once migration 1094 is applied. That was false
  (A_REVIEW F1). With the column present, the unwired call graded a closable `N/A "never attempted"`
  for every asset. Since `a77d50005` it reads `NO_DETECTOR — attempt linkage not wired`. Real grading
  needs both migration 1094 and the attempt query (R42–R56). Today the instrument is absent, so both
  measurements read `NO_DETECTOR — instrument absent (migration 1094), scoped to this run`. This was
  re-measured this pass on all 40 L0 assets: 80/80 rows.
- **Out-of-scope finding registered by the commit itself, not fixed:** `depth_census` makes
  per-column `count(c)` passes over `kala_field`.
  - **Row count, recounted exactly this pass (v1.1):** `SELECT count(*) FROM kala_field` =
    **10,982,957** (12.1 s). That matches the A-3 commit's figure. The planner estimate
    (`pg_class.reltuples`) is 10,280,842. The "10.9M" above is the exact count; "10.3M" in the code
    comments is the estimate.
  - **Cost, measured in isolation this pass (v1.1):**
    `depth_census("kala_field", <23 columns>)` took **24.3 s**. That is two full scans: `count(*)`,
    then one pass of 23 `count(c)`. It found one never-populated column, `refinement_residual`.
  - This is well under the 180 s default timeout. It is still a real cost and a candidate for the
    same R40 treatment. Not fixed; out of scope.
- A-4 (below) is the explicit stop point; R42–R56 were not started.

## 4 — Combined test run (all four Lane A test files, live DB)

> **v1.1:** the run below is v1.0's run of 41 tests. After the corrections the Lane A suite has six
> files and 75 tests. Re-run live this pass: **75 passed, 0 skipped**. Details in §10.

```
$ source .../pgenv.sh   # PGPORT=5433, read-only confirmed
$ python3 -m pytest \
    platform/scripts/governance/__tests__/test_b1_asset_census_blocked_dependency.py \
    platform/scripts/governance/__tests__/test_a2_emit_gaps_closure.py \
    platform/scripts/governance/__tests__/test_a3_earn_cost_grading.py \
    platform/scripts/governance/__tests__/test_a3_fault_isolation_and_population.py -v
41 items collected
======================== 41 passed in 63.91s (0:01:03) =========================
```
No failures, no errors, no skips (the one DB-gated test ran and passed with the live connection).

## 5 — The T3 closure-loop proof (`a2_t3_proof/asset_gaps.jsonl`)

The committed ledger is at
`00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave1/a2_t3_proof/asset_gaps.jsonl` — note this is
**not** the path implied by a literal reading of the execution prompt's `nikasha_test/wave1/...`
(there is no `nikasha_test/` at the repo root in this checkout); the actual location, confirmed by
`git show 432ed07da --stat` and `git ls-tree`, is under `00_ARCHITECTURE/briefs/nirmana/`. 218 lines,
matching the commit's stat (`218 ++++++++++`) exactly.

Every line for `gap_id = bg_nakshatra_medical-Build.registered` (grep'd from the full file, read in
full — the file is small enough at 218 lines to read entirely):

| line | ts | state | what |
|---|---|---|---|
| 99 | 04:23:22 | OPEN | "measured: @register in bg_medical_mappings.py but registry says has_writer=false" |
| 213 | 04:23:36 | CLOSED | "CLOSED by measurement: @register in bg_medical_mappings.py; registry agrees" |
| 215 | 04:23:52 | OPEN | "RE-OPENED by measurement: @register in bg_medical_mappings.py but registry says has_writer=false" |
| 217 | 04:24:06 | CLOSED | "CLOSED by measurement: @register in bg_medical_mappings.py; registry agrees" |

This is **exactly** the OPEN → CLOSED → RE-OPENED → CLOSED cycle the commit and the execution
prompt both require, on one row, driven by real `has_writer` flips and real census runs against the
`nikasha_sandbox` DB (not a fixture) — timestamps are 14–36 seconds apart, consistent with the
commit's description of a live, sequential A/B run. A companion gap_id
(`bg_nakshatra_medical-Build.exercised`, lines 214/216/218) moves with the same `has_writer` toggles.
**v1.1 correction:** it moves **inversely**, not "in lockstep" as v1.0 said. Line 214 is its first
OPEN, when `has_writer` became true and an asset with a writer has never been run. Line 216 is
CLOSED, back to "no writer, never run" = N/A. Line 218 is RE-OPENED. So each toggle closes one of the
two gap rows and opens the other. Both rows read the same registry field, so this is expected and is
not a defect. It does explain why the asset's total `gaps_open` stays flat through the cycle (§12).

**Not independently re-run:** this report did not re-execute the sandbox toggle sequence against the
`nikasha_sandbox` DB (the `.sandbox/` Postgres instance is still running at
`00_ARCHITECTURE/briefs/nirmana/nikasha_test/.sandbox/pgdata`, confirmed via `ps aux`, but replaying
the exact toggle sequence risks disturbing that sandbox's state without a clear net gain over the
committed ledger, which already shows the full cycle unambiguously). The `test_full_loop_open_closed_reopened_closed`
unit test (§2 above, re-run and PASSING) exercises the identical logic in-process against a
disposable temp ledger, which this report treats as sufficient corroboration of the mechanism
without touching the sandbox.

**v1.1:** the paragraph below is superseded. The tracker figures 9/12 → 6/7 were **VERIFIED** by
the gate reviewer with both real trackers (A_REVIEW §2 item 1). This pass re-ran the tracker after
every step of a live T3 cycle (§12). The v1.0 text is kept for the record.

The tracker-side "0 → 1 → 0 → 1" claim (execution prompt §3) is **cited from the commit message
only, not independently re-verified**: the commit states "the pre-A2 tracker (no last-wins) reports
gaps_open=9/12 for that asset; the fixed tracker correctly collapses to 6/7" as the A/B comparison,
which is a different (and more informative) number pair than the prompt's shorthand "0→1→0→1" for
the *elevation* count specifically. This report could not locate a raw tracker-output artifact
(only the `asset_gaps.jsonl` ledger was committed, not a tracker JSON snapshot at each of the four
points in time), so the tracker-side collapse is reported as a commit-message claim, labelled as
such, not as independently confirmed.

## 6 — A-4 · stopping honestly

R42–R56 (completion/registration/latest-row work) were **not started**, exactly as A-3's commit
message states ("A-4: stopping here... not started"). No trace of any R42–R56 work exists in any of
the three commits' diffs or in the working tree's Lane-A-owned files.

**The "background timing comparison job":** this report searched the three commits' full diffs, the
committed proof directory, `STATE.md`, `EVENTS.jsonl`, and the wider repository for any reference to
a background timing-comparison job and found **none** attributable to Lane A or this wave. The only
related text found is a **pre-existing, unrelated** `EVENTS.jsonl` entry from an earlier phase-2
event ("Ground truth for kala_field being computed manually in background"), timestamped
2026-09-26T12:06:38Z — before wave 1 was launched — describing a different, already-closed defect
discovery (R34/R35), not a job Lane A started. The R40 old-vs-new timing comparison itself (46.3s vs
8.2s) is a **completed, one-shot measurement recorded in the A-3 commit message**, not a running or
background job. `ps aux` shows no Python process, cron entry, or `nohup`/background shell job
belonging to this wave; the only running background process found is the `nikasha_sandbox` Postgres
instance itself (§5), which is idle infrastructure, not a job. **Conclusion: unknown / not found.**
If the builder meant something not captured in any committed artifact, that intent did not survive
the interruption.

## 7 — Findings outside scope

1. `depth_census`'s per-column `count(c)` cost over `kala_field` is unfixed. The A-3 commit
   registered it as a candidate for a later R40-style pass (§3, honest limits). **v1.1:** measured at
   24.3 s over the exact 10,982,957 rows.
2. A-2's non-port of `idem_scan`'s seeder-following enhancement and the F1/F3/F4/F5/F6 data/writer-run
   fixes has a stated-but-unquantified consequence for the tracker's `ELEVATED` figure (§2, honest
   limits) — this report could not find a quantification of that consequence anywhere in the
   committed evidence and does not invent one.
3. No other findings outside Lane A's named scope were found in the diffs or test files.

## 8 — CAPABILITY_MANIFEST.json / fingerprint / drift

**Files changed by the three commits:** `platform/scripts/governance/asset_census.py`,
`00_ARCHITECTURE/control/asset_elevation_tracker.py`, four new test files under
`platform/scripts/governance/__tests__/`, and the new proof ledger
`.../wave1/a2_t3_proof/asset_gaps.jsonl`.

**Manifest registration check:** searched `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (both a direct
grep and a full recursive walk of every string value in the JSON) for `asset_census.py` and
`asset_elevation_tracker.py` — **neither file, nor any of the new test/proof files, is registered in
the manifest.** No fingerprint rotation is applicable to any file this lane touched.

**`manifest_fingerprint.py --check`:**
```
entries: 141 (declared 141)
fingerprint declared: f484f581767ad641
fingerprint observed: f484f581767ad641
MATCH
```
Clean MATCH — expected, since Lane A touched no manifest-registered file.

**`drift_detector.py` (run with `pgenv.sh` sourced, read-only production, under `timeout 600`):**
```
drift_detector: 1 findings; exit=3
  JSON: 00_ARCHITECTURE/drift_reports/DRIFT_REPORT_adhoc_20260927T060545Z.json
  MD:   00_ARCHITECTURE/drift_reports/DRIFT_REPORT_adhoc_20260927T060545Z.md
```
Exit 3 (medium/low findings only — within the "exit 0 or 3 only" bound the execution prompt
requires). The one LOW finding is **`a3_category_not_yet_populated`** — 73 `CHART_FACTS_SCHEMA.json`
categories not yet written by any L1 writer (pre-existing, chart-facts-schema-vs-DB drift,
unrelated to Lane A's asset-census/tracker changes; the finding names `chart_facts` and
`CHART_FACTS_SCHEMA.json`, neither of which either lane touched). The generated report file lives
under `00_ARCHITECTURE/drift_reports/`, which is gitignored (`.gitignore:32`) — it was not committed
and required no cleanup.

## 9 — Summary

| step | claim | independently re-run? | result |
|---|---|---|---|
| A-1 | 8/8 B1 tests green | yes | 8/8 PASS |
| A-2 | 15/15 D4-acceptance tests green; real T3 cycle in the ledger | yes (tests); ledger read in full, not replayed | 15/15 PASS; OPEN→CLOSED→RE-OPENED→CLOSED confirmed in the committed ledger |
| A-3 | 11+7=18 tests green; R40 5.6x speedup; R220 21/23 population; R41 0 ERRORED; L3 completes in ~89s vs pre-fix abort | yes, all | 18/18 PASS incl. the live-DB e2e test; R40 speedup independently reproduced (46.755s → 8.468s, same 0-duplicate answer); R220 population independently reproduced exactly (21/23, same two excluded ids); R41 independently reproduced (0 ERRORED in a live `--layer L3` run); L3 completed in 98.955s live (same order of magnitude as claimed, not identical) |
| combined | 41 tests, all four files, live DB | yes | 41/41 PASS |
| manifest/fingerprint | no registered file touched | yes | confirmed absent from manifest; `--check` MATCH |
| drift | exit 0 or 3 only | yes | exit 3, 1 pre-existing unrelated LOW finding |

**v1.1 correction:** the next sentence is withdrawn. The gate review found claims in the three
commits and in this report that were false: "no further code change" (F1), the N/A closure on an
errored `count_sql` (F2), tests that could not fail (F3), the WITHDRAWN re-open (F4), D6 item 5 =
"yes" (F11), and "lockstep" (§5). §10 maps each one to its correction. v1.0 text follows:

No proof claimed in the three commits was found to be false. Two items could not be independently
re-verified beyond what the commit states (the tracker's exact `gaps_open` A/B numbers in §5, and the
`depth_census` cost characterization in §3/§7) and are labelled as commit-message claims, not
independent confirmations. R42–R56 remain untouched, and the "background timing comparison job" the
builder's last words referenced could not be found anywhere in the committed evidence.

## 10 — Corrections after gate review (v1.1)

The gate (`A_REVIEW.md`, commit `8a57a3320`) rejected v1.0 on a narrow basis. Each finding maps to
the table row below. F1–F5 were committed by the previous builder. F6–F9, F11 and F12 were committed
in this pass. Every mutation was applied to the working file, the suite was run, and the file was
restored (`git diff` empty after each run).

| # | finding | commit | test(s) that fail without the fix | mutation evidence |
|---|---|---|---|---|
| F1 | unwired D6 attempt path read closable `N/A "never attempted"` once 1094 lands | `a77d50005` | `test_case_instrument_present_attempt_linkage_unwired_grades_no_detector_not_na`, `test_case_attempt_linkage_unwired_is_the_default_measure_call_shape`, `test_emit_gaps_does_not_close_on_the_unwired_no_detector` | guard reverted → 2 failed (grading + emit_gaps closure) |
| F2 | errored `count_sql` → `N/A "no count_sql"` → gap CLOSED | `065e620b2` | `test_live_counts_distinguishes_errored_query_from_no_count_sql` (offline), `test_live_e2e_a_broken_count_sql_grades_errored_not_na` (live) | `errored[aid]` line removed → offline test fails |
| F3 | proofs that could not fail (M8, M9 survived) | `cf955e3a3` | `_measure_contract` / `_measure_idem` behavioural tests; `test_live_e2e_depth_census_failure_…`; `test_live_registry_l3_excludes_the_two_retired_rows` | M8 → offline failure (uncaught `Unknown`). **M9 still survives offline**, re-run this pass: 71 passed, 4 skipped under M9. It is caught live only: the L3 registry test fails, and the CLI exits 4 via F7. |
| F4 | WITHDRAWN re-opened, contrary to the code's comment | `3a9c66cf9` | `test_case_withdrawn_is_terminal_never_reopened` | bare `else: reopen` → (0,0,1) instead of (0,0,0) |
| F5 | `superseded_by` read from the latest row only | `cbc8b6724` | `test_case4b_superseded_survives_a_later_row_that_omits_the_flag` | latest-row check → (0,0,1,0) instead of (0,0,0,0) |
| F6 | tracker counted 129/23, not the 127/21 active | `6574d729b` | `test_f6_tracker_counts_only_the_active_population_and_states_it` (tracker's real SQL on SQLite) | `NOT dead_flag` → 1 row; no filter → 4 rows; pre-fix tracker → shape error |
| F7 | zero-active population exited 0 silently | `0c16969a3`, `64af00534` | `test_f7_registry_raises_unknown_on_zero_active_rows`, `test_f7_main_exits_4_with_a_message_on_zero_active_rows` | old guard → "DID NOT RAISE"; main prints "0 assets … assets measured 0" and does not return 4 |
| F8 | detector return code / verdict vocabulary unchecked | `e4505eafc` | `test_f8_a_detector_that_crashes_after_printing_pass_is_not_a_pass`, `test_f8_a_verdict_outside_the_closed_set_is_not_adopted` (+ positive control) | rc check off → PASS adopted; vocab check off → `'GREEN'` adopted |
| F9 | `Vocab.identity` lost its duplicate figure | `705d20058` | `test_f9_identity_fail_states_the_duplicate_count`, `test_f9_identity_pass_states_zero_and_never_runs_the_count`, `test_f9_a_count_that_errors_keeps_the_probe_fail` | pre-fix → 3 fail; inner guard off → 1 fail; count always run → 1 fail |
| F10 | report overstated | this file, v1.1 | — | corrected in place: §3 (no-further-code-change, D6 item 5, R41/R220 coverage, kala_field, depth_census), §5 (inverse, tracker), §7, §9 |
| F11 | D6 item 5 not tested against the engine | `8ef861e0b` | `test_a4_d6_engine_conformance.py`, 13 tests (see below) | 6 census mutations, all caught (see below) |
| F12 | R41 scope limit (and ledger merge order) undisclosed | `afa1d4146` | `test_f12_a_failed_layer_wide_read_names_itself_and_the_r41_limit` | pre-fix → fails; read name dropped → fails |

**F11 in detail.** The test suite reads `/Users/Dev/madhav-engine` at `8edba0533` read-only, using
`git show`. Nothing is imported, run against a database, or written.

The seven scenarios:

| scenario | engine fact pinned | census grade asserted |
|---|---|---|
| absent column | `_duration_columns_present` probes `public.asset_throughput.duration_seconds`, the column 1094 adds | the census probe is now identical (it lacked `table_schema`; fixed) |
| zero rows | `_compute_duration_and_rate(0, 2.5)` = (2.5, 0.0), executed from engine source | PASS, rate 0.0 |
| unknown NULL | six durations the engine refuses | NO_DETECTOR, never PASS |
| completion write | only `_run_data_writer` writes `duration_seconds`, and it marks `disposition='build'` | (the adapter contract) |
| skip after prior timing | the skip path leaves the prior duration in place | N/A, prior baseline kept |
| failure | the error path never touches duration or disposition | N/A, not a timing defect |
| probe-green | the engine writes `state='complete'` with **no disposition** | N/A given an adapter-derived `probe_green` |
| legacy `ga_*` | `_telemetry.update_asset_throughput` defaults `duration_seconds=None` and upserts it | FAIL |

- **Runs:** 13/13 at `8edba0533`. 13/13 at engine HEAD `e5dd65b8f`, where `asset_runner.py` is
  identical. With the checkout absent, all tests skip and state the reason.
- **Mutations** (each caught): the probe without `table_schema`; zero-row not PASS; unknown NULL →
  PASS (6/6 caught); duration checked before disposition; `reached_completion_write` ignored; the
  legacy branch removed.
- **Findings for the R42–R56 adapter:**
  - The engine never writes a `probe_green` disposition. The adapter must derive it from complete +
    NULL disposition + probe receipt.
  - `reached_completion_write` is `disposition = 'build'`.
- **Still not testable here:** running the engine's write paths against a database carrying migration
  1094 and grading the real rows. Two reasons:
  - It needs migration 1094 applied and builds run, and this wave allows no migration and no
    production write.
  - The census has no attempt query to read such rows (F1: unwired).
- **D6 item 5 verdict: PARTLY met.**

**Scope incident, disclosed rather than repaired.** The F5 commit `cbc8b6724` also swept in Lane B's
then-uncommitted working-tree edits:
- `catalog_provenance.py` and its test;
- `provenance/BUILD_DEPENDENCIES_READER_SCAN.md`, `CLOSURE_REPORT.md` and
  `producer_provenance.derived.json`.

These are 7 files in total, 5 of them Lane B's. The content is Lane B's work, not Lane A's. The
commit's own message does not mention it. History was not rewritten, because Lane B has committed on
top since. Every commit in this pass uses `git commit -- <explicit paths>` (only-mode), which commits
nothing else staged in the shared index.

**Test count.** At the start of this pass the Lane A suite had 52 tests: offline 48 passed, 4 skipped
(the 4 are live-only). After this pass it has **75**: 10 new in `test_a4_gate_corrections.py`, 13 new
in `test_a4_d6_engine_conformance.py`.

- **Offline:** 71 passed, 4 skipped.
- **Live** (read-only production, `default_transaction_read_only = on`): **75 passed, 0 skipped**
  (232.9 s).
- **First live attempt:** 74 passed, 1 failed. The failing test was
  `test_live_e2e_one_simulated_query_timeout_degrades_not_aborts`, and the cause was
  `server closed the connection unexpectedly` inside the layer-wide `build_history` read. That is the
  R41 limit F12 discloses, showing up live on a transient connection drop. It is not a code defect.
  The DB was re-checked and the whole suite re-run green.

## 11 — L0 census at HEAD vs `7ed870775` (live, read-only)

Both runs were made against production on the same code inputs. Base is the `7ed870775`
`asset_census.py` run from scratch. HEAD includes F1–F12.

| | base `7ed870775` | HEAD |
|---|---|---|
| runtime / exit | 63 s / 2 | 57 s / 2 |
| assets | 40 | 40 (same set) |
| FAIL · PARTIAL/NO_DETECTOR · ERRORED | 39 · 170 · 0 | 39 · 170 · 0 |
| verdict tally | PASS 413 · PARTIAL 50 · NO_DETECTOR 120 · FAIL 39 · NOT_GENERIC 80 · N/A 68 | identical |

**Verdict flips: none.** The per-asset, per-criterion diff shows zero verdict changes. Why each
correction leaves L0 unchanged today:

- **F1:** the instrument is absent, so the unwired branch is unreachable. Earn and Cost read
  `instrument absent (migration 1094)` on 80/80 rows in both runs.
- **F2:** no L0 `count_sql` errors. `Build.completion` has 0 ERRORED.
- **F7:** the population is 40 of 40 active.
- **F8:** no detector file is registered.
- **F11:** the probe answers "absent" whether or not it is schema-qualified.
- **F12:** the only change is the message on failure.

**Text-only change:** `Vocab.identity` on 37 assets, from "no duplicates" to "0 duplicate(s)" (F9).
That is the pre-R40 wording, restored. None of the 37 has duplicates, so the count query never runs
on L0. It was checked separately against production (`brahma_class_priors`) and returns `0, 0`.

**The base figure.** The gate measured L0 FAIL **119 → 39** from `9981b8f5d` to `7ed870775`.
The A-3 commit's "~122" was the base figure at its own measurement time.

**The 80 fewer FAILs** are `Earn.build_record` and `Cost.baseline`, 40 each. Both moved FAIL →
NO_DETECTOR because the instrument is absent (A_REVIEW §4). That is unchanged by this pass.

## 12 — T3 closure cycle, re-run against a ledger copy (live, read-only)

Setup:
- The production `measure("L0")` and `emit_gaps()` ran against read-only production.
- `NIKASHA_CONTROL_DIR` pointed at a scratch copy of both production ledgers.
- `bg_nakshatra_medical.has_writer` was flipped **in memory only**; its production value is `false`.
- The HEAD tracker (with F6) was read after every step.
- Target row: `bg_nakshatra_medical-Build.registered`.

| step | has_writer | emit (added, skipped, closed, reopened) | ledger lines | target row (line, state) | tracker gaps_open/total for the asset |
|---|---|---|---|---|---|
| 0 | — | — | 263 | 137 OPEN | 6 / 6 |
| 1 | false | (0, 209, 0, 0) | 263 | 137 OPEN | 6 / 6 |
| 2 | true | (1, 208, 1, 0) | 265 | 264 **CLOSED** | 6 / 7 |
| 3 | false | (0, 208, 1, 1) | 267 | 266 **OPEN** (RE-OPENED) | 6 / 7 |
| 4 | true | (0, 208, 1, 1) | 269 | 268 **CLOSED** | 6 / 7 |
| idempotency | true again | (0, 209, 0, 0) | 269 → 269 | — | — |

- The target row cycles OPEN → CLOSED → RE-OPENED → CLOSED. Its closed state reads 0 → 1 → 0 → 1.
- The asset's `gaps_open` stays at 6 because `Build.exercised` moves inversely (§5): each toggle closes
  one of the two rows and opens the other.
- Production `asset_gaps.jsonl` / `asset_certs.jsonl` are byte-identical before and after (md5
  compared). `git status` shows them clean.

## 13 — Manifest, fingerprint, drift at close (this pass)

- **Registration:** none of `asset_census.py`, `asset_elevation_tracker.py` or the new test files is
  registered in `CAPABILITY_MANIFEST.json` (grep count 0). No fingerprint rotation applies.
- **`manifest_fingerprint.py --check`:** entries 141 (declared 141), fingerprint `f484f581767ad641`,
  **MATCH**.
- **`drift_detector.py`** (pgenv.sh, read-only, `timeout 600`): **exit 3**, 1 finding. It is LOW
  `a3_category_not_yet_populated`, pre-existing, the same as v1.0 §8, and unrelated to Lane A. The
  report file `DRIFT_REPORT_adhoc_20260927T073612Z.*` is gitignored and was not committed.
- **Tracker live:** `--layer all` with F6, against read-only production and a ledger copy, reads
  **127** assets. L3 prints "21 active of 23 registry rows (is_active AND dead_flag IS NOT TRUE) —
  excluded (inactive/dead): ka_gochara_sweep, ka_gochara_v3_century_materialize".
