---
artifact: NIKASHA_WAVE1_LANE_A_REVIEW
reviewer: Opus gate (fresh context, read-only, not the implementer)
reviewed_on: 2026-09-27
packet_commits:
  - e2819e625   # A-1 R216 rebase
  - 432ed07da   # A-2 P3 closure loop
  - 7ed870775   # A-3 P4 precursors (R41, R40, R220, D6)
report_reviewed: d1a3988f4 (A_REPORT.md, written by a report-writer, not the builder)
verdict: REJECT (narrow)
---

# Nikaṣa wave 1 · Lane A · gate review

## §1 — Verdict

**REJECT (narrow).** The central part of Lane A holds up. A-1 matches engine `17e5a1257` hunk for hunk. A-2's
`emit_gaps` meets all six D4 acceptance cases, and each case has a test that fails when I break the code it
guards (6 of 6 mutations were caught). I re-ran the T3 cycle live with the production tools and it runs
OPEN→CLOSED→RE-OPENED→CLOSED. The tracker figures 9/12 → 6/7 reproduce with the real tracker. No untouchable file
moved, and both ledgers are unchanged across the packet. Three things fail the gate's own standard ("would this
survive someone trying to break it?"):

1. **An error can still close a gap (D4 case 1 is broken, shown live).** When a `count_sql` query fails, the
   census records `Build.completion = N/A "no count_sql"` (a false statement), and `emit_gaps` then **CLOSES**
   the open gap (F2). R40 exists because statement timeouts happen in production, so this path is real.
2. **The D6 path that is not wired will issue false closures the day migration 1094 lands.** `measure()` passes
   `attempt=None` whatever the detector finds. Once the instrument is present, every asset grades
   `Earn.build_record = N/A "never attempted"`, and N/A can close a gap. Simulated on the production ledger, this
   closes **all 40 open L0 `Earn.build_record` gaps** (F1). Migration 1094 already exists on the engine branch
   (`campaign/nirmana-engine`, `8edba0533`), and the deploy runs `migrate.ts`. The claim in the commit and the
   report that it "will grade for real … with no further code change" is false.
3. **Some proofs cannot fail.** The R220 tests and the R41 contract/idem tests check the source text, or test
   helper functions defined inside the test file itself. Two mutations survive the whole offline suite:
   reverting the R220 NULL-trap filter, and making the `Build.contract` guard re-raise. The second also survives
   the live suite (F3).

**What changes the verdict to ACCEPT:**
- **F1:** when the instrument is present but no attempt is supplied, read `NO_DETECTOR — attempt linkage not
  wired`, not N/A. Add a test that fails today.
- **F2:** make a failed `count_sql` read `ERRORED`, not N/A. Add a test that fails today.
- **F3:** replace the source-text tests with behavioural ones, meaning `measure()` or `registry()` run against a
  stubbed `psql`, so that mutations M8 and M9 fail.
- **F4:** make the `WITHDRAWN` handling in `emit_gaps` match its own comment.
- **F10:** correct the report where it overstates.

F5–F9 and F11–F12 can ride as corrections.

## §2 — Checklist

### Item 1 — the proof proves the claim

**Tests.** Ran all four files with the database env sourced, after checking
`SHOW default_transaction_read_only` = `on`:
```
$ python3 -m pytest test_b1_asset_census_blocked_dependency.py test_a2_emit_gaps_closure.py \
    test_a3_earn_cost_grading.py test_a3_fault_isolation_and_population.py -q
41 passed in 67.40s
```
Without the database, the result is 40 passed and 1 skipped (the live R41 test).

**T3 closure cycle, proof ledger.** In `a2_t3_proof/asset_gaps.jsonl`, `bg_nakshatra_medical-Build.registered`
appears at:

| line | state | time |
|---|---|---|
| 99 | OPEN | 04:23:22 |
| 213 | CLOSED | 04:23:36 |
| 215 | OPEN ("RE-OPENED") | 04:23:52 |
| 217 | CLOSED | 04:24:06 |

This is confirmed.

**T3 closure cycle, live re-run.** I did not write to the shared sandbox. Instead I ran `measure("L0")` four
times against read-only production with the production `emit_gaps`, into a temporary copy of the production
ledger, flipping `has_writer` for `bg_nakshatra_medical` in memory:
```
1 has_writer=False emit (0,209,0,0) -> OPEN      owner=asset_census
2 has_writer=True  emit (1,208,1,0) -> CLOSED    "CLOSED by measurement: @register in bg_medical_mappings.py; …"
3 has_writer=False emit (0,208,1,1) -> OPEN      "RE-OPENED by measurement: …"
4 has_writer=True  emit (0,208,1,1) -> CLOSED
```

**Tracker, with the real tool (not a transcription).**
- `asset_elevation_tracker.py --layer L0` at base `9981b8f5d`, on the proof ledger: `bg_nakshatra_medical`
  gaps_open/total = **9/12**.
- At HEAD with `NIKASHA_CONTROL_DIR`: **6/7**.
- Cutting the proof ledger at lines 212 / 213 / 215 / 217, the HEAD tracker gives 6 → 5 → 7 → 5. The target row
  moves open → closed → open → closed, which is the "0→1→0→1" in closed terms.

**Mutation tests.** Each mutation was applied to a scratch copy, the suite was run, and the copy was reverted:

| # | mutation | caught by |
|---|---|---|
| M1 | `CLOSABLE += NOT_GENERIC` | `test_case1_not_generic_never_closes_an_open_gap` |
| M2 | superseded check removed | `test_case4_superseded_id_never_resurrected` |
| M3 | `LIVE_GAP_STATES = ("OPEN",)` | `test_case2_in_progress_closes_on_pass` |
| M4 | owner not carried | both `test_case5_*carried*` |
| M5 | re-run appends a line | `test_case6_rerun_unchanged_failing_target_appends_nothing` |
| M6 | unclassified NULL → PASS | `test_case_unclassified_null_grades_no_detector_never_pass` |
| M7 | absent instrument → PARTIAL | two D6 tests |
| M8 | `Build.contract` guard re-raises | **nothing, offline or live** |
| M9 | R220 filter reverted to `is_active AND NOT dead_flag` | **nothing offline.** Live, only the R41 e2e test fails, with the message "layer must still be fully measured, not aborted" (it catches this by accident; the test is about something else) |
| M10 | `CLOSABLE += ERRORED` | `test_errored_never_closes_a_gap_and_never_opens_one` |
| M11 | Cost made dependent on the latest attempt | `test_case_failure_does_not_erase_a_prior_cost_baseline` |

**The specific attacks:**
- **Can NOT_GENERIC, UNKNOWN or ERRORED close a gap?** No; all were tested, including an arbitrary `"UNKNOWN"`
  string, which gave (0,0,0,0).
- **Can an unmeasured criterion close a gap?** No, it is skipped.
- **Can an errored check close a gap?** **Yes, through `Build.completion` (F2).** Live `measure("L0")` with
  `bg_ephemeris`'s count forced to `live_counts`' own `except Unknown → None` path gave:
  ```
  bg_ephemeris Build.completion: {'v': 'N/A', 'measured': "no count_sql; build state='lit'"}
  emit (0, 208, 1, 0) → bg_ephemeris-Build.completion CLOSED "CLOSED by measurement: no count_sql; …"
  ```
- **Can a superseded id be resurrected?** Not while the latest row carries `superseded_by`. It can if a later
  row without the flag follows (F5).
- **Does `emit_gaps` twice on an unchanged target append nothing?** Correct. Live L0 census, run twice against a
  copy of the production ledger: (0,209,0,0) then (0,209,0,0), 263 → 263 lines.
- **Is hand `change`/`owner`/`gate` carried onto transition rows?** Yes; tested by M4.
- **Can D6 read PASS on a NULL of unknown cause?** No. A healthy skip reads N/A with its reason. Earn and Cost
  are separate functions of different inputs (M11 is caught).
- **With the instrument absent, what do Earn and Cost read?** Both read `NO_DETECTOR — instrument absent
  (migration 1094), scoped to this run` in the census JSON, for 40/40 L0 assets and 21/21 L3 assets.
- **R41, one check made to raise.** A live L0 run with `contract_scan` raising for `bg_nakshatra_medical` gave
  `n_assets 40`, one `ERRORED` (`Build.contract`), 19 other criteria on that asset still measured, and the
  ledger still emitted.
- **R220 population.** `registry()` scopes the census; the live L3 JSON states
  `population_active 21 / registry_total 23` and names the two excluded ids. The tracker is **not** scoped
  (F6).

### Item 2 — nothing untouchable touched; ledgers append-only

Files changed by each commit (`git show --name-status`):

| commit | files |
|---|---|
| e2819e625 | `asset_census.py`, and `test_b1_*` (new) |
| 432ed07da | `asset_census.py`, `asset_elevation_tracker.py`, `test_a2_*` (new), `a2_t3_proof/asset_gaps.jsonl` (new) |
| 7ed870775 | `asset_census.py`, `test_a3_*` ×2 (new) |

- In the range `9981b8f5d..7ed870775`, the Lane B files (`catalog_provenance.py`, `provenance/**`, `B_*.md`)
  come only from `4e586118d` and `b2a2a7920`. None of them are in the Lane A commits.
- No writer, orchestrator file, sealed tier, `editorial.ts`/`compiler.ts`, register/plan/decisions/STATE file,
  or migration was touched.
- `git diff 9981b8f5d HEAD -- 00_ARCHITECTURE/control/asset_gaps.jsonl asset_certs.jsonl` is **empty**. The
  ledgers are 263 and 1 lines, and there are no uncommitted changes to them in the worktree.
- The census has no DB write path. The tracker opens a `readonly=True` session.
- The worktree does carry uncommitted Lane B edits to `catalog_provenance.py` and its test. They are not Lane A's
  and I left them alone.

### Item 3 — every status can read false (§N.8)

Which verdicts have a real failing case:

| verdict / transition | has a failing case? | evidence |
|---|---|---|
| CLOSED, RE-OPENED, IN_PROGRESS→CLOSED, superseded, idempotency | yes | M1–M5 |
| D6 NO_DETECTOR / PASS / FAIL / N/A branches | yes | M6, M7, M11 |
| ERRORED as non-closable | yes | M10 |
| R41 on `Vocab.identity` | yes | live test |
| R41 on `Build.contract` and `Idem.pattern` | **no detector behind it** | the test only checks that the source contains `except Unknown as exc:`; M8 survives |
| R220 filter | **no offline detector** | `test_population_filter_excludes_null_dead_flag_correctly` tests `naive_filter`/`fixed_filter` defined **inside the test** (lines 143–156) and never calls `asset_census`; M9 survives |

**D6 item 2, the unwired path.** Today the output is honest: `NO_DETECTOR — instrument absent`. But the unwired
state is not labelled as unwired. The honest label depends on the column being absent, not on the wiring being
present. When the column appears, the unwired path emits a green-looking, closable `N/A — never attempted` for
assets that have build records (F1). This is exactly the defect class the campaign exists to remove, sitting one
migration away from firing.

### Item 4 — idempotency and last-wins

- **Idempotency** is verified live (item 1).
- **Last-wins order.** Both `emit_gaps` and the tracker resolve by file order, not by `ts`.
  - For an append-only file, append order is the truth, so ties or out-of-order `ts` cannot hide a later OPEN
    behind an earlier CLOSED within one file.
  - The residual risk is outside the code: a git merge of two branches that both appended to the ledger
    concatenates rows in merge order, and a stale CLOSED could land after a newer OPEN. Neither tool detects
    this (F12, advisory).
- **Tracker on the production ledger.** The HEAD tracker and the base tracker, both run with `--layer all`, give
  **0 per-asset differences** in state, gaps_open or gaps_total across 129 assets. The production ledger has no
  duplicate gap_ids today.

### Item 5 — scope

- A-1, A-2 and A-3 only.
- R42–R56 were not started. There is no completion/registration/latest-row logic in the diff, and A-3's commit
  says it stopped.
- Extras:
  - The `Carr.detector` file binding is in scope (A-2 item d).
  - The `main()` ERRORED print and the exit-code change (ERRORED → exit 3) are reasonable and in scope.
  - Nothing out of scope was added.

### Item 6 — honesty of the report

The report is careful in most places. It overstates in four:

- **(a) "Lands … with no further code change"** (A_REPORT:252, :271, repeating the commit) is false (F1).
- **(b) D6 item 5 is marked "yes"** (A_REPORT:255). The ruling requires testing "against the engine
  implementation (`asset_runner.py` at `8edba0533`+, migration 1094)". The 11 tests use hand-built dicts only
  (F11).
- **(c) R41/R220 tests listed as coverage, "All PASS".** Four of the seven are source-text or tautological (F3).
- **(d) "`Build.exercised` … flips in lockstep"** (A_REPORT:319) is wrong. It flips inversely: line 214 is its
  first OPEN, 216 CLOSED, 218 RE-OPENED.

On the two figures the report labelled "commit-message-only":
- **`gaps_open` 9/12 → 6/7:** now VERIFIED with both real trackers (item 1).
- **The `depth_census` cost:** not re-measured. It was registered as an out-of-scope finding, and its absence
  does not block anything.

### Item 7 — regression

**Census, `--layer L0` against production.** Base ran in a temporary `git worktree` at `9981b8f5d` (since
removed), HEAD in this checkout, both read-only.
- Base: 102s, `FAIL 119 · PARTIAL/NO_DETECTOR 90`, exit 2.
- HEAD: 100s, `FAIL 39 · PARTIAL/NO_DETECTOR 170 · ERRORED 0`, exit 2.
- Runtime is unchanged. The asset set is the same 40.
- Every flip is in §4.

**Census, `--layer L3` at HEAD:** 100s, 21 assets, ERRORED 0. I did not re-run base on L3; the commit reports a
28m52s abort, and repeating that would put about 30 minutes of load on production for no gain.

**Tracker:** no change on the production ledger.

**Information lost:** the `Vocab.identity` measurement no longer states the duplicate *count* ("N
duplicate(s)" became "duplicate group(s) exist"). It changed on 37 L0 assets (F9). The `Build.history` text now
carries the blocked counts (B1), with no verdict change on L0.

**Latent regression:** before, `registry()` raised `Unknown` when it found zero rows. It now raises only when
the registry *total* is zero, so a zero-active population measures nothing and exits **0** (F7).

## §3 — Findings

| # | finding | evidence | blocks |
|---|---|---|---|
| **F1** | **Unwired D6 path → mass false CLOSE when migration 1094 lands.** `measure()` calls `_grade_earn_cost(attempt=None, instrument_present=<detected>, baseline=None)` unconditionally. With the instrument present, `attempt=None` → `N/A "never attempted — see Build.exercised"`, and N/A is in `CLOSABLE`. Simulation against a copy of the production ledger: `emit (0,169,40,0)` → **40 `Earn.build_record` gaps CLOSED** ("CLOSED by measurement: never attempted"). `test_case_never_attempted_grades_na` locks the branch in. The docstring also says `measure()` passes `False`, which it does not. | `asset_census.py:677`, `:524`, `:495`; `test_a3_earn_cost_grading.py:132` | Lane A acceptance; D6 adoption; §N.8 |
| **F2** | **Errored count query → false N/A → gap CLOSED.** `live_counts` maps a failing `count_sql` to `None` (`:328`, `:344`). `measure()` renders that as `N/A "no count_sql"` (`:660`), and `emit_gaps` closes on N/A. Demonstrated live on `bg_ephemeris-Build.completion`. D4 case 1 ("never on an errored check") is violated, and R41 is incomplete: this failure is not surfaced as ERRORED. | `asset_census.py:328,344,660,814` | Lane A acceptance (D4 case 1) |
| **F3** | **Proofs that cannot fail.** `test_contract_scan_exception_degrades_to_errored_not_layer_abort` asserts that the monkeypatch raises, then greps the source. `test_depth_census_timeout_…` counts `except Unknown` strings. `test_population_filter_…` tests functions defined in the test. The `registry`/`measure` population tests grep the source. M8 and M9 survive the offline suite; M8 survives live too. | `test_a3_fault_isolation_and_population.py:32–53,114–124,129–175` | §2.5 of the prompt ("a test that fails without the change") |
| **F4** | **`WITHDRAWN` is re-opened, contrary to the code's own comment.** The comment says anything other than OPEN/IN_PROGRESS/CLOSED "is left alone rather than re-opened by inference". The code re-opens it: WITHDRAWN + FAIL → (0,0,0,1), new OPEN row. The schema defines WITHDRAWN (ledger line 1). This is the same defect class as the §N.7 "allowlist contradicts its own docstring". | `asset_census.py:818` vs `:887` | Lane A acceptance (correction) |
| F5 | The superseded check reads only the latest row. A `superseded_by` on an earlier row followed by a later hand row without it → the census closes or re-opens that id again. Demonstrated: `(0,0,1,0)`. | `asset_census.py:869` | D4 migration (R80/R81), before any crosswalk lands |
| F6 | R220 is not applied to the tracker. It counts 23 L3 / 129 total, the census counts 127. The prompt says "every population figure", and the tracker is a Lane A file. | `asset_elevation_tracker.py:141–146` | the fold of R220 |
| F7 | A zero-active population exits 0 silently. Before, it raised `Unknown` (exit 4). With the NULL-trap filter, M9 produced `n_assets 0` and no error. | `asset_census.py:315` | §N.8 (correction) |
| F8 | The `Carr.detector` binding ignores `returncode` and does not validate `out["verdict"]` against the closed set. A crashing detector whose last stdout line says `"PASS"` would close a gap. | `asset_census.py:779–782` | before any detector file is registered |
| F9 | `Vocab.identity` lost its duplicate-count figure. The ledger `_schema` requires `what` = "measured: <figure …>". | `asset_census.py:714` | advisory |
| F10 | The report overstates, items 6(a)–(d). | A_REPORT:252, 255, 271, 319 | report re-issue |
| F11 | D6 item 5 ("tested … against the engine implementation") is not met. It needs a test against real `8edba0533` `build_run_assets`/`asset_throughput` shapes. | `test_a3_earn_cost_grading.py` | D6 adoption |
| F12 | R41's scope limit is not disclosed. Layer-level reads (`catalog`, `throughput`, `build_history`, `registered_ids`) still abort the whole layer on `Unknown`. The merge-order risk from item 4 also applies. | `asset_census.py` `measure()` head | advisory |

## §4 — Verdict flips per asset (L0, base `9981b8f5d` → HEAD `7ed870775`, live production, read-only)

| criterion | base → HEAD | assets | explanation |
|---|---|---|---|
| `Earn.build_record` | FAIL → NO_DETECTOR | 40/40 | D6 item 1. `asset_throughput.duration_seconds` is absent (migration 1094 not applied), so the result is `NO_DETECTOR — instrument absent (migration 1094), scoped to this run`. Base's FAIL came from `rows_per_second=NULL`, which cannot tell a stale column from an unmeasured one. Correct per the ruling. |
| `Cost.baseline` | FAIL → NO_DETECTOR | 40/40 | Same cause and label. Correct per the ruling. |
| every other criterion | no flip | 40 | `Vocab.identity` text changed on 37 assets (F9) and `Build.history` text on 13 (B1 blocked counts); no verdict moved. |

The FAIL total falls from 119 to 39 (80 = 40 + 40). The commit's "~122" was the base figure at its own
measurement time; I measured 119. There were no L0 population changes (40 active of 40).

## §5 — Fact spot-check

| # | claim (source) | result |
|---|---|---|
| 1 | 41 Lane A tests pass, live DB (report §4) | **VERIFIED**: 41 passed, 67.4s |
| 2 | A-1 ported verbatim from engine `17e5a1257`, 175 diff lines (A-1 commit) | **VERIFIED**: `+/-` hunks identical; engine patch is 175 lines; test file byte-identical |
| 3 | Proof ledger 218 lines; target row at 99/213/215/217 OPEN→CLOSED→OPEN→CLOSED (report §5) | **VERIFIED** |
| 4 | Pre-A2 tracker 9/12, fixed 6/7 for `bg_nakshatra_medical` (A-2 commit; report "not verified") | **VERIFIED** with both real trackers |
| 5 | Registry 129 rows / 127 active; `dead_flag` NULL on every row; the literal `is_active AND NOT dead_flag` matches 0 (A-3 commit) | **VERIFIED**: 129 / 127 / 0; NULL on 129 of 129 |
| 6 | Excluded ids `ka_gochara_sweep`, `ka_gochara_v3_century_materialize`; L3 21 of 23 (A-3 commit) | **VERIFIED** (live L3 JSON) |
| 7 | `kala_field` EXISTS probe ≈ 8.2s, 0 duplicates (A-3 commit) | **VERIFIED**: 8.20s, `f` |
| 8 | `kala_field` 10,982,957 rows (A-3 commit) | **NOT RE-COUNTED**: `pg_class.reltuples` estimate is 10,280,842; the exact count was not re-run |
| 9 | Fixed L3 completes in ~89s, 0 ERRORED (A-3 commit) | **VERIFIED in order**: 100.4s, 0 ERRORED, exit 2 |
| 10 | L0 FAIL "~122 → 39" (A-3 commit) | **PARTLY**: 119 → 39 today; 39 matches, and 119 vs ~122 is a drift in the base figure |
| 11 | Earn/Cost read NO_DETECTOR for all L0 assets (A-3 commit) | **VERIFIED**: 40/40 L0, 21/21 L3, text `instrument absent (migration 1094)` |
| 12 | "Will grade for real the moment migration 1094 lands, with no further code change" (A-3 commit; report :252/:271) | **WRONG**: grades 40/40 `N/A "never attempted"` and closes 40 gaps (F1) |
| 13 | `Build.exercised` flips "in lockstep" (report :319) | **WRONG**: inverse (214 first OPEN, 216 CLOSED, 218 RE-OPENED) |
| 14 | D6 item 5 covered, "yes" (report :255) | **WRONG**: not tested against the engine implementation (F11) |
| 15 | Neither ledger changed; 263 / 1 lines (A-2 commit) | **VERIFIED**: empty `git diff`; 263 / 1 |
| 16 | Manifest does not register `asset_census.py` / tracker (report §8) | not re-run; out of the gate's blocking path |
