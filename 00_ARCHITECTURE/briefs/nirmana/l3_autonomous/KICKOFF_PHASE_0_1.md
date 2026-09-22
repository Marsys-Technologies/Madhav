---
artifact: KALA_KICKOFF_PHASE_0_1
version: "1.0"
status: READY_TO_EXECUTE
date: 2026-09-22
governed_by: KALA_PRE_ELEVATION_CRITICAL_REVIEW_v1_0.md §7
authorizes: Phase 0 (freeze + measure) and Phase 1 (Strategy W0 safety) ONLY
stops_at: WAITING_FOR_STRATEGIC_BRIEF (Foundation Contract §9.9)
---

# Kickoff — Kāla pre-elevation setup, Phases 0 and 1

You are opening the **Kāla (L3) pre-elevation setup campaign**. This is execution, not planning.
Phases 0 and 1 of an approved plan. You run autonomously; the native is asleep and reads your
morning report.

## 0. What you are doing and why it is bounded

A seven-lane readiness exercise and a critical review against the governing texts have closed. The
review's §7 carries a six-phase corrected plan. **You are authorized for Phase 0 and Phase 1 only.**
Phase 2 onward is gated on five native decisions that you will PREPARE but must not pre-empt.

Phase 0 = freeze and measure; change nothing.
Phase 1 = make the programme safe (the Strategy's own W0).

When both are complete you stop in `WAITING_FOR_STRATEGIC_BRIEF` (Foundation Contract §9 item 9).
Activity never self-authorizes the next stage.

## 1. Read first, in this order, in full

1. `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_PRE_ELEVATION_CRITICAL_REVIEW_v1_0.md`
   — your governing document. §7 is your plan. §6 lists the five decisions you prepare, not answer.
2. `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_ELEVATION_READINESS_PACKAGE_v1_0.md`
   — the consolidated findings, with its `_work/` lane files as evidence (read what you need).
3. `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_L3_KALA_STRATEGY_v1_0.md`
   — §2 (L3-Q01–Q13), §3 (the data contract), §4 (dependency/lifecycle rules), §5 (efficient
   computation + the benchmark contract), §6.4 (waves), §7 (acceptance states).
4. `00_ARCHITECTURE/briefs/nirmana/MADHAV_DATA_PLANE_FOUNDATION_CONTRACT_AND_GATES_v1_0.md`
   — F01–F28, §3 vocabularies, §8 gate matrix, §9 workflow.
5. `00_ARCHITECTURE/MADHAV_PRODUCT_DEFINITION_v3_0.md` — §9 experiences, §10.2 graceful
   incompleteness, §14 proof obligations. §5.2 typed confidence.
6. Root `CLAUDE.md` — especially §N.2 (frozen orchestrator contract), §N.3 (idempotency),
   §N.7, §N.8 (earned signals).

Do not re-audit. The measurements are done. Your job is to freeze, measure cost, and make it safe.

## 2. Environment

- **Worktree:** create your own from `origin/main`. Suggested `/Users/Dev/madhav-l3/setup`,
  branch `l3/kala-setup-phase01`. Never work in `/Users/Dev/madhav-l3/readiness`,
  `/Users/Dev/madhav-l3/audit` or `/Users/Dev/Vibe-Coding/Apps/Madhav`.
- **Read-only production DB:** `source /Users/Dev/madhav-l3/dbenv.sh` then `psql`.
- **Builder identity (read-only too):** `source /Users/Dev/madhav-l3/dbenv_builder.sh`.
- **Never echo, print, cat or log a password, connection string or `DATABASE_URL`.** A credential
  leaked into logs once in this campaign. `/Users/Dev/madhav-l3/redact.py --scrub <dir>` exists;
  run it before every commit. It is defence in depth, not permission to be careless.
- **Disposable Postgres harness** — the pattern that worked (socket path must be short, `/tmp/...`,
  or you hit the 103-byte limit):
  ```
  PGBIN=/opt/homebrew/opt/postgresql@15/bin
  $PGBIN/initdb -D /tmp/kx/data -U kxuser --auth=trust
  $PGBIN/pg_ctl -D /tmp/kx/data -o "-p 59500 -k /tmp/kx -c fsync=off" -l /tmp/kx/pg.log start
  # schema: pg_dump --schema-only --no-owner --no-privileges -t public.<tables> from production
  # seed:   \copy (SELECT ... ) TO STDOUT  |  \copy <table> FROM STDIN
  ```
  **Carry the trigger FUNCTIONS too** — a table-scoped `pg_dump` drops seven of them and my earlier
  pathfinder ran without production's guard layer. Tear the instance down when done and prove it.
- **Canonical chart:** `482012f1-710e-4a25-994a-93821f5871aa`. `362f9f17-…` is a dead phantom.
- **Never print private chart narrative or interpretation content.** Aggregates, counts, schema, IDs.

## 3. Phase 0 — freeze and measure. Change nothing in production.

**0.1 Freeze the baseline.** The acceptance baseline is the Strategy's own **L3-Q01–Q13** (§2),
plus Product §14's three first-proving-set cases (a deep structural question with no forced
forecast; a structure–time question; a historical challenge that seeks misfit), plus **one ordinary
period** case — Product §9 requires the layer to work for ordinary charts and ordinary periods, and
every fixture we hold is dramatic. Record today's actual answer for each against the deployed
system. This is the "before" that makes elevation falsifiable; it is unrecoverable if skipped.
Deliverable: `KALA_BASELINE_v1_0.md` + a machine-readable fixture set.

**0.2 Confirm the Strategy's P0 safety hazards are actually repaired.** §5 names two: Kshetra
planning mutating before resume filtering, and Bhavishya's empty-input return preceding its
outcome-preservation guard. Both *appear* fixed in code; no receipt shows the required tests ran.
The Strategy demands "zero planning/dry-run mutations; crash/resume and empty-generation tests."
Run them on the disposable harness. If they pass, say so with evidence. If either is still open,
it becomes a Phase 1 item.

**0.3 Measure cost properly.** Adopt the Strategy §5 **benchmark contract verbatim** — record
hardware, dependency/ephemeris versions, workload dimensions, cache state, wall/CPU/RSS, time in
Swiss calls/lock, SQL count and round-trip, rows/bytes/WAL, and time to first qualified result;
repeated matched runs with spread, never a single run. Measure the **five distinct profiles** §5
names: new chart, unchanged replay, dependency correction, extended horizon, precise on-demand
inquiry. Cover every asset you can on the harness; where an asset cannot be measured, say why.
Then **retire `asset_registry.estimated_seconds`** from every calculation and mark it null-worthy
per F28 — it claims 24.3 min for the layer while `ka_kshetra` alone measures ~7.5 h.
Deliverable: `KALA_COST_PROFILE_v1_0.md`.

**0.4 Build the internal input/output/use matrix.** VA §13.3 item 3 and Strategy §4's "two related
maps": the computational build DAG *and* the semantic relationship/use graph, each edge carrying
its **F12 operator role** (`computation`, `applicability`, `counterevidence`, `uncertainty`,
`interpretation`, `exclusion`, `relevance_navigation`, `evaluation`), its source, generation
selector and required coverage. Compare against `depends_on`; unexplained omissions and cycles
block the affected packet. This is the concrete artifact behind "elevate synergistically as a
layer." Deliverable: `KALA_IO_USE_MATRIX_v1_0.md`.

**0.5 Prepare the five decisions** (review §6) as a ruling sheet with your recommendation, the
evidence, and the cost of being wrong for each. Do this EARLY — the native can rule while Phase 1
runs. Do not act on any of them. Deliverable: `KALA_PHASE2_DECISIONS_v1_0.md`.

## 4. Phase 1 — make the programme safe (Strategy W0)

Each item is a separate small PR with its own proof. Migration range **1071–1119** (1070 consumed).
Author each migration surgically, verify it actually applied, and never edit an applied migration.

**1.1 Close B1 — the live deletion path for the protected snapshot.** Three parts, all needed:
  - `asset_registry.ka_gochara.target_table` is `kala_gochara_windows`; its writer only ever
    writes `kala_gochara_windows_v2` (`ka_gochara.py:120,336,362`) and its `count_sql` reads `_v2`.
    Correct the registry row.
  - `platform/src/app/api/cockpit/clear/route.ts:114-117` loads `asset_registry` with no
    `is_active` filter; `clearScopeFilter.ts`'s `layer` branch ignores `is_active` too. Retired
    `ka_gochara_sweep` (`is_active=false`, `scope='per_chart'`, `layer='kala'`) is therefore in
    scope for a layer Clear, and `allowedScopes = ['per_chart']` at `:93` means **a non-admin chart
    owner can reach it**. Add the filter.
  - `build_protected_assets` has **zero rows for every chart** and there is **not one non-internal
    trigger on any `kala_*` table** (positive control). The target is
    `kala_gochara_windows WHERE generation='v1'` — **38,287 rows** — which is the retired
    `ka_gochara_sweep` data the Strategy calls "snapshot-protected and never rebuildable" (§4) and
    the Execution Brief lists under must-not-touch. Put a real guard behind it.
  **Proof required:** a test that fails on today's code and passes after — for each of the three.
  Do not weaken any guard; you are adding one.

**1.2 Builder read grants.** `data_plane_builder` lacks SELECT on `bg_transit_moorti`,
`bg_synthetic_cohort`, `bg_synthetic_cohort_md` — grant these three. **Hold
`phala_rectification`**: that is L3 reading L4, a dependency pointing upward, and it belongs in the
Kshetra brief rather than being cemented by a grant. Use migration 1070's fail-closed
`has_table_privilege` pattern so a silent no-op cannot pass as applied.

**1.3 Explicit timeout on `data_plane_builder`.** It currently has **no** `rolconfig` at all —
no `idle_in_transaction_session_timeout`, no `statement_timeout`. `amjis_app` carries 600 s / 1800 s.
The 600 s killer is the most probable cause of `ka_kshetra`'s `worker_crash: the connection is lost`
(it ran 2026-09-11, a week before the identity cutover). The new identity removes that failure and
introduces the opposite one: an unattended hung build with no server-side bound. Set a deliberate
value; state your reasoning; `db.py:46-70` documents the 20-minute-CPU-substep case that any bound
must survive.

**1.4 Supervisor and session posture.** Apply `_work/LANE_G_ENVIRONMENT_SPEC.md` §2 — the progress
detector counts any file change as progress, so the three-strikes idle halt can never fire; and add
the idle backoff. Also: a `.claude/settings.json` allow/deny scope, and mechanical
`CLAUDE_CODE_FORCE_SESSION_PERSISTENCE=1`.

**1.5 Cascade coordination.** The five-table `ON DELETE CASCADE` from `bodha_msr_signals` has
already fired once on the canonical chart. The separate **Nirmāṇa campaign already adjudicated this
(rulings D-CND-15/16) and already built `cascade_check.sql`.** Verify that campaign's current state
first; adopt its tool; agree a build-order rule. Do not design a new mechanism — the structural fix
(binding to an L2 generation) is Phase 2 and gated on decision 1.

## 5. Hard constraints

- **No Phase 2+ work.** No generation substrate, no temporal-contract change, no qualification
  binding, no force-fit removal, no asset elevation. Prepare, don't pre-empt.
- **Never edit `platform-mcp/src/tools/kala_views/`** or any Pūrṇa-owned file, script or PR. The
  seven hardcoded `dissent: []` sites and the budget-protection work are a Pūrṇa **interface
  packet** (L3-U04/U11), not your code. If you touch that door you will collide with a live campaign.
- Never edit applied migrations (1033–1070), `.github/workflows/deploy.yml`, or weaken any guard.
- `WATCHDOG_SECRET` on revision `amjis-web-02826-huf` is human-owned. Do not touch it.
- No credential rotation. That is the native's decision.
- `ka_gochara_sweep` stays retired, snapshot-protected, never rebuilt.
- "Data is disposable" holds for **rebuildable projections only**. It does NOT cover the sweep
  snapshot, issued claims/observations (F17), or `kala_bhavishya`'s retained outcomes.

## 6. How to work

- **Subagents run in the FOREGROUND.** Put a whole wave's `Agent` calls in ONE message so they run
  concurrently, and never end a turn with "waiting for agents" — a prior cycle exited that way and
  killed its own agents, losing the work and ~$9. Commit each wave before dispatching the next.
- **The live-path test.** For every hazard you report, state whether a live caller reaches it
  today. Three separate lanes in this campaign reported a mechanism that *can* fail as if it *is*
  failing, without checking whether anything reaches it. Say "no live caller found within scope:
  <scope>" rather than "unused".
- **Evidence discipline (F28 / §N.8).** Every claim cites `file:line` or the exact SQL/command.
  "COULD NOT VERIFY: <what, why>" beats a plausible default. A flag with no detector behind it is
  null, not green. Verify at the authority — never by re-running the claim's own query.
- **Proof tiers stay separate** (F24): computational correctness ≠ explanatory value ≠ empirical
  performance. A passing test is not a demonstrated distinction.
- **Push early and verify content, not commit ancestry** — `main` squash-merges, so a merged PR
  rewrites SHAs. Check the file is on `main`, not that your commit is an ancestor.
- The merge queue locks the branch while a PR is queued; a rejected push is usually that, not a
  failure. Re-check rather than forcing.
- zsh: use `${b}` brace form in refspecs (`"refs/heads/$b:refs/heads/$b"` parses as a history
  modifier), and `${=VAR}` when you need word splitting.
- **An honest stop beats invented activity.** If something is genuinely blocked, write the blocker
  and move to another item. Do not manufacture adjacent work.

## 7. What "done" looks like

Five deliverables on `main` (or in cleanly queued PRs): `KALA_BASELINE_v1_0.md`,
`KALA_COST_PROFILE_v1_0.md`, `KALA_IO_USE_MATRIX_v1_0.md`, `KALA_PHASE2_DECISIONS_v1_0.md`, and a
`KALA_PHASE01_CLOSE_v1_0.md` recording what was done, what each proof showed, what is still open
and why. Phase 1's five items each merged with a test that fails before and passes after, or
explicitly blocked with the reason.

Then stop in `WAITING_FOR_STRATEGIC_BRIEF`. Report to the native: what you proved, what you
changed, the five decisions with your recommendations, and what Phase 2 needs from them.

Start by creating your worktree and reading the critical review in full.
