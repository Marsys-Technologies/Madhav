---
artifact: NIKASHA_WAVE2_W2-1_REPORT
packet: W2-1 — no unearned closure; no silent absence (freeze blockers)
version: "1.2"
status: CORRECTIONS C1/C3 (W2-1_REVIEW, 8af39a194) and C4/C5 (W2-1_C1_REVIEW, 763529d07) APPLIED; R222 precondition MET per the C1 re-gate
changelog:
  - "1.2 (2026-09-27): C1 re-gate corrections — C4 tests pin the execution marker (b98fc92c7); C5 wording: both
    started_at sites named (asset_runner.py:1403, run_heavy_writer_standalone.py:137) in report and docstring,
    executed = started stated, new #36 (C1 writerless unstarted N/A) → 36 branches, R42 heading, earn_cost_signal
    obsolete not a miss, C1-M4 log re-run with both guards reverted; F-C4 (newline-split rows) listed."
  - "1.1 (2026-09-27): corrections after gate review — C1 code fix (1ae91dae4: a queued/never-started
    build_run_assets row is not an execution; Build.history never PASSes at 0 completions), re-census and
    re-emit; C3 wording: R42 basis mismatches (bo_upaya, ga_condition), R52 A5 flip under target_floor=0,
    Dens.served partial 29 (not 31), proxy labels #1/#2/#3/#25/#29, #5/#32 relabelled fixed, T1 presented
    16/16 applicable + 1 awaiting re-spec, §7 findings C2/F4–F8 listed. New §11."
  - "1.0 (2026-09-27): builder report."
produced_on: 2026-09-27
builder: Opus (wave-2 builder, packet W2-1 only)
base: 9baaa307b
head_code: 1ae91dae4 + C5 docstring (v1.0: d465d5a2c); tests b98fc92c7
rows: [R224, R231, R223, R222, R225, R42, R52, R56, R48]
files_touched:
  - platform/scripts/governance/asset_census.py
  - platform/scripts/governance/__tests__/test_w2_1_earned_verdicts.py   (new)
  - platform/scripts/governance/__tests__/test_a3_earn_cost_grading.py
  - platform/scripts/governance/__tests__/test_a3_fault_isolation_and_population.py
  - platform/scripts/governance/__tests__/test_a4_d6_engine_conformance.py
  - platform/scripts/governance/__tests__/test_a4_gate_corrections.py
  - 00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave2/** (this report + w2-1_evidence/)
not_touched: asset_elevation_tracker.py (no change needed), writers, orchestrator, migrations, sealed tiers,
  editorial.ts/compiler.ts, register/plan/decisions/STATE, catalog_provenance.py and its tests, provenance/**,
  00_ARCHITECTURE/control/asset_gaps.jsonl + asset_certs.jsonl (md5 30365ff2… / 514cbdfc…, 263 / 1 lines,
  unchanged before and after every run in this packet)
---

# Nikaṣa wave 2 · W2-1 · builder report

## §0 — Summary

Nine rows, nine commits, one row per commit (`git commit -- <paths>`, only-mode; nothing pushed). Every row
has a test that fails without its change, with the mutation run recorded (§2, full output in
`w2-1_evidence/mutation_runs.log`).

| row | commit | one line |
|---|---|---|
| R224 | `9af0fcce5` | Population scoped by `asset_registry.layer`; `lel_events` is measured; the census counts 127, like the tracker. |
| R231 | `58cf4c238` | `$1` is bound to the canonical chart, and each count is read against that chart's own build record. **All 78** L1–L5 ERRORED `Build.completion` readings are now measured (0 ERRORED on any layer). |
| R223 | `9079830b9` | A real `subprocess.TimeoutExpired` becomes `CheckTimeout(Unknown)`, so that check reads ERRORED. |
| R222 | `61c6e637a` | The four latent paths now read NO_DETECTOR/ERRORED with a reason: NULL count, unrecognised writer, missing caps dir, and an empty table on depth (plus identity on an empty table, same class). |
| R225 | `14f3f5d1c` | Behavioural test of the `measure()` call site with the instrument present. `attempt_linkage_wired` now defaults to `False`. |
| R42 | `cfa9f42c0` | `Build.completion` actually compares `rows_written` with live, on a stated basis (not always like for like — v1.1, §11). A non-completed build record, or a constant `count_sql`, can no longer PASS. |
| R52 | `e9db66f2b` | Non-emptiness is checked first and separately. Emptying a table FAILs unless the registry declares zero rows complete. |
| R56 | `416fe4574` | A declared floor over a parameterised or multi-table `count_sql` always gets a verdict. The three differential breaches are now reported. |
| R48 | `d465d5a2c` | `Count.floor` is emitted on every asset that declares `target_floor` (121/121). `target_floor=0` reads N/A, not a vacuous PASS. |

**Packet proofs.**

1. **Branch enumeration (§3).** 36 PASS/N/A-yielding branches (v1.2; 35 before C1 added #36):
   - **19 genuine measurement** of **36** branches (v1.2: C1 added #36; v1.1 said 18 of 35; v1.0 said 23). Of these, 5 are Earn/Cost branches that `measure()` cannot
     reach today.
   - **10 fixed** in a W2-1 commit (v1.1: + #5 and #32 by C1, `1ae91dae4`).
   - **3 proxies** (#1, #2, #3) relabelled after the review's attacks.
   - **4 genuine-but-contested** gradings are listed as out of scope, with their owning row or finding. They are
     not fixed and not called genuine without a caveat.
   - **8 branches that existed at `9baaa307b` are gone:** every one was an unmeasured → closable path.
2. **Census diff (§4).** Full six-layer census at HEAD vs `9baaa307b`:
   - 223 verdict changes. Every one is attributed to a W2-1 row; 0 are unexplained.
   - ERRORED falls 78 → 0.
   - `lel_events` is newly measured.
3. **T1 planted suite (§5).** It ran in full on the sandbox, at both commits. `build_completion_truncate` now
   reads **FAIL**; it was FAIL→PASS at `9baaa307b`. 16/16 applicable plants are detected at HEAD (15/16 at base).
   The 17th plant, `earn_cost_signal`, is **obsolete** at both commits (D6 retired `rows_per_second` as the
   Earn/Cost basis) and awaits re-specification under R55 — it is not a miss (v1.2 wording).
4. **`--emit-gaps` dry run (§6).** Six layers, on a ledger copy:
   - 596 OPEN rows appended, **0 CLOSED, 0 RE-OPENED**, 209 already present.
   - A re-emit is byte-identical (idempotent).
   - No CLOSED row exists that lacks a genuine PASS or justified N/A. Across all 127 assets, only 3 closable
     N/A verdicts fall outside the justified set, all the contested `Build.target` (R53, W2-2).

**Suite and checks.**
- Offline suite: 178 → 219 tests.
  - At `9baaa307b`: 171 passed, 5 skipped, 2 failed.
  - At HEAD: 208 passed, 9 skipped, 2 failed.
- Live suite at HEAD: 217 passed, 2 failed.
- The same 2 failures (`test_drift_detector_h35_h38.py`) are pre-existing at `9baaa307b`.
- `manifest_fingerprint --check`: MATCH.
- `drift_detector`: exit 3 (1 LOW).

## §1 — Scope and safety

- **Database.** Every production query ran through the session scratchpad `pgenv.sh`, and
  `SHOW default_transaction_read_only` = `on` was verified once at session open. `dbenv.sh` and `gcloud` were not
  used. Every DB/long command ran under `timeout 300`; `drift_detector` ran under `timeout 600`.
  - The live suite was split into three invocations to stay under that cap (§7).
  - The one write target was the **sandbox** (`nikasha_sandbox`, the T1 harness's own local DB, via its own
    socket). Every plant was restored and verified (`restore_ok=True` 17/17 at both commits).
- **Ledgers.** Production `asset_gaps.jsonl` / `asset_certs.jsonl` were never written. They are md5-identical
  before and after (`30365ff2…` / `514cbdfc…`, 263 / 1 lines). Every emit ran on a copy via
  `NIKASHA_CONTROL_DIR=<scratch>/w2-1/ctrl_emit`.
- **Scratch.** Everything lives under `<scratchpad>/w2-1/`. Two temporary worktrees (`9baaa307b` for the base
  census and base plants, HEAD for the plants) lived there and were removed after (`git worktree list` shows
  neither).
  - The T1 code plants (writer / capability-file edits) ran **inside those worktrees**, never in this checkout.
    Both were `git status`-clean after restore.
- **No writer, orchestrator, migration, sealed tier, register/plan/decisions/STATE or Lane B file changed.**
  `git diff --stat 9baaa307b..d465d5a2c` lists only the six files in the frontmatter.

## §2 — Per row: commit, diff, test, mutation evidence

Mutation method (`w2-1_evidence/mut.sh`): copy the file, apply one surgical replacement, run the named test
file, restore the copy (checked byte-identical with `cmp`), then re-run the whole governance suite (offline,
drift tests excluded) and confirm it is green. `live` means `pgenv.sh` was sourced (read-only production).

### R224 — population by `asset_registry.layer` · `9af0fcce5`

**Diff.**
- `registry()` scopes all three reads by `layer = '<registry_layer>'`, not `asset_id LIKE '<prefix>%'`
  (`asset_census.py:367`).
- New `_asset_scope()` (`:466`): `throughput()` and `build_history()` read the measured ids
  (`asset_id IN (…)`), so `lel_events`' build record and history are read like any other asset's.
- The prefix still names the layer's writers and capability modules.
- The test stubs in `test_a4_gate_corrections.py` accept the extra argument.

**Why.** A_REVIEW2 G5: `lel_events` (layer `mimamsa`, no `mi_` prefix) sat outside every census. The census
measured 126 where the tracker counts 127.

**Test.** `test_r224_registry_measures_an_active_asset_outside_the_prefix`,
`test_r224_build_record_is_read_for_the_measured_population_not_the_prefix` (offline), and
`test_live_r224_population_is_127_and_includes_lel_events` (live).
- The offline tests use a fake that **evaluates** the scope predicate the census actually sent (equality,
  LIKE, or IN-list) against a fixed row set.
- It is text-keyed, and that is disclosed. The live test is the real-SQL proof.

**Mutations.**
```
R224-M1 scope -> asset_id LIKE '<prefix>%'   offline: 2 failed (both r224 tests) · live: 3 failed (+ live 127 test)
R224-M2 _asset_scope ignores ids             offline: 1 failed (build_record_is_read_for_the_measured_population)
after revert: 154 passed, 6 skipped (governance suite, drift tests deselected)
```

**Live.** Census population is 127 = the tracker's figure (L5 15, including `lel_events`).

### R231 — canonical chart bound to `$1` · `58cf4c238`

**Diff.**
- `CANONICAL_CHART_ID` / `CHART_ID` (env `NIKASHA_CENSUS_CHART_ID`).
- `_bind_chart()` (`:138`) replaces `$1` with the quoted chart id, which is the engine's own binding in
  `asset_runner._data_rows_present`.
  - It refuses the `362f9f17` phantom and any non-uuid chart.
  - Any other unbound parameter goes to `errored` with the reason; it is never run half-bound.
- `throughput()` keeps one record per `(asset, chart)`. `_build_record()` (`:494`) picks the record that matches
  the count's scope:
  - a chart-scoped count uses that chart's record;
  - a global count uses the NULL-chart record;
  - otherwise the bound chart's record is used, and the label says so.
- The verdict names the chart. The census states `chart_scope` / `chart_scoped_count_sql`.

**Why.** A_REVIEW2 G4: 78 `count_sql` could not bind `$1`, so `Build.completion` was unmeasured above L0.
The pre-R231 `throughput()` also kept one arbitrary chart's row per asset, so a count for chart A would have been
compared with chart B's `rows_written`.

**Test.** `test_r231_chart_scoped_count_sql_is_bound_and_measured`,
`test_r231_the_build_record_is_the_bound_charts_not_another_charts`,
`test_r231_an_unbindable_parameter_is_errored_not_run_half_bound`, `test_r231_the_phantom_chart_is_refused`,
and `test_live_r231_every_l4_count_sql_is_measured_for_the_canonical_chart`. The offline fake answers like
PostgreSQL: an unbound `$1` → `ERROR: there is no parameter $1`.

**Mutations.**
```
R231-M1 bound = q (no binding)                    offline: 2 failed · live: 3 failed (+ live L4 test)
R231-M2 _build_record takes an arbitrary chart   offline: 1 failed (the_build_record_is_the_bound_charts…)
after revert: 158 passed, 7 skipped
```

**Live.** 79 chart-scoped `count_sql` (the 78 plus `lel_events`), **0 errored** (all six layers,
`live_counts` direct).
- In the full census the 78 former ERRORED readings resolve as 46 PASS, 13 FAIL on comparison (R42),
  11 FAIL as not a completed build (R42), and 8 FAIL empty (R52).
- The uniqueness assumption under `_build_record()` was checked live: `asset_throughput` has **no** duplicate
  `(chart_id, asset_id)`.

### R223 — a real psql timeout → ERRORED · `9079830b9`

**Diff.** `psql()` (`:167`) catches `subprocess.TimeoutExpired` and raises `CheckTimeout(Unknown)` (`:158`),
naming the limit and the query. Every per-check `except Unknown` then grades ERRORED. A timed-out layer-wide read
still aborts the layer, fail-closed and naming the read (F12, unchanged).

**Test.** `test_r223_psql_converts_the_real_timeout_expired` and
`test_r223_a_real_timeout_in_one_check_grades_errored_and_the_layer_completes`.
- A `psql` on `PATH` that `exec sleep 30`, with a 1 s client timeout, so `subprocess.run` raises the **real**
  `TimeoutExpired`. The tests assert `__cause__` is that type.
- `measure()` runs end to end with the real `depth_census`. `Complete.depth` reads ERRORED and the asset's other
  checks are still measured.

**Mutations.**
```
R223-M1 except clause no longer matches TimeoutExpired   2 failed (both r223 tests)
R223-M2 CheckTimeout(Exception) instead of (Unknown)     2 failed
after revert: 160 passed, 7 skipped
```

### R222 — the four latent unmeasured → closable paths · `61c6e637a`

**Diff.**

| path | before (`9baaa307b`) | now (HEAD) | where |
|---|---|---|---|
| **N1**: `count_sql` returns NULL or a non-integer | mapped to `None` with no error, then `Build.completion` N/A "no count_sql" (false text) | `live_counts._take()` records it as errored: `Build.completion` **ERRORED** "count_sql returned NULL". A comment-only `count_sql` is errored the same way. | `:439` |
| N1, absent `count_sql` | N/A for any asset | N/A only when nothing is built (no writer, or a declared service with no `target_table`). A writer-backed data asset with no `count_sql` is **NO_DETECTOR**. | `:991` |
| **N2**: no recognised `@register` | `contract_scan` / `idem_scan` returned N/A for an empty file list | They return NO_DETECTOR. New `_no_writer_scanned()` (`:771`) grades N/A only when the registry says `has_writer=false`; with `has_writer=true` it reads **NO_DETECTOR** "never scanned". `_measure_contract` / `_measure_idem` take `has_writer` (a required argument, not a defaulted one). | `:259`, `:295`, `:771` |
| **N3**: capability directory missing | `Dens.served` N/A | `capability_scan` returns `scanned=False`, so `Dens.served` reads **NO_DETECTOR** "never scanned". `scanned is not True` is the test, so a missing key is unsafe-proof. | `:1150` |
| **N5**: empty or column-less table | `Complete.depth` PASS "table empty" | **NO_DETECTOR** | `:1058` |
| N5, same class (disclosed extension) | `Vocab.identity` "0 duplicate(s)" on 0 rows | **NO_DETECTOR** "vacuous on 0 rows". The row count comes from the depth census, or from one `EXISTS` probe when depth errored. | `:1119` |

**Why.** A_REVIEW2 G2. One live ledger-copy run produced 26 false closures through these paths. The
enumeration in §3 also found that **N2 was live, not latent**: 13 writer-backed L3/L4/L5 assets
(constant-indirection `@register(ASSET_ID)`, R43) read the closable N/A at `9baaa307b`. G2's "none fires on
production data" held for L0 only (OS-8).

**Test.** 9 tests `test_r222_*`. Each runs the real `measure()`, and where relevant the real `capability_scan` or
`depth_census`, then `emit_gaps` on a ledger copy that holds the gap OPEN. Nothing closes. Positive controls keep
the genuine N/A: a service with no `count_sql`, `has_writer=false`, and a scanned directory with no referencing
module.

**Mutations** (each path reverted individually):
```
R222-N1 _take no longer records NULL as errored          1 failed (n1_a_count_sql_returning_null…)
R222-N1-absent no-count N/A for any asset               1 failed (n1_a_genuinely_absent_count_sql…)
R222-N2 _no_writer_scanned always N/A                   1 failed (n2_an_unrecognised_writer…)
R222-N3 scanned check disabled                          1 failed (n3_a_missing_capability_directory…)
R222-N5-depth empty-table branch disabled               1 failed (n5_an_empty_table…)
R222-N5-identity empty guard disabled                   2 failed (n5_an_empty_table…, n5_identity_…_probes_when_depth_errored)
after each revert: 168 passed, 7 skipped
```

Wave-1 tests changed: `test_a3_fault_isolation_and_population.py` passes `has_writer` to the two helpers, and
its source-grep call-shape test was updated to the new call text. That grep test is wave-1's, kept as a
structural backstop and not claimed as proof.

### R225 — the `measure()` Earn/Cost call site; safe default · `14f3f5d1c`

**Diff.**
- `_grade_earn_cost(attempt_linkage_wired=…)` defaults to **`False`**.
- The wave-1 source-grep test `test_case_attempt_linkage_unwired_is_the_default_measure_call_shape` could not
  fail (a comment satisfied it, G1). It now asserts the default's *behaviour* instead.
- The legitimately wired callers now pass `True` explicitly: the never-attempted N/A test, and the D6
  engine-conformance helper (13/13 still pass).

**Test.** `test_r225_measure_with_the_instrument_present_reads_no_detector_and_closes_nothing` runs the real
`measure()` with `duration_instrument_present → True`.
- Earn and Cost both equal `NO_DETECTOR — attempt linkage not wired`.
- An open `Earn.build_record` gap stays OPEN.
- Also `test_r225_the_default_is_the_safe_value`.

**Mutations.**
```
R225-M1 call site passes attempt_linkage_wired=True                          1 failed (the measure() test)
R225-M2 F1b shape (kwarg dropped) under the OLD unsafe default True          3 failed
R225-M3 F1b shape under the NEW default                                      survives — by design: identical behaviour
after revert: 170 passed, 7 skipped
```

### R42 — `Build.completion` compares `rows_written` with live, on a stated basis · `cfa9f42c0`

**Diff (`:990–:1030`).**
- **The defect.** The pre-fix final branch read PASS for **any** `rows_written > 0` without comparing.
  "mi_kula 15 vs 11 scored PASS" came from that branch; 15 vs any figure would have passed.
- **Now:**
  - `rows_written != live` reads FAIL, with both figures.
  - The build record must be a completed build: state `lit` or `stale`. `COMPLETED_STATES` is at `:135`, and
    staleness itself is R45's (W2-2). An `error`, `incomplete`, `dormant` or `building` record reads FAIL "not a
    completed build — see Build.history". **Disclosed extension:** without this, rows left by a failed build
    that happen to equal the live count read PASS (8 of the 11 live cases, §4).
  - A `count_sql` that reads no table reads **NO_DETECTOR**. `_count_tables()` is at `:117`; the live case is
    bo_samvada, `SELECT 0 AS count`.
- **Basis stated.** A multi-table `count_sql` is compared as the **total** over the tables it reads. For mi_kula
  the writer's `rows_written` is the same total (`mi_kula.py:302/353`: `len(_FAMILIES) + len(_CONTROLS)`). The target
  table's own row count is appended as context ("whole table — context, not the compared figure"). Assets gain
  `live_rows_basis` and `count_sql_tables`.
- **v1.1 correction (C3-i).** "The writer's `rows_written` is the same total" does **not** hold in general, so the
  comparison is on a *stated* basis, not always like for like. The gate review found two live counter-examples:
  bo_upaya's `rows_written` (240) sums **5** tables while its `count_sql` sums **2** (45 + 135 = 180), and
  ga_condition's `rows_written` (45) is `ga_condition_composite` alone while its `count_sql` also counts
  chart_facts avastha rows (2 970). Those two FAILs are **basis mismatches between the registry count and the
  writer's tally, not data disagreements**. The direction is fail-safe (FAIL, never closable).

**Ruling I applied, and why (reviewer: please check).** The handverify table's "truth FAIL" for mi_kula
compared a two-table `rows_written` (15 = 11 + 4) with one table (11). I did not adopt it. That is
apples-to-oranges. The census now shows the decomposition explicitly instead:
```
L5 mi_kula Build.completion PASS | rows_written=15 = live=15 (count_sql total over 2 table(s):
mimamsa_signal_families, mimamsa_negative_controls; global); target_table mimamsa_signal_families alone: 11 row(s)
```
"Compares count_sql against itself" is closed in two senses:
- a comparison now actually happens;
- a figure that cannot vary (a constant) is never compared.

A **residual true self-comparison** is not detected: the engine's no-op-completion path sets
`rows_written = count_sql`. There is 1 `asset.noop_completion` event in `orchestrator_event_register` (limits,
§8).

**Test.** 5 tests `test_r42_*`: disagreement FAILs; multi-table PASS with basis and target-alone; multi-table
disagreement FAILs; constant NO_DETECTOR; state `error` FAILs.

**Mutations.**
```
R42-M1 comparison removed                 2 failed
R42-M2 completed-state guard removed      1 failed
R42-M3 constant count measured            1 failed
R42-M4 multi-table basis dropped          1 failed
after revert: 175 passed, 7 skipped
```

### R52 — non-emptiness, measured separately and first · `e9db66f2b`

**Diff (`:1001`).** `live == 0` FAILs ("empty: live=0 … the registry does not declare zero rows complete
(target_floor=…)") **whatever the build record says**.
- The one exception is where the registry declares zero rows complete (`target_floor=0`). That is the engine's own
  `zero_rows_is_complete` rule, and only there does the consistency check (R42) run, labelled "zero rows declared
  complete by target_floor=0".
- The old PASS branch "live=0 and rows_written=0 — consistent (empty by design or service)" is **removed**.

**Test.**
- `test_r52_emptying_a_table_never_reads_pass`, parametrised floor {None, 5, 164575} × rows_written {0, 8579}.
- `test_r52_the_truncate_plant_flips_toward_fail_never_toward_pass`: the `bg_muhurta_lattice` shape.
- `test_r52_zero_rows_pass_only_under_the_registry_declaration`: a declared-empty asset whose build wrote rows
  that are now gone still FAILs.

**Mutations.**
```
R52-M1 non-emptiness branch removed       7 failed — the 3 rows_written=0 cases + the before/after test on the
                                          VERDICT; the 3 rows_written=8579 cases on the text only (their
                                          verdict stays FAIL via the R42 comparison)
R52-M2 floor=0 declaration ignored        1 failed
after revert: 183 passed, 7 skipped
```

### R56 — parameterised / multi-table `count_sql` always yields a verdict · `416fe4574`

**Diff.** `Count.floor` grading is extracted to `_grade_count_floor()` (`:810`). Where a floor is declared and a
`count_sql` exists:
- an unmeasurable count (errored, unbound parameter, NULL) reads **ERRORED** "floor=N not measured" (it was
  silently absent);
- a constant reads NO_DETECTOR;
- otherwise the verdict is PASS/FAIL, with a multi-table total labelled `count_sql total=`.

**Test.**
- `test_r56_an_unmeasurable_parameterised_count_emits_errored_not_absent`.
- `test_r56_a_multi_table_chart_scoped_count_is_graded_against_the_floor`.
- `test_live_r56_the_differentials_three_breaches_are_reported` (live): ga_vargas, bo_laksana and ph_sankrama
  each read `Count.floor` FAIL.

**Mutations.**
```
R56-M1 errored count -> absent again            1 failed
R56-M2 chart binding removed (live)             5 failed (incl. the live three-breach test)
after revert: 185 passed, 8 skipped
```

**Live figures** (canonical chart; the differential's figures were sandbox whole-table counts):
- ga_vargas 0 < 22 092
- bo_laksana 50 529 < 60 000
- ph_sankrama 155 < 2 510

All three FAIL.

### R48 — `Count.floor` on every asset that declares `target_floor` · `d465d5a2c`

**Diff.** `_grade_count_floor()` returns `None` (criterion absent) **only** when no floor is declared. Otherwise:
- a declared floor with no `count_sql` reads NO_DETECTOR;
- a non-integer floor reads NO_DETECTOR;
- **`target_floor=0` reads N/A** "the registry declares zero rows complete — there is no floor to breach". This
  replaces a PASS on `live >= 0`, which could never read false (§N.8). It is a disclosed grading change: 5 live
  verdicts go PASS → N/A.

**Test.**
- `test_r48_a_declared_floor_without_a_count_sql_is_no_detector_not_absent`.
- `test_r48_a_zero_floor_is_a_declaration_not_a_vacuous_pass`.
- `test_r48_a_non_integer_floor_is_no_detector`.
- `test_r48_an_undeclared_floor_stays_absent`.
- `test_live_r48_every_l3_asset_declaring_a_floor_gets_a_verdict`.

**Mutations.**
```
R48-M1 declared floor + no count_sql -> absent        1 failed
R48-M2 zero floor -> vacuous PASS                     1 failed
R48-M3 L3 declared floors -> absent (live)            3 failed (incl. the live L3 test)
R48-M4 non-integer floor -> absent                    1 failed
after revert: 189 passed, 9 skipped
```

**Live coverage.** `Count.floor` is present on **121 of the 121** assets that declare a floor. Per layer:
L0 38/38, L1 19/19, L2 23/23, L3 19/19, L4 7/7, L5 15/15. It is absent on exactly the 6 that declare none
(bg ×2, ka_graha_sancara, ka_muhurta_seva, ph_pramana, ph_sodhana).

## §3 — Proof 1: every branch that can yield PASS or N/A

Scope: `asset_census.py` at `d465d5a2c`. `CLOSABLE = (PASS, NA)` at `:1211`. Label legend:
- **genuine** — the verdict rests on a measurement of exactly what it claims.
- **fixed in X** — the branch is now reachable only under a genuine measurement; the unmeasured way into it was
  removed in commit X.
- **not fixed** — the branch can close on something contested; it is named here, not dressed up.

Line numbers are at `d465d5a2c` (v1.0) except rows #5, #30–32 and #36, which give lines at the C1/C5 head.

| # | file:line | criterion — condition | label |
|---|---|---|---|
| 1 | `:288` | `Build.contract` PASS — the registered class subclasses WriterBase, has an entry point, no `ctx.db_conn.commit/close`, no `asset_throughput` write (AST) | **proxy (v1.1)** — genuine for literal class-body syntax only; an aliased `conn = ctx.db_conn; conn.commit()` or a module-level helper writing `asset_throughput` evades it (review A1; 0 live instances) |
| 2 | `:304` | `Idem.pattern` PASS — `ON CONFLICT` in the writer's own SQL strings (upsert layer) | **proxy (v1.1)** — text presence anywhere in the writer, not on the target table (review A2); deeper resolution is R20, W2-3 |
| 3 | `:307` | `Idem.pattern` PASS — `DELETE FROM` (delete-then-insert layers) | **proxy (v1.1)** — a DELETE on a sibling table passes (review A2; live shape bo_upaya, correct today by coincidence) |
| 4 | `:618` | `Build.history` PASS — cascade-blocked rows only, ≥1 completion (B1 C-4) | genuine |
| 5 | `:651` | `Build.history` PASS — no error/abort in the history, **≥1 completion** | **fixed in `1ae91dae4` (C1, v1.1)** — v1.0 labelled this genuine with a latent edge; the review showed 0 completions + 0 errors (only `queued` rows, 1 465 persist in finished runs) read PASS "0 complete". Now NO_DETECTOR with the reason. |
| 6 | `:703` | `Earn.build_record` N/A — never attempted | genuine per D6 **but unreachable from `measure()`** (`attempt_linkage_wired=False` at `:1045`; proven behaviourally by R225, `14f3f5d1c`) |
| 7 | `:706` | Earn N/A — healthy non-execution | as #6 |
| 8 | `:708` | Earn N/A — failed before completion | as #6 |
| 9 | `:713` | Earn PASS — completion write with a finite duration | as #6 |
| 10 | `:725` | `Cost.baseline` PASS — sanctioned baseline | as #6 |
| 11 | `:778` | `Build.contract` / `Idem.pattern` N/A — no writer and `has_writer=false` | **fixed in `61c6e637a`** (the `has_writer=true` way in now reads NO_DETECTOR `:771`; the raw scans' own N/A at 9baaa `:191`/`:227` is removed, `:259`/`:295`) |
| 12 | `:830` | `Count.floor` N/A — `target_floor=0` declaration | **fixed in `d465d5a2c`** (was a vacuous PASS at 9baaa `:811`) |
| 13 | `:845` | `Count.floor` PASS — live count ≥ floor, measured for the bound chart | **fixed in `416fe4574`** (with `58cf4c238`; the unmeasurable count is ERRORED, never absent) |
| 14 | `:890` | `Carr.detector` adopted verdict (PASS/N/A possible) — exit 0 and a verdict from the closed set only | genuine (wave-1 F8) |
| 15 | `:935` | `Build.registered` PASS — one `@register` and the registry agrees | genuine |
| 16 | `:943` | `Build.registered` N/A — no `@register` and `has_writer=false` | genuine (both sources agree; if both are wrong together, nothing can see it — R43 caveat) |
| 17 | `:951` | `Build.target` PASS — `target_table` declared | genuine (declaration; a declared-but-missing table FAILs `Complete.depth`) |
| 18 | `:953` | `Build.target` N/A — `asset_kind` non-empty or no writer | **not fixed — contested (R53, W2-2).** Genuine for a declared service or no writer (6 + 1 live). For `asset_kind='data'` **with a writer** (bg_prashna_rules, ga_strength, ga_structural) it is closable although the FAIL text describes exactly that case. No such gap is open in the production ledger (the emit closed 0). |
| 19 | `:959` | `Build.dag` PASS — "N edge(s), all resolvable" | **not fixed — measures in-layer (prefix) edges only**; cross-layer `depends_on` entries are never resolved, and the `missing` list at `:957` is computed and unused. OS-2, no row. |
| 20 | `:965` | `Build.count_integrity` PASS — `count_sql` and `integrity_check_sql` both present | genuine (presence) |
| 21 | `:965` | `Build.count_integrity` N/A — no writer and no `count_sql` | genuine |
| 22 | `:991` | `Build.completion` N/A — no `count_sql`, and nothing is built (no writer, or a service with no target) | **fixed in `61c6e637a`** (9baaa `:782` read N/A "no count_sql" for a NULL-returning count too; a writer-backed data asset with no `count_sql` is now NO_DETECTOR) |
| 23 | `:1028` | `Build.completion` PASS — `rows_written == live`, completed build record, non-empty unless declared | **fixed in `cfa9f42c0` + `e9db66f2b`** (9baaa `:790` PASS with no comparison and `:788` PASS on 0/0 are removed; ERRORED/constant/no-record/state/empty are each separate non-closable branches). Residuals (v1.1): A5 — a declared-zero asset truncated can flip FAIL→PASS (§8 item 3); A7 — the constant guard is syntactic (`SELECT 15 … FROM t LIMIT 1` evades it). 0 live instances of either. |
| 24 | `:1067` | `Complete.depth` PASS — rows > 0 and no never-populated column | **fixed in `61c6e637a`** (9baaa `:820` PASS on an empty table) |
| 25 | `:1109` | `Vocab.identity` PASS — declared-key duplicate probe finds none, on a non-empty table | **fixed in `61c6e637a`** (vacuous PASS on 0 rows removed) — **proxy caveat (v1.1, review F7):** keys come from enforced `pg_constraint` u/p, so the probe can FAIL only through NULL key members; on L0 (no nullable key member) this PASS cannot read false. Pre-existing. |
| 26 | `:1129` | `Vocab.alias` PASS — every entity class has aliases (only computed when the table has rows) | genuine |
| 27 | `:1142` | `Ldgr.source_presence` PASS — citation column populated on all rows (rows > 0) | genuine |
| 28 | `:1157` | `Dens.served` N/A — a real scan found no referencing module | **fixed in `61c6e637a`** (9baaa `:887` read N/A for an unscanned, missing directory) |
| 29 | `:1157` | `Dens.served` PASS — ≥1 referencing module declares `density_contract` | **not fixed — grading contested and a proxy (OS-3):** PASS when **any** of N modules declares (**29** of 42 live PASS verdicts are partial — v1.0 said 31, wrong), and the declaration test is a substring match, so a comment mentioning `density_contract` counts (review A4; 0 live instances). No row. |
| 30 | `:1198` | `Build.exercised` N/A — never run (no `build_run_assets` row) and no writer | genuine |
| 31 | `:1199` | `Build.history` N/A — never run (`Build.exercised` owns it; it FAILs when there is a writer) | genuine delegation (A_REVIEW2 #12) |
| 32 | `:1213` | `Build.exercised` PASS — ≥1 **started** (`started_at IS NOT NULL`; "executed" means started — dispatched past the building flip, incl. skip_no_delta, probe-green and pre-writer-error attempts) `build_run_assets` row | **fixed in `1ae91dae4` (C1, v1.1)** — v1.0 labelled this genuine; it counted never-started `queued` rows (review A8: it would close the OPEN production gap `bg_sign_medical-Build.exercised`) |
| 33 | `:1174` | `Build.dep_liveness` PASS — every dependency has a `lit` build record | **not fixed — scope caveat:** `lit` on **any** chart (`hist["lit"]` is chart-agnostic) — registered R45 (W2-2) |
| 34 | `:1177` | `Build.dep_liveness` N/A — no declared dependencies | genuine |
| 35 | `:1211` | `CLOSABLE = (PASS, NA)` — the only closing allowlist; ERRORED/NOT_GENERIC/UNKNOWN/absent never close | genuine (wave-1, tested) |
| 36 | `:1208` | `Build.exercised` N/A — rows exist but none was ever started, and no writer (added by C1, `1ae91dae4`) | genuine, like #30 (v1.2; the writer-backed twin of this case reads FAIL) |

**Tally: 36 branches (v1.2; C1 added #36).**
- **19 genuine measurement:** #4, 6–10, 14–17, 20–21, 26–27, 30–31, 34–36. Of these, #6–10 are unreachable from
  `measure()` today.
- **10 fixed in a W2-1 commit:** #11, 12, 13, 22, 23, 24, 25 (with the F7 proxy caveat), 28, and — after the
  review — **#5 and #32 in `1ae91dae4` (C1)**.
- **3 proxies (measured, but a weaker signal than the label):** #1 (A1), #2, #3 (A2).
- **4 not fixed, contested:** #18 (R53), #19 (OS-2), #29 (OS-3, also a proxy per A4), #33 (R45 / review C2).

v1.0 read "23 genuine, 8 fixed, 4 not fixed" and put #1–3, #5 and #32 in "genuine"; the review's attacks A1, A2,
A3 and A8 disproved that for those five.

**Removed at HEAD — the 8 unmeasured → closable branches that existed at `9baaa307b`:**
- `:191`, `:227` — N/A "no writer file";
- `:782` — N/A "no count_sql" on a NULL count;
- `:788` — PASS on 0/0;
- `:790` — PASS with no comparison;
- `:811` — vacuous PASS on floor 0;
- `:820` — PASS on an empty table;
- `:887` — N/A on a missing caps dir.

The one silent-absence branch (`Count.floor` absent whenever `live is None`, `:809` at 9baaa) is also removed.

## §4 — Proof 2: full census, six layers, HEAD vs `9baaa307b`

**Method.**
- Read-only, `--out` to scratch, no `--emit-gaps`.
- HEAD ran in this checkout; `9baaa307b` ran in a temporary worktree under `<scratch>/w2-1/` (removed after).
- Per layer, 6 in parallel, `timeout 300` each. The base L2 run hit the 300 s cap once under load and was re-run
  alone (63 s).
- The diff script is `w2-1_evidence/diff_census.py`; its full output is `census_diff_9baaa307b_vs_head.txt`.

**Headline per layer** (FAIL · PARTIAL+NO_DETECTOR · ERRORED; population):

| layer | `9baaa307b` | HEAD | assets |
|---|---|---|---|
| L0 | 39 · 170 · 0 | 43 · 172 · 0 | 40 → 40 |
| L1 | 1 · 102 · **19** | 7 · 106 · 0 | 19 → 19 |
| L2 | 8 · 120 · **22** | 15 · 121 · 0 | 23 → 23 |
| L3 | 38 · 91 · **17** | 55 · 111 · 0 | 21 → 21 |
| L4 | 18 · 43 · **9** | 27 · 45 · 0 | 9 → 9 |
| L5 | 21 · 57 · **11** | 31 · 72 · 0 | **14 → 15** (`lel_events`) |
| all | ERRORED **78** | ERRORED **0** | 126 → **127** |

HEAD runtimes (six in parallel): L0 72 s, L1 181 s, L2 210 s, L3 154 s, L4 21 s, L5 22 s. Every run exited 2
(failures measured).

**Every per-asset verdict change, grouped by cause.** 223 changes; 0 were classed UNEXPLAINED by the diff script.

| cause | L0 | L1 | L2 | L3 | L4 | L5 | total |
|---|---|---|---|---|---|---|---|
| R231 bound — `Build.completion` ERRORED → PASS | · | 15 | 17 | 9 | 3 | 2 | 46 |
| R42 compared — ERRORED → FAIL (`rows_written` ≠ live) | · | 3 | 5 | · | 5 | · | 13 |
| R42 compared — PASS → FAIL (the old no-compare PASS) | 4 | · | · | · | · | · | 4 |
| R42 not a completed build — ERRORED → FAIL | · | · | · | 2 | · | 9 | 11 |
| R42 constant `count_sql` — PASS → NO_DETECTOR | · | · | 1 | · | · | · | 1 |
| R52 empty — ERRORED → FAIL | · | 1 | · | 6 | 1 | · | 8 |
| R231+R56 `Count.floor` absent → PASS | · | 16 | 17 | 8 | 4 | · | 45 |
| R231+R56 `Count.floor` absent → FAIL | · | 2 | 2 | 9 | 3 | · | 16 |
| R48 `Count.floor` absent → N/A (declared floor 0) | · | 1 | 3 | 2 | · | 11 | 17 |
| R48 `Count.floor` vacuous PASS → N/A (floor 0) | 1 | · | 1 | · | · | 3 | 5 |
| R222 N2 `Build.contract`/`Idem.pattern` N/A → NO_DETECTOR | · | · | · | 20 | 2 | 4 | 26 |
| R222 N5 `Complete.depth` PASS → NO_DETECTOR (empty table) | 1 | 2 | · | · | · | 4 | 7 |
| R222 N5 `Vocab.identity` PASS → NO_DETECTOR (empty table) | 1 | 2 | · | · | · | 4 | 7 |
| R224 `lel_events` newly measured (17 criteria) | · | · | · | · | · | 17 | 17 |
| **all** | **7** | **42** | **46** | **56** | **18** | **54** | **223** |

**The rows, by group.** The full per-row list, with the measured text, is in the evidence file.

- **R231 → PASS (46).** Each reads `rows_written=N = live=N (… chart 482012f1)`. Examples: ga_dashas
  483 870 = 483 870; bo_laksana 50 529 = 50 529; ka_taranga 92 412; ph_rectification 186 (a two-table total);
  ga_prashna and mi_abhilekha 0 = 0 under a declared floor of 0.
- **R42 compared → FAIL (13 + 4).** Disagreements between the build record and the live count. **v1.1 (C3-i):**
  at least bo_upaya and ga_condition are **basis mismatches** (the writer's tally covers different tables from
  the count query), not data disagreements; the others were not individually re-checked for basis:
  - L1: ga_condition 45 vs 2 970, ga_strength 13 715 vs 14 141, ga_structural 106 707 vs 102 037.
  - L2: bo_bimba 255 vs 385, bo_cdlm_summary 70 vs 5, bo_karanajala 864 vs 849, bo_sangati 535 vs 475,
    bo_upaya 240 vs 180.
  - L4: ph_muhurta 139 vs 134; ph_nimitta / ph_pramana / ph_suddha_sodhana 139 vs 4; ph_sankrama 2 510 vs 155.
  - L0: bg_cohort 10 000 vs 110 000, bg_formula_constants 10 vs 17, bg_medical_mappings 60 vs 21,
    bg_transit_rules 104 vs 76. At `9baaa307b` all four L0 cases read PASS through the no-compare branch.
- **R42 not a completed build (11).**
  - `state='error'`: ka_avadhi, ka_kshetra (1 183 134 vs 8 570 075), mi_adhilepa, mi_bhara, mi_bhavisya,
    mi_darshana, mi_gunanaka, mi_pariksha, mi_pramana, mi_sambandha.
  - `state='dormant'`: mi_sankalpa.
  - At `9baaa307b` these were ERRORED. Without the guard, 8 of them would read PASS: ka_avadhi and mi_adhilepa,
    mi_bhavisya, mi_darshana, mi_pariksha, mi_pramana, mi_sambandha on equal figures, and mi_sankalpa on 0 = 0
    under its declared floor of 0.
- **R42 constant (1).** bo_samvada `SELECT 0 AS count`.
- **R52 empty (8).** ga_vargas; ka_bhavishya_lekha, ka_gochara, ka_kala_darshana, ka_kalasutra, ka_sangam,
  ka_vighnakara (their canonical-chart tables are empty); ph_sodhana (no floor declared, 0 rows).
- **`Count.floor` FAIL (16).**
  - ga_vargas 0/22 092, ga_yoga 53/63, bo_laksana 50 529/60 000, bo_samskara 50 678/60 000.
  - ka_bhavishya_lekha, ka_gochara, ka_kala_darshana, ka_kalasutra, ka_sangam and ka_vighnakara read 0 against
    their floors. Also ka_kota_chakra 585/588, ka_kshetra 8 570 075/8 599 775, ka_moorti_nirnaya 71/72.
  - ph_nimitta 4/139, ph_sankrama 155/2 510, ph_suddha_sodhana 4/139.
- **R222 N2 (26 = 13 assets × 2 criteria).** Assets: ka_dasha_kala, ka_gochara_resonance, ka_kota_chakra,
  ka_kshetra, ka_moorti_nirnaya, ka_muhurta_seva, ka_sudarshana_varsha, ka_tithi_pravesha, ka_tulana,
  ka_vedha_gochara, ph_rectification, mi_bhara, mi_sankalpa. These are the constant-indirection writers (R43,
  W2-2). They read closable N/A at `9baaa307b` and now read NO_DETECTOR.
- **R222 N5 (7 + 7).** bg_sarvatobhadra_grid, ga_prashna, ga_vargas, mi_abhilekha, mi_sankalpa, mi_seva,
  mi_vistara. Their target tables are empty.
- **Verdict unchanged, text changed:**
  - L0 `Build.completion` ×36 (the chart/basis label);
  - L0 `Count.floor` ×12 ("count_sql total=" on multi-table);
  - L0 `Build.contract`/`Idem.pattern` ×4 (the N/A reason is now stated);
  - L3 ×4 and L5 ×3 `Build.completion` (the N/A reason is now stated).

## §5 — Proof 3: T1 planted suite

**What ran.** All 17 plants, twice: at HEAD and at `9baaa307b`, on the sandbox (`nikasha_sandbox`, local socket,
the harness's own DB; `default_transaction_read_only=off` there by design).
- Each run starts from a fresh clean baseline measured by the same code (L0 / L3 / L4).
- The harness is a scratch copy, `plant_w2.py`. Its diff is `w2-1_evidence/plant_w2.patch` (45 lines):
  - `ROOT` points at the scratch worktree, so code plants never touch this checkout;
  - outputs go to scratch;
  - the baselines are fresh;
  - one expectation changed for `build_completion_truncate`: from `FAIL->PASS (inverted)` (the recorded old
    behaviour) to `STAYS_FAIL` (after the truncation the check must read FAIL).
- Every plant was restored and verified (`restore_ok` 17/17 both runs). Both worktrees were `git status`-clean
  after.

| plant | `9baaa307b` | HEAD |
|---|---|---|
| vocab_identity (L4) | DET PASS→FAIL | DET PASS→FAIL |
| count_floor | DET PASS→FAIL | DET PASS→FAIL (+ same-asset `Build.completion` PASS→FAIL: 5 written vs 4 live, R42) |
| build_completion_rw0 | DET PASS→FAIL | DET PASS→FAIL |
| **build_completion_truncate** | **miss FAIL→PASS** "live=0 and rows_written=0 — consistent (empty by design or service)" | **DET FAIL→FAIL** "empty: live=0 (count_sql over the target table; global) and the registry does not declare zero rows complete (target_floor=164575); build record rows_written=0" |
| earn_cost_signal | obsolete (D6) — NO_DETECTOR→NO_DETECTOR | obsolete (D6) — NO_DETECTOR→NO_DETECTOR |
| build_dag | DET PASS→FAIL | DET PASS→FAIL |
| build_target_null | DET PASS→N/A (degraded by design, R53) | DET PASS→N/A |
| count_integrity | DET PASS→PARTIAL | DET PASS→PARTIAL |
| ldgr_source | DET PASS→PARTIAL | DET PASS→PARTIAL |
| vocab_alias | DET FAIL→FAIL (text sensitivity) | DET FAIL→FAIL |
| build_history | DET PASS→FAIL | DET PASS→FAIL |
| build_exercised | DET PASS→FAIL | DET PASS→FAIL |
| dep_liveness | DET PASS→FAIL | DET PASS→FAIL, collateral 1 (below) |
| build_registered | DET PASS→FAIL | DET PASS→FAIL |
| build_contract | DET PASS→FAIL | DET PASS→FAIL |
| idem_pattern | DET PASS→PARTIAL | DET PASS→PARTIAL |
| dens_served | DET N/A→FAIL | DET N/A→FAIL |
| **detected** (applicable plants) | **15/16** | **16/16** |
| awaiting re-specification (`earn_cost_signal`, R55 / OS-11) | 1 | 1 |

**Notes on the results.**
- **The TRUNCATE plant now FAILs.** Its same-asset effects at HEAD: `Complete.depth` PASS→NO_DETECTOR and
  `Vocab.identity` PASS→NO_DETECTOR (R222 N5), and `Ldgr.source_presence` absent. At `9baaa307b` depth stayed
  **PASS** on the emptied table, which is the N5 defect.
- **`earn_cost_signal` is not applicable at either commit, by design** (v1.1 wording, per review §4(d); v1.0 called it a "miss"). Since wave-1 D6, Earn/Cost do not read
  `rows_per_second` at all (NO_DETECTOR, instrument absent), so this plant tests a signal that no longer exists.
  It needs re-specifying under R55 (OS-11).
- **`dep_liveness` collateral at HEAD** is `bg_ghatana/Build.completion PASS→FAIL`. The plant sets
  **bg_ghatana's own** build record to `state='error'`, and R42's completed-state guard reads that record
  correctly. It is a true detection on the planted fact, not noise. At base the harness saw 0 collateral.

**What could and could not run:** everything ran. No plant needed production.

## §6 — Proof 4: `--emit-gaps` dry run on a ledger copy

**Command.** For each of `L0`–`L5`, run under `NIKASHA_CONTROL_DIR=<scratch>/w2-1/ctrl_emit` (a copy of the
263-line production ledger, md5 `30365ff2…`):
```
timeout 300 python3 platform/scripts/governance/asset_census.py --layer <L> --emit-gaps --out <scratch>
```
The layers ran sequentially, so there were no concurrent appends. Log: `w2-1_evidence/emit_dry_run.log`.

```
L0  ledger: 6 row(s) appended, 209 already present, 0 closed by measurement, 0 re-opened
L1  ledger: 113 row(s) appended, 0 already present, 0 closed by measurement, 0 re-opened
L2  ledger: 136 row(s) appended, 0 already present, 0 closed by measurement, 0 re-opened
L3  ledger: 166 row(s) appended, 0 already present, 0 closed by measurement, 0 re-opened
L4  ledger:  72 row(s) appended, 0 already present, 0 closed by measurement, 0 re-opened
L5  ledger: 103 row(s) appended, 0 already present, 0 closed by measurement, 0 re-opened
```

**Transitions by type:**
- **OPEN (new): 596.** By criterion: Build.completion 38, Build.contract 13, Build.count_integrity 4,
  Build.dep_liveness 27, Build.history 83, Build.registered 13, Carr.detector 87, Complete.depth 51,
  Cost.baseline 87, Count.floor 16, Dens.served 35, Earn.build_record 87, Idem.pattern 48, Vocab.identity 7.
- **CLOSED: 0. RE-OPENED: 0.** Already present, still failing: 209 (all L0).
- The 6 new L0 rows are:
  - the 4 R42 `Build.completion` disagreements (bg_cohort, bg_formula_constants, bg_medical_mappings,
    bg_transit_rules);
  - bg_sarvatobhadra_grid `Complete.depth` and `Vocab.identity` (N5).

**Closure check** (`w2-1_evidence/check_emit.py`, output `emit_closure_check.out`):
- **CLOSED rows lacking a genuine PASS / justified N/A: none.** There are no CLOSED rows, so this check is met
  vacuously.
- The stronger, non-vacuous check covers **every closable verdict the census emitted**, on all 127 assets. Every
  N/A is in the justified set except **3**: `Build.target` for bg_prashna_rules, ga_strength and ga_structural
  (the contested R53 branch, #18).
- The N/A distribution: Build.completion 6 (declared services); Build.contract / Idem.pattern /
  Build.registered 5 each (`has_writer=false`); count_integrity 2; dep_liveness 28; exercised 5; history 6;
  Build.target 6 service + 4 data; Count.floor 23 (floor 0); Dens.served 26 (scanned, no module).

**Idempotency.** Re-emitting the same six census documents onto the copy (`ac.emit_gaps(census)`) gives
`(0, N, 0, 0)` per layer, and the ledger copy is **byte-identical** after it (`cmp`).

**Production ledgers are untouched:** md5 is unchanged, and they hold 0 CLOSED rows before and after.

## §7 — Governance suite, fingerprint, drift

| run | result |
|---|---|
| offline, `9baaa307b` (worktree) | 171 passed · 5 skipped · **2 failed** (178) |
| offline, HEAD | 208 passed · 9 skipped · **2 failed** (219; +41 new in `test_w2_1_earned_verdicts.py`) |
| live, HEAD (3 invocations under the 300 s cap) | 215 passed + 2 failed in 99.9 s; `test_live_e2e_one_simulated_query_timeout_degrades_not_aborts` 1 passed in 43.9 s; `test_live_e2e_depth_census_failure_does_not_blind_identity_for_the_same_asset` 1 passed in 121.5 s → **217 passed, 2 failed, 0 skipped** |
| engine conformance (`test_a4_d6_engine_conformance.py`) | 13/13 |

**Pre-existing failures, identical at `9baaa307b`:**
- `test_drift_detector_h35_h38.py::test_f163_current_row_flagged_predecessor_row_is_not`
- `test_drift_detector_h35_h38.py::test_h35_critical_when_canonical_artifacts_missing`

Both fail offline in the `9baaa307b` worktree, before any W2-1 change. They are outside the Lane A files.

**Other checks.**
- `python3 platform/scripts/governance/manifest_fingerprint.py --check` → `entries: 141 (declared 141) …
  e33e8fe1a0d53545 … MATCH`. No touched file is manifest-registered.
- `timeout 600 python3 platform/scripts/governance/drift_detector.py` (with pgenv) → **exit 3**, 1 finding, LOW:
  "73 CHART_FACTS_SCHEMA.json categories not yet in DB (pending writers)".
  - It writes its report to the gitignored `00_ARCHITECTURE/drift_reports/`.

## §8 — Honest limits

1. **One chart per run (R231).** Every chart-scoped verdict is the canonical chart's. The other five charts
   are unmeasured, and the verdict says which chart it measured.
   - A global `count_sql` with only per-chart build rows (mi_seva) is compared with the bound chart's row, and
     labelled so.
   - R231 selects the record per `(chart, asset)`. It is not R44 ("latest row"); today there is exactly one row
     per `(chart_id, asset_id)` (verified live).
2. **R42 extensions beyond the literal row text** are disclosed: the completed-state guard and the constant
   guard. The mi_kula "truth FAIL" from handverify is **not** adopted, for the reasons in §2.
   - The engine's no-op-completion path makes `rows_written = count_sql`, a true self-comparison, and the
     census cannot see it (1 such event on record).
   - "target_table alone" is a **whole-table** count (all charts), shown as context next to a chart-scoped
     figure.
3. **R52 guarantee scope.** "Emptying never reads PASS" holds for every asset that does **not** declare
   `target_floor=0` (104 of the 127 active assets; 23 declare 0).
   - For a declared-zero asset whose build record also says 0, an emptied table is indistinguishable from a
     legitimate zero-row build. By the registry's declaration it is complete, and it reads PASS with that
     declaration named.
   - A declared-zero asset whose build wrote rows that are now gone still FAILs (`rows_written ≠ live`).
   - **v1.1 (C3-ii, review A5):** the other direction is possible. A declared-zero asset reading FAIL on
     "rows_written=0 against live>0" flips to **PASS** when its table is truncated (0 = 0 under the declaration).
     No live instance: no declared-zero asset is `lit` with rw=0 and live>0, and none of the 10 open production
     `Build.completion` gaps declares floor 0.
   - Mutation R52-M1: the three `rows_written=8579` parametrisations fail on text only. Their verdict stays FAIL
     through the R42 comparison.
4. **R223 limits.**
   - A timed-out **layer-wide** read still aborts the layer (fail-closed, exit 4).
   - After a batched count times out, the per-asset fallback may spend up to the client timeout per asset. That
     is a runtime risk, not a correctness one.
5. **R225.** Dropping the keyword at the call site is now harmless by construction (M3 survives by design). The
   classifier is still not **adopted**: attempt linkage (R42–R56 adapter, D6 item 5) is unwired, so Earn/Cost
   read NO_DETECTOR.
6. **R224.** The offline proof stub is text-keyed: it evaluates the predicate the census sent. The live test is
   the real-SQL proof.
7. **R48 grading change.** The 5 live `Count.floor` PASS → N/A (floor 0) are a deliberate §N.8 change, not a
   measurement change.
8. **R222.** The identity-on-empty and depth "no columns" branches are same-class additions beyond the four
   named paths.
9. **Proof 4 closure check is vacuous.** The emit dry run closed nothing, so "no unjustified CLOSED row" is met
   vacuously. The complementary check over every closable verdict is the substantive one, and it leaves 3
   contested (R53).
10. **Census runtime.** The HEAD L2 run took 210 s in parallel (it was 148 s at base), because it binds charts
    and measures more. The base L2 run hit the 300 s cap once under concurrent load and was re-run alone
    (63 s). Running six layers in parallel is near the cap on a loaded DB.

## §9 — Out-of-scope findings (listed, not fixed)

- **OS-1 / #18 (R53, W2-2).** `Build.target` N/A for `asset_kind='data'` with a writer and no `target_table` is
  closable: bg_prashna_rules, ga_strength, ga_structural.
- **OS-2 / #19 (no row).** `Build.dag` PASS "all resolvable" resolves only same-prefix edges.
  - Cross-layer `depends_on` entries, and any non-prefix in-layer id (`lel_events`), are never checked.
  - The `missing` list (`asset_census.py:957`) is dead code.
- **OS-3 / #29 (no row).** `Dens.served` PASS when ≥1 of N referencing modules declares `density_contract`.
  **29** live PASS verdicts are partial (v1.0 said 31; corrected per review §8 #19), `index.ts` /
  `coverage_matrix.ts` count as "modules", and a comment mentioning `density_contract` counts as a declaration (A4).
- **OS-4 / #5 — FIXED in v1.1 by C1 (`1ae91dae4`).** v1.0 listed this as latent with "0 live instances"; the
  review showed it is routinely reachable (1 465 persistent `queued` rows) and, with #32, closes a real open gap.
- **OS-5 (no row).** `lel_events` has `has_writer=false` and no build record will ever exist. It reads
  `Build.completion` FAIL "no build record at all" permanently, so the gap is not actionable. Criterion
  applicability for writerless data assets should be decided in the D4 criterion registry.
- **OS-6 (R45, registered).** `Build.dep_liveness` counts a dependency live if it is `lit` on any chart.
- **OS-7 (R43, registered).** 13 writer-backed L3/L4/L5 assets use `@register(ASSET_ID)`. The census does not
  recognise them, so `Build.registered` FAILs falsely and `Build.contract`/`Idem.pattern` now read NO_DETECTOR
  (they were a false closable N/A).
- **OS-8 (correction to A_REVIEW2 G2).** "None fires on today's production data" held for L0 only. The N2 path
  was **live** on L3/L4/L5 (those 13 assets). No production ledger row was ever closed by it, because no
  `--emit-gaps` had run on those layers.
- **OS-9 (data, not inspector).** The now-measured canonical chart shows build/data disagreements (§4; v1.1: the
  bo_upaya and ga_condition FAILs are basis mismatches, not data — C3-i):
  - six Kala tables are empty for the chart;
  - ph_nimitta / ph_pramana / ph_suddha_sodhana are at 139 → 4;
  - ka_kshetra 8 570 075 < floor 8 599 775;
  - ga_vargas has 0 `chart_divisionals` rows;
  - 10 L3/L5 assets have `state='error'` build records.
  These are findings for their owners, not census defects.
- **OS-10 (no row).** `registered_ids()` is still prefix-filtered (`rid.startswith(prefix)`). A writer
  registering a non-prefix id of the layer would be missed. There is no live instance; `lel_events` has no
  writer.
- **OS-11 (R55).** The T1 `earn_cost_signal` plant is obsolete since D6 and needs re-specifying against
  `duration_seconds` / attempt linkage.
- **OS-12 (process).** `drift_detector` writes an ad-hoc report into the gitignored
  `00_ARCHITECTURE/drift_reports/`, which is a repo-path write. It is harmless (ignored), and noted for the scope
  audit.

## §10 — Evidence index (`nikasha_test/wave2/w2-1_evidence/`)

- `mutation_runs.log` — every mutation run above, verbatim.
- `census_diff_9baaa307b_vs_head.txt`, `census_head_summary.log`, `census_9baaa307b_summary.log`,
  `diff_census.py`.
- `T1_RESULTS_head.json`, `T1_RESULTS_9baaa307b.json`, `plant_w2.patch`, `plants_run.sh`.
- `emit_dry_run.log`, `emit_closure_check.out`, `check_emit.py`.
- `mut.sh`.
- v1.1 (C1): `mutation_runs_C1.log`, `census_diff_d465d5a2c_vs_C1.txt`, `census_C1_summary.log`,
  `emit_dry_run_C1.log`, `emit_closure_check_C1.out`.

## §11 — Corrections after gate review (v1.1; `W2-1_REVIEW.md`, 8af39a194)

| item | what | commit | test | mutation evidence |
|---|---|---|---|---|
| **C1** | A never-started `build_run_assets` row (e.g. `queued`) no longer counts as a run; `Build.history` never PASSes at 0 completions | `1ae91dae4` | `test_c1_a_queued_only_asset_is_neither_exercised_nor_history_pass` (a); `test_c1_b_reviewer_reproduction_the_open_bg_sign_medical_gap_stays_open` (b); `test_c1_history_never_passes_with_zero_completions`; `test_c1_an_executed_row_still_exercises` (positive control) | M1 exercised counts rows → 2 fail (a, b); M2 zero-completion PASS restored → 3 fail; M3 `started_at` ignored → 3 fail; M4 both guards reverted → 3 fail (a, b, history); reverted, suite green (`mutation_runs_C1.log`) |
| **C3** | Report wording (this v1.1): (i) R42 basis mismatches; (ii) R52 A5 flip under floor 0; (iii) Dens.served 29 not 31; (iv) proxy labels #1/#2/#3/#25/#29, #5/#32 relabelled fixed, #23 residuals A5/A7, T1 as 16/16 + 1; (v) this section | this report commit | — (text) | — |
| **C4** | Tests pin C1's execution marker (W2-1_C1_REVIEW §7: mutations M2 state-list and M5 `ended_at` survived) | `b98fc92c7` (tests only) | `test_c4_a_unstarted_aborted_and_blocked_error_rows_do_not_exercise_or_close` (ledger COPY, gap stays OPEN); `test_c4_b_an_ended_but_never_started_row_is_not_executed`; `test_live_c4_executed_equals_the_started_at_count` (+ xfail(strict) twin documenting F-C4) | C4-M2 executed = state in {complete, error, aborted} → 3 fail (a, b, live); C4-M5 `(a.ended_at IS NOT NULL)` → 3 fail (a, b, live); reverted, suite green (`mutation_runs_C4.log`) |
| **C5** | Wording (this v1.2): both `started_at` sites named (report §11 and the `build_history()` docstring — a text-only change in `asset_census.py`); executed = started stated; #36 added (36 branches, 19 genuine); R42 heading; `earn_cost_signal` obsolete, not a miss; C1-M4 re-run with **both** guards reverted (appended to `mutation_runs_C1.log`: 4 failed — c1_a, c1_history, c1_b, c4_a — then restored byte-identical; the original M4 entry is annotated as not evidencing it) | this report commit | — (text) | — |

### C1 — the executed-state set, and why

**Chosen: an attempt is executed iff `build_run_assets.started_at IS NOT NULL`, not a list of states.**

- **Engine.** `started_at` is set at **two** sites, both meaning "this attempt was started in state
  `'building'`" (v1.2; v1.1 wrongly said "exactly one site"): `asset_runner.py:1403` (the orchestrator's
  `'building'` transition, `INSERT INTO build_run_assets … VALUES (…, 'building', NOW()) ON CONFLICT … SET
  state='building', started_at=NOW()`) and `run_heavy_writer_standalone.py:137` (the standalone heavy-writer
  runner, `INSERT … VALUES (…, 'building', NOW())`). **"Executed" throughout C1 means *started*** — dispatched
  past the building flip — so it includes `skip_no_delta`, probe-green and pre-writer-error attempts, not only
  writer runs. Rows that never reach either site keep `started_at` NULL whatever their terminal state:
  - `queued` leftovers in finished runs;
  - `aborted` rows terminalised straight from `queued` (`runner.py` `_terminalize_preflight_failure`,
    guardian cleanup, manual reaps);
  - `error` rows written by `_mark_asset_blocked` ("BLOCKED: … The asset is NOT executed").
- **Data** (live, read-only, 2026-09-27), `state: rows (started)`:
  - `complete` 3 133 (3 133), including `skip_no_delta` 61 (61) and `build` 150 (150);
  - `error` 1 515 (**319**);
  - `aborted` 649 (**8**);
  - `queued` 1 465 (**0**);
  - `building` / `skipped` 0.
- **So the coordinator's candidate set {complete, error, aborted} would still count 1 837 never-started rows**
  (1 196 BLOCKED/unstarted errors plus 641 unstarted aborts) as runs. `started_at` is the engine's own marker
  and matches every observed state exactly (every `complete` row is started; no `queued` row is).
- `skip_no_delta` rows count as executed. The engine started the asset and decided no delta; they are
  `complete` with `started_at` set.

**Zero completions → NO_DETECTOR, not FAIL.** With 0 completions and 0 errors or aborts, no attempt reached an
outcome, so there is nothing to grade: "no error" is the absence of a measurement. NO_DETECTOR is non-closable
and opens a gap, with the reason and the per-state row counts in `measured`.
- The *missing execution* itself is `Build.exercised`'s finding. It reads **FAIL** when rows exist but none
  started ("registered with a writer and the orchestrator has NEVER executed it: N build_run_assets row(s),
  none ever started (states: …)"), or N/A only when the asset has no writer.
- The delegating N/A (#31) was **not** reused for this case, because N/A would close a gap too.
- History tallies are otherwise unchanged. Unstarted BLOCKED/aborted rows still weigh on `Build.history` in the
  fail-safe direction; re-attributing them is B1/R49 territory and was not touched.

**Census re-run** (six layers, read-only, HEAD `1ae91dae4`, `census_C1_summary.log`): FAIL · PARTIAL+NO_DET ·
ERRORED = L0 43·172·0, L1 7·106·0, L2 15·121·0, L3 55·111·0, L4 27·45·0, L5 31·72·0.
- **Verdicts moved by C1: 0** (`census_diff_d465d5a2c_vs_C1.txt`). No asset today has only never-started rows,
  so C1 closes a *reachable* path (A8), not a live verdict.
- Text-only changes: `Build.exercised` on every exercised asset (121) now states "N executed run(s) of M
  build_run_assets row(s)". **97 of them carry unstarted rows beside the executed ones** (L0 11, L1 19, L2 23,
  L3 21, L4 9, L5 14), each of which the v1.0 count included.

**Emit dry run** (fresh copy of the production ledger, six layers sequentially, CLI `--emit-gaps`,
`emit_dry_run_C1.log`):
- 596 OPEN appended (per layer 6 / 113 / 136 / 166 / 72 / 103), 209 already present, **0 CLOSED, 0 RE-OPENED**.
- Criterion counts are identical to v1.0 §6.
- The re-emit gives `(0, N, 0, 0)` per layer and a byte-identical ledger copy.
- `bg_sign_medical-Build.exercised` stays OPEN.
- Production ledgers md5 `30365ff2…` / `514cbdfc…`, unchanged.

**Suite.** Offline governance suite **212 passed, 9 skipped, 2 failed** (223; +4 C1 tests). The 2 failures are
the same pre-existing `test_drift_detector_h35_h38.py` pair. Live: `test_w2_1_earned_verdicts.py` +
`test_b1_…` 53 passed.

### Gate-review findings carried (listed here; the executor registers them at the fold — not registered by the builder)

- **C2 — `Build.dep_liveness` PASS on `lit` on *any* chart.** Live on 10 assets whose dependency is `stale` on the
  canonical chart and `lit` only on 1c826d5a: bo_anveshana, bo_chart_gestalt, bo_pramana_mapa, bo_samvada,
  bo_upaya, bo_yantra_mechanism, ka_avadhi, ka_kshetra, ka_sangam, ka_yojaka. **Blocks any production emit after
  the first** (closures of dep_liveness gaps) until R45 (W2-2) lands. It does not block the first emit, which
  only appends.
- **F4 — register rows missing** for:
  - OS-2 (`Build.dag` cross-layer blindness; dead `missing` list);
  - OS-3 (`Dens.served` ≥1-of-N and substring match, A4);
  - A1 (contract scan misses an aliased commit and module-level helpers);
  - A2 (Idem proxy; near R20);
  - A7 (constant guard is syntactic).
- **F5 — `Build.target` FAIL is dead** (`asset_kind` NOT NULL CHECK). The 3 data-with-writer N/As can never be
  opened; R53 (W2-2). Not a closure risk.
- **F6 — scope mismatch.** Depth, identity, alias and Ldgr measure whole tables while `Build.completion` is
  chart-scoped. For example, ka_bhavishya_lekha Ldgr PASS on other charts' rows beside Build.completion FAIL
  empty. Belongs to the D4 criterion registry.
- **F7 — `Vocab.identity` can fail only through NULL key members** under an enforced declared key. On L0 its PASS
  cannot read false. Pre-existing; D4 registry.
- **F8 — `ka_gochara` registry data.** The `count_sql` and `target_table` name `kala_gochara_windows` (v1,
  frozen), while the writer targets `kala_gochara_windows_v2`, so its "empty" FAIL measures the wrong table.
  For the owner.

**R222 precondition.** C1 is the only correction the review bound to the first production `--emit-gaps`. With
`1ae91dae4` it is proposed as met, **subject to the C1 re-gate**. The builder does not declare it met.


### v1.2 — found while pinning C1 (C4), listed, not fixed

- **F-C4 — `build_history()` splits rows on newlines in `error`.** The read selects `left(a.error,200)` raw. An
  error text containing a newline (Python tracebacks) splits one psql row into several lines:
  - that row's `started_at` flag is lost, so `executed` is undercounted (fail-safe for `Build.exercised`);
  - traceback fragments appear as phantom per-asset keys in `hist["per"]` (ignored by `measure()`, which only
    reads registry ids);
  - the split row's `sample_error` is truncated.
  Live 2026-09-27: 57 rows across 29 assets; ph_sodhana reads executed 39 against 41 started. Pinned by
  `test_live_c4_executed_equals_the_started_at_count_over_all_rows` (`xfail(strict=True)`, so it fails the day
  the read becomes newline-safe). C4 was scoped tests-only, so the code is **not** changed. The fix is one
  `replace(…, E'\n', ' ')` in the SELECT; it is for the executor to register (same defect class as `registry()`'s
  json_agg note).
- The C1 re-gate's other carried items (C2 dep_liveness any-chart, F-S1 Dens.served comment match, F-L1
  complete-but-unstarted, F-P1 B1 "latest run complete" text) are listed in `W2-1_C1_REVIEW.md` §7 for the fold.
  They are not registered or fixed here.

**Suite at v1.2:**
- Offline governance suite: **214 passed, 11 skipped, 2 failed** (227). The 2 failures are the pre-existing
  `test_drift_detector_h35_h38.py` pair.
- Live `test_w2_1_earned_verdicts.py`: 48 passed + 1 xfailed.
