---
artifact: NIKASHA_WAVE2_W2-1_REVIEW
packet: W2-1 — no unearned closure; no silent absence
reviewer: Opus gate (fresh context, read-only; not the implementer)
reviewed_on: 2026-09-27
base: 9baaa307b
head: 986054d7b (code head d465d5a2c)
packet_commits:
  - 9af0fcce5  # R224
  - 58cf4c238  # R231
  - 9079830b9  # R223
  - 61c6e637a  # R222
  - 14f3f5d1c  # R225
  - cfa9f42c0  # R42
  - e9db66f2b  # R52
  - 416fe4574  # R56
  - d465d5a2c  # R48
  - 986054d7b  # report + evidence
verdict: ACCEPT_WITH_CORRECTIONS
r222_precondition: NOT_MET
r222_precondition_reason: >
  One more unmeasured-to-closable path exists, and it is not among the four R222 names. A build_run_assets
  row left in state 'queued' (1 465 such rows persist in failed, stopped and completed runs) reads
  Build.exercised PASS and Build.history PASS "0 complete". That would CLOSE the real OPEN production gap
  bg_sign_medical-Build.exercised although the asset never executed. Correction C1 lifts this.
scratch: <scratchpad>/rev-w2-1/ (census outputs, ledger copies, mutation copy, attack tests; nothing in the repo)
---

# Nikaṣa wave 2 · W2-1 · gate review

## §1 — Verdict

**ACCEPT_WITH_CORRECTIONS.**

**The nine rows are done.** Each row is closed by a proof that could have failed. I re-ran my own mutation
for every row (15 offline mutations and 1 live mutation, §3), and every one was killed. The reported figures
reproduce exactly:
- census per-layer table, and ERRORED 0 everywhere;
- population 127;
- the 78 → 46 / 13 / 11 / 8 split;
- 223 verdict changes;
- emit: 596 OPEN, 0 CLOSED, idempotent.

The one exception is the Dens.served partial count: 29, not 31. Nothing untouchable was touched. No verdict
moved in the favourable direction without a new measurement behind it (§6).

**The R222 precondition is NOT_MET.** The packet's core claim is "23 genuine branches". That claim does not
survive attack on branch #32 (`Build.exercised` PASS) together with #5 (`Build.history` PASS on 0
completions):
- A `queued` `build_run_assets` row (never executed) reads PASS on both.
- `bg_sign_medical-Build.exercised` is **OPEN in the production ledger today**.
- The next L0 run that ends before reaching that asset would CLOSE this gap on an unmeasured basis.
- Demonstrated with the real `build_history()`, `measure()` and `emit_gaps()` (A8, §2).

That is exactly the R222 defect class: an unmeasured check yielding a closable verdict. It is live-reachable,
because queued rows persist in 100 terminal runs. Correction C1 (small, in `asset_census.py`) lifts it.

The four contested branches do not block the **first** production emit. Only `Build.dep_liveness` blocks
a *subsequent* one until R45 lands (§2.3).

**Fold instruction.**
- **Fold R224, R231, R223, R225, R42, R52, R56 and R48 as closed.**
- **Fold R222 as "four named paths closed".** Register C1 as a new BLOCKS_FREEZE row that inherits R222's
  clause "must close before the first `--emit-gaps` run against the production ledger".
- Do not record the precondition as met until C1 is accepted.

## §2 — Independent branch enumeration and attacks

### §2.1 — Enumeration

I read all 1 398 lines of `asset_census.py` at HEAD and followed every helper that returns a verdict:
- `contract_scan`, `idem_scan`, `capability_scan`;
- `_grade_build_history`, `_grade_earn_cost`, `_no_writer_scanned`;
- `_measure_contract`, `_measure_idem`, `_grade_count_floor`, `_run_carriage_detector`;
- the inline grading in `measure()`;
- `CLOSABLE` in `emit_gaps`.

**The report's list of 35 is complete.** I found no PASS/N/A branch it omits:
- `contract_scan` and `idem_scan` return NO_DETECTOR on an empty file list, never N/A.
- The Count.floor `None` is non-closable absence, and only when nothing is declared.

My rulings differ from the report's labels where an attack succeeded:

| # | branch | report label | reviewer ruling |
|---|---|---|---|
| 1 | Build.contract PASS | genuine | **genuine for literal class-body syntax only.** The A1 attack defeats it (0 live instances). |
| 2–3 | Idem.pattern PASS (ON CONFLICT / DELETE FROM) | genuine (text presence) | **proxy.** The A2 attack defeats it: a DELETE on a sibling table passes (live shape: bo_upaya). |
| 4 | Build.history PASS (blocked, ≥1 complete) | genuine | genuine |
| 5 | Build.history PASS (no error) | genuine, OS-4 latent | **not genuine at 0 completions.** Reachable via persistent `queued` rows (A3/A8). Part of C1. |
| 6–10 | Earn/Cost N/A·PASS | genuine, unreachable | unreachable from `measure()`: confirmed. The literal is `attempt_linkage_wired=False` and the default is False (R225). |
| 11 | contract/idem N/A, `has_writer=false` | fixed 61c6e637a | fixed (registry-trust, same as #16) |
| 12 | Count.floor N/A, floor 0 | fixed d465d5a2c | fixed |
| 13 | Count.floor PASS | fixed 416fe4574 | fixed |
| 14 | Carr.detector adopted | genuine | genuine. No `control/detectors/` exists in production, so it reads NO_DETECTOR everywhere today. |
| 15–16 | Build.registered PASS / N/A | genuine | genuine |
| 17 | Build.target PASS | genuine (declaration) | genuine |
| 18 | Build.target N/A | contested (R53) | contested, and **cannot close** (§2.3) |
| 19 | Build.dag PASS | contested (OS-2) | contested, and cannot close today (§2.3). The A6 attack defeats it. |
| 20–21 | count_integrity PASS / N/A | genuine (presence) | genuine (presence) |
| 22 | Build.completion N/A | fixed 61c6e637a | fixed (declared service; registry-trust) |
| 23 | Build.completion PASS | fixed cfa9f42c0 + e9db66f2b | fixed. Residual A5 (declared-zero truncation) and A7 (constant naming a table): 0 live instances. |
| 24 | Complete.depth PASS | fixed 61c6e637a | fixed. The table is counted whole, not per chart (a disclosed scope). |
| 25 | Vocab.identity PASS | fixed 61c6e637a | fixed for empty tables. **The detector can fail only through NULL key members.** Keys come from enforced `pg_constraint` u/p. The T1 harness itself records that no L0 target table has a nullable key member, so on L0 this PASS cannot read false. Pre-existing (§7 F7). |
| 26 | Vocab.alias PASS | genuine | genuine |
| 27 | Ldgr.source_presence PASS | genuine | genuine. My attack with `''`/`[]`/`{}` citations found 0 across all 58 live PASS tables. |
| 28 | Dens.served N/A | fixed 61c6e637a | fixed |
| 29 | Dens.served PASS | contested (OS-3) | contested (§2.3). The A4 attack defeats it (0 live instances). |
| 30 | Build.exercised N/A | genuine | genuine |
| 31 | Build.history N/A (never run) | genuine | genuine |
| 32 | Build.exercised PASS | **genuine** | **NOT genuine.** "≥1 `build_run_assets` row" counts `queued` rows that never executed (A8). **Blocks R222 → C1.** |
| 33 | dep_liveness PASS | contested (R45) | contested, and **live**: 10 assets PASS while a dependency is `stale` on the canonical chart (§2.3) |
| 34 | dep_liveness N/A | genuine | genuine |
| 35 | CLOSABLE allowlist | genuine | genuine |

### §2.2 — Attacks

Scratch tests: `rev-w2-1/attacks/test_attacks.py` and `test_attack_queued.py`. They import the real module and
the packet's own test helpers, and nothing in the repo is modified. All 8 constructed attacks **succeed**.

| id | target | construction | result | live instance? |
|---|---|---|---|---|
| A1 | #1 Build.contract | `conn = ctx.db_conn; conn.commit()`, plus a module-level helper that UPDATEs `asset_throughput` | PASS `['conformant']` | none. Grep over writers found no aliased commit. |
| A2 | #3 Idem.pattern | bo_upaya.py copied to scratch with its two `replace_prior_rm_*` target-table deletes removed | PASS "DELETE FROM present". It matched the 3 sibling-table DELETEs. | shape is live. bo_upaya's real target is idempotent via the helper, so today's PASS is right by coincidence. |
| A3 | #5 Build.history | 3 runs, all `queued` | PASS "0 complete, no error or abort" | no asset is queued-only today |
| **A8** | **#32 + #5 end to end** | real `build_history()` fed one `queued` row; OPEN `bg_sign_medical-Build.exercised` on a ledger copy | Build.exercised PASS "1 run(s)", Build.history PASS "0 complete", **emit closes 1** | **The gap is OPEN in production today.** 1 465 `queued` rows persist across 100 terminal runs (failed / stopped / completed), so the trigger is routine. |
| A4 | #29 Dens.served | a module whose only mention is `// TODO: … no density_contract yet` | `density=1`, which reads PASS | none. All 29 partial PASS verdicts rest on a real `density_contract:` property. |
| A5 | #23 Build.completion | declared floor 0; `rows_written=0`, live 7 reads FAIL; truncate to 0 | FAIL → **PASS** "zero rows declared complete" | none. No declared-zero asset is lit with rw=0 and live>0, and none of the 10 open production Build.completion gaps declares floor 0. |
| A6 | #19 Build.dag | `depends_on=['ka_does_not_exist','ga_nope']` on an L2 asset | PASS "2 edge(s), all resolvable" | none. All 337 live edges resolve to active assets. |
| A7 | #23 constant guard | `SELECT 15 AS count FROM t_main LIMIT 1`, rw=15 | PASS (the guard only catches a count_sql with no FROM) | none. bo_samvada is the only count_sql without `count(`. |

**Output** (`attacks.out`, `attack_a8.out`):
```
A1 PASS ['conformant']
A2 PASS ['DELETE FROM present (delete-then-insert)']
A3 {'v': 'PASS', 'measured': '0 complete, no error or abort; 0 skip_no_delta (healthy)'}
A4 {'modules': ['get_x.ts', 'get_y.ts'], 'density': 1, 'note': '', 'scanned': True}
A5 FAIL 'build record says rows_written=0 against live=7 (global)' -> PASS 'rows_written=0 = live=0 … declared complete by target_floor=0'
A6 {'v': 'PASS', 'measured': '2 edge(s), all resolvable'}
A7 {'v': 'PASS', 'measured': 'rows_written=15 = live=15 (count_sql over the target table; global)'}
A8 Build.exercised PASS '1 run(s), scope(s): layer, last 2026-09-28' · Build.history PASS '0 complete, no error or abort' · closed 1
```

**Live evidence for A8.**
- `build_run_assets` by state: complete 3 133, error 1 515, **queued 1 465**, aborted 649.
- The queued rows sit in runs whose own state is: failed / asset_set 936 (61 runs), failed / layer 259 (21),
  completed / layer 146 (12), failed / global 57, stopped / global 57, failed / asset 9, stopped / asset 1.
- `bg_sign_medical` has 0 rows today. Its gap row reads "registered with a writer and the orchestrator has
  NEVER run it".

### §2.3 — The four contested branches: can each close a real gap on the production ledger today?

I mapped every OPEN or IN_PROGRESS row of the production `asset_gaps.jsonl` (263 lines, md5 `30365ff2…`)
to its verdict in my HEAD census:
- NO_DETECTOR 120, PARTIAL 50, FAIL 39, not a census id 53;
- **PASS/N/A 0.**

| branch | open production gaps of this criterion | can it close one today? | ruling |
|---|---|---|---|
| #18 Build.target N/A | 0 | **No.** `asset_kind` is `NOT NULL CHECK (data\|service\|artifact)`, verified live. So the FAIL branch is dead and the census can never open a Build.target gap, and it therefore never closes one. | A missed detection, not an unearned closure. It does not block. R53 (W2-2) owns it. Only a hand-written Build.target row could be falsely closed. |
| #19 Build.dag PASS | 0. The first production emit would open 0. | **No.** A gap opens only on an unknown same-prefix dependency, and PASS then genuinely covers that edge. Cross-layer blindness (A6) is a missed detection. | Does not block. Needs a register row (OS-2). |
| #29 Dens.served partial PASS | 24 (L0), all reading FAIL today. The first emit adds 35. | Not today. Later, a gap closes when ≥1 of N modules declares `density_contract`. That is a *measured* but lenient grade, and the closing row states "declaring: k". | Not an unmeasured basis, so it does not block. Register OS-3; R51 (W2-2) is adjacent. |
| #33 dep_liveness PASS | 0. The first emit adds 27. | Not today. **Live today, though:** 10 assets read PASS while a dependency is `stale` on the canonical chart and `lit` only on 1c826d5a: bo_anveshana, bo_chart_gestalt, bo_pramana_mapa, bo_samvada, bo_upaya, bo_yantra_mechanism, ka_avadhi, ka_kshetra, ka_sangam, ka_yojaka. After the first production emit, the 27 new OPEN rows can close on *another chart's* `lit` state, which is unmeasured for the chart the census binds. | Does not block the first production emit, which only appends. It **blocks any later production emit** from being trusted for `Build.dep_liveness` closures until R45 (W2-2) lands. |

## §3 — Per-row mutations (reviewer's own)

**Method.**
- Work on a scratch copy of `asset_census.py` plus `__tests__/`, with pytest run from the repo cwd so
  `ROOT` resolves.
- Apply one replacement, run the Lane A and W2-1 files, and restore (asserted byte-identical).
- The baseline copy is 107 passed; `test_f6_tracker_…` is deselected in the copy only, a path artifact. It
  passes in the repo: 108 passed.

| row | my mutation | killed by |
|---|---|---|
| R224 | registry scope → `asset_id LIKE prefix%` | 2 failed (both r224 offline) |
| R231 | `_bind_chart` returns `q` unbound | 3 failed offline (r231 ×2, r56 multi-table). **Live:** 3 failed (live L4 test, live R56 three-breach test, wave-1 live e2e) |
| R231b | `_build_record` takes an arbitrary chart's row | 1 failed |
| R223 | `except subprocess.TimeoutExpired` → `except CalledProcessError` | 2 failed (both r223; the fixture raises the real `TimeoutExpired` from a `sleep 30` psql) |
| R222-N1 | `_take` stops recording NULL as errored | 1 failed. Note: the verdict **stays ERRORED** through the second guard at `measure()`, "count_sql produced no value"; the test kills it on text. Defence in depth, sound. |
| R222-N2 | `_no_writer_scanned` always N/A | 1 failed |
| R222-N3 | `scanned` check disabled | 1 failed |
| R222-N5 | depth empty-table branch fires only on "no columns" | 1 failed |
| R225 | call site passes `attempt_linkage_wired=True` | 1 failed (`test_r225_measure_with_the_instrument_present…`) |
| R42 | comparison `int(rw) != live` disabled | 3 failed |
| R42-state | completed-state guard disabled | 1 failed |
| R52 | non-emptiness branch disabled | 7 failed. The 3 `rows_written=8579` cases fail on text; their verdict stays FAIL through R42, as the report says. |
| R56 | unmeasurable count → absent (`return None`) | 1 failed |
| R48 | floor 0 no longer special-cased (it reads a vacuous PASS) | 1 failed |
| R48-none | declared floor with no count_sql → absent | 1 failed |

The builder's `mutation_runs.log` holds 29 recorded mutations, consistent with the above.

**Specific confirmations.**
- **R231.** Every layer's census states `chart_scope = 482012f1-710e-4a25-994a-93821f5871aa`, and there are 79
  chart-scoped count_sql (L1 19, L2 22, L3 17, L4 9, L5 12). The 78 formerly-ERRORED readings split as
  **46 PASS / 13 FAIL (comparison) / 11 FAIL (not completed) / 8 FAIL (empty)**, reproduced asset by asset.
  `asset_throughput` holds 0 duplicate `(chart_id, asset_id)`.
- **R223.** Uses the real `subprocess.TimeoutExpired`; `__cause__` is asserted.
- **R225.** The default is `False` (signature). The behavioural test with the instrument present fails if
  the call site passes True.
- **R52.** Emptying a table never flips to PASS, except under `target_floor=0` (§4 rules on that).
- **R56.** Live: ga_vargas `live=0, floor=22092`; bo_laksana `50529 < 60000`; ph_sankrama `155 < 2510`. All
  three read FAIL.

## §4 — Rulings on the builder's judgement calls

**(a) mi_kula PASS 15 = 15. The builder is right; the handverify "truth FAIL" was wrong.**
- In `mi_kula.py` (`@register("mi_kula")` at :286), `run()` DELETEs and re-INSERTs **both**
  `mimamsa_signal_families` and `mimamsa_negative_controls`. It returns
  `rows_inserted=len(_FAMILIES) + len(_CONTROLS)`.
- The registry count_sql is the sum over the same two tables.
- Live: 11 + 4 = 15. The global build record is `lit`, rows_written 15.
- Comparing 15 with 11 (one table) is apples to oranges. The census now states the basis and shows the
  target table alone as context. That is the honest rendering.

**Caveat (correction C3).** The report generalises this to "the writer's `rows_written` is the same total"
for multi-table assets. That does not hold in general:
- **bo_upaya.** `rows_written` sums 5 tables (resonances + prescriptions + summary + bundles + patterns);
  count_sql sums 2. The live figures are 45 + 135 = 180 against the recorded 240.
- **ga_condition.** `rows_written=45` equals `ga_condition_composite` alone (45 live), while count_sql also
  counts chart_facts avastha rows (total 2 970).

These FAILs are basis mismatches, not the "real disagreements between the build record and the live count"
that §4 and OS-9 call them. The direction is fail-safe, so they cannot close anything, but the report's
wording must change.

**(b) The two guards beyond R42's literal text are sound, not overreach.**
- **Completed-state guard.** An `error`, `dormant` or `incomplete` record's `rows_written` is not a
  completed build's figure. Without the guard, 8 live assets PASS on equal figures, a §N.8 green with no
  detector behind "the build completed". It overlaps Build.history (the same fact read twice), but in the
  fail-safe direction, and the gap closes only on a real successful rebuild. Counting `stale` as completed
  is acceptable pending R45.
- **Constant `count_sql` → NO_DETECTOR.** Correct under §N.8. It is syntactic (A7 evades it), with 0 live
  instances; note it, do not block.

**(c) R52's `target_floor=0` limit is acceptable.** It is the registry's and the engine's own completion rule
(`asset_runner.py`: `zero_rows_is_complete = … or target_floor == 0`). It is not a blocker:
- no live instance;
- no open production Build.completion gap declares floor 0.

The disclosure is incomplete, though. The report does not state that a declared-zero asset reading FAIL on
"rows_written=0 against live>0" flips to **PASS** when truncated (A5). Add it to §8 item 3 (C3).

**(d) `earn_cost_signal` "obsolete" is honest.** D6 retired `rows_per_second` as the Earn/Cost basis. Both
criteria now read NO_DETECTOR, which is non-closable and stated. There is no hidden missing detector
dressed as a verdict. The plant premise, a FAIL→PASS flip on `rows_per_second`, is dead by ruling. Present
the result as 16/16 applicable, plus 1 plant awaiting re-specification under R55 (OS-11), rather than as a
"miss".

## §5 — Proofs reproduced

**Census at HEAD** (read-only, pgenv, six layers in parallel, `timeout 300`, `--out` to scratch, ledger dir
pointed at a scratch copy):

| layer | FAIL · PARTIAL+NO_DET · ERRORED | assets | runtime |
|---|---|---|---|
| L0 | 43 · 172 · 0 | 40 | 75 s |
| L1 | 7 · 106 · 0 | 19 | 200 s |
| L2 | 15 · 121 · 0 | 23 | 221 s |
| L3 | 55 · 111 · 0 | 21 | 174 s |
| L4 | 27 · 45 · 0 | 9 | 21 s |
| L5 | 31 · 72 · 0 | 15 | 22 s |

The population is 127 and every run exits 2. All of this is **identical to the report's §4.** L2 is under
the 300 s cap by 79 s under parallel load, which confirms the report's limit 10.

**Base census.** I ran it at `9baaa307b` in a temporary worktree under scratch, since removed (`git worktree
list` shows none): 39·170·0, 1·102·19, 8·120·22, 38·91·17, 18·43·9, 21·57·11. Identical to the report. My
own diff gives **223 verdict changes**, the same count and the same class breakdown.

**Emit dry run on ledger copies.**
- **Python path.** `emit_gaps` over my six census documents gives **596 OPEN appended, 209 already present,
  0 closed, 0 re-opened**. The criterion counts are identical to the report's. The second pass gives
  (0, 805, 0, 0) and the ledger copy is byte-identical.
- **Real CLI path.** `asset_census.py --layer L4,L5 --emit-gaps`, run twice on a fresh copy, re-measured:
  - run 1: 72 + 103 appended, 0 closed;
  - run 2: 0 appended, 72 + 103 present, 0 closed;
  - md5 unchanged between runs (`a31e3e28…`).
- **Production ledgers.** md5 `30365ff2…` / `514cbdfc…`, before and after every run.

**T1 sandbox.** The sandbox is reachable (socket `.sandbox`, port 54329). Under my read-only discipline I
did not re-plant. What I did:
- Checked the restored state: `bg_muhurta_lattice` 8 579 rows, `lit/0`, floor 164 575.
- Ran a read-only (`PGOPTIONS=-c default_transaction_read_only=on`) HEAD census of L0 on the sandbox:
  Build.completion **FAIL** "rows_written=0 against live=8579" (baseline).
- Checked the post-truncation shape (live 0, rw 0, floor 164 575). It takes the R52 branch to FAIL, which is
  covered by `test_r52_the_truncate_plant_flips_toward_fail_never_toward_pass` and by my R52 mutation.
- Checked the evidence JSON:
  - `build_completion_truncate`: FAIL→FAIL at HEAD, FAIL→PASS at base;
  - `dep_liveness`: detected;
  - `earn_cost_signal`: NO_DETECTOR both, `restore_ok` true.

**Not reproduced:** the plants themselves (not re-run), and "31" partial Dens.served (I count 29, below).

**Suite.** Offline full governance suite: **208 passed, 9 skipped, 2 failed**. The 2 failures are in
`test_drift_detector_h35_h38.py`, as reported. W2-1 live tests: 4/4 passed. Changes to wave-1 tests are
signature-only, plus the R225 grep test replaced by a behavioural assertion. No assertion was weakened.

## §6 — Scope and regression

**Scope.**
- `git show --stat` over the 10 commits lists only these, plus the report and evidence under
  `nikasha_test/wave2/`:
  - `asset_census.py`;
  - `__tests__/test_w2_1_earned_verdicts.py` (new);
  - `test_a3_earn_cost_grading.py`, `test_a3_fault_isolation_and_population.py`;
  - `test_a4_d6_engine_conformance.py`, `test_a4_gate_corrections.py`.
- `git diff 9baaa307b HEAD -- 00_ARCHITECTURE/control/` is **empty**.
- No Lane B file, writer, orchestrator, migration, sealed tier, editorial/compiler, register, plan or STATE
  file was touched. `asset_elevation_tracker.py` is untouched, as declared.
- My session left the working tree clean (the pre-existing `.agents/` aside) and removed my worktree.

**Regression.** 119 verdicts moved into a closable state (PASS/N/A). I checked each one; every one has a new
measurement or a declaration behind it:

| movement | count | basis |
|---|---|---|
| ERRORED → PASS, `Build.completion` | 46 | R231 binding plus a genuine like-for-like comparison on the canonical chart's own record |
| absent → PASS, `Count.floor` | 45 | measured count ≥ declared floor |
| absent → N/A, `Count.floor` | 17 | declared `target_floor=0` |
| `lel_events` newly measured | 11 | 1 Count.floor N/A (floor 0) plus 10 writerless or dependency-free N/As and PASSes, each stating its reason |

- 5 verdicts moved PASS → N/A (floor 0), a deliberate §N.8 change.
- **0 moved FAIL→PASS, NO_DETECTOR→PASS or PARTIAL→PASS.**
- Unfavourable moves (53 into FAIL, 44 into NO_DETECTOR, 2 new NOT_GENERIC on `lel_events`) are each
  attributed in the report.
- 119 + 5 + 53 + 44 + 2 = 223.

## §7 — Remaining findings and the gate each blocks

| id | finding | blocks |
|---|---|---|
| **C1** | `Build.exercised` PASS counts `queued` rows (never executed), and `_grade_build_history` PASSes at 0 completions and 0 errors (OS-4). Together they close the OPEN production gap `bg_sign_medical-Build.exercised` on an unmeasured basis (A8; 1 465 persistent queued rows). **Fix:** count only executed attempts (`complete` / `error` / `aborted`) as a run, and never PASS history with 0 completions. Add a behavioural test (queued-only row + open gap → closes nothing) and a recorded mutation, and relabel #5 and #32 in §3. | **The R222 precondition: the first `--emit-gaps` against the production ledger.** W2-1 re-gate on C1 only. |
| **C2** | `Build.dep_liveness` PASS rests on `lit` on **any** chart. It is live on 10 assets whose dependencies are `stale` on the canonical chart. | **Any production emit after the first**, whose CLOSED dep_liveness rows would otherwise be trusted. **R45 (W2-2) must land first.** It does not block the first emit. |
| C3 | Report honesty, fixed in the report without a code change: (i) R42 "like for like" overstated (bo_upaya 5-table rows_written against a 2-table count; ga_condition 45 = one table); (ii) R52 limit omits the A5 FAIL→PASS flip on declared-zero assets; (iii) "31 partial Dens.served" should read 29; (iv) #1, #2–3, #25 and #29 relabelled as proxies per A1, A2, F7 and A4. | Folding the report text as the record. It does not block the rows. |
| F4 | Register rows are missing for OS-2 (Build.dag cross-layer; dead `missing` list), OS-3 (Dens.served ≥1-of-N plus substring match, A4), A1 (contract scan misses aliased commit and module-level helpers), A2 (Idem proxy; close to R20) and A7 (constant guard is syntactic). | Executor register fold. W2-2 and W2-3 scope. |
| F5 | Build.target FAIL is dead (asset_kind NOT NULL CHECK). The 3 data-with-writer N/As (bg_prashna_rules, ga_strength, ga_structural) can never be opened. | R53, W2-2 gate. Not a closure risk. |
| F6 | Depth, identity, alias and Ldgr measure whole tables while Build.completion is chart-scoped. For example, ka_bhavishya_lekha reads Ldgr PASS on 100 rows from other charts, and Build.completion FAIL empty for the canonical chart. | D4 criterion registry (scope declaration). Not blocking. |
| F7 | Vocab.identity under an enforced declared key can FAIL only through NULL key members. On L0, no target table has a nullable key member, so its PASS cannot read false (§N.8). Pre-existing. | D4 criterion registry. Not W2-1. |
| F8 | `ka_gochara`: the registry count_sql and target_table name `kala_gochara_windows` (v1, frozen), while the writer's only DELETE/INSERT target is `kala_gochara_windows_v2`. Its "empty" FAIL measures the wrong table. A registry data finding. | The owner, not the inspector. |

## §8 — Fact spot-check (report claims → independent result)

| # | claim | result |
|---|---|---|
| 1 | Per-layer HEAD table: L0 43·172·0 … L5 31·72·0, ERRORED 0 | ✓ exact (§5) |
| 2 | Population 127; L5 15 including `lel_events` | ✓ |
| 3 | 79 chart-scoped count_sql, all bound to 482012f1 | ✓ (19 + 22 + 17 + 9 + 12) |
| 4 | 78 former ERRORED → 46 / 13 / 11 / 8 | ✓ asset lists match |
| 5 | 223 verdict changes, base vs HEAD | ✓ (my own base census) |
| 6 | Emit: 596 OPEN / 209 present / 0 CLOSED; idempotent | ✓ (Python path and real CLI) |
| 7 | `Count.floor` on 121/121 declaring assets; absent on exactly bg_ephemeris_engine, bg_panchanga, ka_graha_sancara, ka_muhurta_seva, ph_pramana, ph_sodhana | ✓ |
| 8 | 23 assets declare floor 0; 104 do not | ✓ |
| 9 | ga_vargas 0 < 22 092, bo_laksana 50 529 < 60 000, ph_sankrama 155 < 2 510 | ✓ |
| 10 | mi_kula 15 = 15 over two tables; writer `len(_FAMILIES)+len(_CONTROLS)` | ✓ (11 + 4 live) |
| 11 | No duplicate `(chart_id, asset_id)` in asset_throughput | ✓ 0 |
| 12 | 1 `asset.noop_completion` event | ✓ (ka_gochara, 2026-09-10). It currently reads FAIL empty, so no PASS rests on a self-comparison today. |
| 13 | N2 live on 13 writer-backed assets (OS-8) | ✓ 13 contract + 13 idem N/A→NO_DETECTOR, all `has_writer=true` |
| 14 | bo_samvada `SELECT 0 AS count` → NO_DETECTOR | ✓ |
| 15 | bg_cohort 10 000 vs 110 000; ph_nimitta 139 vs 4; ka_kshetra 8 570 075 < 8 599 775 | ✓ as figures (see C3 on basis) |
| 16 | `lel_events` has_writer=false, Build.completion FAIL "no build record" | ✓ |
| 17 | Offline suite 208 / 9 / 2 | ✓ |
| 18 | Production ledgers md5 `30365ff2…` / `514cbdfc…`, 263 lines, unchanged | ✓ |
| 19 | "31 live assets partial" on Dens.served | ✗ **29** of 42 Dens.served PASS verdicts are partial |
| 20 | "0 live instances" of OS-4 | ✓ for today's data. **But** 1 465 persistent queued rows make it routinely reachable, which is C1. |
| 21 | Build.dag `missing` list is dead code | ✓ (computed, never read) |
