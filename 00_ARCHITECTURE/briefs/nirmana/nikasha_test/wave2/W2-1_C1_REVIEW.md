---
artifact: NIKASHA_WAVE2_W2-1_C1_REVIEW
packet: W2-1 correction C1 (+ C3 report wording) — re-gate of the R222 precondition
reviewer: Opus gate (fresh context, read-only; not the implementer, not the W2-1 reviewer)
reviewed_on: 2026-09-27
base: 8af39a194 (W2-1_REVIEW.md)
head: 8fc9bcac5
commits:
  - 1ae91dae4  # C1 — asset_census.py + test_w2_1_earned_verdicts.py
  - 8fc9bcac5  # C3 — W2-1_REPORT.md v1.1 + C1 evidence
verdict: ACCEPT_WITH_CORRECTIONS
r222_precondition: MET
r222_precondition_reason: >
  The A8 path is closed at HEAD. "Executed" is `build_run_assets.started_at IS NOT NULL`. The engine sets
  started_at only when a row enters 'building', and no path writes 'complete' to an unstarted row, so the
  marker is right. At 0 completions Build.history reads NO_DETECTOR, and no route leads it to PASS or N/A.
  All 262 live rows in the current production ledger were mapped to their verdicts at HEAD: 0 read PASS or
  N/A. A real-CLI first emit, run on six ledger copies, appends 596 OPEN rows and closes 0.
  The corrections below are test and wording fixes only. None of them is needed before the first
  production --emit-gaps. C2 (dep_liveness) still blocks any later emit.
scratch: <scratchpad>/rev-w2-1c/ (attack tests, mutation copy, six emit copies, census JSONs; nothing in the repo)
---

# Nikaṣa wave 2 · W2-1 · C1 re-gate review

## §1 — Verdict

**ACCEPT_WITH_CORRECTIONS. The R222 precondition is MET: the first production `--emit-gaps` may run.**

- **C1 does what the review asked.**
  - A never-started row no longer counts as a run.
  - Build.history no longer PASSes at 0 completions.
  - The reviewer's original A8 reproduction, re-run verbatim, now fails its own assertion: 0 closed, gap OPEN.
  - My own reproduction on a fresh copy of the production ledger leaves `bg_sign_medical-Build.exercised`
    OPEN under every never-started shape.
- **The decisive test.** Of the 262 live (OPEN/IN_PROGRESS) rows in the production ledger, **0** read PASS
  or N/A at HEAD (§3).
- **The simulated first emit.** The real CLI, run on all six layers against ledger copies, gives:
  - **596 OPEN appended, 209 already present, 0 CLOSED, 0 RE-OPENED**;
  - an idempotent re-run;
  - production ledgers unchanged (§4).
- **The corrections are not blockers for the first emit.**
  - **C4 (test):** the committed suite does not kill a regression to the state-list design that the C1
    commit itself rejects. My mutation M2 survives, and on that mutant the A8 closure comes back through an
    unstarted `aborted` or BLOCKED row. The code at HEAD is right, but nothing pins it.
  - **C5 (wording):** three accuracy fixes to the report and the docstring.
  - Both are for the W2-1 fold. Neither changes a verdict the first emit would write.

## §2 — C1 attack

### §2.1 — The executed marker against the engine (read-only)

**Where `started_at` is written.** I grepped every `INSERT INTO` / `UPDATE build_run_assets` in the repo
(Python, TypeScript, SQL):
- `asset_runner.py:1403`: the `'building'` transition, `started_at = NOW()`.
- `run_heavy_writer_standalone.py:137`: `INSERT … 'building', NOW()`, followed by the writer.
- `runner.py:406/419` set `build_runs.started_at`, not `build_run_assets`.
- No other site writes `build_run_assets.started_at`.

The report and the docstring say "exactly one site". That is inaccurate by one, although the second site has
the same meaning (C5).

**Can a row become `complete` without being started?** No.
- Every `'complete'` write targets either a row that `run_asset` already set to `building`
  (`asset_runner.py:642/856/929/1205`) or the standalone row, which is inserted as started.
- The watchdog completes only `bra.state='building'` rows (`watchdog/route.ts:256`).
- Every script and runner path that touches unstarted rows writes `aborted` or `error` from `queued`:
  - `_terminalize_preflight_failure`;
  - the watchdog undispatched reap;
  - `dispatch_*` `mark_dispatch_failed`;
  - `_mark_asset_blocked` (`runner.py:495`).
- The ~40 `dispatch_*`/`rebuild_*` scripts only INSERT `'queued'`.

**Can the writer run without `started_at`?** No, for any orchestrator path: `run_asset` flips to `building`
before it chooses a writer. The standalone runner also sets it. The fail-safe direction (a writer run
outside `build_run_assets`) yields "never run" → FAIL, which is non-closable.

**Can a row be started without the writer running?** Yes. This matters for wording (C5), not for closure.
After the `building` flip, the engine can finish or fail an asset without invoking its writer:

| path | outcome | why it is still an earned signal |
|---|---|---|
| `_skip_no_delta` | `complete`, disposition `skip_no_delta` (61 live rows, all started) | It requires a `proven` stored receipt whose code, config, upstream and partition digests all match. That is a verified prior success, not a guess. `bg_sign_medical` has **0** receipts, so its first dispatch cannot skip. |
| `_mark_probe_green` | `complete`, no rows written | A real probe or integrity check passed. **Dead today:** `rebuild_on_probe_fail` is false on every active asset (0 eligible, verified live). |
| legacy `_run_service_health_probe` | `complete` | Writerless services only, whose Build.exercised is N/A anyway. |
| pre-writer `mark_asset_error` | `error`, started (no writer / birth_params / provenance / probe-failed-no-writer) | Build.exercised PASS ("dispatched"), and Build.history FAILs on the same row. The defect stays visible. |

**Ruling.** `started_at IS NOT NULL` measures "the orchestrator dispatched this asset past the building
transition". That is exactly what Build.exercised claims, since its gap text is "the orchestrator has NEVER
run it". Every completion that rests on a started row is backed by a writer run, a proven receipt, or a
probe. **Genuine.** The report's word "executed" overstates this slightly; "started" is precise (C5).

### §2.2 — Live distribution (read-only, pgenv, 2026-09-27)

`state: rows (started) · skip_no_delta`:
- `aborted` 649 (8) · 0;
- `complete` 3 133 (3 133) · 61;
- `error` 1 515 (319) · 0;
- `queued` 1 465 (0) · 0.

**This reproduces the report exactly.** Other live checks:
- Across the 121 active assets that have rows, **0** are unstarted-only and **0** are started but never
  complete.
- `bg_sign_medical` is the only active writer-backed asset with no `build_run_assets` row.

### §2.3 — `skip_no_delta` under the census's own semantics

`skip_no_delta` rows are started (61/61) and `complete`. The census counts them as executed and as
completions, and it reports them as "(healthy)".
- This is consistent. The gate only skips on a `proven` receipt, and a receipt exists only after a prior
  success (`provenance.previous_receipt_matches_inputs`, which fails open to execution).
- A history whose only completions are skips still rests on a real earlier completion.
- **Correct.**

### §2.4 — Build.history with zero completions

I walked every return of `_grade_build_history` with `complete == 0`:

| condition | verdict |
|---|---|
| last state `error` (not blocked-only) or `aborted` | FAIL |
| any genuine error or abort on record | PARTIAL |
| blocked-only | PARTIAL (the C-4 guard) |
| otherwise | **NO_DETECTOR** (new) |

**No `complete == 0` route reaches PASS or N/A.** The only N/A for Build.history is the "never run"
delegation (#31), where Build.exercised FAILs for a writer-backed asset.

One route to PASS needs `complete ≥ 1` on an unstarted row. No engine or script path can write that (§2.1),
and there are 0 live instances. It would read Exercised FAIL beside History PASS. It is latent and
non-blocking (F-L1).

### §2.5 — Reproductions and attacks

These are in `rev-w2-1c/attacks/`. Each imports the real `build_history()`, `measure()` and `emit_gaps()`,
fakes only psql, and uses a **fresh copy of the production `asset_gaps.jsonl`**, where
`bg_sign_medical-Build.exercised` is OPEN.

| id | input | result at HEAD |
|---|---|---|
| **original A8** (`rev-w2-1/attacks/test_attack_queued.py`, verbatim) | 1 `queued` row | its PASS/PASS/closed=1 assertion **now fails**: Exercised FAIL "none ever started", History NO_DETECTOR, **closed 0**, all rows OPEN |
| R0 | A8 with the old 6-column row | Exercised FAIL, gap OPEN |
| R1 | 1 `queued`, started=`f` | FAIL / NO_DETECTOR, gap OPEN |
| R2 | queued + guardian-aborted + BLOCKED error + blocked_dependency error, all unstarted | FAIL / PARTIAL, gap OPEN |
| R3 | blocked_dependency errors only | FAIL / PARTIAL (C-4), gap OPEN |
| R4 | one started row left in `building` (orphan) | Exercised PASS (a real start); History **NO_DETECTOR**, not closable |
| R5 | psql `'f'` must not be truthy | FAIL, gap OPEN |
| R6 | positive control: started `complete` + queued leftover | PASS / PASS, gap CLOSED: the detector can read true |

All 7 pass. The only other closures on the copies (`bg_sign_medical-Idem.pattern`, `-Build.completion`) are
harness stubs: a stubbed idem PASS and a stubbed build record equal to live. They are not C1.

### §2.6 — Mutations (reviewer's own)

**Method.**
- A scratch mirror of `asset_census.py` plus `__tests__/`, run from the repo cwd.
- The census files plus `test_a2`/`a3`/`a4`/`b1`/`w2_1` are run against each mutant.
- The copy is restored and checked byte-identical afterwards.
- The baseline shows 1 failure, `test_f6_tracker…`, a path artefact of the mirror.

| mutation | killed by the committed suite? |
|---|---|
| M1 `if started in ("t","true")` → `if started:` (`'f'` becomes truthy) | **killed**, 3 tests |
| M2 executed = `state in ("complete","error","aborted")`, the design the C1 commit rejects | **SURVIVES.** Run against my R2/R3/R5 inputs, it re-closes `bg_sign_medical-Build.exercised` on an unstarted `aborted` or BLOCKED row (`attacks_vs_M2.out`: "closed … bg_sign_medical-Build.exercised"). → **C4** |
| M3 zero-completion NO_DETECTOR guard removed | killed, 3 |
| M4 unstarted writer-backed asset reads N/A instead of FAIL | killed, 2 |
| M5 SQL `started_at` → `ended_at` | **SURVIVES** (offline and live). No test pins the column. → **C4** |
| M6 exercised gate on `runs` instead of `executed` | killed, 2 |
| M7 unstarted history → delegating N/A | killed, 2 |

**Suite at HEAD (live, pgenv):** 221 passed, 2 failed. The 2 failures are the pre-existing
`test_drift_detector_h35_h38.py` pair; 0 skipped. The W2-1 file offline gives 41 passed, 4 skipped.

**Builder's evidence note.** In `mutation_runs_C1.log`, "M4 full-revert-both" has the same substitution size
as M2 (80→67 chars), so it does not evidence reverting both guards. Its after-revert line reads "2 failed,
191 passed". HEAD itself is clean in my run, so this is a log-quality issue only (C5).

## §3 — Open-ledger-row → verdict map (the decisive test)

**Production `asset_gaps.jsonl`.**
- 263 lines, md5 `30365ff2…`; `asset_certs.jsonl` md5 `514cbdfc…`.
- Unchanged at the start and the end of this review.
- The last commit touching `control/` is `6574d729b`, an ancestor of `9baaa307b`.
- The latest row per `gap_id`: 261 OPEN, 1 IN_PROGRESS, 0 superseded, giving **262 live rows**.

I mapped each one to its verdict in my six-layer HEAD census (the census JSONs from §4):

| verdict at HEAD | rows |
|---|---|
| NO_DETECTOR | 120 |
| PARTIAL | 50 |
| FAIL | 39 |
| not a census id (hand rows, including the IN_PROGRESS `bg_sarvatobhadra_grid-G01`) | 53 |
| **PASS / N/A** | **0** |

**Would-close list: empty.** The first production emit closes nothing.

### §3.1 — The NEXT instance: every live census-id row, and the only branch that could close it

All live census-id rows are L0. For each criterion, I asked whether that branch can close the row on an
unmeasured basis today.

| criterion (open) | HEAD verdict | closing branch (#, report §3) | unmeasured closure possible today? |
|---|---|---|---|
| Build.exercised (1: bg_sign_medical) | FAIL, no rows | #32, ≥1 started row | **No.** A start is a real dispatch. It has no receipt (no skip) and no probe-rebuild policy (no probe-green). A pre-writer error start closes Exercised but FAILs History. Genuine. |
| Build.history (13) | PARTIAL, all with an error or abort on record | #4 / #5 | **No.** `bad` only grows, so these can never reach PASS. They are permanent opens: fail-safe, not a closure. |
| Build.completion (10) | FAIL, 8 × `rows_written=0` vs live > 0; 2 × no build record | #23 PASS / #22 N/A | **No.** Each needs a completed record with `rows_written == live`. None declares floor 0, so the A5 residual does not apply. None has a constant count_sql, so A7 does not apply. The skip path keeps `rows_written` (0 stays 0). Probe-green is dead. #22 needs no count_sql, and all 10 have one. |
| Build.registered (2) | FAIL: `@register` present but registry has_writer=false | #15 / #16 | No. PASS or N/A needs the source scan and the registry to agree. Genuine. |
| Build.count_integrity (1) | PARTIAL: integrity_check_sql missing | #20 presence | No. The claim *is* presence. Genuine (declaration). |
| Count.floor (1: bg_parihara_rules 440 < 449) | FAIL | #13 measured / #12 floor 0 | No. A measured count, or a floor re-declaration, which is §N.4 doctrine ("floors aspirational"). |
| Vocab.alias (1) | FAIL | #26 | No. Measured. |
| Complete.depth (9) | PARTIAL: never-populated columns | #24 | No. Measured (whole-table scope, F6). |
| Idem.pattern (27) | PARTIAL: no ON CONFLICT in the writer | #2, a proxy (A2) | Not today. A later closure needs a real SQL string (docstrings are excluded) containing ON CONFLICT on *some* table. That is measured but weaker than the claim. Registered as A2/R20. |
| Dens.served (24) | FAIL: modules present, 0 declaring | #29, contested (OS-3 / A4) | Not today. **Later:** a *comment* containing `density_contract` in any referencing module would close it, which is an unmeasured basis (F-S1, below). |
| Carr.detector (40) | NO_DETECTOR | #14 | No. `control/detectors/` does not exist; a detector must exist, exit 0, and emit a closed-set verdict. |
| Earn.build_record / Cost.baseline (80) | NO_DETECTOR | #6–10 | No. Unreachable: the only call site is `measure()` `:1074`, which passes `attempt_linkage_wired=False`. |

The criteria with contested closure branches (Build.dep_liveness, Build.target, Build.dag) have **0 live
production rows**.

**The new C1 branch is not in the report's enumeration.** When rows exist, none started, and the asset has
no writer, Build.exercised reads **N/A** ("never executed … no writer — consistent"). This is the sibling of
#30, and it gets the same ruling: genuine by consistency with #30. It is new since `d465d5a2c` and is not
listed in report §3, so the true count is 36 branches (C5). 0 live instances, and 0 open rows on writerless
assets.

**Conclusion for the first emit:** no live production row can be closed on an unmeasured basis by any branch
at HEAD. **There is no NEXT instance that reaches the production ledger today.**

## §4 — The first production emit, simulated end to end

**Method.**
- `00_ARCHITECTURE/control/` was copied six times to `rev-w2-1c/emit/<L>/control/`.
- For each layer: `NIKASHA_CONTROL_DIR=<copy> timeout 300 python3 platform/scripts/governance/asset_census.py
  --layer <L> --emit-gaps --out <scratch>`, all six in parallel.
- Gap ids are per-asset and asset ids do not overlap across layers, so the union of the six appends equals
  one sequential run.

| layer | FAIL · PARTIAL+NO_DET · ERRORED | appended OPEN | already present | CLOSED | RE-OPENED | exit / secs |
|---|---|---|---|---|---|---|
| L0 | 43 · 172 · 0 | 6 | 209 | 0 | 0 | 2 / 79 |
| L1 | 7 · 106 · 0 | 113 | 0 | 0 | 0 | 2 / 211 |
| L2 | 15 · 121 · 0 | 136 | 0 | 0 | 0 | 2 / 233 |
| L3 | 55 · 111 · 0 | 166 | 0 | 0 | 0 | 2 / 181 |
| L4 | 27 · 45 · 0 | 72 | 0 | 0 | 0 | 2 / 22 |
| L5 | 31 · 72 · 0 | 103 | 0 | 0 | 0 | 2 / 23 |
| **total** | | **596** | **209** | **0** | **0** | |

**Transitions by type:**
- 596 new OPEN, 0 CLOSED, 0 RE-OPENED.
- By criterion: Earn.build_record 87, Cost.baseline 87, Carr.detector 87, Build.history 83, Complete.depth
  51, Idem.pattern 48, Build.completion 38, Dens.served 35, Build.dep_liveness 27, Count.floor 16,
  Build.registered 13, Build.contract 13, Vocab.identity 7, Build.count_integrity 4.

**Integrity checks.**
- Every copy's ledger begins with the production bytes: append-only.
- Every copy's `asset_certs.jsonl` is byte-identical to production.
- **Idempotent.** A second CLI emit on the L0, L4 and L5 copies gives 0 appended (215 / 72 / 103 present),
  0 closed, and an unchanged md5.
- Production md5 before and after: `30365ff2…` / `514cbdfc…`.

**Every CLOSED row has a genuine measurement behind it.** This holds vacuously: there are none. The figures
match the report's §11 and the W2-1 review's §5 exactly.

## §5 — C3 spot-check (the five corrections against the review)

| item | review asked | v1.1 | ok? |
|---|---|---|---|
| (i) R42 basis | bo_upaya 5-table vs 2-table; ga_condition one table; call them basis mismatches | §2 R42 body (`:274–280`), §4 (`:508–510`) and OS-9 (`:726`) all say so, with figures | ✓. **Residual:** the R42 heading (`:258`) still reads "compares, like for like" (C5). |
| (ii) R52 A5 flip | disclose FAIL→PASS on truncating a floor-0 asset | §8 item 3 (`:678–681`), with the no-live-instance and no-open-gap statements | ✓ |
| (iii) Dens.served | 29, not 31 | §3 #29 and OS-3 read 29 | ✓ |
| (iv) proxy labels | #1, #2–3, #25, #29 as proxies; #5 and #32 relabelled | §3 table and tally (18 / 10 / 3 / 4) | ✓. #25 is noted as "fixed with F7 proxy caveat" rather than counted among the 3 proxies; acceptable. |
| (v) T1 framing, plus §11 | 16/16 applicable + 1 awaiting re-spec | §0 item 3 and §5 table | ✓. **Residual:** §0 (`:67–68`) and §5 (`:564`) still call `earn_cost_signal` a "miss" beside the new framing (C5). |

## §6 — Scope

**Files touched.**
- `git show --stat 1ae91dae4 8fc9bcac5` lists only:
  - `platform/scripts/governance/asset_census.py`;
  - `platform/scripts/governance/__tests__/test_w2_1_earned_verdicts.py`;
  - `nikasha_test/wave2/W2-1_REPORT.md`;
  - five files under `nikasha_test/wave2/w2-1_evidence/`.
- HEAD is `8fc9bcac5`, and the two commits are the only ones after `8af39a194`.
- `git diff 9baaa307b HEAD -- 00_ARCHITECTURE/control/ platform/python-sidecar` is **empty**. No engine,
  writer or ledger file was touched.

**My own footprint.**
- The working tree is clean apart from the pre-existing `.agents/agents/`.
- No repo file was edited other than this review.
- All scratch work is in `rev-w2-1c/`.
- The DB was accessed only through the read-only pgenv.

## §7 — Findings and the gate each blocks

| id | finding | blocks |
|---|---|---|
| **C4** | **Test gap in C1.** Mutation M2 (executed = state list `{complete, error, aborted}`, the design the C1 commit rejects) and M5 (SQL reads `ended_at` instead of `started_at`) both survive the committed suite. On the M2 mutant, the A8 closure of `bg_sign_medical-Build.exercised` returns through an unstarted `aborted` or BLOCKED-`error` row. **Fix:** (a) add an offline test with unstarted `aborted` plus unstarted non-disposition `error` rows for a writer-backed asset with an open gap, asserting Exercised FAIL and 0 closed; my R2 is ready to adapt. (b) Add a SQL-text or live assertion that `build_history()` selects `started_at IS NOT NULL`. Record both mutations. | **W2-1 fold** (row C1 recorded closed). Does **not** block the first production emit: the code at HEAD is correct (§2.1, R2/R3/R5). |
| **C5** | Wording and accuracy, text only: (a) "started_at is set at exactly one site", in the report `:765` and the docstring `:540`, omits `run_heavy_writer_standalone.py:137`, which has the same meaning; (b) "executed" means *started* (dispatched past the building flip), which includes `skip_no_delta`, probe-green and pre-writer-error attempts, and the report should say so; (c) the new writerless unstarted Build.exercised N/A branch is missing from §3, so the count is 36 with the new branch ruled genuine like #30; (d) R42 heading `:258` "like for like"; (e) "miss" for `earn_cost_signal` at `:67–68` and `:564`; (f) the `mutation_runs_C1.log` M4 entry does not evidence "both reverted" and shows a 2-failed after-revert line. | Folding the report text as the record. Not the rows, and not the emit. |
| C2 (carried) | Build.dep_liveness PASS on `lit` on any chart. The first emit **opens 27** dep_liveness rows, which a later emit could close on another chart's state. The same class covers `lit` rows set outside the orchestrator: `bg_sign_medical` is `lit` with no build run. | **Any production emit after the first**, until R45 (W2-2). Unchanged. |
| F-S1 | Dens.served #29 accepts a *comment* containing `density_contract` as a declaration (A4). After the first emit, 59 Dens.served rows are open (24 + 35), so a later emit could close one on a comment, which is an unmeasured basis. 0 live instances. | Recommended: add it to the same "subsequent emits" gate as C2 (hand-verify any CLOSED Dens.served row) until OS-3 is fixed. Not the first emit. |
| F-L1 | Latent: the census counts `complete` rows regardless of `started_at`. A complete-but-unstarted row would read Exercised FAIL beside History PASS. No engine or script path writes one, and there are 0 live instances. Optional hardening: count completions only on started rows. | None (latent). |
| F-P1 | Pre-existing (B1): when the last row is a blocked_dependency error, `_grade_build_history`'s PARTIAL text says "latest run complete". False text, non-closable direction. | B1 owner. Not W2-1. |

**Bottom line.** C1 is correct and closes the only unmeasured-to-closable path the W2-1 review bound to the
R222 precondition. No live production row can be closed at HEAD on an unmeasured basis. The simulated first
emit closes nothing. **R222 precondition: MET.** C4 and C5 are due at the W2-1 fold. C2, plus F-S1 as
recommended, gate any emit after the first.
