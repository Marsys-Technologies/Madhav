---
artifact: NIKASHA_WAVE1_LANE_A_REPORT
canonical_id: NIKASHA_WAVE1_LANE_A_REPORT
version: "1.0"
status: LANE COMPLETE — awaiting the reviewer gate (§5 of the execution prompt)
lane: A
commits:
  - e2819e625e152427a98876865d8cf733a8f2b457   # A-1: R216 rebase
  - 432ed07dae3511596a20a057e49f8b68570eff77   # A-2: P3 closure loop
  - 7ed8707757195e680fc972fc42dc82f1ebc1d50b   # A-3: P4 precursors
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
| 2 | Attributes timing to an attempt — measurement identity is `(asset, chart scope, latest build_run_assets attempt)`, not `duration + last_built_at` alone | `_grade_earn_cost(attempt, ...)`'s parameter shape and docstring specify the identity | **structurally present, not live-wired.** `measure()` calls `_grade_earn_cost(attempt=None, instrument_present=instrument_present, baseline=None)` unconditionally — the commit is explicit that the actual per-attempt query wiring "lands with migration 1094, with no further code change." No test exercises a real `attempt` dict sourced from a live `build_run_assets` row; the 11 tests all hand-construct `attempt`/`baseline` dicts. This is an honest gap, not a hidden one — the commit message itself says so. |
| 3 | Grades `Earn.build_record` by cause (finite duration incl. zero-row → PASS; healthy non-execution/no-writer service → N/A; legacy `_telemetry` completion-no-duration → FAIL; failed/aborted before completion → N/A; unclassified NULL → NO_DETECTOR, never PASS) | `_grade_earn_cost`'s five-branch cause classifier | `test_case_zero_rows_with_finite_duration_grades_pass_with_rate_zero`, `test_case_skip_no_delta_grades_na_and_preserves_prior_baseline`, `test_case_probe_green_grades_na`, `test_case_legacy_health_probe_service_no_writer_grades_na`, `test_case_legacy_telemetry_path_grades_fail`, `test_case_failure_before_completion_grades_earn_na_cost_by_prior_baseline`, `test_case_unclassified_null_grades_no_detector_never_pass`, `test_case_never_attempted_grades_na` | yes, all five named branches covered |
| 4 | Grades `Cost.baseline` against the most recent sanctioned (measured) completion, independent of the latest attempt's outcome; no measured completion ever → `FAIL — no sanctioned baseline build` | `_grade_earn_cost`'s `cost = ...` branch | `test_case_failure_does_not_erase_a_prior_cost_baseline` (plus the cost side of several of the item-3 tests, which assert `Cost.baseline` alongside `Earn.build_record`) | yes |
| 5 | Tested before adoption against the engine implementation: failure, zero rows, skip after a prior timing, probe-green, the legacy `ga_*` path, the absent column, an unknown NULL (seven named scenarios) | n/a (a testing obligation, not a code branch) | 11 tests total in `test_a3_earn_cost_grading.py`; the seven named scenarios each have a directly-named test (absent column → `test_case_absent_column_grades_no_detector_never_partial`; zero rows → `test_case_zero_rows_with_finite_duration_grades_pass_with_rate_zero`; skip-after-prior-timing → `test_case_skip_no_delta_grades_na_and_preserves_prior_baseline`; probe-green → `test_case_probe_green_grades_na`; unknown NULL → `test_case_unclassified_null_grades_no_detector_never_pass`; failure → `test_case_failure_before_completion_grades_earn_na_cost_by_prior_baseline`); plus two tests beyond the seven (`test_case_instrument_unreachable_is_a_distinct_reason`, `test_case_never_attempted_grades_na`), matching the commit's own count ("11 tests cover the seven named scenarios... plus instrument-unreachable and never-attempted"). One honest caveat: the ruling's phrase "the legacy `ga_*` path" does not map unambiguously onto a single test name — this report identifies `test_case_legacy_health_probe_service_no_writer_grades_na` and `test_case_legacy_telemetry_path_grades_fail` as the two candidates (a no-writer health-probe service and the pre-1094 `_telemetry` completion-with-no-duration path, respectively) but the commit does not state which one the ruling's exact wording refers to, so this report does not force a single mapping it cannot verify | yes, with the one naming caveat above |

R41/R220 test coverage (not part of D6, listed separately since the execution prompt names them
alongside D6 in A-3): `test_contract_scan_exception_degrades_to_errored_not_layer_abort`,
`test_errored_never_closes_a_gap_and_never_opens_one`,
`test_live_e2e_one_simulated_query_timeout_degrades_not_aborts` (live, PASSED against production —
see above), `test_depth_census_timeout_does_not_block_vocab_or_ldgr_checks_from_running` (R41);
`test_population_filter_excludes_null_dead_flag_correctly`, `test_registry_returns_population_tuple_shape`,
`test_measure_states_the_population_never_silently_drops_it` (R220). All PASS, live-DB included.

**Honest limits:**

- D6 item 2 (attempt-linked provenance) is specified in the function signature and docstring but
  not wired into `measure()`'s call site with a real attempt — `measure()` passes `attempt=None`
  unconditionally today because `asset_throughput.duration_seconds` (migration 1094) is confirmed
  absent in both production and the nikasha_sandbox proof DB. The commit is explicit this wiring
  "lands... with no further code change" once the migration is applied; until then, `Earn.build_record`
  and `Cost.baseline` read `NO_DETECTOR` for every asset in every layer, which this report confirmed
  live (`--layer L3` re-run above: `Earn.build_record`/`Cost.baseline` do not appear among the FAIL
  lines at all, consistent with a blanket `NO_DETECTOR`).
- **Out-of-scope finding registered by the commit itself, not fixed:** `depth_census`'s per-column
  `count(c)` over the same 10.9M-row `kala_field` table is a further, unfixed cost. The commit states
  it "did not dominate the pre-fix runtime in this measurement, but is a candidate for the same R40
  treatment in a later pass." This report did not independently re-measure `depth_census`'s cost in
  isolation; it is carried forward here exactly as the commit states it, not re-verified further.
- A-4 (below) is the explicit stop point; R42–R56 were not started.

## 4 — Combined test run (all four Lane A test files, live DB)

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
(`bg_nakshatra_medical-Build.exercised`, lines 214/216/218) flips in lockstep as a side effect of the
same `has_writer` toggles, which is expected (both criteria read the same registry field) and is not
a defect.

**Not independently re-run:** this report did not re-execute the sandbox toggle sequence against the
`nikasha_sandbox` DB (the `.sandbox/` Postgres instance is still running at
`00_ARCHITECTURE/briefs/nirmana/nikasha_test/.sandbox/pgdata`, confirmed via `ps aux`, but replaying
the exact toggle sequence risks disturbing that sandbox's state without a clear net gain over the
committed ledger, which already shows the full cycle unambiguously). The `test_full_loop_open_closed_reopened_closed`
unit test (§2 above, re-run and PASSING) exercises the identical logic in-process against a
disposable temp ledger, which this report treats as sufficient corroboration of the mechanism
without touching the sandbox.

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

1. `depth_census`'s per-column `count(c)` cost over `kala_field` (10.9M rows) is unfixed and
   registered by the A-3 commit itself as a candidate for a later R40-style pass (§3, honest limits).
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

No proof claimed in the three commits was found to be false. Two items could not be independently
re-verified beyond what the commit states (the tracker's exact `gaps_open` A/B numbers in §5, and the
`depth_census` cost characterization in §3/§7) and are labelled as commit-message claims, not
independent confirmations. R42–R56 remain untouched, and the "background timing comparison job" the
builder's last words referenced could not be found anywhere in the committed evidence.
