---
artifact: NIKASHA_WAVE1_LANE_A_REVIEW_2
reviewer: Opus gate review 2 (fresh context, read-only, not the implementer)
reviewed_on: 2026-09-27
prior_review: 00_ARCHITECTURE/briefs/nirmana/nikasha_test/wave1/A_REVIEW.md (8a57a3320, REJECT narrow, F1–F12)
packet_commits:
  - a77d50005   # F1
  - 065e620b2   # F2
  - cf955e3a3   # F3
  - 3a9c66cf9   # F4
  - cbc8b6724   # F5 (Lane A hunks only; 5 swept Lane B files accepted in B_REVIEW5)
  - 6574d729b   # F6
  - 0c16969a3   # F7
  - 64af00534   # F7 test stub
  - e4505eafc   # F8
  - 705d20058   # F9
  - 8ef861e0b   # F11
  - afa1d4146   # F12
  - 7352ba484   # A_REPORT.md v1.1 (F10)
head_reviewed: 7352ba484
verdict: ACCEPT_WITH_CORRECTIONS
---

# Nikaṣa wave 1 · Lane A · gate review 2

## §1 — Verdict

**ACCEPT_WITH_CORRECTIONS.**

**What holds.** Both false-closure paths from review 1 are closed in code, and I confirmed it live:
- **F1:** with the instrument simulated present, all 40 L0 assets read `NO_DETECTOR — attempt linkage not wired` for
  both Earn and Cost. `emit_gaps` on a copy of the production ledger closed **0** of the 40 open `Earn.build_record`
  gaps.
- **F2:** `bg_ephemeris`'s `count_sql` was made to raise. It reads ERRORED, and its open `Build.completion` gap stays
  OPEN.

The rest:
- F4–F9, F11 and F12 each have a test that I could make fail with a mutation.
- F3's M8 now fails offline. M9 fails live only, which is disclosed.
- L0 at HEAD vs `7ed870775`: **0 verdict flips**, and the only text change is `Vocab.identity` on 37 assets.
- The T3 cycle re-runs exactly as A_REPORT §12 states.
- The production ledgers are byte-identical to `8a57a3320`.
- No untouchable path moved.

**What does not fully hold (corrections, §7).**
- **G1 — the F1 fix's call site has no failable proof.** If `attempt_linkage_wired=False` is dropped from the
  `measure()` call, **no test fails, offline or live.** The only guard is a source-text test. The same string appears
  in a comment inside `measure()`, so that test cannot fail. The parameter also defaults to the unsafe value (`True`).
  This is the F3 defect class, re-introduced inside the F1 correction. It is latent until migration 1094 lands.
- **G2 — the defect class has further instances.** An unmeasured check can still grade a closable N/A (or PASS)
  through three more branches. I demonstrated them live on a ledger copy: **26 false closures in one run.** None is
  triggered by production data or code today. All three are pre-existing grading branches that A-2's closure loop
  newly turns into ledger closures.
- **G3–G7:** R41 does not isolate real timeouts; three honesty gaps in A_REPORT; a census/tracker population mismatch
  of one asset; and advisory hygiene items.

None of G1–G7 produces a false closure on the production ledger today. Each is bound to the event that would arm it
(§7). That is why this is ACCEPT_WITH_CORRECTIONS and not REJECT.

## §2 — The two false-closure paths, attacked; and every N/A branch

### F1 — the D6 path that is not wired

**Live, read-only.** I ran the unmodified HEAD `measure("L0")` against production, with `duration_instrument_present`
forced to True to simulate migration 1094 applied. `emit_gaps` wrote into a scratch copy of the production ledger.

```
Earn.build_record: {'NO_DETECTOR | NO_DETECTOR — attempt linkage not wired': 40}
Cost.baseline:     {'NO_DETECTOR': 40}
emit: (0, 208, 0, 0)   appended rows: 0   CLOSED: {}
```
The ledger had 40 open `Earn.build_record` gaps, and none closed. Review 1's simulation closed 40.

**Mutations:**

| mutation | offline | live |
|---|---|---|
| F1a: guard removed (`if attempt is None and not attempt_linkage_wired` → `if False`) | caught, 2 tests (grading + emit_gaps) | — |
| **F1b: call site drops `attempt_linkage_wired=False`** (default `True` applies) | **nothing** | **nothing** |

F1b survives because of how `test_case_attempt_linkage_unwired_is_the_default_measure_call_shape` works:
- It asserts the substring `attempt_linkage_wired=False` is in `inspect.getsource(ac.measure)`.
- That substring is also in the comment at `asset_census.py:798`.
- No test runs `measure()` with the instrument present. `_stub_layer` pins `duration_instrument_present` to False.

This is **G1**.

### F2 — an errored `count_sql`

**Live.** In the same run, `bg_ephemeris.count_sql` was replaced with a query on a relation that does not exist:
```
bg_ephemeris Build.completion: {'v': 'ERRORED', 'measured': 'check errored: ERROR:  relation "nikasha_review_no_such_relation" does not exist'}
```
The open `bg_ephemeris-Build.completion` gap was not closed. The skipped count fell from 209 to 208 because ERRORED
neither opens nor skips.

**Mutations:**
- F2a, the ERRORED branch in `measure()` removed:
  - offline: survives;
  - live: caught by `test_live_e2e_a_broken_count_sql_grades_errored_not_na`.
- F2b, `errored[aid]` never recorded: caught offline by `test_live_counts_distinguishes_errored_query_from_no_count_sql`.

F2's effect on `measure()` is therefore proven live only. This is the same shape as M9. The ruling in §3 applies to
it too.

### Every N/A-producing branch in `asset_census.py` (HEAD `7352ba484`)

`CLOSABLE = (PASS, NA)` (`:937`). For each branch: is it a genuine N/A, or an absence of measurement?

| # | line | criterion / condition | genuine or absence | evidence |
|---|---|---|---|---|
| 1 | `:191` | `Build.contract` N/A "no writer file". The `files` list is empty. | Genuine when the registry also says `has_writer=false`. **Absence when `has_writer=true`**: the writer exists but `@register` was not recognised, so the contract scan never ran. | **N2, demonstrated.** `registered_ids` stops recognising `bg_reference`. Result: `Build.registered` FAIL (opens), `Build.contract` N/A, `Idem.pattern` N/A → **`bg_reference-Idem.pattern` CLOSED** "no writer file". |
| 2 | `:227` | `Idem.pattern` N/A "no writer file" | Same as #1. | Same run. |
| 3 | `:563` | `Earn.build_record` N/A "never attempted" | Genuine once attempt linkage is wired (the query found no row). **Unreachable today** (`measure()` passes `False`), but the only thing keeping it unreachable is G1. | F1 above. |
| 4 | `:566` | `Earn` N/A "healthy non-execution" | Genuine per D6 item 3. Unreachable today. | engine suite |
| 5 | `:568` | `Earn` N/A "attempt … before completion" | Genuine per D6 item 3 (`Build.history` owns the failure). Unreachable today. | engine suite |
| 6 | `:748` | `Build.registered` N/A: no `@register` found and the registry agrees | Genuine; both sources agree. | — |
| 7 | `:758` | `Build.target` N/A: `asset_kind` is non-empty **or** there is no writer | Genuine for services with no writer. Questionable for `asset_kind='data'` with a writer and no `target_table`: the code's own FAIL text describes exactly that case. Live instance: `bg_prashna_rules` (registry-wide also `ga_structural`, `ga_strength`). | advisory, G7 |
| 8 | `:770` | `Build.count_integrity` N/A: no writer and no `count_sql` | Genuine. | — |
| 9 | `:782` | `Build.completion` N/A "no count_sql" | Genuine when `count_sql` is empty. **Absence when `count_sql` exists but returns NULL or a non-integer** (`:350`, `:356` map it to `None` without recording an error), and then the text "no count_sql" is false. | **N1, demonstrated.** With `bg_ontology.count_sql = SELECT NULL::bigint`, the verdict is N/A "no count_sql" → **`bg_ontology-Build.completion` CLOSED**. Production today: 0 assets on any layer return NULL (scanned L0–L5). |
| 10 | `:887` | `Dens.served` N/A: no capability module matched | Genuine only if the capability directory exists. **Absence when it is missing**: `capability_scan` returns `modules=[]` with the note "no capability directory" (`:248`). | **N3, demonstrated.** With the L0 caps dir pointed at a missing path, **all 24 open `Dens.served` gaps CLOSED**. |
| 11 | `:894` | `Build.exercised` N/A: never run, no writer | Genuine. | — |
| 12 | `:897` | `Build.history` N/A "never run; check 7 owns this" | Genuine delegation: `Build.exercised` FAILs when there is a writer. | — |
| 13 | `:907` | `Build.dep_liveness` N/A: no declared dependencies | Genuine. | — |
| 14 | `:656` | `Carr.detector` N/A adopted from a detector | Genuine after F8: only exit 0 with a verdict from the closed set is adopted. | F8 mutations |

**A PASS reached the same way** (not an N/A branch, but the same class): `Complete.depth` reads **PASS "table empty"**
when the target table has 0 rows (`:612` → `:820`, because `never=[]`).
- Live today: `bg_sarvatobhadra_grid` reads PASS on 0 rows.
- It closes nothing today because no `Complete.depth` gap exists for that id.
- A table with an open depth gap that is truncated to 0 rows would close it. This is **N5**.

**Whole attack run** (one live L0 census, faults N1 + N2 + N3 injected, ledger copy):
`emit (1, 182, 26, 0)` → CLOSED `{'Dens.served': 24, 'Build.completion': 1, 'Idem.pattern': 1}`. The control
run without the new faults gave `(0, 208, 0, 0)`. **Result: further false-closure paths exist (G2).**

**Non-closure paths checked.**
- **Timeouts (G3).**
  - `psql()` does not convert `subprocess.TimeoutExpired`. I showed `ac.psql("SELECT pg_sleep(3)", timeout=1)`
    raises `TimeoutExpired`, which is not an `Unknown`.
  - Production's `statement_timeout` is **30 min**, above the census's 180 s client timeout. So a real timeout always
    arrives as `TimeoutExpired`, escapes every per-check `except Unknown`, and ends the run with exit 5.
  - That is fail-closed and never a closure. But R41's stated claim ("a per-check exception (timeout …) degrades to
    ERRORED", `:87`) is false for the real mechanism. The R41 tests simulate a timeout by raising `Unknown`.
- **ERRORED, NOT_GENERIC, UNKNOWN strings, and absent criteria:** none of them closes (M10 caught; unchanged from
  review 1).

## §3 — F3 to F12

Mutations were run in a scratch `git worktree` at HEAD outside the repo (since removed). Offline means the PG
environment is unset. Live means read-only production, `default_transaction_read_only = on`.

| # | mutation | offline | live | matches A_REPORT §10? |
|---|---|---|---|---|
| F3 / M8 | `_measure_contract` re-raises | caught (`test_contract_scan_exception_degrades_to_errored_not_layer_abort`) | caught | yes |
| F3 / M8b | `_measure_idem` re-raises | caught (`test_idem_scan_…`) | — | (not listed; consistent) |
| F3 / M9 | R220 filter → `is_active AND NOT dead_flag` | **survives** (71 passed, 4 skipped) | caught by 4 live tests, including `test_live_registry_l3_excludes_the_two_retired_rows` | yes, disclosed |
| F4 | `elif prior_state == "CLOSED"` → `elif True` | caught (`test_case_withdrawn_is_terminal_never_reopened`) | — | yes |
| F5 | superseded check reverted to latest-row-only | caught (`test_case4b_…`) | — | yes |
| F6 | tracker predicate → `TRUE`; → `is_active AND NOT dead_flag` | both caught (SQLite runs the real SQL) | — | yes |
| F7 | `if not out and total == 0` | caught (2 tests) | — | yes |
| F8 | return-code check off; vocabulary check off | each caught | — | yes |
| F9 | figure dropped | caught | — | yes |
| F11 | census probe loses `table_schema` | caught (engine test) | — | yes |
| F12 | `_layer_read` stops naming the read | caught | — | yes |
| M10 | `CLOSABLE += ERRORED` | caught | — | (review 1) |

**Ruling on the offline-only gaps (M9, F2a): non-blocking.**
- M9 cannot produce a false closure. Since F7, a zero-active population raises `Unknown` → exit 4, so the defect
  announces itself at runtime.
- F2a is caught by the live suite. The live suite is the gate's instrument for this lane.

Both should gain a stubbed-`psql` offline twin before the suite is relied on in a DB-less CI. That is advisory.

**F4 and F5 on a copy of the production ledger** (263 lines plus the constructed rows, gap
`bg_ontology-Idem.pattern`, which is OPEN in production):

| case | emit | appended |
|---|---|---|
| WITHDRAWN latest, FAIL / NO_DETECTOR / PASS / lower-case `withdrawn` | (0,1,0,0) / (0,1,0,0) / (0,0,0,0) / (0,1,0,0) | nothing |
| control: CLOSED latest, FAIL | (0,0,0,1) | RE-OPENED |
| superseded, then a later plain OPEN, PASS | (0,0,0,0) | nothing |
| superseded, then a later plain CLOSED, FAIL | (0,0,0,0) | nothing |
| superseded → plain OPEN → WITHDRAWN, FAIL | (0,0,0,0) | nothing |
| `superseded_by: ""` (empty), then plain, PASS | (0,0,1,0) | CLOSED (an empty flag names no successor; acceptable) |

WITHDRAWN is terminal. `superseded_by` is permanent across a gap_id's history.

**F11 (engine suite).**
- `test_a4_d6_engine_conformance.py`: **13 passed at `8edba0533`, and 13 passed at engine HEAD `e5dd65b8f`**.
  `asset_runner.py` is identical between the two.
- With `NIKASHA_ENGINE_DIR=/nonexistent` all 13 skip, with the reason stated.
- It reads the engine only with `git show`. The engine worktree's `git status` is unchanged by the run.

**Is "D6 item 5 PARTLY met" honest?** Yes, and it is precise. What cannot be tested without migration 1094 applied:
- the engine's write paths (`_run_data_writer`, `_skip_no_delta`, `_mark_probe_green`, `mark_asset_error`,
  `_telemetry.update_asset_throughput`) actually producing `build_run_assets` + `asset_throughput.duration_seconds`
  rows;
- an adapter (R42–R56, not yet written) turning those real rows into the classifier's attempt dict;
- and those real rows being graded.

The suite pins each path's SQL and runs the engine's pure arithmetic from its own source. But the attempt dicts it
grades are hand-built to what an adapter *would* produce. The test header and A_REPORT §10 say exactly this. The
`probe_green` adapter obligation (the engine writes no such disposition) is a real finding, correctly routed to
R42–R56.

**F12 — is the R41 limit disclosed where a reader will see it?** Yes, in three places:
- the `measure()` docstring;
- the runtime message whenever a layer-wide read aborts ("R41 isolates per-asset checks only …");
- A_REPORT §10.

The merge-order limit is in the `emit_gaps` docstring. Two gaps remain:
- The disclosure does not cover G3: the per-asset checks are not isolated from real timeouts either.
- Under a multi-layer `--emit-gaps` run, the abort message says "no census file written", but it does not say that
  earlier layers' ledger rows were already appended. `emit_gaps` runs per layer inside the loop.

## §4 — Regression

**L0 census, live and read-only.** HEAD in this checkout; `7ed870775` in a temporary worktree (removed). Both
`--out` to scratch, no `--emit-gaps`.

| | `7ed870775` | HEAD `7352ba484` |
|---|---|---|
| runtime / exit | 72 s / 2 | 76 s / 2 |
| assets | 40 | 40 (same set) |
| FAIL · PARTIAL/NO_DETECTOR · ERRORED | 39 · 170 · 0 | 39 · 170 · 0 |
| tally | PASS 413 · PARTIAL 50 · NO_DETECTOR 120 · FAIL 39 · NOT_GENERIC 80 · N/A 68 | identical |

- Verdict flips: **none**.
- Criteria present on one side only: none.
- Text changes: **`Vocab.identity` on 37 assets only**, "no duplicates" → "0 duplicate(s)".

**Outside L0 — a real change the report does not state (G4).** F2 changes verdicts on L1–L5, because 78 of 86
L1–L5 `count_sql` are chart-scoped (`$1`) and cannot run standalone. Their `Build.completion` moved from the
closable, false N/A "no count_sql" to ERRORED:

| layer | assets now ERRORED on `Build.completion` |
|---|---|
| L1 | 19/19 |
| L2 | 22/23 |
| L3 | 17/21 |
| L4 | 9/9 |
| L5 | 11/14 |

- **The fix is correct.** Before it, `--emit-gaps` on those layers would have closed any open `Build.completion`
  gap.
- **The consequence:** `Build.completion` is now unmeasured on those 78 assets until the census binds a chart scope.
- The live L3 census at HEAD reads `FAIL 38 · PARTIAL/NO_DETECTOR 91 · ERRORED 17`, in 79 s, 21 of 23 active.

**T3 cycle, live, on a ledger copy.** `NIKASHA_CONTROL_DIR` pointed at scratch; `has_writer` for
`bg_nakshatra_medical` flipped in memory only; the HEAD tracker read after every step. Target row:
`bg_nakshatra_medical-Build.registered`.

| step | emit | lines | target row (line, state) | tracker gaps_open/total |
|---|---|---|---|---|
| 0 | — | 263 | 137 OPEN | 6/6 |
| 1 has_writer=F | (0,209,0,0) | 263 | 137 OPEN | 6/6 |
| 2 has_writer=T | (1,208,1,0) | 265 | 264 CLOSED | 6/7 |
| 3 has_writer=F | (0,208,1,1) | 267 | 266 OPEN (RE-OPENED) | 6/7 |
| 4 has_writer=T | (0,208,1,1) | 269 | 268 CLOSED | 6/7 |
| 5 re-emit, unchanged | (0,209,0,0) | 269 → 269 | 268 CLOSED | 6/7 |

This is identical to A_REPORT §12.

**Ledgers.**
- `git diff 8a57a3320 HEAD -- 00_ARCHITECTURE/control/` changes `asset_elevation_tracker.py` only.
- `asset_gaps.jsonl` (263 lines, md5 `30365ff2…`) and `asset_certs.jsonl` (1 line, md5 `514cbdfc…`) are
  byte-identical to `8a57a3320`, both before and after every run in this review.
- `asset_census.json` and the gitignored `asset_elevation_tracker.json` in `control/` were not written (their mtimes
  predate this review).

## §5 — Scope

**Files per Lane A commit** (`git show --name-only`). Every one falls in the Lane A allowlist: `asset_census.py`,
`asset_elevation_tracker.py`, `__tests__/test_a[234]_*.py`, and `A_REPORT.md`. The one exception:
- `cbc8b6724` also carries 5 Lane B files: `catalog_provenance.py`, its test, and 3 `provenance/` artifacts.
- Its Lane A hunks are the F5 change (18 diff lines in `asset_census.py`) and the F5 test.
- A_REPORT §10 discloses the sweep ("7 files … 5 of them Lane B's").
- The commit message itself does not mention it.

**Untouched.** Across `8a57a3320..HEAD` there is no change to:
- any writer, `pipeline/orchestrator/`, or `supabase/migrations/`;
- the `*_FINAL.md` sealed tiers or `LAYER_DEFINITION_…`;
- `editorial.ts` or `compiler.ts`;
- any register, plan, DECISIONS or STATE file.

**Other scope checks.**
- No production write: the census has no write path, and the tracker opens `readonly=True`.
- No migration applied.
- HEAD is not on `origin/campaign/nikasha-test`, so nothing was pushed.
- None of the touched files is registered in `CAPABILITY_MANIFEST.json` (grep count 0).

## §6 — Honesty of A_REPORT v1.1

**Corrected well.** Every review-1 overstatement is corrected in place and labelled v1.1:
- "no further code change";
- D6 item 5 is now PARTLY;
- R41/R220 coverage, with M9 disclosed as surviving offline;
- "inversely", not "lockstep";
- the tracker figures;
- `kala_field` and `depth_census`;
- §9's withdrawn sentence.

The Lane B sweep is disclosed. Every figure I re-ran reproduces (§8).

**Three gaps (G4, G6).**
1. **F2's effect outside L0 is absent.**
   - The report never says that 78 L1–L5 assets now read ERRORED on `Build.completion`. The F2 commit message and a
     test docstring say it for L1.
   - §3's "0 ERRORED" L3 run and §9's "R41 independently reproduced (0 ERRORED in a live `--layer L3` run)" were
     not marked as v1.0-time. At HEAD, L3 reads ERRORED 17.
2. **F1's call-shape test is overclaimed.** §10 lists `test_case_attempt_linkage_unwired_is_the_default_measure_call_shape`
   among "test(s) that fail without the fix", and its docstring says it "fails if the call site regresses". It does
   not (G1).
3. **D4 case 1 is marked PASS without qualification.** §2's table still marks it PASS on the strength of the
   NOT_GENERIC tests. The "unmeasured" half of case 1 is not met on the branches in G2.

Nothing is claimed complete that is shown partial, except items 2 and 3.

## §7 — Remaining findings, each bound to the gate it blocks

| # | finding | evidence | blocks |
|---|---|---|---|
| **G1** | **The F1 fix's call site has no failable proof.** Dropping `attempt_linkage_wired=False` from `measure()` survives offline and live. The call-shape test greps source that a comment also satisfies. The default `attempt_linkage_wired=True` is the unsafe value. **Fix:** a `_stub_layer` test that runs the real `measure()` with `duration_instrument_present → True` and asserts `NO_DETECTOR — attempt linkage not wired` on both Earn and Cost; preferably also make the default `False`. | §2 F1b; `asset_census.py:506`, `:798`, `:806`; `test_a3_earn_cost_grading.py` call-shape test | **Adoption of the D6 classifier (R55)**; **applying migration 1094 to any database the census runs `--emit-gaps` against**; the R42–R56 lane's first edit of that call site. It does not block folding R55 as "classifier landed, not adopted, NO_DETECTOR today". |
| **G2** | **Three more unmeasured → closable paths, and one PASS.** Each needs a failable test, like F2's. **N1:** a `count_sql` that returns NULL or a non-integer reads N/A "no count_sql" (false text); it should be ERRORED or NO_DETECTOR. **N2:** `has_writer=true` with no recognised `@register` makes `Build.contract`/`Idem.pattern` read N/A; they should read NO_DETECTOR. **N3:** a missing capability directory makes `Dens.served` read N/A; it should read NO_DETECTOR. **N5:** an empty target table makes `Complete.depth` read PASS. | §2 table rows 1, 2, 9, 10 and the note; live ledger-copy run: 26 CLOSED. Latent: production today has 0 NULL counts, the writers are recognised, and the caps dirs exist. | **The first `--emit-gaps` run against the production ledger** (the closure loop going live). **R57's fold** must record D4 case 1 as met for NOT_GENERIC / UNKNOWN / ERRORED / absent criteria, with G2 open, not as fully met. |
| G3 | **R41 does not isolate real timeouts.** `psql()` lets `subprocess.TimeoutExpired` escape. Production's `statement_timeout` (30 min) is above the client timeout (180 s), so every real timeout is `TimeoutExpired`, and the run ends with exit 5. The tests simulate timeouts as `Unknown`. It is fail-closed. Separately, the multi-layer abort message omits that earlier layers' ledger rows were already appended. **Fix (2 lines):** catch `TimeoutExpired` in `psql()` and raise `Unknown`. | §2 non-closure paths; `asset_census.py:105–112`, `:87` | **R41's fold wording.** Fold as "per-asset isolation of query *errors*; client-side timeouts abort the run (exit 5)" unless fixed first. Not blocking. |
| G4 | **F2's cross-layer effect is undisclosed, and §3/§9 carry the stale "0 ERRORED" L3 figure.** | §4 table: L3 ERRORED 17 at HEAD | **The register fold's figures** (use §8 and the acceptance statement below). A_REPORT v1.2 is advisory. |
| G5 | **The census population silently omits `lel_events`** (active, `layer='mimamsa'`, no `mi_` prefix). The census `--layer all` covers 126; the tracker covers 127. L5 is 14 vs 15. The census's per-layer `registry_total` is prefix-scoped, so it cannot show the gap. The tracker comment at `:132` says "the census counts 127", which is false by one. | live registry query; tracker `scan()` on all layers | **R220's fold wording.** R220 says "every population figure scoped to 127"; fold it as census 126 (prefix-scoped) and tracker 127, with the reason. Not blocking. |
| G6 | A_REPORT §10 overclaims the F1 call-shape test, and §2 marks D4 case 1 PASS without qualification. | §6 items 2–3 | report re-issue (advisory) |
| G7 | Advisory: (a) the 8 pass-2 commits end `Co-Authored-By: Claude Opus 5.5`, not §2.7's `Claude Fable 5.1`; (b) the F2a and M9 detectors are live-only; (c) `Build.target`'s N/A for `asset_kind='data'` with a writer and no target (`bg_prashna_rules`) is wider than its own FAIL text; (d) the tracker has no F7 equivalent (a zero-active layer shows 0 assets silently). | §3, §5, §2 row 7 | none |

## §8 — Fact spot-check

| # | claim (source) | result |
|---|---|---|
| 1 | Suite grew 52 → 75 (A_REPORT §10) | **VERIFIED.** 48 passed + 4 skipped at `cbc8b6724`; 71 + 4 at HEAD (40 + 1 at `8a57a3320`). |
| 2 | Offline: 71 passed, 4 skipped | **VERIFIED.** 71 passed, 4 skipped in 0.39 s. |
| 3 | Live: 75 passed, 0 skipped (232.9 s) | **VERIFIED.** 75 passed in 225.3 s. |
| 4 | `kala_field` = 10,982,957 rows (12.1 s) | **VERIFIED.** 10,982,957 in 12.2 s. |
| 5 | `depth_census(kala_field)` 24.3 s, 23 columns, `refinement_residual` never populated | **VERIFIED.** 24.5 s, 23 columns, `['refinement_residual']`. |
| 6 | L0 FAIL 39; tally PASS 413 · PARTIAL 50 · NO_DETECTOR 120 · FAIL 39 · NOT_GENERIC 80 · N/A 68, identical at both commits | **VERIFIED.** |
| 7 | Zero verdict flips; `Vocab.identity` text changed on 37 assets | **VERIFIED.** |
| 8 | T3 table §12 (lines 137/264/266/268, emit tuples, tracker 6/6 → 6/7, idempotent 269 → 269) | **VERIFIED**, exactly. |
| 9 | Engine suite 13/13 at `8edba0533` and at `e5dd65b8f`; `asset_runner.py` identical | **VERIFIED.** |
| 10 | M9 survives offline and is caught live | **VERIFIED.** 4 live tests fail under M9. |
| 11 | F1: "guard reverted → 2 failed" | **VERIFIED.** But the listed call-shape test does not catch a call-site regression: **PARTLY** (G1). |
| 12 | F2: "`errored[aid]` line removed → offline test fails" | **VERIFIED.** The `measure()`-side branch is caught live only. |
| 13 | "R41 independently reproduced (0 ERRORED in a live `--layer L3` run)" (§9) | **STALE.** L3 reads ERRORED 17 at HEAD, via F2 (G4). |
| 14 | Sweep in `cbc8b6724`: 7 files, 5 of them Lane B's; the commit message does not say so | **VERIFIED.** |
| 15 | Production ledgers byte-identical before and after | **VERIFIED.** md5 unchanged; `git diff` against `8a57a3320` is empty. |
| 16 | Tracker `--layer all` reads 127; L3 "21 active of 23", the two ids named (§13) | **VERIFIED** (tracker). The census covers 126 (G5). |
| 17 | F1 with the instrument present grades NO_DETECTOR and closes nothing (commit `a77d50005`) | **VERIFIED live.** 40/40; emit (0,208,0,0). |
| 18 | No touched file is manifest-registered (§13) | **VERIFIED.** grep count 0. |

---

**Acceptance statement (for the executor's register fold):**

> Lane A (Nikaṣa wave 1) is ACCEPTED WITH CORRECTIONS at gate review 2 (`A_REVIEW2.md`), final commit `7352ba484`
> (code: `afa1d4146`/`8ef861e0b`). **R216** (B1 rebase) and **P3 — R57/R58/R47/R62/R30** fold as landed:
> `emit_gaps` closes only on an explicit `(PASS, N/A)` allowlist, keeps WITHDRAWN terminal and `superseded_by`
> permanent, carries hand `change/owner/gate` onto every transition, and is idempotent. The tracker resolves
> last-wins per `gap_id` and is scoped to the active population. The T3 cycle re-runs
> OPEN→CLOSED→RE-OPENED→CLOSED live on a ledger copy (tracker 6/6 → 6/7), and the production ledgers are
> byte-identical to `8a57a3320` (263/1 lines). R57 carries one open correction, **G2**: three latent unmeasured→N/A
> paths (a NULL `count_sql`, an unrecognised writer, a missing capability dir) and one PASS on an empty table. G2
> must be closed before the first `--emit-gaps` run against the production ledger. **R40/R41/R220** fold with
> these figures and limits:
> - R40: `kala_field` has 10,982,957 rows, and its EXISTS probe completes (L3 census 79 s).
> - R41 isolates per-asset query *errors* only. Layer-wide reads abort the layer (disclosed), and client-side
>   psql timeouts abort the run with exit 5 (**G3**).
> - R220: the census measures 126 active assets (prefix-scoped; `lel_events` unmeasured) and the tracker 127
>   (**G5**).
> - F2 correctly moves 78 of 86 L1–L5 `Build.completion` readings to ERRORED (chart-scoped `$1` count_sql), so
>   that criterion is unmeasured there until a chart scope is bound.
>
> **D6 / R55** folds as "classifier landed, graded NO_DETECTOR today (instrument absent: 80/80 L0 rows), tested
> against the engine at `8edba0533` read-only (13/13) — D6 item 5 PARTLY met: grading real rows needs migration
> 1094 plus the R42–R56 attempt adapter". R55 stays OPEN. The classifier is **not adopted** until **G1** lands (a
> behavioural test of the `measure()` call site with the instrument present). G1 is required before migration
> 1094 is applied anywhere the census emits.
>
> Figures:
> - Lane A suite: 75 tests, 71 passed + 4 skipped offline, 75 passed live.
> - L0 census at HEAD: FAIL 39 · PARTIAL/NO_DETECTOR 170 · ERRORED 0, with 0 verdict flips vs `7ed870775`.
> - `depth_census(kala_field)`: 24.3–24.5 s (out of scope, unfixed).
