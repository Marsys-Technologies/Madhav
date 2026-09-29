---
artifact: SUVARNA_ROLE_MONITOR
canonical_id: SUVARNA_ROLE_MONITOR
version: "1.3"
status: "PRE-FINAL v1.5 — for the parallel independent reviews (GPT-6 Astra, Kimi K3; N-30); then reconciled by Strategic Suvarṇa into the final set; then N-1"
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa"
changelog:
  - "1.3 (2026-09-30, plan set v1.5 pre-final): runs as a launchd daemon under the suvarna user from the native-owned control checkout /Users/Dev/suvarna/control (N-34, N-37). Check severities follow the stage-aware check matrix (Astra F3; LG.3). hold reads the hold ledger (N-35); isolation measured as the suvarna user, the builder credential unreadable (N-25, N-36; LG.2); new decision-log integrity (owner and mode of authority/), hold-ledger integrity, per-session heartbeats (--session engine|exec) and a post-merge audit of every swarm-merged PR, a violation setting a hold (N-38). builder_scope includes the global-L0 grant (N-31). The interim alerting-only watchdog and waiting for the native dropped: the watchdog relaunches under the durable runtime, then holds and parks to Strategic Suvarṇa (N-34, N-28)."
  - "1.2.1 (2026-09-30, review pass 3; REVIEW_PASS3_DISPOSITION_v1_0.md): isolation warns until N-25 is decided (exit 1 only from it before N-25); builder_scope warns until E7.2 writes builder_identity.json."
  - "1.2 (2026-09-29, review pass 2 folded): runs from the committed code in the hq worktree and is restarted after each plan merge; D6 applied (credential_readonly reads ok); builder_scope measured through the authenticated preflight, not the reader; new isolation and decision_writers checks (L.16a; code items in REVIEW_PASS2_DISPOSITION)."
  - "1.1 (2026-09-29, L.12 sweep to the v1.3 set): eight checks, including credential_readonly (D6: the login is suvarna_reader with no write path by effective privilege); builder_scope added by E7.3 (D1). Credential semantics match monitor.py: missing blocks; group/world-readable or a backup beside it warns; a changed file is not detectable by stat. Power: warn on battery at 50% or more, block below; a build treats a power warn as a failed precondition. Stalls and spend belong to the Conductor (arch §12.8), not the Monitor. New: the Conductor watchdog (D5, charter G15; alerting from L.15, relaunch from L.14). Whole-item blocked events are the Conductor's (arch §12.1); the Monitor's only blocked event is the watchdog's. Stale 'ROLE_COMMON open question 9' references replaced by arch §12.8 and §12.1. Sources: REVIEW_PASS1_DISPOSITION_v1_0.md (C15, C16, C34, C43; S16, S27 residuals); D5, D6."
  - "1.0 (2026-09-29): first draft, from arch §3.1, §5.4, §8, §11.3, charter G15, R10, §10 and platform/scripts/governance/suvarna_tracker/monitor.py."
---

# Role · Monitor

Read `ROLE_COMMON_v1_0.md` first. It holds the shared rules; this file does not repeat them.

## Who you are

The Monitor is a script, not a model (arch §3.1: "no model — a script"). It checks the environment the swarm runs in,
repairs what it is allowed to, watches the Conductors' heartbeats, and writes what it sees to the event log. This file
is for the runtime that starts it (a launchd daemon under the `suvarna` user, part of the durable runtime L.14, N-34)
and for every role that reads its output. Always on, one instance, serving both execution sessions.

## Inputs

- `/Users/Dev/suvarna/control/platform/scripts/governance/suvarna_tracker/monitor.py`: the native-owned control checkout
  pinned to a tagged control release (`suvarna-control-v<x>`), never a working copy elsewhere; restarted when SS moves
  the control release (N-37). Environment: `SUVARNA_HOME=/Users/Dev/suvarna`; the
  credential path defaults to `~/.config/suvarna/pgenv.sh`, which the `credential` check only `stat`s and never opens.
  The `credential_readonly` check runs one read-only catalog query through that file, in a subprocess, and never prints
  it.

## What it does

1. **launchd keeps it running** (N-34) as the `suvarna` user with:
   `PYTHONPATH=/Users/Dev/suvarna/control/platform/scripts/governance SUVARNA_HOME=/Users/Dev/suvarna python3 -m suvarna_tracker.monitor --watch 300 --emit --repair`
2. **Checks** every 300 seconds, each `ok`, `warn` or `block` (arch §8); overall exit 0 / 1 / 2. **Which checks apply,
   and whether a failure warns or blocks, is set per campaign stage by the stage-aware check matrix** (Astra F3; LG.3);
   the matrix in the control release is authoritative over the severities below:
   - `db_proxy`: the database proxy listening on 5433;
   - `credential`: the file exists (missing blocks); owner-only (group- or world-readable warns); no
     `pgenv*.bak*`, `pgenv.previous*` or `.pgenv.*.tmp` beside it (warns). It cannot see whether the contents changed;
   - `credential_readonly` (D6): session and current user both `suvarna_reader`, its role default read-only, and no
     write path by effective privilege (tables, columns, sequences, CREATE, memberships, ownership, SECURITY DEFINER
     functions) and no exposure of withheld columns. Any write path or exposure blocks. D6 is applied (2026-09-29), so
     it reads ok; if it ever blocks, nothing is dispatched;
   - `power`: AC ok; on battery at 50% or more warns; below 50% blocks. A production build treats a `power` warn as a
     failed precondition (charter §6.7);
   - `sleep_prevented`: `caffeinate` or an active assertion;
   - `hold` (N-35): any active hold in `authority/HOLDS.jsonl` (no matching line in `authority/HOLD_CLEARS.jsonl`), or a
     legacy `run/SUVARNA_HOLD`, blocks; the hold ledger's integrity (file append-only, directory native-owned) is checked
     too, and a breach blocks;
   - `disk`: below 20 GB warns, below 5 GB blocks;
   - `tracker`: `/api/health` answers.
   - `isolation` (L.16a, arch §2.4, N-25; LG.2): measured **as the `suvarna` user**: who the process runs as, that the
     native's credential files and the builder credential (held by `_suvarnabuild`, N-36) are not readable, what it can
     write, settings-file hashes;
   - `decision_log` (N-37): `$SUVARNA_HOME/authority/` and `DECISIONS.jsonl` native-owned with the expected modes, the
     swarm read-only; any `decided` line not written by `strategic-suvarna` blocks (`decision_writers`);
   - `heartbeats` (N-34): each session's Conductor heartbeat (`--session engine`, `--session exec`) is fresh; a stale one
     feeds the watchdog (step 4);
   - `merge_audit` (N-38): every PR the swarm identity merged is audited after the merge (CI green on the merged head, a
     gate-reviewer ACCEPT for that head SHA, the path guard); a violation sets a hold, and a revert PR follows.
   A check that cannot measure reports `warn`, never `ok`. `builder_scope` (E7.3, D1) reads the builder's own scope from
   `suvarna-build --preflight` (the reader cannot read `chart_grants.permission` or `profiles`): `guest`, `active`,
   grants exactly `{(482012f1, 'build')}` plus the global-L0 build grant (N-31), matching `run/builder_identity.json`;
   it reads `warn` until E7.2 writes that file; after, anything else, or a failed preflight, blocks.
3. **Repairs** (`--repair`, G15), only when the process is verifiably not running: restart the database proxy on 5433
   (never a proxy on another workstream's port), the tracker supervisor (`run_tracker.sh`), and `caffeinate`. With the
   any hold active, it repairs nothing.
4. **Conductor watchdog** (D5, arch §5.5, G15; N-34). A Conductor whose per-session heartbeat is stale is stalled:
   emit `blocked` on the session's Conductor, write `$SUVARNA_HOME/run/CONDUCTOR_STALLED`, and relaunch one headless
   pass through the durable runtime (L.14: `claude -p` with the Conductor prompt, `--permission-mode dontAsk`, in the hq
   worktree; the queue fence refuses a duplicate). At most three relaunches an hour per session; then set a hold
   (`python3 -m suvarna_tracker.hold --set --reason …`), emit why, and park to Strategic Suvarṇa. A usage-limit pause
   reads as a stall: read the CLI's error and wait it out; never restart-loop. There is no alerting-only interim and no
   waiting for the native. The watchdog is an N-1 prerequisite (LG.6); until it is in the control release it does not
   exist: do not improvise it.
5. **Never touches** the credentials, a hold (it sets one after the third relaunch or a merge-audit violation, and never
   clears one, N-35), disk or power (G15, R10). Those are reported, and the Steward parks them. A missing credential file, or one that fails
   `credential_readonly` or `builder_scope`, is never recreated or changed (charter §10).

## Pausing dispatch

- The Monitor does not stop other agents itself. **Before each dispatch the Conductor runs**
  `python3 -m suvarna_tracker.monitor --once` **and dispatches nothing on exit 2 (block)** (arch §8, §12.8).
- On a block the Conductor emits the pause, and the resume, as `note` events (ROLE_CONDUCTOR step 2). Items already
  running finish.
- **Agent stalls and the spend meter belong to the Conductor** (arch §12.8). The Monitor does not measure them.
- The tracker's `monitor_check_ok` detector runs `monitor --once --json` itself (arch §11.7); `run/monitor_state.json`
  keeps only the non-ok set.

## Outputs and where they go

- `$SUVARNA_HOME/run/monitor_state.json` (the last non-ok set); `$SUVARNA_HOME/run/proxy.log` for a proxy it started;
  `$SUVARNA_HOME/run/CONDUCTOR_STALLED` when the watchdog fires.
- Events in `$SUVARNA_HOME/run/EVENTS.jsonl` (below).

## Report as it happens

With `--emit` the script writes, as actor `monitor`:
- a `heartbeat` every pass (`ok: <n>/<n>`, or `WARN: …` / `BLOCK: …` listing the non-ok checks);
- a `note` when the set of non-ok checks changes, including when it clears;
- a `note` per repair taken (`repair: …`), per Conductor relaunch and per merge-audit result;
- the watchdog's `blocked` on a stalled Conductor. Every other whole-item `blocked` on a plan item is the Conductor's
  (arch §11.3, §12.1).
If the monitor's own emit fails, its output shows `emit errors`: treat that as the log being unwritable (P12) and stop
dispatch until it is fixed.

## Authority

- **Acts under:** G15 (repair the database proxy, the tracker supervisor and sleep prevention; relaunch a stalled
  Conductor, at most three times an hour, then hold and park), G14 (set a hold, after the third relaunch or a
  merge-audit violation).
- **Park to Strategic Suvarṇa through the Steward:** a credential check that blocks (R10); hold on, disk low, power on
  battery.
- **Refuse:** P1 (it never reads a credential), P2, P13 (a relaunch never uses a bypass mode).

## Stop conditions

The watch loop ends only on SIGTERM or interrupt. launchd restarts it (step 1); a Conductor that finds it down reports
it, never starts a copy of its own.
The Conductor's own `--once` check before each dispatch does not depend on the watch loop being up.

## Done means

Always on: a `monitor` heartbeat no older than about 300 seconds on the tracker, a note for every change of state, a
note for every repair and relaunch.
