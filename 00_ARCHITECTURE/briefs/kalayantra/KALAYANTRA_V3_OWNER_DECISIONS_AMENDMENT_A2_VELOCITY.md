---
title: KĀLA-YANTRA v3 owner decisions — Amendment A2 (throughput)
version: 1.1
status: CURRENT
date: 2026-10-15
amends: KALAYANTRA_V3_OWNER_DECISIONS_v1_0.md and Amendment A1 (D-14, D-16), KALAYANTRA_RELAUNCH_PLAN_v2_7.md (§8 escalation, max_loops), the cockpit fast-lane launcher and its COMMON_HEADER
precedence: where this amendment and any amended document disagree, THIS AMENDMENT GOVERNS. Amended files stay byte-identical (packets pin their hashes), exactly as A1 did.
changelog:
  - "1.1 (2026-10-16): D-OWNER-TESTS-20261016 replaces D-17 review/acceptance rules; fixed-finding proof and other safeguards retained."
  - 1.0 (2026-10-15): created on the owner direction of 2026-10-15 (native, in chat, ~08:55Z, "Approved for everything") approving the throughput plan derived from the measured run of 2026-10-14.
---

# Amendment A2 — throughput

**Written for:** the cockpit session (conductor), the owner surrogate and every fleet job. Rules are §2–§6; §7 is the execution order; §8 is how success is measured.

## §1 · Why — what 2026-10-14 measured

| Measure (2026-10-14 UTC) | Value |
|---|---|
| Codex jobs launched | 128 |
| Agent-hours | 45 |
| Tracker items closed | 8 (4 verdicts, 2 planning, 2 capability) |
| Share of agent effort spent on fix-then-re-review loops of 4 already-built packets | ~60% |
| Jobs per item, worst cases | K7-3: 17 · K12: 12 · K3: 9 |
| Jobs ending `blocked` | 20 of 122 finished |
| `blocked` jobs launched in the locked sandbox | 18 of 20 |
| Hours with no launches while work was pending | ~9 of 21 |
| Overnight stall (cockpit session ended, nothing resumed it) | 21:06Z → 07:38Z |
| Plan scope change (J-0m, PR #3499) | 152 → 213 items, at 19:04Z |

Not a bottleneck: CI (median 2 min) and merge latency (median 1.6 h).

## §2 · D-17 — optimum testing and bounded review (amended 2026-10-16)

1. **One bounded review round.** [D-OWNER-TESTS-20261016](DECISION_TESTING_STANDARD_v1_0.md) governs campaign-wide; a second round is permitted only for a BLOCKING finding. Non_blocking findings never trigger another round.
2. **MET is earned per distinct production claim.** Oracles pass at the pinned merged head. The REVIEWER, not the author, enumerates every distinct production claim from the brief, packet and cited classical rules in the verdict; each has a doctrine-grounded oracle (classical source cited; B.3/B.10) whose single planted reversion fails at that head. Every real defect is fixed with fail-on-revert proof; no automatic acceptance based on rounds spent.
3. **Optimum tests.** Plant at most one reversion per claim; no combinatorial variants or per-mutant oracle demands. An already-covered variant or a change with no production behaviour is non_blocking and never blocks MET. Never golden-capture current output. Known real defects are fixed regardless; they are not carried forward to obtain acceptance.
4. **The fixer proves its own fix.** A FIX/REWORK job's result must include, per finding, a test that fails on a copy with the fix reverted and passes with it (the revert applied to a copy under the job folder). The re-reviewer checks that evidence and the diff; it does not re-derive the whole packet.
5. **Six-job budget.** Every model job that names an item counts against it (build, fix, rework, CI repair, merge repair, review, re-review). The **seventh** job for an item needs a recorded surrogate ruling: continue (with a reason), split, or retire. The cockpit keeps the count per item in `run/JOB_BUDGET.json`.
6. **Dispatcher safety limits are not acceptance.** The retired dispatcher's `max_loops: 2` and A1 D-14 automatic-stop safeguards remain operational limits. They neither authorize a second round for non_blocking findings nor confer MET; D-OWNER-TESTS-20261016 governs testing and review rounds.
7. **No review of a head that is already queued to merge**, and no re-review triggered only by a merge from main with no conflict in the item's own paths (the existing "approval carries over" record is used instead).

This does not lower the acceptance bar for what is reviewed: every review still runs the earned-signal standard (root CLAUDE.md §N.8). It stops the bar from being re-set every round.

## §3 · D-18 — jobs that touch the database can reach the test database

1. The disposable local PostgreSQL test cluster (native PostgreSQL 15 on `127.0.0.1:55433`, not Docker; production is never reachable from a job) is the database for every job whose diff or tests touch SQL, migrations, writers or DB-backed suites.
2. **The fast-lane launcher's default mode becomes `full`.** `locked` is used only for jobs that change no code or tests (documents, plan-model edits, read-only triage). The locked sandbox turns networking off, which also cut jobs off from the local cluster; that, not a Docker ban, produced 18 of yesterday's 20 `blocked` results.
3. **COMMON_HEADER** states this plainly so jobs stop reporting a Docker ban as the reason they could not run DB suites: "DB suites run against 127.0.0.1:55433 with the suite's own guarded fixture; Docker is neither needed nor used."
4. **The cockpit does not create per-job databases.** DB suites use their own guarded fixtures, which create and drop isolated databases inside the job. On 2026-10-14 the cockpit's own throwaway databases could not be dropped (Claude Code's built-in destructive-action guard refused it, correctly) and the cockpit stalled 13:57Z → 16:08Z waiting for a human. Any leftover databases are listed in a tracked owner item at session end; work never waits on them. Nobody works around that guard.

## §4 · D-19 — the conductor is woken, never replaced

1. A **wake-only watchdog** (`00_ARCHITECTURE/briefs/kalayantra/watchdog/`, installed as the launchd service `com.madhav.kalayantra.watchdog`) checks every 15 minutes.
2. It wakes the cockpit session only when **all** hold: no live process holds the cockpit session (the Claude Code session registry); work is pending (a fleet job running, a finished job newer than the session's last activity, or a `ready` tracker item); and the session has been silent for at least 20 minutes. The global HOLD (`run/HOLD`) or an owner `pause` suppresses every wake.
3. A wake resumes the **same** session in the background (`claude --bg --resume <id>`) with one fixed instruction: continue the campaign per the cockpit prompt and this amendment. The watchdog never plans, launches jobs, merges, writes campaign state or reads credentials.
4. After **three** wakes that produce no session activity within 10 minutes, it stops waking and notifies the owner.
5. **The cockpit never blocks on a housekeeping question.** Anything that genuinely needs a human becomes a tracked owner item; work continues (A1 D-12).

## §5 · D-20 — fleet size follows the shape of the work

1. Until Wave 4 packets P01–P09 and J-4p have landed: pools as now (A1 D-16), all on the five open packets and J-4p.
2. After that, the Wave 4 spine (J-1a → J-2a…J-2d → J-3a…J-3d → J-4a → J-4b → … → J-6l → V-J6) is strictly serial. Pools drop to **one builder, one verifier, one standby**. The cockpit pre-stages the next phase's job while the current phase's build or readback runs. The assertion children of a phase close with their phase; no agent is launched for them.
3. A1 D-16's "start 8 builders / 4 verifiers" is amended accordingly; it returns only if more than three items are `ready` at once.
4. Finished campaign worktrees are removed within 24 hours under the owner's policy (`git worktree remove`, then `git worktree prune`; dirty ones bundled to `/Users/Dev/Archives/` first). The A1 D-16 ceiling (24 all / 16 own) is a ceiling, not a target.

## §6 · D-21 — one honest number, split by wave

1. **One percentage:** complete ÷ total, where complete = done + not applicable. The tracker's weighted `overall.pct` is not shown as progress.
2. The owner view shows three lines: **Wave 4**, **everything else**, **total**. Scope changes are marked on the history chart with their time and size (first: 152 → 213 at 2026-10-14 19:04Z).
3. Daily closures are split into **capability** items and **verdict/planning** items.
4. Velocity is reported as **agent-hours per closed item** (2026-10-14: about 5.6; target below 2).

## §7 · Execution order (cockpit)

| Step | Action | Proof it is done |
|---|---|---|
| 1 | Launcher default `locked` → `full`; COMMON_HEADER DB paragraph replaced (§3.3) | next DB job's `run.sh` shows the full sandbox; header diff recorded |
| 2 | `run/JOB_BUDGET.json` built from existing job folders; rounds counted for open items | file lists every open item with jobs and rounds so far |
| 3 | §2 applied to open items: the five open Wave 4 packets (P01, P03, P04, P06, P07) and J-4p | each has its reviewer-enumerated distinct claims, passing merged-head oracles and one failing reversion per claim; real defects fixed; non_blocking variants never trigger another round |
| 4 | D-17…D-21 appended to `run/DECISIONS_SURROGATE.jsonl` and the tracker as owner decisions (`decided_by: owner direction 2026-10-15`) | entries present |
| 5 | Watchdog installed (`watchdog/README.md`), session id pinned to the cockpit session | **Done 2026-10-15 09:04Z** by the owner's analysis session: `com.madhav.kalayantra.watchdog` loaded, pinned to session 94345d41, first check logged "session live, no action" |
| 6 | Dispatcher `max_loops` default 3 → 2 by a reviewed fleet change | merged PR |
| 7 | Dashboard change for §6 as a normal packet | merged PR |
| 8 | Pools reduced per §5.2 when P01–P09 and J-4p are merged | pool settings and the next status report |
| 9 | Worktree clean-up per §5.4 | worktree count reported |

## §8 · How success is measured (24 hours after step 3)

| Measure | Target |
|---|---|
| `blocked` share of finished jobs | below 5% |
| Items past six jobs without a ruling | 0 |
| Gaps over 30 minutes with work pending and no launch | 0 |
| Items closed | at least 10 |
| Agent-hours | at most 25 |

If two of these miss, the cockpit reports which and why in plain terms, and the surrogate decides the adjustment. None of these rules relaxes A1's kept owner rules (credentials, `rm -rf` on working copies, fabricated records, the global HOLD, no L0–L2 asset in a Kāla run) or root CLAUDE.md §N.
